from ui.NodeEditor.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType
from P4 import P4Exception
from lib.p4util import get_latest_rev


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
        p4 = internal_data_dict.get('P4 Inst', None)
        if p4 is None:
            return 0
        try:
            sync_path = internal_data_dict['Sync path']
            if sync_path:
                get_latest_rev(sync_path)
            else:
                get_latest_rev('//...')
        except P4Exception as e:
            return 4, e
