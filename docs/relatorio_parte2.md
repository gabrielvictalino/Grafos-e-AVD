# Relatório Técnico e Análise Visual (AVD) — Parte 2: Dataset Maior (TMDB)

- **Disciplinas:** Teoria dos Grafos + Análise e Visualização de Dados (AVD)
- **Equipe:**
  - Aline Takakura
  - David Magalhães
  - Gabriel Victalino Mancebo
  - Júlia Ferreira

> **Aviso de conformidade (Diretrizes de IA):** Conforme as regras da disciplina, todas as interpretações, discussões críticas, justificativas de análise de dados/gráficos, narrativa (*storytelling*), notas analíticas das visualizações e resposta à pergunta de pesquisa devem ser **autorais do grupo**. Neste documento, todos os números, métricas estruturais, tabelas de limpeza, distribuições, correlações e limites de *outliers* foram extraídos diretamente de `src/graphs/io.py`, `src/solve.py`, `data/dataset_parte2/tmdb_limpo.csv.gz` e dos notebooks em `notebooks/`, enquanto os trechos que exigem redação autoral estão marcados com **`[AUTORAL — PREENCHER PELO GRUPO]`**.

---

## 1. Proposta do Dataset, Domínio e Pergunta de Pesquisa

- **Fonte:** Kaggle — *TMDB Movies Daily Updates* (`alanvourch/tmdb-movies-daily-updates`, arquivo `TMDB_all_movies.csv`, versão 1072, dados coletados da API do TMDB).
- **Domínio:** Cinema / rede cronológica de filmes conectados por elenco compartilhado (não aéreo e não grade/labirinto).
- **Tipo do grafo:** **Dirigido** e **ponderado**, com pesos negativos derivados diretamente das avaliações dos filmes (`imdb_rating`).
- **Dimensão construída em `src/graphs/io.py`:** $|V| = 416.243$ vértices (filmes únicos válidos) e $|E| = 500.000$ arestas dirigidas (teto configurado por `max_arestas=500_000`).

> **`[AUTORAL — PREENCHER PELO GRUPO]`**
> 1. **Pergunta de pesquisa (aprovada no checkpoint de 12/10/2026):** `[TRANSCREVER A PERGUNTA DE PESQUISA OFICIAL DO GRUPO]`
> 2. **Justificativa da amostragem/corte (`max_arestas = 500_000`):** explicar por que o corte em `500.000` arestas foi adotado (critério do enunciado para datasets acima de ~500 mil arestas) e como a ordenação cronológica (`release_date`, `id`) e o índice invertido por ator determinam o recorte do grafo.
> 3. **Significado no domínio:** explicar o que representam, no contexto cinematográfico escolhido pelo grupo, um **"caminho mínimo"** (sequência de filmes ligados por atores com menor soma de variação de `imdb_rating`) e um **"ciclo negativo"**.

---

## 2. Descrição e Modelagem do Grafo (`src/graphs/io.py`)

### 2.1 Regras de Construção (`carregar_grafo_tmdb`)

1. **Vértices ($V$):** cada filme único (`id` sem duplicatas) com valores válidos em `id`, `title`, `release_date`, `imdb_rating` e `cast`, ordenado cronologicamente por `(release_date, id)`.
2. **Arestas ($E$) e direção:** para cada ator presente na coluna `cast`, percorre-se pares de filmes $(u, v)$ em que o ator participou; existe arco dirigido $u \to v$ sempre que `release_date(u) < release_date(v)` (do filme mais antigo para o filme mais recente), sem arestas paralelas (`arestas_vistas` garante unicidade do par $(u, v)$).
3. **Pesos originais (Bellman-Ford):**
   $$\text{peso}(u \to v) = \text{imdb\_rating}(v) - \text{imdb\_rating}(u) \in [-10{,}0;\; +10{,}0]$$
   - Peso **negativo** ($< 0$): queda de nota IMDb entre o filme anterior e o posterior com ator em comum.
   - Peso **positivo** ($> 0$): aumento de nota IMDb.
   - Peso **zero** ($= 0$): mesma nota IMDb.
4. **Transformação não negativa (Dijkstra):** com `transformacao_peso="nao_negativo"`, aplica-se deslocamento aditivo constante:
   $$\text{peso}_{\text{Dijkstra}}(u \to v) = \text{peso}(u \to v) + 10{,}0 \ge 0$$
5. **Aciclicidade do grafo completo:** como a condição `datas[i] < datas[j]` impõe ordem temporal estrita, o grafo construído por `carregar_grafo_tmdb` é um **DAG** (Grafo Acíclico Dirigido): possui arcos negativos, porém **sem ciclos negativos** no grafo completo.

### 2.2 Métricas Globais e Distribuição de Pesos (`notebooks/exploracao_grafo_avd.ipynb`)

| Métrica | Valor observado |
| :--- | ---: |
| Ordem ($\|V\|$) | `416.243` |
| Tamanho ($\|E\|$) | `500.000` |
| Densidade dirigida ($\frac{\|E\|}{\|V\|(\|V\|-1)}$) | `0.00000289` |
| Arestas com peso positivo ($> 0$) | `292.659` (`58,53%`) |
| Arestas com peso negativo ($< 0$) | `190.441` (`38,09%`) |
| Arestas com peso zero ($= 0$) | `16.900` (`3,38%`) |

### 2.3 Top 10 Vértices (Hubs) por Grau Total (`notebooks/exploracao_grafo_avd.ipynb`)

| Posição | `id` | Título (`title`) | Grau de entrada | Grau de saída | Grau total |
| ---: | :--- | :--- | ---: | ---: | ---: |
| 1 | `194055` | *1776, or The Hessian Renegades* | 173 | 836 | 1009 |
| 2 | `193964` | *The Usurer* | 241 | 725 | 966 |
| 3 | `384913` | *A Strange Meeting* | 135 | 820 | 955 |
| 4 | `487462` | *The Newlyweds* | 197 | 750 | 947 |
| 5 | `522108` | *The Long Road* | 204 | 726 | 930 |
| 6 | `334061` | *The Primal Call* | 168 | 740 | 908 |
| 7 | `193953` | *Fighting Blood* | 216 | 683 | 899 |
| 8 | `418136` | *The Two Brothers* | 213 | 677 | 890 |
| 9 | `194000` | *The Oath and the Man* | 242 | 636 | 878 |
| 10 | `387015` | *The Broken Locket* | 156 | 722 | 878 |

*(Complementar com histograma/distribuição completa de graus de entrada e saída exportada em `out/parte2/`.)*

---

## 3. Exploração dos Dados pelos 4 Pilares de AVD

### 3.1 Pilar Estrutural e Pipeline de Limpeza

| Etapa do dataset | Registros (linhas) | Colunas | Duplicatas | Observações |
| :--- | ---: | ---: | ---: | :--- |
| **Bruto (`TMDB_all_movies.csv`)** | `1.278.466` | `30` | `0` | `imdb_rating` ausente em `62,05%`; `cast` em `31,54%`; `release_date` em `10,84%` |
| **Pós-limpeza (`projeto_pos_limpeza.ipynb`)** | `416.470` | `27` | `0` | Remoção de `music_composer`, `tagline`, `certification_us` e de nulos em `title`, `release_date`, `imdb_rating`, `cast`; `0` datas inválidas (`1878-06-19` a `2028-05-10`) |
| **Arquivo do grafo (`tmdb_limpo.csv.gz`)** | `416.243` | `5` | `0` | Colunas `id`, `title`, `release_date`, `cast`, `imdb_rating`; `0` nulos (após deduplicação por `id` e leitura em `io.py`) |

Classificação dos atributos adotada nos notebooks (`projeto_pos_limpeza.ipynb`):
- **Quantitativas (8):** `vote_average`, `vote_count`, `revenue`, `runtime`, `budget`, `popularity`, `imdb_rating`, `imdb_votes`.
- **Qualitativas (13 + 6 de alta cardinalidade):** `status`, `release_date`, `original_language`, `genres`, `production_companies`, `production_countries`, `spoken_languages`, `cast`, `director`, `director_of_photography`, `writers`, `producers`, `keywords` (e alta cardinalidade: `id`, `imdb_id`, `title`, `poster_path`, `original_title`, `overview`).

### 3.2 Qualidade, Dados Faltantes e Mecanismo de Ausência

Percentuais de ausência observados antes e depois da limpeza:

| Coluna | % Ausente (Bruto, $n=1.278.466$) | % Ausente (Pós-limpeza, $n=416.470$) | Ação tomada |
| :--- | ---: | ---: | :--- |
| `certification_us` | `92,60%` | — | Coluna removida |
| `music_composer` | `88,38%` | — | Coluna removida |
| `tagline` | `84,54%` | — | Coluna removida |
| `director_of_photography` | `72,43%` | `52,16%` | Mantida no dataset completo |
| `keywords` | `71,45%` | `55,50%` | Mantida no dataset completo |
| `producers` | `65,27%` | `43,05%` | Mantida no dataset completo |
| `imdb_rating` / `imdb_votes` | `62,05%` | `0,00%` | Linhas sem `imdb_rating` removidas (obrigatória no peso) |
| `production_companies` | `51,45%` | `27,32%` | Mantida no dataset completo |
| `writers` | `49,12%` | `20,23%` | Mantida no dataset completo |
| `imdb_id` | `45,20%` | `0,00%` | Zerou após exigir `imdb_rating` |
| `production_countries` | `37,15%` | `15,06%` | Mantida no dataset completo |
| `spoken_languages` | `36,26%` | `14,98%` | Mantida no dataset completo |
| `cast` | `31,54%` | `0,00%` | Linhas sem `cast` removidas (obrigatória nas arestas) |
| `genres` | `26,30%` | `6,03%` | Mantida no dataset completo |
| `poster_path` | `23,86%` | `8,10%` | Mantida no dataset completo |
| `director` | `16,01%` | `2,90%` | Mantida no dataset completo |
| `overview` | `15,40%` | `4,72%` | Mantida no dataset completo |
| `release_date` | `10,84%` | `0,00%` | Linhas sem data removidas (obrigatória na direção) |
| `title` / `original_title` | `0,001%` | `0,00%` | Linhas sem título removidas |

Correlações entre ausências identificadas no dataset bruto (`projeto.ipynb`):
- `original_title` e `title`: `1,00`
- `imdb_votes` e `imdb_rating`: `1,00`
- `imdb_rating` e `imdb_id`: `0,71`
- `imdb_votes` e `imdb_id`: `0,71`

> **`[AUTORAL — PREENCHER PELO GRUPO]`**
> - Discutir o **mecanismo de ausência** (se é MCAR, MAR ou MNAR — ex.: por que filmes sem `imdb_id` ou lançamentos muito obscuros/antigos tendem a não ter `imdb_rating` nem `imdb_votes`, como mostra a correlação `0,71`) e justificar o tratamento adotado (remoção apenas nas 4 colunas estruturais do grafo vs. preservação nas demais, avaliando eventual viés introduzido).

### 3.3 Pilar Distribucional

Medidas de dispersão no dataset pós-limpeza (`projeto_pos_limpeza.ipynb`, $n = 416.470$):

| Variável quantitativa | Variância | Desvio-padrão | IQR |
| :--- | ---: | ---: | ---: |
| `vote_average` | `9,26` | `3,04` | `6,50` |
| `vote_count` | `418.670,30` | `647,05` | `9,00` |
| `revenue` | `8,336580e+14` | `28.873.136,78` | `0,00` |
| `runtime` | `2.791,58` | `52,84` | `65,00` |
| `budget` | `6,277760e+13` | `7.923.231,93` | `0,00` |
| `popularity` | `15,29` | `3,91` | `1,09` |
| `imdb_rating` | `1,72` | `1,31` | `1,70` |
| `imdb_votes` | `1,242914e+09` | `35.254,99` | `308,00` |

Resumo específico da variável de peso `imdb_rating` no arquivo do grafo (`tmdb_limpo.csv.gz`, $n = 416.243$):
- **Média:** `6,1840` | **Desvio-padrão:** `1,3130`
- **Mínimo:** `1,0` | **Q1 (25%):** `5,4` | **Mediana (50%):** `6,3` | **Q3 (75%):** `7,1` | **Máximo:** `10,0`

Principais categorias qualitativas pós-limpeza (`projeto_pos_limpeza.ipynb`):
- `status`: `Released` = `416.428` (`~100%`); `Post Production` = `28`; `In Production` = `11`; `Canceled`, `Rumored`, `Planned` = `1` cada.
- `original_language`: `en` (`200.872` / `48,2%`), `fr` (`23.480` / `5,6%`), `es` (`23.143` / `5,6%`), `de` (`21.175` / `5,1%`), `ja` (`14.429` / `3,5%`).

> **`[AUTORAL — PREENCHER PELO GRUPO]`**
> - Interpretar as distribuições (assimetria forte à direita em `revenue`, `budget`, `vote_count`, `imdb_votes` e `popularity`, pico de zeros em variáveis financeiras e distribuição aproximadamente simétrica/concentrada em `imdb_rating`).

### 3.4 Pilar Relacional e Exploração Multivariada

Correlações já obtidas nos notebooks:
- **No dataset bruto (`projeto.ipynb`, Spearman):** `vote_count` × `vote_average = 0,94`; `imdb_votes` × `vote_count = 0,78`.
- **Nas arestas do grafo (`exploracao_grafo_avd.ipynb`, correlação com o `peso`):**
  - `imdb_rating` do filme de destino: **Pearson `0,652148`** | **Spearman `0,618118`**
  - `ano` de lançamento do filme de destino: **Pearson `0,034871`** | **Spearman `0,012559`**

> **Nota técnica importante:** `data/dataset_parte2/tmdb_limpo.csv.gz` contém apenas 5 colunas (`id`, `title`, `release_date`, `cast`, `imdb_rating`). Para cumprir integralmente o critério de AVD de **exploração multivariada** (mapear o atributo-alvo/variável central com **os demais atributos**, não apenas 1 ou 2), utilizar o dataframe de 27 colunas gerado em `notebooks/projeto_pos_limpeza.ipynb` cruzando com `budget`, `revenue`, `popularity`, `runtime`, `vote_average`, `vote_count`, `imdb_votes`, `genres`, `original_language` e atributos do grafo.

> **`[AUTORAL — PREENCHER PELO GRUPO]`**
> - Apresentar e interpretar as relações multivariadas entre o atributo-alvo (`imdb_rating` / variação de nota `peso`) e os demais atributos do dataset, classificando cada relação como **direta/inversa**, **linear/não linear** e **forte/moderada/fraca**.

### 3.5 Detecção e Tratamento de Outliers (Regra do IQR)

Resultados da detecção por IQR ($[Q_1 - 1{,}5 \cdot \text{IQR},\; Q_3 + 1{,}5 \cdot \text{IQR}]$) no dataset pós-limpeza (`projeto_pos_limpeza.ipynb`):

| Variável | Limite inferior | Limite superior | Nº de outliers |
| :--- | ---: | ---: | ---: |
| `vote_average` | `-9,75` | `16,25` | `0` |
| `vote_count` | `-13,50` | `22,50` | `59.530` |
| `revenue` | `0,00` | `0,00` | `22.823` |
| `runtime` | `-64,50` | `195,50` | `2.021` |
| `budget` | `0,00` | `0,00` | `35.208` |
| `popularity` | `-1,30` | `3,06` | `23.267` |
| `imdb_rating` | `2,85` | `9,65` | `6.372` |
| `imdb_votes` | `-438,00` | `794,00` | `64.363` |

Decisão registrada pelo grupo em `notebooks/projeto_pos_limpeza.ipynb`:
> Os valores classificados como outliers pelo IQR não foram automaticamente removidos, pois representam observações legítimas do domínio (filmes com alta popularidade, grande volume de votos, grandes orçamentos/receitas ou notas extremas válidas de 1 a 10). O tratamento considera a validade do registro no domínio, e não apenas a distância estatística ao centro. *(Complementar no PDF se houver qualquer filtro adicional específico para visualizações de AVD, ex.: recortes de `runtime` ou escala log.)*

---

## 4. Execução dos 4 Algoritmos e Casos Obrigatórios

### 4.1 BFS e DFS ($\ge 3$ Fontes Distintas)

*(Preencher após executar os testes com $\ge 3$ filmes-fonte.)*

| Fonte (`id` — Título) | Algoritmo | Vértices alcançados | Camadas / Profundidade máx. | Ciclo detectado? | Tempo (ms) |
| :--- | :--- | ---: | ---: | :--- | ---: |
| `[PREENCHER Fonte 1]` | BFS | — | — | — | — |
| `[PREENCHER Fonte 1]` | DFS | — | — | — | — |
| `[PREENCHER Fonte 2]` | BFS | — | — | — | — |
| `[PREENCHER Fonte 2]` | DFS | — | — | — | — |
| `[PREENCHER Fonte 3]` | BFS | — | — | — | — |
| `[PREENCHER Fonte 3]` | DFS | — | — | — | — |

### 4.2 Dijkstra ($\ge 5$ Pares Origem–Destino com Pesos $\ge 0$)

**Transformação de pesos utilizada (`src/graphs/io.py`):** como `imdb_rating` varia de `0` a `10` (na prática `1.0` a `10.0`), a diferença $\text{imdb\_rating}(v) - \text{imdb\_rating}(u)$ tem mínimo teórico `-10,0`. Ao usar `transformacao_peso="nao_negativo"`, cada arco recebe `peso + 10.0 >= 0`, permitindo a execução válida do Dijkstra.

| # | Origem (`id` — Título) | Destino (`id` — Título) | Nº de arestas ($k$) | Custo Dijkstra ($\sum (w + 10)$) | Custo original equivalente ($\text{custo} - 10k$) | Tempo (ms) |
| ---: | :--- | :--- | ---: | ---: | ---: | ---: |
| 1 | `[PREENCHER]` | `[PREENCHER]` | — | — | — | — |
| 2 | `[PREENCHER]` | `[PREENCHER]` | — | — | — | — |
| 3 | `[PREENCHER]` | `[PREENCHER]` | — | — | — | — |
| 4 | `[PREENCHER]` | `[PREENCHER]` | — | — | — | — |
| 5 | `[PREENCHER]` | `[PREENCHER]` | — | — | — | — |

> **`[AUTORAL — PREENCHER PELO GRUPO]`**
> - Explicar o impacto matemático e semântico da transformação `peso + 10.0`: como somar `+10.0` por aresta penaliza caminhos com mais saltos ($+10k$), caminhos com menor custo deslocado nem sempre coincidem com os de menor soma pura de pesos originais (diferença entre Dijkstra deslocado e Bellman-Ford original quando há múltiplos saltos).

### 4.3 Bellman-Ford (Sem Ciclo Negativo e Com Ciclo Negativo)

| Cenário | Descrição do recorte / grafo | Fonte (`id`) | Ciclo negativo detectado? | Resultado / Sequência do ciclo e custo | Tempo (ms) |
| :--- | :--- | :--- | :--- | :--- | ---: |
| **1. Pesos negativos sem ciclo negativo** | Grafo cronológico padrão (`io.py`, DAG) | `[PREENCHER]` | Não | `[PREENCHER caminhos/custos]` | — |
| **2. Com ciclo negativo** | `[Pendente: recorte/transformação documentada]` | `[PREENCHER]` | Sim | `[PREENCHER ciclo detectado e custo]` | — |

> **`[AUTORAL — PREENCHER PELO GRUPO]`**
> - Documentar exatamente **qual recorte ou transformação dos dados** foi construído para gerar o caso com ciclo negativo (necessário porque o grafo completo em `io.py` exige `datas[i] < datas[j]` e, portanto, é acíclico — ex.: subgrafo onde filmes lançados na mesma data ou em um recorte sem restrição temporal estrita formam um ciclo de variação líquida negativa de nota) e interpretar o ciclo encontrado.

---

## 5. Desempenho e Escalabilidade (`out/parte2/parte2_report.json`)

O benchmark definido em `src/solve.py` (`executar_benchmark_parte2`) mede o tempo médio de **5 execuções** por algoritmo em **3 tamanhos** do grafo (`10%` = `41.624` filmes, `50%` = `208.121` filmes e `100%` = `416.243` filmes).

| Escala | Vértices ($\|V\|$) | Arestas ($\|E\|$) | BFS (ms) | DFS (ms) | Dijkstra (ms) | Bellman-Ford (ms) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| `10%` (`41.624` filmes) | `[Pendente]` | `[Pendente]` | `[Pendente]` | `[Pendente]` | `[Pendente]` | `[Pendente]` |
| `50%` (`208.121` filmes) | `[Pendente]` | `[Pendente]` | `[Pendente]` | `[Pendente]` | `[Pendente]` | `[Pendente]` |
| `100%` (`416.243` filmes) | `416.243` | `500.000` | `[Pendente]` | `[Pendente]` | `[Pendente]` | `[Pendente]` |

Complexidades teóricas de referência:
- **BFS / DFS:** $O(|V| + |E|)$
- **Dijkstra (com `heapq`):** $O((|V| + |E|) \log |V|)$
- **Bellman-Ford:** $O(|V| \cdot |E|)$

### Visualizações de Comparação dos Algoritmos

1. **Comparação por escala (barras):** `[Pendente: gerar out/parte2/comparacao_algoritmos_barras.png via python -m src.viz]`
2. **Escalabilidade por número de vértices (linhas):** `[Pendente: gerar out/parte2/escalabilidade_algoritmos_linhas.png via python -m src.viz]`

> **`[AUTORAL — PREENCHER PELO GRUPO]`**
> - Comparar o crescimento empírico observado nas 3 escalas (10%, 50%, 100%) com a complexidade teórica de cada algoritmo (ex.: comportamento linear de BFS/DFS vs. custo quadrático/produto $|V|\cdot|E|$ do Bellman-Ford e impacto do número de arestas limitadas em `500.000`).

---

## 6. Análise Exploratória e Explanatória dos Dados (AVD)

*(Critérios: mínimo de **6 visualizações** — 4 exploratórias + 2 explanatórias, sendo pelo menos 1 explanatória respondendo à pergunta de pesquisa; todas com título, legenda e identificação dos eixos; gráficos de pizza e radar evitados salvo justificativa muito forte; interpretação e notas 100% autorais.)*

### 6.1 Da Exploratória à Explanatória (*Storytelling*)

> **`[AUTORAL — PREENCHER PELO GRUPO]`**
> - Registrar o raciocínio analítico completo:
>   1. **O que foi encontrado na análise exploratória?**
>   2. **Qual história relevante o grupo decidiu contar a partir disso (*storytelling*)?**
>   3. **Por que essa mensagem é a mais relevante para responder à pergunta de pesquisa?**
>   4. **Quais técnicas visuais e atributos pré-atentivos (cor, tamanho, posição, destaque/anotação) foram usados para destacar a mensagem?**

### 6.2 Visualizações Exploratórias (Mínimo 4)

#### Exploratória 1 — `[Título do gráfico]`
- **Arquivo em `out/parte2/`:** `[Pendente]`
- **Nota analítica `[AUTORAL — PREENCHER PELO GRUPO]`:**
  - *O que está sendo mostrado:* `[...]`
  - *Insight extraído:* `[...]`
  - *Por que este tipo de gráfico foi escolhido:* `[...]`

#### Exploratória 2 — `[Título do gráfico]`
- **Arquivo em `out/parte2/`:** `[Pendente]`
- **Nota analítica `[AUTORAL — PREENCHER PELO GRUPO]`:**
  - *O que está sendo mostrado:* `[...]`
  - *Insight extraído:* `[...]`
  - *Por que este tipo de gráfico foi escolhido:* `[...]`

#### Exploratória 3 — `[Título do gráfico]`
- **Arquivo em `out/parte2/`:** `[Pendente]`
- **Nota analítica `[AUTORAL — PREENCHER PELO GRUPO]`:**
  - *O que está sendo mostrado:* `[...]`
  - *Insight extraído:* `[...]`
  - *Por que este tipo de gráfico foi escolhido:* `[...]`

#### Exploratória 4 — `[Título do gráfico]`
- **Arquivo em `out/parte2/`:** `[Pendente]`
- **Nota analítica `[AUTORAL — PREENCHER PELO GRUPO]`:**
  - *O que está sendo mostrado:* `[...]`
  - *Insight extraído:* `[...]`
  - *Por que este tipo de gráfico foi escolhido:* `[...]`

### 6.3 Visualizações Explanatórias (Mínimo 2 — sendo $\ge 1$ respondendo à pergunta de pesquisa)

*(Devem ser interpretáveis por alguém que não conhece o projeto.)*

#### Explanatória 1 — `[Título do gráfico — Responde à pergunta de pesquisa]`
- **Arquivo em `out/parte2/`:** `[Pendente]`
- **Nota analítica `[AUTORAL — PREENCHER PELO GRUPO]`:**
  - *O que está sendo mostrado:* `[...]`
  - *Insight principal e resposta à pergunta:* `[...]`
  - *Por que este tipo de gráfico foi escolhido:* `[...]`
  - *Seleção de elementos exibidos e atributos pré-atentivos usados (cor, tamanho, posição, rótulos):* `[...]`

#### Explanatória 2 — `[Título do gráfico]`
- **Arquivo em `out/parte2/`:** `[Pendente]`
- **Nota analítica `[AUTORAL — PREENCHER PELO GRUPO]`:**
  - *O que está sendo mostrado:* `[...]`
  - *Insight principal:* `[...]`
  - *Por que este tipo de gráfico foi escolhido:* `[...]`
  - *Seleção de elementos exibidos e atributos pré-atentivos usados (cor, tamanho, posição, rótulos):* `[...]`

---

## 7. Discussão Crítica e Resposta à Pergunta de Pesquisa

> **`[AUTORAL — PREENCHER PELO GRUPO]`**
>
> 1. **Quando e por que cada algoritmo é mais adequado neste domínio:** comparar BFS, DFS, Dijkstra (com deslocamento `+10.0`) e Bellman-Ford (com pesos negativos originais) em termos de corretude, semântica do caminho e custo computacional.
> 2. **Limites do design de pesos e da modelagem:** discutir criticamente as limitações do peso $\text{imdb\_rating}(v) - \text{imdb\_rating}(u)$, do deslocamento $+10{,}0$ (que soma $+10$ por salto e mistura variação de qualidade com número de arestas), do teto de `500.000` arestas e do fato de o grafo cronológico ser acíclico.
> 3. **Resposta fundamentada à pergunta de pesquisa:** sintetizar a resposta final apoiada tanto nas evidências dos algoritmos de grafos quanto nas descobertas da análise visual (AVD).
