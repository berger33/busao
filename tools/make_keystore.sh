#!/bin/bash
# Gera keystore de release fora do repo — nunca commitar.
# Uso: ./tools/make_keystore.sh [caminho_saida]
# Requer: JDK 17 (keytool)  -> RSA 4096, validade 10000 dias
set -e
# Padrão: ../corre-pro-ponto.keystore (irmão do repo, == $HOME se repo em $HOME/busao)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEFAULT_OUT="$(cd "$SCRIPT_DIR/.." && pwd)/../corre-pro-ponto.keystore"
# Se já estamos em /home/user/busao, ../ == /home/user -> normaliza para $HOME quando coincide
if [ "$DEFAULT_OUT" = "/home/user/busao/../corre-pro-ponto.keystore" ]; then
  DEFAULT_OUT="$HOME/corre-pro-ponto.keystore"
fi
OUT="${1:-$DEFAULT_OUT}"
ALIAS="correpro"
if [ -f "$OUT" ]; then
  echo "Keystore já existe: $OUT"
  echo "Use outro caminho ou remova o existente."
  exit 1
fi
if ! command -v keytool >/dev/null 2>&1; then
  echo "keytool não encontrado. Instale JDK 17 (Temurin/Adoptium)."
  exit 1
fi
echo "Gerando keystore de release em: $OUT"
keytool -genkeypair -v \
  -keystore "$OUT" \
  -alias "$ALIAS" \
  -keyalg RSA -keysize 4096 -validity 10000 \
  -storepass "troque-esta-senha" -keypass "troque-esta-senha" \
  -dname "CN=Arena Busao, OU=Corre pro Ponto, O=Arena, L=Guarulhos, S=SP, C=BR"
echo ""
echo "OK. Configure no Godot: Editor -> Export -> Android -> keystore/release"
echo "Caminho: $OUT"
echo "Alias: $ALIAS"
echo "Validade: 10000 dias | Algo: RSA 4096"
echo "IMPORTANTE: faça backup em 1Password/Google Drive e NUNCA commite (*.keystore no .gitignore)."
echo "Depois, exporte AAB assinado: Project -> Export -> Android -> Export PCK/AAB (caminho build/corre-pro-ponto.aab)"
echo "Valide: keytool -list -v -keystore \"$OUT\"  ;  jarsigner -verify -verbose -certs build/corre-pro-ponto.aab (após export)"
