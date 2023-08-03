import dearpygui.dearpygui as dpg
from ui.ToolsViewer.utils import tkinter_file_dialog
from multiprocessing import Queue
from core.utils import create_queueHandler_logger, json_load_from_file_path
from collections import OrderedDict
from pathlib import Path


# TODO re-apply new NG logics to this, including: var node loading, caching, dirty trigger for var on exec
class ToolsViewer:
    """Main class to handle exported data from Node Editor and display them to DPG widgets
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
        self._tab_dict = OrderedDict([])
        self._use_debug_print = use_debug_print
        # ------ ATTRIBUTES -----
        self.project_name = 'MyRUTProject'
        if setting_dict is None:
            self._setting_dict = {}
        else:
            self._setting_dict = setting_dict

        # ------- LOGGING ______
        self.logging_queue = logging_queue
        self.logger = create_queueHandler_logger(__name__, logging_queue, self._use_debug_print)

        # ------- INITIALIZATION ______
        # Main viewport
        self._init_main_viewport([])

    def _callback_close_window(self, sender, app_data, user_data):
        pass

    def callback_project_open(self):
        """
        Open new project
        """
        project_file_path = tkinter_file_dialog()
        self._clean_current_project()
        self._batch_open_tools_in_project(project_file_path)
        self._update_project_data(project_file_path.parent)

    def _clean_current_project(self):
        tab_name_list = list(self._tab_dict.keys())
        for tab_name in tab_name_list:
            self._delete_tab(tab_name)

    def _delete_tab(self, tab_name: str):
        self._tab_dict.pop(tab_name)
        dpg.delete_item(tab_name)
        self.logger.info(f'****Deleted tab {tab_name}****')

    def _batch_open_tools_in_project(self, project_file_path: Path):
        project_dict = json_load_from_file_path(project_file_path)
        for tool_name, tool_path in project_dict.items():
            self._open_tool(tool_name)

    def _open_tool(self, tool_name):
        new_tab_id = self._init_new_tab(tool_name)
        self._import_tool_to_tab(new_tab_id, tool_name)

    def _init_new_tab(self, new_tab_name: str):
        new_tab_id = dpg.add_tab(label=new_tab_name, parent=self.tab_bar_id, closable=False)
        return new_tab_id

    def _import_tool_to_tab(self, tab_id: int, tool_name: str):
        tool_data = json_load_from_file_path(self._tab_dict[tool_name])

    def _update_project_data(self, project_path: Path):
        self._update_project_name(project_path.name)
        self.project_folder_path = project_path

    def _update_project_name(self, new_project_name: str):
        self.project_name = new_project_name
        dpg.configure_item(self.project_name_text_field_id, label=new_project_name)

    def _callback_help_menu(self, sender, app_data, user_data):
        pass

    def _init_main_viewport(self, input_var: list):
        # Create your main window and other widgets here
        with dpg.child_window(
            tag=self.tools_viewer_tag,
            label=self.tools_viewer_label,
            border=False
        ):
            self.project_name_text_field_id = dpg.add_button(label=self.project_name, width=-1, enabled=False)
            with dpg.tab_bar(reorderable=True, callback=self.callback_tab_bar_change) as self.tab_bar_id:
                with dpg.tab(tag='Default', label='Default', parent=self.tab_bar_id, closable=False):
                    with dpg.child_window(label="Main Window",
                                          height=self._setting_dict['viewport_height'] - 200,
                                          autosize_x=True):
                        for each in input_var:
                            if each['button_name']:
                                dpg.add_button(label=each['button_name'],
                                               tag=each['id'] + 'Event',
                                               width=-1,
                                               height=self._setting_dict['button_height'],
                                               # callback=self.trigger_event,
                                               user_data=each['id']
                                               )
                                with dpg.tooltip(each['id'] + 'Event'):
                                    dpg.add_text('A tool tip of {}!'.format(each['id']))
                    with dpg.child_window(label="Log Window",
                                          autosize_x=True,
                                          horizontal_scrollbar=True):
                        dpg.add_text(tag='log', tracked=False, track_offset=1.0)

    def callback_tab_bar_change(self, sender, app_data):
        pass
