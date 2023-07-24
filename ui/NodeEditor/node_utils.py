import dearpygui.dearpygui as dpg
from ui.NodeEditor.classes.node import NodeTypeFlag
from ui.NodeEditor.utils import sort_data_link_dict, sort_flow_link_dict


def delete_selected_node(node_editor, node_id=None):
    if node_id is None:
        # Get item ID from the first selected node
        _item_id = dpg.get_selected_nodes(node_editor.current_node_editor_instance.id)[0]
    else:  # If specified node id, use it instead
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
