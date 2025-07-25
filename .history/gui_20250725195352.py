

import customtkinter as ctk
import yaml
import queue
from tkinter import messagebox
from src.automation_engine import AutomationEngine

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("《魔兽世界》技能自动化助手 (YOLO版)")
        self.geometry("1000x600")

        self.config_path = 'config.yaml'
        self.automation_thread = None
        self.log_queue = queue.Queue()
        self.strategy_widgets = {}

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
        self.load_strategy_from_config()
        self.process_log_queue()

    def setup_ui(self):
        # 左侧: 策略编辑器
        self.left_frame.grid_rowconfigure(1, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.left_frame, text="策略编辑器", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.tab_view = ctk.CTkTabview(self.left_frame)
        self.tab_view.grid(row=1, column=0, padx=10, pady=0, sticky="nsew")
        
        button_frame = ctk.CTkFrame(self.left_frame)
        button_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(button_frame, text="保存策略", command=self.save_strategy_to_config).pack(side="left")
        ctk.CTkButton(button_frame, text="重新加载", command=self.load_strategy_from_config).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="添加技能", command=self.add_skill_to_current_tab).pack(side="left")

        # 右侧: 状态与日志
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.right_frame, text="状态与日志", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.log_textbox = ctk.CTkTextbox(self.right_frame, state="disabled", wrap="word")
        self.log_textbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # 底部: 控制按钮
        self.start_button = ctk.CTkButton(self.control_frame, text="启动引擎", command=self.start_automation)
        self.start_button.pack(side="left", padx=10, pady=5)
        self.stop_button = ctk.CTkButton(self.control_frame, text="停止引擎", state="disabled", command=self.stop_automation)
        self.stop_button.pack(side="left", padx=10, pady=5)

    def load_strategy_from_config(self):
        for tab_name in self.strategy_widgets:
            for widget in self.strategy_widgets[tab_name]['skills']:
                widget['frame'].destroy()
        self.strategy_widgets = {}
        
        for tab in self.tab_view.winfo_children(): tab.destroy()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f: self.config = yaml.safe_load(f)
            profile = self.config.get('profiles', {}).get('Frostfire Mage - Main', {})
            
            for mode in ['aoe_priority', 'single_target_priority']:
                tab = self.tab_view.add(mode.replace('_priority', ''))
                frame = ctk.CTkScrollableFrame(tab, label_text=f"{mode.replace('_priority', '').upper()} 优先级")
                frame.pack(fill="both", expand=True, padx=5, pady=5)
                self.strategy_widgets[mode] = {'frame': frame, 'skills': []}
                for spell in profile.get(mode, []):
                    self.add_skill_widget(mode, frame, spell)
            self.log("策略已从 config.yaml 加载。")
        except Exception as e:
            messagebox.showerror("错误", f"加载配置文件失败: {e}")

    def add_skill_widget(self, mode, parent, data):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(frame, text="名称:").pack(side="left", padx=5)
        name_entry = ctk.CTkEntry(frame, placeholder_text="技能名 (如 frostbolt)")
        name_entry.insert(0, data.get('name', ''))
        name_entry.pack(side="left", padx=5, expand=True, fill="x")
        ctk.CTkLabel(frame, text="按键:").pack(side="left", padx=5)
        key_entry = ctk.CTkEntry(frame, width=80)
        key_entry.insert(0, data.get('keybind', ''))
        key_entry.pack(side="left", padx=5)
        ctk.CTkButton(frame, text="删除", width=50, command=lambda f=frame: f.destroy()).pack(side="right", padx=5)
        self.strategy_widgets[mode]['skills'].append({'frame': frame, 'name': name_entry, 'keybind': key_entry})

    def add_skill_to_current_tab(self):
        tab_name = self.tab_view.get() + "_priority"
        if tab_name in self.strategy_widgets:
            self.add_skill_widget(tab_name, self.strategy_widgets[tab_name]['frame'], {})

    def save_strategy_to_config(self):
        try:
            for mode, widgets in self.strategy_widgets.items():
                new_priority = []
                for skill_frame in widgets['frame'].winfo_children():
                    if isinstance(skill_frame, ctk.CTkFrame):
                        name = [w for w in skill_frame.winfo_children() if isinstance(w, ctk.CTkEntry)][0].get()
                        keybind = [w for w in skill_frame.winfo_children() if isinstance(w, ctk.CTkEntry)][1].get()
                        if name: new_priority.append({'name': name, 'keybind': keybind})
                self.config['profiles']['Frostfire Mage - Main'][mode] = new_priority
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, sort_keys=False)
            messagebox.showinfo("成功", "策略已成功保存！")
            self.load_strategy_from_config()
        except Exception as e:
            messagebox.showerror("错误", f"保存配置文件失败: {e}")

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
