from tkinter import Tk, filedialog, PhotoImage
import dearpygui.dearpygui as dpg
from pathlib import Path


def tkinter_file_dialog() -> Path:
    root = Tk()
    root.withdraw()  # Hide the main tkinter window
    icon_photo = PhotoImage(file='icons/logo_square.png')
    root.iconphoto(False, icon_photo)
    file_path = filedialog.askopenfilename(title='Open Project',
                                           filetypes=[('MPROJECT Files', '*.mproject')],
                                           initialdir=Path(__file__).parent.parent.parent)
    root.destroy()
    return Path(file_path)


def get_node_by_id(data: list, uid: str) -> dict:
    result = None
    for each in data:
        if each["id"] == uid:
            result = each
            break
    return result


def callback_project_open_menu():
    dpg.show_item('project_open')
