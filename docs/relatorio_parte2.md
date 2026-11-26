# Relatório Técnico e Análise Visual (AVD) — Parte 2: Dataset Maior (TMDB)

- **Disciplinas:** Teoria dos Grafos + Análise e Visualização de Dados (AVD)
- **Equipe:**
  - Aline Takakura
  - David Magalhães
  - Gabriel Victalino Mancebo
  - Júlia Ferreira

> **Origem dos dados:** todos os números, métricas estruturais, tabelas de limpeza, distribuições, correlações e limites de *outliers* foram extraídos de `src/graphs/io.py`, `src/solve.py`, `src/avd_parte2.py`, `data/dataset_parte2/tmdb_limpo.csv.gz`, dos notebooks em `notebooks/` e dos arquivos em `out/parte2/`.

---

## 1. Proposta do Dataset, Domínio e Pergunta de Pesquisa

- **Fonte:** Kaggle — *TMDB Movies Daily Updates* (`alanvourch/tmdb-movies-daily-updates`, arquivo `TMDB_all_movies.csv`, versão 1072, dados coletados da API do TMDB).
- **Domínio:** Cinema / rede cronológica de filmes conectados por elenco compartilhado (não aéreo e não grade/labirinto).
- **Tipo do grafo:** **Dirigido** e **ponderado**, com pesos negativos derivados diretamente das avaliações dos filmes (`imdb_rating`).
- **Dimensão construída em `src/graphs/io.py`:** $|V| = 416.243$ vértices (filmes únicos válidos) Exploração estrutural (Seção 2): $|E| = 500.000$ arestas dirigidas (`modo_arestas="todos_pares"`, `max_arestas=500_000`). Experimentos e AVD (Seções 4–6): $|E| = 3.381.516$ (`modo_arestas="consecutivo"`, sem teto).

**Pergunta de pesquisa:** *Quando um ator emenda um filme no outro, a nota IMDb tende a cair ou a subir? Existem cadeias cronológicas de filmes, ligadas por elenco em comum, em que a nota cai de forma sistemática?*

**Justificativa da amostragem/corte.** Ligar todos os pares de filmes de cada ator (`modo_arestas="todos_pares"`) gera `O(k²)` arcos por ator com `k` filmes, cerca de 78 milhões no dataset completo. Isso inviabiliza a memória e, principalmente, o Bellman-Ford (`O(V·E)`). Por isso foram usadas duas estratégias de redução, ambas determinísticas graças à ordenação `(release_date, id)`:
- **Exploração estrutural (Seção 2.2):** grafo `todos_pares` cortado em `max_arestas = 500.000`. Como os filmes são percorridos cronologicamente, o corte favorece filmes antigos, o que explica por que os hubs da Seção 2.3 são todos do cinema mudo.
- **Experimentos e AVD (Seções 4–6):** grafo `modo_arestas="consecutivo"`, em que cada filme liga apenas ao próximo filme do mesmo ator. São 416.243 vértices e **3.381.516 arcos** no grafo 100%. Esse modelo preserva a cronologia de cada carreira sem a explosão quadrática. Os casos obrigatórios da Seção 4 rodam num recorte dos 1.000 primeiros filmes (864 arcos), para que os caminhos possam ser inspecionados manualmente.

**Significado no domínio.**
- **Caminho mínimo** (Bellman-Ford, pesos originais): é a sequência de filmes, ligados por atores em comum e em ordem de lançamento, que acumula a **maior queda de nota IMDb** entre a origem e o destino. Em outras palavras, é a "trajetória de declínio" mais forte que conecta dois filmes pelo elenco.
- **Ciclo negativo:** seria voltar ao filme de partida com saldo de nota negativo. No mundo real isso é impossível, porque os arcos só vão do filme mais antigo para o mais recente e o grafo é um DAG. Ele só aparece em um recorte construído de propósito (Seção 4.3) e serve como teste de corretude do algoritmo, não como fenômeno do cinema.

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

**Mecanismo de ausência.** A falta de `imdb_rating`/`imdb_votes` (62%) **não é MCAR**. As duas colunas faltam juntas (correlação de 1,00) e acompanham a falta de `imdb_id` (0,71). Isso indica filmes sem cadastro no IMDb, como curtas, produções independentes, títulos muito antigos ou de países pouco representados. Como a ausência pode ser explicada por variáveis observadas (`imdb_id` ausente, `vote_count` e `popularity` baixos, idioma), o mecanismo é predominantemente **MAR**. Há também um componente **MNAR** plausível: filmes de baixa visibilidade, possivelmente com menor qualidade percebida, tendem a não receber nota.

**Tratamento.** Removemos as linhas apenas nas 4 colunas estruturais do grafo (`title`, `release_date`, `imdb_rating`, `cast`), porque sem elas não existe vértice, direção ou peso. Não imputamos a nota, já que ela é o próprio peso, e imputar criaria arestas artificiais. As demais colunas foram mantidas com nulos porque não entram no grafo. **Viés introduzido:** o grafo representa os filmes "visíveis" no IMDb (48% em inglês, mais votados), então as conclusões valem para esse universo, e não para todo o cinema mundial.

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

**Interpretação.**
- `revenue` e `budget` têm IQR igual a 0 porque a maioria dos registros vale **0**, o que, na prática, é valor não informado. Por isso, qualquer valor positivo vira "outlier" e a cauda à direita é longa. Analisar essas variáveis exige filtrar `> 0` e usar escala log.
- `vote_count`, `imdb_votes` e `popularity` têm assimetria forte à direita: poucos filmes concentram a atenção do público, num padrão próximo de lei de potência.
- `runtime` se concentra entre curtas e longas comuns (IQR de 65 min).
- `imdb_rating` é a variável mais bem-comportada: média de 6,18, mediana de 6,3 e assimetria levemente negativa (−0,42), com uma cauda curta de notas muito baixas (ver Exploratória 3).
- Os pesos `nota(v) − nota(u)` do grafo consecutivo ficam centrados exatamente em 0 (média de −0,0003, mediana de 0, desvio-padrão de 1,48), e 57% dos arcos variam no máximo 1 ponto (ver Exploratória 4).

### 3.4 Pilar Relacional e Exploração Multivariada

Correlações já obtidas nos notebooks:
- **No dataset bruto (`projeto.ipynb`, Spearman):** `vote_count` × `vote_average = 0,94`; `imdb_votes` × `vote_count = 0,78`.
- **Nas arestas do grafo (`exploracao_grafo_avd.ipynb`, correlação com o `peso`):**
  - `imdb_rating` do filme de destino: **Pearson `0,652148`** | **Spearman `0,618118`**
  - `ano` de lançamento do filme de destino: **Pearson `0,034871`** | **Spearman `0,012559`**

> **Nota técnica importante:** `data/dataset_parte2/tmdb_limpo.csv.gz` contém apenas 5 colunas (`id`, `title`, `release_date`, `cast`, `imdb_rating`). Para cumprir integralmente o critério de AVD de **exploração multivariada** (mapear o atributo-alvo/variável central com **os demais atributos**, não apenas 1 ou 2), utilizar o dataframe de 27 colunas gerado em `notebooks/projeto_pos_limpeza.ipynb` cruzando com `budget`, `revenue`, `popularity`, `runtime`, `vote_average`, `vote_count`, `imdb_votes`, `genres`, `original_language` e atributos do grafo.

**Interpretação das relações.**
- **`peso` × `imdb_rating` do destino:** relação direta, linear e forte (Pearson de 0,65). É uma consequência da própria fórmula do peso, então não constitui uma descoberta independente.
- **`peso` × ano:** relação praticamente nula (Pearson de 0,03; Spearman de 0,01). A Explanatória 2 confirma isso no grafo completo: a média por década fica entre −0,02 e +0,07.
- **`vote_count` × `vote_average`:** relação direta, monotônica e forte (Spearman de 0,94), mas não linear. Com poucos votos, a média é 0 ou instável; depois ela se estabiliza.
- **`imdb_votes` × `vote_count`:** relação direta e forte (0,78). As duas medem popularidade em plataformas diferentes.

> **Pendente:** ainda não calculamos as relações de `imdb_rating` com `runtime`, `budget`/`revenue` (> 0, em log), `popularity`, `genres` e `original_language`. Elas precisam do dataframe de 27 colunas de `projeto_pos_limpeza.ipynb`.

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

Fonte: `out/parte2/parte2_tarefas.json`, recorte dos 1.000 primeiros filmes (grafo consecutivo, 864 arcos).

| Fonte (`id` — Título) | Algoritmo | Vértices alcançados | Camadas / Profundidade máx. | Ciclo detectado? | Tempo (ms) |
| :--- | :--- | ---: | ---: | :--- | ---: |
| `428699 — Phono-Cinéma-Théâtre` | BFS | 30 | 13 camadas (0–12) | — | 0,104 |
| `428699 — Phono-Cinéma-Théâtre` | DFS | 30 | arcos: 29 árv., 0 ret., 4 av., 2 cruz. | não | 0,137 |
| `232935 — The Fatal Hour` | BFS | 63 | 6 camadas (0–5) | — | 0,118 |
| `232935 — The Fatal Hour` | DFS | 63 | 62 árv., 0 ret., 42 av., 87 cruz. | não | 0,155 |
| `622716 — Richard III` | BFS | 51 | 7 camadas (0–6) | — | 0,108 |
| `622716 — Richard III` | DFS | 51 | 50 árv., 0 ret., 31 av., 60 cruz. | não | 0,140 |

Interpretação: em todas as fontes há 0 arcos de retorno, o que confirma que o grafo é um DAG. A grande quantidade de arcos de cruzamento e avanço mostra que os elencos se sobrepõem bastante: chega-se ao mesmo filme por vários atores diferentes. No grafo 100% (`parte2_report.json`), as fontes *Looping*, *Office Romance* e *Kira* alcançam 75, 377 e 2.956 filmes (14, 12 e 20 camadas), também sem arcos de retorno.

### 4.2 Dijkstra ($\ge 5$ Pares Origem–Destino com Pesos $\ge 0$)

**Transformação de pesos utilizada (`src/graphs/io.py`):** como `imdb_rating` varia de `0` a `10` (na prática `1.0` a `10.0`), a diferença $\text{imdb\_rating}(v) - \text{imdb\_rating}(u)$ tem mínimo teórico `-10,0`. Ao usar `transformacao_peso="nao_negativo"`, cada arco recebe `peso + 10.0 >= 0`, permitindo a execução válida do Dijkstra.

| # | Origem (`id` — Título) | Destino (`id` — Título) | Nº de arestas ($k$) | Custo Dijkstra ($\sum (w + 10)$) | Custo original equivalente ($\text{custo} - 10k$) | Tempo (ms) |
| ---: | :--- | :--- | ---: | ---: | ---: | ---: |
| 1 | `428699 Phono-Cinéma-Théâtre` | `427270 Jules Moy` | 1 | 7,5 | -2,5 | 1,035 |
| 2 | `232935 The Fatal Hour` | `1163703 Leah, the Forsaken` | 2 | 17,4 | −2,6 | 1,901 |
| 3 | `622716 Richard III` | `1163703 Leah, the Forsaken` | 1 | 9,2 | −0,8 | 1,536 |
| 4 | `290574 The Taming of the Shrew` | `413249 The Honor of Thieves` | 1 | 8,2 | −1,8 | 1,031 |
| 5 | `382980 The Feud and the Turkey` | `413249 The Honor of Thieves` | 2 | 18,4 | −1,6 | 0,845 |

Cada destino é o filme com a maior queda acumulada (menor distância do Bellman-Ford) a partir da origem.

**Análise da transformação +10:** o custo deslocado de um caminho com k arcos é igual a custo_original + 10k. Como o termo 10k depende do número de saltos, o Dijkstra passa a preferir caminhos com menos arestas, e o resultado só coincide com o caminho de menor soma original quando os candidatos têm o mesmo k. Um exemplo: um caminho de 3 saltos com soma −5 custa 25, e um de 1 salto com soma −1 custa 9. O Dijkstra escolhe o segundo, mas o Bellman-Ford escolhe o primeiro. Nos 5 pares acima os custos coincidiram com a queda acumulada do Bellman-Ford porque o recorte é pequeno e há poucos caminhos alternativos. Isso não é garantido em geral. Semântica: o Dijkstra deslocado responde "qual é a ligação mais curta, em número de filmes, que ainda tem a menor variação de nota", e não "qual é a maior queda de nota".

### 4.3 Bellman-Ford (Sem Ciclo Negativo e Com Ciclo Negativo)

| Cenário | Descrição do recorte / grafo | Fonte (`id`) | Ciclo negativo detectado? | Resultado / Sequência do ciclo e custo | Tempo (ms) |
| :--- | :--- | :--- | :--- | :--- | ---: |
| **1. Pesos negativos sem ciclo negativo** | 1.000 primeiros filmes, DAG, 864 arcos, dos quais 403 negativos | `428699 Phono-Cinéma-Théâtre` | Não | `30 alcançados; menor distância: Jules Moy, −2,5` | 0,294 |
| **2. Com ciclo negativo** | 300 primeiros filmes, arcos nos dois sentidos, peso = −\|Δnota\| (276 arcos) | `189579 Departure by Car` | Sim | `Le goûter des bébés → The Little Girl and Her Cat → Le goûter des bébés; custo −1,8` | 6,69 |

**Documentação do ciclo:** o grafo original não tem ciclos porque exige data(u) < data(v). Para criar o caso obrigatório, pegamos os 300 primeiros filmes por data, removemos a restrição temporal (arcos nos dois sentidos entre filmes com ator em comum) e forçamos todos os pesos a serem negativos (−|nota(v) − nota(u)|). Com isso, qualquer par de filmes com notas diferentes forma um ciclo de 2 arcos com custo negativo. O ciclo encontrado tem custo −1,8, ou seja, |Δnota| = 0,9 em cada sentido. Como "ir e voltar" sempre diminui o custo, a distância mínima não existe (tende a −∞), e o Bellman-Ford mostra isso ao continuar relaxando arestas na V-ésima iteração. Esse caso é um teste de corretude, não uma conclusão sobre o cinema. A fonte foi escolhida pelo maior grau de saída no recorte.

---

## 5. Desempenho e Escalabilidade (`out/parte2/parte2_report.json`)

O benchmark definido em `src/solve.py` (`executar_benchmark_parte2`) mede o tempo médio de **5 execuções** por algoritmo em **3 tamanhos** do grafo (`10%` = `41.624` filmes, `50%` = `208.122` filmes e `100%` = `416.243` filmes).

| Escala | Vértices ($\|V\|$) | Arestas ($\|E\|$) | BFS (ms) | DFS (ms) | Dijkstra (ms) | Bellman-Ford (ms) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| `10%` | `41.624` | `384.336` | `4,98` | `6,75` | `51,87` | `209,35` |
| `50%` | `208.122` | `1.899.964` | `35,89` | `42,80` | `338,86` | `1.167,13` |
| `100%` | `416.243` | `3.381.516` | `262,76` | `261,79` | `1.965,25` | `5.003,95` |

*(Grafo `modo_arestas="consecutivo"`, sem `max_arestas`; origem `33229` — Dickson Greeting, que alcança 7 filmes.)*

Complexidades teóricas de referência:
- **BFS / DFS:** $O(|V| + |E|)$
- **Dijkstra (com `heapq`):** $O((|V| + |E|) \log |V|)$
- **Bellman-Ford:** $O(|V| \cdot |E|)$

### Visualizações de Comparação dos Algoritmos

1. **Comparação por escala (barras):** `out/parte2/comparacao_algoritmos_barras.png`
2. **Escalabilidade por número de vértices (linhas):** `out/parte2/escalabilidade_algoritmos_linhas.png`
3. **Empírico vs. teórico:** `out/parte2/empirico_vs_teorico.png`

**Empírico vs. teórico.** De 10% para 100%, V cresce 10× e E cresce 8,8×. Os tempos cresceram: BFS ~53×, DFS ~39×, Dijkstra ~38× e Bellman-Ford só ~24×.
- **Bellman-Ford abaixo do previsto.** O `O(V·E)` indicaria um crescimento de ~88×. O valor menor se explica porque a origem alcança apenas 7 filmes: a implementação encerra quando uma rodada não altera nenhuma distância, converge em poucas iterações e se comporta como `O(E)` vezes uma constante pequena.
- **BFS e DFS acima do linear.** Mesmo visitando 7 nós, eles cresceram mais que o esperado. Isso indica que o tempo é dominado pela inicialização das estruturas em `O(V)` e por efeitos de memória, cache e coletor de lixo do Python, e não pela travessia. A grande variação entre execuções no grafo 100% (157–466 ms) reforça essa leitura.
- **A ordem relativa segue a teoria:** BFS ≈ DFS < Dijkstra (fator `log V` do heap) < Bellman-Ford.
- **Limitação:** para observar o `O(V·E)` de fato, seria necessária uma origem com alcance grande (por exemplo, *Kira*, com 2.956 filmes).

---

## 6. Análise Exploratória e Explanatória dos Dados (AVD)

*(Critérios: mínimo de **6 visualizações** — 4 exploratórias + 2 explanatórias, sendo pelo menos 1 explanatória respondendo à pergunta de pesquisa; todas com título, legenda e identificação dos eixos; gráficos de pizza e radar evitados salvo justificativa muito forte; interpretação e notas 100% autorais.)*

### 6.1 Da Exploratória à Explanatória (*Storytelling*)

1. **O que a análise exploratória encontrou.** A nota IMDb é concentrada (mediana de 6,3) e levemente assimétrica à esquerda. Já a popularidade e os votos são muito desiguais. O grafo de elenco é extremamente esparso (densidade de ~3·10⁻⁶): no recorte de 500 mil arestas, a grande maioria dos filmes não tem arco nenhum e poucos hubs do cinema mudo concentram centenas de ligações. A variação de nota entre filmes consecutivos de um ator (o peso) fica centrada exatamente em 0.
2. **A história escolhida.** *"Trabalhar com o mesmo ator não prevê se o próximo filme será melhor ou pior: a nota sobe e cai na mesma proporção, em todas as épocas. As quedas grandes existem, mas são casos pontuais, e é isso que os caminhos mínimos revelam."*
3. **Por que essa mensagem.** Ela responde diretamente à pergunta de pesquisa (a nota tende a subir ou a cair?) e une o resultado estatístico (sinal e média dos pesos) ao resultado dos algoritmos (caminhos de queda acumulada do Bellman-Ford).
4. **Técnicas visuais.** Vermelho é a única cor de destaque, reservada para "queda de nota"; o restante fica em cinza ou azul. Os valores aparecem como rótulos diretamente nas barras. Há uma linha de referência no zero, as barras começam no zero com o eixo fixo em 0–100%, e os títulos já declaram a conclusão. A escala log é usada apenas nos histogramas de grau, onde a cauda é extrema.

> **Nota metodológica:** o recorte `todos_pares` de 500 mil arestas (Seção 2.2) indica 58,5% de arcos positivos. Esse número é um artefato do recorte, que liga filmes antigos a todos os filmes posteriores do mesmo ator. No grafo `consecutivo` completo (3,38 milhões de arcos), usado nas Explanatórias, a proporção é 48,3% positivos contra 48,6% negativos.

### 6.2 Visualizações Exploratórias

#### Exploratória 1 — Distribuição do grau de entrada
- **Arquivo:** `out/parte2/histograma_grau_entrada.png`
- **O que mostra:** quantos filmes têm cada grau de entrada no grafo de 500 mil arestas, com o eixo y em escala log.
- **Insight:** a distribuição é de cauda pesada. A enorme maioria dos vértices tem grau 0 ou muito baixo e poucos filmes recebem centenas de arcos. Isso indica que o recorte deixa a maior parte do dataset isolada, o que limita o alcance da BFS e da DFS.
- **Por que histograma:** é a forma padrão de mostrar a distribuição de uma variável discreta. A escala log torna a cauda visível.

#### Exploratória 2 — Distribuição do grau de saída
- **Arquivo:** `out/parte2/histograma_grau_saida.png`
- **O que mostra:** a mesma análise para o grau de saída (máximo de 836).
- **Insight:** o pico em 0 é ainda maior, e a cauda chega a 600–836. Os hubs de saída são filmes de 1910–1920 (Seção 2.3) cujos atores fizeram muitos filmes depois. Isso evidencia o viés cronológico do corte por `max_arestas`.
- **Por que histograma:** permite comparar diretamente com a Exploratória 1 (mesma escala e tipo de gráfico).

#### Exploratória 3 — Distribuição das notas IMDb
- **Arquivo:** `out/parte2/avd_e3_distribuicao_imdb_rating.png`
- **O que mostra:** histograma de `imdb_rating` dos 416.243 filmes, com linhas de média (6,18) e mediana (6,30).
- **Insight:** a nota se concentra entre 5 e 7,5, com assimetria levemente negativa (−0,42), já que a média fica abaixo da mediana. Como a variável é concentrada, as diferenças entre filmes vizinhos tendem a ser pequenas.
- **Por que histograma:** a variável é contínua, e as linhas de média e mediana mostram a assimetria sem precisar de outro gráfico.

#### Exploratória 4 — Distribuição da variação de nota (peso dos arcos)
- **Arquivo:** `out/parte2/avd_e4_distribuicao_pesos.png`
- **O que mostra:** histograma dos 3.381.516 pesos `nota(posterior) − nota(anterior)`, com quedas em vermelho e aumentos em azul.
- **Insight:** a distribuição é simétrica em torno de 0 (média de −0,0003; desvio-padrão de 1,48), e 57% dos arcos variam no máximo 1 ponto. Quedas e aumentos grandes (|Δ| > 3) são raros e aparecem nas duas direções na mesma proporção.
- **Por que histograma com duas cores:** a cor separa visualmente as duas metades da pergunta (cai ou sobe) sem exigir leitura de eixo.

### 6.3 Visualizações Explanatórias

#### Explanatória 1 — "No próximo filme de um ator, a nota IMDb sobe e cai praticamente na mesma proporção" (responde à pergunta)
- **Arquivo:** `out/parte2/avd_x1_sinal_variacao_nota.png`
- **O que mostra:** a porcentagem dos 3,38 milhões de arcos em que a nota sobe (48,3%), cai (48,6%) ou fica igual (3,2%).
- **Insight e resposta:** não há tendência de queda nem de subida. Ter o mesmo ator não prediz o sentido da nota do filme seguinte.
- **Por que barras horizontais:** comparar comprimentos a partir de um zero comum é a tarefa perceptiva mais precisa. O formato horizontal comporta rótulos legíveis. Pizza foi evitada porque fatias de 48,3% e 48,6% seriam indistinguíveis.
- **Elementos e atributos pré-atentivos:** apenas a barra "cai" em vermelho (a cor marca o foco da pergunta), rótulos de porcentagem no fim das barras, eixo fixo em 0–100% para não exagerar diferenças, título que já enuncia a conclusão e bordas superior e direita removidas.

#### Explanatória 2 — "A variação média de nota entre filmes de um ator não muda com a época"
- **Arquivo:** `out/parte2/avd_x2_variacao_por_decada.png`
- **O que mostra:** a média do peso por década do filme posterior (de 1910 a 2020, apenas décadas com 1.000 ou mais arcos).
- **Insight:** todas as médias ficam entre −0,02 e +0,07, coladas no zero. A porcentagem de quedas fica estável entre 45% e 49%. Isso confirma a correlação nula entre peso e ano (0,03), ou seja, não houve uma época de declínio.
- **Por que linha:** o eixo x é temporal e ordenado, e a linha mostra tendência (aqui, a ausência dela).
- **Elementos e atributos pré-atentivos:** linha de referência no zero com anotação "0 = sem variação". O eixo y foi fixado em ±1 de propósito: com o zoom automático, oscilações de 0,01 pareceriam grandes, o que seria uma distorção visual.

*(As figuras de desempenho da Seção 5 — barras, linhas e empírico vs. teórico — complementam a análise, mas não entram na contagem de AVD.)*

---

## 7. Discussão Crítica e Resposta à Pergunta de Pesquisa

**1. Quando usar cada algoritmo.**
- **BFS:** é adequado para medir a quantos "saltos de elenco" um filme está de outro, sem considerar pesos. É o mais barato (`O(V+E)`).
- **DFS:** classifica arcos e, com 0 arcos de retorno, prova que o grafo cronológico é acíclico. Também é a base para uma ordenação topológica.
- **Dijkstra com +10:** é rápido (`O((V+E) log V)`), mas responde a outra pergunta, porque penaliza o número de saltos (Seção 4.2).
- **Bellman-Ford:** é o único correto para a maior queda acumulada com pesos negativos e para detectar ciclos negativos, porém é o mais caro. Como o grafo real é um DAG, um caminho mínimo por ordenação topológica (`O(V+E)`) daria o mesmo resultado do Bellman-Ford de forma muito mais rápida. Seria a escolha ideal em produção.

**2. Limites do design de pesos e da modelagem.**
- O Δnota ignora quantos votos sustentam cada nota: uma nota baseada em 10 votos pesa o mesmo que uma baseada em 1 milhão.
- O deslocamento de +10 mistura qualidade com comprimento do caminho.
- Pela correlação de 0,65, o peso é explicado em boa parte pela nota do destino. Parte do "sinal" é, portanto, consequência da construção do peso.
- O teto de 500 mil arestas no modo `todos_pares` favorece filmes antigos e chega a inverter conclusões: dá 58,5% de arcos positivos, contra 48,3% no grafo completo.
- Ligar todos os pares de filmes de um ator cria arcos entre filmes separados por décadas, enquanto o modo `consecutivo` representa melhor a sequência de uma carreira.
- O grafo cronológico é um DAG, então o ciclo negativo só existe em um recorte artificial.
- O benchmark usou uma origem que alcança apenas 7 filmes, o que esconde o custo real do Bellman-Ford.

**3. Resposta à pergunta de pesquisa.** **Não há tendência sistemática.** Em 3,38 milhões de transições entre filmes consecutivos de um mesmo ator, a nota IMDb cai em 48,6% dos casos e sobe em 48,3%, com variação média praticamente nula (−0,0003). Esse equilíbrio se mantém em todas as décadas de 1910 a 2020. Ainda assim, os algoritmos mostram que **trajetórias de declínio existem localmente**: o Bellman-Ford encontra cadeias como *The Fatal Hour* → *Richard III* → *Leah, the Forsaken*, com queda acumulada de −2,6 pontos em dois filmes. Essas cadeias são exceções identificáveis, e não a regra.
