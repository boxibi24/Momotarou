from ui.NodeEditor.classes.node import BaseNode, NodeTypeFlag
from ui.NodeEditor.classes.pin import InputPinType, OutputPinType
from tkinter import simpledialog


class Node(BaseNode):
    """Input default Integer value or prompt user for input"""

    ver = '0.0.1'
    # node_label needs to match with the OutputPinType. Later on, this param will be overridden by var_name
    node_label = 'Get Int'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'Int out': OutputPinType.Int
    }
    # Var node need to store a reference to a shared internal data across multiple calls of the same var


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
