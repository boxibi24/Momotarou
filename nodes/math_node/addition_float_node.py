from ui.NodeEditor.classes.node import BaseNode, NodeTypeFlag
from ui.NodeEditor.classes.pin import InputPinType, OutputPinType


class Node(BaseNode):
    """Float Addition"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Add Float'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'A': InputPinType.Float,
        'B': InputPinType.Float,
        'Sum': OutputPinType.Float
    }

    @staticmethod
    def run(internal_data_dict):
        internal_data_dict.update({'Sum': float(internal_data_dict.get('A', 0)) + float(internal_data_dict.get('B', 0))})
