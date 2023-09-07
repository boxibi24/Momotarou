from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType


class Node(BaseNode):
    """Join String Array with a string"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Join Strings'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'StringArray in': InputPinType.StringArray,
        'Join with': InputPinType.String,
        'Result String': OutputPinType.String
    }

    @staticmethod
    def run(internal_data_dict):
        internal_data_dict['Result String'] = internal_data_dict['Join with'].join(internal_data_dict['StringArray in'])
