#!/usr/bin/env python3
"""
reorganizar_manual.py
─────────────────────────────────────────────────────────────────────
Reorganiza os arquivos de modulos/procedimentos/ para pastas temáticas
e atualiza os caminhos no sidebar.html automaticamente.

Execute dentro da pasta Manual/:
    python3 reorganizar_manual.py

Estrutura criada:
    modulos/matricula/      → Pré-matrícula, matrícula, transferências, docs SERE
    modulos/sere/           → Cadastros, lançamentos, abonos, estatística
    modulos/sei/            → Processos SEI
    modulos/servidores/     → Justificativas, quinzenal, documentação de servidores
    modulos/legislacao/     → Leis 14.648, 14.936 e progressões (pasta já existe)
─────────────────────────────────────────────────────────────────────
"""

import os
import shutil
from pathlib import Path

# ─── CONFIGURAÇÃO ─────────────────────────────────────────────────────────────
BASE_DIR          = Path(__file__).parent          # pasta Manual/
MODULOS_DIR       = BASE_DIR / "modulos"
PROCEDIMENTOS_DIR = MODULOS_DIR / "procedimentos"
SIDEBAR_FILE      = BASE_DIR / "sidebar.html"

# ─── MAPEAMENTO arquivo → pasta de destino (dentro de modulos/) ───────────────
MAPEAMENTO: dict[str, str] = {

    # ── MATRÍCULA ──────────────────────────────────────────────────────────────
    "pre_matricula.html":            "matricula",
    "documentacao.html":             "matricula",
    "matriculas.html":               "matricula",
    "anexo_de_documentos.html":      "matricula",
    "transferencias.html":           "matricula",
    "declaracoes_de_matricula.html": "matricula",
    "declaracao_de_matricula.html":  "matricula",   # variação de nome
    "pareceres.html":                "matricula",
    "parecer.html":                  "matricula",   # variação de nome
    "guia_de_transferencia.html":    "matricula",

    # ── SERE / RCO ─────────────────────────────────────────────────────────────
    "cadastro_alunos.html":          "sere",
    "cadastro_funcionarios.html":    "sere",
    "cadastro_professores.html":     "sere",
    "abono_de_faltas.html":          "sere",
    "grade_aulas.html":              "sere",
    "lancar_livros_de_chamada.html": "sere",
    "estatistica.html":              "sere",

    # ── SEI ────────────────────────────────────────────────────────────────────
    "iniciar_processos.html":      "sei",
    "cota.html":                   "sei",
    "documentos_externos.html":    "sei",

    # ── SERVIDORES ─────────────────────────────────────────────────────────────
    "abonos.html":                         "servidores",
    "compensacao_de_horas.html":           "servidores",
    "justificativas.html":                 "servidores",
    "quinzenal.html":                      "servidores",
    "atestados.html":                      "servidores",
    "declaracoes.html":                    "servidores",
    "CAT.html":                            "servidores",
    "cat.html":                            "servidores",   # mesmo arquivo, caixa diferente no Linux
    "carta_de_apresentacao.html":          "servidores",
    "ficha_funcional.html":                "servidores",
    "solicitacao_de_vale_transporte.html": "servidores",
    "ficha_epi.html":                      "servidores",

    # ── LEGISLAÇÃO (pasta já existe) ───────────────────────────────────────────
    "14648.html":             "legislacao",
    "14936.html":             "legislacao",
    "progressoes_14648.html": "legislacao",
    "progressoes_14936.html": "legislacao",
}


# ─── FUNÇÕES ──────────────────────────────────────────────────────────────────

def mover_arquivos() -> tuple[list, list]:
    """Move cada arquivo para a pasta correta. Retorna (movidos, não_encontrados)."""
    movidos: list[tuple[str, str]] = []
    nao_encontrados: list[str]     = []

    for arquivo, pasta_destino in MAPEAMENTO.items():
        origem      = PROCEDIMENTOS_DIR / arquivo
        destino_dir = MODULOS_DIR / pasta_destino
        destino     = destino_dir / arquivo

        if not origem.exists():
            nao_encontrados.append(arquivo)
            continue

        destino_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(origem), str(destino))
        movidos.append((arquivo, pasta_destino))
        print(f"  ✔  {arquivo:<45}  →  modulos/{pasta_destino}/")

    return movidos, nao_encontrados


def atualizar_sidebar(movidos: list[tuple[str, str]]) -> None:
    """Substitui todos os caminhos antigos no sidebar.html pelos novos."""
    if not SIDEBAR_FILE.exists():
        print("\n⚠  sidebar.html não encontrado — caminhos não foram atualizados.")
        return

    conteudo   = SIDEBAR_FILE.read_text(encoding="utf-8")
    alteracoes = 0

    for arquivo, pasta_destino in movidos:
        antigo = f"/Manual/modulos/procedimentos/{arquivo}"
        novo   = f"/Manual/modulos/{pasta_destino}/{arquivo}"
        if antigo in conteudo:
            conteudo = conteudo.replace(antigo, novo)
            alteracoes += 1
            print(f"  ↪  sidebar: procedimentos/{arquivo}  →  {pasta_destino}/{arquivo}")

    SIDEBAR_FILE.write_text(conteudo, encoding="utf-8")
    print(f"\n  ✔  sidebar.html salvo — {alteracoes} caminho(s) atualizado(s).")


def listar_restantes() -> None:
    """Mostra o que ainda ficou em procedimentos/ após a reorganização."""
    restantes = list(PROCEDIMENTOS_DIR.glob("*.html"))
    if restantes:
        print("\n📂 Arquivos que permaneceram em modulos/procedimentos/")
        print("   (não constavam no mapeamento — provavelmente ainda em criação):")
        for f in sorted(restantes):
            print(f"   – {f.name}")
    else:
        print("\n  ✔  modulos/procedimentos/ está vazia — tudo foi reorganizado.")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main() -> None:
    sep = "─" * 60
    print(sep)
    print("  Reorganizador do Manual do Escriturário Escolar")
    print(sep)
    print(f"\n  Base    : {BASE_DIR}")
    print(f"  Origem  : {PROCEDIMENTOS_DIR}")
    print()

    if not PROCEDIMENTOS_DIR.exists():
        print("❌  Pasta 'modulos/procedimentos/' não encontrada.")
        print("    Execute este script dentro da pasta Manual/")
        return

    # 1. Mover arquivos
    print("Movendo arquivos...\n")
    movidos, nao_encontrados = mover_arquivos()

    # 2. Relatório de não encontrados
    if nao_encontrados:
        print(f"\n⚠  Listados no mapeamento mas ausentes na pasta procedimentos/:")
        for f in nao_encontrados:
            print(f"   – {f}")

    # 3. Atualizar sidebar
    print("\nAtualizando sidebar.html...\n")
    atualizar_sidebar(movidos)

    # 4. O que ficou
    listar_restantes()

    # 5. Resumo final
    print(f"\n{sep}")
    print(f"  ✅  Concluído!")
    print(f"     {len(movidos)} arquivo(s) movido(s)")
    print(f"     {len(nao_encontrados)} arquivo(s) não encontrado(s) / ainda não criados")
    print(sep)


if __name__ == "__main__":
    main()