import dearpygui.dearpygui as dpg
from ui.NodeEditor.utils import sort_data_link_dict, sort_flow_link_dict
from ui.NodeEditor.classes.node import NodeTypeFlag


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
        node_editor.detail_panel.refresh_ui()

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


def delete_selected_node(node_editor, node_id=None):
    if node_id is None:
        # Get item ID from the first selected node
        _item_id = dpg.get_selected_nodes(node_editor.current_node_editor_instance.id)[0]
    else:   # If specified node id, use it instead
        _item_id = node_id
    # Get the node label and ID from item ID
    node_tag = dpg.get_item_alias(_item_id)
    node_instance = node_editor.current_node_editor_instance.node_instance_dict.get(node_tag, None)

    # If node is of Event Node, also delete them from the splitter
    if node_instance.node_type == NodeTypeFlag.Event:
        node_editor.current_node_editor_instance.splitter_panel.event_dict.pop(node_instance.node_tag)
        node_editor.current_node_editor_instance.splitter_panel.event_dict = node_editor.current_node_editor_instance.splitter_panel.event_dict
        # pop tobe_exported_event_dict entry is handled in the delink function
    # Remove item from node list
    try:
        node_editor.current_node_editor_instance.node_instance_dict.pop(node_tag)
    except KeyError:
        node_editor.current_node_editor_instance.logger.exception(f"Cannot find {node_instance} to remove")
    except:
        node_editor.current_node_editor_instance.logger.exception("Cannot remove item")
    # Link exist in either source or destination
    link_remove_list = []
    if link_remove_list:
        link_remove_list.clear()
    for link in node_editor.current_node_editor_instance.data_link_list:
        source_node_tag = link.source_node_tag
        destination_node_tag = link.target_node_tag
        # Store it on a list of links to iteratively remove it later
        if source_node_tag == node_tag or destination_node_tag == node_tag:
            link_remove_list.append(link)
    for remove_link in link_remove_list:
        try:
            # No need to dpg.delete the links since it is handled internally
            node_editor.current_node_editor_instance.callback_delink('', app_data=remove_link.link_id)
        except ValueError:
            node_editor.current_node_editor_instance.logger.exception(f"Could not find link {remove_link}")
    # Link exist in either source or destination
    link_remove_list = []
    if link_remove_list:
        link_remove_list.clear()
    for link in node_editor.current_node_editor_instance.flow_link_list:
        source_node_tag = link.source_node_tag
        destination_node_tag = link.target_node_tag
        # Store it on a list of links to iteratively remove it later
        if source_node_tag == node_tag or destination_node_tag == node_tag:
            link_remove_list.append(link)
    for remove_link in link_remove_list:
        # Remove flow link instance in the flow_link_list
        try:
            # No need to dpg.delete the links since it is handled internally
            node_editor.current_node_editor_instance.callback_delink('', app_data=remove_link.link_id)
        except ValueError:
            node_editor.current_node_editor_instance.logger.exception(f"Could not find link {remove_link}")

    # Cleanup node info in node_dict
    for node_info in node_editor.current_node_editor_instance.node_dict['nodes']:
        if node_info['id'] == node_tag:
            try:
                node_editor.current_node_editor_instance.node_dict['nodes'].remove(node_info)
                break
            except:
                node_editor.current_node_editor_instance.logger.exception(
                    f"Something wrong removing node info: {node_info}")
                break

    # Delete the node
    dpg.delete_item(node_tag)
    # Sort the connection list
    node_editor.current_node_editor_instance.node_data_link_dict = sort_data_link_dict(
        node_editor.current_node_editor_instance.data_link_list)
    node_editor.current_node_editor_instance.node_flow_link_dict = sort_flow_link_dict(
        node_editor.current_node_editor_instance.flow_link_list)
    node_editor.current_node_editor_instance.logger.info(f'**** Deleted node {node_tag} ****')
    node_editor.current_node_editor_instance.logger.debug(
        f'    node_editor.data_link_list       :    {node_editor.current_node_editor_instance.data_link_list}')
    node_editor.current_node_editor_instance.logger.debug(
        f'    node_editor.flow_link_list       :    {node_editor.current_node_editor_instance.flow_link_list}')
    node_editor.current_node_editor_instance.logger.debug(
        f'    sef.node_data_link_dict  :    {node_editor.current_node_editor_instance.node_data_link_dict}')
    node_editor.current_node_editor_instance.logger.debug(
        f'    node_editor.node_flow_link_dict  :    {node_editor.current_node_editor_instance.node_flow_link_dict}')
