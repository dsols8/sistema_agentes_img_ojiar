import os
from PIL import Image
import glob
import openai

# Coloca aquí tu API Key
openai.api_key = "TU_API_KEY"


# Carpeta de entrada
INPUT_FOLDER = 'input_imagenes/'

def obtener_imagenes(folder):
    extensiones_validas = ['*.jpg', '*.jpeg', '*.png']
    imagenes = []
    for ext in extensiones_validas:
        imagenes.extend(glob.glob(os.path.join(folder, ext)))
    return imagenes

def main():
    imagenes = obtener_imagenes(INPUT_FOLDER)

    if not imagenes:
        print("No se encontraron imágenes en la carpeta.")
        return

    print(f"Total de imágenes encontradas: {len(imagenes)}")

    for i, img_path in enumerate(imagenes):
        print(f"[{i+1}] {os.path.basename(img_path)}")

        # Mostrar la primera imagen como validación
        if i == 0:
            img = Image.open(img_path)
            img.show()

if __name__ == '__main__':
    main()
