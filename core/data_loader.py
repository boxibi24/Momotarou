from core.enum_types import PinMetaType, NodeTypeFlag
from importlib import import_module
from copy import deepcopy
from core.utils import extract_var_name_from_node_info, dpg_get_value, is_var_type_of_string_based
from typing import Tuple, List
import dearpygui.dearpygui as dpg
import re
from tkinter import Tk, messagebox
from traceback import format_exc

nodes_data = {}
vars_data = {}
events_data = {}
node_list = []
data_link_list = []
flow_link_list = []


def refresh_core_data_with_json_dict(json_dict: dict):
    _clear_all_data()
    _load_json_node_dict(json_dict)
    _load_events_data(json_dict)
    _load_data_link_list(json_dict)
    _load_flow_link_list(json_dict)
    _load_vars_data(json_dict)
    try:
        _load_nodes_data()
    except ValueError:
        return 4, format_exc()
    return 1, ''


def _clear_all_data():
    global nodes_data, vars_data, events_data, node_list, data_link_list, flow_link_list
    nodes_data.clear()
    vars_data.clear()
    events_data.clear()
    node_list.clear()
    data_link_list.clear()
    flow_link_list.clear()


def _load_json_node_dict(json_dict: dict):
    global node_list
    node_list = json_dict['nodes']


def _load_events_data(json_dict: dict):
    global events_data
    events_data.update(json_dict['events'])


def _load_data_link_list(json_dict: dict):
    global data_link_list
    data_link_list = json_dict['data_links']


def _load_flow_link_list(json_dict: dict):
    global flow_link_list
    flow_link_list = json_dict['flows']


def _load_vars_data(json_dict: dict):
    global vars_data
    vars_data.update(_restructure_imported_vars_data(json_dict))


def _restructure_imported_vars_data(json_dict: dict) -> dict:
    """
    Replace var tag with var name as dictionary keys
    :param json_dict: imported data
    :return:
    """
    restructured_vars_dict = {}
    for key, vars_info in json_dict['vars'].items():
        _name_removed_vars_info_dict = deepcopy(vars_info)
        _name_removed_vars_info_dict.pop('name')
        restructured_vars_dict.update({vars_info['name'][0]: _name_removed_vars_info_dict})
    return restructured_vars_dict


def _load_nodes_data():
    for first_exec_node_tag in list(events_data.values()):
        for node_index, node_info in enumerate(node_list):
            if node_info['uuid'] == first_exec_node_tag:
                _propagate_construct_nodes(node_index)


def _propagate_construct_nodes(node_index: int):
    _propagate_preceding_nodes_connection_info(node_index)
    following_node_index_list = _get_following_exec_node_and_update_connection_data(node_index)
    for following_node_index in following_node_index_list:
        _propagate_construct_nodes(following_node_index)


def _propagate_preceding_nodes_connection_info(node_index: int):
    for pin_index, pin_info in enumerate(_get_pin_list_of_node(node_index)):
        if not _is_data_input_pin_type(pin_info['meta_type']):
            continue
        preceding_node_index, preceding_pin_index = _get_source_node_and_pin_index_dataLinked_to_pin(
            _get_pin_info_in_node_list(node_index, pin_index))
        if preceding_node_index == -1:
            _set_pin_unconnected(node_index, pin_index)
            continue
        _update_connected_data_to_pins_couple(node_index, preceding_node_index, pin_index, preceding_pin_index)
        if _is_process_node(preceding_node_index):
            continue
        _propagate_preceding_nodes_connection_info(preceding_node_index)
    _construct_and_update_node_info(node_index)


def _is_data_input_pin_type(pin_type: PinMetaType) -> bool:
    if pin_type == PinMetaType.DataIn:
        return True
    return False


def _get_source_node_and_pin_index_dataLinked_to_pin(pin_info: dict) -> Tuple[int, int]:
    data_link = _get_data_link_connected_to_destination_pin(pin_info['uuid'])
    if not data_link:
        return -1, -1
    source_node_index, source_pin_index = _get_source_node_index_in_data_link(data_link)
    if source_node_index is None:
        raise Exception(f'Could not find source node info from {data_link}')
    return source_node_index, source_pin_index


def _get_data_link_connected_to_destination_pin(destination_pin_id):
    for data_link in data_link_list:
        if data_link[1] == destination_pin_id:
            return data_link


def _get_source_node_index_in_data_link(data_link: dict) -> Tuple[int, int]:
    for source_node_index, source_node_info in enumerate(node_list):
        for source_pin_index, pin_info in enumerate(source_node_info['pins']):
            if pin_info['uuid'] == data_link[0]:
                return source_node_index, source_pin_index


def _update_connected_data_to_pins_couple(source_node_index: int, destination_node_index: int,
                                          source_pin_index: int, destination_pin_index: int):
    _update_pin_connected_status_from_one_pin_to_another(
        _get_pin_info_in_node_list(source_node_index, source_pin_index),
        _get_pin_uuid_from_node_and_pin_index(destination_node_index, destination_pin_index),
        _get_node_uuid_from_index(destination_node_index))
    _update_pin_connected_status_from_one_pin_to_another(
        _get_pin_info_in_node_list(destination_node_index, destination_pin_index),
        _get_pin_uuid_from_node_and_pin_index(source_node_index, source_pin_index),
        _get_node_uuid_from_index(source_node_index))


def _update_pin_connected_status_from_one_pin_to_another(this_pin_info: dict, targeted_pin_uuid: str,
                                                         targeted_node_uuid: str):
    this_pin_info.update({'is_connected': True,
                          'connected_to_pin': targeted_pin_uuid,
                          'connected_to_node': targeted_node_uuid})


def _get_pin_info_in_node_list(node_index: int, pin_index: int) -> dict:
    return _get_pin_list_of_node(node_index)[pin_index]


def _get_pin_list_of_node(node_index: int) -> list:
    return node_list[node_index]['pins']


def _get_pin_uuid_from_node_and_pin_index(node_index: int, pin_index: int) -> str:
    return node_list[node_index]['pins'][pin_index]['uuid']


def _is_process_node(node_index: int) -> bool:
    if node_list[node_index]['type'] & NodeTypeFlag.Exec:
        return True
    return False


def _set_pin_unconnected(node_index: int, pin_index: int):
    node_list[node_index]['pins'][pin_index].update({'is_connected': False})


def _construct_and_update_node_info(node_index: int):
    global nodes_data
    node_data = node_list[node_index]
    module = import_module(node_data['import_path'])
    node_run_func = getattr(module, 'Node').run
    node_internal_data = _construct_node_internal_data(node_index)
    nodes_data.update({node_data['uuid']: {
        'label': node_data['label'],
        'pins': node_data['pins'],
        'type': node_data['type'],
        'run': node_run_func,
        'is_dirty': True,
        'is_executed': False,
        'internal_data': node_internal_data
    }})


def _construct_node_internal_data(node_index: int) -> dict:
    internal_data = {}
    node_info = node_list[node_index]
    _update_standard_node_internal_data(internal_data, node_info['pins'])
    if node_list[node_index]['type'] & NodeTypeFlag.Variable:
        _update_var_node_internal_data(internal_data, extract_var_name_from_node_info(node_info))
    return internal_data


def _update_standard_node_internal_data(internal_data_reference: dict, pin_list: list):
    for pin_info in pin_list:
        if pin_info['meta_type'] == PinMetaType.DataIn:
            internal_data_reference.update({pin_info['label']: pin_info['value']})


def _update_var_node_internal_data(internal_data_reference: dict, var_name: str):
    var_info = vars_data[var_name]
    internal_data_reference.update({'var_value': var_info['value'],
                                    'default_var_value': var_info['default_value'],
                                    'var_name': var_name})
    if var_info['is_exposed'][0]:
        # internal_data_reference['var_value'][0] = dpg_get_value(var_info['user_input_box_tag'])
        internal_data_reference['var_value'][0] = _get_var_value_from_user_input_and_terminate_if_regex_fails(var_name)


def _get_var_value_from_user_input_and_terminate_if_regex_fails(var_name: str):
    """
    Reset every vars' value to None if it's not exposed, else get from user input box

    :return:
    """
    var_info = vars_data[var_name]
    user_input_value = dpg.get_value(var_info['user_input_box_tag'])
    if is_var_type_of_string_based(var_info['type'][0]):
        if not _is_full_match_regex(user_input_value, var_info['regex'][0]):
            warn_user_of_incorrect_input_and_terminate(var_name)
    return user_input_value


def _is_full_match_regex(to_check_string: str, regex: str) -> bool:
    pattern = re.compile(regex)
    match_object = re.fullmatch(pattern, to_check_string)
    if match_object is not None:
        return True
    return False


def warn_user_of_incorrect_input_and_terminate(var_name: str):
    root = Tk()
    root.withdraw()
    messagebox.showerror('Execution Error', f'Incorrect input value for {var_name}')
    root.destroy()
    raise ValueError(f'Incorrect input value for {var_name}')


def _get_following_exec_node_and_update_connection_data(node_index: int) -> List[int]:
    following_node_index_list = []
    for pin_index, pin_info in enumerate(_get_pin_list_of_node(node_index)):
        if pin_info['meta_type'] != PinMetaType.FlowOut:
            continue
        following_node_index, following_pin_index = _get_destination_node_and_pin_index_flowLinked_to_pin(pin_info)
        if following_node_index == -1:
            _set_pin_unconnected(node_index, pin_index)
            continue
        _update_pin_connected_to_following_node(pin_info, _get_node_uuid_from_index(following_node_index))
        following_node_index_list.append(following_node_index)
    return following_node_index_list


def _get_destination_node_and_pin_index_flowLinked_to_pin(pin_info: dict) -> Tuple[int, int]:
    flow_link = _get_flow_link_connected_to_source_pin(pin_info['uuid'])
    if flow_link is None:
        return -1, -1
    destination_node_index, destination_pin_index = _get_destination_node_index_in_flow_link(flow_link)
    if destination_node_index is None:
        raise Exception(f'Could not find destination node info from {flow_link}')
    return destination_node_index, destination_pin_index


def _get_flow_link_connected_to_source_pin(source_pin_id):
    for flow_link in flow_link_list:
        if flow_link[0] == source_pin_id:
            return flow_link


def _get_destination_node_index_in_flow_link(flow_link: dict) -> Tuple[int, int]:
    for destination_node_index, destination_node_info in enumerate(node_list):
        for destination_pin_index, pin_info in enumerate(destination_node_info['pins']):
            if pin_info['uuid'] == flow_link[1]:
                return destination_node_index, destination_pin_index


def _update_pin_connected_to_following_node(this_pin_info: dict, following_node_uuid: str):
    this_pin_info.update({'is_connected': True,
                          'connected_to_node': following_node_uuid})


def _get_node_uuid_from_index(node_index: int) -> str:
    return node_list[node_index]['uuid']
