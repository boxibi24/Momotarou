from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType


class Node(BaseNode):
    """Convert Float data to Integer data"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Convert Float to Int'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'Float in': InputPinType.Float,
        'Int out': OutputPinType.Int
    }

    @staticmethod
    def run(internal_data_dict):
        internal_data_dict.update({'Int out': int(internal_data_dict.get('Float in', 0))})
