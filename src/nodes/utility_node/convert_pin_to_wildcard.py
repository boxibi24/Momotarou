from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType


class Node(BaseNode):
    """Convert any given pin to a WildCard output pin"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Convert Output pin to WildCard'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'Pin to convert': InputPinType.WildCard,
        'WildCard out': OutputPinType.WildCard
    }

    @staticmethod
    def run(internal_data_dict):
        internal_data_dict['Pin to convert'] = internal_data_dict['WildCard in']
