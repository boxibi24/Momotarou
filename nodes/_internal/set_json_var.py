from ui.NodeEditor.classes.node import BaseNode, NodeTypeFlag
from ui.NodeEditor.classes.pin import InputPinType, OutputPinType


class Node(BaseNode):
    """Input default Integer value or prompt user for input"""

    ver = '0.0.1'
    # node_label needs to match with the OutputPinType. Later on, this param will be overridden by var_name
    node_label = 'Set Json'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'Json in': InputPinType.Json,
        'Json out': OutputPinType.Json
    }

    @staticmethod
    def run(internal_data_dict):
        var_value = internal_data_dict.get('var_value', None)
        if var_value is None:
            # KeyError could not find var_value in internal_data_dict
            return 8
        else:
            internal_data_dict['var_value'][0] = internal_data_dict['Json in']
            internal_data_dict['Json out'] = internal_data_dict['Json in']
