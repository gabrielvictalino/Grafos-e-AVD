# [IA] Antigravity (Gemini) – configuração do pytest e helpers para construção de grafos de teste

import sys
from pathlib import Path

import networkx as nx

RAIZ = Path(__file__).resolve().parents[1]
SRC_DIR = RAIZ / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from graphs.labirinto import Aresta, No  # noqa: E402

DIRECOES_PADRAO = ("N", "L", "S", "O")


def construir_grafo_dirigido(vertices, arestas):
    """Constrói um grafo dirigido com objetos No/Aresta e um DiGraph espelho do networkx.

    Parâmetros:
        vertices: sequência de nomes (str) ou tuplas (nome, tipo).
        arestas: sequência de tuplas (origem, destino, peso) ou
                 (origem, destino, peso, direcao).
    Retorna:
        (nos_por_nome, lista_nos, grafo_nx)
    """
    nos_por_nome = {}
    lista_nos = []

    for indice, item in enumerate(vertices):
        if isinstance(item, tuple):
            nome, tipo = item
        else:
            nome, tipo = item, "."

        if nome in nos_por_nome:
            raise ValueError(f"Vértice duplicado: {nome}")

        no = No(indice, 0, tipo)
        nos_por_nome[nome] = no
        lista_nos.append(no)

    grafo_nx = nx.DiGraph()
    for nome in nos_por_nome:
        grafo_nx.add_node(nome)

    direcoes_usadas = {nome: set() for nome in nos_por_nome}

    for item in arestas:
        if len(item) == 3:
            origem_nome, destino_nome, peso = item
            direcao = None
        elif len(item) == 4:
            origem_nome, destino_nome, peso, direcao = item
        else:
            raise ValueError(f"Aresta inválida: {item}")

        if origem_nome not in nos_por_nome or destino_nome not in nos_por_nome:
            raise ValueError(f"Vértice inexistente na aresta: {item}")

        if direcao is None:
            disponiveis = [d for d in DIRECOES_PADRAO if d not in direcoes_usadas[origem_nome]]
            if not disponiveis:
                raise ValueError(f"Vértice {origem_nome} excedeu o limite de 4 arestas de saída.")
            direcao = disponiveis[0]
        elif direcao not in DIRECOES_PADRAO:
            raise ValueError(f"Direção inválida '{direcao}' na aresta {item}.")
        elif direcao in direcoes_usadas[origem_nome]:
            raise ValueError(f"Direção '{direcao}' já utilizada para o vértice {origem_nome}.")

        direcoes_usadas[origem_nome].add(direcao)

        no_origem = nos_por_nome[origem_nome]
        no_destino = nos_por_nome[destino_nome]

        aresta = Aresta(no_origem, no_destino, peso)
        no_origem.adicionar_adjacencia(direcao, aresta)
        no_origem.grau_saida += 1
        no_destino.grau_entrada += 1

        grafo_nx.add_edge(origem_nome, destino_nome, weight=peso)

    return nos_por_nome, lista_nos, grafo_nx


def reconstruir_caminho(anteriores, origem, destino):
    """Reconstrói o caminho de `origem` até `destino` usando o dicionário `anteriores`."""
    if destino not in anteriores:
        return None
    if destino is not origem and anteriores.get(destino) is None:
        return None

    caminho = []
    atual = destino
    visitados = set()

    while atual is not None:
        if id(atual) in visitados:
            raise AssertionError("Ciclo detectado no dicionário `anteriores`.")
        visitados.add(id(atual))
        caminho.append(atual)
        if atual is origem:
            break
        atual = anteriores.get(atual)

    if not caminho or caminho[-1] is not origem:
        return None

    caminho.reverse()
    return caminho


def custo_caminho(caminho):
    """Soma os pesos das arestas consecutivas ao longo de `caminho`."""
    if not caminho or len(caminho) == 1:
        return 0

    total = 0
    for u, v in zip(caminho, caminho[1:]):
        pesos = [
            aresta.custo
            for aresta in u.lista_arestas
            if aresta != 0 and aresta.destino is v
        ]
        if not pesos:
            raise AssertionError("Transição inválida no caminho: aresta inexistente entre nós.")
        total += min(pesos)
    return total
