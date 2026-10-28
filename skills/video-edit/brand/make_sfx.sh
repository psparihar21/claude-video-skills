#!/usr/bin/env bash
# Builds the gaming pack's sound tracks from synthesised whoosh/impact/click sounds (no library, no licence).
# Re-run after changing any animation time in hf/*.html; times below mirror those timelines.
set -eu
cd "$(dirname "$0")"; mkdir -p sfx; cd sfx; rm -f *.wav
F="ffmpeg -v error -y"
$F -f lavfi -i "anoisesrc=d=0.45:c=pink:a=0.9:seed=4" -af "highpass=f=250,lowpass=f=7000,aphaser=in_gain=0.6:out_gain=0.9:speed=1.6:decay=0.5,afade=t=in:d=0.28:curve=exp,afade=t=out:st=0.28:d=0.17,volume=1.3" whoosh.wav
$F -f lavfi -i "aevalsrc=0.95*sin(2*PI*(52*t+70*(1-exp(-25*t))/25))*exp(-5*t):d=0.7" -f lavfi -i "anoisesrc=d=0.06:c=white:a=0.6:seed=8" \
   -filter_complex "[1]lowpass=f=3500,afade=t=out:d=0.06[n];[0][n]amix=2:normalize=0,volume=0.9" impact.wav
$F -f lavfi -i "aevalsrc=0.5*sin(2*PI*2400*t)*exp(-90*t):d=0.05" tick.wav
$F -f lavfi -i "aevalsrc=0.7*sin(2*PI*1700*t)*exp(-260*t)+0.4*sin(2*PI*1100*(t-0.035))*exp(-260*(t-0.035))*gte(t\,0.035):d=0.09" click.wav
$F -f lavfi -i "aevalsrc=0.6*sin(2*PI*(380*t+2600*t*t))*exp(-26*t):d=0.12" pop.wav
$F -f lavfi -i "aevalsrc=0.3*(sin(2*PI*1320*t)+0.6*sin(2*PI*2640*t)+0.3*sin(2*PI*3960*t))*exp(-4*t):d=0.9" bell.wav

# track NAME DURATION "sound@start ..."
track() {
  local name=$1 dur=$2 i=0 ins="" fl="" mix=""
  for ev in $3; do
    s=${ev%@*}; t=${ev#*@}
    ins="$ins -i $s.wav"; fl="$fl[$i]adelay=$(awk "BEGIN{print int($t*1000)}"):all=1[s$i];"; mix="$mix[s$i]"; i=$((i+1))
  done
  $F $ins -filter_complex "${fl}${mix}amix=$i:normalize=0,apad=whole_dur=$dur,atrim=0:$dur,alimiter=limit=0.7:level=disabled" -ar 48000 -ac 2 "$name.wav"
}
track intro_long 2.9 "whoosh@0 impact@0.34 tick@0.72 tick@0.84 whoosh@2.22"
track transition 1 "whoosh@0 impact@0.4 whoosh@0.46"
track subscribe 3.4 "pop@0 click@1.2 pop@1.45 click@2.0 bell@2.05"
track outro_long 15 "whoosh@0 impact@0.36 pop@0.55 pop@0.67 tick@1.0 tick@1.12 pop@1.15 tick@1.45"
track intro_short 2.6 "whoosh@0 impact@0.3 tick@0.3 whoosh@2.0"
track outro_short 3.6 "whoosh@0 impact@0.34 tick@0.62 pop@0.75 click@1.95 pop@2.2 click@2.75 bell@2.8"
rm whoosh.wav impact.wav tick.wav click.wav pop.wav bell.wav
ls -la
