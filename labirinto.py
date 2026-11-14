DicionarioCustos = {".":1,"S":1,"G":1,",":3,"~":5,"a":1,"b":1,"c":1,"d":1,"A":1,"B":1,"C":1,
                        "D":1,">":1,"<":1,"^":1,"v":1,"+":-4,"*":-2}
class No:
    #0 ->N, 1 -> L, S -> 2, O -> 3
    dicionario_direcoes = {"N":0, "L": 1, "S":2, "O":3}

    
    def __init__(self, posicao_linha,posicao_coluna,tipo):
        self.posicao_linha = posicao_linha
        self.posicao_coluna = posicao_coluna
        self.tipo = tipo
        self.lista_arestas = [0,0,0,0]

    def adicionar_adjacencia(self,direcao,aresta):
        if self.lista_arestas[self.dicionario_direcoes[direcao]] == 0:
            self.lista_arestas[self.dicionario_direcoes[direcao]] = aresta


class Aresta:
    def __init__(self,origem,destino,custo):
        self.origem = origem
        self.destino = destino
        self.custo = custo



class No_estados:
    bloqueado = 0
    def __init__(self,chaves,bonus,estado_de_visualizacao,no):
        self.no = no
        self.chaves = chaves
        self.bonus = bonus
        self.estado_de_visualizacao = estado_de_visualizacao
        
    
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
    caracteres_permitidos = set("#.S,~abcdABDCD><^v+*\\n")
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
    estado_incial = 0
    estado_final = 0

    lista_nos = []
    arquivo = open(caminho_do_labirinto,"r")
    for indice_linha,linha in enumerate(arquivo):
        for indice_caractere,caractere in enumerate(linha):
            if caractere !=  "#":
                no = No(indice_linha,indice_caractere,caractere)
                if caractere == "S":
                    estado_incial = no
                elif caractere == "G":
                    estado_final = no
                lista_nos.append(no)
    arquivo.close()
    ligar_elementos_lista_nos(lista_nos)
    return Labirinto(estado_incial,estado_final,lista_nos)

def ligar_elementos_lista_nos(lista_nos):
    for no_1 in lista_nos:
        custo_1 = DicionarioCustos[no_1.tipo]
        for no_2 in lista_nos:
            custo_2 = DicionarioCustos[no_2.tipo]
            #Implementar esteiras. 
            if (no_1.posicao_linha+1 == no_2.posicao_linha):
                
                no_1.adicionar_adjacencia("L",Aresta(no_1,no_2,custo_2))
                no_2.adicionar_adjacencia("O",Aresta(no_2,no_1,custo_1))

            if (no_1.posicao_linha-1 == no_2.posicao_linha):

                no_1.adicionar_adjacencia("O",Aresta(no_2,no_1,custo_2))
                no_2.adicionar_adjacencia("L",Aresta(no_2,no_1,custo_1))

            if (no_1.posicao_coluna +1 == no_2.posicao_coluna):

                no_1.adicionar_adjacencia("N",Aresta(no_1,no_2,custo_2))
                no_2.adicionar_adjacencia("S",Aresta(no_2,no_1,custo_1))

            if (no_1.posicao_linha -1== no_2.posicao_linha):

                no_1.adicionar_adjacencia("S",Aresta(no_1,no_2,custo_2))  
                no_2.adicionar_adjacencia("N",Aresta(no_2,no_1,custo_1))  

def buscar_no_estado_a_partir_posicao(lista_nos_estados,no_posicao_alvo):
    for i in lista_nos_estados:
        if lista_nos_estados[i].no == no_posicao_alvo:
            return lista_nos_estados[i]

def bfs_grafo_estados(Labirinto):
    lista_nos_estados = []
    estado_inicial = 0
    estado_final = 0
    for i in Labirinto.lista_nos:
        no = No_estados("-","-",i.tipo,"Não Visitado",i)
        if no.tipo == "S":
            estado_inicial = no
            estado_inicial.estado_de_visualizacao = "Visitado"
        elif no.tipo == "G":
            estado_final = no
        elif no.tipo =="A" or no.tipo =="B" or no.tipo =="C" or no.tipo =="D":
            no.bloqueado = 1 
        
    lista_nos_estados.append(estado_inicial)
    while lista_nos_estados[0] != estado_final:
        lista_nos_estados[0].estado_de_visualizacao = "Encerrado"
        elemento_analisado = lista_nos_estados.pop(0)
        for i in range(4):
            if elemento_analisado.lista_arestas[i] != 0:
                novo_elemento = buscar_no_estado_a_partir_posicao(lista_nos_estados,elemento_analisado.lista_arestas[i].destino)
                if novo_elemento.estado_visualizacao == "Não Visitado" and (novo_elemento.bloqueado == 0 or elemento_analisado.lista_arestas[i].tipo == elemento_analisado.lista_arestas[i].chaves.upper()):
                #chaves é uma lista. como eu consigo fazer uma comparação para porta?
                    lista_nos_estados.append(novo_elemento)
                    novo_elemento.estado = "Visitado"      
                if novo_elemento.bloqueado == 1:
                    break #fazer a lógica para o algoritmo não continuar quando bater em uma porta e não tiver chave.         
