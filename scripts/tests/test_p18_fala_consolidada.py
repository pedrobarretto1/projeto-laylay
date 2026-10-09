"""A autoria pode substituir um candidato antes da voz, nunca durante ela."""

from scripts.tests.test_voz_filas_isoladas import _runtime


def test_candidato_tardio_nao_muda_texto_ou_emocao_da_fala_em_reproducao():
    runtime = _runtime()
    runtime.chave_turno_cb = lambda: 25.0
    runtime.iniciar_worker = lambda: None
    assert runtime.falar("Resposta factual confirmada.", "calma", 1) is True
    observacoes = []

    def reproduzir(texto, emocao, nivel):
        pedido = runtime._pedido_turno_pendente
        antes = dict(pedido)
        aceitou = runtime.falar("Uma bronca diferente durante a entrega.", "brava", 3)
        observacoes.append((texto, emocao, nivel, aceitou, antes, dict(pedido)))
        runtime.stop_event.set()
        return True

    runtime.reproduzir_fala = reproduzir
    runtime.worker_de_falas()
    texto, emocao, nivel, aceitou, antes, depois = observacoes[0]
    assert aceitou is False, "o candidato já estava congelado para a voz"
    assert (texto, emocao, nivel) == (antes["texto"], antes["emocao"], antes["nivel"])
    assert (depois["texto"], depois["emocao"], depois["nivel"]) == (texto, emocao, nivel)
    assert runtime.fila.qsize() == 0


def test_candidato_antes_da_reproducao_ainda_pode_consolidar_uma_fila():
    runtime = _runtime()
    runtime.chave_turno_cb = lambda: 25.0
    runtime.iniciar_worker = lambda: None
    assert runtime.falar("Aguarde.") is True
    assert runtime.falar("O resultado confirmado é este.") is True
    assert runtime.fila.qsize() == 1
    assert runtime._pedido_turno_pendente["texto"] == "O resultado confirmado é este."
