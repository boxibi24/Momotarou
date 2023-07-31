import dearpygui.dearpygui as dpg
import datetime
from ui.NodeEditor.utils import callback_ng_file_open_menu, callback_ng_file_import_menu, callback_ng_file_save_menu, \
    callback_project_save_menu, callback_project_open_menu, callback_project_new_menu
import os


def initialize_file_dialog(node_editor):
    # Menu bar setup
    # Open project dialog
    with dpg.file_dialog(
        directory_selector=True,
        show=False,
        modal=True,
        height=int(dpg.get_viewport_height() / 2),
        width=int(dpg.get_viewport_width() / 2),
        callback=callback_file_dialog,
        id='project_new',
        label='New Project',
        user_data=node_editor,
        default_filename='MyRUTProject'
    ):
        pass
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
        id='project_open',
        label='Open Project',
        user_data=node_editor,
        cancel_callback=callback_cancel_file_dialog
    ):
        dpg.add_file_extension('.rproject')
        dpg.add_file_extension('', color=(150, 255, 150, 255))

    # Import Project Dialog

    with dpg.file_dialog(
        directory_selector=False,
        show=False,
        modal=True,
        height=int(dpg.get_viewport_height() / 2),
        width=int(dpg.get_viewport_width() / 2),
        callback=callback_file_dialog,
        id='project_save',
        label='Save Project',
        user_data=node_editor,
        cancel_callback=callback_cancel_file_dialog
    ):
        dpg.add_file_extension('.rproject')
        dpg.add_file_extension('', color=(150, 255, 150, 255))

    # Open tool dialog
    with dpg.file_dialog(
        directory_selector=False,
        show=False,
        modal=True,
        height=int(dpg.get_viewport_height() / 2),
        width=int(dpg.get_viewport_width() / 2),
        callback=callback_file_dialog,
        id='NG_file_open',
        label='Open Node Graph in new tab',
        user_data=node_editor,
        cancel_callback=callback_cancel_file_dialog
    ):
        dpg.add_file_extension('.rtool')
        dpg.add_file_extension('', color=(150, 255, 150, 255))

    # Export tool dialog
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
        label='Save current tab as',
        user_data=node_editor,
        cancel_callback=callback_cancel_file_dialog
    ):
        dpg.add_file_extension('.rtool')
        dpg.add_file_extension('', color=(150, 255, 150, 255))

    # Import tool Dialog

    with dpg.file_dialog(
        directory_selector=False,
        show=False,
        modal=True,
        height=int(dpg.get_viewport_height() / 2),
        width=int(dpg.get_viewport_width() / 2),
        callback=callback_file_dialog,
        id='NG_file_import',
        label='Import node graph to current tab',
        user_data=node_editor,
        cancel_callback=callback_cancel_file_dialog
    ):
        dpg.add_file_extension('.rtool')
        dpg.add_file_extension('', color=(150, 255, 150, 255))


def callback_file_dialog(sender, app_data, user_data):
    if sender == 'project_new':
        user_data.callback_project_new(sender, app_data)
    elif sender == 'project_open':
        user_data.callback_project_open(sender, app_data)
    elif sender == 'project_save':
        user_data.callback_project_save(sender, app_data)
    elif sender == 'NG_file_save':
        user_data.current_node_editor_instance.callback_tool_save(sender, app_data)
    elif sender == 'NG_file_open':
        user_data.current_node_editor_instance.callback_file_open(sender, app_data)
    elif sender == 'NG_file_import':
        user_data.current_node_editor_instance.callback_file_import(sender, app_data)


def callback_cancel_file_dialog():
    pass


def initialize_menu_bar(node_editor_project: object):
    with dpg.menu_bar(label='Main Menu', tag='__menu_bar'):
        # Export/Import file
        with dpg.menu(label='File'):
            dpg.add_menu_item(
                tag='Menu_Project_New',
                label='New Project',
                callback=callback_project_new_menu
            )
            dpg.add_menu_item(
                tag='Menu_Project_Open',
                label='Open Project',
                callback=callback_project_open_menu
            )
            dpg.add_menu_item(
                tag='Menu_Project_Save',
                label='Save Project',
                callback=callback_project_save_menu
            )
            dpg.add_separator()
            dpg.add_menu_item(
                tag='Menu_File_Open',
                label='Open Node Graph in new tab',
                callback=callback_ng_file_open_menu
            )
            dpg.add_menu_item(
                tag='Menu_File_Export',
                label='Save current tab as',
                callback=callback_ng_file_save_menu
            )
            dpg.add_menu_item(
                tag='Menu_File_Import',
                label='Import Node Graph to current tab',
                callback=callback_ng_file_import_menu
            )
        with dpg.menu(label='View'):
            dpg.add_menu_item(
                tag='Menu_Save_Viewport',
                label='Save Current Viewport',
                callback=lambda: save_init
            )
        with dpg.menu(label='Build'):
            dpg.add_menu_item(
                tag='Menu_Compile_Tool',
                label='Compile',
                callback=node_editor_project.callback_compile_current_node_graph
            )


def save_init():
    dpg.save_init_file("dpg.ini")
