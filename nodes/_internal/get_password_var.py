from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, OutputPinType


class Node(BaseNode):
    """Input default Integer value or prompt user for input"""

    ver = '0.0.1'
    # node_label needs to match with the OutputPinType. Later on, this param will be overridden by var_name
    node_label = 'Get Password'
    node_type = NodeTypeFlag.GetVariable
    pin_dict = {
        'Password out': OutputPinType.Password
    }

    # Var node need to store a reference to a shared internal data across multiple calls of the same var

    @staticmethod
    def run(internal_data_dict):
        var_value = internal_data_dict.get('var_value', None)
        if var_value is None:
            return 8
        if var_value[0] is None:
            var_value[0] = internal_data_dict['default_var_value'][0]
        internal_data_dict['Password out'] = var_value[0]
