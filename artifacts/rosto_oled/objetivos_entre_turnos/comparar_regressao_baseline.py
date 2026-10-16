"""Roda casos de receipt com os cinco módulos congelados, sem editar produção."""
from pathlib import Path
import sys
import types
import pytest

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
BASE = Path(__file__).resolve().parent / "baseline"
for nome in ("cognicao.modelo_corporal", "memoria_mental.experiencia_corporal_runtime",
             "autonomia.companhia_corporal", "especialistas.corpo_motor_runtime", "especialistas.mapa_habilidades"):
    completo = "mente_laylay." + nome
    caminho = BASE / (nome.split(".")[-1] + ".py")
    modulo = types.ModuleType(completo)
    modulo.__file__ = str(caminho)
    modulo.__package__ = completo.rsplit(".", 1)[0]
    sys.modules[completo] = modulo
    exec(compile(caminho.read_text(encoding="utf-8"), str(caminho), "exec"), modulo.__dict__)
raise SystemExit(pytest.main([
    "scripts/tests/test_corpo_motor.py::test_composicao_instalada_resolve_executa_publica_e_conhece_corpo",
    "scripts/tests/test_som_corporal.py::test_executor_instalado_publica_falha_para_o_mesmo_rosto_sonoro",
    "-q", "--tb=short"]))
