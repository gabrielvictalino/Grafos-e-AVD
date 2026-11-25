"""Execução de algoritmos e benchmark do dataset da Parte 2."""

import csv
import html
import json
import math
import re
import time
from pathlib import Path

from src.graphs.algorithms import (
    bellman_ford,
    bellman_ford_sem_ciclo_negativo,
    bfs,
    bfs_estados_armadilha,
    bfs_grafo_estados_exploracao,
    converter_grafo_estados,
    dfs,
    dijkstra,
    exportar_arestas,
    formatar_estado,
)
from src.graphs.labirinto import (
    No_estados,
    gerar_labirinto,
    preparar_estados,
    rotulo_camada,
    validar_labirinto,
)
from src.graphs.io import carregar_grafo_tmdb

def reconstruir_caminho(anteriores: dict, origem, destino) -> list[str]:
    if destino not in anteriores or anteriores[destino] is None and destino != origem:
        return []
    caminho = []
    atual = destino
    visitados = set()
    while atual is not None:
        if atual in visitados:  # proteção contra laços
            break
        visitados.add(atual)
        caminho.append(f"{atual.id} ({atual.titulo})")
        atual = anteriores.get(atual)
    caminho.reverse()
    return caminho


def executar_algoritmo_parte2(lista_nos, mapa_nos, alg: str, source_id: str, target_id: str | None, out_dir: Path):
    origem = mapa_nos[source_id]
    destino = mapa_nos.get(target_id) if target_id else None

    inicio = time.perf_counter()
    if alg == "BFS":
        distancias, anteriores = bfs(lista_nos, origem)
    elif alg == "DIJKSTRA":
        distancias, anteriores, peso_negativo = dijkstra(lista_nos, origem)
        if peso_negativo:
            raise ValueError("Dijkstra não pode ser executado em grafos com pesos negativos.")
    elif alg == "BELLMAN_FORD":
        distancias, anteriores, tem_ciclo_negativo, ciclo_negativo = bellman_ford(
            lista_nos, origem
        )
        if tem_ciclo_negativo:
            raise ValueError(f"O grafo contém ciclo negativo: {ciclo_negativo}")
    elif alg == "DFS":
        distancias, anteriores = dfs(lista_nos, origem)
    else:
        raise NotImplementedError(f"Algoritmo {alg} ainda não conectado no solve.py")
    tempo_ms = (time.perf_counter() - inicio) * 1000

    resultado = {
        "algoritmo": alg,
        "origem": f"{origem.id} - {origem.titulo}",
        "destino": f"{destino.id} - {destino.titulo}" if destino else None,
        "tempo_ms": round(tempo_ms, 3),
        "custo_total": distancias[destino] if destino else None,
        "caminho": reconstruir_caminho(anteriores, origem, destino) if destino else None,
    }

    saida_path = out_dir / f"resultado_{alg.lower()}_{source_id}.json"
    saida_path.parent.mkdir(parents=True, exist_ok=True)
    with open(saida_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    print(f"[OK] {alg} concluído em {tempo_ms:.2f} ms. Salvo em: {saida_path}")
    return resultado


def executar_benchmark_parte2(dataset_path: str | Path, out_dir: Path, repeticoes: int = 5):
    """
    Roda os algoritmos em 3 escalas (10%, 50% e 100%) com média de 5 execuções
    e salva out/parte2/parte2_report.json.
    """
    if repeticoes < 1:
        raise ValueError("O número de repetições precisa ser pelo menos 1.")

    tamanhos = [
        ("10%", 41_624),
        ("50%", 208_121),
        ("100%", None),
    ]
    relatorio = {"escalabilidade": []}

    for rotulo, limite in tamanhos:
        print(f"\n--- Avaliando escala {rotulo} ---")
        nos_pos, mapa_pos = carregar_grafo_tmdb(dataset_path, limite_filmes=limite, transformacao_peso="nao_negativo")
        nos_orig, mapa_orig = carregar_grafo_tmdb(dataset_path, limite_filmes=limite, transformacao_peso="original")

        # Escolhe como fonte o primeiro nó que possua arestas de saída
        origem_pos = next((n for n in nos_pos if n.lista_arestas), nos_pos[0])
        origem_orig = mapa_orig[origem_pos.id]

        total_arestas = sum(len(n.lista_arestas) for n in nos_orig)
        tempos = {}

        for nome_alg, fn, grafo, fonte in [
            ("BFS", bfs, nos_orig, origem_orig),
            ("DFS", dfs, nos_orig, origem_orig),
            ("DIJKSTRA", dijkstra, nos_pos, origem_pos),
            ("BELLMAN_FORD", bellman_ford, nos_orig, origem_orig),
        ]:
            duracoes = []
            for _ in range(repeticoes):
                t0 = time.perf_counter()
                fn(grafo, fonte)
                duracoes.append((time.perf_counter() - t0) * 1000)
            tempos[nome_alg] = {
                "tempo_medio_ms": round(sum(duracoes) / repeticoes, 3),
                "execucoes_ms": [round(d, 3) for d in duracoes],
            }
            print(f"  {nome_alg}: média = {tempos[nome_alg]['tempo_medio_ms']} ms")

        relatorio["escalabilidade"].append({
            "escala": rotulo,
            "vertices": len(nos_orig),
            "arestas": total_arestas,
            "algoritmos": tempos,
        })

    report_path = out_dir / "parte2_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Relatório consolidado salvo em {report_path}")



# Exportação e métricas dos mapas da Parte 1.
_ORDEM_DIRECOES = ("N", "L", "S", "O")


def obter_id_mapa(caminho: Path) -> str:
    match = re.match(r"^(m\d+)_", caminho.stem)
    return match.group(1) if match else caminho.stem


def descobrir_mapas(entrada: str | Path) -> list[Path]:
    caminho = Path(entrada)
    if caminho.is_file():
        return [caminho]
    if not caminho.is_dir():
        raise FileNotFoundError(f"Caminho de mapas não encontrado: {caminho}")

    mapas = sorted(caminho.glob("*.txt"))
    pasta_grupo = Path("data/mapas_grupo")
    if pasta_grupo.is_dir() and caminho.resolve() != pasta_grupo.resolve():
        mapas.extend(sorted(pasta_grupo.glob("*.txt")))
    return mapas


def chave_ordenacao_estado(estado) -> tuple:
    return (
        estado.no_pos.posicao_linha,
        estado.no_pos.posicao_coluna,
        estado.chaves,
        tuple(sorted(getattr(estado, "bonus", frozenset()))),
    )


def _formatar_bonus(estado) -> str:
    bonus = getattr(estado, "bonus", frozenset())
    return "{" + ",".join(str(b) for b in sorted(bonus)) + "}"


def reconstruir_caminho_nos(anteriores: dict, inicio, fim) -> list | None:
    if fim is inicio:
        return [inicio]
    if fim not in anteriores or anteriores.get(fim) is None:
        return None
    caminho = []
    atual = fim
    visitados = set()
    while atual is not None:
        if id(atual) in visitados:
            return None
        visitados.add(id(atual))
        caminho.append(atual)
        if atual is inicio:
            break
        atual = anteriores.get(atual)
    if not caminho or caminho[-1] is not inicio:
        return None
    caminho.reverse()
    return caminho


def encontrar_aresta(no_u, no_v) -> tuple[str, int | float]:
    for direcao in _ORDEM_DIRECOES:
        idx = no_u.dicionario_direcoes[direcao]
        aresta = no_u.lista_arestas[idx]
        if aresta != 0 and aresta.destino is no_v:
            return direcao, aresta.custo
    raise ValueError("Transição não encontrada entre os vértices informados.")


def _calcular_custo_caminho(caminho_nos: list) -> int | float:
    return sum(encontrar_aresta(u, v)[1] for u, v in zip(caminho_nos, caminho_nos[1:]))


def _maior_grau_com_desempate(dicionario_graus: dict) -> dict:
    if not dicionario_graus:
        return {"estado": None, "grau": 0}
    estado_top, grau_top = min(
        dicionario_graus.items(),
        key=lambda item: (
            -item[1],
            item[0].no_pos.posicao_linha,
            item[0].no_pos.posicao_coluna,
            formatar_estado(item[0]),
        ),
    )
    return {"estado": formatar_estado(estado_top), "grau": grau_top}


def _exportar_graus_csv(labirinto, mapa_id: str, out_dir: Path) -> Path:
    caminho_csv = out_dir / f"graus_{mapa_id}.csv"
    estados_ordenados = sorted(
        labirinto.dicionario_graus_entrada.keys(),
        key=chave_ordenacao_estado,
    )
    with open(caminho_csv, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["estado", "grau_entrada", "grau_saida"])
        for estado in estados_ordenados:
            escritor.writerow([
                formatar_estado(estado),
                labirinto.dicionario_graus_entrada[estado],
                labirinto.dicionario_graus_saida[estado],
            ])
    return caminho_csv


def _exportar_armadilhas_csv(armadilhas: set, labirinto, mapa_id: str, out_dir: Path) -> Path:
    caminho_csv = out_dir / f"armadilhas_{mapa_id}.csv"
    ordenadas = sorted(armadilhas, key=chave_ordenacao_estado)
    with open(caminho_csv, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["estado", "linha", "coluna", "chaves", "bonus", "casa", "grau_saida"])
        for estado in ordenadas:
            escritor.writerow([
                formatar_estado(estado),
                estado.no_pos.posicao_linha,
                estado.no_pos.posicao_coluna,
                estado.chaves or "-",
                _formatar_bonus(estado),
                estado.no_pos.tipo,
                labirinto.dicionario_graus_saida[estado],
            ])
    return caminho_csv


def exportar_parte1(entrada_mapas: str | Path = "data/mapas", out_dir: str | Path = "out/parte1") -> list[Path]:
    """Executa exploração, métricas e algoritmos da Parte 1 e exporta todos os arquivos obrigatórios."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    mapas_paths = descobrir_mapas(entrada_mapas)
    if not mapas_paths:
        raise FileNotFoundError(f"Nenhum mapa .txt encontrado em {entrada_mapas}")

    arquivos_gerados: list[Path] = []
    metricas_globais: dict = {}
    camadas_globais: dict = {}
    linhas_solucoes: list[list] = []
    linhas_dfs: list[list] = []

    for mapa_path in mapas_paths:
        if not validar_labirinto(str(mapa_path)):
            raise ValueError(f"Mapa inválido segundo validar_labirinto: {mapa_path}")

        mapa_id = obter_id_mapa(mapa_path)
        labirinto = gerar_labirinto(str(mapa_path))
        modelos, inicio, fim = preparar_estados(labirinto)
        arestas_geradas, camadas = bfs_grafo_estados_exploracao(modelos, inicio, fim)

        # 1) out/parte1/arestas_<mapa>.csv
        arq_arestas = Path(exportar_arestas(arestas_geradas, mapa_id, diretorio=str(out_path)))
        arquivos_gerados.append(arq_arestas)

        # 2) out/parte1/graus_<mapa>.csv e métricas globais
        labirinto.calcular_graus_estado(arestas_geradas, camadas)
        arquivos_gerados.append(_exportar_graus_csv(labirinto, mapa_id, out_path))

        ordem_est = sum(len(c.lista_nos_estados) for c in camadas)
        tamanho_est = sum(1 for _, destino, _, _, _ in arestas_geradas if destino != "ALVO")
        densidade_est = tamanho_est / (ordem_est * (ordem_est - 1)) if ordem_est >= 2 else 0.0
        teto = labirinto.metricas.teto_teorico
        taxa_ocupacao = (ordem_est / teto) if teto > 0 else 0.0
        multiplicidades = [len(no.lista_estados_gerados) for no in labirinto.lista_nos]
        mult_max = max(multiplicidades, default=0)
        casas_mult_max = sum(1 for m in multiplicidades if m == mult_max)
        becos_rotulos = [
            formatar_estado(e)
            for e in sorted(labirinto.becos.keys(), key=chave_ordenacao_estado)
        ]

        metricas_globais[mapa_id] = {
            "arquivo": mapa_path.name,
            "G_pos": {
                "ordem": labirinto.metricas.ordem,
                "tamanho": labirinto.metricas.tamanho,
                "densidade": labirinto.metricas.densidade,
            },
            "G_est": {
                "ordem": ordem_est,
                "tamanho": tamanho_est,
                "densidade": densidade_est,
            },
            "num_chaves": labirinto.metricas.num_chaves,
            "num_bonus": labirinto.metricas.num_bonus,
            "teto_teorico": teto,
            "taxa_ocupacao": taxa_ocupacao,
            "maior_grau_entrada": _maior_grau_com_desempate(labirinto.dicionario_graus_entrada),
            "maior_grau_saida": _maior_grau_com_desempate(labirinto.dicionario_graus_saida),
            "multiplicidade_maxima": mult_max,
            "casas_com_multiplicidade_maxima": casas_mult_max,
            "num_becos": len(becos_rotulos),
            "becos": becos_rotulos,
        }

        # 3) Métricas por camada e arcos entre camadas
        info_camadas = {}
        for camada in camadas:
            camada.calcular_metricas_camada(arestas_geradas)
            # [IA] Claude – camadas rotuladas por (chaves, bônus) via rotulo_camada
            info_camadas[camada.rotulo] = {
                "ordem": camada.metricas.ordem,
                "tamanho": camada.metricas.tamanho,
                "densidade": camada.metricas.densidade,
            }

        arcos_entre_camadas = []
        contagem_casas_entre: dict[tuple[int, int, str], int] = {}
        for origem, destino, movimento, casa_destino, peso in arestas_geradas:
            if destino != "ALVO" and (origem.chaves, origem.bonus) != (destino.chaves, destino.bonus):
                r_dest = destino.no_pos.posicao_linha
                c_dest = destino.no_pos.posicao_coluna
                arcos_entre_camadas.append({
                    "origem": formatar_estado(origem),
                    "destino": formatar_estado(destino),
                    "camada_origem": rotulo_camada(origem.chaves, origem.bonus),
                    "camada_destino": rotulo_camada(destino.chaves, destino.bonus),
                    "movimento": movimento,
                    "casa_destino": casa_destino,
                    "posicao_destino": [r_dest, c_dest],
                    "peso": peso,
                })
                chave_casa = (r_dest, c_dest, casa_destino)
                contagem_casas_entre[chave_casa] = contagem_casas_entre.get(chave_casa, 0) + 1

        casas_geradoras = [
            {"linha": r, "coluna": c, "simbolo": simb, "quantidade_arcos": qtd}
            for (r, c, simb), qtd in sorted(contagem_casas_entre.items())
        ]
        camadas_globais[mapa_id] = {
            "arquivo": mapa_path.name,
            "camadas": info_camadas,
            "total_arcos_entre_camadas": len(arcos_entre_camadas),
            "casas_geradoras_entre_camadas": casas_geradoras,
            "arcos_entre_camadas": arcos_entre_camadas,
        }

        # 4) Algoritmos no grafo de estados com nó virtual ALVO
        lista_nos, no_ini, alvo, nos_por_estado = converter_grafo_estados(
            arestas_geradas, camadas, inicio, fim, incluir_alvo=True
        )
        estado_por_no = {no: est for est, no in nos_por_estado.items()}

        # 4a) BFS
        modelos_bfs = {no: No_estados("-", "-", "Não Visitado", no) for no in lista_nos}
        caminho_bfs = bfs(list(modelos_bfs.values()), modelos_bfs[no_ini], modelos_bfs[alvo])
        if caminho_bfs:
            caminho_real_bfs = [no for no in caminho_bfs if no is not alvo]
            passos_bfs = len(caminho_real_bfs) - 1
            custo_bfs = _calcular_custo_caminho(caminho_real_bfs)
            rotulos_bfs = " -> ".join(formatar_estado(estado_por_no[n]) for n in caminho_real_bfs)
            linhas_solucoes.append([mapa_id, "BFS", passos_bfs, custo_bfs, "OK", rotulos_bfs])
        else:
            linhas_solucoes.append([mapa_id, "BFS", "", "", "SEM_SOLUCAO", ""])

        # 4b) Dijkstra
        d_dist, d_ant, d_recusado = dijkstra(lista_nos, no_ini)
        caminho_real_dijk = None
        if d_recusado:
            linhas_solucoes.append([mapa_id, "DIJKSTRA", "", "", "RECUSA", ""])
        elif not math.isfinite(d_dist[alvo]):
            linhas_solucoes.append([mapa_id, "DIJKSTRA", "", "", "SEM_SOLUCAO", ""])
        else:
            caminho_dijk = reconstruir_caminho_nos(d_ant, no_ini, alvo)
            caminho_real_dijk = [no for no in caminho_dijk if no is not alvo]
            passos_dijk = len(caminho_real_dijk) - 1
            custo_dijk = d_dist[alvo]
            rotulos_dijk = " -> ".join(formatar_estado(estado_por_no[n]) for n in caminho_real_dijk)
            linhas_solucoes.append([mapa_id, "DIJKSTRA", passos_dijk, custo_dijk, "OK", rotulos_dijk])

        # 4c) Bellman-Ford
        bf_dist, bf_ant, bf_tem_ciclo, bf_ciclo = bellman_ford(lista_nos, no_ini)
        if bf_tem_ciclo:
            linhas_solucoes.append([mapa_id, "BELLMAN_FORD", "", "", "CICLO_NEGATIVO", ""])
        elif not math.isfinite(bf_dist[alvo]):
            linhas_solucoes.append([mapa_id, "BELLMAN_FORD", "", "", "SEM_SOLUCAO", ""])
        else:
            caminho_bf = reconstruir_caminho_nos(bf_ant, no_ini, alvo)
            caminho_real_bf = [no for no in caminho_bf if no is not alvo]
            passos_bf = len(caminho_real_bf) - 1
            custo_bf = bf_dist[alvo]
            rotulos_bf = " -> ".join(formatar_estado(estado_por_no[n]) for n in caminho_real_bf)
            linhas_solucoes.append([mapa_id, "BELLMAN_FORD", passos_bf, custo_bf, "OK", rotulos_bf])

        # 5) percurso_m03.json
        if mapa_id == "m03" and caminho_real_dijk is not None:
            estados_percurso = _construir_estados_percurso(caminho_real_dijk, estado_por_no)
            arquivos_gerados.append(
                _salvar_percurso_json(
                    out_path, mapa_id, mapa_path, "DIJKSTRA", d_dist[alvo], estados_percurso
                )
            )

        # 6) ciclo_negativo_m06.json
        if mapa_id == "m06":
            arquivos_gerados.append(
                _salvar_ciclo_negativo_json(
                    out_path, mapa_id, mapa_path, bf_tem_ciclo, bf_ciclo, estado_por_no
                )
            )

        # 7) armadilhas_m04.csv, armadilhas_m07.csv e mapas do grupo com armadilhas
        # [IA] Antigravity (Gemini) – exporta armadilhas_<mapa>.csv também para mapas do grupo com estados-armadilha
        if mapa_id in ("m04", "m07") or mapa_path.parent.name == "mapas_grupo":
            armadilhas = bfs_estados_armadilha(arestas_geradas, camadas)
            if mapa_id in ("m04", "m07") or armadilhas:
                arquivos_gerados.append(_exportar_armadilhas_csv(armadilhas, labirinto, mapa_id, out_path))

        # 8) DFS no grafo de estados sem nó virtual ALVO
        lista_nos_sem_alvo, no_ini_sem_alvo, _, _ = converter_grafo_estados(
            arestas_geradas, camadas, inicio, fim, incluir_alvo=False
        )
        res_dfs = dfs(lista_nos_sem_alvo, no_ini_sem_alvo, detalhado=True)
        contagem_dfs = res_dfs["contagem"]
        linhas_dfs.append([
            mapa_id,
            contagem_dfs["arvore"],
            contagem_dfs["retorno"],
            contagem_dfs["avanco"],
            contagem_dfs["cruzamento"],
        ])

    # Grava arquivos agregados
    metricas_path = out_path / "metricas_global.json"
    with open(metricas_path, "w", encoding="utf-8") as f:
        json.dump(metricas_globais, f, indent=2, ensure_ascii=False)
    arquivos_gerados.append(metricas_path)

    camadas_path = out_path / "camadas.json"
    with open(camadas_path, "w", encoding="utf-8") as f:
        json.dump(camadas_globais, f, indent=2, ensure_ascii=False)
    arquivos_gerados.append(camadas_path)

    solucoes_path = out_path / "solucoes.csv"
    with open(solucoes_path, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["mapa", "algoritmo", "passos", "custo", "status", "caminho"])
        escritor.writerows(linhas_solucoes)
    arquivos_gerados.append(solucoes_path)

    dfs_path = out_path / "dfs_classificacao.csv"
    with open(dfs_path, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["mapa", "arvore", "retorno", "avanco", "cruzamento"])
        escritor.writerows(linhas_dfs)
    arquivos_gerados.append(dfs_path)

    return arquivos_gerados


# [IA] Antigravity (Gemini) – helpers e orquestração individual da Parte 1 (--mapa)
def _construir_estados_percurso(
    caminho_real: list,
    estado_por_no: dict,
    fonte_consumivel: bool = False,
) -> list[dict]:
    estados_percurso = []
    custo_acum = 0
    fontes_consumidas: set[tuple[int, int]] = set()

    for idx, no in enumerate(caminho_real):
        est = estado_por_no[no]
        if idx == 0:
            movimento = None
            custo_passo = 0
        else:
            movimento, custo_passo = encontrar_aresta(caminho_real[idx - 1], no)
            if fonte_consumivel and est.no_pos.tipo == "*":
                pos_fonte = (est.no_pos.posicao_linha, est.no_pos.posicao_coluna)
                if pos_fonte in fontes_consumidas:
                    custo_passo = 1
                else:
                    fontes_consumidas.add(pos_fonte)
            custo_acum += custo_passo

        estados_percurso.append({
            "passo": idx,
            "estado": formatar_estado(est),
            "camada": rotulo_camada(est.chaves, est.bonus),
            "linha": est.no_pos.posicao_linha,
            "coluna": est.no_pos.posicao_coluna,
            "casa": est.no_pos.tipo,
            "chaves": est.chaves or "-",
            "bonus": sorted(getattr(est, "bonus", frozenset())),
            "movimento": movimento,
            "custo_passo": custo_passo,
            "custo_acumulado": custo_acum,
        })
    return estados_percurso


def _construir_detalhes_ciclo(bf_ciclo: list, estado_por_no: dict) -> tuple[list[dict], int | float]:
    transicoes_ciclo = []
    custo_ciclo = 0
    for u, v in zip(bf_ciclo, bf_ciclo[1:]):
        mov, peso = encontrar_aresta(u, v)
        est_u = estado_por_no[u]
        est_v = estado_por_no[v]
        custo_ciclo += peso
        transicoes_ciclo.append({
            "origem": formatar_estado(est_u),
            "destino": formatar_estado(est_v),
            "movimento": mov,
            "casa_destino": est_v.no_pos.tipo,
            "peso": peso,
        })
    return transicoes_ciclo, custo_ciclo


def _salvar_percurso_json(
    out_path: Path,
    mapa_id: str,
    mapa_path: Path,
    alg: str,
    custo_total,
    estados_percurso: list[dict],
) -> Path:
    percurso_path = out_path / f"percurso_{mapa_id}.json"
    estados_limpos = [
        {k: v for k, v in item.items() if k != "camada"}
        for item in estados_percurso
    ]
    with open(percurso_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "mapa": mapa_id,
                "arquivo": mapa_path.name,
                "algoritmo": alg,
                "status": "OK",
                "passos": max(0, len(estados_limpos) - 1),
                "custo_total": custo_total,
                "estados": estados_limpos,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    return percurso_path


def _salvar_ciclo_negativo_json(
    out_path: Path,
    mapa_id: str,
    mapa_path: Path,
    bf_tem_ciclo: bool,
    bf_ciclo: list,
    estado_por_no: dict,
) -> Path:
    transicoes_ciclo, custo_ciclo = _construir_detalhes_ciclo(bf_ciclo, estado_por_no)
    ciclo_path = out_path / f"ciclo_negativo_{mapa_id}.json"
    with open(ciclo_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "mapa": mapa_id,
                "arquivo": mapa_path.name,
                "algoritmo": "BELLMAN_FORD",
                "tem_ciclo_negativo": bf_tem_ciclo,
                "custo_ciclo": custo_ciclo,
                "tamanho_ciclo": len(transicoes_ciclo),
                "ciclo_estados": [formatar_estado(estado_por_no[n]) for n in bf_ciclo],
                "transicoes": transicoes_ciclo,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    return ciclo_path


def _executar_algoritmo_unico_parte1(
    alg: str,
    arestas_geradas: list,
    camadas: list,
    inicio,
    fim,
    mapa_id: str,
    mapa_path: Path,
    fonte_consumivel: bool = False,
) -> tuple[dict, list, dict, object]:
    """Executa um algoritmo específico sobre G_est e retorna (resultado_dict, bf_ciclo, estado_por_no, alvo)."""
    t0 = time.perf_counter()

    if alg == "DFS":
        lista_nos_sem_alvo, no_ini_sem_alvo, _, nos_por_estado = converter_grafo_estados(
            arestas_geradas, camadas, inicio, fim, incluir_alvo=False
        )
        estado_por_no = {no: est for est, no in nos_por_estado.items()}
        res_dfs = dfs(lista_nos_sem_alvo, no_ini_sem_alvo, detalhado=True)
        tempo_ms = round((time.perf_counter() - t0) * 1000, 3)

        ordem_estados = [formatar_estado(estado_por_no[n]) for n in res_dfs["ordem"]]
        estados_dfs = []
        for idx, no in enumerate(res_dfs["ordem"]):
            est = estado_por_no[no]
            dist = res_dfs["distancias"].get(no)
            estados_dfs.append({
                "passo": idx,
                "estado": formatar_estado(est),
                "camada": rotulo_camada(est.chaves, est.bonus),
                "linha": est.no_pos.posicao_linha,
                "coluna": est.no_pos.posicao_coluna,
                "casa": est.no_pos.tipo,
                "chaves": est.chaves or "-",
                "bonus": sorted(getattr(est, "bonus", frozenset())),
                "movimento": None if idx == 0 else "DFS",
                "custo_passo": 0,
                "custo_acumulado": dist if dist is not None and math.isfinite(dist) else None,
            })
        classificacao = [
            {
                "origem": formatar_estado(estado_por_no[u]),
                "destino": formatar_estado(estado_por_no[v]),
                "tipo": tipo,
            }
            for u, v, tipo in res_dfs["classificacao"]
        ]
        resultado = {
            "mapa": mapa_id,
            "arquivo": mapa_path.name,
            "algoritmo": "DFS",
            "fonte_consumivel": False,
            "status": "OK",
            "tempo_ms": tempo_ms,
            "tem_ciclo": res_dfs["tem_ciclo"],
            "contagem": res_dfs["contagem"],
            "ordem_estados": ordem_estados,
            "estados": estados_dfs,
            "classificacao": classificacao,
        }
        return resultado, [], estado_por_no, None

    lista_nos, no_ini, alvo, nos_por_estado = converter_grafo_estados(
        arestas_geradas, camadas, inicio, fim, incluir_alvo=True
    )
    estado_por_no = {no: est for est, no in nos_por_estado.items()}

    base = {
        "mapa": mapa_id,
        "arquivo": mapa_path.name,
        "algoritmo": alg,
        "fonte_consumivel": fonte_consumivel if alg == "BELLMAN_FORD" else False,
    }

    if alg == "BFS":
        modelos_bfs = {no: No_estados("-", "-", "Não Visitado", no) for no in lista_nos}
        caminho_bfs = bfs(list(modelos_bfs.values()), modelos_bfs[no_ini], modelos_bfs[alvo])
        tempo_ms = round((time.perf_counter() - t0) * 1000, 3)
        if not caminho_bfs:
            return {**base, "status": "SEM_SOLUCAO", "tempo_ms": tempo_ms}, [], estado_por_no, alvo
        caminho_real = [no for no in caminho_bfs if no is not alvo]
        estados = _construir_estados_percurso(caminho_real, estado_por_no)
        custo_total = estados[-1]["custo_acumulado"] if estados else 0
        return (
            {
                **base,
                "status": "OK",
                "tempo_ms": tempo_ms,
                "passos": len(caminho_real) - 1,
                "custo_total": custo_total,
                "caminho": [e["estado"] for e in estados],
                "estados": estados,
            },
            [],
            estado_por_no,
            alvo,
        )

    if alg == "DIJKSTRA":
        d_dist, d_ant, d_recusado = dijkstra(lista_nos, no_ini)
        tempo_ms = round((time.perf_counter() - t0) * 1000, 3)
        if d_recusado:
            return (
                {
                    **base,
                    "status": "RECUSA",
                    "tempo_ms": tempo_ms,
                    "motivo": "Dijkstra recusou o grafo por conter arco(s) de peso negativo.",
                },
                [],
                estado_por_no,
                alvo,
            )
        if not math.isfinite(d_dist[alvo]):
            return {**base, "status": "SEM_SOLUCAO", "tempo_ms": tempo_ms}, [], estado_por_no, alvo
        caminho_dijk = reconstruir_caminho_nos(d_ant, no_ini, alvo)
        if not caminho_dijk:
            return {**base, "status": "SEM_SOLUCAO", "tempo_ms": tempo_ms}, [], estado_por_no, alvo
        caminho_real = [no for no in caminho_dijk if no is not alvo]
        estados = _construir_estados_percurso(caminho_real, estado_por_no)
        return (
            {
                **base,
                "status": "OK",
                "tempo_ms": tempo_ms,
                "passos": len(caminho_real) - 1,
                "custo_total": d_dist[alvo],
                "caminho": [e["estado"] for e in estados],
                "estados": estados,
            },
            [],
            estado_por_no,
            alvo,
        )

    if alg == "BELLMAN_FORD":
        if fonte_consumivel:
            # Adapta os nós do grafo convertido (No) para o atributo .no_pos esperado por bellman_ford_sem_ciclo_negativo
            for no in lista_nos:
                if not hasattr(no, "no_pos"):
                    no.no_pos = no
            bf_dist, bf_ant = bellman_ford_sem_ciclo_negativo(lista_nos, no_ini)
            tempo_ms = round((time.perf_counter() - t0) * 1000, 3)
            if not math.isfinite(bf_dist[alvo]):
                return {**base, "status": "SEM_SOLUCAO", "tempo_ms": tempo_ms}, [], estado_por_no, alvo
            caminho_bf = reconstruir_caminho_nos(bf_ant, no_ini, alvo)
            if not caminho_bf:
                return {**base, "status": "SEM_SOLUCAO", "tempo_ms": tempo_ms}, [], estado_por_no, alvo
            caminho_real = [no for no in caminho_bf if no is not alvo]
            estados = _construir_estados_percurso(caminho_real, estado_por_no, fonte_consumivel=True)
            return (
                {
                    **base,
                    "status": "OK",
                    "tempo_ms": tempo_ms,
                    "passos": len(caminho_real) - 1,
                    "custo_total": bf_dist[alvo],
                    "caminho": [e["estado"] for e in estados],
                    "estados": estados,
                },
                [],
                estado_por_no,
                alvo,
            )

        bf_dist, bf_ant, bf_tem_ciclo, bf_ciclo = bellman_ford(lista_nos, no_ini)
        tempo_ms = round((time.perf_counter() - t0) * 1000, 3)
        if bf_tem_ciclo:
            transicoes_ciclo, custo_ciclo = _construir_detalhes_ciclo(bf_ciclo, estado_por_no)
            return (
                {
                    **base,
                    "status": "CICLO_NEGATIVO",
                    "tempo_ms": tempo_ms,
                    "tem_ciclo_negativo": True,
                    "custo_ciclo": custo_ciclo,
                    "tamanho_ciclo": len(transicoes_ciclo),
                    "ciclo_estados": [formatar_estado(estado_por_no[n]) for n in bf_ciclo],
                    "transicoes": transicoes_ciclo,
                },
                bf_ciclo,
                estado_por_no,
                alvo,
            )
        if not math.isfinite(bf_dist[alvo]):
            return {**base, "status": "SEM_SOLUCAO", "tempo_ms": tempo_ms}, [], estado_por_no, alvo
        caminho_bf = reconstruir_caminho_nos(bf_ant, no_ini, alvo)
        if not caminho_bf:
            return {**base, "status": "SEM_SOLUCAO", "tempo_ms": tempo_ms}, [], estado_por_no, alvo
        caminho_real = [no for no in caminho_bf if no is not alvo]
        estados = _construir_estados_percurso(caminho_real, estado_por_no)
        return (
            {
                **base,
                "status": "OK",
                "tempo_ms": tempo_ms,
                "passos": len(caminho_real) - 1,
                "custo_total": bf_dist[alvo],
                "caminho": [e["estado"] for e in estados],
                "estados": estados,
            },
            [],
            estado_por_no,
            alvo,
        )

    raise ValueError(f"Algoritmo não suportado na Parte 1: {alg}")


def _gerar_html_interativo(
    mapa_path: Path,
    mapa_id: str,
    arestas_geradas: list,
    camadas: list,
    inicio,
    fim,
    out_path: Path,
    alg_inicial: str | None = None,
    fonte_consumivel: bool = False,
) -> Path:
    with open(mapa_path, "r", encoding="utf-8") as f:
        linhas_grade = [l.rstrip("\r\n") for l in f if l.strip() and not l.startswith(";")]

    tem_fonte = any("*" in linha for linha in linhas_grade)
    execucoes_spec: list[tuple[str, str, bool]] = [
        ("BFS", "BFS", False),
        ("DIJKSTRA", "DIJKSTRA", False),
        ("BELLMAN_FORD", "BELLMAN_FORD", False),
    ]
    if fonte_consumivel or tem_fonte:
        execucoes_spec.append(("BELLMAN_FORD_FONTE", "BELLMAN_FORD", True))
    execucoes_spec.append(("DFS", "DFS", False))

    algoritmos_dados: dict[str, dict] = {}
    for chave_alg, alg_nome, usar_fonte in execucoes_spec:
        res, _, _, _ = _executar_algoritmo_unico_parte1(
            alg_nome,
            arestas_geradas,
            camadas,
            inicio,
            fim,
            mapa_id,
            mapa_path,
            fonte_consumivel=usar_fonte,
        )
        algoritmos_dados[chave_alg] = {
            "rotulo": (
                "Bellman-Ford (fonte * consumível)"
                if chave_alg == "BELLMAN_FORD_FONTE"
                else alg_nome
            ),
            "status": res.get("status"),
            "passos": res.get("passos"),
            "custo_total": res.get("custo_total"),
            "motivo": res.get("motivo"),
            "custo_ciclo": res.get("custo_ciclo"),
            "ciclo_estados": res.get("ciclo_estados", []),
            "contagem": res.get("contagem"),
            "tem_ciclo": res.get("tem_ciclo"),
            "quadros": res.get("estados", []),
        }

    armadilhas_set = bfs_estados_armadilha(arestas_geradas, camadas)
    armadilhas_lista = [
        {
            "estado": formatar_estado(e),
            "camada": rotulo_camada(e.chaves, e.bonus),
            "linha": e.no_pos.posicao_linha,
            "coluna": e.no_pos.posicao_coluna,
        }
        for e in sorted(armadilhas_set, key=chave_ordenacao_estado)
    ]

    camadas_ordem = [c.rotulo for c in camadas]
    if alg_inicial == "BELLMAN_FORD" and fonte_consumivel and "BELLMAN_FORD_FONTE" in algoritmos_dados:
        alg_padrao = "BELLMAN_FORD_FONTE"
    elif alg_inicial in algoritmos_dados:
        alg_padrao = alg_inicial
    elif algoritmos_dados["DIJKSTRA"]["status"] == "OK":
        alg_padrao = "DIJKSTRA"
    elif algoritmos_dados["BELLMAN_FORD"]["status"] == "OK":
        alg_padrao = "BELLMAN_FORD"
    else:
        alg_padrao = "BFS"

    payload = {
        "mapa": mapa_id,
        "arquivo": mapa_path.name,
        "grade": linhas_grade,
        "camadas": camadas_ordem,
        "armadilhas": armadilhas_lista,
        "algoritmo_padrao": alg_padrao,
        "algoritmos": algoritmos_dados,
    }
    payload_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    titulo = html.escape(f"Labirinto Interativo — {mapa_id} ({mapa_path.name})")

    html_doc = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{titulo}</title>
  <style>
    :root {{
      --bg: #f5f7fb; --card: #ffffff; --border: #e5e7eb;
      --text: #111827; --muted: #6b7280; --accent: #3b5bdb;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background: var(--bg); color: var(--text); }}
    .wrap {{ max-width: 1280px; margin: 0 auto; padding: 20px; }}
    h1 {{ margin: 0 0 6px; font-size: 1.6rem; }}
    .sub {{ color: var(--muted); font-size: .92rem; margin-bottom: 16px; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 12px 14px; margin-bottom: 14px; }}
    .toolbar label {{ font-size: .85rem; color: var(--muted); display: flex; align-items: center; gap: 6px; }}
    select, button {{ font: inherit; padding: 6px 10px; border-radius: 8px; border: 1px solid #d1d5db; background: #fff; cursor: pointer; }}
    button.primary {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
    button:disabled {{ opacity: .5; cursor: not-allowed; }}
    .status-bar {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 14px; }}
    .stat {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px; min-width: 140px; }}
    .stat .k {{ font-size: .74rem; text-transform: uppercase; color: var(--muted); font-weight: 700; }}
    .stat .v {{ font-size: 1.25rem; font-weight: 700; margin-top: 2px; }}
    .main {{ display: grid; grid-template-columns: 2fr 1fr; gap: 16px; align-items: start; }}
    @media (max-width: 900px) {{ .main {{ grid-template-columns: 1fr; }} }}
    .board-card, .panel {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 14px; }}
    .board-wrap {{ background: #0f1d26; padding: 12px; border-radius: 10px; overflow: auto; }}
    .grid {{ display: grid; gap: 2px; margin: 0 auto; width: max-content; }}
    .cell {{ width: 28px; height: 28px; display: grid; place-items: center; position: relative; border-radius: 4px; font: 700 13px ui-monospace, monospace; background: #eef3f1; color: #203741; }}
    .cell.wall {{ background: #1d313c; color: transparent; }}
    .cell.start {{ background: #3b5bdb; color: #fff; }}
    .cell.goal {{ background: #2f9e44; color: #fff; }}
    .cell.mud {{ background: #e9d5a8; }}
    .cell.water {{ background: #9fd0e8; }}
    .cell.key {{ background: #ffe58f; color: #7a5200; }}
    .cell.door {{ background: #8d6748; color: #fff; }}
    .cell.belt {{ background: #e2dcff; color: #4b3a8c; }}
    .cell.neg {{ background: #ffd1e3; color: #9c1f55; }}
    .cell > span {{ position: relative; z-index: 3; }}
    .trail {{ position: absolute; inset: 0; border-radius: 4px; opacity: .52; z-index: 1; }}
    .trap {{ position: absolute; inset: 0; border-radius: 4px; z-index: 2; box-shadow: inset 0 0 0 2px #e03131; background: repeating-linear-gradient(135deg,#e0313155 0 3px,transparent 3px 7px); }}
    .negcycle {{ position: absolute; inset: 1px; border-radius: 4px; z-index: 2; border: 2px solid #ffd43b; }}
    .agent {{ position: absolute; width: 65%; height: 65%; border-radius: 50%; z-index: 4; background: #fff; border: 3px solid #111827; box-shadow: 0 0 0 2px rgba(255,255,255,.5); }}
    .panel h3 {{ margin: 0 0 10px; font-size: 1rem; }}
    .row {{ display: flex; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid #f3f4f6; font-size: .9rem; }}
    .row:last-child {{ border-bottom: 0; }}
    .legend {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; font-size: .8rem; color: var(--muted); }}
    .legend span {{ display: inline-flex; align-items: center; gap: 5px; }}
    .swatch {{ width: 12px; height: 12px; border-radius: 3px; display: inline-block; }}
    input[type="range"] {{ vertical-align: middle; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>{titulo}</h1>
    <div class="sub">Visualização interativa da Parte 1 gerada via CLI (<code>--interactive</code>)</div>

    <div class="toolbar">
      <label>Algoritmo: <select id="algSelect"></select></label>
      <label>Camada: <select id="layerSelect"></select></label>
      <button id="btnStart">⏮ Início</button>
      <button id="btnPrev">◀ Voltar</button>
      <button id="btnPlay" class="primary">▶ Reproduzir</button>
      <button id="btnNext">Avançar ▶</button>
      <label>Passo: <input id="stepSlider" type="range" min="0" max="0" value="0" /> <span id="stepLabel">0/0</span></label>
      <label>Velocidade: <input id="speedSlider" type="range" min="0.25" max="4" step="0.25" value="1" /> <span id="speedLabel">1.0x</span></label>
      <label><input id="chkTrap" type="checkbox" checked /> Realçar armadilhas</label>
      <label><input id="chkCycle" type="checkbox" checked /> Realçar ciclo negativo</label>
    </div>

    <div class="status-bar" id="summaryBar"></div>

    <div class="main">
      <div class="board-card">
        <div class="board-wrap"><div class="grid" id="grid"></div></div>
        <div class="legend" id="legend"></div>
      </div>
      <div class="panel">
        <h3>Estado Atual</h3>
        <div id="statePanel"></div>
      </div>
    </div>
  </div>

  <script>
    const DATA = {payload_json};
    const COLORS = ["#f76707","#7048e8","#12a37f","#d6336c","#1971c2","#5c940d","#1098ad","#f08c00","#c92a2a","#2b8a3e"];
    const SETAS = {{ "^": "↑", ">": "→", "v": "↓", "<": "←" }};
    const layerColor = (layer) => COLORS[Math.max(0, DATA.camadas.indexOf(layer)) % COLORS.length];

    let currentAlg = DATA.algoritmo_padrao;
    let currentLayer = "__ALL__";
    let step = 0;
    let timer = null;

    const algSelect = document.getElementById("algSelect");
    const layerSelect = document.getElementById("layerSelect");
    const stepSlider = document.getElementById("stepSlider");
    const stepLabel = document.getElementById("stepLabel");
    const speedSlider = document.getElementById("speedSlider");
    const speedLabel = document.getElementById("speedLabel");
    const chkTrap = document.getElementById("chkTrap");
    const chkCycle = document.getElementById("chkCycle");
    const btnPlay = document.getElementById("btnPlay");

    for (const [k, v] of Object.entries(DATA.algoritmos)) {{
      const opt = document.createElement("option");
      opt.value = k;
      opt.textContent = v.rotulo;
      if (k === currentAlg) opt.selected = true;
      algSelect.appendChild(opt);
    }}

    function populateLayers() {{
      layerSelect.innerHTML = "";
      for (const [val, text] of [["__ALL__", "Todas as camadas"], ["__CURRENT__", "Só a camada atual"]]) {{
        const opt = document.createElement("option");
        opt.value = val;
        opt.textContent = text;
        layerSelect.appendChild(opt);
      }}
      for (const c of DATA.camadas) {{
        const opt = document.createElement("option");
        opt.value = c;
        opt.textContent = "Camada: " + c;
        layerSelect.appendChild(opt);
      }}
      layerSelect.value = currentLayer;
    }}

    function cellClass(ch) {{
      if (ch === "#") return "wall";
      if (ch === "S") return "start";
      if (ch === "G") return "goal";
      if (ch === ",") return "mud";
      if (ch === "~") return "water";
      if ("abcd".includes(ch)) return "key";
      if ("ABCD".includes(ch)) return "door";
      if ("><^v".includes(ch)) return "belt";
      if (ch === "+" || ch === "*") return "neg";
      return "";
    }}

    function stopPlay() {{
      if (timer) {{ clearInterval(timer); timer = null; }}
      btnPlay.textContent = "▶ Reproduzir";
    }}

    function startPlay() {{
      stopPlay();
      const frames = DATA.algoritmos[currentAlg].quadros || [];
      if (frames.length <= 1) return;
      if (step >= frames.length - 1) step = 0;
      const ms = Math.round(1000 / parseFloat(speedSlider.value));
      btnPlay.textContent = "⏸ Pausar";
      timer = setInterval(() => {{
        const maxIdx = (DATA.algoritmos[currentAlg].quadros || []).length - 1;
        if (step >= maxIdx) {{ stopPlay(); return; }}
        step += 1;
        render();
      }}, ms);
    }}

    function render() {{
      const alg = DATA.algoritmos[currentAlg];
      const frames = alg.quadros || [];
      const maxIdx = Math.max(0, frames.length - 1);
      step = Math.max(0, Math.min(step, maxIdx));
      stepSlider.max = String(maxIdx);
      stepSlider.value = String(step);
      stepLabel.textContent = frames.length ? `${{step}}/${{maxIdx}}` : "0/0";

      const cur = frames[step] || null;
      const activeLayer = currentLayer === "__CURRENT__" ? (cur ? cur.camada : "__ALL__") : currentLayer;

      const summary = [
        ["Status", alg.status || "-"],
        ["Passos", alg.passos ?? (frames.length ? frames.length - 1 : "—")],
        ["Custo", alg.custo_total ?? (alg.custo_ciclo !== undefined ? `Ciclo (${{alg.custo_ciclo}})` : "—")],
        ["Armadilhas", `${{DATA.armadilhas.length}}`],
        ["Camadas", `${{DATA.camadas.length}}`],
      ];
      document.getElementById("summaryBar").innerHTML = summary
        .map(([k, v]) => `<div class="stat"><div class="k">${{k}}</div><div class="v">${{v}}</div></div>`)
        .join("");

      const trailMap = new Map();
      for (let i = 0; i <= step && i < frames.length; i++) {{
        const f = frames[i];
        if (activeLayer === "__ALL__" || f.camada === activeLayer) {{
          trailMap.set(`${{f.linha}},${{f.coluna}}`, layerColor(f.camada));
        }}
      }}
      const trapSet = new Set(
        DATA.armadilhas
          .filter(t => activeLayer === "__ALL__" || t.camada === activeLayer)
          .map(t => `${{t.linha}},${{t.coluna}}`)
      );
      const cycleSet = new Set();
      for (const s of (alg.ciclo_estados || [])) {{
        const m = s.match(/\\((\\d+),(\\d+)\\)/);
        if (m) cycleSet.add(`${{m[1]}},${{m[2]}}`);
      }}

      const cols = DATA.grade[0] ? DATA.grade[0].length : 0;
      const grid = document.getElementById("grid");
      grid.style.gridTemplateColumns = `repeat(${{cols}}, 28px)`;
      let htmlCells = "";
      for (let r = 0; r < DATA.grade.length; r++) {{
        const line = DATA.grade[r];
        for (let c = 0; c < line.length; c++) {{
          const ch = line[c];
          const key = `${{r}},${{c}}`;
          const disp = ch === "#" ? "" : (SETAS[ch] || (ch === "." ? "·" : ch));
          htmlCells += `<div class="cell ${{cellClass(ch)}}">`;
          if (trailMap.has(key)) htmlCells += `<div class="trail" style="background:${{trailMap.get(key)}}"></div>`;
          if (chkTrap.checked && trapSet.has(key)) htmlCells += `<div class="trap"></div>`;
          if (chkCycle.checked && cycleSet.has(key)) htmlCells += `<div class="negcycle"></div>`;
          if (cur && cur.linha === r && cur.coluna === c) htmlCells += `<div class="agent" style="border-color:${{layerColor(cur.camada)}}"></div>`;
          htmlCells += `<span>${{disp}}</span></div>`;
        }}
      }}
      grid.innerHTML = htmlCells;

      document.getElementById("legend").innerHTML = DATA.camadas
        .map(c => `<span><i class="swatch" style="background:${{layerColor(c)}}"></i>${{c}}</span>`)
        .join("");

      const panel = document.getElementById("statePanel");
      if (!cur) {{
        const extra = alg.motivo ? `<div class="row"><span>Motivo</span><b>${{alg.motivo}}</b></div>` : "";
        const ciclo = alg.ciclo_estados && alg.ciclo_estados.length
          ? `<div class="row"><span>Ciclo</span><b>${{alg.ciclo_estados.join(" → ")}}</b></div>` : "";
        panel.innerHTML = `<div class="row"><span>Status</span><b>${{alg.status}}</b></div>${{extra}}${{ciclo}}`;
      }} else {{
        const bonusTxt = cur.bonus && cur.bonus.length ? cur.bonus.join(", ") : "nenhum";
        panel.innerHTML = `
          <div class="row"><span>Estado</span><b>${{cur.estado}}</b></div>
          <div class="row"><span>Camada</span><b>${{cur.camada}}</b></div>
          <div class="row"><span>Posição</span><b>(${{cur.linha}}, ${{cur.coluna}}) · '${{cur.casa}}'</b></div>
          <div class="row"><span>Chaves</span><b>${{cur.chaves}}</b></div>
          <div class="row"><span>Bônus</span><b>${{bonusTxt}}</b></div>
          <div class="row"><span>Movimento</span><b>${{cur.movimento || "—"}}</b></div>
          <div class="row"><span>Custo passo</span><b>${{cur.custo_passo}}</b></div>
          <div class="row"><span>Custo acumulado</span><b>${{cur.custo_acumulado ?? "—"}}</b></div>
        `;
      }}
    }}

    algSelect.addEventListener("change", () => {{ stopPlay(); currentAlg = algSelect.value; step = 0; render(); }});
    layerSelect.addEventListener("change", () => {{ currentLayer = layerSelect.value; render(); }});
    stepSlider.addEventListener("input", () => {{ stopPlay(); step = parseInt(stepSlider.value, 10); render(); }});
    speedSlider.addEventListener("input", () => {{
      speedLabel.textContent = parseFloat(speedSlider.value).toFixed(2).replace(/\\.00$/, ".0") + "x";
      if (timer) startPlay();
    }});
    chkTrap.addEventListener("change", render);
    chkCycle.addEventListener("change", render);
    document.getElementById("btnStart").addEventListener("click", () => {{ stopPlay(); step = 0; render(); }});
    document.getElementById("btnPrev").addEventListener("click", () => {{ stopPlay(); step = Math.max(0, step - 1); render(); }});
    document.getElementById("btnNext").addEventListener("click", () => {{
      stopPlay();
      const maxIdx = Math.max(0, (DATA.algoritmos[currentAlg].quadros || []).length - 1);
      step = Math.min(maxIdx, step + 1);
      render();
    }});
    btnPlay.addEventListener("click", () => {{ if (timer) stopPlay(); else startPlay(); }});

    populateLayers();
    render();
  </script>
</body>
</html>
"""
    html_path = out_path / "labirinto_interativo.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    return html_path


def executar_mapa_parte1(
    mapa_path: str | Path,
    out_dir: str | Path,
    alg: str | None = None,
    fonte_consumivel: bool = False,
    armadilhas: bool = False,
    interactive: bool = False,
) -> dict:
    """Executa a Parte 1 para um mapa individual e grava os arquivos de saída em ``out_dir``."""
    caminho = Path(mapa_path)
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo de mapa não encontrado: {caminho}")
    if not validar_labirinto(str(caminho)):
        raise ValueError(f"Mapa inválido segundo validar_labirinto: {caminho}")

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    mapa_id = obter_id_mapa(caminho)

    labirinto = gerar_labirinto(str(caminho))
    modelos, inicio, fim = preparar_estados(labirinto)
    arestas_geradas, camadas = bfs_grafo_estados_exploracao(modelos, inicio, fim)
    labirinto.calcular_graus_estado(arestas_geradas, camadas)

    arquivos_gerados: list[Path] = []
    arq_arestas = Path(exportar_arestas(arestas_geradas, mapa_id, diretorio=str(out_path)))
    arquivos_gerados.append(arq_arestas)
    arquivos_gerados.append(_exportar_graus_csv(labirinto, mapa_id, out_path))

    ordem_est = sum(len(c.lista_nos_estados) for c in camadas)
    tamanho_est = sum(1 for _, destino, _, _, _ in arestas_geradas if destino != "ALVO")

    resultado_alg = None
    if alg:
        resultado_alg, bf_ciclo, estado_por_no, _ = _executar_algoritmo_unico_parte1(
            alg,
            arestas_geradas,
            camadas,
            inicio,
            fim,
            mapa_id,
            caminho,
            fonte_consumivel=fonte_consumivel,
        )
        sufixo = "_fonte_consumivel" if (alg == "BELLMAN_FORD" and fonte_consumivel) else ""
        res_path = out_path / f"resultado_{mapa_id}_{alg.lower()}{sufixo}.json"
        with open(res_path, "w", encoding="utf-8") as f:
            json.dump(resultado_alg, f, indent=2, ensure_ascii=False)
        arquivos_gerados.append(res_path)

        if alg == "DIJKSTRA" and resultado_alg.get("status") == "OK":
            arquivos_gerados.append(
                _salvar_percurso_json(
                    out_path,
                    mapa_id,
                    caminho,
                    "DIJKSTRA",
                    resultado_alg["custo_total"],
                    resultado_alg["estados"],
                )
            )
        elif (
            alg == "BELLMAN_FORD"
            and not fonte_consumivel
            and resultado_alg.get("status") == "CICLO_NEGATIVO"
        ):
            arquivos_gerados.append(
                _salvar_ciclo_negativo_json(
                    out_path, mapa_id, caminho, True, bf_ciclo, estado_por_no
                )
            )

    info_armadilhas = None
    if armadilhas:
        conj_armadilhas = bfs_estados_armadilha(arestas_geradas, camadas)
        arquivos_gerados.append(_exportar_armadilhas_csv(conj_armadilhas, labirinto, mapa_id, out_path))
        qtd = len(conj_armadilhas)
        pct = round((qtd / ordem_est * 100.0) if ordem_est else 0.0, 2)
        info_armadilhas = {"quantidade": qtd, "total_estados": ordem_est, "percentual": pct}

    if interactive:
        arquivos_gerados.append(
            _gerar_html_interativo(
                caminho,
                mapa_id,
                arestas_geradas,
                camadas,
                inicio,
                fim,
                out_path,
                alg_inicial=alg,
                fonte_consumivel=fonte_consumivel,
            )
        )

    # Modo completo para mapa único quando nenhuma flag específica de ação é passada
    if alg is None and not armadilhas and not interactive:
        linhas_solucoes = []
        resultados_por_alg = {}
        for nome_alg in ("BFS", "DIJKSTRA", "BELLMAN_FORD"):
            res_item, bf_ciclo_item, est_por_no_item, _ = _executar_algoritmo_unico_parte1(
                nome_alg,
                arestas_geradas,
                camadas,
                inicio,
                fim,
                mapa_id,
                caminho,
                fonte_consumivel=False,
            )
            resultados_por_alg[nome_alg] = res_item
            status_item = res_item["status"]
            if status_item == "OK":
                linhas_solucoes.append([
                    mapa_id,
                    nome_alg,
                    res_item["passos"],
                    res_item["custo_total"],
                    status_item,
                    " -> ".join(res_item["caminho"]),
                ])
            else:
                linhas_solucoes.append([mapa_id, nome_alg, "", "", status_item, ""])

            if nome_alg == "DIJKSTRA" and status_item == "OK":
                arquivos_gerados.append(
                    _salvar_percurso_json(
                        out_path,
                        mapa_id,
                        caminho,
                        "DIJKSTRA",
                        res_item["custo_total"],
                        res_item["estados"],
                    )
                )
            if nome_alg == "BELLMAN_FORD" and status_item == "CICLO_NEGATIVO":
                arquivos_gerados.append(
                    _salvar_ciclo_negativo_json(
                        out_path, mapa_id, caminho, True, bf_ciclo_item, est_por_no_item
                    )
                )

        solucoes_mapa_path = out_path / f"solucoes_{mapa_id}.csv"
        with open(solucoes_mapa_path, "w", newline="", encoding="utf-8") as f:
            escritor = csv.writer(f)
            escritor.writerow(["mapa", "algoritmo", "passos", "custo", "status", "caminho"])
            escritor.writerows(linhas_solucoes)
        arquivos_gerados.append(solucoes_mapa_path)

        res_dfs, _, _, _ = _executar_algoritmo_unico_parte1(
            "DFS", arestas_geradas, camadas, inicio, fim, mapa_id, caminho
        )
        resultados_por_alg["DFS"] = res_dfs
        contagem_dfs = res_dfs["contagem"]
        dfs_mapa_path = out_path / f"dfs_classificacao_{mapa_id}.csv"
        with open(dfs_mapa_path, "w", newline="", encoding="utf-8") as f:
            escritor = csv.writer(f)
            escritor.writerow(["mapa", "arvore", "retorno", "avanco", "cruzamento"])
            escritor.writerow([
                mapa_id,
                contagem_dfs["arvore"],
                contagem_dfs["retorno"],
                contagem_dfs["avanco"],
                contagem_dfs["cruzamento"],
            ])
        arquivos_gerados.append(dfs_mapa_path)

        conj_armadilhas = bfs_estados_armadilha(arestas_geradas, camadas)
        arquivos_gerados.append(_exportar_armadilhas_csv(conj_armadilhas, labirinto, mapa_id, out_path))
        qtd_arm = len(conj_armadilhas)
        pct_arm = round((qtd_arm / ordem_est * 100.0) if ordem_est else 0.0, 2)
        info_armadilhas = {"quantidade": qtd_arm, "total_estados": ordem_est, "percentual": pct_arm}

        metricas_mapa_path = out_path / f"metricas_{mapa_id}.json"
        with open(metricas_mapa_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "mapa": mapa_id,
                    "arquivo": caminho.name,
                    "G_pos": {
                        "ordem": labirinto.metricas.ordem,
                        "tamanho": labirinto.metricas.tamanho,
                        "densidade": labirinto.metricas.densidade,
                    },
                    "G_est": {
                        "ordem": ordem_est,
                        "tamanho": tamanho_est,
                        "densidade": (
                            tamanho_est / (ordem_est * (ordem_est - 1)) if ordem_est >= 2 else 0.0
                        ),
                    },
                    "num_camadas": len(camadas),
                    "armadilhas": info_armadilhas,
                    "solucoes": {
                        k: {
                            "status": v.get("status"),
                            "passos": v.get("passos"),
                            "custo_total": v.get("custo_total"),
                        }
                        for k, v in resultados_por_alg.items()
                        if k != "DFS"
                    },
                    "dfs": {
                        "tem_ciclo": res_dfs["tem_ciclo"],
                        "contagem": contagem_dfs,
                    },
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        arquivos_gerados.append(metricas_mapa_path)
        resultado_alg = resultados_por_alg

    return {
        "mapa": mapa_id,
        "arquivo": caminho.name,
        "ordem_pos": labirinto.metricas.ordem,
        "tamanho_pos": labirinto.metricas.tamanho,
        "ordem_est": ordem_est,
        "tamanho_est": tamanho_est,
        "num_camadas": len(camadas),
        "resultado_alg": resultado_alg,
        "armadilhas": info_armadilhas,
        "arquivos_gerados": arquivos_gerados,
    }
