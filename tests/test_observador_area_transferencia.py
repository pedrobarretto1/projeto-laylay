from __future__ import annotations

import time

from mente_laylay.especialistas.area_transferencia import (
    AreaTransferenciaRuntime,
    classificar_conteudo_passivo,
)
from mente_laylay.percepcao.observador_area_transferencia import (
    ObservadorAreaTransferenciaRuntime,
    classificar_resposta_oferta,
)
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime


def _recibo_presenca_agendada():
    return {
        "status": "proposta_cognitiva",
        "proposta_comunicativa": {
            "agendada": True,
            "autoriza_execucao": False,
        },
    }


class ClipboardFalso:
    def __init__(self, texto: str = "") -> None:
        self.texto = texto

    def ler(self):
        return self.texto

    def escrever(self, texto):
        self.texto = texto


def _pendencias() -> PendenciaAcaoRuntime:
    estado = {}

    def atualizar(transformar):
        novo = transformar(dict(estado))
        estado.clear()
        estado.update(novo)
        return dict(estado)

    return PendenciaAcaoRuntime(
        estado_getter=lambda: estado,
        estado_atualizar=atualizar,
        agora=lambda: 100.0,
        log=lambda *_args: None,
    )


def test_resposta_da_oferta_reutiliza_linguagem_natural_compartilhada() -> None:
    aceites = (
        "sim", "quero sim", "eu quero sim", "pode sim", "manda ver",
        "pode abrir", "pode me falar",
    )
    recusas = (
        "não", "não quero", "agora não", "não precisa", "deixa quieto",
        "não investiga isso", "deixa para depois", "melhor deixar isso pra depois",
    )

    for texto in aceites:
        assert classificar_resposta_oferta(texto, "investigar_erro") == "aceitar"
    for texto in recusas:
        assert classificar_resposta_oferta(texto, "investigar_erro") == "recusar"


def _area(clipboard: ClipboardFalso) -> AreaTransferenciaRuntime:
    return AreaTransferenciaRuntime(
        falar=lambda *_args: None,
        leitor=clipboard.ler,
        escritor=clipboard.escrever,
        log=lambda *_args: None,
    )


def test_classificacao_passiva_nao_devolve_texto_bruto() -> None:
    casos = {
        "https://example.com/caminho?origem=teste": "link",
        "Traceback: ValueError: volume inválido": "erro",
        "def exemplo():\n    return 1\nclass Outra:\n    pass": "codigo",
        "texto " * 160: "texto_longo",
        "uma frase qualquer": "texto_curto",
    }
    for conteudo, tipo in casos.items():
        resultado = classificar_conteudo_passivo(conteudo)
        assert resultado["tipo"] == tipo
        assert conteudo not in str(resultado)


def test_snapshot_sensivel_publica_so_metadados() -> None:
    clipboard = ClipboardFalso("API_KEY=segredo-super-secreto-123")
    snapshot = _area(clipboard).snapshot_passivo()

    assert snapshot["tipo"] == "sensivel"
    assert snapshot["bloqueado"] is True
    assert "segredo-super" not in str(snapshot)
    assert "conteudo" not in snapshot


def test_primeiro_conteudo_vira_baseline_e_nao_interrompe() -> None:
    clipboard = ClipboardFalso("Traceback: ValueError: antigo")
    area = _area(clipboard)
    eventos = []
    runtime = ObservadorAreaTransferenciaRuntime(
        snapshot_getter=area.snapshot_passivo,
        considerar_presenca=lambda evento: eventos.append(evento) or _recibo_presenca_agendada(),
        estabilidade_s=1,
        log=lambda *_args: None,
    )

    assert runtime.observar_uma_vez()["status"] == "baseline"
    assert runtime.observar_uma_vez()["status"] == "sem_mudanca"
    assert eventos == []


def test_baseline_preparada_antes_da_thread_detecta_primeira_copia_nova() -> None:
    agora = [0.0]
    clipboard = ClipboardFalso("conteúdo antigo")
    area = _area(clipboard)
    eventos = []
    runtime = ObservadorAreaTransferenciaRuntime(
        snapshot_getter=area.snapshot_passivo,
        considerar_presenca=lambda evento: eventos.append(evento) or _recibo_presenca_agendada(),
        estabilidade_s=1,
        clock=lambda: agora[0],
        log=lambda *_args: None,
    )
    assert runtime.preparar_baseline()["status"] == "baseline"
    clipboard.texto = "Error: falha copiada depois da inicialização"

    assert runtime.observar_uma_vez()["status"] == "estabilizando"
    agora[0] = 1.1
    assert runtime.observar_uma_vez()["status"] == "publicada"
    assert eventos[0]["acao_sugerida"] == "investigar_erro"


def test_novo_ctrl_c_do_mesmo_texto_e_detectado_pela_sequencia_windows() -> None:
    agora = [0.0]
    sequencia = [10]
    snapshot = {
        "status": "ok", "tipo": "erro", "relevante": True,
        "assinatura": "hash-igual", "sequencia_evento": 10,
        "tamanho": 40, "confianca": 0.92,
    }
    eventos = []
    runtime = ObservadorAreaTransferenciaRuntime(
        snapshot_getter=lambda: {**snapshot, "sequencia_evento": sequencia[0]},
        considerar_presenca=lambda evento: eventos.append(evento) or _recibo_presenca_agendada(),
        estabilidade_s=1,
        clock=lambda: agora[0],
        log=lambda *_args: None,
    )
    runtime.preparar_baseline()
    sequencia[0] = 11

    assert runtime.observar_uma_vez()["status"] == "estabilizando"
    agora[0] = 1.1
    assert runtime.observar_uma_vez()["status"] == "publicada"
    assert eventos


def test_mesmo_conteudo_nao_oferece_de_novo_depois_que_fala_comecou() -> None:
    agora = [0.0]
    sequencia = [10]
    snapshot = {
        "status": "ok", "tipo": "erro", "relevante": True,
        "assinatura": "hash-do-erro", "sequencia_evento": 10,
        "tamanho": 40, "confianca": 0.92,
    }
    eventos = []
    entregues = []
    runtime = ObservadorAreaTransferenciaRuntime(
        snapshot_getter=lambda: {**snapshot, "sequencia_evento": sequencia[0]},
        considerar_presenca=lambda evento: eventos.append(evento) or _recibo_presenca_agendada(),
        oferta_entregue=lambda oferta: entregues.append(dict(oferta)),
        estabilidade_s=1,
        clock=lambda: agora[0],
        log=lambda *_args: None,
    )
    runtime.preparar_baseline()
    sequencia[0] = 11
    runtime.observar_uma_vez()
    agora[0] = 1.1
    assert runtime.observar_uma_vez()["status"] == "publicada"
    eventos[0]["ao_iniciar"]()
    eventos[0]["ao_concluir"](True, "entregue")

    sequencia[0] = 12
    agora[0] = 2.0
    resultado = runtime.observar_uma_vez()

    assert resultado["status"] == "duplicada_conteudo"
    assert len(eventos) == 1


def test_oferta_bloqueada_e_retentada_quando_contexto_fica_livre() -> None:
    agora = [0.0]
    clipboard = ClipboardFalso("inicial")
    area = _area(clipboard)
    decisoes = [
        {"status": "bloqueada", "motivo": "usuario_acabou_de_falar"},
        _recibo_presenca_agendada(),
    ]
    runtime = ObservadorAreaTransferenciaRuntime(
        snapshot_getter=area.snapshot_passivo,
        considerar_presenca=lambda _evento: decisoes.pop(0),
        estabilidade_s=1,
        clock=lambda: agora[0],
        log=lambda *_args: None,
    )
    runtime.observar_uma_vez()
    clipboard.texto = "Timeout: serviço não respondeu"
    runtime.observar_uma_vez()
    agora[0] = 1.1

    assert runtime.observar_uma_vez()["status"] == "aguardando_contexto"
    agora[0] = 5.0
    assert runtime.observar_uma_vez()["status"] == "aguardando_contexto"
    agora[0] = 9.2
    assert runtime.observar_uma_vez()["status"] == "publicada"
    assert decisoes == []


def test_erro_novo_estavel_vira_oportunidade_sem_texto_bruto() -> None:
    agora = [0.0]
    clipboard = ClipboardFalso("inicial")
    area = _area(clipboard)
    eventos = []
    runtime = ObservadorAreaTransferenciaRuntime(
        snapshot_getter=area.snapshot_passivo,
        considerar_presenca=lambda evento: eventos.append(evento) or _recibo_presenca_agendada(),
        contexto_getter=lambda: {"titulo_janela": "Visual Studio Code"},
        estabilidade_s=2,
        clock=lambda: agora[0],
        log=lambda *_args: None,
    )
    runtime.observar_uma_vez()
    clipboard.texto = "Traceback: ValueError: detalhe privado do projeto"

    assert runtime.observar_uma_vez()["status"] == "estabilizando"
    agora[0] = 1.5
    assert runtime.observar_uma_vez()["status"] == "estabilizando"
    agora[0] = 2.1
    resultado = runtime.observar_uma_vez()

    assert resultado["status"] == "publicada"
    assert len(eventos) == 1
    assert eventos[0]["categoria"] == "dica"
    assert eventos[0]["executar_automaticamente"] is False
    assert "detalhe privado" not in str(eventos[0])
    assert eventos[0]["evidencias"] == [
        "mensagem de erro copiada", "Visual Studio Code",
    ]
    assert "diga:" not in eventos[0]["fala"].casefold()
    assert eventos[0]["fala"].endswith("Quer que eu investigue?")


def test_recusa_recente_silencia_nova_oferta_da_mesma_acao() -> None:
    agora = [0.0]
    clipboard = ClipboardFalso("inicial")
    area = _area(clipboard)
    eventos = []
    runtime = ObservadorAreaTransferenciaRuntime(
        snapshot_getter=area.snapshot_passivo,
        considerar_presenca=lambda evento: eventos.append(evento)
        or _recibo_presenca_agendada(),
        contexto_getter=lambda: {
            "clipboard_ofertas_silenciadas": {
                "investigar_erro": time.time() + 600.0,
            },
        },
        estabilidade_s=1,
        clock=lambda: agora[0],
        log=lambda *_args: None,
    )
    runtime.observar_uma_vez()
    clipboard.texto = "Traceback: RuntimeError: falha nova"
    runtime.observar_uma_vez()
    agora[0] = 1.1

    resultado = runtime.observar_uma_vez()

    assert resultado["status"] == "silenciada_por_recusa"
    assert resultado["acao_sugerida"] == "investigar_erro"
    assert eventos == []


def test_oferta_aceita_respostas_naturais_sem_comando_exato() -> None:
    for texto in ("sim", "pode", "dá uma olhada", "investiga isso pra mim"):
        assert classificar_resposta_oferta(texto, "investigar_erro") == "aceitar"
    for texto in ("não precisa", "deixa quieto", "agora não"):
        assert classificar_resposta_oferta(texto, "investigar_erro") == "recusar"
    assert classificar_resposta_oferta("vou abrir outro programa", "investigar_erro") == "ignorar"
    assert classificar_resposta_oferta("pode me dizer as horas?", "investigar_erro") == "ignorar"


def test_pendencia_sobrevive_quando_usuario_interrompe_fala_ja_iniciada() -> None:
    agora = [0.0]
    clipboard = ClipboardFalso("inicial")
    area = _area(clipboard)
    eventos = []
    entregues = []
    runtime = ObservadorAreaTransferenciaRuntime(
        snapshot_getter=area.snapshot_passivo,
        considerar_presenca=lambda evento: eventos.append(evento) or _recibo_presenca_agendada(),
        oferta_entregue=lambda oferta: entregues.append(dict(oferta)),
        estabilidade_s=1,
        clock=lambda: agora[0],
        log=lambda *_args: None,
    )
    runtime.observar_uma_vez()
    clipboard.texto = "Traceback: RuntimeError: algo falhou"
    runtime.observar_uma_vez()
    agora[0] = 1.1
    runtime.observar_uma_vez()

    assert entregues == []
    eventos[0]["ao_iniciar"]()
    assert entregues[0]["acao_sugerida"] == "investigar_erro"
    assert entregues[0]["assinatura"]
    eventos[0]["ao_concluir"](False, "fila_recusou")
    assert len(entregues) == 1


def test_modo_sombra_classifica_sem_publicar() -> None:
    agora = [0.0]
    clipboard = ClipboardFalso("inicial")
    area = _area(clipboard)
    eventos = []
    runtime = ObservadorAreaTransferenciaRuntime(
        snapshot_getter=area.snapshot_passivo,
        considerar_presenca=lambda evento: eventos.append(evento),
        modo="sombra",
        estabilidade_s=1,
        clock=lambda: agora[0],
        log=lambda *_args: None,
    )
    runtime.observar_uma_vez()
    clipboard.texto = "https://example.com/documento"
    runtime.observar_uma_vez()
    agora[0] = 1.1

    resultado = runtime.observar_uma_vez()

    assert resultado["status"] == "sombra"
    assert eventos == []
    assert resultado["evento"]["executar_automaticamente"] is False


def test_conteudo_consumido_por_comando_explicito_nao_gera_oferta() -> None:
    agora = [0.0]
    clipboard = ClipboardFalso("inicial")
    area = _area(clipboard)
    eventos = []
    runtime = ObservadorAreaTransferenciaRuntime(
        snapshot_getter=area.snapshot_passivo,
        considerar_presenca=lambda evento: eventos.append(evento) or _recibo_presenca_agendada(),
        estabilidade_s=1,
        clock=lambda: agora[0],
        log=lambda *_args: None,
    )
    runtime.observar_uma_vez()
    clipboard.texto = "texto longo " * 80
    assert runtime.observar_uma_vez()["status"] == "estabilizando"

    assert runtime.marcar_conteudo_consumido(area.snapshot_passivo()) is True
    agora[0] = 2.0

    assert runtime.observar_uma_vez()["status"] in {
        "duplicada_conteudo", "sem_mudanca",
    }
    assert eventos == []


def test_segredo_e_texto_curto_sao_silenciosos_e_deduplicados() -> None:
    agora = [0.0]
    clipboard = ClipboardFalso("inicial")
    area = _area(clipboard)
    eventos = []
    runtime = ObservadorAreaTransferenciaRuntime(
        snapshot_getter=area.snapshot_passivo,
        considerar_presenca=lambda evento: eventos.append(evento),
        estabilidade_s=1,
        clock=lambda: agora[0],
        log=lambda *_args: None,
    )
    runtime.observar_uma_vez()

    clipboard.texto = "token=segredo-super-secreto-123"
    runtime.observar_uma_vez()
    agora[0] = 1.1
    assert runtime.observar_uma_vez()["status"] == "bloqueada"

    clipboard.texto = "copiar e colar"
    agora[0] = 2.0
    runtime.observar_uma_vez()
    agora[0] = 3.1
    assert runtime.observar_uma_vez()["status"] == "ignorada"
    assert runtime.observar_uma_vez()["status"] == "sem_mudanca"
    assert eventos == []


def test_escrita_da_propria_laylay_nao_gera_sugestao() -> None:
    clipboard = ClipboardFalso("original")
    area = AreaTransferenciaRuntime(
        falar=lambda *_args: None,
        enviar_mensagem=lambda *_args, **_kwargs: "resultado " * 120,
        leitor=clipboard.ler,
        escritor=clipboard.escrever,
        pendencia_runtime=_pendencias(),
        log=lambda *_args: None,
    )
    area.processar("resume o que eu copiei")
    area.processar("copia o resultado")

    snapshot = area.snapshot_passivo()

    assert snapshot["escrita_propria"] is True
