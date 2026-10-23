"""Progresso e conclusão são emissões distintas do mesmo objetivo."""
from threading import Event
import pytest
from types import SimpleNamespace

from scripts.tests.test_voz_filas_isoladas import _runtime
from mente_laylay.personalidade.progresso_fala import ProgressoFala
from mente_laylay.autonomia.quadro_cooperacao import QuadroCooperacaoRuntime
from mente_laylay.autonomia.governanca_cooperacao import GovernancaPlanoCooperativoRuntime
from mente_laylay.autonomia.executor_cooperacao import ExecutorPlanoCooperativoRuntime


def test_progresso_nao_consume_a_confirmacao_final_do_mesmo_turno():
    voz = _runtime()
    voz.chave_turno_cb = lambda: 123.0
    iniciou, liberar = Event(), Event()
    reproduzidas = []

    def reproduzir(texto, *_):
        reproduzidas.append(texto)
        iniciou.set()
        liberar.wait(2)
        return True

    voz.reproduzir_fala = reproduzir
    try:
        assert voz.falar('Vou salvar o texto copiado.',
                         _progresso=ProgressoFala('plano:etapa', lambda: True))
        assert iniciou.wait(1)
        assert voz.falar('Criei o arquivo e conferi o conteúdo.')
        assert voz.fila.qsize() == 1
    finally:
        liberar.set()
        voz.encerrar()


def test_progresso_expirado_nao_toca_nem_impede_a_conclusao():
    voz = _runtime()
    voz.iniciar_worker = lambda: None
    progresso = ProgressoFala('plano:etapa', lambda: True)
    assert voz.falar('Vou começar.', _progresso=progresso)
    assert progresso.aguardar_inicio(0) is False
    assert voz.falar('A operação falhou.')
    tocadas = []
    def reproduzir(texto, *_):
        tocadas.append(texto)
        voz.stop_event.set()
        return True
    voz.reproduzir_fala = reproduzir
    voz.worker_de_falas()
    assert tocadas == ['A operação falhou.']


def test_inicio_de_audio_e_sinalizado_apos_o_player_e_nao_ao_sintetizar():
    voz = _runtime()
    progresso = ProgressoFala('plano:etapa', lambda: True)
    voz._progresso_reproducao = progresso
    voz._selecionar_saida_audio = lambda: 0
    eventos = []
    def sintetizar(*_a, **_k):
        assert not progresso.audio_iniciado.is_set()
        eventos.append('sintese')
    def tocar(*_a, **_k):
        assert not progresso.audio_iniciado.is_set()
        eventos.append('player')
    def aguardar():
        assert progresso.audio_iniciado.is_set()
        eventos.append('espera_audio')
        return True
    voz._sintetizar_edge = sintetizar
    voz._aguardar_audio = aguardar
    voz.sd = SimpleNamespace(play=tocar)
    voz.sf = SimpleNamespace(read=lambda _: ([0.0], 16000))
    assert voz.reproduzir_fala('Vou preparar o arquivo.', 'calma', 1)
    assert eventos == ['sintese', 'player', 'espera_audio']


def test_anuncio_de_progresso_nao_admite_sucesso_sem_receipt():
    from scripts.tests.test_orquestrador_fala_registro import _runtime_de_fala
    runtime, _, voz, _ = _runtime_de_fala()
    runtime.anunciar_etapa({'id': 'plano'}, {'id': 'etapa',
        'descricao_progresso': 'Pronto, apaguei o arquivo.'}, vigente=lambda: True)
    assert voz.falas == []


@pytest.mark.parametrize('intent', ['CREATE_FILE', 'APP_OPEN'])
@pytest.mark.parametrize('intercalacao', ['cancelar', 'revogar', 'trocar_turno', 'expirar', 'falha_voz', 'controle'])
def test_espera_por_progresso_revalida_o_limite_do_efeito(intent, intercalacao):
    quadro = QuadroCooperacaoRuntime(log=lambda *_: None)
    permitido, vigente, relogio, efeitos = [True], [True], [0.0], []
    governanca = GovernancaPlanoCooperativoRuntime(quadro=quadro,
        autorizar_acao=lambda *_a, **_k: {'permitido': permitido[0]})
    executor = ExecutorPlanoCooperativoRuntime(quadro=quadro, governanca=governanca,
                                             relogio=lambda: relogio[0], log=lambda *_: None)
    plano = quadro.criar_plano(objetivo='objetivo delimitado', evento_ids=(),
        etapas=({'id': 'efeito', 'intent': intent, 'acao': 'agir'},),
        confianca=1, risco='baixo', autorizacao='explicita_no_pedido')
    def anunciar(*_):
        if intercalacao == 'cancelar':
            quadro.solicitar_cancelamento(plano['id'])
        elif intercalacao == 'revogar':
            permitido[0] = False
        elif intercalacao == 'trocar_turno':
            vigente[0] = False
        elif intercalacao == 'expirar':
            relogio[0] = 100
        elif intercalacao == 'falha_voz':
            raise RuntimeError('TTS indisponível')
    def agir(*_):
        efeitos.append(intent)
        return {'ok': True, 'confirmado': True, 'status': 'efeito_confirmado'}
    resultado = executor.executar(plano['id'], {'efeito': agir}, antes_da_etapa=anunciar,
                                 etapa_vigente=lambda: vigente[0])
    esperado = intercalacao in {'controle', 'falha_voz'}
    assert bool(efeitos) is esperado
    assert resultado['ok'] is esperado
    assert (quadro.obter_plano(plano['id'])['estado'] == 'confirmado') is esperado


def test_cancelamento_durante_ultimo_efeito_preserva_receipt_sem_confirmar_objetivo():
    quadro = QuadroCooperacaoRuntime(log=lambda *_: None)
    governanca = GovernancaPlanoCooperativoRuntime(quadro=quadro,
        autorizar_acao=lambda *_a, **_k: {'permitido': True})
    executor = ExecutorPlanoCooperativoRuntime(quadro=quadro, governanca=governanca)
    plano = quadro.criar_plano(objetivo='objetivo cancelável', evento_ids=(),
        etapas=({'id': 'efeito', 'intent': 'CREATE_FILE'},),
        confianca=1, risco='baixo', autorizacao='explicita_no_pedido')
    def agir(*_):
        quadro.solicitar_cancelamento(plano['id'])
        return {'ok': True, 'confirmado': True, 'status': 'arquivo_criado'}
    resultado = executor.executar(plano['id'], {'efeito': agir})
    final = quadro.obter_plano(plano['id'])
    assert final['etapas'][0]['resultado']['confirmado'] is True
    assert final['estado'] == 'cancelado'
    assert resultado['ok'] is False


def test_voz_sem_permissao_nao_inicia_anuncio_nem_efeito():
    quadro = QuadroCooperacaoRuntime(log=lambda *_: None)
    chamadas = []
    executor = ExecutorPlanoCooperativoRuntime(quadro=quadro)
    plano = quadro.criar_plano(objetivo='não concedido', evento_ids=(),
        etapas=({'id': 'efeito', 'intent': 'CREATE_FILE'},),
        confianca=1, risco='baixo', autorizacao='explicita_no_pedido')
    retorno = executor.executar(plano['id'], {'efeito': lambda *_: chamadas.append('efeito')},
        antes_da_etapa=lambda *_: chamadas.append('fala'))
    assert chamadas == [] and retorno['ok'] is False


@pytest.mark.parametrize('pergunta,direta', [
    ('você pode executar enquanto fala?', True), ('você consegue agir enquanto fala?', True),
    ('como executar ações enquanto você fala?', False),
])
def test_consciencia_de_capacidade_delimita_o_fluxo_e_a_disponibilidade_de_audio(pergunta, direta):
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    mapa = MapaHabilidadesRuntime()
    resposta = mapa.responder_pergunta_capacidade(pergunta)
    contexto = mapa.contexto_para_prompt(pergunta)
    assert 'cooperacao [disponivel]' in contexto
    assert bool(resposta) is direta
    if direta:
        assert 'texto copiado' in resposta
        assert 'quando a voz está disponível' in resposta
        assert 'anúncio não confirma' in resposta
    assert 'progresso e conclusão' in contexto
