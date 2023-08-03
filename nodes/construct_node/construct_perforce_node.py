from ui.NodeEditor.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType
from P4 import P4
from random import randint
import os


class Node(BaseNode):
    """Opens a Perforce workspace"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Perforce Construct'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'User': InputPinType.String,
        'Password': InputPinType.Password,
        'Port': InputPinType.String,
        'Charset': InputPinType.String,
        'Client': InputPinType.String,
        'P4 Inst': OutputPinType.PerforceInstance
    }

    @staticmethod
    def run(internal_data_dict):

        p4 = P4()
        p4.user = internal_data_dict['User']
        p4.password = internal_data_dict['Password']
        p4.port = internal_data_dict['Port']
        p4.charset = internal_data_dict['Charset']
        if internal_data_dict['Client'] == '':
            p4.client = p4.user + '_' + os.environ['COMPUTERNAME'] + '_' + str(randint(100, 9999))
        else:
            p4.client = internal_data_dict['Client']
        internal_data_dict['P4 Inst'] = p4
