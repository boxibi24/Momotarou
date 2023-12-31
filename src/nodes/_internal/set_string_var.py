from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType


class Node(BaseNode):
    """Input default Integer value or prompt user for input"""

    ver = '0.0.1'
    # node_label needs to match with the OutputPinType. Later on, this param will be overridden by var_name
    node_label = 'Set String'
    node_type = NodeTypeFlag.SetVariable
    pin_dict = {
        'String in': InputPinType.String,
        'String out': OutputPinType.String
    }

    @staticmethod
    def run(internal_data_dict):
        internal_data_dict['var_value'][0] = internal_data_dict['String in']
        internal_data_dict['String out'] = internal_data_dict['String in']
