"""Execute na pasta do jogo: python -m unittest discover -s tests -v"""
import heapq
from itertools import count
from pathlib import Path
import unittest

from utils import (a_bordo, entregues, gerar_grafo_taxi, comparar_com_dijkstra,
                   reproduzir_percurso, serializar_grafo, validar_texto)

RAIZ = Path(__file__).resolve().parents[1]


def referencia(grafo):
    """Oráculo independente com heap para conferir o Dijkstra original."""
    contador = count()
    fila = [(0, next(contador), grafo.inicio)]
    custos = {grafo.inicio: 0}
    anteriores = {}
    while fila:
        custo, _, no = heapq.heappop(fila)
        if custo != custos[no]:
            continue
        if no in grafo.finais:
            comandos = []
            while no != grafo.inicio:
                no, direcao = anteriores[no]
                comandos.append(direcao)
            return custo, comandos[::-1]
        for direcao, (vizinho, peso) in grafo.transicoes[no].items():
            novo = custo + peso
            if novo < custos.get(vizinho, float('inf')):
                custos[vizinho] = novo
                anteriores[vizinho] = no, direcao
                heapq.heappush(fila, (novo, next(contador), vizinho))
    raise AssertionError('Sem solução')


class TestJogo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grafos = {p.name: gerar_grafo_taxi(p.read_text()) for p in (RAIZ/'mapas').glob('*.txt')}

    def test_todos_mapas_e_dijkstra_original(self):
        for nome, g in self.grafos.items():
            with self.subTest(mapa=nome):
                esperado, comandos = referencia(g)
                resultado = comparar_com_dijkstra(g, comandos)
                self.assertEqual(resultado['custo_otimo'], esperado)
                self.assertEqual(resultado['custo_extra'], 0)
                self.assertEqual(resultado['eficiencia'], 100)
                print(f"\n{nome}: {len(g.estados)} estados, custo ótimo {esperado}, {len(comandos)} passos")

    def test_capacidade_e_entregas_em_todos_estados(self):
        for g in self.grafos.values():
            for estado in g.estados:
                self.assertLessEqual(len(a_bordo(estado)), 3)
                self.assertTrue(set(entregues(estado)) <= set(estado.chaves))
                for direcao, (destino, custo) in g.transicoes[estado].items():
                    self.assertGreater(custo, 0)
                    self.assertTrue(set(estado.chaves) <= set(destino.chaves))
                    self.assertTrue(set(entregues(estado)) <= set(entregues(destino)))
                    if destino.no_pos.tipo in 'ABCD':
                        self.assertIn(destino.no_pos.tipo.lower(), entregues(destino))
                    if destino.no_pos.tipo == 'G':
                        self.assertEqual(entregues(destino), g.passageiros)
                        self.assertEqual(a_bordo(destino), '')

    def test_quarto_embarque_bloqueado(self):
        g = self.grafos['02_tres_lugares.txt']
        caminho, _ = reproduzir_percurso(g, ['L'] * 7)
        atual = caminho[-1]  # coluna 8, d está na coluna 9
        self.assertEqual(a_bordo(atual), 'abc')
        self.assertNotIn('L', g.transicoes[atual])

    def test_entrega_libera_vaga_sem_reembarque(self):
        g = self.grafos['02_tres_lugares.txt']
        _, comandos = referencia(g)
        caminho, _ = reproduzir_percurso(g, comandos)
        self.assertTrue(any(e.chaves == 'abcd' for e in caminho))
        self.assertTrue(any(e.chaves == 'abcd' and len(a_bordo(e)) <= 3 for e in caminho))
        for e in g.estados:
            if e.no_pos.tipo in 'abcd' and e.no_pos.tipo in entregues(e):
                self.assertNotIn(e.no_pos.tipo, a_bordo(e))

    def test_porta_e_casa_antes_da_hora(self):
        g = gerar_grafo_taxi('#########\n#S.A..G.#\n#..a....#\n#########\n')
        caminho, _ = reproduzir_percurso(g, ['L'])
        self.assertNotIn('L', g.transicoes[caminho[-1]])
        self.assertTrue(all(entregues(e) == 'a' for e in g.finais))

    def test_terrenos_e_mao_unica(self):
        g = self.grafos['03_hora_do_rush.txt']
        vistos = set()
        for e in g.estados:
            if e.no_pos.tipo == '>':
                self.assertLessEqual(set(g.transicoes[e]), {'L'})
            for destino, peso in g.transicoes[e].values():
                if destino.no_pos.tipo in ',~':
                    self.assertEqual(peso, {',':3, '~':5}[destino.no_pos.tipo])
                    vistos.add(destino.no_pos.tipo)
        self.assertEqual(vistos, {',','~'})

    def test_rota_pior_tem_custo_extra(self):
        g = self.grafos['01_primeira_corrida.txt']
        _, comandos = referencia(g)
        resultado = comparar_com_dijkstra(g, ['L','O'] + comandos)
        self.assertEqual(resultado['custo_extra'], 2)
        self.assertLess(resultado['eficiencia'], 100)

    def test_rejeita_trajetos_incompletos_e_falsificados(self):
        g = self.grafos['01_primeira_corrida.txt']
        for comandos in [[], ['N'], ['teleporte'], [None], None]:
            with self.subTest(comandos=comandos), self.assertRaises(ValueError):
                comparar_com_dijkstra(g, comandos)

    def test_validacao(self):
        invalidos = ['', '###\n#SG#\n###', '#####\n#SaG#\n#####',
                     '#####\n#S+G#\n#####', '#####\n#S*G#\n#####',
                     '#####\n#S G#\n#####', '#####\n#SGG#\n#####',
                     '#####\n.S.G#\n#####']
        for texto in invalidos:
            with self.subTest(mapa=texto), self.assertRaises(ValueError):
                validar_texto(texto)

    def test_sem_solucao(self):
        with self.assertRaisesRegex(ValueError, 'sem solução'):
            gerar_grafo_taxi('#########\n#S#aA#G##\n#########')

    def test_serializacao_preserva_arestas(self):
        g = self.grafos['01_primeira_corrida.txt']
        dados = serializar_grafo(g)
        _, comandos = referencia(g)
        i, custo = dados['inicio'], 0
        for d in comandos:
            i, peso = dados['estados'][i]['saidas'][d]
            custo += peso
        self.assertTrue(dados['estados'][i]['final'])
        self.assertEqual(reproduzir_percurso(g, comandos)[1], custo)


if __name__ == '__main__':
    unittest.main()
