from __future__ import annotations

from copy import deepcopy
import inspect
import json
import time
from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.autonomia.processamento_resposta_ia import extrair_leitura_semantica_da_ia
from mente_laylay.cognicao.composicao_turno import ComposicaoTurnoRuntime
from mente_laylay.cognicao.contratos_turno import ContratoOcorrenciaTurno, ContratoPropostaPrincipal
from mente_laylay.cognicao.decisao_turno import (
    criar_validador_comandos_turno_runtime,
    motivo_incoerencia_contratos_turno,
)
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.orquestrador_turno_runtime import (
    alinhar_identidade_plano_revisao,
    atualizar_planejamento_turno,
    registrar_leitura_semantica_principal,
)
from mente_laylay.cognicao.plano_turno import atualizar_plano_turno, planejar_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, ResultadoModelo
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.trilha_turno import registrar_etapa_turno


CASOS = [
    ("cria a playlist foco", "PLAYLIST_CREATE"),
    ("liga a lâmpada do quarto", "IOT_CONTROL"),
    ("abre a Calculadora", "APP_OPEN"),
]


def _frame(texto: str) -> dict:
    turno = classificar_modalidade_turno(texto)
    retrato, _ = construir_retrato_turno(texto, turno=turno, mente={}, contexto_perceptivo={})
    turno["retrato_id"] = retrato["id"]
    plano = planejar_turno(texto, turno=turno, mente={})
    return {"turno_atual": turno, "plano_turno_atual": plano, "retrato_turno_atual": retrato}


def _nova_ocorrencia(frame: dict) -> dict:
    novo = deepcopy(frame)
    identidade = int(frame["turno_atual"]["id"]) + 1
    novo["turno_atual"].update(id=identidade, retrato_id=identidade)
    novo["plano_turno_atual"].update(id=identidade, retrato_id=identidade)
    novo["plano_turno_atual"]["decisao_turno"]["turno_id"] = identidade
    novo["retrato_turno_atual"]["id"] = identidade
    return novo


def _servicos(estado: EstadoCompartilhadoRuntime) -> dict:
    return {
        "_estado_compartilhado_runtime": estado,
        "_atualizar_plano_turno_mente": atualizar_plano_turno,
        "_registrar_etapa_turno_mente": registrar_etapa_turno,
        "time": time, "print": lambda *_args: None,
    }


def _principal(frame: dict, texto: str, *, sucesso: bool = True) -> ContratoPropostaPrincipal:
    return ContratoPropostaPrincipal(
        turno_id=frame["turno_atual"]["id"], texto_usuario=texto,
        resposta_bruta='{"fala":"Vou verificar.","comandos":[],"leitura_turno":["pedido_acao"]}',
        sucesso_modelo=sucesso,
    )


def _publicar(estado, fase, principal, **kwargs):
    # Compatibilidade apenas para reproduzir o comportamento anterior ao candidato.
    parametros = inspect.signature(atualizar_planejamento_turno).parameters
    extras = {"proposta_principal": principal} if "proposta_principal" in parametros else {}
    return atualizar_planejamento_turno(lambda: _servicos(estado), fase, **extras, **kwargs)


@pytest.mark.parametrize("texto,intent", CASOS)
@pytest.mark.parametrize("fase", ["resposta_planejada", "executado", "falha_execucao"])
def test_callback_antigo_nao_publica_em_nova_ocorrencia_coerente(texto, intent, fase) -> None:
    original = _frame(texto)
    principal = _principal(original, texto)
    atual = _nova_ocorrencia(original)
    assert motivo_incoerencia_contratos_turno(
        atual["turno_atual"], atual["plano_turno_atual"], atual["retrato_turno_atual"],
    ) == "", "o RED deve alcançar um frame novo internamente coerente"
    estado = EstadoCompartilhadoRuntime(mental=atual)
    antes = estado.snapshot()

    publicado = _publicar(
        estado, fase, principal, comandos=[{"intent": intent}], fala="Vou verificar.",
    )

    assert publicado == {}, "callback de outra ocorrência precisa ser recusado antes da escrita"
    assert estado.snapshot() == antes, "não alterar plano, receipts, fase ou trilha do turno novo"


@pytest.mark.parametrize("principal", [None, {}, {"turno_id": "42"}])
def test_writer_moderno_nao_reconstroi_ocorrencia_de_fonte_malformada(principal) -> None:
    estado = EstadoCompartilhadoRuntime(mental=_frame("cria a playlist foco"))
    antes = estado.snapshot()
    assert _publicar(estado, "resposta_planejada", principal) == {}
    assert estado.snapshot() == antes


@pytest.mark.parametrize("sucesso", [True, False])
@pytest.mark.parametrize("comandos", [None, []])
def test_mesma_ocorrencia_preserva_receipt_inclusive_na_falha_do_modelo(sucesso, comandos) -> None:
    texto = "cria a playlist foco"
    original = _frame(texto)
    receipt = {"id_solicitacao": "execucao-foco", "intent": "PLAYLIST_CREATE", "alvo": "foco",
               "executou": True, "confirmado": True, "status": "sucesso"}
    original["plano_turno_atual"] = atualizar_plano_turno(
        original["plano_turno_atual"], fase="executado", comandos=[receipt],
    )
    receipts_antes = deepcopy(original["plano_turno_atual"]["comandos"])
    estado = EstadoCompartilhadoRuntime(mental=original)
    publicado = _publicar(estado, "resposta_planejada", _principal(original, texto, sucesso=sucesso), comandos=comandos)
    assert publicado["comandos"] == receipts_antes
    assert publicado["fase"] == "resposta_planejada"
    assert estado.mental["trilha_decisoes_turno"][-1]["turno_id"] == original["turno_atual"]["id"]


def test_writer_confere_ocorrencia_dentro_da_transacao() -> None:
    texto = "cria a playlist foco"
    original = _frame(texto)
    estado = EstadoCompartilhadoRuntime(mental=original)
    atualizar_real = estado.atualizar
    atual = _nova_ocorrencia(original)

    def trocar_antes_do_lock(grupo, funcao):
        estado.substituir("mental", atual)
        return atualizar_real(grupo, funcao)

    estado.atualizar = trocar_antes_do_lock
    publicado = _publicar(estado, "resposta_planejada", _principal(original, texto))
    assert publicado == {}
    assert estado.obter_copia("mental", "plano_turno_atual") == atual["plano_turno_atual"]


@pytest.mark.parametrize("texto,intent", CASOS)
@pytest.mark.parametrize("troca", ["nenhuma", "apos_validacao", "durante_dispatch"])
def test_runtime_interrompe_fluxo_quando_writer_recusa_ocorrencia(texto, intent, troca) -> None:
    original = _frame(texto)
    estado = EstadoCompartilhadoRuntime(mental=original)
    composicao = ComposicaoTurnoRuntime(servicos=_servicos(estado))
    validador = criar_validador_comandos_turno_runtime(estado_runtime=estado)
    chamadas = []
    publicacoes = []
    snapshot_novo = []

    def trocar():
        estado.substituir("mental", _nova_ocorrencia(original))
        snapshot_novo.append(estado.snapshot())

    class ValidarETrocar:
        def __call__(self, comandos):
            return validador(comandos)

        def validar_proposta(self, comandos, principal):
            resultado = validador.validar_proposta(comandos, principal)
            assert resultado["ocorrencia_vinculada"] is True
            if troca == "apos_validacao":
                trocar()
            return resultado

    def publicar_proposta(fase, principal, **kwargs):
        moderno = getattr(composicao, "atualizar_proposta", None)
        publicado = moderno(fase, principal, **kwargs) if callable(moderno) else composicao.atualizar(fase, **kwargs)
        publicacoes.append((fase, publicado))
        return publicado

    def dispatch(*_args):
        chamadas.append("dispatch")
        if troca == "durante_dispatch":
            trocar()
        return {"erros": []}

    comando = {"intent": intent, "params": {}}
    runtime = RespostaIARuntime(contexto_getter=lambda: {
        "obter_turno_atual": lambda: estado.obter_copia("mental", "turno_atual"),
        "usar_modo_rapido": lambda _texto: False,
        "preparacao_conversa": SimpleNamespace(preparar_pacote=lambda _texto: PacotePrompt(())),
        "modelo_llm": SimpleNamespace(executar=lambda _pedido: ResultadoModelo(
            json.dumps({"fala": "Vou verificar.", "comandos": [comando]}), True,
        )),
        "preparar_resposta": lambda _texto, bruto: json.loads(bruto),
        "validar_comandos_planejados": ValidarETrocar(),
        "atualizar_plano_turno": composicao.atualizar,
        "atualizar_plano_proposta": publicar_proposta,
        "contexto_dispatch_runtime": SimpleNamespace(montar=lambda: {}),
        "executar_comandos_json": dispatch,
        "contexto_finalizacao_runtime": SimpleNamespace(montar=lambda: {}),
        "finalizar_execucao": lambda *_args: chamadas.append("finalizacao") or {},
    }, log=lambda *_args: None)

    runtime.processar(texto)
    if troca == "nenhuma":
        assert chamadas == ["dispatch", "finalizacao"]
        assert [fase for fase, _ in publicacoes] == ["resposta_planejada", "executado"]
        assert all(plano for _, plano in publicacoes)
    else:
        assert publicacoes and publicacoes[-1][1] == {}, "a primeira fronteira é a publicação recusada"
        assert chamadas == ([] if troca == "apos_validacao" else ["dispatch"])
        assert estado.snapshot() == snapshot_novo[-1]


@pytest.mark.parametrize("texto,intent", CASOS)
def test_leitura_principal_antiga_nao_contamina_turno_novo(texto, intent) -> None:
    original = _frame(texto)
    principal = _principal(original, texto)
    estado = EstadoCompartilhadoRuntime(mental=_nova_ocorrencia(original))
    antes = estado.snapshot()
    leitura = extrair_leitura_semantica_da_ia(principal.resposta_bruta, texto)
    parametros = inspect.signature(registrar_leitura_semantica_principal).parameters
    extras = {"proposta_principal": principal} if "proposta_principal" in parametros else {}
    publicado = registrar_leitura_semantica_principal(
        lambda: _servicos(estado), texto, leitura, **extras,
    )
    assert publicado == {}, "a leitura do mesmo texto ainda pertence à ocorrência antiga"
    assert estado.snapshot() == antes


def test_writer_recusa_texto_diferente_mesmo_com_id_reutilizado() -> None:
    original = _frame("cria a playlist foco")
    atual = _frame("cria a playlist estudo")
    identidade = original["turno_atual"]["id"]
    atual["turno_atual"].update(id=identidade, retrato_id=identidade)
    atual["plano_turno_atual"].update(id=identidade, retrato_id=identidade)
    atual["plano_turno_atual"]["decisao_turno"]["turno_id"] = identidade
    atual["retrato_turno_atual"]["id"] = identidade
    estado = EstadoCompartilhadoRuntime(mental=atual)
    antes = estado.snapshot()
    assert _publicar(estado, "resposta_planejada", _principal(original, "cria a playlist foco")) == {}
    assert estado.snapshot() == antes


def test_writer_vinculado_preserva_revisao_legitima() -> None:
    texto = "Abre o Opera... não, abre a Calculadora."
    revisao = resolver_revisao_intra_turno(texto)
    efetivo = revisao["texto_operacional_efetivo"]
    frame = _frame(efetivo)
    frame["turno_atual"].update(texto=texto, texto_original=texto, texto_operacional_efetivo=efetivo)
    frame["plano_turno_atual"] = alinhar_identidade_plano_revisao(
        frame["plano_turno_atual"], texto_original=texto,
        texto_operacional_efetivo=efetivo, revisao_intra_turno=revisao,
    )
    estado = EstadoCompartilhadoRuntime(mental=frame)
    plano = _publicar(estado, "resposta_planejada", _principal(frame, texto))
    assert plano["id"] == frame["turno_atual"]["id"]
    assert plano["texto_operacional_efetivo"] == efetivo


def test_leitura_vinculada_preserva_frame_e_autoridade_do_mesmo_turno() -> None:
    texto = "cria a playlist foco"
    original = _frame(texto)
    estado = EstadoCompartilhadoRuntime(mental=original)
    antes = estado.obter_copia("mental", "plano_turno_atual")
    composicao = ComposicaoTurnoRuntime(servicos=_servicos(estado))
    principal = _principal(original, texto)
    leitura = extrair_leitura_semantica_da_ia(principal.resposta_bruta, texto)
    resultado = composicao.registrar_leitura_proposta(texto, leitura, principal)
    assert resultado["somente_observacao"] is True
    assert estado.mental["plano_turno_atual"] == antes
    assert estado.mental["turno_atual"]["autoriza_execucao"] == original["turno_atual"]["autoriza_execucao"]


def test_leitura_confere_snapshot_na_publicacao_apos_derivacao(monkeypatch) -> None:
    from mente_laylay.cognicao import orquestrador_turno_runtime as modulo

    texto = "cria a playlist foco"
    original = _frame(texto)
    estado = EstadoCompartilhadoRuntime(mental=original)
    comparar_real = modulo.comparar_com_legado
    atual = _nova_ocorrencia(original)
    snapshot_novo = []

    def comparar_e_trocar(*args):
        resultado = comparar_real(*args)
        estado.substituir("mental", atual)
        snapshot_novo.append(estado.snapshot())
        return resultado

    monkeypatch.setattr(modulo, "comparar_com_legado", comparar_e_trocar)
    principal = _principal(original, texto)
    leitura = extrair_leitura_semantica_da_ia(principal.resposta_bruta, texto)
    resultado = ComposicaoTurnoRuntime(servicos=_servicos(estado)).registrar_leitura_proposta(
        texto, leitura, principal,
    )
    assert resultado == {}
    assert estado.snapshot() == snapshot_novo[-1]


def test_estado_sem_transacao_nao_promete_publicacao_vinculada() -> None:
    original = _frame("cria a playlist foco")
    estado = SimpleNamespace(mental=deepcopy(original))
    estado.atualizar_campos = lambda *_args, **campos: estado.mental.update(campos)
    principal = _principal(original, "cria a playlist foco")
    assert _publicar(estado, "resposta_planejada", principal) == {}
    assert estado.mental == original
    publicado_legado = atualizar_planejamento_turno(lambda: _servicos(estado), "resposta_planejada")
    assert publicado_legado["fase"] == "resposta_planejada"


def test_conclusao_tecnica_suprimida_recusa_ocorrencia_trocada_apos_primeira_publicacao() -> None:
    texto = "cria a playlist foco"
    original = _frame(texto)
    estado = EstadoCompartilhadoRuntime(mental=original)
    composicao = ComposicaoTurnoRuntime(servicos=_servicos(estado))
    publicacoes = []
    escritas_legadas = []
    efeitos = []
    snapshot_novo = []

    def publicar_e_trocar(fase, principal, **kwargs):
        publicado = composicao.atualizar_proposta(fase, principal, **kwargs)
        publicacoes.append((fase, bool(publicado)))
        if fase == "resposta_planejada" and publicado:
            estado.substituir("mental", _nova_ocorrencia(original))
            snapshot_novo.append(estado.snapshot())
        return publicado

    def publicar_legado(fase, **kwargs):
        escritas_legadas.append(fase)
        return composicao.atualizar(fase, **kwargs)

    runtime = RespostaIARuntime(contexto_getter=lambda: {
        "obter_turno_atual": lambda: estado.obter_copia("mental", "turno_atual"),
        "usar_modo_rapido": lambda _texto: False,
        "preparacao_conversa": SimpleNamespace(preparar_pacote=lambda _texto: PacotePrompt(())),
        "modelo_llm": SimpleNamespace(executar=lambda _pedido: ResultadoModelo("", False)),
        "preparar_resposta": lambda _texto, bruto: {
            "fala": "", "comandos": [], "suprimir_fala": True,
        },
        "validar_comandos_planejados": criar_validador_comandos_turno_runtime(estado_runtime=estado),
        "atualizar_plano_turno": publicar_legado,
        "atualizar_plano_proposta": publicar_e_trocar,
        "contexto_dispatch_runtime": SimpleNamespace(montar=lambda: {}),
        "executar_comandos_json": lambda *_args: efeitos.append("dispatch") or {"erros": []},
        "contexto_finalizacao_runtime": SimpleNamespace(montar=lambda: {}),
        "finalizar_execucao": lambda *_args: efeitos.append("fala") or {},
    }, log=lambda *_args: None)

    runtime.processar(texto)

    assert publicacoes == [
        ("resposta_planejada", True), ("resposta_tecnica_suprimida", False),
    ], "a conclusão técnica ainda pertence à ocorrência capturada e precisa passar pelo writer vinculado"
    assert escritas_legadas == []
    assert efeitos == []
    assert estado.snapshot() == snapshot_novo[-1]


@pytest.mark.parametrize("ocorrencia", [None, {}, ContratoOcorrenciaTurno(True, "oi"),
                                       ContratoOcorrenciaTurno("", "oi"), ContratoOcorrenciaTurno(42, None)])
def test_conclusao_local_recusa_origem_ausente_ou_malformada(ocorrencia) -> None:
    estado = EstadoCompartilhadoRuntime(mental=_frame("oi"))
    antes = estado.snapshot()
    composicao = ComposicaoTurnoRuntime(servicos=_servicos(estado))
    assert composicao.atualizar_ocorrencia("tratado_prioritario", ocorrencia) == {}
    assert estado.snapshot() == antes


def test_conclusao_local_confere_origem_no_commit_e_nao_reconstroi_frame_vazio() -> None:
    texto = "cria a playlist foco"
    original = _frame(texto)
    estado = EstadoCompartilhadoRuntime(mental=original)
    atualizar = estado.atualizar
    snapshots_limpos = []

    def limpar_antes_do_lock(grupo, funcao):
        estado.substituir("mental", {})
        # A normalização canônica acrescenta a pendência vazia ao domínio.
        snapshots_limpos.append(estado.snapshot())
        return atualizar(grupo, funcao)

    estado.atualizar = limpar_antes_do_lock
    ocorrencia = ContratoOcorrenciaTurno(original["turno_atual"]["id"], texto)
    assert ocorrencia.autoriza_execucao is False
    assert not hasattr(ocorrencia, "resposta_bruta"), "ocorrência local não certifica emissão de modelo"
    assert ComposicaoTurnoRuntime(servicos=_servicos(estado)).atualizar_ocorrencia(
        "tratado_prioritario", ocorrencia,
    ) == {}
    assert estado.snapshot() == snapshots_limpos[-1]


def test_conclusao_local_preserva_revisao_intra_turno_e_receipts() -> None:
    texto = "Abre o Opera... não, abre a Calculadora."
    revisao = resolver_revisao_intra_turno(texto)
    efetivo = revisao["texto_operacional_efetivo"]
    frame = _frame(efetivo)
    frame["turno_atual"].update(texto=texto, texto_original=texto, texto_operacional_efetivo=efetivo)
    frame["plano_turno_atual"] = alinhar_identidade_plano_revisao(
        frame["plano_turno_atual"], texto_original=texto,
        texto_operacional_efetivo=efetivo, revisao_intra_turno=revisao,
    )
    receipt = {"id_solicitacao": "controle-sem-efeito", "intent": "APP_OPEN",
               "executou": True, "confirmado": True, "status": "sucesso"}
    frame["plano_turno_atual"] = atualizar_plano_turno(
        frame["plano_turno_atual"], fase="executado", comandos=[receipt],
    )
    receipts_antes = deepcopy(frame["plano_turno_atual"]["comandos"])
    estado = EstadoCompartilhadoRuntime(mental=frame)
    publicado = ComposicaoTurnoRuntime(servicos=_servicos(estado)).atualizar_ocorrencia(
        "tratado_prioritario", ContratoOcorrenciaTurno(frame["turno_atual"]["id"], texto),
    )
    assert publicado["texto_operacional_efetivo"] == efetivo
    assert publicado["comandos"] == receipts_antes


def test_conclusao_local_recusa_original_diferente_com_o_mesmo_id() -> None:
    texto = "cria a playlist foco"
    frame = _frame(texto)
    estado = EstadoCompartilhadoRuntime(mental=frame)
    antes = estado.snapshot()
    assert ComposicaoTurnoRuntime(servicos=_servicos(estado)).atualizar_ocorrencia(
        "tratado_prioritario", ContratoOcorrenciaTurno(frame["turno_atual"]["id"], "cria a playlist estudo"),
    ) == {}
    assert estado.snapshot() == antes


@pytest.mark.parametrize("rota", ("modo_chat", "prioritario", "pre_fluxo", "social_jogo"))
@pytest.mark.parametrize("troca", ("nenhuma", "vazio", "novo_turno"))
def test_todas_as_conclusoes_locais_usam_ocorrencia_capturada(rota, troca, monkeypatch) -> None:
    from mente_laylay.autonomia import resposta_ia_runtime as modulo

    texto = "oi"
    original = _frame(texto)
    estado = EstadoCompartilhadoRuntime(mental=original)
    composicao = ComposicaoTurnoRuntime(servicos=_servicos(estado))
    publicacoes, traces, snapshots = [], [], []

    def processar(*_args, **_kwargs):
        if troca != "nenhuma":
            estado.substituir("mental", {} if troca == "vazio" else _nova_ocorrencia(original))
        snapshots.append(estado.snapshot())
        return True

    def publicar(fase, ocorrencia):
        resultado = composicao.atualizar_ocorrencia(fase, ocorrencia)
        publicacoes.append((fase, resultado))
        return resultado

    # Estímulos de rota: o owner transacional real não é substituído.
    ctx = {
        "obter_turno_atual": lambda: estado.obter_copia("mental", "turno_atual"),
        "atualizar_plano_ocorrencia": publicar,
        "atualizar_plano_turno": lambda *_a, **_k: pytest.fail("conclusão moderna usou writer legado"),
        "atualizar_trace_diagnostico": lambda *_a, **k: traces.append(k),
        "modo_chat_runtime": SimpleNamespace(processar_texto=processar if rota == "modo_chat" else lambda *_: False),
        "processar_comandos_prioritarios": processar if rota == "prioritario" else lambda *_: False,
        "processar_inicio_fluxo": processar if rota == "pre_fluxo" else lambda *_: False,
        "modo_jogo_ativo": rota == "social_jogo",
        "usar_modo_rapido": lambda *_: True,
    }
    monkeypatch.setattr(modulo, "responder_conversa_social_curta", lambda *a, **k: (processar(), "social_jogo"))
    RespostaIARuntime(contexto_getter=lambda: ctx, log=lambda *_: None).processar(texto)
    assert len(publicacoes) == 1
    fase, plano = publicacoes[0]
    assert fase == "tratado_" + rota
    if troca == "nenhuma":
        assert plano["id"] == original["turno_atual"]["id"]
    else:
        assert plano == {}
        assert estado.snapshot() == snapshots[-1]
        assert any(t.get("fase") == "conclusao_local_obsoleta" for t in traces)


@pytest.mark.parametrize("retorno", (None, True, "feito", []))
def test_writer_local_malformado_nao_cai_no_legado_e_registra_falha(retorno) -> None:
    original = _frame("oi")
    estado = EstadoCompartilhadoRuntime(mental=original)
    antes = estado.snapshot()
    falhas = []
    runtime = RespostaIARuntime(contexto_getter=lambda: {
        "obter_turno_atual": lambda: estado.obter_copia("mental", "turno_atual"),
        "processar_comandos_prioritarios": lambda *_: True,
        "atualizar_plano_ocorrencia": lambda *_: retorno,
        "atualizar_plano_turno": lambda *_: pytest.fail("writer malformado caiu no legado"),
        "registrar_falha_diagnostico": lambda *a, **k: falhas.append((a, k)),
    }, log=lambda *_: None)
    assert runtime._processar_serializado("oi") is False
    assert estado.snapshot() == antes
    assert len(falhas) == 1 and isinstance(falhas[0][1]["erro"], TypeError)
