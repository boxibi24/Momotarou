import dearpygui.dearpygui as dpg
from ui.NodeEditor.node_editor_project import NodeEditor
from ui.NodeEditor.menu_bar import initialize_file_dialog, initialize_menu_bar
from core.executor import setup_executor_logger
from multiprocessing import Queue
import os


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


def initialize_node_editor_project(setting_dict: dict, logger_queue: Queue, is_debug_mode: bool):
    node_editor_project: NodeEditor = _initialize_primary_window_as_node_graph(setting_dict, logger_queue,
                                                                               is_debug_mode)
    render_dpg_frame(node_editor_project)

    _on_close_project(node_editor_project)


def _initialize_primary_window_as_node_graph(setting_dict: dict, logger_queue: Queue,
                                             is_debug_mode: bool) -> NodeEditor:
    with dpg.window(
        width=1280,
        height=1000,
        tag='Main_Window',
        menubar=True,
        no_scrollbar=True
    ):
        node_editor_project = NodeEditor(setting_dict=setting_dict, use_debug_print=is_debug_mode,
                                         logging_queue=logger_queue)

        initialize_file_dialog(node_editor_project)
        initialize_menu_bar(node_editor_project)
    dpg.set_primary_window('Main_Window', True)
    dpg.show_viewport()
    setup_executor_logger(logger_queue, is_debug_mode)
    return node_editor_project


def render_dpg_frame(node_editor_project: NodeEditor):
    while dpg.is_dearpygui_running():
        node_editor_project.refresh_node_graph_bounding_box()
        dpg.render_dearpygui_frame()


def _on_close_project(node_editor_project: NodeEditor):
    # Stop logging queue listener
    for node in node_editor_project.current_node_editor_instance.node_instance_dict.values():
        node.on_node_deletion()
    node_editor_project.terminate_flag = True
    dpg.destroy_context()
