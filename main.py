# ============================
# main.py (en la raíz)
# ============================
"""
Menú para el pipeline completo.
Ejecuta desde la raíz:
    python main.py
"""
import sys
from src.process_catalog_LLM import process_catalog_llm


def main():
    while True:
        print("\n--- Menú Pipeline Catálogos ---")
        print("1) Procesar con GPT-4o Vision")
        print("1) Entrenar GPT-4o Vision")
        print("3) Salir")
        choice = input("Selecciona [1-4]: ")
        if choice == "1":
            # Importar y ejecutar
            process_catalog_llm()
        elif choice == "2":
            # Entrenar
            print("Entrenando GPT-4o Vision...")
        elif choice == "3":
            print("Saliendo...")
            sys.exit(0)
        else:
            print("Opción inválida.")

if __name__ == "__main__":
    main()