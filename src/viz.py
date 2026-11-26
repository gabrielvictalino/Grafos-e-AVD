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


# [IA] Antigravity (Gemini) – aprimoramento em matplotlib do heatmap (grade completa com paredes, paleta discreta, legenda e marcadores)
def exportar_heatmap(heatmap, nome_mapa, diretorio="out/parte1", mapa_path=None):
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    from matplotlib.patches import Patch

    os.makedirs(diretorio, exist_ok=True)

    if mapa_path is not None:
        grade = _ler_grade_mapa(mapa_path)
        n_linhas = len(grade)
        n_colunas = len(grade[0])
        matriz = []
        for r in range(n_linhas):
            linha_vals = []
            for c in range(n_colunas):
                if grade[r][c] == "#":
                    linha_vals.append(float("nan"))
                else:
                    val = heatmap[r][c] if r < len(heatmap) and c < len(heatmap[r]) else None
                    linha_vals.append(float("nan") if val is None else val)
            matriz.append(linha_vals)
    else:
        matriz = [
            [float("nan") if valor is None else valor for valor in linha]
            for linha in heatmap
        ]
        n_linhas = len(matriz)
        n_colunas = len(matriz[0]) if matriz else 0

    valores_validos = [v for linha in matriz for v in linha if v == v]
    min_val = int(min(valores_validos, default=1))
    max_val = int(max(valores_validos, default=1))

    paleta_base = ["#fff3bf", "#fed976", "#fd8d3c", "#e31a1c", "#800026"]
    if min_val == 0:
        cores = ["#dee2e6"] + paleta_base[: max(1, max_val)]
        limites = [i - 0.5 for i in range(0, max_val + 2)]
        ticks = list(range(0, max_val + 1))
    else:
        n_niveis = max(1, max_val)
        cores = (paleta_base * ((n_niveis // len(paleta_base)) + 1))[:n_niveis]
        limites = [i - 0.5 for i in range(1, max_val + 2)]
        ticks = list(range(1, max_val + 1))

    cmap = ListedColormap(cores).copy()
    cmap.set_bad(color="#1d2b36")
    norm = BoundaryNorm(limites, cmap.N)

    largura_fig = 19 if n_colunas > 30 else 11
    altura_fig = 9.5 if n_linhas > 15 else 7.5
    fig, ax = plt.subplots(figsize=(largura_fig, altura_fig))

    imagem = ax.imshow(
        matriz,
        cmap=cmap,
        norm=norm,
        interpolation="nearest",
        aspect="equal",
    )

    if mapa_path is not None:
        casas_mult_max = sum(1 for v in valores_validos if int(v) == max_val)
        grade = _ler_grade_mapa(mapa_path)
        estilos_especiais = {
            "S": ("#2b8a3e", "#ffffff", "S (Início)"),
            "G": ("#d9480f", "#ffffff", "G (Saída)"),
            "chave": ("#ffd43b", "#111111", "a–d (Chaves)"),
            "porta": ("#5f3dc4", "#ffffff", "A–D (Portas)"),
        }
        usados = set()
        for r, linha_txt in enumerate(grade):
            for c, simb in enumerate(linha_txt):
                if simb == "S":
                    cor_bg, cor_fg, _ = estilos_especiais["S"]
                    usados.add("S")
                elif simb == "G":
                    cor_bg, cor_fg, _ = estilos_especiais["G"]
                    usados.add("G")
                elif simb in "abcd":
                    cor_bg, cor_fg, _ = estilos_especiais["chave"]
                    usados.add("chave")
                elif simb in "ABCD":
                    cor_bg, cor_fg, _ = estilos_especiais["porta"]
                    usados.add("porta")
                else:
                    continue
                ax.text(
                    c,
                    r,
                    simb,
                    ha="center",
                    va="center",
                    fontsize=8.5 if n_colunas > 30 else 10,
                    fontweight="bold",
                    color=cor_fg,
                    bbox=dict(
                        boxstyle="round,pad=0.18",
                        facecolor=cor_bg,
                        edgecolor="#ffffff",
                        linewidth=0.9,
                    ),
                    zorder=5,
                )

        ax.set_title(
            f"Heatmap de Multiplicidade de Estados por Casa — {nome_mapa} "
            f"(máx. = {max_val} em {casas_mult_max} casas)",
            fontsize=14,
            fontweight="bold",
            pad=14,
        )
        itens_legenda = [
            Patch(facecolor="#1d2b36", edgecolor="#495057", label="# Parede (intransponível)")
        ]
        for chave_leg in ("S", "G", "chave", "porta"):
            if chave_leg in usados:
                cor_bg, _, rot = estilos_especiais[chave_leg]
                itens_legenda.append(Patch(facecolor=cor_bg, edgecolor="#343a40", label=rot))
        ax.legend(
            handles=itens_legenda,
            title="Elementos do mapa",
            loc="upper center",
            bbox_to_anchor=(0.5, -0.09),
            ncol=len(itens_legenda),
            frameon=True,
            facecolor="#f8f9fa",
            fontsize=9.5,
            title_fontsize=10,
        )
    else:
        ax.set_title(f"Heatmap de estados por posição — {nome_mapa}", fontsize=13, fontweight="bold")

    ax.set_xlabel("Coluna", fontsize=11, fontweight="bold")
    ax.set_ylabel("Linha", fontsize=11, fontweight="bold")

    passo_x = 5 if n_colunas > 25 else 1
    passo_y = 5 if n_linhas > 20 else 1
    ax.set_xticks(range(0, n_colunas, passo_x))
    ax.set_yticks(range(0, n_linhas, passo_y))
    ax.tick_params(labelsize=9)

    cbar = fig.colorbar(
        imagem,
        ax=ax,
        ticks=ticks,
        fraction=0.028,
        pad=0.02,
    )
    cbar.set_label("Multiplicidade (nº de estados alcançáveis por casa)", fontsize=10.5, fontweight="bold")
    cbar.ax.tick_params(labelsize=9.5)

    caminho = os.path.join(diretorio, f"heatmap_{nome_mapa}.png")
    fig.savefig(caminho, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return caminho


# [IA] Antigravity (Gemini) – visualizações estáticas da Parte 1 (percursos, grafo em camadas, árvore BFS e heatmap)
_CORES_CAMADA_PERCURSO = {
    "-": ("#1971c2", "Sem chaves (-)"),
    "a": ("#e8590c", "Com chave a"),
    "ab": ("#2b8a3e", "Com chaves ab"),
    "abc": ("#c92a2a", "Com chaves abc"),
    "abcd": ("#7048e8", "Com chaves abcd"),
}


def _ler_grade_mapa(caminho_mapa: str | Path) -> list[str]:
    """Lê a grade retangular completa de um mapa .txt ignorando comentários ';'."""
    texto = Path(caminho_mapa).read_text(encoding="utf-8")
    return [
        linha.rstrip("\r\n")
        for linha in texto.splitlines()
        if linha.strip() and not linha.startswith(";")
    ]


# [IA] Antigravity (Gemini) – sintaxe matplotlib para desenho do percurso ótimo sobre a grade do mapa
def exportar_percurso_mapa(
    caminho_mapa: str | Path,
    nome_mapa: str,
    diretorio: str | Path = "out/parte1",
) -> Path:
    """Desenha o caminho de menor custo (Dijkstra) sobre a grade, mudando de cor a cada chave."""
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch, Rectangle
    from src.graphs.algorithms import (
        bfs_grafo_estados_exploracao,
        converter_grafo_estados,
        dijkstra,
    )
    from src.graphs.labirinto import gerar_labirinto, preparar_estados
    from src.solve import reconstruir_caminho_nos

    grade = _ler_grade_mapa(caminho_mapa)
    n_linhas = len(grade)
    n_colunas = len(grade[0])

    labirinto = gerar_labirinto(str(caminho_mapa))
    modelos, inicio, fim = preparar_estados(labirinto)
    arestas_geradas, camadas = bfs_grafo_estados_exploracao(modelos, inicio, fim)
    lista_nos, no_ini, alvo, nos_por_estado = converter_grafo_estados(
        arestas_geradas, camadas, inicio, fim, incluir_alvo=True
    )
    estado_por_no = {no: est for est, no in nos_por_estado.items()}

    distancias, anteriores, recusado = dijkstra(lista_nos, no_ini)
    if recusado or not (distancias and distancias[alvo] < float("inf")):
        raise ValueError(f"Não foi possível calcular caminho de menor custo em {caminho_mapa}")

    caminho_nos = [n for n in reconstruir_caminho_nos(anteriores, no_ini, alvo) if n is not alvo]
    custo_total = distancias[alvo]
    passos_totais = len(caminho_nos) - 1

    chaves_camadas = []
    for no in caminho_nos:
        ch = estado_por_no[no].chaves or "-"
        if ch not in chaves_camadas:
            chaves_camadas.append(ch)

    offsets_base = [
        (-0.18, -0.18),
        (0.18, -0.18),
        (-0.18, 0.18),
        (0.18, 0.18),
        (0.0, 0.0),
    ]
    offset_por_camada = {
        ch: offsets_base[idx % len(offsets_base)]
        for idx, ch in enumerate(chaves_camadas)
    }

    cores_celulas = {
        "#": "#2b343b",
        ".": "#f8f9fa",
        ",": "#e6c78b",
        "~": "#7fb7d9",
        "S": "#51cf66",
        "G": "#ff922b",
        "+": "#fcc2d7",
        "*": "#fcc2d7",
    }
    for ch in "abcd":
        cores_celulas[ch] = "#ffe066"
    for pt in "ABCD":
        cores_celulas[pt] = "#b197fc"
    for est in "><^v":
        cores_celulas[est] = "#d0ebff"

    grande = n_colunas > 30
    fig, ax = plt.subplots(figsize=(20, 10.5) if grande else (14, 8.5))

    for r, linha_txt in enumerate(grade):
        for c, simb in enumerate(linha_txt):
            cor_cel = cores_celulas.get(simb, "#f8f9fa")
            ax.add_patch(
                Rectangle(
                    (c - 0.5, r - 0.5),
                    1.0,
                    1.0,
                    facecolor=cor_cel,
                    edgecolor="#adb5bd" if simb != "#" else "#1f262c",
                    linewidth=0.35 if grande else 0.7,
                    zorder=1,
                )
            )

    # Desenha o percurso por segmento de camada com pequeno deslocamento para distinguir sobreposições
    pontos_por_no = []
    for no in caminho_nos:
        est = estado_por_no[no]
        ch = est.chaves or "-"
        dx, dy = offset_por_camada[ch]
        pontos_por_no.append((est.no_pos.posicao_coluna + dx, est.no_pos.posicao_linha + dy, ch, est))

    coletas_chave = []
    for idx in range(len(pontos_por_no) - 1):
        x1, y1, ch1, est1 = pontos_por_no[idx]
        x2, y2, ch2, est2 = pontos_por_no[idx + 1]
        cor_seg, _ = _CORES_CAMADA_PERCURSO.get(ch2 if ch1 != ch2 else ch1, ("#343a40", ch1))
        ax.plot(
            [x1, x2],
            [y1, y2],
            color=cor_seg,
            linewidth=2.3 if grande else 3.2,
            solid_capstyle="round",
            alpha=0.92,
            zorder=3,
        )
        if ch1 != ch2:
            coletas_chave.append((est2.no_pos.posicao_coluna, est2.no_pos.posicao_linha, est2.no_pos.tipo, cor_seg))
        elif idx % (8 if grande else 4) == 0:
            ax.annotate(
                "",
                xy=(x1 + 0.65 * (x2 - x1), y1 + 0.65 * (y2 - y1)),
                xytext=(x1 + 0.2 * (x2 - x1), y1 + 0.2 * (y2 - y1)),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=cor_seg,
                    lw=0,
                    mutation_scale=10 if grande else 12,
                ),
                zorder=4,
            )

    # Rótulos nítidos de elementos sobre o mapa
    simbolos_destaque = {"S", "G", "a", "b", "c", "d", "A", "B", "C", "D"}
    for r, linha_txt in enumerate(grade):
        for c, simb in enumerate(linha_txt):
            if simb in simbolos_destaque:
                if simb == "S":
                    bg, fg = "#2b8a3e", "#ffffff"
                elif simb == "G":
                    bg, fg = "#d9480f", "#ffffff"
                elif simb in "abcd":
                    bg, fg = "#ffd43b", "#111111"
                else:
                    bg, fg = "#5f3dc4", "#ffffff"
                ax.text(
                    c,
                    r,
                    simb,
                    ha="center",
                    va="center",
                    fontsize=8.5 if grande else 11.5,
                    fontweight="bold",
                    color=fg,
                    bbox=dict(
                        boxstyle="round,pad=0.16" if grande else "round,pad=0.22",
                        facecolor=bg,
                        edgecolor="#ffffff",
                        linewidth=0.9,
                    ),
                    zorder=6,
                )
            elif not grande and simb in (",", "~"):
                ax.text(
                    c,
                    r,
                    simb,
                    ha="center",
                    va="center",
                    fontsize=10,
                    fontweight="bold",
                    color="#495057",
                    zorder=2,
                )

    for cx, cy, ch_coleta, cor_seg in coletas_chave:
        ax.scatter(
            [cx],
            [cy],
            s=230 if grande else 340,
            facecolors="none",
            edgecolors=cor_seg,
            linewidths=2.2,
            zorder=5,
        )

    ax.set_xlim(-0.5, n_colunas - 0.5)
    ax.set_ylim(n_linhas - 0.5, -0.5)
    ax.set_aspect("equal")
    passo_x = 5 if grande else 1
    passo_y = 5 if grande else 1
    ax.set_xticks(range(0, n_colunas, passo_x))
    ax.set_yticks(range(0, n_linhas, passo_y))
    ax.set_xlabel("Coluna", fontsize=11, fontweight="bold")
    ax.set_ylabel("Linha", fontsize=11, fontweight="bold")
    ax.set_title(
        f"Percurso Ótimo (Dijkstra) sobre o Mapa {nome_mapa} — "
        f"{passos_totais} passos, custo {int(custo_total) if float(custo_total).is_integer() else custo_total} "
        f"(cor muda a cada chave)",
        fontsize=14,
        fontweight="bold",
        pad=14,
    )

    handles_camadas = [
        Line2D(
            [0],
            [0],
            color=_CORES_CAMADA_PERCURSO.get(ch, ("#343a40", ch))[0],
            lw=3.2,
            label=_CORES_CAMADA_PERCURSO.get(ch, ("#343a40", f"Chaves: {ch}"))[1],
        )
        for ch in chaves_camadas
    ]
    handles_mapa = [
        Patch(facecolor="#2b343b", edgecolor="#1f262c", label="# Parede"),
        Patch(facecolor="#f8f9fa", edgecolor="#adb5bd", label=". Chão (1)"),
        Patch(facecolor="#e6c78b", edgecolor="#adb5bd", label=", Lama (3)"),
        Patch(facecolor="#7fb7d9", edgecolor="#adb5bd", label="~ Água (5)"),
        Patch(facecolor="#2b8a3e", edgecolor="#ffffff", label="S Início"),
        Patch(facecolor="#d9480f", edgecolor="#ffffff", label="G Saída"),
        Patch(facecolor="#ffd43b", edgecolor="#343a40", label="a–d Chave"),
        Patch(facecolor="#5f3dc4", edgecolor="#ffffff", label="A–D Porta"),
    ]
    if grande:
        leg1 = ax.legend(
            handles=handles_camadas,
            title="Etapas do percurso por chaves coletadas",
            loc="upper left",
            bbox_to_anchor=(0.0, -0.07),
            ncol=len(handles_camadas),
            frameon=True,
            facecolor="#f8f9fa",
            fontsize=9.5,
            title_fontsize=10,
        )
        ax.add_artist(leg1)
        ax.legend(
            handles=handles_mapa,
            title="Elementos do mapa",
            loc="upper right",
            bbox_to_anchor=(1.0, -0.07),
            ncol=4,
            frameon=True,
            facecolor="#f8f9fa",
            fontsize=9.0,
            title_fontsize=10,
        )
    else:
        leg1 = ax.legend(
            handles=handles_camadas,
            title="Etapas do percurso por chaves coletadas",
            loc="upper center",
            bbox_to_anchor=(0.5, -0.085),
            ncol=len(handles_camadas),
            frameon=True,
            facecolor="#f8f9fa",
            fontsize=9.5,
            title_fontsize=10,
        )
        ax.add_artist(leg1)
        ax.legend(
            handles=handles_mapa,
            title="Elementos do mapa",
            loc="upper center",
            bbox_to_anchor=(0.5, -0.195),
            ncol=4,
            frameon=True,
            facecolor="#f8f9fa",
            fontsize=9.0,
            title_fontsize=10,
        )

    out_dir = Path(diretorio)
    out_dir.mkdir(parents=True, exist_ok=True)
    caminho_saida = out_dir / f"percurso_{nome_mapa}.png"
    fig.savefig(caminho_saida, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return caminho_saida


# [IA] Antigravity (Gemini) – sintaxe matplotlib para desenho do grafo de estados do m02 em camadas
def exportar_grafo_estados_m02(
    caminho_mapa: str | Path,
    diretorio: str | Path = "out/parte1",
) -> Path:
    """Desenha o grafo de estados do m02 organizado por camadas, destacando o arco entre camadas."""
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
    from src.graphs.algorithms import bfs_grafo_estados_exploracao
    from src.graphs.estados import formatar_estado
    from src.graphs.labirinto import gerar_labirinto, preparar_estados

    labirinto = gerar_labirinto(str(caminho_mapa))
    modelos, inicio, fim = preparar_estados(labirinto)
    arestas_geradas, camadas = bfs_grafo_estados_exploracao(modelos, inicio, fim)

    camada_offsets = {"-": 4.2, "a": 0.0}
    camada_rotulos = {
        "-": f'Camada "-" (sem chaves) — {len(camadas[0].lista_nos_estados)} estados',
        "a": f'Camada "a" (com chave a) — {len(camadas[1].lista_nos_estados)} estados',
    }

    posicoes: dict = {}
    estados_por_camada: dict[str, list] = {}
    for camada in camadas:
        rot = camada.rotulo
        estados_por_camada[rot] = camada.lista_nos_estados
        y_base = camada_offsets[rot]
        for est in camada.lista_nos_estados:
            r = est.no_pos.posicao_linha
            c = est.no_pos.posicao_coluna
            posicoes[est] = (float(c), y_base + (3 - r))

    alvo_pos = (12.4, camada_offsets["a"] + (3 - 1))

    fig, ax = plt.subplots(figsize=(17, 9.5))

    # Painéis de fundo para as duas camadas
    paineis = [
        ("-", "#eef5ff", "#3b82f6", 4.2),
        ("a", "#fff4e6", "#e8590c", 0.0),
    ]
    for rot, cor_bg, cor_borda, y0 in paineis:
        painel = FancyBboxPatch(
            (0.35, y0 - 0.55),
            12.65 if rot == "a" else 11.3,
            3.1,
            boxstyle="round,pad=0.12,rounding_size=0.22",
            facecolor=cor_bg,
            edgecolor=cor_borda,
            linewidth=1.6,
            alpha=0.55,
            zorder=0,
        )
        ax.add_patch(painel)
        n_est = len(estados_por_camada[rot])
        n_int = sum(
            1
            for o, d, _, _, _ in arestas_geradas
            if d != "ALVO" and o.chaves == d.chaves and (o.chaves or "-") == rot
        )
        ax.text(
            0.55,
            y0 + 2.38,
            f'Camada "{rot}" — {n_est} estados, {n_int} arcos internos',
            fontsize=11,
            fontweight="bold",
            color=cor_borda,
            va="center",
            zorder=2,
        )

    # Casa ghost da porta A bloqueada na camada "-"
    ax.add_patch(
        FancyBboxPatch(
            (5.65, camada_offsets["-"] + 2 - 0.28),
            0.70,
            0.56,
            boxstyle="round,pad=0.04,rounding_size=0.1",
            facecolor="#f1f3f5",
            edgecolor="#868e96",
            linestyle="--",
            linewidth=1.3,
            zorder=2,
        )
    )
    ax.text(
        6.0,
        camada_offsets["-"] + 2,
        "A (1,6)\nbloqueada",
        ha="center",
        va="center",
        fontsize=7.5,
        color="#495057",
        fontweight="bold",
        zorder=3,
    )

    pares_arcos = {
        (o, d)
        for o, d, _, _, _ in arestas_geradas
        if d != "ALVO"
    }

    # Desenha as arestas dirigidas
    for origem, destino, mov, casa_dest, peso in arestas_geradas:
        if destino == "ALVO":
            x1, y1 = posicoes[origem]
            x2, y2 = alvo_pos
            seta = FancyArrowPatch(
                (x1 + 0.34, y1),
                (x2 - 0.38, y2),
                arrowstyle="-|>,head_length=6,head_width=3.5",
                color="#495057",
                linestyle="--",
                linewidth=1.5,
                zorder=2,
            )
            ax.add_patch(seta)
            ax.text(
                (x1 + x2) / 2,
                y1 + 0.17,
                "peso 0",
                ha="center",
                va="bottom",
                fontsize=8,
                color="#495057",
                fontweight="bold",
            )
            continue

        x1, y1 = posicoes[origem]
        x2, y2 = posicoes[destino]
        entre_camadas = (origem.chaves or "-") != (destino.chaves or "-")
        bidirecional = (destino, origem) in pares_arcos

        if entre_camadas:
            seta = FancyArrowPatch(
                (x1 + 0.12, y1 - 0.25),
                (x2 + 0.12, y2 + 0.25),
                connectionstyle="arc3,rad=-0.22",
                arrowstyle="-|>,head_length=8,head_width=4.5",
                color="#e03131",
                linewidth=2.8,
                zorder=5,
            )
            ax.add_patch(seta)
            ax.text(
                x1 + 0.35,
                3.1,
                f"Mudança de camada ({mov}, '{casa_dest}', peso {peso})\n"
                f"{formatar_estado(origem)} → {formatar_estado(destino)}",
                ha="right",
                va="center",
                fontsize=8.5,
                fontweight="bold",
                color="#c92a2a",
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    facecolor="#fff5f5",
                    edgecolor="#e03131",
                    linewidth=1.2,
                ),
                zorder=6,
            )
        else:
            cor_arco = "#b07d2b" if peso == 3 else "#6c757d"
            larg = 1.6 if peso == 3 else 1.15
            rad = 0.20 if bidirecional else 0.0
            seta = FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                connectionstyle=f"arc3,rad={rad}",
                arrowstyle="-|>,head_length=5,head_width=2.8",
                color=cor_arco,
                linewidth=larg,
                shrinkA=17,
                shrinkB=17,
                alpha=0.88,
                zorder=2,
            )
            ax.add_patch(seta)
            if peso == 3 and x2 > x1:
                ax.text(
                    (x1 + x2) / 2,
                    (y1 + y2) / 2 + 0.18,
                    "3",
                    ha="center",
                    va="bottom",
                    fontsize=7.5,
                    fontweight="bold",
                    color="#8f5f14",
                    zorder=4,
                )

    # Desenha os nós de estado
    for est, (x, y) in posicoes.items():
        simb = est.no_pos.tipo
        if simb == "S":
            fc, ec, tc = "#2b8a3e", "#1b5e20", "#ffffff"
        elif simb == "G":
            fc, ec, tc = "#d9480f", "#9c3208", "#ffffff"
        elif simb == "a":
            fc, ec, tc = "#ffd43b", "#b08900", "#111111"
        elif simb == "A":
            fc, ec, tc = "#5f3dc4", "#3b2385", "#ffffff"
        elif simb == ",":
            fc, ec, tc = "#f3d9a4", "#b07d2b", "#212529"
        else:
            fc, ec, tc = "#ffffff", "#343a40", "#212529"

        tag = f" {simb}" if simb in ("S", "G", "a", "A", ",") else ""
        rotulo_no = f"({est.no_pos.posicao_linha},{est.no_pos.posicao_coluna}){tag}"
        ax.add_patch(
            FancyBboxPatch(
                (x - 0.36, y - 0.22),
                0.72,
                0.44,
                boxstyle="round,pad=0.04,rounding_size=0.1",
                facecolor=fc,
                edgecolor=ec,
                linewidth=1.5,
                zorder=4,
            )
        )
        ax.text(
            x,
            y,
            rotulo_no,
            ha="center",
            va="center",
            fontsize=7.3,
            fontweight="bold",
            color=tc,
            zorder=5,
        )

    # Nó virtual ALVO
    ax.add_patch(
        FancyBboxPatch(
            (alvo_pos[0] - 0.38, alvo_pos[1] - 0.24),
            0.76,
            0.48,
            boxstyle="round,pad=0.04,rounding_size=0.1",
            facecolor="#e9ecef",
            edgecolor="#495057",
            linestyle="--",
            linewidth=1.6,
            zorder=4,
        )
    )
    ax.text(
        alvo_pos[0],
        alvo_pos[1],
        "ALVO\n(virtual)",
        ha="center",
        va="center",
        fontsize=7.5,
        fontweight="bold",
        color="#212529",
        zorder=5,
    )

    ax.set_xlim(0.1, 13.25)
    ax.set_ylim(-0.85, 7.1)
    ax.set_xticks(range(1, 12))
    ax.set_yticks([0, 1, 2, 4.2, 5.2, 6.2])
    ax.set_yticklabels(["L3 (a)", "L2 (a)", "L1 (a)", "L3 (-)", "L2 (-)", "L1 (-)"])
    ax.set_xlabel("Coluna do labirinto", fontsize=11, fontweight="bold")
    ax.set_ylabel("Linha do labirinto por camada", fontsize=11, fontweight="bold")
    ax.set_title(
        "Grafo de Estados do Mapa m02 em Camadas (39 estados, 74 arcos dirigidos + arco virtual ALVO)",
        fontsize=14,
        fontweight="bold",
        pad=14,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    handles_leg = [
        Patch(facecolor="#2b8a3e", edgecolor="#1b5e20", label="S (Início)"),
        Patch(facecolor="#f3d9a4", edgecolor="#b07d2b", label=", (Lama, peso 3)"),
        Patch(facecolor="#ffd43b", edgecolor="#b08900", label="a (Chave)"),
        Patch(facecolor="#5f3dc4", edgecolor="#3b2385", label="A (Porta)"),
        Patch(facecolor="#d9480f", edgecolor="#9c3208", label="G (Saída)"),
        Patch(facecolor="#e9ecef", edgecolor="#495057", linestyle="--", label="ALVO virtual (peso 0)"),
        Line2D([0], [0], color="#6c757d", lw=1.6, label="Arco interno (peso 1)"),
        Line2D([0], [0], color="#b07d2b", lw=1.8, label="Arco para lama (peso 3)"),
        Line2D([0], [0], color="#e03131", lw=2.8, label="Arco entre camadas (- → a)"),
    ]
    ax.legend(
        handles=handles_leg,
        title="Legenda de vértices e arcos dirigidos",
        loc="upper center",
        bbox_to_anchor=(0.5, -0.09),
        ncol=5,
        frameon=True,
        facecolor="#f8f9fa",
        fontsize=9.2,
        title_fontsize=10,
    )

    out_dir = Path(diretorio)
    out_dir.mkdir(parents=True, exist_ok=True)
    caminho_saida = out_dir / "grafo_estados_m02.png"
    fig.savefig(caminho_saida, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return caminho_saida


# [IA] Antigravity (Gemini) – sintaxe matplotlib para desenho da árvore BFS do m02 com níveis visíveis
def exportar_arvore_bfs_m02(
    caminho_mapa: str | Path,
    diretorio: str | Path = "out/parte1",
) -> Path:
    """Desenha a árvore BFS do grafo de estados do m02 com todos os níveis visíveis."""
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
    from src.graphs.algorithms import bfs, bfs_grafo_estados_exploracao, converter_grafo_estados
    from src.graphs.estados import formatar_estado
    from src.graphs.labirinto import gerar_labirinto, preparar_estados
    from src.solve import reconstruir_caminho_nos

    labirinto = gerar_labirinto(str(caminho_mapa))
    modelos, inicio, fim = preparar_estados(labirinto)
    arestas_geradas, camadas = bfs_grafo_estados_exploracao(modelos, inicio, fim)
    lista_nos, no_ini, _, nos_por_estado = converter_grafo_estados(
        arestas_geradas, camadas, inicio, fim, incluir_alvo=False
    )
    estado_por_no = {no: est for est, no in nos_por_estado.items()}

    niveis, anteriores = bfs(lista_nos, no_ini)
    no_saida = next(no for no, est in estado_por_no.items() if est.no_pos.tipo == "G")
    caminho_otimo = set(reconstruir_caminho_nos(anteriores, no_ini, no_saida) or [])

    max_nivel = int(max(niveis.values()))

    # Posiciona os nós por ramo (raiz, ramo superior bloqueado, ramo principal "-", ramo principal "a")
    x_por_no = {}
    for no, nv in niveis.items():
        est = estado_por_no[no]
        if nv == 0:
            x_por_no[no] = 0.0
        elif est.chaves == "" and est.no_pos.posicao_linha == 1:
            x_por_no[no] = -2.2
        elif est.chaves == "":
            x_por_no[no] = 0.5
        else:
            x_por_no[no] = 3.2

    fig, ax = plt.subplots(figsize=(13, 17))

    # Faixas alternadas e linhas de nível horizontais
    for nv in range(max_nivel + 1):
        y = -nv
        if nv % 2 == 0:
            ax.axhspan(y - 0.48, y + 0.48, facecolor="#f8f9fa", zorder=0)
        ax.axhline(y, color="#dee2e6", linestyle="--", linewidth=0.65, zorder=0)

    # Arestas da árvore BFS
    for no, pai in anteriores.items():
        if pai is None:
            continue
        x1, y1 = x_por_no[pai], -niveis[pai]
        x2, y2 = x_por_no[no], -niveis[no]
        est_pai = estado_por_no[pai]
        est_no = estado_por_no[no]
        entre_camadas = est_pai.chaves != est_no.chaves
        no_caminho = (pai in caminho_otimo) and (no in caminho_otimo)

        if entre_camadas:
            cor, lw = "#e03131", 2.8
        elif no_caminho:
            cor, lw = "#1971c2", 2.2
        else:
            cor, lw = "#868e96", 1.5

        rad = 0.14 if x1 != x2 else 0.0
        seta = FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            connectionstyle=f"arc3,rad={rad}",
            arrowstyle="-|>,head_length=5.5,head_width=3",
            color=cor,
            linewidth=lw,
            shrinkA=12,
            shrinkB=12,
            zorder=2,
        )
        ax.add_patch(seta)

        if entre_camadas:
            ax.text(
                (x1 + x2) / 2 + 0.1,
                (y1 + y2) / 2 + 0.42,
                "coleta 'a'\n(muda camada)",
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontweight="bold",
                color="#c92a2a",
                bbox=dict(boxstyle="round,pad=0.22", facecolor="#fff5f5", edgecolor="#e03131"),
                zorder=5,
            )

    # Anotação do ramo morto na camada "-"
    no_bloqueado = next(
        no
        for no, est in estado_por_no.items()
        if est.chaves == "" and (est.no_pos.posicao_linha, est.no_pos.posicao_coluna) == (1, 5)
    )
    ax.text(
        x_por_no[no_bloqueado],
        -niveis[no_bloqueado] - 1.15,
        "Sem saída na camada '-':\nporta A em (1,6) bloqueada",
        ha="center",
        va="top",
        fontsize=8.5,
        fontweight="bold",
        color="#495057",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#f1f3f5", edgecolor="#adb5bd", linestyle="--"),
        zorder=4,
    )

    # Caixas dos nós com rótulo obrigatório e papel no mapa
    for no, nv in niveis.items():
        est = estado_por_no[no]
        simb = est.no_pos.tipo
        x, y = x_por_no[no], -nv
        tag = f" [{simb}]" if simb in ("S", "G", "a", "A", ",") else ""
        rotulo = f"{formatar_estado(est)}{tag}"

        if simb == "S":
            fc, ec, tc = "#2b8a3e", "#1b5e20", "#ffffff"
        elif simb == "G":
            fc, ec, tc = "#d9480f", "#9c3208", "#ffffff"
        elif simb == "a":
            fc, ec, tc = "#ffd43b", "#b08900", "#111111"
        elif simb == "A":
            fc, ec, tc = "#5f3dc4", "#3b2385", "#ffffff"
        elif est.chaves == "":
            fc, ec, tc = "#e7f5ff", "#1971c2", "#1864ab"
        else:
            fc, ec, tc = "#fff4e6", "#e8590c", "#9c3208"

        ax.add_patch(
            FancyBboxPatch(
                (x - 0.88, y - 0.31),
                1.76,
                0.62,
                boxstyle="round,pad=0.04,rounding_size=0.12",
                facecolor=fc,
                edgecolor=ec,
                linewidth=1.35,
                zorder=3,
            )
        )
        ax.text(
            x,
            y,
            rotulo,
            ha="center",
            va="center",
            fontsize=8.0,
            fontweight="bold",
            color=tc,
            zorder=4,
        )

    ax.set_xlim(-3.5, 4.5)
    ax.set_ylim(-max_nivel - 1.1, 1.0)
    ax.set_yticks([-nv for nv in range(max_nivel + 1)])
    ax.set_yticklabels([f"Nível {nv}" for nv in range(max_nivel + 1)], fontsize=8.5)
    ax.set_xticks([-2.2, 0.5, 3.2])
    ax.set_xticklabels(
        [
            "Ramo superior (-)\nbloqueado em A",
            "Ramo principal (-)\nrumo à chave 'a'",
            "Camada 'a'\nretorno e saída G",
        ],
        fontsize=9.5,
        fontweight="bold",
    )
    ax.set_xlabel("Ramo / Camada do Grafo de Estados", fontsize=11, fontweight="bold", labelpad=8)
    ax.set_ylabel("Nível BFS (passos a partir de S)", fontsize=11, fontweight="bold")
    ax.set_title(
        f"Árvore BFS do Grafo de Estados do Mapa m02 ({len(lista_nos)} estados, níveis 0 a {max_nivel})",
        fontsize=14,
        fontweight="bold",
        pad=14,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    handles_leg = [
        Patch(facecolor="#e7f5ff", edgecolor="#1971c2", label='Estado na camada "-"'),
        Patch(facecolor="#fff4e6", edgecolor="#e8590c", label='Estado na camada "a"'),
        Patch(facecolor="#2b8a3e", edgecolor="#1b5e20", label="S (Raiz / Nível 0)"),
        Patch(facecolor="#ffd43b", edgecolor="#b08900", label="a (Coleta chave, Nível 12)"),
        Patch(facecolor="#5f3dc4", edgecolor="#3b2385", label="A (Porta aberta, Nível 29)"),
        Patch(facecolor="#d9480f", edgecolor="#9c3208", label="G (Saída, Nível 34)"),
        Line2D([0], [0], color="#1971c2", lw=2.2, label="Aresta de árvore (caminho ótimo)"),
        Line2D([0], [0], color="#868e96", lw=1.6, label="Aresta de árvore (ramo morto)"),
        Line2D([0], [0], color="#e03131", lw=2.8, label="Transição entre camadas (- → a)"),
    ]
    ax.legend(
        handles=handles_leg,
        title="Legenda dos níveis, vértices e arestas da árvore BFS",
        loc="upper center",
        bbox_to_anchor=(0.5, -0.055),
        ncol=3,
        frameon=True,
        facecolor="#f8f9fa",
        fontsize=9.0,
        title_fontsize=10,
    )

    out_dir = Path(diretorio)
    out_dir.mkdir(parents=True, exist_ok=True)
    caminho_saida = out_dir / "arvore_bfs_m02.png"
    fig.savefig(caminho_saida, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return caminho_saida


# [IA] Antigravity (Gemini) – orquestração da geração das 5 figuras PNG da Parte 1
def gerar_figuras_parte1(
    pasta_mapas: str | Path = "data/mapas",
    diretorio_saida: str | Path = "out/parte1",
) -> list[Path]:
    """Gera as 5 figuras PNG obrigatórias da Seção 8 da Parte 1."""
    from src.graphs.algorithms import bfs_grafo_estados_exploracao
    from src.graphs.labirinto import gerar_labirinto, preparar_estados

    base = Path(pasta_mapas)
    out_dir = Path(diretorio_saida)
    out_dir.mkdir(parents=True, exist_ok=True)

    m02 = base / "m02_uma_chave.txt"
    m03 = base / "m03_tres_chaves.txt"
    m08 = base / "m08_grande.txt"

    caminhos = [
        exportar_percurso_mapa(m03, "m03", out_dir),
        exportar_percurso_mapa(m08, "m08", out_dir),
        exportar_grafo_estados_m02(m02, out_dir),
        exportar_arvore_bfs_m02(m02, out_dir),
    ]

    lab_m08 = gerar_labirinto(str(m08))
    modelos_m08, ini_m08, fim_m08 = preparar_estados(lab_m08)
    bfs_grafo_estados_exploracao(modelos_m08, ini_m08, fim_m08)
    heatmap_m08 = lab_m08.calcular_heatmap()
    caminhos.append(Path(exportar_heatmap(heatmap_m08, "m08", diretorio=str(out_dir), mapa_path=m08)))

    return caminhos


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
    parser = argparse.ArgumentParser(description="Gera gráficos da Parte 1 e da Parte 2.")
    parser.add_argument("relatorio", nargs="?", help="Caminho para parte2_report.json (gráficos do benchmark)")
    parser.add_argument("--graus", metavar="DATASET", help="Gera os histogramas de grau a partir do dataset limpo")
    # [IA] Antigravity (Gemini) – opções --parte1 e --mapas na CLI para gerar as 5 figuras da Parte 1
    parser.add_argument("--parte1", action="store_true", help="Gera as 5 figuras PNG obrigatórias da Parte 1")
    parser.add_argument("--mapas", default="data/mapas", help="Pasta com os mapas .txt da Parte 1 (padrão: data/mapas)")
    parser.add_argument("--out", default=None, help="Diretório para salvar os gráficos")
    args = parser.parse_args()
    if not args.relatorio and not args.graus and not args.parte1:
        parser.error("informe --parte1, o relatório do benchmark e/ou --graus DATASET")

    # [IA] Antigravity (Gemini) – execução da geração das figuras da Parte 1 via CLI
    if args.parte1:
        destino_p1 = args.out or "out/parte1"
        for caminho in gerar_figuras_parte1(args.mapas, destino_p1):
            print(f"[OK] Figura Parte 1 salva em {caminho}")
    if args.relatorio:
        destino_p2 = args.out or "out/parte2"
        for caminho in gerar_graficos_parte2(args.relatorio, destino_p2):
            print(f"[OK] Gráfico salvo em {caminho}")
    if args.graus:
        destino_p2 = args.out or "out/parte2"
        for caminho in gerar_histogramas_grau(args.graus, destino_p2):
            print(f"[OK] Gráfico salvo em {caminho}")


if __name__ == "__main__":
    main()
