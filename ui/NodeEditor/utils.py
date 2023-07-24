import dearpygui.dearpygui as dpg
from collections import OrderedDict
from uuid import uuid1
import logging
from logging.handlers import QueueHandler
import json
import traceback


def generate_uuid() -> str:
    """Generate a UUID1
    :return: uuid1
    """
    # Use UUID1 because it is time based so no replication produced
    return uuid1().hex


def dpg_set_value(tag: str, value):
    """
    Check if exist node with tag, then set the value
    :param tag: tag to check
    :param value: value to set
    """

    if dpg.does_item_exist(tag):
        dpg.set_value(tag, value)


def dpg_get_value(tag: str):
    """
    Get value from a node with tag
    :param tag: tags of node to query value
    :return: the value of node with tag
    """
    value = None
    if dpg.does_item_exist(tag):
        value = dpg.get_value(tag)
    return value


def callback_project_open_menu():
    dpg.show_item('project_open')


def callback_project_save_menu():
    dpg.show_item('project_save')


def callback_project_import_menu():
    dpg.show_item('project_import')


def callback_ng_file_open_menu():
    dpg.show_item('NG_file_open')


def callback_ng_file_save_menu():
    dpg.show_item('NG_file_save')


def callback_ng_file_import_menu():
    dpg.show_item('NG_file_import')


def callback_drop_var(sender, app_data):
    var_name = app_data[0].get(app_data[1], None)[0]
    if var_name is None:
        return 2
    with dpg.window(
        popup=True,
        autosize=True,
        no_move=True,
        no_open_over_existing_popup=True,
        no_saved_settings=True,
        min_size=[10, 10]
    ):
        dpg.add_selectable(label='Get ' + var_name)
        dpg.add_separator()
        dpg.add_selectable(label='Set ' + var_name)


def callback_create_get_var_node(sender, app_data, user_data):
    pass


def callback_create_set_var_node(sender, appdata, user_data):
    pass


def sort_node_graph(data_link_list: list, flow_link_list: list):
    if data_link_list:
        sort_data_link_dict(data_link_list)
    if flow_link_list:
        sort_flow_link_dict(flow_link_list)


def sort_data_link_dict(data_link_list: list):
    # Initialize temp dicts for storing
    node_tag_dict = OrderedDict({})
    node_data_link_dict = OrderedDict({})
    # Loop through the list of links and make:
    # 1: node_tag_dict = 'target_node' : source_node
    # 2: node_data_link_dict = 'target_node' : [source_pin_instance, target_pin_instance]
    for link in data_link_list:
        source_node_tag = link.source_node_tag
        target_node_tag = link.target_node_tag
        if target_node_tag not in node_tag_dict:
            node_tag_dict[target_node_tag] = [source_node_tag]
        else:
            node_tag_dict[target_node_tag].append(source_node_tag)
        source_pin_instance = link.source_pin_instance
        target_pin_instance = link.target_pin_instance
        # Keep a dict of connections (links) that contains list of [source_pin_instance, target_pin_instance]
        if target_node_tag not in node_data_link_dict:
            node_data_link_dict[target_node_tag] = [[source_pin_instance, target_pin_instance]]
        else:
            node_data_link_dict[target_node_tag].append([source_pin_instance, target_pin_instance])

    # Make lists of the above dicts to perform insert and swaps (retain ordering):
    # 1: node_tag_list = [(target_node1, source_node1), ...]
    # 2: node_connection_list = [(target_node1, [source_pin1, target_pin1]), ...]
    node_tag_list = list(node_tag_dict.items())
    node_connection_list = list(node_data_link_dict.items())
    # Swap processing order from input to output (to compute input first)
    # Loop through elements of node_tag_list; find the target node that acts as source node in another link
    # , since its result needs computing to be an input for other nodes, its position needs to be pushed upwards.
    # Result list would be an ordered list from the most "source node" to the most "computed node"
    index = 0
    while index < len(node_tag_list):
        swap_flag = False
        # for check_id in pin_link_list[index][1]:
        for check_source_node_tag in node_tag_list[index][1]:
            # Loop through the rest (index + 1) of node list
            for i in range(index + 1, len(node_tag_list)):
                if node_tag_list[i][0] == check_source_node_tag:
                    # Swap 2 elements
                    node_tag_list[i], node_tag_list[index] = node_tag_list[index], node_tag_list[i]
                    node_connection_list[i], node_connection_list[index] \
                        = node_connection_list[index], node_connection_list[i]
                    swap_flag = True
                    break
        if not swap_flag:
            index += 1

    # Add nodes that do not appear in the connection list (input nodes, etc.)
    # index = 0
    return OrderedDict(node_connection_list)


def sort_flow_link_dict(flow_link_list: list):
    # Initialize temp dicts for storing
    node_tag_dict = OrderedDict({})
    flow_dict = OrderedDict({})
    # Loop through the list of links and make:
    # 1: node_tag_dict = 'target_node' : source_node
    # 2: flow_dict = 'target_node' : [source_pin_instance, target_pin_instance]
    for link in flow_link_list:
        source_node_tag = link.source_node_tag
        target_node_tag = link.target_node_tag
        if target_node_tag not in node_tag_dict:
            node_tag_dict[target_node_tag] = [source_node_tag]
        else:
            node_tag_dict[target_node_tag].append(source_node_tag)
        source_pin_instance = link.source_pin_instance
        target_pin_instance = link.target_pin_instance
        # Keep a dict of connections (links) that contains list of [source_pin_instance, target_pin_instance]
        if target_node_tag not in flow_dict:
            flow_dict[target_node_tag] = [[source_pin_instance, target_pin_instance]]
        else:
            flow_dict[target_node_tag].append([source_pin_instance, target_pin_instance])

    # Make lists of the above dicts to perform insert and swaps (retain ordering):
    # 1: node_tag_list = [(target_node1, source_node1), ...]
    # 2: flow_list = [(target_node1, [source_pin1, target_pin1]), ...]
    node_tag_list = list(node_tag_dict.items())
    flow_list = list(flow_dict.items())
    # Swap processing order from input to output (to compute input first)
    # Loop through elements of node_tag_list; find the target node that acts as source node in another link
    # , since its result needs computing to be an input for other nodes, its position needs to be pushed upwards.
    # Result list would be an ordered list from the most "source node" to the most "computed node"
    index = 0
    while index < len(node_tag_list):
        swap_flag = False
        # for check_id in pin_link_list[index][1]:
        for check_source_node_tag in node_tag_list[index][1]:
            # Loop through the rest (index + 1) of node list
            for i in range(index + 1, len(node_tag_list)):
                if node_tag_list[i][0] == check_source_node_tag:
                    # Swap 2 elements
                    node_tag_list[i], node_tag_list[index] = node_tag_list[index], node_tag_list[i]
                    flow_list[i], flow_list[index] \
                        = flow_list[index], flow_list[i]
                    swap_flag = True
                    break
        if not swap_flag:
            index += 1

    # Add nodes that do not appear in the connection list (input nodes, etc.)
    # index = 0
    return OrderedDict(flow_list)


def create_queueHandler_logger(logger_name, queue, is_debug_mode: bool):
    logger = logging.getLogger(logger_name)
    qh = QueueHandler(queue)
    logger.addHandler(qh)
    if is_debug_mode:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger


def add_user_input_box(var_type, callback=None, default_value=None,
                       user_data=None, text='', add_separator=False, width=None):
    if var_type == 'String':
        if text:
            dpg.add_text(text)
        if default_value is None:
            _default_value = ''
        else:
            _default_value = default_value
        if width is None:
            _width = 200
        else:
            _width = width
        _user_input_box = dpg.add_input_text(on_enter=True, default_value=_default_value,
                                             callback=callback,
                                             user_data=user_data,
                                             hint='one line text',
                                             width=_width)
        if add_separator:
            dpg.add_separator()
        return _user_input_box
    elif var_type == 'Int':
        if text:
            dpg.add_text(text)
        if default_value is None:
            _default_value = 0
        else:
            _default_value = default_value
        if width is None:
            _width = 200
        else:
            _width = width
        _user_input_box = dpg.add_input_int(on_enter=True, default_value=_default_value,
                                            callback=callback,
                                            user_data=user_data,
                                            width=_width)
        if add_separator:
            dpg.add_separator()
        return _user_input_box
    elif var_type == 'Float':
        if text:
            dpg.add_text(text)
        if default_value is None:
            _default_value = 0.0
        else:
            _default_value = default_value
        if width is None:
            _width = 200
        else:
            _width = width
        _user_input_box = dpg.add_input_float(on_enter=True, default_value=_default_value,
                                              callback=callback,
                                              user_data=user_data,
                                              width=_width)
        if add_separator:
            dpg.add_separator()
        return _user_input_box
    elif var_type == 'MultilineString':
        if text:
            dpg.add_text(text)
        if default_value is None:
            _default_value = ''
        else:
            _default_value = default_value
        if width is None:
            _width = 400
        else:
            _width = width
        _user_input_box = dpg.add_input_text(on_enter=True, multiline=True,
                                             default_value=_default_value,
                                             callback=callback,
                                             user_data=user_data,
                                             width=_width)
        if add_separator:
            dpg.add_separator()
        return _user_input_box
    elif var_type == 'Password':
        if text:
            dpg.add_text(text)
        if default_value is None:
            _default_value = ''
        else:
            _default_value = default_value
        if width is None:
            _width = 200
        else:
            _width = width
        _user_input_box = dpg.add_input_text(on_enter=True, password=True,
                                             default_value=_default_value,
                                             callback=callback,
                                             user_data=user_data,
                                             hint='password',
                                             width=_width)
        if add_separator:
            dpg.add_separator()
        return _user_input_box
    elif var_type == 'Bool':
        if text:
            dpg.add_text(text)
        if default_value is None:
            _default_value = False
        else:
            _default_value = default_value
        _user_input_box = dpg.add_checkbox(callback=callback,
                                           default_value=_default_value,
                                           user_data=user_data)
        if add_separator:
            dpg.add_separator()
        return _user_input_box


def json_write_to_file(file_path, value):
    with open(file_path, 'w') as fp:
        json.dump(value, fp, indent=4)


def json_load_from_file(file_path):
    with open(file_path, 'r') as fp:
        try:
            return_dict = json.load(fp)
            return return_dict
        except FileNotFoundError:
            return None


