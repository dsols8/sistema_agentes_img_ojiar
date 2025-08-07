#!/usr/bin/env python
"""create_catalog.py – Catálogo vertical con GPT‑4o visión + DALL·E 3
=============================================================================
Genera un PDF tamaño **carta vertical** (8.5 × 11 in) donde cada página contiene:

1. **Fondo** creado por DALL·E 3 usando un prompt generado por GPT‑4o visión.
2. **Foto del producto** centrada en la parte superior.
3. **Bloque de texto** (nombre, código y precio) anclado SIEMPRE al margen
   inferior, respetando la zona reservada (~20 % inferior) que el prompt exige.

Uso rápido
----------
```bash
python create_catalog.py imgs/ products.xlsx -o catalog.pdf \
       --openai-model gpt-4o --dalle-model dall-e-3
```

Requisitos
----------
```bash
pip install openai>=1.12.0 pandas reportlab pillow requests
export OPENAI_API_KEY=sk-...
```
"""

# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------
from __future__ import annotations

import argparse
import base64
import io
import os
from pathlib import Path
from typing import Tuple

import openai  # SDK oficial 1.x
import pandas as pd
import requests
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

# ---------------------------------------------------------------------------
# RUTAS Y FUENTES
# ---------------------------------------------------------------------------
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
FONTS_DIR = SRC_DIR / "fonts"

FONTS: dict[str, Path] = {
    "LeagueSpartan-Bold":     FONTS_DIR / "LeagueSpartan-Bold.ttf",
    "LeagueSpartan-Regular":  FONTS_DIR / "LeagueSpartan-Regular.ttf",
    "BebasNeue":              FONTS_DIR / "BebasNeue-Regular.ttf",
    "Montserrat-Bold":        FONTS_DIR / "Montserrat-Bold.ttf",
}
for name, path in FONTS.items():
    if path.exists():
        pdfmetrics.registerFont(TTFont(name, str(path)))
    else:
        print(f"⚠️  Fuente faltante {path.name} – se usará Helvetica.")

FN_NAME   = "LeagueSpartan-Bold"    if "LeagueSpartan-Bold"    in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
FN_DIGITS = "BebasNeue"             if "BebasNeue"             in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
FN_SYMBOL = "Montserrat-Bold"       if "Montserrat-Bold"       in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
FN_CODE   = "LeagueSpartan-Regular" if "LeagueSpartan-Regular" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"

# ---------------------------------------------------------------------------
# CONSTANTES DE DISEÑO
# ---------------------------------------------------------------------------
LINE_SPACING = 25           # pt entre líneas del bloque inferior
TEXT_BLOCK_H = LINE_SPACING * 2 + 26  # Altura total (Nombre + Código + Precio)

# ---------------------------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------------------------

def _abs(path_like: str | Path) -> Path:
    p = Path(path_like)
    return p if p.is_absolute() else PROJECT_ROOT / p


def _split_price(raw: str) -> Tuple[str, str]:
    digits = ''.join(ch for ch in raw if ch.isdigit())
    if not digits:
        return '₡', raw
    num = int(digits)
    formatted = ' '.join(f"{num:,}".split(','))
    return '₡', formatted

# ---------------------------------------------------------------------------
# GPT‑4o VISIÓN → PROMPT DALL·E
# ---------------------------------------------------------------------------

def describe_image_with_openai(img_path: Path, model: str) -> str:
    """Devuelve un prompt (UNA línea) para DALL·E 3 a partir de la foto."""
    data_url = f"data:image/png;base64,{base64.b64encode(img_path.read_bytes()).decode()}"

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    system_prompt = (
        "You are an expert in product catalog backgrounds. "
        "Generate the BEST possible DALL·E 3 prompt to create a vertical, letter-size (8.5x11 in) background that matches the CATEGORY of the attached product image. "
        "The background must be completely light, in bright neutral or soft pastel tones only, with no dark or high-contrast areas. "
        "The entire background should be suitable for overlaying black text anywhere. "
        "The center should be clear, soft and empty, ready for the product photo. "
        "Capture an environment relevant to the product type, but never describe, mention, or imply the product or any brand. "
        "No objects, no logos, no text, no visual clutter. "
        "Make the promt as detailed as possible. "
        "Return only the prompt, in English, for direct use in DALL·E 3."
    )


    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": data_url}},
            {"type": "text", "text": "Return only the prompt for the background."}
        ]},
    ]




    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.0,
        )
        return resp.choices[0].message.content.strip()
    except openai.OpenAIError as exc:
        print(f"⚠️  GPT‑4o rechazó la imagen: {exc}. Se usará prompt neutro.")
        return "Neutral light-gray studio background, empty, subtle vignette"

# ---------------------------------------------------------------------------
# DALL·E 3 → BACKGROUND
# ---------------------------------------------------------------------------

def generate_dalle_background(prompt: str, dalle_model: str, size: str = "1024x1792") -> ImageReader:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        res = client.images.generate(model=dalle_model, prompt=prompt, size=size, n=1)
        url = res.data[0].url
        img_bytes = requests.get(url, timeout=30).content
        return ImageReader(io.BytesIO(img_bytes))
    except Exception as exc:
        print(f"⚠️  DALL·E error: {exc}. Fondo blanco.")
        buf = io.BytesIO()
        Image.new('RGB', (1024, 1792), 'white').save(buf, format='PNG')
        buf.seek(0)
        return ImageReader(buf)

# ---------------------------------------------------------------------------
# GENERADOR PRINCIPAL
# ---------------------------------------------------------------------------

def generate_catalog(
    images_dir: str | Path,
    excel_path: str | Path,
    output_pdf: str | Path = 'catalog.pdf',
    *,
    openai_model: str = 'gpt-4.1',
    dalle_model: str = 'dall-e-3',
) -> None:
    images_dir, excel_path, output_pdf = map(_abs, (images_dir, excel_path, output_pdf))

    if not images_dir.is_dir():
        raise FileNotFoundError(f"No existe carpeta de imágenes: {images_dir}")
    if not excel_path.exists():
        raise FileNotFoundError(f"No existe archivo de datos: {excel_path}")
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    # Carga spreadsheet
    df = (pd.read_excel(excel_path, engine='openpyxl') if excel_path.suffix.lower() in {'.xls', '.xlsx', '.xlsm'}
          else pd.read_csv(excel_path))
    if not {"Nombre", "Codigo", "Precio"}.issubset(df.columns):
        raise ValueError("El Excel/CSV debe tener columnas Nombre, Codigo, Precio")

    page_w, page_h = letter
    margin = 0.5 * inch

    c: Canvas = Canvas(str(output_pdf), pagesize=letter)

    for _, row in df.iterrows():
        nombre, codigo, precio_raw = map(str, (row['Nombre'], row['Codigo'], row['Precio']))
        img_path = images_dir / f"{codigo}.png"
        if not img_path.exists():
            raise FileNotFoundError(f"Imagen faltante: {img_path}")

        # 1️⃣ GPT‑4o visión → Prompt
        prompt = describe_image_with_openai(img_path, openai_model)
        print(f"\n✅ {codigo} → prompt DALL·E:\n{prompt}")

        # 2️⃣ DALL·E fondo
        bg = generate_dalle_background(prompt, dalle_model)
        c.drawImage(bg, 0, 0, width=page_w, height=page_h, preserveAspectRatio=False)

        # 3️⃣ Foto producto (parte superior)
        max_img_h = page_h - 2 * margin - TEXT_BLOCK_H - 12  # reserva zona texto
        max_img_w = page_w - 2 * margin
        prod = ImageReader(str(img_path))
        iw, ih = prod.getSize()
        scale = min(max_img_w / iw, max_img_h / ih)
        dw, dh = iw * scale, ih * scale
        img_x = (page_w - dw) / 2
        img_y = page_h - margin - dh
        c.drawImage(prod, img_x, img_y, dw, dh, preserveAspectRatio=True, mask='auto')

        # 4️⃣ Bloque inferior SIEMPRE anclado a bottom margin
        base_x = margin
        base_y = margin + TEXT_BLOCK_H  # baseline del nombre

        c.setFont(FN_NAME, 26)
        c.drawString(base_x, base_y, nombre.strip())

        c.setFont(FN_CODE, 15)
        c.drawString(base_x, base_y - LINE_SPACING, f"cod {codigo.strip()}")

        sym, digits = _split_price(precio_raw)
        price_y = base_y - 2 * LINE_SPACING
        c.setFont(FN_SYMBOL, 15)
        sym_w = pdfmetrics.stringWidth(sym, FN_SYMBOL, 20)
        c.drawString(base_x, price_y, sym)
        c.setFont(FN_DIGITS, 20)
        c.drawString(base_x + sym_w + 2, price_y, digits)

        c.showPage()

    c.save()
    print(f"✅ PDF generado: {output_pdf}")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Genera un catálogo PDF usando GPT‑4o visión + DALL·E 3.")
    ap.add_argument('images_dir', help='Carpeta con imágenes PNG/JPG')
    ap.add_argument('excel_path', help='Archivo Excel/CSV con Nombre, Codigo, Precio')
    ap.add_argument('-o', '--output', default='catalog.pdf', help='PDF de salida')
    ap.add_argument('--openai-model', default='gpt-4o', help='Modelo GPT‑4 visión')
    ap.add_argument('--dalle-model', default='dall-e-3', help='Modelo DALL·E')
    args = ap.parse_args()

    generate_catalog(
        args.images_dir,
        args.excel_path,
        args.output,
        openai_model=args.openai_model,
        dalle_model=args.dalle_model,
    )
