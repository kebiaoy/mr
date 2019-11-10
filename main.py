from OperateWidget import *
import sys
from Recognition import Recognition
from config import config


if __name__ == "__main__":
    app = QApplication(sys.argv)
    OperateWidget.instance().show()
    OperateWidget.instance().start_recognize.connect(Recognition.instance().start_recognize)
    OperateWidget.instance().start_game.connect(Recognition.instance().start_game)
    OperateWidget.instance().start_game.connect(Recognition.instance().start_game)
    OperateWidget.instance().capture.connect(Recognition.instance().on_capture)
    OperateWidget.instance().reload.connect(config.instance().reload)
    app.exec()
