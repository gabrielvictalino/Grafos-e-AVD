# [IA] Gemini Orquestração de execução única, reconstrução de caminho e benchmark de escalabilidade (Parte 2)
import json
import time
from pathlib import Path
from src.graphs.io import carregar_grafo_tmdb
from src.graphs.algorithms import dijkstra, bellman_ford, dfs  # inclua bfs quando criar


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
    if alg == "DIJKSTRA":
        distancias, anteriores = dijkstra(lista_nos, origem)
    elif alg == "BELLMAN_FORD":
        distancias, anteriores = bellman_ford(lista_nos, origem)
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
    with open(saida_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    print(f"[OK] {alg} concluído em {tempo_ms:.2f} ms. Salvo em: {saida_path}")
    return resultado


def executar_benchmark_parte2(dataset_path: str | Path, out_dir: Path, repeticoes: int = 5):
    """
    Roda os algoritmos em 3 escalas (10%, 50% e 100%) com média de 5 execuções
    e salva out/parte2/parte2_report.json.
    """
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
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Relatório consolidado salvo em {report_path}")