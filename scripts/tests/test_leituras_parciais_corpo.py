"""Observação numérica e conclusão do objetivo têm provas independentes."""
from pathlib import Path
import shutil
import subprocess

import pytest

from scripts.tests.test_decisao_observada import experiencia

from scripts.tests.test_imu_corporal import EspImu
from scripts.tests.test_companhia_corporal import montar


class EspLeituraParcial(EspImu):
    def __init__(self, *, resultado='TEMPO_LIMITE', valor=23.75, correlacao='atual', parada=True):
        super().__init__(resultado=resultado, correlacao=correlacao)
        self.valor, self.stopped = valor, parada

    def write(self, dados):
        inicio = len(self.rx)
        n = super().write(dados)
        if dados.startswith(b'TURN ') and self.resultado != 'AUSENTE':
            trecho = bytes(self.rx[inicio:]).decode().splitlines()
            for i, linha in enumerate(trecho):
                if linha.startswith('TURNEND '):
                    campos = linha.split()
                    campos[-1] = str(round(self.valor * 100))
                    trecho[i] = ' '.join(campos)
            self.rx[inicio:] = ('\n'.join(trecho) + '\n').encode()
        return n


@pytest.mark.parametrize('resultado,valor,valida', [
    ('TEMPO_LIMITE', 23.75, True), ('SEM_ROTACAO', 0.0, True),
    ('SENTIDO_DIVERGENTE', -17.25, True), ('ULTRAPASSOU', 110.5, True),
    ('IMU_OU_SESSAO', 23.75, False), ('SATURACAO', 23.75, False),
    ('PROTECAO', 23.75, False), ('INTERROMPIDO', 23.75, False),
])
def test_transporte_qualifica_leitura_sem_promover_objetivo(resultado, valor, valida):
    _, _, rosto, _, _, _ = montar(esp=EspLeituraParcial(resultado=resultado, valor=valor))
    try:
        r = rosto.girar_corpo(90)
        assert r['rotacao_medida_graus'] == valor, 'controle: número chegou pelo protocolo'
        assert r['ok'] is False and r['prova_rotacao'] is False
        assert r['aplicacao_pwm_confirmada'] and r['parada_confirmada']
        assert r.get('leitura_rotacao_valida') is valida, 'primeira fronteira: leitura e objetivo não têm validação independente'
    finally:
        rosto.encerrar()


@pytest.mark.parametrize('correlacao', ['outra_sequencia', 'outra_sessao'])
def test_leitura_de_outra_ocorrencia_nao_recebe_validade(correlacao):
    _, _, rosto, _, _, _ = montar(esp=EspLeituraParcial(correlacao=correlacao))
    try:
        r = rosto.girar_corpo(90)
        assert r['rotacao_medida_graus'] is None
        assert r.get('leitura_rotacao_valida', False) is False
    finally:
        rosto.encerrar()


def test_medida_permanece_observada_quando_parada_nao_e_confirmada():
    _, _, rosto, _, _, _ = montar(esp=EspLeituraParcial(parada=False))
    try:
        r = rosto.girar_corpo(90)
        assert r['ok'] is False and r['parada_confirmada'] is False
        assert r['rotacao_medida_graus'] == 23.75
        assert r.get('leitura_rotacao_valida') is True
    finally:
        rosto.encerrar()


def test_firmware_host_distingue_leitura_parcial_e_interrupcao_ambigua(tmp_path):
    compiler = shutil.which('clang++') or r'C:\Program Files\Windhawk\Compiler\bin\clang++.exe'
    if not Path(compiler).is_file():
        pytest.skip('Validação C++ host exige clang++ instalado.')
    raiz = Path(__file__).resolve().parents[2]
    host = raiz / 'firmware/rosto_laylay/validacao_host'
    exe = tmp_path / 'leituras.exe'
    comp = subprocess.run([compiler, '-std=c++17', '-static', '-I'+str(host),
        str(host/'validar_leituras_parciais.cpp'), '-o', str(exe)], capture_output=True, text=True)
    assert comp.returncode == 0, comp.stderr
    p = subprocess.run([str(exe)], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
    assert 'LEITURAS_HOST_GREEN' in p.stdout
    assert 'TEMPO_LIMITE' in p.stdout and 'SEM_ROTACAO' in p.stdout and 'SATURACAO' in p.stdout


def registrar_parcial(*, valor=23.75, valida=True, evidencia='turnend_correlacionado_imu_valida', objetivo=None):
    estado, runtime = experiencia()
    e = runtime.iniciar(nome='giro', origem_intencao='pedido_usuario', perfil='bancada')
    retorno = {'ok': False, 'prova_rotacao': False, 'rotacao_medida_graus': valor,
        'leitura_rotacao_valida': valida, 'evidencia_leitura_rotacao': evidencia}
    if objetivo is not None:
        retorno['angulo_solicitado_graus'] = objetivo
    receipt = {'ok': False, 'aplicacao_pwm_confirmada': True, 'parada_confirmada': True}
    e = runtime.registrar(e, retorno, [receipt])
    return estado, runtime, e


@pytest.mark.parametrize('valor', [23.75, 0.0, -17.25])
def test_historico_conserva_observacao_independente_de_objetivo(valor):
    _, runtime, e = registrar_parcial(valor=valor)
    assert e['confirmado'] is False and e['prova_rotacao'] is False
    assert e.get('leitura_rotacao_valida') is True, 'captura perde a qualificação independente'
    fonte = runtime.recuperar_explicacao('Por que você fez esse gesto?', turno={'id': 'consulta'})
    assert fonte.episodios[0].confirmado is False
    assert len(fonte.episodios[0].medicoes) == 1
    assert fonte.episodios[0].medicoes[0].valor == valor


@pytest.mark.parametrize('objetivo', [90, -180])
def test_escopo_do_resultado_global_inclui_objetivo_solicitado(objetivo):
    _, runtime, e = registrar_parcial(objetivo=objetivo)
    assert e['confirmado'] is False and e['parada_confirmada'] is True
    assert e['escopo_confirmacao'] == 'giro solicitado, PWM e parada elétrica', 'resultado global não pode omitir a obrigação angular'
    f = runtime.recuperar_explicacao('Por que você fez esse gesto?', turno={'id': 'consulta'})
    assert f.episodios[0].escopo_confirmacao == e['escopo_confirmacao']


@pytest.mark.parametrize('objetivo', [None, True, '90', 90.0])
def test_medida_ou_valor_nao_canonico_nao_inventa_obrigacao_angular(objetivo):
    _, _, e = registrar_parcial(objetivo=objetivo)
    assert e['escopo_confirmacao'] == 'PWM e parada elétrica'
    assert e['confirmado'] is False and e['autoriza_execucao'] is False


@pytest.mark.parametrize('chave,valor', [
    ('leitura_rotacao_valida', None), ('leitura_rotacao_valida', False),
    ('leitura_rotacao_valida', 1), ('evidencia_leitura_rotacao', 'parecer_da_ia'),
    ('rotacao_medida_graus', None), ('rotacao_medida_graus', True),
    ('rotacao_medida_graus', '23.75'), ('rotacao_medida_graus', float('nan')),
    ('rotacao_medida_graus', float('inf')),
])
def test_recuperacao_parcial_nao_completa_premissas_pelo_diagnostico_ou_ia(chave, valor):
    estado, runtime, e = registrar_parcial()
    if valor is None:
        e.pop(chave, None)
    else:
        e[chave] = valor
    estado.atualizar_campos('mental', historico_corporal=[e],
        corpo_motor={'rotacao_medida_graus': 90, 'leitura_rotacao_valida': True},
        experiencia_corporal={'fidelidade_verificada': True, 'apoio_confirmado': True,
            'evidencia_leitura_rotacao': 'turnend_correlacionado_imu_valida'})
    antes = estado.retrato_dominio('mental')
    f = runtime.recuperar_explicacao('Por que você fez esse gesto?', turno={'id': 'consulta'})
    assert f.episodios and not f.episodios[0].medicoes
    assert f.episodios[0].confirmado is False and f.autoriza_execucao is False
    assert estado.retrato_dominio('mental') == antes


@pytest.fixture(scope='module')
def parciais_instaladas(tmp_path_factory):
    from scripts.tests.test_motivo_decisao_composicao import decisao_instalada
    with pytest.MonkeyPatch.context() as ambiente:
        ambiente.setenv('LAYLAY_COLETAR_MEDIDAS_OCORRENCIA', '1')
        ambiente.setenv('LAYLAY_COLETAR_LEITURAS_PARCIAIS', '1')
        return decisao_instalada.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('nome,valor', [('parcial', 23.75), ('zero', 0.0), ('divergente', -17.25),
    ('ultrapassou', 110.5), ('sem_parada', 23.75), ('imu_invalida', None), ('saturacao', None),
    ('protecao', None), ('interrompido', None), ('outra_sequencia', None)])
def test_explicacao_instalada_distingue_observacao_e_conclusao(nome, valor, parciais_instaladas):
    c = parciais_instaladas['medidas_ocorrencias'][nome]
    assert all(parciais_instaladas['owners'].values()) and c['publicacoes']
    assert c['publicacoes'][0]['confirmado'] is False
    assert c['experiencia']['confirmado'] is False and c['experiencia'].get('prova_rotacao', False) is False
    assert c['experiencia']['escopo_confirmacao'] == 'giro solicitado, PWM e parada elétrica'
    assert c['fonte']['episodios'][0]['escopo_confirmacao'] == c['experiencia']['escopo_confirmacao']
    persistido = next(evento for evento in c['eventos_aprendizado']
        if evento['contexto']['experiencia']['id'] == c['experiencia']['id'])
    assert persistido['contexto']['experiencia'] == c['experiencia']
    assert persistido['sinal'] < 0, 'leitura válida não transforma falha do objetivo em aprendizado positivo'
    medidas = c['fonte']['episodios'][0]['medicoes']
    if valor is None:
        assert not medidas
    else:
        assert c['experiencia'].get('leitura_rotacao_valida') is True
        assert len(medidas) == 1 and medidas[0]['valor'] == valor
        assert 'não confirma conclusão da operação' in c['fala_owner']
    assert 'sem confirmação' in c['fala_owner']
    assert c['sem_novos_efeitos'] and c['sem_mutacao_historico']
    for turno in c['turnos']:
        assert turno['textos'] == [c['fala_owner']] and not turno['executores']
        assert turno['codec_integral'] and turno['contexto_fechado']


def test_modelo_local_opcional_conserva_parcial_e_zero_sem_concluir_operacao(parciais_instaladas):
    casos = parciais_instaladas['medidas_ocorrencias']
    if casos['parcial'].get('qwen_real') is None:
        pytest.skip('Coleta HTTP opcional exige LAYLAY_MEDIDAS_QWEN_REAL=1.')
    for nome in ('parcial', 'zero'):
        q = casos[nome]['qwen_real']
        assert q['resultado']['sucesso']
        assert q['http'] and all(h.get('status') == 200 for h in q['http'])
        assert q['bruto_integral'], 'modelo deve conservar a realização inteira antes da revisão'
