import dearpygui.dearpygui as dpg
import argparse
import os
import json
from ui.NodeEditor.node_editor import NodeEditor
import logging
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Queue
import dearpygui.demo as demo
import datetime
from ui.NodeEditor.utils import callback_ng_file_open_menu, callback_ng_file_import_menu, callback_ng_file_save_menu, \
    callback_project_import_menu, callback_project_save_menu, callback_project_open_menu


def save_init():
    dpg.save_init_file("dpg.ini")


def get_arg():
    """Function to get arg from CLI or use NodeEditor.cfg as default"""
    parser = argparse.ArgumentParser(description="Riot Universal Tool - Node Editor", )

    parser.add_argument(
        "--setting",
        type=str,
        default=os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         'Config/NodeEditor.cfg')),
    )
    parser.add_argument(
        "--unused_async_loop",
        action='store_false'
    )

    parser.add_argument(
        "--is_debug_mode",
        action='store_false'
    )

    args = parser.parse_args()
    return args


def callback_file_dialog(sender, app_data, user_data):
    if sender == 'project_save':
        user_data.callback_project_save(sender, app_data)
    elif sender == 'project_open':
        user_data.callback_project_open(sender, app_data)
    elif sender == 'project_import':
        user_data.callback_project_import(sender, app_data)
    elif sender == 'NG_file_save':
        user_data.current_node_editor_instance.callback_file_save(sender, app_data)
    elif sender == 'NG_file_open':
        user_data.current_node_editor_instance.callback_file_open(sender, app_data)
    elif sender == 'NG_file_import':
        user_data.current_node_editor_instance.callback_file_import(sender, app_data)


def main():
    # Get flags from command line
    args = get_arg()
    setting = args.setting
    is_debug_mode = args.is_debug_mode

    # Get logger format
    outer_dir = os.path.dirname(os.path.abspath(__file__))
    fp_path = outer_dir + '/Config/NodeEditor.cfg'
    with open(fp_path) as fp:
        json_dict = json.load(fp)

    module_formatter = logging.Formatter(json_dict['logging_format'])

    # Setup master logger

    current_path = os.path.dirname(os.path.abspath(__file__))
    logger = logging.getLogger('NodeEditor')
    logger_queue = Queue()
    # Set logger level based on user args
    if is_debug_mode:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    # Define log output dir
    log_dir = current_path + '/Logs'
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    fileHandler = logging.FileHandler(f'{log_dir}/{logger.name}.log', mode='w')
    fileHandler.setLevel(logging.DEBUG)
    fileHandler.setFormatter(module_formatter)

    # Add stream handler
    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(logging.INFO)
    streamHandler.setFormatter(module_formatter)

    # Create Queue listener to handle multiprocessing logging
    ql = QueueListener(logger_queue, fileHandler, streamHandler, respect_handler_level=True)
    # Start listening to the queue
    ql.start()
    qh = QueueHandler(logger_queue)
    logger.addHandler(qh)

    # Load config
    logger.info("***** Load Config *****")
    with open(setting) as fp:
        setting_dict = json.load(fp)
    # DearPyGui window settings
    editor_width = setting_dict['editor_width']
    editor_height = setting_dict['editor_height']

    logger.info('**** DearPyGui Setup *****')
    dpg.create_context()

    # Load ini file if exist
    # ini_file_path = os.path.join(os.path.dirname(__file__), 'dpg.ini')
    # if os.path.isfile(ini_file_path):
    dpg.configure_app(init_file='dpg.ini')

    # demo.show_demo()
    dpg.create_viewport(
        title="RUT Node Editor",
        width=editor_width,
        height=editor_height
    )

    dpg.setup_dearpygui()
    # Setup DPG font
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with dpg.font_registry():
        with dpg.font(
            current_dir +
            '/ui/NodeEditor/font/OpenSans-Regular.ttf',
            16
        ) as default_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Vietnamese)
    dpg.bind_font(default_font)

    with dpg.window(
        width=1280,
        height=1000,
        tag='Main_Window',
        menubar=True,
        no_scrollbar=True
    ):
        node_editor = NodeEditor(setting_dict=setting_dict, use_debug_print=is_debug_mode,
                                 logging_queue=logger_queue)
        # Menu bar setup
        # Open project dialog
        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            modal=True,
            height=int(dpg.get_viewport_height() / 2),
            width=int(dpg.get_viewport_width() / 2),
            callback=callback_file_dialog,
            id='project_open',
            label='Open new Project',
            user_data=node_editor
        ):
            dpg.add_file_extension('.json')
            dpg.add_file_extension('', color=(150, 255, 150, 255))

        # Save project dialog
        datetime_now = datetime.datetime.now()
        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            modal=True,
            height=int(dpg.get_viewport_height() / 2),
            width=int(dpg.get_viewport_width() / 2),
            default_filename=datetime_now.strftime('%Y%m%d'),
            callback=callback_file_dialog,
            id='project_save',
            label='Save Project as ...',
            user_data=node_editor
        ):
            dpg.add_file_extension('.json')
            dpg.add_file_extension('', color=(150, 255, 150, 255))

        # Import Project Dialog

        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            modal=True,
            height=int(dpg.get_viewport_height() / 2),
            width=int(dpg.get_viewport_width() / 2),
            callback=callback_file_dialog,
            id='project_import',
            label='Import Project',
            user_data=node_editor
        ):
            dpg.add_file_extension('.json')
            dpg.add_file_extension('', color=(150, 255, 150, 255))

        # Open file dialog
        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            modal=True,
            height=int(dpg.get_viewport_height() / 2),
            width=int(dpg.get_viewport_width() / 2),
            callback=callback_file_dialog,
            id='NG_file_open',
            label='Open new Node Graph',
            user_data=node_editor
        ):
            dpg.add_file_extension('.json')
            dpg.add_file_extension('', color=(150, 255, 150, 255))

        # Export file dialog
        datetime_now = datetime.datetime.now()
        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            modal=True,
            height=int(dpg.get_viewport_height() / 2),
            width=int(dpg.get_viewport_width() / 2),
            default_filename=datetime_now.strftime('%Y%m%d'),
            callback=callback_file_dialog,
            id='NG_file_save',
            label='Save current Node Graph as ...',
            user_data=node_editor
        ):
            dpg.add_file_extension('.json')
            dpg.add_file_extension('', color=(150, 255, 150, 255))

        # Import File Dialog

        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            modal=True,
            height=int(dpg.get_viewport_height() / 2),
            width=int(dpg.get_viewport_width() / 2),
            callback=callback_file_dialog,
            id='NG_file_import',
            label='Import to current Node Graph',
            user_data=node_editor
        ):
            dpg.add_file_extension('.json')
            dpg.add_file_extension('', color=(150, 255, 150, 255))
        with dpg.menu_bar(label='Main Menu', tag='__menu_bar'):
            # Export/Import file
            with dpg.menu(label='File'):
                dpg.add_menu_item(
                    tag='Menu_Project_Open',
                    label='Open new Project',
                    callback=callback_project_open_menu
                )
                dpg.add_menu_item(
                    tag='Menu_Project_Save',
                    label='Save Project as ...',
                    callback=callback_project_save_menu
                )
                dpg.add_menu_item(
                    tag='Menu_Project_Import',
                    label='Import Project',
                    callback=callback_project_import_menu
                )
                dpg.add_menu_item(
                    tag='Menu_File_Open',
                    label='Open new Node Graph',
                    callback=callback_ng_file_open_menu
                )
                dpg.add_menu_item(
                    tag='Menu_File_Export',
                    label='Save current Node Graph as ...',
                    callback=callback_ng_file_save_menu
                )
                dpg.add_menu_item(
                    tag='Menu_File_Import',
                    label='Import to current Node Graph',
                    callback=callback_ng_file_import_menu
                )
            with dpg.menu(label='View'):
                dpg.add_menu_item(
                    tag='Menu_Save_Viewport',
                    label='Save Current Viewport',
                    callback=lambda: save_init
                )

    dpg.set_primary_window('Main_Window', True)
    dpg.show_viewport()
    # Synchronously Update tasks
    logger.info('**** Start Main Event Loop ****')
    logger.debug("Running main synchronously")
    while dpg.is_dearpygui_running():
        # Update node graph bounding box to restrict right click menu only shows when cursor is inside of it
        _current_tab_id = node_editor.current_tab_id
        node_editor.node_editor_bb[0] = (dpg.get_item_pos(_current_tab_id)[0] + 8,
                                         dpg.get_item_pos(_current_tab_id)[1] + 30)
        node_editor.node_editor_bb[1] = (dpg.get_item_pos('__details_panel')[0] - 2,
                                         dpg.get_viewport_height() - 47)
        # Render DPG frame
        dpg.render_dearpygui_frame()
    logger.info('**** Terminate process ****')
    # Stop logging queue listener
    ql.stop()
    logger.info('**** Close All Node ****')
    for node in node_editor.current_node_editor_instance.node_instance_dict.values():
        node.on_node_deletion()

    logger.info('**** Stop Event Loop ****')
    node_editor.terminate_flag = True
    logger.info('**** Destroy DearPyGui Context ****')
    dpg.destroy_context()


if __name__ == '__main__':
    main()
