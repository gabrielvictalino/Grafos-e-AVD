"""Execução de algoritmos e benchmark do dataset da Parte 2."""

import csv
import json
import math
import re
import time
from pathlib import Path

from src.graphs.algorithms import (
    bellman_ford,
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


def exportar_parte1(entrada_mapas: str | Path = "mapas", out_dir: str | Path = "out/parte1") -> list[Path]:
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
            estados_percurso = []
            custo_acum = 0
            for idx, no in enumerate(caminho_real_dijk):
                est = estado_por_no[no]
                if idx == 0:
                    movimento = None
                    custo_passo = 0
                else:
                    movimento, custo_passo = encontrar_aresta(caminho_real_dijk[idx - 1], no)
                    custo_acum += custo_passo
                estados_percurso.append({
                    "passo": idx,
                    "estado": formatar_estado(est),
                    "linha": est.no_pos.posicao_linha,
                    "coluna": est.no_pos.posicao_coluna,
                    "casa": est.no_pos.tipo,
                    "chaves": est.chaves or "-",
                    "bonus": sorted(getattr(est, "bonus", frozenset())),
                    "movimento": movimento,
                    "custo_passo": custo_passo,
                    "custo_acumulado": custo_acum,
                })
            percurso_path = out_path / "percurso_m03.json"
            with open(percurso_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "mapa": mapa_id,
                        "arquivo": mapa_path.name,
                        "algoritmo": "DIJKSTRA",
                        "status": "OK",
                        "passos": len(caminho_real_dijk) - 1,
                        "custo_total": d_dist[alvo],
                        "estados": estados_percurso,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            arquivos_gerados.append(percurso_path)

        # 6) ciclo_negativo_m06.json
        if mapa_id == "m06":
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
            ciclo_path = out_path / "ciclo_negativo_m06.json"
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
            arquivos_gerados.append(ciclo_path)

        # 7) armadilhas_m04.csv e armadilhas_m07.csv
        if mapa_id in ("m04", "m07"):
            armadilhas = bfs_estados_armadilha(arestas_geradas, camadas)
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
