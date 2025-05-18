from ultralytics import YOLO
from pathlib import Path
import pytesseract, re, openpyxl, cv2

MODEL_PATH = r"../runs/detect/producto_v3/weights/best.pt"
IMG_DIR = Path("../input_imagenes")
EXCEL_FILE = "productos.xlsx"

detector = YOLO(MODEL_PATH)
wb = openpyxl.Workbook()
ws = wb.active
ws.append(["Nombre", "Código", "Precio", "Página", "Archivo"])

for img_path in IMG_DIR.glob("*.jpg"):
    page = int(re.findall(r"(\d+)", img_path.stem)[-1])
    img = cv2.imread(str(img_path))

    boxes = detector(img_path, conf=0.05)[0].boxes.xyxy.cpu().numpy()
    if not len(boxes):
        boxes = [[0, 0, img.shape[1], img.shape[0]]]

    for x1, y1, x2, y2 in boxes:
        crop = img[int(y1):int(y2), int(x1):int(x2)]
        text = pytesseract.image_to_string(crop, lang="spa")

        nombre = re.search(r"^[A-ZÁÉÍÓÚ][^\n]{3,}", text, re.M)
        codigo = re.search(r"\b\d{5}\b", text)
        precio = re.search(r"\b[\d.,]+\b", text)

        ws.append([
            nombre.group(0).strip() if nombre else "",
            codigo.group(0) if codigo else "",
            precio.group(0).replace(".", "").replace(",", "") if precio else "",
            page,
            img_path.name
        ])

wb.save(EXCEL_FILE)
print(f"Generado {EXCEL_FILE} con {ws.max_row-1} filas")

