from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType
from random import randint
import os
from libs.p4util import create_p4_inst


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

        if internal_data_dict['Client'] == '':
            p4_client = internal_data_dict['User'] + '_' + os.environ['COMPUTERNAME'] + '_' + str(randint(100, 9999))
        else:
            p4_client = internal_data_dict['Client']

        p4 = create_p4_inst(user=internal_data_dict['User'],
                              password=internal_data_dict['Password'],
                              port=internal_data_dict['Port'],
                              client=p4_client,
                              charset=internal_data_dict['Charset'])
        internal_data_dict['P4 Inst'] = p4
