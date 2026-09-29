"""Owner externo e snapshot completo; não é interpretação automática de texto."""

from dataclasses import replace

import pytest

from mente_laylay.cognicao.contrato_inventario_contextual import ReferenteContextual
from scripts.analises.grafo_premissas_didaticas import (
    FonteDidatica, ReferenteAncorado, PremissaDidatica, CondicaoDidatica, RegraDidatica,
    conferir_qualificacao_na_conversa,
)
from scripts.analises.contrato_vigencia_criterios import (
    RegistroVigenciaCriterios, conferir_qualificacao_com_vigencia, retratar_vigencia,
)


def _cenario(alvo="duto"):
    leitura = f"A pressão do {alvo} foi 9 bar."
    condicao = f"a pressão do {alvo} ficar acima de 8 bar"
    regra = f"Se {condicao}, o {alvo} é crítico."
    fontes = (FonteDidatica("leitura", "usuario", "sessao", leitura),
              FonteDidatica("criterio", "usuario", "sessao", regra))
    referentes = (ReferenteAncorado(ReferenteContextual(
        alvo, "equipamento", f"pressão do {alvo}", "usuario", "sessao",
    ), "leitura", alvo),)
    premissas = (PremissaDidatica("medida", alvo, f"pressão do {alvo}", "9",
                                 "bar", "leitura", leitura),)
    regras = (RegraDidatica("regra", (CondicaoDidatica(
        alvo, f"pressão do {alvo}", ">", "8", "bar", "criterio", condicao,
    ),), alvo, "estado", "crítico", "criterio", regra, "unico", "condicoes_suficientes"),)
    kwargs = dict(escopo="sessao", regra_id="regra", texto_atual=regra,
                  mensagens=[{"role": "user", "content": leitura}])
    return (fontes, referentes, premissas, regras), kwargs


def _conferir(grafo, kwargs, registro):
    return conferir_qualificacao_com_vigencia(
        *grafo, **kwargs, registro=registro, premissa_id="medida", rotulo="crítico",
    )


@pytest.mark.parametrize("estado,esperado", [
    (None, "vigencia_fonte_pendente"), ("revogado", "criterio_revogado"),
    ("indeterminado", "vigencia_fonte_pendente"),
    ("vigente", "condicao_numerica_satisfeita_relacao_pendente"),
])
def test_revisao_eh_externa_e_nunca_autoriza_composicao(estado, esperado):
    grafo, kwargs = _cenario()
    registro = RegistroVigenciaCriterios()
    if estado:
        registro.registrar_revisao(retratar_vigencia(*grafo, **kwargs), estado=estado)
    resultado = _conferir(grafo, kwargs, registro)
    assert resultado["estado"] == esperado
    assert resultado["comparacao_numerica"] is (estado == "vigente")
    assert resultado["aprovado_para_compor"] is False
    assert resultado["autoriza_efeito"] is False


@pytest.mark.parametrize("nova_fala", [
    "A regra anterior foi revogada.",
    "A regra anterior foi revogada?",
    "A regra anterior não foi revogada.",
    "A regra do compressor foi revogada, não a do duto.",
    "Ela disse: a regra foi revogada.",
    "Não use mais essa regra.",
])
def test_texto_novo_invalida_retrato_sem_inventar_decisao_de_revogacao(nova_fala):
    grafo, kwargs = _cenario()
    registro = RegistroVigenciaCriterios()
    registro.registrar_revisao(retratar_vigencia(*grafo, **kwargs), estado="vigente")
    kwargs = {**kwargs, "mensagens": [*kwargs["mensagens"],
                                    {"role": "user", "content": kwargs["texto_atual"]}],
              "texto_atual": nova_fala}
    resultado = _conferir(grafo, kwargs, registro)
    assert resultado["estado"] == "vigencia_fonte_pendente"
    assert resultado["vigencia"] == "sem_revisao"
    assert resultado["comparacao_numerica"] is False
    # Um revisor confiável pode concluir que era outra regra; não há veto
    # eterno por palavra. Isto não simula compreensão automática de linguagem.
    registro.registrar_revisao(retratar_vigencia(*grafo, **kwargs), estado="vigente")
    assert _conferir(grafo, kwargs, registro)["comparacao_numerica"] is True


def test_revisoes_conflitantes_nao_elegem_ultima_nem_repeticao():
    grafo, kwargs = _cenario()
    retrato = retratar_vigencia(*grafo, **kwargs)
    registro = RegistroVigenciaCriterios()
    for estado in ("revogado", "vigente", "vigente"):
        registro.registrar_revisao(retrato, estado=estado)
    assert _conferir(grafo, kwargs, registro)["vigencia"] == "revisoes_conflitantes"


def test_mesmo_id_em_outro_alvo_nao_reusa_revisao():
    registro = RegistroVigenciaCriterios()
    grafo, kwargs = _cenario()
    registro.registrar_revisao(retratar_vigencia(*grafo, **kwargs), estado="vigente")
    outro, contexto = _cenario("compressor")
    assert _conferir(outro, contexto, registro)["vigencia"] == "sem_revisao"


def test_registro_ou_json_de_outro_owner_nao_eh_autoridade():
    grafo, kwargs = _cenario()
    registro = RegistroVigenciaCriterios()
    registro.registrar_revisao(retratar_vigencia(*grafo, **kwargs), estado="vigente")
    assert _conferir(grafo, kwargs, RegistroVigenciaCriterios())["vigencia"] == "sem_revisao"
    assert _conferir(grafo, kwargs, {"vigente": True})["estado"] == "registro_vigencia_invalido"
    with pytest.raises(ValueError):
        registro.registrar_revisao({"chave": "inventada"}, estado="vigente")


def test_selo_preserva_ordem_repeticao_e_texto_depois_de_500_caracteres():
    grafo, kwargs = _cenario()
    a = {**kwargs, "mensagens": [*kwargs["mensagens"],
         {"role": "user", "content": "x" * 501 + " a regra permanece"}]}
    b = {**kwargs, "mensagens": [*kwargs["mensagens"],
         {"role": "user", "content": "x" * 501 + " a regra foi revogada"}]}
    assert retratar_vigencia(*grafo, **a) != retratar_vigencia(*grafo, **b)
    repetido = {**a, "mensagens": [*a["mensagens"], a["mensagens"][0]]}
    invertido = {**a, "mensagens": list(reversed(a["mensagens"]))}
    assert retratar_vigencia(*grafo, **a) != retratar_vigencia(*grafo, **repetido)
    assert retratar_vigencia(*grafo, **a) != retratar_vigencia(*grafo, **invertido)


def test_revisao_nao_substitui_guarda_de_direcao_numerica():
    grafo, kwargs = _cenario()
    fontes, referentes, premissas, regras = grafo
    errada = replace(regras[0], condicoes=(replace(regras[0].condicoes[0], operador="<"),))
    grafo = fontes, referentes, premissas, (errada,)
    registro = RegistroVigenciaCriterios()
    registro.registrar_revisao(retratar_vigencia(*grafo, **kwargs), estado="vigente")
    resultado = _conferir(grafo, kwargs, registro)
    assert resultado["comparacao_numerica"] is False
    assert resultado["estado"] == "direcao_literal_pendente"


def test_fonte_autodeclarada_nao_eh_validada_por_revisao():
    grafo, kwargs = _cenario()
    kwargs["texto_atual"] = "Outro assunto"
    with pytest.raises(ValueError, match="observação integral"):
        retratar_vigencia(*grafo, **kwargs)
    resultado = _conferir(grafo, kwargs, RegistroVigenciaCriterios())
    assert resultado["estado"] == "retrato_vigencia_invalido"


@pytest.mark.parametrize("alvo", ["duto", "compressor"])
def test_contexto_real_nao_pode_ser_omitido_da_lista_proposta_de_fontes(alvo):
    grafo, kwargs = _cenario(alvo)
    # A proposta contém só leitura/regra. A fala real posterior continua
    # sendo autoridade para exigir revisão, mesmo omitida pelo proponente.
    kwargs["mensagens"].append({"role": "user", "content": kwargs["texto_atual"]})
    kwargs["texto_atual"] = f"Não use mais essa regra sobre o {alvo}."
    resultado = conferir_qualificacao_na_conversa(
        *grafo, **kwargs, premissa_id="medida", rotulo="crítico",
    )
    assert resultado["estado"] == "contexto_criterio_pendente"
    assert resultado["comparacao_numerica"] is False


def test_repetir_regra_nao_apaga_revogacao_intermediaria():
    grafo, kwargs = _cenario()
    kwargs["mensagens"].extend([
        {"role": "user", "content": kwargs["texto_atual"]},
        {"role": "user", "content": "A regra foi revogada."},
    ])
    resultado = conferir_qualificacao_na_conversa(
        *grafo, **kwargs, premissa_id="medida", rotulo="crítico",
    )
    assert resultado["estado"] == "contexto_criterio_pendente"


def test_texto_da_assistente_nao_revoga_fonte_do_usuario():
    grafo, kwargs = _cenario()
    kwargs["mensagens"].extend([
        {"role": "user", "content": kwargs["texto_atual"]},
        {"role": "assistant", "content": "Essa regra foi revogada."},
    ])
    resultado = conferir_qualificacao_na_conversa(
        *grafo, **kwargs, premissa_id="medida", rotulo="crítico",
    )
    assert resultado["comparacao_numerica"] is True
    assert resultado["aprovado_para_compor"] is False


def test_ordem_proposta_das_fontes_nao_muda_cronologia_real():
    grafo, kwargs = _cenario()
    kwargs["mensagens"].append({"role": "user", "content": kwargs["texto_atual"]})
    kwargs["texto_atual"] = "A regra foi revogada."
    fontes, *resto = grafo
    resultado = conferir_qualificacao_na_conversa(
        tuple(reversed(fontes)), *resto, **kwargs, premissa_id="medida", rotulo="crítico",
    )
    assert resultado["estado"] == "contexto_criterio_pendente"
