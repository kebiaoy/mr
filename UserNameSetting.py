from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class UserNameSetting(QDialog):
    def __init__(self, parent):
        super(UserNameSetting, self).__init__(parent)
        vbox = QVBoxLayout()
        labelWaining = QLabel()
        labelWaining.setText("不识别的用户，请确认用户名字")
        self.labelImg = QLabel()
        self.nameEdit = QLineEdit()
        vbox.addWidget(labelWaining)
        vbox.addWidget(self.labelImg)
        vbox.addWidget(self.nameEdit)

        btnConfirm = QPushButton()
        btnConfirm.clicked.connect(self.accept)
        btnConfirm.setText("确认")
        vbox.addWidget(btnConfirm)
        self.setLayout(vbox)

    def set_img(self, img):
        self.labelImg.resize(img.size())
        self.labelImg.setPixmap(QPixmap.fromImage(img))

    def get_name(self):
        return self.nameEdit.text()
