# ============================
# process_catalog_LLM.py
# ============================
"""
Script para procesar los recortes generados por YOLO con GPT-4o Vision,
extraer JSON (nombre, código, precio) y volcarlo en un Excel.
Ejecuta:
  python src/process_catalog_gpt4o.py
"""
import os
import re
import json
import base64
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from ultralytics import YOLO
import openpyxl
import cv2

# Carga clave API
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Rutas
ROOT       = Path(__file__).parent.parent
IMG_DIR    = ROOT / "input_imagenes"
MODEL_PATH = ROOT / "runs" / "detect" / "producto_v3" / "weights" / "best.pt"
CROPS_DIR  = ROOT / "runs" / "crops"
EXCEL_PATH = ROOT / "productos.xlsx"

CROPS_DIR.mkdir(parents=True, exist_ok=True)
model = YOLO(str(MODEL_PATH))

# Prepara Excel
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Productos"
ws.append(["Nombre", "Código", "Precio", "Página", "Archivo", "CropPath"])

# Función helper
def extract_with_gpt4o(crop_path):
    b64 = base64.b64encode(crop_path.read_bytes()).decode()
    messages = [
        {"role":"system","content":"Eres un asistente multimodal experto en catálogos. Extrae nombre (texto grande), código y precio (solo dígitos)."},
        {"role":"user","content":[
            {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}},
            {"type":"text","text":"Devuélveme **solo** un JSON con {\"nombre\":...,\"codigo\":...,\"precio\":...}."}
        ]}
    ]
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    return resp.choices[0].message.content.strip()

# Procesamiento
for img_file in sorted(IMG_DIR.glob("*.jpg")):
    page = int(re.findall(r"(\d+)", img_file.stem)[-1]) if re.findall(r"(\d+)", img_file.stem) else None
    results = model.predict(source=str(img_file), conf=0.2, verbose=False)
    boxes = results[0].boxes.xyxy.cpu().numpy() or [[0,0,*results[0].orig_shape[:2][::-1]]]

    for idx, (x1,y1,x2,y2) in enumerate(boxes):
        crop = results[0].orig_img[int(y1):int(y2), int(x1):int(x2)]
        crop_name = f"{img_file.stem}_page{page}_{idx}.jpg"
        crop_path = CROPS_DIR / crop_name
        cv2.imwrite(str(crop_path), crop)
        try:
            json_str = extract_with_gpt4o(crop_path)
            data = json.loads(json_str)
        except:
            continue
        if all(k in data and data[k] for k in ("nombre","codigo","precio")):
            ws.append([
                data["nombre"],
                data["codigo"],
                re.sub(r"\D","",data["precio"]),
                page,
                img_file.name,
                str(crop_path.relative_to(ROOT))
            ])

wb.save(EXCEL_PATH)
print(f"✅ Excel generado en {EXCEL_PATH} con {ws.max_row-1} productos.")
