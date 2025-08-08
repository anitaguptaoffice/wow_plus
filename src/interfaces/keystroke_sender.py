
from abc import ABC, abstractmethod

class AbstractKeystrokeSender(ABC):
    """按键模拟器的抽象基类"""

    def __init__(self, config=None):
        self.config = config or {}
        self.initialize()

    @abstractmethod
    def initialize(self):
        """执行特定发送器所需的任何初始化步骤。"""
        pass

    @abstractmethod
    def send_key(self, key_string):
        """发送单个按键或组合键。"""
        pass

    @abstractmethod
    def press_key(self, key_string):
        """模拟按下按键（不释放）。"""
        pass

    @abstractmethod
    def release_key(self, key_string):
        """模拟释放按键。"""
        pass

    def cleanup(self):
        """执行特定发送器所需的任何清理步骤（可选）。"""
        pass
