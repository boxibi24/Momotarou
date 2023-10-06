import dearpygui.dearpygui as dpg
from ui.ToolsViewer.tools_viewer_project import ToolsViewer
from multiprocessing import Queue
from pathlib import Path
from ui.ToolsViewer.menu_bar import initialize_menu_bar
from libs.constants import TOOLS_VIEWER_APP_NAME, RECENT_PROJECTS_STORAGE_FILE_PATH, LAST_SESSIONS_DIR, LOCALAPPDATA,\
    TOOLS_VIEWER_LOG_DIR
from core.utils import camel_case_split, get_last_project_file_path, json_write_to_file_path


def initialize_dpg(editor_width: int, editor_height: int):
    dpg.create_context()

    dpg.configure_app(init_file='dpg.ini')

    dpg.create_viewport(
        title=camel_case_split(camel_case_split(TOOLS_VIEWER_APP_NAME)),
        width=editor_width,
        height=editor_height
    )

    dpg.setup_dearpygui()


def setup_dpg_font():
    # Setup DPG font
    font_path = Path(__file__).parent.parent.parent / 'font/OpenSans-Regular.ttf'
    with dpg.font_registry():
        with dpg.font(font_path.as_posix(),
                      16
                      ) as default_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Vietnamese)
    dpg.bind_font(default_font)


def setup_dpg_icon():
    # Setup DPG font
    icon_path = Path(__file__).parent.parent.parent / f'icons/{TOOLS_VIEWER_APP_NAME}.ico'
    dpg.set_viewport_large_icon(icon_path.as_posix())
    dpg.set_viewport_small_icon(icon_path.as_posix())


def initialize_tools_viewer_project(setting_dict: dict, logger_queue: Queue,
                                    is_debug_mode: bool, project_path: str):
    create_localappdata_storage_dir()
    tools_viewer_project: ToolsViewer = _initialize_primary_window_as_node_graph(setting_dict,
                                                                                 logger_queue,
                                                                                 is_debug_mode)

    if project_path:
        tools_viewer_project.callback_project_open(0, {'file_path_name': project_path})
    else:
        last_project_file_path = get_last_project_file_path()
        if last_project_file_path:
            tools_viewer_project.callback_project_open(0, {'file_path_name': last_project_file_path})
    render_dpg_frame()

    return destroy_project_and_get_update_status(tools_viewer_project)


def create_localappdata_storage_dir():
    init_recent_projects_storage()


def init_recent_projects_storage():
    if not LAST_SESSIONS_DIR.parent.exists():
        LAST_SESSIONS_DIR.parent.mkdir()
    if not LAST_SESSIONS_DIR.exists():
        LAST_SESSIONS_DIR.mkdir()
        init_recent_project_file()
    if not RECENT_PROJECTS_STORAGE_FILE_PATH.exists():
        init_recent_project_file()


def init_recent_project_file():
    json_write_to_file_path(RECENT_PROJECTS_STORAGE_FILE_PATH, {
        "last_project": {
            "project_name": "",
            "project_file_path": ""
        },
        "recent_projects": []
    })


def _initialize_primary_window_as_node_graph(setting_dict: dict, logger_queue: Queue,
                                             is_debug_mode: bool) -> ToolsViewer:
    with dpg.window(
        width=1280,
        height=1000,
        tag='Main_Window',
        menubar=True,
        no_scrollbar=True
    ):
        tools_viewer_project = ToolsViewer(setting_dict=setting_dict,
                                           use_debug_print=is_debug_mode,
                                           logging_queue=logger_queue)

        initialize_menu_bar(tools_viewer_project, setting_dict)
    dpg.set_primary_window('Main_Window', True)
    dpg.show_viewport()
    return tools_viewer_project


def render_dpg_frame():
    while dpg.is_dearpygui_running():
        _update_log_window()
        dpg.render_dearpygui_frame()


def _update_log_window():
    with open(TOOLS_VIEWER_LOG_DIR, 'r') as f:
        dpg.configure_item('log', default_value=f.read())


def destroy_project_and_get_update_status(tools_viewer_project: ToolsViewer):
    tools_viewer_project.update_cached_user_inputs_files_with_current_tab()
    tools_viewer_project.cache_as_last_project()
    is_schedule_update = tools_viewer_project.is_schedule_for_update
    tools_viewer_project.thread_pool.close()
    tools_viewer_project.thread_pool.join()
    dpg.destroy_context()
    return is_schedule_update
