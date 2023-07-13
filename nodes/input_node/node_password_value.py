from ui.NodeEditor.classes.node import BaseNode, NodeTypeFlag
from ui.NodeEditor.classes.pin import InputPinType, OutputPinType


class Node(BaseNode):
    """Input default Password value or prompt user for input"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Password value'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'Password in': InputPinType.Password,
        'Prompt user for input?': InputPinType.Bool,
        'Password out': OutputPinType.Password
    }

    @staticmethod
    def run(internal_data_dict):
        internal_data_dict.update({'Password out': internal_data_dict.get('Password in', '')})
