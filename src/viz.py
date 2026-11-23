"""Exportação de dados e imagens da exploração do labirinto."""

import csv
import os

from src.graphs.estados import formatar_estado


def exportar_arestas(lista_arestas, nome_mapa):

    diretorio = "out/parte1"

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

        for origem, destino, movimento, peso in lista_arestas:

            escritor.writerow([
                formatar_estado(origem),
                formatar_estado(destino),
                movimento,
                destino.no_pos.tipo,
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
