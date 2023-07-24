import dearpygui.dearpygui as dpg
from ui.NodeEditor.classes.node import NodeTypeFlag
from ui.NodeEditor.utils import sort_data_link_dict, sort_flow_link_dict, \
    dpg_get_value, dpg_set_value, json_write_to_file
import traceback


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


def simplify_link_list(in_link_list):
    """
    Replaces instances in link list with their tags
    """
    out_link_list = []
    for link_instance in in_link_list:
        source_pin_tag = link_instance.source_pin_instance.pin_tag
        target_pin_tag = link_instance.target_pin_instance.pin_tag
        out_link_list.append([source_pin_tag, target_pin_tag])
    return out_link_list


def update_pin_values_in_node_dict(node_info):
    """
    Update current pin values to node dict
    """
    for pin_info in node_info['pins']:
        pin_value = pin_info.get('value', None)
        if pin_value is None:
            continue
        # If source
        pin_info.update({'value': dpg_get_value(pin_info['pin_instance'].value_tag)})


def update_flow_links_to_export_dict(flow_link_list: list, export_dict: dict):
    """
    Replace flow link lists with elements consist of the [source_pin_tag, target_pin_tag]
    """
    _simplified_flow_link_list = simplify_link_list(flow_link_list)
    export_dict.update({'flows': _simplified_flow_link_list})


def update_data_links_to_export_dict(data_link_list: list, export_dict: dict):
    """
    Replace flow link lists with elements consist of the [source_pin_tag, target_pin_tag]
    """
    _simplified_data_link_list = simplify_link_list(data_link_list)
    export_dict.update({'data_links': _simplified_data_link_list})


def eliminate_non_primitive_internal_node_data(node_instance):
    """
    Set value to None if found non-primitive type in internal node data
    """
    # Clears out complex structs inside nodes' internal_data since pickle can't handle serializing them
    for key in node_instance.internal_data.keys():
        if node_instance.internal_data[key].__class__ in [str, int, float, type(None), list]:
            continue
        node_instance.internal_data[key] = None


def reset_var_values_to_none(var_dict):
    # Resetting all the vars value to None
    for var_info in var_dict.values():
        var_info['value'][0] = None


def remove_export_dict_redundancies(in_dict):
    for node in in_dict['nodes']:
        # Remove redundant entries : node_instance
        node.pop('node_instance')
        # Remove redundant entries : pin_instances
        for pin in node['pins']:
            pin.pop('pin_instance')
        # Update node position
        node['position']['x'], node['position']['y'] = dpg.get_item_pos(node['id'])


def save_dict_to_json(in_dict, file_path) -> tuple:
    try:
        json_write_to_file(file_path=file_path, value=in_dict)
    except Exception:
        return 4, traceback.format_exc()
    else:
        return 1, f'exported_dict : {in_dict}'


def update_pin_mapping_entry_with_imported_node_pin(imported_node_pins: list, new_node, pin_mapping_dict: dict):
    # Loop through a list of to-be-imported pins
    for imported_pin in imported_node_pins:
        imported_pin_label = imported_pin['label']
        for added_pin in new_node.pin_list:
            # Get the matching pin id from the newly created pins list of the newly created node
            if imported_pin_label == added_pin['label']:
                pin_mapping_dict.update({imported_pin['id']: added_pin['id']})
                break


def reapply_imported_pin_value_to_new_node(imported_pin_list, new_node):
    for new_pin_info in new_node.pin_list:
        # if this new pin does not require value then skip
        if new_pin_info.get('value', None):
            continue
        # Get value from imported pin info that matches label:
        imported_value = None
        for imported_pin_info in imported_pin_list:
            if imported_pin_info['label'] == new_pin_info['label']:
                imported_value = imported_pin_info.get('value', None)
        if imported_value is None:
            continue
        # Set the imported value to this new pin's value
        dpg_set_value(new_pin_info['pin_instance'].value_tag, imported_value)

