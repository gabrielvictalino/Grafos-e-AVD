"""Execute: python -m streamlit run jogo.py"""
from pathlib import Path
import hashlib
import json
from uuid import uuid4

import streamlit as st
import streamlit.components.v1 as components

from utils import gerar_grafo_taxi, serializar_grafo, carregar_sprites, comparar_com_dijkstra

RAIZ = Path(__file__).resolve().parent
st.set_page_config(page_title="Última corrida · Táxi Labirinto", page_icon="🚕", layout="wide")
st.markdown("""<style>
.stApp {background:#101b22;color:#f4f1e8}
.block-container {max-width:none;padding:3.3rem clamp(.5rem,1.5vw,1.6rem) 1rem}
header[data-testid="stHeader"] {background:transparent}
[data-testid="stSidebar"] {background:#16252e}
h1 {font-size:2.3rem!important;letter-spacing:-.07rem}
</style>""", unsafe_allow_html=True)


@st.cache_resource(max_entries=6)
def preparar(texto):
    grafo = gerar_grafo_taxi(texto)
    return grafo, serializar_grafo(grafo)


@st.cache_data
def sprites():
    return carregar_sprites(RAIZ / "sprites")


# [IA] ChatGPT – apoio à organização da interface do minijogo e à integração do componente com o Streamlit.
tabuleiro = components.declare_component("taxi_labirinto", path=str(RAIZ / "componente"))


with st.sidebar:
    st.subheader("Sua corrida")
    arquivos = sorted((RAIZ / "mapas").glob("*.txt"))
    if not arquivos:
        st.error("A pasta mapas precisa conter arquivos .txt.")
        st.stop()
    nomes = {
        "01_primeira_corrida": "01 · Primeira corrida",
        "02_tres_lugares": "02 · Três lugares, quatro pessoas",
        "03_hora_do_rush": "03 · Hora do rush",
    }
    escolhido = st.selectbox("Bairro", arquivos, format_func=lambda p: nomes.get(p.stem, p.stem))
    enviado = st.file_uploader("Ou carregue seu mapa .txt", type=["txt"])
    velocidade = st.select_slider("Ritmo ao segurar a seta", ["Tranquilo", "Normal", "Ágil"], value="Normal")
    reiniciar = st.button("↻ Reiniciar corrida", use_container_width=True)
    st.divider()
    st.markdown("**Como jogar**")
    st.write("Clique no tabuleiro e use ↑ ↓ ← →. Também há botões na tela.")
    st.write("Busque os passageiros e passe pela marca na rua ao lado da fachada com a mesma letra. O embarque e a entrega são automáticos.")
    st.write("Leve até 3 passageiros. Com o carro cheio, entregue alguém antes de entrar na célula de um quarto passageiro.")
    st.write("Os destinos ficam bloqueados até você buscar a pessoa correspondente. Depois da entrega, continuam abertos.")
    st.caption("Rua: custo 1 · Obras (,): 3 · Alagamento (~): 5. Setas do mapa indicam a única direção permitida para sair daquela célula.")
    st.caption("Só entre em G depois de concluir todas as entregas. O custo mede o percurso, não o tempo no teclado.")

try:
    texto = enviado.getvalue().decode("utf-8-sig") if enviado else escolhido.read_text(encoding="utf-8")
    with st.spinner("Preparando as ruas e os estados da corrida…"):
        grafo, dados = preparar(texto)
    imagens = sprites()
except (ValueError, UnicodeError, OSError) as erro:
    st.error(str(erro))
    st.stop()

assinatura = hashlib.sha256(texto.encode()).hexdigest()
if reiniciar or st.session_state.get("mapa_taxi") != assinatura:
    st.session_state.mapa_taxi = assinatura
    st.session_state.partida_taxi = uuid4().hex
    st.session_state.resultado_taxi = None

resposta = tabuleiro(
    grafo=dados, sprites=imagens, partida=st.session_state.partida_taxi,
    intervalo={"Tranquilo":260, "Normal":180, "Ágil":125}[velocidade],
    resultado=st.session_state.resultado_taxi,
    key="tabuleiro_taxi", default=None,
)
if (isinstance(resposta, dict) and resposta.get("partida") == st.session_state.partida_taxi
        and st.session_state.resultado_taxi is None):
    try:
        with st.spinner("Corrida concluída! Comparando seu percurso com Dijkstra…"):
            st.session_state.resultado_taxi = comparar_com_dijkstra(grafo, resposta.get("movimentos"))
        st.rerun()
    except ValueError as erro:
        st.error(str(erro))

resultado = st.session_state.resultado_taxi
if resultado:
    st.caption("Dijkstra minimiza o custo total. A rota exibida é uma das rotas ótimas; o número de passos pode ser diferente.")
    st.download_button("Baixar relatório da corrida", json.dumps({"mapa":grafo.linhas, **resultado}, ensure_ascii=False, indent=2),
                       file_name="minha_corrida.json", mime="application/json")

with st.expander("Grafo de estados e compatibilidade com o projeto"):
    st.write(f"{len(grafo.estados):,} estados jogáveis · {len(grafo.arestas_geradas):,} arestas · {len(grafo.camadas)} camadas · {len(grafo.armadilhas)} estados armadilha.")
    st.write("Cada estado identifica posição, passageiros já buscados e entregas concluídas. O carro só percorre arestas desse grafo.")
    st.code("gerar_labirinto → preparar_estados → bfs_grafo_estados_exploracao\n→ refinamento de capacidade e entregas em utils.py\n→ converter_grafo_estados → dijkstra", language=None)
    st.caption("Os módulos originais estão em src/. Mapas com + ou * são recusados porque seus custos negativos não são compatíveis com Dijkstra.")
