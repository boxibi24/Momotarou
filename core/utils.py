import json
import logging
from logging.handlers import QueueHandler
from multiprocessing import Queue
from logging import Logger
from time import perf_counter

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


def dpg_set_value(tag: str, value):
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
