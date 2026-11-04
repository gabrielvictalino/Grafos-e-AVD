class No:
    #0 ->N, 1 -> L, S -> 2, O -> 3
    dicionario_direcoes = {"N":0, "L": 1, "S":2, "0":3}
    lista_arestas = []

    def __init__(self, nome):
        self.nome = nome

    def adicionar_adjacencia(self,direcao,aresta,no):
        no.lista_arestas[self.dicionario_direcoes[direcao]] = aresta

class Aresta:
    def __init__(self,origem,destino,custo):
        self.origem = origem
        self.destino = destino
        self.custo = custo


class Labirinto:
    def __init__(self,estado_incial, estado_final):
        self.estado_incial = estado_incial
        self.estado_final = estado_final
        
