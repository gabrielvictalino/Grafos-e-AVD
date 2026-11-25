# [IA] Antigravity (Gemini) – testes unitários de validação de mapas e leitura de dataset (IO)

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.graphs.io import carregar_grafo_tmdb  # noqa: E402
from src.graphs.labirinto import validar_labirinto  # noqa: E402


def _criar_mapa(tmp_path, nome, conteudo):
    caminho = tmp_path / nome
    caminho.write_text(conteudo.lstrip("\n"), encoding="utf-8")
    return caminho


def _assert_mapa_invalido(caminho, capsys):
    try:
        resultado = validar_labirinto(str(caminho))
    except ValueError as exc:
        assert str(exc).strip()
        return

    capturado = capsys.readouterr()
    mensagem = (capturado.out + capturado.err).strip()
    assert resultado is False
    assert mensagem


def test_mapa_valido_aceito(tmp_path):
    caminho = _criar_mapa(
        tmp_path,
        "valido.txt",
        """
#####
#S.G#
#####
""",
    )

    assert validar_labirinto(str(caminho)) is True


def test_todos_mapas_fornecidos_sao_validos():
    pasta_mapas = RAIZ / "data" / "mapas"
    arquivos = sorted(pasta_mapas.glob("m0[1-8]_*.txt"))
    assert len(arquivos) == 8

    for caminho in arquivos:
        assert validar_labirinto(str(caminho)) is True


def test_mapa_nao_retangular_gera_erro_claro(tmp_path, capsys):
    caminho = _criar_mapa(
        tmp_path,
        "nao_retangular.txt",
        """
#####
#S.G
#####
""",
    )

    _assert_mapa_invalido(caminho, capsys)


def test_mapa_com_dois_S_gera_erro_claro(tmp_path, capsys):
    caminho = _criar_mapa(
        tmp_path,
        "dois_s.txt",
        """
######
#SS.G#
######
""",
    )

    _assert_mapa_invalido(caminho, capsys)


def test_mapa_sem_G_gera_erro_claro(tmp_path, capsys):
    caminho = _criar_mapa(
        tmp_path,
        "sem_g.txt",
        """
#####
#S..#
#####
""",
    )

    _assert_mapa_invalido(caminho, capsys)


def test_mapa_com_simbolo_desconhecido_gera_erro_claro(tmp_path, capsys):
    caminho = _criar_mapa(
        tmp_path,
        "simbolo_invalido.txt",
        """
#####
#SXG#
#####
""",
    )

    _assert_mapa_invalido(caminho, capsys)


def test_mapa_com_comentario_ponto_e_virgula_aceito(tmp_path):
    caminho = _criar_mapa(
        tmp_path,
        "com_comentario.txt",
        """
; mapa de teste com comentario
#####
#S.G#
#####
""",
    )

    assert validar_labirinto(str(caminho)) is True


def test_mapa_com_multiplas_saidas_G_aceito(tmp_path):
    caminho = _criar_mapa(
        tmp_path,
        "multiplos_g.txt",
        """
######
#S.GG#
######
""",
    )

    assert validar_labirinto(str(caminho)) is True


def test_carregar_grafo_tmdb_direcao_e_pesos_originais(tmp_path):
    csv_path = tmp_path / "tmdb_limpo.csv"
    csv_path.write_text(
        "\n".join([
            'id,title,release_date,imdb_rating,cast',
            '1,Filme A,2020-01-01,8.0,"Ator 1, Ator 2"',
            '2,Filme B,2021-01-01,6.5,"Ator 1, Ator 3"',
            '3,Filme C,2022-01-01,9.0,"Ator 3"',
        ]) + "\n",
        encoding="utf-8",
    )

    lista_nos, mapa_nos = carregar_grafo_tmdb(csv_path, transformacao_peso="original")

    assert len(lista_nos) == 3
    arestas_1 = [(a.destino.id, a.custo) for a in mapa_nos["1"].lista_arestas]
    arestas_2 = [(a.destino.id, a.custo) for a in mapa_nos["2"].lista_arestas]
    arestas_3 = [(a.destino.id, a.custo) for a in mapa_nos["3"].lista_arestas]

    assert arestas_1 == [("2", -1.5)]
    assert arestas_2 == [("3", 2.5)]
    assert arestas_3 == []


def test_carregar_grafo_tmdb_transformacao_nao_negativo(tmp_path):
    csv_path = tmp_path / "tmdb_limpo.csv"
    csv_path.write_text(
        "\n".join([
            'id,title,release_date,imdb_rating,cast',
            '1,Filme A,2020-01-01,8.0,"Ator 1, Ator 2"',
            '2,Filme B,2021-01-01,6.5,"Ator 1, Ator 3"',
            '3,Filme C,2022-01-01,9.0,"Ator 3"',
        ]) + "\n",
        encoding="utf-8",
    )

    lista_nos, mapa_nos = carregar_grafo_tmdb(csv_path, transformacao_peso="nao_negativo")

    arestas_1 = [(a.destino.id, a.custo) for a in mapa_nos["1"].lista_arestas]
    arestas_2 = [(a.destino.id, a.custo) for a in mapa_nos["2"].lista_arestas]

    assert arestas_1 == [("2", 8.5)]
    assert arestas_2 == [("3", 12.5)]
    assert all(a.custo >= 0 for no in lista_nos for a in no.lista_arestas)


def test_carregar_grafo_tmdb_diretorio_vazio_gera_erro(tmp_path):
    with pytest.raises(FileNotFoundError):
        carregar_grafo_tmdb(tmp_path)
