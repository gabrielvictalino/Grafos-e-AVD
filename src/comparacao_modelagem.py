# [IA] Claude Code – gera a tabela comparacao_modelagem.csv (BFS em G_pos com portas como chão, G_pos com portas como parede e G_est); só chama as funções do grupo
"""Seção 6 do enunciado: por que o grafo de posições não basta.

Uso (a saída é gerada por quem rodar o comando):
    python -m src.comparacao_modelagem --out out/parte1

Colunas: mapa, abordagem, passos, caminho_valido, observacao.
`caminho_valido` é conferido por simulação: percorre o caminho encontrado casa a casa,
guarda as chaves coletadas e exige a chave minúscula ao entrar numa porta.
A coluna `observacao` só relata fatos medidos nessa simulação; a explicação é do grupo.
"""

import argparse
import csv
import math
from pathlib import Path

from src.graphs.algorithms import bfs, bfs_grafo_estados_exploracao, converter_grafo_estados
from src.graphs.labirinto import gerar_labirinto, preparar_estados

MAPAS_PADRAO = ("m02_uma_chave", "m03_tres_chaves", "m04_esteiras")
PASTA_PADRAO = Path("data/mapas")
ABORDAGENS = (
    "G_pos com portas como chão",
    "G_pos com portas como parede",
    "G_est (modelagem correta)",
)


def _caminho_de_nos(anteriores: dict, origem, destino) -> list:
    caminho, atual, vistos = [], destino, set()
    while atual is not None and id(atual) not in vistos:
        vistos.add(id(atual))
        caminho.append(atual)
        if atual is origem:
            return caminho[::-1]
        atual = anteriores.get(atual)
    return []


def _validar_caminho(posicoes_e_casas: list[tuple[int, int, str]]) -> tuple[bool, str]:
    """Simula o caminho: pega chaves e confere cada porta."""
    chaves: set[str] = set()
    for linha, coluna, casa in posicoes_e_casas:
        if casa in "abcd":
            chaves.add(casa)
        elif casa in "ABCD" and casa.lower() not in chaves:
            return False, f"entra na porta {casa} em ({linha},{coluna}) sem a chave {casa.lower()}"
    return True, "todas as portas cruzadas com a chave correspondente"


def _linha(mapa: str, abordagem: str, passos, valido, observacao: str) -> dict:
    return {"mapa": mapa, "abordagem": abordagem, "passos": passos,
            "caminho_valido": valido, "observacao": observacao}


def _bfs_posicoes(caminho_arquivo: Path, portas_como_parede: bool) -> tuple[int | None, bool, str]:
    labirinto = gerar_labirinto(str(caminho_arquivo))
    nos = labirinto.lista_nos
    if portas_como_parede:
        for no in nos:
            for i, aresta in enumerate(no.lista_arestas):
                if aresta != 0 and aresta.destino.tipo in "ABCD":
                    no.lista_arestas[i] = 0
        nos = [n for n in nos if n.tipo not in "ABCD"]
    origem, destino = labirinto.estado_incial, labirinto.estado_final
    niveis, anteriores = bfs(nos, origem)
    if not math.isfinite(niveis[destino]):
        return None, False, "sem caminho"
    caminho = _caminho_de_nos(anteriores, origem, destino)
    valido, obs = _validar_caminho([(n.posicao_linha, n.posicao_coluna, n.tipo) for n in caminho])
    return int(niveis[destino]), valido, obs


def _bfs_estados(caminho_arquivo: Path) -> tuple[int | None, bool, str]:
    labirinto = gerar_labirinto(str(caminho_arquivo))
    modelos, inicio, fim = preparar_estados(labirinto)
    arestas, camadas = bfs_grafo_estados_exploracao(modelos, inicio, fim)
    lista, no_ini, alvo, nos_por_estado = converter_grafo_estados(arestas, camadas, inicio, fim, incluir_alvo=True)
    niveis, anteriores = bfs(lista, no_ini)
    if not math.isfinite(niveis[alvo]):
        return None, False, "ALVO inalcançável no grafo de estados"
    caminho = [n for n in _caminho_de_nos(anteriores, no_ini, alvo) if n is not alvo]
    estado_por_no = {no: est for est, no in nos_por_estado.items()}
    valido, obs = _validar_caminho([
        (estado_por_no[n].no_pos.posicao_linha, estado_por_no[n].no_pos.posicao_coluna, estado_por_no[n].no_pos.tipo)
        for n in caminho
    ])
    return int(niveis[alvo]) - 1, valido, obs   # o último arco (G -> ALVO) é virtual


def comparar_modelagens(pasta_mapas: Path = PASTA_PADRAO, mapas=MAPAS_PADRAO) -> list[dict]:
    linhas = []
    for mapa in mapas:
        arquivo = Path(pasta_mapas) / f"{mapa}.txt"
        id_mapa = mapa.split("_")[0]
        for abordagem, funcao in zip(ABORDAGENS, (
            lambda a: _bfs_posicoes(a, portas_como_parede=False),
            lambda a: _bfs_posicoes(a, portas_como_parede=True),
            _bfs_estados,
        )):
            passos, valido, obs = funcao(arquivo)
            linhas.append(_linha(id_mapa, abordagem, "—" if passos is None else passos, valido, obs))
    return linhas


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera comparacao_modelagem.csv (Seção 6).")
    parser.add_argument("--out", required=True, help="Diretório de saída")
    parser.add_argument("--mapas", default=str(PASTA_PADRAO), help="Pasta dos mapas (padrão: data/mapas)")
    args = parser.parse_args()

    linhas = comparar_modelagens(Path(args.mapas))
    saida = Path(args.out)
    saida.mkdir(parents=True, exist_ok=True)
    caminho = saida / "comparacao_modelagem.csv"
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=["mapa", "abordagem", "passos", "caminho_valido", "observacao"])
        escritor.writeheader()
        escritor.writerows(linhas)
    print(f"[OK] {len(linhas)} linhas salvas em {caminho}")


if __name__ == "__main__":
    main()
