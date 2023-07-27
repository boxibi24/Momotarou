import argparse
import os
import json
import logging
from logging import Logger, Formatter, Handler
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Queue
from ui.NodeEditor.main_ui import initialize_node_editor_project, setup_dpg_font, initialize_dpg
import dearpygui.demo as demo

APPLICATION_NAME = 'NodeEditor'


def main():
    setting_file_path, is_debug_mode = parse_argument()
    logger, logger_queue = setup_logger(is_debug_mode)
    logger.info("***** Load Config *****")
    setting_dict = load_setting_file(setting_file_path)
    logger.info('**** DearPyGui Setup *****')
    initialize_dpg(editor_width=setting_dict['editor_width'], editor_height=setting_dict['editor_height'])
    setup_dpg_font()
    # demo.show_demo()
    logger.info('**** Initialize Node Editor Project *****')
    initialize_node_editor_project(setting_dict, logger_queue, is_debug_mode)
    logger.info('**** DearPyGui Terminated! *****')


def parse_argument():
    """
    Get flags from command line

    :return:
    """
    args = get_arg()
    setting_file_path = args.setting
    is_debug_mode = args.is_debug_mode

    return setting_file_path, is_debug_mode


def get_arg():
    """
    Get arg from CLI or use .cfg file as default

    :return:
    """
    parser = argparse.ArgumentParser(description="Riot Universal Tool - Node Editor", )

    parser.add_argument(
        "--setting",
        type=str,
        default=os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         f'Config/{APPLICATION_NAME}.cfg')),
    )
    parser.add_argument(
        "--is_debug_mode",
        action='store_false'
    )

    args = parser.parse_args()
    return args


def setup_logger(is_debug_mode: bool) -> tuple[Logger, Queue]:
    logger_name = APPLICATION_NAME
    logger = logging.getLogger(logger_name)
    logging_formatter = _get_logging_formatter(logger_name)
    _set_logger_level_on_debug_mode(logger, is_debug_mode)
    file_handler = _setup_file_handler(logger_name, logging_formatter)
    stream_handler = _setup_stream_handler(logging_formatter)
    logger_queue = _construct_and_add_queue_handler_to_logger(logger, file_handler, stream_handler)

    return logger, logger_queue


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


def _construct_and_add_queue_handler_to_logger(logger: Logger, *args: Handler):
    logger_queue = Queue()
    ql = QueueListener(logger_queue, *args, respect_handler_level=True)
    ql.start()
    qh = QueueHandler(logger_queue)
    logger.addHandler(qh)
    return logger_queue


def load_setting_file(file_path: str) -> dict:
    with open(file_path) as fp:
        setting_dict = json.load(fp)
    return setting_dict


if __name__ == '__main__':
    main()
