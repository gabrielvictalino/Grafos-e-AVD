# [IA] Antigravity (Gemini) – testes unitários do algoritmo Bellman-Ford (pesos negativos sem ciclo e detecção/retorno de ciclo negativo)

import math
import sys
from pathlib import Path

import networkx as nx

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.graphs.algorithms import bellman_ford  # noqa: E402
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
    nos, lista_nos, grafo_nx = _construir_grafo_dirigido(vertices, arestas)

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

    caminho = _reconstruir_caminho(anteriores, nos["S"], nos["D"])
    assert caminho == [nos["S"], nos["B"], nos["A"], nos["C"], nos["D"]]
    assert _custo_caminho(caminho) == 1


def test_bellman_ford_pesos_nao_negativos_e_no_inalcancavel():
    vertices = [("S", "S"), "A", "B", "Z"]
    arestas = [
        ("S", "A", 2),
        ("A", "B", 3),
        ("S", "B", 10),
    ]
    nos, lista_nos, grafo_nx = _construir_grafo_dirigido(vertices, arestas)

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
    nos, lista_nos, grafo_nx = _construir_grafo_dirigido(vertices, arestas)

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
    nos, lista_nos, grafo_nx = _construir_grafo_dirigido(vertices, arestas)

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
    nos, lista_nos, _ = _construir_grafo_dirigido(vertices, arestas)

    distancias, _, tem_ciclo_negativo, ciclo_negativo = bellman_ford(
        lista_nos, nos["S"]
    )

    assert tem_ciclo_negativo is False
    assert not ciclo_negativo
    assert distancias[nos["A"]] == 2
    assert math.isinf(distancias[nos["X"]])
    assert math.isinf(distancias[nos["Y"]])



# [IA] Claude Code – 2 testes sugeridos para o Bellman-Ford; os cálculos à mão estão nos comentários
# e o grupo deve conferi-los antes de aceitar os testes.

def test_bellman_ford_sugestao_ciclo_negativo_detectado_e_devolvido():
    # Grafo: S->A (1), A->B (2), B->C (-4), C->A (1).
    # Ciclo A->B->C->A: 2 + (-4) + 1 = -1  (negativo, alcançável a partir de S).
    # S fica fora do ciclo; ele só chega a A pela aresta S->A.
    vertices = [("S", "S"), "A", "B", "C"]
    arestas = [("S", "A", 1), ("A", "B", 2), ("B", "C", -4), ("C", "A", 1)]
    nos, lista_nos, _ = _construir_grafo_dirigido(vertices, arestas)

    _, _, tem_ciclo_negativo, ciclo_negativo = bellman_ford(lista_nos, nos["S"])

    assert tem_ciclo_negativo is True
    nos_ciclo, custo = _validar_ciclo_negativo(ciclo_negativo)
    assert nos_ciclo == {nos["A"], nos["B"], nos["C"]}
    assert nos["S"] not in nos_ciclo
    assert custo == -1


def test_bellman_ford_sugestao_peso_negativo_sem_ciclo():
    # Grafo (sem ciclo): S->A (3), S->B (2), A->B (-2), B->C (-1).
    # dist(S) = 0
    # dist(A) = 3
    # dist(B) = min(S->B = 2, S->A->B = 3 + (-2) = 1) = 1
    # dist(C) = dist(B) + (-1) = 0
    # Melhor caminho até C: S->A->B->C, custo 3 - 2 - 1 = 0.
    vertices = [("S", "S"), "A", "B", "C"]
    arestas = [("S", "A", 3), ("S", "B", 2), ("A", "B", -2), ("B", "C", -1)]
    nos, lista_nos, _ = _construir_grafo_dirigido(vertices, arestas)

    distancias, anteriores, tem_ciclo_negativo, ciclo_negativo = bellman_ford(lista_nos, nos["S"])

    assert tem_ciclo_negativo is False
    assert not ciclo_negativo
    assert distancias[nos["S"]] == 0
    assert distancias[nos["A"]] == 3
    assert distancias[nos["B"]] == 1
    assert distancias[nos["C"]] == 0
    caminho = _reconstruir_caminho(anteriores, nos["S"], nos["C"])
    assert caminho == [nos["S"], nos["A"], nos["B"], nos["C"]]
    assert _custo_caminho(caminho) == 0
