# [IA] Gemini Interface de linha de comando (CLI) conectada ao src/solve.py
# [IA] Antigravity (Gemini) – adiciona --exportar-parte1 e conecta execução individual via --mapa na Parte 1
import argparse
from pathlib import Path
from src.graphs.io import carregar_grafo_tmdb
from src.solve import (
    executar_algoritmo_parte2,
    executar_benchmark_parte2,
    executar_mapa_parte1,
    exportar_parte1,
)


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Projeto Final - Teoria dos Grafos + AVD (2026.2)"
    )

    entrada = parser.add_mutually_exclusive_group(required=True)
    entrada.add_argument("--mapa", type=str, help="Caminho do mapa (.txt) da Parte 1")
    entrada.add_argument("--dataset", type=str, help="Caminho da pasta ou CSV da Parte 2")
    entrada.add_argument(
        "--exportar-parte1",
        nargs="?",
        const="mapas",
        type=str,
        help="Exporta todos os arquivos obrigatórios da Parte 1 a partir da pasta de mapas (padrão: mapas)",
    )

    parser.add_argument(
        "--alg",
        type=str,
        choices=["BFS", "DFS", "DIJKSTRA", "BELLMAN_FORD"],
        help="Algoritmo de busca/caminho mínimo",
    )
    parser.add_argument("--source", type=str, help="Vértice de origem (ID do filme na Parte 2)")
    parser.add_argument("--target", type=str, help="Vértice de destino (ID do filme na Parte 2)")

    parser.add_argument("--benchmark", action="store_true", help="Executa benchmark e escalabilidade (Parte 2)")
    parser.add_argument("--fonte-consumivel", action="store_true", help="Torna '*' consumível (Parte 1)")
    parser.add_argument("--armadilhas", action="store_true", help="Identifica estados-armadilha (Parte 1)")
    parser.add_argument("--interactive", action="store_true", help="Gera visualização interativa (Parte 1)")

    parser.add_argument("--out", type=str, required=True, help="Diretório de saída")
    return parser


def main() -> None:
    parser = criar_parser()
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.dataset:
        if args.fonte_consumivel or args.armadilhas or args.interactive:
            parser.error(
                "--fonte-consumivel, --armadilhas e --interactive são válidos apenas com --mapa."
            )
        if args.benchmark:
            executar_benchmark_parte2(args.dataset, out_dir)
        elif args.alg:
            if not args.source:
                parser.error("--source é obrigatório ao usar --alg com --dataset.")
            
            modo_peso = "nao_negativo" if args.alg == "DIJKSTRA" else "original"
            lista_nos, mapa_nos = carregar_grafo_tmdb(args.dataset, transformacao_peso=modo_peso)
            
            if args.source not in mapa_nos:
                raise ValueError(f"Vértice de origem '{args.source}' não encontrado no grafo.")
            if args.target and args.target not in mapa_nos:
                raise ValueError(f"Vértice de destino '{args.target}' não encontrado no grafo.")

            executar_algoritmo_parte2(lista_nos, mapa_nos, args.alg, args.source, args.target, out_dir)
        else:
            parser.error("Informe --alg ou --benchmark para --dataset.")

    elif args.exportar_parte1 is not None:
        arquivos = exportar_parte1(args.exportar_parte1, out_dir)
        print(f"[OK] {len(arquivos)} arquivos exportados em {out_dir}:")
        for arq in arquivos:
            print(f"  - {arq}")

    elif args.mapa:
        # [IA] Antigravity (Gemini) – orquestração dos comandos individuais da Parte 1 via --mapa
        if args.benchmark or args.source or args.target:
            parser.error("--benchmark, --source e --target são válidos apenas com --dataset.")

        alg = args.alg
        if args.fonte_consumivel:
            if alg is not None and alg != "BELLMAN_FORD":
                parser.error("--fonte-consumivel só pode ser usado com --alg BELLMAN_FORD.")
            if alg is None:
                alg = "BELLMAN_FORD"

        resumo = executar_mapa_parte1(
            args.mapa,
            out_dir,
            alg=alg,
            fonte_consumivel=args.fonte_consumivel,
            armadilhas=args.armadilhas,
            interactive=args.interactive,
        )
        print(
            f"[OK] Mapa {resumo['mapa']} ({resumo['arquivo']}): "
            f"G_pos=({resumo['ordem_pos']}V, {resumo['tamanho_pos']}E), "
            f"G_est=({resumo['ordem_est']}V, {resumo['tamanho_est']}E, {resumo['num_camadas']} camadas)"
        )

        res_alg = resumo.get("resultado_alg")
        if alg and isinstance(res_alg, dict):
            status = res_alg.get("status")
            if alg == "DFS":
                print(
                    f"  - DFS: status={status}, tem_ciclo={res_alg.get('tem_ciclo')}, "
                    f"contagem={res_alg.get('contagem')}"
                )
            elif status == "OK":
                extra = " (fonte * consumível)" if res_alg.get("fonte_consumivel") else ""
                print(
                    f"  - {alg}{extra}: status=OK, passos={res_alg.get('passos')}, "
                    f"custo={res_alg.get('custo_total')}, tempo={res_alg.get('tempo_ms')} ms"
                )
            elif status == "CICLO_NEGATIVO":
                print(
                    f"  - {alg}: status=CICLO_NEGATIVO, custo_ciclo={res_alg.get('custo_ciclo')}, "
                    f"ciclo={' -> '.join(res_alg.get('ciclo_estados', []))}"
                )
            else:
                motivo = f" ({res_alg.get('motivo')})" if res_alg.get("motivo") else ""
                print(f"  - {alg}: status={status}{motivo}")
        elif isinstance(res_alg, dict):
            for nome_alg, dados in res_alg.items():
                if nome_alg == "DFS":
                    print(
                        f"  - DFS: tem_ciclo={dados.get('tem_ciclo')}, contagem={dados.get('contagem')}"
                    )
                else:
                    print(
                        f"  - {nome_alg}: status={dados.get('status')}, "
                        f"passos={dados.get('passos')}, custo={dados.get('custo_total')}"
                    )

        if resumo.get("armadilhas") is not None:
            arm = resumo["armadilhas"]
            print(
                f"  - Armadilhas: {arm['quantidade']} de {arm['total_estados']} estados "
                f"({arm['percentual']}%)"
            )

        print(f"[OK] {len(resumo['arquivos_gerados'])} arquivos gerados em {out_dir}:")
        for arq in resumo["arquivos_gerados"]:
            print(f"  - {arq}")
        if args.interactive:
            print("[DICA] Você também pode abrir o app Streamlit com: streamlit run app.py")


if __name__ == "__main__":
    main()