import dearpygui.dearpygui as dpg


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
        # Store existing configs first, then refresh it
        self._width = dpg.get_item_width(self._window_id)
        self._height = dpg.get_item_height(self._window_id)
        self._pos = dpg.get_item_pos(self._window_id)
        self._table_cell = dpg.get_item_parent(self._tag)
        dpg.delete_item(self._window_id)
        self.__init__(width=self._width, height=self._height, pos=self._pos,
                      table_cell=self._table_cell, parent_instance=self._parent_instance)

        # Update info on the window
        selected_nodes = dpg.get_selected_nodes(self._parent_instance.current_node_editor_instance.id)
        if selected_nodes:
            selected_node_tag = dpg.get_item_alias(selected_nodes[0])
            node = self._parent_instance.current_node_editor_instance.node_instance_dict.get(selected_node_tag)
            # Header

            with dpg.collapsing_header(label='__internal_data', parent=self._window_id, default_open=True):
                # dpg.add_separator(parent=self._window_id)
                dpg.add_text(default_value=f'Name: {node.node_label}')
                dpg.add_text(default_value=f'Tag: {node.node_tag}')
                dpg.add_text(default_value=f'Internal data: {node.internal_data}')
                dpg.add_text(default_value=f'Succeeding links: {node.succeeding_data_link_list}')
                dpg.add_separator()
                dpg.add_text(default_value=f'Is Dirty: {node.is_dirty}')
                dpg.add_text(default_value=f'Is Exposed: {node.is_exposed}')

        self._parent_instance.logger.debug('**** Refreshed Details Panel ****')

    def callback_show_var_detail(self, sender, app_data, user_data):
        print(f'sender: {sender}')
        print(f'app_data : {app_data}')
        print(f'user_data : {user_data}')
        var_detail = self._parent_instance.current_node_editor_instance.var_dict.get(user_data, None)
        if var_detail is None:
            # KeyError could not find key {user_data} in current_node_graph 's var_dict
            return 8
        print(f'var_detail {var_detail}')
        var_name_reference = var_detail['name']
        var_name = var_detail['name'][0]
        var_type = var_detail['type'][0]
        var_value = var_detail['value'][0]
        default_var_value_reference = var_detail['default_value']
        default_var_value = var_detail['default_value'][0]
        # Clear current detail ui
        # Store existing configs first, then refresh it
        self._width = dpg.get_item_width(self._window_id)
        self._height = dpg.get_item_height(self._window_id)
        self._pos = dpg.get_item_pos(self._window_id)
        self._table_cell = dpg.get_item_parent(self._tag)
        dpg.delete_item(self._window_id)
        self.__init__(width=self._width, height=self._height, pos=self._pos,
                      table_cell=self._table_cell, parent_instance=self._parent_instance)

        # Display var detail
        with dpg.collapsing_header(label='Var Details', parent=self._window_id, default_open=True):
            dpg.add_text(default_value=f'Var Name: {var_name}')
            dpg.add_text(default_value=f'Var Tag: {user_data}')
            dpg.add_text(default_value=f'Var Type: {var_type}')
            dpg.add_text(default_value=f'Var Value: {var_value}')
            dpg.add_text(default_value=f'Var Default Value: {default_var_value}')

        with dpg.collapsing_header(label='Variable Attributes', parent=self._window_id, default_open=True):
            with dpg.tree_node(label='Default Value:', default_open=True):
                if var_type == 'String':
                    dpg.add_input_text(on_enter=True, default_value=default_var_value,
                                       callback=self.callback_default_var_value_update,
                                       user_data=(var_name_reference, default_var_value_reference),
                                       hint='one line text')
                elif var_type == 'Int':
                    dpg.add_input_int(on_enter=True, default_value=default_var_value,
                                      callback=self.callback_default_var_value_update,
                                      user_data=(var_name_reference, default_var_value_reference))
                elif var_type == 'Float':
                    dpg.add_input_float(on_enter=True, default_value=default_var_value,
                                        callback=self.callback_default_var_value_update,
                                        user_data=(var_name_reference, default_var_value_reference))
                elif var_type == 'MultilineString':
                    dpg.add_input_text(on_enter=True, multiline=True,
                                       default_value=default_var_value,
                                       callback=self.callback_default_var_value_update,
                                       user_data=(var_name_reference, default_var_value_reference))
                elif var_type == 'Password':
                    dpg.add_input_text(on_enter=True, password=True,
                                       default_value=default_var_value,
                                       callback=self.callback_default_var_value_update,
                                       user_data=(var_name_reference, default_var_value_reference),
                                       hint='password')
                elif var_type == 'Bool':
                    dpg.add_checkbox(callback=self.callback_default_var_value_update,
                                     default_value=default_var_value,
                                     user_data=(var_name_reference, default_var_value_reference))

    def callback_default_var_value_update(self, sender, app_data, user_data):
        print(f'sender: {sender}')
        print(f'app_data : {app_data}')
        print(f'user_data : {user_data}')
        user_data[1][0] = app_data
        print(self._parent_instance.current_node_editor_instance.var_dict)
        # Set every Get nodes of this variable to dirty
        for node_get in self._parent_instance.current_node_editor_instance.node_instance_dict.values():
            if node_get.node_label == 'Get ' + user_data[0][0]:
                node_get.is_dirty = True
