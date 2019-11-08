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
            f = open("./res/resource.json", "r")

            self.res_config = json.load(f)
            f.close()
        return self.res_config
