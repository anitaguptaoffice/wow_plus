import unittest
from unittest.mock import patch, MagicMock
from multiprocessing import Queue

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine.mode_manager import ModeManager
from pynput.keyboard import Key

class TestModeManager(unittest.TestCase):

    def setUp(self):
        self.log_queue = Queue()
        # Mock the put method directly on the queue instance for each test
        self.log_queue.put = MagicMock()

        mock_config = {
            'mode_switch_keys': {
                'aoe_mode': 'f1',
                'single_target_mode': 'f2',
                'stop_casting': 'f3'
            }
        }

        # We patch ConfigManager to control the config used by ModeManager
        self.config_patcher = patch('src.engine.mode_manager.ConfigManager')
        self.mock_config_manager = self.config_patcher.start()

        mock_config_instance = self.mock_config_manager.return_value
        mock_config_instance.get_config.return_value = mock_config
        mock_config_instance.get.side_effect = mock_config.get

        # We patch the keyboard listener so it doesn't actually start
        self.listener_patcher = patch('src.engine.mode_manager.keyboard.Listener')
        self.mock_listener = self.listener_patcher.start()

        self.mode_manager = ModeManager(self.log_queue)

    def tearDown(self):
        self.config_patcher.stop()
        self.listener_patcher.stop()

    def test_initial_mode(self):
        """测试初始模式是否为STOP。"""
        self.assertEqual(self.mode_manager.current_mode, ModeManager.MODE_STOP)

    def test_switch_to_aoe(self):
        """测试切换到AOE模式。"""
        mock_key = MagicMock(spec=Key)
        mock_key.name = 'f1'

        self.mode_manager.on_key_press(mock_key)

        self.assertEqual(self.mode_manager.current_mode, ModeManager.MODE_AOE)
        self.log_queue.put.assert_called_with("切换到AOE模式")

    def test_switch_to_single_target(self):
        """测试切换到单体模式。"""
        mock_key = MagicMock(spec=Key)
        mock_key.name = 'f2'

        self.mode_manager.on_key_press(mock_key)

        self.assertEqual(self.mode_manager.current_mode, ModeManager.MODE_SINGLE)
        self.log_queue.put.assert_called_with("切换到单体模式")

    def test_switch_to_stop(self):
        """测试切换到停止模式。"""
        # First, switch to another mode to ensure we are changing state
        self.mode_manager.current_mode = ModeManager.MODE_AOE

        mock_key = MagicMock(spec=Key)
        mock_key.name = 'f3'

        self.mode_manager.on_key_press(mock_key)

        self.assertEqual(self.mode_manager.current_mode, ModeManager.MODE_STOP)
        self.log_queue.put.assert_called_with("停止自动释放技能")

    def test_unassigned_key(self):
        """测试按下未分配的按键时，模式不应改变。"""
        initial_mode = self.mode_manager.current_mode
        initial_log_count = self.log_queue.put.call_count

        mock_key = MagicMock(spec=Key)
        mock_key.name = 'f12' # An unassigned key

        self.mode_manager.on_key_press(mock_key)

        self.assertEqual(self.mode_manager.current_mode, initial_mode)
        self.assertEqual(self.log_queue.put.call_count, initial_log_count)

if __name__ == '__main__':
    unittest.main()
