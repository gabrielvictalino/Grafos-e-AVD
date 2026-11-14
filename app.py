"""Apresentação interativa do labirinto (Parte 1, item 9) — app Streamlit.

Rodar na raiz do repositório:
    pip install -r requirements.txt
    streamlit run app_labirinto.py

Este arquivo NÃO implementa busca nem regra do labirinto. Ele só:
  1. lista os mapas .txt da pasta mapas/;
  2. chama as funções do próprio projeto:
       labirinto.validar_labirinto(caminho)
       labirinto.gerar_labirinto(caminho)            -> Labirinto
       labirinto.bfs_grafo_estados(Labirinto)
       algorithms.dijkstra(lista_nos, origem)
       algorithms.bellmon_ford(lista_nos, origem)
       algorithms.dfs(...)                          (quando existir)
  3. desenha e anima o resultado que essas funções devolverem.

Formato de retorno que o app entende (qualquer um dos dois):
  a) (distancias, anteriores)  -> dicionários indexados por nó/estado; o
     caminho é lido seguindo `anteriores` a partir do estado final.
  b) lista de nós/estados do caminho, de S até G.
Cada nó/estado pode ser um `No` (posicao_linha, posicao_coluna, tipo) ou um
`No_estados` (com .no, .chaves, .bonus). Se o estado tiver o atributo
`armadilha` verdadeiro, a célula é realçada como estado-armadilha.
"""
import glob
import inspect
import os
import sys
import time
import traceback

import streamlit as st

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "src", "graphs"))
PASTA_MAPAS = os.path.join(RAIZ, "mapas")

CORES_CAMADA = ["#3b5bdb", "#e8590c", "#0c8599", "#9c36b5", "#2b8a3e",
                "#c2255c", "#5c940d", "#1864ab", "#862e9c", "#d9480f"]
SETAS = {"^": "↑", ">": "→", "v": "↓", "<": "←"}


# ------------------------------------------------------------ ponte com o repo
def importar_projeto():
    """Importa os módulos do repositório e devolve (labirinto, algorithms, erros)."""
    erros, lab_mod, alg_mod = [], None, None
    try:
        import labirinto as lab_mod
    except Exception:
        erros.append("Falha ao importar labirinto.py:\n" + traceback.format_exc())
    try:
        import algorithms as alg_mod
    except Exception:
        erros.append("Falha ao importar src/graphs/algorithms.py:\n" + traceback.format_exc())
    return lab_mod, alg_mod, erros


def algoritmos_disponiveis(lab_mod, alg_mod):
    """Só oferece as funções que existem no projeto."""
    algs = {}
    if lab_mod and hasattr(lab_mod, "bfs_grafo_estados"):
        algs["BFS (bfs_grafo_estados)"] = lambda L: lab_mod.bfs_grafo_estados(L)
    if alg_mod:
        for nome in ("bfs", "dfs", "dijkstra", "bellman_ford", "bellmon_ford"):
            f = getattr(alg_mod, nome, None)
            if f is None:
                continue
            n_params = len(inspect.signature(f).parameters)
            if n_params == 1:
                algs[nome] = (lambda f: lambda L: f(L))(f)
            else:
                algs[nome] = (lambda f: lambda L: f(L.lista_nos, L.estado_incial))(f)
    return algs


def posicao(x):
    no = getattr(x, "no", x)
    return no.posicao_linha, no.posicao_coluna


def interpretar_resultado(resultado, L):
    """Transforma o retorno do algoritmo em uma lista de quadros para animar.
    Não calcula nada da busca: só lê o que o algoritmo devolveu."""
    if resultado is None:
        raise ValueError("O algoritmo não retornou nada (falta um `return`).")
    distancias = None
    if isinstance(resultado, tuple) and len(resultado) == 2 and all(isinstance(r, dict) for r in resultado):
        distancias, anteriores = resultado
        alvo = next((x for x in anteriores if posicao(x) == posicao(L.estado_final)
                     and distancias.get(x, float("inf")) != float("inf")), None)
        if alvo is None:
            raise ValueError("O estado final (G) não aparece alcançado em `distancias`/`anteriores`.")
        caminho, x, vistos = [], alvo, set()
        while x is not None:
            if id(x) in vistos:
                raise ValueError("`anteriores` tem um ciclo; não dá para montar o caminho.")
            vistos.add(id(x)); caminho.append(x); x = anteriores.get(x)
        caminho.reverse()
        if posicao(caminho[0]) != posicao(L.estado_incial):
            raise ValueError("O caminho reconstruído por `anteriores` não começa em S.")
    elif isinstance(resultado, (list, tuple)):
        caminho = list(resultado)
        if not caminho:
            raise ValueError("O algoritmo retornou um caminho vazio.")
    else:
        raise ValueError(f"Formato de retorno não reconhecido: {type(resultado).__name__}.")

    quadros = []
    for i, x in enumerate(caminho):
        quadros.append({
            "pos": posicao(x),
            "tipo": getattr(getattr(x, "no", x), "tipo", "?"),
            "custo": distancias.get(x) if distancias else None,
            "chaves": getattr(x, "chaves", None),
            "bonus": getattr(x, "bonus", None),
            "armadilha": bool(getattr(x, "armadilha", False)),
        })
    return quadros


@st.cache_data(show_spinner=False)
def ler_texto(caminho, _mtime):
    with open(caminho, encoding="utf-8") as f:
        return f.read()


# ------------------------------------------------------------ desenho
CSS = """
<style>
.lab{display:inline-grid;border-radius:6px;overflow:hidden;background:#2b2f36}
.lab div{width:var(--cs);height:var(--cs);display:flex;align-items:center;justify-content:center;position:relative;
  background:#fbfaf7;border:1px solid #ece8df;font:600 calc(var(--cs)*.38) system-ui,sans-serif;color:#555;box-sizing:border-box}
.lab .w{background:#2b2f36;border-color:#2b2f36}
.lab .sand{background:#ecd9a8}.lab .water{background:#a9cdea}
.lab .st{background:#495057;color:#fff}.lab .go{background:#2b8a3e;color:#fff}
.lab .key span{background:#ffd43b;color:#5c4400;border-radius:50%;width:62%;height:62%;display:flex;align-items:center;justify-content:center}
.lab .door{background:#8a5a2b;color:#fff}
.lab .conv{background:#eee9fb;color:#5f3dc4;font-size:calc(var(--cs)*.55)}
.lab .bon span{background:#2b8a3e;color:#fff;border-radius:5px;padding:0 4px}
.lab .ov{position:absolute;inset:0;pointer-events:none}
.lab .trap{position:absolute;inset:0;pointer-events:none;box-shadow:inset 0 0 0 2px #d6336c;
  background:repeating-linear-gradient(45deg,rgba(214,51,108,.45) 0 3px,transparent 3px 8px)}
.lab .ag{position:absolute;width:58%;height:58%;border-radius:50%;border:3px solid #fff;box-shadow:0 1px 5px rgba(0,0,0,.45);z-index:2}
.ev{padding:9px 13px;border-radius:7px;border-left:4px solid #3b5bdb;background:#eef1fb;margin:4px 0 8px;color:#1f2328}
.ev.bad{border-left-color:#d6336c;background:#fdeef3}.ev.ok{border-left-color:#2b8a3e;background:#ebf7ee}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}
</style>
"""


def chave_camada(chaves):
    if chaves is None or chaves in ("-", ""):
        return ""
    return "".join(sorted(str(c) for c in chaves)) if not isinstance(chaves, str) else chaves


def desenhar(linhas, quadros, idx, cor, realcar_armadilha):
    W = max(len(l) for l in linhas)
    cs = max(8, min(44, 560 // max(W, 1)))
    atual = quadros[idx]
    rastro = {}
    for q in quadros[: idx + 1]:
        rastro[q["pos"]] = chave_camada(q["chaves"])
    armadilhas = {q["pos"] for q in quadros[: idx + 1] if q["armadilha"]}
    html = ['<div style="overflow-x:auto">', f'<div class="lab" style="--cs:{cs}px;grid-template-columns:repeat({W},{cs}px)">']
    for r, linha in enumerate(linhas):
        for c in range(W):
            ch = linha[c] if c < len(linha) else "#"
            if ch == "#":
                html.append('<div class="w"></div>'); continue
            cls, dentro = "", ""
            if ch == "S": cls, dentro = "st", "S"
            elif ch == "G": cls, dentro = "go", "G"
            elif ch == ",": cls = "sand"
            elif ch == "~": cls = "water"
            elif ch in "abcd": cls, dentro = "key", f"<span>{ch}</span>"
            elif ch in "ABCD": cls, dentro = "door", ch
            elif ch in SETAS: cls, dentro = "conv", SETAS[ch]
            elif ch in "+*": cls, dentro = "bon", f"<span>{ch}</span>"
            elif ch != ".": dentro = ch
            p = (r, c)
            if p in rastro:
                dentro += f'<i class="ov" style="background:{cor(rastro[p])};opacity:.4"></i>'
            if realcar_armadilha and p in armadilhas:
                dentro += '<i class="trap"></i>'
            if p == atual["pos"]:
                fundo = "#d6336c" if atual["armadilha"] else cor(chave_camada(atual["chaves"]))
                dentro += f'<b class="ag" style="background:{fundo}"></b>'
            html.append(f'<div class="{cls}" title="linha {r}, coluna {c}">{dentro}</div>')
    html.append("</div></div>")
    return "".join(html)


# ------------------------------------------------------------ app
def main():
    st.set_page_config(page_title="Labirinto interativo", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    ss = st.session_state
    ss.setdefault("idx", 0); ss.setdefault("tocando", False); ss.setdefault("avancar", False)

    def reiniciar():
        ss.idx, ss.tocando = 0, False

    st.title("Labirinto interativo")
    st.caption("Visualização dos algoritmos e mapas do projeto (labirinto.py e src/graphs/algorithms.py).")

    lab_mod, alg_mod, erros_import = importar_projeto()
    for e in erros_import:
        st.error("```\n" + e + "\n```")
    if lab_mod is None:
        return

    mapas = sorted(glob.glob(os.path.join(PASTA_MAPAS, "*.txt")))
    algs = algoritmos_disponiveis(lab_mod, alg_mod)

    with st.sidebar:
        st.header("Configuração")
        if not mapas:
            st.warning("Nenhum mapa encontrado. Coloque os arquivos .txt em `mapas/` na raiz do repositório.")
            return
        mapa = st.selectbox("Mapa", mapas, format_func=os.path.basename, key="mapa", on_change=reiniciar)
        if not algs:
            st.warning("Nenhum algoritmo encontrado no projeto.")
            return
        nome_alg = st.selectbox("Algoritmo", list(algs), key="alg", on_change=reiniciar)
        velocidade = st.slider("Velocidade (passos/s)", 0.5, 8.0, 1.5, 0.5)
        realcar = st.toggle("Realçar estados-armadilha", value=True)

    texto = ler_texto(mapa, os.path.getmtime(mapa))
    linhas = [l for l in texto.replace("\r", "").split("\n") if l]

    # --- chama o código do projeto
    etapa = "validar_labirinto"
    try:
        valido = lab_mod.validar_labirinto(mapa)
        if valido is False:
            st.warning("`validar_labirinto` reprovou este mapa. Tentando gerar mesmo assim.")
        etapa = "gerar_labirinto"
        L = lab_mod.gerar_labirinto(mapa)
        etapa = nome_alg
        resultado = algs[nome_alg](L)
        etapa = "leitura do resultado"
        quadros = interpretar_resultado(resultado, L)
    except Exception as e:
        st.error(f"O código do projeto falhou em **{etapa}**: `{type(e).__name__}: {e}`")
        with st.expander("Traceback completo"):
            st.code(traceback.format_exc())
        st.markdown(desenhar(linhas, [{"pos": (-1, -1), "chaves": None, "armadilha": False}], 0,
                             lambda k: "#3b5bdb", False), unsafe_allow_html=True)
        return

    ultimo = len(quadros) - 1
    camadas = []
    for q in quadros:
        k = chave_camada(q["chaves"])
        if k not in camadas:
            camadas.append(k)
    cor = lambda k: CORES_CAMADA[(camadas.index(k) if k in camadas else 0) % len(CORES_CAMADA)]

    if ss.avancar:
        ss.avancar = False
        if ss.tocando:
            ss.idx = min(ss.idx + 1, ultimo)
            if ss.idx >= ultimo:
                ss.tocando = False
    ss.idx = min(ss.idx, ultimo)

    col_mapa, col_estado = st.columns([2.4, 1.6], gap="large")
    with col_mapa:
        def mover(d):
            ss.tocando = False; ss.idx = max(0, min(ultimo, ss.idx + d))

        def alternar():
            if ss.tocando:
                ss.tocando = False
            else:
                if ss.idx >= ultimo: ss.idx = 0
                ss.tocando = True

        b = st.columns([1.2, 1.2, 1.3, 1.2, 1])
        b[0].button("⏮ Início", on_click=lambda: mover(-ss.idx), use_container_width=True)
        b[1].button("◀ Passo", on_click=mover, args=(-1,), use_container_width=True)
        b[2].button("⏸ Pausar" if ss.tocando else ("↻ Repetir" if ss.idx >= ultimo else "▶ Play"),
                    on_click=alternar, type="primary", use_container_width=True)
        b[3].button("Passo ▶", on_click=mover, args=(1,), use_container_width=True)
        if ultimo > 0:
            st.slider("Passo", 0, ultimo, key="idx", label_visibility="collapsed",
                      on_change=lambda: ss.update(tocando=False))

        q = quadros[ss.idx]
        if ss.idx == 0:
            msg, cls = f"Início em S (linha {q['pos'][0]}, coluna {q['pos'][1]}).", ""
        else:
            ant = quadros[ss.idx - 1]
            msg, cls = f"Andou para linha {q['pos'][0]}, coluna {q['pos'][1]} (célula `{q['tipo']}`).", ""
            if chave_camada(ant["chaves"]) != chave_camada(q["chaves"]):
                msg += f" Mudou de camada: chaves {ant['chaves']} → {q['chaves']}."
            if q["armadilha"]:
                msg += " Estado-armadilha."; cls = "bad"
            if ss.idx == ultimo:
                msg += " Chegou em G."; cls = "ok"
        st.markdown(f'<div class="ev {cls}">{msg}</div>', unsafe_allow_html=True)
        st.markdown(desenhar(linhas, quadros, ss.idx, cor, realcar), unsafe_allow_html=True)

    with col_estado:
        st.subheader("Estado atual")
        st.metric("Custo acumulado", "—" if q["custo"] is None else q["custo"])
        st.markdown(
            f"**Passo:** {ss.idx} de {ultimo}  \n"
            f"**Posição:** linha {q['pos'][0]}, coluna {q['pos'][1]}  \n"
            f"**Chaves:** {'—' if q['chaves'] is None else q['chaves']}  \n"
            f"**Bônus consumidos:** {'—' if q['bonus'] is None else q['bonus']}  \n"
            f"**Camada:** <span class='dot' style='background:{cor(chave_camada(q['chaves']))}'></span>"
            f"{chave_camada(q['chaves']) or 'sem chave'}", unsafe_allow_html=True)
        st.caption("“—” = o algoritmo não devolveu essa informação.")

    if ss.tocando:
        time.sleep(1.0 / velocidade)
        ss.avancar = True
        st.rerun()


if __name__ == "__main__":
    main()