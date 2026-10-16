"""Um ato resolvido não autoriza outro parâmetro só por manter o intent."""
from copy import deepcopy

import pytest

from mente_laylay.autonomia.orquestrador_deterministico import detectar_intencao_deterministica_mente
from mente_laylay.autonomia.roteador_deterministico import extrair_intencao_abrir_app
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from scripts.tests.test_escopo_autorizacao_por_ato import _runtime


def resolver_real(texto, frame):
    return detectar_intencao_deterministica_mente(texto, {
        "normalizar_texto": normalizar_texto, "mente_integrada_estado": frame,
        "extrair_intencao_abrir_app": lambda fonte: extrair_intencao_abrir_app(fonte,
            normalizar_texto=normalizar_texto, limpar_destino=lambda s: s,
            apps_map={}, sites_diretos={}),
    })


@pytest.mark.parametrize("texto,errado", [
    ("aumenta o volume em 10", {"intent": "VOLUME", "params": {"acao": "set", "nivel_volume": 10}}),
    ("aumenta o volume em 10", {"intent": "VOLUME", "params": {"acao": "up", "aumento": "10", "unidade": "db"}}),
    ("coloca o volume em 40", {"intent": "VOLUME", "params": {"acao": "set", "nivel_volume": 100}}),
    ("pausa a música", {"intent": "MEDIA_CONTROL", "params": {"acao": "play"}}),
    ("abre o aplicativo Calculadora", {"intent": "APP_OPEN", "params": {"nome_app": "Notepad"}}),
    ("abre o site github", {"intent": "OPEN_URL", "params": {"alvo": "youtube"}}),
])
def test_proposta_nao_empresta_intent_para_trocar_operacao_valor_ou_alvo(texto, errado):
    certo = resolver_real(texto, {})
    assert certo and certo["intent"] == errado["intent"], "controle: mesma intenção já resolvida pelo owner"
    validar, estado = _runtime(texto, resolver_real)
    antes = estado.snapshot()
    proposta = [deepcopy(errado), deepcopy(certo)]
    resultado = validar(proposta)
    assert resultado["comandos"] == [certo]
    assert len(resultado["rejeitados"]) == 1
    assert estado.snapshot() == antes and proposta == [errado, certo]


@pytest.mark.parametrize("texto", ["aumenta o volume em 10", "coloca o volume em 40",
    "pausa a música", "abre o aplicativo Calculadora", "abre o site github"])
def test_proposta_canonica_legitima_do_ato_unico_continua_admitida(texto):
    pedido = resolver_real(texto, {})
    assert pedido
    validar, _ = _runtime(texto, resolver_real)
    assert validar([pedido])["comandos"] == [pedido]


def test_ato_unico_nao_autoriza_repetir_a_mesma_proposta():
    texto = "abre o aplicativo Calculadora"
    pedido = resolver_real(texto, {})
    validar, _ = _runtime(texto, resolver_real)
    assert validar([pedido, deepcopy(pedido)])["comandos"] == [pedido]


@pytest.mark.parametrize("mudanca", [{"target": "pc_b"}, {"delta": 5},
    {"delta": True}, {"_execucao_silenciosa": True}, {"unidade": "db"}])
def test_ato_resolvido_nao_permite_parametro_extra_ou_outra_maquina(mudanca):
    texto = "aumenta o volume em 10"
    pedido = resolver_real(texto, {})
    pedido["params"].update(mudanca)
    validar, _ = _runtime(texto, resolver_real)
    assert validar([pedido])["comandos"] == []


def test_equivalencia_ja_canonica_de_destino_padrao_e_caixa_do_app_e_preservada():
    texto = "abre a calculadora"
    pedido = resolver_real(texto, {})
    equivalente = deepcopy(pedido)
    equivalente["params"].update(nome_app=pedido["params"]["nome_app"].upper(), target="pc_a")
    validar, _ = _runtime(texto, resolver_real)
    assert validar([equivalente])["comandos"] == [equivalente]


def test_nivel_absoluto_sem_acao_preserva_equivalencia_ja_aceita_pelo_executor():
    validar, _ = _runtime("coloca o volume em 40", resolver_real)
    proposta = {"intent": "VOLUME", "params": {"nivel_volume": 40}}
    assert validar([proposta])["comandos"] == [proposta]


@pytest.mark.parametrize("proposta", [
    {"acao": "open_url", "alvo": "github"},
    {"intent": "OPEN_URL", "params": {"url": "github"}},
])
def test_alias_de_seletor_web_preserva_abertura_legitima_sem_mudar_alvo(proposta):
    validar, _ = _runtime("abre o site github", resolver_real)
    assert validar([proposta])["comandos"] == [proposta]


@pytest.mark.parametrize("params", [
    {"alvo": "github", "url": "youtube"}, {"url": "github", "target": "pc_b"},
    {"url": "github", "_execucao_silenciosa": True},
])
def test_projecao_de_alias_nao_apaga_seletor_conflitante_destino_ou_extras(params):
    validar, _ = _runtime("abre o site github", resolver_real)
    assert validar([{"intent": "OPEN_URL", "params": params}])["comandos"] == []


def _detector_agenda_real(frame):
    from mente_laylay.autonomia.agendamento_mental import extrair_acao_agendada_local
    from mente_laylay.autonomia.orquestrador_deterministico import DeteccaoDeterministicaRuntime
    return DeteccaoDeterministicaRuntime(namespace_getter=lambda: {
        "_normalizar_texto_com_apelidos": normalizar_texto,
        "_extrair_acao_agendada_local": lambda t: extrair_acao_agendada_local(t, normalizar_texto),
        "_extrair_intencao_abrir_app": lambda t: resolver_real(t, frame),
    }, estado_getter=lambda: frame, sites_diretos={}, apps_map={})


def _resolver_agenda_real(texto, frame):
    return _detector_agenda_real(frame).detectar(texto, estado_mental=frame)


@pytest.mark.parametrize("texto", ["abre a calculadora daqui 5 minutos",
    "coloca o volume em 40 daqui 5 minutos", "pausa a música daqui 5 minutos"])
def test_controle_agendamento_de_mesma_rota_ja_atende_ao_escopo(texto):
    pedido = _resolver_agenda_real(texto, {})
    assert pedido and pedido["intent"] == "AGENDAR_ACAO"
    validar, _ = _runtime(texto, _resolver_agenda_real)
    assert validar([pedido])["comandos"] == [pedido]


@pytest.mark.parametrize("texto", [
    "abre a calculadora daqui 5 minutos", "abre o bloco de notas daqui 2 minutos",
    "coloca o volume em 40 daqui 5 minutos", "coloca em 40 daqui 5 minutos",
    "pausa a música daqui 5 minutos",
])
def test_rota_de_interpretacao_nao_troca_identidade_do_mesmo_efeito_agendado(texto):
    from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
    from mente_laylay.autonomia.agendamento_mental import extrair_acao_agendada_local
    from scripts.tests.test_regressoes_contexto_operacional import _volume_confirmado_para_continuacao
    validar, estado = _runtime(texto, _resolver_agenda_real)
    antecedente = _volume_confirmado_para_continuacao()
    for chave in ("turno_atual", "plano_turno_atual", "retrato_turno_atual"):
        antecedente.pop(chave, None)
    estado.atualizar_campos("mental", **antecedente)
    frame = estado.snapshot()["mental"]
    detector = _detector_agenda_real(frame)
    autorizado = detector.detectar(texto)
    proposta, rota = resolver_intencao(texto, "teste", {
        "normalizar_texto": normalizar_texto,
        "extrair_acao_agendada": lambda t: extrair_acao_agendada_local(t, normalizar_texto),
        "detectar_intencao_deterministica": detector.detectar,
    })
    assert autorizado and proposta and autorizado["intent"] == proposta["intent"] == "AGENDAR_ACAO"
    assert rota == "agendamento"
    comparavel = deepcopy(proposta)
    assert comparavel["params"].pop("rota_original") == "deterministico-explicito"
    esperado = deepcopy(autorizado)
    assert esperado["params"].pop("rota_original") == "deterministico"
    assert comparavel == esperado, "controle: ação, alvo e prazo já coincidem antes da admissão"
    antes, entrada = estado.snapshot(), deepcopy(proposta)
    resultado = validar([proposta, deepcopy(proposta)])
    assert resultado["comandos"] == [proposta], "primeira divergência: proveniência não define o efeito"
    assert len(resultado["rejeitados"]) == 1, "metadado não libera consumo duplicado do ato"
    assert proposta == entrada and estado.snapshot() == antes


@pytest.mark.parametrize("rota", ["deterministico-explicito", "rota_diagnostica", "autorizado", "", None])
def test_projecao_de_proveniencia_e_isolada_e_nao_altera_comando_do_executor(rota):
    from mente_laylay.autonomia.dispatcher_comandos_json import normalizar_candidato_json_para_intencao
    pedido = _resolver_agenda_real("abre a calculadora daqui 5 minutos", {})
    if rota is None:
        pedido["params"].pop("rota_original")
    else:
        pedido["params"]["rota_original"] = rota
    antes = deepcopy(pedido)
    compacto = normalizar_candidato_json_para_intencao(pedido, compactar_aliases=True)
    esperado = deepcopy(antes)
    esperado["params"].pop("rota_original", None)
    assert compacto == esperado
    assert normalizar_candidato_json_para_intencao(pedido) == antes
    assert pedido == antes


@pytest.mark.parametrize("mudanca", ["acao", "alvo", "prazo", "hora", "destino", "destino_interno",
    "texto_acao", "extra", "substituir", "metadado_interno"])
def test_proveniencia_diferente_nao_esconde_divergencia_operacional_no_agendamento(mudanca):
    texto = "abre a calculadora daqui 5 minutos"
    certo = _resolver_agenda_real(texto, {})
    certo["params"]["rota_original"] = "deterministico-explicito"
    errado = deepcopy(certo)
    params = errado["params"]
    if mudanca == "acao": params["acao_agendada"]["intent"] = "CLOSE_APP"
    elif mudanca == "alvo": params["acao_agendada"]["params"]["nome_app"] = "Notepad"
    elif mudanca == "prazo": params["atraso_segundos"] = 600
    elif mudanca == "hora": params["hora_alvo"] = "23:30"
    elif mudanca == "destino": params["target"] = "pc_b"
    elif mudanca == "destino_interno": params["acao_agendada"]["params"]["target"] = "pc_b"
    elif mudanca == "texto_acao": params["texto_acao"] = "fecha a calculadora"
    elif mudanca == "extra": params["_execucao_silenciosa"] = True
    elif mudanca == "substituir": params["substituir_agendamento_anterior"] = True
    else: params["acao_agendada"]["params"]["rota_original"] = "deterministico"
    validar, _ = _runtime(texto, _resolver_agenda_real)
    resultado = validar([errado, certo])
    assert resultado["comandos"] == [certo]
    assert len(resultado["rejeitados"]) == 1


@pytest.mark.parametrize("rota", [None, True, 1, [], {"target": "pc_b"}])
def test_rota_nao_textual_nao_e_apagada_para_fabricar_equivalencia(rota):
    from mente_laylay.autonomia.dispatcher_comandos_json import normalizar_candidato_json_para_intencao
    pedido = _resolver_agenda_real("abre a calculadora daqui 5 minutos", {})
    pedido["params"]["rota_original"] = rota
    antes = deepcopy(pedido)
    assert normalizar_candidato_json_para_intencao(pedido, compactar_aliases=True) is None
    assert pedido == antes


def test_nome_de_metadado_em_outro_contrato_nao_e_ignorado_globalmente():
    pedido = resolver_real("abre a calculadora", {})
    pedido["params"]["rota_original"] = "autorizado"
    validar, _ = _runtime("abre a calculadora", resolver_real)
    assert validar([pedido])["comandos"] == []


@pytest.mark.parametrize("texto", ["não aumenta o volume em 10", "como eu faria para aumentar o volume em 10?",
    "quando eu confirmar, aumenta o volume em 10"])
def test_resolver_nao_e_consultado_para_dar_autoridade_ao_turno_vetado(texto):
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    from mente_laylay.cognicao.plano_turno import planejar_turno
    from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
    from mente_laylay.cognicao.decisao_turno import criar_validador_comandos_turno_runtime
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
    # A fixture positiva compartilhada exige autoriza=True. Aqui usamos os
    # mesmos owners reais sem essa pré-condição, para alcançar a guarda de veto.
    turno = classificar_modalidade_turno(texto)
    assert not turno["autoriza_execucao"]
    retrato, _ = construir_retrato_turno(texto, turno=turno, mente={}, contexto_perceptivo={})
    turno["retrato_id"] = retrato["id"]
    estado = EstadoCompartilhadoRuntime(mental={"turno_atual": turno,
        "plano_turno_atual": planejar_turno(texto, turno=turno, mente={}), "retrato_turno_atual": retrato})
    validar = criar_validador_comandos_turno_runtime(estado_runtime=estado,
        resolver_ato=lambda *_: pytest.fail("veto deve anteceder resolução"))
    assert validar([{"intent": "VOLUME", "params": {"acao": "up", "delta": 10}}])["comandos"] == []


def test_identidade_de_outra_ocorrencia_e_recusada_antes_da_resolucao():
    from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
    texto = "aumenta o volume em 10"
    validar, _ = _runtime(texto, lambda *_: pytest.fail("proposta obsoleta não consulta owner"))
    proposta = ContratoPropostaPrincipal(turno_id="outra", texto_usuario=texto, resposta_bruta='{"comandos":[]}')
    assert validar.validar_proposta([{"intent": "VOLUME", "params": {"acao": "up", "delta": 10}}], proposta)["comandos"] == []


def test_resolucao_inconclusiva_nao_e_reportada_como_escopo_validado():
    # Limite explícito deste incremento: ato único sem resolução continua no
    # contrato agregado legado. Não fingir validação paramétrica/semântica.
    pedido = {"intent": "VOLUME", "params": {"acao": "set", "nivel_volume": 40}}
    validar, _ = _runtime("coloca o volume em 40", lambda *_: None)
    resultado = validar([pedido])
    assert resultado["comandos"] == [pedido]
    assert not resultado.get("escopo_operacional_por_ato")


@pytest.mark.parametrize("texto", ["coloca em quarenta e onze", "coloca em 5.5", "coloca em quarenta minutos",
    "coloca em quarenta"])
@pytest.mark.parametrize("proposta", [
    {"intent": "MUSIC_SEARCH", "params": {"query": "em quarenta"}},
    {"intent": "VOLUME", "params": {"acao": "set", "nivel_volume": 40}},
    {"intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}},
])
def test_ajuste_sem_resolucao_nao_aceita_valor_referente_ou_outro_dominio_da_proposta(texto, proposta):
    assert resolver_real(texto, {}) is None, "controle: owner não resolveu o ajuste"
    validar, estado = _runtime(texto, resolver_real)
    antes = estado.snapshot()
    resultado = validar([proposta])
    assert resultado["comandos"] == [], "admissão não pode converter ausência de resolução em permissão"
    assert resultado["rejeitados"] and estado.snapshot() == antes


def test_ajuste_contextual_resolvido_admite_apenas_valor_e_destino_vinculados():
    from scripts.tests.test_regressoes_contexto_operacional import _volume_confirmado_para_continuacao
    validar, estado = _runtime("coloca em quarenta", resolver_real)
    antecedente = _volume_confirmado_para_continuacao()
    for chave in ("turno_atual", "plano_turno_atual", "retrato_turno_atual"):
        antecedente.pop(chave, None)
    estado.atualizar_campos("mental", **antecedente)
    certo = resolver_real("coloca em quarenta", estado.mental)
    assert certo and certo["params"]["nivel_volume"] == 40
    errado = {"intent": "VOLUME", "params": {"acao": "set", "nivel_volume": 80}}
    resultado = validar([errado, certo])
    assert resultado["comandos"] == [certo]


@pytest.mark.parametrize("titulo", ["Em Quarenta e Onze", "Em 5.5", "Água e Sol", "UnStraße"])
def test_admissao_de_titulo_literal_resolve_a_fonte_original_e_nao_sua_copia_minuscula(titulo):
    texto = f'coloca "{titulo}"'
    certo = resolver_real(texto, {})
    assert certo == {"intent": "MUSIC_SEARCH", "params": {"query": titulo}}
    validar, _ = _runtime(texto, resolver_real)
    resultado = validar([certo])
    assert resultado["comandos"] == [certo], "primeiro limite: argumento literal mudou na resolução por ato"
    assert resultado["escopo_operacional_por_ato"][0]["pedido"] == certo


@pytest.mark.parametrize("texto", [
    'Toca a música "Água e Sol"',
    'Abre o site "https://Example.test/MinhaPasta?chave=AbC"',
    'Abre o arquivo "Meu Relatório Final.TXT"',
    'Cria uma nota "Minha Revisão: A e B"',
])
def test_resolver_por_ato_recebe_literal_e_frame_da_mesma_fonte_sem_reclassificar_autoridade(texto):
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    from mente_laylay.cognicao.escopo_autorizacao import construir_autorizacoes_por_ato
    turno = classificar_modalidade_turno(texto)
    assert len(turno["segmentos"]) == 1 and turno["segmentos"][0]["autoriza_execucao"]
    chamadas = []
    def observar(fonte, frame):
        chamadas.append((fonte, deepcopy(frame)))
        return {"intent": "APP_OPEN", "params": {"nome_app": "controle_do_transporte"}}
    antes = deepcopy(turno)
    escopos = construir_autorizacoes_por_ato(turno, {}, observar)
    assert len(escopos) == 1 and len(chamadas) == 1
    fonte, frame = chamadas[0]
    assert fonte == texto, "primeiro limite: classificação normalizada não pode substituir o argumento"
    assert frame["turno_atual"]["texto_original"] == fonte
    assert frame["turno_atual"]["texto"] == fonte and frame["turno_atual"]["texto_operacional"] == fonte
    assert frame["turno_atual"]["autoriza_execucao"] is True
    assert turno == antes


@pytest.mark.parametrize("alteracao", ["sem_fonte", "texto_divergente", "truncado"])
def test_resolucao_por_ato_sem_coordenadas_comprovadas_nao_inventa_texto_original(alteracao):
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    from mente_laylay.cognicao.escopo_autorizacao import construir_autorizacoes_por_ato
    turno = classificar_modalidade_turno('Toca a música "Água e Sol"')
    if alteracao == "sem_fonte":
        turno["texto_original"] = turno["texto"] = ""
    elif alteracao == "texto_divergente":
        turno["segmentos"][0].update(texto="toca outro alvo", texto_estrutural="toca outro alvo")
    else:
        turno["segmentos"][0].update(texto="toca " + "x" * 300, texto_estrutural="toca " + "x" * 300)
    chamadas = []
    assert construir_autorizacoes_por_ato(turno, {}, lambda *a: chamadas.append(a)) == ()
    assert chamadas == [], "não chamar resolver sobre fonte sem vínculo demonstrável"


@pytest.mark.parametrize("alteracao", ["outro_nome", "minusculas", "outro_destino", "extra"])
def test_preservar_fonte_literal_nao_torna_argumentos_diferentes_equivalentes(alteracao):
    texto = 'coloca "Em Quarenta e Onze"'
    certo = resolver_real(texto, {})
    errado = deepcopy(certo)
    if alteracao == "outro_nome": errado["params"]["query"] = "Outro Nome"
    elif alteracao == "minusculas": errado["params"]["query"] = certo["params"]["query"].casefold()
    elif alteracao == "outro_destino": errado["params"]["target"] = "pc_b"
    else: errado["params"]["unidade"] = "campo_nao_pedido"
    validar, _ = _runtime(texto, resolver_real)
    resultado = validar([errado, certo, deepcopy(certo)])
    assert resultado["comandos"] == [certo]
    assert len(resultado["rejeitados"]) == 2


def test_segmentacao_de_duas_ordens_musicais_preserva_negacao_por_ato():
    texto = 'Toca a música "Água e Sol"; não toca a música "Noite e Lua"'
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    turno = classificar_modalidade_turno(texto)
    assert len(turno["segmentos"]) == 2, "primeiro limite independente: atos musicais foram fundidos antes da resolução"
    assert turno["segmentos"][0]["autoriza_execucao"] is True
    assert turno["segmentos"][1]["veto_execucao_operacional"] is True
    certo = {"intent": "MUSIC_SEARCH", "params": {"query": "Água e Sol"}}
    errado = {"intent": "MUSIC_SEARCH", "params": {"query": "Noite e Lua"}}
    validar, _ = _runtime(texto, resolver_real)
    resultado = validar([errado, certo])
    assert resultado["comandos"] == [certo]
    assert resultado["atos_autorizados_vinculados"] == [0]


def test_segmentacao_musical_com_outro_dominio_negado_preserva_fronteira_por_ato():
    texto = 'Toca a música "Água e Sol"; não abre a calculadora'
    certo = {"intent": "MUSIC_SEARCH", "params": {"query": "Água e Sol"}}
    errado = {"intent": "APP_OPEN", "params": {"nome_app": "calculadora"}}
    validar, estado = _runtime(texto, resolver_real)
    assert len(estado.mental["turno_atual"]["segmentos"]) == 2, "primeiro limite independente: negação foi fundida ao pedido musical"
    resultado = validar([errado, certo])
    assert resultado["comandos"] == [certo]
    assert resultado["atos_autorizados_vinculados"] == [0]


@pytest.mark.parametrize("texto", [
    'Toca a música "Água e Sol"; quando eu confirmar, toca a música "Noite e Lua"',
    'Abre o site "https://Example.test/MinhaPasta"; não liga a luz',
])
def test_fonte_original_nao_reintroduz_ato_condicionado_ou_negado(texto):
    validar, estado = _runtime(texto, resolver_real)
    turno = estado.mental["turno_atual"]
    assert len(turno["segmentos"]) == 2
    assert turno["segmentos"][1]["veto_execucao_operacional"]
    certo = resolver_real(texto.split(";")[0], {})
    assert certo
    negado = {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "lampada_quarto"}}
    resultado = validar([negado, certo])
    assert resultado["comandos"] == [certo]
    assert resultado["atos_autorizados_vinculados"] == [0]


def test_duas_fontes_literais_repetidas_preservam_escopos_independentes():
    texto = 'Toca a música "Água e Sol"; toca a música "Água e Sol"'
    certo = {"intent": "MUSIC_SEARCH", "params": {"query": "Água e Sol"}}
    validar, _ = _runtime(texto, resolver_real)
    resultado = validar([certo, deepcopy(certo), deepcopy(certo)])
    assert resultado["comandos"] == [certo, certo]
    assert resultado["atos_autorizados_vinculados"] == [0, 1]
