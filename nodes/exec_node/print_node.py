from ui.NodeEditor.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType


class Node(BaseNode):
    """Print Wildcard"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Print'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'Wildcard': InputPinType.WildCard,
        'String': OutputPinType.String
    }

    @staticmethod
    def run(internal_data_dict):
        internal_data_dict.update({'String': internal_data_dict.get('Wildcard', '')})
        a = internal_data_dict.get('Wildcard', None)
        print(internal_data_dict['String'])
