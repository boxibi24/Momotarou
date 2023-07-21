import dearpygui.dearpygui as dpg
from collections import OrderedDict
from copy import deepcopy
from ui.NodeEditor.classes.pin import InputPinType
from ui.NodeEditor.utils import generate_uuid, add_user_input_box
from ui.NodeEditor.item_right_click_menus import variable_right_click_menu, event_right_click_menu
from ui.NodeEditor.input_handler import delete_selected_node


class Splitter:
    splitter_label = 'Splitter'

    @property
    def event_dict(self) -> OrderedDict:
        return self._event_dict

    @event_dict.setter
    def event_dict(self, value: OrderedDict):
        self._event_dict = value
        self.refresh_event_graph_window()
        self._old_event_dict = deepcopy(self._event_dict)

    @property
    def exposed_var_dict(self) -> OrderedDict:
        return self._exposed_var_dict

    @exposed_var_dict.setter
    def exposed_var_dict(self, value: OrderedDict):
        self._exposed_var_dict = value
        self.refresh_exposed_var_window()
        self._old_exposed_var_dict = deepcopy(self._exposed_var_dict)

    @property
    def var_dict(self) -> OrderedDict:
        return self._var_dict

    @var_dict.setter
    def var_dict(self, value: dict):
        self._var_dict = value
        self.refresh_variable_window()
        self._old_var_dict = deepcopy(self._var_dict)

    @property
    def splitter_id(self) -> int:
        return self._splitter_id

    @property
    def combo_dict(self) -> dict:
        return self._combo_dict

    def __init__(self,
                 width=400,
                 height=800,
                 pos=None,
                 event_dict=None,
                 var_dict=None,
                 exposed_var_dict=None,
                 parent_instance=None
                 ):
        self._parent_instance = parent_instance
        self._old_event_dict = OrderedDict([])
        self._old_var_dict = OrderedDict([])
        self._old_exposed_var_dict = OrderedDict([])
        self._width = width
        self._height = height
        self._combo_dict = {}
        if pos is None:
            self._pos = [8, 30]
        else:
            self._pos = pos
        if event_dict is None:
            self._event_dict = OrderedDict([])
        else:
            self._event_dict = event_dict
        if var_dict is None:
            self._var_dict = OrderedDict([])
        else:
            self._var_dict = var_dict
        if exposed_var_dict is None:
            self._exposed_var_dict = OrderedDict([])
        else:
            self._exposed_var_dict = exposed_var_dict
        # Splitter
        with dpg.child_window(
            width=self._width,
            label='Splitter',
            border=False,
            autosize_x=True

        ) as self._splitter_id:
            # TODO: select other items will deselect nodes
            # Exposed var list
            self._exposed_var_collapsing_header = dpg.add_collapsing_header(label='Exposed Variables',
                                                                            default_open=True)
            # Event graph list
            self._event_graph_collapsing_header = dpg.add_collapsing_header(label='Event Graph',
                                                                            default_open=True)
            with dpg.item_handler_registry():
                dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Right,
                                             callback=self.event_graph_header_right_click_menu,
                                             user_data=('', 'Button'))
            dpg.bind_item_handler_registry(self._event_graph_collapsing_header, dpg.last_container())

            self._default_var_header = dpg.add_collapsing_header(label='Variables', tag='__var_header',
                                                                 default_open=True)
            with dpg.item_handler_registry():
                dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Right,
                                             callback=self.variable_header_right_click_menu,
                                             user_data='var')
            dpg.bind_item_handler_registry(self._default_var_header, dpg.last_container())

            self._parent_instance.logger.debug('**** Initialized Splitter ****')

    def event_graph_header_right_click_menu(self, sender, app_data, user_data, instant_add=False):
        parent = self._event_graph_collapsing_header
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        # Try to generate a default name that does not match with any existing ones
        children_list: list = dpg.get_item_children(parent)[1]
        not_match_any_flag = False
        default_name = user_data[1]
        _null_str = user_data[0]
        new_event_tag = '__event' + generate_uuid()
        if children_list:
            temp_name = default_name
            i = 0
            while not not_match_any_flag:
                if i != 0:
                    temp_name = default_name + '_' + str(i)
                for child_item in children_list:
                    if temp_name == dpg.get_item_label(child_item):
                        break
                    elif child_item == children_list[-1] and temp_name != dpg.get_item_label(child_item):
                        not_match_any_flag = True
                        default_name = temp_name
                i += 1
        new_user_data_tuple = (_null_str, default_name)
        if instant_add:
            added_node = self._parent_instance.callback_current_editor_add_node(sender=new_event_tag,
                                                                                app_data=True,
                                                                                user_data=new_user_data_tuple,
                                                                                sender_tag=new_event_tag)
            return added_node
        else:
            with dpg.window(
                popup=True,
                autosize=True,
                no_move=True,
                no_open_over_existing_popup=True,
                no_saved_settings=True,
                max_size=[200, 200],
                min_size=[10, 10]
            ):
                _selectable_id = dpg.add_selectable(label='Add',
                                                    tag=new_event_tag,
                                                    callback=self._parent_instance.callback_current_editor_add_node,
                                                    user_data=new_user_data_tuple
                                                    )

    def variable_header_right_click_menu(self, sender, app_data, user_data):
        with dpg.window(
            popup=True,
            autosize=True,
            no_move=True,
            no_open_over_existing_popup=True,
            no_saved_settings=True,
            max_size=[200, 200],
            min_size=[10, 10]
        ):
            dpg.add_selectable(label='Add', callback=self.add_var, user_data=user_data)

    def refresh_event_graph_window(self):
        """
        Refresh the Event Graph collapsing header on Splitter
        """
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _detail_panel_inst = self._parent_instance.detail_panel
        # First clear out existing items in splitter:
        for value in self._old_event_dict.values():
            splitter_id = value.get('splitter_id', None)
            if splitter_id is None:
                continue
            dpg.delete_item(splitter_id)
        # Then add back the events item to the splitter
        for key, value in self._event_dict.items():
            _event_tag = key
            _event_name = value['name'][0]
            splitter_selectable_item = dpg.add_selectable(label=_event_name,
                                                          parent=self._event_graph_collapsing_header,
                                                          callback=_detail_panel_inst.callback_show_event_detail,
                                                          user_data=_event_tag,
                                                          payload_type='__event',
                                                          drop_callback=self.drop_callback_reorder_event)
            with dpg.drag_payload(parent=dpg.last_item(),
                                  drag_data=_event_tag,
                                  payload_type='__event'):
                dpg.add_text('Event ' + _event_name)
            with dpg.item_handler_registry() as item_handler_id:
                dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Right,
                                             callback=event_right_click_menu,
                                             user_data=(_event_tag, self._parent_instance))
            dpg.bind_item_handler_registry(splitter_selectable_item, dpg.last_container())
            _current_node_editor_instance.item_registry_dict.update({_event_tag: item_handler_id})
            self._event_dict[_event_tag].update({'splitter_id': splitter_selectable_item})

        _current_node_editor_instance.logger.debug('**** Refreshed event graph window ****')

    def drop_callback_reorder_event(self, sender, app_data):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _source_event_tag = app_data
        _destination_event_tag = None
        for event_tag, value in self._event_dict.items():
            if value['splitter_id'] == sender:
                _destination_event_tag = event_tag
                break
        if _destination_event_tag is None:
            _current_node_editor_instance.logger.error(f'Could not find '
                                                       f'Event {dpg.get_item_label(sender)} from event dict!')
            return 3
        source_event_index = -1
        destination_event_index = -1
        for _index, event_tag in enumerate(self._event_dict.keys()):
            if _source_event_tag == event_tag:
                source_event_index = _index
            if _destination_event_tag == event_tag:
                destination_event_index = _index

        if source_event_index == -1 or destination_event_index == -1:
            _current_node_editor_instance.logger.error(f'Could not find the indices of the events in event dict')
            return 3

        # Make a copy of event dict keys
        temp_dict = OrderedDict(enumerate(self._event_dict.keys()))

        _push_up_order = False
        _index_gap = 0
        if source_event_index - destination_event_index < 0:  # push down the order
            _index_gap = destination_event_index - source_event_index
            _push_up_order = False
        else:
            _index_gap = source_event_index - destination_event_index
            _push_up_order = True

        if _push_up_order:
            for i in range(destination_event_index + 1, len(temp_dict)):
                if i - destination_event_index == _index_gap:
                    continue
                _current_node_editor_instance.event_dict.move_to_end(key=temp_dict[i])
        else:
            for i in range(source_event_index, len(temp_dict)):
                if 0 < i - source_event_index <= _index_gap:
                    continue
                _current_node_editor_instance.event_dict.move_to_end(key=temp_dict[i])
        self.event_dict = _current_node_editor_instance.event_dict
        _current_node_editor_instance.logger.debug(f'**** New event dict order updated ****')

    def refresh_exposed_var_window(self):
        """
        Refresh the Exposed Variables collapsing header on Splitter
        """
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        # First clear out existing items in splitter:
        for value in self._old_exposed_var_dict.values():
            splitter_id = value.get('splitter_id', None)
            if splitter_id is None:
                continue
            dpg.delete_item(splitter_id)
        # Then add back the events item to the splitter
        for key, value in self._exposed_var_dict.items():
            _var_tag = key
            _var_name = value['name'][0]
            _is_var_exposed = value['is_exposed']
            if _is_var_exposed[0]:
                with dpg.table(parent=self._exposed_var_collapsing_header,
                               header_row=False, no_pad_outerX=True) as splitter_selectable_item:
                    dpg.add_table_column(no_reorder=True, no_resize=True, init_width_or_weight=100)
                    dpg.add_table_column(no_reorder=True, no_resize=True, init_width_or_weight=400)
                    with dpg.table_row():
                        _selectable_id = dpg.add_selectable(label=_var_name,
                                                            # parent=self._exposed_var_collapsing_header,
                                                            callback=self._parent_instance.detail_panel.callback_show_var_detail,
                                                            user_data=_var_tag,
                                                            payload_type='__exposed_var',
                                                            drop_callback=self.drop_callback_reorder_var)
                        with dpg.drag_payload(parent=dpg.last_item(),
                                              drag_data=_var_tag,
                                              payload_type='__exposed_var'):
                            dpg.add_text(_var_name)
                        _user_input_box = add_user_input_box(var_type=value['type'][0], width=300)
                        _current_node_editor_instance.register_var_user_input_box(_var_tag, _user_input_box)
                self._exposed_var_dict[_var_tag].update({'splitter_id': splitter_selectable_item,
                                                         'selectable_id': _selectable_id})

        _current_node_editor_instance.logger.debug('**** Refreshed exposed var window ****')

    def drop_callback_reorder_var(self, sender, app_data):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _source_var_tag = app_data
        _destination_var_tag = None
        for var_tag, value in self._exposed_var_dict.items():
            if value['is_exposed'][0]:
                if value['selectable_id'] == sender:
                    _destination_var_tag = var_tag
                    break
        if _destination_var_tag is None:
            _current_node_editor_instance.logger.error(f'Could not find '
                                                       f'variable {dpg.get_item_label(sender)} from splitter'
                                                       f' var dict!')
            return 3
        _source_var_index = -1
        _destination_var_index = -1
        for _index, var_tag in enumerate(self._exposed_var_dict.keys()):
            if _source_var_tag == var_tag:
                _source_var_index = _index
            if _destination_var_tag == var_tag:
                _destination_var_index = _index

        if _source_var_index == -1 or _destination_var_index == -1:
            _current_node_editor_instance.logger.error(f'Could not find the indices of the vars in splitter var dict')
            return 3

        # Make a copy of var dict keys
        temp_dict = OrderedDict(enumerate(self._exposed_var_dict.keys()))

        _push_up_order = False
        _index_gap = 0
        if _source_var_index - _destination_var_index < 0:  # push down the order
            _index_gap = _destination_var_index - _source_var_index
            _push_up_order = False
        else:
            _index_gap = _source_var_index - _destination_var_index
            _push_up_order = True

        if _push_up_order:
            for i in range(_destination_var_index + 1, len(temp_dict)):
                if i - _destination_var_index == _index_gap:
                    continue
                _current_node_editor_instance.var_dict.move_to_end(key=temp_dict[i])
        else:
            for i in range(_source_var_index, len(temp_dict)):
                if 0 < i - _source_var_index <= _index_gap:
                    continue
                _current_node_editor_instance.var_dict.move_to_end(key=temp_dict[i])
        self.exposed_var_dict = deepcopy(_current_node_editor_instance.var_dict)
        _current_node_editor_instance.logger.debug(f'**** New event dict order updated ****')

    def refresh_variable_window(self):
        """
        Refresh the Variables collapsing header on Splitter
        """
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        # First clear out variable items in splitter:
        for value in self._old_var_dict.values():
            splitter_id = value.get('splitter_id', None)
            if splitter_id is None:
                continue
            dpg.delete_item(splitter_id)
        if not self._var_dict:
            # Reset old var dict
            self._old_var_dict = OrderedDict([])
        # Then add back the variable item to the splitter
        for key, value in self._var_dict.items():
            self.add_var(sender='', app_data='', user_data=value['name'][0],
                         refresh=True, var_tag=key)

        _current_node_editor_instance.logger.debug('**** Refreshed variable window ****')

    def add_var(self, sender, app_data, user_data, refresh=None, var_tag='',
                default_value=None, var_type=None, default_is_exposed_flag=False):
        """
        Add new variable
        """
        parent = self._default_var_header
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        # Try to generate a default name that does not match with any existing ones
        children_list: list = dpg.get_item_children(parent)[1]
        not_match_any_flag = False
        default_name = user_data
        if not refresh:
            new_var_tag = generate_uuid()
        else:
            new_var_tag = var_tag
        if children_list:
            temp_name = default_name
            if refresh is None:
                i = 0
                while not not_match_any_flag:
                    # Skip first iteration
                    if i != 0:
                        temp_name = default_name + '_' + str(i)
                    for child_item in children_list:
                        if temp_name == dpg.get_item_label(child_item):
                            break
                        elif child_item == children_list[-1] and temp_name != dpg.get_item_label(child_item):
                            not_match_any_flag = True
                            default_name = temp_name
                    i += 1

        with dpg.table(label=default_name, header_row=False, no_pad_outerX=True, parent=parent) as var_splitter_id:
            dpg.add_table_column(init_width_or_weight=400)
            dpg.add_table_column(init_width_or_weight=300)
            with dpg.table_row():
                _selectable_id = dpg.add_selectable(label=default_name,
                                                    callback=self._parent_instance.detail_panel.callback_show_var_detail,
                                                    user_data=new_var_tag)
                with dpg.drag_payload(parent=dpg.last_item(),
                                      drag_data=new_var_tag,
                                      payload_type='__var'):
                    dpg.add_text(default_name)
                # Var type will be one of the InputPinType except for  'Exec' input
                var_type_list = [member.name for member in InputPinType if member.name not in ['Exec', 'WildCard']]
                if self._combo_dict.get(new_var_tag, None) is None:
                    default_type = var_type_list[0]
                else:
                    default_type = self._combo_dict[new_var_tag][1][0]
                _combo_id = dpg.add_combo(var_type_list, width=95, popup_align_left=True,
                                          callback=self.combo_update_callback, user_data=new_var_tag,
                                          default_value=default_type)
            # Add right-click handler to selectable
            with dpg.item_handler_registry() as item_handler_id:
                dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Right,
                                             callback=variable_right_click_menu,
                                             user_data=(new_var_tag, self._parent_instance))
            dpg.bind_item_handler_registry(_selectable_id, dpg.last_container())
            _current_node_editor_instance.item_registry_dict.update({new_var_tag: item_handler_id})

        # If param var_type exist (import new tool), however, override the default type
        if var_type is not None:
            default_type = var_type
            # Update the combo list UI
            dpg.configure_item(_combo_id, default_value=var_type)
        # Prep data
        new_var_info = {
            new_var_tag: {
                'name': [default_name],
                'type': [default_type],
                'splitter_id': var_splitter_id
            }}
        if self._combo_dict.get(new_var_tag, None) is None:
            self._combo_dict.update({
                new_var_tag:
                    [new_var_info[new_var_tag]['name'],
                     new_var_info[new_var_tag]['type']]
            })
        else:
            self._combo_dict[new_var_tag][0][0] = default_name
            self._combo_dict[new_var_tag][1][0] = default_type
        # Update the new var info to the internal var_dict
        if self._var_dict.get(new_var_tag, None) is None:
            self._var_dict.update(new_var_info)
        else:
            self._var_dict[new_var_tag]['name'][0] = default_name
            self._var_dict[new_var_tag]['type'][0] = default_type
            self._var_dict[new_var_tag]['splitter_id'] = var_splitter_id
        # Also update child node graph var dict
        if not refresh:
            print(default_is_exposed_flag)
            self._parent_instance.current_node_editor_instance.add_var(new_var_info,
                                                                       default_value, default_is_exposed_flag)

        # Update old var dict cache
        self._old_var_dict = deepcopy(self._var_dict)

        _current_node_editor_instance.logger.debug('***** Added new var on Splitter ****')
        _current_node_editor_instance.logger.debug(f'Splitter Combo dict: {self._combo_dict}')

    def combo_update_callback(self, sender, app_data, user_data):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _var_tag = user_data
        _var_name = _current_node_editor_instance.var_dict[_var_tag]['name'][0]
        _new_var_type = app_data
        _found_var_node_instance = False
        # Find first Get/Set node instances in current node graph, if found re-confirm with user for node replacement
        for node in _current_node_editor_instance.node_instance_dict.values():
            if node.node_label == 'Set ' + _var_name or node.node_label == 'Get ' + _var_name:
                _found_var_node_instance = True
                break

        if _found_var_node_instance:
            _mid_widget_pos = [int(dpg.get_viewport_width() / 2.5), int(dpg.get_viewport_height() / 2.5)]
            with dpg.window(modal=True, label='Change variable type',
                            pos=_mid_widget_pos) as _modal_window:
                dpg.add_text("Changing variable type will delink and replace all node instances of this var !\n"
                             "This operation cannot be undone!")
                with dpg.group(horizontal=True):
                    dpg.add_button(label="OK", width=75, callback=self.callback_replace_node_of_new_type,
                                   user_data=((_var_tag, _new_var_type), _modal_window))
                    dpg.add_button(label="Cancel", width=75, callback=lambda: dpg.delete_item(_modal_window))
        else:
            self.var_type_update(_var_tag, _new_var_type)

    def var_type_update(self, var_tag, new_type):
        _var_tag = var_tag
        _new_var_type = new_type
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _var_name = _current_node_editor_instance.var_dict[_var_tag]['name'][0]

        self._combo_dict[_var_tag][1][0] = _new_var_type
        # Need to refresh the child Node Graph's var value & default value also
        _current_node_editor_instance.var_dict[_var_tag]['value'][0] = None
        default_var_value = None
        # set default var value based on value type
        if _new_var_type in ['String', 'MultilineString', 'Password']:
            default_var_value = ''
        elif _new_var_type == 'Int':
            default_var_value = 0
        elif _new_var_type == 'Float':
            default_var_value = 0.0
        elif _new_var_type == 'Bool':
            default_var_value = False
        _current_node_editor_instance.var_dict[_var_tag]['default_value'][0] = default_var_value
        # Refresh the exposed variable window
        self.exposed_var_dict = deepcopy(_current_node_editor_instance.var_dict)
        # Also emulate a details callback to refresh show var detail
        self._parent_instance.detail_panel.callback_show_var_detail('', '', user_data=_var_tag)

        _current_node_editor_instance.logger.info(f'Updated new type for var of name {_var_name}: {_new_var_type}')

    def callback_replace_node_of_new_type(self, sender, app_data, user_data):
        # Delete the modal window first
        dpg.delete_item(user_data[1])
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _var_tag = user_data[0][0]
        _var_type = user_data[0][1]
        _var_name = _current_node_editor_instance.var_dict[_var_tag]['name'][0]

        try:
            _internal_module_dict = self._parent_instance.menu_construct_dict['_internal']
        except KeyError:
            self._parent_instance.logger.exception('Could not query _internal modules:')
            return -1
        # Get the module & import path to construct user data for callback_add_node
        try:
            _set_var_module_tuple = _internal_module_dict['Set ' + _var_type]
            _get_var_module_tuple = _internal_module_dict['Get ' + _var_type]
        except KeyError:
            self._parent_instance.logger.exception(
                f'Could not find internal module matched with this variable type: {_var_type}')
            return -1
        # Store a node list first to avoid interfering with the original node_instance_dict
        _node_list = []
        for node in _current_node_editor_instance.node_instance_dict.values():
            _node_list.append(node)
        for node in _node_list:
            if node.node_label == 'Set ' + _var_name:
                _node_pos = dpg.get_item_pos(node.id)
                # Delete the node
                delete_selected_node(self._parent_instance, node_id=node.id)
                _current_node_editor_instance.callback_add_node(sender, app_data,
                                                                user_data=(_set_var_module_tuple[0],
                                                                           _set_var_module_tuple[1],
                                                                           (_var_tag,
                                                                            'Set ' + _var_name)),
                                                                pos=_node_pos)
            elif node.node_label == 'Get ' + _var_name:
                _node_pos = dpg.get_item_pos(node.id)
                # Delete the node
                delete_selected_node(self._parent_instance, node_id=node.id)
                _current_node_editor_instance.callback_add_node(sender, app_data,
                                                                user_data=(_get_var_module_tuple[0],
                                                                           _get_var_module_tuple[1],
                                                                           (_var_tag,
                                                                            'Get ' + _var_name)),
                                                                pos=_node_pos)

        # Finally reflect new type changes to the databases
        self.var_type_update(_var_tag, _var_type)
