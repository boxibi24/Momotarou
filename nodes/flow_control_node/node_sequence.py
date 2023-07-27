from ui.NodeEditor.classes.node import BaseNode
from core.enum_type import NodeTypeFlag, InputPinType, OutputPinType


class Node(BaseNode):
    """Executes a series of pins in order"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Sequence'
    node_type = NodeTypeFlag.Sequential
    pin_dict = {
        'Exec In': InputPinType.Exec,
        'Then 0': OutputPinType.Exec,
        'Then 1': OutputPinType.Exec,
        'Then 2': OutputPinType.Exec
    }

    @staticmethod
    def run(internal_data_dict):
        pass
