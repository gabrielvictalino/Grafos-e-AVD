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
        menor=float('inf')
        for no in lista_nos:
            if not visitados[no] and distancias[no] < menor_distancia:
                menor_distancia = distancias[no]
                u = no
        if u is None or menor_distancia == float('inf'):
            break
        visitados[u] = True


def bellmon_ford(listas_nos,origem):
    anteriores={}
    distancias={}
    arestas=[]
    for no in listas_nos:
        distancias[no]= float('inf')
        anteriores[no]= None
    distancias[origem]= 0
    
    for i in range (len(listas_nos)-1):
        for org,dest, peso in arestas:
            if distancias[org]!= float('inf'):
                if distancias[org] + peso< distancias[dest]:
                    distancias[dest]=distancias[org] + peso
                    anteriores[dest]=org
                return distancias, anteriores