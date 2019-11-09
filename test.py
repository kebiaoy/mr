from win32gui import *

titles = list()


def foo(hwnd, mouse):
    if IsWindow(hwnd) and IsWindowEnabled(hwnd) and IsWindowVisible(hwnd):
        titles.append([GetWindowText(hwnd), hwnd])


EnumWindows(foo, 0)
lt = [t for t in titles if t]
lt.sort()
for t in lt:
    if t[0].find("欢乐麻将全集") >= 0:
        print(GetWindowRect(t[1]))
        MoveWindow(t[1], 0, 0, 700, 500, True)
