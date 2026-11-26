
# [IA] Claude Code – testes sugeridos para src/comparacao_modelagem.py. Os valores esperados estão calculados à mão nos comentários; o grupo deve conferi-los.

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.comparacao_modelagem import _validar_caminho, comparar_modelagens  # noqa: E402


def test_validar_caminho_porta_sem_chave_e_com_chave():
    # S . A  -> entra na porta A sem ter a chave a: inválido.
    valido, obs = _validar_caminho([(1, 1, "S"), (1, 2, "."), (1, 3, "A")])
    assert valido is False and "A" in obs
    # S a A  -> pega a chave a antes da porta: válido.
    valido, _ = _validar_caminho([(1, 1, "S"), (1, 2, "a"), (1, 3, "A")])
    assert valido is True


def test_comparacao_modelagem_m02_m03_m04():
    # Valores conferidos com out/parte1/solucoes.csv (BFS no G_est): m02=34, m03=87, m04=20 passos.
    linhas = comparar_modelagens(RAIZ / "data" / "mapas")
    assert len(linhas) == 9
    por_chave = {(l["mapa"], l["abordagem"]): l for l in linhas}
    for mapa, passos_est in (("m02", 34), ("m03", 87), ("m04", 20)):
        chao = por_chave[(mapa, "G_pos com portas como chão")]
        parede = por_chave[(mapa, "G_pos com portas como parede")]
        est = por_chave[(mapa, "G_est (modelagem correta)")]
        assert chao["caminho_valido"] is False        # (a) atravessa porta sem chave
        assert parede["passos"] == ""                 # (b) G inalcançável
        assert est["caminho_valido"] is True and est["passos"] == passos_est
