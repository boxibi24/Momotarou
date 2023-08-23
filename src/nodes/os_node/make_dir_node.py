from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType
from pathlib import Path


class Node(BaseNode):
    """Make new directory"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Make directory'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'Directory': InputPinType.String
    }

    @staticmethod
    def run(internal_data_dict):
        new_dir = Path(internal_data_dict['Directory'])
        new_dir.mkdir(parents=True, exist_ok=True)
