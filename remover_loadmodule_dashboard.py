#!/usr/bin/env python3
"""
Remove todas as linhas que contenham `loadModule('dashboard')`
de todos os arquivos .html dentro da pasta `modulos` (recursivamente).

Antes de apagar qualquer coisa, faz backup de cada arquivo alterado
dentro de uma pasta `modulos_backup_<timestamp>` no mesmo nível da
pasta `modulos`.

Uso:
    python remover_loadmodule_dashboard.py

Não é necessário passar nenhum caminho. O script localiza a pasta
`modulos` automaticamente, pois ela deve estar sempre ao lado deste
arquivo .py (dentro da pasta Manual), não importa de onde você execute
o comando no terminal.
"""

import shutil
from pathlib import Path
from datetime import datetime

ALVO = "loadModule('dashboard')"

# Pasta onde este script está salvo (ex: .../SERE/2026/Manual)
PASTA_SCRIPT = Path(__file__).resolve().parent


def processar_arquivo(caminho: Path) -> int:
    """Remove linhas que contenham ALVO. Retorna quantas linhas foram removidas."""
    texto_original = caminho.read_text(encoding="utf-8", errors="ignore")
    linhas = texto_original.splitlines(keepends=True)

    linhas_novas = [linha for linha in linhas if ALVO not in linha]
    removidas = len(linhas) - len(linhas_novas)

    if removidas > 0:
        caminho.write_text("".join(linhas_novas), encoding="utf-8")

    return removidas


def main():
    pasta_modulos = PASTA_SCRIPT / "modulos"

    if not pasta_modulos.exists() or not pasta_modulos.is_dir():
        print(f"ERRO: pasta não encontrada: {pasta_modulos.resolve()}")
        raise SystemExit(1)

    arquivos_html = sorted(pasta_modulos.rglob("*.html"))

    if not arquivos_html:
        print(f"Nenhum arquivo .html encontrado em {pasta_modulos.resolve()}")
        raise SystemExit(0)

    # Pasta de backup, criada ao lado da pasta modulos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_backup = pasta_modulos.parent / f"modulos_backup_{timestamp}"

    print(f"Procurando '{ALVO}' em {len(arquivos_html)} arquivo(s) .html...")
    print(f"Backup será salvo em: {pasta_backup.resolve()}\n")

    total_arquivos_alterados = 0
    total_linhas_removidas = 0

    for arquivo in arquivos_html:
        texto = arquivo.read_text(encoding="utf-8", errors="ignore")
        if ALVO not in texto:
            continue

        # Faz backup preservando a estrutura de subpastas
        caminho_relativo = arquivo.relative_to(pasta_modulos)
        destino_backup = pasta_backup / caminho_relativo
        destino_backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(arquivo, destino_backup)

        removidas = processar_arquivo(arquivo)
        if removidas > 0:
            total_arquivos_alterados += 1
            total_linhas_removidas += removidas
            print(f"  [OK] {caminho_relativo} -> {removidas} linha(s) removida(s)")

    print(f"\nConcluído.")
    print(f"Arquivos alterados: {total_arquivos_alterados}")
    print(f"Linhas removidas no total: {total_linhas_removidas}")
    if total_arquivos_alterados > 0:
        print(f"Backup dos arquivos originais em: {pasta_backup.resolve()}")
    else:
        print("Nenhum arquivo continha a linha procurada.")


if __name__ == "__main__":
    main()