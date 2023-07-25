from collections import OrderedDict
from enum import IntFlag

from ui.NodeEditor.utils import dpg_set_value, dpg_get_value
from ui.NodeEditor.classes.pin import *


def get_pin_class(pin_type):
    """
    Get pin class that corresponds to pin_type
    :param enumerate pin_type: pin_type from pin enumeration
    :return: pin class
    """
    # Since pin_type are Int enums, only need to compare pin_type to InputPinType
    if pin_type == InputPinType.Exec:
        return PinExec
    elif pin_type == InputPinType.Int:
        return PinInt
    elif pin_type == InputPinType.Float:
        return PinFloat
    elif pin_type == InputPinType.String:
        return PinString
    elif pin_type == InputPinType.MultilineString:
        return PinMultilineString
    elif pin_type == InputPinType.Password:
        return PinPassword
    elif pin_type == InputPinType.Json:
        return PinJson
    elif pin_type == InputPinType.Bool:
        return PinBool
    elif pin_type == InputPinType.WildCard:
        return PinWildCard
    elif pin_type == InputPinType.PerforceInstance:
        return PerforceInstancePin
    else:
        return PinBase


class NodeTypeFlag(IntFlag):
    Dummy = 0
    Pure = 1 << 0
    Exec = 1 << 1
    Sequential = 1 << 2 | Pure
    Event = 1 << 3
    Blueprint = Pure | Exec


class BaseNode:
    """
        Root class for node

        :param parent: tag of the Node Editor
        :type parent: str
        :param setting_dict: dictionary that holds settings and position of node
        :type setting_dict: dict
        :param callback: callback function of this node
        :type callback: func
        :param pos: node's position
        :type pos: list
        """
    # Static members
    ver = '0.0.1'
    node_label = 'Base Node'
    node_type = NodeTypeFlag.Dummy
    pin_dict = OrderedDict({})

    @property
    def node_tag(self) -> str:
        return self._node_tag

    @property
    def import_path(self) -> str:
        return self._import_path

    @property
    def pin_list(self) -> list:
        return self._pin_list

    @property
    def node_setting_dict(self) -> dict:
        return {}

    @node_setting_dict.setter
    def node_setting_dict(self, value: dict):
        pass

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, value):
        self._callback = value

    @property
    def pos(self) -> list:
        return self._pos

    @pos.setter
    def pos(self, value: list):
        self._pos = value

    @property
    def parent(self) -> str:
        return self._parent

    @parent.setter
    def parent(self, value: str):
        self._parent = value

    @property
    def setting_dict(self) -> dict:
        return self._setting_dict

    @setting_dict.setter
    def setting_dict(self, value):
        self._setting_dict = value

    @property
    def is_dirty(self) -> bool:
        return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, value: bool):
        self._is_dirty = value
        # Go down the chain of succeeding nodes to mark them as 'dirty'
        for link in self._succeeding_data_link_list:
            # Get the target node
            target_node = link.target_node_instance
            # Mark it status as 'dirty'
            target_node.is_dirty = True

    @property
    def is_executed(self) -> bool:
        return self._is_executed

    @is_executed.setter
    def is_executed(self, value: bool):
        self._is_executed = value

    @property
    def internal_data(self) -> dict:
        return self._internal_data

    @property
    def succeeding_data_link_list(self) -> list:
        return self._succeeding_data_link_list

    @succeeding_data_link_list.setter
    def succeeding_data_link_list(self, value: list):
        self._succeeding_data_link_list = value

    @property
    def id(self) -> int:
        return self._node_id

    def __init__(self,
                 parent=None,
                 setting_dict=None,
                 callback=None,
                 pos=None,
                 import_path='',
                 node_tag=None,
                 succeeding_data_link_list=None,
                 label='',
                 internal_data=None
                 ):
        self._tag_node_name = None
        self._node_setting_dict = None
        self._callback = callback
        self._node_id = -1
        if pos is None:
            self._pos = [0, 0]
        else:
            self._pos = pos
        # Override node_label if param label is not None
        if label:
            self.node_label = label
        self._parent = parent
        self._setting_dict = setting_dict
        self._setup_dict = {'ver': self.ver}
        if node_tag:
            self._node_tag = node_tag
        self._node_tag = generate_uuid()
        self._pin_list = []
        self._import_path = import_path
        self._default_output_value_dict = {}
        if internal_data is None:
            self._internal_data = {}
        else:
            self._internal_data = internal_data
        # self._is_prompt_for_input_tag = ''
        if succeeding_data_link_list:
            self._succeeding_data_link_list = succeeding_data_link_list
        else:
            self._succeeding_data_link_list = []

        # ____FLAGS____
        if self.node_type & NodeTypeFlag.Event:
            self._is_dirty = False
        else:
            self._is_dirty = True
        self._is_executed = False

    def construct_pin(self, pin_type, label='', callback=None):
        """
        Construct pin
        :param pin_type: type of the pin
        :param label: name of the pin (uuid is internally assigned)
        :param callback: callback function on pin's value changed
        """
        if pin_type.__class__ == InputPinType:
            attribute_type = dpg.mvNode_Attr_Input
            pin_class = get_pin_class(pin_type)
            # Exec pins get different meta_type
            if pin_type == InputPinType.Exec:
                meta_type = 'FlowIn'
            else:
                meta_type = 'DataIn'
            pin = pin_class(parent=self.node_tag, attribute_type=attribute_type, pin_type=pin_type,
                            label=label,
                            input_window_width=self.setting_dict['input_window_width'],
                            callback=callback)
            self.pin_list.append(OrderedDict({
                'id': pin.pin_tag,
                'pin_instance': pin,
                'label': label,
                'meta_type': meta_type,
                'pin_type': pin.pin_type
            }))
            if pin_type != InputPinType.Exec:
                self.pin_list[-1].update({'value': dpg_get_value(pin.value_tag)})
            # Update internal data
            if pin_type != InputPinType.Exec:
                self._internal_data.update({pin.label: pin.default_data})
        else:
            attribute_type = dpg.mvNode_Attr_Output
            pin_class = get_pin_class(pin_type)
            # Exec pins get different meta_type
            if pin_type == InputPinType.Exec:
                meta_type = 'FlowOut'
            else:
                meta_type = 'DataOut'
            pin = pin_class(parent=self.node_tag, attribute_type=attribute_type, pin_type=pin_type,
                            label=label,
                            input_window_width=self.setting_dict['input_window_width'])
            self.pin_list.append(OrderedDict({
                'id': pin.pin_tag,
                'pin_instance': pin,
                'label': label,
                'meta_type': meta_type,
                'pin_type': pin.pin_type
            }))
            if meta_type == 'DataOut':
                self._default_output_value_dict.update({label: dpg_get_value(pin.value_tag)})
            # Output pins will need to store a default value for Tools viewer in case node is not computed for value
            # therefore prompt KeyErrorException
            if pin_type != OutputPinType.Exec:
                self.pin_list[-1].update({'default_value': dpg_get_value(pin.value_tag)})
            # Update internal data
            if pin_type != InputPinType.Exec:
                self._internal_data.update({pin.label: pin.default_data})

    def initialize_node(self, parent, label, pos=None):
        """
        Construct elements in current node instance
        :param parent: parent of the node, typically the Node Editor
        :param label: label of the node
        :param pos: spawn position
        """
        if pos is None:
            _pos = [0, 0]
        else:
            _pos = pos
        with dpg.node(
            tag=self.node_tag,
            parent=parent,
            label=label,
            pos=_pos
        ) as self._node_id:
            if self.pin_dict:
                # First check node type to add common pins
                if self.node_type & NodeTypeFlag.Pure:
                    # TODO: change styling to Green background for example (pure functions in UE)
                    pass
                # For Event pin, need to explicitly define PinEvent with special callback
                if self.node_type & NodeTypeFlag.Event:
                    out_exec_pin = PinEvent(self.node_tag, dpg.mvNode_Attr_Output, OutputPinType.Exec, label='Exec out',
                                            input_window_width=self.setting_dict['input_window_width'],
                                            callback=self.callback, user_data=self.node_tag)
                    self.pin_list.append(OrderedDict({
                        'id': out_exec_pin.pin_tag,
                        'pin_instance': out_exec_pin,
                        'label': 'Exec Out',
                        'meta_type': 'FlowOut',
                        'pin_type': out_exec_pin.pin_type
                    }))

                if self.node_type & NodeTypeFlag.Exec:
                    self.construct_pin(InputPinType.Exec, 'Exec In')
                    self.construct_pin(OutputPinType.Exec, 'Exec Out')
                if self.node_type & NodeTypeFlag.Sequential:
                    pass
                # Loop through list to add pins
                for label, pin_type in self.pin_dict.items():
                    self.construct_pin(pin_type, label, self.on_pin_value_change)
            elif self.node_type is not NodeTypeFlag.Dummy:
                assert "Non-Dummy nodes cannot contain zero pins!"
            else:
                with dpg.node_attribute(
                    tag=generate_uuid(),
                    attribute_type=dpg.mvNode_Attr_Static
                ):
                    dpg.add_text(label="dummy",
                                 tag=generate_uuid())
        # Right click context menu
        with dpg.item_handler_registry() as item_handler_id:
            dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Right,
                                         callback=self.node_right_click_menu)
        dpg.bind_item_handler_registry(self._node_id, dpg.last_container())

    def node_right_click_menu(self):
        with dpg.window(
            popup=True,
            autosize=True,
            no_move=True,
            no_open_over_existing_popup=True,
            no_saved_settings=True,
            max_size=[200, 200],
            min_size=[10, 10]
        ):
            dpg.add_selectable(label='Delete')
            dpg.add_selectable(label='Cut')
            dpg.add_selectable(label='Copy')
            dpg.add_selectable(label='Duplicate')

    def create_node(self, **kwargs):
        assert not hasattr(super(), 'CreateNode')
        if kwargs:
            self.callback = kwargs.get('callback', None)
            self._internal_data = kwargs.get('internal_data', None)
        node = NodeInstance(self.parent,
                            self.setting_dict,
                            self.callback,
                            self.pos,
                            self.node_label,
                            self.node_type,
                            self.pin_dict,
                            run_function=self.run,
                            internal_data=self.internal_data)
        return node

    @staticmethod
    def run(internal_data_dict: dict) -> dict:
        assert not hasattr(super(), 'Run')
        return {}

    def query_input_value(self,
                          link
                          ):
        """
        Update input pins' values with the connection info to preceding nodes
        """
        assert not hasattr(super(), 'query_input_values')
        if link.source_pin_type is not OutputPinType.Exec:
            source_value = dpg_get_value(link.source_pin_instance.value_tag)
            dpg_set_value(link.target_pin_instance.value_tag, source_value)
            return source_value

    def refresh_output_pin_value(self):
        for pin_label, default_value in self._default_output_value_dict.items():
            self._internal_data[pin_label] = default_value
        self.update_output_pin_value()

    def update_custom_pin_value(self,
                                link):
        """
        Skip primitive pin value storage and query value from node's internal data
        """
        assert not hasattr(super(), 'update_custom_pin_value')
        if link.source_pin_type is not OutputPinType.Exec:
            # Try to get value from previous node's internal data instead if the pin's value is None
            # this case happens when the pin is of user created Pin Class
            source_value = link.source_node_instance.internal_data.get(link.source_pin_instance.label, None)
            self._internal_data.update({link.target_pin_instance.label: source_value})

    def on_node_deletion(self, **kwargs):
        assert not hasattr(super(), 'Close')

    def update_internal_input_data(self):
        for pin_info in self.pin_list:
            if pin_info['meta_type'] == 'DataIn':
                pin_value = dpg.get_value(pin_info['pin_instance'].value_tag)
                if pin_value is not None:
                    self._internal_data.update({pin_info['label']: pin_value})

    def compute_internal_output_data(self):
        # First update the input values
        for pin_info in self.pin_list:
            if pin_info['meta_type'] == 'DataIn' and \
                pin_info['pin_instance'].connected_link_list:
                queried_value = self.query_input_value(pin_info['pin_instance'].connected_link_list[0])
                # In case of custom pin, skip pin value data query
                if queried_value is None:
                    self.update_custom_pin_value(pin_info['pin_instance'].connected_link_list[0])
        # Update the internal data with the new inputs values first
        self.update_internal_input_data()
        # Compute new output values from node's Run()
        self.run(self._internal_data)
        # Update the whole internal data again
        # self._internal_data.update(computed_internal_data_dict)
        # Update the output pins' value with fresh internal data
        self.update_output_pin_value()
        # After computing for all outputs, mark this node as clean
        self._is_dirty = False
        # This node is executed!
        self._is_executed = True

    def update_output_pin_value(self):
        for pin_info in self.pin_list:
            if pin_info['meta_type'] == 'DataOut':
                for key, value in self._internal_data.items():
                    if key == pin_info['label']:
                        dpg_set_value(pin_info['pin_instance'].value_tag, value)
                        break

    def on_pin_value_change(self, sender):
        self.is_dirty = True
        self.update_internal_input_data()


class NodeInstance(BaseNode):
    def __init__(self,
                 parent=None,
                 setting_dict=None,
                 callback=None,
                 pos=None,
                 node_label=None,
                 node_type=None,
                 pin_dict=None,
                 run_function=None,
                 internal_data=None
                 ):
        super().__init__(parent=parent, setting_dict=setting_dict, callback=callback,
                         pos=pos, internal_data=internal_data)
        self.node_label = node_label
        self.node_type = node_type
        self.pin_dict = pin_dict
        if run_function:
            self.run = run_function
        self.initialize_node(parent, self.node_label, pos=self.pos)
