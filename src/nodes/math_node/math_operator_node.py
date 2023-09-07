from core.classes.node import BaseNode
from core.enum_types import NodeTypeFlag, InputPinType, OutputPinType
import operator

operator_mapping = {
    '+': operator.add,
    'in': operator.contains,
    '-': operator.sub,
    '*': operator.sub,
    '**': operator.pow,
    '/': operator.truediv,
    '//': operator.floordiv,
    '%': operator.mod,
    '&': operator.and_,
    '|': operator.or_,
    'is': operator.is_,
    'is not': operator.is_not,
    '^': operator.xor,
    '>': operator.gt,
    '>=': operator.ge,
    '==': operator.eq,
    '!=': operator.ne,
    '<': operator.lt,
    '<=': operator.le,
}


class Node(BaseNode):
    """Multi-purposes math utility node with customizable operator"""

    # Define class members
    ver = '0.0.1'
    node_label = 'Multi-purpose math operator'
    node_type = NodeTypeFlag.Pure
    pin_dict = {
        'A': InputPinType.WildCard,
        'Operator': InputPinType.String,
        'B': InputPinType.WildCard,
        'Result': OutputPinType.WildCard
    }

    @staticmethod
    def run(internal_data_dict):
        internal_data_dict['Result'] = operator_mapping[internal_data_dict['Operator']](internal_data_dict['A'],
                                                                                        internal_data_dict['B'])
