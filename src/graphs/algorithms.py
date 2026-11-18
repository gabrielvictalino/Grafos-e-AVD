from graphs.labirinto import buscar_no_estado_a_partir_posicao

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
        visitados[u] = True
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

            novo_elemento.estado_de_visualizacao = "Visitado"
            anteriores[novo_elemento] = elemento_analisado

            lista_estados_analisados.append(novo_elemento)

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


    
    

def bfs_grafo_estados(lista_nos_estados, estado_inicial, estado_final):

    camadas = 0
    chaves = set()

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

            # Verifica se encontrou uma chave
            if novo_elemento.no_pos.tipo in ("a", "b", "c", "d"):
                camada += 1
                chaves.add(novo_elemento.no_pos.tipo)

            # Verifica se o nó já foi visitado
            if novo_elemento.estado_de_visualizacao != "Não Visitado":
                continue

            # Verifica se o nó está bloqueado
            if novo_elemento.bloqueado == 1:

                tipo_porta = aresta.tipo.lower()

                if tipo_porta not in chaves:
                    continue

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
