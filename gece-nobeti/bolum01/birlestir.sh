#!/usr/bin/env bash
# Render karelerini, ekran yazılarını ve sesi tek bir dikey MP4'e birleştirir.
# Kullanım: ./birlestir.sh <kare_klasoru> <cikti.mp4>
# Seslendirmesiz sürüm için: SESLENDIRME=0 ./birlestir.sh ...
set -euo pipefail
KARE=$(realpath "${1:?kare klasörü gerekli}")
OUT=$(realpath -m "${2:?çıktı dosyası gerekli}")
cd "$(dirname "$0")"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

python3 yazilar.py "$TMP/yazilar" >/dev/null
python3 ses.py "$TMP/ses.wav" >/dev/null

# Tam kare dizisi: saat çekiminde (265-360) render edilmeyen kareler en yakın kareyle doldurulur.
mkdir "$TMP/seq"
for f in $(seq 1 816); do
  src=$f
  if   (( f >= 266 && f <= 308 )); then src=265
  elif (( f >= 317 && f <= 360 )); then src=316
  fi
  ln -s "$KARE/$(printf %04d "$src").png" "$TMP/seq/$(printf %04d "$f").png"
done

# Yazı katmanları (fade in/out ile)
INPUTS=()
FILTER="[0:v]scale=1080:1920:flags=lanczos,unsharp=5:5:0.5,"
# 3. çekim (saat, 11–15 sn) fazla karanlık: orta tonlar açılır
FILTER+="eq=gamma=1.7:brightness=0.03:enable='between(t,11.0,15.0)',"
# 6. çekim (27–34 sn) daha karanlık ve kontrastlı
FILTER+="eq=brightness=-0.05:contrast=1.18:saturation=1.1:enable='between(t,27,34)',"
FILTER+="eq=contrast=1.05:saturation=0.92,vignette=angle=PI/4.2,noise=alls=6:allf=t,"
FILTER+="fade=t=in:st=0:d=0.7,fade=t=out:st=33.4:d=0.6,"
FILTER+="tpad=stop_mode=add:stop_duration=4.5:color=black[v0]"
i=1
prev=v0
while read -r path a b; do
  d=$(python3 -c "print($b-$a)")
  INPUTS+=(-loop 1 -t "$d" -framerate 24 -i "$path")
  fo=$(python3 -c "print(max(0,$b-$a-0.35))")
  FILTER+=";[$i:v]format=rgba,fade=t=in:st=0:d=0.35:alpha=1,fade=t=out:st=$fo:d=0.35:alpha=1,setpts=PTS+$a/TB[t$i]"
  FILTER+=";[$prev][t$i]overlay=0:0:eof_action=pass[v$i]"
  prev=v$i
  i=$((i+1))
done < "$TMP/yazilar/yazilar.txt"
FILTER+=";[$prev]format=yuv420p[vout]"

mkdir -p "$(dirname "$OUT")"
ffmpeg -loglevel error -y \
  -framerate 24 -i "$TMP/seq/%04d.png" \
  "${INPUTS[@]}" \
  -i "$TMP/ses.wav" \
  -filter_complex "$FILTER" \
  -map "[vout]" -map "$i:a" \
  -c:v libx264 -preset slow -crf 18 -r 24 \
  -c:a aac -b:a 192k -movflags +faststart -t 38.5 \
  "$OUT"
echo "video hazır: $OUT"
