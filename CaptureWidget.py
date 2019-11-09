from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from config import config


class CaptureWidget(QWidget):
    North = 0
    South = 1
    West = 2
    east = 3

    def __init__(self):
        super(CaptureWidget, self).__init__()
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip)
        self.user_name = ""
        self.game_is_start = False
        self.is_playing = False
        self.direct = -1

    # 根据识别到的开始点，定位整个窗口的位置信息
    def set_point(self, point):
        res = config.instance().get_res()
        self.move(point.x() - res["game"]["rec_offset_width"], point.y() - res["game"]["rec_offset_height"])

    def set_user_name(self, user_name):
        self.user_name = user_name

    def is_game_start(self):
        return self.game_is_start

    def set_game_start(self, is_game_start):
        self.game_is_start = is_game_start

    def set_is_playing(self, is_playing):
        self.is_playing = is_playing

    def get_is_playing(self):
        return self.is_playing

    def get_user_name(self):
        return self.user_name

    def set_user_direct(self, direct):
        self.direct = direct

    def get_user_direct(self):
        return self.direct

    def sizeHint(self):
        res = config.instance().get_res()
        return QSize(res["game"]["width"], res["game"]["height"])

    def paintEvent(self, QPaintEvent):
        painter = QPainter(self)
        pen = QPen()
        pen.setColor(QColor(23, 200, 76, 100))
        pen.setWidth(5)
        painter.setPen(pen)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
        super(CaptureWidget, self).paintEvent(QPaintEvent)
