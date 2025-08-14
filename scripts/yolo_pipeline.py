import os
import sys
import subprocess
import time
import yaml
from datetime import datetime
import mss
import mss.tools

class YOLOPipeline:
    def __init__(self, config_path="config.yaml"):
        self.config = self._load_config(config_path)
        self.pipeline_config = self.config.get("yolo_pipeline", {})
        self.raw_data_dir = self.pipeline_config.get("raw_data_dir", "raw_yolo_data")
        self.classes_file = self.pipeline_config.get("classes_file", "yolo_class_names.txt")
        self.class_names_list = self.pipeline_config.get("class_names", [])

    def _load_config(self, path):
        """加载YAML配置文件"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"错误: 配置文件 {path} 未找到。")
            return {}
        except Exception as e:
            print(f"加载配置文件时出错: {e}")
            return {}

    def setup_environment(self):
        """确保所有必要的目录和文件都存在"""
        os.makedirs(self.raw_data_dir, exist_ok=True)
        if not os.path.exists(self.classes_file) and self.class_names_list:
            print(f"正在创建类别文件: {self.classes_file}")
            with open(self.classes_file, "w", encoding="utf-8") as f:
                for name in self.class_names_list:
                    f.write(name + "\n")

    def screenshot_mode(self):
        """启动自动循环截图模式"""
        print("--- 已进入自动截图模式 ---")
        try:
            interval = float(input("请输入每次截图的间隔时间 (秒): "))
            if interval <= 0:
                print("错误: 间隔时间必须是正数。")
                return
        except ValueError:
            print("错误: 无效输入，请输入一个数字。")
            return

        print(f"准备开始... 5秒后将以每 {interval} 秒一次的频率自动截图。")
        print("切换到您的游戏窗口。要停止截图，请返回此窗口并按下 [Ctrl+C]。")

        try:
            time.sleep(5)
            print("--- 开始截图 ---")
            count = 0
            with mss.mss() as sct:
                while True:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    filename = os.path.join(self.raw_data_dir, f"{timestamp}.png")

                    # Grab the data from the primary monitor
                    sct_img = sct.grab(sct.monitors[1])

                    # Save to the picture file
                    mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)

                    count += 1
                    print(f"({count}) 截图已保存: {filename}")
                    time.sleep(interval)
        except KeyboardInterrupt:
            print("\n--- 截图已停止 ---")
        except Exception as e:
            print(f"截图过程中发生错误: {e}")

    def launch_labelimg(self):
        """启动LabelImg并自动加载数据目录和类别文件"""
        print("--- 正在启动 LabelImg ---")
        if not os.path.exists(self.raw_data_dir) or not os.listdir(self.raw_data_dir):
            print("警告: 原始数据目录是空的。请先进行截图。")
            return

        try:
            # Determine the path to the labelImg executable
            python_executable_dir = os.path.dirname(sys.executable)
            if sys.platform == "win32":
                labelimg_executable = os.path.join(python_executable_dir, "Scripts", "labelImg.exe")
            else:
                labelimg_executable = os.path.join(python_executable_dir, "bin", "labelImg")

            if not os.path.exists(labelimg_executable):
                print(f"警告: 在 '{labelimg_executable}' 未找到 labelImg。将回退到在系统PATH中搜索。")
                labelimg_executable = "labelImg"

            command = [labelimg_executable, os.path.abspath(self.raw_data_dir), os.path.abspath(self.classes_file)]
            print(f"执行命令: {' '.join(command)}")
            subprocess.Popen(command)
        except FileNotFoundError:
            print("错误: 无法找到 'labelImg' 命令。请确保已通过 'pip install labelimg' 安装，并且它位于您的系统路径或虚拟环境的Scripts目录中。")
        except Exception as e:
            print(f"启动LabelImg时发生错误: {e}")

    def launch_training(self):
        """调用训练脚本，启动YOLO训练"""
        print("--- 准备启动训练流水线 ---")
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            command = ["python", os.path.join(script_dir, "train_yolo.py")]
            print(f"执行命令: {' '.join(command)}")
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            rc = process.poll()
            print(f"--- 训练脚本执行完毕，退出代码: {rc} ---")
        except Exception as e:
            print(f"启动训练时发生错误: {e}")

def main_menu():
    """显示主菜单并处理用户输入"""
    pipeline = YOLOPipeline()
    pipeline.setup_environment()

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

        if choice == "1":
            pipeline.screenshot_mode()
        elif choice == "2":
            pipeline.launch_labelimg()
        elif choice == "3":
            pipeline.launch_training()
        elif choice == "4":
            print("再见！")
            break
        else:
            print("无效输入，请输入1到4之间的数字。")

if __name__ == "__main__":
    main_menu()
