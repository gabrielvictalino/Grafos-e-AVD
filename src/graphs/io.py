
from itertools import combinations
from pathlib import Path
import pandas as pd
from src.graphs.graph import No


def carregar_grafo_tmdb(
    caminho: str | Path,
    limite_filmes: int | None = None,
    max_arestas: int = 500_000,
    transformacao_peso: str = "original",
) -> tuple[list[No], dict[str, No]]:
    """
    Lê o tmdb_limpo.csv e retorna (lista_nos, mapa_nos_por_id).
    transformacao_peso:
      - "original": peso = imdb_rating(recente) - imdb_rating(antigo) (pode ser negativo)
      - "nao_negativo": desloca os pesos somando +10.0 para garantir peso >= 0 (para Dijkstra)
    """
    caminho_path = Path(caminho)
    if caminho_path.is_dir():
        arquivos = list(caminho_path.glob("*.csv*"))
        if not arquivos:
            raise FileNotFoundError(f"Nenhum CSV encontrado em {caminho_path}")
        caminho_path = arquivos[0]

    colunas = ["id", "title", "release_date", "imdb_rating", "cast"]
    df = pd.read_csv(caminho_path, usecols=lambda c: c in colunas, low_memory=False)
    df = df.dropna(subset=colunas).copy()
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df = df.dropna(subset=["release_date"]).drop_duplicates(subset=["id"])
    df = df.sort_values(by=["release_date", "id"]).reset_index(drop=True)

    if limite_filmes is not None:
        df = df.head(limite_filmes)

    # Cria os vértices (filmes)
    mapa_nos: dict[str, No] = {}
    lista_nos: list[No] = []
    for row in df.itertuples(index=False):
        id_str = str(row.id)
        no = No(id_no=id_str, titulo=str(row.title))
        mapa_nos[id_str] = no
        lista_nos.append(no)

    # Índice invertido por ator
    ator_para_indices: dict[str, list[int]] = {}
    for idx, elenco in enumerate(df["cast"]):
        for ator in str(elenco).split(","):
            ator_limpo = ator.strip()
            if ator_limpo:
                ator_para_indices.setdefault(ator_limpo, []).append(idx)

    ids = df["id"].astype(str).tolist()
    datas = df["release_date"].tolist()
    notas = df["imdb_rating"].astype(float).tolist()

    arestas_vistas: set[tuple[str, str]] = set()

    for indices in ator_para_indices.values():
        if len(indices) < 2:
            continue
        for i, j in combinations(indices, 2):
            if datas[i] < datas[j]:
                u_id, v_id = ids[i], ids[j]
                if (u_id, v_id) not in arestas_vistas:
                    arestas_vistas.add((u_id, v_id))
                    peso = round(notas[j] - notas[i], 4)
                    if transformacao_peso == "nao_negativo":
                        # Como notas vão de 0 a 10, a diferença mínima é -10; somar 10 garante peso >= 0
                        peso = round(peso + 10.0, 4)

                    mapa_nos[u_id].adicionar_aresta(mapa_nos[v_id], peso)

                    if len(arestas_vistas) >= max_arestas:
                        return lista_nos, mapa_nos

    return lista_nos, mapa_nos