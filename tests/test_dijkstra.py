# [IA] Antigravity (Gemini) – testes unitários do algoritmo de Dijkstra (pesos não negativos e recusa de peso negativo)

import math

import networkx as nx
import pytest

from conftest import construir_grafo_dirigido, custo_caminho, reconstruir_caminho
from graphs.algorithms import dijkstra


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
    nos, lista_nos, grafo_nx = construir_grafo_dirigido(vertices, arestas)

    distancias, anteriores = dijkstra(lista_nos, nos["S"])

    esperado = nx.single_source_dijkstra_path_length(grafo_nx, "S", weight="weight")
    assert distancias[nos["S"]] == 0
    assert distancias[nos["B"]] == 1
    assert distancias[nos["A"]] == 2
    assert distancias[nos["C"]] == 2
    assert distancias[nos["D"]] == 3
    assert distancias[nos["T"]] == 4

    for nome, dist_esperada in esperado.items():
        assert distancias[nos[nome]] == dist_esperada

    caminho = reconstruir_caminho(anteriores, nos["S"], nos["T"])
    assert caminho == [nos["S"], nos["B"], nos["C"], nos["D"], nos["T"]]
    assert custo_caminho(caminho) == 4


def test_dijkstra_aceita_aresta_com_peso_zero():
    vertices = [("S", "S"), "A", "B"]
    arestas = [
        ("S", "A", 0),
        ("A", "B", 2),
        ("S", "B", 5),
    ]
    nos, lista_nos, grafo_nx = construir_grafo_dirigido(vertices, arestas)

    distancias, _ = dijkstra(lista_nos, nos["S"])

    esperado = nx.single_source_dijkstra_path_length(grafo_nx, "S", weight="weight")
    assert distancias[nos["A"]] == esperado["A"] == 0
    assert distancias[nos["B"]] == esperado["B"] == 2


def test_dijkstra_respeita_direcao_e_nos_inalcancaveis():
    vertices = [("S", "S"), "A", "B", "C"]
    arestas = [
        ("S", "A", 2),
        ("B", "A", 1),
    ]
    nos, lista_nos, _ = construir_grafo_dirigido(vertices, arestas)

    distancias, anteriores = dijkstra(lista_nos, nos["S"])

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
    nos, lista_nos, grafo_nx = construir_grafo_dirigido(vertices, arestas)

    distancias, anteriores = dijkstra(lista_nos, nos["S"])

    esperado = nx.dijkstra_path_length(grafo_nx, "S", "G", weight="weight")
    assert distancias[nos["G"]] == esperado == 3
    caminho = reconstruir_caminho(anteriores, nos["S"], nos["G"])
    assert caminho == [nos["S"], nos["B"], nos["G"]]


def test_dijkstra_recusa_peso_negativo_sem_ciclo():
    vertices = [("S", "S"), "A", "B"]
    arestas = [
        ("S", "A", 2),
        ("A", "B", -4),
        ("S", "B", 1),
    ]
    nos, lista_nos, _ = construir_grafo_dirigido(vertices, arestas)

    with pytest.raises(ValueError) as exc:
        dijkstra(lista_nos, nos["S"])

    assert str(exc.value).strip()


def test_dijkstra_recusa_peso_negativo_em_ciclo():
    vertices = [("S", "S"), "A", "B"]
    arestas = [
        ("S", "A", 1),
        ("A", "B", -2),
        ("B", "A", 1),
    ]
    nos, lista_nos, _ = construir_grafo_dirigido(vertices, arestas)

    with pytest.raises(ValueError) as exc:
        dijkstra(lista_nos, nos["S"])

    assert str(exc.value).strip()
