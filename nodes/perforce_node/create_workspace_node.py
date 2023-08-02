from ui.NodeEditor.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType
from P4 import P4, P4Exception
import os


class Node(BaseNode):
    """Opens a Perforce workspace"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Create P4V workspace'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'P4 Inst': InputPinType.PerforceInstance,
        # 'Project Name': InputPinType.String,
        'Options': InputPinType.String,
        'Submit Options': InputPinType.String,
        'P4ROOT': InputPinType.String,
        'P4STREAM': InputPinType.String,
        'P4 Inst out': OutputPinType.PerforceInstance
    }

    @staticmethod
    def run(internal_data_dict):
        p4 = internal_data_dict.get('P4 Inst', None)
        if p4 is None:
            return 0, ''
        # client_name = internal_data_dict.get('Project Name', '') + '_' + p4.user + '_' + os.environ.get('COMPUTERNAME', 'NullPCName')
        client_config = {'Backup': 'enable',
                         'Client': p4.client,
                         'Description': 'Created by {}.\n'.format(p4.user),
                         'Host': os.environ.get('COMPUTERNAME', 'NullPCName'),
                         'LineEnd': 'local',
                         # 'Options': 'noallwrite noclobber nocompress unlocked nomodtime rmdir',
                         'Options': internal_data_dict['Options'],
                         'Owner': p4.user,
                         'Root': internal_data_dict['P4ROOT'],
                         'SubmitOptions': internal_data_dict['Submit Options'],
                         'Type': 'writeable',
                         'Stream': internal_data_dict['P4STREAM']
                         }
        try:
            p4.save_client(client_config)
        except P4Exception as e:
            return 4, e
        internal_data_dict['P4 Inst Out'] = p4
