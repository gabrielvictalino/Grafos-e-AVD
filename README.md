<!-- [IA] Antigravity (Gemini) – atualização da estrutura, comandos e documentação do README -->
# Grafos-e-AVD

Projeto Final interdisciplinar das disciplinas de **Teoria dos Grafos** e **Análise e Visualização de Dados (AVD) — 2026.2** (CESAR School).

**Equipe (Turma 5B — Grupo 4):**
- Aline May Takakura
- David Magalhães Porto Oliveira
- Gabriel Victalino Mancebo
- Júlia Ventura Ferreira

O projeto é dividido em duas partes integradas:
- **Parte 1 — Labirinto com Chaves e Portas (Grafo de Estados):** leitura e validação de mapas em texto (`.txt`), construção do grafo de posições (`G_pos`) e do grafo de estados (`G_est`) por exploração com nó virtual `ALVO`, comparação de modelagens, execuções com implementações próprias de `BFS`, `DFS` (com classificação de arcos), `Dijkstra` (com recusa a peso negativo) e `Bellman-Ford` (com detecção e exibição de ciclo negativo e correção `--fonte-consumivel`), detecção de estados-armadilha via grafo transposto, 2 mapas próprios do grupo, 5 figuras estáticas obrigatórias e apresentação interativa em Streamlit (além do modo HTML interativo e do minijogo temático extra `taxi_labirinto`).
- **Parte 2 — Dataset Maior (TMDB), Comparação de Algoritmos e AVD:** construção de grafo dirigido e ponderado de filmes ligados por elenco compartilhado (`416.243` vértices válidos em `tmdb_limpo.csv.gz`, pesos negativos derivados de $\Delta\text{imdb\_rating}$), casos obrigatórios dos 4 algoritmos (incluindo recorte com ciclo negativo), benchmark e escalabilidade em `10%`, `50%` e `100%` (média de 5 execuções), e análise exploratória e explanatória com visualizações de AVD.

---

## Requisitos e Instalação

- **Python 3.11+** (ambiente testado com `.venv`).
- Dependências em `requirements.txt`: `streamlit>=1.30`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`, `kagglehub`, `networkx` *(usado exclusivamente como oráculo dentro de `tests/`)*, `pyvis` e `pytest`.

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
├─ app.py                                      # Labirinto interativo da Parte 1 (Streamlit)
├─ .streamlit/
│  └─ config.toml                              # Tema da interface Streamlit
├─ docs/
│  ├─ DECLARACAO_IA.pdf                        # Declaração de Uso de IA assinada por todos os integrantes
│  ├─ relatorio_parte1.md                      # Documentação técnica e manual da Parte 1
│  ├─ relatorio_parte2.md                      # Documentação técnica, benchmark e análise AVD da Parte 2
│  ├─ matriz_contribuicao_dados.md             # Contagem de commits por autor e por pasta (git log)
│  └─ rascunho_declaracao_ia.md                # Levantamento de conferência de usos de IA
├─ data/
│  ├─ mapas/                                   # 8 mapas fornecidos (m01_terreno.txt a m08_grande.txt)
│  ├─ mapas_grupo/                             # 2 mapas próprios do grupo (g01 e g02)
│  └─ dataset_parte2/
│     └─ tmdb_limpo.csv.gz                     # Dataset limpo da Parte 2 (416.243 filmes)
├─ out/
│  ├─ parte1/                                  # Arestas, graus, métricas, camadas, soluções, DFS, armadilhas, comparação e 5 PNGs
│  └─ parte2/                                  # parte2_report.json, parte2_tarefas.json, avd_parte2_stats.json e 9 PNGs
├─ notebooks/
│  ├─ projeto.ipynb                            # Exploração inicial do dataset bruto (AVD)
│  ├─ projeto_pos_limpeza.ipynb                # Limpeza, validação e checagem pós-tratamento
│  └─ exploracao_grafo_avd.ipynb               # Métricas do grafo, correlações e gráficos exploratórios
├─ src/
│  ├─ cli.py                                   # Interface de linha de comando (Parte 1 e Parte 2)
│  ├─ solve.py                                 # Orquestração da Parte 1 (lote/individual/HTML) e Parte 2 (algoritmos/benchmark)
│  ├─ viz.py                                   # Figuras da Parte 1 (--parte1), gráficos de benchmark e histogramas de grau (--graus)
│  ├─ comparacao_modelagem.py                  # Comparação de modelagens da Seção 6 (portas como chão × parede × G_est)
│  ├─ tarefas_parte2.py                        # Casos obrigatórios da Parte 2 (BFS/DFS, Dijkstra, Bellman-Ford com/sem ciclo)
│  ├─ avd_parte2.py                            # Visualizações exploratórias e explanatórias de AVD da Parte 2
│  └─ graphs/
│     ├─ algorithms.py                         # Implementações próprias de BFS, DFS, Dijkstra e Bellman-Ford
│     ├─ estados.py                            # Exploração do grafo de estados, camadas e estados-armadilha
│     ├─ graph.py                              # Classes adaptadoras (No e Aresta) compatíveis com algorithms.py
│     ├─ io.py                                 # Leitura do dataset TMDB e construção do grafo da Parte 2
│     └─ labirinto.py                          # Leitura, validação de mapas e estrutura do labirinto
├─ tests/                                      # Suíte automatizada (7 módulos, 44 testes em pytest)
│  ├─ test_bfs.py
│  ├─ test_dfs.py
│  ├─ test_dijkstra.py
│  ├─ test_bellman_ford.py
│  ├─ test_estados.py
│  ├─ test_io.py
│  └─ test_modelagem_e_atores.py
└─ taxi_labirinto/                             # Minijogo demonstrativo temático extra (Streamlit + HTML/JS)
```

---

## Como Executar

### Parte 1 — Labirinto com Chaves e Portas (Grafo de Estados)

1. **Exportar todas as saídas em lote da Parte 1** (`arestas_<mapa>.csv`, `graus_<mapa>.csv`, `metricas_global.json`, `camadas.json`, `solucoes.csv`, `dfs_classificacao.csv`, `percurso_m03.json`, `ciclo_negativo_m06.json`, `armadilhas_m04.csv`, `armadilhas_m07.csv`, `armadilhas_g02_armadilha.csv`):

```bash
python -m src.cli --exportar-parte1 data/mapas --out out/parte1
```

2. **Gerar a comparação de modelagens da Seção 6** (`out/parte1/comparacao_modelagem.csv` para `m02`, `m03` e `m04`):

<!-- [IA] Claude Code – comandos dos módulos src/comparacao_modelagem.py e src/tarefas_parte2.py -->
```bash
python -m src.comparacao_modelagem --out out/parte1
```

3. **Gerar as 5 figuras PNG obrigatórias da Seção 8** (`percurso_m03.png`, `percurso_m08.png`, `grafo_estados_m02.png`, `arvore_bfs_m02.png`, `heatmap_m08.png`):

```bash
python -m src.viz --parte1 --mapas data/mapas --out out/parte1
```

4. **Executar a CLI em um mapa individual** (útil para inspeção pontual e demonstração ao vivo com mapa surpresa):

```bash
python -m src.cli --mapa data/mapas/m03_tres_chaves.txt --alg BFS --out out/parte1
python -m src.cli --mapa data/mapas/m03_tres_chaves.txt --alg DIJKSTRA --out out/parte1
python -m src.cli --mapa data/mapas/m05_bonus.txt --alg BELLMAN_FORD --out out/parte1
python -m src.cli --mapa data/mapas/m06_fonte.txt --alg BELLMAN_FORD --fonte-consumivel --out out/parte1
python -m src.cli --mapa data/mapas/m04_esteiras.txt --armadilhas --out out/parte1
python -m src.cli --mapa data/mapas/m03_tres_chaves.txt --interactive --out out/parte1
python -m src.cli --mapa data/mapas_grupo/g02_armadilha.txt --armadilhas --out out/parte1
```

5. **Executar o labirinto interativo (Streamlit):**

```bash
streamlit run app.py
```

Recursos disponíveis em `app.py`: seleção de mapa (`data/mapas/` e `data/mapas_grupo/`), seleção de algoritmo (`BFS`, `Dijkstra`, `Bellman-Ford`, `DFS`), alternância entre `Grafo de estados` e `Grafo padrão`, animação passo a passo com controle de velocidade e slider, painéis separados por camada (conjunto de chaves), cartão do estado atual (posição, chaves, bônus consumidos, custo acumulado) e realce de estados-armadilha e ciclo negativo.

6. **Executar o minijogo demonstrativo extra (`taxi_labirinto`, opcional):**

```bash
streamlit run taxi_labirinto/jogo.py
```

---

### Parte 2 — Dataset Maior (TMDB), Comparação de Algoritmos e AVD

1. **Executar o benchmark de escalabilidade** (média de 5 execuções por algoritmo em `10%`, `50%` e `100%`, salvo em `out/parte2/parte2_report.json`):

```bash
python -m src.cli --dataset data/dataset_parte2/tmdb_limpo.csv.gz --benchmark --out out/parte2
```

2. **Executar os casos obrigatórios por algoritmo** (BFS/DFS em 3 fontes, Dijkstra em 5 pares, Bellman-Ford sem ciclo e com ciclo negativo, gravando `out/parte2/parte2_tarefas.json` e opcionalmente incorporando ao relatório):

```bash
python -m src.tarefas_parte2 --dataset data/dataset_parte2/tmdb_limpo.csv.gz --out out/parte2
# opcional: acrescenta a chave "tarefas" ao relatório existente, sem apagar "escalabilidade"
python -m src.tarefas_parte2 --dataset data/dataset_parte2/tmdb_limpo.csv.gz --out out/parte2 --relatorio out/parte2/parte2_report.json
```

3. **Executar um algoritmo específico entre origem e destino (IDs TMDB):**

```bash
python -m src.cli --dataset data/dataset_parte2/tmdb_limpo.csv.gz --alg DIJKSTRA --source <ID_ORIGEM> --target <ID_DESTINO> --out out/parte2
```

4. **Gerar os gráficos de comparação, escalabilidade, empírico vs. teórico e histogramas de grau** (`comparacao_algoritmos_barras.png`, `escalabilidade_algoritmos_linhas.png`, `empirico_vs_teorico.png`, `histograma_grau_entrada.png`, `histograma_grau_saida.png`):

```bash
python -m src.viz out/parte2/parte2_report.json --graus data/dataset_parte2/tmdb_limpo.csv.gz --out out/parte2
```

5. **Gerar as visualizações exploratórias e explanatórias de AVD** (`avd_e3_distribuicao_imdb_rating.png`, `avd_e4_distribuicao_pesos.png`, `avd_x1_sinal_variacao_nota.png`, `avd_x2_variacao_por_decada.png` e `avd_parte2_stats.json`):

```bash
python -m src.avd_parte2
```

---

### Testes Automatizados (`pytest`)

Para executar toda a suíte obrigatória (`44` testes cobrindo BFS, DFS dirigida, Dijkstra, Bellman-Ford, construção do grafo de estados com mapa mínimo conferido à mão, mapas próprios do grupo, validação IO e comparação de modelagens):

```bash
pytest tests/
```

> Nota: informe `tests/` explicitamente para evitar que o pytest colete a suíte independente `taxi_labirinto/tests/test_jogo.py` a partir da raiz.

---

## Documentação e Declaração de Uso de IA

- **Relatório Técnico + Manual da Parte 1:** `docs/relatorio_parte1.md`
- **Relatório Técnico + Comparação + AVD da Parte 2:** `docs/relatorio_parte2.md`
- **Matriz de Contribuição (dados do `git log`):** `docs/matriz_contribuicao_dados.md`
- **Declaração de Uso de IA (assinada por todos os integrantes):** `docs/DECLARACAO_IA.pdf`
- **Rascunho de conferência de uso de IA:** `docs/rascunho_declaracao_ia.md`
