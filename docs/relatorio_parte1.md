# Relatório Técnico e Manual — Parte 1: Labirinto com Chaves e Portas (Grafo de Estados)

- **Disciplinas:** Teoria dos Grafos + Análise e Visualização de Dados (AVD)
- **Equipe:**
  - Aline Takakura
  - David Magalhães
  - Gabriel Victalino Mancebo
  - Júlia Ferreira

> **Aviso de conformidade (Diretrizes de IA):** Conforme as regras da disciplina, todas as análises interpretativas, justificativas técnicas, discussões críticas, notas analíticas e a prova do mapa `m05` devem ser **autorais do grupo**. Neste documento, os dados numéricos e estruturais foram extraídos diretamente das saídas geradas pelo código (`out/parte1/`) e dos testes (`tests/`), enquanto os trechos que exigem redação autoral estão marcados com **`[AUTORAL — PREENCHER PELO GRUPO]`**.

---

## 1. Manual Técnico e Modelagem do Grafo de Estados

### 1.1 Símbolos e Custos dos Mapas

Os mapas de entrada (`*.txt`) são grades retangulares de caracteres. Linhas iniciadas por `;` representam comentários.

| Símbolo | Significado | Custo de entrar |
| :--- | :--- | :--- |
| `#` | Parede (intransponível) | — |
| `.` | Chão | `1` |
| `S` | Início (exatamente um por mapa) | `1` |
| `G` | Saída (pelo menos uma; ao entrar em `G` o jogo termina) | `1` |
| `,` | Lama | `3` |
| `~` | Água | `5` |
| `a`–`d` | Chave (ao entrar, o jogador coleta e mantém para sempre) | `1` |
| `A`–`D` | Porta (só passa com a chave minúscula correspondente; não fecha e não gasta a chave) | `1` |
| `> < ^ v` | Esteira (pode entrar por qualquer lado; estando nela, só sai na direção da seta) | `1` |
| `+` | Bônus consumível (`-4` na 1ª visita; `1` nas seguintes, como chão) | `-4`, depois `1` |
| `*` | Fonte de energia (não se esgota; vale `-2` em toda entrada) | `-2` |

### 1.2 Regras Obrigatórias de Movimento

1. Movimentos testados sempre em 4 direções na ordem fixa **N, L, S, O** (cima, direita, baixo, esquerda), definindo a ordem da lista de adjacência (essencial para a classificação de arcos da DFS).
2. O custo de uma transição é o custo da **casa de destino** (com verificação de consumo para `+`).
3. Não é permitido sair da grade nem entrar em parede (`#`); portas (`A`–`D`) exigem a chave correspondente no inventário do estado de origem.
4. Estando em uma esteira (`> < ^ v`), o único movimento permitido é na direção apontada pela seta.
5. Estados posicionados em `G` não possuem arestas de saída para outras casas do mapa (o jogo termina).

### 1.3 Definição dos Grafos (`G_pos` e `G_est`), Rótulos e Nó Virtual `ALVO`

- **Grafo de Posições (`G_pos`):** cada vértice representa apenas a coordenada livre `(linha, coluna)` do mapa, ignorando chaves e bônus consumidos (modelo ingênuo usado para comparação).
- **Grafo de Estados (`G_est`):** cada vértice é um estado `(posição, chaves, bônus)`, onde:
  - `posição`: coordenada `(linha, coluna)` no mapa;
  - `chaves`: conjunto ordenado das chaves já coletadas (ou `-` quando vazio);
  - `bônus`: conjunto de IDs (`0, 1, 2, ...`, numerados em ordem de leitura linha-por-linha) dos bônus `+` já consumidos (ou `{}` quando vazio).
- **Rótulo obrigatório de cada estado:** `(linha,coluna)|chaves|{bonus}` (ex.: estado inicial do `m02` é `(1,1)|-|{}`; exemplo completo `(3,5)|ab|{0,2}`).
- **Construção por exploração:** `G_est` é construído por BFS a partir do estado inicial (`S`, sem chaves e sem bônus), garantindo que apenas estados **efetivamente alcançáveis** entrem no grafo, evitando a explosão combinatória de gerar todas as $2^{\text{chaves}} \times 2^{\text{bônus}}$ combinações de antemão.
- **Nó virtual `ALVO`:** todo estado em `G` recebe um arco dirigido de custo `0` para `ALVO`. Os caminhos até a saída são calculados até `ALVO`, mas o nó virtual e seus arcos incidentes **não** entram nas métricas globais nem nas métricas por camada.

### 1.4 Por que o Grafo Precisa Ser Dirigido?
>
>  O grafo precisa ser dirigido pois, pois possui caractéristicas que tornam cada transição única. Em duas casas adjacentes, que representam nós do grafo, os movimentos de ida e de volta são diferentes, pois possuem direções diferentes ( Direção é um dos rótulos necessários para identificar arestas no projeto). Além disso, as regras impõem limitações para o movimento entre casas, como as esteiras, que fazem com que seja apenas permitido o movimento em uma direção, quebrando a reciprocidade.

## 2. Métricas Globais, Camadas e Graus (`m01` a `m08`)

Definições adotadas (grafo dirigido, sem o nó virtual `ALVO`):
- **Ordem:** $|V|$
- **Tamanho:** $|E|$
- **Densidade dirigida:** $\frac{|E|}{|V|(|V| - 1)}$ (e $0$ se $|V| < 2$)
- **Teto teórico:** $\text{casas livres} \times 2^{\text{nº de chaves}} \times 2^{\text{nº de bônus}}$
- **Taxa de ocupação:** $\frac{|V(G_{\text{est}})|}{\text{teto teórico}}$

### 2.1 Métricas Globais (`out/parte1/metricas_global.json`)

| Mapa | $\|V(G_{\text{pos}})\|$ | $\|E(G_{\text{pos}})\|$ | Dens. $G_{\text{pos}}$ | $\|V(G_{\text{est}})\|$ | $\|E(G_{\text{est}})\|$ | Dens. $G_{\text{est}}$ | Chaves | Bônus | Teto teórico | Ocupação |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `m01` (`m01_terreno.txt`) | 24 | 48 | 0.086957 | 24 | 46 | 0.083333 | 0 | 0 | 24 | 100.00% |
| `m02` (`m02_uma_chave.txt`) | 23 | 44 | 0.086957 | 39 | 74 | 0.049933 | 1 | 0 | 46 | 84.78% |
| `m03` (`m03_tres_chaves.txt`) | 76 | 168 | 0.029474 | 213 | 466 | 0.010320 | 3 | 0 | 608 | 35.03% |
| `m04` (`m04_esteiras.txt`) | 24 | 40 | 0.072464 | 37 | 66 | 0.049550 | 1 | 0 | 48 | 77.08% |
| `m05` (`m05_bonus.txt`) | 44 | 92 | 0.048626 | 215 | 438 | 0.009520 | 0 | 3 | 352 | 61.08% |
| `m06` (`m06_fonte.txt`) | 24 | 48 | 0.086957 | 24 | 46 | 0.083333 | 0 | 0 | 24 | 100.00% |
| `m07` (`m07_impossivel.txt`) | 31 | 70 | 0.075269 | 16 | 38 | 0.158333 | 1 | 0 | 62 | 25.81% |
| `m08` (`m08_grande.txt`) | 1169 | 2576 | 0.001887 | 2919 | 6364 | 0.000747 | 4 | 0 | 18704 | 15.61% |

### 2.2 Graus, Multiplicidade e Becos (`out/parte1/metricas_global.json` e `graus_<mapa>.csv`)

*(Desempate no maior grau pela ordem de leitura do rótulo.)*

| Mapa | Maior grau de entrada | Maior grau de saída | Multiplicidade máx. | Casas na mult. máx. | Becos (grau saída 0 fora de `G`) |
| :--- | :--- | :--- | ---: | ---: | :--- |
| `m01` | `(1,1)\|-|{}` (2) | `(1,1)\|-|{}` (2) | 1 | 24 | 0 |
| `m02` | `(1,1)\|-|{}` (2) | `(1,1)\|-|{}` (2) | 2 | 16 | 0 |
| `m03` | `(1,12)\|ab|{}` (3) | `(3,4)\|abc|{}` (3) | 4 | 12 | 0 |
| `m04` | `(3,8)\|-|{}` (3) | `(3,8)\|-|{}` (3) | 2 | 17 | 2: `(1,3)\|-|{}`, `(1,3)\|a|{}` |
| `m05` | `(3,2)\|-\|{0,1,2}` (4) | `(3,1)\|-\|{0,1,2}` (3) | 6 | 21 | 0 |
| `m06` | `(1,1)\|-|{}` (2) | `(1,1)\|-|{}` (2) | 1 | 24 | 0 |
| `m07` | `(3,1)\|-|{}` (3) | `(3,1)\|-|{}` (3) | 1 | 16 | 0 |
| `m08` | `(3,15)\|abcd|{}` (4) | `(3,15)\|abcd|{}` (4) | 5 | 165 | 0 |

> - A **multiplicidade máxima no `m08`** é **5** e **165 casas** atingem essa multiplicidade. O número de multiplicade de 5 se deve ao fato de existirem 4 chaves no mapa. Cada combinação distinta de chaves e bonûs (inclusive a ausência deles) gera um
>   estado distinto como não há nenhum bonûs no mapa, o número máximo de estados por casa é 5. Comentar a diferença entre o **teto teórico** e os **estados realmente alcançáveis** nos mapas com chaves ou bônus.

### 2.3 Métricas por Camada e Arcos Entre Camadas (`out/parte1/camadas.json`)

| Mapa | Camada | Ordem | Tamanho | Densidade | Arcos entre camadas | Casas que geram mudança de camada |
| :--- | :--- | ---: | ---: | ---: | ---: | :--- |
| `m01` | `-` | 24 | 46 | 0.083333 | 0 | Nenhuma |
| `m02` | `-` | 16 | 30 | 0.125000 | 1 | `(3,11)` símbolo `a` (1 arco) |
| `m02` | `a` | 23 | 43 | 0.084980 | — | — |
| `m03` | `-` | 12 | 22 | 0.166667 | 3 | `(8,1)` `a` (1), `(1,12)` `b` (1), `(6,6)` `c` (1) |
| `m03` | `a` | 53 | 114 | 0.041364 | — | — |
| `m03` | `ab` | 72 | 160 | 0.031299 | — | — |
| `m03` | `abc` | 76 | 167 | 0.029298 | — | — |
| `m04` | `-` | 17 | 30 | 0.110294 | 1 | `(3,11)` símbolo `a` (1 arco) |
| `m04` | `a` | 20 | 35 | 0.092105 | — | — |
| `m05` | `-` | 21 | 39 | 0.092857 | 12 | `(3,2)` `+` (6 arcos), `(3,10)` `+` (4 arcos), `(5,4)` `+` (2 arcos) |
| `m05` | `-\|{0}` | 22 | 43 | 0.093074 | — | — |
| `m05` | `-\|{2}` | 42 | 82 | 0.047619 | — | — |
| `m05` | `-\|{0,2}` | 43 | 86 | 0.047619 | — | — |
| `m05` | `-\|{1,2}` | 43 | 86 | 0.047619 | — | — |
| `m05` | `-\|{0,1,2}` | 44 | 90 | 0.047569 | — | — |
| `m06` | `-` | 24 | 46 | 0.083333 | 0 | Nenhuma |
| `m07` | `-` | 16 | 38 | 0.158333 | 0 | Nenhuma (`a` inalcançável) |
| `m08` | `-` | 165 | 356 | 0.013156 | 6 | `(27,5)` `a` (2), `(3,23)` `b` (1), `(5,37)` `c` (2), `(3,29)` `d` (1) |
| `m08` | `a` | 314 | 670 | 0.006817 | — | — |
| `m08` | `ab` | 442 | 940 | 0.004822 | — | — |
| `m08` | `abc` | 829 | 1818 | 0.002649 | — | — |
| `m08` | `abcd` | 1169 | 2574 | 0.001885 | — | — |

> - Só é possível haver arestas entre camadas quando a combinação de chaves/bonûs muda (pois é o que define uma camada). Por esse motivo os arcos entre camadas são apenas de casas com bonûs ou chaves.

## 3. Comparação de Modelagens (`m02`, `m03`, `m04`) e Prova do `m05`

### 3.1 Portas como Chão vs. Portas como Parede vs. Grafo de Estados

| Mapa | Abordagem | Passos (BFS) | Caminho válido? | Observação |
| :--- | :--- | ---: | :--- | :--- |
| `m02` | `G_pos` (portas como chão) | `[Pendente: gerar comparacao_modelagem.csv]` | Não | `[Pendente]` |
| `m02` | `G_pos` (portas como parede) | `[Pendente: gerar comparacao_modelagem.csv]` | Não | `[Pendente]` |
| `m02` | `G_est` (modelagem correta) | 34 | Sim | Coleta `a` em `(3,11)` e retorna para cruzar `A` |
| `m03` | `G_pos` (portas como chão) | `[Pendente: gerar comparacao_modelagem.csv]` | Não | `[Pendente]` |
| `m03` | `G_pos` (portas como parede) | `[Pendente: gerar comparacao_modelagem.csv]` | Não | `[Pendente]` |
| `m03` | `G_est` (modelagem correta) | 87 | Sim | Ordem obrigatória `a -> b -> c` |
| `m04` | `G_pos` (portas como chão) | `[Pendente: gerar comparacao_modelagem.csv]` | Não | `[Pendente]` |
| `m04` | `G_pos` (portas como parede) | `[Pendente: gerar comparacao_modelagem.csv]` | Não | `[Pendente]` |
| `m04` | `G_est` (modelagem correta) | 20 | Sim | Coleta `a` e evita esteiras-armadilha |

> - Após gerar `out/parte1/comparacao_modelagem.csv`, preencher os passos e observações faltantes na tabela acima.
> - Portas como chão acavbam por gerar caminhos que que são inválidos pois as portas acabam por ser transpostas sem nenhum tipo de limitação de aquisição de chaves. Portas como parede geram falhas pois tornam o caminho intransponível, mesmo com as chaves necessárias para passar pela porta. A implementação via estados permite com que "novas casas" com condições diferentes sejam geradas a medida que o estado muda. Esse tipo de modelagem acaba por possibilitar, por exemplo, que caminhos intransponívieis no estado atual possam ser transpostos com uma mudança que estados.


### 3.2 Pesos Negativos no `m05` e Prova de Ausência de Ciclo Negativo em `G_est`

Dados observados em `G_est` do `m05` (`m05_bonus.txt`, com 3 casas `+` de bônus):
- Ordem / tamanho de `G_est`: `215` estados e `438` arcos.
- **Dijkstra:** `RECUSA` (presença de arcos de peso `-4` ao consumir cada `+` pela 1ª vez).
- **Bellman-Ford em `G_est`:** `OK`, **20 passos**, **custo total `5`**, terminando em `(1,13)|-|{0,1,2}` (todos os 3 bônus consumidos, sem ciclo negativo).

> 1. A execução do bellmann ford considerando sem o grafo de estados originou o ciclo ciclo = [(5, 4), (5, 5), (5, 4)]
> 2. Se desconsiderarmos o grafo de estados tirando os bonûs, todas outras arestas possuem pesos positivos no grafo do m05. Se você desconsiderar a regra do grafo de estados onde o bônus é consumido apenas uma vez, é possível gerar ciclos negativos visto que é possível realizar um caminho onde é possível passar por esses bônus repetidas vezes, diminuindo o custo a cada passagem por eles.


## 4. Resultados dos 4 Algoritmos e Estados-Armadilha

### 4.1 Tabela Consolidada de Caminhos (`out/parte1/solucoes.csv`)

| Mapa | Algoritmo | Passos | Custo | Status | Observação |
| :--- | :--- | ---: | ---: | :--- | :--- |
| `m01` | BFS | 10 | 30 | `OK` | Caminho direto pela água (`~`) |
| `m01` | Dijkstra | 14 | 20 | `OK` | Desvio pela lama (`,`) e chão (`.`) |
| `m01` | Bellman-Ford | 14 | 20 | `OK` | Mesmo custo ótimo que Dijkstra |
| `m02` | BFS | 34 | 46 | `OK` | — |
| `m02` | Dijkstra | 34 | 46 | `OK` | — |
| `m02` | Bellman-Ford | 34 | 46 | `OK` | — |
| `m03` | BFS | 87 | 119 | `OK` | — |
| `m03` | Dijkstra | 91 | 99 | `OK` | Percurso completo em `out/parte1/percurso_m03.json` |
| `m03` | Bellman-Ford | 91 | 99 | `OK` | — |
| `m04` | BFS | 20 | 36 | `OK` | — |
| `m04` | Dijkstra | 20 | 36 | `OK` | — |
| `m04` | Bellman-Ford | 20 | 36 | `OK` | — |
| `m05` | BFS | 12 | 18 | `OK` | Caminho direto sem passar pelos bônus `+` |
| `m05` | Dijkstra | — | — | `RECUSA` | Recusado por conter pesos negativos (`-4`) |
| `m05` | Bellman-Ford | 20 | 5 | `OK` | Coleta os 3 bônus `{0,1,2}` |
| `m06` | BFS | 10 | 10 | `OK` | Caminho direto em linha reta até `G` |
| `m06` | Dijkstra | — | — | `RECUSA` | Recusado por conter peso negativo (`-2` na fonte `*`) |
| `m06` | Bellman-Ford | — | — | `CICLO_NEGATIVO` | Detalhes em `out/parte1/ciclo_negativo_m06.json` |
| `m07` | BFS | — | — | `SEM_SOLUCAO` | Saída `G` inalcançável a partir de `S` |
| `m07` | Dijkstra | — | — | `SEM_SOLUCAO` | Saída `G` inalcançável a partir de `S` |
| `m07` | Bellman-Ford | — | — | `SEM_SOLUCAO` | Saída `G` inalcançável a partir de `S` |
| `m08` | BFS | 392 | 524 | `OK` | — |
| `m08` | Dijkstra | 396 | 482 | `OK` | — |
| `m08` | Bellman-Ford | 396 | 482 | `OK` | — |

### 4.2 Classificação de Arcos na DFS (`out/parte1/dfs_classificacao.csv`)

DFS executada a partir do estado inicial no grafo de estados **sem** o nó virtual `ALVO`, examinando vizinhos na ordem **N, L, S, O**.

| Mapa | Arcos de árvore | Arcos de retorno | Arcos de avanço | Arcos de cruzamento | Total de arcos | Possui ciclo? (`retorno > 0`) |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `m01` | 23 | 22 | 0 | 1 | 46 | Sim |
| `m02` | 38 | 36 | 0 | 0 | 74 | Sim |
| `m03` | 212 | 231 | 23 | 0 | 466 | Sim |
| `m04` | 36 | 30 | 0 | 0 | 66 | Sim |
| `m05` | 214 | 208 | 5 | 11 | 438 | Sim |
| `m06` | 23 | 22 | 0 | 1 | 46 | Sim |
| `m07` | 15 | 19 | 4 | 0 | 38 | Sim |
| `m08` | 2918 | 3178 | 265 | 3 | 6364 | Sim |

### 4.3 Ciclo Negativo no `m06` (`out/parte1/ciclo_negativo_m06.json`)

- **Ciclo detectado:** `(3,6)|-|{} -> (3,5)|-|{} -> (3,6)|-|{}`
- **Tamanho do ciclo:** `2` transições
- **Custo do ciclo:** `-1`
- **Transições:**
  1. `(3,6)|-|{}` $\xrightarrow{\text{O}}$ `(3,5)|-|{}` (casa destino `*`, peso `-2`)
  2. `(3,5)|-|{}` $\xrightarrow{\text{L}}$ `(3,6)|-|{}` (casa destino `.`, peso `+1`)

### 4.4 Estados-Armadilha (`armadilhas_m04.csv` e `armadilhas_m07.csv`)

Estados alcançáveis a partir de `S` dos quais `ALVO` é inalcançável (identificados via busca a partir de `ALVO` no grafo transposto):

- **`m04` (`4` estados-armadilha de `37` alcançáveis = `10.81%`):**
  - `(1,3)|-|{}` (casa `^`, grau de saída `0` — beco)
  - `(1,3)|a|{}` (casa `^`, grau de saída `0` — beco)
  - `(1,8)|-|{}` (casa `>`, grau de saída `1`)
  - `(1,9)|-|{}` (casa `.`, grau de saída `1`)
- **`m07` (`16` estados-armadilha de `16` alcançáveis = `100.00%`):**
  - Todos os 16 estados da camada `-`: `(1,1)` (`S`), `(1,2)`..`(1,5)` (`.`), `(2,1)` (`.`), `(3,1)`..`(3,5)` (`.`), `(4,1)`..`(4,5)` (`.`).

### 4.5 Discussões Obrigatórias (`m01`, `m06` e `m07`)

#### Discussão `m01`: Divergência entre BFS e Dijkstra

>
>  BFS encontra um caminho de **10 passos / custo 30** (atravessando água `~` de custo 5) enquanto Dijkstra encontra **14 passos / custo 20** (contornando por baixo pela lama `,` de custo 3 e chão `.` de custo 1). Isso ocorre primariamente pelo fato de que o BFS não utiliza como principal métrica para escolher o estado o peso da aresta, ele adiciona estados em uma fila e busca a menor quantidade de pulos, ou passos, para chegar no destino. Enquanto isso, a principal métrica para definir o destino do djikstra é o custo da aresta.

#### Discussão `m06`: Correção do "Exploit" e Opção `--fonte-consumivel`

>
> 1. O mapa m06 possui fontes adjacentes, o que faz com que seja possível pular de uma para outra repetidamente reduzindo o custo até que o número máximo de iterações acabe.
> 2. Para resolver isso, a equipe fez com que a redução no custo só pudesse ser obtida no primeiro relaxamento e nas próximas iterações o custo vira 1.
> 3. Isso resolve a multiplicidade de reduções que ocorre através das múltiplas passagens por essas fontes.

#### Discussão `m07`: Prova de Impossibilidade pela Busca

> Todos os 16 estados alcansáveis são estados armadilha e estão relatados no arquivo armadilhas_m07.csv. Todos os estados alcansáveis são envoltos de paredes e a única saída não-parede é através da porta A. Porém não é possível chegar na chave a, que abriria esta porta.

## 5. Visualizações Estáticas e Labirinto Interativo

### 5.1 Figuras Obrigatórias da Seção 8

Todas as figuras devem conter **título, legenda e rótulos**:

1. **Percurso sobre o mapa `m03` (cor mudando a cada chave):** `out/parte1/percurso_m03.png`
2. **Percurso sobre o mapa `m08` (cor mudando a cada chave):** `out/parte1/percurso_m08.png`
3. **Grafo de estados do `m02` desenhado em camadas (destacando arcos entre camadas):** `out/parte1/grafo_estados_m02.png`
4. **Árvore BFS de estados do `m02` (com níveis visíveis):** `out/parte1/arvore_bfs_m02.png`
5. **Heatmap de multiplicidade das casas do `m08`:** `out/parte1/heatmap_m08.png`

### 5.2 Labirinto Interativo (`app.py`)

A interface interativa da Parte 1 foi implementada em **Streamlit** (`app.py`, executável via `streamlit run app.py`) e atende aos requisitos interativos da Seção 9:
- **Seleção de mapa, algoritmo e modelo:** escolha entre os mapas de `mapas/` (e `data/mapas/`, `data/mapas_grupo/` quando presentes), entre os 4 algoritmos (`BFS`, `Dijkstra`, `Bellman-Ford`, `DFS`) e entre `Grafo de estados` e `Grafo padrão`.
- **Animação passo a passo controlável:** controles de `Início`, `Voltar`, `Reproduzir/Pausar`, `Avançar`, slider de quadro e controle de velocidade (`0.25` a `4.0` quadros/s).
- **Painel de estado atual:** exibe passo atual, custo acumulado (ou distância registrada / classificação de arco na DFS), posição `(linha, coluna)` e símbolo da casa, etiquetas de chaves coletadas e bônus consumidos.
- **Camadas e realces visuais:** exibição simultânea ou filtrada das camadas `(chaves, bônus)` (`Todas as camadas`, `Só as já visitadas`, `Só a camada atual`), rastro colorido por camada, realce hachurado em vermelho para **estados-armadilha** e contorno amarelo para nós de **ciclo negativo**.

---

## 6. Mapas Próprios do Grupo (`data/mapas_grupo/`)

*(Criar 2 mapas em `data/mapas_grupo/` e preencher após a exportação.)*

| Requisito | Arquivo do grupo | Estados ($\|V(G_{\text{est}})\|$) | Arcos ($\|E(G_{\text{est}})\|$) | Passos (BFS) | Custo ótimo (Dijkstra / BF) | Estados-armadilha (% alcançáveis) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| Mapa 1 ($\ge 3$ chaves + esteiras + bônus) | `[PREENCHER]` | — | — | — | — | — |
| Mapa 2 (Armadilha: $\ge 20\%$ estados-armadilha) | `[PREENCHER]` | — | — | — | — | — |

---

## 7. Conferência Manual do Mapa Mínimo de Testes (`tests/test_estados.py`)

Para atender ao requisito mínimo de testes (`test_mapa_minimo_estados_e_arcos_conferidos_a_mao`), foi utilizado um mapa `4 × 6` (dentro do limite `até 5 × 7`):

```text
######
#S.AG#
#a####
######
```

### 7.1 Casas Livres e Teto Teórico

- **Casas livres (`5`):** `(1,1)`=`S`, `(1,2)`=`.`, `(1,3)`=`A`, `(1,4)`=`G`, `(2,1)`=`a`.
- **Chaves:** `1` (`a`); **Bônus:** `0`.
- **Teto teórico:** $5 \times 2^1 \times 2^0 = 10$ estados.

### 7.2 Estados Alcançáveis Calculados à Mão (`7` estados)

- **Camada `-` (`2` estados):**
  1. `(1,1)|-|{}` (estado inicial em `S`)
  2. `(1,2)|-|{}` (chão `.`; a porta `A` em `(1,3)` bloqueia a passagem sem a chave `a`)
- **Camada `a` (`5` estados):**
  3. `(2,1)|a|{}` (coleta da chave `a`)
  4. `(1,1)|a|{}`
  5. `(1,2)|a|{}`
  6. `(1,3)|a|{}` (porta `A` liberada após coletar `a`)
  7. `(1,4)|a|{}` (saída `G` — terminal no mapa)

### 7.3 Arcos Dirigidos Calculados à Mão (`10` entre estados + `1` para `ALVO` = `11`)

Ordem de varredura dos vizinhos: **N, L, S, O**.

| # | Origem | Destino | Mov. | Casa destino | Peso | Observação |
| ---: | :--- | :--- | :---: | :---: | ---: | :--- |
| 1 | `(1,1)\|-|{}` | `(1,2)\|-|{}` | `L` | `.` | 1 | — |
| 2 | `(1,1)\|-|{}` | `(2,1)\|a|{}` | `S` | `a` | 1 | Muda da camada `-` para `a` |
| 3 | `(1,2)\|-|{}` | `(1,1)\|-|{}` | `O` | `S` | 1 | `L` para `(1,3)` bloqueado (`A`) |
| 4 | `(2,1)\|a|{}` | `(1,1)\|a|{}` | `N` | `S` | 1 | — |
| 5 | `(1,1)\|a|{}` | `(1,2)\|a|{}` | `L` | `.` | 1 | — |
| 6 | `(1,1)\|a|{}` | `(2,1)\|a|{}` | `S` | `a` | 1 | Já possui `a`, permanece na camada `a` |
| 7 | `(1,2)\|a|{}` | `(1,3)\|a|{}` | `L` | `A` | 1 | Porta `A` aberta pela chave `a` |
| 8 | `(1,2)\|a|{}` | `(1,1)\|a|{}` | `O` | `S` | 1 | — |
| 9 | `(1,3)\|a|{}` | `(1,4)\|a|{}` | `L` | `G` | 1 | Chegada à saída `G` |
| 10 | `(1,3)\|a|{}` | `(1,2)\|a|{}` | `O` | `.` | 1 | — |
| 11 | `(1,4)\|a|{}` | `ALVO` | `-` | `-` | 0 | Arco virtual terminal (não entra nas métricas) |

Todos esses valores (`5` casas livres, `7` estados alcançáveis divididos em `2` e `5` por camada, `10` arcos entre estados, `1` arco virtual até `ALVO`, `11` transições totais) são validados automaticamente por `pytest tests/test_estados.py`.

---

## 8. Limitações e Conclusões (Parte 1)

> A implementação do grafo de estados pode gerar um overhead no sistema quando o grafo possui múltiplos estados, pois todo estado é uma nova instância de objeto. O tratamento de ciclos negativos acaba por ser outra limitação, pois acaba descaracterizando algoritmos como o bellman ford que de forma tradicional não possui mudanças de pesos durante sua execução. De um modo geral, a utilização de grafos de estado possibilita uma implementações mais completas e robustas para o problema de labirintos.


## 9. Matriz de Contribuição da Equipe

*(Confirmar a divisão de **Dono** e **Revisor** por pacote, garantindo que todos os integrantes tenham commits em pelo menos 2 pacotes.)*

| Pacote | Escopo (enunciado) | Dono | Revisor | Evidências observadas no histórico Git |
| :--- | :--- | :--- | :--- | :--- |
| **P1** — Modelagem e grafo de estados | `io.py`, `estados.py`, `arestas`, `test_io`, `test_estados` | `[PREENCHER]` | `[PREENCHER]` | `estados.py`, `labirinto.py` (`David-git123`, `juliavfe`); `test_estados.py`, `test_io.py` (`gabrielvictalino`) |
| **P2** — Algoritmos e testes | BFS, DFS com classificação, Dijkstra, Bellman-Ford com ciclo, transposto e testes | `[PREENCHER]` | `[PREENCHER]` | `algorithms.py` (`David-git123`, `juliavfe`, `AlineTakakura`, `gabrielvictalino`); `test_bfs/dfs/dijkstra/bellman_ford.py` (`gabrielvictalino`) |
| **P3** — Análises da Parte 1 | Métricas, camadas, comparação de modelagens, prova do `m05`, correção do `m06`, mapas do grupo | `[PREENCHER]` | `[PREENCHER]` | `solve.py`, exportação Parte 1 (`gabrielvictalino`, `juliavfe`) |
| **P4** — Parte 2: dados e experimentos | Proposta, dataset, pesos negativos, casos obrigatórios, benchmark e escalabilidade | `[PREENCHER]` | `[PREENCHER]` | `io.py`, `graph.py`, `cli.py`, `solve.py`, `notebooks/`, `tmdb_limpo.csv.gz` (`AlineTakakura`) |
| **P5** — Visualização e comunicação | Figuras da Parte 1, app interativo, visualizações AVD, README e PDF *(dividido entre os outros pacotes em grupos de 4)* | `[PREENCHER]` | `[PREENCHER]` | `app.py` (`juliavfe`, `David-git123`), `viz.py` (`juliavfe`), `taxi_labirinto/` (`David-git123`) |
