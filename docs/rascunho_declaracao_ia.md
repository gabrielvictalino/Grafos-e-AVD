# Rascunho — Declaração de Uso de IA

> **Rascunho para conferência.** Foi montado a partir dos marcadores `# [IA] <ferramenta> – <finalidade>` encontrados no repositório e do histórico de trabalho do Claude. A equipe precisa conferir cada linha, completar o que ficou de fora (conversas com IA que não deixaram marcador no código) e só então copiar para a declaração oficial e assinar. Este arquivo não substitui `docs/DECLARACAO_IA.pdf`.

## 1. Usos encontrados no código (conferir)

| Ferramenta | Onde | Finalidade |
| :--- | :--- | :--- |
| Antigravity (Gemini) | `tests/test_bfs.py`, `test_dfs.py`, `test_dijkstra.py`, `test_bellman_ford.py`, `test_estados.py`, `test_io.py` | Testes unitários dos algoritmos, do grafo de estados e da leitura de mapas/dataset |
| Antigravity (Gemini) / Gemini | `src/cli.py` | Interface de linha de comando e a opção `--exportar-parte1` |
| Gemini | `notebooks/exploracao_grafo_avd.ipynb` (3 células) | Métricas estruturais do grafo em DataFrames; cruzamento de arestas com elenco e atributos; merge e matriz de correlação |
| ChatGPT | `notebooks/projeto_pos_limpeza.ipynb` (2 células) | Apoio com pandas: exclusão de colunas e remoção de registros incompletos; conversão e validação de datas |
| Claude | `app.py` (interface Streamlit) | Visual do app (tema, cartões, legenda, rastro colorido) e painéis separados por camada (chaves + bônus) |
| Claude | `src/graphs/labirinto.py`, `src/graphs/estados.py`, `src/solve.py` | Camada passa a ser identificada por (chaves, bônus consumidos): campo `bonus` em `Camada`, `rotulo_camada`, comparações nas camadas e rótulos em `camadas.json`. A lógica de exploração e de custos não foi alterada |
| Claude | `src/graficos_atores.py` | Gráficos de atores (variação de notas, constância, receita), idioma e produtoras. Escolha dos critérios (metades da carreira, mínimos de filmes) proposta pelo Claude; **a equipe precisa confirmar ou ajustar** |
| Claude | `src/viz.py` (`gerar_histogramas_grau`, `calcular_graus`) | Histogramas de grau de entrada e de saída (sintaxe matplotlib) |
| Antigravity (Gemini) | `src/viz.py` (`exportar_heatmap`, `exportar_percurso_mapa`, `exportar_grafo_estados_m02`, `exportar_arvore_bfs_m02`, `gerar_figuras_parte1`, `main`) | Apoio com sintaxe matplotlib para gerar as 5 figuras PNG obrigatórias da Parte 1 (percursos de `m03`/`m08`, grafo em camadas e árvore BFS de `m02`, heatmap de `m08`) e flags `--parte1`/`--mapas` na CLI |

Os arquivos `out/parte1/camadas.json`, `out/parte1/*.png` e `out/parte2/*.png` são saídas geradas por esse código.

## 2. Pontos para a equipe completar antes de assinar

- [ ] Conversas com ChatGPT, Gemini, Antigravity ou Claude que **não** deixaram marcador no código (ideias, depuração, explicações). Listar ferramenta, data aproximada e finalidade.
- [ ] `taxi_labirinto/`: não há marcadores `[IA]`. Confirmar se houve uso de IA.
- [ ] `docs/relatorio_parte1.md`, `docs/relatorio_parte2.md` e os checklists: confirmar quais trechos foram redigidos ou revisados com IA. Os blocos autorais (análises e notas) não podem ser feitos com IA.
- [ ] Versão do dataset: o Claude baixou a versão 1072 do dataset bruto do Kaggle (`alanvourch/tmdb-movies-daily-updates`) para gerar os gráficos de revenue, idioma e produtoras. Os notebooks usaram as versões 1069 e 1070. Decidir qual versão registrar.
- [ ] Verificar que todo trecho com apoio de IA tem o marcador `# [IA] <ferramenta> – <finalidade>`, como pede `docs/CHECKLIST_ENTREGA_PARTE1.md`.
- [ ] Assinatura de todos os integrantes e exportação para `docs/DECLARACAO_IA.pdf`.

## 3. O que a IA **não** fez

- Não escreveu as análises, interpretações e notas autorais dos relatórios.
- Não alterou os algoritmos (BFS, DFS, Dijkstra, Bellman-Ford) nem a lógica do grafo de estados.
