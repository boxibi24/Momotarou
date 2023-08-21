from enum import IntFlag, IntEnum, auto, Enum


class NodeTypeFlag(IntFlag):
    Dummy = 0
    Pure = 1 << 0
    Exec = 1 << 1
    Sequential = 1 << 2 | Pure
    Event = 1 << 3
    Blueprint = Pure | Exec
    Variable = 1 << 4
    SetVariable = Variable | Blueprint
    GetVariable = Variable | Pure


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
    StringArray = auto()


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
    StringArray = auto()


class PinMetaType(IntEnum):
    DataIn = auto()
    DataOut = auto()
    FlowIn = auto()
    FlowOut = auto()
