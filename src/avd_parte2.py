"""Gera as visualizações de AVD da Parte 2 em out/parte2/ (python -m src.avd_parte2)."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.graphs.io import _ler_dataframe_tmdb

DATASET = Path("data/dataset_parte2/tmdb_limpo.csv.gz")
OUT = Path("out/parte2")
CINZA, VERMELHO, AZUL = "#9e9e9e", "#d62728", "#1f77b4"


def arestas_consecutivas(df: pd.DataFrame) -> pd.DataFrame:
    """Mesma regra de io.carregar_grafo_tmdb(modo_arestas='consecutivo'), em pandas."""
    notas = df["imdb_rating"].astype(float).to_numpy()
    datas = df["release_date"].to_numpy()
    anos = df["release_date"].dt.year.to_numpy()
    ator_idx: dict[str, list[int]] = {}
    for idx, elenco in enumerate(df["cast"]):
        for ator in str(elenco).split(","):
            if ator.strip():
                ator_idx.setdefault(ator.strip(), []).append(idx)
    vistos: set[tuple[int, int]] = set()
    origem, destino = [], []
    for ind in ator_idx.values():
        for i, j in zip(ind, ind[1:]):
            if datas[i] >= datas[j] or (i, j) in vistos:
                continue
            vistos.add((i, j))
            origem.append(i)
            destino.append(j)
    o, d = np.array(origem), np.array(destino)
    return pd.DataFrame({"peso": np.round(notas[d] - notas[o], 4), "nota_destino": notas[d], "ano_destino": anos[d]})


def salvar(fig, nome):
    fig.tight_layout()
    fig.savefig(OUT / nome, dpi=150)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = _ler_dataframe_tmdb(DATASET)
    ar = arestas_consecutivas(df)
    stats = {"filmes": len(df), "arestas": len(ar)}

    # E3 — distribuição de imdb_rating
    nota = df["imdb_rating"].astype(float)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(nota, bins=np.arange(1, 10.1, 0.25), color=AZUL, edgecolor="white")
    ax.axvline(nota.mean(), color="black", ls="--", label=f"Média = {nota.mean():.2f}")
    ax.axvline(nota.median(), color=VERMELHO, ls=":", lw=2, label=f"Mediana = {nota.median():.2f}")
    ax.set(title="Distribuição das notas IMDb dos filmes do grafo", xlabel="Nota IMDb (imdb_rating)", ylabel="Nº de filmes")
    ax.legend()
    salvar(fig, "avd_e3_distribuicao_imdb_rating.png")
    stats["nota"] = {"media": nota.mean(), "mediana": nota.median(), "assimetria": float(nota.skew())}

    # E4 — distribuição dos pesos (Δ nota)
    fig, ax = plt.subplots(figsize=(9, 5))
    bins = np.arange(-9, 9.01, 0.25)
    cnt, edges = np.histogram(ar["peso"], bins=bins)
    cores = [VERMELHO if e + 0.125 < 0 else AZUL for e in edges[:-1]]
    ax.bar(edges[:-1], cnt, width=0.25, align="edge", color=cores, edgecolor="white")
    ax.axvline(0, color="black", lw=1)
    ax.set(title="Distribuição da variação de nota entre filmes consecutivos de um mesmo ator",
           xlabel="Peso do arco = nota(filme posterior) − nota(filme anterior)", ylabel="Nº de arcos")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=VERMELHO), plt.Rectangle((0, 0), 1, 1, color=AZUL)],
              labels=["Queda de nota (peso < 0)", "Aumento ou igual (peso ≥ 0)"])
    salvar(fig, "avd_e4_distribuicao_pesos.png")
    stats["peso"] = {"media": ar["peso"].mean(), "mediana": ar["peso"].median(), "dp": ar["peso"].std(),
                     "abs_ate_1": float((ar["peso"].abs() <= 1).mean())}

    # X1 — sinal dos pesos (responde à pergunta)
    pos, neg, zero = (ar["peso"] > 0).mean(), (ar["peso"] < 0).mean(), (ar["peso"] == 0).mean()
    stats["sinal"] = {"positivo": pos, "negativo": neg, "zero": zero}
    fig, ax = plt.subplots(figsize=(9, 3.8))
    rotulos = ["Nota sobe", "Nota cai", "Nota igual"]
    vals = [pos * 100, neg * 100, zero * 100]
    barras = ax.barh(rotulos, vals, color=[CINZA, VERMELHO, CINZA])
    for b, v in zip(barras, vals):
        ax.text(v + 1, b.get_y() + b.get_height() / 2, f"{v:.1f}%", va="center", fontsize=12)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set(title="No próximo filme de um ator, a nota IMDb sobe e cai praticamente na mesma proporção",
           xlabel=f"% dos {len(ar):,} arcos do grafo".replace(",", "."))
    ax.spines[["top", "right"]].set_visible(False)
    salvar(fig, "avd_x1_sinal_variacao_nota.png")

    # X2 — variação média por década (sem tendência temporal)
    ar["decada"] = (ar["ano_destino"] // 10) * 10
    g = ar[ar["decada"] >= 1910].groupby("decada")["peso"].agg(["mean", "count",
                                                                 lambda s: (s < 0).mean()])
    g.columns = ["media", "n", "pct_neg"]
    g = g[g["n"] >= 1000]
    stats["decadas"] = g.round(4).reset_index().to_dict(orient="records")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.axhline(0, color="black", lw=1)
    ax.plot(g.index, g["media"], marker="o", color=AZUL, lw=2)
    ax.set_ylim(-1, 1)
    ax.set(title="A variação média de nota entre filmes de um ator não muda com a época",
           xlabel="Década de lançamento do filme posterior", ylabel="Variação média de nota IMDb (peso)")
    ax.annotate("0 = sem variação", xy=(g.index.min(), 0), xytext=(g.index.min(), -0.35), fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    salvar(fig, "avd_x2_variacao_por_decada.png")

    (OUT / "avd_parte2_stats.json").write_text(json.dumps(stats, indent=2, default=float), encoding="utf-8")
    print(json.dumps(stats, indent=2, default=float))


if __name__ == "__main__":
    main()
