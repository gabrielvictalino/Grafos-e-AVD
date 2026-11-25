"""Gráficos da Parte 2 (AVD): evolução das notas dos atores, receita, idioma e produtoras.

Uso:
    python -m src.graficos_atores --bruto caminho/TMDB_all_movies.csv --out out/parte2

O dataset limpo (tmdb_limpo.csv.gz) só tem id, título, data, elenco e nota. Revenue,
idioma original e produtoras vêm do dataset bruto, ligado pelo `id`.
Sem --bruto, só os três primeiros gráficos são gerados.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

LIMPO_PADRAO = "data/dataset_parte2/tmdb_limpo.csv.gz"
MIN_FILMES_VARIACAO = 10    # atores com menos filmes não entram no ranking de variação
MIN_FILMES_CONSTANCIA = 20  # desvio padrão só é estável com amostra maior
MIN_FILMES_COM_RECEITA = 3  # filmes com revenue > 0 para calcular a receita típica do ator
TOP_N = 15


def carregar_filmes(limpo: str | Path, bruto: str | Path | None = None) -> pd.DataFrame:
    filmes = pd.read_csv(limpo)
    filmes["release_date"] = pd.to_datetime(filmes["release_date"], errors="coerce")
    filmes = filmes.dropna(subset=["release_date", "imdb_rating", "cast"]).drop_duplicates("id")
    if bruto is not None:
        extras = pd.read_csv(
            bruto,
            usecols=["id", "revenue", "original_language", "production_companies"],
            low_memory=False,
        ).drop_duplicates("id")
        filmes = filmes.merge(extras, on="id", how="left")
    return filmes


def atores_por_filme(filmes: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por par (ator, filme), em ordem cronológica."""
    colunas = [c for c in ("id", "release_date", "imdb_rating", "revenue") if c in filmes]
    longo = filmes[colunas].assign(ator=filmes["cast"].str.split(","))
    longo = longo.explode("ator")
    longo["ator"] = longo["ator"].str.strip()
    longo = longo[longo["ator"] != ""].drop_duplicates(["ator", "id"])
    return longo.sort_values(["ator", "release_date", "id"]).reset_index(drop=True)


def variacao_por_ator(longo: pd.DataFrame, minimo: int = MIN_FILMES_VARIACAO) -> pd.DataFrame:
    """Variação = nota média da 2ª metade da carreira − nota média da 1ª metade.

    Os filmes do ator são ordenados por data; com quantidade ímpar o filme do meio fica de fora.
    """
    posicao = longo.groupby("ator").cumcount()
    total = longo.groupby("ator")["id"].transform("size")
    metade = total // 2
    primeira = longo[posicao < metade]
    segunda = longo[posicao >= total - metade]
    tabela = pd.DataFrame({
        "nota_inicio": primeira.groupby("ator")["imdb_rating"].mean(),
        "nota_fim": segunda.groupby("ator")["imdb_rating"].mean(),
        "filmes": longo.groupby("ator")["id"].size(),
    })
    tabela = tabela[tabela["filmes"] >= minimo].copy()
    tabela["variacao"] = tabela["nota_fim"] - tabela["nota_inicio"]
    return tabela.sort_values("variacao")


def _salvar(figura, caminho: Path) -> Path:
    figura.tight_layout()
    figura.savefig(caminho, dpi=200)
    import matplotlib.pyplot as plt
    plt.close(figura)
    return caminho


def grafico_barras_variacao(tabela: pd.DataFrame, saida: Path, aumentaram: bool) -> Path:
    import matplotlib.pyplot as plt

    destaque = tabela.tail(TOP_N) if aumentaram else tabela.head(TOP_N)
    destaque = destaque.sort_values("variacao", ascending=not aumentaram)
    cor = "#2b8a3e" if aumentaram else "#c92a2a"
    figura, eixo = plt.subplots(figsize=(10, 7))
    rotulos = [f"{ator} ({int(f)} filmes)" for ator, f in zip(destaque.index, destaque["filmes"])]
    eixo.barh(rotulos, destaque["variacao"], color=cor)
    eixo.invert_yaxis()
    eixo.set_xlabel("Variação da nota média (2ª metade − 1ª metade da carreira)")
    eixo.set_title(f"Atores cujas notas mais {'aumentaram' if aumentaram else 'diminuíram'} "
                   f"(mín. {MIN_FILMES_VARIACAO} filmes)")
    eixo.grid(axis="x", alpha=0.25)
    nome = "atores_notas_aumentaram_barras.png" if aumentaram else "atores_notas_diminuiram_barras.png"
    return _salvar(figura, saida / nome)


def grafico_boxplot_constancia(longo: pd.DataFrame, saida: Path) -> Path:
    import matplotlib.pyplot as plt

    resumo = longo.groupby("ator")["imdb_rating"].agg(["std", "size"])
    resumo = resumo[resumo["size"] >= MIN_FILMES_CONSTANCIA].sort_values("std").head(TOP_N)
    dados = [longo.loc[longo["ator"] == ator, "imdb_rating"] for ator in resumo.index]
    rotulos = [f"{ator}\n(dp {std:.2f}, n={n})" for ator, std, n in zip(resumo.index, resumo["std"], resumo["size"])]
    figura, eixo = plt.subplots(figsize=(10, 8))
    eixo.boxplot(dados, tick_labels=rotulos, orientation="horizontal", patch_artist=True,
                 boxprops={"facecolor": "#a5d8ff"}, medianprops={"color": "#1c1c1c"})
    eixo.invert_yaxis()
    eixo.set_xlabel("imdb_rating dos filmes")
    eixo.set_title(f"Atores mais constantes: menor desvio padrão das notas (mín. {MIN_FILMES_CONSTANCIA} filmes)")
    eixo.grid(axis="x", alpha=0.25)
    return _salvar(figura, saida / "atores_mais_constantes_boxplot.png")


def grafico_dispersao_receita(longo: pd.DataFrame, tabela: pd.DataFrame, saida: Path) -> tuple[Path, float, int]:
    import matplotlib.pyplot as plt

    com_receita = longo[longo["revenue"] > 0]
    receita = com_receita.groupby("ator")["revenue"].agg(receita_mediana="median", filmes_com_receita="size")
    dados = tabela.join(receita, how="inner")
    dados = dados[dados["filmes_com_receita"] >= MIN_FILMES_COM_RECEITA]
    x, y = dados["variacao"], np.log10(dados["receita_mediana"])
    correlacao = float(dados["variacao"].corr(dados["receita_mediana"], method="spearman"))
    angular, linear = np.polyfit(x, y, 1)

    figura, eixo = plt.subplots(figsize=(10, 7))
    eixo.scatter(x, y, s=5, alpha=0.15, color="#4c6ef5", linewidths=0, label="Atores")
    maiores = dados.nlargest(TOP_N, "variacao")
    eixo.scatter(maiores["variacao"], np.log10(maiores["receita_mediana"]), s=34, color="#2b8a3e",
                 label=f"{TOP_N} que mais aumentaram")
    # Legenda dos destaques em ordem decrescente de receita, deslocada na vertical para não sobrepor
    ordenados = maiores.sort_values("receita_mediana", ascending=False)
    limites_y = eixo.get_ylim()
    passo = (limites_y[1] - limites_y[0]) / (TOP_N + 4)
    for posicao, (ator, linha) in enumerate(ordenados.iterrows()):
        eixo.annotate(ator, (linha["variacao"], np.log10(linha["receita_mediana"])), fontsize=7,
                      xytext=(x.max() + 0.25, limites_y[1] - (posicao + 1) * passo), textcoords="data",
                      va="center", arrowprops={"arrowstyle": "-", "color": "#2b8a3e", "lw": 0.6, "alpha": 0.7})
    eixo.set_xlim(x.min() - 0.1, x.max() + 1.6)
    xs = np.linspace(x.min(), x.max(), 100)
    eixo.plot(xs, angular * xs + linear, color="#e8590c", linewidth=2, label="Linha de tendência")
    eixo.set_xlabel("Variação da nota média do ator (2ª metade − 1ª metade da carreira)")
    eixo.set_ylabel("Receita mediana dos filmes do ator (log10 US$)")
    eixo.set_title(f"Variação das notas × receita dos filmes (Spearman = {correlacao:.2f}, n = {len(dados)} atores)")
    eixo.legend()
    eixo.grid(alpha=0.25)
    return _salvar(figura, saida / "atores_variacao_x_revenue_dispersao.png"), correlacao, len(dados)


def _boxplot_por_categoria(df: pd.DataFrame, coluna: str, titulo: str, rotulo_x: str,
                           nome_arquivo: str, saida: Path, top: int, minimo: int = 1) -> Path:
    import matplotlib.pyplot as plt

    contagem = df[coluna].value_counts()
    categorias = contagem[contagem >= minimo].head(top).index
    ordem = df[df[coluna].isin(categorias)].groupby(coluna)["imdb_rating"].median().sort_values(ascending=False).index
    dados = [df.loc[df[coluna] == c, "imdb_rating"] for c in ordem]
    rotulos = [f"{c}\n(n={contagem[c]})" for c in ordem]
    figura, eixo = plt.subplots(figsize=(13, 7))
    eixo.boxplot(dados, tick_labels=rotulos, patch_artist=True, flierprops={"markersize": 2, "alpha": 0.3},
                 boxprops={"facecolor": "#ffd8a8"}, medianprops={"color": "#1c1c1c"})
    eixo.set_xlabel(rotulo_x)
    eixo.set_ylabel("imdb_rating")
    eixo.set_title(titulo)
    eixo.grid(axis="y", alpha=0.25)
    plt.setp(eixo.get_xticklabels(), rotation=45 if len(ordem) > 10 else 0, ha="right" if len(ordem) > 10 else "center")
    return _salvar(figura, saida / nome_arquivo)


def grafico_idioma(filmes: pd.DataFrame, saida: Path, top: int = 12) -> Path:
    base = filmes.dropna(subset=["original_language"])
    return _boxplot_por_categoria(
        base, "original_language",
        f"imdb_rating por idioma original (os {top} idiomas com mais filmes)",
        "original_language", "imdb_rating_x_original_language_boxplot.png", saida, top)


def grafico_produtoras(filmes: pd.DataFrame, saida: Path, top: int = 15, minimo: int = 100) -> Path:
    base = filmes.dropna(subset=["production_companies"])[["imdb_rating", "production_companies"]].copy()
    base["produtora"] = base["production_companies"].str.split(",")
    base = base.explode("produtora")
    base["produtora"] = base["produtora"].str.strip()
    base = base[base["produtora"] != ""]
    return _boxplot_por_categoria(
        base, "produtora",
        f"imdb_rating por produtora (as {top} com mais filmes)",
        "production_companies", "imdb_rating_x_production_companies_boxplot.png", saida, top, minimo)


def gerar_graficos_atores(limpo: str | Path = LIMPO_PADRAO, bruto: str | Path | None = None,
                          diretorio_saida: str | Path = "out/parte2") -> list[Path]:
    saida = Path(diretorio_saida)
    saida.mkdir(parents=True, exist_ok=True)
    filmes = carregar_filmes(limpo, bruto)
    longo = atores_por_filme(filmes)
    tabela = variacao_por_ator(longo)

    caminhos = [
        grafico_barras_variacao(tabela, saida, aumentaram=False),
        grafico_barras_variacao(tabela, saida, aumentaram=True),
        grafico_boxplot_constancia(longo, saida),
    ]
    if bruto is None:
        print("[AVISO] Sem --bruto: dispersão de revenue, idioma e produtoras não foram gerados.")
        return caminhos

    caminho, correlacao, n = grafico_dispersao_receita(longo, tabela, saida)
    print(f"[INFO] Spearman(variação da nota, receita mediana) = {correlacao:.3f} em {n} atores")
    caminhos += [caminho, grafico_idioma(filmes, saida), grafico_produtoras(filmes, saida)]
    return caminhos


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera os gráficos de atores da Parte 2.")
    parser.add_argument("--limpo", default=LIMPO_PADRAO, help="CSV limpo (id, title, release_date, cast, imdb_rating)")
    parser.add_argument("--bruto", default=None, help="TMDB_all_movies.csv (revenue, original_language, production_companies)")
    parser.add_argument("--out", default="out/parte2", help="Diretório de saída")
    args = parser.parse_args()
    for caminho in gerar_graficos_atores(args.limpo, args.bruto, args.out):
        print(f"[OK] Gráfico salvo em {caminho}")


if __name__ == "__main__":
    main()
