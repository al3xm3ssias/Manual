import os

BASE_DIR = os.path.join("modulos", "documentos")

DIRETORIOS = [
    "Atribuições",
    "Calendario Escolares",
    "Documentos modelo CTARH",
    "Informativos EFE",
    "Leis e Decretos",
    "Modelos de documentos da EFE",
]

def main():
    for nome in DIRETORIOS:
        caminho = os.path.join(BASE_DIR, nome)
        os.makedirs(caminho, exist_ok=True)
        print(f"Criado: {caminho}")

if __name__ == "__main__":
    main()