from ui.NodeEditor.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType


class Node(BaseNode):
    """Convert Integer data to Float data"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Convert Int to Float'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'Int in': InputPinType.Int,
        'Float out': OutputPinType.Float
    }

    @staticmethod
    def run(internal_data_dict):
        internal_data_dict.update({'Float out': float(internal_data_dict.get('Int in', 0))})
