from ui.NodeEditor.utils import generate_uuid, create_queueHandler_logger
from multiprocessing import Queue
from ui.NodeEditor.input_handler import *
from ui.NodeEditor.right_click_menu import RightClickMenu
from ui.NodeEditor.splitter import Splitter
from ui.NodeEditor.details_panel import DetailPanel
from ui.NodeEditor._internal_node_editor import DPGNodeEditor
from tkinter import Tk, simpledialog
from collections import OrderedDict
import os
import platform
from glob import glob
from importlib import import_module
from copy import deepcopy


class NodeEditor:
    _ver = '0.0.1'
    node_editor_label = 'Node Editor'
    node_editor_tag = generate_uuid()

    @property
    def requested_exec_node_tag(self) -> str:
        return self._requested_exec_node_tag

    @requested_exec_node_tag.setter
    def requested_exec_node_tag(self, value: str):
        self._requested_exec_node_tag = value

    @property
    def node_editor_bb(self) -> list[tuple]:
        return self._node_editor_bb

    @node_editor_bb.setter
    def node_editor_bb(self, value: list[tuple]):
        self._node_editor_bb = value

    def __init__(
        self,
        setting_dict=None,
        node_dir='nodes',
        node_menu_dict=None,
        use_debug_print=False,
        logging_queue=Queue()
    ):
        # ------ FLAGS --------
        # self._refresh_trigger_flag = False
        # ------ SETTINGS ------
        self._var_drop_popup_id = -1
        self._use_debug_print = use_debug_print
        if setting_dict is None:
            self._setting_dict = {}
        else:
            self._setting_dict = setting_dict

        # ------ ATTRIBUTES -----
        self.current_node_editor_instance = None
        self._requested_exec_node_tag = None
        self._node_editor_dict = OrderedDict([])
        # dict to keep track of the imported modules
        self._imported_module_dict = {}
        # Tuple to store current node editor boundaries position
        self._node_editor_bb = [(), ()]

        # ------- LOGGING ______
        self.logging_queue = logging_queue
        self.logger = create_queueHandler_logger(__name__, logging_queue, self._use_debug_print)

        self.logger.info('***** Loading Master Node Editor *****')

        _menu_construct_dict = OrderedDict([])
        # Default menu if none is applied
        if node_menu_dict is None:
            self._node_menu_dict = OrderedDict({
                '_internal': '_internal',
                'Process Node': 'process_node',
                'Output Node': 'output_node',
                'Exec Node': 'exec_node',
                'Math Node': 'math_node',
                'Flow Control': 'flow_control_node',
                'Perforce Node': 'perforce_node'
            })
            self.menu_construct_dict = OrderedDict([])
            # Add right-click-menu items defined
            for tree_node_info in self._node_menu_dict.items():
                # Store paths of written nodes
                node_sources_path = os.path.join(
                    node_dir,
                    tree_node_info[1],
                    '*.py'
                )
                # Get path of included node_sources_path files
                node_sources = glob(node_sources_path)
                for node_source in node_sources:
                    # split up files names and import them
                    import_path = os.path.splitext(
                        os.path.normpath(node_source)
                    )[0]
                    if platform.system() == 'Windows':
                        import_path = import_path.replace('\\', '.')
                    else:
                        import_path = import_path.replace('/', '.')
                    import_path = import_path.split('.')
                    import_path = '.'.join(import_path[-3:])

                    # Exclude __init__ import
                    if import_path.endswith('__init__'):
                        continue

                    # import the module
                    module = import_module(import_path)
                    if module:
                        self._imported_module_dict.update({import_path: module})
                        node_category = tree_node_info[0]
                        if self.menu_construct_dict.get(node_category, None) is None:
                            node_module_item = OrderedDict([])
                            node_module_item.update({module.Node.node_label: (import_path, module)})
                            self.menu_construct_dict.update({node_category:
                                                                 node_module_item
                                                             })
                        else:
                            self.menu_construct_dict[node_category].update(
                                {module.Node.node_label: (import_path, module)})
                    else:
                        self.logger.critical(f"Could not import module {import_path}")

        # Main viewport
        with dpg.child_window(
            tag=self.node_editor_tag,
            label=self.node_editor_label,
            border=False
        ):
            with dpg.table(header_row=True, resizable=True, reorderable=False, borders_outerH=False,
                           borders_outerV=False, borders_innerV=False, borders_innerH=False):
                dpg.add_table_column(label='My Project', width_fixed=True, init_width_or_weight=300)
                dpg.add_table_column(label='Event Graph')
                dpg.add_table_column(label='Details', width_fixed=True,
                                     init_width_or_weight=300)
                with dpg.table_row():
                    self.splitter_panel = Splitter(parent_instance=self)
                    with dpg.tab_bar(reorderable=True, callback=self.callback_tab_bar_change) as self._tab_bar_id:
                        self.current_tab = dpg.add_tab(label='Default', parent=self._tab_bar_id,
                                                       closable=True, payload_type='__var',
                                                       drop_callback=self.var_drop_callback)
                        new_node_editor = DPGNodeEditor(parent_tab=self.current_tab,
                                                        splitter_panel=self.splitter_panel,
                                                        setting_dict=self._setting_dict,
                                                        imported_module_dict=self._imported_module_dict,
                                                        use_debug_print=self._use_debug_print,
                                                        logging_queue=logging_queue)
                        self._node_editor_dict.update({self.current_tab: new_node_editor})
                        self.current_node_editor_instance = new_node_editor
                        dpg.add_tab_button(label='+', callback=self._add_node_graph_tab, user_data=self._tab_bar_id,
                                           no_reorder=True, trailing=True)
                    self.detail_panel = DetailPanel(parent_instance=self)
            # Initialize right click menu
            self.right_click_menu = RightClickMenu(parent_inst=self,
                                                   imported_module_dict=self._imported_module_dict,
                                                   menu_construct_dict=self.menu_construct_dict,
                                                   setting_dict=self._setting_dict,
                                                   use_debug_print=self._use_debug_print,
                                                   logging_queue=self.logging_queue)

            # Add handler registry
            self._add_handler_registry()

    def _callback_show_right_click_menu(self):
        if not dpg.get_selected_nodes(self.current_node_editor_instance.id):
            self.right_click_menu.show = True

    def _add_handler_registry(self):
        """
        Add all input handler registry and their callback
        """
        add_keyboard_handler_registry(self)
        add_mouse_handler_registry(self)

        for handler in dpg.get_item_children("__node_editor_keyboard_handler", 1):
            dpg.set_item_callback(handler, event_handler)

        for handler in dpg.get_item_children("__node_editor_mouse_handler", 1):
            dpg.set_item_callback(handler, event_handler)

    def _add_node_graph_tab(self, sender, app_data, user_data):
        root = Tk()
        root.withdraw()
        new_tab_name = simpledialog.askstring(title='Rename tab', prompt='Name your new tab: ')
        root.destroy()
        new_tab = dpg.add_tab(label=new_tab_name, parent=user_data,
                              closable=True, payload_type='__var', drop_callback=self.var_drop_callback)
        new_node_editor = DPGNodeEditor(parent_tab=new_tab,
                                        splitter_panel=self.splitter_panel,
                                        setting_dict=self._setting_dict,
                                        imported_module_dict=self._imported_module_dict,
                                        use_debug_print=self._use_debug_print,
                                        logging_queue=self.logging_queue)
        self._node_editor_dict.update({new_tab: new_node_editor})

    def callback_tab_bar_change(self, sender, app_data):
        _old_node_editor_instance = self.current_node_editor_instance
        _old_tab_id = self.current_tab
        # Refresh the dict first in case user closes the tab
        self.refresh_node_editor_dict()
        try:
            self.current_node_editor_instance = self._node_editor_dict[app_data]
            self.current_tab = app_data
        except KeyError:
            self.logger.exception('Could not query current node editor instance:')
            return -1
        # Also do a refresh of detail_panel
        self.detail_panel.refresh_ui()
        # Also do a refresh of splitter, assigning new dict will trigger its UI refresh methods
        self.splitter_panel.event_dict = self.current_node_editor_instance.event_dict
        self.splitter_panel.var_dict = self.current_node_editor_instance.splitter_var_dict
        self.splitter_panel.exposed_var_dict = deepcopy(self.current_node_editor_instance.var_dict)

        # If tab not deleted, delete the orphaned registry from old node graph
        # since all selectable-headers will be refreshed
        if self._node_editor_dict.get(_old_tab_id, None) is not None:
            for registry_id in _old_node_editor_instance.item_registry_dict.values():
                dpg.delete_item(registry_id)
            _old_node_editor_instance.item_registry_dict.clear()

    def refresh_node_editor_dict(self):
        tuple_list = list(self._node_editor_dict.items())
        for tab_id, node_graph_inst in tuple_list:
            if not dpg.is_item_visible(tab_id):
                self._node_editor_dict.pop(tab_id)
                deleted_tab_name = dpg.get_item_label(tab_id)
                # Delete all registry that stored in the node graph
                for registry_id in node_graph_inst.item_registry_dict.values():
                    dpg.delete_item(registry_id)
                # Delete the node graph in dpg
                dpg.delete_item(node_graph_inst.id)
                # Delete the node graph inst
                del node_graph_inst
                # Finally delete the tab
                dpg.delete_item(tab_id)
                self.logger.info(f'****Deleted tab {deleted_tab_name}****')

    def var_drop_callback(self, sender, app_data):
        """
        Callback function upon variable drop on child Node Editor
        """
        # Try deleting old popup window to avoid duplication
        try:
            is_window_exist = dpg.is_item_enabled(self._var_drop_popup_id)
        except SystemError:
            is_window_exist = False
        if is_window_exist:
            dpg.delete_item(self._var_drop_popup_id)

        # Init popup window
        with dpg.window(
            popup=True,
            autosize=True,
            no_move=True,
            no_open_over_existing_popup=True,
            no_saved_settings=True,
            max_size=[200, 200],
            min_size=[10, 10]
        ) as self._var_drop_popup_id:
            # Get variable selectable
            _var_name = self.current_node_editor_instance.var_dict[app_data]['name'][0]
            _var_tag = app_data
            dpg.add_selectable(label='Get ' + _var_name,
                               tag='__get_var',
                               callback=self.callback_current_editor_add_node,
                               user_data=(_var_tag, _var_name))
            dpg.add_separator()
            # Set variable selectable
            dpg.add_selectable(label='Set ' + _var_name,
                               tag='__set_var',
                               callback=self.callback_current_editor_add_node,
                               user_data=(_var_tag, _var_name))

    def callback_current_editor_add_node(self, sender, app_data, user_data, sender_tag=None):
        """
        Callback function to add variable node on the child Node Editor
        """
        if sender_tag is None:
            _sender_tag = dpg.get_item_alias(sender)
        else:
            _sender_tag = sender_tag
        _item_tag = user_data[0]
        _item_name = user_data[1]
        added_node = None
        if _sender_tag == '__get_var':
            # Get the imported internal modules
            try:
                _internal_module_dict = self.menu_construct_dict['_internal']
            except KeyError:
                self.logger.exception('Could not query _internal modules:')
                return -1
            # Get the module & import path to construct user data for callback_add_node
            _var_type = self.current_node_editor_instance.var_dict[_item_tag]['type'][0]
            try:
                _var_module_tuple = _internal_module_dict['Get ' + _var_type]
            except KeyError:
                self.logger.exception(f'Could not find internal module matched with this variable type: {_var_type}')
                return -1
            # Run child Node Editor's callback_add_node
            added_node = self.current_node_editor_instance.callback_add_node(sender, app_data,
                                                                             user_data=(_var_module_tuple[0],
                                                                                        _var_module_tuple[1],
                                                                                        (_item_tag,
                                                                                         'Get ' + _item_name)))

        elif _sender_tag == '__set_var':
            # Get the imported internal modules
            try:
                _internal_module_dict = self.menu_construct_dict['_internal']
            except KeyError:
                self.logger.exception('Could not query _internal modules:')
                return -1
            # Get the module & import path to construct user data for callback_add_node
            _var_type = self.current_node_editor_instance.var_dict[_item_tag]['type'][0]
            try:
                _var_module_tuple = _internal_module_dict['Set ' + _var_type]
            except KeyError:
                self.logger.exception(f'Could not find internal module matched with this variable type: {_var_type}')
                return -1
            # Run child Node Editor's callback_add_node
            added_node = self.current_node_editor_instance.callback_add_node(sender, app_data,
                                                                             user_data=(_var_module_tuple[0],
                                                                                        _var_module_tuple[1],
                                                                                        (_item_tag,
                                                                                         'Set ' + _item_name)))
        elif '__event' in _sender_tag:
            # Get the imported internal modules
            try:
                _internal_module_dict = self.menu_construct_dict['_internal']
            except KeyError:
                self.logger.exception('Could not query _internal modules:')
                return -1
            try:
                _var_module_tuple = _internal_module_dict['Event']
            except KeyError:
                self.logger.exception(f'Could not find internal module: Event')
                return -1
            # Run child Node Editor's callback_add_node
            added_node = self.current_node_editor_instance.callback_add_node(sender, app_data,
                                                                             user_data=(_var_module_tuple[0],
                                                                                        _var_module_tuple[1],
                                                                                        (_item_tag,
                                                                                         'Event ' + _item_name)))

        return added_node
