import json
from time import perf_counter
import dill
from copy import deepcopy
from ui.NodeEditor.utils import *
from ui.NodeEditor.classes.link import Link
from ui.NodeEditor.classes.pin import OutputPinType, InputPinType
from ui.NodeEditor.classes.node import NodeTypeFlag
import ui.NodeEditor.node_utils as node_utils
from multiprocessing import Queue
import ui.NodeEditor.logger_message as log_message


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
        self.last_pos = [0, 0]
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
        """

        node_utils.reset_var_values_to_none(self._vars_dict)

        # Cleanup nodes
        if self.node_dict.get('nodes', None) is not None:
            for node_info in self.node_dict['nodes']:
                # Update the is exposed status of the nodes and the pins value
                node_utils.update_pin_values_in_node_dict(node_info)
                # Clean up non-primitive value from node internal data
                node_instance = node_info['node_instance']
                node_utils.eliminate_non_primitive_internal_node_data(node_instance)

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
        """
        node_utils.update_flow_links_to_export_dict(self.flow_link_list, export_dict)
        node_utils.update_data_links_to_export_dict(self.data_link_list, export_dict)
        # Add the events list to dict
        export_dict['events'] = self.tobe_exported_event_dict
        # Add var dict
        export_dict.update({'vars': self._vars_dict})

    def _construct_export_dict(self) -> dict:
        """
        Construct an export dict
        """
        # Deep copying existing node dict, so we don't mistakenly modify it
        export_dict = dill.loads(dill.dumps(self.node_dict))
        self._update_necessary_entries_export_dict(export_dict)
        # Remove redundancies, such as node / pin instances
        node_utils.remove_export_dict_redundancies(export_dict)

        return export_dict

    def callback_tool_save(self, sender, app_data):
        """
        Callback to save tool as JSON file
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
        return_message = node_utils.save_dict_to_json(tobe_exported_dict, file_path)
        # Log
        log_message.log_on_return_code(logger=self.logger, action=action,
                                       return_message=return_message)

    def callback_file_import(self, sender, app_data):  # Import means to append the existing node graph
        self.logger.info('**** Start file importing ****')
        self.logger.debug(f"Sender : {sender}")
        self.logger.debug(f"Appdata: {app_data}")
        pin_mapping = {}
        if app_data['file_name'] != '.':
            # Read JSON
            try:
                with open(app_data['file_path_name']) as fp:
                    setting_dict = json.load(fp)
            except FileNotFoundError:
                self.logger.exception('File does not exist!')
            if not setting_dict:
                self.logger.error("Could not load Json file")
                raise Exception("Could not load Json for import!")
            self.logger.debug(f"Imported setting dict: {setting_dict}")
            # -----------Initialize Variables -----------
            for var_info in setting_dict['vars'].values():
                self.splitter_panel.add_var('', '', var_info['name'][0],
                                            default_value=var_info['default_value'][0],
                                            var_type=var_info['type'][0],
                                            default_is_exposed_flag=var_info['is_exposed'][0])

            # Refresh exposed var window since it does not update by itself
            self.splitter_panel.exposed_var_dict = deepcopy(self._vars_dict)

            # -----------Initialize Node-------------
            for node in setting_dict['nodes']:
                node_type = node.get('type', None)
                if not node_type:
                    self.logger.error(f"Could not find node type from this node: {node}")
                import_path = '.'.join(node_type.split('.')[:-1])
                self.logger.debug(f'import path : {import_path}')
                module = self._imported_module_dict.get(import_path, None)
                self.logger.debug(f"Node to be imported: {node}")
                self.logger.debug(f'current module dict: {self._imported_module_dict}')
                self.logger.debug(f' Module to be imported: {module}')
                if module:
                    # Creating new nodes using imported info
                    if node['meta_type'] == 8:  # Event nodes have custom labels, use splitter event add instead
                        added_node = self.splitter_panel.event_graph_header_right_click_menu('', '',
                                                                                             user_data=('',
                                                                                                        ' '.join(node[
                                                                                                                     'label'].split(
                                                                                                            ' ')[1:])),
                                                                                             instant_add=True)
                    else:
                        added_node = self.callback_add_node(sender='Menu_' + node['label'],
                                                            app_data=False,
                                                            user_data=(import_path, module),
                                                            pos=[node['position']['x'], node['position']['y']])
                    # Perform mapping new pins IDs to old ones to replicate exported connections
                    imported_pins = node.get('pins', None)
                    if imported_pins:
                        # Loop through a list of to-be-imported pins
                        for imported_pin in imported_pins:
                            imported_pin_label = imported_pin.get('label')
                            if imported_pin_label:
                                for added_pin in added_node.pin_list:
                                    # Get the matching pin id from the newly created pins list of the newly created node
                                    if imported_pin_label == added_pin['label']:
                                        try:
                                            pin_mapping.update({imported_pin['id']: added_pin['id']})
                                        except KeyError:
                                            self.logger.exception('Error querying value from pin dicts:')
                                            break

                            else:
                                self.logger.error(f"Could not get label for this pin : {imported_pin}")
                                continue
                    else:
                        self.logger.error(f'Failed to query pins info for this node : {node}')
                    # Perform applying imported pin value to newly created pins
                    for new_pin_info in added_node.pin_list:
                        # if this new pin does not require value then skip
                        if new_pin_info.get('value', None):
                            continue
                        # Get value from imported pin info that matches label:
                        imported_value = None
                        for imported_pin_info in node['pins']:
                            if imported_pin_info['label'] == new_pin_info['label']:
                                imported_value = imported_pin_info.get('value', None)
                        if imported_value is None:
                            continue
                        # Set the imported value to this new pin's value
                        try:
                            dpg_set_value(new_pin_info['pin_instance'].value_tag, imported_value)
                        except:
                            self.logger.exception(
                                f'Something wrong setting up the pin value of this pin {new_pin_info}')

                else:
                    self.logger.error(f"Could not find an entry in imported module dict for {node['type']}")
                self.logger.debug(f'pin_mapping: {pin_mapping}')

            # Initialize Flow links
            for link in setting_dict['flows']:
                self.callback_link(sender=self.id, app_data=[pin_mapping[link[0]], pin_mapping[link[1]]])
            # Initialize Data Links
            for link in setting_dict['data_links']:
                self.callback_link(sender=self.id, app_data=[pin_mapping[link[0]], pin_mapping[link[1]]])

            self.logger.info('**** File imported ****')
            self.logger.debug(f'     sender              :   {sender}')
            self.logger.debug(f'     app_data            :   {app_data}')
            self.logger.debug(f'     self.data_link_list :   {self.data_link_list}')
            self.logger.debug(f'     self.flow_link_list :   {self.flow_link_list}')
            self.logger.debug(f'     node_connection_dict:   {self.node_data_link_dict}')

    def _get_var_names_from_var_dict(self, imported_var_name):
        """
        Return list of var names, queries from var dict
        """
        _var_name_list = []
        for var_info in self._vars_dict:
            _var_name_list.append(var_info['name'])
        return _var_name_list

    def callback_file_open(self, sender, app_data):

        # First clear out everything from the current node graph
        self.node_dict.clear()
        self.flow_link_list.clear()
        self.data_link_list.clear()
        for node_instance in self.node_instance_dict.values():
            dpg.delete_item(node_instance.node_tag)
        self.node_instance_dict.clear()
        self.logger.info('**** Cleared current node graph ****')
        self.logger.debug(f'     sender              :   {sender}')
        self.logger.debug(f'     app_data            :   {app_data}')
        self.logger.debug(f'     self.data_link_list :   {self.data_link_list}')
        self.logger.debug(f'     self.flow_link_list :   {self.flow_link_list}')
        self.logger.debug(f'     node_connection_dict:   {self.node_data_link_dict}')
        self.logger.debug(f'     node_instance_dict  :   {self.node_instance_dict}')
        # Then perform file JSON import
        self.callback_file_import(sender, app_data)

    def callback_add_node(self, sender, app_data, user_data, pos=None):
        """
        Callback function of adding a node from menu bar
        """
        # For variables, override node_label, stored in user_data[2][1]
        user_data_len = len(user_data)
        label = None
        _var_tag = ''
        if user_data_len == 3:
            label = user_data[2][1]
            _var_tag = user_data[2][0]

        # Grab node instance using node label passed in as event
        intermediate_node = user_data[1].Node(
            parent=self.id,
            setting_dict=self._setting_dict,
            pos=[0, 0],
            label=label,
            internal_data={'var_value': self._vars_dict[_var_tag]['value'] if _var_tag else None,
                           'default_var_value': self._vars_dict[_var_tag]['default_value']} if _var_tag else None
        )
        # Get current node_editor instance
        # Stack nodes nicely if found last clicked position
        if self.last_pos is not None and pos is None:
            self.last_pos[0] += 10
            self.last_pos[1] += 10

        # print(self.node_instance_dict)
        if pos:
            intermediate_node.pos = pos
        else:
            intermediate_node.pos = self.last_pos
        # Clear node selection after adding a node to avoid last_pos being overriden
        dpg.clear_selected_nodes(node_editor=self.id)
        # Create node
        node = intermediate_node.create_node()
        # Store event list to display it on Splitter
        if node.node_type == NodeTypeFlag.Event:
            # Strip the first string 'Event ' out
            _event_stripped_name = ' '.join(node.node_label.split(' ')[1:])
            self._event_dict.update(
                {node.node_tag: {'name': [_event_stripped_name], 'type': ['Button']}})
            self.splitter_panel.event_dict = self._event_dict
        # Store the node instance along with its tag
        self.node_instance_dict[node.node_tag] = node
        # add pins entries to private _node_dict
        if not self._node_dict.get('nodes'):
            self._node_dict['nodes'] = []
        self._node_dict['nodes'].append(OrderedDict({
            'id': node.node_tag,
            'label': node.node_label,
            'node_instance': node,
            'pins': node.pin_list,
            'meta_type': node.node_type,
            'type': user_data[0] + '.' + node.__class__.__name__,
            'position':
                {
                    'x': self.last_pos[0],
                    'y': self.last_pos[1]
                }
        }))
        self.node_data_link_dict = sort_data_link_dict(self.data_link_list)
        self.node_flow_link_dict = sort_flow_link_dict(self.flow_link_list)
        self.logger.info('**** Node added ****')
        self.logger.debug(f'    Node ID         :    {str(node.node_tag)}')
        self.logger.debug(f'    sender          :    {str(sender)}')
        self.logger.debug(f'    data            :    {str(app_data)}')
        self.logger.debug(f'    user_data       :    {str(user_data)}')
        return node

    def callback_link(self, sender, app_data: list):
        source_pin_type = None
        destination_pin_type = None
        source_pin_tag = dpg.get_item_alias(app_data[0])
        target_pin_tag = dpg.get_item_alias(app_data[1])
        source_pin_instance = None
        target_pin_instance = None
        source_node_tag = None
        target_node_tag = None
        source_node_instance = None
        target_node_instance = None
        link = None
        # Loop through the node_dict to find pin id that matches with source and get its type
        found_flag = False
        for node in self.node_dict['nodes']:
            pin_dict_list = node['pins']
            for pin_dict in pin_dict_list:
                if pin_dict['id'] == source_pin_tag:
                    source_pin_type = pin_dict['pin_type']
                    found_flag = True
                    source_node_tag = node['id']
                    source_pin_instance = pin_dict['pin_instance']
                    source_node_instance = node['node_instance']
                    break
            if found_flag:
                break
        # Loop through the node_dict to find pin id that matches with target and get its type
        found_flag = False
        for node in self.node_dict['nodes']:
            pin_dict_list = node['pins']
            for pin_dict in pin_dict_list:
                if pin_dict['id'] == target_pin_tag:
                    destination_pin_type = pin_dict['pin_type']
                    found_flag = True
                    target_node_tag = node['id']
                    target_pin_instance = pin_dict['pin_instance']
                    target_node_instance = node['node_instance']
                    break
            if found_flag:
                break

        # Perform "Type check" before linking
        if not source_pin_type:
            self.logger.warning("Could not get source pin type")
        elif not destination_pin_type:
            self.logger.warning("Could not get target pin type")
        # TODO: implement ways to prevent nodes looping
        # elif destination_node_tag in self.node_connection_dict:
        #     raise RuntimeError("Cannot loop the nodes")
        elif not (source_pin_type == destination_pin_type or destination_pin_type == InputPinType.WildCard):
            self.logger.warning("Cannot connect pins with different types")
        # Cannot connect exec pin to wildcard pins also
        elif source_pin_type == OutputPinType.Exec and destination_pin_type == InputPinType.WildCard:
            self.logger.warning("Cannot connect exec pins to wildcards")
        elif not source_pin_instance:
            self.logger.warning("Cannot find source pin instance from node dict")
        elif not target_pin_instance:
            self.logger.warning("Cannot find target pin instance from node dict")
        else:
            # First link occurrence
            if source_pin_type == OutputPinType.Exec:  # Direct flow links to flow_link_list
                if len(self.flow_link_list) == 0:
                    # Also disallowing already connected Exec pin to perform further linkage
                    if not source_pin_instance.is_connected:
                        try:
                            link = Link(source_node_tag,
                                        source_node_instance,
                                        source_pin_instance,
                                        source_pin_type,
                                        target_node_tag,
                                        target_node_instance,
                                        target_pin_instance,
                                        destination_pin_type,
                                        self.id)
                        except:
                            self.logger.exception("Failed to link")

                        if link:
                            self.flow_link_list.append(link)
                            # Set pin's connected status
                            source_pin_instance.is_connected = True
                            target_pin_instance.is_connected = True
                            source_pin_instance.connected_link_list.append(link)
                            target_pin_instance.connected_link_list.append(link)
                            # Update event dict to store target node tag if it's connected to an event node
                            if source_node_instance.node_type == NodeTypeFlag.Event:
                                self.tobe_exported_event_dict.update({source_node_tag: target_node_tag})
                        else:
                            self.logger.error("Cannot add a null link")
                # Check if duplicate linkage, can happen if user swap link direction
                else:
                    if not source_pin_instance.is_connected:
                        duplicate_flag = False
                        for node_link in self.flow_link_list:
                            if target_pin_instance == node_link.target_pin_instance:
                                duplicate_flag = True
                        if not duplicate_flag:
                            try:
                                link = Link(source_node_tag,
                                            source_node_instance,
                                            source_pin_instance,
                                            source_pin_type,
                                            target_node_tag,
                                            target_node_instance,
                                            target_pin_instance,
                                            destination_pin_type,
                                            self.id)
                            except:
                                self.logger.exception("Failed to link")
                            if link:
                                self.flow_link_list.append(link)
                                # Set pin's connected status
                                source_pin_instance.is_connected = True
                                target_pin_instance.is_connected = True
                                source_pin_instance.connected_link_list.append(link)
                                target_pin_instance.connected_link_list.append(link)
                                # Update event dict to store target node tag if it's connected to an event node
                                if source_node_instance.node_type == NodeTypeFlag.Event:
                                    self.tobe_exported_event_dict.update({source_node_tag: target_node_tag})
                            else:
                                self.logger.error("Cannot add a null link")
            else:  # Direct data links to data_link_list
                if len(self.data_link_list) == 0:
                    try:
                        link = Link(source_node_tag,
                                    source_node_instance,
                                    source_pin_instance,
                                    source_pin_type,
                                    target_node_tag,
                                    target_node_instance,
                                    target_pin_instance,
                                    destination_pin_type,
                                    self.id)
                    except:
                        self.logger.exception("Failed to link")

                    if link:
                        self.data_link_list.append(link)
                        # Mark the target node as dirty
                        target_node_instance.is_dirty = True
                        # Also update the nodes' data_link_list
                        source_node_instance.succeeding_data_link_list.append(link)
                        # Set pin's connected status
                        source_pin_instance.is_connected = True
                        target_pin_instance.is_connected = True
                        source_pin_instance.connected_link_list.append(link)
                        target_pin_instance.connected_link_list.append(link)
                    else:
                        self.logger.error("Cannot add a null link")
                # Check if duplicate linkage, can happen if user swap link direction
                else:
                    duplicate_flag = False
                    for node_link in self.data_link_list:
                        if target_pin_instance == node_link.target_pin_instance:
                            duplicate_flag = True
                    if not duplicate_flag:
                        try:
                            link = Link(source_node_tag,
                                        source_node_instance,
                                        source_pin_instance,
                                        source_pin_type,
                                        target_node_tag,
                                        target_node_instance,
                                        target_pin_instance,
                                        destination_pin_type,
                                        self.id)
                        except:
                            self.logger.exception("Failed to link")
                        if link:
                            self.data_link_list.append(link)
                            # Mark the target node as dirty
                            target_node_instance.is_dirty = True
                            # Also update the nodes' data_link_list
                            source_node_instance.succeeding_data_link_list.append(link)
                            # Set pin's connected status and store the link instance into both of the pins
                            source_pin_instance.is_connected = True
                            target_pin_instance.is_connected = True
                            source_pin_instance.connected_link_list.append(link)
                            target_pin_instance.connected_link_list.append(link)
                        else:
                            self.logger.error("Cannot add a null link")
        self.node_data_link_dict = sort_data_link_dict(self.data_link_list)
        self.node_flow_link_dict = sort_flow_link_dict(self.flow_link_list)
        if link:
            self.logger.info('**** Nodes linked ****')

        # Debug print
        if link:
            self.logger.debug(f'    sender                     :     {sender}')
            self.logger.debug(f'    source_pin_tag             :     {source_pin_instance}')
            self.logger.debug(f'    target_pin_tag             :     {target_pin_instance}')
            self.logger.debug(f'    self.data_link_list        :     {self.data_link_list}')
            self.logger.debug(f'    self.flow_link_list        :     {self.flow_link_list}')
            self.logger.debug(f'    self.node_dict             :     {self.node_dict}')
            self.logger.debug(f'    self.node_data_link_dict   :     {self.node_data_link_dict}')
            self.logger.debug(f'    self.node_flow_link_dict   :     {self.node_flow_link_dict}')
            self.logger.debug(f'    self.event_dict            :     {self.tobe_exported_event_dict}')

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
                    link.target_pin_instance.is_connected = False
                    # Set target pin's connected link instance to None
                    link.target_pin_instance.connected_link_list.clear()
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
                    link.target_pin_instance.is_connected = False
                    # Also set the connected link instance of the pins to None
                    link.source_pin_instance.connected_link_list.clear()
                    link.target_pin_instance.connected_link_list.clear()
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
                            next_node = pin_info['pin_instance'].connected_link_list[0].target_node_instance
                            break
            else:
                for pin_info in current_node.pin_list:
                    if pin_info['meta_type'] == 'FlowOut':
                        if pin_info['pin_instance'].is_connected and pin_info['label'] == 'False':
                            next_node = pin_info['pin_instance'].connected_link_list[0].target_node_instance
                            break
        # If normal Blueprint node which has only one Exec pin out then next_node is deterministic
        else:
            # First found exec out pin will be the next node (this might be changed later)
            for pin_info in current_node.pin_list:
                if pin_info['meta_type'] == 'FlowOut':
                    if pin_info['pin_instance'].is_connected:
                        next_node = pin_info['pin_instance'].connected_link_list[0].target_node_instance
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
                            anchors.append(pin_info['pin_instance'].connected_link_list[0].target_node_instance)
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
