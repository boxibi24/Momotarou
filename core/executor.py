import logging
from time import perf_counter
from core.enum_types import OutputPinType
from core.utils import create_queueHandler_logger, start_timer, stop_timer_and_get_elapsed_time
from core.data_loader import nodes_data, events_data, vars_data
import dearpygui.dearpygui as dpg
from core.enum_types import PinMetaType, NodeTypeFlag
from pprint import pprint

logger = logging.getLogger('')
is_debug_mode = False


def setup_executor_logger(logger_queue, debug_mode: bool):
    global logger, is_debug_mode
    is_debug_mode = debug_mode
    logger = create_queueHandler_logger(__name__, logger_queue, is_debug_mode)


def execute_event(event_node_tag: str, ) -> tuple[int, str]:
    preprocess_execute_event()
    start_timer()
    logger.info(f'**** Exec event : {event_node_tag} ****')
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
    logger.debug(f"Elapsed time for the event {event_node_tag}: {stop_timer_and_get_elapsed_time()} ")
    logger.info(f'**** Event {event_node_tag} finished ****')
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
        if anchor['this_node_label'] == 'Do N':
            _set_for_loop_index_value(anchor['this_node_tag'], anchor['index'])
        elif anchor['this_node_label'] == 'For each loop':
            _set_for_each_index_and_element(anchor['this_node_tag'], anchor['index'])
        sub_anchors = []
        if sub_anchors:
            sub_anchors.clear()
        forward_propagate_flow(anchor['next_node_tag'], sub_anchors)
        if sub_anchors:
            flow_control_redirect(sub_anchors)


def _set_for_each_index_and_element(node_tag: str, index: int):
    if not _is_completed_body(node_tag, index):
        _set_for_loop_index_value(node_tag, index)
        _set_for_loop_element_value(node_tag, index)


def _is_completed_body(node_tag: str, index: int) -> bool:
    return index > len(nodes_data[node_tag]['internal_data']['String Array']) - 1


def _set_for_loop_index_value(node_tag: str, value: int):
    pin_info = _find_index_pin_info_in_for_loop_node(node_tag)
    pin_info['value'] = value
    dirty_propagate(node_tag)


def _find_index_pin_info_in_for_loop_node(node_tag) -> dict:
    for pin_info in nodes_data[node_tag]['pins']:
        if 'Index' in pin_info['label']:
            return pin_info


def _set_for_loop_element_value(node_tag: str, element_index: int):
    pin_info = _find_element_pin_info_for_each_node(node_tag)
    pin_info['value'] = nodes_data[node_tag]['internal_data']['String Array'][element_index]
    dirty_propagate(node_tag)


def _find_element_pin_info_for_each_node(node_tag: str) -> dict:
    for pin_info in nodes_data[node_tag]['pins']:
        if pin_info['label'] == 'Array Str Element':
            return pin_info


def forward_propagate_flow(current_node_tag: str, anchors: list):
    compute_node_with_timer(current_node_tag)
    current_node_info = nodes_data[current_node_tag]
    if current_node_info['type'] == NodeTypeFlag.Sequential:
        update_anchors(current_node_info, current_node_tag, anchors)
    next_node_tag = _get_next_node_tag(current_node_info)
    if next_node_tag:
        forward_propagate_flow(next_node_tag, anchors)


def compute_node_with_timer(node_tag: str):
    t1_start = perf_counter()
    current_node_elapsed_time = compute_node(node_tag)
    t1_stop = perf_counter()
    logger.debug(f"**** Executing {node_tag} ****")
    logger.debug(f"Compute time: {current_node_elapsed_time}")
    backward_propagate_time = t1_stop - t1_start - current_node_elapsed_time
    logger.debug(f"Time to backward propagate: {backward_propagate_time}")


def compute_node(node_tag: str):
    current_node_info = nodes_data[node_tag]
    # Blueprint nodes still need to be executed even if it's clean
    if not current_node_info['is_dirty'] and (
        current_node_info['type'] == NodeTypeFlag.Blueprint or current_node_info['type'] == NodeTypeFlag.Sequential):
        compute_internal_output_data(node_tag)
    # If the nodes (Blueprint is also Pure) is dirty, perform computing output values from inputs
    if current_node_info['is_dirty'] and current_node_info['type'] & NodeTypeFlag.Pure:
        for pin_info in current_node_info['pins']:
            pre_node_tag = _get_pre_node_tag_if_should_backward_propagate(pin_info)
            if pre_node_tag not in [None, '']:
                compute_node(pre_node_tag)
        start_timer()
        compute_internal_output_data(node_tag)
        return stop_timer_and_get_elapsed_time()
    # If the current node is already clean, can safely skip computation and use it outputs values right away
    else:
        return 0


def _get_pre_node_tag_if_should_backward_propagate(pin_info: dict) -> str:
    if pin_info['meta_type'] == PinMetaType.DataIn:
        if pin_info['is_connected'] is False:
            return ''
        pre_node_tag = pin_info['connected_to_node']
        pre_node_info = nodes_data[pre_node_tag]
        if _should_skip_backward_compute_node(pre_node_info):
            return ''
        # Recursively compute every dirty Pure nodes
        elif _is_dirty_pure_node(pre_node_info):
            return pre_node_tag
        # Recursively compute dirty Blueprint nodes even if it's executed
        elif _is_dirty_executed_blueprint_node(pre_node_info):
            return pre_node_tag


def compute_internal_output_data(node_tag: str):
    node_info = nodes_data[node_tag]
    _set_pins_value_from_connected_preceding_pin_value(node_info)
    _update_internal_input_data(node_info)
    _run_node_and_set_to_clean(node_info)
    _update_pins_value_in_node_info(node_info)
    nodes_data.update({node_tag: node_info})


def _set_pins_value_from_connected_preceding_pin_value(node_info: dict):
    for pin_info in node_info['pins']:
        if pin_info['meta_type'] == PinMetaType.DataIn and pin_info['is_connected']:
            preceding_node_info = nodes_data[pin_info['connected_to_node']]
            pre_pin_info = _find_pin_info_in_pin_list_match_uuid(preceding_node_info,
                                                                 pin_info['connected_to_pin'])
            if pre_pin_info is None:
                raise Exception('Could not find preceding pin info matched with ')
            try:
                pin_info['value'] = pre_pin_info['value']
            except KeyError:
                pin_info['value'] = pre_pin_info['default_value']


def _update_internal_input_data(node_info: dict):
    for pin_info in node_info['pins']:
        if pin_info['meta_type'] == PinMetaType.DataIn:
            node_info['internal_data'].update({pin_info['label']: pin_info['value']})


def _find_pin_info_in_pin_list_match_uuid(node_info: dict, match_pin_uuid: str) -> dict:
    for pin_info in node_info['pins']:
        if pin_info['uuid'] == match_pin_uuid:
            return pin_info


def _run_node_and_set_to_clean(node_info: dict):
    Run = node_info['run']
    Run(node_info['internal_data'])
    node_info['is_dirty'] = False


def _update_pins_value_in_node_info(node_info: dict):
    for pin_info in node_info['pins']:
        if pin_info['meta_type'] == PinMetaType.DataOut:
            for key, value in node_info['internal_data'].items():
                if key == pin_info['label']:
                    pin_info['value'] = value
                    break


def _is_dirty_pure_node(node_info: dict) -> bool:
    return node_info['is_dirty'] and \
        (node_info['type'] == NodeTypeFlag.Pure or node_info['type'] == NodeTypeFlag.GetVariable)


def _is_dirty_executed_blueprint_node(node_info: dict) -> bool:
    return node_info['is_dirty'] and \
        (node_info['type'] & NodeTypeFlag.Blueprint or node_info['type'] & NodeTypeFlag.Sequential) and \
        node_info['is_executed']


def _should_skip_backward_compute_node(node_info: dict) -> bool:
    return _is_dirty_unexecuted_blueprint_node(node_info) and \
        _is_clean_executed_blueprint_node(node_info) and \
        _is_clean_unexecuted_blueprint_node(node_info)


def _is_dirty_unexecuted_blueprint_node(node_info: dict) -> bool:
    return node_info['is_dirty'] and \
        (node_info['type'] & NodeTypeFlag.Blueprint or node_info['type'] & NodeTypeFlag.Sequential) and \
        not node_info['is_executed']


def _is_clean_executed_blueprint_node(node_info: dict) -> bool:
    return not node_info['is_dirty'] and \
        (node_info['type'] & NodeTypeFlag.Blueprint or node_info['type'] & NodeTypeFlag.Sequential) and \
        node_info['is_executed']


def _is_clean_unexecuted_blueprint_node(node_info: dict) -> bool:
    return not node_info['is_dirty'] and \
        (node_info['type'] & NodeTypeFlag.Blueprint or node_info['type'] & NodeTypeFlag.Sequential) and \
        not node_info['is_executed']


def update_anchors(current_node_info: dict, current_node_tag: str, anchors: list):
    if current_node_info['label'] == 'Sequence':
        for pin_info in current_node_info['pins']:
            if pin_info['meta_type'] == PinMetaType.FlowOut and pin_info['is_connected']:
                anchors.append({'next_node_tag': pin_info['connected_to_node'],
                                'this_node_tag': current_node_tag,
                                'this_node_label': current_node_info['label']})
    elif current_node_info['label'] == 'Do N':
        iteration_num = current_node_info['internal_data']['N']
        for pin_info in current_node_info['pins']:
            if pin_info['meta_type'] == PinMetaType.FlowOut and pin_info['is_connected']:
                for i in range(iteration_num):
                    anchors.append({'next_node_tag': pin_info['connected_to_node'],
                                    'index': i,
                                    'this_node_tag': current_node_tag,
                                    'this_node_label': current_node_info['label']})
                break
    elif current_node_info['label'] == 'For each loop':
        iteration_num = len(current_node_info['internal_data']['String Array'])
        for pin_info in current_node_info['pins']:
            if pin_info['label'] == 'Loop Body' and pin_info['is_connected']:
                for i in range(iteration_num):
                    anchors.append({'next_node_tag': pin_info['connected_to_node'],
                                    'index': i,
                                    'this_node_tag': current_node_tag,
                                    'this_node_label': current_node_info['label']})
            elif pin_info['label'] == 'Completed' and pin_info['is_connected']:
                anchors.append({'next_node_tag': pin_info['connected_to_node'],
                                'this_node_tag': current_node_tag,
                                'index': iteration_num,
                                'this_node_label': current_node_info['label']})


def _get_next_node_tag(current_node_info: dict) -> str:
    next_node_tag = None
    if current_node_info['label'] == 'Branch':
        next_node_tag = _get_next_node_tag_from_branch_node(current_node_info)
    if current_node_info['type'] == NodeTypeFlag.Blueprint:
        next_node_tag = _get_next_node_tag_from_blueprint_node(current_node_info)
    if current_node_info['type'] == NodeTypeFlag.SetVariable:
        _dirty_propagate_all_get_var_nodes(current_node_info)
        next_node_tag = _get_next_node_tag_from_blueprint_node(current_node_info)
    return next_node_tag


def _get_next_node_tag_from_branch_node(current_node_info: dict):
    condition = current_node_info['internal_data']['Condition']
    if condition is True or condition == 'True':
        for pin_info in current_node_info['pins']:
            if pin_info['meta_type'] == PinMetaType.FlowOut:
                if pin_info['is_connected'] and pin_info['label'] == 'True':
                    next_node_tag = pin_info['connected_to_node']
                    return next_node_tag
    else:
        for pin_info in current_node_info['pins']:
            if pin_info['meta_type'] == PinMetaType.FlowOut:
                if pin_info['is_connected'] and pin_info['label'] == 'False':
                    next_node_tag = pin_info['connected_to_node']
                    return next_node_tag


def _get_next_node_tag_from_blueprint_node(current_node_info: dict):
    for pin_info in current_node_info['pins']:
        if pin_info['meta_type'] == PinMetaType.FlowOut:
            if pin_info['is_connected']:
                next_node_tag = pin_info['connected_to_node']
                return next_node_tag


def _dirty_propagate_all_get_var_nodes(current_node_info: dict):
    for node_tag, node_info in nodes_data.items():
        if node_info['internal_data'].get('var_name', '') == current_node_info['internal_data']['var_name']:
            dirty_propagate(node_tag)


def dirty_propagate(node_tag: str):
    current_node_info = nodes_data[node_tag]
    if current_node_info['is_dirty']:
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
