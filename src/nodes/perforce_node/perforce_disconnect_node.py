from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType
from P4 import P4Exception


class Node(BaseNode):
    """Opens a Perforce workspace"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Perforce Disconnect'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'P4 Inst': InputPinType.PerforceInstance
    }

    @staticmethod
    def run(internal_data_dict):
        p4 = internal_data_dict.get('P4 Inst', None)
        if p4 is None:
            raise RuntimeError("P4 Inst could not be None")
        p4.disconnect()

