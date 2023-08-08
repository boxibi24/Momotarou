import dearpygui.dearpygui as dpg
import webbrowser


def initialize_menu_bar(tools_viewer_project, setting_dict: dict):
    with dpg.menu_bar(label='Main Menu', tag='__menu_bar'):
        # Export/Import file
        with dpg.menu(label='File'):
            dpg.add_menu_item(
                tag='Menu_Project_Open',
                label='Open project',
                callback=tools_viewer_project.callback_project_open
            )
        with dpg.menu(label='Help'):
            dpg.add_menu_item(
                tag='Menu_Help_Documentation',
                label='Documentation',
                callback=callback_open_doc_url,
                user_data=setting_dict['doc_url']
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
