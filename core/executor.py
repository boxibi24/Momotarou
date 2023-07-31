import logging
from time import perf_counter
from core.enum_types import NodeTypeFlag, PinMetaType
from core.utils import create_queueHandler_logger, extract_var_name_from_node_info
from core.data_loader import nodes_data, events_data, vars_data
from pprint import pprint
import dearpygui.dearpygui as dpg

logger = logging.getLogger('')
is_debug_mode = False


def setup_executor_logger(logger_queue, debug_mode: bool):
    global logger, is_debug_mode
    is_debug_mode = debug_mode
    logger = create_queueHandler_logger(__name__, logger_queue, is_debug_mode)


def execute_event(event_node_tag: str, ) -> tuple[int, str]:
    print('vars data')
    pprint(vars_data)
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
    if 'Set ' in current_node_info['label']:
        _var_name = extract_var_name_from_node_info(current_node_info)
        # If found declared var, set all its Get nodes to dirty
        if _var_name in vars_data.keys():
            logger.debug(f'Set {_var_name} triggered all Get {_var_name} nodes dirty propagation!')
            for node_tag, node_info in nodes_data.values():
                if 'Get ' + _var_name == node_info['label']:
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
        current_node_info['type'] & NodeTypeFlag.Blueprint or current_node_info['type'] & NodeTypeFlag.Sequential):
        compute_internal_output_data(node_tag)
    # If found var set nodes, trigger dirty propagation to all of its Get nodes
    if current_node_info['type'] & NodeTypeFlag.Blueprint and 'Set ' in current_node_info['label']:
        for node_get in nodes_data.values():
            if node_get['label'] == 'Get ' + node_get['label'].split(' ')[1]:
                node_get.is_dirty = True
    # If the nodes (Blueprint is also Pure) is dirty, perform computing output values from inputs
    if current_node_info['is_dirty'] and current_node_info['type'] & NodeTypeFlag.Pure:
        for pin_info in current_node_info['pins']:
            if pin_info['meta_type'] == PinMetaType.DataIn:
                if pin_info['is_connected'] is False:
                    continue
                pre_node_tag = pin_info['connected_to_node']
                pre_node_info = nodes_data[pre_node_tag]
                # Recursively compute every dirty Pure nodes
                if pre_node_info['is_dirty'] and pre_node_info['type'] == NodeTypeFlag.Pure:
                    compute_node(pre_node_info)

                # Recursively compute dirty Blueprint nodes even if it's executed
                elif pre_node_info['is_dirty'] and \
                    (pre_node_info['type'] & NodeTypeFlag.Blueprint or
                     pre_node_info['type'] & NodeTypeFlag.Sequential) and \
                    pre_node_info['is_executed']:
                    compute_node(pre_node_info)

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
        # After getting the clean inputs, perform computing outputs values for this node
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
    print(f'computing internal data for node: {node_tag}')
    node_data = nodes_data.get(node_tag, None)
    if node_data is None:
        logger.error(f'Could not find node_data for {node_data}')
        return -1
    for pin_info in node_data['pins']:
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
    internal_data = {}
    for pin_info in node_data['pins']:
        if pin_info['meta_type'] == PinMetaType.DataIn:
            internal_data.update({pin_info['label']: pin_info['value']})
    node_data['internal_data'] = internal_data
    # Compute output pin values
    Run = node_data['run']
    print(node_data['internal_data'])
    Run(node_data['internal_data'])
    # Update the output pins' value with fresh internal data
    for pin_info in node_data['pins']:
        if pin_info['meta_type'] == PinMetaType.DataOut:
            for key, value in node_data['internal_data'].items():
                if key == pin_info['label']:
                    pin_info['value'] = value
                    break
    # After computing for all outputs, mark this node as clean
    node_data['is_dirty'] = False
    # Update back to the master node dict
    nodes_data.update({node_tag: node_data})
    logger.debug(f'Internal input data for node {node_data} has been computed')
    logger.debug(node_data['internal_data'])


def dirty_propagate(current_node_tag: str):
    current_node_info = nodes_data.get(current_node_tag, None)
    if current_node_info is None:
        logger.error(f'Could not find node_info for {current_node_tag}')
        return -1
    if current_node_info['is_dirty']:
        logger.debug(f'Node {current_node_tag} is already dirty so no propagation needed!')
        return 0
    # Mark current node to 'dirty'
    current_node_info['is_dirty'] = True
    # Propagate to any connected following node to 'dirty' as well
    for pin_info in current_node_info['pins']:
        # if pin type is exec, skip
        if pin_info['pin_type'] == 5:
            continue
        # if pin is not connected, skip
        if pin_info.get('is_connected', False) is False:
            continue
        # propagate to the connected node
        dirty_propagate(pin_info['connect_to_node'])
