import os
import base64
from dotenv import load_dotenv
from openai import OpenAI

# Carga tu API key desde .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Lee y codifica tu imagen de prueba
with open("runs/detect/predict/crops/product/EST2507_Página_002.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

# Llamada al endpoint multimodal
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Eres un asistente multimodal experto en catálogos."},
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            {"type": "text", "text": (
                "Extrae un JSON con {nombre, código, precio}. "
                "El nombre es el texto más grande/negrita; ignora la descripción pequeña."
            )}
        ]},
    ],
)
print(response.choices[0].message.content)
