"""Gera gráficos de comparação a partir do relatório de benchmark da Parte 2."""

import argparse
import json
from pathlib import Path


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera gráficos do benchmark da Parte 2.")
    parser.add_argument("relatorio", help="Caminho para parte2_report.json")
    parser.add_argument("--out", default="out/parte2", help="Diretório para salvar os gráficos")
    args = parser.parse_args()

    for caminho in gerar_graficos_parte2(args.relatorio, args.out):
        print(f"[OK] Gráfico salvo em {caminho}")


if __name__ == "__main__":
    main()
