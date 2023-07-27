import logging
from logging.handlers import QueueHandler
from multiprocessing import Queue
from logging import Logger


def create_queueHandler_logger(logger_name: str, queue: Queue, is_debug_mode: bool) -> Logger:
    logger = logging.getLogger(logger_name)
    qh = QueueHandler(queue)
    logger.addHandler(qh)
    if is_debug_mode:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger
