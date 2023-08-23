# Default import modules for standard nodes
from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType

# Import necessary modules to be used in run()


class Node(BaseNode):
    """Insert Docstring here. This is also shown on menu items as tooltips"""

    # Define class members
    ver = '0.0.1'  # Version should be matched with the Node Editor version
    node_label = 'Template Node'  # Name of the node that will be displayed in node graph

    # Type of the node, from one of these enums, currently supports:
    # 1. NodeTypeFlag.Dummy : does not have any data pins or exec pins
    # 2. NodeTypeFlag.Pure: Use to compute data, compute per request. Does not have Exec pins
    # 3. NodeTypeFlag.Event: Each node instance of this type will represent a callback event on ToolsViewer
    # 4. NodeTypeFlag.Blueprint: consist of data pins and exec pins. Will be computed upon execution
    node_type = NodeTypeFlag.Pure
    # Specify dict of pins to initialize. You DO NOT need to specify exec pins as it is default builtin for
    # blueprint nodes
    # pin_dict schema: {'Pin Label': <PinType>} Currently PinType supports: Int, Float, String,
    # MultilineString, WildCard, Bool, Custom classes, ...
    pin_dict = {
        'Value in': InputPinType.Int,
        # Optional: if this node is a PRIMITIVE INPUT VALUE. Uncommenting the below line will ask user for input
        # 'Prompt user for input?': InputPinType.Bool,
        'Value out': OutputPinType.Int
    }

    # Uncomment if you want to add logics if you want to perform further clean up (i.e. close files)
    # after closing NodeEditor

    # def on_node_deletion(self, node_id, **kwargs):
    #     """Called upon Node Editor closure"""
    #     super().on_node_deletion(node_id, **kwargs)
    @staticmethod
    def run(internal_data_dict):
        """Core computation function to be run by Node Editor and Tools Viewer"""
        try:
            internal_data_dict['Value out'] = internal_data_dict['Value in'] + 'Hello World!'
        except:
            raise ValueError('Raise any exception if you want to terminate the execution')

