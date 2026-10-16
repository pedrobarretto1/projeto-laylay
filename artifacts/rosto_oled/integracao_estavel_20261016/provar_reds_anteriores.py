"""Retira em memória o bloqueio de quietude deste incremento; não edita produção."""
import inspect
from pathlib import Path
import sys
import textwrap

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import mente_laylay.autonomia.companhia_corporal as modulo
import pytest

fonte=textwrap.dedent(inspect.getsource(modulo.CompanhiaCorporalRuntime.processar))
blocos=[
    ('if not decisao.permite_movimento:',
     'if decisao.motivo == "repouso_espontaneo" or (decisao.pontuacoes and not decisao.permite_movimento):'),
    ('if self._atencao_prioritaria() or projetar_execucao_operacional(atividade):',
     'if self._atencao_prioritaria() or projetar_execucao_operacional(atividade) or ((self.perfil_corporal == "rodas_suspensas" or proposta) and not decisao.permite_movimento):')]
for antigo,novo in blocos:
    assert fonte.count(antigo)==1,'Baseline mudou; não aplicar cegamente'
    fonte=fonte.replace(antigo,novo,1)
namespace=dict(modulo.__dict__)
exec(compile(fonte,'<processar_antes_da_quietude>','exec'),namespace)
modulo.CompanhiaCorporalRuntime.processar=namespace['processar']
raise SystemExit(pytest.main([
    'scripts/tests/test_companhia_corporal.py::test_fala_gesticula_uma_vez_e_silencio_nao_concede_modo',
    'scripts/tests/test_companhia_corporal.py::test_composicao_instalada_ativa_por_fala_aprende_receipt_e_conhece_modo',
    '-q','--tb=short']))
