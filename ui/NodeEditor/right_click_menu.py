import dearpygui.dearpygui as dpg
from collections import OrderedDict
from multiprocessing import Queue
from ui.NodeEditor.utils import create_queueHandler_logger


class RightClickMenu:

    @property
    def imported_module_dict(self) -> OrderedDict:
        return self._imported_module_dict

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
                 imported_module_dict=None,
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
        # dict of imported module to expose to Node Editor
        if imported_module_dict is None:
            self._imported_module_dict = OrderedDict([])
        else:
            self._imported_module_dict = imported_module_dict
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
            # TODO: find better way to filter selectable
            dpg.add_input_text(label="Filter (inc, -exc)",
                               callback=lambda s, a: dpg.set_value('__right_click_menu_filter', a))
            with dpg.filter_set(tag='__right_click_menu_filter'):
                for node_category_info in self._menu_construct_dict.items():
                    # Skip loading _internal category
                    if node_category_info[0] == '_internal':
                        continue
                    with dpg.collapsing_header(label=node_category_info[0], filter_key=node_category_info[0]):
                        for node_module_item in node_category_info[1].items():
                            import_path, module = node_module_item[1]
                            node = module.Node(
                                parent=self._parent_id,
                                setting_dict=self._setting_dict,
                                pos=[0, 0]
                            )
                            # add menu item for the node
                            dpg.add_selectable(
                                tag='Menu_' + node.node_label,
                                label=node.node_label,
                                callback=self.child_editor_add_node,
                                user_data=(import_path, module)
                            )
                            with dpg.tooltip('Menu_' + node.node_label):
                                dpg.add_text(f'{node.__doc__}')
                            # DEBUG
                            self.logger.debug("******* ADD NODE CONTEXT *******")
                            self.logger.debug(f'     node._ver           :   {node.ver}')
                            self.logger.debug(f'     node.node_tag       :   {node.node_tag}')
                            self.logger.debug(f'     node.node_label     :   {node.node_label}')

    def child_editor_add_node(self, sender, app_data, user_data):
        self._parent_inst.current_node_editor_instance.callback_add_node(sender, app_data, user_data)
