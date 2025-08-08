# gui.py (PySide6 Version)

import os
import sys

import yaml
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)

from src.app_controller import AppController
from src.utils.config_manager import ConfigManager


class SkillWidget(QFrame):
    """单个技能的UI控件组"""

    def __init__(self, mode, data, parent_widget=None):
        super().__init__()
        self.parent_widget = parent_widget
        self.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(self)

        layout.addWidget(QLabel("名称:"))
        self.name_entry = QLineEdit()
        self.name_entry.setPlaceholderText("技能名 (如 frostbolt)")
        self.name_entry.setText(data.get("name", ""))
        layout.addWidget(self.name_entry)

        layout.addWidget(QLabel("按键:"))
        self.key_entry = QLineEdit()
        self.key_entry.setFixedWidth(80)
        self.key_entry.setText(data.get("key", ""))
        layout.addWidget(self.key_entry)

        delete_button = QPushButton("删除")
        delete_button.setFixedWidth(50)
        delete_button.clicked.connect(self.delete_widget)
        layout.addWidget(delete_button)

    def get_data(self):
        return {"name": self.name_entry.text(), "key": self.key_entry.text()}

    def delete_widget(self):
        if self.parent_widget:
            self.parent_widget.remove_skill_widget(self)
        self.deleteLater()


class StrategyTab(QWidget):
    """单个策略模式的标签页 (AOE/单体)"""

    def __init__(self, mode_name):
        super().__init__()
        self.mode_name = mode_name
        self.skill_widgets = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        self.scroll_content = QWidget()
        self.skills_layout = QVBoxLayout(self.scroll_content)
        self.skills_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(self.scroll_content)

    def add_skill_widget(self, data={}):
        widget = SkillWidget(self.mode_name, data, self)
        self.skills_layout.addWidget(widget)
        self.skill_widgets.append(widget)

    def remove_skill_widget(self, widget):
        if widget in self.skill_widgets:
            self.skill_widgets.remove(widget)

    def load_skills(self, skills_data):
        # Clear existing widgets
        for widget in self.skill_widgets:
            widget.deleteLater()
        self.skill_widgets = []

        for skill_data in skills_data:
            self.add_skill_widget(skill_data)

    def get_skills_data(self):
        return [
            widget.get_data() for widget in self.skill_widgets if widget.name_entry.text() and widget.key_entry.text()
        ]


class App(QMainWindow):
    AOE_MODE = "aoe_priority"
    SINGLE_TARGET_MODE = "single_target_priority"
    MODES = [AOE_MODE, SINGLE_TARGET_MODE]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("《魔兽世界》技能自动化助手 (YOLO版)")
        self.setGeometry(100, 100, 1200, 700)

        self.config_manager = ConfigManager('config.yaml')
        self.controller = AppController(self.config_manager.config_path)
        self.current_strategy_path = None
        self.current_strategy = {}

        self.setup_ui()
        self.load_strategy_from_config()
        self.process_log_queue()
        self.process_yolo_data_queue()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_v_layout = QVBoxLayout(main_widget)

        top_h_layout = QHBoxLayout()

        # --- Left Frame: Strategy Editor ---
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        top_h_layout.addWidget(left_frame, 1)

        # Strategy selection
        strategy_select_layout = QHBoxLayout()
        strategy_select_layout.addWidget(QLabel("当前策略:"))
        self.strategy_path_entry = QLineEdit()
        strategy_select_layout.addWidget(self.strategy_path_entry)
        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(self.browse_strategy)
        strategy_select_layout.addWidget(browse_button)
        load_button = QPushButton("加载")
        load_button.clicked.connect(self.load_strategy_from_path)
        strategy_select_layout.addWidget(load_button)
        left_layout.addLayout(strategy_select_layout)

        # Tabs for modes
        self.tab_widget = QTabWidget()
        self.tabs = {}
        for mode in self.MODES:
            tab_title = mode.replace("_priority", "").capitalize()
            tab = StrategyTab(mode)
            self.tab_widget.addTab(tab, tab_title)
            self.tabs[mode] = tab
        left_layout.addWidget(self.tab_widget)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("保存策略")
        save_button.clicked.connect(self.save_strategy_to_config)
        button_layout.addWidget(save_button)
        reload_button = QPushButton("重新加载")
        reload_button.clicked.connect(self.load_strategy_from_config)
        button_layout.addWidget(reload_button)
        add_skill_button = QPushButton("添加技能")
        add_skill_button.clicked.connect(self.add_skill_to_current_tab)
        button_layout.addWidget(add_skill_button)
        new_strategy_button = QPushButton("新建策略")
        new_strategy_button.clicked.connect(self.create_new_strategy)
        button_layout.addWidget(new_strategy_button)
        left_layout.addLayout(button_layout)

        # --- Right Frame: Status & Logs ---
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        top_h_layout.addWidget(right_frame, 1)

        log_label = QLabel("状态与日志")
        log_label.setFont(QFont("Arial", 16, QFont.Bold))
        right_layout.addWidget(log_label)
        self.log_textbox = QTextEdit()
        self.log_textbox.setReadOnly(True)
        right_layout.addWidget(self.log_textbox)

        # YOLO Real-time Monitor
        yolo_label = QLabel("YOLO 实时识别")
        yolo_label.setFont(QFont("Arial", 16, QFont.Bold))
        right_layout.addWidget(yolo_label)
        self.yolo_textbox = QTextEdit()
        self.yolo_textbox.setReadOnly(True)
        self.yolo_textbox.setFixedHeight(100)
        right_layout.addWidget(self.yolo_textbox)

        main_v_layout.addLayout(top_h_layout)

        # --- Bottom Frame: Controls ---
        bottom_frame = QFrame()
        bottom_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        control_layout = QHBoxLayout(bottom_frame)
        self.start_button = QPushButton("启动引擎")
        self.start_button.clicked.connect(self.start_automation)
        control_layout.addWidget(self.start_button)
        self.stop_button = QPushButton("停止引擎")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_automation)
        control_layout.addWidget(self.stop_button)
        self.debug_checkbox = QCheckBox("调试模式")
        control_layout.addWidget(self.debug_checkbox)
        self.mode_info_label = QLabel("使用说明: ...")
        control_layout.addWidget(self.mode_info_label)
        main_v_layout.addWidget(bottom_frame)

    def browse_strategy(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择策略文件", "strategies", "YAML files (*.yaml *.yml)")
        if file_path:
            self.strategy_path_entry.setText(file_path)

    def load_strategy_from_path(self):
        strategy_path = self.strategy_path_entry.text()
        if strategy_path and os.path.exists(strategy_path):
            self.load_strategy_file(strategy_path)
        else:
            QMessageBox.critical(self, "错误", "策略文件不存在")

    def load_strategy_from_config(self):
        strategy_path = self.config_manager.get("current_strategy", "strategies/frostfire_mage.yaml")
        if strategy_path and os.path.exists(strategy_path):
            self.strategy_path_entry.setText(strategy_path)
            self.load_strategy_file(strategy_path)
        else:
            self.log(f"警告: 默认策略文件 '{strategy_path}' 未找到。")
            QMessageBox.warning(
                self, "未找到策略", f"无法找到默认策略文件: '{strategy_path}'\n\n将为您创建一个新的空策略。"
            )
            self.create_new_strategy()

    def load_strategy_file(self, strategy_path):
        try:
            with open(strategy_path, "r", encoding="utf-8") as f:
                self.current_strategy = yaml.safe_load(f)
            self.current_strategy_path = strategy_path

            self.update_strategy_info()
            for mode, tab in self.tabs.items():
                tab.load_skills(self.current_strategy.get(mode, []))
            self.log(f"策略已从 {strategy_path} 加载。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载策略文件失败: {e}")
            self.current_strategy = {}

    def update_strategy_info(self):
        mode_keys = self.config_manager.get("mode_switch_keys", {})
        aoe_key = mode_keys.get("aoe_mode", "N/A").upper()
        single_key = mode_keys.get("single_target_mode", "N/A").upper()
        stop_key = mode_keys.get("stop_casting", "N/A").upper()
        self.mode_info_label.setText(
            f"使用说明: 按 {aoe_key} 进入AOE模式, 按 {single_key} 进入单体模式, 按 {stop_key} 停止"
        )

    def save_strategy_to_config(self):
        self.update_strategy_from_widgets()
        if not self.current_strategy:
            QMessageBox.critical(self, "错误", "没有可保存的策略")
            return

        save_path = self.current_strategy_path
        if not save_path:
            save_path, _ = QFileDialog.getSaveFileName(self, "保存策略文件", "strategies", "YAML files (*.yaml *.yml)")
            if not save_path:
                return

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                yaml.dump(self.current_strategy, f, allow_unicode=True, sort_keys=False)

            self.config_manager.set("current_strategy", save_path)
            self.config_manager.save()

            self.current_strategy_path = save_path
            self.strategy_path_entry.setText(save_path)
            QMessageBox.information(self, "成功", f"策略已成功保存到: {save_path}")
            self.log(f"策略已保存到: {save_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存策略文件失败: {e}")

    def update_strategy_from_widgets(self):
        for mode, tab in self.tabs.items():
            self.current_strategy[mode] = tab.get_skills_data()

    def add_skill_to_current_tab(self):
        current_tab = self.tab_widget.currentWidget()
        if isinstance(current_tab, StrategyTab):
            current_tab.add_skill_widget()

    def create_new_strategy(self):
        self.current_strategy = {
            "name": "New Strategy",
            "class": "未指定",
            "spec": "未指定",
            "description": "新策略描述",
            "bindings": {},
            self.AOE_MODE: [],
            self.SINGLE_TARGET_MODE: [],
        }
        self.current_strategy_path = None
        self.strategy_path_entry.clear()
        for tab in self.tabs.values():
            tab.load_skills([])
        self.log("已创建新的空策略。请在保存时指定文件名。")

    def start_automation(self):
        debug_mode = self.debug_checkbox.isChecked()
        if self.controller.start_engine(debug_mode):
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.debug_checkbox.setEnabled(False)

    def stop_automation(self):
        self.controller.stop_engine()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.debug_checkbox.setEnabled(True)

    def log(self, message):
        self.controller.log(message)

    def process_log_queue(self):
        log_queue = self.controller.get_log_queue()
        try:
            while not log_queue.empty():
                message = log_queue.get_nowait()
                if isinstance(message, dict) and message.get("type") == "debug_step":
                    self.handle_debug_step(message)
                else:
                    self.log_textbox.append(str(message))
        finally:
            QTimer.singleShot(100, self.process_log_queue)

    def process_yolo_data_queue(self):
        yolo_data_queue = self.controller.get_yolo_data_queue()
        try:
            while not yolo_data_queue.empty():
                labels = yolo_data_queue.get_nowait()
                self.yolo_textbox.setText(", ".join(labels) or "无识别目标")
        finally:
            QTimer.singleShot(100, self.process_yolo_data_queue)

    def handle_debug_step(self, debug_data):
        spell = debug_data.get('spell')
        keybind = debug_data.get('keybind')
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("调试步骤")
        msg_box.setText(f"准备施放技能: {spell} (按键: {keybind})")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.button(QMessageBox.Yes).setText('执行')
        msg_box.button(QMessageBox.No).setText('跳过')
        reply = msg_box.exec()

        command_queue = self.controller.get_command_queue()
        if reply == QMessageBox.Yes:
            command_queue.put('execute')
        else:
            command_queue.put('skip')

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "退出", "您确定要退出吗？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.stop_automation()
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
