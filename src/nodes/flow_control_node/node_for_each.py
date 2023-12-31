from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType


class Node(BaseNode):
    """Branch Statement If Condition is true, execution goes to True, otherwise it goes to False"""

    # Define class members
    ver = '0.0.1'
    node_label = 'For each loop'
    node_type = NodeTypeFlag.Sequential  # Blueprint because it has input value pins that need computing
    pin_dict = {
        'Exec': InputPinType.Exec,
        'String Array': InputPinType.StringArray,
        'Loop Body': OutputPinType.Exec,
        'Array Str Element': OutputPinType.String,
        'Array Index': OutputPinType.Int,
        'Completed': OutputPinType.Exec
    }

    @staticmethod
    def run(internal_data_dict):
        pass
