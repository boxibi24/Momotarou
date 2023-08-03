import dearpygui.dearpygui as dpg


def initialize_menu_bar(tools_viewer_project):
    with dpg.menu_bar(label='Main Menu', tag='__menu_bar'):
        # Export/Import file
        with dpg.menu(label='File'):
            dpg.add_menu_item(
                tag='Menu_Project_Open',
                label='Open project',
                callback=tools_viewer_project.callback_project_open
            )
