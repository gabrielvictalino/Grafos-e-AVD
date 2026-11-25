"""Visualização dos algoritmos do projeto. Execute com streamlit run app.py."""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from itertools import accumulate, pairwise
from math import isfinite
from pathlib import Path
from time import monotonic, sleep
from traceback import format_exc

import streamlit as st
from src.graphs import algorithms as graph_algorithms
from src.graphs import labirinto as maze


RAIZ = Path(__file__).resolve().parent
PASTA_MAPAS = RAIZ / "data" / "mapas"
# [IA] Claude – também procura nas pastas da estrutura do enunciado, se existirem
PASTAS_MAPAS = [RAIZ / "data" / "mapas", RAIZ / "data" / "mapas_grupo"]
# [IA] Claude – cores do rastro, uma por camada (conjunto de chaves)
CORES_CAMADAS = ["#f76707", "#7048e8", "#12a37f", "#d6336c", "#1971c2", "#5c940d",
                 "#1098ad", "#f08c00", "#7048e8", "#c92a2a", "#2b8a3e", "#495057",
                 "#0b7285", "#a61e4d", "#5f3dc4", "#087f5b"]

ALGORITMOS = ("BFS", "Dijkstra", "Bellman-Ford", "DFS")
CLASSES_DFS = {
    "arvore": ("Árvore", "#117a67"),
    "retorno": ("Retorno", "#b43459"),
    "avanco": ("Avanço", "#3458ad"),
    "cruzamento": ("Cruzamento", "#985121"),
}
SETAS = {"^": "↑", ">": "→", "v": "↓", "<": "←"}
MODOS_CAMADAS = ("Todas as camadas", "Só as já visitadas", "Só a camada atual")

# [IA] Claude – visual novo (tema claro, cartões, rastro colorido por camada)
CSS = """
<style>
.block-container { padding-top: 2.2rem; max-width: 1400px; }
h1, h2, h3 { letter-spacing: -.01em; }
.lab-topo { display:flex; align-items:center; gap:14px; flex-wrap:wrap; margin-bottom:.4rem; }
.lab-topo h1 { margin:0; padding:0; font-size:2rem; }
.lab-chip { display:inline-flex; align-items:center; gap:6px; padding:3px 10px; border-radius:999px;
  font-size:.82rem; font-weight:600; background:#eef2ff; color:#3b4a8f; border:1px solid #dbe2ff; }
.lab-chip.alg { background:#fff4e6; color:#a14a00; border-color:#ffe2bf; }
.lab-chip.tipo { background:#e6fcf5; color:#0b6e55; border-color:#c3f0e0; }
.lab-cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:12px; margin:.6rem 0 1rem; }
.lab-card { background:#fff; border:1px solid #e6e8ef; border-radius:14px; padding:12px 16px;
  box-shadow:0 1px 2px rgba(16,24,40,.04); }
.lab-card .rot { font-size:.78rem; color:#6b7280; text-transform:uppercase; letter-spacing:.04em; font-weight:600; }
.lab-card .val { font-size:1.65rem; font-weight:750; color:#111827; line-height:1.2; margin-top:2px; }
.lab-card .sub { font-size:.78rem; color:#6b7280; }
.lab-card.alerta { border-color:#ffc9c9; background:#fff5f5; }
.lab-card.alerta .val { color:#c92a2a; font-size:1.05rem; }
.lab-painel { padding:14px; background:#0f1d26; border-radius:16px;
  box-shadow:inset 0 0 0 1px #20343f, 0 8px 24px rgba(15,29,38,.18); overflow-x:auto; }
.lab-grade { display:grid; grid-template-columns:repeat(var(--colunas), minmax(0,1fr));
  width:100%; min-width:var(--minimo); max-width:var(--largura); margin:0 auto; gap:2px; }
.lab-celula { aspect-ratio:1; display:grid; place-items:center; position:relative;
  background:#eef3f1; color:#203741; font:700 var(--fonte) ui-monospace, SFMono-Regular, monospace;
  border-radius:4px; transition: background .2s; }
.lab-celula > span { position:relative; z-index:3; }
.lab-celula.parede { background:#1d313c; }
.lab-celula.partida { background:#3b5bdb; color:#fff; }
.lab-celula.saida { background:#2f9e44; color:#fff; }
.lab-celula.areia { background:#e9d5a8; }
.lab-celula.agua { background:#9fd0e8; }
.lab-celula.chave { background:#ffe58f; color:#7a5200; }
.lab-celula.porta { background:#8d6748; color:#fff; }
.lab-celula.esteira { background:#e2dcff; color:#4b3a8c; }
.lab-celula.peso-negativo { background:#ffd1e3; color:#9c1f55; }
.lab-celula.fora-da-camada { opacity:.3; filter:saturate(.4); }
.lab-rastro, .lab-armadilha, .lab-ciclo-negativo, .lab-arco, .lab-atual {
  position:absolute; pointer-events:none; border-radius:inherit; }
.lab-rastro { inset:0; background:var(--cor); opacity:.55; z-index:1; }
.lab-armadilha { inset:0; z-index:2; box-shadow:inset 0 0 0 2px #e03131;
  background:repeating-linear-gradient(135deg,#e0313160 0 3px,transparent 3px 7px); }
.lab-ciclo-negativo { inset:2px; z-index:2; border:3px solid #ffd43b; border-radius:4px;
  box-shadow:0 0 0 1px #7a4b00; }
.lab-arco { inset:1px; z-index:2; box-shadow:inset 0 0 0 3px var(--arco); }
.lab-atual { width:62%; aspect-ratio:1; border-radius:50%; z-index:4; background:#ffffff;
  border:3px solid var(--cor, #0f1d26); box-sizing:border-box;
  box-shadow:0 0 0 3px rgba(255,255,255,.45), 0 2px 8px rgba(0,0,0,.45);
  animation: lab-pulso 1.4s ease-in-out infinite; }
.lab-atual.encerrado { background:#2f9e44; border-color:#fff; animation:none; }
@keyframes lab-pulso { 0%,100% { transform:scale(1); } 50% { transform:scale(.82); } }
.lab-legenda { display:flex; flex-wrap:wrap; gap:6px 14px; margin:.7rem 0 .2rem; font-size:.8rem; color:#4b5563; }
.lab-legenda span { display:inline-flex; align-items:center; gap:6px; }
.lab-legenda i { width:14px; height:14px; border-radius:4px; display:inline-block; box-shadow:inset 0 0 0 1px rgba(0,0,0,.12); }
.lab-estado { background:#fff; border:1px solid #e6e8ef; border-radius:16px; padding:16px 18px;
  box-shadow:0 1px 2px rgba(16,24,40,.04); }
.lab-estado h4 { margin:0 0 10px; font-size:1rem; color:#111827; }
.lab-estado .linha { display:flex; justify-content:space-between; gap:10px; padding:7px 0;
  border-bottom:1px solid #f1f3f5; font-size:.9rem; }
.lab-estado .linha:last-child { border-bottom:0; }
.lab-estado .rot { color:#6b7280; }
.lab-estado .custo { font-size:2.1rem; font-weight:800; color:#111827; margin:6px 0 2px; }
.lab-estado .barra { height:6px; background:#f1f3f5; border-radius:99px; overflow:hidden; margin-top:8px; }
.lab-estado .barra > div { height:100%; background:linear-gradient(90deg,#3b5bdb,#12a37f); border-radius:99px; }
.lab-tag { display:inline-block; padding:1px 8px; border-radius:6px; font-weight:700; font-size:.82rem;
  color:#fff; margin-left:3px; }
.lab-tag.cinza { background:#e9ecef; color:#495057; }
.lab-camada { margin-bottom:6px; }
.lab-camada-topo { display:flex; align-items:center; flex-wrap:wrap; gap:8px; padding:8px 12px;
  background:#fff; border:1px solid #e6e8ef; border-left:8px solid var(--cor); border-radius:12px 12px 0 0;
  font-size:.9rem; }
.lab-camada-topo b { color:#111827; }
.lab-camada-topo .sub { color:#6b7280; font-size:.78rem; margin-left:auto; }
.lab-camada.ativa .lab-camada-topo { box-shadow:0 0 0 2px var(--cor); }
.lab-camada .lab-painel { border-radius:0 0 14px 14px; }
.lab-camada.ativa .lab-painel { box-shadow:inset 0 0 0 1px #20343f, 0 0 0 2px var(--cor); }
.lab-arco-info { margin-top:10px; padding:8px 10px; border-radius:10px; background:#f8f9fa; font-size:.82rem; }
</style>
"""

CASAS = {
    "#": ("parede", ""),
    ".": ("", ""),
    "S": ("partida", "S"),
    "G": ("saida", "G"),
    ",": ("areia", ""),
    "~": ("agua", ""),
    "+": ("peso-negativo", "+"),
    "*": ("peso-negativo", "*"),
}
CASAS.update({chave: ("chave", chave) for chave in "abcd"})
CASAS.update({porta: ("porta", porta) for porta in "ABCD"})
CASAS.update({casa: ("esteira", seta) for casa, seta in SETAS.items()})


@dataclass(frozen=True)
class Vertice:
    posicao: tuple[int, int]
    casa: str
    chaves: str | None = None
    bonus: tuple[int, ...] | None = None
    alvo: bool = False

    @property
    def bonus_exibido(self):
        if self.bonus is None:
            return "—"
        return ", ".join(map(str, self.bonus)) or "Nenhum"

    @property
    def rotulo(self):
        if self.alvo:
            return "ALVO"
        linha, coluna = self.posicao
        posicao = f"({linha}, {coluna})"
        if self.chaves is None:
            return posicao
        return f"{posicao} · chaves {self.chaves or '∅'} · bônus {self.bonus_exibido}"


@dataclass(frozen=True)
class ArcoDFS:
    origem: Vertice
    destino: Vertice
    movimento: str
    classe: str


@dataclass(frozen=True)
class Quadro:
    estado: Vertice
    custo: int | float
    arco: ArcoDFS | None = None


@dataclass(frozen=True)
class Diagnostico:
    etapa: str
    mensagem: str
    traceback: str | None = None


@dataclass
class Resultado:
    quadros: list[Quadro] = field(default_factory=list)
    camadas: dict[tuple, list[Vertice]] = field(default_factory=dict)
    armadilhas: set[Vertice] | None = None
    erro_armadilhas: Diagnostico | None = None
    erros: list[Diagnostico] = field(default_factory=list)
    aviso: str | None = None
    recusa: str | None = None  # [IA] Claude – mensagem quando o Dijkstra recusa pesos negativos
    custo_minimo: bool = False
    contagem_dfs: dict[str, int] = field(default_factory=dict)
    tem_ciclo_dfs: bool | None = None
    ciclo_negativo: bool = False
    nos_ciclo_negativo: set[Vertice] = field(default_factory=set)
    quadros_ciclo_negativo: list[Quadro] = field(default_factory=list)
    repetiu_predecessor: bool = False


@dataclass
class Grafo:
    lista_nos: list[maze.No]
    vertices: dict[maze.No, Vertice]
    inicio: maze.No
    fim: maze.No
    camadas: dict[tuple, list[Vertice]] = field(default_factory=dict)


def chave_camada(estado):
    """# [IA] Claude – identifica a camada de um estado: (chaves, bônus consumidos)."""
    return estado.chaves, estado.bonus


def posicao(no):
    return no.posicao_linha, no.posicao_coluna


def grafo_padrao(mapa):
    vertices = {
        no: Vertice(posicao(no), no.tipo, alvo=(no is mapa.estado_final))
        for no in mapa.lista_nos
    }
    return Grafo(mapa.lista_nos, vertices, mapa.estado_incial, mapa.estado_final)


def caminho_dos_anteriores(inicio, fim, distancias, anteriores):
    """Lê a sequência já determinada pelo algoritmo."""
    if not isfinite(distancias[fim]):
        return []
    caminho = [fim]
    vistos = {fim}
    while caminho[-1] is not inicio:
        anterior = anteriores.get(caminho[-1])
        if anterior in vistos:
            raise ValueError("A cadeia de predecessores devolvida contém um ciclo.")
        if anterior is None:
            raise ValueError("A cadeia de predecessores devolvida termina antes de S.")
        vistos.add(anterior)
        caminho.append(anterior)
    return caminho[::-1]


def cadeia_dos_predecessores(fim, anteriores):
    """Lê o dicionário a partir do alvo e inclui a primeira repetição."""
    cadeia = []
    vistos = set()
    atual = fim
    while atual is not None:
        cadeia.append(atual)
        if atual in vistos:
            return cadeia, True
        vistos.add(atual)
        atual = anteriores[atual]
    return cadeia, False


def movimento_e_peso(origem, destino):
    for movimento, indice in origem.dicionario_direcoes.items():
        arco = origem.lista_arestas[indice]
        if arco != 0 and arco.destino is destino:
            return movimento, arco.custo
    raise ValueError("O algoritmo devolveu uma transição ausente no grafo.")


def quadros_do_caminho(caminho, grafo, distancias=None):
    if distancias is None:
        pesos = (movimento_e_peso(u, v)[1] for u, v in pairwise(caminho))
        custos = accumulate(pesos, initial=0)
    else:
        custos = (distancias[no] for no in caminho)

    quadros = []
    for no, custo in zip(caminho, custos):
        estado = grafo.vertices[no]
        if no is grafo.fim and grafo.camadas and quadros:
            # ALVO é virtual. A interface mantém o inventário do G de onde ele veio.
            ultimo = quadros[-1].estado
            estado = Vertice(estado.posicao, estado.casa, ultimo.chaves, ultimo.bonus, alvo=True)
        quadros.append(Quadro(estado, custo))
    return quadros


def executar(algoritmo, grafo, resultado):
    com_estados = bool(grafo.camadas)
    nos = grafo.lista_nos

    if algoritmo == "DFS":
        dfs = graph_algorithms.dfs(nos, grafo.inicio, detalhado=True)
        distancias = dfs["distancias"]
        resultado.quadros.append(Quadro(grafo.vertices[grafo.inicio], distancias[grafo.inicio]))
        for u, v, classe in dfs["classificacao"]:
            movimento, _ = movimento_e_peso(u, v)
            if v is grafo.fim and com_estados:
                movimento = "ALVO"
            arco = ArcoDFS(grafo.vertices[u], grafo.vertices[v], movimento, classe)
            atual = v if classe == "arvore" else u
            estado = grafo.vertices[atual]
            if atual is grafo.fim and com_estados:
                estado = Vertice(estado.posicao, estado.casa, arco.origem.chaves, arco.origem.bonus, alvo=True)
            resultado.quadros.append(Quadro(estado, distancias[atual], arco))
        resultado.contagem_dfs = dfs["contagem"]
        resultado.tem_ciclo_dfs = dfs["tem_ciclo"]
        return

    if algoritmo == "BFS":
        # A BFS original recebe uma lista de invólucros de No, inclusive no grafo padrão.
        modelos = {no: maze.No_estados("-", "-", "Não Visitado", no) for no in nos}
        caminho = graph_algorithms.bfs(modelos.values(), modelos[grafo.inicio], modelos[grafo.fim])
        resultado.quadros = quadros_do_caminho(caminho or [], grafo)
        return

    if algoritmo == "Dijkstra":
        distancias, anteriores,tem_pesos_negativos = graph_algorithms.dijkstra(nos, grafo.inicio)
        # [IA] Claude – o dijkstra do grupo devolve (None, None, True) quando recusa o grafo
        if distancias is None:
            resultado.recusa = (
                "RECUSA: o Dijkstra não aceita arcos com peso negativo, e este grafo tem "
                "bônus (+) ou fonte (*). Use o Bellman-Ford para este mapa."
            )
            return
        if tem_pesos_negativos:
            resultado.aviso = (
                "O Dijkstra retornou um resultado para um grafo com pesos negativos."
                "O custo devolvido pode divergir do mínimo."
            )
    elif algoritmo == "Bellman-Ford":
        distancias, anteriores, tem_ciclo, ciclo = graph_algorithms.bellman_ford(nos, grafo.inicio)
        resultado.ciclo_negativo = tem_ciclo
        if tem_ciclo:
            resultado.quadros_ciclo_negativo = quadros_do_caminho(ciclo, grafo)
            resultado.nos_ciclo_negativo = {quadro.estado for quadro in resultado.quadros_ciclo_negativo}
            if isfinite(distancias[grafo.fim]):
                cadeia, resultado.repetiu_predecessor = cadeia_dos_predecessores(grafo.fim, anteriores)
                resultado.quadros = quadros_do_caminho(cadeia[::-1], grafo, distancias)
            return
    else:
        raise ValueError(f"Algoritmo desconhecido: {algoritmo}")

    caminho = caminho_dos_anteriores(grafo.inicio, grafo.fim, distancias, anteriores)
    resultado.quadros = quadros_do_caminho(caminho, grafo, distancias)
    resultado.custo_minimo = bool(caminho) and resultado.aviso is None


def registrar_erro(etapa, erro):
    return Diagnostico(etapa, f"{type(erro).__name__}: {erro}", format_exc())


def carregar(caminho, algoritmo, com_estados):
    if not maze.validar_labirinto(caminho):
        return None, None

    # [IA] Antigravity (Gemini) – ignora comentários (;) e linhas vazias para alinhar a grade com labirinto.py
    linhas = [
        linha
        for linha in Path(caminho).read_text(encoding="utf-8").splitlines()
        if linha.strip() and not linha.startswith(";")
    ]
    resultado = Resultado()
    try:
        mapa = maze.gerar_labirinto(caminho)
    except Exception as erro:
        resultado.erros.append(registrar_erro("gerar_labirinto", erro))
    if resultado.erros:
        return linhas, resultado

    if com_estados:
        try:
            modelos, origem, saida = maze.preparar_estados(mapa)
            transicoes, camadas = graph_algorithms.bfs_grafo_estados_exploracao(modelos, origem, saida)
            lista_nos, inicio, alvo, nos_por_estado = graph_algorithms.converter_grafo_estados(
                transicoes, camadas, origem, saida
            )

            vertices = {alvo: Vertice(posicao(alvo), "G", alvo=True)}
            camadas_visuais = {}
            # Camadas vêm prontas do backend: (chaves, bônus consumidos)
            for camada in camadas:
                camada_visual = camadas_visuais.setdefault((camada.chaves, tuple(sorted(camada.bonus))), [])
                for estado in camada.lista_nos_estados:
                    casa = estado.no_pos
                    vertice = Vertice(posicao(casa), casa.tipo, estado.chaves, tuple(sorted(estado.bonus)))
                    vertices[nos_por_estado[estado]] = vertice
                    camada_visual.append(vertice)
            grafo = Grafo(lista_nos, vertices, inicio, alvo, camadas_visuais)
        except Exception as erro:
            resultado.erros.append(registrar_erro("Construção do grafo de estados", erro))
            return linhas, resultado
        resultado.camadas = grafo.camadas
        try:
            armadilhas = graph_algorithms.bfs_estados_armadilha(transicoes, camadas)
            if armadilhas is None:
                resultado.erro_armadilhas = Diagnostico(
                    "bfs_estados_armadilha", "A função retornou None. O realce está indisponível."
                )
            else:
                resultado.armadilhas = {grafo.vertices[nos_por_estado[estado]] for estado in armadilhas}
        except Exception as erro:
            resultado.erro_armadilhas = registrar_erro("bfs_estados_armadilha", erro)
    else:
        grafo = grafo_padrao(mapa)

    try:
        executar(algoritmo, grafo, resultado)
    except Exception as erro:
        resultado.erros.append(registrar_erro(algoritmo, erro))
    return linhas, resultado


def desenhar(linhas, resultado, indice, camada, realcar, realcar_ciclo, painel=1):
    quadros = resultado.quadros
    quadro = quadros[indice] if quadros else None
    atual = quadro.estado if quadro else None
    arco = quadro.arco if quadro else None

    def visivel(estado):
        return camada is None or chave_camada(estado) == camada

    # [IA] Claude – guarda a camada da última passagem para colorir o rastro
    visitas = {}
    for q in quadros[:indice + 1]:
        if visivel(q.estado):
            visitas[q.estado.posicao] = chave_camada(q.estado)
    estados_por_posicao = {}
    for chaves, estados in resultado.camadas.items():
        if camada is None or chaves == camada:
            for estado in estados:
                estados_por_posicao[estado.posicao] = estados_por_posicao.get(estado.posicao, 0) + 1
    armadilhas_por_posicao = {}
    if realcar and resultado.armadilhas is not None:
        for estado in resultado.armadilhas:
            if visivel(estado):
                armadilhas_por_posicao[estado.posicao] = armadilhas_por_posicao.get(estado.posicao, 0) + 1

    ciclo_por_posicao = {}
    if realcar_ciclo and resultado.nos_ciclo_negativo:
        for estado in resultado.nos_ciclo_negativo:
            if visivel(estado):
                ciclo_por_posicao[estado.posicao] = ciclo_por_posicao.get(estado.posicao, 0) + 1

    extremidades = {}
    if arco:
        cor = CLASSES_DFS[arco.classe][1]
        extremidades = {estado.posicao: cor for estado in (arco.origem, arco.destino) if visivel(estado)}

    colunas = len(linhas[0])
    fonte = max(5, min(17, round(820 / (colunas * painel))))
    html = [
        '<div class="lab-painel" tabindex="0" aria-label="Mapa do labirinto">',
        f'<div class="lab-grade" style="--colunas:{colunas};--largura:{max(560, colunas * 52)}px;'
        f'--minimo:{colunas * (8 if painel > 1 else 12)}px;--fonte:{fonte}px">',
    ]
    for r, linha in enumerate(linhas):
        for c, casa in enumerate(linha):
            pos = (r, c)
            classe, simbolo = CASAS.get(casa, ("", escape(casa)))
            titulo = f"Linha {r}, coluna {c} · {casa}"
            if classe != "parede" and resultado.camadas:
                quantidade = estados_por_posicao.get(pos, 0)
                titulo += f" · estados na vista {quantidade}"
                if not quantidade:
                    classe += " fora-da-camada"

            conteudo = [f"<span>{simbolo}</span>" if simbolo else ""]
            if pos in visitas:
                cor = cor_camada(visitas[pos], resultado.camadas)
                conteudo.append(f'<i class="lab-rastro" style="--cor:{cor}"></i>')
            if pos in armadilhas_por_posicao:
                titulo += f" · estados-armadilha {armadilhas_por_posicao[pos]}"
                conteudo.append('<i class="lab-armadilha"></i>')
            if pos in ciclo_por_posicao:
                titulo += f" · estados do ciclo negativo {ciclo_por_posicao[pos]}"
                conteudo.append('<i class="lab-ciclo-negativo"></i>')
            if pos in extremidades:
                conteudo.append(f'<i class="lab-arco" style="--arco:{extremidades[pos]}"></i>')
            if atual and atual.posicao == pos and visivel(atual):
                titulo += " · estado atual"
                marcador = "lab-atual encerrado" if atual.alvo else "lab-atual"
                cor = cor_camada(chave_camada(atual), resultado.camadas)
                conteudo.append(f'<i class="{marcador}" style="--cor:{cor}"></i>')
            html.append(f'<div class="lab-celula {classe}" title="{escape(titulo)}">{"".join(conteudo)}</div>')
    html.append("</div></div>")
    return "".join(html)


def ordem_camadas(camadas):
    """# [IA] Claude – ordena as camadas: menos chaves, depois menos bônus, depois alfabético."""
    return sorted(camadas, key=lambda k: (len(k[0] or ""), k[0] or "", len(k[1] or ()), k[1] or ()))


def cor_camada(chave, camadas):
    """# [IA] Claude – cor fixa de cada camada (sem camadas: cor padrão)."""
    ordem = ordem_camadas(camadas) if camadas else []
    if chave not in ordem:
        return CORES_CAMADAS[0]
    return CORES_CAMADAS[ordem.index(chave) % len(CORES_CAMADAS)]


def nome_camada(chave):
    chaves, bonus = chave
    partes = [f"Chaves {', '.join(chaves)}" if chaves else "Sem chaves"]
    if bonus:
        partes.append(f"bônus {', '.join(map(str, bonus))}")
    return " · ".join(partes)


def tag_chaves(estado, camadas):
    """# [IA] Claude – chaves como etiquetas coloridas."""
    if estado.chaves is None:
        return "—"
    if not estado.chaves:
        return '<span class="lab-tag cinza">nenhuma</span>'
    cor = cor_camada(chave_camada(estado), camadas)
    return "".join(f'<span class="lab-tag" style="background:{cor}">{escape(c)}</span>' for c in estado.chaves)


def cabecalho_camada(chave, resultado, atual):
    """# [IA] Claude – título de cada painel de camada (cor, nome, nº de estados, marca de ativa)."""
    cor = cor_camada(chave, resultado.camadas)
    ativa = ' <span class="lab-tag" style="background:#111827">atual</span>' if chave == atual else ""
    return (f'<div class="lab-camada{" ativa" if chave == atual else ""}" style="--cor:{cor}">'
            f'<div class="lab-camada-topo"><b>{escape(nome_camada(chave))}</b>{ativa}'
            f'<span class="sub">{len(resultado.camadas[chave])} estados</span></div></div>')


def mostrar_estado(quadro, algoritmo, camadas, passo, total, cadeia_de_predecessores=False):
    """# [IA] Claude – painel do estado atual em cartão (posição, chaves, bônus, custo)."""
    estado = quadro.estado
    linha, coluna = estado.posicao
    if cadeia_de_predecessores:
        rotulo_custo = "Distância registrada (Bellman-Ford)"
    elif algoritmo == "DFS":
        rotulo_custo = "Custo acumulado na árvore DFS"
    else:
        rotulo_custo = "Custo acumulado"
    custo = quadro.custo
    custo_txt = f"{custo:g}" if isinstance(custo, (int, float)) and isfinite(custo) else str(custo)
    posicao_txt = "ALVO" if estado.alvo else f"({linha}, {coluna})"
    casa_txt = "" if estado.alvo else f' <span class="lab-tag cinza">{escape(estado.casa)}</span>'
    progresso = 100 if total <= 0 else round(100 * passo / total)
    html = [
        '<div class="lab-estado">',
        f'<h4>Estado atual · passo {passo} de {max(total, 0)}</h4>',
        f'<div class="rot" style="font-size:.78rem;color:#6b7280">{rotulo_custo}</div>',
        f'<div class="custo">{custo_txt}</div>',
        f'<div class="barra"><div style="width:{progresso}%"></div></div>',
        '<div style="margin-top:10px">',
        f'<div class="linha"><span class="rot">Posição</span><span>{posicao_txt}{casa_txt}</span></div>',
        f'<div class="linha"><span class="rot">Chaves</span><span>{tag_chaves(estado, camadas)}</span></div>',
        f'<div class="linha"><span class="rot">Bônus consumidos</span><span>{escape(estado.bonus_exibido)}</span></div>',
        '</div>',
    ]
    if quadro.arco:
        arco = quadro.arco
        nome, cor = CLASSES_DFS[arco.classe]
        html.append(
            f'<div class="lab-arco-info"><b style="color:{cor}">Arco de {nome.lower()}</b> · {escape(arco.movimento)}'
            f'<br>de {escape(arco.origem.rotulo)}<br>para {escape(arco.destino.rotulo)}</div>'
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def legenda_html(resultado, realcar, realcar_ciclo, camada):
    """# [IA] Claude – legenda com as cores do mapa e das camadas."""
    itens = [("#3b5bdb", "S partida"), ("#2f9e44", "G saída"), ("#e9d5a8", "lama (3)"),
             ("#9fd0e8", "água (5)"), ("#ffe58f", "chave"), ("#8d6748", "porta"),
             ("#e2dcff", "esteira"), ("#ffd1e3", "bônus + / fonte *")]
    partes = [f'<span><i style="background:{c}"></i>{t}</span>' for c, t in itens]
    if resultado.camadas:
        partes.append('<span><i style="background:linear-gradient(90deg,#f76707,#7048e8,#12a37f)"></i>'
                      'rastro (a cor é a da camada)</span>')
    else:
        partes.append(f'<span><i style="background:{CORES_CAMADAS[0]}"></i>rastro</span>')
    if realcar and resultado.armadilhas is not None:
        partes.append('<span><i style="background:repeating-linear-gradient(135deg,#e03131 0 3px,#fff 3px 7px)"></i>estado-armadilha</span>')
    if realcar_ciclo and resultado.nos_ciclo_negativo:
        partes.append('<span><i style="background:#fff;box-shadow:inset 0 0 0 3px #ffd43b"></i>ciclo negativo</span>')
    return '<div class="lab-legenda">' + "".join(partes) + "</div>"


def cards_html(cards):
    """# [IA] Claude – linha de cartões de métricas. cards: lista de (rótulo, valor, subtítulo, alerta)."""
    html = ['<div class="lab-cards">']
    for rotulo, valor, sub, alerta in cards:
        classe = "lab-card alerta" if alerta else "lab-card"
        sub_html = f'<div class="sub">{escape(sub)}</div>' if sub else ""
        html.append(f'<div class="{classe}"><div class="rot">{escape(rotulo)}</div>'
                    f'<div class="val">{escape(str(valor))}</div>{sub_html}</div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def controlar_animacao(ultimo, periodo):
    sessao = st.session_state
    if sessao.tocando and monotonic() >= sessao.proximo_passo:
        sessao.passo = min(sessao.passo + 1, ultimo)
        sessao.proximo_passo = monotonic() + periodo
        if sessao.passo == ultimo:
            sessao.tocando = False
            st.rerun()

    def mover(indice):
        sessao.passo = indice
        if sessao.tocando:
            sessao.tocando = False
            sessao.pausar_timer = True

    inicio, anterior, reproduzir, seguinte = st.columns(4)
    with inicio:
        st.button("Início", disabled=sessao.passo == 0, on_click=mover, args=(0,), use_container_width=True)
    with anterior:
        st.button("Voltar", disabled=sessao.passo == 0, on_click=mover,
                  args=(max(0, sessao.passo - 1),), use_container_width=True)
    with reproduzir:
        texto = "Pausar" if sessao.tocando else "Reproduzir"
        if st.button(texto, type="primary", use_container_width=True):
            if sessao.passo == ultimo:
                sessao.passo = 0
            sessao.tocando = not sessao.tocando
            sessao.proximo_passo = monotonic() + periodo
            st.rerun()
    with seguinte:
        st.button("Avançar", disabled=sessao.passo == ultimo, on_click=mover,
                  args=(min(ultimo, sessao.passo + 1),), use_container_width=True)

    if sessao.pausar_timer:
        sessao.pausar_timer = False
        st.rerun()

    def pausar():
        mover(sessao.passo)

    st.slider("Quadro", min_value=0, max_value=ultimo, key="passo", on_change=pausar)


def mostrar_diagnostico(diagnostico, fatal=True):
    exibir = st.error if fatal else st.warning
    exibir(f"{diagnostico.etapa} · {diagnostico.mensagem}")
    if diagnostico.traceback:
        with st.expander(f"Debug · {diagnostico.etapa}"):
            st.code(diagnostico.traceback, language="python")


def mostrar_resultado(resultado, algoritmo):
    if resultado.recusa:  # [IA] Claude
        cards_html([("Status", "RECUSA", None, True)])
        st.error(resultado.recusa)
        return
    if resultado.aviso:
        st.warning(resultado.aviso)
    if resultado.erro_armadilhas:
        mostrar_diagnostico(resultado.erro_armadilhas, fatal=False)
    if resultado.erros:
        for diagnostico in resultado.erros:
            mostrar_diagnostico(diagnostico)
        return
    if resultado.tem_ciclo_dfs is not None:
        # [IA] Claude – contagem da DFS em cartões
        ciclo = "Sim" if resultado.tem_ciclo_dfs else "Não"
        cards_html([("Ciclo encontrado", ciclo, None, False)] + [
            (f"Arcos de {CLASSES_DFS[classe][0].lower()}", total, None, False)
            for classe, total in resultado.contagem_dfs.items()
        ])
        st.caption("A DFS examina os vizinhos na ordem N, L, S, O.")
        with st.expander("Classificação dos arcos em ordem de exame"):
            linhas = []
            for quadro in resultado.quadros[1:]:
                arco = quadro.arco
                linhas.append({
                    "Origem": arco.origem.rotulo,
                    "Destino": arco.destino.rotulo,
                    "Movimento": arco.movimento,
                    "Classificação": CLASSES_DFS[arco.classe][0],
                })
            if linhas:
                st.dataframe(linhas, hide_index=True, use_container_width=True)
            else:
                st.info("Nenhum arco examinado.")
        return
    if resultado.ciclo_negativo:
        st.warning("O Bellman-Ford detectou um ciclo negativo alcançável a partir de S.")
        if resultado.quadros_ciclo_negativo:
            cards_html([("Status", "CICLO NEGATIVO", None, True),  # [IA] Claude
                        ("Custo do ciclo", resultado.quadros_ciclo_negativo[-1].custo, None, False),
                        ("Estados no ciclo", len(resultado.nos_ciclo_negativo), None, False)])
            with st.expander("Sequência do ciclo negativo"):
                st.text("\n".join(quadro.estado.rotulo for quadro in resultado.quadros_ciclo_negativo))
        st.subheader("Cadeia de predecessores a partir de ALVO")
        if not resultado.quadros:
            st.info("O Bellman-Ford registrou ALVO como inalcançável.")
            return
        st.caption("A animação começa em ALVO e segue as referências devolvidas em anteriores.")
        if resultado.repetiu_predecessor:
            ultimo = resultado.quadros[-1].estado.rotulo
            st.info(f"A cadeia repete {ultimo}. A animação termina nessa repetição.")
        with st.expander("Sequência de predecessores"):
            st.text("\n".join(quadro.estado.rotulo for quadro in resultado.quadros))
        return
    if algoritmo == "Bellman-Ford":
        st.info("O Bellman-Ford não detectou ciclos negativos alcançáveis a partir de S.")
    if not resultado.quadros:
        st.info("O retorno do algoritmo não contém um caminho até ALVO.")
        return

    # [IA] Claude – cartões no lugar dos st.metric
    custo_final = resultado.quadros[-1].custo
    cards = [
        ("Menor número de passos" if algoritmo == "BFS" else "Passos", len(resultado.quadros) - 1,
         "inclui G → ALVO (custo 0)" if resultado.camadas else None, False),
        ("Menor custo" if resultado.custo_minimo else "Custo do caminho",
         f"{custo_final:g}" if isinstance(custo_final, (int, float)) else custo_final, None, False),
    ]
    if resultado.camadas:
        cards.append(("Estados no grafo", sum(len(v) for v in resultado.camadas.values()), None, False))
        cards.append(("Camadas", len(resultado.camadas), None, False))
    if resultado.armadilhas is not None:
        cards.append(("Estados-armadilha", len(resultado.armadilhas), None, False))
    cards_html(cards)


def main():
    st.set_page_config(page_title="Labirinto interativo", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    # [IA] Claude – lista mapas de todas as pastas conhecidas (sem repetir nome)
    mapas, vistos = [], set()
    for pasta in PASTAS_MAPAS:
        if pasta.is_dir():
            for caminho in sorted(pasta.rglob("*.txt")):
                chave = caminho.relative_to(pasta).as_posix() if pasta.name != "mapas_grupo" else f"grupo/{caminho.name}"
                if chave not in vistos:
                    vistos.add(chave)
                    mapas.append(caminho)
    if not mapas:
        st.warning("Nenhum mapa encontrado em data/mapas/ ou data/mapas_grupo/.")
        return

    with st.sidebar:
        st.header("Configuração")
        mapa = st.selectbox("Mapa", mapas, format_func=lambda caminho: (
            f"{caminho.stem}  (grupo)" if caminho.parent.name == "mapas_grupo" else caminho.stem))
        tipo = st.radio("Tipo de grafo", ("Grafo de estados", "Grafo padrão"))
        algoritmo = st.selectbox("Algoritmo", ALGORITMOS)
        velocidade = st.slider("Velocidade (quadros/s)", 0.25, 4.0, 1.0, 0.25)
        realcar = st.toggle("Realçar estados-armadilha", value=True) if tipo == "Grafo de estados" else False
        realcar_ciclo = st.toggle("Realçar nós do ciclo negativo", value=True) if algoritmo == "Bellman-Ford" else False

    sessao = st.session_state
    try:
        arquivo = mapa.stat()
        versao = (arquivo.st_mtime_ns, arquivo.st_size)
        com_estados = tipo == "Grafo de estados"
        selecao = (str(mapa), versao, algoritmo, com_estados)
        if sessao.get("selecao") != selecao or "resultado_mapa" not in sessao:
            sessao.update(passo=0, tocando=False, pausar_timer=False)
            sessao.pop("camada_modo", None)
            with st.spinner("Executando o algoritmo…"):
                sessao.resultado_mapa = carregar(mapa, algoritmo, com_estados)
            sessao.selecao = selecao
        linhas, resultado = sessao.resultado_mapa
    except Exception as erro:
        st.error(f"Falha ao preparar {mapa.name} para {algoritmo} · {type(erro).__name__}: {erro}")
        with st.expander("Debug · traceback completo"):
            st.code(format_exc(), language="python")
        return
    if resultado is None:
        st.error(f"O mapa {mapa.name} foi reprovado por validar_labirinto.")
        return

    # [IA] Claude – cabeçalho com o que está selecionado
    st.markdown(
        f'<div class="lab-topo"><h1>Labirinto interativo</h1>'
        f'<span class="lab-chip">{escape(mapa.stem)}</span>'
        f'<span class="lab-chip alg">{escape(algoritmo)}</span>'
        f'<span class="lab-chip tipo">{escape(tipo)}</span></div>',
        unsafe_allow_html=True,
    )
    mostrar_resultado(resultado, algoritmo)
    periodo = 1.0 / velocidade

    def visualizacao():
        quadros = resultado.quadros
        if len(quadros) > 1:
            controlar_animacao(len(quadros) - 1, periodo)
        passo = sessao.get("passo", 0)
        quadro = quadros[passo] if quadros else None

        # [IA] Claude – um painel por camada (chaves + bônus), em vez de um seletor único
        atual = chave_camada(quadro.estado) if quadro else None
        ordem = ordem_camadas(resultado.camadas)
        exibidas = ordem
        if resultado.camadas:
            modo = st.radio("Camadas exibidas", MODOS_CAMADAS, horizontal=True, key="camada_modo",
                            index=0 if len(ordem) <= 6 else 1)
            visitadas = {chave_camada(q.estado) for q in quadros[:passo + 1]}
            if modo == MODOS_CAMADAS[1]:
                exibidas = [c for c in ordem if c in visitadas or c == atual]
            elif modo == MODOS_CAMADAS[2]:
                exibidas = [c for c in ordem if c == atual]

        mapa_col, estado_col = st.columns([3, 1], gap="large")
        with mapa_col:
            if not resultado.camadas:
                st.markdown(desenhar(linhas, resultado, passo, None, realcar, realcar_ciclo), unsafe_allow_html=True)
            else:
                largura = 1 if len(exibidas) <= 1 else 2
                for inicio in range(0, len(exibidas), largura):
                    for coluna, chave in zip(st.columns(largura), exibidas[inicio:inicio + largura]):
                        with coluna:
                            st.markdown(cabecalho_camada(chave, resultado, atual), unsafe_allow_html=True)
                            st.markdown(desenhar(linhas, resultado, passo, chave, realcar, realcar_ciclo, largura),
                                        unsafe_allow_html=True)
                if not exibidas:
                    st.info("Nenhuma camada na vista.")
            st.markdown(legenda_html(resultado, realcar, realcar_ciclo, None), unsafe_allow_html=True)
            if realcar and resultado.armadilhas is not None:
                armadilhas = [e.rotulo for e in sorted(resultado.armadilhas, key=lambda e: (e.posicao, e.chaves, e.bonus))
                              if not resultado.camadas or chave_camada(e) in exibidas]
                with st.expander(f"Estados-armadilha na vista ({len(armadilhas)})"):
                    if armadilhas:
                        st.dataframe({"Estado": armadilhas}, hide_index=True, use_container_width=True)
                    else:
                        st.write("Nenhum estado-armadilha na vista.")
            if realcar_ciclo and resultado.nos_ciclo_negativo:
                estados_ciclo = [e.rotulo for e in sorted(resultado.nos_ciclo_negativo, key=lambda e: (e.posicao, e.chaves or "", e.bonus or ()))
                                 if not resultado.camadas or chave_camada(e) in exibidas]
                with st.expander(f"Nós do ciclo negativo na vista ({len(estados_ciclo)})"):
                    if estados_ciclo:
                        st.dataframe({"Estado": estados_ciclo}, hide_index=True, use_container_width=True)
                    else:
                        st.write("Nenhum nó do ciclo negativo na vista.")
        with estado_col:
            if quadro:
                mostrar_estado(quadro, algoritmo, resultado.camadas, passo, len(quadros) - 1,
                               cadeia_de_predecessores=resultado.ciclo_negativo)

    if hasattr(st, "fragment"):
        st.fragment(run_every=periodo if sessao.tocando else None)(visualizacao)()
    else:
        visualizacao()
        if sessao.tocando:
            sleep(max(0.0, sessao.proximo_passo - monotonic()))
            st.rerun()


if __name__ == "__main__":
    main()
