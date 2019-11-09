import cv2 as cv
import numpy as np
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from OperateWidget import OperateWidget
import threading
from CaptureWidget import CaptureWidget
from config import config
from win32gui import *
from UserNameSetting import UserNameSetting
import qimage2ndarray


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
        self.capture_timer = QTimer(self)
        self.find_game_timer = QTimer(self)
        res = config.instance().get_res()
        self.capture_timer.setInterval(res["game"]["capture_interval"])
        self.capture_timer.timeout.connect(self.recgnoze)

    def sort_window(self):
        titles = list()
        res = config.instance().get_res()

        def foo(hwnd, mouse):
            if IsWindow(hwnd) and IsWindowEnabled(hwnd) and IsWindowVisible(hwnd):
                titles.append([GetWindowText(hwnd), hwnd])

        EnumWindows(foo, 0)
        lt = [t for t in titles if t]
        lt.sort()
        x = res["game"]["sort_x"]
        y = res["game"]["sort_y"]
        for t in lt:
            if t[0].find(res["game"]["name"]) >= 0:
                rc = GetWindowRect(t[1])
                is_repaint = True
                if rc[2] == res["game"]["width"] and rc[3] == res["game"]["height"]:
                    is_repaint = True
                MoveWindow(t[1], x, y, res["game"]["width"], res["game"]["height"], is_repaint)
                if x == 0:
                    x += res["game"]["width"]
                    continue
                if x > 0:
                    y += res["game"]["height"]
                    x = 0

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

    def is_game_over(self, capture_img):
        res = config.instance().get_res()
        game_over_image = cv.imread(res["game"]["game_over"], 0)
        rc_rects = self.detect_image(capture_img, game_over_image)
        if len(rc_rects) > 0:
            return True
        return False

    def is_game_start(self, capture_img):
        res = config.instance().get_res()
        started_img = cv.imread(res["game"]["game_started"], 0)
        rc_rects = self.detect_image(capture_img, started_img)
        if len(rc_rects) > 0:
            return True
        return False

    def get_direct(self, capture_img):
        res = config.instance().get_res()
        directs = res["game"]["direct"]
        for i in range(len(directs)):
            direct_0 = cv.imread(directs[i]["img"], 0)
            rc_rects = self.detect_image(capture_img, direct_0)
            if len(rc_rects) > 0:
                return i
            direct_0 = cv.imread(directs[i]["confirm_img"], 0)
            rc_rects = self.detect_image(capture_img, direct_0)
            if len(rc_rects) > 0:
                return i
        return -1

    def save_img(self, img, widget, file_path):
        datatime = QDateTime.currentDateTime()
        file_name = file_path + datatime.toString(
            "yyyyMMddhhmmsszzz") + widget.get_user_name() + ".jpg"
        cv.imwrite(file_name, img)

    def is_user_playing(self, widget, img):
        res = config.instance().get_res()
        direct = widget.get_user_direct()
        if direct < 0:
            return False
        direct_0 = cv.imread(res["game"]["direct"][direct]["img"], 0)
        rc_rects = self.detect_image(img, direct_0)
        if len(rc_rects) > 0:
            return False
        direct_0 = cv.imread(res["game"]["direct"][direct]["confirm_img"], 0)
        rc_rects = self.detect_image(img, direct_0)
        if len(rc_rects) > 0:
            return True
        return False

    @pyqtSlot()
    def recgnoze(self):
        img = self.get_screen_img()
        res = config.instance().get_res()
        # 遍历窗口
        for widget in self.capture_widgets:
            capture_img = self.get_img_rect(img, widget.geometry())
            if OperateWidget.instance().use_collection() is True:
                self.save_img(capture_img, widget, res["game"]["collection_dir"])

            # 如果游戏还没有开始不识别
            if widget.is_game_start() is False:
                if self.is_game_start(capture_img) is True:
                    OperateWidget.instance().show_log("用户{}匹配到房间，游戏开始".format(widget.get_user_name()))
                    widget.set_game_start(True)
                    self.save_img(capture_img, widget, res["game"]["error_dir"])
                    # 判别用户方位
                    direct = self.get_direct(capture_img)
                    if direct < 0:
                        OperateWidget.instance().show_log("获取用户{}方位失败".format(widget.get_user_name()))
                        self.save_img(capture_img, widget, res["game"]["error_dir"])
                    else:
                        OperateWidget.instance().show_log("获取用户{}方位成功".format(widget.get_user_name()))
                        widget.set_user_direct(direct)
                else:
                    OperateWidget.instance().show_log("用户{}正在匹配房间".format(widget.get_user_name()))
                    continue

            # 判断游戏是否结束
            if self.is_game_over(capture_img) is True:
                OperateWidget.instance().show_log("用户{}游戏结束".format(widget.get_user_name()))
                widget.set_game_start(False)
                widget.set_is_playing(False)
                continue

            # 判断是否是当前用户正在打牌
            is_playing = self.is_user_playing(widget, capture_img)
            if is_playing is True and widget.get_is_playing() is False:
                OperateWidget.instance().show_log("用户{}正在打牌".format(widget.get_user_name()))
                widget.set_is_playing(True)
                self_card_info, self_gang_peng_info = self.get_all_self_card(capture_img, widget)
                hand_card_info = ""
                gang_peng_card_info = ""
                for cards in self_card_info:
                    for card in cards:
                        hand_card_info = hand_card_info + " " + res["card_name"][str(card["card_id"])]["name"]
                for cards in self_gang_peng_info:
                    for card in cards:
                        gang_peng_card_info = gang_peng_card_info + " " + res["card_name"][str(card - 100)]["name"]
                OperateWidget.instance().show_log("用户{}手牌为：".format(widget.get_user_name()) + hand_card_info)
                OperateWidget.instance().show_log("用户{}杠碰为：".format(widget.get_user_name()) + gang_peng_card_info)

            elif is_playing is False and widget.get_is_playing() is True:
                widget.set_is_playing(False)
                OperateWidget.instance().show_log("用户{}打完牌，等待其它用户出牌".format(widget.get_user_name()))

    def get_all_self_card(self, capture_img, widget):
        res = config.instance().get_res()
        hand_card_dir = res["game"]["bottom_image_hand"]
        bottom_rect = res["game"]["bottom_area"]
        bottom_area_img = self.get_img_rect(capture_img,
                                            QRect(bottom_rect[0], bottom_rect[1], bottom_rect[2],
                                                  bottom_rect[3]))
        hand_card = []
        gang_peng = []
        leave_count = res["game"]["handle_card_total"]
        # 查找手牌万子
        cards, length = self.find_card(1, 10, bottom_area_img, hand_card_dir, False)
        leave_count = leave_count - length
        hand_card.append(cards)
        if leave_count != 0:
            # 查找手牌条子
            cards, length = self.find_card(11, 20, bottom_area_img, hand_card_dir, False)
            leave_count = leave_count - length
            hand_card.append(cards)
            if leave_count != 0:
                # 查找手牌筒子
                cards, length = self.find_card(21, 30, bottom_area_img, hand_card_dir, False)
                leave_count = leave_count - length
                hand_card.append(cards)
                if leave_count != 0:
                    # 查找东南西北中发财白板
                    cards, length = self.find_card(31, 38, bottom_area_img, hand_card_dir, False)
                    leave_count = leave_count - length
                    hand_card.append(cards)

        # 如果手牌没有找齐，开始找杠碰牌
        if leave_count > 0:
            cards, length = self.find_card(101, 110, bottom_area_img, hand_card_dir, True)
            leave_count = leave_count - length
            gang_peng.append(cards)
            if leave_count > 0:
                cards, length = self.find_card(111, 120, bottom_area_img, hand_card_dir, True)
                leave_count = leave_count - length
                gang_peng.append(cards)
                if leave_count > 0:
                    cards, length = self.find_card(121, 130, bottom_area_img, hand_card_dir, True)
                    leave_count = leave_count - length
                    gang_peng.append(cards)
                    if leave_count > 0:
                        cards, length = self.find_card(131, 138, bottom_area_img, hand_card_dir, True)
                        leave_count = leave_count - length
                        gang_peng.append(cards)

        if leave_count != 0:
            OperateWidget.instance().show_log("获取用户{}手牌失败".format(widget.get_user_name()))
            # self.save_img(capture_img, widget, res["game"]["error_dir"])
        return hand_card, gang_peng

    def find_card(self, start, end, area_img, temp_dir, is_gang_peng):
        file = QFile()
        card = []
        length = 0
        for i in range(start, end):
            img_dir = temp_dir + "{}.jpg".format(i)
            if file.exists(img_dir) is False:
                continue
            template = cv.imread(img_dir, 0)
            rects = self.detect_image(area_img, template)
            if is_gang_peng is True:
                length += 3
                # 识别到碰牌
                if len(rects) == 2:
                    # 查找有多少个转置
                    img_dir = temp_dir + "{}_t.jpg".format(i)
                    count = 3
                    if file.exists(img_dir) is True:
                        template_t = cv.imread(img_dir, 0)
                        rects_t = self.detect_image(area_img, template_t)
                        if len(rects_t) > 0:
                            count += len(rects_t)
                    for k in range(count):
                        card.append(i)
                    continue
                if len(rects) == 3:
                    for k in range(4):
                        card.append(i)
                    continue
            else:
                for rect in rects:
                    length += 1
                    card.append(
                        {
                            "card_id": i,
                            "rect": rect
                        })

        return card, length

    @pyqtSlot()
    def start_game(self):
        self.capture_timer.start()

    def find_game(self):
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
                if caputure_img.size == 0:
                    OperateWidget.instance().show_log("识别失败")
                    continue
                user_name = None
                for user in res["users"]:
                    user_img = cv.imread(user["user_image"], 0)
                    user_rects = self.detect_image(caputure_img, user_img)
                    if len(user_rects) > 0:
                        user_name = user["name"]
                        break
                if user_name is None:
                    # 截取用户图片
                    user_img_rect = res["game"]["user_name_start_area"]
                    user_img_array = self.get_img_rect(caputure_img,
                                                       QRect(user_img_rect[0], user_img_rect[1], user_img_rect[2],
                                                             user_img_rect[3]))
                    user_img = qimage2ndarray.array2qimage(user_img_array)

                    # 弹出窗口，让用户设置该图片的用户名
                    user_name_setting = UserNameSetting(OperateWidget.instance())
                    user_name_setting.setModal(True)
                    user_name_setting.set_img(user_img)
                    if user_name_setting.exec() == QDialog.Accepted:
                        user_name = user_name_setting.get_name()
                        # 设置完之后，保存到json
                        res["users"].append({
                            "name": user_name,
                            "user_image": "./res/users_image/{}.jpg".format(user_name)
                        })
                        cv.imwrite("./res/users_image/{}.jpg".format(user_name), user_img_array)
                        config.instance().save_res(res)
                    else:
                        continue
                OperateWidget.instance().show_log("找到用户{}".format(user_name))
                caputure_w.set_user_name(user_name)
                count = count + 1
        else:
            OperateWidget.instance().show_log("识别窗口失败，没有找到目标窗口，"
                                              "请确认游戏窗口是否启动，并停留在开始界面")

    @pyqtSlot()
    def start_recognize(self):
        # 排序所有游戏窗口
        OperateWidget.instance().show_log("排序窗口")
        self.sort_window()
        OperateWidget.instance().show_log("排序窗口完成，开始识别窗口")
        self.find_game_timer.singleShot(300, self.find_game)

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
