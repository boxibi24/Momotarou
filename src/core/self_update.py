import requests
from core.utils import convert_version_to_int
from libs.constants import TOOLSET_NAME, TEMP_DIR
import os
import wx
import urllib3
import win32api
import tkinter as tk
from tkinter import ttk, PhotoImage
import threading

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class UpdateManager:
    def __init__(self, parent):
        self.window = tk.Toplevel()
        self.result = None
        self.parent = parent
        self.window.grab_set()
        w = 350
        h = 100
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = (sw - w) / 2
        y = (sh - h) / 2
        self.window.geometry('{0}x{1}+{2}+{3}'.format(w, h, int(x), int(y)))
        self.window.resizable(width=False, height=False)
        icon_photo = PhotoImage(file='icons/logo_square.png')
        self.window.iconphoto(False, icon_photo)
        self.msi_dir = TEMP_DIR / (TOOLSET_NAME + '.msi')

        def disable_event():
            pass

        def install_update():
            win32api.ShellExecute(0, 'open', self.msi_dir.as_posix(), None, None, 10)
            self.parent.destroy()

        def start_update_manager():

            if self.msi_dir.exists():
                os.remove(self.msi_dir)
            else:
                self.msi_dir.touch()

            with requests.get(f'https://vngitlab.virtuosgames.com/api/v4/projects/110/'
                              f'packages/generic/releases/{get_latest_version()}/{TOOLSET_NAME}.msi',
                              stream=True, verify=False) as r:
                self.progressbar['maximum'] = int(r.headers.get('Content-Length'))
                r.raise_for_status()

                with open(self.msi_dir, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=4096):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
                            self.progressbar['value'] += 4096
            self.button1.config(text='Install', state=tk.NORMAL)

        text = ttk.Label(self.window, text=f"Downloading {TOOLSET_NAME}.msi v{get_latest_version()}, please wait!")
        text.place(relx=0.5, rely=0.3, anchor=tk.CENTER)
        self.progressbar = ttk.Progressbar(self.window,
                                           orient='horizontal',
                                           length=200,
                                           mode='determinate',
                                           value=0,
                                           maximum=0)
        self.progressbar.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.button1 = ttk.Button(self.window, text='Wait!', state=tk.DISABLED, command=install_update)
        self.button1.place(x=-83, relx=1.0, y=-33, rely=1.0)
        self.window.protocol("WM_DELETE_WINDOW", disable_event)
        self.t1 = threading.Thread(target=start_update_manager)
        self.t1.start()


def is_user_schedule_update_task(current_version: str, is_startup=True) -> bool:
    app = wx.App()
    if is_current_software_latest(current_version) and is_startup:
        del app
        return False
    elif is_current_software_latest(current_version) and not is_startup:
        wx.MessageBox(
            f'{TOOLSET_NAME} is already in latest version: {current_version}. ',
            'Update information',
            wx.OK | wx.ICON_INFORMATION)
        del app
        return False

    msg_box_type = wx.YES | wx.NO | wx.ICON_WARNING
    result = wx.MessageBox(
        f'{TOOLSET_NAME} {current_version} needs to update to version {get_latest_version()}. '
        f'If not, some functions might not work!'
        f'\nSchedule an update?',
        'Update information',
        msg_box_type)

    if result == wx.YES:
        msg_box_type = wx.OK | wx.ICON_INFORMATION
        wx.MessageBox(
            "The update task has been scheduled to be run after you close the current session!",
            'Update information',
            msg_box_type)
        del app
        return True
    else:
        del app
        return False


def is_current_software_latest(current_version: str) -> bool:
    if convert_version_to_int(current_version) < convert_version_to_int(get_latest_version()):
        return False
    return True


def get_latest_version() -> str:
    session = requests.Session()
    try:
        packages_data = requests.get("https://vngitlab.virtuosgames.com/api/v4/projects/110/packages",
                                     verify=False).json()
        return packages_data[-1]['version']
    except requests.exceptions.ConnectionError:
        app = wx.App()
        wx.MessageBox(
            'Failed to connect to https://vngitlab.virtuosgames.com ! '
            'Try turning off VPN or troubleshooting your internet connection.',
            'Update connection error',
            wx.OK | wx.ICON_ERROR)
        del app
        return '1.0.0'


def update_tool_to_lastest_version():
    root = tk.Tk()
    root.withdraw()
    root.title('Update Downloader')
    UpdateManager(root)
    root.mainloop()


def init_update_manager_ui():
    t1 = threading.Thread(target=update_tool_to_lastest_version)
    t1.start()
