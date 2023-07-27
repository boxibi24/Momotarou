# Default import modules for standard nodes
from ui.NodeEditor.classes.node import BaseNode
from core.enum_type import NodeTypeFlag, InputPinType, OutputPinType

# Import necessary modules to be used in run()

import tkinter as tk
from tkinter import simpledialog


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
    # MultilineString, WildCard, Bool,
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
        # The below block will prompt a tkinter UI letting user input value
        if internal_data_dict.get('Prompt user for input?', None):
            ROOT = tk.Tk()
            ROOT.withdraw()
            # Getting input from tkinter to apply on the output computed_dict
            internal_data_dict.update({'Value out': simpledialog.askinteger(title="Value in",
                                                                            prompt="Give me your number Now!:")})
        # Otherwise, compute every output pins here and reapply to the internal_data_dict
        # **** For example ****
        # internal_data_dict.update({'Value out': 'Hello World!'}

        # No need to return anything, since we have edited internal_data_dict as a reference.
