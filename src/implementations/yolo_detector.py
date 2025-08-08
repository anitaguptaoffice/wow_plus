
from ultralytics import YOLO
from PIL import ImageGrab
import numpy as np

class YoloDetector:
    def __init__(self, model_path):
        """
        初始化YOLOv8检测器。
        :param model_path: 训练好的YOLOv8模型文件路径 (e.g., 'best.pt')。
        """
        try:
            self.model = YOLO(model_path)
            print(f"YOLO model loaded successfully from {model_path}")
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            raise

    def detect_skills(self, screen_region=None):
        """
        在整个屏幕或指定区域进行截图，并使用YOLO模型检测技能。

        :param screen_region: [x1, y1, x2, y2] 格式的截图区域，如果为None则截取全屏。
        :return: 一个列表，包含所有检测到的技能信息。
                 每个技能信息是一个字典: {'name': str, 'confidence': float, 'box': [x1, y1, x2, y2]}
        """
        try:
            # 截图
            if screen_region:
                screenshot = ImageGrab.grab(bbox=screen_region)
            else:
                screenshot = ImageGrab.grab()

            # PIL图像转为OpenCV格式 (YOLO内部处理)
            results = self.model(screenshot, verbose=False) # 直接调用模型进行预测

            detections = []
            # result in results is a generator, so we need to iterate
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # 获取类别ID和置信度
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    # 获取类别名称
                    class_name = self.model.names[class_id]
                    
                    # 获取边界框坐标
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    detections.append({
                        'name': class_name,
                        'confidence': confidence,
                        'box': [x1, y1, x2, y2]
                    })
            
            return detections
        except Exception as e:
            print(f"An error occurred during skill detection: {e}")
            return []

if __name__ == '__main__':
    # 用于独立测试
    # 确保你有一个 best.pt 文件，或者使用预训练模型进行测试
    # model_path = 'yolov8n.pt' # 使用预训练模型测试，它能识别通用物体
    # detector = YoloDetector(model_path=model_path)
    
    # 假设你已经训练好了自己的模型
    try:
        custom_model_path = 'runs/detect/train/weights/best.pt' # 默认训练输出路径
        detector = YoloDetector(model_path=custom_model_path)
        print("Detecting skills on screen...")
        detected_skills = detector.detect_skills()
        if detected_skills:
            print("Detected skills:")
            for skill in detected_skills:
                print(f"  - {skill['name']} (Confidence: {skill['confidence']:.2f}) at {skill['box']}")
        else:
            print("No skills detected.")
    except Exception as e:
        print(f"Failed to run test: {e}")
        print("Please make sure you have a trained model at the specified path or change the path.")
