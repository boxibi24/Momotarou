import logging
from logging import Logger
from time import perf_counter
from core.enum_type import NodeTypeFlag
from core.utils import create_queueHandler_logger

logger = None
is_debug_mode = False
data_base = {}

def setup_core_logger(logger_queue, debug_mode: bool):
    global logger, is_debug_mode
    is_debug_mode= debug_mode
    logger = create_queueHandler_logger(__name__, logger_queue, is_debug_mode)


def setup_execution_data_base(data: dict):
    global data_base
    data_base = data


def execute_event(event_node_tag: str, ):
    # Perform initial cleanup
    preprocess_execute_event()
    t1_start = 0
    if logger.level == logging.DEBUG:
        t1_start = perf_counter()
    logger.info(f'**** Exec event : {event_node_tag} ****')

    # Get first node instance that is connected to this user_data node
    current_node_tag = tobe_exported_event_dict.get(event_node_tag, None)
    if not current_node_tag:
        logger.error('Cannot find the event, this could be due to the event node not connecting to anything!')
        return 1
    current_node = node_instance_dict.get(current_node_tag, None)

    # This will propagate the flow chain until it meets the end (unconnected Exec out)
    anchors = []
    if anchors:
        anchors.clear()
    forward_propagate_flow(current_node, anchors)
    flow_control_redirect(anchors)
    logger.info(f'**** Event {event_node_tag} finished ****')
    if logger.level == logging.DEBUG:
        t1_stop = perf_counter()
        logger.debug(f"Elapsed time for the event {event_node_tag}: {t1_stop - t1_start} ")


def preprocess_execute_event():
    # Reset every vars' value to None if it's not exposed, else get from user input box
    for var_info in self._vars_dict.values():
        if var_info['is_exposed'][0] is False:
            var_info['value'][0] = None
        else:
            user_input_value = dpg_get_value(var_info['user_input_box_id'])
            var_info['value'][0] = user_input_value
    # Reset all nodes' is_executed flags to False and set them to dirty
    for node in self.node_instance_dict.values():
        if not node.is_dirty:
            node.is_dirty = True
        node.is_executed = False


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


def forward_propagate_flow(current_node, anchors: list):
    if is_debug_mode:
        t1_start = perf_counter()
        current_node_elapsed_time = compute_node(current_node)
        t1_stop = perf_counter()
        logger.debug(f"**** Executing {current_node.node_tag} ****")
        logger.debug(f"Compute time: {current_node_elapsed_time}")
        backward_propagate_time = t1_stop - t1_start - current_node_elapsed_time
        logger.debug(f"Time to backward propagate: {backward_propagate_time}")
    else:
        compute_node(current_node)
    # Get next node to compute
    next_node = None
    # Branch node got to explicitly decide next_node based on its condition bool value
    if current_node.node_label == 'Branch':
        condition = current_node.internal_data.get('Condition', None)
        if condition is None:
            logger.error(f'Can not query condition value for this branch node : {current_node.node_tag}')
            return -1
        if condition is True or condition == 'True':
            for pin_info in current_node.pin_list:
                if pin_info['meta_type'] == 'FlowOut':
                    if pin_info['pin_instance'].is_connected and pin_info['label'] == 'True':
                        next_node = pin_info['pin_instance'].connected_link_list[0].destination_node_instance
                        break
        else:
            for pin_info in current_node.pin_list:
                if pin_info['meta_type'] == 'FlowOut':
                    if pin_info['pin_instance'].is_connected and pin_info['label'] == 'False':
                        next_node = pin_info['pin_instance'].connected_link_list[0].destination_node_instance
                        break
    # If normal Blueprint node which has only one Exec pin out then next_node is deterministic
    else:
        # First found exec out pin will be the next node (this might be changed later)
        for pin_info in current_node.pin_list:
            if pin_info['meta_type'] == 'FlowOut':
                if pin_info['pin_instance'].is_connected:
                    next_node = pin_info['pin_instance'].connected_link_list[0].destination_node_instance
                break
    # If current node is a Set variable value type, then mark all of its get nodes to dirty
    if 'Set ' in current_node.node_label:
        _var_name = ' '.join(current_node.node_label.split(' ')[1:])
        # Find if current node is a Set Var node
        _is_var_declared = False
        for _var_info in _vars_dict.values():
            if _var_name == _var_info['name'][0]:
                _is_var_declared = True
                break
        # If found declared var, set all its Get nodes to dirty
        if _is_var_declared:
            logger.debug(f'Set {_var_name} triggered all Get {_var_name} nodes dirty propagation!')
            for node in node_instance_dict.values():
                if 'Get ' + _var_name == node.node_label:
                    node.is_dirty = True

    # Store anchors point if current node is sequential nodes
    if current_node.node_type == NodeTypeFlag.Sequential:
        if current_node.node_label == 'Sequence':
            for pin_info in current_node.pin_list:
                if pin_info['meta_type'] == 'FlowOut':
                    if pin_info['pin_instance'].is_connected:
                        anchors.append(pin_info['pin_instance'].connected_link_list[0].destination_node_instance)
            return 0
        elif current_node.node_label == 'Do N':
            iteration_num = current_node.internal_data.get('N', None)
            if iteration_num and next_node:
                for i in range(iteration_num):
                    anchors.append(next_node)
                return 0
            else:
                logger.error(
                    f'Could not find anchors point upon processing this node: {current_node.node_tag} ')
    if next_node:
        forward_propagate_flow(next_node, anchors)
    else:
        return 0


def compute_node(self, node):
    # Blueprint nodes still need to be executed even if it's clean
    if not node.is_dirty and (node.node_type & NodeTypeFlag.Blueprint or node.node_type & NodeTypeFlag.Sequential):
        node.compute_internal_output_data()
    # If found var set nodes, trigger dirty propagation to all of its Get nodes
    if node.node_type & NodeTypeFlag.Blueprint and 'Set ' in node.node_label:
        for node_get in _node_instance_dict.values():
            if node_get.node_label == 'Get ' + node.node_label.split(' ')[1]:
                node_get.is_dirty = True
    # If the nodes (Blueprint is also Pure) is dirty, perform computing output values from inputs
    if node.is_dirty and node.node_type & NodeTypeFlag.Pure:
        # Get all the links that's connected to this node's inputs
        input_links = node_data_link_dict.get(node.node_tag, None)
        if input_links:
            for input_link in input_links:
                pre_node_instance = node_instance_dict.get(input_link[0].parent)
                if not pre_node_instance:
                    logger.error(
                        f'Could not find node instance that matches this tag : {input_link[0].parent}')
                    continue

                # Recursively compute every dirty Pure nodes
                if pre_node_instance.is_dirty and pre_node_instance.node_type == NodeTypeFlag.Pure:
                    compute_node(pre_node_instance)

                # Recursively compute dirty Blueprint nodes even if it's executed
                elif pre_node_instance.is_dirty and \
                    (pre_node_instance.node_type & NodeTypeFlag.Blueprint or
                     pre_node_instance.node_type & NodeTypeFlag.Sequential) and \
                    pre_node_instance.is_executed:
                    compute_node(pre_node_instance)

                # Skip computing for dirty Blueprint un-executed nodes (avoid premature execution)
                elif pre_node_instance.is_dirty and \
                    (pre_node_instance.node_type & NodeTypeFlag.Blueprint or
                     pre_node_instance.node_type & NodeTypeFlag.Sequential) and \
                    not pre_node_instance.is_executed:
                    pass

                # Clean and executed Blueprint nodes does not need to do anything, ofcourse
                elif not pre_node_instance.is_dirty and \
                    (pre_node_instance.node_type & NodeTypeFlag.Blueprint or
                     pre_node_instance.node_type & NodeTypeFlag.Sequential) and \
                    pre_node_instance.is_executed:
                    pass

                # Clean but not executed Blueprint nodes will skip computing (avoid premature execution next
                # time the event triggers)
                elif not pre_node_instance.is_dirty and \
                    (pre_node_instance.node_type & NodeTypeFlag.Blueprint or
                     pre_node_instance.node_type & NodeTypeFlag.Sequential) and \
                    not pre_node_instance.is_executed:
                    pass

        # Debug timer starts
        t1_start = 0
        if is_debug_mode:
            t1_start = perf_counter()
        # After getting the clean inputs, perform computing outputs values for this node
        node.compute_internal_output_data()
        # Debug timer stops
        if is_debug_mode:
            t1_stop = perf_counter()
            elapsed_time = t1_stop - t1_start
            return elapsed_time
        return 0
    # If the current node is already clean, can safely skip computation and use it outputs values right away
    else:
        return 0
