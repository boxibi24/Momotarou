from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType
from lib.p4util import p4_login
from P4 import P4Exception
import traceback


class Node(BaseNode):
    """Opens a Perforce workspace"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Perforce login'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'P4 Inst': InputPinType.PerforceInstance,
        'Successful login?': OutputPinType.Bool
    }

    @staticmethod
    def run(internal_data_dict):
        p4inst = internal_data_dict['P4 Inst']
        try:
            p4_login(p4inst)
            internal_data_dict['Successful login?'] = True
        except P4Exception:
            internal_data_dict['Successful login?'] = False
            return 4, traceback.format_exc()\

