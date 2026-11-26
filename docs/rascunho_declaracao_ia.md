# Rascunho — Declaração de Uso de IA

> **Rascunho para conferência.** Foi montado a partir dos marcadores `# [IA] <ferramenta> – <finalidade>` encontrados no repositório e do histórico de trabalho do Claude. A equipe precisa conferir cada linha, completar o que ficou de fora (conversas com IA que não deixaram marcador no código) e só então copiar para a declaração oficial e assinar. Este arquivo não substitui `docs/DECLARACAO_IA.pdf`.

## 1. Usos encontrados no código (conferir)

| Ferramenta | Onde | Finalidade |
| :--- | :--- | :--- |
| Antigravity (Gemini) | `tests/test_bfs.py`, `test_dfs.py`, `test_dijkstra.py`, `test_bellman_ford.py`, `test_estados.py`, `test_io.py` | Testes unitários dos algoritmos, do grafo de estados (incluindo validação dos 2 mapas extras do grupo) e da leitura de mapas/dataset |
| Antigravity (Gemini) / Gemini | `src/cli.py`, `src/solve.py` | Interface de linha de comando, `--exportar-parte1`, orquestração individual da Parte 1 (`--mapa`, `--fonte-consumivel`, `--armadilhas`, `--interactive`) e exportação de `armadilhas_<mapa>.csv` para `data/mapas_grupo/` |
| Antigravity (Gemini) | `data/mapas_grupo/g01_chaves_esteiras_bonus.txt`, `g02_armadilha.txt` | Sugestão dos 2 mapas extras do grupo (conferidos e validados pelo código e pelos testes unitários em `tests/test_estados.py`) |
| Antigravity (Gemini) | `app.py` | Filtro de linhas comentadas (`;`) e linhas vazias na leitura da grade em `carregar` |
| Gemini | `notebooks/exploracao_grafo_avd.ipynb` (3 células) | Métricas estruturais do grafo em DataFrames; cruzamento de arestas com elenco e atributos; merge e matriz de correlação |
| ChatGPT | `notebooks/projeto_pos_limpeza.ipynb` (2 células) | Apoio com pandas: exclusão de colunas e remoção de registros incompletos; conversão e validação de datas |
| ChatGPT | `src/graphs/algorithms.py` (`bellman_ford_sem_ciclo_negativo`); `taxi_labirinto/jogo.py`, `utils.py`, `componente/index.html` | Revisão conceitual da modelagem de bônus consumíveis e apoio ao desenho/integração do minijogo de táxi; conferir a implementação e os marcadores com o grupo |
| Claude | `app.py` (interface Streamlit) | Visual do app (tema, cartões, legenda, rastro colorido) e painéis separados por camada (conjunto de chaves) |
| Claude | `src/viz.py` (`gerar_histogramas_grau`, `calcular_graus`) | Histogramas de grau de entrada e de saída (sintaxe matplotlib) |
| Antigravity (Gemini) | `src/viz.py` (`exportar_heatmap`, `exportar_percurso_mapa`, `exportar_grafo_estados_m02`, `exportar_arvore_bfs_m02`, `gerar_figuras_parte1`, `main`) | Apoio com sintaxe matplotlib para gerar as 5 figuras PNG obrigatórias da Parte 1 (percursos de `m03`/`m08`, grafo em camadas e árvore BFS de `m02`, heatmap de `m08`) e flags `--parte1`/`--mapas` na CLI |

| Claude Code | `data/mapas/` (movida de `mapas/`), `app.py`, `src/cli.py`, `src/solve.py`, `src/viz.py`, `tests/test_io.py`, `README.md` | Mover os mapas com `git mv` e atualizar os caminhos que apontavam para `mapas` |
| Claude Code | `tests/test_bellman_ford.py` | 2 testes sugeridos (ciclo negativo detectado e devolvido; peso negativo sem ciclo), com cálculo à mão nos comentários |
| Claude Code | `tests/test_modelagem_e_atores.py` | 3 testes sugeridos para `comparacao_modelagem` e `variacao_consecutiva_por_ator`, com conta à mão nos comentários (**o grupo precisa conferir**) |
| Claude Code | `src/comparacao_modelagem.py` | Orquestração da Seção 6 (BFS em G_pos com portas como chão, G_pos com portas como parede e G_est) chamando as funções do grupo; validade do caminho conferida por simulação |
| Claude Code | `src/tarefas_parte2.py` | Orquestração das tarefas da Parte 2 (BFS/DFS em 3 fontes, Dijkstra em 5 pares, Bellman-Ford sem ciclo e com ciclo negativo) chamando os algoritmos do grupo. A transformação do caso de ciclo negativo é só uma **proposta**: o grupo decide |
| Claude Code | `notebooks/exploracao_grafo_avd.ipynb` (células no fim) | Sintaxe pandas/matplotlib para os histogramas de grau e para 6 gráficos pedidos pela equipe (barras de atores que mais diminuíram/aumentaram, boxplot de constância, dispersão com tendência, boxplots por idioma e por produtora). Os tipos de gráfico e a pergunta vieram da equipe; os valores dos parâmetros (mínimos de filmes, quantos mostrar) ficam numa célula marcada como **decisão do grupo** |
| Claude Code | `docs/matriz_contribuicao_dados.md` | Contagem de commits por autor e por pasta a partir do `git log` (dados, sem comentários) |
| Claude Code | `README.md` | Versão do Python, lista de comandos do CLI e comandos dos módulos novos |

Os arquivos `out/parte1/camadas.json`, `out/parte1/*.png` e `out/parte2/*.png` são saídas geradas por esse código.

## 2. Pontos para a equipe completar antes de assinar

- [ ] Conversas com ChatGPT, Gemini, Antigravity ou Claude que **não** deixaram marcador no código (ideias, depuração, explicações). Listar ferramenta, data aproximada e finalidade.
- [ ] `taxi_labirinto/`: foram adicionados marcadores `[IA] ChatGPT` com base no histórico compartilhado; grupo deve conferir o escopo exato da contribuição.
- [ ] `docs/relatorio_parte1.md`, `docs/relatorio_parte2.md` e os checklists: confirmar quais trechos foram redigidos ou revisados com IA. Os blocos autorais (análises e notas) não podem ser feitos com IA.
- [ ] Versão do dataset: o Claude baixou a versão 1072 do dataset bruto do Kaggle (`alanvourch/tmdb-movies-daily-updates`) para gerar os gráficos de revenue, idioma e produtoras. Os notebooks usaram as versões 1069 e 1070. Decidir qual versão registrar.
- [ ] Verificar que todo trecho com apoio de IA tem o marcador `# [IA] <ferramenta> – <finalidade>`, como pede `docs/CHECKLIST_ENTREGA_PARTE1.md`.
- [ ] Assinatura de todos os integrantes e exportação para `docs/DECLARACAO_IA.pdf`.

## 3. Conferência contra as regras de uso de IA do enunciado

**Permitido (com registro):** tirar dúvidas conceituais; depurar código do grupo; sugerir casos de teste e mapas extras, conferidos pelo grupo; apoio com pandas e bibliotecas de visualização; revisão de ortografia e clareza.
**Proibido:** gerar BFS, DFS, Dijkstra, Bellman-Ford ou a construção do grafo de estados; gerar análises, discussões, conclusões, notas analíticas ou a prova do m05; pedir que a IA interprete gráficos, escolha o tipo de gráfico ou os elementos de destaque, ou monte a história explanatória; pedir que a IA resolva os mapas; entregar trecho que ninguém sabe explicar.

**Removido do repositório por ser proibido ou de risco** (continua visível só no histórico do git):
- A mudança de camadas por (chaves, bônus) em `estados.py`, `labirinto.py` e `solve.py`. Voltou ao original: a camada é o conjunto de chaves.
- O módulo de gráficos de atores (`src/graficos_atores.py`) e as 6 imagens geradas por ele: os critérios e destaques foram escolhidos pelo Claude. Os mesmos gráficos voltaram como células do notebook, a pedido da equipe, com os critérios em parâmetros que o grupo deve definir e sem cores de destaque escolhidas pelo Claude.

**O que o Claude fez e permanece:**

| Trabalho do Claude | Enquadramento | Situação |
| :--- | :--- | :--- |
| Testes novos (`test_bellman_ford.py`, `test_modelagem_e_atores.py`) | Permitido: sugerir casos de teste | Grupo precisa conferir os valores à mão (estão nos comentários) |
| Caminhos `data/mapas`, README, matriz de contribuição, `.pyc` fora do git | Organização e dados, sem análise | Sem pendência |
| Histogramas de grau (`viz.py` e notebook) | Sintaxe matplotlib de um gráfico que o enunciado já define | Grupo escreve a interpretação |
| `comparacao_modelagem.py` e `tarefas_parte2.py` | Orquestração; os algoritmos chamados são do grupo | Grupo precisa saber explicar o código. O caso de ciclo negativo é só proposta: a decisão é do grupo |
| Visual do `app.py` (cartões, painéis por camada) | Apoio com biblioteca de visualização | Grupo precisa saber explicar |


