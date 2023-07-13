from ui.NodeEditor.classes.node import BaseNode, NodeTypeFlag
from ui.NodeEditor.classes.pin import InputPinType
from subprocess import Popen


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
        print(p4.user)
        print(p4.client)
        print(p4.password)
        print(p4.charset)
        print(p4.port)

        # sp = Popen()
