from ui.NodeEditor.classes.node import BaseNode, NodeTypeFlag
from ui.NodeEditor.classes.pin import InputPinType, OutputPinType
from tkinter import simpledialog


class Node(BaseNode):
    """Input default Integer value or prompt user for input"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Int Value'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'Int in': InputPinType.Int,
        'Prompt user for input?': InputPinType.Bool,
        'Int out': OutputPinType.Int
    }

    @staticmethod
    def run(internal_data_dict):
        if internal_data_dict.get('Prompt user for input?', None):
            try:
                internal_data_dict.update({'Int out': simpledialog.askinteger(title="Int input",
                                                                              prompt="Give me your number Now!:")})
            except:
                return 2
        else:
            internal_data_dict.update({'Int out': internal_data_dict['Int in']})
