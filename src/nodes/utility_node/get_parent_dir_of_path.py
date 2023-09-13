from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType
from pathlib import Path


class Node(BaseNode):
    """Shows a messagebox, defaults to be an information popup"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Get parent directory of file path'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        "Directory": InputPinType.String,
        "Parent Directory": OutputPinType.String

    }

    @staticmethod
    def run(internal_data_dict):
        input_path = Path(internal_data_dict['Directory'])
        internal_data_dict['Parent Directory'] = input_path.parent.as_posix()
