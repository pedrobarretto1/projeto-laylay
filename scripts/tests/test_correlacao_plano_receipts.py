from __future__ import annotations

import time

import pytest

from mente_laylay.cognicao.decisao_turno import filtrar_comandos_pelo_turno
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.orquestrador_turno_runtime import (
    alinhar_identidade_plano_revisao,
    atualizar_planejamento_turno,
    verificar_fala_do_turno,
)
from mente_laylay.cognicao.plano_turno import (
    atualizar_plano_turno,
    planejar_turno,
    verificar_fala_turno,
)
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.trilha_turno import registrar_etapa_turno


def _frame(texto: str = "cria a playlist foco", *, revisada: bool = False) -> dict:
    revisao = resolver_revisao_intra_turno(texto) if revisada else {}
    efetivo = revisao.get("texto_operacional_efetivo") or texto
    turno = classificar_modalidade_turno(efetivo)
    retrato, _entidades = construir_retrato_turno(
        efetivo, turno=turno, mente={}, contexto_perceptivo={},
    )
    turno["retrato_id"] = retrato["id"]
    plano = planejar_turno(efetivo, turno=turno, mente={})
    if revisada:
        turno.update(texto=texto, texto_original=texto, texto_operacional_efetivo=efetivo)
        plano = alinhar_identidade_plano_revisao(
            plano, texto_original=texto, texto_operacional_efetivo=efetivo,
            revisao_intra_turno=revisao,
        )
    receipt = {
        "id_solicitacao": "ocorrencia-confirmada", "intent": "PLAYLIST_CREATE",
        "alvo": "foco", "status": "sucesso", "executou": True, "confirmado": True,
        "confirmacao_oferecida": "persistencia_local", "evidencia_confirmacao": "receipt local",
    }
    plano = atualizar_plano_turno(plano, fase="executado", comandos=[receipt])
    return {
        "turno_atual": turno, "plano_turno_atual": plano, "retrato_turno_atual": retrato,
        "trilha_decisoes_turno": registrar_etapa_turno([], plano, fase="executado"),
    }


def _namespace(estado: EstadoCompartilhadoRuntime) -> dict:
    return {
        "_estado_compartilhado_runtime": estado,
        "_atualizar_plano_turno_mente": atualizar_plano_turno,
        "_registrar_etapa_turno_mente": registrar_etapa_turno,
        "_verificar_fala_turno_mente": verificar_fala_turno,
        "_contexto_horario_atual": lambda: "tarde",
        "time": time, "print": lambda *_args: None,
    }


_DIVERGENCIAS = [
    "plano_estrangeiro", "turno_sem_id", "plano_sem_id", "decisao_sem_id",
    "retrato_sem_id", "turno_sem_retrato_id", "plano_sem_retrato_id", "retrato_ausente",
    "turno_sem_texto", "plano_sem_texto", "retrato_sem_texto",
    "turno_texto_divergente", "plano_texto_divergente", "retrato_texto_divergente",
    "ids_booleanos", "ids_fracionarios", "ids_mappings", "ids_listas",
    "textos_booleanos", "textos_numericos", "textos_mappings", "textos_listas",
    "decisao_malformada", "retrato_malformado",
]


def _divergir(mental: dict, divergencia: str) -> None:
    turno = mental["turno_atual"]
    plano = mental["plano_turno_atual"]
    retrato = mental["retrato_turno_atual"]
    if divergencia == "plano_estrangeiro":
        plano["id"] += 1
        plano["retrato_id"] += 1
        plano["decisao_turno"]["turno_id"] += 1
    elif divergencia == "retrato_ausente":
        mental.pop("retrato_turno_atual")
    elif divergencia.startswith("ids_"):
        valor = {
            "ids_booleanos": True, "ids_fracionarios": 1.5,
            "ids_mappings": {"id": "mesmo"}, "ids_listas": ["mesmo"],
        }[divergencia]
        turno.update(id=valor, retrato_id=valor)
        plano.update(id=valor, retrato_id=valor)
        plano["decisao_turno"]["turno_id"] = valor
        retrato["id"] = valor
    elif divergencia.startswith("textos_"):
        valor = {
            "textos_booleanos": True, "textos_numericos": 42,
            "textos_mappings": {"texto": "mesmo"}, "textos_listas": ["mesmo"],
        }[divergencia]
        turno["texto"] = plano["texto_usuario"] = retrato["texto"] = valor
    elif divergencia == "decisao_malformada":
        plano["decisao_turno"] = ["invalida"]
    elif divergencia == "retrato_malformado":
        mental["retrato_turno_atual"] = ["invalido"]
    else:
        contratos = {"turno": turno, "plano": plano, "decisao": plano["decisao_turno"], "retrato": retrato}
        dono, operacao, campo = divergencia.split("_", 2)
        campo = {"plano": {"texto": "texto_usuario"}, "decisao": {"id": "turno_id"}}.get(dono, {}).get(campo, campo)
        if operacao == "sem":
            contratos[dono].pop(campo)
        else:
            # As variantes terminam em texto_divergente, sem alterar outros campos.
            contratos[dono]["texto_usuario" if dono == "plano" else "texto"] = "apaga o arquivo foco"


@pytest.mark.parametrize("divergencia", _DIVERGENCIAS)
def test_writer_recusa_frame_incoerente_sem_republicar_receipts(divergencia: str) -> None:
    mental = _frame()
    _divergir(mental, divergencia)
    estado = EstadoCompartilhadoRuntime(mental=mental)
    antes = estado.snapshot()

    publicado = atualizar_planejamento_turno(
        lambda: _namespace(estado), "resposta_planejada", comandos=[], fala="Criei a playlist foco.",
    )

    assert publicado == {}, "a primeira fronteira não deve publicar um plano incoerente"
    assert estado.snapshot() == antes, "receipt, fase e trilha devem permanecer preservados"


@pytest.mark.parametrize("divergencia", _DIVERGENCIAS)
def test_reader_nao_consume_receipt_incoerente_e_entrega_conclusao_observavel(divergencia: str) -> None:
    mental = _frame()
    _divergir(mental, divergencia)
    estado = EstadoCompartilhadoRuntime(mental=mental)
    ns = _namespace(estado)
    verificacoes = []

    def verificar(fala: str, **argumentos) -> dict:
        verificacoes.append(argumentos["plano"])
        return verificar_fala_turno(fala, **argumentos)

    ns["_verificar_fala_turno_mente"] = verificar
    antes = estado.snapshot()
    resultado = verificar_fala_do_turno(lambda: ns, "Criei a playlist foco.", origem="ia_final")

    assert verificacoes == [], "não enviar evidência de outro frame ao verificador de alegações"
    assert resultado["aceita"] is True
    assert resultado["fala"] and "não" in resultado["fala"].casefold()
    assert resultado["fala"] != "Criei a playlist foco."
    assert resultado["problemas"]
    assert estado.snapshot() == antes


@pytest.mark.parametrize("valor", [True, False, 1.5, {"id": "mesmo"}, ["mesmo"]])
def test_filtro_compartilha_recusa_de_ids_malformados_mesmo_quando_iguais(valor) -> None:
    mental = _frame()
    turno, plano, retrato = (mental[chave] for chave in ("turno_atual", "plano_turno_atual", "retrato_turno_atual"))
    turno.update(id=valor, retrato_id=valor)
    plano.update(id=valor, retrato_id=valor)
    plano["decisao_turno"]["turno_id"] = valor
    retrato["id"] = valor

    resultado = filtrar_comandos_pelo_turno(
        [{"intent": "PLAYLIST_CREATE"}], turno=turno, plano=plano, retrato=retrato,
    )

    assert resultado["autoriza_execucao"] is False
    assert resultado["comandos"] == []


@pytest.mark.parametrize("comandos", [None, []])
def test_writer_preserva_receipt_valido_por_omissao_ou_lista_vazia(comandos) -> None:
    estado = EstadoCompartilhadoRuntime(mental=_frame())
    ns = _namespace(estado)
    receipt = estado.obter_copia("mental", "plano_turno_atual")["comandos"]

    publicado = atualizar_planejamento_turno(
        lambda: ns, "resposta_planejada", comandos=comandos, fala="Criei a playlist foco.",
    )

    assert publicado["comandos"] == receipt
    assert estado.mental["plano_turno_atual"]["fase"] == "resposta_planejada"
    assert estado.mental["trilha_decisoes_turno"][-1]["turno_id"] == publicado["id"]
    assert verificar_fala_do_turno(lambda: ns, "Criei a playlist foco.", origem="ia_final")["fala"] == "Criei a playlist foco."


@pytest.mark.parametrize("texto", [
    "Abre o Opera... não, abre a Calculadora.",
    "Liga a lâmpada... não, deixa desligada.",
])
def test_writer_e_reader_preservam_revisao_legitima_do_mesmo_turno(texto: str) -> None:
    estado = EstadoCompartilhadoRuntime(mental=_frame(texto, revisada=True))
    ns = _namespace(estado)

    publicado = atualizar_planejamento_turno(lambda: ns, "resposta_planejada")
    resultado = verificar_fala_do_turno(lambda: ns, "Entendi seu pedido.")

    assert publicado["id"] == estado.mental["turno_atual"]["id"]
    assert publicado["texto_usuario"] == texto
    assert publicado["texto_operacional_efetivo"] != texto
    assert "contratos_turno_incoerentes" not in resultado["problemas"]


def test_writer_e_reader_preservam_contrato_legado_sem_retrato() -> None:
    plano = atualizar_plano_turno({}, fase="executado", comandos=[{
        "intent": "NOTIFICATIONS", "status": "notificacoes_lidas", "executou": True,
        "confirmado": True, "evidencia_confirmacao": "triagem persistida",
    }])
    estado = EstadoCompartilhadoRuntime(mental={"plano_turno_atual": plano})
    ns = _namespace(estado)

    publicado = atualizar_planejamento_turno(lambda: ns, "tratado_prioritario")
    resultado = verificar_fala_do_turno(lambda: ns, "Tenho dois avisos importantes.")

    assert publicado["comandos"] == plano["comandos"]
    assert resultado["fala"] == "Tenho dois avisos importantes."


def test_reader_nao_sobrescreve_novo_turno_publicado_durante_verificacao() -> None:
    estado = EstadoCompartilhadoRuntime(mental=_frame())
    ns = _namespace(estado)
    proximo = _frame("liga a lâmpada do quarto")
    novo_snapshot = {}

    def verificar_e_trocar_turno(fala: str, **argumentos) -> dict:
        resultado = verificar_fala_turno(fala, **argumentos)
        estado.atualizar_campos("mental", **proximo)
        novo_snapshot.update(estado.snapshot())
        return resultado

    ns["_verificar_fala_turno_mente"] = verificar_e_trocar_turno
    resultado = verificar_fala_do_turno(lambda: ns, "Criei a playlist foco.", origem="ia_final")

    assert estado.mental["plano_turno_atual"]["id"] == proximo["plano_turno_atual"]["id"]
    assert estado.snapshot() == novo_snapshot
    assert resultado["fala"] != "Criei a playlist foco."
    assert resultado["fala"] and "não" in resultado["fala"].casefold()
