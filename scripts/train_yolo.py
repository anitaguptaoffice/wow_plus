
import os
import shutil
import random
import yaml
from ultralytics import YOLO

class YOLOTrainer:
    def __init__(self, config_path="config.yaml"):
        self.config = self._load_config(config_path)
        self.pipeline_config = self.config.get("yolo_pipeline", {})
        self.training_config = self.config.get("yolo_training", {})

        # 从配置中获取参数
        self.source_dir = self.pipeline_config.get("raw_data_dir", "raw_yolo_data")
        self.dest_dir = self.training_config.get("output_dir", "yolo_dataset")
        self.classes_file = self.pipeline_config.get("classes_file", "yolo_class_names.txt")
        self.split_ratio = self.training_config.get("split_ratio", 0.8)
        self.epochs = self.training_config.get("epochs", 50)
        self.model = self.training_config.get("model", "yolov8n.pt")
        self.imgsz = self.training_config.get("imgsz", 640)

    def _load_config(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise RuntimeError(f"错误: 配置文件 {path} 未找到。")
        except Exception as e:
            raise RuntimeError(f"加载配置文件时出错: {e}")

    def prepare_dataset(self):
        """自动将源数据分割成训练集和验证集"""
        print("--- 开始准备数据集 ---")
        # ... (此处省略了 prepare_dataset 的内部实现，因为它无需修改)
        all_files = os.listdir(self.source_dir)
        image_extensions = {'.jpg', '.jpeg', '.png'}
        images = [f for f in all_files if os.path.splitext(f)[1].lower() in image_extensions]
        
        valid_pairs = []
        for img_file in images:
            label_file = os.path.splitext(img_file)[0] + '.txt'
            if label_file in all_files:
                valid_pairs.append((img_file, label_file))
            else:
                print(f"警告: 图片 '{img_file}' 缺少对应的标签文件，将被跳过。")

        if not valid_pairs:
            raise ValueError(f"在源目录 '{self.source_dir}' 中没有找到任何有效的图片-标签对。")

        random.shuffle(valid_pairs)
        split_index = int(len(valid_pairs) * self.split_ratio)
        train_pairs = valid_pairs[:split_index]
        val_pairs = valid_pairs[split_index:]

        paths = {
            'train_images': os.path.join(self.dest_dir, 'images', 'train'),
            'train_labels': os.path.join(self.dest_dir, 'labels', 'train'),
            'val_images': os.path.join(self.dest_dir, 'images', 'val'),
            'val_labels': os.path.join(self.dest_dir, 'labels', 'val'),
        }
        for path in paths.values():
            os.makedirs(path, exist_ok=True)

        def copy_files(pairs, img_dest, lbl_dest):
            for img_file, lbl_file in pairs:
                shutil.copy(os.path.join(self.source_dir, img_file), img_dest)
                shutil.copy(os.path.join(self.source_dir, lbl_file), lbl_dest)

        copy_files(train_pairs, paths['train_images'], paths['train_labels'])
        copy_files(val_pairs, paths['val_images'], paths['val_labels'])
        print("--- 数据集准备完成 ---")
        return self.dest_dir

    def create_dataset_yaml(self, class_names):
        """创建 dataset.yaml 文件"""
        yaml_path = os.path.join(self.dest_dir, 'dataset.yaml')
        data = {
            'path': os.path.abspath(self.dest_dir),
            'train': 'images/train',
            'val': 'images/val',
            'names': {i: name for i, name in enumerate(class_names)}
        }
        with open(yaml_path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)
        print(f"已创建 dataset.yaml 文件于: {yaml_path}")
        return yaml_path

    def run_training(self, yaml_path):
        """启动YOLOv8训练"""
        print("--- 开始YOLOv8训练 ---")
        try:
            model = YOLO(self.model)
            results = model.train(
                data=yaml_path,
                epochs=self.epochs,
                imgsz=self.imgsz,
                project='runs/detect',
                name='train'
            )
            print("--- 训练成功完成 ---")
            print(f"最佳模型已保存至: {results.save_dir}/weights/best.pt")
        except Exception as e:
            print(f"!!! 训练过程中发生错误: {e}")

    def execute(self):
        """执行完整的训练流水线"""
        # 1. 读取类别文件
        try:
            with open(self.classes_file, 'r') as f:
                class_names = [line.strip() for line in f if line.strip()]
            if not class_names:
                raise ValueError("类别文件为空或未找到。")
            print(f"成功加载 {len(class_names)} 个类别。")
        except FileNotFoundError:
            raise RuntimeError(f"错误: 类别文件 {self.classes_file} 未找到。")

        # 2. 准备数据集
        prepared_dataset_dir = self.prepare_dataset()

        # 3. 创建 dataset.yaml
        yaml_file_path = self.create_dataset_yaml(class_names)

        # 4. 启动训练
        self.run_training(yaml_file_path)

if __name__ == "__main__":
    trainer = YOLOTrainer()
    trainer.execute()
