import json
from tkinter import Tk, filedialog
import logging
from logging.handlers import QueueHandler


def load_json() -> dict:
    root = Tk()
    root.withdraw()  # Hide the main tkinter window
    file_path = filedialog.askopenfilename(filetypes=[('JSON Files', '*.json')])
    if file_path:
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
                return data
            except json.JSONDecodeError:
                pass


def get_node_by_id(data: list, uid: str) -> dict:
    result = None
    for each in data:
        if each["id"] == uid:
            result = each
            break
    return result


def create_queueHandler_logger(logger_name, queue, is_debug_mode: bool):
    logger = logging.getLogger(logger_name)
    qh = QueueHandler(queue)
    logger.addHandler(qh)
    if is_debug_mode:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger
