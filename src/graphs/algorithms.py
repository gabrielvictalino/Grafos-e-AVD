"""Algoritmos gerais de busca e caminhos mínimos."""

from src.graphs.labirinto import Camada, No_estados, buscar_no_estado_a_partir_posicao
from src.graphs.estados import (
    adicionar_estado_a_camada,
    bfs_estados_armadilha,
    bfs_grafo_estados_exploracao,
    bfs_grafo_nos,
    converter_grafo_estados,
    formatar_estado,
    verificar_bonus,
    verificar_bloqueio,
    verificar_chaves,
)
from src.viz import exportar_arestas, exportar_heatmap
from collections import deque


def bfs(lista_nos, origem):
    """Retorna níveis e predecessores da BFS a partir de ``origem``."""
    if origem not in lista_nos:
        raise ValueError("A origem deve pertencer à lista de nós.")

    niveis = {no: float("inf") for no in lista_nos}
    anteriores = {no: None for no in lista_nos}
    niveis[origem] = 0
    fila = deque([origem])

    while fila:
        atual = fila.popleft()
        for aresta in atual.lista_arestas:
            if aresta == 0:
                continue
            vizinho = aresta.destino
            if niveis[vizinho] == float("inf"):
                niveis[vizinho] = niveis[atual] + 1
                anteriores[vizinho] = atual
                fila.append(vizinho)

    return niveis, anteriores

def dijkstra(lista_nos, origem):
    for no in lista_nos:
        for i in no.lista_arestas:
            if i !=0 and i.custo<0:
                return None,None,True

    anteriores={} # Para escrever o caminho no final
    distancias= {} #guarda o menor custo
    visitados={} #fechados
    for no in lista_nos:
        distancias[no] = float('inf')
        visitados[no] = False

        anteriores[no] = None
    distancias[origem] = 0
    while True:
        u= None
        menor_distancia=float('inf')
        for no in lista_nos:
            if not visitados[no] and distancias[no] < menor_distancia:
                menor_distancia = distancias[no]
                u = no
        if u is None or menor_distancia == float('inf'):
            break
        if u.tipo == "G":
            break
        visitados[u] = True
        for aresta in u.lista_arestas:
            if aresta!= 0:
                v=aresta.destino
                if distancias[v] > distancias[u] + aresta.custo:
                    distancias[v] = distancias[u] + aresta.custo
                    anteriores[v] = u
    return distancias, anteriores,False


def bellman_ford(listas_nos, origem):
    anteriores = {}
    distancias = {}
    arestas = []

    for no in listas_nos:
        distancias[no] = float('inf')
        anteriores[no] = None

        for i in no.lista_arestas:
            if i != 0:
                arestas.append(i)

    distancias[origem] = 0

    # Relaxamento das arestas
    for i in range(len(listas_nos) - 1):
        mudou = False

        for aresta in arestas:
            org = aresta.origem
            dest = aresta.destino
            peso = aresta.custo

            if distancias[org] != float('inf'):
                if distancias[org] + peso < distancias[dest]:
                    distancias[dest] = distancias[org] + peso
                    anteriores[dest] = org
                    mudou = True

        if not mudou:
            break

    # Passagem adicional para detectar ciclo negativo
    mudou = False
    atual = None
    ciclo = []

    for aresta in arestas:
        org = aresta.origem
        dest = aresta.destino
        peso = aresta.custo

        if distancias[org] != float('inf'):
            if distancias[org] + peso < distancias[dest]:
                distancias[dest] = distancias[org] + peso
                anteriores[dest] = org
                mudou = True
                atual = dest

    if mudou:

        # Entra no ciclo
        for _ in range(len(anteriores)):
            atual = anteriores[atual]

        # Reconstrói o ciclo
        inicio_ciclo = atual
        ciclo = [inicio_ciclo]

        atual = anteriores[inicio_ciclo]

        while atual != inicio_ciclo:
            ciclo.append(atual)
            atual = anteriores[atual]

        ciclo.append(inicio_ciclo)
        ciclo.reverse()


    return distancias, anteriores, mudou, ciclo


def dfs(lista_nos, origem, detalhado=False):
    anteriores = {} # pra escrever o caminho no final
    distancias = {} # custo do caminho encontrado pelo DFS
    cores = {}

    for no in lista_nos:
            distancias[no] = float('inf')
            cores[no] = 'branco'
            anteriores[no] = None

    descoberta = {}
    termino = {}
    ordem = []
    classificacao = []
    contagem = {
        'arvore': 0,
        'retorno': 0,
        'avanco': 0,
        'cruzamento': 0,
    }

    if origem not in cores:
        raise ValueError('A origem deve pertencer a lista de nos.')

    tempo = 1
    cores[origem] = 'cinza'
    descoberta[origem] = tempo
    distancias[origem] = 0
    ordem.append(origem)

    # o iterador guarda qual será a próxima aresta examinada
    pilha = [(origem, iter(origem.lista_arestas))]

    while pilha:
        u, arestas = pilha[-1]
        aresta = next(arestas, None)

        if aresta is None:
            # todas as arestas desse nó foram examinadas
            cores[u] = 'preto'
            tempo += 1
            termino[u] = tempo
            pilha.pop()
            continue

        if aresta == 0:
            continue

        v = aresta.destino

        if cores[v] == 'branco':
            tipo = 'arvore'
            anteriores[v] = u
            distancias[v] = distancias[u] + aresta.custo

            cores[v] = 'cinza'
            tempo += 1
            descoberta[v] = tempo
            ordem.append(v)

            pilha.append((v, iter(v.lista_arestas)))

        elif cores[v] == 'cinza':
            # volta a um ancestral ativo ou ao próprio nó
            tipo = 'retorno'

        elif descoberta[u] < descoberta[v]:
            # destino já encerrado e descendente de u
            tipo = 'avanco'

        else:
            # destino já encerrado em outro ramo da busca
            tipo = 'cruzamento'

        classificacao.append((u, v, tipo))
        contagem[tipo] += 1

    if detalhado:
        return {
            'distancias': distancias,
            'anteriores': anteriores,
            'descoberta': descoberta,
            'termino': termino,
            'ordem': ordem,
            'classificacao': classificacao,
            'contagem': contagem,
            'tem_ciclo': contagem['retorno'] > 0,
        }

    return distancias, anteriores

def bfs(lista_nos_estados,estado_inicial,estado_final):
    
    estado_inicial.estado_de_visualizacao = "Visitado"
    
    anteriores = {estado_inicial: None}
    lista_estados_analisados = [estado_inicial]

    while lista_estados_analisados:

        elemento_analisado = lista_estados_analisados.pop(0)

        # Verifica se chegou ao destino
        if elemento_analisado == estado_final:
            break

        elemento_analisado.estado_de_visualizacao = "Encerrado"

        for i in range(4):

            aresta = elemento_analisado.no_pos.lista_arestas[i]

            if aresta == 0:
                continue

            novo_elemento = buscar_no_estado_a_partir_posicao(
                lista_nos_estados,
                aresta.destino
            )

            if novo_elemento is None:
                continue
            if novo_elemento.estado_de_visualizacao != "Não Visitado":
                continue
            anteriores[novo_elemento] = elemento_analisado

            lista_estados_analisados.append(novo_elemento)

            anteriores[novo_elemento] = elemento_analisado
            novo_elemento.estado_de_visualizacao = "Visitado"

        
    caminho = []
    
    if estado_final not in anteriores:
        return None

    atual = estado_final

    while atual is not None:
        caminho.append(atual.no_pos)
        atual = anteriores.get(atual)

    caminho.reverse()

    return caminho


def bfs_grafo_estados_exploracao(lista_nos_estados, estado_inicial, estado_final):

    estado_inicial.bonus = frozenset()

    # Cada nó "+" (ordenado por linha, coluna) recebe um id: 0, 1, 2, ...
    posicoes_bonus = sorted({
        (no.no_pos.posicao_linha, no.no_pos.posicao_coluna)
        for no in lista_nos_estados
        if no.no_pos.tipo == "+"
    })
    mapa_bonus = {pos: indice for indice, pos in enumerate(posicoes_bonus)}

    arestas_geradas = []

    camadas = [Camada()]
    camadas[0].chaves = ""

    estado_inicial.chaves = ""
    estado_inicial.estado_de_visualizacao = "Visitado"

    lista_estados_analisados = [estado_inicial]

    # Identifica os estados por posição e chaves
    estados = {
        (estado_inicial.no_pos, estado_inicial.chaves, estado_inicial.bonus): estado_inicial
    }

    while lista_estados_analisados:

        elemento_analisado = lista_estados_analisados.pop(0)

        # Registra o estado na camada
        adicionar_estado_a_camada(camadas, elemento_analisado)
        if elemento_analisado not in elemento_analisado.no_pos.lista_estados_gerados:
            elemento_analisado.no_pos.lista_estados_gerados.append(elemento_analisado)
        elemento_analisado.estado_de_visualizacao = "Encerrado"

        # Estados G possuem uma transição até ALVO
        if elemento_analisado.no_pos.tipo == "G":

            arestas_geradas.append((
                elemento_analisado,
                "ALVO",
                "-",
                "-",
                0
            ))

            # Considerando G como terminal
            continue

        for i in range(4):

            aresta = elemento_analisado.no_pos.lista_arestas[i]

            if aresta == 0:
                continue

            novo_elemento = buscar_no_estado_a_partir_posicao(
                lista_nos_estados,
                aresta.destino
            )

            if novo_elemento is None:
                continue

            # Verifica se o movimento é permitido
            esta_bloqueado = verificar_bloqueio(
                novo_elemento,
                elemento_analisado.chaves
            )

            if esta_bloqueado:
                continue

            casa_destino = novo_elemento.no_pos.tipo

            # Cria um estado independente, herdando chaves e bônus
            novo_elemento = No_estados(
                elemento_analisado.chaves,
                "-",
                "Não Visitado",
                novo_elemento.no_pos
            )
            novo_elemento.bonus = elemento_analisado.bonus

            # Atualiza as chaves ao entrar no destino
            camadas, novo_elemento = verificar_chaves(
                novo_elemento, camadas
            )

            # Consome o bônus (se houver) e define o custo da transição
            novo_elemento, custo_transicao = verificar_bonus(
                novo_elemento,
                aresta.custo,
                mapa_bonus
            )

            identificador = (
                novo_elemento.no_pos,
                novo_elemento.chaves,
                novo_elemento.bonus
            )

            # Verifica se o estado já foi gerado
            if identificador in estados:
                novo_elemento = estados[identificador]

            else:
                estados[identificador] = novo_elemento

                lista_estados_analisados.append(novo_elemento)

                novo_elemento.estado_de_visualizacao = "Visitado"

            # Registra a transição válida
            arestas_geradas.append((
                elemento_analisado,
                novo_elemento,
                dicionario_direcoes_ao_contrario[i],
                casa_destino,
                custo_transicao
            ))

    return arestas_geradas, camadas

def bfs_estados_armadilha(arestas_geradas,camadas):
    estados_gerados = {
        estado
        for camada in camadas
        for estado in camada.lista_nos_estados
    }
    grafo_transposto = {}
    for origem,destino,movimento,casa,peso in arestas_geradas:
        if destino not in grafo_transposto:
            grafo_transposto[destino] = []
        grafo_transposto[destino].append(origem)
    fila = ["ALVO"]
    nos_alcansaveis = {"ALVO"}
    while fila:
        no = fila.pop(0)
        vizinhos_no = grafo_transposto.get(no, [])
        for i in vizinhos_no:
            if i not in nos_alcansaveis:
                fila.append(i)
                nos_alcansaveis.add(i)
    estados_armadilha = estados_gerados - nos_alcansaveis
    return estados_armadilha
        
        
        
        
    
        
            
    

    
# def bfs_grafo_estados(lista_nos_estados, estado_inicial, estado_final):

#     camadas = [Camada()]
#     camadas[0].chaves = ""
#     estado_inicial.chaves = ""
#     estado_inicial.estado_de_visualizacao = "Visitado"

#     anteriores = {estado_inicial: None}
#     lista_estados_analisados = [estado_inicial]

#     while lista_estados_analisados:

#         elemento_analisado = lista_estados_analisados.pop(0)

#         camadas,elemento_analisado = verificar_chaves(
#             elemento_analisado, camadas
#         )
#         elemento_analisado = adicionar_estado_a_camada(camadas,elemento_analisado)
#         if elemento_analisado is None:
#             continue
#         # Verifica se chegou ao destino
#         if elemento_analisado.no_pos.tipo == "G":
#             estado_final = elemento_analisado
#             break

#         elemento_analisado.estado_de_visualizacao = "Encerrado"

#         for i in range(4):

#             aresta = elemento_analisado.no_pos.lista_arestas[i]

#             if aresta == 0:
#                 continue

#             novo_elemento = buscar_no_estado_a_partir_posicao(
#                 lista_nos_estados,
#                 aresta.destino
#             )

#             if novo_elemento is None:
#                 continue

#             # Verifica se o nó está bloqueado
#             esta_bloqueado = verificar_bloqueio(
#                 novo_elemento,
#                 elemento_analisado.chaves
#             )

#             if esta_bloqueado:
#                 continue

#             # Propaga as chaves em toda movimentação
#             novas_chaves = elemento_analisado.chaves
#             novo_elemento = No_estados(
#                 "-", "-",
#                 novo_elemento.no_pos.tipo,
#                 "Não Visitado",
#                 novo_elemento.no_pos
#             )
#             #evita que o elemento "novo_elemento", que é compartulhado com a lista de estados, seja também alterado de forma global.
#             novo_elemento.chaves = novas_chaves

#             anteriores[novo_elemento] = elemento_analisado

#             lista_estados_analisados.append(novo_elemento)

#             novo_elemento.estado_de_visualizacao = "Visitado"

#     # Reconstrução do caminho
#     caminho = []

#     if estado_final not in anteriores:
#         return None

#     atual = estado_final

#     while atual is not None:
#         caminho.append(atual.no_pos)
#         atual = anteriores.get(atual)

#     caminho.reverse()

#     return caminho, camadas


def verificar_chaves(elemento_analisado, camadas):

    if elemento_analisado.no_pos.tipo in ("a", "b", "c", "d"):

        chave = elemento_analisado.no_pos.tipo

        # Evita adquirir a mesma chave novamente
        if chave not in elemento_analisado.chaves:
            novo_estado = No_estados(
                "-", "-",
                "Não Visitado",
                elemento_analisado.no_pos
            )
            novo_estado.chaves = elemento_analisado.chaves
            novo_estado.bonus = elemento_analisado.bonus
            novo_estado.chaves = "".join(
                sorted(elemento_analisado.chaves + chave)
            )

            # Verifica se já existe uma camada com essas chaves
            for camada in camadas:
                if camada.chaves == novo_estado.chaves:
                    return camadas, novo_estado

            # Cria uma nova camada
            nova_camada = Camada()
            nova_camada.chaves = novo_estado.chaves
            camadas.append(nova_camada)

            return camadas,novo_estado

    return camadas,elemento_analisado

def verificar_bonus(elemento_analisado, custo_padrao, mapa_bonus):

    if elemento_analisado.no_pos.tipo == "+":
        pos = (
            elemento_analisado.no_pos.posicao_linha,
            elemento_analisado.no_pos.posicao_coluna,
        )
        id_b = mapa_bonus[pos]

        if id_b not in elemento_analisado.bonus:
            # 1a vez: consome o bonus e aplica custo -4
            # (união imutável: cria um novo frozenset, sem alterar o anterior)
            elemento_analisado.bonus = elemento_analisado.bonus | frozenset({id_b})
            return elemento_analisado, -4

        else:
            # já consumido: comporta-se como chão (custo 1)
            return elemento_analisado, 1

    # Qualquer outra casa mantém bônus e custo padrão
    return elemento_analisado, custo_padrao

def verificar_bloqueio(novo_elemento, chaves):

    if novo_elemento.bloqueado == 1:

        tipo_porta = novo_elemento.no_pos.tipo.lower()

        if tipo_porta not in chaves:
            return True

    return False        

def adicionar_estado_a_camada(camadas,elemento_analisado):

        estado_existente = False
        for camada in camadas:
            for estado in camada.lista_nos_estados:
                if (estado.no_pos == elemento_analisado.no_pos
                        and estado.chaves == elemento_analisado.chaves and estado.bonus == elemento_analisado.bonus):
                    estado_existente = True
                    break
            if estado_existente == True:
                break

        if estado_existente:
            return None
        else:


            # Adiciona o estado à camada correspondente
            camada_encontrada = None

            for camada in camadas:
                if camada.chaves == elemento_analisado.chaves:
                    camada_encontrada = camada
                    break

            if camada_encontrada is None:
                camada_encontrada = Camada()
                camada_encontrada.chaves = elemento_analisado.chaves
                camadas.append(camada_encontrada)

            camada_encontrada.lista_nos_estados.append(elemento_analisado)
            return elemento_analisado

def formatar_estado(estado):

    linha = estado.no_pos.posicao_linha
    coluna = estado.no_pos.posicao_coluna

    chaves = estado.chaves if estado.chaves else "-"

    bonus = getattr(estado, "bonus", frozenset())

    bonus_formatado = "{" + ",".join(
        str(b) for b in sorted(bonus)
    ) + "}"

    return f"({linha},{coluna})|{chaves}|{bonus_formatado}"




#ajusta desempacotamento de 5 elementos e exclui arcos virtuais até ALVO
def exportar_arestas(lista_arestas, nome_mapa, diretorio="out/parte1"):

    os.makedirs(diretorio, exist_ok=True)

    caminho_arquivo = os.path.join(
        diretorio,
        f"arestas_{nome_mapa}.csv"
    )

    with open(
        caminho_arquivo,
        "w",
        newline="",
        encoding="utf-8"
    ) as arquivo:

        escritor = csv.writer(arquivo)

        escritor.writerow([
            "origem",
            "destino",
            "movimento",
            "casa_destino",
            "peso"
        ])

        for origem, destino, movimento, casa_destino, peso in lista_arestas:
            if destino == "ALVO":
                continue

            escritor.writerow([
                formatar_estado(origem),
                formatar_estado(destino),
                movimento,
                casa_destino,
                peso
            ])

    return caminho_arquivo




def exportar_heatmap(heatmap, nome_mapa):

    os.makedirs("out/parte1", exist_ok=True)

    # Converte None (paredes) para NaN
    matriz = [
        [float("nan") if valor is None else valor for valor in linha]
        for linha in heatmap
    ]

    fig, ax = plt.subplots(figsize=(10, 8))

    imagem = ax.imshow(
        matriz,
        cmap="hot",
        interpolation="nearest",
        vmin=0
    )

    ax.set_title("Heatmap de estados por posição")
    ax.set_xlabel("Coluna")
    ax.set_ylabel("Linha")

    fig.colorbar(
        imagem,
        ax=ax,
        label="Quantidade de estados"
    )

    caminho = f"out/parte1/heatmap_{nome_mapa}.png"

    fig.savefig(
        caminho,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(fig)

    return caminho




from .labirinto import Aresta, No 


# adiciona parâmetro opcional incluir_alvo para permitir métricas/DFS sem nó virtual
def converter_grafo_estados(arestas_geradas, camadas, estado_inicial, estado_final, incluir_alvo=True):
    """Retorna (lista_nos, inicio, alvo, nos_por_estado).
    estado_inicial e estado_final são os No_estados de preparar_estados.
    nos_por_estado associa cada estado original ao No correspondente e também
    contém a entrada "ALVO" quando incluir_alvo=True. A saída física fornece a
    posição do alvo virtual, inclusive quando a exploração não alcança nenhuma
    instância de G.
    """
    nos_por_estado = {}
    for camada in camadas:
        for estado in camada.lista_nos_estados:
            casa = estado.no_pos
            # O Dijkstra do projeto para no primeiro No de tipo G.
            # Reservamos esse tipo para o ALVO comum a todas as saídas.
            tipo = "." if (incluir_alvo and casa.tipo == "G") else casa.tipo
            nos_por_estado[estado] = No(casa.posicao_linha, casa.posicao_coluna, tipo)

    alvo = None
    if incluir_alvo:
        saida = estado_final.no_pos
        alvo = No(saida.posicao_linha, saida.posicao_coluna, "G")
        nos_por_estado["ALVO"] = alvo

    for origem, destino, movimento, _, peso in arestas_geradas:
        if not incluir_alvo and destino == "ALVO":
            continue
        no_origem = nos_por_estado[origem]
        no_destino = nos_por_estado[destino]
        # G tem um único arco virtual. Usamos o primeiro slot de adjacência.
        direcao = "N" if destino == "ALVO" else movimento
        no_origem.adicionar_adjacencia(direcao, Aresta(no_origem, no_destino, peso))
        no_origem.grau_saida += 1
        no_destino.grau_entrada += 1

    lista_nos = list(nos_por_estado.values())
    return lista_nos, nos_por_estado[estado_inicial], alvo, nos_por_estado


