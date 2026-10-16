"""Destino absoluto e magnitude relativa não são o mesmo parâmetro."""
import pytest

from mente_laylay.autonomia.roteador_deterministico import detectar_volume_ou_midia
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.iot.runtime import RuntimeIoT
from scripts.tests.test_iot_lampada import MemoriaIoTFalsa
from mente_laylay.cognicao.gramatica_operacional import interpretar_relacao_valor_ajuste
from mente_laylay.autonomia.orquestrador_deterministico import detectar_intencao_deterministica_mente


@pytest.mark.parametrize("texto,acao,delta", [
    ("aumenta o volume em 10", "up", 10),
    ("abaixa o volume em 10.", "down", 10),
    ("aumente o som em 5", "up", 5),
    ("reduza o volume em 25", "down", 25),
])
def test_valor_relativo_nao_se_transforma_em_nivel_final(texto, acao, delta):
    candidato = detectar_volume_ou_midia(normalizar_texto(texto), params_cb=lambda **p: p)
    assert candidato and candidato["intent"] == "VOLUME"
    assert candidato["params"] == {"acao": acao, "delta": delta}


@pytest.mark.parametrize("texto,nivel", [
    ("aumenta o volume para 40", 40), ("abaixa o volume para 25", 25),
    ("coloca o volume em 10", 10), ("volume em 35", 35),
])
def test_destino_explicito_preserva_atribuicao(texto, nivel):
    candidato = detectar_volume_ou_midia(texto, params_cb=lambda **p: p)
    assert candidato == {"intent": "VOLUME", "params": {"acao": "set", "nivel_volume": nivel}}


def _iot_com_brilho(brilho=60):
    estado = {"ultimo_alvo_iot": "lampada_quarto", "ultima_propriedade_iot": "ajustar_brilho",
        "ultimos_parametros_iot": {"brilho": brilho, "alvo": "lampada_quarto"}}
    return RuntimeIoT(memoria_sqlite=MemoriaIoTFalsa(), falar=lambda *_: None,
        estado_mental_getter=lambda: estado, emitir_fala=False, modo="simulado", log=lambda *_: None)


@pytest.mark.parametrize("texto,valor", [
    ("aumenta o brilho da luz em 10", 70),
    ("diminui o brilho da luz em 5", 55),
    ("aumenta o brilho da luz para 10", 10),
    ("coloca o brilho da luz em 10", 10),
])
def test_mesma_relacao_numerica_preserva_propriedade_em_outro_dominio(texto, valor):
    candidato = _iot_com_brilho().detectar(texto)
    assert candidato and candidato["intent"] == "IOT_CONTROL"
    assert candidato["params"]["acao"] == "ajustar_brilho"
    assert candidato["params"]["valor"] == valor


@pytest.mark.parametrize("propriedade", ["volume", "brilho", "velocidade", "temperatura"])
@pytest.mark.parametrize("verbo,direcao", [("aumenta", "aumentar"), ("reduza", "diminuir")])
@pytest.mark.parametrize("relacao,modo", [("em", "relativo"), ("para", "absoluto"), ("pra", "absoluto")])
def test_papel_do_numero_independe_da_habilidade(propriedade, verbo, direcao, relacao, modo):
    texto = f"{verbo} o {propriedade} {relacao} 15"
    ajuste = interpretar_relacao_valor_ajuste(texto, intervalo_valor=(len(texto) - 2, len(texto)))
    assert ajuste and (ajuste.modo, ajuste.valor, ajuste.direcao) == (modo, 15, direcao)
    assert not hasattr(ajuste, "autoriza_execucao")


@pytest.mark.parametrize("texto,intervalo", [
    ("volume em 40", (-1, 2)), ("volume em 40", (True, 2)),
    ("volume em 40", (0, 6)), ("volume em 40", (10, 30)),
    ("volume em 40", [10, 12]),
])
def test_numero_exige_intervalo_literal_validado(texto, intervalo):
    assert interpretar_relacao_valor_ajuste(texto, intervalo_valor=intervalo) is None


@pytest.mark.parametrize("brilho", [None, True, "60", -1, 101])
def test_delta_de_brilho_sem_base_valida_nao_inventa_set(brilho):
    assert _iot_com_brilho(brilho).detectar("aumenta o brilho da luz em 10") is None


@pytest.mark.parametrize("valor", [0, 101, 999])
def test_destino_brilho_invalido_nao_vira_passo_relativo_padrao(valor):
    assert _iot_com_brilho().detectar(f"aumenta o brilho da luz para {valor}") is None


@pytest.mark.parametrize("texto", [
    "não aumenta o volume em 10", "como eu faria para aumentar o volume em 10?",
    "ontem eu aumentei o volume em 10", 'toca a música "Aumenta o Volume em 10"',
    "se eu confirmar, aumenta o volume em 10",
])
def test_relacao_numerica_nao_concede_autorizacao_ao_turno(texto):
    from mente_laylay.cognicao.arbitro_turno import arbitrar_turno, CandidatoDecisao
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    # O detector bruto pode propor leitura de uma oração negada/relatada.
    # A fronteira correta da segurança é o árbitro, não ausência de proposta.
    candidato = detectar_intencao_deterministica_mente(texto, {"normalizar_texto": normalizar_texto})
    candidatos = [CandidatoDecisao(tipo="comando_explicito", valor=candidato,
        origem="detector_real", confianca=1.0)] if candidato else []
    resultado = arbitrar_turno(texto, candidatos, turno=classificar_modalidade_turno(texto))
    assert not resultado.get("decisao") or resultado["decisao"]["intent"] != "VOLUME", resultado


@pytest.mark.parametrize("texto,acao,valor", [
    ("aumenta o volume em 10", "up", 10), ("abaixa o som em 5", "down", 5),
    ("aumenta o volume para 40", "set", 40), ("coloca o som em 25", "set", 25),
])
def test_detector_composto_instanciado_preserva_valor_e_operacao(texto, acao, valor):
    candidato = detectar_intencao_deterministica_mente(texto, {"normalizar_texto": normalizar_texto})
    assert candidato and candidato["intent"] == "VOLUME"
    assert candidato["params"]["acao"] == acao
    assert candidato["params"]["nivel_volume" if acao == "set" else "delta"] == valor


@pytest.mark.parametrize("texto", [
    "aumenta o volume 10", "aumenta o volume em 5%", "aumenta o volume em 5 por cento",
    "aumenta o volume em 10 db", "aumenta o volume em 5.5",
])
def test_detector_nao_apaga_unidade_ou_ambiguidade_para_escolher_delta(texto):
    assert detectar_volume_ou_midia(texto, params_cb=lambda **p: p) is None


@pytest.mark.parametrize("texto", [
    "aumenta o brilho da luz 10", "aumenta o brilho da luz em 5%",
    "aumenta o brilho da luz em 10 db", "aumenta o brilho da luz em 5.5",
])
def test_mesma_ambiguidade_de_valor_nao_materializa_brilho(texto):
    assert _iot_com_brilho().detectar(texto) is None


@pytest.mark.parametrize("texto", ["aumenta o volume em 5%", "aumenta o volume em 5.5"])
def test_composicao_preserva_pontuacao_quantitativa_antes_da_normalizacao(texto):
    assert detectar_intencao_deterministica_mente(texto, {"normalizar_texto": normalizar_texto}) is None


@pytest.mark.parametrize("texto", ["aumenta o brilho da luz em 5%", "aumenta o brilho da luz em 5.5"])
def test_composicao_iot_preserva_pontuacao_da_fonte(texto):
    runtime = _iot_com_brilho()
    candidato = detectar_intencao_deterministica_mente(texto, {
        "normalizar_texto": normalizar_texto, "detectar_intencao_iot": runtime.detectar,
        "mente_integrada_estado": {"ultimos_parametros_iot": {"brilho": 60}}})
    assert not candidato or candidato["intent"] != "IOT_CONTROL", candidato


@pytest.mark.parametrize("texto", [
    "aumenta o volume em 5%", "aumenta o volume em 5.5",
    "aumenta o brilho da luz em 5%", "aumenta o brilho da luz em 5,5",
    'abre o site "ensaio de novo"', 'abre "ensaio de novo"',
    "abre o arquivo resultado.md", "abre o site exemplo.com/teste?pagina=2",
    "coloca o volume em 40%",
])
def test_coordenador_entrega_fonte_literal_ao_owner_do_argumento(texto):
    from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno

    recebidos = []
    resolver_intencao(texto, "terminal", {
        "normalizar_texto": normalizar_texto,
        "turno_atual": classificar_modalidade_turno(texto),
        "detectar_intencao_deterministica": lambda fonte: recebidos.append(fonte),
    })
    assert recebidos == [texto]


@pytest.mark.parametrize("modalidade,revisao", [
    ("misto", {}),
    ("comando", {"detectada": True, "resolvida": True, "cancelada": False}),
])
@pytest.mark.parametrize("efetivo", ["aumenta o volume em 5%", 'abre "ensaio de novo"'])
def test_recorte_canonico_preserva_argumento_sem_reintroduzir_ato_descartado(modalidade, revisao, efetivo):
    from mente_laylay.autonomia.coordenador_intencao import resolver_intencao

    recebidos = []
    resolver_intencao(f"abre a calculadora; na verdade, {efetivo}", "terminal", {
        "normalizar_texto": normalizar_texto,
        "turno_atual": {"modalidade": "comando", "modalidade_geral": modalidade,
            "autoriza_execucao": True, "texto_operacional_efetivo": efetivo,
            "revisao_intra_turno": revisao},
        "detectar_intencao_deterministica": lambda fonte: recebidos.append(fonte),
    })
    assert recebidos == [efetivo]


def test_preservar_fonte_nao_atravessa_veto_canonico():
    from mente_laylay.autonomia.coordenador_intencao import resolver_intencao

    recebidos = []
    resultado = resolver_intencao("aumenta o volume em 5%", "terminal", {
        "turno_atual": {"veto_execucao_operacional": True},
        "detectar_intencao_deterministica": lambda fonte: recebidos.append(fonte),
    })
    assert resultado == (None, "veto_operacional_turno")
    assert recebidos == []


@pytest.mark.parametrize("texto", ["aumenta o brilho da luz em 5%", "aumenta o brilho da luz em 5.5"])
def test_coordenador_nao_reoferece_argumento_destruido_ao_contexto(texto):
    from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno

    recebidos = []
    resolver_intencao(texto, "terminal", {
        "normalizar_texto": normalizar_texto,
        "turno_atual": classificar_modalidade_turno(texto),
        "resolver_comando_contextual_forcado": lambda fonte: recebidos.append(fonte),
    })
    assert recebidos == [texto]


@pytest.mark.parametrize("texto,esperado", [
    ("aumenta o brilho da luz em 5%", None),
    ("aumenta o brilho da luz em 5.5", None),
    ("aumenta o brilho da luz em 5", 65),
    ("coloca o brilho da luz em 40%", 40),
])
def test_owner_contextual_iot_preserva_argumento_para_detector_real(texto, esperado):
    from types import SimpleNamespace
    from mente_laylay.memoria_mental.contexto_imediato import ContextoImediatoRuntime

    iot = _iot_com_brilho()
    estado = SimpleNamespace(mental=iot.estado_mental_getter())
    contexto = ContextoImediatoRuntime(estado_runtime_getter=lambda: estado,
        servicos_iniciais={"_normalizar_texto_com_apelidos": normalizar_texto}, iot=iot)
    candidato = contexto.resolver_iot(texto)
    if esperado is None:
        assert candidato is None
    else:
        assert candidato["params"]["valor"] == esperado


@pytest.mark.parametrize("sufixo", ["", " em 5%", " em 5.5"])
def test_correcao_canonica_do_verbo_nao_destroi_argumentos_iot(sufixo):
    recebidos = []
    detectar_intencao_deterministica_mente("liag o ventilador" + sufixo, {
        "normalizar_texto": normalizar_texto,
        "detectar_intencao_iot": lambda fonte, _estado: recebidos.append(fonte),
    })
    assert recebidos and all(fonte == "liga o ventilador" + sufixo for fonte in recebidos)


@pytest.mark.parametrize("texto,params", [
    ("coloca o volume em quarenta", {"acao": "set", "nivel_volume": 40}),
    ("aumenta o volume para oitenta e dois", {"acao": "set", "nivel_volume": 82}),
    ("diminui o volume em quinze", {"acao": "down", "delta": 15}),
    ("deixa o som do computador em quarenta por cento", {"acao": "set", "nivel_volume": 40}),
    ("deixa o som do computador em 40 por cento", {"acao": "set", "nivel_volume": 40}),
    ("coloca o volume em cem", {"acao": "set", "nivel_volume": 100}),
])
def test_quantidade_literal_composta_nao_vira_busca_ou_passo_padrao(texto, params):
    candidato = detectar_intencao_deterministica_mente(texto, {"normalizar_texto": normalizar_texto})
    assert candidato == {"intent": "VOLUME", "params": params}


@pytest.mark.parametrize("texto,valor", [
    ("coloca o brilho da luz em quarenta", 40),
    ("aumenta o brilho da luz para trinta", 30),
    ("diminui o brilho da luz em cinco", 55),
    ("aumenta o brilho da luz em vinte e dois", 82),
])
def test_mesma_quantidade_por_extenso_no_owner_de_brilho(texto, valor):
    candidato = _iot_com_brilho().detectar(texto)
    assert candidato and candidato["params"]["valor"] == valor


@pytest.mark.parametrize("literal,valor", [
    ("zero", 0), ("um", 1), ("duas", 2), ("três", 3), ("Quatorze", 14),
    ("dezesseis", 16), ("vinte e dois", 22), ("noventa e nove", 99),
    ("cem", 100), ("cento e um", 101), ("duzentos", 200),
    ("duzentos e quinze", 215), ("novecentos e noventa e nove", 999), ("40", 40),
])
def test_leitor_inteiro_literal_compoe_numero_sem_estado_ou_habilidade(literal, valor):
    from mente_laylay.cognicao.gramatica_operacional import interpretar_inteiro_literal
    assert interpretar_inteiro_literal(literal) == valor


@pytest.mark.parametrize("literal", ["quarenta e onze", "vinte cinco", "um e dois", "cento",
    "cem e dois", "cento e zero", "cento e cem", "mil", "quarenta e meio", "40.5", "-5", True, None])
def test_leitor_nao_trunca_literal_invalido_para_obter_inteiro(literal):
    from mente_laylay.cognicao.gramatica_operacional import interpretar_inteiro_literal
    assert interpretar_inteiro_literal(literal) is None


@pytest.mark.parametrize("literal", ["quarenta e onze", "quarenta e meio", "quarenta vírgula cinco",
    "quarenta e 5", "40 e cinco", "mil"])
@pytest.mark.parametrize("recurso", ["volume", "brilho da luz"])
def test_quantidade_nao_compreendida_nao_vira_prefixo_valido_ou_passo_padrao(literal, recurso):
    texto = f"aumenta o {recurso} para {literal}"
    candidato = (_iot_com_brilho().detectar(texto) if recurso == "brilho da luz"
        else detectar_volume_ou_midia(texto, params_cb=lambda **p: p))
    assert candidato is None


@pytest.mark.parametrize("nome", ["Quarenta e Dois", "Cem por Cento", "Volume em Quarenta"])
def test_numero_em_titulo_literal_nao_vira_quantidade_de_outro_comando(nome):
    candidato = detectar_intencao_deterministica_mente(f'toca a música "{nome}"', {"normalizar_texto": normalizar_texto})
    assert candidato and candidato["intent"] == "MUSIC_SEARCH"
    assert normalizar_texto(candidato["params"]["query"]) == normalizar_texto(nome)


@pytest.mark.parametrize("molde", ["não aumenta o volume para {}", "como eu faria para aumentar o volume para {}?",
    "quando eu confirmar, aumenta o volume para {}", "ontem eu aumentei o volume para {}"])
def test_quantidade_por_extenso_nao_concede_autoridade(molde):
    from mente_laylay.cognicao.arbitro_turno import arbitrar_turno, CandidatoDecisao
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    texto = molde.format("quarenta e dois")
    candidato = detectar_intencao_deterministica_mente(texto, {"normalizar_texto": normalizar_texto})
    resultado = arbitrar_turno(texto, [CandidatoDecisao(tipo="comando_explicito", valor=candidato,
        origem="detector_real", confianca=1.0)] if candidato else [], turno=classificar_modalidade_turno(texto))
    assert not resultado.get("decisao") or resultado["decisao"]["intent"] != "VOLUME"


@pytest.mark.parametrize("texto,acao", [
    ("deixa a luz em um azul claro", "ajustar_cor"),
    ("coloca a luz em uma cor azul", "ajustar_cor"),
    ("deixa a luz em um branco quente", "ajustar_branco"),
    ("aumenta o brilho da luz em um pouco", "ajustar_brilho"),
])
def test_artigo_e_intensidade_nao_sao_cardinal_de_propriedade(texto, acao):
    candidato = _iot_com_brilho().detectar(texto)
    assert candidato and candidato["params"]["acao"] == acao
    if "um pouco" in texto:
        assert candidato["params"]["valor"] == 70


@pytest.mark.parametrize("literal", ["4e1", "4 e1", "um db"])
@pytest.mark.parametrize("recurso", ["volume", "brilho da luz"])
def test_numero_ou_unidade_nao_admitidos_nao_viram_ajuste_parcial(literal, recurso):
    texto = f"aumenta o {recurso} em {literal}"
    candidato = (_iot_com_brilho().detectar(texto) if recurso == "brilho da luz"
        else detectar_volume_ou_midia(texto, params_cb=lambda **p: p))
    assert candidato is None


@pytest.mark.parametrize("dezena,base", [("vinte", 20), ("trinta", 30), ("quarenta", 40),
    ("cinquenta", 50), ("sessenta", 60), ("setenta", 70), ("oitenta", 80), ("noventa", 90)])
@pytest.mark.parametrize("unidade,valor", [("um", 1), ("dois", 2), ("três", 3), ("quatro", 4),
    ("cinco", 5), ("seis", 6), ("sete", 7), ("oito", 8), ("nove", 9)])
def test_regra_de_composicao_da_quantidade_independe_de_frase_de_comando(dezena, base, unidade, valor):
    from mente_laylay.cognicao.gramatica_operacional import interpretar_inteiro_literal, localizar_quantidade_ajuste
    literal = f"{dezena} e {unidade}"
    texto = f"parâmetro para {literal} por cento"
    intervalo = localizar_quantidade_ajuste(texto, apos_recurso=len("parâmetro"))
    assert intervalo and texto[slice(*intervalo)] == literal
    assert interpretar_inteiro_literal(literal) == base + valor
    leitura = interpretar_relacao_valor_ajuste(texto, intervalo_valor=intervalo)
    assert leitura and leitura.valor == base + valor and leitura.modo == "absoluto"
    assert leitura.unidade == "por cento"


@pytest.mark.parametrize("texto,apos", [(None, 0), ("volume em dez", True),
    ("volume em dez", -1), ("volume em dez", 100), ("volume. coloca outro em dez", 6),
    ("volume; brilho em dez", 6)])
def test_localizacao_nao_reconstroi_indice_invalido_nem_cruza_oracao(texto, apos):
    from mente_laylay.cognicao.gramatica_operacional import localizar_quantidade_ajuste
    assert localizar_quantidade_ajuste(texto, apos_recurso=apos) is None


@pytest.mark.parametrize("literal,valor", [("quarenta e onze", None), ("mil", None),
    ("5.5", None), ("-5", None), ("vinte e dois", 22), ("40", 40),
    ("ponto cinco", None), ("vírgula cinco", None)])
def test_forma_quantitativa_e_valor_admitido_sao_evidencias_distintas(literal, valor):
    from mente_laylay.cognicao.gramatica_operacional import localizar_quantidade_literal, interpretar_inteiro_literal
    fonte = f"prefixo {literal} restante"
    intervalo = localizar_quantidade_literal(fonte, inicio=len("prefixo "))
    assert intervalo and fonte[slice(*intervalo)] == literal
    assert interpretar_inteiro_literal(fonte[slice(*intervalo)]) == valor


@pytest.mark.parametrize("texto,inicio", [(None, 0), ("dez", True), ("dez", -1),
    ("dez", 4), ("nome com dez", 0), ('"quarenta"', 0), ("", 0),
    ("ponto morto", 0), ("vírgula", 0)])
def test_forma_quantitativa_nao_inventa_inicio_nem_procura_numero_em_nome(texto, inicio):
    from mente_laylay.cognicao.gramatica_operacional import localizar_quantidade_literal
    assert localizar_quantidade_literal(texto, inicio=inicio) is None


@pytest.mark.parametrize("texto", ["coloca em quarenta e onze", "coloca em 5.5", "deixa em quarenta minutos"])
def test_barreira_reconhece_forma_invalida_sem_declara_la_valor_valido(texto):
    from mente_laylay.cognicao.gramatica_operacional import (
        texto_pede_ajuste_parametrico_contextual, texto_pede_ajuste_numerico_contextual,
        ler_nivel_atribuicao_contextual,
    )
    assert texto_pede_ajuste_parametrico_contextual(texto)
    assert not texto_pede_ajuste_numerico_contextual(texto)
    assert ler_nivel_atribuicao_contextual(texto) is None


def test_continuidade_reexporta_mesma_gramatica_usada_por_escopo():
    from mente_laylay.cognicao import gramatica_operacional, escopo_autorizacao
    from mente_laylay.memoria_mental import contexto_imediato
    assert contexto_imediato.texto_pede_ajuste_parametrico_contextual is gramatica_operacional.texto_pede_ajuste_parametrico_contextual
    assert escopo_autorizacao.texto_pede_ajuste_parametrico_contextual is gramatica_operacional.texto_pede_ajuste_parametrico_contextual
