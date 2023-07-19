from ui.NodeEditor.utils import generate_uuid
from enum import auto, IntEnum
import dearpygui.dearpygui as dpg

# Define some colors for label of each type
BLUE = (92, 108, 255, 255)
TEAL = (84, 252, 255, 255)
PINK = (221, 84, 255, 255)
ORANGE = (255, 172, 84, 255)
WHITE = (255, 255, 255, 255)
GREEN = (102, 255, 51, 255)
DARKPINK = (204, 0, 153, 255)
DARKRED = (204, 51, 0, 255)
BROWN = (102, 51, 0, 255)


class InputPinType(IntEnum):
    """Enum class for pin input types, order matters"""
    String = auto()
    Float = auto()
    Json = auto()
    Int = auto()
    Exec = auto()
    WildCard = auto()
    Password = auto()
    Bool = auto()
    MultilineString = auto()
    PerforceInstance = auto()


class OutputPinType(IntEnum):
    """Enum class for pin outputs, order matters"""
    String = auto()
    Float = auto()
    Json = auto()
    Int = auto()
    Exec = auto()
    WildCard = auto()
    Password = auto()
    Bool = auto()
    MultilineString = auto()
    PerforceInstance = auto()


class PinBase:
    def __init__(self,
                 parent=None,
                 attribute_type=dpg.mvNode_Attr_Input,
                 pin_type=InputPinType.Int,
                 pin_shape=dpg.mvNode_PinShape_Circle,
                 input_window_width=240,
                 label='',
                 enable_input=True,
                 callback=None,
                 pin_tag=None,
                 show_data=True,
                 default_data=None,
                 user_data=None
                 ):
        self._parent = parent
        if pin_tag:
            self._pin_tag = pin_tag
        else:
            self._pin_tag = generate_uuid()
        self._pin_type = pin_type
        self._pin_shape = pin_shape
        self._attribute_type = attribute_type
        self._label = label
        self._enable_input = enable_input
        # Exec pins should not have value
        if self._pin_type != OutputPinType.Exec:
            self._value_tag = generate_uuid()  # tag only used if exist an "add_input_..." item
        else:
            self._value_tag = None
        self._callback = callback
        self._input_window_width = input_window_width - 76
        self._show_data = show_data
        self._default_data = default_data
        # Turn on this flag to show output pin value
        self._debug_mode = False
        self._is_connected = False
        self._connected_link_list = []
        self._user_data = user_data

    @property
    def parent(self):
        return self._parent

    @property
    def is_connected(self):
        return self._is_connected

    @is_connected.setter
    def is_connected(self, value):
        """
        Set status of this pin to connected, also hide its value display
        :return:
        """
        self._is_connected = value
        if self.value_tag:
            if self.attribute_type == dpg.mvNode_Attr_Input:
                try:
                    dpg.configure_item(self.value_tag, show=not value)
                except:
                    pass
            elif self.attribute_type == dpg.mvNode_Attr_Output and self._debug_mode:
                try:
                    dpg.configure_item(self.value_tag, show=not value)
                except:
                    pass

    @property
    def connected_link_list(self):
        return self._connected_link_list

    @connected_link_list.setter
    def connected_link_list(self, value):
        self._connected_link_list = value

    @property
    def enable_input(self) -> bool:
        return self._enable_input

    @property
    def value_tag(self) -> str:
        return self._value_tag

    @enable_input.setter
    def enable_input(self, value: bool):
        self._enable_input = value

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = value

    @property
    def pin_tag(self) -> str:
        return self._pin_tag

    @property
    def pin_type(self):
        return self._pin_type

    @property
    def attribute_type(self):
        return self._attribute_type

    @property
    def default_data(self):
        return self._default_data

    def CreatePin(self):
        """Create pins depends on instances' PinType"""
        # Input Pin
        if self.attribute_type == dpg.mvNode_Attr_Input:
            if self.pin_type == InputPinType.Int:  # Int input Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape,

                ):
                    dpg.add_text(default_value=self.label,
                                 color=BLUE)
                    dpg.add_slider_int(tag=self.value_tag,
                                       default_value=self._default_data,
                                       width=self._input_window_width,
                                       callback=self._callback,
                                       enabled=self.enable_input,
                                       show=self._show_data)
            elif self.pin_type == InputPinType.Float:  # Float input Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 color=GREEN)
                    dpg.add_slider_float(tag=self.value_tag,
                                         default_value=self._default_data,
                                         width=self._input_window_width,
                                         callback=self._callback,
                                         enabled=self.enable_input,
                                         show=self._show_data)
            elif self.pin_type == InputPinType.String:  # String input Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 color=PINK)
                    dpg.add_input_text(tag=self.value_tag,
                                       default_value=self._default_data,
                                       width=self._input_window_width,
                                       callback=self._callback,
                                       readonly=not self.enable_input,
                                       show=self._show_data)
            elif self.pin_type == InputPinType.Json:  # Json input Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 color=ORANGE)
                    dpg.add_input_text(tag=self.value_tag,
                                       width=self._input_window_width,
                                       callback=self._callback,
                                       readonly=not self.enable_input,
                                       multiline=True,
                                       tab_input=True,
                                       show=self._show_data)
            elif self.pin_type == InputPinType.Exec:  # Exec input Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 color=WHITE)
            elif self.pin_type == InputPinType.WildCard:  # Wildcard input Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 color=BROWN)
                    dpg.add_input_text(tag=self.value_tag,
                                       default_value=self._default_data,
                                       width=self._input_window_width,
                                       callback=self._callback,
                                       readonly=not self.enable_input,
                                       show=self._show_data)
            elif self.pin_type == InputPinType.Password:  # Password input Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 color=DARKPINK)
                    dpg.add_input_text(tag=self.value_tag,
                                       default_value=self._default_data,
                                       width=self._input_window_width,
                                       callback=self._callback,
                                       readonly=not self.enable_input,
                                       password=True,
                                       show=self._show_data)
            elif self.pin_type == InputPinType.Bool:  # Bool input Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 color=DARKRED)
                    dpg.add_checkbox(tag=self.value_tag,
                                     default_value=self._default_data,
                                     callback=self._callback,
                                     enabled=self.enable_input,
                                     show=self._show_data)
            elif self.pin_type == InputPinType.MultilineString:  # Multiline input Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label)
                    dpg.add_input_text(tag=self.value_tag,
                                       width=self._input_window_width,
                                       callback=self._callback,
                                       readonly=not self.enable_input,
                                       multiline=True,
                                       tab_input=True,
                                       show=self._show_data)
            else:  # User defined pin type
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 color=TEAL)
        elif self.attribute_type == dpg.mvNode_Attr_Output:
            # Output Pin
            if self.pin_type == OutputPinType.Int:  # Int output Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape,
                ):
                    dpg.add_text(default_value=self.label,
                                 indent=self._input_window_width,
                                 color=BLUE)
                    dpg.add_slider_int(tag=self.value_tag,
                                       default_value=self._default_data,
                                       width=self._input_window_width - 50,
                                       enabled=False,
                                       show=self._debug_mode,
                                       indent=self._input_window_width - 50)
            elif self.pin_type == OutputPinType.Float:  # Float output Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 indent=self._input_window_width,
                                 color=GREEN)
                    dpg.add_slider_float(tag=self.value_tag,
                                         default_value=self._default_data,
                                         width=self._input_window_width - 50,
                                         enabled=False,
                                         show=self._debug_mode,
                                         indent=self._input_window_width - 50)
            elif self.pin_type == OutputPinType.String:  # String output Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 indent=self._input_window_width,
                                 color=PINK)
                    dpg.add_input_text(tag=self.value_tag,
                                       default_value=self._default_data,
                                       width=self._input_window_width - 50,
                                       readonly=True,
                                       show=self._debug_mode,
                                       indent=self._input_window_width - 50)
            elif self.pin_type == OutputPinType.Json:  # Json output Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 indent=self._input_window_width,
                                 color=ORANGE)
                    dpg.add_input_text(tag=self.value_tag,
                                       width=self._input_window_width - 50,
                                       callback=self._callback,
                                       readonly=True,
                                       multiline=True,
                                       tab_input=True,
                                       show=self._debug_mode,
                                       indent=self._input_window_width - 50)
            elif self.pin_type == OutputPinType.Exec:  # Exec output Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 indent=self._input_window_width)
            elif self.pin_type == OutputPinType.WildCard:  # Wildcard input Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 indent=self._input_window_width,
                                 color=BROWN)
                    dpg.add_input_text(tag=self.value_tag,
                                       default_value=self._default_data,
                                       callback=self._callback,
                                       width=self._input_window_width - 50,
                                       readonly=not self.enable_input,
                                       show=self._debug_mode,
                                       indent=self._input_window_width - 50)
            elif self.pin_type == OutputPinType.Password:  # Password output Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 indent=self._input_window_width,
                                 color=DARKPINK)
                    dpg.add_input_text(tag=self.value_tag,
                                       width=self._input_window_width - 50,
                                       callback=self._callback,
                                       default_value=self._default_data,
                                       readonly=True,
                                       password=False,
                                       show=self._debug_mode,
                                       indent=self._input_window_width - 50)
            elif self.pin_type == OutputPinType.Bool:  # Bool output Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 indent=self._input_window_width,
                                 color=DARKRED)
                    dpg.add_checkbox(tag=self.value_tag,
                                     default_value=self._default_data,
                                     callback=self._callback,
                                     enabled=False,
                                     show=self._debug_mode,
                                     indent=self._input_window_width)
            elif self.pin_type == OutputPinType.MultilineString:  # Password output Pin
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 indent=self._input_window_width,
                                 color=PINK)
                    dpg.add_input_text(tag=self.value_tag,
                                       default_value=self._default_data,
                                       label=self.label,
                                       width=self._input_window_width - 50,
                                       callback=self._callback,
                                       readonly=True,
                                       multiline=True,
                                       tab_input=True,
                                       indent=self._input_window_width - 50,
                                       show=self._debug_mode)
            else:  # User defined pin type
                with dpg.node_attribute(
                    tag=self._pin_tag,
                    attribute_type=self.attribute_type,
                    shape=self._pin_shape
                ):
                    dpg.add_text(default_value=self.label,
                                 indent=self._input_window_width,
                                 color=TEAL)
        # Static Pin
        else:
            with dpg.node_attribute(
                tag=self._pin_tag,
                attribute_type=dpg.mvNode_Attr_Static,
                shape=self._pin_shape
            ):
                dpg.add_text(default_value=self.label)


class PinInt(PinBase):

    def __init__(self,
                 parent,
                 attribute_type,
                 pin_type,
                 pin_shape=dpg.mvNode_PinShape_Circle,
                 input_window_width=240,
                 label='Int',
                 enable_input=True,
                 callback=None,
                 pin_tag=None,
                 show_data=True,
                 default_data=0,
                 user_data=None
                 ):
        super().__init__(parent, attribute_type, pin_type, pin_shape, input_window_width, label, enable_input, callback,
                         pin_tag, show_data, default_data, user_data)
        self.CreatePin()


class PinFloat(PinBase):

    def __init__(self,
                 parent,
                 attribute_type,
                 pin_type,
                 pin_shape=dpg.mvNode_PinShape_Circle,
                 input_window_width=240,
                 label='Float',
                 enable_input=True,
                 callback=None,
                 pin_tag=None,
                 show_data=True,
                 default_data=0.0,
                 user_data=None
                 ):
        super().__init__(parent, attribute_type, pin_type, pin_shape, input_window_width, label, enable_input, callback,
                         pin_tag, show_data, default_data, user_data)
        self.CreatePin()


class PinString(PinBase):

    def __init__(self,
                 parent,
                 attribute_type,
                 pin_type,
                 pin_shape=dpg.mvNode_PinShape_Circle,
                 input_window_width=240,
                 label='String',
                 enable_input=True,
                 callback=None,
                 pin_tag=None,
                 show_data=True,
                 default_data='',
                 user_data=None
                 ):
        super().__init__(parent, attribute_type, pin_type, pin_shape, input_window_width, label, enable_input, callback,
                         pin_tag, show_data, default_data, user_data)
        self.CreatePin()


class PinJson(PinBase):

    def __init__(self,
                 parent,
                 attribute_type,
                 pin_type,
                 pin_shape=dpg.mvNode_PinShape_Circle,
                 input_window_width=240,
                 label='Json',
                 enable_input=True,
                 callback=None,
                 pin_tag=None,
                 show_data=True,
                 default_data='',
                 user_data=None
                 ):
        super().__init__(parent, attribute_type, pin_type, pin_shape, input_window_width, label, enable_input, callback,
                         pin_tag, show_data, default_data, user_data)
        self.CreatePin()


class PinExec(PinBase):

    def __init__(self,
                 parent,
                 attribute_type,
                 pin_type,
                 pin_shape=dpg.mvNode_PinShape_Triangle,
                 input_window_width=240,
                 label='Exec',
                 enable_input=True,
                 callback=None,
                 pin_tag=None
                 ):
        super().__init__(parent, attribute_type, pin_type, pin_shape, input_window_width, label, enable_input, callback,
                         pin_tag)
        self.CreatePin()


class PinEvent(PinBase):

    def __init__(self,
                 parent,
                 attribute_type,
                 pin_type,
                 pin_shape=dpg.mvNode_PinShape_Triangle,
                 input_window_width=240,
                 label='Event',
                 enable_input=True,
                 callback=None,
                 pin_tag=None,
                 user_data=None
                 ):
        super().__init__(parent, attribute_type, pin_type, pin_shape, input_window_width, label, enable_input, callback,
                         pin_tag, user_data=user_data)
        self.CreatePin()


class PinWildCard(PinBase):

    def __init__(self,
                 parent,
                 attribute_type,
                 pin_type,
                 pin_shape=dpg.mvNode_PinShape_Quad,
                 input_window_width=240,
                 label='WildCard',
                 enable_input=True,
                 callback=None,
                 pin_tag=None,
                 show_data=True,
                 default_data='',
                 user_data=None
                 ):
        super().__init__(parent, attribute_type, pin_type, pin_shape, input_window_width, label, enable_input, callback,
                         pin_tag, show_data, default_data, user_data)
        self.CreatePin()


class PinPassword(PinBase):

    def __init__(self,
                 parent,
                 attribute_type,
                 pin_type,
                 pin_shape=dpg.mvNode_PinShape_Circle,
                 input_window_width=240,
                 label='Password',
                 enable_input=True,
                 callback=None,
                 pin_tag=None,
                 show_data=True,
                 default_data='',
                 user_data=None
                 ):
        super().__init__(parent, attribute_type, pin_type, pin_shape, input_window_width, label, enable_input, callback,
                         pin_tag, show_data, default_data, user_data)
        self.CreatePin()


class PinBool(PinBase):

    def __init__(self,
                 parent,
                 attribute_type,
                 pin_type,
                 pin_shape=dpg.mvNode_PinShape_Circle,
                 input_window_width=240,
                 label='Bool',
                 enable_input=True,
                 callback=None,
                 pin_tag=None,
                 show_data=True,
                 default_data=False,
                 user_data=None
                 ):
        super().__init__(parent, attribute_type, pin_type, pin_shape, input_window_width, label, enable_input, callback,
                         pin_tag, show_data, default_data, user_data)
        self.CreatePin()


class PinMultilineString(PinBase):

    def __init__(self,
                 parent,
                 attribute_type,
                 pin_type,
                 pin_shape=dpg.mvNode_PinShape_Circle,
                 input_window_width=240,
                 label='Multiline String',
                 enable_input=True,
                 callback=None,
                 pin_tag=None,
                 show_data=True,
                 default_data='',
                 user_data=None
                 ):
        super().__init__(parent, attribute_type, pin_type, pin_shape, input_window_width, label, enable_input, callback,
                         pin_tag, show_data, default_data, user_data)
        self.CreatePin()


class PerforceInstancePin(PinBase):

    def __init__(self,
                 parent,
                 attribute_type,
                 pin_type,
                 pin_shape=dpg.mvNode_PinShape_Circle,
                 input_window_width=240,
                 label='Perforce Credential',
                 enable_input=False,
                 callback=None,
                 pin_tag=None,
                 show_data=True,
                 default_data=None,
                 user_data=None
                 ):
        super().__init__(parent, attribute_type, pin_type, pin_shape, input_window_width, label, enable_input, callback,
                         pin_tag, show_data, default_data, user_data)
        self.CreatePin()
