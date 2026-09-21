"""Executável com unittest no ambiente torch isolado, sem pytest/sklearn."""
import copy
from pathlib import Path
import runpy
import unittest

import numpy as np
try:
    import torch
except ImportError as erro:
    raise unittest.SkipTest("executar no ambiente isolado .venv_neural314 com torch") from erro

api = runpy.run_path(str(Path(__file__).resolve().parents[2] / "mente_laylay/neural/perda_encoder.py"))
agregar_tokens = api["agregar_tokens"]
calcular_perda = api["calcular_perda"]
logits_por_tokens = api["logits_por_tokens"]


class TestPerdaEncoder(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(27)
        self.estados = torch.randn(5, 384, dtype=torch.float64, requires_grad=True)
        # O subtoken 2 participa de dois tokens literais.
        self.mapa = [{"indices": [1, 2], "pesos": [0.25, 0.75]},
                     {"indices": [2, 3], "pesos": [0.5, 0.5]}]

    def test_equivalencia_numerica_e_derivada_com_subtoken_compartilhado(self):
        saida = agregar_tokens(self.estados, self.mapa)
        esperado = []
        for m in self.mapa:
            v = np.average(self.estados.detach().numpy()[m["indices"]], axis=0, weights=m["pesos"])
            esperado.append(v / np.linalg.norm(v))
        np.testing.assert_allclose(saida.detach().numpy(), esperado, rtol=1e-12, atol=1e-12)
        self.assertTrue(torch.autograd.gradcheck(lambda x: agregar_tokens(x, self.mapa),
                                               (self.estados,), fast_mode=True))

    def test_especiais_fora_do_mapa_nao_recebem_gradiente_da_agregacao(self):
        agregar_tokens(self.estados, self.mapa).sum().backward()
        self.assertEqual(torch.count_nonzero(self.estados.grad[[0, 4]]).item(), 0)
        self.assertGreater(torch.count_nonzero(self.estados.grad[2]).item(), 0)

    def test_loss_confere_formula_e_aponta_para_classe_correta(self):
        logits = torch.zeros(2, 10, requires_grad=True)
        perda = calcular_perda(logits, [1, 4])
        self.assertAlmostEqual(perda.item(), np.log(10), places=6)
        perda.backward()
        self.assertLess(logits.grad[0, 1].item(), 0)
        self.assertGreater(logits.grad[0, 2].item(), 0)
        self.assertLess(logits.grad[1, 4].item(), 0)

    def test_congelamento_preserva_gradiente_da_cabeca(self):
        for liberar in (False, True):
            estados = self.estados.detach().clone().requires_grad_(liberar)
            cabeca = torch.nn.Linear(384, 10).double()
            antes = copy.deepcopy(cabeca.state_dict())
            calcular_perda(cabeca(agregar_tokens(estados, self.mapa)), [1, 4]).backward()
            self.assertEqual(estados.grad is not None, liberar)
            self.assertTrue(torch.isfinite(cabeca.weight.grad).all().item())
            self.assertTrue(torch.equal(antes["weight"], cabeca.weight))

    def test_mapa_invalido_nao_e_corrigido_silenciosamente(self):
        for mapa in ([{"indices": [-1], "pesos": [1]}],
                     [{"indices": [8], "pesos": [1]}],
                     [{"indices": [1, 1], "pesos": [0.5, 0.5]}],
                     [{"indices": [1], "pesos": [float("nan")]}],
                     [{"indices": [1], "pesos": [0.5]}], []):
            with self.subTest(mapa=mapa), self.assertRaises(ValueError):
                agregar_tokens(self.estados, mapa)

    def test_rotulos_truncados_fora_catalogo_e_nan_abortam(self):
        for rotulos in ([1], [1, 10], [1, -100], [True, 2], []):
            with self.subTest(rotulos=rotulos), self.assertRaises(ValueError):
                calcular_perda(torch.zeros(2, 10), rotulos)
        with self.assertRaises(ValueError):
            calcular_perda(torch.full((2, 10), float("nan")), [1, 2])
        with self.assertRaises(ValueError):
            agregar_tokens(torch.zeros(5, 384), self.mapa)

    def test_inferencia_recusa_supervisao_na_entrada(self):
        with self.assertRaisesRegex(ValueError, "campos desconhecidos"):
            logits_por_tokens(None, None, {"supervisao": [1]})


if __name__ == "__main__":
    unittest.main()
