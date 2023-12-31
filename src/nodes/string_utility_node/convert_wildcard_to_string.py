from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType


class Node(BaseNode):
    """Convert WildCard data to String data"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Convert WildCard to String'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'WildCard in': InputPinType.WildCard,
        'String out': OutputPinType.String
    }

    @staticmethod
    def run(internal_data_dict):
        internal_data_dict['String out'] = str(internal_data_dict.get('WildCard in', 0))
