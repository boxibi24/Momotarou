from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType
from pathlib import Path


class Node(BaseNode):
    """Make new file"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Make file'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'File path': InputPinType.String
    }

    @staticmethod
    def run(internal_data_dict):
        new_dir = Path(internal_data_dict['File path'])
        new_dir.touch(exist_ok=False)
        if not new_dir.is_file():
            raise RuntimeError('Failed creating new file. Maybe the file path is incorrect?')
