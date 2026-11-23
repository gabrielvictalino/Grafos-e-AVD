# [IA] Antigravity (Gemini) – testes unitários do algoritmo DFS (detecção de ciclo e classificação de arcos em grafo dirigido)

import math
import sys
from pathlib import Path

import networkx as nx
import pytest

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.graphs.algorithms import dfs  # noqa: E402
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
    nos, lista_nos, grafo_nx = _construir_grafo_dirigido(vertices, arestas)

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
    nos, lista_nos, grafo_nx = _construir_grafo_dirigido(vertices, arestas)

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
    nos, lista_nos, _ = _construir_grafo_dirigido(vertices, arestas)

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
    nos, lista_nos, _ = _construir_grafo_dirigido(vertices, arestas)

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
    _, lista_nos, _ = _construir_grafo_dirigido(["A", "B"], [("A", "B", 1)])
    no_externo = No(99, 99, ".")

    with pytest.raises(ValueError):
        dfs(lista_nos, no_externo)
