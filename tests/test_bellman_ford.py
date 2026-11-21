# [IA] Antigravity (Gemini) – testes unitários do algoritmo Bellman-Ford (pesos negativos sem ciclo e detecção/retorno de ciclo negativo)

import math

import networkx as nx

from conftest import construir_grafo_dirigido, custo_caminho, reconstruir_caminho
from graphs.algorithms import bellman_ford


def _validar_ciclo_negativo(ciclo):
    """Valida que `ciclo` representa um ciclo dirigido existente com soma de pesos < 0."""
    assert isinstance(ciclo, (list, tuple))
    assert len(ciclo) >= 1

    if len(ciclo) >= 2 and ciclo[0] is ciclo[-1]:
        sequencia_fechada = list(ciclo)
        nos_unicos = set(ciclo[:-1])
    else:
        sequencia_fechada = list(ciclo) + [ciclo[0]]
        nos_unicos = set(ciclo)

    assert len(nos_unicos) >= 1

    custo_total = 0
    for u, v in zip(sequencia_fechada, sequencia_fechada[1:]):
        pesos = [
            aresta.custo
            for aresta in u.lista_arestas
            if aresta != 0 and aresta.destino is v
        ]
        assert pesos, "O ciclo retornado contém transição inexistente no grafo."
        custo_total += min(pesos)

    assert custo_total < 0
    return nos_unicos, custo_total


def test_bellman_ford_pesos_negativos_sem_ciclo_negativo():
    vertices = [("S", "S"), "A", "B", "C", "D"]
    arestas = [
        ("S", "A", 4),
        ("S", "B", 5),
        ("B", "A", -3),
        ("A", "C", 3),
        ("C", "D", -4),
        ("B", "D", 6),
    ]
    nos, lista_nos, grafo_nx = construir_grafo_dirigido(vertices, arestas)

    distancias, anteriores, tem_ciclo_negativo, ciclo_negativo = bellman_ford(
        lista_nos, nos["S"]
    )

    assert tem_ciclo_negativo is False
    assert not ciclo_negativo

    esperado = nx.single_source_bellman_ford_path_length(grafo_nx, "S", weight="weight")
    assert distancias[nos["S"]] == 0
    assert distancias[nos["B"]] == 5
    assert distancias[nos["A"]] == 2
    assert distancias[nos["C"]] == 5
    assert distancias[nos["D"]] == 1

    for nome, dist_esperada in esperado.items():
        assert distancias[nos[nome]] == dist_esperada

    caminho = reconstruir_caminho(anteriores, nos["S"], nos["D"])
    assert caminho == [nos["S"], nos["B"], nos["A"], nos["C"], nos["D"]]
    assert custo_caminho(caminho) == 1


def test_bellman_ford_pesos_nao_negativos_e_no_inalcancavel():
    vertices = [("S", "S"), "A", "B", "Z"]
    arestas = [
        ("S", "A", 2),
        ("A", "B", 3),
        ("S", "B", 10),
    ]
    nos, lista_nos, grafo_nx = construir_grafo_dirigido(vertices, arestas)

    distancias, anteriores, tem_ciclo_negativo, ciclo_negativo = bellman_ford(
        lista_nos, nos["S"]
    )

    assert tem_ciclo_negativo is False
    assert not ciclo_negativo

    esperado = nx.single_source_bellman_ford_path_length(grafo_nx, "S", weight="weight")
    assert distancias[nos["B"]] == esperado["B"] == 5
    assert math.isinf(distancias[nos["Z"]])
    assert anteriores[nos["Z"]] is None


def test_bellman_ford_detecta_e_retorna_ciclo_negativo_dois_nos():
    vertices = [("S", "S"), "A", "B", ("G", "G")]
    arestas = [
        ("S", "A", 1),
        ("A", "B", -2),
        ("B", "A", 1),
        ("B", "G", 1),
    ]
    nos, lista_nos, grafo_nx = construir_grafo_dirigido(vertices, arestas)

    assert nx.negative_edge_cycle(grafo_nx, weight="weight") is True

    _, _, tem_ciclo_negativo, ciclo_negativo = bellman_ford(lista_nos, nos["S"])

    assert tem_ciclo_negativo is True
    nos_ciclo, custo = _validar_ciclo_negativo(ciclo_negativo)
    assert nos_ciclo == {nos["A"], nos["B"]}
    assert custo == -1


def test_bellman_ford_detecta_e_retorna_ciclo_negativo_tres_nos():
    vertices = [("S", "S"), "A", "B", "C", "T"]
    arestas = [
        ("S", "A", 2),
        ("A", "B", 1),
        ("B", "C", -5),
        ("C", "A", 1),
        ("C", "T", 2),
    ]
    nos, lista_nos, grafo_nx = construir_grafo_dirigido(vertices, arestas)

    assert nx.negative_edge_cycle(grafo_nx, weight="weight") is True

    _, _, tem_ciclo_negativo, ciclo_negativo = bellman_ford(lista_nos, nos["S"])

    assert tem_ciclo_negativo is True
    nos_ciclo, custo = _validar_ciclo_negativo(ciclo_negativo)
    assert nos_ciclo == {nos["A"], nos["B"], nos["C"]}
    assert custo == -3


def test_bellman_ford_ciclo_negativo_inalcancavel_nao_dispara():
    vertices = [("S", "S"), "A", "X", "Y"]
    arestas = [
        ("S", "A", 2),
        ("X", "Y", -3),
        ("Y", "X", 1),
    ]
    nos, lista_nos, _ = construir_grafo_dirigido(vertices, arestas)

    distancias, _, tem_ciclo_negativo, ciclo_negativo = bellman_ford(
        lista_nos, nos["S"]
    )

    assert tem_ciclo_negativo is False
    assert not ciclo_negativo
    assert distancias[nos["A"]] == 2
    assert math.isinf(distancias[nos["X"]])
    assert math.isinf(distancias[nos["Y"]])
