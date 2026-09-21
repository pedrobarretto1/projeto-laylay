from __future__ import annotations

import threading
import time

import mente_laylay.autonomia.fluxos_conversa as fluxos_conversa
from mente_laylay.autonomia.feedback_pendente_runtime import FeedbackPendenteRuntime
from mente_laylay.personalidade.orquestrador_fala_runtime import OrquestradorFalaRuntime


URL = "https://www.youtube.com/watch?v=aaaaaaaaaaa"
TITULO = "Faixa Receipt"
CANAL = "Canal Receipt"
TURNO_ID = "red151-c3-turno"


class _EstadoCompartilhadoFake:
    def __init__(self):
        self.mental = {
            "turno_atual": {
                "id": TURNO_ID,
                "modalidade": "confirmacao",
                "modalidade_geral": "confirmacao",
                "autoriza_execucao": False,
                "veto_execucao_operacional": False,
            },
            "plano_turno_atual": {
                "id": TURNO_ID,
                "fase": "planejado",
                "texto_usuario": "sim",
                "modalidade": "confirmacao",
                "ato_principal": "confirmacao",
                "requer_execucao": False,
                "autoriza_execucao": False,
                "comandos": [],
                "erros": [],
            },
            "ultima_entrada": "sim",
            "pendencia_atual": {},
        }
        self.conversacional = {}

    def substituir(self, dominio, valor):
        if dominio == "mental":
            self.mental = dict(valor or {})
        elif dominio == "conversacional":
            self.conversacional = dict(valor or {})

    def atualizar_campos(self, dominio, **campos):
        atual = dict(getattr(self, dominio, {}) or {})
        atual.update(campos)
        setattr(self, dominio, atual)


class _VozFake:
    def __init__(self, eventos):
        self.eventos = eventos
        self.falas = []

    def falar(self, texto, emocao="calma", nivel=1, **_kwargs):
        fala = str(texto or "")
        self.eventos.append(("voz", fala))
        self.falas.append(fala)
        return True


class _MusicaOperacoesOK:
    def __init__(self, eventos):
        self.eventos = eventos
        self.ultima = ""

    def faixa_atual(self):
        return {
            "url": URL,
            "title": TITULO,
            "canal": CANAL,
        }

    def criar_playlist(self, nome):
        self.eventos.append(("create", nome))
        return {
            "ok": True,
            "criada": True,
            "status": "playlist_criada",
            "nome": nome,
        }

    def adicionar_faixa(self, nome, url, titulo, canal):
        self.eventos.append(("add", nome, url, titulo, canal))
        return True

    def definir_ultima_playlist(self, nome):
        self.eventos.append(("ultima", nome))
        self.ultima = str(nome or "")


def _novo_orquestrador(estado, eventos, logs):
    voz = _VozFake(eventos)

    def dirigir_fala(
        fala,
        *,
        texto_usuario="",
        estado_mental=None,
        emocao="calma",
        nivel=None,
        proativa=False,
        preservar_texto=True,
        **_kwargs,
    ):
        return {
            "fala": str(fala or ""),
            "emocao": str(emocao or "calma"),
            "nivel": int(nivel or 1),
            "proativa": bool(proativa),
            "preservar_texto": bool(preservar_texto),
        }

    servicos = {
        "_registrar_mente_curta": lambda *_args, **_kwargs: None,
        "_estado_compartilhado_runtime": estado,
        "_encerrar_topico_mente": (
            lambda mental, conversa, motivo="": (
                dict(mental or {}),
                dict(conversa or {}),
            )
        ),
        "salvar_memoria": lambda: None,
        "print": lambda *args, **_kwargs: logs.append(
            " ".join(str(x) for x in args)
        ),
        "_dirigir_fala_mente": dirigir_fala,
        "_voz_runtime": voz,
        "_registrar_continuidade_da_fala_mente": (
            lambda mental, _fala, **_kwargs: dict(mental or {})
        ),
        "_threading": threading,
        "_agendar_fala_proativa": lambda *_args, **_kwargs: False,
    }

    return OrquestradorFalaRuntime(servicos_iniciais=servicos), voz


def _registrador_plano_fake(estado, eventos):
    """
    Simula somente a parte que interessa do adaptador real:
    um receipt operacional confirmado precisa entrar em plano.comandos
    ANTES de a fala chegar ao guardião.
    """
    chamadas = []

    def registrar(
        resultado=None,
        texto="",
        executou=None,
        *,
        origem="",
        status="",
    ):
        dados = dict(resultado or {}) if isinstance(resultado, dict) else {}
        intent = str(
            dados.get("intent")
            or dados.get("acao")
            or ""
        ).strip().upper()
        status_final = str(
            status
            or dados.get("status")
            or ""
        ).strip()
        confirmado = dados.get("confirmado")
        executou_final = (
            executou
            if executou is not None
            else dados.get("executou")
        )

        chamadas.append(
            {
                "intent": intent,
                "status": status_final,
                "confirmado": confirmado,
                "executou": executou_final,
                "texto": str(texto or ""),
                "origem": str(origem or ""),
            }
        )
        eventos.append(
            (
                "receipt",
                intent,
                status_final,
                confirmado,
                executou_final,
            )
        )

        plano = dict(estado.mental.get("plano_turno_atual") or {})
        comandos = list(plano.get("comandos") or [])
        comandos.append(
            {
                "intent": intent,
                "status": status_final,
                "confirmado": confirmado,
                "executou": executou_final,
                "params": dict(dados.get("params") or {}),
                "alvo": str(dados.get("alvo") or ""),
                "origem": str(origem or dados.get("origem") or ""),
            }
        )
        plano["comandos"] = comandos
        estado.atualizar_campos(
            "mental",
            plano_turno_atual=plano,
        )

    return registrar, chamadas


def _montar_feedback_com_saida_final(monkeypatch):
    eventos = []
    logs = []
    estado = _EstadoCompartilhadoFake()
    orquestrador, voz = _novo_orquestrador(estado, eventos, logs)
    musica = _MusicaOperacoesOK(eventos)

    continuidades = {
        "playlist_sugestao_pendente": {
            "playlist": "vmz",
            "ts": time.time(),
        },
        "rotina_sugestao_pendente": None,
        "email_sugestao_pendente": None,
    }

    def continuidades_get(chave):
        return continuidades.get(chave)

    def continuidades_update(**valores):
        continuidades.update(valores)

    registrar, receipts = _registrador_plano_fake(
        estado,
        eventos,
    )

    # A primeira variante de sucesso é uma variante REAL de produção:
    # "Beleza, criei e guardei ...".
    # Forçá-la remove a aleatoriedade e prova que nenhuma frase válida pode
    # depender da sorte para atravessar o guardião.
    monkeypatch.setattr(
        fluxos_conversa,
        "_escolher_fala_variada",
        lambda itens, *_args, **_kwargs: list(itens)[0],
    )

    feedback = FeedbackPendenteRuntime(
        contexto_getter=lambda: {
            "handle_feedback_pendente": fluxos_conversa.handle_feedback_pendente,
            "continuidades_get": continuidades_get,
            "continuidades_update": continuidades_update,
            "musica_operacoes": musica,
            "falar_com_lipsync": orquestrador.falar,
            "yt_clean_title": lambda valor: str(valor or ""),
            # A produção já fornece essa dependência ao contexto geral.
            # O RED verifica se o feedback simples realmente a usa/repassa.
            "registrar_resultado_execucao": registrar,
        },
        log=lambda *_args, **_kwargs: None,
    )

    return {
        "feedback": feedback,
        "estado": estado,
        "voz": voz,
        "musica": musica,
        "continuidades": continuidades,
        "eventos": eventos,
        "logs": logs,
        "receipts": receipts,
        "registrar": registrar,
        "orquestrador": orquestrador,
    }


def test_red151_c3_feedback_simples_registra_receipt_antes_da_fala(monkeypatch):
    """
    RED principal.

    CREATE/ADD confirmados não podem falar sucesso antes de publicar o receipt
    no plano que o guardião usa como fonte de verdade.
    """
    ctx = _montar_feedback_com_saida_final(monkeypatch)

    tratado = ctx["feedback"].handle_feedback_pendente("sim")

    assert tratado is True

    # CREATE e ADD aconteceram.
    assert ctx["eventos"][0] == ("create", "vmz")
    assert ctx["eventos"][1][:2] == ("add", "vmz")

    # PRIMEIRA FRONTEIRA RED:
    # o feedback simples atual não repassa/usa registrar_resultado_execucao.
    assert ctx["receipts"], (
        "RED151-C3: CREATE/ADD foram executados, mas nenhum receipt operacional "
        "foi registrado no plano antes da fala."
    )

    # O receipt confirmado precisa existir antes da voz.
    indice_receipt = next(
        i for i, evento in enumerate(ctx["eventos"])
        if evento[0] == "receipt" and evento[3] is True
    )
    indice_voz = next(
        i for i, evento in enumerate(ctx["eventos"])
        if evento[0] == "voz"
    )

    assert indice_receipt < indice_voz, (
        "RED151-C3: a fala foi publicada antes do receipt confirmado."
    )

    plano = dict(
        ctx["estado"].mental.get("plano_turno_atual")
        or {}
    )
    confirmados = [
        item
        for item in list(plano.get("comandos") or [])
        if isinstance(item, dict)
        and item.get("confirmado") is True
    ]
    assert confirmados, (
        "RED151-C3: o plano visto pelo guardião não recebeu comando confirmado."
    )

    esperado = (
        f"Beleza, criei e guardei {TITULO} "
        "na playlist vmz."
    )
    assert ctx["voz"].falas == [esperado], (
        "RED151-C3: uma operação realmente confirmada teve sua fala reescrita "
        "pelo guardião por falta de receipt no plano. "
        f"Fala final={ctx['voz'].falas!r}; logs={ctx['logs']!r}"
    )


def test_controle_guardiao_reescreve_criei_sem_receipt():
    """
    Controle positivo do diagnóstico:
    sem receipt, o guardião DEVE desconfiar de "criei".
    """
    eventos = []
    logs = []
    estado = _EstadoCompartilhadoFake()
    orquestrador, voz = _novo_orquestrador(
        estado,
        eventos,
        logs,
    )

    original = (
        f"Beleza, criei e guardei {TITULO} "
        "na playlist vmz."
    )

    assert orquestrador.falar(original) is True
    assert len(voz.falas) == 1
    assert voz.falas[0] != original
    assert "me adiantei" in voz.falas[0].casefold()
    assert any(
        "execucao_alegada_sem_resultado" in log
        for log in logs
    )


def test_controle_guardiao_preserva_criei_com_receipt_confirmado():
    """
    Controle negativo:
    o guardião não precisa ser relaxado; com receipt confirmado ele preserva
    a mesma fala que rejeita no controle anterior.
    """
    eventos = []
    logs = []
    estado = _EstadoCompartilhadoFake()

    plano = dict(
        estado.mental["plano_turno_atual"]
    )
    plano["comandos"] = [
        {
            "intent": "PLAYLIST_ADD",
            "alvo": "vmz",
            "status": "playlist_musica_adicionada",
            "params": {
                "nome_playlist": "vmz",
            },
            "executou": True,
            "confirmado": True,
            "origem": "feedback_playlist",
        }
    ]
    estado.atualizar_campos(
        "mental",
        plano_turno_atual=plano,
    )

    orquestrador, voz = _novo_orquestrador(
        estado,
        eventos,
        logs,
    )

    original = (
        f"Beleza, criei e guardei {TITULO} "
        "na playlist vmz."
    )

    assert orquestrador.falar(original) is True
    assert voz.falas == [original]
    assert not any(
        "execucao_alegada_sem_resultado" in log
        for log in logs
    )


def test_controle_falar_resultado_operacional_sozinho_nao_injeta_receipt_no_plano():
    """
    Falsificação importante:
    trocar apenas falar() por falar_resultado_operacional() não basta.

    Essa API deduplica a confirmação, mas ainda chama self.falar(); quem torna
    a alegação confiável é o receipt já presente em plano.comandos.
    """
    eventos = []
    logs = []
    estado = _EstadoCompartilhadoFake()
    orquestrador, voz = _novo_orquestrador(
        estado,
        eventos,
        logs,
    )

    resultado = {
        "intent": "PLAYLIST_ADD",
        "alvo": "vmz",
        "status": "playlist_musica_adicionada",
        "params": {
            "nome_playlist": "vmz",
        },
        "executou": True,
        "confirmado": True,
        "origem": "feedback_playlist",
    }
    original = (
        f"Beleza, criei e guardei {TITULO} "
        "na playlist vmz."
    )

    assert orquestrador.falar_resultado_operacional(
        resultado,
        original,
    ) is True

    # A API de voz, sozinha, não altera plano.comandos.
    plano = dict(
        estado.mental.get("plano_turno_atual")
        or {}
    )
    assert list(plano.get("comandos") or []) == []

    # Portanto o guardião ainda reescreve a alegação.
    assert len(voz.falas) == 1
    assert voz.falas[0] != original
    assert "me adiantei" in voz.falas[0].casefold()
