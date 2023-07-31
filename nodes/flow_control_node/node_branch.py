from ui.NodeEditor.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType


class Node(BaseNode):
    """Branch Statement If Condition is true, execution goes to True, otherwise it goes to False"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Branch'
    node_type = NodeTypeFlag.Sequential  # Blueprint because it has input value pins that need computing
    pin_dict = {
        'Exec in': InputPinType.Exec,
        'Condition': InputPinType.Bool,
        'True': OutputPinType.Exec,
        'False': OutputPinType.Exec
    }

    @staticmethod
    def run(internal_data_dict):
        pass
