# src/process_catalog_llm.py
# ============================
"""
Función para procesar imágenes completas con GPT-4o Vision y generar un Excel
con todos los productos extraídos.
"""
import os
import re
import json
import base64
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import openpyxl

# Carga la clave de OpenAI desde .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define la raíz del proyecto (un nivel arriba de src/)
ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "input_imagenes"
EXCEL_PATH = ROOT / "productos.xlsx"


def _extract_json(text: str) -> str:
    """
    Extrae el primer bloque JSON array de text, soportando fences ```json ...```
    o buscando el primer '[' y el último ']' en el contenido.
    """
    # fenced code block
    m = re.search(r"```json\s*(\[.*?\])\s*```", text, re.S)
    if m:
        return m.group(1)
    # plain JSON array
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return ""


def process_catalog_llm():
    """
    1) Itera sobre cada JPG en input_imagenes
    2) Llama a GPT-4o Vision para extraer un JSON array de productos
    3) Genera productos.xlsx con Nombre, Código, Precio, Página y Archivo
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Productos"
    # Encabezados: Nombre, Código, Precio, Página, Archivo
    ws.append(["Nombre", "Código", "Precio", "Página", "Archivo"])

    for img_file in sorted(IMG_DIR.glob("*.jpg")):
        # Número de página extraído del filename
        nums = re.findall(r"(\d+)", img_file.stem)
        page = int(nums[-1]) if nums else None

        # Codifica imagen en base64
        img_b64 = base64.b64encode(img_file.read_bytes()).decode()
        messages = [
            {"role": "system", "content": (
                "Eres un asistente multimodal experto en catálogos de productos. "
                "Solo debes devolver un JSON array con objetos {\"nombre\",\"codigo\",\"precio\"}, nada más."
            )},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                {"type": "text", "text": (
                    "Extrae todos los productos de esta página y devuélvelos solo como un JSON array."
                )}
            ]}
        ]

        # Llamada a la API multimodal
        resp = client.chat.completions.create(
            model="gpt-4o", messages=messages, temperature=0.0
        )
        raw = resp.choices[0].message.content
        print(f"\n--- RAW GPT RESPONSE for {img_file.name} ---\n{raw}\n---------------------------")

        # Extrae el bloque JSON
        jtext = _extract_json(raw)
        if not jtext:
            print(f"⚠️ No se encontró JSON válido en {img_file.name}, se omite.")
            continue

        # Parsea JSON
        try:
            products = json.loads(jtext)
        except json.JSONDecodeError:
            print(f"⚠️ JSON malformado en {img_file.name}, contenido:\n{jtext}")
            continue

        # Agrega cada producto válido al Excel
        for prod in products:
            nombre = prod.get("nombre", "").strip()
            codigo = re.sub(r"\D", "", str(prod.get("codigo", "")))
            precio = re.sub(r"\D", "", str(prod.get("precio", "")))

            if not (nombre and codigo and precio):
                print(f"⚠️ Falta nombre/código/precio en {img_file.name}, se omite.")
                continue

            ws.append([nombre, codigo, precio, page, img_file.name])

        print(f"✅ Procesados {len(products)} productos en {img_file.name}")

    # Guarda el archivo
    wb.save(EXCEL_PATH)
    print(f"\n🎉 Excel generado en {EXCEL_PATH} con {ws.max_row - 1} productos.")
