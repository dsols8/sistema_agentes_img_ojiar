"""
create_catalog.py
------------------
Genera un catálogo PDF multipágina usando:
  • Carpeta de imágenes PNG (<Codigo>.png)
  • Excel/CSV con columnas: Nombre, Codigo, Precio

Tipografías (sin cambios):
  League Spartan Bold – nombre  
  Bebas Neue Regular – código y dígitos  
  Montserrat Regular – símbolo ₡

**Nuevo layout**
===============
• La **imagen ahora se coloca arriba** y ocupa mayor altura.  
• El bloque de texto (nombre‑código‑precio) queda DEBAJO de la imagen,
  dentro de un cuadro cuyo desplazamiento controlas con:

```python
TEXT_OFFSET_X = 0   # +→ derecha | −→ izquierda
TEXT_OFFSET_Y = 0   # +→ arriba  | −→ abajo (respecto al borde inferior de la imagen)
```

Puedes seguir ajustando `LINE_SPACING` para la distancia vertical entre
líneas dentro del bloque.

Dependencias: `pandas`, `openpyxl`, `reportlab`
"""

from pathlib import Path
import argparse

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ------------------------------------------------------------
# Rutas y fuentes
# ------------------------------------------------------------
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
FONTS_DIR = SRC_DIR / "fonts"

FONTS = {
    "LeagueSpartan-Bold": FONTS_DIR / "LeagueSpartan-Bold.ttf",
    "LeagueSpartan-Regular": FONTS_DIR / "LeagueSpartan-Regular.ttf",
    "BebasNeue":          FONTS_DIR / "BebasNeue-Regular.ttf",
    "Montserrat-Bold": FONTS_DIR / "Montserrat-Bold.ttf",
}
for name, fpath in FONTS.items():
    if fpath.exists():
        pdfmetrics.registerFont(TTFont(name, str(fpath)))
    else:
        print(f"⚠️  Falta {fpath.name} → se usará Helvetica.")

FN_NAME   = "LeagueSpartan-Bold" if "LeagueSpartan-Bold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
FN_DIGITS = "BebasNeue"          if "BebasNeue"          in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
FN_SYMBOL = "Montserrat-Bold" if "Montserrat-Bold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
FN_CODE   = "LeagueSpartan-Regular" if "LeagueSpartan-Regular" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"

# ------------------------------------------------------------
# Layout parameters
# ------------------------------------------------------------
LINE_SPACING  = 25  # pt entre líneas dentro del bloque
TEXT_OFFSET_X = 0   # desplaza todo el bloque X
TEXT_OFFSET_Y = 0   # desplaza bloque Y (+ arriba, - abajo)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

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

# ------------------------------------------------------------
# Core
# ------------------------------------------------------------

def generate_catalog(images_dir: str | Path, excel_path: str | Path, output_pdf: str | Path = 'catalog.pdf'):
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

        # ---- Calcular área disponible para imagen ----
        text_block_height = LINE_SPACING * 2 + 26  # aprox altura de las 3 líneas
        max_img_h = page_h - 2 * margin - text_block_height - 12  # 12 pt de separación
        max_img_w = page_w - 2 * margin

        img = ImageReader(str(img_path))
        iw, ih = img.getSize()
        scale = min(max_img_w / iw, max_img_h / ih)
        dw, dh = iw * scale, ih * scale
        img_x = (page_w - dw) / 2
        img_y = page_h - margin - dh
        c.drawImage(img, img_x, img_y, dw, dh, preserveAspectRatio=True, mask='auto')

        # ---- Texto debajo de la imagen ----
        base_x = margin + TEXT_OFFSET_X
        base_y = img_y - 12 - TEXT_OFFSET_Y  # 12 pt de padding debajo de la imagen

        c.setFont(FN_NAME, 26)
        c.drawString(base_x, base_y, nombre)

        c.setFont(FN_CODE, 15)
        c.drawString(base_x, base_y - LINE_SPACING, 'cod '+codigo)

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

# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Genera un catálogo con imagen grande y texto debajo.')
    ap.add_argument('images_dir')
    ap.add_argument('excel_path')
    ap.add_argument('-o', '--output', default='catalog.pdf')
    args = ap.parse_args()

    generate_catalog(args.images_dir, args.excel_path, args.output)
