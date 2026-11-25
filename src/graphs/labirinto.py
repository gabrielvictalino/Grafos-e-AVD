DicionarioCustos = {".":1,"S":1,"G":1,",":3,"~":5,"a":1,"b":1,"c":1,"d":1,"A":1,"B":1,"C":1,
                        "D":1,">":1,"<":1,"^":1,"v":1,"+":-4,"*":-2}
class No:
    #0 ->N, 1 -> L, S -> 2, O -> 3
    dicionario_direcoes = {"N":0, "L": 1, "S":2, "O":3}

    
    def __init__(self, posicao_linha,posicao_coluna,tipo):
        self.posicao_linha = posicao_linha
        self.posicao_coluna = posicao_coluna
        self.lista_estados_gerados = []
        self.tipo = tipo
        self.lista_arestas = [0,0,0,0]
        self.grau_entrada = 0
        self.grau_saida = 0

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
    def gerar_rotulo(self):
        return "("+self.no_pos.posicao_linha+","+self.no_pos.posicao_coluna+") | "+self.chaves+ "| "+self.bonus
        
    


class Labirinto:
    def __init__(self,estado_incial, estado_final,lista_nos,metricas):
        self.estado_incial = estado_incial
        self.estado_final = estado_final
        self.lista_nos = lista_nos
        self.metricas = metricas
        self.maior_grau_entrada = 0
        self.maior_grau_saida = 0
        self.dicionario_graus_entrada = {}
        self.dicionario_graus_saida = {}
        self.becos = {}
    # exclui nó virtual ALVO das métricas de grau e filtra becos fora de G
    def calcular_graus_estado(self, arestas_geradas, camadas):

        estados_gerados = {
            estado
            for camada in camadas
            for estado in camada.lista_nos_estados
        }

        graus_entrada = {estado: 0 for estado in estados_gerados}
        graus_saida = {estado: 0 for estado in estados_gerados}

        for origem, destino, movimento, casa, peso in arestas_geradas:
            if destino == "ALVO":
                continue
            graus_saida[origem] += 1
            graus_entrada[destino] += 1
        self.dicionario_graus_entrada = graus_entrada
        self.dicionario_graus_saida = graus_saida
        
        becos = {
            chave: valor
            for chave, valor in graus_saida.items()
            if valor == 0 and chave.no_pos.tipo != "G"
        }
        self.becos = becos 
        self.maior_grau_entrada = max(graus_entrada.values(), default = 0)
        self.maior_grau_saida = max(graus_saida.values(), default = 0)
    
    def calcular_heatmap(self):

        numero_linhas = max(no.posicao_linha for no in self.lista_nos) + 1
        numero_colunas = max(no.posicao_coluna for no in self.lista_nos) + 1

        heatmap = [
            [None for _ in range(numero_colunas)]
            for _ in range(numero_linhas)
        ]

        for no in self.lista_nos:
            linha = no.posicao_linha
            coluna = no.posicao_coluna

            heatmap[linha][coluna] = len(no.lista_estados_gerados)

        return heatmap
            
        

class Metricas:
    
    def __init__(self):
        self.densidade = 0
        self.ordem = 0
        self.tamanho = 0
        self.num_estados = 0
        self.teto_teorico = 0
        self.num_chaves = 0
        self.num_bonus = 0
    
    
    def setOrdem(self,ordem):
        self.ordem = ordem
    def setTamanho(self,tamanho):
        self.tamanho = tamanho
    def definirDensidade(self):
        #corrige limiar de densidade
        if self.ordem >= 2:
            self.densidade = self.tamanho/(self.ordem*(self.ordem-1))
        else:
            self.densidade = 0
    def definir_teto(self,num_chaves,num_bonus):
        # corrige fórmula do teto teórico
        self.num_chaves = num_chaves
        self.num_bonus = num_bonus
        self.teto_teorico = self.ordem * (2 ** num_chaves) * (2 ** num_bonus)
    def definir_num_estados(self,camadas):
        # conta estados diretamente de lista_nos_estados sem descontar ALVO
        contador_estados = 0
        for camada in camadas:
            contador_estados += len(camada.lista_nos_estados)
        self.num_estados = contador_estados
    
                    
        
    

def rotulo_camada(chaves, bonus):
    """Rótulo da camada: chaves ("-" se nenhuma); com bônus consumidos, acrescenta "|{ids}"."""
    rotulo = chaves or "-"
    if bonus:
        rotulo += "|{" + ",".join(str(b) for b in sorted(bonus)) + "}"
    return rotulo


# [IA] Claude – camada passa a ser (chaves, bônus consumidos): campo bonus, rotulo e rotulo_camada
class Camada:
    def __init__(self, chaves="", bonus=frozenset()):
        # Uma camada é identificada pelo par (chaves, bônus consumidos)
        self.chaves = chaves
        self.bonus = frozenset(bonus)
        self.lista_nos_estados = []
        self.metricas = Metricas()
        self.arestas_transicao = []

    @property
    def rotulo(self):
        return rotulo_camada(self.chaves, self.bonus)

    def calcular_metricas_camada(self, arestas_geradas):
        ordem = len(self.lista_nos_estados)
        self.metricas.setOrdem(ordem)

        estados_camada = set(self.lista_nos_estados)

        tamanho = 0
        self.arestas_transicao = []

        for origem, destino, movimento, casa, peso in arestas_geradas:
            # ignora arcos virtuais até ALVO e corrige chamada a definirDensidade
            if destino == "ALVO":
                continue

            if origem in estados_camada and destino not in estados_camada:
                self.arestas_transicao.append(
                    Aresta(origem, destino, peso)
                )

            if origem in estados_camada and destino in estados_camada:
                tamanho += 1

        self.metricas.setTamanho(tamanho)
        self.metricas.definirDensidade()
        
        
        
#Ver se as paredes são # ou não
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
    linhas = texto.splitlines()

    resultado_paredes = (
        len(linhas) > 0
        and all(linhas)
        and all(caractere == "#" for caractere in linhas[0])
        and all(caractere == "#" for caractere in linhas[-1])
        and all(linha[0] == "#" and linha[-1] == "#" for linha in linhas)
    )

    
    if not resultado_paredes:
        print("O labirinto não está envolto de paredes")
    if not resultado_tamanho_igual:
        print("Número de linhas e colunas diferentes")

    if numeroS != 1 or numeroG != 1:
        print("Número de entradas ou saídas inválidos")

    if existe_diferenca:
        print("Não validado, possui caracteres inválidos")
        return False

    if not resultado_tamanho_igual:
        return False

    if numeroS != 1 or numeroG < 1:
        return False

    print("Validado")
    return True 

def gerar_labirinto(caminho_do_labirinto):
    estado_inicial = 0
    estado_final = 0
    ordem = 0
    lista_nos = []
    #contabiliza chaves distintas do teto teórico
    chaves_unicas = set()
    num_bonus = 0
    arquivo = open(caminho_do_labirinto,"r")
    # [IA] Claude – depuração: pula comentários (;) para a linha 0 ser a primeira linha do mapa
    linhas_do_mapa = [l for l in arquivo if l.strip() and not l.startswith(";")]
    for indice_linha,linha in enumerate(linhas_do_mapa):
        for indice_caractere,caractere in enumerate(linha):
            if caractere !=  "#" and caractere != "\n":
                if caractere in ["a","b","c","d"]:
                    chaves_unicas.add(caractere)
                if caractere == "+":
                    num_bonus += 1
                ordem += 1
                no = No(indice_linha,indice_caractere,caractere)
                if caractere == "S":
                    estado_inicial = no
                elif caractere == "G":
                    estado_final = no
                lista_nos.append(no)
    arquivo.close()
    num_chaves = len(chaves_unicas)
    metricas = Metricas()
    metricas.setOrdem(ordem)
    tamanho = ligar_elementos_lista_nos(lista_nos)
    metricas.setTamanho(tamanho)
    metricas.definirDensidade()
    metricas.definir_teto(num_chaves,num_bonus)
    
    return Labirinto(estado_inicial,estado_final,lista_nos,metricas)

def preparar_estados(labirinto):
    """Prepara a entrada da BFS a partir do Labirinto retornado por gerar_labirinto."""
    modelos = []
    inicio = None
    fim = None

    for no in labirinto.lista_nos:
        modelo = No_estados("-", "-", "Não Visitado", no)
        if no.tipo == "S":
            inicio = modelo
        elif no.tipo == "G":
            fim = modelo
        elif no.tipo in ("A", "B", "C", "D"):
            modelo.bloqueado = 1
        modelos.append(modelo)

    if inicio is None or fim is None:
        raise ValueError("O labirinto precisa ter uma célula S e uma célula G.")
    return modelos, inicio, fim




def ligar_elementos_lista_nos(lista_nos):
    num_arestas = 0
    for no_1 in lista_nos:
        custo_1 = DicionarioCustos[no_1.tipo]
        for no_2 in lista_nos:
            custo_2 = DicionarioCustos[no_2.tipo]
            if (no_1.posicao_linha == no_2.posicao_linha and no_1.posicao_coluna + 1 == no_2.posicao_coluna):
                
                if no_1.tipo != "<" and no_1.tipo != "v" and no_1.tipo != "^":
                    no_1.adicionar_adjacencia("L",Aresta(no_1,no_2,custo_2))
                    num_arestas += 1
                    no_1.grau_saida += 1
                    no_2.grau_entrada += 1
                if no_2.tipo != ">" and no_2.tipo != "v" and no_2.tipo != "^":    
                    no_2.adicionar_adjacencia("O",Aresta(no_2,no_1,custo_1))
                    num_arestas += 1
                    no_2.grau_saida += 1
                    no_1.grau_entrada += 1

            
            if (no_1.posicao_coluna == no_2.posicao_coluna and no_1.posicao_linha +1 == no_2.posicao_linha):
                if no_1.tipo != ">" and no_1.tipo != "^" and no_1.tipo != "<":
                    no_1.adicionar_adjacencia("S",Aresta(no_1,no_2,custo_2))
                    num_arestas += 1
                    no_1.grau_saida += 1
                    no_2.grau_entrada += 1
                if no_2.tipo != ">" and no_2.tipo != "v" and no_2.tipo != "<":
                    no_2.adicionar_adjacencia("N",Aresta(no_2,no_1,custo_1))
                    num_arestas += 1
                    no_2.grau_saida += 1
                    no_1.grau_entrada += 1

    return num_arestas

def buscar_no_estado_a_partir_posicao(lista_nos_estados,no_posicao_alvo):
    for i in lista_nos_estados:
        if i.no_pos == no_posicao_alvo:
            return i
        
def gerar_grafo_estados(labirinto):
    lista_nos_estados = []

    estado_inicial = None
    estado_final = None

    for no in labirinto.lista_nos:
        novo_no = No_estados("-", "-", "Não Visitado", no)

        if no.tipo == "S":
            estado_inicial = novo_no

        elif no.tipo == "G":
            estado_final = novo_no

        elif no.tipo in ("A", "B", "C", "D"):
            novo_no.bloqueado = 1

        lista_nos_estados.append(novo_no)

    return lista_nos_estados, estado_inicial, estado_final


