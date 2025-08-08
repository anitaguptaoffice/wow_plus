import time

class AutomationLoop:
    def __init__(self, yolo_detector, keystroke_sender, strategy_manager, mode_manager, log_queue, yolo_data_queue, command_queue, debug_mode, stop_event, screen_region):
        self.yolo_detector = yolo_detector
        self.keystroke_sender = keystroke_sender
        self.strategy_manager = strategy_manager
        self.mode_manager = mode_manager
        self.log_queue = log_queue
        self.yolo_data_queue = yolo_data_queue
        self.command_queue = command_queue
        self.debug_mode = debug_mode
        self._stop_event = stop_event
        self.screen_region = screen_region

    def run(self):
        while not self._stop_event.is_set():
            if self.mode_manager.current_mode == self.mode_manager.MODE_STOP or not self.strategy_manager.current_strategy:
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
                            time.sleep(self.strategy_manager.global_cooldown)
                        else:
                            self.log("[调试] 指令: 跳过")
                            time.sleep(0.1)
                    else:
                        self.log(f"模式: {self.mode_manager.current_mode.upper()} | 施放: {spell_to_cast}")
                        self.keystroke_sender.send_key(spell_keybind)
                        time.sleep(self.strategy_manager.global_cooldown)
                else:
                    time.sleep(0.1)

            except Exception as e:
                self.log(f"引擎主循环发生错误: {e}")
                time.sleep(1)

    def _find_spell_to_cast(self, ready_skills):
        if self.mode_manager.current_mode not in [self.mode_manager.MODE_AOE, self.mode_manager.MODE_SINGLE]:
            return None, None

        priority_map = {
            self.mode_manager.MODE_AOE: 'aoe_priority',
            self.mode_manager.MODE_SINGLE: 'single_target_priority'
        }
        priority_list = self.strategy_manager.current_strategy.get(priority_map[self.mode_manager.current_mode], [])

        for spell in priority_list:
            spell_name = spell['name']
            if spell_name in ready_skills:
                bindings = self.strategy_manager.current_strategy.get('bindings', {})
                keybind = bindings.get(spell['key'], spell['key'])
                return spell_name, keybind
        return None, None

    def log(self, message):
        self.log_queue.put(message)
