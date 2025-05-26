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
from src.train_LLM import train_llm


def main():
    while True:
        print("\n--- Menú Pipeline Catálogos ---")
        print("1) Procesar con GPT-4o Vision")
        print("2) Entrenar GPT-4o Vision")
        print("3) Salir")
        choice = input("Selecciona [1-3]: ")
        if choice == "1":
            # Importar y ejecutar
            while True:
                print("\n--- Selecciona un catálogo: ---")
                print("1) Estilos")
                print("2) Estilos Ofertas")
                print("3) Oriflame")
                print("4) Volver")
                choice2 = input("Selecciona [1-4]: ")
                if choice2 == "1":
                    process_catalog_llm("input_imagenes/Estilos", "estilos")
                elif choice2 == "2":
                    process_catalog_llm("input_imagenes/Estilos_Ofertas", "estilos_ofertas")
                elif choice2 == "3":
                    process_catalog_llm("input_imagenes/Oriflame", "oriflame")
                elif choice2 == "4":
                    print("Volviendo...")
                    break
                else:
                    print("Opción inválida.")
                    
        elif choice == "2":
            # Entrenar
            # while True:
            #     print("\n--- Selecciona un catálogo: ---")
            #     print("1) Estilos")
            #     print("2) Estilos Ofertas")
            #     print("3) Oriflame")
            #     print("4) Volver")
            #     choice2 = input("Selecciona [1-4]: ")
            #     if choice2 == "1":
            #         train_llm("excel/estilos", "estilos_arreglado.xlsx")
            #     elif choice2 == "2":
            #         train_llm("excel/estilos_ofertas", "estilos_ofertas_arreglado.xlsx")
            #     elif choice2 == "3":
            #         train_llm("excel/oriflame", "oriflame_arreglado.xlsx")
            #     elif choice2 == "4":
            #         print("Volviendo...")
            #         break
            #     else:
            #         print("Opción inválida.")
            print("\n--- Entrenamiento no implementado aún ---")
        elif choice == "3":
            print("Saliendo...")
            sys.exit(0)
        else:
            print("Opción inválida.")

if __name__ == "__main__":
    main()