import dill
from copy import deepcopy
from core.enum_types import InputPinType, OutputPinType
from ui.NodeEditor.node_utils import *
from multiprocessing import Queue
from core.utils import create_queueHandler_logger, json_load_from_file_path, \
    generate_uuid, log_on_return_message, get_var_default_value_on_type, is_var_type_of_primitive_types, \
    is_var_type_of_string_based, cache_undo_action


class DPGNodeEditor:

    @property
    def id(self) -> int:
        return self._id

    @property
    def tag(self) -> str:
        return self._tag

    @property
    def node_instance_dict(self) -> dict:
        return self._node_instance_dict

    @property
    def data_link_list(self) -> list:
        return self._data_link_list

    @property
    def flow_link_list(self) -> list:
        return self._flow_link_list

    @property
    def node_data_link_dict(self) -> dict:
        return self._node_data_link_dict

    @node_data_link_dict.setter
    def node_data_link_dict(self, value):
        self._node_data_link_dict = value

    @property
    def node_flow_link_dict(self) -> dict:
        return self._node_flow_link_dict

    @node_flow_link_dict.setter
    def node_flow_link_dict(self, value):
        self._node_flow_link_dict = value

    @property
    def node_dict(self) -> dict:
        return self._node_dict

    @property
    def tobe_exported_event_dict(self) -> dict:
        return self._tobe_exported_event_dict

    @tobe_exported_event_dict.setter
    def tobe_exported_event_dict(self, value: dict):
        self._tobe_exported_event_dict = value

    @property
    def event_dict(self) -> OrderedDict:
        return self._event_dict

    @property
    def var_dict(self) -> OrderedDict:
        return self._var_dict

    @property
    def splitter_var_dict(self) -> OrderedDict:
        return self._splitter_var_dict

    def __init__(self,
                 node_editor_project_tab,
                 node_editor_project_instance,
                 setting_dict=None,
                 use_debug_print=False,
                 logging_queue=Queue(),
                 ):
        # ------ SETTINGS ------
        self._splitter_var_dict = OrderedDict([])
        self._use_debug_print = use_debug_print
        if setting_dict is None:
            self._setting_dict = {}
        else:
            self._setting_dict = setting_dict
        # ----- PARENT ITEMS -----
        # Shared splitter panel from master app
        self.node_editor_project_instance = node_editor_project_instance
        self.splitter_panel = node_editor_project_instance.splitter_panel
        # ----- ATTRIBUTES ------
        self._tab_id = node_editor_project_tab
        self.last_pos = (0, 0)
        self._node_instance_dict = {}
        self._node_dict = {'nodes': []}
        self._flow_link_list = []
        self._data_link_list = []
        self._node_data_link_dict = OrderedDict([])
        self._node_flow_link_dict = OrderedDict([])
        # dict of event nodes as keys and their first connected node as value
        self._tobe_exported_event_dict = {}
        # dict of events nodes for splitter entries
        self._event_dict = OrderedDict([])
        # dict of vars and its value stored in a list (make use of referencing_
        self._var_dict = OrderedDict([])
        # list of all item registries declared that will get deleted after the node graph termination
        self.item_registry_dict = {}
        self._id = dpg.add_node_editor(
            callback=self.callback_link,
            delink_callback=self.callback_delink,
            minimap=True,
            minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
            parent=node_editor_project_tab
        )
        self._tag = generate_uuid()
        # ------ LOGGER ----------
        self.logger = create_queueHandler_logger(__name__ + '_' + dpg.get_item_label(node_editor_project_tab),
                                                 logging_queue, self._use_debug_print)

        if not self.node_editor_project_instance.init_flag:
            self.logger.info('***** Child Node Editor initialized! *****')

    def delete_logger(self):
        while self.logger.hasHandlers():
            self.logger.removeHandler(self.logger.handlers[0])
        del self.logger

    @cache_undo_action
    def add_node_from_module(self, node_module, pos=(0, 0), override_label=''):
        """
        Callback function of adding a node from menu bar

        :param node_module: imported node module
        :param pos: spawn position of the node
        :param override_label: label of the node, if left to blank the node will use its default node label
        :return: added node instance
        """
        intermediate_node = self._prepare_intermediate_node(node_module, pos, override_label)
        node = intermediate_node.create_node()
        self._store_new_node_data(node)
        return node

    def _prepare_intermediate_node(self, node_module, pos, label: str):
        """
        Prepare an intermediate node

        :param node_module: the imported module of the node
        :param pos: spawn position of the node
        :param label: label of the node, if left to blank the node will use its default node label
        :return: intermediate node instance
        """
        intermediate_node = self._initialize_node_instance_from_import_module(node_module, label)
        self._set_intermediate_node_position(intermediate_node, pos)
        # Clear node selection after adding a node to avoid last_pos being overriden
        dpg.clear_selected_nodes(node_editor=self.id)
        return intermediate_node

    def _initialize_node_instance_from_import_module(self, node_module, label):
        """
        Initialize an intermediate standard node

        :param node_module: imported intermediate node module
        :param str label: node label if want to override the default
        :return: intermediate node
        """
        intermediate_node = node_module.python_module.Node(
            parent=self.id,
            setting_dict=self._setting_dict,
            pos=[0, 0],
            label=label,
            import_path=node_module.import_path
        )
        return intermediate_node

    def _set_intermediate_node_position(self, intermediate_node, pos):
        """
        Set intermediate node position

        :param intermediate_node:
        :param tuple[float,float] pos: node position
        :return:
        """
        if pos == (0, 0):
            # offset last pos a little bit
            self.last_pos = (self.last_pos[0] + 10, self.last_pos[1] + 10)
            intermediate_node.pos = self.last_pos
        else:
            intermediate_node.pos = pos

    def _store_new_node_data(self, node):
        """
        Store newly created node to the following:
        1. Event list
        2. Node instance dict
        3. Node info dict
        4. Flow link dict
        5. Data link dict

        :param node:
        :return:
        """
        if node.node_type == NodeTypeFlag.Event:
            self._update_splitter_event(node)
        self.node_instance_dict[node.node_tag] = node
        self._add_node_info_to_node_dict(node)
        self.node_flow_link_dict = sort_flow_link_dict(self.flow_link_list)
        self.node_data_link_dict = sort_data_link_dict(self.data_link_list)

    def _update_splitter_event(self, event_node):
        """
        Update the splitter event with the input event node instance

        :param event_node: event node instance
        :return:
        """
        # Strip the first string 'Event ' out
        _event_stripped_name = ' '.join(event_node.node_label.split(' ')[1:])
        self._event_dict.update(
            {event_node.node_tag: {'name': [_event_stripped_name], 'type': ['Button']}})
        # Set splitter event will also display it
        self.splitter_panel.event_dict = self._event_dict

    def _add_node_info_to_node_dict(self, node):
        """
        Add node info to node dict

        :param node: node instance
        :return:
        """
        if not self._node_dict.get('nodes', None):
            self._node_dict['nodes'] = []
        self._node_dict['nodes'].append(({
            'uuid': node.node_tag,
            'label': node.node_label,
            'node_instance': node,
            'pins': node.pin_list,
            'type': node.node_type,
            'import_path': node.import_path,
            'position':
                {
                    'x': self.last_pos[0],
                    'y': self.last_pos[1]
                }
        }))

    def callback_tool_save(self, sender, app_data):
        """
        Callback to save tool as JSON file

        :param sender: DPG item that triggers this callback
        :param app_data: DPG item's data
        :return:
        """
        try:
            action = dpg.get_item_label(sender)
        except SystemError:
            action = 'Tool Save'
        file_path = app_data['file_path_name']
        self._refresh_node_editor_data()
        tobe_exported_dict = self._construct_export_dict()
        return_message = save_dict_to_json(tobe_exported_dict, file_path)
        if sender == 'NG_file_save':
            log_on_return_message(logger=self.logger, action=action,
                                  return_message=return_message)

    def _refresh_node_editor_data(self):
        """
        Refresh all internal data to reflect latest node statuses

        :return:
        """

        reset_var_values_to_none(self._var_dict)
        self._clean_up_nodes_and_update_pins_values()
        self._refresh_event_order_in_node_dict()

    def _clean_up_nodes_and_update_pins_values(self):
        for node_info in self._node_dict['nodes']:
            # Update the is exposed status of the nodes and the pins value
            update_pins_values_in_node_dict(node_info)
            # Clean up non-primitive value from node internal data
            eliminate_non_primitive_internal_node_data(node_info['node_instance'])

    def _refresh_event_order_in_node_dict(self):
        """
        Reorder the node_dict to reflect the current ordering of events
        :return:
        """
        # Incrementally match event nodes with _event_dict and move_to_end till the event_dict exhausts
        for _event_tag in self._event_dict.keys():
            _index = 0
            for node_info in self._node_dict['nodes']:
                if node_info['uuid'] == _event_tag:
                    self._node_dict['nodes'].append(self._node_dict['nodes'].pop(_index))
                    break
                _index += 1

    def _construct_export_dict(self) -> dict:
        """
        Construct an export dict

        :return: dictionary to be exported to file
        """
        # Deep copying existing node dict, so we don't mistakenly modify it
        export_dict = dill.loads(dill.dumps(self._node_dict))
        self._update_necessary_entries_export_dict(export_dict)
        # Remove redundancies, such as node / pin instances
        prepare_node_info_for_export(export_dict)

        return export_dict

    def _update_necessary_entries_export_dict(self, export_dict: dict):
        """
        Update Flow link, Data link, Var dict to export dict

        :param export_dict: reference to the to be exported dict to update data to it
        :return:
        """
        update_flow_links_to_export_dict(self.flow_link_list, export_dict)
        update_data_links_to_export_dict(self.data_link_list, export_dict)
        # Add the events list to dict
        export_dict['events'] = self.tobe_exported_event_dict
        # Add var dict
        export_dict.update({'vars': self._var_dict})

    def callback_tool_open(self, sender, app_data):
        """
        Callback to open an RTool file as a new node graph

        :param sender: DPG item that triggers this callback
        :param app_data: DPG item's data
        """

        self.node_editor_project_instance.add_node_graph_tab_ask_name('', '', is_open_tool=True, import_path=app_data)

    def clear_all_data(self):
        """
        Clear all storage databases from this node graph

        :return:
        """
        self._node_dict.clear()
        self._flow_link_list.clear()
        self._data_link_list.clear()
        for node_instance in self.node_instance_dict.values():
            dpg.delete_item(node_instance.node_tag)
        self._node_instance_dict.clear()

        self.logger.info('**** Cleared current node graph ****')

    def return_current_node_editor_and_set_it_to_newly_added_tab(self):
        tab_name_list = list(self.node_editor_project_instance.node_editor_tab_dict.keys())
        stored_node_editor_instance = self.node_editor_project_instance.current_node_editor_instance
        self.node_editor_project_instance.current_node_editor_instance = \
            self.node_editor_project_instance.node_editor_tab_dict[tab_name_list[-1]]['node_editor_instance']
        return stored_node_editor_instance

    def callback_tool_import(self, sender, app_data):
        """
        Callback to perform RTool import to current node graph

        :param sender: DPG item that triggers this callback
        :param app_data: DPG item's data
        :return:
        """
        try:
            action = dpg.get_item_label(sender)
        except SystemError:
            action = 'Tool Import'
        _file_path = app_data['file_path_name']
        return_message = self._tool_import(_file_path)
        if not self.node_editor_project_instance.init_flag:
            log_on_return_message(self.logger, action, return_message)

    def _tool_import(self, file_path):  # Import means to append the existing node graph
        """
        Rtool import to current node graph

        :param file_path: Rtool file path
        :return:
        """
        # Read JSON
        imported_dict = json_load_from_file_path(file_path)
        if imported_dict is None:
            return 0, 'Could not load Json file!'
        # prepare a pin_mapping dict that lets functions know which pins linked together
        pin_mapping_dict = {}
        # -----------Initialize Variables -----------
        self._batch_import_variable(imported_dict['vars'])

        # -----------Initialize Node-------------
        self._batch_import_node(imported_dict['nodes'], pin_mapping_dict)

        # -----------Initialize Flow links -------------
        self._batch_import_link(imported_dict['flows'], pin_mapping_dict)

        # -----------Initialize Data links -------------
        self._batch_import_link(imported_dict['data_links'], pin_mapping_dict)

        return 1, f'Current node graph : {self._node_dict}'

    def _batch_import_variable(self, var_info_dict: dict):
        """
        Batch import variables with a var info dict

        :param var_info_dict: variable info
        :return:
        """
        for var_info in var_info_dict.values():
            self.splitter_panel.add_var('', '', var_info['name'][0],
                                        default_value=var_info['default_value'][0],
                                        var_type=var_info['type'][0],
                                        default_is_exposed_flag=var_info['is_exposed'][0],
                                        regex=var_info['regex'][0])

        # Refresh exposed var window since it does not update by itself
        self.splitter_panel.exposed_var_dict = deepcopy(self._var_dict)

    def _batch_import_node(self, node_info_list: list, pin_mapping: dict):
        """
        Batch import nodes from node info list

        :param list node_info_list: imported node info list
        :param dict pin_mapping: reference to a pin_mapping that will be updated per node creation
        :return:
        """
        for node_info in node_info_list:
            _imported_pin_list = node_info['pins']
            added_node = self._add_node_with_imported_info(node_info)
            if added_node is None:
                self.logger.error(f'Could not add this node {node_info}')
                continue
            # Perform mapping new pins IDs to old ones to replicate exported connections
            add_pin_mapping_entries(_imported_pin_list, added_node, pin_mapping)
            # Perform applying imported pin value to newly created pins
            reapply_imported_pin_value_to_new_node(_imported_pin_list, added_node)

    def _add_node_with_imported_info(self, node_info):
        """
        Add node with imported info

        :param dict node_info: imported node info
        :return:
        """
        import_path = node_info['import_path']
        _node_label = node_info['label']
        node_module = self._get_module_from_node_import_path(import_path)
        if node_module is None:
            return None
        if node_module.node_type == NodeTypeFlag.Event:  # Event nodes have custom labels, use splitter event add instead
            added_node = self.splitter_panel.event_graph_header_right_click_menu(sender='__add_node',
                                                                                 app_data=False,
                                                                                 user_data=(
                                                                                     reconstruct_node_pos_from_imported_info(
                                                                                         node_info),
                                                                                     split_event_name_from_node_label(
                                                                                         _node_label)),
                                                                                 instant_add=True)
        elif node_module.node_type & NodeTypeFlag.Variable:
            added_node = self.add_node_from_module(node_module, reconstruct_node_pos_from_imported_info(node_info),
                                                   override_label=node_info['label'])
        else:
            added_node = self.add_node_from_module(node_module, reconstruct_node_pos_from_imported_info(node_info))
        return added_node

    def _get_module_from_node_import_path(self, import_path):
        """
        Get imported node_module of node type

        :param str import_path: type of the node
        :return: a tuple of (import_path, node_module)
        :rtype: tuple(str, Any)
        """
        node_category = get_node_category_from_import_path(import_path)
        return self.node_editor_project_instance.menu_construct_dict[node_category][import_path]

    def _batch_import_link(self, link_list: list, pin_mapping_dict: dict):
        """
        Batch import link from a pin mapping

        :param link_list: imported link list
        :param pin_mapping_dict: a mapping of imported pin with newly created pins from nodes
        :return:
        """
        for link in link_list:
            self.callback_link(sender=self.id, app_data=[pin_mapping_dict[link[0]],
                                                         pin_mapping_dict[link[1]]])

    def callback_link(self, sender, app_data: list):
        source_pin_tag = dpg.get_item_alias(app_data[0])
        destination_pin_tag = dpg.get_item_alias(app_data[1])
        return_message = self.add_link_from_sourcePin_to_destinationPin(source_pin_tag, destination_pin_tag)
        if not self.node_editor_project_instance.init_flag:
            log_on_return_message(self.logger, 'Link Node', return_message)

    @cache_undo_action
    def add_link_from_sourcePin_to_destinationPin(self, source_pin_tag, destination_pin_tag) -> Tuple[int, str]:

        prepared_link_info = self._construct_link_info_from_source_and_destination_pin_tag(source_pin_tag,
                                                                                           destination_pin_tag)

        if not self._is_linkable(prepared_link_info):
            return 0, f'Link skipped, did not pass type check:' \
                      f' {prepared_link_info.source_pin_info.pin_type} to {prepared_link_info.destination_pin_info.pin_type}'

        if prepared_link_info.source_pin_info.pin_type == OutputPinType.Exec:
            link = self._add_flow_link_from_source_pin_to_destination_pin(prepared_link_info)
        else:
            link = self._add_data_link_from_source_pin_to_destination_pin(prepared_link_info)

        if link:
            return 1, f"New link created from {link.source_pin_instance.pin_tag} to {link.destination_pin_instance.pin_tag}"
        else:
            return 0, f'No link established'

    def _construct_link_info_from_source_and_destination_pin_tag(self, source_pin_tag, destination_pin_tag):
        source_pin_info = find_pin_and_construct_pin_info_in_node_list(source_pin_tag, self._node_dict['nodes'])
        destination_pin_info = find_pin_and_construct_pin_info_in_node_list(destination_pin_tag,
                                                                            self._node_dict['nodes'])
        return construct_link_info_from_source_and_destination_pin_info(source_pin_info, destination_pin_info)

    def _is_linkable(self, link_info) -> bool:
        """
        can source and destination pin link?

        :param link_info: link info
        :return: can these two pins link
        :rtype: bool
        """
        if not (link_info.source_pin_info.pin_type == link_info.destination_pin_info.pin_type or
                link_info.destination_pin_info.pin_type == InputPinType.WildCard or
                link_info.source_pin_info.pin_type == InputPinType.WildCard):
            self.logger.warning("Cannot connect pins with different types")
            return False
        # Cannot connect exec pin to wildcard pins also
        elif link_info.source_pin_info.pin_type == OutputPinType.Exec and \
            link_info.destination_pin_info.pin_type == InputPinType.WildCard:
            self.logger.warning("Cannot connect exec pin to wildcard")
            return False
        else:
            return True

    def _add_flow_link_from_source_pin_to_destination_pin(self, link_info):
        link = self._create_flow_link_if_not_duplicate(link_info)
        if link:
            self._reflect_new_flow_link_to_all_data(link)
            return link
        else:
            return None

    def _create_flow_link_if_not_duplicate(self, link_info):
        if not is_link_duplicate_in_check_list(link_info, self.flow_link_list):
            return create_link_object_from_link_info_if_node_unconnected(link_info)
        else:
            return None

    def _reflect_new_flow_link_to_all_data(self, link):
        self._append_flow_link_to_list(link)
        reflect_new_link_to_pins(link)
        self._update_new_event_if_source_is_event_node(link)

    def _append_flow_link_to_list(self, link):
        self.flow_link_list.append(link)

    def _update_new_event_if_source_is_event_node(self, link):
        if link.source_node_instance.node_type == NodeTypeFlag.Event:
            self.tobe_exported_event_dict.update({link.source_node_tag: link.destination_node_tag})

    def _add_data_link_from_source_pin_to_destination_pin(self, link_info):
        link = self._create_data_link_if_not_duplicate(link_info)
        if link:
            self._reflect_new_data_link_to_all_data(link)
            return link
        else:
            return None

    def _create_data_link_if_not_duplicate(self, link_info):
        if not is_link_duplicate_in_check_list(link_info, self.data_link_list):
            return create_link_object_from_link_info(link_info)
        else:
            return None

    def _reflect_new_data_link_to_all_data(self, link):
        self._append_data_link_to_list(link)
        reflect_new_link_to_pins(link)

    def _append_data_link_to_list(self, link):
        self.data_link_list.append(link)

    def _refresh_link_dict(self):
        self.node_data_link_dict = sort_data_link_dict(self.data_link_list)
        self.node_flow_link_dict = sort_flow_link_dict(self.flow_link_list)

    def callback_delink(self, sender, app_data):
        action = 'Delink'
        tobe_removed_link_id = app_data
        tobe_removed_link, is_data_link = self._get_link_from_id(tobe_removed_link_id)
        if is_data_link:
            self.remove_data_link(tobe_removed_link)
        else:
            self.remove_flow_link(tobe_removed_link)
        log_on_return_message(self.logger, action, (1, ''))

    def _get_link_from_id(self, link_id) -> Tuple[Link, bool]:
        for link in self._data_link_list:
            if link.link_id == link_id:
                return link, True
        for link in self._flow_link_list:
            if link.link_id == link_id:
                return link, False

    @cache_undo_action
    def remove_data_link(self, link: Link):
        self._remove_data_link_in_all_data_bases(link)
        self._reflect_remove_data_link_on_connected_pins(link)
        return 1,

    def _remove_data_link_in_all_data_bases(self, link: Link):
        dpg.delete_item(link.link_id)
        self.data_link_list.remove(link)
        self._refresh_link_dict()

    def _reflect_remove_data_link_on_connected_pins(self, link):
        self._reflect_remove_data_link_on_source_pin(link)
        self._reflect_remove_link_on_destination_pin(link)

    def _reflect_remove_data_link_on_source_pin(self, link: Link):
        """
        Check and set source pin to unconnected only if it does not have any other existing links

        :param link:
        :return:
        """
        found_flag = False
        source_pin_tag = link.source_pin_instance.pin_tag
        for alt_link in self.data_link_list:
            if source_pin_tag == alt_link.source_pin_instance.pin_tag:
                found_flag = True
                link.source_pin_instance.connected_link_list.remove(link)
                break
        if not found_flag:
            link.source_pin_instance.is_connected = False
            link.source_pin_instance.connected_link_list.clear()

    @staticmethod
    def _reflect_remove_link_on_destination_pin(link: Link):
        # Safely set target pin's status to not connected
        link.destination_pin_instance.is_connected = False
        # Set target pin's connected link instance to None
        link.destination_pin_instance.connected_link_list.clear()

    @cache_undo_action
    def remove_flow_link(self, link: Link):
        self._remove_flow_link_in_all_data_bases(link)
        self._reflect_remove_flow_link_on_connected_pins(link)

    def _remove_flow_link_in_all_data_bases(self, link: Link):
        dpg.delete_item(link.link_id)
        self._flow_link_list.remove(link)
        self._refresh_link_dict()

    def _reflect_remove_flow_link_on_connected_pins(self, link: Link):
        self._reflect_remove_flow_link_on_source_pin(link)
        self._reflect_remove_link_on_destination_pin(link)

    def _reflect_remove_flow_link_on_source_pin(self, link: Link):
        link.source_pin_instance.is_connected = False
        link.source_pin_instance.connected_link_list.clear()
        # Also remove this entry from event dict
        if link.source_node_instance.node_type == NodeTypeFlag.Event:
            self.tobe_exported_event_dict.pop(link.source_node_instance.node_tag)

    @cache_undo_action
    def add_var(self, var_info: dict, default_value=None, default_is_exposed_flag=False, regex=None):
        # Save one for the splitter's var_dict
        self._splitter_var_dict.update(var_info)
        var_tag: str = list(var_info.keys())[0]
        var_name: list = var_info[var_tag]['name']
        var_type: list = var_info[var_tag]['type']
        _default_var_value = None
        if default_value is None:
            _default_var_value = get_var_default_value_on_type(var_type[0])
        else:
            _default_var_value = default_value
        if _default_var_value is None and \
            is_var_type_of_primitive_types(var_type[0]):
            self.logger.critical(f'Could not retrieve default value for {var_name}')
            return
        if regex is None and is_var_type_of_string_based(var_type[0]):
            regex = '.+'
        if self._var_dict.get(var_tag, None) is None:
            self._var_dict.update({
                var_tag: {
                    'name': var_name,
                    'type': var_type,
                    'value': [None],
                    'default_value': [_default_var_value],
                    'is_exposed': [default_is_exposed_flag if default_is_exposed_flag is not None else False],
                    'regex': [regex]
                }})
        else:  # Refresh UI
            self._var_dict[var_tag]['name'][0] = var_name[0]
            self._var_dict[var_tag]['type'][0] = var_type[0]

        self.logger.debug('**** Added new var entries ****')
        self.logger.debug(f'var_dict: {self._var_dict}')
        self.logger.debug(f'splitter_var_dict:  {self._splitter_var_dict}')

    def register_var_user_input_box_tag(self, var_tag: str, user_input_box_tag: str):
        """
        Callback function upon enabling variable's exposed for user input flag
        """
        self._var_dict[var_tag]['user_input_box_tag'] = user_input_box_tag
        self.logger.debug(f'**** Registered {var_tag} to take input from dpg item : {user_input_box_tag} ****')

    def delete_item_registry(self, item_tag: str):
        """
        Delete item registry from dpg and registry dict
        """
        registry_id = self.item_registry_dict[item_tag]
        dpg.delete_item(registry_id)
        self.item_registry_dict.pop(item_tag)

