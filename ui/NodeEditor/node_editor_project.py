import dearpygui.dearpygui as dpg
from typing import List, Tuple
from multiprocessing import Queue
from multiprocessing.pool import ThreadPool
from ui.NodeEditor.utils import callback_project_save_as
from ui.NodeEditor.input_handler import add_keyboard_handler_registry, add_mouse_handler_registry, event_handler
from ui.NodeEditor.right_click_menu import RightClickMenu
from ui.NodeEditor.splitter import Splitter
from ui.NodeEditor.details_panel import DetailPanel
from ui.NodeEditor._internal_node_editor import DPGNodeEditor
from ui.NodeEditor.item_right_click_menus import tab_right_click_menu
from core.classes.node import NodeModule
from ui.NodeEditor.node_utils import construct_var_node_label, construct_module_name_from_var_action_and_type
from collections import OrderedDict
import os
from pathlib import Path
import shutil
from importlib import import_module
from copy import deepcopy
import traceback
from core.utils import create_queueHandler_logger, json_load_from_file_path, json_write_to_file_path, generate_uuid, \
    log_on_return_message, construct_tool_path_from_tools_path_and_tool_name, convert_python_path_to_import_path, \
    is_string_contains_special_characters, warn_file_dialog_and_reshow_widget, clear_file_dialog_children
from core.data_loader import refresh_core_data_with_json_dict
from core.executor import execute_event
from lib.constants import CACHE_DIR

INTERNAL_NODE_CATEGORY = '_internal'
EVENT_IMPORT_PATH = ''


class NodeEditor:
    _ver = '0.0.1'
    node_editor_label = 'Node Editor'
    node_editor_tag = generate_uuid()

    @property
    def node_editor_bb(self) -> List[tuple]:
        return self._node_editor_bb

    @node_editor_bb.setter
    def node_editor_bb(self, value: List[tuple]):
        self._node_editor_bb = value

    @property
    def node_editor_tab_dict(self) -> OrderedDict:
        return self._node_editor_tab_dict

    def __init__(
        self,
        setting_dict=None,
        node_dir=Path('nodes'),
        node_menu_list=None,
        use_debug_print=False,
        logging_queue=Queue()
    ):
        # ------ FLAGS --------
        self._init_flag = True
        self._use_debug_print = use_debug_print
        # ------ SETTINGS ------
        self._var_drop_popup_id = -1
        if setting_dict is None:
            self._setting_dict = {}
        else:
            self._setting_dict = setting_dict

        # ------ ATTRIBUTES -----
        self.current_tab_id = None
        self.menu_construct_dict = None
        self.current_node_editor_instance = None
        self._node_editor_tab_dict = OrderedDict([])
        # Tuple to store current node editor boundaries position
        self._node_editor_bb = [(), ()]
        self.project_name = 'MyRUTProject'

        # ------- LOGGING ______
        self.logging_queue = logging_queue
        self.logger = create_queueHandler_logger(__name__, logging_queue, self._use_debug_print)

        # ------- INITIALIZATION ______
        self.construct_node_menu(node_menu_list, node_dir)
        # Main viewport
        self._init_main_viewport()
        # Add handler registry
        self._add_handler_registry()
        # Cache this project to local appdata
        self.project_folder_path = self._create_cache_project_folder()
        # Thread pool
        self.thread_pool = ThreadPool()
        # Initialization done
        self._init_flag = False
        self.logger.info('**** Loaded main viewport')

    def construct_node_menu(self, node_menu_list: list, node_dir: Path):
        if node_menu_list is None:
            node_menu_list = [
                '_internal',
            ]
        self.menu_construct_dict = OrderedDict([])
        for node_category in node_menu_list:
            node_sources_path = node_dir / node_category
            for node_source in node_sources_path.glob('*.py'):
                import_path = convert_python_path_to_import_path(node_source)
                # Exclude __init__ import
                if import_path.endswith('__init__'):
                    continue
                self._import_node_module(node_category, import_path)

    def _import_node_module(self, node_category: str, import_path: str):
        module = import_module(import_path)
        if self.menu_construct_dict.get(node_category, None) is None:
            node_module_item = OrderedDict([])
            node_module_item.update(
                {import_path: NodeModule(module, import_path, module.Node.node_type)})
            if 'event' in import_path:
                global EVENT_IMPORT_PATH
                EVENT_IMPORT_PATH = import_path
            self.menu_construct_dict.update({node_category: node_module_item})
        else:
            self.menu_construct_dict[node_category].update(
                {import_path: NodeModule(module, import_path, module.Node.node_type)})

    def _init_main_viewport(self):
        with dpg.child_window(
            tag=self.node_editor_tag,
            label=self.node_editor_label,
            border=False
        ):
            with dpg.table(header_row=True, resizable=True, reorderable=False, borders_outerH=False,
                           borders_outerV=False, borders_innerV=False, borders_innerH=False):
                self.splitter_column = dpg.add_table_column(label=self.project_name, width_fixed=True,
                                                            init_width_or_weight=300)
                dpg.add_table_column(label='Event Graph')
                dpg.add_table_column(label='Details', width_fixed=True,
                                     init_width_or_weight=300)
                with dpg.table_row():
                    # Splitter
                    self.splitter_panel = Splitter(parent_instance=self)
                    # Node Graph
                    with dpg.tab_bar(reorderable=True, callback=self.callback_tab_bar_change) as self.tab_bar_id:
                        self.current_tab_id, self.current_node_editor_instance = \
                            self.callback_add_tab('', app_data='Default', user_data=(0, self.tab_bar_id))

                        dpg.add_tab_button(label='+', callback=self.add_node_graph_tab_ask_name,
                                           no_reorder=True, trailing=True)
                    self.detail_panel = DetailPanel(parent_instance=self)
            # Initialize right click menu
            self.right_click_menu = RightClickMenu(parent_inst=self,
                                                   menu_construct_dict=self.menu_construct_dict,
                                                   setting_dict=self._setting_dict,
                                                   use_debug_print=self._use_debug_print,
                                                   logging_queue=self.logging_queue)
        with dpg.window(
            label='Output Log',
            horizontal_scrollbar=True,
            no_close=True,
            show=False,
            height=300,
            width=500
        ) as self.output_log_id:
            self.log_output_window_id = dpg.add_text(tag='log')

    def add_node_graph_tab_ask_name(self, sender, app_data, is_retry=False,
                                    is_open_tool=False, import_path=None):
        _mid_widget_pos = [int(dpg.get_viewport_width() / 2.5), int(dpg.get_viewport_height() / 2.5)]
        with dpg.window(label='New tab',
                        pos=_mid_widget_pos, min_size=[10, 10], no_resize=True) as _modal_window:
            with dpg.group(horizontal=True):
                dpg.add_text("Name your new tab: ")
                if is_open_tool:
                    dpg.add_input_text(width=200, callback=self.callback_add_tab_and_import_tool,
                                       on_enter=True, user_data=(_modal_window, import_path),
                                       hint='Input and press "Enter" to apply')
                else:
                    dpg.add_input_text(width=200, callback=self.callback_add_tab,
                                       on_enter=True, user_data=_modal_window,
                                       hint='Input and press "Enter" to apply')
            if is_retry:
                dpg.add_text('Name existed or contains special characters, please retry another name!',
                             color=(204, 51, 0, 255))

    def callback_add_tab(self, sender, app_data, user_data):
        # delete the modal window
        if user_data:
            dpg.delete_item(user_data)
        new_tab_name = app_data
        return self._init_new_tab(new_tab_name)

    def _init_new_tab(self, new_tab_name: str, is_open_tool=False, tool_import_path=''):
        self.refresh_node_editor_dict()
        if self._node_editor_tab_dict.get(new_tab_name, None) is not None or \
            is_string_contains_special_characters(new_tab_name):
            return self.add_node_graph_tab_ask_name('', new_tab_name, is_retry=True,
                                                    is_open_tool=is_open_tool, import_path=tool_import_path)
        new_tab_id = dpg.add_tab(label=new_tab_name, parent=self.tab_bar_id,
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
        self._node_editor_tab_dict.update({new_tab_name: {'node_editor_instance': new_node_editor,
                                                          'id': new_tab_id
                                                          }})
        return new_tab_id, new_node_editor

    def callback_add_tab_and_import_tool(self, sender, app_data, user_data):
        # delete the modal window
        if user_data[0]:
            dpg.delete_item(user_data[0])
        new_tab_name = app_data
        tool_import_path = user_data[1]
        try:
            new_tab_id, new_node_editor = self._init_new_tab(new_tab_name, is_open_tool=True,
                                                             tool_import_path=tool_import_path)
            self._cache_current_node_editor_and_import_tool_to_new_tab(new_node_editor, tool_import_path)
        except Exception:
            pass

    def _cache_current_node_editor_and_import_tool_to_new_tab(self, new_node_editor_instance, tool_import_path: dict):
        _cache_node_editor_instance = self.current_node_editor_instance
        self.current_node_editor_instance = new_node_editor_instance
        new_node_editor_instance.callback_tool_import('NG_file_open', tool_import_path)
        self.current_node_editor_instance = _cache_node_editor_instance
        self.refresh_splitter_data()

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

    def callback_tab_bar_change(self, sender, app_data):
        self.update_current_tab_id_and_instance(app_data)
        self.detail_panel.refresh_ui_with_selected_node_info()
        self.refresh_splitter_data()
        self.clean_old_node_graph_registry_item()

    def update_current_tab_id_and_instance(self, tab_id: int):
        _selected_tab = dpg.get_item_label(tab_id)
        # Refresh the dict first in case user closes the tab
        self.refresh_node_editor_dict()
        try:
            self.current_node_editor_instance = self._node_editor_tab_dict[_selected_tab]['node_editor_instance']
            self.current_tab_id = tab_id
        except KeyError:
            self.logger.exception('Could not query current node editor instance:')
            return -1

    def refresh_node_editor_dict(self):
        self._check_all_tabs_and_trigger_deletion_if_found_closed()
        self._reflect_current_order_to_tab_dict()

    def _reflect_current_order_to_tab_dict(self):
        sorted_tab_list = self._get_tab_list_with_order()
        self._refresh_tab_dict_with_new_order_from_list(sorted_tab_list)

    def _refresh_tab_dict_with_new_order_from_list(self, new_order: list):
        for tab_name in new_order:
            self._node_editor_tab_dict.move_to_end(tab_name)

    def _check_all_tabs_and_trigger_deletion_if_found_closed(self):
        tuple_list = list(self._node_editor_tab_dict.items())
        for tab_name, tab_info in tuple_list:
            if not dpg.is_item_visible(tab_info['id']) and self._init_flag is False:
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

    def refresh_splitter_data(self):
        self.splitter_panel.event_dict = self.current_node_editor_instance.event_dict
        self.splitter_panel.var_dict = self.current_node_editor_instance.splitter_var_dict
        self.splitter_panel.exposed_var_dict = deepcopy(self.current_node_editor_instance.var_dict)

    def clean_old_node_graph_registry_item(self):
        _old_node_editor_instance = self.current_node_editor_instance
        _old_tab_name = dpg.get_item_label(self.current_tab_id)
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

    def _get_tab_list_with_order(self) -> list:
        converter = {}
        tab_name_list_with_order = []
        for item in dpg.get_item_children(self.tab_bar_id, 1):
            # Skip add button
            if dpg.get_item_label(item) == '+':
                continue
            converter[tuple(dpg.get_item_rect_min(item))] = dpg.get_item_label(item)

        pos = [dpg.get_item_rect_min(item) for item in dpg.get_item_children(self.tab_bar_id, 1) if
               dpg.get_item_label(item) != '+']
        sortedPos = sorted(pos, key=lambda position: pos[0])

        for item in sortedPos:
            tab_name_list_with_order.append(converter[tuple(item)])

        return tab_name_list_with_order

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

    def current_editor_add_event_node(self, event_name, override_pos=(0, 0)):
        event_module = self._get_event_module()
        added_node = self.current_node_editor_instance.add_node_from_module(event_module, pos=override_pos,
                                                                            override_label='Event ' + event_name)
        return added_node

    def _get_event_module(self):
        _internal_module_dict = self._get_internal_modules_dict()
        event_module = _internal_module_dict[EVENT_IMPORT_PATH]
        return event_module

    def _get_internal_modules_dict(self):
        try:
            _internal_module_dict = self.menu_construct_dict['_internal']
            return _internal_module_dict
        except KeyError:
            self.logger.exception('Could not query _internal modules:')
            return -1

    def _create_cache_project_folder(self):
        if CACHE_DIR.parent.exists():
            shutil.rmtree(CACHE_DIR.parent)
        CACHE_DIR.parent.mkdir()
        CACHE_DIR.mkdir()
        self._project_save_to_folder()
        return CACHE_DIR

    def callback_project_save_as(self, sender, app_data):
        project_path = Path(app_data['file_path_name'])
        action = dpg.get_item_label(sender)
        file_dialog_tag = sender
        if is_string_contains_special_characters(project_path.name):
            return_message = (3, 'Project name contains special character(s), please rename!')
            warn_file_dialog_and_reshow_widget(file_dialog_tag, return_message[1])
            return log_on_return_message(self.logger, action, return_message)
        if os.path.exists(project_path):
            return_message = (3, 'Project existed, please rename')
            warn_file_dialog_and_reshow_widget(file_dialog_tag, return_message[1])
            return log_on_return_message(self.logger, action, return_message)
        self._update_project_data(project_path)
        return_message = self._project_save_to_folder()
        log_on_return_message(self.logger, action, return_message)

    def _update_project_data(self, project_path: Path):
        self._update_project_name(project_path.name)
        self.project_folder_path = project_path

    def _update_project_name(self, new_project_name: str):
        self.project_name = new_project_name
        dpg.configure_item(self.splitter_column, label=new_project_name)

    def callback_project_open(self, sender, app_data):
        project_file_path = Path(app_data['file_path_name'])
        action = dpg.get_item_label(sender)
        return_message = self._open_new_project(project_file_path)
        log_on_return_message(self.logger, action, return_message)

    def _open_new_project(self, project_file_path: Path) -> Tuple[int, object]:
        self._clean_current_project()
        self._init_flag = True
        self._batch_import_tools_to_project(project_file_path)
        self._update_project_data(project_file_path.parent)
        self._init_flag = False
        return 1, ''

    def _clean_current_project(self):
        tuple_list = list(self._node_editor_tab_dict.items())
        for tab_name, tab_info in tuple_list:
            self._delete_tab(tab_info, tab_name)

    def _batch_import_tools_to_project(self, project_file_path: Path):
        project_dict = json_load_from_file_path(project_file_path)
        i = 0
        _first_imported_node_editor_instance = None
        _first_tab_id = 0
        for tool_name, tool_path in project_dict.items():
            self.callback_add_tab('project_open', tool_name, (0, self.tab_bar_id))
            if i == 0:
                _first_imported_node_editor_instance = self._node_editor_tab_dict[tool_name]['node_editor_instance']
                _first_tab_id = self._node_editor_tab_dict[tool_name]['id']
            self.current_node_editor_instance = self._node_editor_tab_dict[tool_name]['node_editor_instance']
            self.current_node_editor_instance.callback_tool_import('project_open', {
                'file_path_name': project_file_path.parent / tool_path})
            i += 1
        self.current_node_editor_instance = _first_imported_node_editor_instance
        self.current_tab_id = _first_tab_id

    def callback_project_save(self, sender):
        # If project is still temp, prompt to save project as another location
        if self.project_folder_path == CACHE_DIR:
            return callback_project_save_as()
        action = dpg.get_item_label(sender)
        return_message = self._project_save_to_folder()
        log_on_return_message(self.logger, action, return_message)

    def _project_save_to_folder(self) -> Tuple[int, object]:
        try:
            self.refresh_node_editor_dict()
            self._delete_tool_files_if_not_used()
            self._construct_project_folder()
        except Exception:
            return 4, traceback.format_exc()
        return 1, ''

    def _delete_tool_files_if_not_used(self):
        tools_path = self.project_folder_path / 'tools'
        if not tools_path.exists():
            return None
        for tool_file in tools_path.glob('*.rtool'):
            if self._node_editor_tab_dict.get(tool_file.name, None) is None:
                tool_file.unlink()

    def _construct_project_folder(self):
        self._construct_tools_folder()
        self._save_project_file()

    def _construct_tools_folder(self):
        self._create_tools_path_if_not_existed()
        for child_node_graph_name, child_node_graph_info in self._node_editor_tab_dict.items():
            child_node_graph_path = self._get_tool_path_from_tool_name(child_node_graph_name)
            child_node_graph_info['node_editor_instance'].callback_tool_save('',
                                                                             {'file_path_name': child_node_graph_path})

    def _create_tools_path_if_not_existed(self):
        tools_path = self.project_folder_path / 'tools'
        if not tools_path.parent.exists():
            tools_path.parent.mkdir()
        if not tools_path.exists():
            tools_path.mkdir()

    def _get_tool_path_from_tool_name(self, tool_name: str) -> str:
        tools_path = self.project_folder_path / 'tools'
        return construct_tool_path_from_tools_path_and_tool_name(tools_path, tool_name)

    def _save_project_file(self):
        tools_path = Path('tools')
        tool_list = []
        for tool_name in self._node_editor_tab_dict.keys():
            tool_path = construct_tool_path_from_tools_path_and_tool_name(tools_path, tool_name)
            tool_list.append((tool_name, tool_path))
        project_file_path = self.project_folder_path / (self.project_name + '.rproject')
        json_write_to_file_path(project_file_path, OrderedDict(tool_list))

    def refresh_node_graph_bounding_box(self):
        # Update node graph bounding box to restrict right click menu only shows when cursor is inside of it
        _current_tab_id = self.current_tab_id
        try:
            self.node_editor_bb[0] = (dpg.get_item_pos(_current_tab_id)[0] + 8,
                                      dpg.get_item_pos(_current_tab_id)[1] + 30)
            self.node_editor_bb[1] = (dpg.get_item_pos('__details_panel')[0] - 2,
                                      dpg.get_viewport_height() - 47)
        except SystemError:
            pass

    def callback_compile_current_node_graph(self):
        cache_file_path = CACHE_DIR / (__name__ + '.rtool')
        action = 'Compile node graph'
        self.current_node_editor_instance.callback_tool_save('',
                                                             app_data={'file_path_name': cache_file_path})
        data_dict = json_load_from_file_path(cache_file_path)
        return_message = refresh_core_data_with_json_dict(data_dict)
        log_on_return_message(self.logger, action, return_message)
        if return_message[0] == 1: #compile success
            return 1

    def subprocess_execution_event(self, event_tag):
        self._pop_output_log_window()
        self.thread_pool.apply_async(execute_event, (event_tag,))
        # Uncomment below if you want to execute event synchronously
        # execute_event(event_tag)

    def _pop_output_log_window(self):
        dpg.configure_item(self.output_log_id, show=True)
