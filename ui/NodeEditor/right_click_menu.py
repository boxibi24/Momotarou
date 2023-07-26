import dearpygui.dearpygui as dpg
from collections import OrderedDict
from multiprocessing import Queue
from ui.NodeEditor.utils import create_queueHandler_logger


class RightClickMenu:

    @property
    def show(self) -> bool:
        return self._show

    @show.setter
    def show(self, value: bool):
        dpg.configure_item(self._window_id, show=value, no_bring_to_front_on_focus=False)
        self._show = value

    @property
    def get_id(self) -> int:
        return self._window_id

    def __init__(self,
                 parent_inst,
                 menu_construct_dict=None,
                 setting_dict=None,
                 use_debug_print=False,
                 logging_queue=Queue()):
        # ----- FLAGS --------
        self._use_debug_print = use_debug_print
        self._show = False
        # ----- PARENT ITEMS -----
        self._parent_id = parent_inst.node_editor_tag
        self._parent_inst = parent_inst
        # ------ SETTINGS ------
        if setting_dict is None:
            self._setting_dict = {}
        else:
            self._setting_dict = setting_dict
        # dict with more info to help construct menu every time called
        if menu_construct_dict is None:
            self._menu_construct_dict = OrderedDict([])
        else:
            self._menu_construct_dict = menu_construct_dict

        # ------ LOGGER ----------
        self.logger = create_queueHandler_logger(__name__,
                                                 logging_queue, self._use_debug_print)
        self.logger.debug('***** Right click menu prepared! *****')

        self.pop_up_window()

    def pop_up_window(self):
        with dpg.window(
            popup=True,
            autosize=True,
            no_move=True,
            no_open_over_existing_popup=True,
            no_saved_settings=True,
            no_bring_to_front_on_focus=True,
            max_size=[200, 200],
        ) as self._window_id:
            with dpg.table(freeze_rows=1, header_row=False, scrollY=True):
                dpg.add_table_column()
                with dpg.table_row():
                    dpg.add_input_text(callback=lambda s, a: dpg.set_value('__right_click_menu_filter', a),
                                       hint='Type to search', width=150)
                with dpg.table_row():
                    with dpg.filter_set(tag='__right_click_menu_filter'):
                        for node_category, node_module_dict in self._menu_construct_dict.items():
                            # Skip loading _internal category
                            if node_category == '_internal':
                                continue
                            dpg.add_separator()
                            dpg.add_text(default_value=node_category, filter_key=node_category, color=(221, 84, 255, 255))
                            dpg.add_separator()
                            for node_name, node_module in node_module_dict.items():
                                node = node_module.python_module.Node(
                                    parent=self._parent_id,
                                    setting_dict=self._setting_dict,
                                    pos=[0, 0],
                                    import_path=node_module.import_path
                                )
                                # add menu item for the node
                                dpg.add_selectable(
                                    tag='Menu_' + node.node_label,
                                    label=node.node_label,
                                    callback=self.child_editor_add_node,
                                    user_data=node_module,
                                    filter_key=node.node_label,
                                    indent=20
                                )
                                with dpg.tooltip('Menu_' + node.node_label):
                                    dpg.add_text(f'{node.__doc__}')
                                # DEBUG
                                self.logger.debug("******* ADD NODE CONTEXT *******")
                                self.logger.debug(f'     node._ver           :   {node.ver}')
                                self.logger.debug(f'     node.node_tag       :   {node.node_tag}')
                                self.logger.debug(f'     node.node_label     :   {node.node_label}')

    def child_editor_add_node(self, sender, app_data, user_data):
        node_module = user_data
        self._parent_inst.current_node_editor_instance.add_node_from_module(node_module)
