import cv2
import numpy as np
import torch
from ultralytics import YOLO
import time
from PIL import ImageFont, ImageDraw, Image

class GarbageDetector:
    def __init__(self, model_path):
        print(f"加载模型: {model_path}")
        self.model = YOLO(model_path)
        self.class_mapping = {
            0: "其他垃圾",
            1: "厨余垃圾",
            2: "可回收垃圾",
            3: "有害垃圾"
        }
        self.conf_threshold = 0.5
        self.font = ImageFont.truetype('simhei.ttf', 20)  # 需要字体文件
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()

    def _draw_chinese(self, frame, text, position):
        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        draw.text(position, text, font=self.font, fill=(0, 255, 0))
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def detect(self, frame):
        # 计算FPS
        self.frame_count += 1
        if time.time() - self.start_time >= 1:
            self.fps = self.frame_count
            self.frame_count = 0
            self.start_time = time.time()

        # 检测处理
        results = self.model(frame, conf=self.conf_threshold)
        detected_class = None
        max_conf = 0

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls.item())
                conf = box.conf.item()

                if conf > max_conf:
                    max_conf = conf
                    detected_class = self.class_mapping[cls_id]

                # 绘制边界框和中文标签
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f"{self.class_mapping[cls_id]}: {conf:.2f}"
                frame = self._draw_chinese(frame, label, (x1, y1-25))

        # 添加FPS显示
        frame = self._draw_chinese(frame, f"FPS: {self.fps}", (10, 10))
        return frame, detected_class