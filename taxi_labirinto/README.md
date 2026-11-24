# Última corrida — Táxi Labirinto

Jogo 2D para Streamlit: busque passageiros, leve cada um ao destino correto e
volte para a casa do motorista. A vitória exige todas as entregas antes de G.

## Executar

Requer Python 3.10 ou mais recente. Extraia o ZIP inteiro e, dentro de
`taxi_labirinto`, execute:

```bash
python -m pip install -r requirements.txt
python -m streamlit run jogo.py
```

Abra o endereço mostrado pelo Streamlit, normalmente http://localhost:8501.
Clique em **Dirigir** ou no tabuleiro e use as setas. Você pode segurar uma seta
ou usar os quatro botões na tela. O navegador precisa manter o foco no tabuleiro
para enviar as teclas ao jogo. A velocidade de repetição é ajustável na barra lateral.

Não é necessário instalar Node, gerar sprites novamente ou ter uma chave de API.
Os arquivos do componente e todos os PNGs já estão incluídos.

## Arquivos

| Arquivo/pasta | Função |
| --- | --- |
| `jogo.py` | Interface Streamlit, seleção/upload de mapa, reinício e comparação final |
| `utils.py` | Validação, construção/refinamento do grafo, serialização, validação do percurso e chamada ao Dijkstra |
| `componente/index.html` | Tabuleiro, teclado, animação, painel de passageiros e reprodução da rota ótima |
| `sprites/` | Doze PNGs separados, RGBA 32 bits, 128 × 128 pixels, com transparência |
| `mapas/` | Três labirintos `.txt` com dificuldade crescente |
| `src/` | Cópias dos módulos necessários do projeto original |
| `tests/test_jogo.py` | Testes de regras e comparação dos caminhos mínimos |

Mantenha `componente/` junto de `jogo.py`: ele é necessário para capturar o
teclado e desenhar o jogo no navegador. A maior parte da lógica está em Python;
o JavaScript consulta as transições já calculadas, sem gerar caminhos alternativos.

## Regras e formato dos mapas

| Caractere | Significado | Custo de entrada |
| --- | --- | ---: |
| `#` | Parede, representada por casa, loja ou prédio | Impassável |
| `.` | Rua | 1 |
| `S` | Partida | 1 ao revisitar; começar custa 0 |
| `G` | Casa do motorista, bloqueada até concluir as entregas | 1 |
| `a`, `b`, `c`, `d` | Passageiros Ana, Bento, Caio e Dora | 1 |
| `A`, `B`, `C`, `D` | Destinos correspondentes | 1 |
| `,` | Obras/terreno lento | 3 |
| `~` | Alagamento | 5 |
| `>`, `<`, `^`, `v` | Mão única: determina a direção permitida para **sair** da célula | 1 |

- O táxi leva no máximo **três passageiros além do motorista**.
- Entrar em uma célula de passageiro faz o embarque automaticamente. Com três
  pessoas a bordo, a célula de um quarto passageiro esperando fica bloqueada.
  É necessário entregar alguém e voltar para buscá-lo.
- Entrar no destino correspondente faz a entrega e libera um lugar.
- Um destino fica bloqueado até que seu passageiro seja buscado. Depois da
  entrega, permanece acessível, preservando a abertura das portas do projeto.
- Passageiros entregues não voltam ao ponto de embarque e não embarcam novamente.
- G é terminal: só pode ser acessado depois de entregar todos.
- Só movimentos aceitos contam como passos e custo. Colidir com paredes não conta.
- As ruas de mão única podem produzir estados sem retorno; o jogo mostra aviso
  de estado sem solução e permite reiniciar pela barra lateral.
- A comparação avalia **custo do percurso**, não segundos de jogo. Em terrenos
  diferentes, menos passos não significa necessariamente menor custo.

Os mapas devem ser retangulares, cercados por `#`, com exatamente um `S` e um `G`.
Cada letra minúscula deve ter exatamente uma maiúscula correspondente; não use
passageiros ou destinos repetidos. São aceitos até quatro passageiros.
Use até 30 linhas e 40 colunas. O refinamento limita o total a 12.000 estados.
Mapas sem solução são recusados antes de começar.

**Custos negativos:** `+` e `*` fazem parte do formato original, mas têm custos
negativos e são recusados com uma explicação. O jogo preserva os demais custos
e não modifica pesos para forçar a execução de Dijkstra.

Coloque seus mapas na pasta `mapas/` ou use o upload na barra lateral.

## Mapas incluídos

| Mapa | Passageiros | Proposta |
| --- | ---: | --- |
| `01_primeira_corrida.txt` | 2 | Aprender embarque, entrega e retorno para casa |
| `02_tres_lugares.txt` | 4 | Planejar entregas para liberar o quarto lugar necessário |
| `03_hora_do_rush.txt` | 4 | Escolher entre vias, obras, alagamentos e mão única |

## Compatibilidade com Grafos-e-AVD

Base consultada: branch `main` de
https://github.com/gabrielvictalino/Grafos-e-AVD,
commit `14df12e1631f962da619382ccc826cb8e57611f2`, em 24/11/2026.

Os arquivos `src/graphs/labirinto.py`, `src/graphs/estados.py`,
`src/graphs/algorithms.py` e `src/viz.py` são cópias **sem alterações** desse commit.

Fluxo real utilizado:

1. `gerar_labirinto(caminho)` cria os nós e as arestas físicas do mapa.
2. `preparar_estados(labirinto)` fornece os modelos e estados inicial/final.
3. `bfs_grafo_estados_exploracao(modelos, inicio, fim)` gera o grafo original.
4. `gerar_grafo_taxi()` em `utils.py` explora esse grafo e o refina para incorporar
   as entregas, os três lugares e a condição de vitória. Essa adaptação é
   necessária: a BFS original só controla as chaves coletadas, sem desembarque.
5. `bfs_estados_armadilha()` identifica estados sem caminho até o objetivo.
6. O carro percorre exclusivamente as arestas do grafo refinado.
7. Ao vencer, Python reproduz e valida todos os movimentos recebidos.
8. `converter_grafo_estados()` converte o **mesmo grafo** para os nós esperados
   por `algorithms.dijkstra()`, que é executado sem reimplementação.

O refinamento mantém `No_estados`, `Camada` e o formato original das arestas:
`(origem, destino, movimento, casa_destino, peso)`.

No jogo, `estado.chaves` guarda todos os passageiros **já buscados**. O atributo
`estado.bonus` guarda os índices dos passageiros **entregues** (`a=0, ..., d=3`).
Portanto, `a_bordo = coletados - entregues`. Esse reaproveitamento do atributo
é restrito aos estados novos do jogo; os estados base e os módulos originais
não são alterados. Bônus negativos de terreno não são usados neste modo.

A conversão reserva o tipo `G` para o ALVO virtual comum. Isso evita que o
Dijkstra do projeto pare em um estado físico de G incorreto. O arco virtual
custa zero e é retirado da contagem de movimentos da comparação.

O grafo fica em cache somente para leitura. A partida é isolada por sessão e
identificador; o componente conserva os movimentos durante reruns da interface.
**Reiniciar corrida** descarta o percurso atual. Atualizar a página inteira
inicia uma nova sessão Streamlit e pode reiniciar a partida.

### Adicionar ao repositório existente

Copie `jogo.py`, `utils.py`, `componente/` e `sprites/` para a raiz do seu projeto;
adicione os novos mapas à pasta `mapas/`. Use os módulos `src/` existentes se
corresponderem às assinaturas do commit citado. O pacote completo também roda
separadamente, sem depender de outro checkout. O `app.py` de visualização não
precisa ser alterado.

## Resultado e reprodução

Ao chegar em G, o painel apresenta custo e passos do jogador e da rota ótima,
custo adicional e eficiência (`100 × custo ótimo / custo do jogador`).
As rotas aparecem sobrepostas em amarelo e verde e podem ser ocultadas
individualmente. O botão **Rever Dijkstra** reproduz a rota ótima com passageiros
e entregas de cada estado. O controle deslizante permite examinar cada passo.
Durante a reprodução, o painel do jogo acompanha o passo mostrado. O resumo abaixo da pista conserva o resultado do jogador.
O relatório JSON contém os movimentos, os índices das rotas e o mapa;
`serializar_grafo(gerar_grafo_taxi(texto))` permite resolver os índices em estados.

## Sprites

Estética de pixel art 2D inspirada em jogos de 32 bits. Os PNGs são efetivamente
RGBA com 8 bits por canal (32 bits por pixel), 128 × 128, fundo transparente.
O jogo desenha cada quadrícula em 64 × 64 e gira o sprite do táxi conforme a
direção; assim, não depende de quatro imagens redundantes do carro.

Arquivos: `carro.png`, `passageiro_a.png`, `passageiro_b.png`, `passageiro_c.png`,
`passageiro_d.png`, `casa.png`, `loja.png`, `predio.png`, `mercado.png` e
`casa_motorista.png`. Os quatro tipos de construção variam nas paredes; os
destinos recebem a letra e a cor do passageiro para diferenciá-los das paredes.
Os sprites transparentes `obras.png` e `alagamento.png` aparecem sobre o asfalto. As marcas +2 e +4 indicam o acréscimo ao custo normal de 1. A fachada do passageiro acende ao embarcar e a casa do motorista acende após a última entrega. Passe pelo quadrado de mesma letra na rua para desembarcar. Em mapas personalizados com paradas sem terreno vizinho disponível, o jogo cria uma pequena calçada na esquina da própria parada para acomodar a fachada.

## Verificação

```bash
python -m unittest discover -s tests -v
```

Os testes conferem os três mapas, capacidade em todos os estados, bloqueio do
quarto embarque, entregas, portas, G, mão única, custos, percursos inválidos e
serialização. O custo do Dijkstra original é comparado com um oráculo independente
que utiliza fila de prioridade apenas nos testes.

Referência do componente Streamlit:
https://docs.streamlit.io/develop/concepts/custom-components/components-v1/intro
