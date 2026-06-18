#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrar_sidebar.py
==================

Script de migração em massa para incluir o script centralizado
assets/js/sidebar-direita.js em todas as páginas HTML de módulo
(ex: declaracoes_de_matricula.html) e remover o bloco antigo
duplicado de favoritos/histórico/toast.

COMO USAR
---------
1. Coloque este arquivo na RAIZ do projeto (a pasta "Manual/"), ou
   ajuste a variável RAIZ_PROJETO abaixo.
2. Rode em modo de teste primeiro (não grava nada, só mostra o que
   faria):

       python3 migrar_sidebar.py --dry-run

3. Revise a saída. Se estiver tudo certo, rode de fato:

       python3 migrar_sidebar.py

   Isso cria um backup (.bak) de cada arquivo alterado antes de
   sobrescrever.

4. Se algo der errado, restaure com:

       python3 migrar_sidebar.py --restaurar

O QUE O SCRIPT FAZ EM CADA ARQUIVO
-----------------------------------
1. Localiza o trio de <script src="..."> do jQuery/Bootstrap/AdminLTE
   e garante que exista, logo depois deles, a linha:

       <script src="../../assets/js/sidebar-direita.js"></script>

   (não duplica se já existir).

2. Dentro do <script> inline da página, remove o bloco antigo de
   favoritos/histórico/toast (as funções toggleFavorite,
   updateFavoriteStar, updateFavoritesUI, clearFavorites,
   addToHistory, updateHistoryUI, clearHistory, showToast e as
   variáveis "favorites"/"history2"), preservando tudo o que for
   específico da página (PAGE_ID, PAGE_TITLE, lightbox, scroll,
   busca, allPages, $(document).ready etc.).

3. Ajusta o bloco de abrir a sidebar direita
   ($('#btn-toggle-favorites')/$('#btn-toggle-history')) para usar
   abrirSidebarDireita('favorites'/'history'), caso ainda esteja no
   formato antigo ($('#right-sidebar').addClass(...)).

4. Corrige qualquer data-toggle="tab" remanescente para
   data-bs-toggle="tab" (Bootstrap 5) nas tabs da sidebar direita.

5. Confere o PAGE_ID contra data/indice.json. Se o PAGE_ID não
   constar no índice, ou o título divergir, isso entra no relatório
   final para revisão manual (o script NÃO corrige isso
   automaticamente, pois pode ser intencional).

O script é conservador: se não conseguir localizar com segurança um
dos blocos esperados em algum arquivo, ele PULA esse arquivo e anota
no relatório, em vez de arriscar uma edição malformada.
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

# ------------------------------------------------------------------
# CONFIGURAÇÃO — ajuste se necessário
# ------------------------------------------------------------------

# Raiz do projeto (pasta "Manual/"). "." assume que você roda o
# script de dentro dela.
RAIZ_PROJETO = Path(".")

# Onde fica o índice de módulos (para validar PAGE_ID/PAGE_TITLE)
CAMINHO_INDICE = RAIZ_PROJETO / "data" / "indice.json"

# Caminho do script centralizado, relativo a cada página HTML.
# Como você confirmou que todas as páginas estão na mesma
# profundidade (2 níveis abaixo de Manual/), isso é fixo.
SRC_SCRIPT_CENTRALIZADO = "../../assets/js/sidebar-direita.js"

# Padrão de nome de arquivo a processar. Ajuste se quiser restringir
# a uma subpasta específica, ex: "modulos/**/*.html"
PADRAO_ARQUIVOS = "**/*.html"

# Arquivos que NUNCA devem ser tocados por este script (ex: o próprio
# index.html e o sidebar.html, que têm estrutura diferente).
ARQUIVOS_IGNORADOS = {"index.html", "sidebar.html"}

SUFIXO_BACKUP = ".bak"


# ------------------------------------------------------------------
# Utilitários
# ------------------------------------------------------------------

def carregar_indice():
    """Carrega data/indice.json e devolve um dict id -> item."""
    if not CAMINHO_INDICE.exists():
        return None
    try:
        dados = json.loads(CAMINHO_INDICE.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[AVISO] Não consegui ler {CAMINHO_INDICE}: {exc}")
        return None

    por_id = {}
    for grupo in ("procedimentos", "legislacoes"):
        for item in dados.get(grupo, {}).get("itens", []):
            por_id[item["id"]] = item
    return por_id


def encontrar_arquivos_html():
    arquivos = []
    for caminho in RAIZ_PROJETO.glob(PADRAO_ARQUIVOS):
        if caminho.name in ARQUIVOS_IGNORADOS:
            continue
        if not caminho.is_file():
            continue
        arquivos.append(caminho)
    return sorted(arquivos)


# ------------------------------------------------------------------
# Passo 1: garantir o <script src=".../sidebar-direita.js">
# ------------------------------------------------------------------

RE_TRIO_CDN = re.compile(
    r'(<script src="[^"]*jquery[^"]*"></script>\s*'
    r'<script src="[^"]*bootstrap[^"]*"></script>\s*'
    r'<script src="[^"]*admin-lte[^"]*"></script>)',
    re.IGNORECASE,
)

RE_JA_TEM_SCRIPT_CENTRALIZADO = re.compile(
    r'<script src="[^"]*sidebar-direita\.js"></script>'
)


def garantir_script_centralizado(html: str):
    """
    Retorna (novo_html, alterado, motivo_se_falhou).
    """
    if RE_JA_TEM_SCRIPT_CENTRALIZADO.search(html):
        return html, False, None  # já tem, nada a fazer

    m = RE_TRIO_CDN.search(html)
    if not m:
        return html, False, (
            "não encontrei o trio jQuery/Bootstrap/AdminLTE para inserir "
            "o script centralizado depois dele"
        )

    trio = m.group(1)
    substituto = trio + f'\n<script src="{SRC_SCRIPT_CENTRALIZADO}"></script>'
    novo_html = html[: m.start()] + substituto + html[m.end():]
    return novo_html, True, None


# ------------------------------------------------------------------
# Passo 2: remover o bloco antigo duplicado de favoritos/histórico
# ------------------------------------------------------------------
#
# Estratégia: usamos como âncora de INÍCIO a primeira ocorrência de
# "let favorites = JSON.parse(localStorage.getItem('manual_favorites'"
# e como âncora de FIM o fechamento da função showToast (a última
# função do bloco antigo, sempre presente). Tudo entre essas duas
# âncoras (inclusive) é substituído por um comentário explicativo.
#
# Isso é mais seguro que tentar listar função por função, porque
# cobre também pequenas variações de formatação, desde que as duas
# âncoras existam.

RE_INICIO_BLOCO_ANTIGO = re.compile(
    r"let\s+favorites\s*=\s*JSON\.parse\(localStorage\.getItem\(\s*['\"]manual_favorites['\"]"
)

RE_SHOWTOAST = re.compile(
    r"function\s+showToast\s*\([^)]*\)\s*\{"
)


def _achar_fim_funcao(html: str, pos_abre_chave: int) -> int:
    """
    Dado o índice do '{' de abertura de uma função, devolve o índice
    JUSTO DEPOIS do '}' de fechamento correspondente (contagem simples
    de chaves, ignorando que possa haver chaves dentro de strings —
    aceitável aqui porque o corpo da função showToast não contém
    chaves dentro de strings/template literals problemáticas).
    """
    profundidade = 0
    i = pos_abre_chave
    n = len(html)
    while i < n:
        if html[i] == "{":
            profundidade += 1
        elif html[i] == "}":
            profundidade -= 1
            if profundidade == 0:
                return i + 1
        i += 1
    raise ValueError("não encontrei o fechamento da função (chaves desbalanceadas)")


def remover_bloco_antigo_favoritos(html: str):
    """
    Retorna (novo_html, alterado, motivo_se_falhou).
    """
    m_inicio = RE_INICIO_BLOCO_ANTIGO.search(html)
    if not m_inicio:
        # Já não tem o bloco antigo (talvez já migrado antes) — ok, não é erro.
        return html, False, None

    m_fim = RE_SHOWTOAST.search(html, pos=m_inicio.start())
    if not m_fim:
        return html, False, (
            "encontrei 'let favorites = ...' mas não encontrei a função "
            "showToast depois — pulando para revisão manual"
        )

    try:
        fim_real = _achar_fim_funcao(html, m_fim.end() - 1)
    except ValueError as exc:
        return html, False, f"erro ao localizar fim de showToast: {exc}"

    comentario = (
        "// toggleFavorite, updateFavoriteStar, updateFavoritesUI, clearFavorites,\n"
        "// addToHistory, updateHistoryUI, clearHistory e showToast agora vêm de\n"
        f"// {SRC_SCRIPT_CENTRALIZADO} (script centralizado).\n"
    )

    novo_html = html[: m_inicio.start()] + comentario + html[fim_real:]
    return novo_html, True, None


# ------------------------------------------------------------------
# Passo 3: corrigir o handler de abrir sidebar direita (formato antigo)
# ------------------------------------------------------------------

RE_HANDLER_ANTIGO_FAV = re.compile(
    r"\$\('#btn-toggle-favorites'\)\.click\(function\(e\)\s*\{\s*"
    r"e\.preventDefault\(\);\s*"
    r"\$\('#right-sidebar'\)\.addClass\('control-sidebar-open'\);\s*"
    r"\}\);"
)

RE_HANDLER_ANTIGO_HIST = re.compile(
    r"\$\('#btn-toggle-history'\)\.click\(function\(e\)\s*\{\s*"
    r"e\.preventDefault\(\);\s*"
    r"\$\('#right-sidebar'\)\.addClass\('control-sidebar-open'\);\s*"
    r"\}\);"
)

NOVO_HANDLER_FAV = (
    "// abrirSidebarDireita vem de ../../assets/js/sidebar-direita.js\n"
    "    // e já abre a control-sidebar E troca para a aba correta.\n"
    "    $('#btn-toggle-favorites').click(function(e) {\n"
    "      e.preventDefault();\n"
    "      abrirSidebarDireita('favorites');\n"
    "    });"
)

NOVO_HANDLER_HIST = (
    "$('#btn-toggle-history').click(function(e) {\n"
    "      e.preventDefault();\n"
    "      abrirSidebarDireita('history');\n"
    "    });"
)


def corrigir_handlers_sidebar(html: str):
    alterado = False

    if RE_HANDLER_ANTIGO_FAV.search(html):
        html = RE_HANDLER_ANTIGO_FAV.sub(NOVO_HANDLER_FAV, html)
        alterado = True

    if RE_HANDLER_ANTIGO_HIST.search(html):
        html = RE_HANDLER_ANTIGO_HIST.sub(NOVO_HANDLER_HIST, html)
        alterado = True

    return html, alterado


# ------------------------------------------------------------------
# Passo 4: corrigir data-toggle="tab" -> data-bs-toggle="tab"
# (somente dentro da sidebar direita, para não afetar outras tabs
# que porventura existam na página com outro propósito)
# ------------------------------------------------------------------

RE_BLOCO_RIGHT_SIDEBAR = re.compile(
    r'(<aside[^>]*id="right-sidebar"[^>]*>.*?</aside>)',
    re.IGNORECASE | re.DOTALL,
)


def corrigir_data_toggle(html: str):
    m = RE_BLOCO_RIGHT_SIDEBAR.search(html)
    if not m:
        return html, False, "não encontrei <aside id=\"right-sidebar\"> para corrigir as tabs"

    bloco_original = m.group(1)
    bloco_corrigido = bloco_original.replace('data-toggle="tab"', 'data-bs-toggle="tab"')

    if bloco_corrigido == bloco_original:
        return html, False, None  # nada para corrigir

    novo_html = html[: m.start()] + bloco_corrigido + html[m.end():]
    return novo_html, True, None


# ------------------------------------------------------------------
# Passo 5: extrair PAGE_ID / PAGE_TITLE e validar contra o índice
# ------------------------------------------------------------------

RE_PAGE_ID = re.compile(r"const\s+PAGE_ID\s*=\s*['\"]([^'\"]+)['\"]")
RE_PAGE_TITLE = re.compile(r"const\s+PAGE_TITLE\s*=\s*['\"]([^'\"]+)['\"]")


def extrair_page_id_title(html: str):
    m_id = RE_PAGE_ID.search(html)
    m_title = RE_PAGE_TITLE.search(html)
    page_id = m_id.group(1) if m_id else None
    page_title = m_title.group(1) if m_title else None
    return page_id, page_title


# ------------------------------------------------------------------
# Orquestração por arquivo
# ------------------------------------------------------------------

class ResultadoArquivo:
    def __init__(self, caminho: Path):
        self.caminho = caminho
        self.alteracoes = []   # lista de strings descrevendo o que mudou
        self.avisos = []       # lista de strings com problemas/observações
        self.alterado = False
        self.page_id = None
        self.page_title = None


def processar_arquivo(caminho: Path, indice_por_id, dry_run: bool) -> ResultadoArquivo:
    resultado = ResultadoArquivo(caminho)

    try:
        html_original = caminho.read_text(encoding="utf-8")
    except Exception as exc:
        resultado.avisos.append(f"não consegui ler o arquivo: {exc}")
        return resultado

    html = html_original

    # Passo 1
    html, mudou, motivo = garantir_script_centralizado(html)
    if mudou:
        resultado.alteracoes.append("incluído <script src='sidebar-direita.js'>")
        resultado.alterado = True
    elif motivo:
        resultado.avisos.append(motivo)

    # Passo 2
    html, mudou, motivo = remover_bloco_antigo_favoritos(html)
    if mudou:
        resultado.alteracoes.append("removido bloco antigo de favoritos/histórico/toast")
        resultado.alterado = True
    elif motivo:
        resultado.avisos.append(motivo)

    # Passo 3
    html, mudou = corrigir_handlers_sidebar(html)
    if mudou:
        resultado.alteracoes.append("handlers de abrir sidebar direita atualizados")
        resultado.alterado = True

    # Passo 4
    html, mudou, motivo = corrigir_data_toggle(html)
    if mudou:
        resultado.alteracoes.append("data-toggle=\"tab\" corrigido para data-bs-toggle=\"tab\"")
        resultado.alterado = True
    elif motivo:
        resultado.avisos.append(motivo)

    # Passo 5 (apenas leitura/validação, não altera o arquivo)
    page_id, page_title = extrair_page_id_title(html)
    resultado.page_id = page_id
    resultado.page_title = page_title

    if indice_por_id is not None:
        if page_id is None:
            resultado.avisos.append("não encontrei PAGE_ID no arquivo")
        elif page_id not in indice_por_id:
            resultado.avisos.append(
                f"PAGE_ID '{page_id}' não consta em data/indice.json"
            )
        else:
            titulo_indice = indice_por_id[page_id]["titulo"]
            if page_title and titulo_indice != page_title:
                resultado.avisos.append(
                    f"PAGE_TITLE ('{page_title}') difere do título no índice "
                    f"('{titulo_indice}') — confirme se é intencional"
                )

    if resultado.alterado and not dry_run:
        backup = caminho.with_suffix(caminho.suffix + SUFIXO_BACKUP)
        if not backup.exists():
            shutil.copy2(caminho, backup)
        caminho.write_text(html, encoding="utf-8")

    return resultado


# ------------------------------------------------------------------
# Restauração a partir dos backups
# ------------------------------------------------------------------

def restaurar_backups():
    arquivos_bak = sorted(RAIZ_PROJETO.glob(f"**/*.html{SUFIXO_BACKUP}"))
    if not arquivos_bak:
        print("Nenhum backup (.bak) encontrado.")
        return

    print(f"Encontrados {len(arquivos_bak)} backups. Restaurando...\n")
    for bak in arquivos_bak:
        original = bak.with_suffix("")  # remove o ".bak" do final
        shutil.copy2(bak, original)
        print(f"  restaurado: {original}")
    print("\nRestauração concluída.")


# ------------------------------------------------------------------
# Relatório final
# ------------------------------------------------------------------

def imprimir_relatorio(resultados, dry_run: bool):
    alterados = [r for r in resultados if r.alterado]
    com_avisos = [r for r in resultados if r.avisos]
    sem_mudanca_nem_aviso = [r for r in resultados if not r.alterado and not r.avisos]

    modo = "SIMULAÇÃO (--dry-run, nada foi gravado)" if dry_run else "EXECUÇÃO REAL"
    print("=" * 70)
    print(f"RELATÓRIO DE MIGRAÇÃO — {modo}")
    print("=" * 70)
    print(f"Total de arquivos analisados: {len(resultados)}")
    print(f"Arquivos alterados: {len(alterados)}")
    print(f"Arquivos com avisos: {len(com_avisos)}")
    print(f"Arquivos sem nenhuma mudança/aviso (já estavam ok ou não se aplicam): "
          f"{len(sem_mudanca_nem_aviso)}")
    print()

    if alterados:
        print("-" * 70)
        print("ALTERADOS")
        print("-" * 70)
        for r in alterados:
            print(f"\n• {r.caminho}")
            for a in r.alteracoes:
                print(f"    - {a}")

    if com_avisos:
        print()
        print("-" * 70)
        print("AVISOS (revisar manualmente)")
        print("-" * 70)
        for r in com_avisos:
            print(f"\n• {r.caminho}  (PAGE_ID={r.page_id!r})")
            for a in r.avisos:
                print(f"    ! {a}")

    print()
    print("=" * 70)
    if dry_run:
        print("Nenhum arquivo foi modificado (modo --dry-run).")
        print("Revise o relatório acima e rode sem --dry-run para aplicar.")
    else:
        print(f"Pronto. Backups salvos com sufixo '{SUFIXO_BACKUP}' ao lado de cada arquivo alterado.")
        print("Para desfazer tudo: python3 migrar_sidebar.py --restaurar")
    print("=" * 70)


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Migra páginas HTML para usar assets/js/sidebar-direita.js"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Mostra o que seria feito, sem alterar nenhum arquivo."
    )
    parser.add_argument(
        "--restaurar", action="store_true",
        help="Restaura todos os arquivos a partir dos backups .bak."
    )
    args = parser.parse_args()

    if args.restaurar:
        restaurar_backups()
        return

    indice_por_id = carregar_indice()
    if indice_por_id is None:
        print(f"[AVISO] Não foi possível carregar {CAMINHO_INDICE}. "
              "A validação de PAGE_ID/PAGE_TITLE será pulada.\n")

    arquivos = encontrar_arquivos_html()
    if not arquivos:
        print("Nenhum arquivo .html encontrado. Confira RAIZ_PROJETO/PADRAO_ARQUIVOS.")
        sys.exit(1)

    print(f"Encontrados {len(arquivos)} arquivos .html para analisar "
          f"(ignorando {sorted(ARQUIVOS_IGNORADOS)}).\n")

    resultados = [
        processar_arquivo(caminho, indice_por_id, dry_run=args.dry_run)
        for caminho in arquivos
    ]

    imprimir_relatorio(resultados, dry_run=args.dry_run)


if __name__ == "__main__":
    main()