# [IA] Antigravity (Gemini) – testes unitários do algoritmo BFS (níveis em grafo dirigido e bfs_grafo_nos)

import math
import sys
from pathlib import Path

import networkx as nx

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.graphs import algorithms  # noqa: E402
from src.graphs.algorithms import bfs_grafo_nos  # noqa: E402
from src.graphs.labirinto import Aresta, No, No_estados  # noqa: E402

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


def _obter_bfs():
    bfs = getattr(algorithms, "bfs", None)
    assert bfs is not None, (
        "Função bfs(lista_nos, origem) ainda não implementada em src/graphs/algorithms.py"
    )
    return bfs


def test_bfs_niveis_grafo_pequeno_dirigido():
    bfs = _obter_bfs()
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
    nos, lista_nos, grafo_nx = _construir_grafo_dirigido(vertices, arestas)

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
    caminho = _reconstruir_caminho(anteriores, nos["A"], nos["F"])
    assert caminho is not None
    assert len(caminho) == 4  # 3 passos -> 4 nós


def test_bfs_ignora_pesos_e_minimiza_passos():
    bfs = _obter_bfs()
    vertices = ["A", "B", "C"]
    arestas = [
        ("A", "C", 10),
        ("A", "B", 1),
        ("B", "C", 1),
    ]
    nos, lista_nos, _ = _construir_grafo_dirigido(vertices, arestas)

    niveis, anteriores = bfs(lista_nos, nos["A"])

    assert niveis[nos["C"]] == 1
    assert anteriores[nos["C"]] is nos["A"]


def test_bfs_respeita_direcao_e_nos_inalcancaveis():
    bfs = _obter_bfs()
    vertices = ["A", "B", "C", "D"]
    arestas = [
        ("A", "B", 1),
        ("C", "B", 1),
    ]
    nos, lista_nos, _ = _construir_grafo_dirigido(vertices, arestas)

    niveis, anteriores = bfs(lista_nos, nos["A"])

    assert niveis[nos["A"]] == 0
    assert niveis[nos["B"]] == 1
    assert math.isinf(niveis[nos["C"]])
    assert math.isinf(niveis[nos["D"]])
    assert anteriores[nos["C"]] is None
    assert anteriores[nos["D"]] is None


def test_bfs_com_ciclo_nao_entra_em_loop():
    bfs = _obter_bfs()
    vertices = ["A", "B", "C", "D"]
    arestas = [
        ("A", "B", 1),
        ("B", "C", 1),
        ("C", "A", 1),
        ("B", "D", 1),
    ]
    nos, lista_nos, grafo_nx = _construir_grafo_dirigido(vertices, arestas)

    niveis, _ = bfs(lista_nos, nos["A"])

    esperado = nx.single_source_shortest_path_length(grafo_nx, "A")
    assert {nome: niveis[nos[nome]] for nome in vertices} == esperado
    assert niveis[nos["A"]] == 0
    assert niveis[nos["B"]] == 1
    assert niveis[nos["C"]] == 2
    assert niveis[nos["D"]] == 2


def test_bfs_grafo_nos_encontra_menor_caminho_em_passos():
    vertices = ["A", "B", "C", "D"]
    arestas = [
        ("A", "B", 1),
        ("B", "C", 1),
        ("C", "D", 1),
        ("A", "D", 10),
    ]
    nos, _, grafo_nx = _construir_grafo_dirigido(vertices, arestas)

    estados_por_nome = {
        nome: No_estados("-", frozenset(), "Não Visitado", no)
        for nome, no in nos.items()
    }
    lista_nos_estados = [estados_por_nome[nome] for nome in vertices]

    caminho = bfs_grafo_nos(
        lista_nos_estados,
        estados_por_nome["A"],
        estados_por_nome["D"],
    )

    esperado_passos = nx.shortest_path_length(grafo_nx, "A", "D")
    assert caminho == [nos["A"], nos["D"]]
    assert len(caminho) - 1 == esperado_passos == 1


def test_bfs_grafo_nos_retorna_none_quando_inalcancavel():
    vertices = ["A", "B", "C", "D"]
    arestas = [
        ("A", "B", 1),
        ("C", "D", 1),
    ]
    nos, _, _ = _construir_grafo_dirigido(vertices, arestas)

    estados_por_nome = {
        nome: No_estados("-", frozenset(), "Não Visitado", no)
        for nome, no in nos.items()
    }
    lista_nos_estados = [estados_por_nome[nome] for nome in vertices]

    caminho = bfs_grafo_nos(
        lista_nos_estados,
        estados_por_nome["A"],
        estados_por_nome["D"],
    )

    assert caminho is None
