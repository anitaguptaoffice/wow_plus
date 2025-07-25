# 《魔兽世界》技能自动化助手 (YOLO版)

这是一个基于YOLOv8图像识别技术的《魔兽世界》技能自动化助手。它通过实时监测屏幕上的技能图标状态，智能地执行预设的技能策略，以辅助玩家完成复杂的技能循环。

## 功能特性

- **实时技能检测**: 使用YOLOv8模型实时识别屏幕上的技能图标及其状态（可用/冷却中）。
- **灵活的策略配置**: 通过简单的YAML文件定义不同场景（如AOE、单体）下的技能优先级。
- **图形化用户界面**: 提供一个直观的GUI，用于管理策略、启动/停止引擎以及查看实时日志。
- **一站式工作流**: 内置截图、标注、训练的完整工作流，帮助用户快速创建和迭代自己的YOLO模型。
- **可扩展的按键模拟**: 支持多种按键模拟方式，并可轻松扩展。

## 安装与设置

1.  **克隆项目**:

    ```bash
    git clone <your-repo-url>
    cd <project-directory>
    ```

2.  **创建虚拟环境并安装依赖**:

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # macOS/Linux
    # .\.venv\Scripts\activate  # Windows

    pip install -r requirements.txt
    ```

3.  **准备YOLO模型**:

    - 如果你没有预训练的模型，可以使用项目内置的工作流来创建自己的模型。详情请见 [工作流](#工作流) 部分。
    - 将训练好的模型（通常是 `best.pt`）放置在 `runs/detect/train/weights/` 目录下，或在 `config.yaml` 中更新其路径。

## 使用说明

1.  **启动主程序**:

    ```bash
    python gui.py
    ```

2.  **配置策略**:

    - 在 `strategies/` 目录下，你可以找到策略示例文件（如 `frostfire_mage.yaml`）。
    - 你可以复制并修改这些文件，或通过GUI新建策略。
    - 在GUI中，通过“浏览”和“加载”按钮来选择和加载你的策略。

3.  **启动/停止引擎**:

    - 点击“启动引擎”按钮，自动化引擎将在后台开始运行。
    - 启动后，你可以通过在 `config.yaml` 中配置的按键（默认为F1, F2, F3）来切换不同的技能模式（AOE/单体）或停止施法。
    - 点击“停止引擎”按钮，将完全停止自动化过程。

## 工作流：创建你自己的YOLO模型

项目提供了一个命令行工具 `scripts/yolo_pipeline.py` 来简化模型的创建流程。

```bash
python scripts/yolo_pipeline.py
```

该工具会提供以下选项：

1.  **[采集] 启动截图模式**: 自动对你的游戏窗口进行截图，用于后续的标注。截图将保存在 `raw_yolo_data` 目录下。
2.  **[标注] 启动 LabelImg**: 启动 `labelImg` 工具，用于在截图上标注技能图标。请确保你已经定义好了 `yolo_class_names.txt` 中的类别。
3.  **[训练] 开始全自动训练**: 当你完成标注后，此选项会自动准备数据集、创建配置文件并开始YOLOv8训练。

## 配置文件说明 (`config.yaml`)

这是项目的主配置文件，包含了所有的关键设置。

- `yolo_pipeline`: YOLO工作流的相关配置。
  - `raw_data_dir`: 原始截图和标签的存放目录。
  - `classes_file`: 类别名称文件的路径。
  - `class_names`: 需要识别的技能状态列表。
- `yolo_training`: YOLO训练参数。
  - `output_dir`: 处理后的数据集存放目录。
  - `split_ratio`: 训练集与验证集的分割比例。
  - `epochs`: 训练轮次。
  - `model`: 使用的YOLOv8基础模型。
  - `imgsz`: 训练图片的输入尺寸。
- `yolo_model_path`: 训练完成后，最终模型的路径。
- `screen_capture_region`: 游戏技能栏在屏幕上的区域 `[x1, y1, x2, y2]`。`null` 代表全屏。
- `keystroke_sender`: 按键模拟器的配置。
- `current_strategy`: 当前默认加载的策略文件路径。
- `mode_switch_keys`: 用于切换模式的全局热键。

## 策略文件说明 (`strategies/*.yaml`)

策略文件定义了不同模式下的技能释放优先级。

- `name`, `class`, `spec`, `description`: 策略的基本信息。
- `global_cooldown`: 施放一个技能后的全局冷却时间（秒）。
- `bindings`: (可选) 按键绑定映射。例如，你可以将策略中的 `spell_1` 映射到实际的游戏按键 `1`。
- `aoe_priority`: AOE模式下的技能优先级列表。
- `single_target_priority`: 单体模式下的技能优先级列表。

每个技能都由 `name` (必须与YOLO类别名对应) 和 `key` (在 `bindings` 中定义的键或实际按键) 组成。
