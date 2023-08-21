import dearpygui.dearpygui as dpg
from collections import OrderedDict
from core.utils import clear_file_dialog_children


def callback_project_save_as():
    clear_file_dialog_children('project_save_as')
    dpg.show_item('project_save_as')


def callback_project_open_menu():
    dpg.show_item('project_open')


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
    # 2: node_data_link_dict = 'target_node' : [source_pin_instance, destination_pin_instance]
    for link in data_link_list:
        source_node_tag = link.source_node_tag
        target_node_tag = link.destination_node_tag
        if target_node_tag not in node_tag_dict:
            node_tag_dict[target_node_tag] = [source_node_tag]
        else:
            node_tag_dict[target_node_tag].append(source_node_tag)
        source_pin_instance = link.source_pin_instance
        target_pin_instance = link.destination_pin_instance
        # Keep a dict of connections (links) that contains list of [source_pin_instance, destination_pin_instance]
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
    # 2: flow_dict = 'target_node' : [source_pin_instance, destination_pin_instance]
    for link in flow_link_list:
        source_node_tag = link.source_node_tag
        target_node_tag = link.destination_node_tag
        if target_node_tag not in node_tag_dict:
            node_tag_dict[target_node_tag] = [source_node_tag]
        else:
            node_tag_dict[target_node_tag].append(source_node_tag)
        source_pin_instance = link.source_pin_instance
        target_pin_instance = link.destination_pin_instance
        # Keep a dict of connections (links) that contains list of [source_pin_instance, destination_pin_instance]
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


