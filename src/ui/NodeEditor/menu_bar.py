import dearpygui.dearpygui as dpg
from ui.NodeEditor.utils import callback_ng_file_open_menu, callback_ng_file_import_menu, callback_ng_file_save_menu, \
    callback_project_open_menu, callback_project_save_as
import webbrowser


def initialize_file_dialog(node_editor_project):
    """
    File dialog setup
    :param node_editor_project: Node editor instance
    :return:
    """

    # Open project dialog
    with dpg.file_dialog(
        directory_selector=False,
        show=False,
        modal=True,
        height=int(dpg.get_viewport_height() / 2),
        width=int(dpg.get_viewport_width() / 2),
        default_filename='MyRUTProject',
        callback=callback_file_dialog,
        id='project_open',
        label='Open project',
        user_data=node_editor_project,
        cancel_callback=callback_cancel_file_dialog
    ):
        dpg.add_file_extension('.mproject')
        dpg.add_file_extension('', color=(150, 255, 150, 255))

    # Save as project dialog
    with dpg.file_dialog(
        directory_selector=True,
        show=False,
        modal=True,
        height=int(dpg.get_viewport_height() / 2),
        width=int(dpg.get_viewport_width() / 2),
        callback=callback_file_dialog,
        id='project_save_as',
        label='Save project as',
        user_data=node_editor_project,
        default_filename=node_editor_project.project_name,
        cancel_callback=callback_cancel_file_dialog
    ):
        pass

    # Open tool dialog
    with dpg.file_dialog(
        directory_selector=False,
        show=False,
        modal=True,
        height=int(dpg.get_viewport_height() / 2),
        width=int(dpg.get_viewport_width() / 2),
        callback=callback_file_dialog,
        id='NG_file_open',
        label='Open node graph in new tab',
        user_data=node_editor_project,
        cancel_callback=callback_cancel_file_dialog
    ):
        dpg.add_file_extension('.mtool')
        dpg.add_file_extension('', color=(150, 255, 150, 255))

    # Export tool dialog
    with dpg.file_dialog(
        directory_selector=False,
        show=False,
        modal=True,
        height=int(dpg.get_viewport_height() / 2),
        width=int(dpg.get_viewport_width() / 2),
        default_filename='MyRUTTool',
        callback=callback_file_dialog,
        id='NG_file_save',
        label='Save current tab as',
        user_data=node_editor_project,
        cancel_callback=callback_cancel_file_dialog
    ):
        dpg.add_file_extension('.mtool')
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
        user_data=node_editor_project,
        cancel_callback=callback_cancel_file_dialog
    ):
        dpg.add_file_extension('.mtool')
        dpg.add_file_extension('', color=(150, 255, 150, 255))


def callback_file_dialog(sender, app_data, user_data):
    if sender == 'project_open':
        user_data.callback_project_open(sender, app_data)
    elif sender == 'project_save_as':
        user_data.callback_project_save_as(sender, app_data)
    elif sender == 'NG_file_save':
        user_data.current_node_editor_instance.callback_tool_save(sender, app_data)
    elif sender == 'NG_file_open':
        user_data.current_node_editor_instance.callback_tool_open(sender, app_data)
    elif sender == 'NG_file_import':
        user_data.current_node_editor_instance.callback_tool_import(sender, app_data)


def callback_cancel_file_dialog():
    pass


def initialize_menu_bar(node_editor_project, setting_dict: dict):
    with dpg.menu_bar(label='Main Menu', tag='__menu_bar'):
        # File
        with dpg.menu(label='File'):
            dpg.add_menu_item(
                tag='Menu_Project_Open',
                label='Open project',
                callback=callback_project_open_menu
            )
            dpg.add_menu_item(
                tag='Menu_Project_Save',
                label='Save project',
                callback=node_editor_project.callback_project_save
            )
            dpg.add_menu_item(
                tag='Menu_Project_Save_As',
                label='Save project as',
                callback=callback_project_save_as
            )
            dpg.add_separator()
            dpg.add_menu_item(
                tag='Menu_File_Open',
                label='Open .mtool in new tab',
                callback=callback_ng_file_open_menu
            )
            dpg.add_menu_item(
                tag='Menu_File_Export',
                label='Save current tab as',
                callback=callback_ng_file_save_menu
            )
            dpg.add_menu_item(
                tag='Menu_File_Import',
                label='Import .mtool to current tab',
                callback=callback_ng_file_import_menu
            )
        # Edit
        with dpg.menu(label='Edit'):
            dpg.add_menu_item(
                tag='Menu_Edit_Undo',
                label='Undo',
                callback=node_editor_project.callback_undo_action
            )
            dpg.add_menu_item(
                tag='Menu_Edit_Redo',
                label='Redo',
                callback=node_editor_project.callback_redo_action
            )
        # View
        with dpg.menu(label='View'):
            dpg.add_menu_item(
                tag='Menu_Save_Viewport',
                label='Save Current Viewport',
                callback=lambda: save_init
            )
        # Debug
        with dpg.menu(label='Debug'):
            dpg.add_menu_item(
                tag='Menu_Compile_Tool',
                label='Compile current tool',
                callback=node_editor_project.callback_compile_current_node_graph
            )
            dpg.add_menu_item(
                tag='Menu_Open_Project_In_ToolsViewer',
                label='Save and open project in ToolsViewer',
                callback=node_editor_project.callback_save_and_open_project_in_toolsviewer
            )
        with dpg.menu(label='Help'):
            dpg.add_menu_item(
                tag='Menu_Help_Documentation',
                label='Documentation',
                callback=callback_open_doc_url,
                user_data=setting_dict['doc_url']
            )
            dpg.add_menu_item(
                tag='Menu_Help_Issue',
                label='Report issue',
                callback=callback_report_issue,
                user_data=setting_dict['git_repository']
            )
            dpg.add_separator()
            dpg.add_menu_item(
                tag='Menu_Help_About',
                label='About',
                callback=callback_show_about_window
            )


def callback_open_doc_url(sender, app_data, user_data):
    doc_url = user_data
    webbrowser.open(doc_url)


def callback_report_issue(sender, app_data, user_data):
    repo_url = user_data
    webbrowser.open(repo_url + '-/issues/new')


def callback_show_about_window():
    with dpg.window(no_resize=True):
        dpg.add_text('RIOT UNIVERSAL TOOL', indent=120)
        dpg.add_separator()
        dpg.add_text('Made by the contribution of Character TS team @ Virtuos-Sparx:')
        dpg.add_text('Nguyen Vu Duc Thuy @thuy.nguyen', bullet=True)
        dpg.add_text('Bui Trung Dung @dung.bui', bullet=True)
        dpg.add_text('Nguyen Anh Tuan Tu @tu.nguyen_b', bullet=True)
        dpg.add_text('Nguyen Nguyen Vinh Truong @truong.nguyen_a', bullet=True)
        dpg.add_text('Le Ngoc My Anh @anh.le_b', bullet=True)
        dpg.add_separator()
        dpg.add_text('Product owner/ Contact point: Nguyen Anh Tuan Tu')


def save_init():
    dpg.save_init_file("dpg.ini")
