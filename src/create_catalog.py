"""
create_catalog.py + GPT‑4 visión
--------------------------------
Genera un catálogo PDF **y**, antes de colocar cada imagen en el PDF, envía la
imagen a la API de OpenAI (GPT‑4 visión) para obtener una descripción que se
muestra por consola.

Requisitos extra:
* `openai>=1.12.0` (u otra versión 1.x)
* Variable de entorno `OPENAI_API_KEY` con tu key.

Cómo usar:
```bash
python create_catalog.py ./imgs catalog.xlsx -o catalog.pdf \
  --openai-model gpt-4o-vision-preview
```
Si omites `--openai-model`, usa por defecto `gpt-4.1`.
"""

# ============================================================
# IMPORTS
# ============================================================
from pathlib import Path
import argparse
import base64
import os
import sys
import time

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import openai  # pip install openai>=1.12.0

# ============================================================
# RUTAS Y FUENTES
# ============================================================
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
FONTS_DIR = SRC_DIR / "fonts"

FONTS = {
    "LeagueSpartan-Bold":     FONTS_DIR / "LeagueSpartan-Bold.ttf",
    "LeagueSpartan-Regular":  FONTS_DIR / "LeagueSpartan-Regular.ttf",
    "BebasNeue":              FONTS_DIR / "BebasNeue-Regular.ttf",
    "Montserrat-Bold":        FONTS_DIR / "Montserrat-Bold.ttf",
}
for name, fpath in FONTS.items():
    if fpath.exists():
        pdfmetrics.registerFont(TTFont(name, str(fpath)))
    else:
        print(f"⚠️  Falta {fpath.name} → se usará Helvetica.")

FN_NAME   = "LeagueSpartan-Bold"    if "LeagueSpartan-Bold"    in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
FN_DIGITS = "BebasNeue"             if "BebasNeue"             in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
FN_SYMBOL = "Montserrat-Bold"       if "Montserrat-Bold"       in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
FN_CODE   = "LeagueSpartan-Regular" if "LeagueSpartan-Regular" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"

# ============================================================
# LAYOUT
# ============================================================
LINE_SPACING  = 25
TEXT_OFFSET_X = 0
TEXT_OFFSET_Y = 0

# ============================================================
# HELPERS
# ============================================================

def _abs(path_like: str | Path) -> Path:
    p = Path(path_like)
    return p if p.is_absolute() else PROJECT_ROOT / p


def _split_price(raw: str):
    digits_only = ''.join(ch for ch in raw if ch.isdigit())
    if not digits_only:
        return '₡', raw
    integer = int(digits_only)
    num = ' '.join(f"{integer:,}".split(','))
    return '₡', num


def describe_image_with_openai(img_path: Path, model: str) -> str:
    """Genera un *prompt* óptimo para DALL·E que cree un **fondo de página tamaño carta**
    acorde al tipo de producto detectado en la imagen.

    Ejemplo de respuesta esperada por GPT‑4:
    ```
    "Fondo minimalista en tonos pastel verdes con textura suave, líneas curvas sutiles
    que evoquen movimiento. Espacio central claro para un par de tenis deportivos blancos
    con detalles rojos. Luz difusa, sombras suaves. Formato vertical carta."
    ```
    """
    # 1) Codifica la imagen a Base‑64
    img_b64 = base64.b64encode(img_path.read_bytes()).decode()
    data_url = f"data:image/png;base64,{img_b64}"

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # 2) Mensajes → solicitamos a GPT‑4 que escriba SOLO el prompt, sin cabeceras extra
    messages = [
        {
            "role": "system",
            "content": (
                "Eres un experto en diseño gráfico. A partir de la imagen proporcionada, "
                "genera un prompt conciso y muy descriptivo que DALL·E pueda usar para "
                "crear un *fondo vertical tamaño carta (8.5×11 pulgadas)*. "
                "El fondo debe resaltar el objeto principal, ser estético y coherente con "
                "su categoría (ej.: deportivo, electrónico, cocina, moda). "
                "Evita mencionar marcas ni logotipos y no incluyas la palabra 'prompt' ni "
                "explicaciones extra: responde solo con la descripción en una línea."
            ),
        },
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url}},
                {"type": "text", "text": (
                    "Analiza el producto y devuelve la mejor descripción de fondo posible "
                    "para que DALL·E lo genere."
                )},
            ],
        },
    ]

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.0,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️  Error llamando a OpenAI: {e}")
        return "[Error al generar prompt]"
    except Exception as e:
        print(f"⚠️  Error llamando a OpenAI: {e}")
        return "[Error al obtener descripción]"

# ============================================================
# CORE
# ============================================================

def generate_catalog(images_dir: str | Path, excel_path: str | Path, output_pdf: str | Path = 'catalog.pdf', *, openai_model: str = 'gpt-4.1'):
    images_dir = _abs(images_dir)
    excel_path = _abs(excel_path)
    output_pdf = _abs(output_pdf)

    if not images_dir.is_dir():
        raise FileNotFoundError(f"No images dir: {images_dir}")
    if not excel_path.exists():
        raise FileNotFoundError(f"No data file: {excel_path}")
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(excel_path, engine='openpyxl') if excel_path.suffix.lower() in {'.xls', '.xlsx', '.xlsm'} else pd.read_csv(excel_path)
    if not {"Nombre", "Codigo", "Precio"}.issubset(df.columns):
        raise ValueError('Excel requiere columnas Nombre, Codigo, Precio')

    page_w, page_h = letter
    margin = 0.5 * inch

    c = canvas.Canvas(str(output_pdf), pagesize=letter)

    for _, row in df.iterrows():
        nombre = str(row['Nombre']).strip()
        codigo = str(row['Codigo']).strip()
        precio_raw = str(row['Precio']).strip()

        img_path = images_dir / f"{codigo}.png"
        if not img_path.exists():
            raise FileNotFoundError(f"Missing image {img_path}")

        # --- Llamada a GPT‑4 visión para descripción ---
        descripcion = describe_image_with_openai(img_path, openai_model)
        print(f"\n{codigo} → {descripcion}")

        # ------------------------------------------------
        # IMAGEN (arriba, escalada)
        # ------------------------------------------------
        text_block_height = LINE_SPACING * 2 + 26
        max_img_h = page_h - 2 * margin - text_block_height - 12
        max_img_w = page_w - 2 * margin

        img = ImageReader(str(img_path))
        iw, ih = img.getSize()
        scale = min(max_img_w / iw, max_img_h / ih)
        dw, dh = iw * scale, ih * scale
        img_x = (page_w - dw) / 2
        img_y = page_h - margin - dh
        c.drawImage(img, img_x, img_y, dw, dh, preserveAspectRatio=True, mask='auto')

        # ------------------------------------------------
        # BLOQUE DE TEXTO
        # ------------------------------------------------
        base_x = margin + TEXT_OFFSET_X
        base_y = img_y - 12 - TEXT_OFFSET_Y

        c.setFont(FN_NAME, 26)
        c.drawString(base_x, base_y, nombre)

        c.setFont(FN_CODE, 15)
        c.drawString(base_x, base_y - LINE_SPACING, f'cod {codigo}')

        sym, digits = _split_price(precio_raw)
        price_y = base_y - 2 * LINE_SPACING
        c.setFont(FN_SYMBOL, 15)
        sym_w = pdfmetrics.stringWidth(sym, FN_SYMBOL, 20)
        c.drawString(base_x, price_y, sym)
        c.setFont(FN_DIGITS, 20)
        c.drawString(base_x + sym_w + 2, price_y, digits)

        c.showPage()

    c.save()
    print(f'✅ PDF generado: {output_pdf}')

# ============================================================
# CLI
# ============================================================
if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Genera un catálogo y describe cada imagen con GPT‑4 Visión.')
    ap.add_argument('images_dir', help='Carpeta con las imágenes PNG')
    ap.add_argument('excel_path', help='Archivo Excel/CSV con los datos de productos')
    ap.add_argument('-o', '--output', default='catalog.pdf', help='Ruta del PDF de salida')
    ap.add_argument('--openai-model', default='gpt-4.1', help='ID del modelo OpenAI (ej. gpt-4o-vision-preview)')
    args = ap.parse_args()

    # Verifica la API key
    if not os.getenv('OPENAI_API_KEY'):
        sys.exit('❌ Falta la variable de entorno OPENAI_API_KEY')

    generate_catalog(args.images_dir, args.excel_path, args.output, openai_model=args.openai_model)
