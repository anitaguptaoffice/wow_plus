from multiprocessing import Process, Event

from src.implementations.pynput_sender import get_keystroke_sender
from src.implementations.yolo_detector import YoloDetector
from src.engine.strategy_manager import StrategyManager
from src.engine.mode_manager import ModeManager
from src.engine.automation_loop import AutomationLoop
from src.utils.config_manager import ConfigManager

class AutomationEngine(Process):
    def __init__(self, config_path, log_queue, yolo_data_queue, command_queue, debug_mode):
        super().__init__()
        # config_path is no longer used here, but kept for compatibility with AppController for now
        self.log_queue = log_queue
        self.yolo_data_queue = yolo_data_queue
        self.command_queue = command_queue
        self.debug_mode = debug_mode
        self._stop_event = Event()

    def run(self):
        self.log("自动化引擎正在启动...")

        config_manager = ConfigManager()
        config = config_manager.get_config()

        if not config:
            self.log("错误: 无法加载配置，引擎将停止。")
            return

        # Initialize components
        yolo_detector = YoloDetector(config.get('yolo_model_path'))
        keystroke_sender = get_keystroke_sender(config)
        strategy_manager = StrategyManager(self.log_queue)
        mode_manager = ModeManager(self.log_queue)

        screen_region = config.get('screen_capture_region')

        automation_loop = AutomationLoop(
            yolo_detector=yolo_detector,
            keystroke_sender=keystroke_sender,
            strategy_manager=strategy_manager,
            mode_manager=mode_manager,
            log_queue=self.log_queue,
            yolo_data_queue=self.yolo_data_queue,
            command_queue=self.command_queue,
            debug_mode=self.debug_mode,
            stop_event=self._stop_event,
            screen_region=screen_region
        )

        self.log("自动化引擎已启动")
        automation_loop.run()

        self.log("自动化引擎正在停止...")
        mode_manager.stop_listener()
        self.log("自动化引擎已停止")

    def log(self, message):
        self.log_queue.put(message)

    def stop(self):
        self._stop_event.set()
