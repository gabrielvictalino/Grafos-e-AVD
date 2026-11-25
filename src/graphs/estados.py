"""Exploração e transformação do grafo de estados do labirinto."""

from src.graphs.labirinto import (
    Aresta,
    Camada,
    No,
    No_estados,
    buscar_no_estado_a_partir_posicao,
)
dicionario_direcoes_ao_contrario = {0:"N", 1: "L", 2:"S", 3:"O"}

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
            # [IA] Claude – a camada é identificada por (chaves, bônus), não só por chaves
            for camada in camadas:
                if camada.chaves == novo_estado.chaves and camada.bonus == novo_estado.bonus:
                    return camadas, novo_estado

            # Cria uma nova camada
            nova_camada = Camada(novo_estado.chaves, novo_estado.bonus)
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
                # [IA] Claude – idem: compara também os bônus consumidos
                if camada.chaves == elemento_analisado.chaves and camada.bonus == elemento_analisado.bonus:
                    camada_encontrada = camada
                    break

            if camada_encontrada is None:
                camada_encontrada = Camada(elemento_analisado.chaves, elemento_analisado.bonus)
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
