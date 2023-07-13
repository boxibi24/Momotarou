from ui.NodeEditor.classes.node import BaseNode, NodeTypeFlag
from ui.NodeEditor.classes.pin import InputPinType, OutputPinType
from P4 import P4Exception


class Node(BaseNode):
    """Opens a Perforce workspace"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Perforce Sync'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'P4 Inst': InputPinType.PerforceInstance
    }

    @staticmethod
    def run(internal_data_dict):
        p4 = internal_data_dict.get('P4 Inst', None)
        if p4 is None:
            return -1
        try:
            p4.run('sync')
            print(p4)
        except P4Exception as e:
            print(e)
