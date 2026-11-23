# [IA] Antigravity (Gemini) – testes unitários do algoritmo de Dijkstra (pesos não negativos e recusa de peso negativo)

import math
import sys
from pathlib import Path

import networkx as nx

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.graphs.algorithms import dijkstra  # noqa: E402
from src.graphs.labirinto import Aresta, No  # noqa: E402

_DIRECOES_PADRAO = ("N", "L", "S", "O")


def _construir_grafo_dirigido(vertices, arestas):
    nos_por_nome = {}
    lista_nos = []

    for indice, item in enumerate(vertices):
        nome, tipo = item if isinstance(item, tuple) else (item, ".")
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

        if direcao is None:
            disponiveis = [d for d in _DIRECOES_PADRAO if d not in direcoes_usadas[origem_nome]]
            if not disponiveis:
                raise ValueError(f"Vértice {origem_nome} excedeu o limite de 4 arestas de saída.")
            direcao = disponiveis[0]
        elif direcao not in _DIRECOES_PADRAO or direcao in direcoes_usadas[origem_nome]:
            raise ValueError(f"Direção inválida ou duplicada '{direcao}' na aresta {item}.")

        direcoes_usadas[origem_nome].add(direcao)
        no_origem = nos_por_nome[origem_nome]
        no_destino = nos_por_nome[destino_nome]

        no_origem.adicionar_adjacencia(direcao, Aresta(no_origem, no_destino, peso))
        no_origem.grau_saida += 1
        no_destino.grau_entrada += 1
        grafo_nx.add_edge(origem_nome, destino_nome, weight=peso)

    return nos_por_nome, lista_nos, grafo_nx


def _reconstruir_caminho(anteriores, origem, destino):
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


def _custo_caminho(caminho):
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


def _assert_dijkstra_recusa_peso_negativo(lista_nos, origem):
    try:
        resultado = dijkstra(lista_nos, origem)
    except ValueError as exc:
        assert str(exc).strip()
        return

    assert isinstance(resultado, tuple) and len(resultado) == 3
    distancias, anteriores, recusado = resultado
    assert distancias is None
    assert anteriores is None
    assert recusado is True


def test_dijkstra_menor_custo_diverge_de_menor_passos():
    vertices = [("S", "S"), "A", "B", "C", "D", "T"]
    arestas = [
        ("S", "A", 5),
        ("A", "T", 5),
        ("S", "B", 1),
        ("B", "C", 1),
        ("C", "D", 1),
        ("D", "T", 1),
        ("B", "A", 1),
        ("C", "T", 3),
    ]
    nos, lista_nos, grafo_nx = _construir_grafo_dirigido(vertices, arestas)

    distancias, anteriores, recusado = dijkstra(lista_nos, nos["S"])

    assert recusado is False
    esperado = nx.single_source_dijkstra_path_length(grafo_nx, "S", weight="weight")
    assert distancias[nos["S"]] == 0
    assert distancias[nos["B"]] == 1
    assert distancias[nos["A"]] == 2
    assert distancias[nos["C"]] == 2
    assert distancias[nos["D"]] == 3
    assert distancias[nos["T"]] == 4

    for nome, dist_esperada in esperado.items():
        assert distancias[nos[nome]] == dist_esperada

    caminho = _reconstruir_caminho(anteriores, nos["S"], nos["T"])
    assert caminho == [nos["S"], nos["B"], nos["C"], nos["D"], nos["T"]]
    assert _custo_caminho(caminho) == 4


def test_dijkstra_aceita_aresta_com_peso_zero():
    vertices = [("S", "S"), "A", "B"]
    arestas = [
        ("S", "A", 0),
        ("A", "B", 2),
        ("S", "B", 5),
    ]
    nos, lista_nos, grafo_nx = _construir_grafo_dirigido(vertices, arestas)

    distancias, _, recusado = dijkstra(lista_nos, nos["S"])

    assert recusado is False
    esperado = nx.single_source_dijkstra_path_length(grafo_nx, "S", weight="weight")
    assert distancias[nos["A"]] == esperado["A"] == 0
    assert distancias[nos["B"]] == esperado["B"] == 2


def test_dijkstra_respeita_direcao_e_nos_inalcancaveis():
    vertices = [("S", "S"), "A", "B", "C"]
    arestas = [
        ("S", "A", 2),
        ("B", "A", 1),
    ]
    nos, lista_nos, _ = _construir_grafo_dirigido(vertices, arestas)

    distancias, anteriores, recusado = dijkstra(lista_nos, nos["S"])

    assert recusado is False
    assert distancias[nos["S"]] == 0
    assert distancias[nos["A"]] == 2
    assert math.isinf(distancias[nos["B"]])
    assert math.isinf(distancias[nos["C"]])
    assert anteriores[nos["B"]] is None
    assert anteriores[nos["C"]] is None


def test_dijkstra_alcanca_destino_G_com_custo_otimo():
    vertices = [("S", "S"), "A", "B", ("G", "G")]
    arestas = [
        ("S", "A", 5),
        ("A", "G", 5),
        ("S", "B", 1),
        ("B", "G", 2),
    ]
    nos, lista_nos, grafo_nx = _construir_grafo_dirigido(vertices, arestas)

    distancias, anteriores, recusado = dijkstra(lista_nos, nos["S"])

    assert recusado is False
    esperado = nx.dijkstra_path_length(grafo_nx, "S", "G", weight="weight")
    assert distancias[nos["G"]] == esperado == 3
    caminho = _reconstruir_caminho(anteriores, nos["S"], nos["G"])
    assert caminho == [nos["S"], nos["B"], nos["G"]]


def test_dijkstra_recusa_peso_negativo_sem_ciclo():
    vertices = [("S", "S"), "A", "B"]
    arestas = [
        ("S", "A", 2),
        ("A", "B", -4),
        ("S", "B", 1),
    ]
    nos, lista_nos, _ = _construir_grafo_dirigido(vertices, arestas)

    _assert_dijkstra_recusa_peso_negativo(lista_nos, nos["S"])


def test_dijkstra_recusa_peso_negativo_em_ciclo():
    vertices = [("S", "S"), "A", "B"]
    arestas = [
        ("S", "A", 1),
        ("A", "B", -2),
        ("B", "A", 1),
    ]
    nos, lista_nos, _ = _construir_grafo_dirigido(vertices, arestas)

    _assert_dijkstra_recusa_peso_negativo(lista_nos, nos["S"])
