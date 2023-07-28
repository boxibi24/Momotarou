import dearpygui.dearpygui as dpg
from core.enum_type import NodeTypeFlag
from ui.NodeEditor.utils import sort_data_link_dict, sort_flow_link_dict, \
    dpg_get_value, dpg_set_value, json_write_to_file
import traceback
from ui.NodeEditor.classes.link import Link, LinkInfo
from ui.NodeEditor.classes.pin import PinInfo


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
        destination_node_tag = link.destination_node_tag
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
        destination_node_tag = link.destination_node_tag
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
        if node_info['uuid'] == node_tag:
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

    :param in_link_list: pre-processed link list that holds link instances
    :return: simplified link list of [source_pin_tag, destination_pin_tag]
    :rtype: list[list[str, str]]
    """
    out_link_list = []
    for link_instance in in_link_list:
        source_pin_tag = link_instance.source_pin_instance.pin_tag
        destination_pin_tag = link_instance.destination_pin_instance.pin_tag
        out_link_list.append([source_pin_tag, destination_pin_tag])
    return out_link_list


def update_flow_links_to_export_dict(flow_link_list: list, export_dict: dict):
    """
    Replace flow link list with simplified elements

    :param flow_link_list: pre-processed link list that holds link instances
    :param export_dict: reference to the export dict that will be updated with new simplified list
    :return:
    """
    _simplified_flow_link_list = simplify_link_list(flow_link_list)
    export_dict.update({'flows': _simplified_flow_link_list})


def update_data_links_to_export_dict(data_link_list: list, export_dict: dict):
    """
    Replace data link list with simplified elements

    :param data_link_list: pre-processed link list that holds link instances
    :param export_dict:  reference to the export dict that will be updated with new simplified list
    :return:
    """
    _simplified_data_link_list = simplify_link_list(data_link_list)
    export_dict.update({'data_links': _simplified_data_link_list})


def update_pin_values_in_node_dict(node_info):
    """
    Update current pin values to node dict

    :param node_info: reference to the node info
    :return:
    """
    for pin_info in node_info['pins']:
        pin_value = pin_info.get('value', None)
        if pin_value is None:
            continue
        # If source
        pin_info.update({'value': dpg_get_value(pin_info['pin_instance'].value_tag)})


def eliminate_non_primitive_internal_node_data(node_instance):
    """
    Set value to None if found non-primitive type in internal node data

    :param node_instance: instance of the node for inspection
    :return:
    """
    # Clears out complex structs inside nodes' internal_data since pickle can't handle serializing them
    for key in node_instance.internal_data.keys():
        if node_instance.internal_data[key].__class__ in [str, int, float, type(None), list]:
            continue
        node_instance.internal_data[key] = None


def reset_var_values_to_none(var_dict):
    """
    Reset all variables' values to None

    :param var_dict: dictionary of variables info
    :return:
    """
    # Resetting all the vars value to None
    for var_info in var_dict.values():
        var_info['value'][0] = None


def prepare_node_info_for_export(in_dict):
    """
    Remove redundancies and update node's position to reflect current states

    :param dict in_dict: to be exported dict
    :return:
    """
    for node in in_dict['nodes']:
        # Remove redundant entries : node_instance
        node.pop('node_instance')
        # Remove redundant entries : pin_instances
        for pin in node['pins']:
            pin.pop('pin_instance')
        # Update node position
        node['position']['x'], node['position']['y'] = dpg.get_item_pos(node['uuid'])


def save_dict_to_json(in_dict, file_path) -> tuple:
    """
    Save dictionary to JSON file

    :param dict in_dict: to be saved dictionary
    :param str file_path: save file path
    :return: return message
    """
    try:
        json_write_to_file(file_path=file_path, value=in_dict)
    except Exception:
        return 4, traceback.format_exc()
    else:
        return 1, f'exported_dict : {in_dict}'


def add_pin_mapping_entries(imported_node_pins: list, new_node, pin_mapping_dict: dict):
    """
    Add pin mapping entries of imported pin id - newly created pin

    :param list imported_node_pins: node pins info
    :param new_node: newly created node
    :param dict pin_mapping_dict: reference of the pin_mapping dict
    :return:
    """
    # Loop through a list of to-be-imported pins
    for imported_pin in imported_node_pins:
        imported_pin_label = imported_pin['label']
        for added_pin in new_node.pin_list:
            # Get the matching pin id from the newly created pins list of the newly created node
            if imported_pin_label == added_pin['label']:
                pin_mapping_dict.update({imported_pin['uuid']: added_pin['uuid']})
                break


def reapply_imported_pin_value_to_new_node(imported_pin_list, new_node):
    """
    Apply imported pin value to the newly created ones of the node

    :param list imported_pin_list: list of imported pins info
    :param new_node:
    :return:
    """
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


def reconstruct_node_pos_from_imported_info(node_info) -> tuple[float, float]:
    """
    Reconstruct node position from imported info

    :param dict node_info: imported node info
    :return:
    """
    return node_info['position']['x'], node_info['position']['y']


def construct_var_node_label(var_name, is_get_var: bool) -> str:
    """
    Construct variable node name based on whether it is get var or set var type

    :param var_name: name of the variable
    :param is_get_var: True if this node is a Get Var node
    :return: Variable node label
    """
    if is_get_var:
        return 'Get ' + var_name
    else:
        return 'Set ' + var_name


def split_event_name_from_node_label(node_label: str):
    return ' '.join(node_label.split(' ')[1:])


def create_link_object_from_link_info(link_info: LinkInfo):
    link = Link(link_info.source_pin_info.parent_node_tag,
                link_info.source_pin_info.parent_node_instance,
                link_info.source_pin_info.pin_instance,
                link_info.source_pin_info.pin_type,
                link_info.destination_pin_info.parent_node_tag,
                link_info.destination_pin_info.parent_node_instance,
                link_info.destination_pin_info.pin_instance,
                link_info.destination_pin_info.pin_type,
                parent=link_info.source_pin_info.parent_node_instance.parent)
    reflect_new_link_on_connected_pins(link)
    return link


def reflect_new_link_on_connected_pins(link: Link):
    _reflect_new_link_on_source_pin(link)
    _reflect_new_link_on_destination_pin(link)


def _reflect_new_link_on_source_pin(link: Link):
    link.source_pin_instance.is_connected = True
    link.source_pin_instance.connected_link_list.append(link)


def _reflect_new_link_on_destination_pin(link: Link):
    link.destination_pin_instance.is_connected = True
    link.destination_pin_instance.connected_link_list.append(link)



def find_pin_and_construct_pin_info_in_node_list(pin_tag: str, node_list: list):
    """
    Get all pin data

    :param node_list:
    :param pin_tag: pin tag
    :return:
    """
    for node in node_list:
        pin_dict_list = node['pins']
        for pin_dict in pin_dict_list:
            if pin_dict['uuid'] == pin_tag:
                pin_instance = pin_dict['pin_instance']
                pin_type = pin_dict['type']
                parent_node_instance = node['node_instance']
                parent_node_tag = node['uuid']
                return PinInfo(pin_instance, pin_type, parent_node_instance, parent_node_tag)


def construct_link_info_from_source_and_destination_pin_info(source_pin_info, destination_pin_info):
    return LinkInfo(source_pin_info, destination_pin_info)


def is_link_duplicate_in_check_list(link_info: LinkInfo, check_list: list) -> bool:
    for node_link in check_list:
        if link_info.destination_pin_info.pin_instance == node_link.destination_pin_instance:
            return True
    return False


def create_link_object_from_link_info_if_node_unconnected(link_info: LinkInfo):
    if not link_info.source_pin_info.pin_instance.is_connected:
        return create_link_object_from_link_info(link_info)
    else:
        return None


def update_new_link_info(link, to_update_link_list, to_update_event_dict):
    # Update event dict to store target node tag if it's connected to an event node
    if link.source_node_type == NodeTypeFlag.Event:
        to_update_event_dict.update({link.source_pin_info: link.destination_node_tag})
    to_update_link_list.append(link)


def reflect_new_link_to_pins(link):
    set_pins_in_link_to_connected(link)
    add_link_to_pins_connected_link_list(link)


def set_pins_in_link_to_connected(link):
    link.source_pin_instance.is_connected = True
    link.destination_pin_instance.is_connected = True


def add_link_to_pins_connected_link_list(link):
    link.source_pin_instance.connected_link_list.append(link)
    link.destination_pin_instance.connected_link_list.append(link)


def get_node_category_from_import_path(import_path) -> str:
    return import_path.split('.')[1]


def construct_module_name_from_var_action_and_type(var_action: str, var_type: str) -> str:
    return var_action + '_' + var_type.lower() + '_var'


def create_list_from_dict_values(in_dict: dict):
    _node_list = []
    for node in in_dict.values():
        _node_list.append(node)
    return _node_list
