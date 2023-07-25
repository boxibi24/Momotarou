from time import perf_counter
import dill
from copy import deepcopy
from ui.NodeEditor.utils import *
from ui.NodeEditor.classes.pin import OutputPinType, InputPinType, PinInfo
from ui.NodeEditor.node_utils import *
from multiprocessing import Queue
from ui.NodeEditor.logger_message import log_on_return_code


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
        return self._vars_dict

    @property
    def splitter_var_dict(self) -> OrderedDict:
        return self._splitter_var_dict

    def __init__(self,
                 parent_tab,
                 splitter_panel,
                 setting_dict=None,
                 imported_module_dict=None,
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
        # dict to keep track of the imported modules
        if imported_module_dict is None:
            self._imported_module_dict = {}
        else:
            self._imported_module_dict = imported_module_dict
        # ----- PARENT ITEMS -----
        # Shared splitter panel from master app
        self.splitter_panel = splitter_panel
        # ----- ATTRIBUTES ------
        self.last_pos = (0, 0)
        self._node_instance_dict = {}
        self._node_dict = {}
        self._flow_link_list = []
        self._data_link_list = []
        self._node_data_link_dict = OrderedDict([])
        self._node_flow_link_dict = OrderedDict([])
        # dict of event nodes as keys and their first connected node as value
        self._tobe_exported_event_dict = {}
        # dict of events nodes for splitter entries
        self._event_dict = OrderedDict([])
        # dict of vars and its value stored in a list (make use of referencing_
        self._vars_dict = OrderedDict([])
        # list of all item registries declared that will get deleted after the node graph termination
        self.item_registry_dict = {}
        self._id = dpg.add_node_editor(
            callback=self.callback_link,
            delink_callback=self.callback_delink,
            minimap=True,
            minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
            parent=parent_tab
        )
        self._tag = generate_uuid()
        # ------ LOGGER ----------
        self.logger = create_queueHandler_logger(__name__ + '_' + dpg.get_item_label(parent_tab),
                                                 logging_queue, self._use_debug_print)

        self.logger.info('***** Child Node Editor initialized! *****')

    def _refresh_node_editor_data(self):
        """
        Refresh all internal data to reflect latest node statuses

        :return:
        """

        reset_var_values_to_none(self._vars_dict)

        # Cleanup nodes
        if self.node_dict.get('nodes', None) is not None:
            for node_info in self.node_dict['nodes']:
                # Update the is exposed status of the nodes and the pins value
                update_pin_values_in_node_dict(node_info)
                # Clean up non-primitive value from node internal data
                node_instance = node_info['node_instance']
                eliminate_non_primitive_internal_node_data(node_instance)

        # Reorder the node_dict to reflect the current ordering of events
        # Incrementally match event nodes with _event_dict and move_to_end till the event_dict exhausts
        for _event_tag in self._event_dict.keys():
            _index = 0
            for node_info in self.node_dict['nodes']:
                if node_info['id'] == _event_tag:
                    self.node_dict['nodes'].append(self.node_dict['nodes'].pop(_index))
                    break
                _index += 1

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
        export_dict.update({'vars': self._vars_dict})

    def _construct_export_dict(self) -> dict:
        """
        Construct an export dict

        :return: dictionary to be exported to file
        """
        # Deep copying existing node dict, so we don't mistakenly modify it
        export_dict = dill.loads(dill.dumps(self.node_dict))
        self._update_necessary_entries_export_dict(export_dict)
        # Remove redundancies, such as node / pin instances
        prepare_node_info_for_export(export_dict)

        return export_dict

    def callback_tool_save(self, sender, app_data):
        """
        Callback to save tool as JSON file

        :param sender: DPG item that triggers this callback
        :param app_data: DPG item's data
        :return:
        """
        # Callback action name
        action = dpg.get_item_label(sender)
        # app_data is the chosen file path
        file_path = app_data['file_path_name']
        # Refresh and cleanup data
        self._refresh_node_editor_data()
        # Construct export dict
        tobe_exported_dict = self._construct_export_dict()
        # Save constructed dict to file
        return_message = save_dict_to_json(tobe_exported_dict, file_path)
        # Log
        log_on_return_code(logger=self.logger, action=action,
                           return_message=return_message)

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
                                        default_is_exposed_flag=var_info['is_exposed'][0])

        # Refresh exposed var window since it does not update by itself
        self.splitter_panel.exposed_var_dict = deepcopy(self._vars_dict)

    def _get_module_from_imported_node_type(self, imported_node_type):
        """
        Get imported module of node type

        :param str imported_node_type: type of the node
        :return: a tuple of (import_path, module)
        :rtype: tuple(str, Any)
        """

        import_path = '.'.join(imported_node_type.split('.')[:-1])
        module = self._imported_module_dict.get(import_path, None)

        if module is None:
            self.logger.error(f"Could not find an entry in imported module dict for {imported_node_type}")
            return None, None

        return import_path, module

    def _add_node_with_imported_info(self, node_info):
        """
        Add node with imported info

        :param dict node_info: imported node info
        :return:
        """
        _node_type = node_info['type']
        _node_label = node_info['label']
        import_path, module = self._get_module_from_imported_node_type(_node_type)
        if module is None:
            return None
        if _node_type == NodeTypeFlag.Event:  # Event nodes have custom labels, use splitter event add instead
            added_node = self.splitter_panel.event_graph_header_right_click_menu(sender='__add_node',
                                                                                 app_data=False,
                                                                                 user_data=('', ' '.join(
                                                                                     _node_label.split(' ')[1:])),
                                                                                 instant_add=True)
        else:
            added_node = self.add_node(import_path, module,
                                       reconstruct_node_pos_from_imported_info(node_info))
        return added_node

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

    def _file_import(self, file_path):  # Import means to append the existing node graph
        """
        Rtool import to current node graph

        :param file_path: Rtool file path
        :return:
        """
        # Read JSON
        imported_dict = json_load_from_file(file_path)
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

        return 1, f'Current node graph : {self.node_dict}'

    def callback_file_import(self, sender, app_data):
        """
        Callback to perform RTool import to current node graph

        :param sender: DPG item that triggers this callback
        :param app_data: DPG item's data
        :return:
        """
        _file_path = app_data['file_path_name']
        return_message = self._file_import(_file_path)
        log_on_return_code(self.logger, action=dpg.get_item_label(sender), return_message=return_message)

    def clear_all_data(self):
        """
        Clear all storage databases from this node graph

        :return:
        """
        self.node_dict.clear()
        self.flow_link_list.clear()
        self.data_link_list.clear()
        for node_instance in self.node_instance_dict.values():
            dpg.delete_item(node_instance.node_tag)
        self.node_instance_dict.clear()

        self.logger.info('**** Cleared current node graph ****')

    def callback_file_open(self, sender, app_data):
        """
        Callback to open an RTool file as a new node graph

        :param sender: DPG item that triggers this callback
        :param app_data: DPG item's data
        """

        # First clear out everything from the current node graph
        self.clear_all_data()
        # Then perform file JSON import
        self.callback_file_import(sender, app_data)

    def _initialize_var_node_instance_from_import_module(self, import_module, var_label, var_tag):
        """
        Initialize an intermediate variable node

        :param import_module: imported intermediate variable node module
        :param var_label: variable label
        :param var_tag: variable tag
        :return: intermediate variable node
        """
        intermediate_node = import_module.Node(
            parent=self.id,
            setting_dict=self._setting_dict,
            pos=[0, 0],
            label=var_label,
            internal_data={'var_value': self._vars_dict[var_tag]['value'] if var_tag else None,
                           'default_var_value': self._vars_dict[var_tag]['default_value']} if var_tag else None
        )
        return intermediate_node

    def _initialize_standard_node_instance_from_import_module(self, import_module, label):
        """
        Initialize an intermediate standard node

        :param import_module: imported intermediate node module
        :param str label: node label if want to override the default
        :return: intermediate node
        """
        intermediate_node = import_module.Node(
            parent=self.id,
            setting_dict=self._setting_dict,
            pos=[0, 0],
            label=label
        )
        return intermediate_node

    def _initialize_intermediate_node(self, import_module, is_variable: bool, label='', var_tag=''):
        """
        Initialize an intermediate node instance that can later be called its create_node method for node initialization

        :param import_module: the imported module of the intermediate node
        :param is_variable: if True, will override default node's label and tag with that label and var_tag
        :param label: label of the variable node
        :param var_tag: tag of the variable node
        :return: An intermediate node holds a create_node() method that when called spawns the actual node
        """
        if is_variable:
            intermediate_node = self._initialize_var_node_instance_from_import_module(import_module, label, var_tag)
        else:
            intermediate_node = self._initialize_standard_node_instance_from_import_module(import_module, label)
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

    def _prepare_intermediate_node(self, import_module, pos, is_variable: bool, label: str, var_tag: str):
        """
        Prepare an intermediate node

        :param import_module: the imported module of the node
        :param pos: spawn position of the node
        :param is_variable: True if this node is a Variable node
        :param label: label of the node, if left to blank the node will use its default node label
        :param var_tag: if this node is variable, will use var_tag to find its initialized references to its value and type
        :return: intermediate node instance
        """
        intermediate_node = self._initialize_intermediate_node(import_module, is_variable, label, var_tag)
        self._set_intermediate_node_position(intermediate_node, pos)
        # Clear node selection after adding a node to avoid last_pos being overriden
        dpg.clear_selected_nodes(node_editor=self.id)
        return intermediate_node

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

    def _add_node_info_to_node_dict(self, node, import_path):
        """
        Add node info to node dict

        :param node: node instance
        :param import_path: path to import the node module
        :return:
        """
        if not self._node_dict.get('nodes'):
            self._node_dict['nodes'] = []
        self._node_dict['nodes'].append(OrderedDict({
            'id': node.node_tag,
            'label': node.node_label,
            'node_instance': node,
            'pins': node.pin_list,
            'meta_type': node.node_type,
            'type': import_path + '.' + node.__class__.__name__,
            'position':
                {
                    'x': self.last_pos[0],
                    'y': self.last_pos[1]
                }
        }))

    def _store_data_after_node_creation(self, node, import_path):
        """
        Store newly created node to the following:
        1. Event list
        2. Node instance dict
        3. Node info dict
        4. Flow link dict
        5. Data link dict

        :param node:
        :param import_path:
        :return:
        """
        if node.node_type == NodeTypeFlag.Event:
            self._update_splitter_event(node)
        self.node_instance_dict[node.node_tag] = node
        self._add_node_info_to_node_dict(node, import_path)
        self.node_flow_link_dict = sort_flow_link_dict(self.flow_link_list)
        self.node_data_link_dict = sort_data_link_dict(self.data_link_list)

    def add_node(self, import_path, import_module, pos=(0, 0), is_variable=False, label='', var_tag=''):
        """
        Callback function of adding a node from menu bar

        :param import_path: path to import the module, still needed this to construct node info dict
        :param import_module: the imported module of the node
        :param pos: spawn position of the node
        :param is_variable: True if this node is a Variable node
        :param label: label of the node, if left to blank the node will use its default node label
        :param var_tag: if this node is variable, will use var_tag to find its initialized references to its value and type
        :return: added node instance
        """
        intermediate_node = self._prepare_intermediate_node(import_module, pos, is_variable, label, var_tag)
        node = intermediate_node.create_node()
        self._store_data_after_node_creation(node, import_path)
        return node

    def _get_pin_info(self, pin_tag):
        """
        Get all pin data

        :param pin_tag: pin tag
        :return:
        """
        for node in self.node_dict['nodes']:
            pin_dict_list = node['pins']
            for pin_dict in pin_dict_list:
                if pin_dict['id'] == pin_tag:
                    pin_instance = pin_dict['pin_instance']
                    pin_type = pin_dict['pin_type']
                    parent_node_instance = node['node_instance']
                    parent_node_tag = node['id']
                    return PinInfo(pin_instance,pin_type,parent_node_instance,parent_node_tag)

    def _can_link(self, source_link_info: PinInfo, destination_link_info: PinInfo) -> bool:
        """
        can source and destination pin link?

        :param source_link_info: source pin info
        :param destination_link_info: destination pin info
        :return: can these two pins link
        :rtype: bool
        """
        if not source_link_info.pin_type:
            self.logger.warning("Could not get source pin type")
            return False
        elif not destination_link_info.pin_type:
            self.logger.warning("Could not get target pin type")
            return False
        elif not (source_link_info.pin_type == destination_link_info.pin_type or
                  destination_link_info.pin_type == InputPinType.WildCard):
            self.logger.warning("Cannot connect pins with different types")
            return False
        # Cannot connect exec pin to wildcard pins also
        elif source_link_info.pin_type == OutputPinType.Exec and destination_link_info.pin_type == InputPinType.WildCard:
            self.logger.warning("Cannot connect exec pins to wildcards")
            return False
        elif not source_link_info.pin_instance:
            self.logger.warning("Cannot find source pin instance from node dict")
            return False
        elif not source_link_info.pin_instance:
            self.logger.warning("Cannot find target pin instance from node dict")
            return False
        else:
            return True

    def _add_link(self, source_pin_info: PinInfo, destination_pin_info: PinInfo):
        # First link occurrence
        if source_pin_type == OutputPinType.Exec:  # Direct flow links to flow_link_list
            if len(self.flow_link_list) == 0:
                # Also disallowing already connected Exec pin to perform further linkage
                if not source_pin_instance.is_connected:
                    create_link_object()

            # Check if duplicate linkage, can happen if user swap link direction
            else:
                if not source_pin_instance.is_connected:
                    if not is_link_duplicate(self.flow_link_list, destination_pin_info.pin_instance):
                        try:
                            link = Link(source_node_tag,
                                        source_node_instance,
                                        source_pin_instance,
                                        source_pin_type,
                                        destination_node_tag,
                                        destination_node_instance,
                                        destination_pin_instance,
                                        destination_pin_type,
                                        self.id)
                        except:
                            self.logger.exception("Failed to link")
                        if link:
                            self.flow_link_list.append(link)
                            # Set pin's connected status
                            source_pin_instance.is_connected = True
                            destination_pin_instance.is_connected = True
                            source_pin_instance.connected_link_list.append(link)
                            destination_pin_instance.connected_link_list.append(link)
                            # Update event dict to store target node tag if it's connected to an event node
                            if source_node_instance.node_type == NodeTypeFlag.Event:
                                self.tobe_exported_event_dict.update({source_node_tag: destination_node_tag})
                        else:
                            self.logger.error("Cannot add a null link")

    def add_link(self, source_pin_tag, destination_pin_tag) -> tuple[int, str]:
        link = None

        source_pin_info = self._get_pin_info(source_pin_tag)
        destination_pin_info = self._get_pin_info(destination_pin_tag)

        if not self._can_link(source_pin_info, destination_pin_info):
            return 0, f'Link skipped, did not pass type check: {source_pin_info.pin_type} to {destination_pin_info.pin_type}'

        else:  # Direct data links to data_link_list
            if len(self.data_link_list) == 0:
                try:
                    link = Link(source_node_tag,
                                source_node_instance,
                                source_pin_instance,
                                source_pin_type,
                                destination_node_tag,
                                destination_node_instance,
                                destination_pin_instance,
                                destination_pin_type,
                                self.id)
                except:
                    self.logger.exception("Failed to link")

                if link:
                    self.data_link_list.append(link)
                    # Mark the target node as dirty
                    destination_node_instance.is_dirty = True
                    # Also update the nodes' data_link_list
                    source_node_instance.succeeding_data_link_list.append(link)
                    # Set pin's connected status
                    source_pin_instance.is_connected = True
                    destination_pin_instance.is_connected = True
                    source_pin_instance.connected_link_list.append(link)
                    destination_pin_instance.connected_link_list.append(link)
                else:
                    self.logger.error("Cannot add a null link")
            # Check if duplicate linkage, can happen if user swap link direction
            else:
                duplicate_flag = False
                for node_link in self.data_link_list:
                    if destination_pin_instance == node_link.destination_pin_instance:
                        duplicate_flag = True
                if not duplicate_flag:
                    try:
                        link = Link(source_node_tag,
                                    source_node_instance,
                                    source_pin_instance,
                                    source_pin_type,
                                    destination_node_tag,
                                    destination_node_instance,
                                    destination_pin_instance,
                                    destination_pin_type,
                                    self.id)
                    except:
                        self.logger.exception("Failed to link")
                    if link:
                        self.data_link_list.append(link)
                        # Mark the target node as dirty
                        destination_node_instance.is_dirty = True
                        # Also update the nodes' data_link_list
                        source_node_instance.succeeding_data_link_list.append(link)
                        # Set pin's connected status and store the link instance into both of the pins
                        source_pin_instance.is_connected = True
                        destination_pin_instance.is_connected = True
                        source_pin_instance.connected_link_list.append(link)
                        destination_pin_instance.connected_link_list.append(link)
                    else:
                        self.logger.error("Cannot add a null link")
        self.node_data_link_dict = sort_data_link_dict(self.data_link_list)
        self.node_flow_link_dict = sort_flow_link_dict(self.flow_link_list)
        if link:
            self.logger.info('**** Nodes linked ****')

    def callback_link(self, sender, app_data: list):
        source_pin_tag = dpg.get_item_alias(app_data[0])
        destination_pin_tag = dpg.get_item_alias(app_data[1])
        return_message = self.add_link(source_pin_tag, destination_pin_tag)
        log_on_return_code(self.logger, 'Link Node', return_message)

    def callback_delink(self, sender, app_data):
        # Remove instance from link list hence trigger its destructor
        for link in self.data_link_list:
            if link.link_id == app_data:
                try:
                    self.data_link_list.remove(link)
                except ValueError:
                    self.logger.exception("Could not find the link for removal")
                except:
                    self.logger.exception("Some thing is wrong deleting the link")
                else:
                    dpg.delete_item(link.link_id)
                    self.node_data_link_dict = sort_data_link_dict(self.data_link_list)
                    # Safely set target pin's status to not connected
                    link.destination_pin_instance.is_connected = False
                    # Set target pin's connected link instance to None
                    link.destination_pin_instance.connected_link_list.clear()
                    # Now check if source pin (output pin) is not connecting to another link
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

        for link in self.flow_link_list:
            if link.link_id == app_data:
                try:
                    self.flow_link_list.remove(link)
                except ValueError:
                    self.logger.exception("Could not find flow link for removal ")
                except:
                    self.logger.exception("Some thing is wrong deleting the link")
                else:
                    dpg.delete_item(link.link_id)
                    self.node_flow_link_dict = sort_flow_link_dict(self.flow_link_list)
                    # Can safely set duo pins' status to not connected
                    link.source_pin_instance.is_connected = False
                    link.destination_pin_instance.is_connected = False
                    # Also set the connected link instance of the pins to None
                    link.source_pin_instance.connected_link_list.clear()
                    link.destination_pin_instance.connected_link_list.clear()
                    # Also remove this entry from event dict
                    if link.source_node_instance.node_type == NodeTypeFlag.Event:
                        self.tobe_exported_event_dict.pop(link.source_node_instance.node_tag)
                    return 0

        self.logger.info('**** Link broke ****')
        self.logger.debug(f'     sender                      :    {sender}')
        self.logger.debug(f'     app_data                    :    {app_data}')
        self.logger.debug(f'     self.data_link_list         :    {self.data_link_list}')
        self.logger.debug(f'     self.flow_link_list         :    {self.flow_link_list}')
        self.logger.debug(f'     self.node_data_link_dict    :    {self.node_data_link_dict}')
        self.logger.debug(f'     self.node_flow_link_dict    :    {self.node_flow_link_dict}')

    def preprocess_execute_event(self):
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

    def execute_event(self, sender, app_data, user_data):
        # Perform initial cleanup
        self.preprocess_execute_event()
        t1_start = 0
        if self._use_debug_print:
            t1_start = perf_counter()
        event_node_tag = user_data
        self.logger.info(f'**** Exec event : {event_node_tag} ****')

        # Get first node instance that is connected to this user_data node
        current_node_tag = self.tobe_exported_event_dict.get(event_node_tag, None)
        if not current_node_tag:
            self.logger.error('Cannot find the event, this could be due to the event node not connecting to anything!')
            return 1
        current_node = self.node_instance_dict.get(current_node_tag, None)

        # This will propagate the flow chain until it meets the end (unconnected Exec out)
        anchors = []
        if anchors:
            anchors.clear()
        self.forward_propagate_flow(current_node, anchors)
        self.flow_control_redirect(anchors)
        self.logger.info(f'**** Event {event_node_tag} finished ****')
        if self._use_debug_print:
            t1_stop = perf_counter()
            self.logger.debug(f"Elapsed time for the event {event_node_tag}: {t1_stop - t1_start} ")

    def flow_control_redirect(self, anchors: list):
        if not anchors:
            return 0
        for anchor in anchors:
            sub_anchors = []
            if sub_anchors:
                sub_anchors.clear()
            self.forward_propagate_flow(anchor, sub_anchors)
            if sub_anchors:
                self.flow_control_redirect(sub_anchors)

    def forward_propagate_flow(self, current_node, anchors: list):
        if self._use_debug_print:
            t1_start = perf_counter()
            current_node_elapsed_time = self.compute_node(current_node)
            t1_stop = perf_counter()
            self.logger.debug(f"**** Executing {current_node.node_tag} ****")
            self.logger.debug(f"Compute time: {current_node_elapsed_time}")
            backward_propagate_time = t1_stop - t1_start - current_node_elapsed_time
            self.logger.debug(f"Time to backward propagate: {backward_propagate_time}")
        else:
            self.compute_node(current_node)
        # Get next node to compute
        next_node = None
        # Branch node got to explicitly decide next_node based on its condition bool value
        if current_node.node_label == 'Branch':
            condition = current_node.internal_data.get('Condition', None)
            if condition is None:
                self.logger.error(f'Can not query condition value for this branch node : {current_node.node_tag}')
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
            for _var_info in self._vars_dict.values():
                if _var_name == _var_info['name'][0]:
                    _is_var_declared = True
                    break
            # If found declared var, set all its Get nodes to dirty
            if _is_var_declared:
                self.logger.debug(f'Set {_var_name} triggered all Get {_var_name} nodes dirty propagation!')
                for node in self.node_instance_dict.values():
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
                    self.logger.error(
                        f'Could not find anchors point upon processing this node: {current_node.node_tag} ')
        if next_node:
            self.forward_propagate_flow(next_node, anchors)
        else:
            return 0

    def compute_node(self, node):
        # Blueprint nodes still need to be executed even if it's clean
        if not node.is_dirty and (node.node_type & NodeTypeFlag.Blueprint or node.node_type & NodeTypeFlag.Sequential):
            node.compute_internal_output_data()
        # If found var set nodes, trigger dirty propagation to all of its Get nodes
        if node.node_type & NodeTypeFlag.Blueprint and 'Set ' in node.node_label:
            for node_get in self._node_instance_dict.values():
                if node_get.node_label == 'Get ' + node.node_label.split(' ')[1]:
                    node_get.is_dirty = True
        # If the nodes (Blueprint is also Pure) is dirty, perform computing output values from inputs
        if node.is_dirty and node.node_type & NodeTypeFlag.Pure:
            # Get all the links that's connected to this node's inputs
            input_links = self.node_data_link_dict.get(node.node_tag, None)
            if input_links:
                for input_link in input_links:
                    pre_node_instance = self.node_instance_dict.get(input_link[0].parent)
                    if not pre_node_instance:
                        self.logger.error(
                            f'Could not find node instance that matches this tag : {input_link[0].parent}')
                        continue

                    # Recursively compute every dirty Pure nodes
                    if pre_node_instance.is_dirty and pre_node_instance.node_type == NodeTypeFlag.Pure:
                        self.compute_node(pre_node_instance)

                    # Recursively compute dirty Blueprint nodes even if it's executed
                    elif pre_node_instance.is_dirty and \
                        (pre_node_instance.node_type & NodeTypeFlag.Blueprint or
                         pre_node_instance.node_type & NodeTypeFlag.Sequential) and \
                        pre_node_instance.is_executed:
                        self.compute_node(pre_node_instance)

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
            if self._use_debug_print:
                t1_start = perf_counter()
            # After getting the clean inputs, perform computing outputs values for this node
            node.compute_internal_output_data()
            # Debug timer stops
            if self._use_debug_print:
                t1_stop = perf_counter()
                elapsed_time = t1_stop - t1_start
                return elapsed_time
            return 0
        # If the current node is already clean, can safely skip computation and use it outputs values right away
        else:
            return 0

    def add_var(self, var_info: dict, default_value=None, default_is_exposed_flag=False):
        # Save one for the splitter's var_dict
        self._splitter_var_dict.update(var_info)
        var_tag: str = list(var_info.keys())[0]
        var_name: list = var_info[var_tag]['name']
        var_type: list = var_info[var_tag]['type']
        _default_var_value = None
        if default_value is None:
            # set default var value based on value type
            if var_type[0] in ['String', 'MultilineString', 'Password']:
                _default_var_value = ''
            elif var_type[0] == 'Int':
                _default_var_value = 0
            elif var_type[0] == 'Float':
                _default_var_value = 0.0
            elif var_type[0] == 'Bool':
                _default_var_value = False
        else:
            _default_var_value = default_value
        if _default_var_value is None and \
            var_type[0] in ['String', 'MultilineString', 'Password', 'Int', 'Float', 'Bool']:
            self.logger.critical(f'Could not retrieve default value for {var_name}')
            return 3
        if self._vars_dict.get(var_tag, None) is None:
            self._vars_dict.update({
                var_tag: {
                    'name': var_name,
                    'type': var_type,
                    'value': [None],
                    'default_value': [_default_var_value],
                    # For unknown reasons, default_is_exposed_flag is None when you add new vars
                    'is_exposed': [default_is_exposed_flag if default_is_exposed_flag is not None else False]
                }})
        else:  # Refresh UI
            self._vars_dict[var_tag]['name'][0] = var_name[0]
            self._vars_dict[var_tag]['type'][0] = var_type[0]

        self.logger.debug('**** Added new var entries ****')
        self.logger.debug(f'var_dict: {self._vars_dict}')
        self.logger.debug(f'splitter_var_dict:  {self._splitter_var_dict}')
        return 0

    def register_var_user_input_box(self, var_tag, user_box_id):
        """
        Callback function upon enabling variable's exposed for user input flag
        """
        self._vars_dict[var_tag]['user_input_box_id'] = user_box_id
        self.logger.debug(f'**** Register {var_tag} to take input from dpg item : {user_box_id} ****')
        self.logger.debug(f'Current var dict of {var_tag}: {self._vars_dict[var_tag]}')

    def delete_item_registry(self, item_name: str):
        """
        Delete item registry from dpg and registry dict
        """
        registry_id = self.item_registry_dict[item_name]
        dpg.delete_item(registry_id)
        self.item_registry_dict.pop(item_name)
