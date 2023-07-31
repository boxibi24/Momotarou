from ui.NodeEditor.classes.node import BaseNode
from core.enum_types import NodeTypeFlag


class Node(BaseNode):
    """Entry node for a user_data with a button to emulate callbacks"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Event'
    node_type = NodeTypeFlag.Event
    # Create an empty pin_dict so that this class declaration does not fall back to a BaseNode
    pin_dict = {
        'Temp': None
    }

    # Need to add __init__ override function in order to pass callback function
    @staticmethod
    def run(internal_data_dict):
        print(f"Running Button Node")
