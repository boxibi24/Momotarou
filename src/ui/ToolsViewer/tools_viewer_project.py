import dearpygui.dearpygui as dpg

from multiprocessing import Queue
from multiprocessing.pool import ThreadPool

from ui.ToolsViewer.utils import tkinter_file_dialog
from core.utils import create_queueHandler_logger, json_load_from_file_path, add_user_input_box, \
    remove_node_type_from_node_label, log_on_return_message, json_write_to_file_path, dpg_get_value
from core.data_loader import refresh_core_data_with_json_dict
from core.executor import execute_event
from core.enum_types import NodeTypeFlag
from core.self_update import is_user_schedule_update_task

from collections import OrderedDict
from pathlib import Path
from typing import Tuple

from libs.constants import CACHE_DIR, LAST_SESSIONS_DIR, RECENT_PROJECTS_STORAGE_FILE_PATH, TOOLS_VIEWER_LOG_DIR
import subprocess


class ToolsViewer:
    """
    Main class to handle exported data from Node Editor and display them to DPG widgets

    """
    _ver = '0.0.1'
    tools_viewer_label = 'Tools Viewer'
    tools_viewer_tag = 'ToolsViewer'

    @property
    def cached_user_inputs_file_path(self) -> Path:
        return LAST_SESSIONS_DIR / (self.project_name + '.json')

    @property
    def file_path(self) -> Path:
        return self.project_folder_path / (self.project_name + '.mproject')

    def __init__(
        self,
        use_debug_print=False,
        setting_dict=None,
        logging_queue=Queue()
    ):
        # ------ FLAGS --------
        self.tab_dict = OrderedDict([])
        self._use_debug_print = use_debug_print

        # ------ ATTRIBUTES -----
        self.current_tab_name = None
        self.project_name = 'MyMomotarouProject'
        self.project_folder_path = CACHE_DIR / self.project_name
        if setting_dict is None:
            self._setting_dict = {}
        else:
            self._setting_dict = setting_dict
        self.thread_pool = ThreadPool()

        # ------- LOGGING ______
        self.logging_queue = logging_queue
        self.logger = create_queueHandler_logger(__name__, logging_queue, self._use_debug_print)

        # ------- UPDATE CHECK ------
        self.is_schedule_for_update = False
        self._check_for_update()

        # ------- INITIALIZATION ______
        self._init_main_viewport()

    def callback_check_for_update(self, sender, app_data, user_data):
        self._check_for_update(is_startup=False)

    def _check_for_update(self, is_startup=True):
        self.is_schedule_for_update = is_user_schedule_update_task(self._setting_dict['version'], is_startup)

    def _init_main_viewport(self):
        default_tab_name = 'Default'
        with dpg.child_window(
            tag=self.tools_viewer_tag,
            label=self.tools_viewer_label,
            border=False
        ):
            self.project_name_button_id = dpg.add_button(label=self.project_name + ' (click to refresh)', width=-1,
                                                         callback=self.refresh_project)
            with dpg.tab_bar(reorderable=True,
                             callback=self.callback_on_tab_bar_change) as self.tab_bar_id:
                with dpg.tab(label=default_tab_name, closable=False) as default_tab_id:
                    with dpg.child_window(label="Main Window",
                                          height=self._setting_dict['viewport_height'] - 200,
                                          autosize_x=True):
                        pass
                self.tab_dict.update({default_tab_name: {'id': default_tab_id,
                                                         'tool_path': Path()}})
                self.current_tab_name = default_tab_name
            with dpg.child_window(label="Log Window",
                                  autosize_x=True,
                                  horizontal_scrollbar=True):
                dpg.add_text(tag='log', tracked=False, track_offset=1.0)

    def refresh_project(self):
        if not self.file_path.exists():
            return
        self._clean_current_project()
        self._batch_open_tools_in_project(self.file_path, self.current_tab_name)

    def callback_on_tab_bar_change(self, sender, app_data):
        self.update_current_tab_name_by_tab_id(tab_id=app_data)
        self.update_cached_user_inputs_files_with_current_tab()

    def update_current_tab_name_by_tab_id(self, tab_id: int):
        for tab_name, tab_info in self.tab_dict.items():
            if tab_info['id'] == tab_id:
                self.current_tab_name = tab_name
                return

    def callback_project_open(self, sender, app_data):
        """
        Open new project
        """
        if app_data:
            project_file_path = Path(app_data['file_path_name'])
        else:
            project_file_path = tkinter_file_dialog()
        if project_file_path == Path('.'):
            return
        self._clean_current_project()
        self._update_project_data(project_file_path.parent)
        self._batch_open_tools_in_project(project_file_path)
        self.cache_as_recent_project()

    def _clean_current_project(self):
        tab_name_list = list(self.tab_dict.keys())
        for tab_name in tab_name_list:
            self._delete_tab(tab_name)

    def _delete_tab(self, tab_name: str):
        dpg.delete_item(self.tab_dict[tab_name]['id'])
        self.tab_dict.pop(tab_name)

    def _batch_open_tools_in_project(self, project_file_path: Path, default_opening_tab_name=''):
        project_dict = json_load_from_file_path(project_file_path)
        for tool_name, tool_relative_path in project_dict.items():
            tool_abs_path = Path(project_file_path).parent / tool_relative_path
            self.current_tab_name = tool_name
            tab_id = self._open_tool(tool_name, tool_abs_path)
            self._update_tab_dict_with_imported_tool(tool_name, tab_id, tool_abs_path)
        if default_opening_tab_name:
            self._select_default_opening_tab(default_opening_tab_name)
        else:
            self.current_tab_name = list(project_dict.keys())[0]

    def _open_tool(self, tool_name: str, tool_path: Path) -> int:
        tab_id, tab_child_window_id = self._init_new_tab_and_get_child_window_id(tool_name)
        self._import_tool_to_tab(tab_child_window_id, tool_path)
        return tab_id

    def _init_new_tab_and_get_child_window_id(self, new_tab_name: str) -> Tuple[int, int]:
        with dpg.tab(label=new_tab_name, parent=self.tab_bar_id, closable=False) as tab_id:
            with dpg.child_window(label="Main Window",
                                  height=self._setting_dict['viewport_height'] - 200,
                                  autosize_x=True) as tab_child_window_id:
                pass
        return tab_id, tab_child_window_id

    def _import_tool_to_tab(self, tab_child_window_id: int, tool_path: Path):
        tool_data = json_load_from_file_path(tool_path)
        self._add_user_input_boxes_to_tab_from_vars_data(tab_child_window_id, tool_data['vars'])
        self._add_event_buttons_to_tab_from_nodes_data(tab_child_window_id, tool_data['nodes'])

    def _add_user_input_boxes_to_tab_from_vars_data(self, tab_window_id: int, vars_data: dict):
        for var_info in vars_data.values():
            if var_info['is_exposed'][0] is False:
                continue
            with dpg.table(parent=tab_window_id, header_row=False, no_pad_outerX=True):
                dpg.add_table_column(no_reorder=True, no_resize=True, init_width_or_weight=100)
                dpg.add_table_column(no_reorder=True, no_resize=True, init_width_or_weight=400)
                with dpg.table_row():
                    _var_name = var_info['name'][0]
                    dpg.add_text(_var_name)
                    exposed_var_user_input_box_tag = var_info.get('user_input_box_tag', None)
                    if exposed_var_user_input_box_tag is not None:
                        cached_user_input_value = self.get_cached_user_inputs().get(_var_name, None)
                        add_user_input_box(var_type=var_info['type'][0],
                                           width=500,
                                           tag=var_info['user_input_box_tag'],
                                           default_value=cached_user_input_value)
                    else:
                        add_user_input_box(var_type=var_info['type'][0],
                                           width=500,
                                           tag=var_info['user_input_box_tag'])

    def get_cached_user_inputs(self):
        user_inputs_data = json_load_from_file_path(self.cached_user_inputs_file_path)
        return user_inputs_data.get(self.current_tab_name, {})

    def _add_event_buttons_to_tab_from_nodes_data(self, tab_window_id: int, nodes_data: list):
        for node_info in nodes_data:
            if node_info['type'] != NodeTypeFlag.Event:
                continue
            event_label = remove_node_type_from_node_label(node_info['label'])
            dpg.add_button(width=-1, label=event_label, callback=self.callback_execute_event,
                           user_data=node_info['uuid'], parent=tab_window_id)

    def _select_default_opening_tab(self, default_opening_tab_name: str):
        default_opening_tab_id = self._get_tab_id_from_label(default_opening_tab_name)
        self.update_current_tab_name_by_tab_id(default_opening_tab_id)
        dpg.set_value(self.tab_bar_id, default_opening_tab_id)

    def _get_tab_id_from_label(self, search_tab_label: str) -> int:
        for tab_label, tab_info in self.tab_dict.items():
            if search_tab_label == tab_label:
                return tab_info['id']
        return list(self.tab_dict.values())[0]['id']

    def _update_tab_dict_with_imported_tool(self, tool_name: str, tab_id: int, tool_abs_path: Path):
        self.tab_dict.update({tool_name: {
            'id': tab_id,
            'tool_path': tool_abs_path
        }})

    def callback_project_open_in_node_editor(self):
        subprocess.Popen(f'../NodeEditor/NodeEditor.exe --project_path "{self.file_path.as_posix()}"')
        self.logger.info(f'**** Opening project {self.project_name} in NodeEditor ****')

    def callback_open_project_log(self):
        subprocess.Popen(f'notepad "{TOOLS_VIEWER_LOG_DIR}"')
        self.logger.info(f'**** Opening Tools Viewer project log ****')

    def callback_execute_event(self, sender, app_data, user_data):
        event_tag = user_data
        return_message = refresh_core_data_with_json_dict(self.get_current_tool_data())
        log_on_return_message(self.logger, 'Compile node graph', return_message)
        if return_message[0] == 1:  # compile success
            self.subprocess_execution_event(event_tag)

    def get_current_tool_data(self) -> dict:
        tool_path = self.tab_dict[self.current_tab_name]['tool_path']
        return json_load_from_file_path(tool_path)

    def subprocess_execution_event(self, event_tag: str):
        self.thread_pool.apply_async(execute_event, (event_tag,))

    def _update_project_data(self, project_path: Path):
        self._update_project_name(project_path.name)
        self.project_folder_path = project_path

    def _update_project_name(self, new_project_name: str):
        self.project_name = new_project_name
        dpg.configure_item(self.project_name_button_id, label=new_project_name + ' (click to refresh)')

    def _init_cached_user_inputs_file(self):
        if not self.cached_user_inputs_file_path.exists():
            to_export_dict = self._get_current_tab_user_inputs()
            json_write_to_file_path(self.cached_user_inputs_file_path, to_export_dict)

    def update_cached_user_inputs_files_with_current_tab(self):
        _to_update_user_inputs_dict = json_load_from_file_path(self.cached_user_inputs_file_path)
        _current_tab_user_inputs_value = self._get_current_tab_user_inputs()
        _to_update_user_inputs_dict.update(_current_tab_user_inputs_value)
        json_write_to_file_path(self.cached_user_inputs_file_path, _to_update_user_inputs_dict)

    def _get_current_tab_user_inputs(self) -> dict:
        current_vars_data = json_load_from_file_path(self.tab_dict[self.current_tab_name]['tool_path'])['vars']
        exposed_var_dict = {}
        for exposed_var_info in current_vars_data.values():
            if not exposed_var_info['is_exposed'][0]:
                continue
            exposed_var_name = exposed_var_info['name'][0]
            user_input_value = dpg_get_value(exposed_var_info['user_input_box_tag'])
            exposed_var_dict.update({exposed_var_name: user_input_value})

        return {self.current_tab_name: exposed_var_dict}

    def cache_as_recent_project(self):
        recent_project_data = json_load_from_file_path(RECENT_PROJECTS_STORAGE_FILE_PATH)
        recent_project_data['recent_projects'].insert(0, {
            "project_name": self.project_name,
            "project_file_path": self.file_path.as_posix()
        })
        while len(recent_project_data) >= self._setting_dict['MAX_RECENT_PROJECT_CACHE']:
            recent_project_data['recent_projects'].pop()
        json_write_to_file_path(RECENT_PROJECTS_STORAGE_FILE_PATH, recent_project_data)

    def cache_as_last_project(self):
        recent_project_data = json_load_from_file_path(RECENT_PROJECTS_STORAGE_FILE_PATH)
        recent_project_data['last_project'].update({
            "project_name": self.project_name,
            "project_file_path": self.file_path.as_posix()
        })
        json_write_to_file_path(RECENT_PROJECTS_STORAGE_FILE_PATH, recent_project_data)
