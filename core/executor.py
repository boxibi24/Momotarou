import logging
from time import perf_counter
from core.enum_types import NodeTypeFlag, PinMetaType, OutputPinType
from core.utils import create_queueHandler_logger
# from core.data_loader import nodes_data, events_data, vars_data
import dearpygui.dearpygui as dpg
import argparse
from core.enum_types import PinMetaType, NodeTypeFlag
from importlib import import_module
from copy import deepcopy
from core.utils import extract_var_name_from_node_info, dpg_get_value


logger = logging.getLogger('')
is_debug_mode = False


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
    _load_nodes_data(json_dict)
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


def _load_nodes_data(json_dict: dict):
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


def _get_source_node_and_pin_index_dataLinked_to_pin(pin_info: dict) -> tuple[int, int]:
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


def _get_source_node_index_in_data_link(data_link: dict) -> tuple[int, int]:
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
        internal_data_reference['var_value'][0] = dpg_get_value(var_info['user_input_box_id'])


def _get_following_exec_node_and_update_connection_data(node_index: int) -> list[int]:
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


def _get_destination_node_and_pin_index_flowLinked_to_pin(pin_info: dict) -> tuple[int, int]:
    flow_link = _get_flow_link_connected_to_source_pin(pin_info['uuid'])
    if flow_link is None:
        return -1, -1
    destination_node_index, destination_pin_index = _get_destination_node_index_in_flow_link(flow_link)
    if not destination_node_index:
        raise Exception(f'Could not find destination node info from {flow_link}')
    return destination_node_index, destination_pin_index


def _get_flow_link_connected_to_source_pin(source_pin_id):
    for flow_link in flow_link_list:
        if flow_link[0] == source_pin_id:
            return flow_link


def _get_destination_node_index_in_flow_link(flow_link: dict) -> tuple[int, int]:
    for destination_node_index, destination_node_info in enumerate(node_list):
        for destination_pin_index, pin_info in enumerate(destination_node_info['pins']):
            if pin_info['uuid'] == flow_link[1]:
                return destination_node_index, destination_pin_index


def _update_pin_connected_to_following_node(this_pin_info: dict, following_node_uuid: str):
    this_pin_info.update({'is_connected': True,
                          'connected_to_node': following_node_uuid})


def _get_node_uuid_from_index(node_index: int) -> str:
    return node_list[node_index]['uuid']



def setup_executor_logger(logger_queue, debug_mode: bool):
    global logger, is_debug_mode
    is_debug_mode = debug_mode
    logger = create_queueHandler_logger(__name__, logger_queue, is_debug_mode)


def execute_event(event_node_tag: str, ) -> tuple[int, str]:
    # Perform initial cleanup
    preprocess_execute_event()
    # Start the debug timer
    t1_start = 0
    if logger.level == logging.DEBUG:
        t1_start = perf_counter()

    logger.info(f'**** Exec event : {event_node_tag} ****')
    # Get first node instance that is connected to this user_data node
    current_node_tag = events_data.get(event_node_tag, None)
    if not current_node_tag:
        logger.error('Cannot find the event, this could be due to the event node not connecting to anything!')
        return 0, ''
    # This will propagate the flow chain until it meets the end (unconnected Exec out)
    anchors = []
    if anchors:
        anchors.clear()
    forward_propagate_flow(current_node_tag, anchors)
    flow_control_redirect(anchors)
    logger.info(f'**** Event {event_node_tag} finished ****')
    # Stop timer and output elapsed time
    if logger.level == logging.DEBUG:
        t1_stop = perf_counter()
        logger.debug(f"Elapsed time for the event {event_node_tag}: {t1_stop - t1_start} ")
    return 1, ''


def preprocess_execute_event():
    # Reset all nodes' is_executed flags to False and set them to dirty
    for node_uuid in nodes_data.keys():
        nodes_data[node_uuid]['is_dirty'] = True
        nodes_data[node_uuid]['is_executed'] = False


def _determine_var_value():
    """
    Reset every vars' value to None if it's not exposed, else get from user input box

    :return:
    """
    for var_info in vars_data.values():
        if var_info['is_exposed'][0] is False:
            var_info['value'][0] = None
        else:
            user_input_value = dpg.get_value(var_info['user_input_box_id'])
            var_info['value'][0] = user_input_value


def flow_control_redirect(anchors: list):
    if not anchors:
        return 0
    for anchor in anchors:
        sub_anchors = []
        if sub_anchors:
            sub_anchors.clear()
        forward_propagate_flow(anchor, sub_anchors)
        if sub_anchors:
            flow_control_redirect(sub_anchors)


def forward_propagate_flow(current_node_tag: str, anchors: list):
    current_node_info = nodes_data[current_node_tag]
    if is_debug_mode:
        t1_start = perf_counter()
        current_node_elapsed_time = compute_node(current_node_tag)
        t1_stop = perf_counter()
        logger.debug(f"**** Executing {current_node_tag} ****")
        logger.debug(f"Compute time: {current_node_elapsed_time}")
        backward_propagate_time = t1_stop - t1_start - current_node_elapsed_time
        logger.debug(f"Time to backward propagate: {backward_propagate_time}")
    else:
        compute_node(current_node_tag)
    # Get next node to compute
    next_node_tag = None
    # Branch node got to explicitly decide next_node_tag based on its condition bool value
    if current_node_info['label'] == 'Branch':
        condition = current_node_info['internal_data'].get('Condition', None)
        if condition is None:
            logger.error(f'Can not query condition value for this branch node : {current_node_tag}')
            return -1
        if condition is True or condition == 'True':
            for pin_info in current_node_info['pins']:
                if pin_info['meta_type'] == PinMetaType.FlowOut:
                    if pin_info['is_connected'] and pin_info['label'] == 'True':
                        next_node_tag = pin_info['connected_to_node']
                        break
        else:
            for pin_info in current_node_info['pins']:
                if pin_info['meta_type'] == PinMetaType.FlowOut:
                    if pin_info['is_connected'] and pin_info['label'] == 'False':
                        next_node_tag = pin_info['connected_to_node']
                        break
    # If normal Blueprint node which has only one Exec pin out then next_node_tag is deterministic
    else:
        # First found exec out pin will be the next node (this might be changed later)
        for pin_info in current_node_info['pins']:
            if pin_info['meta_type'] == PinMetaType.FlowOut:
                if pin_info['is_connected']:
                    next_node_tag = pin_info['connected_to_node']
                break
    # If current node is a Set variable value type, then mark all of its get nodes to dirty
    # if 'Set ' in current_node_info['label']:
    #     _var_name = extract_var_name_from_node_info(current_node_info)
    #     # If found declared var, set all its Get nodes to dirty
    #     if _var_name in vars_data.keys():
    #         logger.debug(f'Set {_var_name} triggered all Get {_var_name} nodes dirty propagation!')
    #         for node_tag, node_info in nodes_data.values():
    #             if 'Get ' + _var_name == node_info['label']:
    #                 dirty_propagate(node_tag)
    if current_node_info['type'] == NodeTypeFlag.SetVariable:
        for node_tag, node_info in nodes_data.items():
            if node_info['internal_data'].get('var_name', '') == current_node_info['internal_data']['var_name']:
                dirty_propagate(node_tag)
    # Store anchors point if current node is sequential nodes
    if current_node_info['type'] == NodeTypeFlag.Sequential:
        if current_node_info['label'] == 'Sequence':
            for pin_info in current_node_info['pins']:
                if pin_info['meta_type'] == PinMetaType.FlowOut:
                    if pin_info['is_connected']:
                        anchors.append(pin_info['connected_to_node'])
            return 0
        elif current_node_info['label'] == 'Do N':
            iteration_num = current_node_info['internal_data'].get('N', None)
            if iteration_num and next_node_tag:
                for i in range(iteration_num):
                    anchors.append(next_node_tag)
                return 0
            else:
                logger.error(
                    f'Could not find anchors point upon processing this node: {current_node_tag} ')
    if next_node_tag:
        forward_propagate_flow(next_node_tag, anchors)
    else:
        return 0


def compute_node(node_tag: str):
    current_node_info = nodes_data[node_tag]
    # Blueprint nodes still need to be executed even if it's clean
    if not current_node_info['is_dirty'] and (
        current_node_info['type'] == NodeTypeFlag.Blueprint or current_node_info['type'] == NodeTypeFlag.Sequential):
        compute_internal_output_data(node_tag)
    # If found var set nodes, trigger dirty propagation to all of its Get nodes
    # if current_node_info['type'] == NodeTypeFlag.SetVariable:
    #     for node_tag, node_info in nodes_data.items():
    #         if node_info['internal_data'].get('var_name', '') == current_node_info['internal_data']['var_name']:
    #             dirty_propagate(node_tag)
    # If the nodes (Blueprint is also Pure) is dirty, perform computing output values from inputs
    if current_node_info['is_dirty'] and current_node_info['type'] & NodeTypeFlag.Pure:
        for pin_info in current_node_info['pins']:
            if pin_info['meta_type'] == PinMetaType.DataIn:
                if pin_info['is_connected'] is False:
                    continue
                pre_node_tag = pin_info['connected_to_node']
                pre_node_info = nodes_data[pre_node_tag]
                # Recursively compute every dirty Pure nodes
                if pre_node_info['is_dirty'] and (
                    pre_node_info['type'] == NodeTypeFlag.Pure or pre_node_info['type'] == NodeTypeFlag.GetVariable):
                    compute_node(pre_node_tag)

                # Recursively compute dirty Blueprint nodes even if it's executed
                elif pre_node_info['is_dirty'] and \
                    (pre_node_info['type'] & NodeTypeFlag.Blueprint or
                     pre_node_info['type'] & NodeTypeFlag.Sequential) and \
                    pre_node_info['is_executed']:
                    compute_node(pre_node_tag)

                # Skip computing for dirty Blueprint un-executed nodes (avoid premature execution)
                elif pre_node_info['is_dirty'] and \
                    (pre_node_info['type'] & NodeTypeFlag.Blueprint or
                     pre_node_info['type'] & NodeTypeFlag.Sequential) and \
                    not pre_node_info['is_executed']:
                    pass

                # Clean and executed Blueprint nodes does not need to do anything, ofcourse
                elif not pre_node_info['is_dirty'] and \
                    (pre_node_info['type'] & NodeTypeFlag.Blueprint or
                     pre_node_info['type'] & NodeTypeFlag.Sequential) and \
                    pre_node_info['is_executed']:
                    pass

                # Clean but not executed Blueprint nodes will skip computing (avoid premature execution next
                # time the event triggers)
                elif not pre_node_info['is_dirty'] and \
                    (pre_node_info['type'] & NodeTypeFlag.Blueprint or
                     pre_node_info['type'] & NodeTypeFlag.Sequential) and \
                    not pre_node_info['is_executed']:
                    pass

        # Debug timer starts
        t1_start = 0
        if is_debug_mode:
            t1_start = perf_counter()
        # After getting the clean inputs, perform computing outputs values for this node\
        compute_internal_output_data(node_tag)
        # Debug timer stops
        if is_debug_mode:
            t1_stop = perf_counter()
            elapsed_time = t1_stop - t1_start
            return elapsed_time
        return 0
    # If the current node is already clean, can safely skip computation and use it outputs values right away
    else:
        return 0


def compute_internal_output_data(node_tag: str):
    node_info = nodes_data.get(node_tag, None)
    if node_info is None:
        logger.error(f'Could not find node_data for {node_info}')
        return -1
    for pin_info in node_info['pins']:
        if pin_info['meta_type'] == PinMetaType.DataIn and pin_info['is_connected']:
            # Get preceding pin value and assign it to current one
            preceding_node_info = nodes_data.get(pin_info['connected_to_node'], None)
            connected_to_pin = None
            try:
                connected_to_pin = pin_info['connected_to_pin']
                connected_pin_value = None
                for pre_pin_info in preceding_node_info['pins']:
                    if pre_pin_info['uuid'] == connected_to_pin:
                        try:
                            connected_pin_value = pre_pin_info['value']
                        except KeyError:
                            connected_pin_value = pre_pin_info['default_value']

            except:
                logger.exception(f'Some thing wrong while trying to get value of pin {connected_to_pin}')
                continue
            else:
                pin_info['value'] = connected_pin_value
    # Update internal input data
    for pin_info in node_info['pins']:
        if pin_info['meta_type'] == PinMetaType.DataIn:
            node_info['internal_data'].update({pin_info['label']: pin_info['value']})
    # # Update vars data if exposed
    # if node_info['type'] == NodeTypeFlag.GetVariable and vars_data[extract_var_name_from_node_info(node_info)]['is_exposed']:
    #     node_info['internal_data']['default_var_value'] = \
    #         vars_data[extract_var_name_from_node_info(node_info)]['value'][0]
    # Compute output pin values
    Run = node_info['run']
    Run(node_info['internal_data'])
    # Update the output pins' value with fresh internal data
    for pin_info in node_info['pins']:
        if pin_info['meta_type'] == PinMetaType.DataOut:
            for key, value in node_info['internal_data'].items():
                if key == pin_info['label']:
                    pin_info['value'] = value
                    break
    # After computing for all outputs, mark this node as clean
    node_info['is_dirty'] = False
    # Update back to the master node dict
    nodes_data.update({node_tag: node_info})
    logger.debug(f'Internal input data for node {node_info} has been computed')
    logger.debug(node_info['internal_data'])


def dirty_propagate(node_tag: str):
    current_node_info = nodes_data.get(node_tag, None)
    if current_node_info is None:
        logger.error(f'Could not find node_info for {node_tag}')
        return -1
    if current_node_info['is_dirty']:
        logger.debug(f'Node {node_tag} is already dirty so no propagation needed!')
        return 0
    # Mark current node to 'dirty'
    current_node_info['is_dirty'] = True
    # Propagate to any connected following node to 'dirty' as well
    for pin_info in current_node_info['pins']:
        # if pin type is exec, skip
        if pin_info['type'] == OutputPinType.Exec:
            continue
        # if pin is not connected, skip
        if pin_info.get('is_connected', False) is False:
            continue
        # propagate to the connected node
        dirty_propagate(pin_info['connected_to_node'])


def parse_argument():
    """
    Get flags from command line

    :return:
    """
    args = get_arg()
    _event_tag = args.event

    return _event_tag


def get_arg():
    """
    :return:
    """
    parser = argparse.ArgumentParser(description="RUT core executor")
    parser.add_argument(
        "-event"
    )

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    event_tag = parse_argument()
    execute_event(event_tag)
