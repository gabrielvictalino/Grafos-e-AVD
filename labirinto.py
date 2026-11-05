class No:
    #0 ->N, 1 -> L, S -> 2, O -> 3
    dicionario_direcoes = {"N":0, "L": 1, "S":2, "0":3}
    lista_arestas = []
    
    def __init__(self, posicao_linha,posicao_coluna,tipo):
        self.posicao_linha = posicao_linha
        self.posicao_coluna = posicao_coluna
        self.tipo = tipo

    def adicionar_adjacencia(self,direcao,aresta,no):
        no.lista_arestas[self.dicionario_direcoes[direcao]] = aresta

class Aresta:
    def __init__(self,origem,destino,custo):
        self.origem = origem
        self.destino = destino
        self.custo = custo


class Labirinto:
    def __init__(self,estado_incial, estado_final,lista_nos):
        self.estado_incial = estado_incial
        self.estado_final = estado_final
        self.lista_nos = lista_nos

def validar_labirinto(caminho_do_labirinto):
    caracteres_permitidos = set("#.S,~aA><^v+*")
    arquivo = open(caminho_do_labirinto, "r")
    string_total = set(arquivo.read())
    arquivo.close()
    existe_diferenca = string_total-caracteres_permitidos
    if(existe_diferenca):
        print("Não validado, possui caracteres inválidos")
        return False
    else:
        print("Validado")
        return True

def gerar_labirinto(caminho_do_labirinto):


    lista_nos = []
    arquivo = open(caminho_do_labirinto,"r")
    for indice_linha,linha in enumerate(arquivo):
        for indice_caractere,caractere in enumerate(linha):
            if caractere !=  "#":
                lista_nos.append(No(indice_linha,indice_caractere,caractere))

#Terminar implementação.

# def ligar_elementos_lista_nos(lista_nos):
#     for no_1 in lista_nos:
#         for no_2 in lista_nos
#
    
