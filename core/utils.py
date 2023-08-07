import json
import logging
import os
import platform
from logging.handlers import QueueHandler
from multiprocessing import Queue
from logging import Logger
from pathlib import Path
from time import perf_counter
from uuid import uuid1
from typing import Union

from dearpygui import dearpygui as dpg

timer_registry = [0]


def create_queueHandler_logger(logger_name: str, queue: Queue, is_debug_mode: bool) -> Logger:
    logger = logging.getLogger(logger_name)
    qh = QueueHandler(queue)
    logger.addHandler(qh)
    if is_debug_mode:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger


def extract_var_name_from_node_info(node_info: dict) -> str:
    node_label = node_info['label']
    return ' '.join(node_label.split(' ')[1:])


def dpg_set_value(tag: Union[int, str], value):
    """
    Check if exist node with tag, then set the value
    :param tag: tag to check
    :param value: value to set
    """

    if dpg.does_item_exist(tag):
        dpg.set_value(tag, value)


def dpg_get_value(tag: str):
    """
    Get value from a node with tag
    :param tag: tags of node to query value
    :return: the value of node with tag
    """
    value = None
    if dpg.does_item_exist(tag):
        value = dpg.get_value(tag)
    return value


def json_load_from_file_path(file_path) -> dict:
    with open(file_path, 'r') as fp:
        try:
            return_dict = json.load(fp)
            return return_dict
        except FileNotFoundError:
            return {}


def json_write_to_file_path(file_path, value: dict):
    with open(file_path, 'w') as fp:
        json.dump(value, fp, indent=4)


def start_timer():
    global timer_registry
    timer_registry[0] = perf_counter()


def stop_timer_and_get_elapsed_time() -> float:
    start_time = timer_registry[0]
    return perf_counter() - start_time


def generate_uuid() -> str:
    """Generate a UUID1
    :return: uuid1
    """
    # Use UUID1 because it is time based so no replication produced
    return uuid1().hex


def add_user_input_box(var_type, callback=None, default_value=None,
                       user_data=None, text='', add_separator=False, width=None,
                       tag='') -> str:
    if not tag:
        user_input_box_tag = generate_uuid()
    else:
        user_input_box_tag = tag
    if text:
        dpg.add_text(text)
    if default_value is None:
        _default_value = get_var_default_value_on_type(var_type)
    else:
        _default_value = default_value
    if width is None:
        _width = 200
    else:
        _width = width
    if var_type == 'String':
        dpg.add_input_text(on_enter=True, default_value=_default_value,
                           callback=callback,
                           user_data=user_data,
                           hint='one line text',
                           width=_width,
                           tag=user_input_box_tag)
    elif var_type == 'Int':
        dpg.add_input_int(on_enter=True, default_value=_default_value,
                          callback=callback,
                          user_data=user_data,
                          width=_width,
                          tag=user_input_box_tag)

    elif var_type == 'Float':
        dpg.add_input_float(on_enter=True, default_value=_default_value,
                            callback=callback,
                            user_data=user_data,
                            width=_width,
                            tag=user_input_box_tag)
    elif var_type == 'MultilineString':
        dpg.add_input_text(on_enter=True, multiline=True,
                           default_value=_default_value,
                           callback=callback,
                           user_data=user_data,
                           width=_width,
                           tag=user_input_box_tag)
    elif var_type == 'Password':
        dpg.add_input_text(on_enter=True, password=True,
                           default_value=_default_value,
                           callback=callback,
                           user_data=user_data,
                           hint='password',
                           width=_width,
                           tag=user_input_box_tag)
    elif var_type == 'Bool':
        dpg.add_checkbox(callback=callback,
                         default_value=_default_value,
                         user_data=user_data,
                         tag=user_input_box_tag)
    if add_separator:
        dpg.add_separator()
    return user_input_box_tag


def get_var_default_value_on_type(var_type: str):
    if var_type in ['String', 'MultilineString', 'Password']:
        return ''
    elif var_type == 'Int':
        return 0
    elif var_type == 'Float':
        return 0.0
    elif var_type == 'Bool':
        return False
    else:
        return None


def log_on_return_message(logger, action: str, return_message=(0, ''), **kwargs):
    return_code = return_message[0]
    message = return_message[1]
    if return_code == 0:
        logger.info(f'{action} was skipped!')
        if message:
            logger.debug(message)
    elif return_code == 1:
        logger.info(f'{action} performed successfully')
        if message:
            logger.debug(message)
    elif return_code == 2:
        logger.info(f'{action} was performed partially')
        if message:
            logger.debug(message)
    elif return_code == 3:
        logger.info(f'{action} did not performed. Failure encountered. Please check the log for details')
        if message:
            logger.error(message)
    elif return_code == 4:
        logger.info(f'{action} did not performed. Exception encountered')
        if message:
            logger.error(message)




def construct_tool_path_from_tools_path_and_tool_name(tools_path: Path, tool_name: str) -> str:
    return (tools_path / (tool_name + '.rtool')).as_posix()


def convert_python_path_to_import_path(python_path: Path) -> str:
    # split up files names and import them
    import_path = os.path.splitext(
        os.path.normpath(python_path)
    )[0]
    if platform.system() == 'Windows':
        import_path = import_path.replace('\\', '.')
    else:
        import_path = import_path.replace('/', '.')
    import_path = import_path.split('.')
    import_path = '.'.join(import_path[-3:])
    return import_path


def is_string_contains_special_characters(check_string: str) -> bool:
    special_chars_list = ['*', '/', '\\']
    for special_char in special_chars_list:
        if special_char in check_string:
            return True
    return False


def remove_node_type_from_node_label(node_label: str):
    return ' '.join(node_label.split(' ')[1:])
