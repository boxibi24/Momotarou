from ui.NodeEditor.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType
from P4 import P4Exception
from lib.p4util import create_p4_workspace
from traceback import format_exc


class Node(BaseNode):
    """Opens a Perforce workspace"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Create P4V workspace'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'P4 Inst': InputPinType.PerforceInstance,
        'Options': InputPinType.String,
        'Submit Options': InputPinType.String,
        'P4ROOT': InputPinType.String,
        'P4STREAM': InputPinType.String,
        'P4 Inst out': OutputPinType.PerforceInstance
    }

    @staticmethod
    def run(internal_data_dict):
        p4 = internal_data_dict['P4 Inst']
        try:
            create_p4_workspace(p4,
                                client=p4.client,
                                user=p4.user,
                                root=internal_data_dict['P4ROOT'],
                                stream=internal_data_dict['P4STREAM'],
                                options=internal_data_dict['Options'],
                                submit_option=internal_data_dict['Submit Options'])
        except P4Exception:
            return 4, format_exc()
        internal_data_dict['P4 Inst Out'] = p4
        return 1, ''
