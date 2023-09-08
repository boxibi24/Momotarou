from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType
import subprocess


class Node(BaseNode):
    """Opens a Perforce workspace"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Open P4V workspace'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'P4 Inst': InputPinType.PerforceInstance
    }

    @staticmethod
    def run(internal_data_dict):
        p4 = internal_data_dict.get('P4 Inst', None)
        subprocess.Popen(f'start "Open P4V" p4v -c {p4.client} -u {p4.user} -C {p4.charset} -p {p4.port}', shell=True)
