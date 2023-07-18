from typing import Any

import dearpygui.dearpygui as dpg
from collections import OrderedDict
from copy import deepcopy
from ui.NodeEditor.classes.pin import InputPinType
from ui.NodeEditor.utils import generate_uuid, add_user_input_box


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

    @property
    def splitter_id(self) -> int:
        return self._splitter_id

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
            with dpg.child_window(autosize_x=True, height=300):
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Move event down", callback=None, arrow=True, direction=dpg.mvDir_Up)
                    dpg.add_button(label="Button", callback=None, arrow=True, direction=dpg.mvDir_Down)
                    dpg.add_button(label="Delete")
                dpg.add_separator()
                with dpg.child_window(border=False):
                    # Exposed var list
                    self._exposed_var_collapsing_header = dpg.add_collapsing_header(label='Exposed Variables',
                                                                                    default_open=True)
                    # Event graph list
                    self._event_graph_collapsing_header = dpg.add_collapsing_header(label='Event Graph',
                                                                                    default_open=True)
            with dpg.child_window(autosize_x=True):
                with dpg.table(header_row=False, no_pad_outerX=True, no_pad_innerX=True):
                    dpg.add_table_column(init_width_or_weight=400)
                    dpg.add_table_column(init_width_or_weight=100)
                    with dpg.table_row():
                        self._default_var_header = dpg.add_collapsing_header(label='Variables', default_open=True)
                        dpg.add_button(label='Add', indent=25, callback=self.add_var,
                                       user_data='var')

            self._parent_instance.logger.debug('**** Initialized Splitter ****')

    def refresh_event_graph_window(self):
        """
        Refresh the Event Graph collapsing header on Splitter
        """
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        # First clear out existing items in splitter:
        for value in self._old_event_dict.values():
            splitter_id = value.get('splitter_id', None)
            if splitter_id is None:
                continue
            dpg.delete_item(splitter_id)
        # Then add back the events item to the splitter
        for key, value in self._event_dict.items():
            splitter_selectable_item = dpg.add_selectable(label=value['name'],
                                                          parent=self._event_graph_collapsing_header)
            self._event_dict[key].update({'splitter_id': splitter_selectable_item})

        _current_node_editor_instance.logger.debug('**** Refreshed event graph window ****')

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
            _is_var_exposed = value['is_exposed']
            if _is_var_exposed[0]:
                with dpg.table(label='test123', parent=self._exposed_var_collapsing_header,
                               header_row=False, no_pad_outerX=True) as splitter_selectable_item:
                    dpg.add_table_column(no_reorder=True, no_resize=True, init_width_or_weight=100)
                    dpg.add_table_column(no_reorder=True, no_resize=True, init_width_or_weight=400)
                    with dpg.table_row():
                        dpg.add_selectable(label=value['name'][0],
                                          # parent=self._exposed_var_collapsing_header,
                                          callback=self._parent_instance.detail_panel.callback_show_var_detail,
                                          user_data=_var_tag)
                        _user_input_box = add_user_input_box(var_type=value['type'][0], width=300)
                        _current_node_editor_instance.register_var_user_input_box(_var_tag, _user_input_box)
                self._exposed_var_dict[_var_tag].update({'splitter_id': splitter_selectable_item})

        _current_node_editor_instance.logger.debug('**** Refreshed exposed var window ****')

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
            self.add_var(sender='', app_data='', user_data=value['name'][0], refresh=True, var_tag=key)

        _current_node_editor_instance.logger.debug('**** Refreshed variable window ****')

    def add_var(self, sender, app_data, user_data, refresh: bool, var_tag=''):
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
        if not children_list:
            if refresh is None:
                default_name += '1'
        else:
            if refresh is None:
                i = 1
                while not not_match_any_flag:
                    temp_name = user_data + str(i)
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
                dpg.add_selectable(label=default_name,
                                   callback=self._parent_instance.detail_panel.callback_show_var_detail,
                                   user_data=new_var_tag)
                with dpg.drag_payload(parent=dpg.last_item(),
                                      drag_data=new_var_tag,
                                      payload_type='var'):
                    dpg.add_text(default_name)
                var_type_list = [member.name for member in InputPinType]
                if self._combo_dict.get(new_var_tag, None) is None:
                    default_type = var_type_list[0]
                else:
                    default_type = self._combo_dict[new_var_tag][1][0]
                dpg.add_combo(var_type_list, width=95, popup_align_left=True,
                              callback=self.combo_update_callback, user_data=new_var_tag,
                              default_value=default_type)
        # Prep data
        new_var_info = {
            new_var_tag: {
                'name': [default_name],
                'type': [default_type],
                'splitter_id': var_splitter_id
            }}
        # Combo dict is initialized first so all of its list get referenced later
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
            self._parent_instance.current_node_editor_instance.add_var(new_var_info)

        self._old_var_dict = self._var_dict

        _current_node_editor_instance.logger.debug('***** Added new var on Splitter ****')
        _current_node_editor_instance.logger.debug(f'Splitter Combo dict: {self._combo_dict}')

    def combo_update_callback(self, sender, app_data, user_data):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _var_tag = user_data
        new_var_type = app_data
        self._combo_dict[_var_tag][1][0] = new_var_type
        # Need to refresh the child Node Graph's var value & default value also
        self._parent_instance.current_node_editor_instance.var_dict[_var_tag]['value'][0] = None
        default_var_value = None
        # set default var value based on value type
        if new_var_type in ['String', 'MultilineString', 'Password']:
            default_var_value = ''
        elif new_var_type == 'Int':
            default_var_value = 0
        elif new_var_type == 'Float':
            default_var_value = 0.0
        elif new_var_type == 'Bool':
            default_var_value = False
        _current_node_editor_instance.var_dict[_var_tag]['default_value'][0] = default_var_value

        _current_node_editor_instance.logger.info(f'Updated new type for var of tag {_var_tag}: {new_var_type}')
