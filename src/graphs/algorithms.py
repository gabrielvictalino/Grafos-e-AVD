from graphs.labirinto import buscar_no_estado_a_partir_posicao
from graphs.labirinto import Camada
from graphs.labirinto import No_estados


def dijkstra(lista_nos, origem):
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
    return distancias, anteriores


def dijkstra_estados(lista_nos_estados, origem, final):
    anteriores={} # Para escrever o caminho no final
    distancias= {} #guarda o menor custo
    visitados={} #fechados
    camadas = [Camada()]
    camadas[0].lista_nos_estados = lista_nos_estados
    
    for no in lista_nos_estados:
        distancias[no] = float('inf')
        visitados[no] = False
        anteriores[no] = None
        
    distancias[origem] = 0
    while True:
        u= None
        menor_distancia=float('inf')
        for no in lista_nos_estados:
            if not visitados[no] and distancias[no] < menor_distancia and not verificar_bloqueio(no,no.chaves):
                menor_distancia = distancias[no]
                u = no
        if u is None or menor_distancia == float('inf'):
            break
            
        visitados[u] = True
        camadas = verificar_chaves(u, camadas)
        chaves = u.chaves
        adicionar_estado_a_camada(camadas,u,chaves)

        for aresta in u.lista_arestas:
            if aresta!= 0:
                v=aresta.destino
                if distancias[v] > distancias[u] + aresta.custo:
                    distancias[v] = distancias[u] + aresta.custo
                    anteriores[v] = u
    return distancias, anteriores

def bellman_ford(listas_nos,origem):
    anteriores={}
    distancias={}
    arestas=[]
    for no in listas_nos:
        distancias[no]= float('inf')
        anteriores[no]= None
        for i in no.lista_arestas:
            if i != 0:
                arestas.append(i)
    distancias[origem]= 0
    
    for i in range (len(listas_nos)-1):
        mudou =False
        for aresta in arestas:
            org = aresta.origem
            dest = aresta.destino
            peso = aresta.custo
            
            if distancias[org]!= float('inf'):
                if distancias[org] + peso< distancias[dest]:
                    distancias[dest]=distancias[org] + peso
                    anteriores[dest]=org
        mudou= True
        if not mudou:
            break

        return distancias, anteriores

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

def bfs_grafo_nos(lista_nos_estados,estado_inicial,estado_final):
    
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

            lista_estados_analisados.append(novo_elemento)

        
        caminho = []
        
        if estado_final not in anteriores:
            return None
    
        atual = estado_final
    
        while atual is not None:
            caminho.append(atual.no_pos)
            atual = anteriores.get(atual)
    
        caminho.reverse()
    
        return caminho

def bfs_grafo_estados(lista_nos_estados, estado_inicial, estado_final):

    camadas = [Camada()]
    camadas[0].chaves = ""
    estado_inicial.chaves = ""
    estado_inicial.estado_de_visualizacao = "Visitado"

    anteriores = {estado_inicial: None}
    lista_estados_analisados = [estado_inicial]

    while lista_estados_analisados:

        elemento_analisado = lista_estados_analisados.pop(0)

        camadas = verificar_chaves(
            elemento_analisado, camadas
        )
        elemento_analisado = adicionar_estado_a_camada(camadas,elemento_analisado)
        if elemento_analisado is None:
            continue
        # Verifica se chegou ao destino
        if elemento_analisado.no_pos.tipo == "G":
            estado_final = elemento_analisado
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

            # Verifica se o nó está bloqueado
            esta_bloqueado = verificar_bloqueio(
                novo_elemento,
                elemento_analisado.chaves
            )

            if esta_bloqueado:
                continue

            # Propaga as chaves em toda movimentação
            novas_chaves = elemento_analisado.chaves
            novo_elemento = No_estados(
                "-", "-",
                novo_elemento.no_pos.tipo,
                "Não Visitado",
                novo_elemento.no_pos
            )
            #evita que o elemento "novo_elemento", que é compartulhado com a lista de estados, seja também alterado de forma global.
            novo_elemento.chaves = novas_chaves

            anteriores[novo_elemento] = elemento_analisado

            lista_estados_analisados.append(novo_elemento)

            novo_elemento.estado_de_visualizacao = "Visitado"

    # Reconstrução do caminho
    caminho = []

    if estado_final not in anteriores:
        return None

    atual = estado_final

    while atual is not None:
        caminho.append(atual.no_pos)
        atual = anteriores.get(atual)

    caminho.reverse()

    return caminho


def verificar_chaves(elemento_analisado, camadas):

    if elemento_analisado.no_pos.tipo in ("a", "b", "c", "d"):

        chave = elemento_analisado.no_pos.tipo

        # Evita adquirir a mesma chave novamente
        if chave not in elemento_analisado.chaves:

            elemento_analisado.chaves = "".join(
                sorted(elemento_analisado.chaves + chave)
            )

            # Verifica se já existe uma camada com essas chaves
            for camada in camadas:
                if camada.chaves == elemento_analisado.chaves:
                    return camadas

            # Cria uma nova camada
            nova_camada = Camada()
            nova_camada.chaves = elemento_analisado.chaves
            camadas.append(nova_camada)

            return camadas

    return camadas


def verificar_bloqueio(novo_elemento, chaves):

    if novo_elemento.bloqueado == 1:

        tipo_porta = novo_elemento.no_pos.tipo.lower()

        if tipo_porta not in chaves:
            return True

    return False        
# #precisa no BFS?
# def verificar_bonus()
def adicionar_estado_a_camada(camadas,elemento_analisado):

        estado_existente = False
        for camada in camadas:
            for estado in camada.lista_nos_estados:
                if (estado.no_pos == elemento_analisado.no_pos
                        and estado.chaves == elemento_analisado.chaves):
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