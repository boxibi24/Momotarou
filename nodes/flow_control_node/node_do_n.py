from ui.NodeEditor.classes.node import BaseNode, NodeTypeFlag
from ui.NodeEditor.classes.pin import InputPinType, OutputPinType


class Node(BaseNode):
    """Executes a series of pins in N times"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Do N'
    node_type = NodeTypeFlag.Sequential
    pin_dict = {
        'Enter': InputPinType.Exec,
        'N': InputPinType.Int,
        'Exit': OutputPinType.Exec
    }

    @staticmethod
    def run(internal_data_dict):
        pass
