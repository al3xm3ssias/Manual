#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerar_indice_documentos.py

Varre a pasta modulos/documentos/ e gera data/documentos.json com a lista de
arquivos agrupados por categoria (cada subpasta de 1º nível = 1 categoria).

Uso:
    python gerar_indice_documentos.py

Saída:
    data/documentos.json

Regras:
- Ignora arquivos terminados em .bak (e qualquer arquivo oculto começando com '.').
- Categoria = nome da subpasta direta dentro de modulos/documentos/.
- Cada arquivo recebe: nome, caminho relativo (url), extensão, tipo (pdf/word/excel/outro),
  tamanho em bytes e tamanho formatado (KB/MB).
- Ordena categorias e arquivos por nome (ordem alfabética, sensível a acentos via locale simples).
"""

import json
import os
import sys
from pathlib import Path

# Raiz do projeto = pasta onde este script está (ajuste se mover o script de lugar)
RAIZ = Path(__file__).resolve().parent
PASTA_DOCUMENTOS = RAIZ / "modulos" / "documentos"
SAIDA_JSON = RAIZ / "data" / "documentos.json"

# Extensões ignoradas completamente (não aparecem na listagem)
EXTENSOES_IGNORADAS = {".bak"}

# Mapeamento de extensão -> tipo lógico (usado pra escolher ícone/comportamento no front-end)
TIPOS_POR_EXTENSAO = {
    ".pdf": "pdf",
    ".doc": "word",
    ".docx": "word",
    ".odt": "word",
    ".xls": "excel",
    ".xlsx": "excel",
    ".ods": "excel",
    ".csv": "excel",
}


def formatar_tamanho(tamanho_bytes: int) -> str:
    """Converte bytes em string legível (KB/MB)."""
    if tamanho_bytes < 1024:
        return f"{tamanho_bytes} B"
    elif tamanho_bytes < 1024 * 1024:
        return f"{tamanho_bytes / 1024:.0f} KB"
    else:
        return f"{tamanho_bytes / (1024 * 1024):.1f} MB"


def deve_ignorar(caminho: Path) -> bool:
    """Retorna True se o arquivo deve ser ignorado (.bak, oculto, etc.)."""
    nome = caminho.name
    if nome.startswith("."):
        return True
    # Cobre tanto "arquivo.pdf.bak" quanto "arquivo.bak"
    if caminho.suffix.lower() in EXTENSOES_IGNORADAS:
        return True
    return False


def montar_url_relativa(caminho_arquivo: Path) -> str:
    """
    Monta o caminho relativo (a partir da raiz do site) usado como href no HTML.
    Ex: modulos/documentos/Atribuições/01-ARQUIVO.docx
    Espaços e caracteres especiais NÃO são url-encoded aqui de propósito:
    o navegador resolve normalmente em href="..."; encoding fica a cargo do
    front-end se for necessário (ver função jsEncodeURI no HTML gerado).
    """
    relativo = caminho_arquivo.relative_to(RAIZ)
    # Sempre usar barras normais (/) mesmo em ambientes Windows
    return str(relativo).replace(os.sep, "/")


def gerar_indice():
    if not PASTA_DOCUMENTOS.exists():
        print(f"[ERRO] Pasta não encontrada: {PASTA_DOCUMENTOS}", file=sys.stderr)
        sys.exit(1)

    categorias = []
    total_arquivos = 0
    total_ignorados = 0

    # Cada subpasta de 1º nível dentro de modulos/documentos/ é uma categoria
    subpastas = sorted(
        [p for p in PASTA_DOCUMENTOS.iterdir() if p.is_dir()],
        key=lambda p: p.name.lower()
    )

    for pasta_categoria in subpastas:
        arquivos_categoria = []

        # Percorre arquivos diretamente dentro da categoria (não recursivo em subníveis)
        candidatos = sorted(
            [f for f in pasta_categoria.iterdir() if f.is_file()],
            key=lambda f: f.name.lower()
        )

        for arquivo in candidatos:
            if deve_ignorar(arquivo):
                total_ignorados += 1
                continue

            extensao = arquivo.suffix.lower()
            tipo = TIPOS_POR_EXTENSAO.get(extensao, "outro")
            try:
                tamanho_bytes = arquivo.stat().st_size
            except OSError:
                tamanho_bytes = 0

            arquivos_categoria.append({
                "nome": arquivo.stem,                          # nome sem extensão
                "nome_completo": arquivo.name,                 # nome com extensão
                "extensao": extensao.lstrip("."),               # ex: "pdf", "docx"
                "tipo": tipo,                                    # pdf | word | excel | outro
                "url": montar_url_relativa(arquivo),
                "tamanho_bytes": tamanho_bytes,
                "tamanho_legivel": formatar_tamanho(tamanho_bytes),
            })
            total_arquivos += 1

        # Só inclui a categoria se tiver pelo menos 1 arquivo válido
        if arquivos_categoria:
            categorias.append({
                "categoria": pasta_categoria.name,
                "slug": pasta_categoria.name.lower()
                    .replace(" ", "-")
                    .replace("ç", "c")
                    .replace("ã", "a")
                    .replace("á", "a")
                    .replace("é", "e")
                    .replace("í", "i")
                    .replace("ó", "o"),
                "total": len(arquivos_categoria),
                "arquivos": arquivos_categoria,
            })

    indice = {
        "gerado_em": _agora_iso(),
        "total_categorias": len(categorias),
        "total_arquivos": total_arquivos,
        "total_ignorados": total_ignorados,
        "categorias": categorias,
    }

    SAIDA_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(SAIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=2)

    print(f"[OK] Índice gerado: {SAIDA_JSON}")
    print(f"     Categorias: {len(categorias)}")
    print(f"     Arquivos incluídos: {total_arquivos}")
    print(f"     Arquivos ignorados (.bak/ocultos): {total_ignorados}")


def _agora_iso() -> str:
    from datetime import datetime
    return datetime.now().isoformat(timespec="seconds")


if __name__ == "__main__":
    gerar_indice()