#!/usr/bin/env python3
"""
gerar_indice.py

Lê o sidebar.html do Manual do Escriturário, extrai todos os itens de menu
(<a> dentro de <li class="nav-item">) e gera data/indice.json classificando
cada item em "procedimento" ou "legislacao" com base no caminho da URL
(/modulos/legislacao/ -> legislacao, demais -> procedimento).

Uso:
    python gerar_indice.py [--sidebar sidebar.html] [--saida data/indice.json]
"""

import argparse
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup


def categoria_por_href(href: str) -> str:
    """Classifica o item com base no caminho da URL."""
    href_lower = href.lower()
    if "/modulos/legislacao/" in href_lower:
        return "legislacao"
    return "procedimento"


def extrair_secao(link_tag) -> str:
    """
    Sobe na árvore até achar o <li class="nav-item has-treeview"> pai
    e retorna o título da seção (texto do <p> do link "#" daquele item).
    Se não houver seção pai (item solto), retorna "Geral".
    """
    li_pai = link_tag.find_parent("li", class_="nav-item")
    if li_pai is None:
        return "Geral"

    treeview_li = li_pai.find_parent("li", class_="has-treeview")
    if treeview_li is None:
        return "Geral"

    titulo_link = treeview_li.find("a", recursive=False)
    if titulo_link is None:
        return "Geral"

    p_tag = titulo_link.find("p")
    if p_tag is None:
        return "Geral"

    # Remove o texto do ícone "right fas fa-angle-left" embutido, se houver
    for icon in p_tag.find_all("i"):
        icon.extract()

    texto = p_tag.get_text(strip=True)
    return texto if texto else "Geral"


def gerar_id(href: str) -> str:
    """Gera um id slug a partir do caminho do arquivo."""
    nome = href.rstrip("/").split("/")[-1]
    nome = re.sub(r"\.html?$", "", nome, flags=re.IGNORECASE)
    nome = nome.lower()
    nome = re.sub(r"[^a-z0-9_-]+", "_", nome)
    return nome or "item"


def extrair_itens(sidebar_html: str):
    soup = BeautifulSoup(sidebar_html, "html.parser")

    procedimentos = []
    legislacoes = []
    vistos = set()

    nav = soup.find("nav")
    contexto = nav if nav else soup

    for li in contexto.find_all("li", class_="nav-item"):
        link = li.find("a", recursive=False)
        if link is None:
            continue

        href = link.get("href", "").strip()

        # ignora links vazios/placeholder, botões de ferramenta e o próprio dashboard
        if not href or href == "#":
            continue
        if link.get("id") in {"btn-toggle-favorites", "btn-toggle-history"}:
            continue
        if link.get("data-module") == "dashboard":
            continue

        p_tag = link.find("p")
        if p_tag is None:
            continue

        p_copy = BeautifulSoup(str(p_tag), "html.parser").find("p")
        for icon in p_copy.find_all("i"):
            icon.extract()
        titulo = p_copy.get_text(strip=True)
        if not titulo:
            continue

        icon_tag = link.find("i", class_="nav-icon")
        icone = " ".join(icon_tag.get("class", [])) if icon_tag else ""

        chave = (href, titulo)
        if chave in vistos:
            continue
        vistos.add(chave)

        item = {
            "id": gerar_id(href),
            "titulo": titulo,
            "url": href,
            "secao": extrair_secao(link),
            "icone": icone,
        }

        if categoria_por_href(href) == "legislacao":
            legislacoes.append(item)
        else:
            procedimentos.append(item)

    return procedimentos, legislacoes


def main():
    parser = argparse.ArgumentParser(description="Gera indice.json a partir do sidebar.html")
    parser.add_argument("--sidebar", default="sidebar.html", help="Caminho do sidebar.html")
    parser.add_argument("--saida", default="data/indice.json", help="Caminho do JSON de saída")
    args = parser.parse_args()

    sidebar_path = Path(args.sidebar)
    if not sidebar_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {sidebar_path}")

    sidebar_html = sidebar_path.read_text(encoding="utf-8")
    procedimentos, legislacoes = extrair_itens(sidebar_html)

    indice = {
        "procedimentos": {
            "total": len(procedimentos),
            "itens": procedimentos,
        },
        "legislacoes": {
            "total": len(legislacoes),
            "itens": legislacoes,
        },
    }

    saida_path = Path(args.saida)
    saida_path.parent.mkdir(parents=True, exist_ok=True)
    saida_path.write_text(
        json.dumps(indice, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"OK: {len(procedimentos)} procedimentos, {len(legislacoes)} legislações")
    print(f"Salvo em: {saida_path.resolve()}")


if __name__ == "__main__":
    main()