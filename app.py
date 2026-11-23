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
PASTA_MAPAS = RAIZ / "mapas"

ALGORITMOS = ("BFS", "Dijkstra", "Bellman-Ford", "DFS")
CLASSES_DFS = {
    "arvore": ("Árvore", "#117a67"),
    "retorno": ("Retorno", "#b43459"),
    "avanco": ("Avanço", "#3458ad"),
    "cruzamento": ("Cruzamento", "#985121"),
}
SETAS = {"^": "↑", ">": "→", "v": "↓", "<": "←"}
SEGUIR_CAMADA = "Acompanhar o estado atual"
TODAS_CAMADAS = "Todas as camadas"

CSS = """
<style>
.lab-painel {
  overflow-x: auto; padding: 12px; background: #15232c;
  border: 1px solid #2c424d; border-radius: 12px;
}
.lab-grade {
  display: grid; grid-template-columns: repeat(var(--colunas), minmax(0, 1fr));
  width: min(100%, var(--largura)); min-width: var(--minimo); gap: 1px;
}
.lab-celula {
  aspect-ratio: 1; display: grid; place-items: center; position: relative;
  background: #e9f1ef; color: #203741;
  font: 750 var(--fonte) ui-monospace, monospace; border-radius: 2px;
}
.lab-celula.parede { background: #2e414b; }
.lab-celula.partida { background: #334b77; color: #fff; }
.lab-celula.saida { background: #196d57; color: #fff; }
.lab-celula.areia { background: #eedbb0; }
.lab-celula.agua { background: #a6ccdd; }
.lab-celula.chave { background: #fbe193; color: #644818; }
.lab-celula.porta { background: #90684b; color: #fff; }
.lab-celula.esteira { background: #dfd8fa; color: #4f3b80; }
.lab-celula.peso-negativo { background: #f0c7df; color: #652451; }
.lab-celula.fora-da-camada { opacity: .37; }
.lab-rastro, .lab-armadilha, .lab-arco, .lab-atual {
  position: absolute; pointer-events: none; border-radius: inherit;
}
.lab-rastro { inset: 0; background: #148a80; opacity: .25; }
.lab-armadilha {
  inset: 0; box-shadow: inset 0 0 0 1px #a42141;
  background: repeating-linear-gradient(135deg, #bf335d70 0 2px, transparent 2px 6px);
}
.lab-arco { inset: 1px; box-shadow: inset 0 0 0 2px var(--arco); }
.lab-atual {
  width: 52%; aspect-ratio: 1; border-radius: 50%; background: #113f49;
  border: 2px solid #fff; box-sizing: border-box; box-shadow: 0 0 0 1px #113f49;
}
.lab-atual.encerrado { background: #2a9b64; }
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
    camadas: dict[str, list[Vertice]] = field(default_factory=dict)
    armadilhas: set[Vertice] | None = None
    erro_armadilhas: Diagnostico | None = None
    erros: list[Diagnostico] = field(default_factory=list)
    aviso: str | None = None
    custo_minimo: bool = False
    contagem_dfs: dict[str, int] = field(default_factory=dict)
    tem_ciclo_dfs: bool | None = None
    ciclo_negativo: bool = False


@dataclass
class Grafo:
    lista_nos: list[maze.No]
    vertices: dict[maze.No, Vertice]
    inicio: maze.No
    fim: maze.No
    camadas: dict[str, list[Vertice]] = field(default_factory=dict)


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
        if tem_pesos_negativos:
            resultado.aviso = (
                "O Dijkstra retornou um resultado para um grafo com pesos negativos."
                "O custo devolvido pode divergir do mínimo."
            )
    elif algoritmo == "Bellman-Ford":
        distancias, anteriores, tem_ciclo, ciclo = graph_algorithms.bellman_ford(nos, grafo.inicio)
        resultado.ciclo_negativo = tem_ciclo
        if tem_ciclo:
            resultado.quadros = quadros_do_caminho(ciclo, grafo)
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

    linhas = Path(caminho).read_text(encoding="utf-8").splitlines()
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
            for camada in camadas:
                camada_visual = camadas_visuais.setdefault(camada.chaves, [])
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


def desenhar(linhas, resultado, indice, camada, realcar):
    quadros = resultado.quadros
    quadro = quadros[indice] if quadros else None
    atual = quadro.estado if quadro else None
    arco = quadro.arco if quadro else None

    def visivel(estado):
        return camada is None or estado.chaves == camada

    visitas = {q.estado.posicao for q in quadros[:indice + 1] if visivel(q.estado)}
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

    extremidades = {}
    if arco:
        cor = CLASSES_DFS[arco.classe][1]
        extremidades = {estado.posicao: cor for estado in (arco.origem, arco.destino) if visivel(estado)}

    colunas = len(linhas[0])
    fonte = max(7, min(16, round(780 / colunas)))
    html = [
        '<div class="lab-painel" tabindex="0" aria-label="Mapa do labirinto">',
        f'<div class="lab-grade" style="--colunas:{colunas};--largura:{colunas * 42}px;'
        f'--minimo:{colunas * 10}px;--fonte:{fonte}px">',
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

            conteudo = [simbolo]
            if pos in visitas:
                conteudo.append('<i class="lab-rastro"></i>')
            if pos in armadilhas_por_posicao:
                titulo += f" · estados-armadilha {armadilhas_por_posicao[pos]}"
                conteudo.append('<i class="lab-armadilha"></i>')
            if pos in extremidades:
                conteudo.append(f'<i class="lab-arco" style="--arco:{extremidades[pos]}"></i>')
            if atual and atual.posicao == pos and visivel(atual):
                titulo += " · estado atual"
                marcador = "lab-atual encerrado" if atual.alvo else "lab-atual"
                conteudo.append(f'<i class="{marcador}"></i>')
            html.append(f'<div class="lab-celula {classe}" title="{escape(titulo)}">{"".join(conteudo)}</div>')
    html.append("</div></div>")
    return "".join(html)


def nome_camada(chaves):
    return f"Chaves {', '.join(chaves)}" if chaves else "Sem chaves"


def mostrar_estado(quadro, algoritmo):
    st.subheader("Estado atual")
    estado = quadro.estado
    linha, coluna = estado.posicao
    if estado.alvo:
        st.markdown(f"**ALVO** · linha {linha}, coluna {coluna}")
    else:
        st.markdown(f"**Linha {linha}, coluna {coluna}** · casa `{estado.casa}`")
    chaves = "—" if estado.chaves is None else nome_camada(estado.chaves)
    st.markdown(f"**Chaves** · {chaves}  \n**Bônus consumidos** · {estado.bonus_exibido}")
    rotulo_custo = "Custo acumulado na árvore DFS" if algoritmo == "DFS" else "Custo acumulado"
    st.metric(rotulo_custo, quadro.custo)
    if quadro.arco:
        arco = quadro.arco
        st.write(f"**{CLASSES_DFS[arco.classe][0]} · {arco.movimento}**")
        st.text(f"De {arco.origem.rotulo}\nPara {arco.destino.rotulo}")


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
    if resultado.aviso:
        st.warning(resultado.aviso)
    if resultado.erro_armadilhas:
        mostrar_diagnostico(resultado.erro_armadilhas, fatal=False)
    if resultado.erros:
        for diagnostico in resultado.erros:
            mostrar_diagnostico(diagnostico)
        return
    if resultado.tem_ciclo_dfs is not None:
        st.subheader("Arcos examinados pela DFS")
        ciclo = "Sim" if resultado.tem_ciclo_dfs else "Não"
        st.write(f"**Ciclo encontrado** · {ciclo}")
        colunas = st.columns(4)
        for coluna, (classe, total) in zip(colunas, resultado.contagem_dfs.items()):
            coluna.metric(CLASSES_DFS[classe][0], total)
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
        if resultado.quadros:
            st.metric("Custo do ciclo", resultado.quadros[-1].custo)
            with st.expander("Sequência do ciclo"):
                st.text("\n".join(q.estado.rotulo for q in resultado.quadros))
        return
    if algoritmo == "Bellman-Ford":
        st.info("O Bellman-Ford não detectou ciclos negativos alcançáveis a partir de S.")
    if not resultado.quadros:
        st.info("O retorno do algoritmo não contém um caminho até ALVO.")
        return

    st.subheader("Caminho até ALVO")
    passos, custo = st.columns(2)
    passos.metric("Menor número de passos" if algoritmo == "BFS" else "Passos", len(resultado.quadros) - 1)
    custo.metric("Menor custo" if resultado.custo_minimo else "Custo do caminho", resultado.quadros[-1].custo)
    if resultado.camadas:
        st.caption("A contagem inclui a transição G → ALVO, com custo zero.")


def main():
    st.set_page_config(page_title="Labirinto interativo", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    st.title("Labirinto interativo")
    mapas = sorted(caminho for caminho in PASTA_MAPAS.rglob("*") if caminho.is_file())
    if not mapas:
        st.warning("Nenhum mapa encontrado na pasta mapas/.")
        return

    with st.sidebar:
        st.header("Configuração")
        mapa = st.selectbox("Mapa", mapas, format_func=lambda caminho: str(caminho.relative_to(PASTA_MAPAS)))
        tipo = st.radio("Tipo de grafo", ("Grafo de estados", "Grafo padrão"))
        algoritmo = st.selectbox("Algoritmo", ALGORITMOS)
        velocidade = st.slider("Velocidade (quadros/s)", 0.25, 4.0, 1.0, 0.25)
        realcar = st.toggle("Realçar estados-armadilha", value=True) if tipo == "Grafo de estados" else False

    sessao = st.session_state
    try:
        arquivo = mapa.stat()
        versao = (arquivo.st_mtime_ns, arquivo.st_size)
        com_estados = tipo == "Grafo de estados"
        selecao = (str(mapa), versao, algoritmo, com_estados)
        if sessao.get("selecao") != selecao or "resultado_mapa" not in sessao:
            sessao.update(passo=0, tocando=False, pausar_timer=False)
            sessao.pop("camada", None)
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

    mostrar_resultado(resultado, algoritmo)
    periodo = 1.0 / velocidade

    def visualizacao():
        quadros = resultado.quadros
        if len(quadros) > 1:
            controlar_animacao(len(quadros) - 1, periodo)
        passo = sessao.get("passo", 0)
        quadro = quadros[passo] if quadros else None

        camada = None
        if resultado.camadas:
            opcoes = [SEGUIR_CAMADA, TODAS_CAMADAS, *resultado.camadas]
            exibicao = st.selectbox("Camada exibida", opcoes, key="camada",
                                   format_func=lambda opcao: nome_camada(opcao) if opcao in resultado.camadas else opcao)
            if exibicao == SEGUIR_CAMADA and quadro:
                camada = quadro.estado.chaves
            elif exibicao in resultado.camadas:
                camada = exibicao

        mapa_col, estado_col = st.columns([3, 1], gap="large")
        with mapa_col:
            st.markdown(desenhar(linhas, resultado, passo, camada, realcar), unsafe_allow_html=True)
            legenda = "S partida · G saída"
            if quadro:
                legenda += " · círculo indica o estado atual"
            if realcar and resultado.armadilhas is not None:
                legenda += " · listras indicam estados-armadilha"
            st.caption(legenda)
            if quadro and camada is not None and camada != quadro.estado.chaves:
                st.info("O estado atual está em outra camada.")
            if realcar and resultado.armadilhas is not None:
                armadilhas = [e.rotulo for e in sorted(resultado.armadilhas, key=lambda e: (e.posicao, e.chaves, e.bonus))
                              if camada is None or e.chaves == camada]
                with st.expander(f"Estados-armadilha na vista ({len(armadilhas)})"):
                    if armadilhas:
                        st.dataframe({"Estado": armadilhas}, hide_index=True, use_container_width=True)
                    else:
                        st.write("Nenhum estado-armadilha na vista.")
        with estado_col:
            if quadro:
                mostrar_estado(quadro, algoritmo)

    if hasattr(st, "fragment"):
        st.fragment(run_every=periodo if sessao.tocando else None)(visualizacao)()
    else:
        visualizacao()
        if sessao.tocando:
            sleep(max(0.0, sessao.proximo_passo - monotonic()))
            st.rerun()


if __name__ == "__main__":
    main()
