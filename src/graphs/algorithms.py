"""Algoritmos gerais de busca e caminhos mínimos."""

from src.graphs.labirinto import Camada, No_estados, buscar_no_estado_a_partir_posicao
from src.graphs.estados import (
    adicionar_estado_a_camada,
    bfs,
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


    return distancias, anteriores, (mudou,ciclo)


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
