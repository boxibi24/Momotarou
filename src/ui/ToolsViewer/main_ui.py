import dearpygui.dearpygui as dpg
from ui.ToolsViewer.tools_viewer_project import ToolsViewer
from multiprocessing import Queue
from pathlib import Path
from ui.ToolsViewer.menu_bar import initialize_menu_bar
from libs.constants import TOOLS_VIEWER_APP_NAME
from core.utils import camel_case_split


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
    tools_viewer_project: ToolsViewer = _initialize_primary_window_as_node_graph(setting_dict,
                                                                                 logger_queue,
                                                                                 is_debug_mode)

    if project_path:
        tools_viewer_project.callback_project_open(0, {'file_path_name': project_path})
    render_dpg_frame()

    _on_close_project(tools_viewer_project)


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
    with open(Path(__file__).parent.parent.parent / 'Logs' / f'ToolsViewer.log', 'r') as f:
        dpg.configure_item('log', default_value=f.read())


def _on_close_project(tools_viewer_project: ToolsViewer):
    tools_viewer_project.thread_pool.close()
    tools_viewer_project.thread_pool.join()
    dpg.destroy_context()
