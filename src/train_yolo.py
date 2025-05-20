# ============================
# train_yolo.py
# ============================
"""
Script para entrenar tu modelo YOLOv8 desde Python.
Ejecuta:
  python src/train_yolo.py
"""
import subprocess
import sys
from pathlib import Path

# Configuración de rutas
ROOT = Path(__file__).parent.parent
# Ajusta estos parámetros según tu experiencia
DATA_YAML = ROOT / "dataset.yaml"
MODEL_BASE = "yolov8n.pt"
IMAGE_SIZE = 640
EPOCHS = 60
BATCH = 8
RUN_NAME = "producto_v3"


def train_yolo():
    cmd = [
        "yolo",
        "task=detect",
        "mode=train",
        f"model={MODEL_BASE}",
        f"data={DATA_YAML}",
        f"imgsz={IMAGE_SIZE}",
        f"epochs={EPOCHS}",
        f"batch={BATCH}",
        f"name={RUN_NAME}"
    ]
    print("Ejecutando entrenamiento YOLOv8:", " ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    train_yolo()
