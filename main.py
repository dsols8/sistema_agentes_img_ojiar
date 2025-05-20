# ============================
# main.py
# ============================
"""
Mini menú para elegir la fase del pipeline:
1) Entrenar YOLO
2) Predecir YOLO
3) Procesar con GPT-4o Vision
4) Salir
Ejecuta desde la raíz:
  python src/main.py
"""
import sys
from train_yolo import train_yolo
from src.preditc_yolo import predict_yolo
from src.process_catalog_LLM import sys as proc_module

def main():
    while True:
        print("\n--- Pipeline de Extracción ---")
        print("1) Entrenar YOLO")
        print("2) Predecir con YOLO")
        print("3) Procesar recortes con GPT-4o Vision")
        print("4) Salir")
        choice = input("Selecciona opción [1-4]: ")
        if choice == "1":
            train_yolo()
        elif choice == "2":
            predict_yolo()
        elif choice == "3":
            proc_module
        elif choice == "4":
            print("Saliendo...")
            sys.exit(0)
        else:
            print("Opción inválida.")

if __name__ == "__main__":
    main()
