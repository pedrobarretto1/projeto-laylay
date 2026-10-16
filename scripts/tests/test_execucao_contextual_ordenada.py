"""Ordem da fonte e admissão explícita antes de cada efeito contextual."""
from copy import deepcopy
from types import SimpleNamespace
from dataclasses import replace
import time

import pytest

from mente_laylay.autonomia import coordenador_intencao
from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.autonomia.dispatcher_comandos_json import executar_comandos_json
from mente_laylay.cognicao.escopo_autorizacao import construir_autorizacoes_por_ato
from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA
from mente_laylay.memoria_mental.resultado_acao import identificar_solicitacao_execucao
from scripts.tests.test_materializacao_contextual import preparar


def cenario(monkeypatch, texto="abre o aplicativo Calculadora e coloca ela à esquerda e coloca o volume em 40",
            *, falhar_primeiro=False, falhar_segundo=False):
    validar, estado, proposta, _, _, _ = preparar(texto)
    mental = estado.snapshot()["mental"]
    autorizacoes = construir_autorizacoes_por_ato(mental["turno_atual"], mental, validar._resolver_ato)
    comandos = [identificar_solicitacao_execucao(a.pedido.como_dict(), nova_identidade=True) for a in autorizacoes]
    assert len(comandos) >= 1
    efeitos, receipts = [], []

    def registrar(receipt, *_args, **_kwargs):
        receipts.append(receipt)
        return True

    def executor(pedido, texto, ctx):
        efeitos.append(deepcopy(pedido))
        falha = (falhar_primeiro and len(efeitos) == 1) or (falhar_segundo and len(efeitos) == 2)
        status = {"APP_OPEN": "app_aberto", "ORGANIZAR_DESKTOP": "layout_confirmado", "VOLUME": "volume_ajustado",
                  "OPEN_URL": "url_aberta", "CLOSE_TAB": "aba_fechada",
                  "MAXIMIZE_WINDOW": "janela_maximizada", "CLOSE_APP": "app_fechado"}[pedido["intent"]]
        AdaptadorResultadoOperacional(pedido, pedido["params"], texto, "local", ctx).marcar_resultado(
            "falha_execucao" if falha else status, executou=not falha, confirmado=not falha)
        return not falha

    monkeypatch.setattr(coordenador_intencao, "executar_intencao", executor)
    ciclo = coordenador_intencao.CicloComandosRuntime(namespace_getter=dict,
        contexto_intencao_runtime=SimpleNamespace(montar=lambda: {
            **estado.snapshot()["mental"], "_registrar_resultado_execucao": registrar}))
    ctx = {"executar_intencao": ciclo.executar_intencao,
        "executar_intencao_observando": ciclo.executar_intencao_observando,
        "executar_ato_observando": ciclo.executar_ato_observando,
        "proposta_principal_vigente": lambda: estado.obter_copia("mental", "turno_atual")["id"] == mental["turno_atual"]["id"]}
    preparar_roteiro = getattr(validar, "preparar_execucao_por_atos", None)
    if callable(preparar_roteiro):
        ctx["roteiro_execucao_principal"] = preparar_roteiro(comandos, proposta)
        ctx["materializar_ato_contextual"] = lambda ato, obs: validar.materializar_ato_contextual(ato, proposta, obs)
        ctx["admitir_ato_contextual"] = lambda m, obs: validar.admitir_ato_contextual(m, proposta, obs)
        ctx["admissao_contextual_vigente"] = lambda a, m, obs: validar.admissao_contextual_vigente(a, m, proposta, obs)
        ctx["etapa_independente_vigente"] = lambda e: validar.etapa_independente_vigente(e, proposta)
    return validar, estado, proposta, comandos, ctx, efeitos, receipts


def test_continuacao_ocupa_sua_posicao_antes_do_ato_independente_seguinte(monkeypatch):
    _, _, proposta, comandos, ctx, efeitos, receipts = cenario(monkeypatch)
    resultado = executar_comandos_json(ctx, proposta.texto_usuario, comandos, "", "comando", False, False, False)
    assert efeitos[0]["intent"] == "APP_OPEN" and receipts[0].confirmado is True
    assert [c["intent"] for c in efeitos] == ["APP_OPEN", "ORGANIZAR_DESKTOP", "VOLUME"], "continuação se perdeu ou foi anexada depois do volume"
    assert efeitos[1]["params"]["left"] == "calculadora"
    assert len(receipts) == 3 and all(r.confirmado is True for r in receipts)
    assert not resultado["erros"]


def test_falha_do_antecedente_nao_libera_continuacao_mas_preserva_ordem_independente(monkeypatch):
    _, _, proposta, comandos, ctx, efeitos, receipts = cenario(monkeypatch, falhar_primeiro=True)
    resultado = executar_comandos_json(ctx, proposta.texto_usuario, comandos, "", "comando", False, False, False)
    assert [c["intent"] for c in efeitos] == ["APP_OPEN", "VOLUME"]
    assert receipts[0].confirmado is False and receipts[1].confirmado is True
    assert any("contextual" in erro for erro in resultado["erros"]), "falha da parte contextual não pode desaparecer"


def executar(c):
    _, _, proposta, comandos, ctx, efeitos, receipts = c
    resultado = executar_comandos_json(ctx, proposta.texto_usuario, comandos, "", "comando", False, False, False)
    return resultado, efeitos, receipts


def test_reordenacao_da_lista_da_llm_nao_reordena_a_fonte(monkeypatch):
    c = cenario(monkeypatch)
    validar, _, proposta, comandos, ctx, _, _ = c
    comandos.reverse()
    ctx["roteiro_execucao_principal"] = validar.preparar_execucao_por_atos(comandos, proposta)
    r, efeitos, _ = executar(c)
    assert [e["intent"] for e in efeitos] == ["APP_OPEN", "ORGANIZAR_DESKTOP", "VOLUME"]
    assert not r["erros"]


def test_turno_trocado_apos_primeiro_receipt_impede_restante(monkeypatch):
    c = cenario(monkeypatch)
    _, estado, _, _, _, _, _ = c
    original = coordenador_intencao.executar_intencao
    def trocar(*args):
        retorno = original(*args)
        turno = estado.obter_copia("mental", "turno_atual")
        turno["id"] = "novo-turno"
        estado.atualizar("mental", lambda atual: {**atual, "turno_atual": turno})
        return retorno
    monkeypatch.setattr(coordenador_intencao, "executar_intencao", trocar)
    r, efeitos, receipts = executar(c)
    assert len(efeitos) == len(receipts) == 1
    assert "não está vigente" in r["erros"][0]


def test_revogacao_apos_admissao_e_conferida_antes_do_segundo_efeito(monkeypatch):
    c = cenario(monkeypatch)
    _, estado, _, _, ctx, _, _ = c
    original = ctx["admitir_ato_contextual"]
    def revogar(m, obs):
        admissao = original(m, obs)
        turno = estado.obter_copia("mental", "turno_atual")
        turno["segmentos"][1]["autoriza_execucao"] = False
        estado.atualizar("mental", lambda atual: {**atual, "turno_atual": turno})
        return admissao
    ctx["admitir_ato_contextual"] = revogar
    r, efeitos, _ = executar(c)
    assert "ORGANIZAR_DESKTOP" not in [e["intent"] for e in efeitos]
    assert r["erros"]


@pytest.mark.parametrize("modo", ["bool", "dict", "alvo_trocado"])
def test_admissao_impostora_nao_e_permissao(monkeypatch, modo):
    c = cenario(monkeypatch)
    _, _, _, _, ctx, _, _ = c
    original = ctx["admitir_ato_contextual"]
    def impostor(m, obs):
        a = original(m, obs)
        if modo == "bool": return True
        if modo == "dict": return {"autoriza_execucao": True}
        pedido = a.pedido.como_dict()
        pedido["params"]["left"] = "Notepad"
        return replace(a, pedido=SnapshotComandoIA(pedido))
    ctx["admitir_ato_contextual"] = impostor
    r, efeitos, _ = executar(c)
    assert "ORGANIZAR_DESKTOP" not in [e["intent"] for e in efeitos]
    assert r["erros"]


def test_publicacao_expira_entre_materializacao_e_admissao(monkeypatch):
    c = cenario(monkeypatch)
    _, _, _, _, ctx, _, _ = c
    original = ctx["admitir_ato_contextual"]
    def expirar(m, obs):
        instante = time.monotonic() + 301.0
        monkeypatch.setattr(time, "monotonic", lambda: instante)
        return original(m, obs)
    ctx["admitir_ato_contextual"] = expirar
    r, efeitos, _ = executar(c)
    assert [e["intent"] for e in efeitos] == ["APP_OPEN", "VOLUME"]
    assert any("contextual não admitida" in e for e in r["erros"])


def test_nenhuma_porta_de_admissao_ausente_libera_efeito(monkeypatch):
    c = cenario(monkeypatch)
    c[4].pop("admissao_contextual_vigente")
    r, efeitos, receipts = executar(c)
    assert not efeitos and not receipts and r["erros"]


def test_bool_tratado_sem_receipt_nao_libera_continuacao(monkeypatch):
    c = cenario(monkeypatch)
    tentativas = []
    def sem_receipt(pedido, *_args):
        tentativas.append(pedido["intent"])
        return True
    monkeypatch.setattr(coordenador_intencao, "executar_intencao", sem_receipt)
    r, _, receipts = executar(c)
    assert tentativas == ["APP_OPEN", "VOLUME"] and not receipts
    assert any("contextual não admitida" in e for e in r["erros"])


def test_fonte_independente_omitida_nao_compila_roteiro_completo(monkeypatch):
    validar, _, proposta, comandos, _, _, _ = cenario(monkeypatch)
    assert validar.preparar_execucao_por_atos(comandos[:1], proposta) is None


def test_texto_de_etapa_alterado_nao_reutiliza_permissao_do_indice(monkeypatch):
    c = cenario(monkeypatch)
    roteiro = c[4]["roteiro_execucao_principal"]
    primeira = replace(roteiro.etapas[0], texto="apaga um arquivo")
    c[4]["roteiro_execucao_principal"] = replace(roteiro, etapas=(primeira, *roteiro.etapas[1:]))
    r, efeitos, _ = executar(c)
    assert not any(e["intent"] in {"APP_OPEN", "ORGANIZAR_DESKTOP"} for e in efeitos)
    assert r["erros"]


def test_mesmo_contrato_abre_site_e_fecha_referente_antes_do_volume(monkeypatch):
    c = cenario(monkeypatch, "abre o site github e fecha ele e coloca o volume em 40")
    r, efeitos, receipts = executar(c)
    assert [e["intent"] for e in efeitos] == ["OPEN_URL", "CLOSE_TAB", "VOLUME"]
    assert efeitos[1]["params"]["alvo"] == "github"
    assert len({r.id_solicitacao for r in receipts}) == 3
    assert not r["erros"]


def test_tres_continuacoes_seguidas_preservam_linhagem_e_receipts_distintos(monkeypatch):
    texto = "abre o aplicativo Calculadora e coloca ela à esquerda e coloca ela à direita e maximiza ela"
    r, efeitos, receipts = executar(cenario(monkeypatch, texto))
    assert len(efeitos) == len(receipts) == 4 and not r["erros"]
    assert [m.indice_antecedente for m in r["atos_materializados"]] == [0, 1, 2]
    assert len({o.pedido.como_dict()["id_solicitacao"] for o in r["execucoes_observadas"]}) == 4
    assert efeitos[1]["params"]["left"] == "calculadora"
    assert efeitos[2]["params"]["right"] == "calculadora"
    assert efeitos[3]["params"]["nome_app"] == "calculadora"


def test_repetir_operacao_depois_de_efeito_intermediario_exige_nova_invocacao(monkeypatch):
    texto = "abre o aplicativo Calculadora e coloca ela à esquerda e coloca ela à direita e coloca ela à esquerda"
    r, efeitos, receipts = executar(cenario(monkeypatch, texto))
    assert len(efeitos) == len(receipts) == 4 and not r["erros"]
    assert len({p.id_solicitacao for p in receipts}) == 4


def test_cache_sem_receipt_novo_nao_confirma_conclusao_composta_completa(monkeypatch):
    texto = "abre o aplicativo Calculadora e coloca ela à esquerda e coloca ela à direita e coloca ela à esquerda"
    c = cenario(monkeypatch, texto)
    # Compatibilidade sem a porta de ato conserva a deduplicação antiga;
    # esse cache continua proibido como prova de uma publicação nova.
    c[4].pop("executar_ato_observando")
    r, _, _ = executar(c)
    assert not r["execucoes_observadas"][-1].publicacoes
    assert any("sem publicação desta invocação" in erro for erro in r["erros"])


def test_cache_de_site_tambem_nao_empresta_receipt_para_continuacao(monkeypatch):
    c = cenario(monkeypatch, "abre o site github e abre ele de novo e fecha ele")
    c[4].pop("executar_ato_observando")
    r, efeitos, receipts = executar(c)
    assert [e["intent"] for e in efeitos] == ["OPEN_URL"]
    assert len(receipts) == 1 and receipts[0].confirmado is True
    assert not r["execucoes_observadas"][-1].publicacoes
    assert any("etapa 2 sem publicação desta invocação" in erro for erro in r["erros"])
    assert any("contextual não admitida: 3" in erro for erro in r["erros"])


def test_ato_novo_de_site_executa_novamente_antes_de_fechar_referente(monkeypatch):
    r, efeitos, receipts = executar(cenario(monkeypatch, "abre o site github e abre ele de novo e fecha ele"))
    assert [e["intent"] for e in efeitos] == ["OPEN_URL", "OPEN_URL", "CLOSE_TAB"]
    assert len(receipts) == len({p.id_solicitacao for p in receipts}) == 3
    assert not r["erros"]


def test_atos_diretos_repetidos_tambem_nao_sao_retries(monkeypatch):
    r, efeitos, receipts = executar(cenario(monkeypatch,
        "abre o aplicativo Calculadora e coloca ela à esquerda e coloca o volume em 40 e coloca o volume em 30 e coloca o volume em 40"))
    assert [e["params"]["nivel_volume"] for e in efeitos if e["intent"] == "VOLUME"] == [40, 30, 40]
    assert len({p.id_solicitacao for p in receipts}) == 5 and not r["erros"]


def test_continuacao_falha_nao_ressuscita_abertura_antiga_mas_volume_independente_continua(monkeypatch):
    texto = "abre o aplicativo Calculadora e coloca ela à esquerda e coloca ela à direita e coloca o volume em 40"
    r, efeitos, receipts = executar(cenario(monkeypatch, texto, falhar_segundo=True))
    assert [e["intent"] for e in efeitos] == ["APP_OPEN", "ORGANIZAR_DESKTOP", "VOLUME"]
    assert [p.confirmado for p in receipts] == [True, False, True]
    assert any("etapa contextual não admitida: 3" in erro for erro in r["erros"])


@pytest.mark.parametrize("modo", ["raw_sem_vinculo", "dict", "receipt_vencido", "receipt_incerto", "duplicado", "prefixo_reordenado"])
def test_vinculo_nao_pode_ser_substituido_por_historico_shape_ou_publicacao_invalida(monkeypatch, modo):
    c = cenario(monkeypatch, "abre o aplicativo Calculadora e coloca ela à esquerda e coloca ela à direita")
    validar, estado, proposta, _, _, _, _ = c
    r, _, _ = executar(c)
    ato = validar.validar_proposta([], proposta)["atos_aguardando_materializacao"][-1]
    prefixo = r["execucoes_por_ato"][:2]
    assert validar.materializar_ato_contextual(ato, proposta, prefixo).indice_antecedente == 1
    primeiro, vinculo = prefixo
    if modo == "raw_sem_vinculo": prefixo = (primeiro, vinculo.observacao)
    elif modo == "dict": prefixo = (primeiro, {"admissao": vinculo.admissao, "observacao": vinculo.observacao})
    elif modo == "receipt_vencido":
        prefixo = (primeiro, replace(vinculo, observacao=replace(vinculo.observacao,
            instantes_publicacao=(time.monotonic() - 301.0,))))
    elif modo == "receipt_incerto":
        receipt = vinculo.observacao.publicacoes[-1].como_dict()
        receipt["confirmado"] = None
        prefixo = (primeiro, replace(vinculo, observacao=replace(vinculo.observacao,
            publicacoes=(SnapshotComandoIA(receipt),))))
    elif modo == "duplicado": prefixo = (*prefixo, vinculo)
    else: prefixo = tuple(reversed(prefixo))
    antes = estado.snapshot()
    assert validar.materializar_ato_contextual(ato, proposta, prefixo) is None
    assert estado.snapshot() == antes


def test_revogar_ato_intermediario_invalida_linhagem_sem_apagar_receipt(monkeypatch):
    c = cenario(monkeypatch, "abre o aplicativo Calculadora e coloca ela à esquerda e coloca ela à direita")
    validar, estado, proposta, _, _, _, _ = c
    r, _, _ = executar(c)
    ato = validar.validar_proposta([], proposta)["atos_aguardando_materializacao"][-1]
    turno = estado.obter_copia("mental", "turno_atual")
    turno["segmentos"][1]["autoriza_execucao"] = False
    estado.atualizar("mental", lambda atual: {**atual, "turno_atual": turno})
    assert validar.materializar_ato_contextual(ato, proposta, r["execucoes_por_ato"][:2]) is None
    assert r["execucoes_observadas"][1].publicacoes[-1].como_dict()["confirmado"] is True


@pytest.mark.parametrize("campo", ["indice", "texto", "id_solicitacao", "alvo", "turno"])
def test_contrato_de_vinculo_recusa_fonte_ou_invocacao_alterada(monkeypatch, campo):
    c = cenario(monkeypatch, "abre o aplicativo Calculadora e coloca ela à esquerda e coloca ela à direita")
    r, _, _ = executar(c)
    vinculo = r["execucoes_por_ato"][1]
    a = vinculo.admissao
    assert vinculo.autoriza_execucao is False
    if campo == "indice": a = replace(a, indice=0)
    elif campo == "texto": a = replace(a, texto="apaga esse arquivo")
    elif campo == "turno": a = replace(a, turno_id="outro-turno")
    else:
        pedido = a.pedido.como_dict()
        if campo == "id_solicitacao": pedido["id_solicitacao"] = "outra-invocacao"
        else: pedido["params"]["left"] = "Notepad"
        a = replace(a, pedido=SnapshotComandoIA(pedido))
    with pytest.raises(ValueError, match="fonte/admissão/invocação"):
        replace(vinculo, admissao=a)


def test_outro_antecedente_independente_nao_desaparece_por_existir_linhagem(monkeypatch):
    texto = "abre o aplicativo Calculadora e coloca ela à esquerda e abre o aplicativo Notepad e coloca ela à direita"
    r, efeitos, _ = executar(cenario(monkeypatch, texto))
    assert [e["intent"] for e in efeitos] == ["APP_OPEN", "ORGANIZAR_DESKTOP", "APP_OPEN"]
    assert any("contextual não admitida: 4" in erro for erro in r["erros"])


def test_alias_de_id_nao_permite_vincular_admissao_a_outra_invocacao(monkeypatch):
    r, _, _ = executar(cenario(monkeypatch,
        "abre o aplicativo Calculadora e coloca ela à esquerda e coloca ela à direita"))
    vinculo = r["execucoes_por_ato"][1]
    pedido_admitido = vinculo.admissao.pedido.como_dict()
    pedido_admitido.pop("id_solicitacao")
    pedido_admitido["request_id"] = "alias-admissao"
    pedido_executado = vinculo.observacao.pedido.como_dict()
    pedido_executado.pop("id_solicitacao")
    pedido_executado["request_id"] = "alias-outra-invocacao"
    receipt = vinculo.observacao.publicacoes[-1].como_dict()
    receipt["id_solicitacao"] = "alias-outra-invocacao"
    admissao = replace(vinculo.admissao, pedido=SnapshotComandoIA(pedido_admitido))
    observacao = replace(vinculo.observacao, pedido=SnapshotComandoIA(pedido_executado),
        publicacoes=(SnapshotComandoIA(receipt),))
    with pytest.raises(ValueError, match="fonte/admissão/invocação"):
        replace(vinculo, admissao=admissao, observacao=observacao)


def test_falha_da_continuacao_nao_e_sucesso_composto(monkeypatch):
    r, efeitos, receipts = executar(cenario(monkeypatch, falhar_segundo=True))
    assert [e["intent"] for e in efeitos] == ["APP_OPEN", "ORGANIZAR_DESKTOP", "VOLUME"]
    assert [r.confirmado for r in receipts] == [True, False, True]
    assert any("ORGANIZAR_DESKTOP" in e for e in r["erros"])


def test_roteiro_independente_tambem_usa_ordem_da_fonte(monkeypatch):
    validar, estado, _, _, _, _, _ = cenario(monkeypatch)
    from scripts.tests.test_decisao_unica_turno import _contratos_reais_do_filtro
    from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
    texto = "coloca o volume em 40 e abre o aplicativo Calculadora"
    turno, plano, retrato = _contratos_reais_do_filtro(texto)
    estado.atualizar("mental", lambda atual: {**atual, "turno_atual": turno,
        "plano_turno_atual": plano, "retrato_turno_atual": retrato})
    proposta = ContratoPropostaPrincipal(turno_id=turno["id"], texto_usuario=texto, resposta_bruta='{"fala":"teste"}')
    mental = estado.snapshot()["mental"]
    autorizacoes = construir_autorizacoes_por_ato(turno, mental, validar._resolver_ato)
    comandos = [identificar_solicitacao_execucao(a.pedido.como_dict()) for a in reversed(autorizacoes)]
    roteiro = validar.preparar_execucao_por_atos(comandos, proposta)
    assert [e.indice for e in roteiro.etapas] == [0, 1]
    assert [e.pedido.como_dict()["intent"] for e in roteiro.etapas] == ["VOLUME", "APP_OPEN"]


@pytest.mark.parametrize("texto", [
    "abre o aplicativo Calculadora e coloca ela à esquerda e coloca ela à direita",
    "abre o aplicativo Notepad e coloca ele à direita e coloca ele à esquerda",
])
def test_ato_contextual_executado_pode_fundamentar_outro_sem_emprestar_ultima_acao(monkeypatch, texto):
    c = cenario(monkeypatch, texto)
    validar, estado, proposta, _, _, _, _ = c
    pendentes = validar.validar_proposta([], proposta)["atos_aguardando_materializacao"]
    assert [a.indice for a in pendentes] == [1, 2], "classificação deve alcançar duas obrigações"
    r, efeitos, receipts = executar(c)
    assert [e["intent"] for e in efeitos[:2]] == ["APP_OPEN", "ORGANIZAR_DESKTOP"]
    assert len(receipts) >= 2 and receipts[0].confirmado is True and receipts[1].confirmado is True
    # Contraprova: o mesmo resolver já materializa o terceiro ato com o
    # primeiro receipt. O RED seguinte não é ausência de gramática/alvo.
    assert validar.materializar_ato_contextual(pendentes[1], proposta, r["execucoes_observadas"][:1]) is not None
    assert len(efeitos) == 3, "vínculo do ato contextual executado foi perdido antes da terceira admissão"
    app = efeitos[0]["params"]["nome_app"]
    lado_final = "right" if "direita" in texto.rsplit(" e ", 1)[1] else "left"
    assert efeitos[2]["params"][lado_final] == app, "descrição do receipt não é identidade do aplicativo"
    assert len({r.id_solicitacao for r in receipts}) == 3
    assert [m.indice_antecedente for m in r["atos_materializados"]] == [0, 1]
    assert not r["erros"]
