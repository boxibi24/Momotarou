import argparse
import os
import json
import logging
from logging import Logger, Formatter, Handler
from logging.handlers import QueueHandler, QueueListener

from libs.constants import TOOLS_VIEWER_APP_NAME, LOCALAPPDATA
from multiprocessing import Queue
from typing import Tuple
import psutil
from core.executor import setup_executor_logger
from core.utils import json_load_from_file_path
from ui.ToolsViewer.main_ui import initialize_dpg, setup_dpg_font, setup_dpg_icon, initialize_tools_viewer_project


def main():
    setting_file_path, packages_file_path, is_debug_mode, project_path = parse_argument()
    logger, logger_queue, queue_listener = setup_logger(is_debug_mode)
    logger.info("***** Load Config *****")
    setting_dict = json_load_from_file_path(setting_file_path)
    logger.info('**** DearPyGui Setup *****')
    initialize_dpg(editor_width=setting_dict['viewport_width'], editor_height=setting_dict['viewport_height'])
    setup_dpg_font()
    setup_dpg_icon()
    logger.info('**** Initialize Node Editor Project *****')
    initialize_tools_viewer_project(setting_dict, logger_queue, is_debug_mode, project_path)
    logger.info('**** DearPyGui Terminated! *****')
    on_terminate_application(queue_listener)


def parse_argument():
    """
    Get flags from command line

    :return:
    """
    args = get_arg()
    setting_file_path = args.setting
    packages_file_path = args.packages
    is_debug_mode = args.is_debug_mode
    project_path = args.project_path

    return setting_file_path, packages_file_path, is_debug_mode, project_path


def get_arg():
    """
    Get arg from CLI or use .cfg file as default

    :return:
    """
    parser = argparse.ArgumentParser(description="Riot Universal Tool - Tools Viewer", )

    parser.add_argument(
        "--setting",
        type=str,
        default=os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         f'Config/{TOOLS_VIEWER_APP_NAME}.cfg')),
    )
    parser.add_argument(
        "--packages",
        type=str,
        default=os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         f'Config/NodePackages.cfg')),
    )
    parser.add_argument(
        "--is_debug_mode",
        action='store_true'
    )

    parser.add_argument(
        "--project_path",
        type=str,
    )

    args = parser.parse_args()
    return args


def setup_logger(is_debug_mode: bool) -> Tuple[Logger, Queue, QueueListener]:
    logger, logger_queue, queue_listener = _setup_main_logger(is_debug_mode)
    setup_executor_logger(logger_queue, is_debug_mode)
    return logger, logger_queue, queue_listener


def _setup_main_logger(is_debug_mode: bool) -> Tuple[Logger, Queue, QueueListener]:
    logger_name = TOOLS_VIEWER_APP_NAME
    logger = logging.getLogger(logger_name)
    logging_formatter = _get_logging_formatter(logger_name)
    _set_logger_level_on_debug_mode(logger, is_debug_mode)
    file_handler = _setup_file_handler(logger_name, logging_formatter)
    stream_handler = _setup_stream_handler(logging_formatter)
    _set_handler_level_on_debug_mode(is_debug_mode, file_handler, stream_handler)
    logger_queue, queue_listener = _construct_and_add_queue_handler_to_logger(logger, file_handler, stream_handler)

    return logger, logger_queue, queue_listener


def _get_logging_formatter(config_file_name: str) -> Formatter:
    config_file_path = _get_config_file_path_from_name(config_file_name)
    return _get_logging_formatter_from_config_file(config_file_path)


def _get_logging_formatter_from_config_file(config_file_path) -> Formatter:
    with open(config_file_path) as fp:
        json_dict = json.load(fp)

    return logging.Formatter(json_dict['logging_format'])


def _get_config_file_path_from_name(config_file_name):
    outer_dir = os.path.dirname(os.path.abspath(__file__))
    return outer_dir + f'/Config/{config_file_name}.cfg'


def _set_logger_level_on_debug_mode(logger: Logger, is_debug_mode: bool):
    # Set logger level based on user args
    if is_debug_mode:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


def _get_log_output_dir(logger_name: str) -> str:
    log_folder = LOCALAPPDATA / 'Logs'
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)
    log_dir = log_folder / f'{logger_name}.log'
    return log_dir.as_posix()


def _setup_file_handler(logger_name: str, handler_formatter: Formatter) -> Handler:
    log_dir = _get_log_output_dir(logger_name)
    fileHandler = logging.FileHandler(log_dir, mode='w')
    fileHandler.setLevel(logging.DEBUG)
    fileHandler.setFormatter(handler_formatter)
    return fileHandler


def _setup_stream_handler(handler_formatter: Formatter) -> Handler:
    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(logging.INFO)
    streamHandler.setFormatter(handler_formatter)
    return streamHandler


def _set_handler_level_on_debug_mode(is_debug_mode: bool, *args: Handler):
    if is_debug_mode:
        for handler in args:
            handler.setLevel(logging.DEBUG)
    else:
        for handler in args:
            handler.setLevel(logging.INFO)


def _construct_and_add_queue_handler_to_logger(logger: Logger, *args: Handler) -> Tuple[Queue, QueueListener]:
    logger_queue = Queue()
    ql = QueueListener(logger_queue, *args, respect_handler_level=True)
    ql.start()
    qh = QueueHandler(logger_queue)
    logger.addHandler(qh)
    return logger_queue, ql


def on_terminate_application(queue_listener: QueueListener):
    queue_listener.stop()
    # Kill child processes if still alive
    this_proc = os.getpid()
    kill_proc_tree(this_proc)


def kill_proc_tree(pid):
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    for child in children:
        child.kill()


if __name__ == '__main__':
    main()
