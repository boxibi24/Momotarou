from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType


class Node(BaseNode):
    """Break an input multiline to an array of strings"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Construct string array from multiline'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'Multiline': InputPinType.MultilineString,
        'String array': OutputPinType.StringArray
    }

    @staticmethod
    def run(internal_data_dict):
        internal_data_dict['String array'] = internal_data_dict['Multiline'].split('\n')
