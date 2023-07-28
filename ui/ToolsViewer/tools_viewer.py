import logging
import dearpygui.dearpygui as dpg
from ui.ToolsViewer.utils import load_json, get_node_by_id, create_queueHandler_logger
from importlib import import_module
from multiprocessing import Queue, current_process
import psutil


# TODO re-apply new NG logics to this, including: var node loading, caching, dirty trigger for var on exec
class ToolsViewer:
    """Main class to handle exported data from Node Editor and display them to DPG widgets
    """
    _ver = '0.0.1'
    tools_viewer_label = 'Tools Viewer'
    tools_viewer_tag = 'ToolsViewer'

    @property
    def exec_flag(self) -> bool:
        """
        Flag to signal the main DearPyGui loop for event execution

        :return: A flag that stated if ToolsViewer needs its events executed
        :rtype: bool
        """
        return self._exec_flag

    @exec_flag.setter
    def exec_flag(self, value: bool):
        self._exec_flag = value

    @property
    def requested_exec_node_tag(self) -> str:
        return self._requested_exec_node_tag

    @requested_exec_node_tag.setter
    def requested_exec_node_tag(self, value):
        self._requested_exec_node_tag = value

    @property
    def compile_list(self) -> list:
        return self._compile_list

    @property
    def node_dict(self) -> dict:
        return self._node_dict

    @node_dict.setter
    def node_dict(self, value: dict):
        self._node_dict = value

    @property
    def event_dict(self) -> dict:
        return self._event_dict

    @property
    def node_list(self) -> list:
        return self._node_list

    @property
    def data_link_list(self) -> list:
        return self._data_link_list

    @property
    def flow_link_list(self) -> list:
        return self._flow_link_list

    def __init__(
        self,
        use_debug_print=False,
        setting_dict=None,
        logging_queue=Queue()
    ):
        self._compile_list = []
        self._exec_flag = False
        self._requested_exec_node_tag = None
        self._use_debug_print = use_debug_print
        self._node_dict = {}
        self._event_dict = {}
        self._node_list = []
        self._data_link_list = []
        self._flow_link_list = []
        if setting_dict is None:
            self._setting_dict = {}
        else:
            self._setting_dict = setting_dict

        self.logger = create_queueHandler_logger(__name__, logging_queue, self._use_debug_print)

        # Main viewport
        self._create_main_window([])
        # Menu Bar
        with dpg.viewport_menu_bar(label='MenuBar'):
            # Export/Import file
            with dpg.menu(label='File'):
                dpg.add_menu_item(
                    tag='Menu_File_Load',
                    label='Open',
                    callback=self._callback_file_load_menu,
                    user_data='Menu_File_Load'
                )
                dpg.add_menu_item(
                    tag='Menu_File_Export',
                    label='Save',
                    callback=self._callback_help_menu,
                    user_data='Menu_File_Help'
                )

    def _callback_close_window(self, sender, app_data, user_data):
        pass

    def _callback_file_load_menu(self):
        """
        Load JSON file
        """
        data = load_json()
        try:
            self._event_dict = data.get('events', None)
            self._node_list = data.get('nodes', None)
            self._data_link_list = data.get('data_links', None)
            self._flow_link_list = data.get('flows', None)
        except AttributeError:
            pass
        self._node_dict.clear()

        # Store list containing events correspond to displayed buttons on UI
        public_ui = []

        for uid in self._event_dict.keys():
            nodes = get_node_by_id(self._node_list, uid)
            if "event_node" in nodes["type"]:
                public_ui.append({'button_name': nodes['label'], 'id': nodes['id']})
        # Refresh main window
        dpg.delete_item(self.tools_viewer_tag + 'Window')
        if public_ui:
            self._create_main_window(public_ui)  # Recreate the main window with the updated data
            # Precompile the events
            self._compile_list = public_ui
            self.compile_events()
            self.logger.info('UI loaded successfully!')
            # self._compile_flag = True

    def _callback_help_menu(self, sender, app_data, user_data):
        pass

    def _create_main_window(self, input_var: list):
        # Create your main window and other widgets here
        with dpg.window(
            tag=self.tools_viewer_tag + 'Window',
            label=self.tools_viewer_label,
            width=self._setting_dict.get('viewport_width', 500),
            height=self._setting_dict.get('viewport_height', 800),
            menubar=True,
            on_close=self._callback_close_window
        ):
            with dpg.child_window(label="Window 1",
                                  height=self._setting_dict['viewport_height'] - 200,
                                  autosize_x=True):
                for each in input_var:
                    if each['button_name']:
                        dpg.add_button(label=each['button_name'],
                                       tag=each['id'] + 'Event',
                                       width=-1,
                                       # span_columns=True,
                                       height=self._setting_dict['button_height'],
                                       callback=self.trigger_event,
                                       user_data=each['id']
                                       )
                        with dpg.tooltip(each['id'] + 'Event'):
                            dpg.add_text('A tool tip of {}!'.format(each['id']))
                        # dpg.add_selectable()
            with dpg.child_window(label="Window 2",
                                  autosize_x=True,
                                  horizontal_scrollbar=True):
                dpg.add_text(tag='log', tracked=False, track_offset=1.0)
        dpg.set_primary_window(self.tools_viewer_tag + 'Window', True)

    def trigger_event(self, sender, app_data, user_data):
        self.exec_flag = True
        self._requested_exec_node_tag = user_data

    def worker(self, input_queue: Queue, logging_queue: Queue):
        logger = create_queueHandler_logger(__name__ + '.' + current_process().name,
                                            logging_queue,
                                            self._use_debug_print)
        for tag in iter(input_queue.get, 'STOP'):
            # print(tag)
            self.execute_event(tag, logger)

    def execute_event(self, event, logger: logging.Logger):
        event_node_tag = event
        logger.info(f'**** Exec event : {event_node_tag}')
        # Reset exec state
        self.exec_flag = False
        # Dirty mark and propagate any exposed input nodes
        for key, value in self.node_dict.items():
            if value['is_exposed']:
                self.dirty_propagate(key, logger)
        # Get first node instance that is connected to this event node
        current_node_tag = self.event_dict.get(event_node_tag, None)
        if not current_node_tag:
            logger.error('Cannot find the event, this could be due to the event node not connected to anything!')
            return 1
        anchors = []
        if anchors:
            anchors.clear()
        self.forward_propagate_flow(current_node_tag, anchors, logger)
        self.flow_control_redirect(anchors, logger)
        # Logging is slow (due to Queue) so the process is killed before having the chance to log
        # logger.info(f'***** Event {event_node_tag} finished *****')
        # Clean up process
        psutil.Process(current_process().pid).kill()

    def flow_control_redirect(self, anchors: list, logger: logging.Logger):
        if not anchors:
            return 0
        for anchor in anchors:
            sub_anchors = []
            if sub_anchors:
                sub_anchors.clear()
            self.forward_propagate_flow(anchor, sub_anchors, logger)
            if sub_anchors:
                self.flow_control_redirect(sub_anchors, logger)

    def forward_propagate_flow(self,
                               node_tag: str,
                               anchors: list,
                               logger: logging.Logger):
        _current_node_info = self.node_dict.get(node_tag, None)
        if _current_node_info is None:
            logger.error(f'Could not find node info for {node_tag}')
            return -1
        self.compute_node(node_tag, logger)

        # Find in flows list if exist a flow link to another node
        next_node = None
        # Branch node got to explicitly decide next_node based on its condition bool value
        if _current_node_info['label'] == 'Branch':
            condition = _current_node_info['internal_data'].get('Condition', None)
            if condition is None:
                logger.error(f'Can not query condition value for this branch node : {_current_node_info}')
                return -1
            if condition is True or condition == 'True':
                for _pin_info in _current_node_info['pins']:
                    if _pin_info['meta_type'] == 'FlowOut':
                        if _pin_info['is_connected'] and _pin_info['label'] == 'True':
                            next_node = _pin_info['connect_to_node']
                            break
            else:
                for _pin_info in _current_node_info['pins']:
                    if _pin_info['meta_type'] == 'FlowOut':
                        if _pin_info['is_connected'] and _pin_info['label'] == 'False':
                            next_node = _pin_info['connect_to_node']
                            break
        # If normal Blueprint node which has only one Exec pin out then next_node is deterministic
        else:
            # First found exec out pin will be the next node (this might be changed later)
            for _pin_info in _current_node_info['pins']:
                if _pin_info['meta_type'] == 'FlowOut':
                    if _pin_info['is_connected']:
                        next_node = _pin_info['connect_to_node']
                        break
        # Store anchors point if current node is sequential nodes
        if _current_node_info['meta_type'] == 5:  # Sequential
            if _current_node_info['label'] == 'Sequence':
                for _pin_info in _current_node_info['pins']:
                    if _pin_info['meta_type'] == 'FlowOut':
                        if _pin_info['is_connected']:
                            anchors.append(_pin_info['connect_to_node'])
                return 0
            elif _current_node_info['label'] == 'Do N':
                iteration_num = _current_node_info['internal_data'].get('N', None)
                if iteration_num and next_node:
                    for i in range(iteration_num):
                        anchors.append(next_node)
                    return 0
                else:
                    logger.error(f'Could not find anchors point upon processing this node: {_current_node_info} ')
                    pass
        if next_node:
            self.forward_propagate_flow(next_node, anchors, logger)
        else:
            return 0

    def compute_node(self, node_tag: str, logger: logging.Logger):
        _current_node_info = self.node_dict.get(node_tag, None)
        if _current_node_info is None:
            logger.error(f'Could not find node info for {node_tag}')
            return -1
        # Blueprint nodes still need to be executed even if it's clean
        if not _current_node_info['is_dirty'] and \
            (_current_node_info['meta_type'] & 3 or _current_node_info['meta_type'] & 5):
            self.compute_internal_output_data(node_tag, logger)
        # If the node is dirty, perform computing output values from inputs
        if _current_node_info['is_dirty'] and _current_node_info['meta_type'] & 1:
            # Go through all input data pins and compute for preceding nodes if found dirty
            for _pin_info in _current_node_info['pins']:
                if _pin_info['meta_type'] == 'DataIn':
                    if _pin_info['is_connected'] is False:
                        continue
                    connected_to_node = _pin_info['connect_to_node']
                    pre_node_info = self.node_dict.get(connected_to_node, None)
                    if not pre_node_info:
                        logger.error(f'Could not find node info that matches this id : {connected_to_node}')
                        continue
                    # If the pre-node also is dirty and not an exec node (to avoid premature-execution),
                    # recursively compute its output values as well
                    if pre_node_info['is_dirty'] and pre_node_info['meta_type'] != 3:
                        self.compute_node(connected_to_node, logger)
            self.compute_internal_output_data(node_tag, logger)
        else:
            return 0

    def compute_internal_output_data(self, node_tag: str, logger: logging.Logger):
        node_info = self.node_dict.get(node_tag, None)
        if node_info is None:
            logger.error(f'Could not find node_info for {node_info}')
            return -1
        for pin_info in node_info['pins']:
            if pin_info['meta_type'] == 'DataIn' and pin_info['is_connected']:
                # Get preceding pin value and assign it to current one
                preceding_node_info = self.node_dict.get(pin_info['connect_to_node'], None)
                connected_to_pin = None
                try:
                    connected_to_pin = pin_info['connect_to_pin']
                    connected_pin_value = None
                    for pre_pin_info in preceding_node_info['pins']:
                        if pre_pin_info['id'] == connected_to_pin:
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
        for pin_info in node_info['pins']:
            if pin_info['meta_type'] == 'DataIn':
                internal_data.update({pin_info['label']: pin_info['value']})
        self.node_dict[node_tag]['internal_data'] = internal_data
        # Compute output pin values
        Run = node_info['run']
        Run(node_info['internal_data'])
        # Update the output pins' value with fresh internal data
        for pin_info in node_info['pins']:
            if pin_info['meta_type'] == 'DataOut':
                for key, value in self.node_dict[node_tag]['internal_data'].items():
                    if key == pin_info['label']:
                        pin_info['value'] = value
                        break
        # After computing for all outputs, mark this node as clean
        node_info['is_dirty'] = False
        # Update back to the master node dict
        self.node_dict.update({node_tag: node_info})
        if self._use_debug_print:
            logger.debug(f'Internal input data for node {node_info} has been computed')
            logger.debug(node_info['internal_data'])
            pass

    def dirty_propagate(self, current_node_tag: str, logger: logging.Logger):
        current_node_info = self.node_dict.get(current_node_tag, None)
        if current_node_info is None:
            logger.error(f'Could not find node_info for {current_node_tag}')
            return -1
        if current_node_info['is_dirty']:
            # Do nothing
            if self._use_debug_print:
                logger.debug(f'Node {current_node_tag} is already dirty so no propagation needed!')
                pass
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
            self.dirty_propagate(pin_info['connect_to_node'], logger)

    def compile_events(self):
        # self.compile_flag = False
        for first_exec_node_tag in list(self._event_dict.values()):
            for i, node_info in enumerate(self._node_list):
                if node_info.get('id', None) == first_exec_node_tag:
                    self.forward_construct_node(node_info, i)
                    break

    def forward_construct_node(self, current_node_info: dict, current_node_index: int):
        self.backward_construct_node(current_node_info, current_node_index)
        self.logger.debug(f'***** Forward construction for node: {current_node_info}')
        for i, pin in enumerate(current_node_info['pins']):
            # Only accept output exec pin
            if pin['meta_type'] != 'FlowOut':
                continue
            # Find in flows list if exist a flow link to another node
            found_link_flag = False
            for flow_link in self.flow_link_list:
                # Find the connected following node
                if flow_link[0] == pin['id']:
                    self.logger.debug(f'Found matching flow link that is connected with this pin {flow_link[0]}')
                    following_node = None
                    following_node_info = None
                    following_node_index = -1
                    for j, node in enumerate(self.node_list):
                        for pin_info in node['pins']:
                            if pin_info['id'] == flow_link[1]:
                                following_node = node['id']
                                following_node_info = node
                                following_node_index = j
                                break
                        if following_node:
                            break
                    if following_node is not None:
                        found_link_flag = True
                        self.node_list[current_node_index]['pins'][i].update({'is_connected': True,
                                                                              'connect_to_node': following_node})
                        self.forward_construct_node(following_node_info, following_node_index)
                        break

            if found_link_flag is False:
                self.node_list[current_node_index]['pins'][i].update({'is_connected': False})

    def backward_construct_node(self, current_node_info: dict, current_node_index: int):
        # Backward propagation to find related nodes
        # update link info to pins :
        # 1. Is connected
        # 2. Connected to node :
        # 3. Connected to pin:
        # 4. If connected to a static data chain then remove the above 3 with a default value
        # temp_pins_list = deepcopy(current_node_info['pins'])
        for i, pin in enumerate(current_node_info['pins']):
            # Skip exec pins
            if pin['pin_type'] == 5:
                continue
            # Skip data output pins
            if pin['meta_type'] == 'DataOut':
                continue
            found_link_flag = False
            for data_link in self.data_link_list:
                if data_link[1] == pin['id']:
                    # Find the connected preceding node
                    self.logger.debug(f'Found matching data link that is connected with this pin {data_link[1]}')
                    preceding_node = None
                    preceding_node_info = None
                    preceding_node_index = -1
                    for j, node in enumerate(self.node_list):
                        for pin_info in node['pins']:
                            if pin_info['id'] == data_link[0]:
                                preceding_node = node['id']
                                preceding_node_info = node
                                preceding_node_index = j
                                break
                        if preceding_node:
                            break
                    if preceding_node is not None:
                        found_link_flag = True
                        self.node_list[current_node_index]['pins'][i].update({'is_connected': True,
                                                                              'connect_to_pin': data_link[0],
                                                                              'connect_to_node': preceding_node})
                        # Update the output data pin of preceding node as well
                        for k, pre_pin_info in enumerate(self.node_list[preceding_node_index]['pins']):
                            if pre_pin_info['id'] == data_link[0]:
                                self.node_list[preceding_node_index]['pins'][k].update({'is_connected': True,
                                                                                        'connect_to_pin':
                                                                                            data_link[
                                                                                                1],
                                                                                        'connect_to_node':
                                                                                            current_node_info[
                                                                                                'id']})
                        if self._use_debug_print:
                            self.logger.debug(f'Updated info to pin : {data_link[1]}')
                            pass

                        if preceding_node_info is None or preceding_node_index == -1:
                            self.logger.error(f'Cannot find the node info that matches id : {preceding_node}')
                            continue
                        # Only if the preceding node is a process node then perform recursion
                        if preceding_node_info['meta_type'] == 1:
                            self.backward_construct_node(preceding_node_info, preceding_node_index)
                    else:
                        self.logger.error(
                            f'Could not find preceding node although this pin {data_link[1]} is connected')
                        continue
                    break
            if found_link_flag is False:
                self.node_list[current_node_index]['pins'][i].update({'is_connected': False})
        # Update node_dict
        node_type = current_node_info.get('type', '')
        import_path = '.'.join(node_type.split('.')[0:-1])
        module = import_module(import_path)
        # Hardcode this because every node definition should declare a Node class
        lib_attr = getattr(module, 'Node')
        # Construct node's internal data
        internal_data = {}
        for pin_info in self.node_list[current_node_index]['pins']:
            if pin_info['meta_type'] == 'DataIn':
                internal_data.update({pin_info['label']: pin_info['value']})
        # Store to master node_dict
        self.node_dict.update({current_node_info['id']: {
            'label': self.node_list[current_node_index]['label'],
            'pins': self.node_list[current_node_index]['pins'],
            'meta_type': self.node_list[current_node_index]['meta_type'],
            'is_exposed': current_node_info.get('is_exposed', False),
            'run': lib_attr.run,
            'is_dirty': True,
            'internal_data': internal_data
        }})
        self.logger.debug(f'***Backward construction node for {current_node_info}')
