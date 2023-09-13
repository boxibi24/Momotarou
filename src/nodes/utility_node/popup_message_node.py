from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType
import wx


class Node(BaseNode):
    """Shows a messagebox, defaults to be an information popup"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Popup messagebox'
    node_type = NodeTypeFlag.Blueprint
    pin_dict = {
        "Title": InputPinType.String,
        "Message": InputPinType.String,
        "Show Warning": InputPinType.Bool,
        "Show Error": InputPinType.Bool,
        "User pressed OK": OutputPinType.Bool
    }

    @staticmethod
    def run(internal_data_dict):
        app = wx.App()
        msg_box_type = wx.OK | wx.CANCEL
        if internal_data_dict['Show Warning']:
            msg_box_type |= wx.ICON_WARNING
        if internal_data_dict['Show Error']:
            msg_box_type |= wx.ICON_ERROR

        result = wx.MessageBox(internal_data_dict['Message'], internal_data_dict['Title'], msg_box_type)
        if result == wx.OK:
            internal_data_dict['User pressed OK'] = True
        else:
            internal_data_dict['User pressed OK'] = False
        del app
