# [IA] Gemini Classes de adaptador (Nó e Aresta) compatíveis com a assinatura de src/graphs/algorithms.py
class Aresta:
    def __init__(self, origem, destino, custo: float):
        self.origem = origem
        self.destino = destino
        self.custo = custo


class No:
    def __init__(self, id_no: str, titulo: str = "", tipo: str | None = None):
        self.id = id_no
        self.titulo = titulo
        self.tipo = tipo  # Evita AttributeError na checagem u.tipo == "G" do Dijkstra
        self.lista_arestas: list[Aresta] = []

    def adicionar_aresta(self, destino: "No", custo: float) -> None:
        self.lista_arestas.append(Aresta(self, destino, custo))

    def __repr__(self) -> str:
        return f"No({self.id})"