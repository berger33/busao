# QA de vitrine — status

> **Atenção:** os relatórios neste diretório (`prelaunch_report.*`) foram
> gerados por `tools/qa_device_farm.py`, que **simula** métricas (seed fixa
> 20260918) — tamanho do AAB, fps por aparelho, cold start, 0 crash/ANR.
> São placeholders de formato, **não medições**.
>
> Trocar por medição real assim que houver o primeiro AAB:
> 1. `./tools/build_aab.sh` (gera `build/corre-pro-ponto.aab`);
> 2. subir no Firebase Test Lab (Robo + 6 aparelhos do farm);
> 3. substituir estes arquivos pelos JSON/MD reais e apagar este aviso.
