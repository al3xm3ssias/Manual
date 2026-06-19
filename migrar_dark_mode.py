#!/usr/bin/env python3
"""
aplicar_dark_mode.py
---------------------
Injeta o modo escuro (assets/css/dark-mode.css + assets/js/dark-mode.js)
em TODOS os arquivos .html do Manual, calculando automaticamente o
caminho relativo correto para cada arquivo (independente da profundidade
de pastas: index.html, modulos/sere/abono_de_faltas.html, etc.).

Uso:
    1. Copie dark-mode.css para  Manual/assets/css/dark-mode.css
    2. Copie dark-mode.js  para  Manual/assets/js/dark-mode.js
    3. Rode este script a partir da raiz do projeto Manual:
         python migrar_dark_mode.py
       (ou indique a raiz manualmente: python migrar_dark_mode.py "C:\caminho\Manual")

O script:
  - Ignora arquivos .bak
  - É idempotente (pode rodar várias vezes sem duplicar as tags)
  - Cria um backup .bak antes de alterar cada arquivo (igual ao padrão
    já usado em migrar_sidebar.py)
"""

import os
import sys
import re
import shutil

MARCADOR_CSS = "dark-mode.css"
MARCADOR_JS = "dark-mode.js"


def calcular_prefixo_relativo(caminho_arquivo, raiz):
    """Calcula quantos '../' são necessários para chegar na raiz do Manual."""
    pasta_arquivo = os.path.dirname(os.path.abspath(caminho_arquivo))
    raiz_abs = os.path.abspath(raiz)
    rel = os.path.relpath(raiz_abs, pasta_arquivo)
    if rel == ".":
        return ""
    return rel.replace("\\", "/") + "/"


def processar_arquivo(caminho, raiz):
    with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
        conteudo = f.read()

    if MARCADOR_CSS in conteudo and MARCADOR_JS in conteudo:
        return False  # já migrado

    prefixo = calcular_prefixo_relativo(caminho, raiz)
    link_css = f'  <link rel="stylesheet" href="{prefixo}assets/css/dark-mode.css">\n'
    script_js = f'  <script src="{prefixo}assets/js/dark-mode.js"></script>\n'

    alterado = False

    # Insere o CSS logo antes de </head> (se ainda não existir)
    if MARCADOR_CSS not in conteudo:
        if re.search(r"</head>", conteudo, re.IGNORECASE):
            conteudo = re.sub(
                r"</head>",
                link_css + "</head>",
                conteudo,
                count=1,
                flags=re.IGNORECASE,
            )
            alterado = True
        else:
            print(f"  [AVISO] {caminho}: tag </head> não encontrada, CSS não inserido.")

    # Insere o JS logo no início do <body ...> (aplica tema cedo, evita flash)
    if MARCADOR_JS not in conteudo:
        match_body = re.search(r"(<body[^>]*>)", conteudo, re.IGNORECASE)
        if match_body:
            conteudo = (
                conteudo[: match_body.end()]
                + "\n"
                + script_js
                + conteudo[match_body.end():]
            )
            alterado = True
        else:
            print(f"  [AVISO] {caminho}: tag <body> não encontrada, JS não inserido.")

    if alterado:
        shutil.copy2(caminho, caminho + ".bak")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)

    return alterado


def main():
    raiz = sys.argv[1] if len(sys.argv) > 1 else "."
    raiz = os.path.abspath(raiz)

    if not os.path.isdir(raiz):
        print(f"Pasta não encontrada: {raiz}")
        sys.exit(1)

    print(f"Procurando arquivos .html em: {raiz}\n")

    total = 0
    migrados = 0

    for dirpath, dirnames, filenames in os.walk(raiz):
        for nome in filenames:
            if not nome.lower().endswith(".html"):
                continue
            if nome.lower().endswith(".bak"):
                continue
            caminho = os.path.join(dirpath, nome)
            total += 1
            try:
                if processar_arquivo(caminho, raiz):
                    migrados += 1
                    print(f"  [OK] {os.path.relpath(caminho, raiz)}")
                else:
                    print(f"  [--] {os.path.relpath(caminho, raiz)} (já migrado)")
            except Exception as e:
                print(f"  [ERRO] {caminho}: {e}")

    print(f"\nConcluído. {migrados} de {total} arquivos .html foram atualizados.")
    print("Backups .bak foram criados para cada arquivo alterado.")


if __name__ == "__main__":
    main()