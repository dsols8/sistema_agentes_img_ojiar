# tests/test_yolo.py
from ultralytics import YOLO
from pathlib import Path
import cv2

model = YOLO("yolov8n.pt")  # modelo pre-entrenado

input_dir = Path("../input_imagenes")  # adapta si tu estructura es distinta
output_dir = Path("../debug_recortes")
output_dir.mkdir(exist_ok=True)

for img_path in input_dir.glob("*.jpg"):
    results = model(img_path)
    boxes = results[0].boxes.xyxy.cpu().numpy()  # array de [x1,y1,x2,y2]
    print(f"{img_path.name}: {len(boxes)} cajas detectadas")
    img = cv2.imread(str(img_path))
    for i, (x1, y1, x2, y2) in enumerate(boxes):
        crop = img[int(y1):int(y2), int(x1):int(x2)]
        cv2.imwrite(str(output_dir / f"{img_path.stem}_{i}.jpg"), crop)
