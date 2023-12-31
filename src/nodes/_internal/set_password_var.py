from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType


class Node(BaseNode):
    """Input default Integer value or prompt user for input"""

    ver = '0.0.1'
    # node_label needs to match with the OutputPinType. Later on, this param will be overridden by var_name
    node_label = 'Set Password'
    node_type = NodeTypeFlag.SetVariable
    pin_dict = {
        'String in': InputPinType.Password,
        'String out': OutputPinType.Password
    }

    @staticmethod
    def run(internal_data_dict):
        var_value = internal_data_dict.get('var_value', None)
        if var_value is None:
            # KeyError could not find var_value in internal_data_dict
            raise ValueError
        else:
            internal_data_dict['var_value'][0] = internal_data_dict['Password in']
            internal_data_dict['Password out'] = internal_data_dict['Password in']
