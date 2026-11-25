# [IA] Antigravity (Gemini) – testes unitários da construção do grafo de estados (mapa mínimo, chaves/camadas, esteira-beco, bônus consumível e conversão)

import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.graphs.algorithms import (  # noqa: E402
    bellman_ford,
    bfs_estados_armadilha,
    bfs_grafo_estados_exploracao,
    converter_grafo_estados,
    dijkstra,
    formatar_estado,
)
from src.graphs.labirinto import gerar_labirinto, preparar_estados, validar_labirinto  # noqa: E402
from src.solve import reconstruir_caminho_nos  # noqa: E402


def _criar_mapa(tmp_path, nome, conteudo):
    caminho = tmp_path / nome
    caminho.write_text(conteudo.strip() + "\n", encoding="utf-8")
    return str(caminho)


def test_mapa_minimo_estados_e_arcos_conferidos_a_mao(tmp_path):
    caminho = _criar_mapa(
        tmp_path,
        "mapa_minimo.txt",
        """
######
#S.AG#
#a####
######
""",
    )

    labirinto = gerar_labirinto(caminho)
    modelos, inicio, fim = preparar_estados(labirinto)
    arestas_geradas, camadas = bfs_grafo_estados_exploracao(modelos, inicio, fim)

    assert len(labirinto.lista_nos) == 5

    rotulos_por_camada = {
        camada.chaves: {formatar_estado(estado) for estado in camada.lista_nos_estados}
        for camada in camadas
    }
    assert rotulos_por_camada == {
        "": {"(1,1)|-|{}", "(1,2)|-|{}"},
        "a": {
            "(2,1)|a|{}",
            "(1,1)|a|{}",
            "(1,2)|a|{}",
            "(1,3)|a|{}",
            "(1,4)|a|{}",
        },
    }

    total_estados = sum(len(camada.lista_nos_estados) for camada in camadas)
    assert total_estados == 7

    arcos_entre_estados = [
        (origem, destino, mov, casa, peso)
        for origem, destino, mov, casa, peso in arestas_geradas
        if destino != "ALVO"
    ]
    arcos_para_alvo = [
        (origem, destino, mov, casa, peso)
        for origem, destino, mov, casa, peso in arestas_geradas
        if destino == "ALVO"
    ]

    assert len(arcos_entre_estados) == 10
    assert len(arcos_para_alvo) == 1
    assert len(arestas_geradas) == 11

    origem_alvo, _, _, _, peso_alvo = arcos_para_alvo[0]
    assert formatar_estado(origem_alvo) == "(1,4)|a|{}"
    assert peso_alvo == 0
    assert all(origem is not origem_alvo for origem, _, _, _, _ in arcos_entre_estados)


def test_coletar_chave_muda_de_camada(tmp_path):
    caminho = _criar_mapa(
        tmp_path,
        "mapa_chave_camada.txt",
        """
######
#S.AG#
#a####
######
""",
    )

    labirinto = gerar_labirinto(caminho)
    modelos, inicio, fim = preparar_estados(labirinto)
    arestas_geradas, camadas = bfs_grafo_estados_exploracao(modelos, inicio, fim)

    transicoes_de_camada = [
        (formatar_estado(origem), formatar_estado(destino), mov, casa, peso)
        for origem, destino, mov, casa, peso in arestas_geradas
        if destino != "ALVO" and origem.chaves != destino.chaves
    ]

    assert transicoes_de_camada == [
        ("(1,1)|-|{}", "(2,1)|a|{}", "S", "a", 1)
    ]

    camada_sem_chave = next(c for c in camadas if c.chaves == "")
    assert all(
        (estado.no_pos.posicao_linha, estado.no_pos.posicao_coluna) != (1, 3)
        for estado in camada_sem_chave.lista_nos_estados
    )


def test_esteira_apontando_para_parede_gera_beco_e_estado_armadilha(tmp_path):
    caminho = _criar_mapa(
        tmp_path,
        "mapa_esteira_beco.txt",
        """
######
#S..G#
###v##
######
""",
    )

    labirinto = gerar_labirinto(caminho)
    modelos, inicio, fim = preparar_estados(labirinto)
    arestas_geradas, camadas = bfs_grafo_estados_exploracao(modelos, inicio, fim)

    labirinto.calcular_graus_estado(arestas_geradas, camadas)
    armadilhas = bfs_estados_armadilha(arestas_geradas, camadas)

    estados = [e for c in camadas for e in c.lista_nos_estados]
    estado_esteira = next(
        e
        for e in estados
        if (e.no_pos.posicao_linha, e.no_pos.posicao_coluna) == (2, 3)
    )

    assert labirinto.dicionario_graus_saida[estado_esteira] == 0
    assert set(labirinto.becos.keys()) == {estado_esteira}
    assert armadilhas == {estado_esteira}


def test_bonus_consumivel_vale_menos_4_primeira_vez_e_1_depois(tmp_path):
    caminho = _criar_mapa(
        tmp_path,
        "mapa_bonus_consumivel.txt",
        """
#####
#S+G#
#####
""",
    )

    labirinto = gerar_labirinto(caminho)
    modelos, inicio, fim = preparar_estados(labirinto)
    arestas_geradas, camadas = bfs_grafo_estados_exploracao(modelos, inicio, fim)

    rotulos = {
        formatar_estado(estado)
        for camada in camadas
        for estado in camada.lista_nos_estados
    }
    assert rotulos == {
        "(1,1)|-|{}",
        "(1,2)|-|{0}",
        "(1,3)|-|{0}",
        "(1,1)|-|{0}",
    }

    pesos = {
        (formatar_estado(origem), formatar_estado(destino)): peso
        for origem, destino, _, _, peso in arestas_geradas
        if destino != "ALVO"
    }

    assert pesos[("(1,1)|-|{}", "(1,2)|-|{0}")] == -4
    assert pesos[("(1,1)|-|{0}", "(1,2)|-|{0}")] == 1


def test_converter_grafo_estados_inclui_alvo(tmp_path):
    caminho = _criar_mapa(
        tmp_path,
        "mapa_conversao.txt",
        """
######
#S.AG#
#a####
######
""",
    )

    labirinto = gerar_labirinto(caminho)
    modelos, inicio, fim = preparar_estados(labirinto)
    arestas_geradas, camadas = bfs_grafo_estados_exploracao(modelos, inicio, fim)

    lista_nos, no_inicio, alvo, nos_por_estado = converter_grafo_estados(
        arestas_geradas, camadas, inicio, fim
    )

    assert len(lista_nos) == 8  # 7 estados alcançáveis + 1 nó virtual ALVO
    assert alvo.tipo == "G"
    assert no_inicio in lista_nos
    assert nos_por_estado["ALVO"] is alvo


# [IA] Antigravity (Gemini) – validação automatizada dos 2 mapas próprios em data/mapas_grupo/
def test_mapa_grupo_chaves_esteiras_bonus_atende_requisitos():
    caminho = RAIZ / "data" / "mapas_grupo" / "g01_chaves_esteiras_bonus.txt"
    assert caminho.is_file()
    assert validar_labirinto(str(caminho)) is True

    labirinto = gerar_labirinto(str(caminho))
    assert labirinto.metricas.num_chaves >= 3
    assert labirinto.metricas.num_bonus >= 1
    assert any(no.tipo in "><^v" for no in labirinto.lista_nos)

    modelos, inicio, fim = preparar_estados(labirinto)
    arestas_geradas, camadas = bfs_grafo_estados_exploracao(modelos, inicio, fim)
    lista_nos, no_ini, alvo, nos_por_estado = converter_grafo_estados(
        arestas_geradas, camadas, inicio, fim, incluir_alvo=True
    )
    estado_por_no = {no: est for est, no in nos_por_estado.items()}

    _, _, recusado = dijkstra(lista_nos, no_ini)
    assert recusado is True

    dist, ant, tem_ciclo, _ = bellman_ford(lista_nos, no_ini)
    assert tem_ciclo is False
    assert math.isfinite(dist[alvo])

    caminho_nos = [n for n in reconstruir_caminho_nos(ant, no_ini, alvo) if n is not alvo]
    estado_final = estado_por_no[caminho_nos[-1]]
    assert len(estado_final.chaves) >= 3
    assert len(estado_final.bonus) >= 1
    assert any(estado_por_no[n].no_pos.tipo in "><^v" for n in caminho_nos)


def test_mapa_grupo_armadilha_atende_minimo_20_por_cento():
    caminho = RAIZ / "data" / "mapas_grupo" / "g02_armadilha.txt"
    assert caminho.is_file()
    assert validar_labirinto(str(caminho)) is True

    labirinto = gerar_labirinto(str(caminho))
    modelos, inicio, fim = preparar_estados(labirinto)
    arestas_geradas, camadas = bfs_grafo_estados_exploracao(modelos, inicio, fim)
    lista_nos, no_ini, alvo, _ = converter_grafo_estados(
        arestas_geradas, camadas, inicio, fim, incluir_alvo=True
    )

    dist, _, recusado = dijkstra(lista_nos, no_ini)
    assert recusado is False
    assert math.isfinite(dist[alvo])

    total_estados = sum(len(c.lista_nos_estados) for c in camadas)
    armadilhas = bfs_estados_armadilha(arestas_geradas, camadas)
    assert total_estados > 0
    assert len(armadilhas) / total_estados >= 0.20

