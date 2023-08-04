import dearpygui.dearpygui as dpg
import argparse
import os
import json
import logging
from logging import Logger, Formatter, Handler
from logging.handlers import QueueHandler, QueueListener

from lib.constants import TOOLS_VIEWER_APP_NAME
from ui.ToolsViewer.tools_viewer_project import ToolsViewer
from multiprocessing import Process, Queue
from typing import Tuple
import psutil
from core.executor import setup_executor_logger
from core.utils import json_load_from_file_path
from ui.ToolsViewer.main_ui import initialize_dpg, setup_dpg_font, initialize_tools_viewer_project


def main():
    setting_file_path, packages_file_path, is_debug_mode = parse_argument()
    logger, logger_queue, queue_listener = setup_logger(is_debug_mode)
    logger.info("***** Load Config *****")
    setting_dict = json_load_from_file_path(setting_file_path)
    packages_list = json_load_from_file_path(packages_file_path)['packages']
    logger.info('**** DearPyGui Setup *****')
    initialize_dpg(editor_width=setting_dict['viewport_width'], editor_height=setting_dict['viewport_height'])
    setup_dpg_font()
    logger.info('**** Initialize Node Editor Project *****')
    initialize_tools_viewer_project(setting_dict, packages_list, logger_queue, is_debug_mode)
    logger.info('**** DearPyGui Terminated! *****')
    _on_terminate_project(queue_listener)


def kill_proc_tree(pid):
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    for child in children:
        child.kill()


def main_old():
    # Get args
    args = get_arg()
    setting = args.setting
    is_debug_mode = args.is_debug_mode

    # Get logger format
    outer_dir = os.path.dirname(os.path.abspath(__file__))
    fp_path = outer_dir + '/Config/ToolsViewer.cfg'
    with open(fp_path) as fp:
        json_dict = json.load(fp)

    module_formatter = logging.Formatter(json_dict['logging_format'])

    # Setup master logger

    current_file_path = os.path.dirname(os.path.abspath(__file__))
    logger = logging.getLogger('ToolsViewer')
    logger_queue = Queue()
    # Set logger level based on user args
    if is_debug_mode:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    # Define log output dir
    log_dir = current_file_path + '/Logs'
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    fileHandler = logging.FileHandler(f'{log_dir}/{logger.name}.log', mode='w')
    fileHandler.setLevel(logging.DEBUG)
    fileHandler.setFormatter(module_formatter)

    # Add stream handler
    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(logging.INFO)
    streamHandler.setFormatter(module_formatter)

    # Create Queue listener to handle multiprocessing logging
    queue_listener = QueueListener(logger_queue, fileHandler, streamHandler, respect_handler_level=True)
    # Start listening to the queue
    queue_listener.start()
    qh = QueueHandler(logger_queue)
    logger.addHandler(qh)

    # Load config
    logger.info("***** Load Config *****")
    with open(setting) as fp:
        setting_dict = json.load(fp)
    # DearPyGui window settings
    viewport_width = setting_dict['viewport_width']
    viewport_height = setting_dict['viewport_height']

    # start the logger process

    logger.info('**** DearPyGui Setup *****')
    dpg.create_context()
    dpg.setup_dearpygui()
    dpg.create_viewport(
        title="RUT Tools Viewer",
        width=viewport_width,
        height=viewport_height
    )

    # Setup DPG font
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with dpg.font_registry():
        with dpg.font(
            current_dir +
            '/ui/ToolsViewer/font/OpenSans-Regular.ttf',
            16
        ) as default_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Vietnamese)
    dpg.bind_font(default_font)
    logger.info("**** Load Tools Viewer ****")
    tool_viewer = ToolsViewer(setting_dict=setting_dict, use_debug_print=is_debug_mode, logging_queue=logger_queue)
    dpg.show_viewport()

    # MULTIPROCESSING task queue initialization
    task_queue = Queue()
    # Keeping a number of processes to kill them when done
    NUMBER_OF_PROCESSES = 0
    logger.info('**** Start Main Event Loop ****')
    logger.debug("Running event's in parallel mode")
    while dpg.is_dearpygui_running():
        if tool_viewer.exec_flag:
            task_queue.put(tool_viewer.requested_exec_node_tag)
            Process(target=tool_viewer.worker, args=(task_queue, logger_queue)).start()
            NUMBER_OF_PROCESSES += 1
            tool_viewer.requested_exec_node_tag = None
        # TODO: this is inefficient, try an alternative
        # TODO: got buggy when closing the JSON file dialog
        with open(f'{current_file_path}/Logs/ToolsViewer.log', 'r') as f:
            try:
                dpg.configure_item('log', default_value=f.read())
            except:
                logger.exception('Error while trying to log:')
        # Now render the frame
        dpg.render_dearpygui_frame()

    logger.info('**** Terminate process ****')
    for i in range(NUMBER_OF_PROCESSES):
        task_queue.put('STOP')
    logger_queue.put(None)

    # Stop logging queue listener
    queue_listener.stop()

    logger.info('**** Close All Node ****')
    logger.info('**** Stop Event Loop ****')
    tool_viewer.terminate_flag = True
    logger.info('**** Destroy DearPyGui Context ****')
    dpg.destroy_context()

    # Kill child processes if still alive
    this_proc = os.getpid()
    kill_proc_tree(this_proc)


def parse_argument():
    """
    Get flags from command line

    :return:
    """
    args = get_arg()
    setting_file_path = args.setting
    packages_file_path = args.packages
    is_debug_mode = args.is_debug_mode

    return setting_file_path, packages_file_path, is_debug_mode


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
        action='store_false'
    )

    args = parser.parse_args()
    return args


def setup_logger(is_debug_mode: bool) -> tuple[Logger, Queue, QueueListener]:
    logger, logger_queue, queue_listener = _setup_main_logger(is_debug_mode)
    setup_executor_logger(logger_queue, is_debug_mode)
    return logger, logger_queue, queue_listener


def _setup_main_logger(is_debug_mode: bool) -> tuple[Logger, Queue, QueueListener]:
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
    current_path = os.path.dirname(os.path.abspath(__file__))
    log_folder = current_path + '/Logs'
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)
    log_dir = log_folder + f'/{logger_name}.log'
    return log_dir


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


def _on_terminate_project(queue_listener: QueueListener):
    queue_listener.stop()


if __name__ == '__main__':
    main()
