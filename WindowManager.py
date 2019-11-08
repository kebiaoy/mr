import win32api, win32gui, win32con
from ctypes import *


# 模拟鼠标单击
def left_button_click():
    win32api.mouse_event(
        win32con.MOUSEEVENTF_LEFTDOWN |
        win32con.MOUSEEVENTF_LEFTUP, 0, 0)


# 模拟移动鼠标
def move_cur_pos(x, y):
    windll.user32.SetCursorPos(x, y)

