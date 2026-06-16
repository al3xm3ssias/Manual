"""
Comprime todos os PDFs dentro de modulos/documentos (recursivamente)
que estejam acima de 1MB, usando Ghostscript.

Estrategia:
- So toca em arquivos > LIMITE_MB.
- Tenta primeiro qualidade "prepress" (alta qualidade, imagens em 300dpi)
  -> se o resultado ainda ficar > LIMITE_MB, tenta "ebook" (150dpi)
  -> so usa "ebook" se realmente precisar, pra nao perder qualidade demais.
- Mantem o arquivo original como .bak ate confirmar que a compressao
  funcionou e reduziu o tamanho. Se o resultado ficar maior ou igual ao
  original, mantem o original e descarta o resultado.

Requisitos:
- Ghostscript instalado e no PATH.
  Windows: https://ghostscript.com/releases/gsdnld.html
  (o executavel costuma se chamar "gswin64c.exe")

Uso:
    python comprimir_pdfs.py
"""

import os
import shutil
import subprocess
import sys

PASTA_BASE = "modulos/documentos"
LIMITE_MB = 1
LIMITE_BYTES = LIMITE_MB * 1024 * 1024


def comprimir_com_gs_dpi(gs_exe, origem, destino, dpi):
    comando = [
        gs_exe,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        "-dSubsetFonts=true",
        "-dDownsampleColorImages=true",
        "-dDownsampleGrayImages=true",
        "-dDownsampleMonoImages=true",
        "-dColorImageDownsampleType=/Bicubic",
        "-dGrayImageDownsampleType=/Bicubic",
        "-dMonoImageDownsampleType=/Subsample",
        f"-dColorImageResolution={dpi}",
        f"-dGrayImageResolution={dpi}",
        f"-dMonoImageResolution={dpi * 2}",
        "-dColorImageDownsampleThreshold=1.0",
        "-dGrayImageDownsampleThreshold=1.0",
        "-dMonoImageDownsampleThreshold=1.0",
        "-dAutoFilterColorImages=false",
        "-dColorImageFilter=/DCTEncode",
        "-dJPEGQ=90",
        f"-sOutputFile={destino}",
        origem,
    ]
    resultado = subprocess.run(comando, capture_output=True, text=True)
    return resultado.returncode == 0 and os.path.exists(destino)


def encontrar_ghostscript():
    candidatos = ["gswin64c", "gswin32c", "gs"]
    for nome in candidatos:
        caminho = shutil.which(nome)
        if caminho:
            return caminho
    return None


def encontrar_qpdf():
    return shutil.which("qpdf")


def comprimir_com_qpdf(qpdf_exe, origem, destino):
    comando = [
        qpdf_exe,
        "--compress-streams=y",
        "--object-streams=generate",
        "--recompress-flate",
        "--compression-level=9",
        origem,
        destino,
    ]
    resultado = subprocess.run(comando, capture_output=True, text=True)
    return resultado.returncode in (0, 3) and os.path.exists(destino)


def tamanho_mb(caminho):
    return os.path.getsize(caminho) / (1024 * 1024)


def comprimir_com_gs(gs_exe, origem, destino, qualidade):
    comando = [
        gs_exe,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{qualidade}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        "-dSubsetFonts=true",
        f"-sOutputFile={destino}",
        origem,
    ]
    resultado = subprocess.run(comando, capture_output=True, text=True)
    return resultado.returncode == 0


def processar_pdf(gs_exe, qpdf_exe, caminho):
    tamanho_original = os.path.getsize(caminho)
    if tamanho_original <= LIMITE_BYTES:
        return

    nome = os.path.basename(caminho)
    print(f"\n[PROCESSANDO] {nome} ({tamanho_original / 1024 / 1024:.2f} MB)")

    temp_path = caminho + ".tmp.pdf"
    melhor_tamanho = tamanho_original
    houve_reducao = False

    # 1) Ghostscript: prepress (alta qualidade) -> ebook (so se ainda precisar)
    for qualidade in ("prepress", "ebook"):
        ok = comprimir_com_gs(gs_exe, caminho, temp_path, qualidade)
        if not ok or not os.path.exists(temp_path):
            print(f"  [ERRO] Ghostscript falhou na qualidade '{qualidade}'")
            continue

        novo_tamanho = os.path.getsize(temp_path)

        if novo_tamanho < melhor_tamanho:
            backup_path = caminho + ".bak"
            if not houve_reducao:
                shutil.copy2(caminho, backup_path)
            shutil.move(temp_path, caminho)
            melhor_tamanho = novo_tamanho
            houve_reducao = True
            print(f"  [OK] gs/{qualidade} -> {novo_tamanho / 1024 / 1024:.2f} MB")
            if novo_tamanho <= LIMITE_BYTES:
                return
        else:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            print(f"  [IGNORADO] gs/{qualidade} nao reduziu o tamanho")

    # 2) Ainda > limite (ou GS nao ajudou): tenta qpdf
    #    Util para PDFs de texto puro, onde o GS ja nao tem mais o que cortar.
    if qpdf_exe and melhor_tamanho > LIMITE_BYTES:
        ok = comprimir_com_qpdf(qpdf_exe, caminho, temp_path)
        if ok and os.path.exists(temp_path):
            novo_tamanho = os.path.getsize(temp_path)
            if novo_tamanho < melhor_tamanho:
                backup_path = caminho + ".bak"
                if not houve_reducao:
                    shutil.copy2(caminho, backup_path)
                shutil.move(temp_path, caminho)
                melhor_tamanho = novo_tamanho
                houve_reducao = True
                print(f"  [OK] qpdf -> {novo_tamanho / 1024 / 1024:.2f} MB")
            else:
                os.remove(temp_path)
                print("  [IGNORADO] qpdf nao reduziu o tamanho")
        else:
            print("  [ERRO] qpdf falhou")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    if not houve_reducao:
        print("  [SEM ALTERACAO] arquivo ja esta no tamanho minimo possivel sem perda de qualidade")

    # 3) Ainda > limite: PDF provavelmente e' um scan (imagem por pagina).
    #    Reduz a resolucao das imagens em etapas (300 -> 200 -> 150 dpi),
    #    mantendo qualidade JPEG alta (90) e parando assim que ficar <= limite.
    if melhor_tamanho > LIMITE_BYTES:
        for dpi in (300, 200, 150):
            ok = comprimir_com_gs_dpi(gs_exe, caminho, temp_path, dpi)
            if not ok:
                print(f"  [ERRO] downsample {dpi}dpi falhou")
                continue

            novo_tamanho = os.path.getsize(temp_path)
            if novo_tamanho < melhor_tamanho:
                backup_path = caminho + ".bak"
                if not houve_reducao:
                    shutil.copy2(caminho, backup_path)
                shutil.move(temp_path, caminho)
                melhor_tamanho = novo_tamanho
                houve_reducao = True
                print(f"  [OK] downsample {dpi}dpi -> {novo_tamanho / 1024 / 1024:.2f} MB")
                if novo_tamanho <= LIMITE_BYTES:
                    break
            else:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                print(f"  [IGNORADO] downsample {dpi}dpi nao reduziu o tamanho")

    if melhor_tamanho > LIMITE_BYTES:
        print(
            f"  [AVISO] reduzido para {melhor_tamanho / 1024 / 1024:.2f} MB, "
            f"mas ainda acima de {LIMITE_MB} MB sem perder qualidade"
        )


def main():
    gs_exe = encontrar_ghostscript()
    if not gs_exe:
        print("Ghostscript nao encontrado no PATH.")
        print("Instale em: https://ghostscript.com/releases/gsdnld.html")
        sys.exit(1)

    qpdf_exe = encontrar_qpdf()
    if not qpdf_exe:
        print("[AVISO] qpdf nao encontrado no PATH. PDFs de texto puro (sem imagens)")
        print("        podem nao reduzir de tamanho. Instale com: sudo apt install qpdf")

    if not os.path.isdir(PASTA_BASE):
        print(f"Pasta '{PASTA_BASE}' nao encontrada no diretorio atual.")
        sys.exit(1)

    print(f"Usando Ghostscript: {gs_exe}")
    if qpdf_exe:
        print(f"Usando qpdf: {qpdf_exe}")
    print(f"Procurando PDFs acima de {LIMITE_MB} MB em '{PASTA_BASE}'...")

    encontrados = 0
    for raiz, _dirs, arquivos in os.walk(PASTA_BASE):
        for arquivo in arquivos:
            if arquivo.lower().endswith(".pdf"):
                caminho = os.path.join(raiz, arquivo)
                if tamanho_mb(caminho) > LIMITE_MB:
                    encontrados += 1
                    processar_pdf(gs_exe, qpdf_exe, caminho)

    if encontrados == 0:
        print("Nenhum PDF acima do limite foi encontrado.")
    else:
        print(f"\nConcluido. {encontrados} arquivo(s) processado(s).")
        print("Os originais foram salvos como .bak ao lado de cada arquivo comprimido.")


if __name__ == "__main__":
    main()