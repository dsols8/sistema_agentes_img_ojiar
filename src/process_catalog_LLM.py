# src/process_catalog_llm.py
# ============================
"""
Función para procesar un catálogo completo con GPT-4o Vision.

La función acepta:
  - image_dir: Ruta de la carpeta con imágenes del catálogo (jpg o png).
  - catalog_name: Nombre para el archivo Excel de salida (sin extensión).

Ejemplo de llamada desde main.py:
    process_catalog_llm("input_imagenes/Estilos", "estilos")

Se genera "excel/estilos.xlsx" en la raíz del proyecto.
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


def _extract_json(text: str) -> str:
    """
    Extrae el primer bloque JSON array de text, soportando fences ```json ...```
    o buscando el primer '[' y el último ']' en el contenido.
    """
    m = re.search(r"```json\s*(\[.*?\])\s*```", text, re.S)
    if m:
        return m.group(1)
    start, end = text.find('['), text.rfind(']')
    if 0 <= start < end:
        return text[start:end+1]
    return ""


def process_catalog_llm(image_dir: str | Path, catalog_name: str, model: str = "gpt-4.1"):
    """
    Procesa todas las imágenes JPG y PNG en image_dir con GPT-4o Vision y genera un Excel.

    :param image_dir: Carpeta con imágenes del catálogo (jpg/png).
    :param catalog_name: Nombre de archivo Excel de salida (sin ".xlsx").
    """
    # Determina carpeta de imágenes
    IMG_DIR = Path(image_dir)
    if not IMG_DIR.is_absolute():
        IMG_DIR = ROOT / image_dir
    if not IMG_DIR.exists():
        raise FileNotFoundError(f"No existe la ruta de imágenes: {IMG_DIR}")

    # Prepara carpeta y ruta del Excel
    EXCEL_DIR = ROOT / "excel"
    print(f"Guardando Excel en: {EXCEL_DIR}")
    EXCEL_DIR.mkdir(parents=True, exist_ok=True)
    EXCEL_PATH = EXCEL_DIR / f"{catalog_name}.xlsx"

    # Crea libro y hoja
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Productos"
    ws.append(["Nombre", "Código", "Precio", "Página", "Archivo"])

    # Obtiene todos los archivos jpg/png
    image_paths = list(IMG_DIR.glob("*.jpg")) + list(IMG_DIR.glob("*.png"))
    image_paths.sort()

    for img_file in image_paths:
        # Extrae número de página del filename (último grupo de dígitos)
        nums = re.findall(r"(\d+)", img_file.stem)
        page = int(nums[-1]) if nums else None

        # Codifica imagen en base64
        img_b64 = base64.b64encode(img_file.read_bytes()).decode()
        messages = [
            {"role": "system", "content": (
                "Eres un asistente multimodal experto en catálogos. "
                "Devuélveme únicamente un JSON array con objetos {\"nombre\",\"codigo\",\"precio\"}, sin texto adicional."
                "Si el producto tiene variantes agrega la variante al nombre, "
                "por ejemplo: \"Nombre Producto - Variante\". "
            )},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/{img_file.suffix[1:]};base64,{img_b64}"}},
                {"type": "text", "text": (
                    "Extrae todos los productos de esta página. Responde solo con el JSON array."
                )}
            ]}
        ]

        try:
            # Llamada GPT-4o Vision
            resp = client.chat.completions.create(
                model=model, messages=messages, temperature=0.0
            )
            raw = resp.choices[0].message.content
            print(f"\n--- RAW GPT RESPONSE for {img_file.name} ---\n{raw}\n---------------------------")

            # Extrae y parsea el bloque JSON
            jtext = _extract_json(raw)
            if not jtext:
                print(f"⚠️ JSON no encontrado en {img_file.name}, omitiendo.")
                continue
            try:
                products = json.loads(jtext)
            except json.JSONDecodeError:
                print(f"⚠️ JSON malformado en {img_file.name}, contenido:\n{jtext}")
                continue

            # Volcar cada producto
            for prod in products:
                nombre = prod.get("nombre", "").strip()
                codigo = re.sub(r"\D", "", str(prod.get("codigo", "")))
                precio = re.sub(r"\D", "", str(prod.get("precio", "")))
                # if not (nombre and codigo and precio):
                #     print(f"⚠️ Campos faltantes en {img_file.name}, omitiendo entrada.")
                #     continue
                ws.append([nombre, codigo, precio, page, img_file.name])

            print(f"✅ Procesados {len(products)} productos en {img_file.name}")
        except Exception as e:
            print(f"⚠️ Error procesando {img_file.name}: {e}")

    # Guarda el Excel
    wb.save(EXCEL_PATH)
    print(f"\n🎉 Archivo guardado en {EXCEL_PATH} con {ws.max_row - 1} productos.")
