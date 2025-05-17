# AI AGENTS PYTHON SYSTEM
## From JOINT ZENTURE

### Necessary Commands:

Train Yolo:
```bash

yolo task=detect mode=train model=yolov8n.pt data=dataset.yaml imgsz=640 epochs=60 batch=8 name=producto_v3

```

Crop new images:
```bash

yolo task=detect mode=predict model=runs/detect/producto_v3/weights/best.pt source=input_imagenes save=True save_crop=True conf=0.05

```