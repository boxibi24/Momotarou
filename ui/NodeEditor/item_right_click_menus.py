import dearpygui.dearpygui as dpg
from ui.NodeEditor.node_utils import delete_selected_node
from copy import deepcopy


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
    _event_node_tag = user_data[0]
    _master_node_editor_instance = user_data[1]
    _master_node_editor_instance.callback_compile_current_node_graph(sender)
    _master_node_editor_instance.subprocess_execution_event(_event_node_tag)


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
            dpg.add_button(label="OK", width=75, callback=callback_delete_event,
                           user_data=(user_data, _modal_window))
            dpg.add_button(label="Cancel", width=75, callback=lambda: dpg.delete_item(_modal_window))


def callback_delete_event(sender, app_data, user_data):
    # Delete the modal window first
    dpg.delete_item(user_data[1])
    _event_tag = user_data[0][0]
    _master_node_editor_instance = user_data[0][1]
    _current_node_editor_instance = _master_node_editor_instance.current_node_editor_instance
    _splitter_panel = _current_node_editor_instance.splitter_panel

    _event_name = _current_node_editor_instance.event_dict[_event_tag]['name'][0]

    for node in _current_node_editor_instance.node_instance_dict.values():
        if 'Event ' + _event_name == node.node_label:
            delete_selected_node(_master_node_editor_instance, node.id)
            break
    # Delete event from the event dicts already performed in the deletion function

    # Refresh all UI elements to reflect var deletion
    # First refresh detail panel
    _master_node_editor_instance.detail_panel.refresh_ui()
    # Refresh splitter items already performed in the deletion function
    # Delete the registry of var selectable
    _current_node_editor_instance.delete_item_registry(_event_tag)


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
    _master_node_editor_instance = user_data[1]
    _current_node_editor_instance = _master_node_editor_instance.current_node_editor_instance
    _found_var_node_instance = False
    _var_tag = user_data[0]
    _var_name = _current_node_editor_instance.var_dict[_var_tag]['name'][0]
    # Find first Get/Set node instances in current node graph, if found re-confirm with user for node replacement
    for node in _current_node_editor_instance.node_instance_dict.values():
        if node.node_label == 'Set ' + _var_name or node.node_label == 'Get ' + _var_name:
            _found_var_node_instance = True
            break

    if _found_var_node_instance:
        _mid_widget_pos = [int(dpg.get_viewport_width() / 2.5), int(dpg.get_viewport_height() / 2.5)]
        with dpg.window(modal=True, label='Delete Variable',
                        pos=_mid_widget_pos) as _modal_window:
            dpg.add_text("Delete variable will delete all node instances of this variable!\nThis operation cannot be "
                         "undone!")
            with dpg.group(horizontal=True):
                dpg.add_button(label="OK", width=75, callback=callback_variable_delete,
                               user_data=(user_data, _modal_window))
                dpg.add_button(label="Cancel", width=75, callback=lambda: dpg.delete_item(_modal_window))
    else:
        delete_var_dict_entry(_master_node_editor_instance, _var_tag)


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

    delete_var_dict_entry(_master_node_editor_instance, _var_tag)


def delete_var_dict_entry(master_inst, var_tag):
    _master_node_editor_instance = master_inst
    _current_node_editor_instance = _master_node_editor_instance.current_node_editor_instance
    _splitter_panel = _current_node_editor_instance.splitter_panel
    _var_tag = var_tag
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
    _current_node_editor_instance.delete_item_registry(_var_tag)


def callback_variable_copy(sender, app_data, user_data):
    pass


def callback_variable_cut(sender, app_data, user_data):
    pass


def callback_variable_duplicate(sender, app_data, user_data):
    pass


def tab_right_click_menu(sender, app_data, user_data):
    with dpg.window(
        popup=True,
        autosize=True,
        no_move=True,
        no_open_over_existing_popup=True,
        no_saved_settings=True,
        max_size=[200, 200],
        min_size=[10, 10]
    ):
        dpg.add_selectable(label='Rename', callback=callback_tab_ask_name, user_data=user_data)


def callback_tab_ask_name(sender, app_data, user_data, is_retry=False):
    _tab_name_reference = user_data[0]
    _node_editor_tab_dict = user_data[1]
    _mid_widget_pos = [int(dpg.get_viewport_width() / 2.5), int(dpg.get_viewport_height() / 2.5)]
    with dpg.window(label='Rename tab',
                    pos=_mid_widget_pos, min_size=[10, 10], no_resize=True) as _modal_window:
        with dpg.group(horizontal=True):
            dpg.add_text("New tab name: ")
            dpg.add_input_text(width=200, callback=callback_rename_tab,
                               on_enter=True, user_data=(_modal_window, _tab_name_reference, _node_editor_tab_dict),
                               hint='Input and press "Enter" to apply')
        if is_retry:
            dpg.add_text('Name existed, please retry another name!', color=(204, 51, 0, 255))


def callback_rename_tab(sender, app_data, user_data):
    # delete the modal window
    dpg.delete_item(user_data[0])
    _new_tab_name = app_data
    _tab_name_reference = user_data[1]
    _old_tab_name = _tab_name_reference[0]
    _node_editor_tab_dict = user_data[2]
    _tab_id = _node_editor_tab_dict[_old_tab_name]['id']
    if _node_editor_tab_dict.get(_new_tab_name, None) is not None:
        return callback_tab_ask_name(sender, app_data, user_data=(_tab_name_reference, _node_editor_tab_dict),
                                     is_retry=True)
    # Update new name to tab name reference
    _tab_name_reference[0] = _new_tab_name
    # Rename the tag UI element
    dpg.configure_item(_tab_id, label=_new_tab_name)
    # Update new name to the stored dict for tabs
    _node_editor_instance = _node_editor_tab_dict[_old_tab_name]['node_editor_instance']
    _node_editor_tab_dict.pop(_old_tab_name)
    _node_editor_tab_dict.update({_new_tab_name: {
        'node_editor_instance': _node_editor_instance,
        'id': _tab_id
    }})
