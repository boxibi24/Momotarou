from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType


class Node(BaseNode):
    """Executes a series of pins for N times"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Do N'
    node_type = NodeTypeFlag.Sequential
    pin_dict = {
        'Enter': InputPinType.Exec,
        'N': InputPinType.Int,
        'Exit': OutputPinType.Exec,
        'Index': OutputPinType.Int
    }

    @staticmethod
    def run(internal_data_dict):
        pass
