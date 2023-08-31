from collections import OrderedDict

from core.enum_types import NodeTypeFlag, PinMetaType
from core.utils import dpg_get_value
from core.classes.pin import *


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
    elif pin_type == InputPinType.StringArray:
        return PinStringArray
    else:
        return PinBase


class NodeModule:
    def __init__(self,
                 python_module,
                 import_path,
                 node_type: NodeTypeFlag):
        self.python_module = python_module
        self.import_path = import_path
        self.node_type = node_type


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

    @property
    def internal_data(self) -> dict:
        return self._internal_data

    @property
    def id(self) -> int:
        return self._node_id

    def __init__(self,
                 parent=None,
                 setting_dict=None,
                 callback=None,
                 pos=None,
                 import_path=None,
                 node_tag=None,
                 label='',
                 internal_data=None
                 ):
        # self._internal_data = None
        self._tag_node_name = None
        self._node_setting_dict = None
        self._callback = callback
        self._node_id = -1
        if pos is None:
            self._pos = [0, 0]
        else:
            self._pos = pos
        if label:
            self.node_label = label
        self._parent = parent
        self._setting_dict = setting_dict
        self._setup_dict = {'ver': self.ver}
        if node_tag:
            self._node_tag = node_tag
        self._node_tag = generate_uuid()
        self._pin_list = []
        if import_path is None:
            self._import_path = ''
        else:
            self._import_path = import_path
        self._import_path = import_path
        self._default_output_value_dict = {}
        if internal_data is None:
            self._internal_data = {}
        else:
            self._internal_data = internal_data

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
                meta_type = PinMetaType.FlowIn
            else:
                meta_type = PinMetaType.DataIn
            pin = pin_class(parent=self.node_tag, attribute_type=attribute_type, pin_type=pin_type,
                            label=label,
                            input_window_width=self.setting_dict['input_window_width'],
                            callback=callback)
            self._pin_list.append(OrderedDict({
                'uuid': pin.pin_tag,
                'pin_instance': pin,
                'label': label,
                'meta_type': meta_type,
                'type': pin.pin_type
            }))
            if pin_type != InputPinType.Exec:
                self._pin_list[-1].update({'value': dpg_get_value(pin.value_tag)})
        else:
            attribute_type = dpg.mvNode_Attr_Output
            pin_class = get_pin_class(pin_type)
            # Exec pins get different meta_type
            if pin_type == InputPinType.Exec:
                meta_type = PinMetaType.FlowOut
            else:
                meta_type = PinMetaType.DataOut
            pin = pin_class(parent=self.node_tag, attribute_type=attribute_type, pin_type=pin_type,
                            label=label,
                            input_window_width=self.setting_dict['input_window_width'])
            self._pin_list.append(OrderedDict({
                'uuid': pin.pin_tag,
                'pin_instance': pin,
                'label': label,
                'meta_type': meta_type,
                'type': pin.pin_type
            }))
            if meta_type == 'DataOut':
                self._default_output_value_dict.update({label: dpg_get_value(pin.value_tag)})
            # Output pins will need to store a default value for Tools viewer in case node is not computed for value
            # therefore prompt KeyErrorException
            if pin_type != OutputPinType.Exec:
                self._pin_list[-1].update({'default_value': dpg_get_value(pin.value_tag)})

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
                    self._pin_list.append(OrderedDict({
                        'uuid': out_exec_pin.pin_tag,
                        'pin_instance': out_exec_pin,
                        'label': 'Exec Out',
                        'meta_type': PinMetaType.FlowOut,
                        'type': out_exec_pin.pin_type
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

    @staticmethod
    def node_right_click_menu():
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
                            internal_data=self.internal_data,
                            import_path=self.import_path)
        return node

    @staticmethod
    def run(internal_data_dict: dict) -> dict:
        assert not hasattr(super(), 'Run')
        return {}

    def on_node_deletion(self, **kwargs):
        assert not hasattr(super(), 'Close')

    def update_internal_input_data(self):
        for pin_info in self._pin_list:
            if pin_info['meta_type'] == PinMetaType.DataIn:
                pin_value = dpg.get_value(pin_info['pin_instance'].value_tag)
                if pin_value is not None:
                    self._internal_data.update({pin_info['label']: pin_value})

    def on_pin_value_change(self, sender):
        # self.is_dirty = True
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
                 internal_data=None,
                 import_path=None
                 ):
        super().__init__(parent=parent, setting_dict=setting_dict, callback=callback,
                         pos=pos, internal_data=internal_data, import_path=import_path)
        self.node_label = node_label
        self.node_type = node_type
        self.pin_dict = pin_dict
        if run_function:
            self.run = run_function
        self.initialize_node(parent, self.node_label, pos=self.pos)
