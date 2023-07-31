import dearpygui.dearpygui as dpg
import argparse
import os
import json
import logging
from logging.handlers import QueueHandler, QueueListener
from ui.ToolsViewer.tools_viewer import ToolsViewer
from multiprocessing import Process, Queue
import psutil


def get_arg():
    """Function to get arg from CLI or use NodeEditor.cfg as default"""
    parser = argparse.ArgumentParser(description="Riot Universal Tool - Tools Viewer", )

    parser.add_argument(
        "--setting",
        type=str,
        default=os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         'Config/ToolsViewer.cfg')),
    )

    parser.add_argument(
        "--is_debug_mode",
        action='store_false'
    )

    args = parser.parse_args()
    return args


def kill_proc_tree(pid):
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    for child in children:
        child.kill()


def main():
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


if __name__ == '__main__':
    main()
