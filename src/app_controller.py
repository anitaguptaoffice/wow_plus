from multiprocessing import Queue
from src.engine.automation_engine import AutomationEngine

class AppController:
    def __init__(self, config_path):
        self.config_path = config_path
        self.log_queue = Queue()
        self.yolo_data_queue = Queue()
        self.command_queue = Queue()
        self.automation_process = None

    def start_engine(self, debug_mode):
        if self.automation_process and self.automation_process.is_alive():
            self.log("自动化引擎已在运行。")
            return

        self.log("正在启动自动化引擎...")
        self.automation_process = AutomationEngine(
            self.config_path,
            self.log_queue,
            self.yolo_data_queue,
            self.command_queue,
            debug_mode
        )
        self.automation_process.start()
        return True

    def stop_engine(self):
        if self.automation_process and self.automation_process.is_alive():
            self.log("正在停止自动化引擎...")
            self.automation_process.terminate()
            self.automation_process.join()
            self.automation_process = None
            self.log("自动化引擎已停止。")
        else:
            self.log("自动化引擎未运行。")

    def log(self, message):
        self.log_queue.put(message)

    def get_log_queue(self):
        return self.log_queue

    def get_yolo_data_queue(self):
        return self.yolo_data_queue

    def get_command_queue(self):
        return self.command_queue
