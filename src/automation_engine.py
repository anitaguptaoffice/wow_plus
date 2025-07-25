import time
import yaml
import os
from multiprocessing import Process, Event
from pynput import keyboard

from src.keybinder import get_keystroke_sender
from src.yolo_detector import YoloDetector

class AutomationEngine(Process):
    # ... (The rest of the class remains largely the same, only the base class changes)
    # 模式常量
    MODE_AOE = "aoe"
    MODE_SINGLE = "single_target"
    MODE_STOP = None

    def __init__(self, config_path, log_queue, yolo_data_queue, command_queue, debug_mode):
        super().__init__()
        self.config_path = config_path
        self.log_queue = log_queue
        self.yolo_data_queue = yolo_data_queue
        self.command_queue = command_queue
        self.debug_mode = debug_mode
        self._stop_event = Event()

    def run(self):
        # Config loading and component initialization must be inside the new process
        self.config = self._load_config()
        self.yolo_detector = YoloDetector(self.config.get('yolo_model_path'))
        self.keystroke_sender = get_keystroke_sender(self.config)
        self.screen_region = self.config.get('screen_capture_region')
        self.current_strategy = {}
        self.global_cooldown = 1.5
        self._load_initial_strategy()
        self.current_mode = self.MODE_STOP
        self.listener = None
        self.mode_switch_keys = self.config.get('mode_switch_keys', {})

        self.log("自动化引擎已启动")
        self.start_listener()

        while not self._stop_event.is_set():
            if self.current_mode == self.MODE_STOP or not self.current_strategy:
                time.sleep(0.1)
                continue

            try:
                detected_objects = self.yolo_detector.detect_skills(self.screen_region)
                ready_skills = {obj['name'].replace('_ready', '') for obj in detected_objects if obj['name'].endswith('_ready')}
                all_detected_labels = [obj['name'] for obj in detected_objects]
                self.yolo_data_queue.put(all_detected_labels)

                if not ready_skills:
                    time.sleep(0.1)
                    continue

                spell_to_cast, spell_keybind = self._find_spell_to_cast(ready_skills)

                if spell_to_cast and spell_keybind:
                    if self.debug_mode:
                        self.log(f"[调试] 暂停，准备施放: {spell_to_cast} (按键: {spell_keybind})")
                        self.log_queue.put({"type": "debug_step", "spell": spell_to_cast, "keybind": spell_keybind})
                        
                        command = self.command_queue.get()
                        if command == 'execute':
                            self.log("[调试] 指令: 执行")
                            self.keystroke_sender.send_key(spell_keybind)
                            time.sleep(self.global_cooldown)
                        else:
                            self.log("[调试] 指令: 跳过")
                            time.sleep(0.1)
                    else:
                        self.log(f"模式: {self.current_mode.upper()} | 施放: {spell_to_cast}")
                        self.keystroke_sender.send_key(spell_keybind)
                        time.sleep(self.global_cooldown)
                else:
                    time.sleep(0.1)

            except Exception as e:
                self.log(f"引擎主循环发生错误: {e}")
                time.sleep(1)

        self.log("自动化引擎已停止")
        self.stop_listener()

    def _load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.log(f"错误: 配置文件 {self.config_path} 未找到。")
            return {}
        except Exception as e:
            self.log(f"加载配置文件失败: {e}")
            return {}

    def _load_initial_strategy(self):
        strategy_path = self.config.get('current_strategy')
        if not strategy_path or not os.path.exists(strategy_path):
            self.log(f"警告: 未在 config.yaml 中找到有效策略路径，或文件不存在。")
            self.log("请在UI中加载一个策略。")
            return
        self.load_strategy(strategy_path)

    def load_strategy(self, strategy_path):
        try:
            with open(strategy_path, 'r', encoding='utf-8') as f:
                self.current_strategy = yaml.safe_load(f)
            self.log(f"已加载策略: {self.current_strategy.get('name', os.path.basename(strategy_path))}")
            self.global_cooldown = self.current_strategy.get('global_cooldown', 1.5)
            self.log(f"全局冷却时间设置为: {self.global_cooldown}秒")
            return True
        except Exception as e:
            self.log(f"加载策略 '{strategy_path}' 失败: {e}")
            self.current_strategy = {}
            return False

    def log(self, message):
        self.log_queue.put(message)

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

    def _get_ready_skills(self):
        detected_objects = self.yolo_detector.detect_skills(self.screen_region)
        return {obj['name'].replace('_ready', '') for obj in detected_objects if obj['name'].endswith('_ready')}

    def _find_spell_to_cast(self, ready_skills):
        if self.current_mode not in [self.MODE_AOE, self.MODE_SINGLE]:
            return None, None

        priority_map = {
            self.MODE_AOE: 'aoe_priority',
            self.MODE_SINGLE: 'single_target_priority'
        }
        priority_list = self.current_strategy.get(priority_map[self.current_mode], [])

        for spell in priority_list:
            spell_name = spell['name']
            if spell_name in ready_skills:
                bindings = self.current_strategy.get('bindings', {})
                keybind = bindings.get(spell['key'], spell['key'])
                return spell_name, keybind
        return None, None

    def stop(self):
        self._stop_event.set()
