from ui.NodeEditor.classes.node import BaseNode, NodeTypeFlag
from ui.NodeEditor.classes.pin import InputPinType, OutputPinType


class Node(BaseNode):
    """String concatenation"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Concatenate String'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'A': InputPinType.String,
        'B': InputPinType.String,
        'String out': OutputPinType.String
    }

    @staticmethod
    def run(internal_data_dict):
        internal_data_dict.update(
            {'String out': str(internal_data_dict.get('A', '')) + str(internal_data_dict.get('B', ''))})
