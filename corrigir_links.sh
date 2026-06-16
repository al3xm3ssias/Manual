#!/usr/bin/env bash
# Corrige links absolutos quebrados nos arquivos .html do Manual
# Uso: rode este script dentro da pasta raiz do projeto (onde está o index.html)

set -e

PREFIXO="/Manual"

echo "Procurando arquivos .html com href=\"/...\" "
echo "----------------------------------------------"
grep -rn 'href="/' --include="*.html" . || echo "Nenhuma ocorrência encontrada."
echo "----------------------------------------------"
echo ""
read -p "Confirma a correção em massa? Isso vai prefixar os links acima com $PREFIXO (s/n): " resposta

if [[ "$resposta" != "s" && "$resposta" != "S" ]]; then
    echo "Operação cancelada."
    exit 0
fi

# Evita duplicar caso já exista /Manual no link
grep -rl 'href="/' --include="*.html" . | while read -r arquivo; do
    sed -i -E "s|href=\"/(?!Manual/)|href=\"${PREFIXO}/|g" "$arquivo" 2>/dev/null || \
    sed -i "s|href=\"${PREFIXO}/|href=\"@@TEMP@@/|g; s|href=\"/|href=\"${PREFIXO}/|g; s|href=\"@@TEMP@@/|href=\"${PREFIXO}/|g" "$arquivo"
done

echo ""
echo "Correção concluída. Resultado:"
echo "----------------------------------------------"
grep -rn 'href="' --include="*.html" . | grep "$PREFIXO"
