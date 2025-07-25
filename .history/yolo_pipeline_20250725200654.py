

import os
import subprocess
import time
from datetime import datetime
from pynput import keyboard
from PIL import ImageGrab

# --- 配置 ---
RAW_DATA_DIR = "raw_yolo_data"         # 存放截图和标签的原始目录
CLASSES_FILE = "yolo_class_names.txt"  # 存放类别名称的文件
SCREENSHOT_HOTKEY = keyboard.Key.f12   # 截图热键

# --- 类别名称定义 ---
# 在这里定义你所有要标注的类别，每个类别占一行。
# 这个列表会自动写入 yolo_class_names.txt 文件。
CLASS_NAMES_LIST = [
    'frostbolt_ready',
    'frostbolt_cooldown',
    'icelance_ready',
    'icelance_cooldown',
    'frozenorb_ready',
    'frozenorb_cooldown',
]

def setup_environment():
    """确保所有必要的目录和文件都存在。"""
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    if not os.path.exists(CLASSES_FILE):
        print(f"正在创建类别文件: {CLASSES_FILE}")
        with open(CLASSES_FILE, 'w') as f:
            for name in CLASS_NAMES_LIST:
                f.write(name + '\n')

def screenshot_mode():
    """启动截图模式，通过热键保存屏幕截图。"""
    print("--- 已进入截图模式 ---")
    print(f"按下 [{SCREENSHOT_HOTKEY.name.upper()}] 键进行截图。")
    print("按下 [ESC] 键退出截图模式。")

    def take_screenshot():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = os.path.join(RAW_DATA_DIR, f"{timestamp}.png")
        ImageGrab.grab().save(filename)
        print(f"截图已保存: {filename}")

    def on_press(key):
        if key == SCREENSHOT_HOTKEY:
            take_screenshot()
        elif key == keyboard.Key.esc:
            print("--- 已退出截图模式 ---")
            return False  # 停止监听

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

def launch_labelimg():
    """启动LabelImg并自动加载数据目录和类别文件。"""
    print("--- 正在启动 LabelImg ---")
    if not os.path.exists(RAW_DATA_DIR) or not os.listdir(RAW_DATA_DIR):
        print("警告: 原始数据目录是空的。请先进行截图。")
        return

    try:
        # 构建命令，自动传入图片目录和预定义类别文件
        command = [
            'labelImg',
            os.path.abspath(RAW_DATA_DIR),
            os.path.abspath(CLASSES_FILE)
        ]
        print(f"执行命令: {' '.join(command)}")
        subprocess.Popen(command)
    except FileNotFoundError:
        print("错误: 无法找到 'labelImg' 命令。")
        print("请确保您已经通过 'pip install labelimg' 安装了它，并且它在您的系统路径中。")
    except Exception as e:
        print(f"启动LabelImg时发生错误: {e}")

def launch_training():
    """调用训练脚本，启动YOLO训练。"""
    print("--- 准备启动训练流水线 ---")
    try:
        command = [
            'python',
            'train_yolo.py',
            '--data-dir', RAW_DATA_DIR,
            '--classes-file', CLASSES_FILE
        ]
        print(f"执行命令: {' '.join(command)}")
        # 使用 Popen 以便实时看到训练脚本的输出
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        rc = process.poll()
        print(f"--- 训练脚本执行完毕，退出代码: {rc} ---")

    except Exception as e:
        print(f"启动训练时发生错误: {e}")

def main_menu():
    """显示主菜单并处理用户输入。"""
    setup_environment()
    
    while True:
        print("\n=======================================")
        print("    YOLOv8 一站式工作流控制台")
        print("=======================================")
        print("1. [采集] 启动截图模式")
        print("2. [标注] 启动 LabelImg")
        print("3. [训练] 开始全自动训练")
        print("4. 退出")
        print("---------------------------------------")
        choice = input("请输入您的选择 (1-4): ")

        if choice == '1':
            screenshot_mode()
        elif choice == '2':
            launch_labelimg()
        elif choice == '3':
            launch_training()
        elif choice == '4':
            print("再见！")
            break
        else:
            print("无效输入，请输入1到4之间的数字。")

if __name__ == "__main__":
    main_menu()

