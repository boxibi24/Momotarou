from typing import Any

import dearpygui.dearpygui as dpg
from collections import OrderedDict
from copy import deepcopy
from ui.NodeEditor.classes.pin import InputPinType
from ui.NodeEditor.utils import dpg_get_value, dpg_set_value


class Splitter:
    splitter_label = 'Splitter'

    @property
    def event_dict(self) -> OrderedDict:
        return self._event_dict

    @event_dict.setter
    def event_dict(self, value: OrderedDict):
        self._event_dict = value
        self.refresh_ui()
        self._old_event_dict = deepcopy(self._event_dict)

    @property
    def splitter_id(self) -> int:
        return self._splitter_id

    def __init__(self,
                 width=400,
                 height=800,
                 pos=None,
                 event_dict=None
                 ):
        self._old_event_dict = OrderedDict([])
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
                    with dpg.collapsing_header(label='EventGraph', default_open=True) as self._default_event_graph:
                        # dpg.add_selectable(label='event1')
                        # dpg.add_selectable(label='event2')
                        pass
            with dpg.child_window(autosize_x=True):
                with dpg.table(header_row=False, no_pad_outerX=True, no_pad_innerX=True):
                    dpg.add_table_column(init_width_or_weight=400)
                    dpg.add_table_column(init_width_or_weight=100)
                    with dpg.table_row():
                        var_header = dpg.add_collapsing_header(label='Variables', default_open=True)
                        dpg.add_button(label='Add', indent=25, callback=self.add_var, user_data=[var_header, 'var'])

    def refresh_ui(self):
        # First clear out existing items in splitter:
        for value in self._old_event_dict.values():
            splitter_id = value.get('splitter_id', None)
            if splitter_id is None:
                continue
            dpg.delete_item(splitter_id)
        for key, value in self._event_dict.items():
            splitter_selectable_item = dpg.add_selectable(label=value['name'], parent=self._default_event_graph)
            self._event_dict[key].update({'splitter_id': splitter_selectable_item})

    def add_var(self, sender, app_data, user_data):
        """
        Add new variable
        """
        parent = user_data[0]
        # Try to generate a default name that does not match with any existing ones
        children_list: list = dpg.get_item_children(parent)[1]
        not_match_any_flag = False
        default_name = user_data[1]
        if not children_list:
            default_name += '1'
        else:
            i = 1
            while not not_match_any_flag:
                default_name = user_data[1] + str(i)
                for child_item in children_list:
                    if default_name == dpg.get_item_label(child_item):
                        break
                    elif child_item == children_list[-1] and default_name != dpg.get_item_label(child_item):
                        not_match_any_flag = True
                i += 1

        with dpg.table(label=default_name, header_row=False, no_pad_outerX=True, parent=parent):
            dpg.add_table_column(init_width_or_weight=400)
            dpg.add_table_column(init_width_or_weight=300)
            with dpg.table_row():
                dpg.add_selectable(label=default_name)
                with dpg.drag_payload(parent=dpg.last_item(),
                                      drag_data=(self._combo_dict, default_name),
                                      payload_type='var'):
                    dpg.add_text(default_name)
                var_type_list = [member.name for member in InputPinType]
                dpg.add_combo(var_type_list, width=95, popup_align_left=True,
                              callback=self.combo_update_callback, user_data=default_name,
                              default_value=var_type_list[0])
                self._combo_dict.update({default_name: (default_name, var_type_list[0])})

    def combo_update_callback(self, sender, app_data, user_data):
        self._combo_dict.update({user_data: (user_data, app_data)})
