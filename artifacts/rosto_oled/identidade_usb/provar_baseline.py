"""Reproduz REDs vizinhos retirando só a seleção nova, em memória, sem editar produção."""
import inspect
import ast
import subprocess
from pathlib import Path
import sys
import textwrap

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
import mente_laylay.especialistas.rosto_oled_runtime as modulo
import pytest

fonte = textwrap.dedent(inspect.getsource(modulo.RostoOledRuntime.sincronizar))
blocos = [(
    '''            else:
                self._identidade_usb_verificada = False
                self._pareamento_usb = validar_identidade_corpo_usb(self.identidade_usb_getter())
                if self._pareamento_usb:
                    self._selecionar_usb_pareado()
            if self._serial is None and self._config_wifi_path is None and self.autodetectar:''',
    '''            elif self.autodetectar:'''), (
    '''            if self._config_wifi_path is None and self._serial is None:''',
    '''            if self._config_wifi_path is None:'''), (
    '''            if not self._identidade_usb_verificada:
                self._porta_ativa = porta''',
    '''            self._porta_ativa = porta'''), (
    '''            if self._config_wifi_path is None and self._pareamento_usb:
                atual = self._ler_saude()
                if atual.get("dispositivo") != self._pareamento_usb["dispositivo"]:
                    raise ConnectionError("identidade_usb_divergente")
''', '')]
for antigo, novo in blocos:
    antigo, novo = textwrap.indent(antigo, "    "), textwrap.indent(novo, "    ")
    assert fonte.count(antigo) == 1, "Baseline abortado: bloco mudou"
    fonte = fonte.replace(antigo, novo, 1)
namespace = dict(modulo.__dict__)
exec(compile(fonte, "<sincronizar_sem_pareamento>", "exec"), namespace)
modulo.RostoOledRuntime.sincronizar = namespace["sincronizar"]
# Nos dois controles, VIGIA não é negociada; o ramo HEALTH não participa.
assert "ICAPS" in fonte and "_selecionar_usb_pareado" not in fonte
executar = subprocess.run
def subprocesso_observado(args, *posicionais, **kwargs):
    if isinstance(args, list) and len(args) >= 3 and args[1] == "-c" and "import_module('laylay')" in args[2]:
        arvore = ast.parse(args[2])
        for nodo in ast.walk(arvore):
            if isinstance(nodo, ast.Assert) and nodo.msg is None:
                nodo.msg = ast.Constant(ast.unparse(nodo.test))
        codigo = ast.unparse(ast.fix_missing_locations(arvore))
        prefixo = ("import mente_laylay.especialistas.rosto_oled_runtime as _baseline\n"
                   f"exec({fonte!r}, _baseline.__dict__)\n"
                   "_baseline.RostoOledRuntime.sincronizar = _baseline.sincronizar\n")
        args = [*args[:2], prefixo + codigo, *args[3:]]
    return executar(args, *posicionais, **kwargs)
subprocess.run = subprocesso_observado
raise SystemExit(pytest.main([
    "scripts/tests/test_rosto_oled.py::test_intervalo_sem_heartbeats_renova_sessao_antes_de_acordar_com_pose_atual",
    "scripts/tests/test_corpo_wifi_transporte.py::test_tcp_real_fragmentado_sincroniza_face_hack_glitch_e_pulso_sem_falar_texto",
    "scripts/tests/test_corpo_wifi_transporte.py::test_composicao_instalada_le_config_tcp_e_catalogo_so_disponivel_com_receipts",
    "scripts/tests/test_coerencia_capacidade_documentada.py::test_indisponibilidade_real_nao_deve_ser_reparada_para_capacidade",
    "-q", "--tb=short",
]))
