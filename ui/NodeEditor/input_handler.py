import dearpygui.dearpygui as dpg
from ui.NodeEditor.node_utils import delete_selected_node


def add_keyboard_handler_registry(node_editor):
    """
    Add input handler from keyboard
    """
    with dpg.handler_registry(tag='__node_editor_keyboard_handler'):
        # Delete key
        dpg.add_key_press_handler(key=dpg.mvKey_Delete, user_data=node_editor)


def add_mouse_handler_registry(node_editor):
    """
    Add input handler from mouse
    """
    with dpg.handler_registry(tag='__node_editor_mouse_handler'):
        dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Left, user_data=node_editor)
        dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Right, user_data=node_editor)


def event_handler(sender, app_data, user_data):
    """
    Switch cases per input type to handle callback
    """
    input_type = dpg.get_item_info(sender)["type"]
    if input_type == "mvAppItemType::mvKeyDownHandler":
        pass
    elif input_type == "mvAppItemType::mvKeyReleaseHandler":
        pass
    elif input_type == "mvAppItemType::mvKeyPressHandler":
        key_press_handler(user_data)
    elif input_type == "mvAppItemType::mvMouseClickHandler":
        if app_data == dpg.mvMouseButton_Left:  # Left click
            mouse_left_click_handler(user_data)
        elif app_data == dpg.mvMouseButton_Right:  # Right click
            mouse_right_click_handler(user_data)
        elif app_data == dpg.mvMouseButton_Middle:  # Middle mouse click
            pass
    elif input_type == "mvAppItemType::mvMouseDoubleClickHandler":
        pass
    elif input_type == "mvAppItemType::mvMouseDownHandler":
        pass
    elif input_type == "mvAppItemType::mvMouseReleaseHandler":
        pass
    elif input_type == "mvAppItemType::mvMouseWheelHandler":
        pass
    elif input_type == "mvAppItemType::mvMouseMoveHandler":
        pass
    elif input_type == "mvAppItemType::mvMouseDragHandler":
        pass


def mouse_left_click_handler(node_editor):
    selected_node = dpg.get_selected_nodes(node_editor.current_node_editor_instance.id)
    if selected_node:
        node_editor.detail_panel.refresh_ui_with_selected_node_info()

    if dpg.is_key_down(key=dpg.mvKey_Control) and dpg.is_key_down(key=dpg.mvKey_Shift):  # Ctrl + Shift pressed
        pass
    elif dpg.is_key_down(key=dpg.mvKey_Control) and dpg.is_key_down(key=dpg.mvKey_Alt):  # Ctrl + Alt
        pass
    elif dpg.is_key_down(key=dpg.mvKey_Alt) and dpg.is_key_down(key=dpg.mvKey_Shift):  # Alt + Shift
        pass
    elif dpg.is_key_down(key=dpg.mvKey_Shift):  # Shift pressed
        pass
    elif dpg.is_key_down(key=dpg.mvKey_Alt):  # Alt pressed
        selected_links = dpg.get_selected_links(node_editor.current_node_editor_instance.id)
        if selected_links:
            node_editor.current_node_editor_instance.callback_delink('', selected_links[0])
    elif dpg.is_key_down(key=dpg.mvKey_Control):  # Ctrl pressed
        pass
    else:  # Normal click
        selected_nodes = dpg.get_selected_nodes(node_editor.current_node_editor_instance.id)
        cache_last_selected_node_pos(node_editor, selected_nodes)
        if not is_cursor_inside_node_graph(node_editor.node_editor_bb) and selected_nodes:
            dpg.clear_selected_nodes(node_editor.current_node_editor_instance.id)


def mouse_right_click_handler(node_editor):
    if dpg.is_key_down(key=dpg.mvKey_Control) and dpg.is_key_down(key=dpg.mvKey_Shift):  # Ctrl + Shift pressed
        pass
    elif dpg.is_key_down(key=dpg.mvKey_Control) and dpg.is_key_down(key=dpg.mvKey_Alt):  # Ctrl + Alt
        pass
    elif dpg.is_key_down(key=dpg.mvKey_Alt) and dpg.is_key_down(key=dpg.mvKey_Shift):  # Alt + Shift
        pass
    elif dpg.is_key_down(key=dpg.mvKey_Shift):  # Shift pressed
        pass
    elif dpg.is_key_down(key=dpg.mvKey_Alt):  # Alt pressed
        pass
    elif dpg.is_key_down(key=dpg.mvKey_Control):  # Ctrl pressed
        pass
    else:  # Normal click
        selected_nodes = dpg.get_selected_nodes(node_editor.current_node_editor_instance.id)
        # Show node selection list
        if not selected_nodes and \
            is_cursor_inside_node_graph(node_editor.node_editor_bb):
            node_editor.right_click_menu.show = True

        if not is_cursor_inside_node_graph(node_editor.node_editor_bb) and selected_nodes:
            dpg.clear_selected_nodes(node_editor.current_node_editor_instance.id)


def is_cursor_inside_node_graph(ng_bb) -> bool:
    """
    Checks if the cursor is inside the boundary of a node graph
    """
    mouse_cursor_pos = dpg.get_mouse_pos(local=False)
    if (mouse_cursor_pos[0] - ng_bb[0][0] > 0) and (mouse_cursor_pos[0] - ng_bb[1][0] < 0):
        if (mouse_cursor_pos[1] - ng_bb[0][1] > 0) and (mouse_cursor_pos[1] - ng_bb[1][1] < 0):
            is_inside = True
        else:
            is_inside = False
    else:
        is_inside = False
    return is_inside


def key_press_handler(node_editor):
    if dpg.is_key_pressed(dpg.mvKey_Delete):
        # Delete selected nodes
        selected_node_list_len = len(dpg.get_selected_nodes(node_editor.current_node_editor_instance.id))
        if selected_node_list_len > 0:
            for i in range(selected_node_list_len):
                delete_selected_node(node_editor)


def cache_last_selected_node_pos(node_editor, selected_nodes):
    # Note: I tried finding the absolute pos of cursor relatively in Node Editor but failed,
    # This is the best method I can think of
    if selected_nodes:
        node_editor.current_node_editor_instance.last_pos = dpg.get_item_pos(selected_nodes[0])
