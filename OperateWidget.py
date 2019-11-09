from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import threading


class OperateWidget(QWidget):
    _instance_lock = threading.Lock()
    start_recognize = pyqtSignal()
    start_game = pyqtSignal()

    def __init__(self):
        super(OperateWidget, self).__init__()
        vbox = QVBoxLayout()
        btn = QPushButton()
        btn.setText("启动识别")
        btn.clicked.connect(self.start_recognize)
        self.use_res_collection = QCheckBox()
        self.use_res_collection.setText("启用资源收集")
        self.use_res_collection.setChecked(False)
        hbox = QHBoxLayout()
        btn_star = QPushButton()
        btn_star.setText("开始游戏")
        btn_star.clicked.connect(self.start_game)
        hbox.addWidget(btn_star)
        hbox.addWidget(self.use_res_collection)
        self.text_edit = QTextEdit()
        vbox.addWidget(btn)
        vbox.addLayout(hbox)
        vbox.addWidget(self.text_edit)
        self.setLayout(vbox)

    @classmethod
    def instance(cls):
        with OperateWidget._instance_lock:
            if not hasattr(OperateWidget, "_instance"):
                OperateWidget._instance = OperateWidget()
        return OperateWidget._instance

    def sizeHint(self):
        return QSize(600, 800)

    def use_collection(self):
        return self.use_res_collection.isChecked()

    def show_log(self, str_log):
        datatime = QDateTime.currentDateTime()
        str_log = datatime.toString("yyyy-MM-dd hh:mm:ss") + " " + str_log + "\n"
        self.text_edit.append(str_log)
        log_file = QFile("./log/mr.log")
        if log_file.exists() is False:
            dir = QDir()
            dir.mkpath("./log")
        if log_file.open(QIODevice.Append):
            out_s = QTextStream(log_file)
            out_s << str_log
            log_file.close()
