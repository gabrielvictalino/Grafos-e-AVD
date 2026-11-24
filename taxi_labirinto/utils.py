"""Regras do Táxi Labirinto e adaptação das funções originais do projeto.

O grafo original guarda as chaves já coletadas. O refinamento adiciona as
entregas: a bordo = coletados - entregues. Nenhum algoritmo original é alterado.
"""
from __future__ import annotations

import base64
from collections import defaultdict, deque
from dataclasses import dataclass
from itertools import product
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

from src.graphs import algorithms
from src.graphs import labirinto as maze
from src.graphs.estados import bfs_grafo_estados_exploracao, converter_grafo_estados

CAPACIDADE = 3
DIRECOES = ("N", "L", "S", "O")
PASSAGEIROS = {
    "a": {"nome": "Ana", "destino": "Casa da Ana", "cor": "#ff927e", "predio": "casa"},
    "b": {"nome": "Bento", "destino": "Padaria", "cor": "#8ebdff", "predio": "loja"},
    "c": {"nome": "Caio", "destino": "Mercado", "cor": "#94d6a0", "predio": "mercado"},
    "d": {"nome": "Dora", "destino": "Edifício da Dora", "cor": "#c5a1f5", "predio": "predio"},
}
LIMITE_ESTADOS = 12000


@dataclass
class GrafoTaxi:
    linhas: list[str]
    passageiros: str
    labirinto: object
    estados: list
    arestas_geradas: list
    camadas: list
    inicio: object
    fim_modelo: object
    transicoes: dict
    finais: set
    armadilhas: set
    estados_base: int

    @property
    def indice(self):
        return {estado: i for i, estado in enumerate(self.estados)}


def entregues(estado):
    """No jogo, bonus guarda os índices das entregas, não bônus de terreno."""
    return "".join(chr(97 + i) for i in sorted(estado.bonus))


def a_bordo(estado):
    feitos = set(entregues(estado))
    return "".join(p for p in estado.chaves if p not in feitos)


def validar_texto(texto):
    linhas = texto.splitlines()
    if not linhas or len(linhas) < 3 or not linhas[0]:
        raise ValueError("O mapa deve ter pelo menos três linhas e ser cercado por #.")
    if len(linhas) > 30 or len(linhas[0]) > 40:
        raise ValueError("Use mapas de até 30 linhas por 40 colunas.")
    if any(len(l) != len(linhas[0]) for l in linhas):
        raise ValueError("Todas as linhas devem ter o mesmo número de caracteres.")
    if any(c != "#" for c in linhas[0] + linhas[-1]) or any(l[0] != "#" or l[-1] != "#" for l in linhas):
        raise ValueError("O contorno inteiro do mapa deve ser #.")
    conteudo = "".join(linhas)
    if set(conteudo) - set("#.SG,~abcdABCD><^v+*"):
        raise ValueError("Há caracteres inválidos. Use # . S G a–d A–D , ~ > < ^ v.")
    if "+" in conteudo or "*" in conteudo:
        raise ValueError("Este jogo usa Dijkstra: + e * têm custos negativos no projeto e não são aceitos. Use . , ou ~.")
    if conteudo.count("S") != 1 or conteudo.count("G") != 1:
        raise ValueError("O mapa precisa conter exatamente um S e um G.")
    for p in "abcd":
        if conteudo.count(p) != conteudo.count(p.upper()) or conteudo.count(p) > 1:
            raise ValueError(f"Use no máximo um passageiro {p} e exatamente um destino {p.upper()} para ele.")
    return linhas


def gerar_grafo_taxi(texto: str) -> GrafoTaxi:
    """Explora o grafo original e o refina por entregas e capacidade.

    Retém o formato (origem, destino, direção, casa, custo) das arestas e as
    classes No_estados/Camada. A entrada de uma 4ª pessoa é bloqueada quando
    há três a bordo. Destinos entregues permanecem liberados.
    """
    linhas = validar_texto(texto)
    passageiros = "".join(p for p in "abcd" if p in texto)
    with TemporaryDirectory(prefix="taxi_mapa_") as tmp:
        arquivo = Path(tmp) / "mapa.txt"
        arquivo.write_text("\n".join(linhas) + "\n", encoding="utf-8")
        labirinto = maze.gerar_labirinto(str(arquivo))
    modelos, inicio_base, fim = maze.preparar_estados(labirinto)
    arestas_base, camadas_base = bfs_grafo_estados_exploracao(modelos, inicio_base, fim)
    adj = defaultdict(list)
    for origem, destino, direcao, casa, peso in arestas_base:
        if destino != "ALVO":
            adj[origem].append((destino, direcao, casa, peso))

    def criar(base, feitas):
        return maze.No_estados(base.chaves, feitas, "Não Visitado", base.no_pos)

    inicial = criar(inicio_base, frozenset())
    identificados = {(inicio_base, frozenset()): inicial}
    fila = deque([(inicio_base, frozenset())])
    camadas_por_id = {}
    arestas, transicoes, finais = [], {}, set()
    todas = frozenset(ord(p) - 97 for p in passageiros)
    while fila:
        base, feitas = fila.popleft()
        atual = identificados[(base, feitas)]
        camada_id = (atual.chaves, feitas)
        if camada_id not in camadas_por_id:
            camadas_por_id[camada_id] = maze.Camada(atual.chaves, feitas)
        camadas_por_id[camada_id].lista_nos_estados.append(atual)
        transicoes[atual] = {}
        if atual.no_pos.tipo == "G":
            finais.add(atual)
            arestas.append((atual, "ALVO", "-", "-", 0))
            continue
        for vizinho, direcao, casa, peso in adj[base]:
            novas = set(vizinho.chaves) - set(base.chaves)
            if novas and len(a_bordo(atual)) + len(novas) > CAPACIDADE:
                continue
            novas_feitas = feitas
            if casa in "ABCD" and casa.lower() in a_bordo(atual):
                novas_feitas = feitas | {ord(casa.lower()) - 97}
            if casa == "G" and novas_feitas != todas:
                continue
            chave = (vizinho, novas_feitas)
            if chave not in identificados:
                if len(identificados) >= LIMITE_ESTADOS:
                    raise ValueError("Mapa muito grande: limite de 12.000 estados. Reduza as ruas ou o número de passageiros.")
                identificados[chave] = criar(vizinho, novas_feitas)
                fila.append(chave)
            destino = identificados[chave]
            transicoes[atual][direcao] = (destino, peso)
            arestas.append((atual, destino, direcao, casa, peso))
    camadas = list(camadas_por_id.values())
    armadilhas = algorithms.bfs_estados_armadilha(arestas, camadas)
    if inicial in armadilhas:
        raise ValueError("Mapa sem solução: não é possível entregar todos com três lugares e chegar em G.")
    return GrafoTaxi(linhas, passageiros, labirinto, list(identificados.values()),
                     arestas, camadas, inicial, fim, transicoes, finais, armadilhas,
                     sum(len(c.lista_nos_estados) for c in camadas_base))


def associar_fachadas(linhas):
    """Reserve um imóvel por parada e priorize imóveis na quadra vizinha."""
    paradas = {}
    for r, linha in enumerate(linhas):
        for c, simbolo in enumerate(linha):
            if simbolo in "ABCDG":
                paradas[simbolo] = (r, c)

    candidatos = []
    for r, c in paradas.values():
        vizinhos = [(r-1,c), (r+1,c), (r,c-1), (r,c+1)]
        candidatos.append([lote for lote in vizinhos if linhas[lote[0]][lote[1]] == "#"] + [None])

    # Uma parada sem parede exclusiva recebe uma pequena calçada na esquina.
    def exclusivos(opcao):
        usados = [lote for lote in opcao if lote is not None]
        return len(set(usados)) == len(usados)

    lotes_escolhidos = min((opcao for opcao in product(*candidatos) if exclusivos(opcao)),
                           key=lambda opcao: opcao.count(None))
    return {simbolo: {"parada": parada, "lote": lote}
            for (simbolo, parada), lote in zip(paradas.items(), lotes_escolhidos)}


def serializar_grafo(grafo):
    ids = grafo.indice
    return {
        "linhas": grafo.linhas,
        "fachadas": associar_fachadas(grafo.linhas),
        "passageiros": {p: PASSAGEIROS[p] for p in grafo.passageiros},
        "inicio": ids[grafo.inicio],
        "estados": [{
            "pos": [e.no_pos.posicao_linha, e.no_pos.posicao_coluna],
            "coletados": e.chaves, "entregues": entregues(e), "bordo": a_bordo(e),
            "final": e in grafo.finais, "armadilha": e in grafo.armadilhas,
            "saidas": {d: [ids[v], c] for d, (v, c) in grafo.transicoes[e].items()},
        } for e in grafo.estados],
    }


def reproduzir_percurso(grafo, movimentos):
    """Validação autoritativa no Python; não confia no custo enviado pelo JS."""
    if not isinstance(movimentos, list) or len(movimentos) > 100000:
        raise ValueError("Percurso inválido ou longo demais.")
    atual, custo = grafo.inicio, 0
    caminho = [atual]
    for direcao in movimentos:
        if not isinstance(direcao, str) or direcao not in grafo.transicoes[atual]:
            raise ValueError("O percurso contém um movimento que não existe no grafo.")
        atual, peso = grafo.transicoes[atual][direcao]
        custo += peso
        caminho.append(atual)
    return caminho, custo


def comparar_com_dijkstra(grafo, movimentos):
    caminho_jogador, custo_jogador = reproduzir_percurso(grafo, movimentos)
    if caminho_jogador[-1] not in grafo.finais:
        raise ValueError("Entregue todos os passageiros e chegue a G antes da comparação.")
    # Esta é a conversão e o Dijkstra do projeto, sem reimplementação.
    nos, inicio, alvo, por_estado = converter_grafo_estados(
        grafo.arestas_geradas, grafo.camadas, grafo.inicio, grafo.fim_modelo)
    distancias, anteriores, negativo = algorithms.dijkstra(nos, inicio)
    if negativo:
        raise ValueError("Dijkstra não aceita arestas com custo negativo.")
    if not isfinite(distancias[alvo]):
        raise ValueError("O Dijkstra não encontrou uma rota válida.")
    inverso = {no: estado for estado, no in por_estado.items() if estado != "ALVO"}
    caminho_otimo = []
    atual = anteriores[alvo]  # Remove apenas ALVO virtual, que custa zero.
    while atual is not None:
        caminho_otimo.append(inverso[atual])
        atual = anteriores[atual]
    caminho_otimo.reverse()
    ids = grafo.indice
    custo_otimo = distancias[alvo]
    return {
        "custo_jogador": custo_jogador, "custo_otimo": custo_otimo,
        "passos_jogador": len(movimentos), "passos_otimo": len(caminho_otimo) - 1,
        "custo_extra": custo_jogador - custo_otimo,
        "eficiencia": round(100 * custo_otimo / custo_jogador, 1) if custo_jogador else 100,
        "rota_jogador": [ids[e] for e in caminho_jogador],
        "rota_otima": [ids[e] for e in caminho_otimo],
        "movimentos": movimentos,
    }


def carregar_sprites(pasta):
    nomes = ["carro", "casa", "loja", "predio", "mercado", "casa_motorista", "obras", "alagamento"]
    nomes += [f"passageiro_{p}" for p in "abcd"]
    imagens = {}
    for nome in nomes:
        arquivo = Path(pasta) / f"{nome}.png"
        if not arquivo.is_file():
            raise FileNotFoundError(f"Sprite ausente: {arquivo}")
        imagens[nome] = "data:image/png;base64," + base64.b64encode(arquivo.read_bytes()).decode()
    return imagens
