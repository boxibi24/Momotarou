from ui.NodeEditor.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType
from copy import deepcopy
from P4 import P4, P4Exception


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
        'P4 Inst': OutputPinType.PerforceInstance
    }

    @staticmethod
    def run(internal_data_dict):

        p4 = P4()
        p4.user = internal_data_dict.get('User', None)
        p4.password = internal_data_dict.get('Password', None)
        p4.port = internal_data_dict.get('Port')
        p4.charset = internal_data_dict.get('Charset')

        internal_data_dict.update({'P4 Inst': p4})
