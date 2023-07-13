from ui.NodeEditor.classes.node import BaseNode, NodeTypeFlag
from ui.NodeEditor.classes.pin import InputPinType, OutputPinType
from tkinter import simpledialog


class Node(BaseNode):
    """Input default Float value or prompt user for input"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Float Value'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'Float in': InputPinType.Float,
        'Prompt user for input?': InputPinType.Bool,
        'Float out': OutputPinType.Float
    }

    @staticmethod
    def run(internal_data_dict):
        if internal_data_dict.get('Prompt user for input?', None):
            try:
                internal_data_dict.update(
                    {'Float out': simpledialog.askfloat(title="Int input", prompt="Give me your float Now!:")})
            except:
                return 2
        else:
            internal_data_dict.update({'Float out': internal_data_dict['Float in']})
