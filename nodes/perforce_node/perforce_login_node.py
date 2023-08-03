from ui.NodeEditor.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType
from P4 import P4Exception


class Node(BaseNode):
    """Opens a Perforce workspace"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Perforce login'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'P4 Inst': InputPinType.PerforceInstance,
        'Successful connection?': OutputPinType.Bool
    }

    @staticmethod
    def run(internal_data_dict):
        p4 = internal_data_dict['P4 Inst']
        try:
            p4.connect()
            p4.run_login()
        except P4Exception as e:
            return 4, e
        if p4.connected():
            internal_data_dict['Successful connection?'] = True
        else:
            internal_data_dict['Successful connection?'] = False
