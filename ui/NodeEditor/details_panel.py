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
