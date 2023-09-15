import dearpygui.dearpygui as dpg
from ui.NodeEditor.node_editor_project import NodeEditor
from ui.NodeEditor.menu_bar import initialize_file_dialog, initialize_menu_bar
from multiprocessing import Queue
from pathlib import Path
from libs.constants import NODE_EDITOR_APP_NAME, CACHE_DIR, LAST_SESSIONS_DIR, RECENT_PROJECTS_STORAGE_FILE_PATH, \
    INTERMEDIATE_DIR, LOCALAPPDATA
from core.utils import camel_case_split, get_last_project_file_path, json_write_to_file_path
import shutil


def initialize_dpg(editor_width: int, editor_height: int):
    dpg.create_context()

    dpg.configure_app(init_file='dpg.ini')
    dpg.create_viewport(
        title=camel_case_split(NODE_EDITOR_APP_NAME),
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
    icon_path = Path(__file__).parent.parent.parent / f'icons/{NODE_EDITOR_APP_NAME}.ico'
    dpg.set_viewport_large_icon(icon_path.as_posix())
    dpg.set_viewport_small_icon(icon_path.as_posix())


def initialize_node_editor_project(setting_dict: dict, packages_list: list,
                                   logger_queue: Queue, is_debug_mode: bool, project_path: str):
    create_localappdata_storage_dir()
    node_editor_project: NodeEditor = _initialize_primary_window_as_node_graph(setting_dict, packages_list,
                                                                               logger_queue,
                                                                               is_debug_mode)
    if project_path:
        node_editor_project.callback_project_open(0, {'file_path_name': project_path})
    else:
        last_project_file_path = get_last_project_file_path()
        if last_project_file_path:
            node_editor_project.callback_project_open(0, {'file_path_name': last_project_file_path})

    render_dpg_frame(node_editor_project)

    _on_close_project(node_editor_project)


def create_localappdata_storage_dir():
    init_cache_dir()
    init_intermediate_dir()
    init_recent_projects_storage()


def init_cache_dir():
    if not CACHE_DIR.parent.exists():
        CACHE_DIR.parent.mkdir()
    if not CACHE_DIR.exists():
        CACHE_DIR.mkdir()
    else:
        refresh_cache_dir()


def refresh_cache_dir():
    shutil.rmtree(CACHE_DIR)
    CACHE_DIR.mkdir()


def init_intermediate_dir():
    if not INTERMEDIATE_DIR.parent.exists():
        INTERMEDIATE_DIR.parent.mkdir()
    if not INTERMEDIATE_DIR.exists():
        INTERMEDIATE_DIR.mkdir()


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


def _initialize_primary_window_as_node_graph(setting_dict: dict, packages_list: list, logger_queue: Queue,
                                             is_debug_mode: bool) -> NodeEditor:
    with dpg.window(
        width=1280,
        height=1000,
        tag='Main_Window',
        menubar=True,
        no_scrollbar=True
    ):
        node_editor_project = NodeEditor(setting_dict=setting_dict, node_menu_list=packages_list,
                                         use_debug_print=is_debug_mode,
                                         logging_queue=logger_queue)

        initialize_file_dialog(node_editor_project)
        initialize_menu_bar(node_editor_project, setting_dict)
    dpg.set_primary_window('Main_Window', True)
    dpg.show_viewport()
    return node_editor_project


def render_dpg_frame(node_editor_project: NodeEditor):
    while dpg.is_dearpygui_running():
        node_editor_project.refresh_node_graph_bounding_box()
        _update_log_window()
        dpg.render_dearpygui_frame()


def _update_log_window():
    with open(LOCALAPPDATA / 'Logs' / 'NodeEditor.log', 'r') as f:
        dpg.configure_item('log', default_value=f.read())


def _on_close_project(node_editor_project: NodeEditor):
    node_editor_project.update_cached_user_inputs_files_with_current_tab()
    node_editor_project.cache_as_last_project()
    for node in node_editor_project.current_node_editor_instance.node_instance_dict.values():
        node.on_node_deletion()
    node_editor_project.thread_pool.close()
    node_editor_project.thread_pool.join()
    # Remove cache folder
    shutil.rmtree(CACHE_DIR)
    dpg.destroy_context()
