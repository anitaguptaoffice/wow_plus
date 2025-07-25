import os
import queue
from tkinter import messagebox, filedialog

import customtkinter as ctk
import yaml

from src.automation_engine import AutomationEngine


class App(ctk.CTk):
    # 模式常量
    AOE_MODE = "aoe_priority"
    SINGLE_TARGET_MODE = "single_target_priority"
    MODES = [AOE_MODE, SINGLE_TARGET_MODE]

    def __init__(self):
        super().__init__()

        self.title("《魔兽世界》技能自动化助手 (YOLO版)")
        self.geometry("1200x700")

        self.config_path = "config.yaml"
        self.automation_thread = None
        self.log_queue = queue.Queue()
        self.strategy_widgets = {}
        self.current_strategy_path = None
        self.current_strategy = {}

        # 主布局
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 左右框架
        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")

        self.setup_ui()
        self.load_config()
        self.load_strategy_from_config()
        self.process_log_queue()

    def setup_ui(self):
        """初始化主UI布局和各个组件"""
        self._setup_strategy_editor()
        self._setup_log_viewer()
        self._setup_controls()

    def _setup_strategy_editor(self):
        """设置左侧的策略编辑器UI"""
        self.left_frame.grid_rowconfigure(2, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        # 策略选择区域
        strategy_select_frame = ctk.CTkFrame(self.left_frame)
        strategy_select_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        strategy_select_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(strategy_select_frame, text="当前策略:").pack(side="left", padx=5)
        self.strategy_path_entry = ctk.CTkEntry(strategy_select_frame)
        self.strategy_path_entry.pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkButton(strategy_select_frame, text="浏览", width=60, command=self.browse_strategy).pack(side="left", padx=5)
        ctk.CTkButton(strategy_select_frame, text="加载", width=60, command=self.load_strategy_from_path).pack(side="left", padx=5)

        ctk.CTkLabel(self.left_frame, text="策略编辑器", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=1, column=0, padx=10, pady=(0, 10), sticky="w"
        )

        self.tab_view = ctk.CTkTabview(self.left_frame)
        self.tab_view.grid(row=2, column=0, padx=10, pady=0, sticky="nsew")

        button_frame = ctk.CTkFrame(self.left_frame)
        button_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(button_frame, text="保存策略", command=self.save_strategy_to_config).pack(side="left")
        ctk.CTkButton(button_frame, text="重新加载", command=self.load_strategy_from_config).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="添加技能", command=self.add_skill_to_current_tab).pack(side="left")
        ctk.CTkButton(button_frame, text="新建策略", command=self.create_new_strategy).pack(side="left", padx=10)

    def _setup_log_viewer(self):
        """设置右侧的状态与日志查看器UI"""
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.right_frame, text="状态与日志", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )
        self.log_textbox = ctk.CTkTextbox(self.right_frame, state="disabled", wrap="word")
        self.log_textbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    def _setup_controls(self):
        """设置底部的控制按钮UI"""
        self.start_button = ctk.CTkButton(self.control_frame, text="启动引擎", command=self.start_automation)
        self.start_button.pack(side="left", padx=10, pady=5)
        self.stop_button = ctk.CTkButton(
            self.control_frame, text="停止引擎", state="disabled", command=self.stop_automation
        )
        self.stop_button.pack(side="left", padx=10, pady=5)

        self.mode_info_label = ctk.CTkLabel(self.control_frame, text="使用说明: 启动引擎后，按 F1 进入AOE模式，按 F2 进入单体模式，按 F3 停止技能释放")
        self.mode_info_label.pack(side="left", padx=10, pady=5)

    def load_config(self):
        """加载主配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            messagebox.showerror("错误", f"加载配置文件失败: {e}")
            self.config = {}

    def browse_strategy(self):
        """浏览策略文件"""
        file_path = filedialog.askopenfilename(
            title="选择策略文件",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")],
            initialdir="strategies"
        )
        if file_path:
            self.strategy_path_entry.delete(0, "end")
            self.strategy_path_entry.insert(0, file_path)

    def load_strategy_from_path(self):
        """从路径加载策略"""
        strategy_path = self.strategy_path_entry.get()
        if strategy_path and os.path.exists(strategy_path):
            self.load_strategy_file(strategy_path)
        else:
            messagebox.showerror("错误", "策略文件不存在")

    def load_strategy_from_config(self):
        """从配置文件加载当前策略"""
        strategy_path = self.config.get("current_strategy", "strategies/frostfire_mage.yaml")
        self.strategy_path_entry.delete(0, "end")
        self.strategy_path_entry.insert(0, strategy_path)
        self.load_strategy_file(strategy_path)

    def load_strategy_file(self, strategy_path):
        """加载并显示策略文件"""
        self._clear_strategy_view()
        try:
            with open(strategy_path, "r", encoding="utf-8") as f:
                self.current_strategy = yaml.safe_load(f)
            self.current_strategy_path = strategy_path

            self.update_strategy_info()
            self._build_strategy_tabs()

            for mode in self.MODES:
                for spell in self.current_strategy.get(mode, []):
                    self.add_skill_widget(mode, self.strategy_widgets[mode]["frame"], spell)
            self.log(f"策略已从 {strategy_path} 加载。")
        except Exception as e:
            messagebox.showerror("错误", f"加载策略文件失败: {e}")
            self.current_strategy = {}

    def _clear_strategy_view(self):
        """清除当前的策略UI"""
        for tab_name in self.strategy_widgets:
            if "skills" in self.strategy_widgets[tab_name]:
                for widget in self.strategy_widgets[tab_name]["skills"]:
                    widget["frame"].destroy()
        self.strategy_widgets = {}
        for tab in self.tab_view.winfo_children():
            tab.destroy()

    def _build_strategy_tabs(self):
        """根据MODES常量创建标签页"""
        for mode in self.MODES:
            tab_title = mode.replace("_priority", "")
            tab = self.tab_view.add(tab_title)
            frame = ctk.CTkScrollableFrame(tab, label_text=f"{tab_title.upper()} 优先级")
            frame.pack(fill="both", expand=True, padx=5, pady=5)
            self.strategy_widgets[mode] = {"frame": frame, "skills": []}

    def update_strategy_info(self):
        """更新策略基本信息显示"""
        mode_keys = self.config.get("mode_switch_keys", {
            'aoe_mode': 'f1',
            'single_target_mode': 'f2',
            'stop_casting': 'f3'
        })
        self.mode_info_label.configure(
            text=f"使用说明: 启动引擎后，按 {mode_keys['aoe_mode'].upper()} 进入AOE模式，"
                 f"按 {mode_keys['single_target_mode'].upper()} 进入单体模式，"
                 f"按 {mode_keys['stop_casting'].upper()} 停止技能释放"
        )

    def update_strategy_from_widgets(self):
        """从UI控件收集数据并更新self.current_strategy"""
        if not self.current_strategy:
            return

        for mode, widgets_info in self.strategy_widgets.items():
            new_priority = []
            for skill_widget_group in widgets_info["skills"]:
                # 检查框架是否已被销毁
                if not skill_widget_group["frame"].winfo_exists():
                    continue
                
                name = skill_widget_group["name_entry"].get()
                key = skill_widget_group["key_entry"].get()
                if name and key:
                    new_priority.append({"name": name, "key": key})
            self.current_strategy[mode] = new_priority

    def add_skill_widget(self, mode, parent, data):
        """向指定的模式选项卡添加一个技能的UI控件组"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=5, padx=5)

        ctk.CTkLabel(frame, text="名称:").pack(side="left", padx=5)
        name_entry = ctk.CTkEntry(frame, placeholder_text="技能名 (如 frostbolt)")
        name_entry.insert(0, data.get("name", ""))
        name_entry.pack(side="left", padx=5, expand=True, fill="x")

        ctk.CTkLabel(frame, text="按键:").pack(side="left", padx=5)
        key_entry = ctk.CTkEntry(frame, width=80)
        key_entry.insert(0, data.get("key", ""))
        key_entry.pack(side="left", padx=5)

        # 创建一个弱引用给删除命令，避免循环引用
        skill_widget_group = {}
        remove_command = lambda f=frame, swg=skill_widget_group: self.remove_skill_widget(f, swg)
        
        ctk.CTkButton(frame, text="删除", width=50, command=remove_command).pack(side="right", padx=5)

        skill_widget_group.update({
            "frame": frame,
            "name_entry": name_entry,
            "key_entry": key_entry
        })
        self.strategy_widgets[mode]["skills"].append(skill_widget_group)

    def remove_skill_widget(self, frame, skill_widget_group):
        """销毁技能框架并从列表中移除"""
        frame.destroy()
        # 遍历所有模式，找到并移除对应的技能字典
        for mode in self.strategy_widgets:
            if skill_widget_group in self.strategy_widgets[mode]["skills"]:
                self.strategy_widgets[mode]["skills"].remove(skill_widget_group)
                break

    def add_skill_to_current_tab(self):
        """在当前选中的标签页添加一个新技能"""
        current_tab_title = self.tab_view.get()
        mode = f"{current_tab_title}_priority"
        if mode in self.strategy_widgets:
            self.add_skill_widget(mode, self.strategy_widgets[mode]["frame"], {})

    def create_new_strategy(self):
        """创建并显示一个新的空策略"""
        self._clear_strategy_view()

        self.current_strategy = {
            "name": "New Strategy",
            "class": "未指定",
            "spec": "未指定",
            "description": "新策略描述",
            "bindings": {},
            self.AOE_MODE: [],
            self.SINGLE_TARGET_MODE: []
        }
        self.current_strategy_path = None
        self.strategy_path_entry.delete(0, "end")

        self._build_strategy_tabs()
        self.log("已创建新的空策略。请在保存时指定文件名。")


    def save_strategy_to_config(self):
        """保存策略到文件"""
        try:
            if not self.current_strategy:
                messagebox.showerror("错误", "没有可保存的策略")
                return

            # 从UI更新策略数据
            self.update_strategy_from_widgets()

            # 确定保存路径
            if self.current_strategy_path:
                save_path = self.current_strategy_path
            else:
                save_path = filedialog.asksaveasfilename(
                    title="保存策略文件",
                    defaultextension=".yaml",
                    filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")],
                    initialdir="strategies"
                )
                if not save_path:
                    return  # 用户取消了保存
                    
            # 保存策略文件
            with open(save_path, "w", encoding="utf-8") as f:
                yaml.dump(self.current_strategy, f, allow_unicode=True, sort_keys=False)
            
            # 更新配置文件中的当前策略路径
            self.config["current_strategy"] = save_path
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, allow_unicode=True, sort_keys=False)
            
            self.current_strategy_path = save_path
            self.strategy_path_entry.delete(0, "end")
            self.strategy_path_entry.insert(0, save_path)
            
            messagebox.showinfo("成功", f"策略已成功保存到: {save_path}")
            self.log(f"策略已保存到: {save_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存策略文件失败: {e}")

    def start_automation(self):
        self.log("正在启动自动化引擎...")
        self.automation_thread = AutomationEngine(self.config_path, self.log_queue)
        self.automation_thread.start()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

    def stop_automation(self):
        if self.automation_thread and self.automation_thread.is_alive():
            self.log("正在停止自动化引擎...")
            self.automation_thread.stop()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def log(self, message):
        self.log_queue.put(message)

    def process_log_queue(self):
        try:
            while not self.log_queue.empty():
                self.log_textbox.configure(state="normal")
                self.log_textbox.insert("end", self.log_queue.get_nowait() + "\n")
                self.log_textbox.configure(state="disabled")
                self.log_textbox.see("end")
        finally:
            self.after(100, self.process_log_queue)

    def on_closing(self):
        if messagebox.askokcancel("退出", "您确定要退出吗？"):
            self.stop_automation()
            self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()