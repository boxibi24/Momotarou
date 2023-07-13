from ui.NodeEditor.classes.node import BaseNode, NodeTypeFlag
from ui.NodeEditor.classes.pin import InputPinType, OutputPinType


class Node(BaseNode):
    """Input default String value or prompt user for input"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Multiline String Value'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'Multiline Str in': InputPinType.MultilineString,
        'Prompt user for input?': InputPinType.Bool,
        'Multiline Str out': OutputPinType.MultilineString
    }

    @staticmethod
    def run(internal_data_dict):
        internal_data_dict.update({'Multiline Str out': internal_data_dict.get('Multiline Str in', '')})
