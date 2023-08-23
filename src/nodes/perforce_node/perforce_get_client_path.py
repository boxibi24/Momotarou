# Default import modules for standard nodes
from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType

# Import necessary modules to be used in run()
from libs.p4util import get_client_path


class Node(BaseNode):
    """Get client path from a depot path"""

    ver = '0.0.1'
    node_label = 'Get Client Path'

    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'Depot path': InputPinType.String,
        'P4 inst': InputPinType.PerforceInstance,
        'Client path': OutputPinType.String
    }

    @staticmethod
    def run(internal_data_dict):
        try:
            internal_data_dict['Client path'] = get_client_path(path=internal_data_dict['Depot path'],
                                                                p4inst=internal_data_dict['P4 inst'])
        except:
            raise Exception('Failed to get client path')

