import dearpygui.dearpygui as dpg
from ui.ToolsViewer.tools_viewer_project import ToolsViewer
from multiprocessing import Queue
import os
from pathlib import Path
from ui.ToolsViewer.menu_bar import initialize_menu_bar


def initialize_dpg(editor_width: int, editor_height: int):
    dpg.create_context()

    dpg.configure_app(init_file='dpg.ini')

    dpg.create_viewport(
        title="RUT Node Editor",
        width=editor_width,
        height=editor_height
    )

    dpg.setup_dearpygui()


def setup_dpg_font():
    # Setup DPG font
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with dpg.font_registry():
        with dpg.font(
            current_dir +
            '/font/OpenSans-Regular.ttf',
            16
        ) as default_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Vietnamese)
    dpg.bind_font(default_font)


def initialize_tools_viewer_project(setting_dict: dict, packages_list: list, logger_queue: Queue, is_debug_mode: bool):
    tools_viewer_project: ToolsViewer = _initialize_primary_window_as_node_graph(setting_dict, packages_list,
                                                                                 logger_queue,
                                                                                 is_debug_mode)
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

        initialize_menu_bar(tools_viewer_project)
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
