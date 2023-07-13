from ui.NodeEditor.classes.node import BaseNode, NodeTypeFlag
from ui.NodeEditor.classes.pin import InputPinType, OutputPinType


class Node(BaseNode):
    """Exec the script put in side Multiline Data field"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Exec Custom Script'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'Multiline String In': InputPinType.MultilineString,
        'Return string': OutputPinType.String
    }

    @staticmethod
    def run(internal_data_dict):
        if internal_data_dict.get('Multiline String In', None):
            try:
                exec(internal_data_dict['Multiline String In'])
            except SyntaxError:
                pass
