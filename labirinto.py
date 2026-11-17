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
    def __init__(self,chaves,bonus,estado_de_visualizacao,no_pos):
        self.no_pos = no_pos
        self.chaves = chaves
        self.bonus = bonus
        self.estado_de_visualizacao = estado_de_visualizacao
        
    


class Labirinto:
    def __init__(self,estado_incial, estado_final,lista_nos):
        self.estado_incial = estado_incial
        self.estado_final = estado_final
        self.lista_nos = lista_nos

def validar_labirinto(caminho_do_labirinto):
    caracteres_permitidos = set("#.S,G~abcdABCD><^v+*\n")

    with open(caminho_do_labirinto, "r") as arquivo:
        texto = arquivo.read()

    string_total = set(texto)

    existe_diferenca = string_total - caracteres_permitidos

    numeroS = texto.count("S")
    numeroG = texto.count("G")

    lista_quantidade_linhas = []

    for indice, linha in enumerate(texto.splitlines()):
        lista_quantidade_linhas.append(len(linha))

    resultado_tamanho_igual = (
        len(lista_quantidade_linhas) > 0 and
        all(elemento == lista_quantidade_linhas[0]
            for elemento in lista_quantidade_linhas)
    )

    if not resultado_tamanho_igual:
        print("Número de linhas e colunas diferentes")

    if numeroS != 1 or numeroG != 1:
        print("Número de entradas ou saídas inválidos")

    if existe_diferenca:
        print("Não validado, possui caracteres inválidos")
        return False

    if not resultado_tamanho_igual:
        return False

    if numeroS != 1 or numeroG != 1:
        return False

    print("Validado")
    return True 

def gerar_labirinto(caminho_do_labirinto):
    estado_incial = 0
    estado_final = 0

    lista_nos = []
    arquivo = open(caminho_do_labirinto,"r")
    for indice_linha,linha in enumerate(arquivo):
        for indice_caractere,caractere in enumerate(linha):
            if caractere !=  "#" and caractere != "\n":
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

                no_1.adicionar_adjacencia("S",Aresta(no_1,no_2,custo_2))
                no_2.adicionar_adjacencia("N",Aresta(no_2,no_1,custo_1))

            if (no_1.posicao_linha -1== no_2.posicao_linha):

                no_1.adicionar_adjacencia("N",Aresta(no_1,no_2,custo_2))  
                no_2.adicionar_adjacencia("S",Aresta(no_2,no_1,custo_1))  

def buscar_no_estado_a_partir_posicao(lista_nos_estados,no_posicao_alvo):
    for i in lista_nos_estados:
        if i == no_posicao_alvo:
            return i

def bfs_grafo_estados(Labirinto):
    chaves = []
    camada = 0
    lista_nos_estados = []
    estado_inicial = 0
    estado_final = 0
    for i in Labirinto.lista_nos:
        no = No_estados("-","-","Não Visitado",i)
        if no.no_pos.tipo == "S":
            estado_inicial = no
            estado_inicial.estado_de_visualizacao = "Visitado"
        elif no.no_pos.tipo == "G":
            estado_final = no
        elif no.no_pos.tipo =="A" or no.no_pos.tipo =="B" or no.no_pos.tipo =="C" or no.no_pos.tipo =="D":
            no.bloqueado = 1

        lista_nos_estados.append(no)
    anteriores = {estado_inicial: None}
    lista_estados_analisados = [estado_inicial]
    while lista_estados_analisados  and lista_estados_analisados[0] != estado_final:
        lista_estados_analisados[0].estado_de_visualizacao = "Encerrado"
        elemento_analisado = lista_estados_analisados.pop(0)
        for i in range(4):
            if elemento_analisado.no_pos.lista_arestas[i] != 0:
                novo_elemento = buscar_no_estado_a_partir_posicao(lista_nos_estados,elemento_analisado.no_pos.lista_arestas[i].destino)
                if novo_elemento is None:
                    continue
                if novo_elemento.no_pos.tipo == "a" or novo_elemento.no_pos.tipo == "b" or novo_elemento.no_pos.tipo == "c" or novo_elemento.no_pos.tipo == "d":
                    chaves.append(novo_elemento.no.tipo)
                    camada += 1
                if novo_elemento.estado_de_visualizacao == "Não Visitado" and (novo_elemento.bloqueado == 0 or elemento_analisado.lista_arestas[i].tipo.lower() in chaves):
                #chaves é uma lista. como eu consigo fazer uma comparação para porta?
                    anteriores[novo_elemento] = elemento_analisado
                    lista_estados_analisados.append(novo_elemento)
                    novo_elemento.estado_de_visualizacao = "Visitado"      
                if novo_elemento.bloqueado == 1:
                    continue #fazer a lógica para o algoritmo não continuar quando bater em uma porta e não tiver chave.         
    caminho = []
    atual = estado_final
    while atual is not None:
        caminho.append(atual.no_pos)  # ou atual, dependendo do que interpretar_resultado espera
        atual = anteriores.get(atual)

    caminho.reverse()
    return caminho