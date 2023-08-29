import dearpygui.dearpygui as dpg

from multiprocessing import Queue
from multiprocessing.pool import ThreadPool

from ui.ToolsViewer.utils import tkinter_file_dialog
from core.utils import create_queueHandler_logger, json_load_from_file_path, add_user_input_box, \
    remove_node_type_from_node_label, log_on_return_message
from core.data_loader import refresh_core_data_with_json_dict
from core.executor import execute_event
from core.enum_types import NodeTypeFlag

from collections import OrderedDict
from pathlib import Path
from typing import Tuple

from libs.constants import CACHE_DIR
import subprocess


class ToolsViewer:
    """
    Main class to handle exported data from Node Editor and display them to DPG widgets

    """
    _ver = '0.0.1'
    tools_viewer_label = 'Tools Viewer'
    tools_viewer_tag = 'ToolsViewer'

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
        self.project_folder_path = CACHE_DIR
        if setting_dict is None:
            self._setting_dict = {}
        else:
            self._setting_dict = setting_dict
        self.thread_pool = ThreadPool()

        # ------- LOGGING ______
        self.logging_queue = logging_queue
        self.logger = create_queueHandler_logger(__name__, logging_queue, self._use_debug_print)

        # ------- INITIALIZATION ______
        self._init_main_viewport()

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
                             callback=self.update_current_tab_name_match_with_tab_id) as self.tab_bar_id:
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
        project_file_path = self.project_folder_path / '{}.mproject'.format(self.project_name)
        if not project_file_path.exists():
            return
        self._clean_current_project()
        self._batch_open_tools_in_project(project_file_path)

    def update_current_tab_name_match_with_tab_id(self, sender, app_data):
        for tab_name, tab_info in self.tab_dict.items():
            if tab_info['id'] == app_data:
                self.current_tab_name = tab_name
                break

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
        self._batch_open_tools_in_project(project_file_path)
        self._update_project_data(project_file_path.parent)

    def _clean_current_project(self):
        tab_name_list = list(self.tab_dict.keys())
        for tab_name in tab_name_list:
            self._delete_tab(tab_name)

    def _delete_tab(self, tab_name: str):
        dpg.delete_item(self.tab_dict[tab_name]['id'])
        self.tab_dict.pop(tab_name)

    def _batch_open_tools_in_project(self, project_file_path: Path):
        project_dict = json_load_from_file_path(project_file_path)
        self.current_tab_name = list(project_dict.keys())[0]
        for tool_name, tool_relative_path in project_dict.items():
            tool_abs_path = Path(project_file_path).parent / tool_relative_path
            tab_id = self._open_tool(tool_name, tool_abs_path)
            self._update_tab_dict_with_imported_tool(tool_name, tab_id, tool_abs_path)

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

    @staticmethod
    def _add_user_input_boxes_to_tab_from_vars_data(tab_window_id: int, vars_data: dict):
        for var_info in vars_data.values():
            if var_info['is_exposed'][0] is False:
                continue
            with dpg.table(parent=tab_window_id, header_row=False, no_pad_outerX=True):
                dpg.add_table_column(no_reorder=True, no_resize=True, init_width_or_weight=100)
                dpg.add_table_column(no_reorder=True, no_resize=True, init_width_or_weight=400)
                with dpg.table_row():
                    dpg.add_text(var_info['name'][0])
                    add_user_input_box(var_type=var_info['type'][0], width=500, tag=var_info['user_input_box_tag'])

    def _add_event_buttons_to_tab_from_nodes_data(self, tab_window_id: int, nodes_data: list):
        for node_info in nodes_data:
            if node_info['type'] != NodeTypeFlag.Event:
                continue
            event_label = remove_node_type_from_node_label(node_info['label'])
            dpg.add_button(width=-1, label=event_label, callback=self.callback_execute_event,
                           user_data=node_info['uuid'], parent=tab_window_id)

    def _update_tab_dict_with_imported_tool(self, tool_name: str, tab_id: int, tool_abs_path: Path):
        self.tab_dict.update({tool_name: {
            'id': tab_id,
            'tool_path': tool_abs_path
        }})

    def callback_project_open_in_node_editor(self):
        project_file_path = self.project_folder_path / '{}.mproject'.format(self.project_name)
        subprocess.Popen(f'../NodeEditor/NodeEditor.exe --project_path {project_file_path.as_posix()}')
        self.logger.info(f'**** Opening project {self.project_name} in NodeEditor ****')

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
