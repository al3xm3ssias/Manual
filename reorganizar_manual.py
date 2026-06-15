#!/usr/bin/env python3
"""
reorganizar_manual.py
─────────────────────────────────────────────────────────────────────
Move arquivos de modulos/procedimentos/ para pastas temáticas,
descobrindo automaticamente a pasta de destino de cada arquivo
pela seção do sidebar.html onde o link aparece.

Lógica de mapeamento automático (por seção <li has-treeview>):
  1. Coleta links filhos já resolvidos (matricula/, sere/, sei/ …)
     → vota na pasta mais frequente entre os irmãos ("pasta dominante")
  2. Links que ainda apontam para procedimentos/ recebem essa pasta
  3. Se a seção não tem irmãos resolvidos, tenta inferir pelo título
     da seção via palavras-chave; se ainda assim falhar, avisa.

Execute dentro da pasta Manual/:
    python3 reorganizar_manual.py
─────────────────────────────────────────────────────────────────────
"""

import re
import shutil
from collections import Counter
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    raise SystemExit("❌  Instale beautifulsoup4:  pip install beautifulsoup4")

# ─── CONFIGURAÇÃO ─────────────────────────────────────────────────────────────
BASE_DIR          = Path(__file__).parent
MODULOS_DIR       = BASE_DIR / "modulos"
PROCEDIMENTOS_DIR = MODULOS_DIR / "procedimentos"
SIDEBAR_FILE      = BASE_DIR / "sidebar.html"

# Pastas temáticas reconhecidas (subpastas de modulos/ que não são "procedimentos")
PASTAS_TEMATICAS = {"matricula", "sere", "sei", "servidores", "legislacao"}

# Aceita /Manual/modulos/<pasta>/<arquivo>.html  ou  /modulos/<pasta>/<arquivo>.html
RE_MODULOS = re.compile(
    r"/(?:[^/]+/)?modulos/([^/]+)/([^/?#]+\.html)$",
    re.IGNORECASE,
)

# Fallback por palavras-chave no título da seção, quando não há irmãos resolvidos
PALAVRAS_CHAVE: list[tuple[list[str], str]] = [
    (["matrícula", "matricula", "transferência", "transferencia", "documento sere"],  "matricula"),
    (["sere", "rco", "cadastro", "censo", "chamada", "letivo", "editar"],            "sere"),
    (["sei", "processo", "cota"],                                                     "sei"),
    (["servidor", "justificativa", "quinzenal", "atestado", "declaração", "cat",
      "compensação", "vale transporte", "ficha", "carta"],                            "servidores"),
    (["legislação", "legislacao", "lei", "progressão"],                               "legislacao"),
]


# ─── MAPEAMENTO AUTOMÁTICO ────────────────────────────────────────────────────

def _inferir_por_titulo(titulo: str) -> str | None:
    """Tenta deduzir a pasta pelo título da seção usando palavras-chave."""
    titulo_lower = titulo.lower()
    for palavras, pasta in PALAVRAS_CHAVE:
        if any(p in titulo_lower for p in palavras):
            return pasta
    return None


def construir_mapeamento(sidebar_path: Path) -> dict[str, str]:
    """
    Lê o sidebar.html e devolve:
        { "nome_do_arquivo.html": "pasta_destino" }

    Apenas arquivos atualmente listados como procedimentos/ são incluídos.
    A pasta destino é inferida pela seção onde o link aparece.
    """
    if not sidebar_path.exists():
        raise FileNotFoundError(f"sidebar.html não encontrado em {sidebar_path}")

    soup = BeautifulSoup(sidebar_path.read_text(encoding="utf-8"), "html.parser")
    mapeamento: dict[str, str] = {}

    for secao in soup.select("li.has-treeview"):
        # Título da seção (texto do link pai)
        titulo_tag = secao.select_one(":scope > a > p")
        titulo = titulo_tag.get_text(strip=True) if titulo_tag else ""
        # Remove o ícone de seta que fica dentro do <p>
        titulo = re.sub(r"\s*<.*", "", titulo).strip()

        links = secao.select("ul.nav-treeview a[href]")

        votos: list[str]    = []
        pendentes: list[str] = []

        for a in links:
            href = a.get("href", "")
            m = RE_MODULOS.match(href)
            if not m:
                continue
            pasta, arquivo = m.group(1), m.group(2)

            if pasta in PASTAS_TEMATICAS:
                votos.append(pasta)
            elif pasta == "procedimentos":
                pendentes.append(arquivo)

        if not pendentes:
            continue

        # 1ª escolha: pasta mais frequente entre os irmãos resolvidos
        if votos:
            pasta_destino = Counter(votos).most_common(1)[0][0]
            origem_info   = f"irmãos ({Counter(votos).most_common(1)[0][1]} votos)"
        else:
            # 2ª escolha: inferir pelo título
            pasta_destino = _inferir_por_titulo(titulo)
            if pasta_destino:
                origem_info = f"título da seção ({titulo!r})"
            else:
                print(f"  ⚠  [{titulo!r}] sem pasta de referência — "
                      f"{len(pendentes)} arquivo(s) não mapeado(s): "
                      f"{', '.join(pendentes)}")
                continue

        print(f"  ✦  [{titulo}]  →  {pasta_destino}/  "
              f"(via {origem_info})")
        for arquivo in pendentes:
            mapeamento[arquivo] = pasta_destino

    return mapeamento


# ─── MOVIMENTAÇÃO ─────────────────────────────────────────────────────────────

def mover_arquivos(mapeamento: dict[str, str]) -> tuple[list, list]:
    """Move cada arquivo para a pasta correta. Retorna (movidos, não_encontrados)."""
    movidos: list[tuple[str, str]] = []
    nao_encontrados: list[str]     = []

    print()
    for arquivo, pasta_destino in sorted(mapeamento.items()):
        origem      = PROCEDIMENTOS_DIR / arquivo
        destino_dir = MODULOS_DIR / pasta_destino
        destino     = destino_dir / arquivo

        if not origem.exists():
            nao_encontrados.append(arquivo)
            print(f"  ✘  {arquivo:<52}  (não existe em procedimentos/)")
            continue

        destino_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(origem), str(destino))
        movidos.append((arquivo, pasta_destino))
        print(f"  ✔  {arquivo:<52}  →  modulos/{pasta_destino}/")

    return movidos, nao_encontrados


# ─── ATUALIZAR SIDEBAR ────────────────────────────────────────────────────────

def atualizar_sidebar(movidos: list[tuple[str, str]]) -> None:
    """Substitui todos os caminhos antigos no sidebar.html pelos novos."""
    conteudo   = SIDEBAR_FILE.read_text(encoding="utf-8")
    alteracoes = 0

    for arquivo, pasta_destino in movidos:
        # Aceita ambos os prefixos para garantir compatibilidade
        for prefixo in ("/Manual/modulos/procedimentos/",
                        "/modulos/procedimentos/"):
            antigo = f"{prefixo}{arquivo}"
            novo   = f"{prefixo.replace('procedimentos', pasta_destino)}{arquivo}"
            if antigo in conteudo:
                conteudo   = conteudo.replace(antigo, novo)
                alteracoes += 1
                print(f"  ↪  procedimentos/{arquivo}  →  {pasta_destino}/{arquivo}")

    SIDEBAR_FILE.write_text(conteudo, encoding="utf-8")
    print(f"\n  ✔  sidebar.html salvo — {alteracoes} caminho(s) atualizado(s).")


# ─── DIAGNÓSTICO ──────────────────────────────────────────────────────────────

def listar_restantes() -> None:
    restantes = sorted(PROCEDIMENTOS_DIR.glob("*.html"))
    if restantes:
        print("\n📂  Arquivos que permaneceram em modulos/procedimentos/")
        print("    (não encontrados no sidebar ou seção sem referência):")
        for f in restantes:
            print(f"    – {f.name}")
    else:
        print("\n  ✔  modulos/procedimentos/ está vazia — tudo reorganizado.")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main() -> None:
    sep = "─" * 64
    print(sep)
    print("  Reorganizador do Manual do Escriturário Escolar")
    print("  (mapeamento automático via sidebar.html)")
    print(sep)
    print(f"\n  Base    : {BASE_DIR}")
    print(f"  Origem  : {PROCEDIMENTOS_DIR}")
    print(f"  Sidebar : {SIDEBAR_FILE}\n")

    if not PROCEDIMENTOS_DIR.exists():
        raise SystemExit("❌  Pasta 'modulos/procedimentos/' não encontrada.\n"
                         "    Execute este script dentro da pasta Manual/")

    # 1. Descobrir mapeamento
    print("Lendo sidebar.html e construindo mapeamento...\n")
    mapeamento = construir_mapeamento(SIDEBAR_FILE)

    if not mapeamento:
        print("\n  ℹ  Nenhum arquivo em procedimentos/ encontrado no sidebar.")
        listar_restantes()
        return

    # 2. Mover arquivos
    print(f"\nMovendo {len(mapeamento)} arquivo(s)...")
    movidos, nao_encontrados = mover_arquivos(mapeamento)

    # 3. Atualizar sidebar
    if movidos:
        print("\nAtualizando sidebar.html...\n")
        atualizar_sidebar(movidos)

    # 4. O que ficou
    listar_restantes()

    # 5. Resumo
    print(f"\n{sep}")
    print(f"  ✅  Concluído!")
    print(f"      {len(movidos)} arquivo(s) movido(s)")
    if nao_encontrados:
        print(f"      {len(nao_encontrados)} no sidebar mas ainda não criados: "
              f"{', '.join(nao_encontrados)}")
    print(sep)


if __name__ == "__main__":
    main()