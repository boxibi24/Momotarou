import requests
from core.utils import convert_version_to_int
from libs.constants import TOOLSET_NAME
import wx
import urllib3
import win32api
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class UpdateManager(tk.Toplevel):
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)

        self.transient(parent)
        self.result = None
        self.grab_set()
        w = 350
        h = 200
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) / 2
        y = (sh - h) / 2
        self.geometry('{0}x{1}+{2}+{3}'.format(w, h, int(x), int(y)))
        self.resizable(width=False, height=False)
        self.title('Update Manager')
        self.wm_iconbitmap('images/Graphicloads-Android-Settings-Contact.ico')

        def install_update():
            win32api.ShellExecute(0, 'open', f'tmp\\{TOOLSET_NAME}.msi', None, None, 10)
            parent.destroy()

        def start_update_manager():
            with requests.get('https://github.com/vsantiago113/Tkinter-MyTestApp/raw/master/'
                              'updates/MyTestApp.msi?raw=true', stream=True, verify=False) as r:
                self.progressbar['maximum'] = int(r.headers.get('Content-Length'))
                r.raise_for_status()
                with open(f'./tmp/{TOOLSET_NAME}.msi', 'wb') as f:
                    for chunk in r.iter_content(chunk_size=4096):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
                            self.progressbar['value'] += 4096
            self.button1.config(text='Install', state=tk.NORMAL)

        self.progressbar = ttk.Progressbar(self,
                                           orient='horizontal',
                                           length=200,
                                           mode='determinate',
                                           value=0,
                                           maximum=0)
        self.progressbar.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.button1 = ttk.Button(self, text='Wait!', state=tk.DISABLED, command=install_update)
        self.button1.place(x=-83, relx=1.0, y=-33, rely=1.0)

        self.t1 = threading.Thread(target=start_update_manager)
        self.t1.start()


def is_user_schedule_update_task(current_version: str, is_startup=True) -> bool:
    app = wx.App()
    if is_current_software_latest(current_version) and is_startup:
        del app
        return False
    elif is_current_software_latest(current_version) and not is_startup:
        wx.MessageBox(
            f'{TOOLSET_NAME} is already in latest version: {current_version}. '
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
    packages_data = requests.get("https://vngitlab.virtuosgames.com/api/v4/projects/110/packages", verify=False).json()
    return packages_data[-1]['version']


def update_tool_to_lastest_version():
    pass
