from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType


class Node(BaseNode):
    """Raise a RuntimeError exception"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Raise RuntimeError exception'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'Message': InputPinType.String
    }

    @staticmethod
    def run(internal_data_dict):
        raise RuntimeError(internal_data_dict['Message'])

