import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import win32gui
import sys


def opencv_detect():
    img_rgb = cv.imread('res/lena.jpg')
    img_gray = cv.cvtColor(img_rgb, cv.COLOR_BGR2GRAY)
    template = cv.imread('res/template.jpg', 0)
    w, h = template.shape[::-1]
    res = cv.matchTemplate(img_gray, template, cv.TM_CCOEFF_NORMED)
    threshold = 0.8
    loc = np.where(res >= threshold)
    img_rgb = cv.imread('res/lena.jpg')
    for pt in zip(*loc[::-1]):
        cv.rectangle(img_rgb, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)

    cv.imwrite('res.png', img_rgb)

    # 因为opencv是BGR格式，需要转换成RGB格式
    b, g, r = cv.split(img_rgb)
    dst = cv.merge([r, g, b])
    plt.imshow(dst)
    plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
    plt.suptitle("ri")
    plt.show()


def screen_shot():
    hwnd_title = dict()

    def get_all_hwnd(hwnd, mouse):
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
            hwnd_title.update({hwnd: win32gui.GetWindowText(hwnd)})

    win32gui.EnumWindows(get_all_hwnd, 0)
    for h, t in hwnd_title.items():
        if t is not "":
            screen = QGuiApplication.primaryScreen()
            window = screen.grabWindow(h)
            if window is not None:
                img = window.toImage()
                img.save("./temp/" + t + ".jpg")


if __name__ == "__main__":
    # app = QApplication(sys.argv)
    # widget = QWidget()
    # widget.show()
    # screen_shot()
    # app.exec()
    opencv_detect()
