from ui.NodeEditor.classes.node import BaseNode
from core.enum_type import NodeTypeFlag, InputPinType, OutputPinType


class Node(BaseNode):
    """Int Addition"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Add Int'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'A': InputPinType.Int,
        'B': InputPinType.Int,
        'Sum': OutputPinType.Int
    }

    @staticmethod
    def run(internal_data_dict):
        internal_data_dict.update({'Sum': int(internal_data_dict.get('A', 0)) + int(internal_data_dict.get('B', 0))})
