import os

PASTA = os.path.join("modulos", "documentos", "Informativos EFE")

# Mapeamento: nome atual -> novo nome
RENOMEAR = {
    "INFORMATIVO_N__01_2026_ABERTURA_ANO_LETIVO.pdf":
        "01-INFORMATIVO N 01 - ABERTURA DO ANO LETIVO.PDF",
    "INFORMATIVO_N__02_2026_HTPC_CMEIs.pdf":
        "02-INFORMATIVO N 02 - HTPC CMEIs.PDF",
    "INFORMATIVO_N__03_2026_GRADE_DE_HORARIO.pdf":
        "03-INFORMATIVO N 03 - GRADE DE HORARIO.PDF",
    "INFORMATIVO_N__04_2026_Pasta_Virtual_e_Historicos.pdf":
        "04-INFORMATIVO N 04 - PASTA VIRTUAL E HISTORICOS.PDF",
    "INFORMATIVO_N__05_2026_AVALIACAO_EDUCACAO_INFANTIL.pdf":
        "05-INFORMATIVO N 05 - AVALIACAO EDUCACAO INFANTIL.PDF",
    "INFORMATIVO_N__06_2026_FECHAMENTO_1__TRIMESTRE.pdf":
        "06-INFORMATIVO N 06 - FECHAMENTO 1 TRIMESTRE.PDF",
    "INFORMATIVO_N__07_2026_SERP.pdf":
        "07-INFORMATIVO N 07 - SERP.PDF",
    "INFORMATIVO_N__08_2026_CENSO.pdf":
        "08-INFORMATIVO N 08 - CENSO.PDF",
    "INFORMATIVO_N__09_2026_AEE_e_SRM.pdf":
        "09-INFORMATIVO N 09 - AEE E SRM.PDF",
    "INFORMATIVO_N__10_2026_Reposicao.pdf":
        "10-INFORMATIVO N 10 - REPOSICAO.PDF",
    "INSTRUCAO_NORMATIVA_11_2026___AVALIACAO_ESCOLAR.pdf":
        "11-INSTRUCAO NORMATIVA 11 - AVALIACAO ESCOLAR.PDF",
    "Jogo_do_SERP__1_.pdf":
        "7.1-JOGO DO SERP.PDF",
    "TUTORIAL_Arquivamento_caso_SERP_escola_v2.pdf":
        "7.2-TUTORIAL ARQUIVAMENTO CASO SERP ESCOLA.PDF",
    "TUTORIAL_DE_COMO_EMITIR_RELATORIO_DE_INFREQUENCIA_ESCOLAR_ATRAVES_DO_SERP.pdf":
        "7.3-TUTORIAL EMITIR RELATORIO DE INFREQUENCIA ESCOLAR ATRAVES DO SERP.PDF",
    "TUTORIAL_REABERTURA_CASOS_ARQUIVADOS.pdf":
        "7.4-TUTORIAL REABERTURA CASOS ARQUIVADOS.PDF",
    "TUTORIAL_Registro_de_Infrequencia__1_.pdf":
        "7.5-TUTORIAL REGISTRO DE INFREQUENCIA.PDF",
}

def main():
    for antigo, novo in RENOMEAR.items():
        caminho_antigo = os.path.join(PASTA, antigo)
        caminho_novo = os.path.join(PASTA, novo)

        if not os.path.exists(caminho_antigo):
            print(f"[NAO ENCONTRADO] {antigo}")
            continue

        os.rename(caminho_antigo, caminho_novo)
        print(f"[OK] {antigo} -> {novo}")

if __name__ == "__main__":
    main()