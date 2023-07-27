from ui.NodeEditor.classes.node import BaseNode
from core.enum_type import NodeTypeFlag, InputPinType, OutputPinType
from P4 import P4, P4Exception
from pprint import pprint
import os


class Node(BaseNode):
    """Opens a Perforce workspace"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Create P4V workspace'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'P4 Inst': InputPinType.PerforceInstance,
        'Project Name': InputPinType.String,
        'P4ROOT': InputPinType.String,
        'P4STREAM': InputPinType.String
    }

    @staticmethod
    def run(internal_data_dict):
        p4 = internal_data_dict.get('P4 Inst', None)
        if p4 is None:
            return -1
        client_name = internal_data_dict.get('Project Name', '') + '_' + p4.user + '_' + os.environ.get('COMPUTERNAME', 'NullPCName')
        client = {'Backup': 'enable',
                  'Client': client_name,
                  'Description': 'Created by {}.\n'.format(p4.user),
                  'Host': os.environ.get('COMPUTERNAME', 'NullPCName'),
                  'LineEnd': 'local',
                  'Options': 'noallwrite noclobber nocompress unlocked nomodtime rmdir',
                  'Owner': p4.user,
                  'Root': internal_data_dict.get('P4ROOT', ''),
                  'SubmitOptions': 'revertunchanged',
                  'Type': 'writeable',
                  'Stream': internal_data_dict.get('P4STREAM', '')
                  }
        try:
            p4.save_client(client)
            p4.client = client_name
            pprint(client)
        except P4Exception as e:
            print(e)
            return -2
