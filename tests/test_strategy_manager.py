import unittest
from unittest.mock import patch, MagicMock
from multiprocessing import Queue

# It's better to add src to python path than using relative imports in tests
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine.strategy_manager import StrategyManager
from src.utils.config_manager import ConfigManager

class TestStrategyManager(unittest.TestCase):

    def setUp(self):
        self.log_queue = Queue()

    @patch('src.engine.strategy_manager.ConfigManager')
    def test_load_valid_strategy(self, MockConfigManager):
        """测试StrategyManager是否能成功加载一个有效的策略文件。"""
        # 准备一个虚拟的配置文件内容
        mock_config = {
            'current_strategy': 'strategies/test_strategy.yaml'
        }

        # 配置Mock ConfigManager实例
        mock_config_instance = MockConfigManager.return_value
        mock_config_instance.get_config.return_value = mock_config
        mock_config_instance.get.side_effect = mock_config.get

        # 创建StrategyManager实例
        strategy_manager = StrategyManager(self.log_queue)

        # 断言
        self.assertIsNotNone(strategy_manager.current_strategy, "当前策略不应为空")
        self.assertEqual(strategy_manager.current_strategy['name'], "Test Strategy", "策略名称不匹配")
        self.assertEqual(strategy_manager.global_cooldown, 1.2, "全局冷却时间不匹配")
        self.assertTrue(self.log_queue.qsize() > 0, "应有日志消息")

        # 验证日志消息
        log_message = self.log_queue.get()
        self.assertIn("已加载策略: Test Strategy", log_message)
        log_message = self.log_queue.get()
        self.assertIn("全局冷却时间设置为: 1.2秒", log_message)

    @patch('src.engine.strategy_manager.ConfigManager')
    def test_load_nonexistent_strategy(self, MockConfigManager):
        """测试当策略文件不存在时，StrategyManager的行为。"""
        mock_config = {
            'current_strategy': 'strategies/nonexistent_strategy.yaml'
        }
        mock_config_instance = MockConfigManager.return_value
        mock_config_instance.get_config.return_value = mock_config
        mock_config_instance.get.side_effect = mock_config.get

        strategy_manager = StrategyManager(self.log_queue)

        self.assertEqual(strategy_manager.current_strategy, {}, "当前策略应为空字典")
        self.assertEqual(strategy_manager.global_cooldown, 1.5, "全局冷却时间应为默认值")

        # 验证警告日志
        log_message = self.log_queue.get()
        self.assertIn("警告: 未在 config.yaml 中找到有效策略路径", log_message)

if __name__ == '__main__':
    unittest.main()
