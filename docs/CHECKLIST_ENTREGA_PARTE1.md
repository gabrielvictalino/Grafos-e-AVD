# Checklist de Entrega Final — Parte 1 (Labirinto com Chaves e Portas)

**Prazo de entrega no Classroom:** `26/11/2026` (todos os integrantes da equipe devem postar todo o material + link do repositório).

---

## 1. O que já está pronto no repositório

- [x] Implementações próprias dos 4 algoritmos (`BFS`, `DFS` com classificação de arcos, `Dijkstra` com recusa a peso negativo e `Bellman-Ford` com detecção e exibição de ciclo negativo) em `src/graphs/algorithms.py`.
- [x] Construção do grafo de posições (`G_pos`) e do grafo de estados (`G_est`) por exploração com nó virtual `ALVO` e busca de estados-armadilha no grafo transposto em `src/graphs/estados.py` e `src/graphs/labirinto.py`.
- [x] Exportação em `out/parte1/` dos arquivos para `m01`–`m08`:
  - `arestas_m01.csv` .. `arestas_m08.csv`
  - `graus_m01.csv` .. `graus_m08.csv`
  - `metricas_global.json`, `camadas.json`, `solucoes.csv`, `dfs_classificacao.csv`
  - `percurso_m03.json`, `ciclo_negativo_m06.json`, `armadilhas_m04.csv`, `armadilhas_m07.csv`
- [x] Aplicação interativa da Parte 1 em Streamlit (`app.py`) com animação passo a passo, controle de velocidade, camadas, painel do estado e realces de armadilhas/ciclo negativo.
- [x] Conferência manual do mapa mínimo de teste (`tests/test_estados.py`).
- [x] `README.md` atualizado com instalação, estrutura, comandos de execução e link da declaração de IA.
- [x] Rascunho técnico completo da Parte 1 (`docs/relatorio_parte1.md`) com todos os números e tabelas já extraídos de `out/parte1/`.

---

## 2. Pendências Obrigatórias antes da Entrega (`26/11/2026`)

### Documentação e Compliance (Crítico)
- [ ] **Gerar e assinar `docs/DECLARACAO_IA.pdf`:** usar o modelo fornecido pela professora, preencher usos (ou compartilhar links das conversas completas), incluir a **reflexão de 10 a 15 linhas** e coletar a **assinatura de todos os integrantes** (manuscrita ou digital, ex.: gov.br). *(Ausência ou falta de assinatura = **nota ZERO** no projeto.)*
- [ ] **Redigir todos os trechos `[AUTORAL — PREENCHER PELO GRUPO]` em `docs/relatorio_parte1.md`:**
  - Por que um grafo não dirigido estaria errado (Seção 1.4).
  - Por que a multiplicidade máxima no `m08` é `5` em `165` casas e comentário sobre teto teórico vs. estados alcançáveis (Seção 2.2).
  - Por que somente chaves/bônus geram arcos entre camadas (Seção 2.3).
  - Análise de `comparacao_modelagem.csv`: por que portas como chão é inválido e portas como parede falha (Seção 3.1).
  - Resultado de Bellman-Ford em `G_pos` do `m05` e **prova curta** de ausência de ciclo negativo em `G_est` do `m05` (Seção 3.2).
  - Discussões obrigatórias de `m01`, `m06` (proposta `--fonte-consumivel` + resultado finito) e `m07` (Seção 4.5).
  - Limitações e conclusões da Parte 1 (Seção 8).
  - Matriz de contribuição confirmada com Dono e Revisor por pacote (Seção 9).
- [ ] **Consolidar o PDF técnico único** (Manual + Parte 1 + Parte 2 + AVD + Matriz de contribuição) a partir de `docs/relatorio_parte1.md` e das análises da Parte 2/AVD.

### Código, Outputs e Testes Faltantes da Parte 1
- [ ] **Gerar `out/parte1/comparacao_modelagem.csv`:** rodar BFS em `m02`, `m03` e `m04` nas 3 modelagens (portas como chão, portas como parede, grafo de estados).
- [x] **Implementar `--mapa` e `--fonte-consumivel` na CLI (`src/cli.py` / `src/solve.py`):** conectados e prontos tanto para demonstrar a correção do `m06` quanto para a **demonstração ao vivo com mapa surpresa** na apresentação.
- [x] **Criar os 2 mapas próprios em `data/mapas_grupo/`:**
  1. `g01_chaves_esteiras_bonus.txt` ($\ge 3$ chaves + esteiras + bônus: caminho ótimo via Bellman-Ford coleta os 2 bônus e passa por 5 esteiras).
  2. `g02_armadilha.txt` (`43/105` = `40.95%` dos estados alcançáveis são estados-armadilha).
  - Exportação (`--exportar-parte1`) reexecutada em `out/parte1/` e gabarito preenchido na Seção 6 de `docs/relatorio_parte1.md`.
- [x] **Gerar as 5 figuras PNG obrigatórias da Seção 8 em `out/parte1/`** (todas com título, legenda e rótulos):
  1. `out/parte1/percurso_m03.png` (cor mudando a cada chave)
  2. `out/parte1/percurso_m08.png` (cor mudando a cada chave)
  3. `out/parte1/grafo_estados_m02.png` (grafo de estados do `m02` em camadas)
  4. `out/parte1/arvore_bfs_m02.png` (árvore BFS de estados do `m02` com níveis visíveis)
  5. `out/parte1/heatmap_m08.png` (multiplicidade por casa)
- [x] **Corrigir falha atual em `tests/test_io.py`:** `validar_labirinto` e `gerar_labirinto` ignoram linhas comentadas com `;` e toda a suíte `pytest tests/` está passando.
- [ ] **Verificar se os mapas em `mapas/` precisam estar também em `data/mapas/`** (conforme a árvore literal de pastas do enunciado).
- [x] **Garantir commits de todos em pelo menos 2 pacotes** no repositório GitHub (verificado no histórico Git: todos os 4 integrantes possuem commits em $\ge 3$ pacotes).
- [ ] **Verificar marcações `# [IA] <ferramenta> – <finalidade>`** em todos os trechos de código feitos com apoio de IA dentro das diretrizes permitidas.
