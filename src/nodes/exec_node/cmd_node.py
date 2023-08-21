from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType
import subprocess


class Node(BaseNode):
    """Exec CMD"""

    # Define class members
    ver = '0.0.1'
    node_label = 'CMD'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'String': InputPinType.String,
        'Return': OutputPinType.String
    }

    @staticmethod
    def run(internal_data_dict):
        p = subprocess.run(internal_data_dict['String'], shell=True, capture_output=True)
        internal_data_dict.update({'Return': p.stdout})
