import cv2 as cv
import numpy as np
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from OperateWidget import OperateWidget
import threading
from CaptureWidget import CaptureWidget
from config import config


def qimage_to_cv_mat(incomingImage):
    incomingImage = incomingImage.convertToFormat(QImage.Format.Format_RGB32)
    width = incomingImage.width()
    height = incomingImage.height()
    ptr = incomingImage.constBits()
    ptr.setsize(height * width * 4)
    arr = np.array(ptr).reshape(height, width, 4)  # Copies the data
    return arr


class Recognition(QObject):
    _instance_lock = threading.Lock()

    def __init__(self):
        super(Recognition, self).__init__()
        self.capture_widgets = []
        self.capture_timer = QTimer()
        res = config.instance().get_res()
        self.capture_timer.setInterval(res["game"]["capture_interval"])
        self.capture_timer.timeout.connect(self.recgnoze)

    def clear_capture_widgets(self):
        self.capture_timer.stop()
        # 启动时重新识别所有窗口，需要清理原先已识别窗口
        for capture in self.capture_widgets:
            capture.deleteLater()
        self.capture_widgets = []

    def get_screen_img(self):
        screen = QGuiApplication.primaryScreen()
        window = screen.grabWindow(0)
        img = window.toImage()
        return qimage_to_cv_mat(img)

    @pyqtSlot()
    def recgnoze(self):
        img = self.get_screen_img()
        res = config.instance().get_res()
        # 遍历窗口
        for widget in self.capture_widgets:
            capture_img = self.get_img_rect(img, widget.geometry())
            # 如果游戏还没有开始不识别
            if widget.is_game_start() is False:
                started_img = cv.imread(res["game"]["game_started"], 0)
                rc_rects = self.detect_image(capture_img, started_img)
                if len(rc_rects) > 0:
                    OperateWidget.instance().show_log("用户{}匹配到房间游戏开始".format(widget.get_user_name()))
                    widget.set_game_start(True)
                else:
                    OperateWidget.instance().show_log("用户{}正在匹配房间".format(widget.get_user_name()))
                    continue

            # 判断是否是当前用户正在打牌
            playing_img = self.get_img_rect(capture_img, QRect(332, 232, 28, 16))
            if np.mean(playing_img) > 120:
                OperateWidget.instance().show_log("用户{}正在打牌".format(widget.get_user_name()))

    @pyqtSlot()
    def start_game(self):
        self.capture_timer.start()

    @pyqtSlot()
    def start_recognize(self):
        OperateWidget.instance().show_log("识别启动，开始查找目标窗口")
        res = config.instance().get_res()
        template = cv.imread(res["game"]["rec_image"], 0)

        self.clear_capture_widgets()
        # 获取屏幕截图
        img = self.get_screen_img()
        rects = self.detect_image(img, template)
        window_count = len(rects)
        if window_count > 0:
            OperateWidget.instance().show_log("识别窗口成功，找到{}个目标窗口".format(window_count))
            count = 1
            # 创建已识别窗口
            for rect in rects:
                caputure_w = CaptureWidget()
                caputure_w.set_point(rect.topLeft())
                caputure_w.show()
                self.capture_widgets.append(caputure_w)

                # 识别该窗口是属于哪个用户的
                OperateWidget.instance().show_log("开始识别第{}个用户".format(count))
                caputure_img = self.get_img_rect(img, caputure_w.geometry())
                user_name = None
                for user in res["users"]:
                    user_img = cv.imread(user["user_image"], 0)
                    user_rects = self.detect_image(caputure_img, user_img)
                    if len(user_rects) > 0:
                        user_name = user["name"]
                        OperateWidget.instance().show_log("找到用户{}".format(user_name))
                        caputure_w.set_user_name(user_name)
                        break
                if user_name is None:
                    # 截取用户图片
                    # 弹出窗口，让用户设置该图片的用户名
                    # 设置完之后，保存到json
                    OperateWidget.instance().show_log("捕获到的窗口没有找到相应的用户")
                count = count + 1
        else:
            OperateWidget.instance().show_log("识别窗口失败，没有找到目标窗口，"
                                              "请确认游戏窗口是否启动，并停留在开始界面")

    def get_img_rect(self, img, rect):
        return img[rect.top():(rect.top() + rect.height()), rect.left():(rect.left() + rect.width())]

    def detect_image(self, src_img, dest_img):
        img_gray = cv.cvtColor(src_img, cv.COLOR_BGR2GRAY)
        res = cv.matchTemplate(img_gray, dest_img, cv.TM_CCOEFF_NORMED)
        threshold = 0.8
        loc = np.where(res >= threshold)
        w = dest_img.shape[0]
        h = dest_img.shape[1]
        rects = []
        for pt in zip(*loc[::-1]):
            rect = QRect(pt[0], pt[1], w, h)
            bFind = False
            # 相近去重
            for item in rects:
                if item.intersects(rect) is True:
                    bFind = True
                    break
            if bFind is False:
                rects.append(QRect(pt[0], pt[1], w, h))
        return rects

    @classmethod
    def instance(cls):
        with Recognition._instance_lock:
            if not hasattr(Recognition, "_instance"):
                Recognition._instance = Recognition()
        return Recognition._instance
