# Checklist de Entrega Final — Parte 2 (Dataset TMDB + Comparação + AVD)

**Prazo de entrega no Classroom:** `26/11/2026` (todos os integrantes da equipe devem postar todo o material + link do repositório).

---

## 1. O que já está pronto no repositório

- [x] Dataset limpo salvo em `data/dataset_parte2/tmdb_limpo.csv.gz` (`416.243` filmes válidos, `5` colunas, `0` nulos).
- [x] Construção do grafo dirigido e ponderado em `src/graphs/io.py` (`carregar_grafo_tmdb`), com pesos negativos originais (`imdb_rating(v) - imdb_rating(u)`) e transformação não negativa (`+10.0`) para Dijkstra.
- [x] Notebooks de exploração e limpeza registrados em `notebooks/projeto.ipynb`, `notebooks/projeto_pos_limpeza.ipynb` e `notebooks/exploracao_grafo_avd.ipynb` (métricas globais do grafo, sinal dos pesos, hubs, matriz de correlação, outliers IQR e correlações de ausências).
- [x] CLI e benchmark implementados em `src/cli.py` e `src/solve.py` (`--benchmark` com escalas `10%`, `50%`, `100%` e `5` repetições; `--alg` com `--source`/`--target`).
- [x] Script de gráficos comparativos de desempenho em `src/viz.py` (`comparacao_algoritmos_barras.png` e `escalabilidade_algoritmos_linhas.png`).
- [x] Rascunho técnico da Parte 2 + AVD (`docs/relatorio_parte2.md`) preenchido com todas as métricas e dados já disponíveis no projeto.

---

## 2. Pendências Obrigatórias antes da Entrega (`26/11/2026`)

### Experimentos, `out/parte2/` e Código
- [ ] **Gerar `out/parte2/parte2_report.json` e gráficos de comparação:** a pasta `out/parte2/` ainda não foi gerada neste repositório. Executar:
  ```bash
  python -m src.cli --dataset data/dataset_parte2/tmdb_limpo.csv.gz --benchmark --out out/parte2
  python -m src.viz out/parte2/parte2_report.json --out out/parte2
  ```
- [ ] **Executar e registrar todos os casos obrigatórios** (tanto em `out/parte2/parte2_report.json` quanto nas tabelas da Seção 4 de `docs/relatorio_parte2.md`):
  - **BFS / DFS** a partir de **$\ge 3$ fontes distintas** (relatar ordem, camadas e ciclos).
  - **Dijkstra** em **$\ge 5$ pares origem–destino** (com pesos deslocados $\ge 0$).
  - **Bellman-Ford** com pelo menos **1 caso com peso negativo sem ciclo negativo** (grafo cronológico padrão) e **1 caso com ciclo negativo** (detectado e exibido).
- [ ] **Construir e documentar o caso de ciclo negativo no Bellman-Ford:** como `carregar_grafo_tmdb` impõe `datas[i] < datas[j]` (tornando o grafo completo um DAG), criar e documentar um recorte ou transformação legítima dos dados que gere ao menos um ciclo negativo detectado e exibido pelo algoritmo.

### Análise de Dados e Visualizações (AVD)
- [ ] **Gerar e salvar em `out/parte2/` no mínimo 6 visualizações de AVD** (`4` exploratórias + `2` explanatórias, sendo ao menos `1` respondendo à pergunta de pesquisa), garantindo em **todas**:
  - Título, legenda e identificação clara dos eixos;
  - Sem gráficos de pizza ou radar (salvo justificativa muito forte);
  - Sem distorções visuais;
  - Exploração de distribuição de graus de entrada e de saída do grafo;
  - Exploração multivariada completa cruzando o atributo-alvo com os demais atributos (`budget`, `revenue`, `popularity`, `runtime`, `genres`, etc. — usando o dataset completo de 27 colunas, já que `tmdb_limpo.csv.gz` tem apenas 5 colunas).

### Redação Autoral e PDF Final (Proibido usar IA para análises/notas)
- [ ] **Preencher todos os blocos `[AUTORAL — PREENCHER PELO GRUPO]` em `docs/relatorio_parte2.md`:**
  - Pergunta de pesquisa oficial, justificativa da amostragem em `500.000` arestas e significado no domínio de "caminho mínimo" e "ciclo negativo" (Seção 1).
  - Discussão do **mecanismo de ausência** (MCAR/MAR/MNAR) e justificativa do tratamento dos dados faltantes (Seção 3.2).
  - Interpretação das distribuições e da exploração multivariada completa (Seções 3.3 e 3.4).
  - Análise da transformação `+10.0` no Dijkstra e documentação do caso com ciclo negativo no Bellman-Ford (Seções 4.2 e 4.3).
  - Comparação do crescimento empírico de tempo com a complexidade teórica (Seção 5).
  - Raciocínio **"da exploratória à explanatória" (storytelling)** + **notas analíticas autorais** individuais para cada uma das $\ge 6$ visualizações (Seção 6).
  - Discussão crítica (adequação de cada algoritmo, limites do design de pesos e **resposta fundamentada à pergunta de pesquisa**) (Seção 7).
- [ ] **Consolidar `docs/relatorio_parte1.md` + `docs/relatorio_parte2.md` em um único PDF técnico** e enviar junto com `docs/DECLARACAO_IA.pdf` assinada por todos no Classroom em `26/11/2026`.
