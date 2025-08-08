from pynput import keyboard
from src.utils.config_manager import ConfigManager

class ModeManager:
    MODE_AOE = "aoe"
    MODE_SINGLE = "single_target"
    MODE_STOP = None

    def __init__(self, log_queue):
        self.log_queue = log_queue
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        self.current_mode = self.MODE_STOP
        self.listener = None
        self.mode_switch_keys = self.config.get('mode_switch_keys', {})
        self.start_listener()

    def on_key_press(self, key):
        try:
            key_name = key.name.lower() if hasattr(key, 'name') else str(key).lower().replace("'", "")
        except AttributeError:
            return

        key_to_mode = {v.lower(): k for k, v in self.mode_switch_keys.items()}

        if key_name in key_to_mode:
            mode_action = key_to_mode[key_name]
            if mode_action == 'aoe_mode':
                self.current_mode = self.MODE_AOE
                self.log(f"切换到AOE模式")
            elif mode_action == 'single_target_mode':
                self.current_mode = self.MODE_SINGLE
                self.log(f"切换到单体模式")
            elif mode_action == 'stop_casting':
                self.current_mode = self.MODE_STOP
                self.log("停止自动释放技能")

    def start_listener(self):
        if not self.mode_switch_keys:
            self.log("警告: 未在配置中找到模式切换按键。")
            return
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()
        self.log("键盘监听器已启动")
        for mode, key in self.mode_switch_keys.items():
            self.log(f"按 {key.upper()} 切换到 {mode.replace('_', ' ')}")

    def stop_listener(self):
        if self.listener:
            self.listener.stop()
            self.listener = None

    def log(self, message):
        self.log_queue.put(message)
