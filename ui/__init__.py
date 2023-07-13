# __version__ = "0.0.1"
#
# import logging
# import logging.config
# import os
#
# current_dir = os.path.dirname(os.path.abspath(__file__))
# master_log_dir = os.path.dirname(current_dir) + '/Logs'
# print("Master log Dir:", master_log_dir)
# if not os.path.exists(master_log_dir):
#     os.mkdir(master_log_dir)
#
# config_file_path = current_dir + '/Config/Logger.cfg'
# logging.config.fileConfig(fname=config_file_path, disable_existing_loggers=False)
#
# default_logger = logging.getLogger(__name__)
#
# module_formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s]: %(message)s')
#
#
# def add_module_handler(logger: logging.Logger,
#                        current_path,
#                        level_fileHandler=logging.DEBUG,
#                        level_streamHandler=logging.INFO):
#     # Add file handler
#     log_dir = current_path + '/Logs'
#     if not os.path.exists(log_dir):
#         os.mkdir(log_dir)
#     fileHandler = logging.FileHandler(f"{log_dir}/{logger.name.replace('.', '-')}.log", mode='w')
#     fileHandler.setLevel(level_fileHandler)
#     fileHandler.setFormatter(module_formatter)
#     logger.addHandler(fileHandler)
#     # Add stream handler
#     streamHandler = logging.StreamHandler()
#     streamHandler.setLevel(level_streamHandler)
#     streamHandler.setFormatter(module_formatter)
#     logger.addHandler(streamHandler)
