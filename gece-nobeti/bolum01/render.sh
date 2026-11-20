#!/usr/bin/env bash
# Bölüm 1'in tüm karelerini render eder (kaldığı yerden devam eder).
# Kullanım: ./render.sh <kare_klasoru> [python]
set -euo pipefail
OUT=${1:?kare klasörü gerekli}
PY=${2:-python3}
mkdir -p "$OUT"
# Saat çekiminde (265-360) kamera sabit: yalnız 265 ve yelkovanın oynadığı 309-316 render edilir,
# birlestir.sh aradaki kareleri kopyalar.
KARELER="1-264,265,309-316,361-816"
cd "$(dirname "$0")"
"$PY" sahne.py --cikti "$OUT" --kalite final --kare "$KARELER" 2>&1 | grep --line-buffered -E "^Saved|Error|Traceback" || true
echo BITTI
