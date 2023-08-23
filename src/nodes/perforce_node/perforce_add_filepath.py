# Default import modules for standard nodes
from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType

# Import necessary modules to be used in run()
from libs.p4util import p4_edit_or_add


class Node(BaseNode):
    """Mark for add the specified file path"""

    ver = '0.0.1'
    node_label = 'Mark for add file path'

    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'File path': InputPinType.String,
        'P4 inst': InputPinType.PerforceInstance
    }

    @staticmethod
    def run(internal_data_dict):
        try:
            p4_edit_or_add(internal_data_dict['File path'],
                           p4inst=internal_data_dict['P4 inst'])
        except:
            raise Exception('Failed to mark for add the file path')

