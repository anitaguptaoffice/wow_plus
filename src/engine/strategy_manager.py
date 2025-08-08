import yaml
import os
from src.utils.config_manager import ConfigManager

class StrategyManager:
    def __init__(self, log_queue):
        self.log_queue = log_queue
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        self.current_strategy = {}
        self.global_cooldown = 1.5
        self._load_initial_strategy()

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
