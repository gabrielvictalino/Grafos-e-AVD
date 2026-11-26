# [IA] Claude Code – orquestra as tarefas por algoritmo da Parte 2 (BFS/DFS em 3 fontes, Dijkstra em 5 pares, Bellman-Ford sem ciclo e com ciclo negativo); só chama os algoritmos do grupo, não os reimplementa
"""Tarefas obrigatórias da Parte 2 por algoritmo, gravadas em JSON.

Uso (a saída é gerada por quem rodar o comando):
    python -m src.tarefas_parte2 --dataset data/dataset_parte2/tmdb_limpo.csv.gz --out out/parte2
    # opcional: acrescentar a chave "tarefas" ao parte2_report.json já existente
    python -m src.tarefas_parte2 --dataset ... --out out/parte2 --relatorio out/parte2/parte2_report.json

Critérios de escolha (registrados no próprio JSON, para o grupo conferir ou trocar):
  - fontes: os vértices com maior grau de saída (desempate pelo id);
  - alvo de cada par do Dijkstra: o vértice alcançável mais distante em níveis de BFS;
  - caso com ciclo negativo: PROPOSTA a ser decidida pelo grupo (ver `transformacao_ciclo_negativo`).
O grafo do TMDB é um DAG (datas estritamente crescentes), então não tem ciclo negativo por construção.
"""

import argparse
import json
import math
import time
from pathlib import Path

from src.graphs.algorithms import bellman_ford, bfs, dfs, dijkstra
from src.graphs.graph import No
from src.graphs.io import carregar_grafo_tmdb

N_FONTES_BFS_DFS = 3
N_PARES_DIJKSTRA = 5
LIMITE_FILMES_PADRAO = 10_000   # o Dijkstra do grupo é O(V^2): um recorte mantém o tempo viável
LIMITE_FILMES_CICLO = 300       # recorte pequeno para exibir o ciclo negativo


def _finito(x):
    return round(x, 4) if isinstance(x, (int, float)) and math.isfinite(x) else None


def _rotulo(no) -> str:
    return f"{no.id} - {no.titulo}"


def _caminho(anteriores: dict, origem, destino) -> list[str]:
    caminho, atual, vistos = [], destino, set()
    while atual is not None and atual not in vistos:
        vistos.add(atual)
        caminho.append(_rotulo(atual))
        if atual is origem:
            return caminho[::-1]
        atual = anteriores.get(atual)
    return []


def _arestas(no):
    return [a for a in no.lista_arestas if a != 0]


def escolher_fontes(lista_nos, quantidade: int) -> list:
    """Vértices com maior grau de saída; desempate pelo id (texto)."""
    return sorted(lista_nos, key=lambda n: (-len(_arestas(n)), str(n.id)))[:quantidade]


def tarefa_bfs_dfs(lista_nos, fontes) -> tuple[list[dict], list[dict]]:
    resultados_bfs, resultados_dfs = [], []
    for fonte in fontes:
        t0 = time.perf_counter()
        niveis, _ = bfs(lista_nos, fonte)
        tempo = round((time.perf_counter() - t0) * 1000, 3)
        alcancados = [n for n, d in niveis.items() if math.isfinite(d)]
        camadas: dict[int, int] = {}
        for n in alcancados:
            camadas[int(niveis[n])] = camadas.get(int(niveis[n]), 0) + 1
        resultados_bfs.append({
            "fonte": _rotulo(fonte),
            "alcancados": len(alcancados),
            "camadas": {str(k): camadas[k] for k in sorted(camadas)},
            "tempo_ms": tempo,
        })

        t0 = time.perf_counter()
        res = dfs(lista_nos, fonte, detalhado=True)
        tempo = round((time.perf_counter() - t0) * 1000, 3)
        resultados_dfs.append({
            "fonte": _rotulo(fonte),
            "visitados": len(res["ordem"]),
            "primeiros_visitados": [_rotulo(n) for n in res["ordem"][:10]],
            "tem_ciclo": res["tem_ciclo"],
            "contagem_arcos": res["contagem"],
            "tempo_ms": tempo,
        })
    return resultados_bfs, resultados_dfs


def tarefa_dijkstra(lista_nos_nao_neg, mapa_nao_neg, lista_nos_orig, mapa_orig, fontes) -> list[dict]:
    """Um par (fonte, alvo) por fonte, com pesos deslocados (+10) para serem >= 0."""
    pares = []
    for fonte in fontes:
        niveis, _ = bfs(lista_nos_orig, mapa_orig[str(fonte.id)])
        alcancaveis = [(d, str(n.id)) for n, d in niveis.items() if math.isfinite(d) and d > 0]
        if not alcancaveis:
            continue
        maior = max(d for d, _ in alcancaveis)
        alvo_id = min(i for d, i in alcancaveis if d == maior)
        origem = mapa_nao_neg[str(fonte.id)]
        alvo = mapa_nao_neg[alvo_id]
        t0 = time.perf_counter()
        distancias, anteriores, peso_negativo = dijkstra(lista_nos_nao_neg, origem)
        tempo = round((time.perf_counter() - t0) * 1000, 3)
        pares.append({
            "origem": _rotulo(origem),
            "destino": _rotulo(alvo),
            "nivel_bfs_do_destino": int(maior),
            "recusou_peso_negativo": bool(peso_negativo),
            "custo_deslocado": _finito(distancias[alvo]) if distancias else None,
            "arcos_no_caminho": max(len(_caminho(anteriores, origem, alvo)) - 1, 0) if anteriores else None,
            "caminho": _caminho(anteriores, origem, alvo) if anteriores else [],
            "tempo_ms": tempo,
        })
    return pares


def tarefa_bellman_ford_sem_ciclo(lista_nos, fonte) -> dict:
    t0 = time.perf_counter()
    distancias, anteriores, tem_ciclo, _ = bellman_ford(lista_nos, fonte)
    tempo = round((time.perf_counter() - t0) * 1000, 3)
    alcancados = {n: d for n, d in distancias.items() if math.isfinite(d)}
    pior = min(alcancados, key=lambda n: (alcancados[n], str(n.id)))
    return {
        "fonte": _rotulo(fonte),
        "tem_ciclo_negativo": bool(tem_ciclo),
        "alcancados": len(alcancados),
        "menor_distancia": {"destino": _rotulo(pior), "custo": round(alcancados[pior], 4),
                            "caminho": _caminho(anteriores, fonte, pior)},
        "arcos_negativos_no_grafo": sum(1 for n in lista_nos for a in _arestas(n) if a.custo < 0),
        "tempo_ms": tempo,
    }


def construir_grafo_ciclo_negativo(lista_nos) -> tuple[list[No], dict[str, No]]:
    """PROPOSTA (decisão do grupo): copia o recorte com arcos nos dois sentidos e peso -|Δnota|.

    Cada par de filmes ligados por ator passa a ter os arcos u->v e v->u com peso -|nota(v)-nota(u)|.
    O ciclo u->v->u soma -2|Δnota|, negativo sempre que as notas diferem.
    """
    copia = {str(n.id): No(str(n.id), n.titulo) for n in lista_nos}
    vistos = set()
    for no in lista_nos:
        for aresta in _arestas(no):
            u, v = str(no.id), str(aresta.destino.id)
            peso = -abs(aresta.custo)
            if (u, v) not in vistos:
                vistos.add((u, v))
                copia[u].adicionar_aresta(copia[v], peso)
            if (v, u) not in vistos:
                vistos.add((v, u))
                copia[v].adicionar_aresta(copia[u], peso)
    return list(copia.values()), copia


def tarefa_bellman_ford_ciclo_negativo(dataset, limite_filmes: int) -> dict:
    nos, _ = carregar_grafo_tmdb(dataset, limite_filmes=limite_filmes, transformacao_peso="original")
    com_arestas = [n for n in nos if _arestas(n)]
    if not com_arestas:
        return {"erro": "o recorte não tem arestas; aumente o limite de filmes"}
    lista, mapa = construir_grafo_ciclo_negativo(nos)
    fonte = mapa[str(escolher_fontes(nos, 1)[0].id)]
    t0 = time.perf_counter()
    _, _, tem_ciclo, ciclo = bellman_ford(lista, fonte)
    tempo = round((time.perf_counter() - t0) * 1000, 3)
    sequencia = [_rotulo(n) for n in ciclo] if ciclo else []
    custo = None
    if ciclo:
        fechado = list(ciclo) if ciclo[0] is ciclo[-1] else list(ciclo) + [ciclo[0]]
        custo = round(sum(min(a.custo for a in _arestas(u) if a.destino is v) for u, v in zip(fechado, fechado[1:])), 4)
    return {
        "transformacao_ciclo_negativo": (
            "PROPOSTA a ser decidida pelo grupo: recorte dos primeiros filmes por data, arcos nos dois "
            "sentidos e peso = -|nota(destino) - nota(origem)|."),
        "recorte_filmes": limite_filmes,
        "vertices": len(lista),
        "arcos": sum(len(_arestas(n)) for n in lista),
        "fonte": _rotulo(fonte),
        "tem_ciclo_negativo": bool(tem_ciclo),
        "ciclo": sequencia,
        "custo_do_ciclo": custo,
        "tempo_ms": tempo,
    }


def executar_tarefas_parte2(dataset, limite_filmes: int = LIMITE_FILMES_PADRAO) -> dict:
    nos_orig, mapa_orig = carregar_grafo_tmdb(dataset, limite_filmes=limite_filmes, transformacao_peso="original")
    nos_pos, mapa_pos = carregar_grafo_tmdb(dataset, limite_filmes=limite_filmes, transformacao_peso="nao_negativo")
    fontes = escolher_fontes(nos_orig, max(N_FONTES_BFS_DFS, N_PARES_DIJKSTRA))
    bfs_res, dfs_res = tarefa_bfs_dfs(nos_orig, fontes[:N_FONTES_BFS_DFS])
    return {
        "parametros": {
            "dataset": str(dataset),
            "recorte_filmes": limite_filmes,
            "vertices": len(nos_orig),
            "arestas": sum(len(_arestas(n)) for n in nos_orig),
            "criterio_fontes": "maiores graus de saída, desempate pelo id",
            "criterio_alvo_dijkstra": "alcançável mais distante em níveis de BFS, desempate pelo menor id",
            "transformacao_pesos_dijkstra": "peso + 10,0 (a nota vai de 1 a 10, então a diferença mínima é -9)",
        },
        "bfs": bfs_res,
        "dfs": dfs_res,
        "dijkstra": tarefa_dijkstra(nos_pos, mapa_pos, nos_orig, mapa_orig, fontes[:N_PARES_DIJKSTRA]),
        "bellman_ford_peso_negativo_sem_ciclo": tarefa_bellman_ford_sem_ciclo(nos_orig, mapa_orig[str(fontes[0].id)]),
        "bellman_ford_ciclo_negativo": tarefa_bellman_ford_ciclo_negativo(dataset, min(limite_filmes, LIMITE_FILMES_CICLO)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Tarefas por algoritmo da Parte 2 (JSON).")
    parser.add_argument("--dataset", required=True, help="CSV ou pasta do dataset da Parte 2")
    parser.add_argument("--out", required=True, help="Diretório de saída (grava parte2_tarefas.json)")
    parser.add_argument("--limite-filmes", type=int, default=LIMITE_FILMES_PADRAO,
                        help="Recorte cronológico (os N primeiros filmes por data)")
    parser.add_argument("--relatorio", default=None,
                        help="parte2_report.json existente: acrescenta a chave 'tarefas' sem apagar 'escalabilidade'")
    args = parser.parse_args()

    resultado = executar_tarefas_parte2(args.dataset, args.limite_filmes)
    saida = Path(args.out)
    saida.mkdir(parents=True, exist_ok=True)
    caminho = saida / "parte2_tarefas.json"
    caminho.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Tarefas salvas em {caminho}")
    if args.relatorio:
        rel = Path(args.relatorio)
        dados = json.loads(rel.read_text(encoding="utf-8"))
        dados["tarefas"] = resultado
        rel.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] Chave 'tarefas' acrescentada em {rel}")


if __name__ == "__main__":
    main()
