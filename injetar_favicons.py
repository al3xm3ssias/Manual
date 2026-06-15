#!/usr/bin/env python3
"""
injetar_favicons.py
─────────────────────────────────────────────────────────────────────
Insere as tags de favicon no <head> de todos os .html dentro de
modulos/ (e subpastas), pulando arquivos que já as possuem.

Execute dentro da pasta Manual/:
    python3 injetar_favicons.py
─────────────────────────────────────────────────────────────────────
"""

from pathlib import Path

# ─── CONFIGURAÇÃO ─────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
MODULOS_DIR = BASE_DIR / "modulos"

BLOCO_FAVICON = """\
  <link rel="icon" href="/Manual/assets/img/favicon.ico" sizes="any">
  <link rel="icon" type="image/png" sizes="32x32" href="/Manual/assets/img/favicon-32.png">
  <link rel="apple-touch-icon" href="/Manual/assets/img/apple-touch-icon.png">"""

# Trecho único para checar se o bloco já existe (evita duplicatas)
MARCA = 'href="/Manual/assets/img/favicon.ico"'


# ─── PROCESSAMENTO ────────────────────────────────────────────────────────────

def injetar(arquivo: Path) -> str:
    """
    Retorna:
      "injetado"  – bloco inserido com sucesso
      "já tinha"  – arquivo já continha o favicon
      "sem head"  – </head> não encontrado no arquivo
    """
    conteudo = arquivo.read_text(encoding="utf-8")

    if MARCA in conteudo:
        return "já tinha"

    # Insere imediatamente antes de </head> (case-insensitive)
    tag_close = conteudo.lower().find("</head>")
    if tag_close == -1:
        return "sem head"

    novo = conteudo[:tag_close] + BLOCO_FAVICON + "\n" + conteudo[tag_close:]
    arquivo.write_text(novo, encoding="utf-8")
    return "injetado"


def main() -> None:
    sep = "─" * 60
    print(sep)
    print("  Injetor de Favicons — Manual do Escriturário")
    print(sep)
    print(f"\n  Pasta   : {MODULOS_DIR}\n")

    arquivos = sorted(MODULOS_DIR.rglob("*.html"))
    if not arquivos:
        print("  ℹ  Nenhum .html encontrado em modulos/")
        return

    contadores = {"injetado": 0, "já tinha": 0, "sem head": 0}

    for arq in arquivos:
        resultado = injetar(arq)
        contadores[resultado] += 1
        icone = {"injetado": "✔", "já tinha": "–", "sem head": "⚠"}[resultado]
        rel   = arq.relative_to(BASE_DIR)
        print(f"  {icone}  [{resultado:<9}]  {rel}")

    print(f"\n{sep}")
    print(f"  ✅  Concluído!")
    print(f"      {contadores['injetado']:>3} arquivo(s) atualizados")
    print(f"      {contadores['já tinha']:>3} já tinham favicon")
    print(f"      {contadores['sem head']:>3} sem </head> (ignorados)")
    print(sep)


if __name__ == "__main__":
    main()