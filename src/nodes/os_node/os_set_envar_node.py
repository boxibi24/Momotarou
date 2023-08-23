from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType
import os


class Node(BaseNode):
    """Set OS environment variable"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Set OS envar'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        'Env var': InputPinType.String,
        'Value': InputPinType.String
    }

    @staticmethod
    def run(internal_data_dict):
        try:
            os.environ[internal_data_dict['Env var']] = internal_data_dict['Value']
        except:
            raise RuntimeError('Cannot set environment variable')
