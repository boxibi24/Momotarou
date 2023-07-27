import dearpygui.dearpygui as dpg
from multiprocessing import Queue
from ui.NodeEditor.utils import generate_uuid, create_queueHandler_logger
from ui.NodeEditor.input_handler import add_keyboard_handler_registry, add_mouse_handler_registry, event_handler
from ui.NodeEditor.right_click_menu import RightClickMenu
from ui.NodeEditor.splitter import Splitter
from ui.NodeEditor.details_panel import DetailPanel
from ui.NodeEditor._internal_node_editor import DPGNodeEditor
from ui.NodeEditor.item_right_click_menus import tab_right_click_menu
from ui.NodeEditor.classes.node import NodeModule
from ui.NodeEditor.node_utils import construct_var_node_label, construct_module_name_from_var_action_and_type
from collections import OrderedDict
import os
import platform
from glob import glob
from importlib import import_module
from copy import deepcopy
from pprint import pprint

INTERNAL_NODE_CATEGORY = '_internal'


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
        self._node_editor_tab_dict = OrderedDict([])
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
                        node_category = tree_node_info[1]
                        if self.menu_construct_dict.get(node_category, None) is None:
                            node_module_item = OrderedDict([])
                            node_module_item.update(
                                {import_path: NodeModule(module, import_path, module.Node.node_type)})
                            if 'event' in import_path:
                                self.EVENT_IMPORT_PATH = import_path
                            self.menu_construct_dict.update({node_category: node_module_item})
                        else:
                            self.menu_construct_dict[node_category].update(
                                {import_path: NodeModule(module, import_path, module.Node.node_type)})
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
                        _tab_name = 'Default'
                        _tab_id = dpg.add_tab(label=_tab_name, parent=self._tab_bar_id,
                                              closable=True, payload_type='__var',
                                              drop_callback=self.var_drop_callback)
                        self.current_tab_id = _tab_id
                        # Right click context menu for tab
                        with dpg.item_handler_registry() as item_handler_id:
                            dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Right,
                                                         callback=tab_right_click_menu,
                                                         user_data=([_tab_name], self._node_editor_tab_dict))
                        dpg.bind_item_handler_registry(_tab_id, dpg.last_container())
                        new_node_editor = DPGNodeEditor(parent_tab=_tab_id,
                                                        parent_instance=self,
                                                        setting_dict=self._setting_dict,
                                                        use_debug_print=self._use_debug_print,
                                                        logging_queue=logging_queue)
                        new_node_editor.item_registry_dict.update({'tab_registry': item_handler_id})
                        self._node_editor_tab_dict.update({_tab_name:
                                                               {'node_editor_instance': new_node_editor,
                                                                'id': _tab_id
                                                                }})
                        self.current_node_editor_instance = new_node_editor
                        dpg.add_tab_button(label='+', callback=self._add_node_graph_tab_ask_name,
                                           user_data=self._tab_bar_id,
                                           no_reorder=True, trailing=True)
                    self.detail_panel = DetailPanel(parent_instance=self)
            # Initialize right click menu
            self.right_click_menu = RightClickMenu(parent_inst=self,
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

    def _add_node_graph_tab_ask_name(self, sender, app_data, user_data, is_retry=False):
        parent = user_data
        _mid_widget_pos = [int(dpg.get_viewport_width() / 2.5), int(dpg.get_viewport_height() / 2.5)]
        with dpg.window(label='New tab',
                        pos=_mid_widget_pos, min_size=[10, 10], no_resize=True) as _modal_window:
            with dpg.group(horizontal=True):
                dpg.add_text("Name your new tab: ")
                dpg.add_input_text(width=200, callback=self._callback_on_name_new_tab,
                                   on_enter=True, user_data=(_modal_window, parent),
                                   hint='Input and press "Enter" to apply')
            if is_retry:
                dpg.add_text('Name existed, please retry another name!', color=(204, 51, 0, 255))

    def _callback_on_name_new_tab(self, sender, app_data, user_data):
        # delete the modal window
        dpg.delete_item(user_data[0])
        new_tab_name = app_data
        parent = user_data[1]
        if self._node_editor_tab_dict.get(new_tab_name, None) is not None:  # Tab name existed
            return self._add_node_graph_tab_ask_name(sender, app_data, user_data=parent, is_retry=True)
        new_tab_id = dpg.add_tab(label=new_tab_name, parent=parent,
                                 closable=True, payload_type='__var', drop_callback=self.var_drop_callback)
        # Right click context menu for tab
        with dpg.item_handler_registry() as item_handler_id:
            dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Right,
                                         callback=tab_right_click_menu,
                                         user_data=([new_tab_name], self._node_editor_tab_dict))
        dpg.bind_item_handler_registry(new_tab_id, dpg.last_container())
        new_node_editor = DPGNodeEditor(parent_tab=new_tab_id,
                                        parent_instance=self,
                                        setting_dict=self._setting_dict,
                                        use_debug_print=self._use_debug_print,
                                        logging_queue=self.logging_queue)
        new_node_editor.item_registry_dict.update({'tab_registry': item_handler_id})
        self._node_editor_tab_dict.update({new_tab_name:
                                               {'node_editor_instance': new_node_editor,
                                                'id': new_tab_id
                                                }})

    def callback_tab_bar_change(self, sender, app_data):
        _old_node_editor_instance = self.current_node_editor_instance
        _old_tab_name = dpg.get_item_label(self.current_tab_id)
        _selected_tab = dpg.get_item_label(app_data)
        # Refresh the dict first in case user closes the tab
        self.refresh_node_editor_dict()
        try:
            self.current_node_editor_instance = self._node_editor_tab_dict[_selected_tab]['node_editor_instance']
            self.current_tab_id = app_data
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
        if self._node_editor_tab_dict.get(_old_tab_name, None) is not None:
            for item, registry_id in _old_node_editor_instance.item_registry_dict.items():
                # skip tab registry
                if item == 'tab_registry':
                    continue
                dpg.delete_item(registry_id)
            # Clear every register except for tab registry id
            _tab_register_id = _old_node_editor_instance.item_registry_dict['tab_registry']
            _old_node_editor_instance.item_registry_dict.clear()
            _old_node_editor_instance.item_registry_dict.update({'tab_registry': _tab_register_id})

    def refresh_node_editor_dict(self):
        self._check_all_tabs_and_trigger_deletion_if_found_closed()
        self._reflect_current_order_to_tab_dict()

    def _check_all_tabs_and_trigger_deletion_if_found_closed(self):
        tuple_list = list(self._node_editor_tab_dict.items())
        for tab_name, tab_info in tuple_list:
            if not dpg.is_item_visible(tab_info['id']):
                self._delete_tab(tab_info, tab_name)

    def _delete_tab(self, tab_info, tab_name):
        node_editor_instance = tab_info['node_editor_instance']
        self._node_editor_tab_dict.pop(tab_name)
        # Delete all registry that stored in the node graph
        for registry_id in node_editor_instance.item_registry_dict.values():
            dpg.delete_item(registry_id)
        # Delete the node graph in dpg
        dpg.delete_item(node_editor_instance.id)
        # Delete the node graph inst
        del node_editor_instance
        # Finally delete the tab
        dpg.delete_item(tab_info['id'])
        self.logger.info(f'****Deleted tab {tab_name}****')

    def _reflect_current_order_to_tab_dict(self):
        self._get_tabs_order()
        pprint(self._node_editor_tab_dict)

    def _get_tabs_order(self):
        converter = {}
        for item in dpg.get_item_children(self._tab_bar_id, 1):
            # Skip add button
            if dpg.get_item_label(item) == '+':
                continue
            converter[tuple(dpg.get_item_rect_min(item))] = dpg.get_item_label(item)

        pos = [dpg.get_item_rect_min(item) for item in dpg.get_item_children(self._tab_bar_id, 1) if dpg.get_item_label(item) != '+']
        sortedPos = sorted(pos, key=lambda pos: pos[0])

        for item in sortedPos:
            print(converter[tuple(item)])

    def var_drop_callback(self, sender, app_data):
        """
        Callback function upon variable drop on child Node Editor
        """
        # Try deleting old popup window to avoid duplication
        self._delete_var_drop_popup()
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

    def _delete_var_drop_popup(self):
        try:
            is_window_exist = dpg.is_item_enabled(self._var_drop_popup_id)
        except SystemError:
            is_window_exist = False
        if is_window_exist:
            dpg.delete_item(self._var_drop_popup_id)

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
        if _sender_tag == '__get_var':
            self.current_editor_add_var_node(_item_tag, _item_name, True)
        elif _sender_tag == '__set_var':
            self.current_editor_add_var_node(_item_tag, _item_name, False)
        elif '__event' in _sender_tag:
            self.current_editor_add_event_node(_item_name)

    def current_editor_add_var_node(self, var_tag, var_name, is_get_var: bool):
        var_module = self._get_internal_var_module(var_tag, is_get_var)
        added_node = self.current_node_editor_instance.add_node_from_module(var_module,
                                                                            override_label=construct_var_node_label(
                                                                                var_name, is_get_var),
                                                                            var_tag=var_tag)
        return added_node

    def _get_internal_var_module(self, var_tag, is_get_var: bool):
        var_type = self._get_var_type_from_var_tag(var_tag)
        var_module = self.get_variable_module_from_var_type_and_action(var_type, is_get_var)
        return var_module

    def _get_var_type_from_var_tag(self, var_tag):
        return self.current_node_editor_instance.var_dict[var_tag]['type'][0]

    def get_variable_module_from_var_type_and_action(self, var_type: str, is_get_var: bool):
        if is_get_var:
            var_action = 'get'
        else:
            var_action = 'set'
        return self._get_var_imported_module_from_var_type_and_action(var_action, var_type)

    def _get_var_imported_module_from_var_type_and_action(self, var_action: str, var_type: str):
        check_string = construct_module_name_from_var_action_and_type(var_action, var_type)
        for import_path, module in self.menu_construct_dict[INTERNAL_NODE_CATEGORY].items():
            if check_string == import_path.split('.')[-1]:
                return module
        self.logger.error(f'Could not find python to {var_action} {var_type} variable')
        return None

    def current_editor_add_event_node(self, event_name, override_pos: tuple[float, float]):
        event_module = self._get_event_module()
        added_node = self.current_node_editor_instance.add_node_from_module(event_module, pos=override_pos,
                                                                            override_label='Event ' + event_name)
        return added_node

    def _get_event_module(self):
        _internal_module_dict = self._get_internal_modules_dict()
        event_module = _internal_module_dict[self.EVENT_IMPORT_PATH]
        return event_module

    def _get_internal_modules_dict(self):
        try:
            _internal_module_dict = self.menu_construct_dict['_internal']
            return _internal_module_dict
        except KeyError:
            self.logger.exception('Could not query _internal modules:')
            return -1

    def callback_project_save(self, sender, app_data):
        self.refresh_node_editor_dict()
        project_dict = self._construct_project_dict()
        self._save_project_to_file(project_dict)

    def _construct_project_dict(self) -> dict:
        project_dict = OrderedDict([])
        self._compile_child_tools_id_to_list()
        self._node_editor_tab_dict

    def callback_project_import(self, sender, app_data):
        pass

    def callback_project_open(self, sender, app_data):
        pass
