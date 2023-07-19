import dearpygui.dearpygui as dpg
from tkinter import Tk, messagebox
from ui.NodeEditor.input_handler import delete_selected_node
from copy import deepcopy


def node_right_click_menu():
    with dpg.window(
        popup=True,
        autosize=True,
        no_move=True,
        no_open_over_existing_popup=True,
        no_saved_settings=True,
        max_size=[200, 200],
        min_size=[10, 10]
    ):
        dpg.add_selectable(label='Delete')
        dpg.add_selectable(label='Cut')
        dpg.add_selectable(label='Copy')
        dpg.add_selectable(label='Duplicate')


def event_right_click_menu(sender, app_data, user_data):
    with dpg.window(
        popup=True,
        autosize=True,
        no_move=True,
        no_open_over_existing_popup=True,
        no_saved_settings=True,
        max_size=[200, 200],
        min_size=[10, 10]
    ):
        dpg.add_selectable(label='Run', callback=callback_run_event, user_data=user_data)
        dpg.add_selectable(label='Delete', callback=callback_ask_event_delete, user_data=user_data)


def callback_run_event(sender, app_data, user_data):
    _event_node_tag = user_data[1][user_data[0]]
    _master_node_editor_instance = user_data[2]
    _current_node_editor_instance = _master_node_editor_instance.current_node_editor_instance
    _current_node_editor_instance.execute_event('', '', user_data=_event_node_tag)


def callback_ask_event_delete(sender, app_data, user_data):
    """
    Callback to re-confirm delete event
    """
    _mid_widget_pos = [int(dpg.get_viewport_width() / 2.5), int(dpg.get_viewport_height() / 2.5)]
    with dpg.window(modal=True, label='Delete Event',
                    pos=_mid_widget_pos) as _modal_window:
        dpg.add_text("Delete event will also delete event node instance!\nThis operation cannot be "
                     "undone!")
        with dpg.group(horizontal=True):
            dpg.add_button(label="OK", width=75, callback=callback_variable_delete,
                           user_data=(user_data, _modal_window))
            dpg.add_button(label="Cancel", width=75, callback=lambda: dpg.delete_item(_modal_window))


def callback_delete_event(sender, app_data, user_data):
    pass


def exposed_var_right_click_menu():
    with dpg.window(
        popup=True,
        autosize=True,
        no_move=True,
        no_open_over_existing_popup=True,
        no_saved_settings=True,
        max_size=[200, 200],
        min_size=[10, 10]
    ):
        dpg.add_selectable(label='Move Up')
        dpg.add_selectable(label='Move Down')


def variable_right_click_menu(sender, app_data, user_data):
    with dpg.window(
        popup=True,
        autosize=True,
        no_move=True,
        no_open_over_existing_popup=True,
        no_saved_settings=True,
        max_size=[200, 200],
        min_size=[10, 10]
    ):
        dpg.add_selectable(label='Delete', callback=callback_ask_variable_delete, user_data=user_data)
        dpg.add_selectable(label='Cut (not implemented)', callback=callback_variable_cut, user_data=user_data)
        dpg.add_selectable(label='Copy (not implemented)', callback=callback_variable_copy, user_data=user_data)
        dpg.add_selectable(label='Duplicate (not implemented)', callback=callback_variable_duplicate,
                           user_data=user_data)


def callback_ask_variable_delete(sender, app_data, user_data):
    """
    Callback to re-confirm delete variable
    """
    _mid_widget_pos = [int(dpg.get_viewport_width() / 2.5), int(dpg.get_viewport_height() / 2.5)]
    with dpg.window(modal=True, label='Delete Variable',
                    pos=_mid_widget_pos) as _modal_window:
        dpg.add_text("Delete variable will delete all node instances of this variable!\nThis operation cannot be "
                     "undone!")
        with dpg.group(horizontal=True):
            dpg.add_button(label="OK", width=75, callback=callback_variable_delete,
                           user_data=(user_data, _modal_window))
            dpg.add_button(label="Cancel", width=75, callback=lambda: dpg.delete_item(_modal_window))


def callback_variable_delete(sender, app_data, user_data):
    # Delete the modal window first
    dpg.delete_item(user_data[1])
    _var_tag = user_data[0][0]
    _master_node_editor_instance = user_data[0][1]
    _current_node_editor_instance = _master_node_editor_instance.current_node_editor_instance
    _splitter_panel = _current_node_editor_instance.splitter_panel

    _var_name = _current_node_editor_instance.var_dict[_var_tag]['name'][0]
    _node_list = []
    for node in _current_node_editor_instance.node_instance_dict.values():
        _node_list.append(node)
    for node in _node_list:
        if _var_name in node.node_label:
            delete_selected_node(_master_node_editor_instance, node.id)
    # Delete var from the var dicts
    _current_node_editor_instance.var_dict.pop(_var_tag)
    _current_node_editor_instance.splitter_var_dict.pop(_var_tag)
    _splitter_panel.combo_dict.pop(_var_tag)

    # Refresh all UI elements to reflect var deletion
    # First refresh detail panel
    _master_node_editor_instance.detail_panel.refresh_ui()
    # Refresh splitter items
    _splitter_panel.var_dict = _current_node_editor_instance.splitter_var_dict
    # Exposed var dict needs deep-copying since it adds a splitter_id entry to the input dict
    _splitter_panel.exposed_var_dict = deepcopy(_current_node_editor_instance.var_dict)

    # Delete the registry of var selectable
    dpg.delete_item(_current_node_editor_instance.item_registry_dict[_var_tag])


def callback_variable_copy(sender, app_data, user_data):
    pass


def callback_variable_cut(sender, app_data, user_data):
    pass


def callback_variable_duplicate(sender, app_data, user_data):
    pass
