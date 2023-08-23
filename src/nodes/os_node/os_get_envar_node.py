from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType
import os


class Node(BaseNode):
    """Get OS environment variable"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Get OS envar'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'Env var': InputPinType.String,
        'Value': OutputPinType.String
    }

    @staticmethod
    def run(internal_data_dict):
        internal_data_dict['Value'] = os.environ.get(internal_data_dict['Env var'], '')
        
