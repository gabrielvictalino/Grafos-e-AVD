# Grafos-e-AVD

Projeto interdisciplinar das disciplinas de **Teoria dos Grafos** e **Análise e Visualização de Dados (AVD) — 2026.2** (CESAR School).

O projeto é dividido em duas partes:
- **Parte 1 — Labirinto com Chaves e Portas (Grafo de Estados):** leitura e validação de mapas em texto, construção do grafo de posições (`G_pos`) e do grafo de estados (`G_est`) por exploração, execução de BFS, DFS (com classificação de arcos), Dijkstra e Bellman-Ford (implementações próprias em Python), detecção de estados-armadilha via grafo transposto e visualização interativa em Streamlit.
- **Parte 2 — Dataset Maior e Análise Visual (TMDB):** construção de grafo dirigido e ponderado com pesos negativos derivados dos dados de filmes, comparação de corretude, desempenho e escalabilidade dos quatro algoritmos, além de análise exploratória e explanatória (AVD).

---

## Requisitos e Instalação

- **Python 3.11+** (ambiente testado com `.venv`).
- Dependências listadas em `requirements.txt` (`streamlit`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`, `kagglehub`, `networkx` apenas para oráculo em `tests/`, `pyvis`, `pytest`).

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux / macOS (bash/zsh)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Estrutura do Projeto

```text
Grafos-e-AVD/
├─ README.md
├─ requirements.txt
├─ app.py                          # Interface interativa Streamlit da Parte 1
├─ docs/
│  ├─ relatorio_parte1.md          # Documentação técnica e manual da Parte 1 (base para o PDF)
│  ├─ relatorio_parte2.md          # Documentação técnica e análise AVD da Parte 2 (base para o PDF)
│  ├─ CHECKLIST_ENTREGA_PARTE1.md  # Checklist de entrega e pendências da Parte 1
│  └─ CHECKLIST_ENTREGA_PARTE2.md  # Checklist de entrega e pendências da Parte 2 e AVD
├─ mapas/                          # Mapas fornecidos da Parte 1 (m01 a m08)
├─ data/
│  └─ dataset_parte2/
│     └─ tmdb_limpo.csv.gz         # Dataset tratado da Parte 2
├─ out/
│  ├─ parte1/                      # Arestas, graus, métricas, camadas, soluções, DFS e armadilhas
│  └─ parte2/                      # Relatório de benchmark e gráficos da Parte 2
├─ notebooks/                      # Exploração e limpeza do dataset da Parte 2 (AVD)
├─ src/
│  ├─ cli.py                       # Interface de linha de comando (CLI)
│  ├─ solve.py                     # Orquestração da Parte 1 (exportação) e Parte 2 (algoritmos/benchmark)
│  ├─ viz.py                       # Exportação de arestas, heatmaps e gráficos da Parte 2
│  └─ graphs/
│     ├─ algorithms.py             # Implementações próprias de BFS, DFS, Dijkstra e Bellman-Ford
│     ├─ estados.py                # Exploração do grafo de estados, camadas e armadilhas
│     ├─ graph.py                  # Estrutura de grafo dirigido
│     ├─ io.py                     # Leitura e carregamento do grafo da Parte 2 (TMDB)
│     └─ labirinto.py              # Leitura, validação de mapas e estrutura do labirinto
├─ tests/                          # Suíte de testes unitários (pytest)
│  ├─ test_bfs.py
│  ├─ test_dfs.py
│  ├─ test_dijkstra.py
│  ├─ test_bellman_ford.py
│  ├─ test_estados.py
│  └─ test_io.py
└─ taxi_labirinto/                 # Demonstração interativa temática extra
```

> **Observação sobre pastas do enunciado:** os mapas fornecidos estão em `mapas/`. Antes da entrega final, caso queira seguir exatamente a árvore literal do enunciado, mova/copie para `data/mapas/`, crie os 2 mapas próprios em `data/mapas_grupo/` e inclua a `docs/DECLARACAO_IA.pdf` assinada por todos.

---

## Como Executar

### Parte 1 — Labirinto com Chaves e Portas

1. **Exportar todas as saídas da Parte 1** (`arestas_<mapa>.csv`, `graus_<mapa>.csv`, `metricas_global.json`, `camadas.json`, `solucoes.csv`, `dfs_classificacao.csv`, `percurso_m03.json`, `ciclo_negativo_m06.json`, `armadilhas_m04.csv`, `armadilhas_m07.csv`):

```bash
python -m src.cli --exportar-parte1 mapas --out out/parte1
```

2. **Executar o labirinto interativo (Streamlit):**

```bash
streamlit run app.py
```

Recursos disponíveis em `app.py`: seleção de mapa e algoritmo (`BFS`, `Dijkstra`, `Bellman-Ford`, `DFS`), alternância entre `Grafo de estados` e `Grafo padrão`, animação passo a passo com controle de velocidade e slider, painéis separados por camada `(chaves, bônus)`, painel do estado atual (posição, chaves, bônus consumidos, custo acumulado) e realce de estados-armadilha e ciclo negativo.

3. **Executar a demonstração temática extra (`taxi_labirinto`, opcional):**

```bash
streamlit run taxi_labirinto/jogo.py
```

4. **Executar os testes unitários obrigatórios (`pytest`):**

```bash
pytest tests/
```

> Nota: execute `pytest tests/` (em vez de `pytest` sem argumentos) para evitar que o pytest tente coletar a suíte independente `taxi_labirinto/tests/test_jogo.py` a partir da raiz.

#### Parâmetros da CLI (`src/cli.py`)

O parser em `src/cli.py` também declara as flags `--mapa`, `--alg {BFS,DFS,DIJKSTRA,BELLMAN_FORD}`, `--fonte-consumivel`, `--armadilhas` e `--interactive`. Atualmente, o fluxo completo da Parte 1 está conectado em `--exportar-parte1` e `app.py`; a execução individual por `--mapa` ainda está pendente de ligação em `src/cli.py` (ver `docs/CHECKLIST_ENTREGA_PARTE1.md`).

---

### Parte 2 — Dataset Maior (TMDB) e Comparação de Algoritmos

Para gerar o relatório de escalabilidade e os gráficos de comparação:

```bash
python -m src.cli --dataset data/dataset_parte2/tmdb_limpo.csv.gz --benchmark --out out/parte2
python -m src.viz out/parte2/parte2_report.json --out out/parte2
```

O benchmark grava médias de tempo (5 execuções por algoritmo em 10%, 50% e 100% do dataset) em `out/parte2/parte2_report.json`. O visualizador salva um gráfico de barras por escala e um gráfico de linhas por quantidade de vértices.

Para executar um algoritmo específico entre origem e destino no dataset da Parte 2:

```bash
python -m src.cli --dataset data/dataset_parte2/tmdb_limpo.csv.gz --alg DIJKSTRA --source <ID_ORIGEM> --target <ID_DESTINO> --out out/parte2
```

---

## Documentação e Uso Responsável de IA

- **Relatório Técnico + Manual da Parte 1:** `docs/relatorio_parte1.md` (contém tabelas de métricas, camadas, soluções, DFS, armadilhas, conferência manual do mapa mínimo de testes e marcações para os trechos autorais exigidos no PDF).
- **Relatório Técnico + AVD da Parte 2:** `docs/relatorio_parte2.md` (contém modelagem do grafo TMDB, métricas estruturais, limpeza e os 4 pilares de AVD, outliers, tabelas para casos obrigatórios/benchmark e marcações para as notas analíticas autorais).
- **Checklists de Entrega:** `docs/CHECKLIST_ENTREGA_PARTE1.md` e `docs/CHECKLIST_ENTREGA_PARTE2.md`.
- **Declaração de Uso de IA:**
  - Link declaração uso IA: https://docs.google.com/document/d/1ueEwSR8WfbdE3lctA6aUqdVEH-oBHdUI/edit?usp=sharing&ouid=117048216939304748895&rtpof=true&sd=true
  - Para a entrega final, exportar a declaração preenchida e assinada por todos os integrantes para `docs/DECLARACAO_IA.pdf` e anexá-la no Classroom.
