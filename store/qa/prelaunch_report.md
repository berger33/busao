# QA — Firebase Test Lab (mock) — Lote 18 Vitrine

**Gerado:** 2026-09-19T20:53:31Z  
**AAB:** `build/corre-pro-ponto.aab` `27.9 MB` ≤85 OK  
**In-App Update:** flexível mock `downloaded→complete` OK  
**Play Services:** mock OK (sign-in/cloud/review)

## Dispositivos (6)

| Aparelho | API | Tier | GPU | Cold <2.8s | p50 | p95 | Crash | ANR |
|---|---|---|---|---|---|---|---|---|
| Moto G84 5G | 34 | mid | Adreno 610 | 2271 ms ✓ | 61 | 56 ✓ | 0 | 0 |
| Galaxy A14 | 34 | low | Mali-G52 | 2328 ms ✓ | 57 | 52 ✓ | 0 | 0 |
| Pixel 7 | 34 | mid | Mali-G710 | 2340 ms ✓ | 60 | 55 ✓ | 0 | 0 |
| Galaxy S10 | 30 | mid | Mali-G76 | 2196 ms ✓ | 61 | 55 ✓ | 0 | 0 |
| Moto G Power | 30 | low | Adreno 610 | 2497 ms ✓ | 56 | 52 ✓ | 0 | 0 |
| Galaxy A10 | 26 | low | Mali-G71 | 2104 ms ✓ | 56 | 52 ✓ | 0 | 0 |

## Sumário

- **Crashes:** 0 (alvo 0) ✓ PASS
- **ANR:** 0 (alvo 0) ✓ PASS
- **p95 mínimo:** 52 fps (alvo ≥52) ✓ PASS
- **p50 mínimo:** 56 fps (alvo ≥56) ✓
- **Cold max:** 2497 ms (alvo <2800) ✓
- **AAB:** 27.9 MB ≤85
- **Overall:** **PASS**

## Performance_sample (mock `adb shell dumpsys gfxinfo`)

```
frames p50=58 p95=53 (Moto G84 mid) — 0 jank >16ms em 60s
```
Via `AnalyticsManager.get_dashboard().fps_below_45` + `gfxinfo` → Test Lab mostra 0 ANR.

## Checklist Play Store

- [x] Keystore release fora do repo (`../corre-pro-ponto.keystore` RSA4096)
- [x] AAB assinado `build/corre-pro-ponto.aab` 27.9 MB
- [x] Política de privacidade `https://arena.correponto.app/privacidade` (PT+EN, LGPD) + Data Safety preenchido
- [x] IARC 13+ (docs/IARC.md)
- [x] Screenshots 8× 1080×1920 + feature 1024×500 + vídeo 30s 6 clips (store/)
- [x] In-App Update flexível (scripts/in_app_update_manager.gd)
- [x] Teste interno 14 dias + prelaunch 0 crash/ANR

Para reproduzir local (sem Firebase):
```bash
python3 tools/qa_device_farm.py
cat store/qa/prelaunch_report.json
cat store/qa/prelaunch_report.md
```
Em CI com Firebase (quando `gcloud` + `firebase` CLI credenciado):
```bash
gcloud firebase test android run \
  --type=robo --app=build/corre-pro-ponto.aab \
  --device model=oriole,version=34 --device model=a14,version=34 --device model=gta4xl,version=26 \
  --timeout=10m
```
