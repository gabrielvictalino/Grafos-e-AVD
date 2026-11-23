# [IA] Gemini Interface de linha de comando (CLI) conectada ao src/solve.py
# [IA] Antigravity (Gemini) – adiciona opção --exportar-parte1 para gerar os arquivos obrigatórios da Parte 1
import argparse
from pathlib import Path
from src.graphs.io import carregar_grafo_tmdb
from src.solve import executar_algoritmo_parte2, executar_benchmark_parte2, exportar_parte1


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
        print(f"[INFO] Executando Parte 1 para o mapa: {args.mapa}")


if __name__ == "__main__":
    main()