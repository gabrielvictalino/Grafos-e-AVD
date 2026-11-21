# [IA] Antigravity (Gemini) – testes unitários do algoritmo BFS (níveis em grafo dirigido)

import math

import networkx as nx

from conftest import construir_grafo_dirigido, reconstruir_caminho
from graphs.algorithms import bfs


def test_bfs_niveis_grafo_pequeno_dirigido():
    vertices = ["A", "B", "C", "D", "E", "F"]
    arestas = [
        ("A", "B", 1),
        ("A", "C", 1),
        ("B", "D", 1),
        ("C", "D", 1),
        ("C", "E", 1),
        ("D", "F", 1),
        ("E", "F", 1),
        ("F", "B", 1),
    ]
    nos, lista_nos, grafo_nx = construir_grafo_dirigido(vertices, arestas)

    niveis, anteriores = bfs(lista_nos, nos["A"])

    esperado = nx.single_source_shortest_path_length(grafo_nx, "A")
    assert set(esperado.keys()) == set(vertices)
    assert niveis[nos["A"]] == 0
    assert niveis[nos["B"]] == 1
    assert niveis[nos["C"]] == 1
    assert niveis[nos["D"]] == 2
    assert niveis[nos["E"]] == 2
    assert niveis[nos["F"]] == 3

    for nome, nivel_esperado in esperado.items():
        assert niveis[nos[nome]] == nivel_esperado

    assert anteriores[nos["A"]] is None
    caminho = reconstruir_caminho(anteriores, nos["A"], nos["F"])
    assert caminho is not None
    assert len(caminho) == 4  # 3 passos -> 4 nós


def test_bfs_ignora_pesos_e_minimiza_passos():
    vertices = ["A", "B", "C"]
    arestas = [
        ("A", "C", 10),
        ("A", "B", 1),
        ("B", "C", 1),
    ]
    nos, lista_nos, _ = construir_grafo_dirigido(vertices, arestas)

    niveis, anteriores = bfs(lista_nos, nos["A"])

    assert niveis[nos["C"]] == 1
    assert anteriores[nos["C"]] is nos["A"]


def test_bfs_respeita_direcao_e_nos_inalcancaveis():
    vertices = ["A", "B", "C", "D"]
    arestas = [
        ("A", "B", 1),
        ("C", "B", 1),
    ]
    nos, lista_nos, _ = construir_grafo_dirigido(vertices, arestas)

    niveis, anteriores = bfs(lista_nos, nos["A"])

    assert niveis[nos["A"]] == 0
    assert niveis[nos["B"]] == 1
    assert math.isinf(niveis[nos["C"]])
    assert math.isinf(niveis[nos["D"]])
    assert anteriores[nos["C"]] is None
    assert anteriores[nos["D"]] is None


def test_bfs_com_ciclo_nao_entra_em_loop():
    vertices = ["A", "B", "C", "D"]
    arestas = [
        ("A", "B", 1),
        ("B", "C", 1),
        ("C", "A", 1),
        ("B", "D", 1),
    ]
    nos, lista_nos, grafo_nx = construir_grafo_dirigido(vertices, arestas)

    niveis, _ = bfs(lista_nos, nos["A"])

    esperado = nx.single_source_shortest_path_length(grafo_nx, "A")
    assert {nome: niveis[nos[nome]] for nome in vertices} == esperado
    assert niveis[nos["A"]] == 0
    assert niveis[nos["B"]] == 1
    assert niveis[nos["C"]] == 2
    assert niveis[nos["D"]] == 2
