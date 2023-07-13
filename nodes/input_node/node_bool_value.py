from ui.NodeEditor.classes.node import BaseNode, NodeTypeFlag
from ui.NodeEditor.classes.pin import InputPinType, OutputPinType


class Node(BaseNode):
    """Input default Bool value or prompt user for input"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Bool Value'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'Bool in': InputPinType.Bool,
        'Prompt user for input?': InputPinType.Bool,
        'Bool out': OutputPinType.Bool
    }

    @staticmethod
    def run(internal_data_dict):
        try:
            internal_data_dict.update({'Bool out': internal_data_dict['Bool in']})
        except:
            return -1
