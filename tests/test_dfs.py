# [IA] Antigravity (Gemini) – testes unitários do algoritmo DFS (detecção de ciclo e classificação de arcos em grafo dirigido)

import math

import networkx as nx
import pytest

from conftest import construir_grafo_dirigido
from graphs.algorithms import dfs
from graphs.labirinto import No


def test_dfs_classificacao_todos_tipos_de_arcos_e_ciclo():
    vertices = ["A", "B", "C", "D"]
    arestas = [
        ("A", "B", 1, "N"),
        ("A", "C", 2, "L"),
        ("A", "D", 4, "S"),
        ("B", "C", 1, "N"),
        ("C", "A", 1, "N"),
        ("D", "C", 1, "N"),
    ]
    nos, lista_nos, grafo_nx = construir_grafo_dirigido(vertices, arestas)

    resultado = dfs(lista_nos, nos["A"], detalhado=True)

    assert resultado["ordem"] == [nos["A"], nos["B"], nos["C"], nos["D"]]
    assert resultado["descoberta"] == {
        nos["A"]: 1,
        nos["B"]: 2,
        nos["C"]: 3,
        nos["D"]: 6,
    }
    assert resultado["termino"] == {
        nos["C"]: 4,
        nos["B"]: 5,
        nos["D"]: 7,
        nos["A"]: 8,
    }
    assert resultado["classificacao"] == [
        (nos["A"], nos["B"], "arvore"),
        (nos["B"], nos["C"], "arvore"),
        (nos["C"], nos["A"], "retorno"),
        (nos["A"], nos["C"], "avanco"),
        (nos["A"], nos["D"], "arvore"),
        (nos["D"], nos["C"], "cruzamento"),
    ]
    assert resultado["contagem"] == {
        "arvore": 3,
        "retorno": 1,
        "avanco": 1,
        "cruzamento": 1,
    }
    assert resultado["tem_ciclo"] is True
    assert resultado["tem_ciclo"] == (not nx.is_directed_acyclic_graph(grafo_nx))


def test_dfs_dag_sem_ciclo():
    vertices = ["A", "B", "C", "D"]
    arestas = [
        ("A", "B", 1, "N"),
        ("A", "C", 1, "L"),
        ("B", "D", 1, "N"),
        ("C", "D", 1, "N"),
    ]
    nos, lista_nos, grafo_nx = construir_grafo_dirigido(vertices, arestas)

    resultado = dfs(lista_nos, nos["A"], detalhado=True)

    assert resultado["tem_ciclo"] is False
    assert nx.is_directed_acyclic_graph(grafo_nx) is True
    assert resultado["contagem"] == {
        "arvore": 3,
        "retorno": 0,
        "avanco": 0,
        "cruzamento": 1,
    }


def test_dfs_autolaco_classificado_como_retorno():
    vertices = ["A"]
    arestas = [("A", "A", 1, "N")]
    nos, lista_nos, _ = construir_grafo_dirigido(vertices, arestas)

    resultado = dfs(lista_nos, nos["A"], detalhado=True)

    assert resultado["tem_ciclo"] is True
    assert resultado["classificacao"] == [(nos["A"], nos["A"], "retorno")]
    assert resultado["contagem"]["retorno"] == 1


def test_dfs_modo_padrao_retorna_distancias_e_anteriores():
    vertices = ["A", "B", "C", "D"]
    arestas = [
        ("A", "B", 2),
        ("B", "C", 3),
    ]
    nos, lista_nos, _ = construir_grafo_dirigido(vertices, arestas)

    retorno = dfs(lista_nos, nos["A"])

    assert isinstance(retorno, tuple) and len(retorno) == 2
    distancias, anteriores = retorno
    assert distancias[nos["A"]] == 0
    assert distancias[nos["B"]] == 2
    assert distancias[nos["C"]] == 5
    assert math.isinf(distancias[nos["D"]])
    assert anteriores[nos["A"]] is None
    assert anteriores[nos["C"]] is nos["B"]
    assert anteriores[nos["D"]] is None


def test_dfs_origem_fora_da_lista_gera_erro():
    _, lista_nos, _ = construir_grafo_dirigido(["A", "B"], [("A", "B", 1)])
    no_externo = No(99, 99, ".")

    with pytest.raises(ValueError):
        dfs(lista_nos, no_externo)
