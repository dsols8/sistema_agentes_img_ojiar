# ============================
# predict_yolo.py
# ============================
"""
Script para generar predicciones y recortes con YOLOv8.
Ejecuta:
  python src/predict_yolo.py
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
# Ajusta según tus rutas
MODEL_WEIGHTS = ROOT / "runs" / "detect" / "producto_v3" / "weights" / "best.pt"
SOURCE_DIR    = ROOT / "input_imagenes"
CONF_THRESHOLD = 0.05


def predict_yolo():
    cmd = [
        "yolo",
        "task=detect",
        "mode=predict",
        f"model={MODEL_WEIGHTS}",
        f"source={SOURCE_DIR}",
        "save=True",
        "save_crop=True",
        f"conf={CONF_THRESHOLD}"
    ]
    print("Ejecutando predicción YOLOv8:", " ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    predict_yolo()