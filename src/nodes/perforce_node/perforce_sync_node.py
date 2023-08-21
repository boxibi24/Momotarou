from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType
from P4 import P4Exception
from libs.p4util import get_latest_rev


class Node(BaseNode):
    """Opens a Perforce workspace"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Perforce Sync'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'P4 Inst': InputPinType.PerforceInstance,
        'Sync path': InputPinType.String
    }

    @staticmethod
    def run(internal_data_dict):
        p4 = internal_data_dict['P4 Inst']
        try:
            sync_path = internal_data_dict['Sync path']
            if sync_path:
                get_latest_rev(sync_path, p4)
            else:
                get_latest_rev('', p4)
        except P4Exception as e:
            return 4, e
