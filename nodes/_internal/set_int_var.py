from ui.NodeEditor.classes.node import BaseNode, NodeTypeFlag
from ui.NodeEditor.classes.pin import InputPinType, OutputPinType
from tkinter import simpledialog


class Node(BaseNode):
    """Input default Integer value or prompt user for input"""

    ver = '0.0.1'
    # node_label needs to match with the OutputPinType. Later on, this param will be overridden by var_name
    node_label = 'Set Int'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'Int in': InputPinType.Int,
        'Int out': OutputPinType.Int
    }

    @staticmethod
    def run(internal_data_dict):
        if True:
            try:
                internal_data_dict.update({'Int out': simpledialog.askinteger(title="Int input",
                                                                              prompt="Give me your number Now!:")})
            except:
                return 2
        # else:
        #     internal_data_dict.update({'Int out': internal_data_dict['Int in']})
