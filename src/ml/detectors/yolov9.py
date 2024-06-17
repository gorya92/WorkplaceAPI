# For machine learning
import torch
# For array computations
import numpy as np
# For image decoding / editing
import cv2
# For environment variables
import os
# For detecting which ML Devices we can use
import platform

from PIL import ImageDraw, Image
# For actually using the YOLO models
from ultralytics import YOLO


class YoloV9ImageObjectDetection:
    PATH = os.environ.get("YOLO_WEIGHTS_PATH", "best.pt")
    _model = None

    def __init__(self):
        self.model = self._load_model()
        self.device = self._get_device()
        self.classes = self.model.names

    def _get_device(self):
        if platform.system().lower() == "darwin":
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    @classmethod
    def _load_model(cls):
        if cls._model is None:
            cls._model = YOLO(YoloV9ImageObjectDetection.PATH)
        return cls._model

    def _get_image_from_chunked(self, chunked):
        arr = np.asarray(bytearray(chunked), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)
        return img

    def score_frame(self, frame):
        self.model.to(self.device)
        frame = [frame]
        results = self.model(frame)
        return results

    def class_to_label(self, x):
        return self.classes[int(x)]

    def plot_boxes(self, results, frame):
        labels = []
        count = 0
        for r in results:
            boxes = r.boxes
            for box in boxes:
                c = box.cls
                l = self.model.names[int(c)]
                labels.append(l)
                print(box.xyxy)
                x1, y1, x2, y2 = box.xyxy[0][:4]
                print(x1, y1, x2, y2, count)
                count += 1
                frame = cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 255), 2)
                frame = cv2.putText(frame, l, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        return frame, labels, count

    def is_point_inside_rect(self, point, rect):
        px, py = point
        rx1, ry1, rx2, ry2 = rect
        return rx1 <= px <= rx2 and ry1 <= py <= ry2

    def check_and_draw_zones(self, frame, results, data1=None, data2=None):
        img = Image.fromarray(frame)
        draw = ImageDraw.Draw(img)

        img_width, img_height = img.size

        if data2 is None or data2[0] == 'string':
            data2 = []
        if data1 is None or data1[0] == 'string':
            data1 = [0, 0, img_width, img_height]

        bright_red = (255, 1, 1)
        bright_green = (0, 255, 0)

        x3, y3, x4, y4 = data1
        draw.rectangle([x3, y3, x4, y4], outline=bright_green, width=5)

        if data2:
            print("data1")
            print(data2)
            x1, y1, x2, y2 = data2
            print("bright_red")
            print(bright_red)
            draw.rectangle([x1, y1, x2, y2], outline="red", width=5)

        centers = [((box.xyxy[0][0] + box.xyxy[0][2]) / 2, (box.xyxy[0][1] + box.xyxy[0][3]) / 2) for r in results for
                   box in
                   r.boxes]

        count_in_green_zone = 0
        count_in_red_zone = 0
        for center in centers:
            in_green_zone = self.is_point_inside_rect(center, data1)
            in_red_zone = self.is_point_inside_rect(center, data2) if data2 else False
            if in_green_zone and not in_red_zone:
                count_in_green_zone += 1
            if in_red_zone:
                count_in_red_zone += 1

        frame_with_zones = np.array(img)
        return frame_with_zones, count_in_green_zone, count_in_red_zone

    def process_image(self, chunked, workplace_id, data1=None, data2=None):
        frame = self._get_image_from_chunked(chunked)
        results = self.score_frame(frame)
        frame, labels, count = self.plot_boxes(results, frame)
        frame_with_zones, green_count, red_count = self.check_and_draw_zones(frame, results, data1, data2)

        output_filename = f'workplace{workplace_id}.jpg'
        output_path = os.path.join("static", output_filename)
        cv2.imwrite(output_path, frame_with_zones)

        return frame_with_zones, green_count, red_count, output_filename
