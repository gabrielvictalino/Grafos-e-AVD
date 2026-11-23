# Grafos-e-AVD
Projeto para as disciplinas de Teoria dos Grafos e AVD (Análise e Visualização de Dados).

Projeto utilizando dataset de filmes

Para gerar o relatório de escalabilidade e os gráficos de comparação:

```bash
python -m src.cli --dataset data/dataset_parte2/tmdb_limpo.csv.gz --benchmark --out out/parte2
python viz_parte2.py out/parte2/parte2_report.json --out out/parte2
```

O benchmark grava médias de tempo em `parte2_report.json`. O visualizador salva
um gráfico de barras por escala e um gráfico de linhas por quantidade de vértices.

link declaração uso IA: https://docs.google.com/document/d/1ueEwSR8WfbdE3lctA6aUqdVEH-oBHdUI/edit?usp=sharing&ouid=117048216939304748895&rtpof=true&sd=true
