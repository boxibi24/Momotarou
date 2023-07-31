from ui.NodeEditor.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType


class Node(BaseNode):
    """Multiplies Floats"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Multiply by Float'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'A': InputPinType.Float,
        'B': InputPinType.Float,
        'Product': OutputPinType.Float
    }

    @staticmethod
    def run(internal_data_dict):
        internal_data_dict.update({'Product': float(internal_data_dict.get('A', 0)) * float(internal_data_dict.get('B', 0))})
