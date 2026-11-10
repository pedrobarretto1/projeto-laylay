"""DTOs diagnósticos não preservam nem fabricam autoridade tipada."""
import json
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys

import pytest

from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA
from mente_laylay.cognicao.fonte_capacidades_turno import FonteCapacidadesTurno, fonte_capacidades_vigente
from mente_laylay.cognicao.referencias_linguagem import PerspectivaEnunciador
from scripts.tests.observacao_tipadas import isolar_codigo_observado, projetar_tipo_observado


@pytest.mark.parametrize('tipo', ['capacidades', 'perspectiva'])
def test_exportacao_observa_papeis_e_disponibilidade_sem_serializar_credencial(tipo):
    fonte = (FonteCapacidadesTurno('turno-host', 'entrada privada', SnapshotComandoIA({
        'dominios_disponiveis': ['app'], 'predicados': [{'dominio': 'app', 'acao': 'abrir', 'objetos': ['app']}],
    })) if tipo == 'capacidades' else PerspectivaEnunciador('turno-host', 'entrada privada'))
    with pytest.raises(TypeError):
        json.dumps(fonte)
    observado = json.loads(json.dumps(fonte, default=projetar_tipo_observado))
    assert observado == {'tipo_observado': type(fonte).__name__, 'projecao': fonte.para_prompt()}
    assert 'entrada privada' not in json.dumps(observado)
    assert observado['projecao']['autoriza_execucao'] is False
    contrato = {'fonte_capacidades_turno': observado, 'turno_id': 'turno-host',
                'origem': 'mente_unica', 'autoriza_execucao': False}
    assert fonte_capacidades_vigente(contrato, 'entrada privada', 'turno-host') is None
    assert fonte.vigente('entrada privada', 'turno-host')


def test_objetos_desconhecidos_e_dataclasses_nao_entram_por_fallback():
    @dataclass
    class FonteDesconhecida:
        segredo: str = 'nao exportar'
        autoriza_execucao: bool = True

    class PerspectivaDerivada(PerspectivaEnunciador):
        pass

    for valor in (object(), FonteDesconhecida(), lambda: 'nao chamar',
                  PerspectivaDerivada('turno', 'entrada')):
        with pytest.raises(TypeError, match='Tipo não previsto na observação'):
            json.dumps(valor, default=projetar_tipo_observado)


@pytest.mark.parametrize('efeito', ['arquivo_externo', 'rede', 'processo'])
def test_subprocesso_observador_bloqueia_efeitos_fora_da_prova(tmp_path, efeito):
    fora = tmp_path / 'fora.txt'
    perfil = tmp_path / 'perfil'
    perfil.mkdir()
    codigos = {
        'arquivo_externo': f"Path({str(fora)!r}).write_text('proibido')",
        'rede': "import socket; socket.socket().connect(('127.0.0.1', 9))",
        'processo': "import subprocess; subprocess.run([sys.executable, '-c', 'pass'])",
    }
    codigo = isolar_codigo_observado(codigos[efeito], perfil)
    processo = subprocess.run([sys.executable, '-B', '-c', codigo],
        cwd=Path(__file__).resolve().parents[2], capture_output=True,
        text=True, encoding='utf-8', timeout=45)
    assert processo.returncode != 0
    assert 'PermissionError' in processo.stderr
    assert not fora.exists()
