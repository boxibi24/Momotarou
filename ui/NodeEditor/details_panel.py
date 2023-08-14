import dearpygui.dearpygui as dpg
from typing import Tuple
from copy import deepcopy
from core.utils import dpg_set_value, add_user_input_box, log_on_return_message, remove_node_type_from_node_label
from core.enum_types import NodeTypeFlag


class DetailPanel:

    def __init__(self,
                 width=400,
                 height=800,
                 pos=None,
                 table_cell=None,
                 parent_instance=None):
        self._parent_instance = parent_instance
        self._width = width
        self._height = height
        self._table_cell = table_cell
        self._tag = '__details_panel'
        if pos is None:
            self._pos = [dpg.get_viewport_width() - 425, 30]
        else:
            self._pos = pos
        if self._table_cell is None:
            with dpg.child_window(
                label='Details',
                border=False,
                autosize_x=True,
                tag=self._tag
            ) as self._window_id:
                pass
        else:
            with dpg.child_window(
                label='Details',
                border=False,
                autosize_x=True,
                tag=self._tag,
                parent=self._table_cell
            ) as self._window_id:
                pass

    def refresh_ui_with_selected_node_info(self):
        self._reinitialize_self_ui()
        self._update_selected_node_info_to_details_panel()

    def _update_selected_node_info_to_details_panel(self):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        selected_nodes = dpg.get_selected_nodes(_current_node_editor_instance.id)
        if selected_nodes:
            selected_node_tag = dpg.get_item_alias(selected_nodes[0])
            node = _current_node_editor_instance.node_instance_dict.get(selected_node_tag)
            with dpg.collapsing_header(label='__internal_data', parent=self._window_id, default_open=True):
                dpg.add_text(default_value=f'Name: {node.node_label}')
                dpg.add_text(default_value=f'Tag: {node.node_tag}')

    def _reinitialize_self_ui(self):
        """
        Store existing configs and then refresh it
        :return:
        """
        self._width = dpg.get_item_width(self._window_id)
        self._height = dpg.get_item_height(self._window_id)
        self._pos = dpg.get_item_pos(self._window_id)
        self._table_cell = dpg.get_item_parent(self._tag)
        dpg.delete_item(self._window_id)
        self.__init__(width=self._width, height=self._height, pos=self._pos,
                      table_cell=self._table_cell, parent_instance=self._parent_instance)

    def callback_show_var_detail(self, sender, app_data, user_data):
        self._reinitialize_self_ui()
        var_tag = user_data
        self._update_var_info_to_details_panel(var_tag)

    def _update_var_info_to_details_panel(self, var_tag: str):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        var_info = _current_node_editor_instance.var_dict[var_tag]
        var_name = var_info['name'][0]
        var_type = var_info['type'][0]
        default_var_value = var_info['default_value'][0]
        var_is_exposed_value = var_info['is_exposed'][0]
        with dpg.collapsing_header(label='Variable Attributes', parent=self._window_id, default_open=True):
            with dpg.group(horizontal=True):
                dpg.add_text('Name: ')
                dpg.add_input_text(default_value=var_name,
                                   callback=self.callback_var_name_update, on_enter=True,
                                   user_data=var_tag)
            if var_type in ['String', 'Int', 'Float', 'MultilineString', 'Password', 'Bool']:
                with dpg.group(horizontal=True):
                    add_user_input_box(var_type, callback=self.callback_default_var_value_update,
                                       default_value=default_var_value,
                                       user_data=var_tag,
                                       text='Default value: ',
                                       add_separator=False)
                with dpg.group(horizontal=True):
                        dpg.add_text('Get value from user input: ')
                        dpg.add_checkbox(callback=self.callback_var_is_exposed_update,
                                         default_value=var_is_exposed_value,
                                         user_data=var_tag,
                                         )

        # Display var detail
        with dpg.collapsing_header(label='_internal_data', parent=self._window_id,
                                   default_open=True):
            dpg.add_text(default_value=f'Name: {var_name}')
            dpg.add_text(default_value=f'Tag: {var_tag}')
            dpg.add_text(default_value=f'Type: {var_type}')
            dpg.add_text(default_value=f'Default Value: {default_var_value}')
            dpg.add_text(default_value=f'Is exposed for user input?: {var_is_exposed_value}')

    def callback_default_var_value_update(self, sender, app_data, user_data):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _var_tag = user_data
        _current_node_editor_instance.var_dict[_var_tag]['default_value'][0] = app_data
        _var_name = _current_node_editor_instance.var_dict[_var_tag]['name'][0]
        # Refresh self
        self.callback_show_var_detail('', '', user_data=_var_tag)
        _current_node_editor_instance.logger.info(f'{_var_name} new default value updated: {app_data}')

    def callback_var_is_exposed_update(self, sender, app_data, user_data):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _var_tag = user_data
        _current_node_editor_instance.var_dict[_var_tag]['is_exposed'][0] = app_data
        if not app_data:  # Remove dpg id if turn off is_exposed
            _current_node_editor_instance.var_dict[_var_tag].pop('user_input_box_id')
        self._refresh_splitter_exposed_vars()
        # Refresh self
        self.callback_show_var_detail('', '', user_data=_var_tag)

    def _refresh_splitter_exposed_vars(self):
        _current_var_dict = self._parent_instance.current_node_editor_instance.var_dict
        _splitter_panel = self._parent_instance.current_node_editor_instance.splitter_panel
        _splitter_panel.exposed_var_dict = deepcopy(_current_var_dict)

    def callback_var_name_update(self, sender, appdata, user_data):
        """
        Callback function upon changing variable's name
        """
        action = 'Update var name'
        return_message = self._update_var_name(new_var_name=appdata, var_tag=user_data, input_box_id=sender)
        log_on_return_message(self._parent_instance.logger, action, return_message)

    def _update_var_name(self, var_tag: str, new_var_name: str, input_box_id: int) -> Tuple[int, object]:
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        old_var_name = _current_node_editor_instance.var_dict[var_tag]['name'][0]
        # Check if new name existed, then skip and set text input back to its previous value
        if self._is_var_name_existed(new_var_name):
            dpg_set_value(input_box_id, old_var_name)
            return 3, f'Could not change variable name, {new_var_name} existed!'
        self._update_new_var_name_to_all_var_nodes(new_var_name, old_var_name)
        self._update_new_var_name_to_current_node_editor_data(var_tag, new_var_name, old_var_name)
        self._refresh_splitter_vars()
        self.callback_show_var_detail('', '', user_data=var_tag)
        return 1, ''

    def _is_var_name_existed(self, var_name: str):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        for var_info in _current_node_editor_instance.splitter_var_dict.values():
            if var_info['name'][0] == var_name:
                return True
        return False

    def _update_new_var_name_to_all_var_nodes(self, new_var_name: str, old_var_name: str):
        """
        Update new name to every Set/Get nodes in current node graph

        :param new_var_name: New var name to update
        :param old_var_name: Old var name to search for nodes
        :return:
        """
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        for node_instance in _current_node_editor_instance.node_instance_dict.values():
            if node_instance.node_type & NodeTypeFlag.Variable and \
                old_var_name == remove_node_type_from_node_label(node_instance.node_label):
                _new_node_label = node_instance.node_label.split(' ')[0] + ' ' + new_var_name
                node_instance.node_label = _new_node_label
                dpg.configure_item(node_instance.id, label=node_instance.node_label)

    def _update_new_var_name_to_current_node_editor_data(self, var_tag: str, new_var_name: str, old_var_name: str):
        self._update_new_var_name_to_current_node_editor_vars_dict(var_tag, new_var_name)
        self._update_new_var_name_to_current_node_editor_node_dict(new_var_name, old_var_name)

    def _update_new_var_name_to_current_node_editor_vars_dict(self, var_tag: str, new_var_name: str):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _current_node_editor_instance.var_dict[var_tag]['name'][0] = new_var_name

    def _update_new_var_name_to_current_node_editor_node_dict(self, new_var_name: str, old_var_name: str):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        node_info_list = _current_node_editor_instance.node_dict['nodes']
        for node_info in node_info_list:
            if node_info['type'] & NodeTypeFlag.Variable and\
                old_var_name == remove_node_type_from_node_label(node_info['label']):
                node_info['label'] = node_info['label'].split(' ')[0] + ' ' + new_var_name

    def _refresh_splitter_vars(self):
        self._refresh_splitter_vars_dict()
        self._refresh_splitter_exposed_vars()

    def _refresh_splitter_vars_dict(self):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        self._parent_instance.splitter_panel.var_dict = _current_node_editor_instance.splitter_var_dict

    def callback_show_event_detail(self, sender, app_data, user_data):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _event_tag = user_data
        _event_detail = _current_node_editor_instance.event_dict[_event_tag]
        _event_name = _event_detail['name'][0]
        _event_type = _event_detail['type'][0]
        self._reinitialize_self_ui()

        with dpg.collapsing_header(label='Event Attributes', parent=self._window_id, default_open=True):
            with dpg.group(horizontal=True):
                dpg.add_text('Name: ')
                dpg.add_input_text(default_value=_event_name,
                                   callback=self.callback_event_name_update, on_enter=True,
                                   user_data=_event_tag)

        # Display var detail
        with dpg.collapsing_header(label='_internal_data', parent=self._window_id,
                                   default_open=True):
            dpg.add_text(default_value=f'Name: {_event_name}')
            dpg.add_text(default_value=f'Tag: {_event_tag}')
            dpg.add_text(default_value=f'Type: {_event_type}')

        _current_node_editor_instance.logger.debug('**** Details Panel refreshed to show event detail ****')

    def callback_event_name_update(self, sender, appdata, user_data):
        """
        callback function upon changing event's name
        """
        action = 'Rename event'
        return_message = self._update_event_name(event_tag=user_data, new_event_name=appdata, input_box_id=sender)
        log_on_return_message(self._parent_instance.logger, action, return_message)

    def _update_event_name(self, event_tag: str, new_event_name: str, input_box_id: int) -> Tuple[int, object]:
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        old_event_name = _current_node_editor_instance.event_dict[event_tag]['name'][0]

        if self._is_event_name_existed(new_event_name):
            dpg_set_value(input_box_id, old_event_name)
            return 3, f'Could not change event name, {new_event_name} existed!'
        self._update_new_event_name_to_event_node(new_event_name, old_event_name)
        self._update_new_event_name_to_current_node_editor(event_tag, new_event_name, old_event_name)
        self.callback_show_event_detail('', '', user_data=event_tag)
        self._refresh_splitter_events()
        return 1, ''

    def _is_event_name_existed(self, event_name: str):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        for event_info in _current_node_editor_instance.splitter_var_dict.values():
            if event_info['name'][0] == event_name:
                return True
        return False

    def _update_new_event_name_to_event_node(self, new_event_name: str, old_event_name: str):
        """
        Update new name to every Set/Get nodes in current node graph

        :param new_event_name: New event name to update
        :param old_event_name: Old event name to search for nodes
        :return:
        """
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        for node_instance in _current_node_editor_instance.node_instance_dict.values():
            if node_instance.node_type == NodeTypeFlag.Event and\
                old_event_name == remove_node_type_from_node_label(node_instance.node_label):
                _new_node_label = node_instance.node_label.split(' ')[0] + ' ' + new_event_name
                node_instance.node_label = _new_node_label
                dpg.configure_item(node_instance.id, label=node_instance.node_label)
                break

    def _update_new_event_name_to_current_node_editor(self, event_tag: str, new_event_name: str, old_event_name: str):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _current_node_editor_instance.event_dict[event_tag]['name'][0] = new_event_name
        node_info_list = _current_node_editor_instance.node_dict['nodes']
        for node_info in node_info_list:
            if node_info['type'] == NodeTypeFlag.Event and\
                old_event_name == remove_node_type_from_node_label(node_info['label']):
                node_info['label'] = node_info['label'].split(' ')[0] + ' ' + new_event_name
                break

    def _refresh_splitter_events(self):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        self._parent_instance.splitter_panel.event_dict = _current_node_editor_instance.event_dict
