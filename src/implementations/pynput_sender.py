import time
from pynput.keyboard import Controller, Key
from src.interfaces.keystroke_sender import AbstractKeystrokeSender

class PynputSender(AbstractKeystrokeSender):
    """使用 pynput 实现的按键模拟器"""

    def initialize(self):
        self.keyboard = Controller()
        self.keypress_delay = self.config.get("keypress_delay_ms", 50) / 1000.0

    def send_key(self, key_string):
        """模拟施法按键"""
        print(f"Casting spell with keybind: {key_string}")
        self.keyboard.press(key_string)
        time.sleep(self.keypress_delay)
        self.keyboard.release(key_string)

    def press_key(self, key_string):
        self.keyboard.press(key_string)

    def release_key(self, key_string):
        self.keyboard.release(key_string)

def get_keystroke_sender(config):
    """根据配置获取按键模拟器实例"""
    sender_type = config.get('keystroke_sender', {}).get('type', 'pynput')
    if sender_type == 'pynput':
        return PynputSender(config.get('keystroke_sender', {}))
    else:
        raise ValueError(f"Unsupported keystroke sender type: {sender_type}")