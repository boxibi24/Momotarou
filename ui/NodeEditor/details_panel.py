import dearpygui.dearpygui as dpg
from copy import deepcopy
from ui.NodeEditor.utils import add_user_input_box, dpg_set_value
from ui.NodeEditor.classes.node import NodeTypeFlag


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

    def refresh_ui(self):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        # Store existing configs first, then refresh it
        self._width = dpg.get_item_width(self._window_id)
        self._height = dpg.get_item_height(self._window_id)
        self._pos = dpg.get_item_pos(self._window_id)
        self._table_cell = dpg.get_item_parent(self._tag)
        dpg.delete_item(self._window_id)
        self.__init__(width=self._width, height=self._height, pos=self._pos,
                      table_cell=self._table_cell, parent_instance=self._parent_instance)

        # Update info on the window
        selected_nodes = dpg.get_selected_nodes(_current_node_editor_instance.id)
        if selected_nodes:
            selected_node_tag = dpg.get_item_alias(selected_nodes[0])
            node = _current_node_editor_instance.node_instance_dict.get(selected_node_tag)
            # Header

            with dpg.collapsing_header(label='__internal_data', parent=self._window_id, default_open=True):
                # dpg.add_separator(parent=self._window_id)
                dpg.add_text(default_value=f'Name: {node.node_label}')
                dpg.add_text(default_value=f'Tag: {node.node_tag}')
                dpg.add_text(default_value=f'Internal data: {node.internal_data}')
                dpg.add_text(default_value=f'Succeeding links: {node.succeeding_data_link_list}')
                dpg.add_separator()
                # Do not show event nodes flags since it does not change
                if not node.node_type & NodeTypeFlag.Event:
                    dpg.add_text(default_value=f'Is Dirty: {node.is_dirty}')
                    dpg.add_text(default_value=f'Is Executed: {node.is_executed}')

        _current_node_editor_instance.logger.debug('**** Details Panel refreshed to show node detail ****')

    def callback_show_var_detail(self, sender, app_data, user_data):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        var_tag = user_data
        var_detail = _current_node_editor_instance.var_dict.get(var_tag, None)
        if var_detail is None:
            # KeyError could not find key {user_data} in current_node_graph 's var_dict
            return 8
        var_name_reference = var_detail['name']
        var_name = var_detail['name'][0]
        var_type = var_detail['type'][0]
        var_value = var_detail['value'][0]
        default_var_value_reference = var_detail['default_value']
        default_var_value = var_detail['default_value'][0]
        var_is_exposed_value = var_detail['is_exposed'][0]
        var_is_exposed_value_reference = var_detail['is_exposed']
        # Clear current detail ui
        # Store existing configs first, then refresh it
        self._width = dpg.get_item_width(self._window_id)
        self._height = dpg.get_item_height(self._window_id)
        self._pos = dpg.get_item_pos(self._window_id)
        self._table_cell = dpg.get_item_parent(self._tag)
        dpg.delete_item(self._window_id)
        self.__init__(width=self._width, height=self._height, pos=self._pos,
                      table_cell=self._table_cell, parent_instance=self._parent_instance)

        with dpg.collapsing_header(label='Variable Attributes', parent=self._window_id, default_open=True):
            with dpg.group(horizontal=True):
                dpg.add_text('Name: ')
                dpg.add_input_text(default_value=var_name,
                                   callback=self.callback_var_name_update, on_enter=True,
                                   user_data=(var_tag, var_name_reference))
                # dpg.add_separator()
            with dpg.group(horizontal=True):
                add_user_input_box(var_type, callback=self.callback_default_var_value_update,
                                   default_value=default_var_value,
                                   user_data=(var_tag, var_name_reference, default_var_value_reference),
                                   text='Default value: ',
                                   add_separator=False)
            with dpg.group(horizontal=True):
                if var_type in ['String', 'Int', 'Float', 'MultilineString', 'Password', 'Bool']:
                    dpg.add_text('Get value from user input: ')
                    dpg.add_checkbox(callback=self.callback_var_is_exposed_update,
                                     default_value=var_is_exposed_value,
                                     user_data=(var_tag, var_is_exposed_value_reference),
                                     )

        # Display var detail
        with dpg.collapsing_header(label='_internal_data', parent=self._window_id,
                                   default_open=True):
            dpg.add_text(default_value=f'Name: {var_name}')
            dpg.add_text(default_value=f'Tag: {user_data}')
            dpg.add_text(default_value=f'Type: {var_type}')
            dpg.add_text(default_value=f'Value: {var_value}')
            dpg.add_text(default_value=f'Default Value: {default_var_value}')
            dpg.add_text(default_value=f'Is exposed for user input?: {var_is_exposed_value}')

        _current_node_editor_instance.logger.debug('**** Details Panel refreshed to show var detail ****')

    def callback_default_var_value_update(self, sender, app_data, user_data):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _var_tag = user_data[0]
        user_data[2][0] = app_data
        # Set every Get nodes of this variable to dirty
        for node_get in self._parent_instance.current_node_editor_instance.node_instance_dict.values():
            if node_get.node_label == 'Get ' + user_data[1][0]:
                node_get.is_dirty = True

        # Refresh self
        self.callback_show_var_detail('', '', user_data=_var_tag)

        _current_node_editor_instance.logger.info(f'{user_data[1][0]} new default value updated: {app_data}')

    def callback_var_is_exposed_update(self, sender, app_data, user_data):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        user_data[1][0] = app_data
        _var_tag = user_data[0]

        if not app_data:  # Turning off is_exposed flag will need some janitor
            _current_node_editor_instance.var_dict[_var_tag].pop('user_input_box_id')

        # Get current Node Graph var dict
        _current_var_dict = self._parent_instance.current_node_editor_instance.var_dict
        # Set current var dict to splitter to trigger its refresh on exposed var collapsing header
        _splitter_panel = self._parent_instance.current_node_editor_instance.splitter_panel
        _splitter_panel.exposed_var_dict = deepcopy(_current_var_dict)

        # Refresh self
        self.callback_show_var_detail('', '', user_data=_var_tag)
        # Logging
        if app_data:
            _current_node_editor_instance.logger.info(
                f'This variable of tag {_var_tag} will now get its initial value from user input!')
        else:
            _current_node_editor_instance.logger.info(
                f'This variable of tag {_var_tag} will now get its initial value from default value!')

    def callback_var_name_update(self, sender, appdata, user_data):
        """
        callback function upon changing variable's name
        """
        _new_var_name = appdata
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _var_tag = user_data[0]
        _old_var_name = user_data[1][0]
        # Check if new name existed, then skip and set text input back to its previous value
        for var_info in _current_node_editor_instance.splitter_var_dict.values():
            if var_info['name'][0] == _new_var_name:
                _current_node_editor_instance.logger.error(f'Could not change variable name, {_new_var_name} existed!')
                dpg_set_value(sender, _old_var_name)
                return 1
        # Update new name to every Set/Get nodes in current node graph
        for node_get in _current_node_editor_instance.node_instance_dict.values():
            if node_get.node_label == 'Get ' + _old_var_name:
                node_get.node_label = 'Get ' + _new_var_name
                dpg.configure_item(node_get.id, label=node_get.node_label)
            if node_get.node_label == 'Set ' + _old_var_name:
                node_get.node_label = 'Set ' + _new_var_name
                dpg.configure_item(node_get.id, label=node_get.node_label)

        # Update new var name to all databases that store it
        # 1. master node_dict:
        user_data[1][0] = _new_var_name
        node_info_list = _current_node_editor_instance.node_dict.get('nodes', None)
        if node_info_list is not None:
            for node_info in node_info_list:
                if 'Set ' + _old_var_name == node_info['label'] or 'Get ' + _old_var_name == node_info['label']:
                    node_info['label'] = node_info['label'].split(' ')[0] + ' ' + _new_var_name
        # 2. Node Graph's splitter_var_dict & Node Graph's var_dict & Splitter's combo_dict all reference the same name
        for var_info in _current_node_editor_instance.splitter_var_dict.values():
            if var_info['name'][0] == _old_var_name:
                var_info['name'][0] = _new_var_name
                break
        # Refresh all UI elements to reflect the new name change
        # First refresh self
        self.callback_show_var_detail('', '', user_data=_var_tag)
        # Refresh splitter items
        _splitter_panel = self._parent_instance.current_node_editor_instance.splitter_panel
        _splitter_panel.var_dict = _current_node_editor_instance.splitter_var_dict
        # Exposed var dict needs deep-copying since it adds a splitter_id entry to the input dict
        _splitter_panel.exposed_var_dict = deepcopy(_current_node_editor_instance.var_dict)

        _current_node_editor_instance.logger.info(f'Changed var name : {_old_var_name} to {_new_var_name}')
        return 0

    def callback_show_event_detail(self, sender, app_data, user_data):
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _event_tag = user_data
        _event_detail = _current_node_editor_instance.event_dict.get(_event_tag, None)
        if _event_detail is None:
            # KeyError could not find key {user_data} in current_node_graph 's var_dict
            return 8
        _event_name_reference = _event_detail['name']
        _event_name = _event_detail['name'][0]
        _event_type = _event_detail['type'][0]
        # Clear current detail ui
        # Store existing configs first, then refresh it
        self._width = dpg.get_item_width(self._window_id)
        self._height = dpg.get_item_height(self._window_id)
        self._pos = dpg.get_item_pos(self._window_id)
        self._table_cell = dpg.get_item_parent(self._tag)
        dpg.delete_item(self._window_id)
        self.__init__(width=self._width, height=self._height, pos=self._pos,
                      table_cell=self._table_cell, parent_instance=self._parent_instance)

        with dpg.collapsing_header(label='Event Attributes', parent=self._window_id, default_open=True):
            with dpg.group(horizontal=True):
                dpg.add_text('Name: ')
                dpg.add_input_text(default_value=_event_name,
                                   callback=self.callback_event_name_update, on_enter=True,
                                   user_data=(_event_tag, _event_name_reference))

        # Display var detail
        with dpg.collapsing_header(label='_internal_data', parent=self._window_id,
                                   default_open=True):
            dpg.add_text(default_value=f'Name: {_event_name}')
            dpg.add_text(default_value=f'Tag: {user_data}')
            dpg.add_text(default_value=f'Type: {_event_type}')

        _current_node_editor_instance.logger.debug('**** Details Panel refreshed to show event detail ****')

    def callback_event_name_update(self, sender, appdata, user_data):
        """
        callback function upon changing event's name
        """
        _new_event_name = appdata
        _current_node_editor_instance = self._parent_instance.current_node_editor_instance
        _event_tag = user_data[0]
        _old_event_name = user_data[1][0]
        # Check if new name existed, then skip and set text input back to its previous value
        for event_info in _current_node_editor_instance.event_dict.values():
            if event_info['name'][0] == _new_event_name:
                _current_node_editor_instance.logger.error(f'Could not change event name, {_new_event_name} existed!')
                dpg_set_value(sender, _old_event_name)
                return 1
        # Update new name to event node in current node graph
        for node_get in _current_node_editor_instance.node_instance_dict.values():
            if node_get.node_label == 'Event ' + _old_event_name:
                node_get.node_label = 'Event ' + _new_event_name
                dpg.configure_item(node_get.id, label=node_get.node_label)
                # Only 1 instance of event node existed, therefore breaks
                break

        # Update new event name to all databases that store it
        # 1. master node_dict:
        user_data[1][0] = _new_event_name
        node_info_list = _current_node_editor_instance.node_dict.get('nodes', None)
        if node_info_list is not None:
            for node_info in node_info_list:
                if 'Event ' + _old_event_name == node_info['label']:
                    node_info['label'] = 'Event ' + _new_event_name
                    # Only 1 instance of event node existed, therefore breaks
                    break
        else:
            _current_node_editor_instance.logger.criticle(f'Could not query master node_dict to update new event name')
        # 2. No other databases need updated since they all share the name reference in Node Graph's event dict
        # Refresh all UI elements to reflect the new name change
        # First refresh self
        self.callback_show_event_detail('', '', user_data=_event_tag)
        # Refresh splitter items
        _splitter_panel = self._parent_instance.current_node_editor_instance.splitter_panel
        _splitter_panel.event_dict = _current_node_editor_instance.event_dict

        _current_node_editor_instance.logger.info(f'Changed event name : {_old_event_name} to {_new_event_name}')
        return 0
