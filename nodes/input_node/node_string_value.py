from ui.NodeEditor.classes.node import BaseNode, NodeTypeFlag
from ui.NodeEditor.classes.pin import InputPinType, OutputPinType

from tkinter import Tk, simpledialog


class Node(BaseNode):
    """Input default String value or prompt user for input"""

    # Define class members
    ver = '0.0.1'
    node_label = 'String Value'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'String in': InputPinType.String,
        'Prompt user for input?': InputPinType.Bool,
        'String out': OutputPinType.String
    }

    @staticmethod
    def run(internal_data_dict: dict):
        if internal_data_dict.get('Prompt user for input?', None):
            try:
                root = Tk()
                root.withdraw()
                internal_data_dict.update(
                    {'String out': simpledialog.askstring(title='Ask String', prompt='Input String')})
                root.destroy()
            except:
                return 2
        else:
            internal_data_dict.update({'String out': internal_data_dict['String in']})
