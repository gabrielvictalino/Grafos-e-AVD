
from itertools import combinations
from pathlib import Path
import pandas as pd
from src.graphs.graph import No

COLUNAS = ["id", "title", "release_date", "imdb_rating", "cast"]


def _ler_dataframe_tmdb(caminho: str | Path, limite_filmes: int | None = None) -> pd.DataFrame:
    """Lê o CSV limpo e ordena por (data, id)."""
    caminho = Path(caminho)
    if caminho.is_dir():
        arquivos = list(caminho.glob("*.csv*"))
        if not arquivos:
            raise FileNotFoundError(f"Nenhum CSV encontrado em {caminho}")
        caminho = arquivos[0]
    df = pd.read_csv(caminho, usecols=lambda c: c in COLUNAS, low_memory=False).dropna(subset=COLUNAS).copy()
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df = df.dropna(subset=["release_date"]).drop_duplicates(subset=["id"])
    df = df.sort_values(by=["release_date", "id"]).reset_index(drop=True)
    return df if limite_filmes is None else df.head(limite_filmes)


def contar_filmes_validos(caminho: str | Path) -> int:
    return len(_ler_dataframe_tmdb(caminho))


def _criar_nos(df: pd.DataFrame) -> tuple[list[No], dict[str, No]]:
    lista_nos = [No(id_no=str(r.id), titulo=str(r.title)) for r in df.itertuples(index=False)]
    return lista_nos, {no.id: no for no in lista_nos}


def carregar_grafo_tmdb(
    caminho: str | Path,
    limite_filmes: int | None = None,
    max_arestas: int | None = None,
    transformacao_peso: str = "original",
    modo_arestas: str = "todos_pares",
) -> tuple[list[No], dict[str, No]]:
    """
    Retorna (lista_nos, mapa_nos_por_id). Peso = nota(recente) - nota(antigo).
    transformacao_peso: "original" (pode ser negativo) | "nao_negativo" (+10, para Dijkstra).
    modo_arestas: "todos_pares" (todo par de filmes do ator; ~78M arestas em 100%) |
                  "consecutivo" (cada filme liga ao próximo do ator; ~3,9M em 100%).
    max_arestas: None = sem limite; se atingido, a construção para e imprime um aviso.
    """
    if modo_arestas not in ("todos_pares", "consecutivo"):
        raise ValueError(f"modo_arestas inválido: {modo_arestas!r}")
    df = _ler_dataframe_tmdb(caminho, limite_filmes)
    lista_nos, mapa_nos = _criar_nos(df)

    ator_para_indices: dict[str, list[int]] = {}
    for idx, elenco in enumerate(df["cast"]):
        for ator in str(elenco).split(","):
            if ator.strip():
                ator_para_indices.setdefault(ator.strip(), []).append(idx)

    ids = df["id"].astype(str).tolist()
    datas = df["release_date"].tolist()
    notas = df["imdb_rating"].astype(float).tolist()
    deslocamento = 10.0 if transformacao_peso == "nao_negativo" else 0.0  # nota ∈ [0,10] => diferença >= -10
    arestas_vistas: set[tuple[str, str]] = set()

    for indices in ator_para_indices.values():
        pares = zip(indices, indices[1:]) if modo_arestas == "consecutivo" else combinations(indices, 2)
        for i, j in pares:
            if datas[i] >= datas[j] or (ids[i], ids[j]) in arestas_vistas:
                continue
            arestas_vistas.add((ids[i], ids[j]))
            mapa_nos[ids[i]].adicionar_aresta(mapa_nos[ids[j]], round(notas[j] - notas[i] + deslocamento, 4))
            if max_arestas is not None and len(arestas_vistas) >= max_arestas:
                print(f"[AVISO] Grafo cortado em max_arestas={max_arestas:,}: está incompleto.")
                return lista_nos, mapa_nos

    return lista_nos, mapa_nos


def construir_caso_ciclo_negativo(
    caminho: str | Path, ano: int | None = None, n_filmes: int = 5, ajuste: float = -0.5
) -> tuple[list[No], dict[str, No]]:
    """
    Caso pequeno com ciclo negativo: os `n_filmes` primeiros filmes de `ano` (padrão: ano com mais
    filmes), ligados em todos os pares nos dois sentidos. Peso u->v = nota(v) - nota(u) + ajuste.
    Sem ajuste todo ciclo soma 0 (os termos se cancelam); com ajuste < 0 um ciclo de k arestas custa k*ajuste.
    """
    if n_filmes < 2 or ajuste >= 0:
        raise ValueError("n_filmes precisa ser >= 2 e ajuste negativo.")
    df = _ler_dataframe_tmdb(caminho)
    anos = df["release_date"].dt.year
    ano = int(anos.value_counts().idxmax()) if ano is None else ano
    recorte = df[anos == ano].head(n_filmes)
    if len(recorte) < 2:
        raise ValueError(f"Menos de 2 filmes em {ano}; escolha outro ano.")

    lista_nos, mapa_nos = _criar_nos(recorte)
    notas = {str(r.id): float(r.imdb_rating) for r in recorte.itertuples(index=False)}
    for u in lista_nos:
        for v in lista_nos:
            if u is not v:
                u.adicionar_aresta(v, round(notas[v.id] - notas[u.id] + ajuste, 4))
    return lista_nos, mapa_nos
