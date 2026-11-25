"""Exportação de dados e imagens da exploração do labirinto."""

import argparse
import csv
import json
import os
from pathlib import Path

from src.graphs.estados import formatar_estado

def exportar_arestas(lista_arestas, nome_mapa, diretorio="out/parte1"):

    os.makedirs(diretorio, exist_ok=True)

    caminho_arquivo = os.path.join(
        diretorio,
        f"arestas_{nome_mapa}.csv"
    )

    with open(
        caminho_arquivo,
        "w",
        newline="",
        encoding="utf-8"
    ) as arquivo:

        escritor = csv.writer(arquivo)

        escritor.writerow([
            "origem",
            "destino",
            "movimento",
            "casa_destino",
            "peso"
        ])

        for origem, destino, movimento, casa_destino, peso in lista_arestas:
            if destino == "ALVO":
                continue

            escritor.writerow([
                formatar_estado(origem),
                formatar_estado(destino),
                movimento,
                casa_destino,
                peso
            ])

    return caminho_arquivo


def exportar_heatmap(heatmap, nome_mapa):
    import matplotlib.pyplot as plt

    os.makedirs("out/parte1", exist_ok=True)

    # Converte None (paredes) para NaN
    matriz = [
        [float("nan") if valor is None else valor for valor in linha]
        for linha in heatmap
    ]

    fig, ax = plt.subplots(figsize=(10, 8))

    imagem = ax.imshow(
        matriz,
        cmap="hot",
        interpolation="nearest",
        vmin=0
    )

    ax.set_title("Heatmap de estados por posição")
    ax.set_xlabel("Coluna")
    ax.set_ylabel("Linha")

    fig.colorbar(
        imagem,
        ax=ax,
        label="Quantidade de estados"
    )

    caminho = f"out/parte1/heatmap_{nome_mapa}.png"

    fig.savefig(
        caminho,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(fig)

    return caminho


def carregar_relatorio_parte2(caminho: str | Path) -> list[dict]:
    """Lê e valida as escalas gravadas pelo benchmark da Parte 2."""
    with Path(caminho).open(encoding="utf-8") as arquivo:
        relatorio = json.load(arquivo)

    escalas = relatorio.get("escalabilidade")
    if not isinstance(escalas, list) or not escalas:
        raise ValueError("O relatório precisa conter uma lista 'escalabilidade' não vazia.")

    for escala in escalas:
        if not {"escala", "vertices", "algoritmos"} <= escala.keys():
            raise ValueError("Cada escala precisa conter 'escala', 'vertices' e 'algoritmos'.")

    return escalas


def gerar_graficos_parte2(
    relatorio: str | Path,
    diretorio_saida: str | Path = "out/parte2",
) -> tuple[Path, Path]:
    """Salva comparação por escala em barras e escalabilidade em linhas."""
    escalas = carregar_relatorio_parte2(relatorio)
    import matplotlib.pyplot as plt

    saida = Path(diretorio_saida)
    saida.mkdir(parents=True, exist_ok=True)

    nomes_algoritmos = list(escalas[0]["algoritmos"])
    rotulos = [str(item["escala"]) for item in escalas]
    medias = {
        nome: [item["algoritmos"][nome]["tempo_medio_ms"] for item in escalas]
        for nome in nomes_algoritmos
    }

    figura, eixo = plt.subplots(figsize=(10, 6))
    largura = 0.8 / len(nomes_algoritmos)
    posicoes = list(range(len(rotulos)))
    for indice, nome in enumerate(nomes_algoritmos):
        deslocamento = (indice - (len(nomes_algoritmos) - 1) / 2) * largura
        eixo.bar(
            [posicao + deslocamento for posicao in posicoes],
            medias[nome],
            width=largura,
            label=nome,
        )
    eixo.set_xticks(posicoes)
    eixo.set_xticklabels(rotulos)
    eixo.set_xlabel("Tamanho do dataset")
    eixo.set_ylabel("Tempo médio (ms)")
    eixo.set_title("Comparação de tempo por algoritmo")
    eixo.legend(title="Algoritmo")
    eixo.grid(axis="y", alpha=0.25)
    figura.tight_layout()
    caminho_barras = saida / "comparacao_algoritmos_barras.png"
    figura.savefig(caminho_barras, dpi=200)
    plt.close(figura)

    figura, eixo = plt.subplots(figsize=(10, 6))
    vertices = [item["vertices"] for item in escalas]
    for nome in nomes_algoritmos:
        eixo.plot(vertices, medias[nome], marker="o", label=nome)
    eixo.set_xlabel("Número de vértices")
    eixo.set_ylabel("Tempo médio (ms)")
    eixo.set_title("Escalabilidade dos algoritmos")
    eixo.legend(title="Algoritmo")
    eixo.grid(True, alpha=0.25)
    figura.tight_layout()
    caminho_linhas = saida / "escalabilidade_algoritmos_linhas.png"
    figura.savefig(caminho_linhas, dpi=200)
    plt.close(figura)

    return caminho_barras, caminho_linhas


# [IA] Claude – histogramas de grau de entrada e de saída do grafo TMDB (só sintaxe matplotlib; a leitura dos gráficos é da equipe)
def calcular_graus(lista_nos) -> tuple[list[int], list[int]]:
    """Retorna (graus_de_entrada, graus_de_saida), um valor por vértice, na ordem de lista_nos."""
    entrada = {no.id: 0 for no in lista_nos}
    for no in lista_nos:
        for aresta in no.lista_arestas:
            entrada[aresta.destino.id] += 1
    return [entrada[no.id] for no in lista_nos], [len(no.lista_arestas) for no in lista_nos]


def gerar_histogramas_grau(dataset: str | Path, diretorio_saida: str | Path = "out/parte2") -> tuple[Path, Path]:
    """Salva os histogramas de grau de entrada e de grau de saída (eixo y em escala log)."""
    import matplotlib.pyplot as plt
    from src.graphs.io import carregar_grafo_tmdb

    lista_nos, _ = carregar_grafo_tmdb(dataset)
    graus_entrada, graus_saida = calcular_graus(lista_nos)
    saida = Path(diretorio_saida)
    saida.mkdir(parents=True, exist_ok=True)

    caminhos = []
    for nome, graus, cor in (("entrada", graus_entrada, "#4c6ef5"), ("saida", graus_saida, "#e8590c")):
        rotulo = "entrada" if nome == "entrada" else "saída"
        figura, eixo = plt.subplots(figsize=(10, 6))
        eixo.hist(graus, bins=range(0, max(graus) + 2), color=cor)
        eixo.set_yscale("log")
        eixo.set_xlabel(f"Grau de {rotulo}")
        eixo.set_ylabel("Número de vértices (escala log)")
        eixo.set_title(f"Distribuição do grau de {rotulo} ({len(graus)} vértices, máx. {max(graus)})")
        eixo.grid(axis="y", alpha=0.25)
        figura.tight_layout()
        caminho = saida / f"histograma_grau_{nome}.png"
        figura.savefig(caminho, dpi=200)
        plt.close(figura)
        caminhos.append(caminho)
    return caminhos[0], caminhos[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera gráficos da Parte 2 (benchmark e graus).")
    parser.add_argument("relatorio", nargs="?", help="Caminho para parte2_report.json (gráficos do benchmark)")
    parser.add_argument("--graus", metavar="DATASET", help="Gera os histogramas de grau a partir do dataset limpo")
    parser.add_argument("--out", default="out/parte2", help="Diretório para salvar os gráficos")
    args = parser.parse_args()
    if not args.relatorio and not args.graus:
        parser.error("informe o relatório do benchmark e/ou --graus DATASET")

    if args.relatorio:
        for caminho in gerar_graficos_parte2(args.relatorio, args.out):
            print(f"[OK] Gráfico salvo em {caminho}")
    if args.graus:
        for caminho in gerar_histogramas_grau(args.graus, args.out):
            print(f"[OK] Gráfico salvo em {caminho}")


if __name__ == "__main__":
    main()
