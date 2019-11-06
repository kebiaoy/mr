import win32gui


class WindowManager(object):
    @classmethod
    def get_all_hwnd(cls):
        all_hwnd = []

        def find_all_hwnd(hwnd, mouse):
            if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
                all_hwnd.append(hwnd)

        win32gui.EnumWindows(find_all_hwnd, 0)
        return all_hwnd
