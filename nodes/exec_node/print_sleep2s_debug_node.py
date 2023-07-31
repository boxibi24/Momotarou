from ui.NodeEditor.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType

from time import sleep


class Node(BaseNode):
    """(Debug only) Print WildCard data then sleep for 2 seconds"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Print sleep 2 seconds'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'Wildcard': InputPinType.WildCard,
        'String': OutputPinType.String
    }

    @staticmethod
    def run(internal_data_dict):
        print(internal_data_dict.get('Wildcard'))
        sleep(2)
        internal_data_dict.update({'String': internal_data_dict.get('Wildcard')})
