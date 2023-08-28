import dearpygui.dearpygui as dpg
from typing import Tuple
from collections import OrderedDict
from copy import deepcopy
from core.enum_types import InputPinType, NodeTypeFlag
from core.utils import generate_uuid, add_user_input_box, get_var_default_value_on_type, \
    remove_node_type_from_node_label
from ui.NodeEditor.item_right_click_menus import variable_right_click_menu, event_right_click_menu, \
    callback_run_event, callback_ask_event_delete, callback_ask_variable_delete
from ui.NodeEditor.input_handler import delete_selected_node
from ui.NodeEditor.node_utils import create_list_from_dict_values, auto_increment_matched_name_in_dpg_container, \
    get_index_in_dict_from_matched_tag_and_key, apply_dict_order_on_source_and_destination_index


class Splitter:
    splitter_label = 'Splitter'
    var_default_name = 'Var'
    event_default_name = 'Button'

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
        self._variable_collapsing_header = None
        self._event_graph_collapsing_header = None
        self._exposed_var_collapsing_header = None
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
            label=self.splitter_label,
            border=False,
            autosize_x=True

        ) as self._splitter_id:
            self.fresh_init_collapsing_headers()
        self._parent_instance.logger.debug('**** Initialized Splitter ****')

    def fresh_init_collapsing_headers(self):
        self._init_exposed_var_collapsing_header()
        self._init_event_graph_collapsing_header()
        self._init_variable_collapsing_header()

    def _init_exposed_var_collapsing_header(self, is_insert=False):
        self._exposed_var_collapsing_header = \
            dpg.add_collapsing_header(parent=self._splitter_id,
                                      label='Exposed Variables',
                                      default_open=True,
                                      before=self._event_graph_collapsing_header if is_insert else 0)

    def _init_event_graph_collapsing_header(self, is_insert=False):
        self._event_graph_collapsing_header = \
            dpg.add_collapsing_header(parent=self._splitter_id,
                                      label='Event Graph',
                                      default_open=True,
                                      before=self._variable_collapsing_header if is_insert else 0)
        with dpg.item_handler_registry():
            dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Right,
                                         callback=self.event_graph_header_right_click_menu,
                                         user_data=('', self.event_default_name))
        dpg.bind_item_handler_registry(self._event_graph_collapsing_header, dpg.last_container())
        self._create_add_event_button()

    def _init_variable_collapsing_header(self):
        self._variable_collapsing_header = dpg.add_collapsing_header(parent=self._splitter_id,
                                                                     label='Variables', tag='__var_header',
                                                                     default_open=True)
        with dpg.item_handler_registry():
            dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Right,
                                         callback=self.variable_header_right_click_menu,
                                         user_data=self.var_default_name)
        dpg.bind_item_handler_registry(self._variable_collapsing_header, dpg.last_container())
        self._create_add_var_button()

    def event_graph_header_right_click_menu(self, sender, app_data, user_data, instant_add=False):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        new_event_tag = '__event' + generate_uuid()
        override_pos = user_data[0]

        non_matching_name = auto_increment_matched_name_in_dpg_container(user_data[1],
                                                                         self._event_graph_collapsing_header)
        if instant_add:
            added_node = self._parent_instance.current_editor_add_event_node(non_matching_name, override_pos)
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
                                                    user_data=('', non_matching_name)
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

        self.clear_old_splitter_dpg_item(self._old_event_dict, self._event_graph_collapsing_header)
        self._add_event_splitter_items()

    def _add_event_splitter_items(self):
        for key, value in self._event_dict.items():
            _event_tag = key
            _event_name = value['name'][0]
            self._add_event_splitter_item(_event_tag, _event_name)

    def _add_event_splitter_item(self, event_tag: str, event_name: str):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _detail_panel_inst = self._parent_instance.detail_panel
        callback_user_data = (event_tag, self._parent_instance)
        with dpg.table(parent=self._event_graph_collapsing_header,
                       header_row=False, no_pad_outerX=True,
                       before=self._event_add_button_id,
                       label=event_name) as splitter_item:
            dpg.add_table_column(no_reorder=True, no_resize=True)
            dpg.add_table_column(no_reorder=True, no_resize=True, width_fixed=True)
            dpg.add_table_column(no_reorder=True, no_resize=True, width_fixed=True)
            with dpg.table_row():
                event_selectable = dpg.add_selectable(label=event_name,
                                                      callback=_detail_panel_inst.callback_show_event_detail,
                                                      user_data=event_tag,
                                                      payload_type='__event',
                                                      drop_callback=self.drop_callback_reorder_event,
                                                      indent=20)
                dpg.add_button(arrow=True, direction=dpg.mvMouseButton_Right, callback=callback_run_event,
                               user_data=callback_user_data)
                dpg.add_button(label='X', width=20, callback=callback_ask_event_delete, user_data=callback_user_data)
        with dpg.drag_payload(parent=event_selectable,
                              drag_data=event_tag,
                              payload_type='__event'):
            dpg.add_text('Event ' + event_name)
        with dpg.item_handler_registry() as item_handler_id:
            dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Right,
                                         callback=event_right_click_menu,
                                         user_data=callback_user_data)
        dpg.bind_item_handler_registry(event_selectable, dpg.last_container())
        _current_node_editor_instance.item_registry_dict.update({event_tag: item_handler_id})
        self._event_dict[event_tag].update({'splitter_id': splitter_item,
                                            'selectable_id': event_selectable})

    def drop_callback_reorder_event(self, sender, app_data):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _source_event_tag = app_data
        _destination_event_tag = self._get_event_tag_from_dpg_id(sender)
        source_event_index = get_index_in_dict_from_matched_tag_and_key(_source_event_tag, self._event_dict)
        destination_event_index = get_index_in_dict_from_matched_tag_and_key(_destination_event_tag, self._event_dict)
        apply_dict_order_on_source_and_destination_index(source_event_index, destination_event_index,
                                                         _current_node_editor_instance.event_dict)
        # Trigger a splitter refresh now that new event_dict order has been set
        self.event_dict = _current_node_editor_instance.event_dict

    def _get_event_tag_from_dpg_id(self, dpg_id: int) -> str:
        for event_tag, value in self._event_dict.items():
            if value['selectable_id'] == dpg_id:
                found_event_tag = event_tag
                return found_event_tag
        raise KeyError(f'Could not find event tag whose id is : {dpg_id}')

    def refresh_exposed_var_window(self):
        """
        Refresh the Exposed Variables collapsing header on Splitter
        """
        self.clear_old_splitter_dpg_item(self._old_exposed_var_dict, self._exposed_var_collapsing_header)
        self._add_exposed_var_splitter_items()

    def _add_exposed_var_splitter_items(self):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        for key, value in self._exposed_var_dict.items():
            _var_tag = key
            _var_name = value['name'][0]
            _is_var_exposed = value['is_exposed'][0]
            if _is_var_exposed:
                with dpg.table(parent=self._exposed_var_collapsing_header,
                               header_row=False, no_pad_outerX=True) as splitter_selectable_item:
                    dpg.add_table_column(no_reorder=True, no_resize=True)
                    dpg.add_table_column(no_reorder=True, no_resize=True, width_fixed=True)
                    with dpg.table_row():
                        _selectable_id = dpg.add_selectable(label=_var_name,
                                                            callback=self._parent_instance.detail_panel.callback_show_var_detail,
                                                            user_data=_var_tag,
                                                            payload_type='__exposed_var',
                                                            drop_callback=self.drop_callback_reorder_var,
                                                            indent=20)
                        with dpg.drag_payload(parent=dpg.last_item(),
                                              drag_data=_var_tag,
                                              payload_type='__exposed_var'):
                            dpg.add_text(_var_name)
                        _user_input_box_tag = add_user_input_box(var_type=value['type'][0], width=250)
                        _current_node_editor_instance.register_var_user_input_box_tag(_var_tag, _user_input_box_tag)
                self._exposed_var_dict[_var_tag].update({'splitter_id': splitter_selectable_item,
                                                         'selectable_id': _selectable_id})

    def drop_callback_reorder_var(self, sender, app_data):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _source_var_tag = app_data
        _destination_var_tag = self._get_var_tag_from_dpg_id(sender)
        _source_var_index = get_index_in_dict_from_matched_tag_and_key(_source_var_tag, self._exposed_var_dict)
        _destination_var_index = get_index_in_dict_from_matched_tag_and_key(_destination_var_tag, self.exposed_var_dict)
        apply_dict_order_on_source_and_destination_index(_source_var_index, _destination_var_index,
                                                         _current_node_editor_instance.var_dict)
        self.exposed_var_dict = deepcopy(_current_node_editor_instance.var_dict)

    def _get_var_tag_from_dpg_id(self, dpg_id: int) -> str:
        for var_tag, value in self._exposed_var_dict.items():
            if value['is_exposed'][0]:
                if value['selectable_id'] == dpg_id:
                    found_var_tag = var_tag
                    return found_var_tag
        raise KeyError(f'Could not find var tag whose selectable id is : {dpg_id}')

    def refresh_variable_window(self):
        """
        Refresh the Variables collapsing header on Splitter
        """
        self.clear_old_splitter_dpg_item(self._old_var_dict, self._variable_collapsing_header)
        for key, value in self._var_dict.items():
            self.add_var(sender='', app_data='', user_data=value['name'][0],
                         refresh=True, var_tag=key)

    def _create_add_var_button(self):
        self._var_add_button_id = dpg.add_button(parent=self._variable_collapsing_header,
                                                 label='+',
                                                 callback=self.add_var,
                                                 user_data=self.var_default_name,
                                                 width=-1,
                                                 indent=20)

    def _create_add_event_button(self):
        self._event_add_button_id = dpg.add_button(parent=self._event_graph_collapsing_header,
                                                   label='+',
                                                   callback=self.callback_add_event_button,
                                                   width=-1,
                                                   indent=20)

    def callback_add_event_button(self):
        self.event_graph_header_right_click_menu('', '', user_data=((0, 0), self.event_default_name), instant_add=True)

    @staticmethod
    def clear_old_splitter_dpg_item(old_dict: dict, parent_id: int):
        for value in old_dict.values():
            splitter_id = value.get('splitter_id', None)
            if splitter_id is None:
                continue
            dpg.delete_item(splitter_id)

    def add_var(self, sender, app_data, user_data, refresh=None, var_tag='',
                default_value=None, var_type=None, default_is_exposed_flag=False, regex=None):
        """
        Add new variable
        """
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        non_matching_name = auto_increment_matched_name_in_dpg_container(user_data, self._variable_collapsing_header)
        if not refresh:
            new_var_tag = generate_uuid()
        else:
            new_var_tag = var_tag

        var_splitter_id, var_combo_id, default_type = self._add_splitter_var_dpg_item(non_matching_name, new_var_tag)
        # Override var_type when importing tool
        if var_type is not None:
            default_type = var_type
            dpg.configure_item(var_combo_id, default_value=var_type)

        new_var_info = self._init_var_data_on_add_new_var(new_var_tag, non_matching_name, default_type, var_splitter_id)
        self._update_splitter_combo_dict_data_on_add_new_var(new_var_info)
        self._update_splitter_var_dict_data_on_add_new_var(new_var_info)

        if not refresh:
            self._parent_instance.current_node_editor_instance.add_var(new_var_info,
                                                                       default_value, default_is_exposed_flag, regex)
        # Update old var dict cache
        self._old_var_dict = deepcopy(self._var_dict)

        _current_node_editor_instance.logger.debug('***** Added new var on Splitter ****')

    def _add_splitter_var_dpg_item(self, var_name: str, var_tag: str) -> Tuple[int, int, str]:
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        callback_user_data = (var_tag, self._parent_instance)
        with dpg.table(label=var_name, header_row=False, no_pad_outerX=True,
                       parent=self._variable_collapsing_header,
                       before=self._var_add_button_id) as var_splitter_id:
            dpg.add_table_column(no_reorder=True, no_resize=True)
            dpg.add_table_column(no_reorder=True, no_resize=True, width_fixed=True)
            dpg.add_table_column(no_reorder=True, no_resize=True, width_fixed=True)
            with dpg.table_row():
                # Variable selectable
                _selectable_id = dpg.add_selectable(label=var_name,
                                                    callback=self._parent_instance.detail_panel.callback_show_var_detail,
                                                    user_data=var_tag,
                                                    indent=20)
                with dpg.drag_payload(parent=_selectable_id,
                                      drag_data=var_tag,
                                      payload_type='__var'):
                    dpg.add_text(var_name)
                # Combo list
                var_type_list = [member.name for member in InputPinType if member.name not in ['Exec', 'WildCard']]
                if self._combo_dict.get(var_tag, None) is None:
                    default_type = var_type_list[0]
                else:
                    default_type = self._combo_dict[var_tag][1][0]
                var_combo_id = dpg.add_combo(var_type_list, width=100, popup_align_left=True,
                                             callback=self.combo_update_callback, user_data=var_tag,
                                             default_value=default_type)
                # Delete button
                dpg.add_button(label='X', width=20, callback=callback_ask_variable_delete, user_data=callback_user_data)

            # Add right-click handler to selectable
            with dpg.item_handler_registry() as item_handler_id:
                dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Right,
                                             callback=variable_right_click_menu,
                                             user_data=callback_user_data)
            dpg.bind_item_handler_registry(_selectable_id, dpg.last_container())
            _current_node_editor_instance.item_registry_dict.update({var_tag: item_handler_id})

        return var_splitter_id, var_combo_id, default_type

    @staticmethod
    def _init_var_data_on_add_new_var(var_tag: str, var_name: str, var_type: str, var_splitter_id: int) -> dict:
        new_var_info = {
            var_tag: {
                'name': [var_name],
                'type': [var_type],
                'splitter_id': var_splitter_id
            }}
        return new_var_info

    def _update_splitter_combo_dict_data_on_add_new_var(self, var_info: dict):
        var_tag = list(var_info.keys())[0]
        var_name = var_info[var_tag]['name']
        var_type = var_info[var_tag]['type']
        if self._combo_dict.get(var_tag, None) is None:
            self._combo_dict.update({
                var_tag:
                    [var_name, var_type]
            })
        else:
            self._combo_dict[var_tag][0][0] = var_name[0]
            self._combo_dict[var_tag][1][0] = var_type[0]

    def _update_splitter_var_dict_data_on_add_new_var(self, var_info: dict):
        var_tag = list(var_info.keys())[0]
        var_name = var_info[var_tag]['name']
        var_type = var_info[var_tag]['type']
        var_splitter_id = var_info[var_tag]['splitter_id']
        if self._var_dict.get(var_tag, None) is None:
            self._var_dict.update(var_info)
        else:
            self._var_dict[var_tag]['name'][0] = var_name[0]
            self._var_dict[var_tag]['type'][0] = var_type[0]
            self._var_dict[var_tag]['splitter_id'] = var_splitter_id

    def combo_update_callback(self, sender, app_data, user_data):
        var_tag = user_data
        new_var_type = app_data
        self._var_type_update_handler(var_tag, new_var_type)

    def _var_type_update_handler(self, var_tag: str, new_var_type: str):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        var_name = _current_node_editor_instance.var_dict[var_tag]['name'][0]

        if self._is_found_var_node_matches_name(var_name):
            self._init_reconfirm_change_var_type_popup(var_tag, new_var_type)
        else:
            self.var_type_update(var_tag, new_var_type)

    def _is_found_var_node_matches_name(self, check_var_name: str) -> bool:
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        for node in _current_node_editor_instance.node_instance_dict.values():
            if node.node_type & NodeTypeFlag.Variable and \
                check_var_name == remove_node_type_from_node_label(node.node_label):
                return True
        return False

    def _init_reconfirm_change_var_type_popup(self, var_tag: str, new_var_type: str):
        _mid_widget_pos = [int(dpg.get_viewport_width() / 2.5), int(dpg.get_viewport_height() / 2.5)]
        with dpg.window(modal=True, label='Change variable type',
                        pos=_mid_widget_pos) as _modal_window:
            dpg.add_text("Changing variable type will delink and replace all node instances of this var !\n"
                         "This operation cannot be undone!")
            with dpg.group(horizontal=True):
                dpg.add_button(label="OK", width=75, callback=self.callback_replace_node_of_new_type,
                               user_data=((var_tag, new_var_type), _modal_window))
                dpg.add_button(label="Cancel", width=75, callback=lambda: dpg.delete_item(_modal_window))

    def callback_replace_node_of_new_type(self, sender, app_data, user_data):
        # Delete the modal window first
        dpg.delete_item(user_data[1])
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        var_tag = user_data[0][0]
        new_var_type = user_data[0][1]
        var_name = self._get_variable_name_from_tag(var_tag)
        node_list = create_list_from_dict_values(_current_node_editor_instance.node_instance_dict)
        for node in node_list:
            if node.node_type & NodeTypeFlag.Variable and var_name == remove_node_type_from_node_label(node.node_label):
                if node.node_type == NodeTypeFlag.SetVariable:
                    self._replace_set_var_node_with_new_type(node, new_var_type, var_tag)
                else:
                    self._replace_get_var_node_with_new_type(node, new_var_type, var_tag)
        # Finally reflect new type changes to the databases
        self.var_type_update(var_tag, new_var_type)

    def var_type_update(self, var_tag, new_type):
        _var_tag = var_tag
        _new_var_type = new_type
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _var_name = _current_node_editor_instance.var_dict[_var_tag]['name'][0]

        self._combo_dict[_var_tag][1][0] = _new_var_type
        # Need to refresh the child Node Graph's var value & default value also
        _current_node_editor_instance.var_dict[_var_tag]['value'][0] = None
        default_var_value = get_var_default_value_on_type(_new_var_type)
        _current_node_editor_instance.var_dict[_var_tag]['default_value'][0] = default_var_value
        # Refresh the exposed variable window
        self.exposed_var_dict = deepcopy(_current_node_editor_instance.var_dict)
        # Also emulate a details callback to refresh show var detail
        self._parent_instance.detail_panel.callback_show_var_detail('', '', user_data=_var_tag)

        _current_node_editor_instance.logger.info(f'Updated new type for var of name {_var_name}: {_new_var_type}')

    def _get_variable_name_from_tag(self, var_tag) -> str:
        return self._parent_instance.current_node_editor_instance.var_dict[var_tag]['name'][0]

    def _replace_get_var_node_with_new_type(self, node, new_var_type: str, var_tag: str):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _node_pos = dpg.get_item_pos(node.id)
        # Delete the node
        delete_selected_node(self._parent_instance, node_id=node.id)
        var_module = self._parent_instance.get_variable_module_from_var_type_and_action(new_var_type, True)
        _current_node_editor_instance.add_node_from_module(var_module, _node_pos, node.node_label, var_tag)

    def _replace_set_var_node_with_new_type(self, node, new_var_type: str, var_tag: str):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _node_pos = dpg.get_item_pos(node.id)
        # Delete the node
        delete_selected_node(self._parent_instance, node_id=node.id)
        var_module = self._parent_instance.get_variable_module_from_var_type_and_action(new_var_type, False)
        _current_node_editor_instance.add_node_from_module(var_module, _node_pos, node.node_label, var_tag)
