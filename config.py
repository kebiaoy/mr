from PyQt5.QtCore import *
import threading
import json


class config(QObject):
    _instance_lock = threading.Lock()

    def __init__(self):
        super(config, self).__init__()
        self.res_config = None

    @classmethod
    def instance(cls):
        with config._instance_lock:
            if not hasattr(config, "_instance"):
                config._instance = config()
        return config._instance

    def get_res(self):
        if self.res_config is None:
            f = open("./res/resource.json", "r", encoding='UTF-8')

            self.res_config = json.load(f)
            f.close()
        return self.res_config

    @pyqtSlot()
    def reload(self):
        f = open("./res/resource.json", "r", encoding='UTF-8')

        self.res_config = json.load(f)
        f.close()

    def save_res(self, res):
        with open("./res/resource.json", 'w', encoding='utf-8') as json_file:
            json.dump(res, json_file, ensure_ascii=False)
        self.res_config = res
