import time

import pytest

from mente_laylay.autonomia.roteador_deterministico import detectar_fechar_alvo
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.coordenador_intencao import executar_fluxo_intencao
from mente_laylay.memoria_mental.contexto_imediato import resolver_comando_janela_contextual
from mente_laylay.memoria_mental.musica_conversacional_runtime import (
    MusicaConversacionalRuntime,
)
from mente_laylay.memoria_mental.pendencia_acao import (
    CHAVE_PENDENCIA_ACAO,
    PendenciaAcaoRuntime,
)
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial, registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.memoria_mental.contexto_imediato import (
    referencia_contextual_imediata, resolver_comando_acao_geral_contextual,
)


@pytest.mark.parametrize("seguimento,nivel", [
    ("coloca em 40", 40),  # relato do desktop: volume em 90 → elipse
    ("coloca em 25", 25),
    ("deixa em 40", 40),
    ("aumenta para 100", 100),
    ("aumente pra 85", 85),
    ("sobe para 80", 80),
    ("suba pra 95", 95),
    ("abaixa para 40", 40),
    ("diminui pra 25", 25),
    ("reduza para 30", 30),
    ("coloca o volume em 40", 40),  # controle com domínio explícito
])
@pytest.mark.parametrize("musica_anterior", [False, True])
def test_ajuste_numerico_apos_volume_confirmado_nao_vira_busca_musical(
    seguimento: str, nivel: int, musica_anterior: bool,
) -> None:
    """Continuidade do parâmetro, não repetir 90 nem escolher título com 40.

    Publicação de memória e detector são reais. Receipts são fixtures, sem
    executar áudio/Windows/YouTube. Não reproduz a sessão desktop inteira.
    """
    estado = estado_mental_inicial()
    if musica_anterior:
        estado = registrar_resultado_execucao(estado, ResultadoAcao(
            id_solicitacao="contexto-musica-anterior", intent="MUSIC_SEARCH",
            alvo="faixa anterior", status="musica_reproduzindo", executou=True,
            confirmado=True, origem="executor", params={"query": "faixa anterior"}),
            "coloca uma música")
    contexto = {"normalizar_texto": normalizar_texto, "mente_integrada_estado": estado}
    inicial = detectar_intencao_deterministica_mente("coloca o volume em 90", contexto)
    assert inicial is not None and inicial["intent"] == "VOLUME"
    assert inicial["params"]["acao"] == "set" and inicial["params"]["nivel_volume"] == 90
    receipt = ResultadoAcao(id_solicitacao="contexto-volume-90", intent="VOLUME", alvo="",
        status="volume_ajustado", executou=True, confirmado=True, origem="executor",
        params=dict(inicial["params"]), confirmacao_oferecida="estado_observado",
        evidencia_confirmacao="API de áudio do Windows releu o volume mestre em 90%")
    estado = registrar_resultado_execucao(estado, receipt, "coloca o volume em 90")
    assert estado["ultima_acao_intent"] == "VOLUME"
    assert estado["ultima_acao_contrato"]["confirmado"] is True
    assert estado["ultima_acao_params"]["nivel_volume"] == 90
    contexto["mente_integrada_estado"] = estado
    referencia = referencia_contextual_imediata(
        mente_integrada_estado=estado, foco_vivo={}, texto_atual=seguimento)
    if "volume" not in seguimento:
        controle_owner = resolver_comando_acao_geral_contextual(seguimento, referencia)
        assert controle_owner and controle_owner["params"]["nivel_volume"] == nivel
    resultado = detectar_intencao_deterministica_mente(seguimento, contexto)
    assert resultado is not None, "ajuste elíptico perdeu o domínio volume na resolução"
    assert resultado["intent"] == "VOLUME", resultado
    assert resultado["params"]["acao"] == "set"
    assert resultado["params"]["nivel_volume"] == nivel
    assert not resultado["params"].get("query"), "número virou título de música"


def _volume_confirmado_para_continuacao() -> dict:
    return registrar_resultado_execucao(estado_mental_inicial(), ResultadoAcao(
        id_solicitacao="volume-continuacao", intent="VOLUME", status="volume_ajustado",
        executou=True, confirmado=True, origem="executor", params={"acao": "set", "nivel_volume": 90}),
        "coloca o volume em 90")


@pytest.mark.parametrize("texto,nivel", [
    ("coloca em quarenta", 40), ("deixa em vinte e dois", 22),
    ("aumenta para cem", 100), ("reduza pra trinta e cinco", 35),
    ("coloca em quarenta por cento", 40), ("Coloca em Três", 3),
    ("coloca em zero", 0), ("aumente para oitenta e dois", 82),
])
def test_quantidade_literal_contextual_reutiliza_owner_e_preserva_destino(texto, nivel):
    from mente_laylay.memoria_mental.contexto_imediato import resolver_continuacao_operacional_confirmada
    estado = registrar_resultado_execucao(estado_mental_inicial(), ResultadoAcao(
        id_solicitacao="volume-extenso", intent="VOLUME", status="volume_ajustado",
        executou=True, confirmado=True, origem="executor",
        params={"acao": "set", "nivel_volume": 90, "target": "pc_b"}), "coloca o volume em 90")
    esperado = {"intent": "VOLUME", "params": {"acao": "set", "nivel_volume": nivel,
        "referencia_contextual": True, "target": "pc_b"}}
    owner = resolver_continuacao_operacional_confirmada(texto, estado, normalizar_texto=normalizar_texto)
    assert owner == esperado, "primeiro limite: quantidade não lida pelo owner contextual"
    candidato = detectar_intencao_deterministica_mente(texto, {
        "normalizar_texto": normalizar_texto, "mente_integrada_estado": estado})
    assert candidato == esperado


@pytest.mark.parametrize("alteracao", ["vencido", "futuro", "nan", "sem_confirmacao", "id", "params",
    "origem", "outro_dominio", "sem_contexto"])
def test_quantidade_por_extenso_nao_recupera_referente_desqualificado(alteracao):
    from mente_laylay.memoria_mental.contexto_imediato import resolver_continuacao_operacional_confirmada
    estado = _volume_confirmado_para_continuacao()
    if alteracao == "vencido": estado["ultima_acao_ts"] = time.time() - 301
    elif alteracao == "futuro": estado["ultima_acao_ts"] = time.time() + 100
    elif alteracao == "nan": estado["ultima_acao_ts"] = float("nan")
    elif alteracao == "sem_confirmacao": estado["ultima_acao_contrato"]["confirmado"] = False
    elif alteracao == "id": estado["ultima_acao_contrato"]["id_solicitacao"] = "outra"
    elif alteracao == "params": estado["ultima_acao_params"]["nivel_volume"] = 12
    elif alteracao == "origem": estado["ultima_acao_contrato"]["origem"] = "modelo"
    elif alteracao == "outro_dominio":
        estado = registrar_resultado_execucao(estado, ResultadoAcao(id_solicitacao="outro-alvo",
            intent="APP_OPEN", alvo="calculadora", status="aberto", executou=True, confirmado=True,
            origem="executor", params={"nome_app": "calculadora"}), "abre a calculadora")
    else: estado = estado_mental_inicial()
    texto = "coloca em quarenta"
    assert resolver_continuacao_operacional_confirmada(texto, estado, normalizar_texto=normalizar_texto) is None
    assert detectar_intencao_deterministica_mente(texto, {
        "normalizar_texto": normalizar_texto, "mente_integrada_estado": estado}) is None


@pytest.mark.parametrize("texto", [
    "não coloca em quarenta", "como eu faria para colocar em quarenta?",
    "ontem eu coloquei em quarenta", "se eu confirmar, coloca em quarenta",
    'o que significa "coloca em quarenta"?', "quarenta",
    "aumenta em dez", "aumenta dez", "coloca em quarenta minutos",
    "coloca em quarenta e onze", "coloca em quarenta e 5", "coloca em 40 e cinco",
    "coloca em quarenta vírgula cinco", "coloca em -5", "coloca em 5.5",
    "coloca em 4e1", "coloca em quarenta o brilho",
])
def test_literal_contextual_nao_empresta_autoridade_nem_reinterpreta_grandeza(texto):
    from mente_laylay.memoria_mental.contexto_imediato import resolver_continuacao_operacional_confirmada
    assert resolver_continuacao_operacional_confirmada(
        texto, _volume_confirmado_para_continuacao(), normalizar_texto=normalizar_texto) is None


@pytest.mark.parametrize("texto", [
    "coloca em quarenta e onze", "coloca em 5.5", "coloca em 5,5",
    "coloca em quarenta minutos", "deixa em quarenta db", "coloca em mil",
    "coloca em quarenta e 5", "coloca em 40 e cinco", "coloca 5.5",
])
@pytest.mark.parametrize("referente", ["vigente", "vencido", "outro_dominio", "ausente"])
def test_valor_invalido_nao_apaga_natureza_parametrica_nem_escolhe_outro_dominio(texto, referente):
    from mente_laylay.memoria_mental.contexto_imediato import resolver_continuacao_operacional_confirmada
    estado = _volume_confirmado_para_continuacao()
    if referente == "vencido": estado["ultima_acao_ts"] = time.time() - 301
    elif referente == "outro_dominio":
        estado = registrar_resultado_execucao(estado, ResultadoAcao(id_solicitacao="app-de-controle",
            intent="APP_OPEN", status="aberto", alvo="calculadora", executou=True, confirmado=True,
            origem="executor", params={"nome_app": "calculadora"}), "abre a calculadora")
    elif referente == "ausente": estado = estado_mental_inicial()
    assert resolver_continuacao_operacional_confirmada(texto, estado, normalizar_texto=normalizar_texto) is None
    assert detectar_intencao_deterministica_mente(texto, {
        "normalizar_texto": normalizar_texto, "mente_integrada_estado": estado}) is None, (
        "primeiro limite: rejeição quantitativa não pode produzir busca ou outro comando")


@pytest.mark.parametrize("texto", ["coloca em quarenta e onze", "coloca em 5.5", "coloca em quarenta minutos"])
def test_leitura_parametrica_invalida_nao_convoca_ia_para_inventar_outro_dominio(texto):
    from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    chamadas = []
    def inventar_busca(fonte):
        chamadas.append(fonte)
        return {"intent": "MUSIC_SEARCH", "params": {"query": "em quarenta"}}
    decisao, rota = resolver_intencao(texto, "teste", {
        "normalizar_texto": normalizar_texto, "turno_atual": classificar_modalidade_turno(texto),
        "detectar_intencao_deterministica": lambda _texto: None,
        "tentar_intencao_ai_primeiro": inventar_busca,
    })
    assert chamadas == [], "rejeição paramétrica não é permissão para buscar outro alvo"
    assert decisao is None and rota == "contexto_parametro_nao_resolvido"


@pytest.mark.parametrize("texto,consulta", [
    ('coloca "Em Quarenta e Onze"', "Em Quarenta e Onze"),
    ('coloca "Em 5.5"', "Em 5.5"),
    ("coloca a música quarenta minutos", "quarenta minutos"),
    ('toca a faixa "Quarenta e Onze"', "Quarenta e Onze"),
    ("coloca em um lugar ao sol", "em um lugar ao sol"),
    ("coloca em ponto morto", "em ponto morto"),
])
def test_protecao_de_valor_nao_classifica_titulo_ou_artigo_como_medida(texto, consulta):
    candidato = detectar_intencao_deterministica_mente(texto, {
        "normalizar_texto": normalizar_texto, "mente_integrada_estado": _volume_confirmado_para_continuacao()})
    assert candidato and candidato["intent"] == "MUSIC_SEARCH"
    assert candidato["params"]["query"] == consulta


def test_destino_absoluto_usa_volume_confirmado_apos_playlist_e_intervalo(monkeypatch):
    from mente_laylay.memoria_mental.contexto_imediato import resolver_continuacao_operacional_confirmada
    agora = time.time()
    estado = registrar_resultado_execucao(estado_mental_inicial(), ResultadoAcao(
        id_solicitacao="playlist-antes-do-ajuste", intent="PLAYLIST_PLAY", alvo="novidades",
        status="playlist_aberta", executou=True, confirmado=True, origem="executor",
        params={"nome_playlist": "novidades"}), "coloca a playlist novidades")
    estado = registrar_resultado_execucao(estado, ResultadoAcao(
        id_solicitacao="volume-70-confirmado", intent="VOLUME", status="volume_ajustado",
        executou=True, confirmado=True, origem="executor",
        params={"acao": "set", "nivel_volume": 70}), "deixa o volume em 70")
    assert estado["ultima_acao_params"]["nivel_volume"] == 70
    monkeypatch.setattr(time, "time", lambda: agora + 67)
    r = resolver_continuacao_operacional_confirmada(
        "aumenta para 100", estado, normalizar_texto=normalizar_texto)
    assert r and r["intent"] == "VOLUME"
    assert r["params"] == {"acao": "set", "nivel_volume": 100, "referencia_contextual": True}


@pytest.mark.parametrize("texto", [
    "aumenta em 10", "abaixa em 20", "aumenta 10", "diminui 20",
    "aumenta para 100 o brilho", "aumenta para 100 graus",
])
def test_variacao_ou_outro_parametro_nao_vira_destino_absoluto_volume(texto):
    from mente_laylay.memoria_mental.contexto_imediato import (
        texto_pede_ajuste_numerico_contextual, resolver_continuacao_operacional_confirmada,
    )
    assert not texto_pede_ajuste_numerico_contextual(texto)
    r = resolver_continuacao_operacional_confirmada(
        texto, _volume_confirmado_para_continuacao(), normalizar_texto=normalizar_texto)
    assert not r or not (r["params"].get("acao") == "set"), r


@pytest.mark.parametrize("alteracao", ["vencido", "sem_confirmacao", "outro_dominio", "sem_contexto"])
def test_destino_direcional_exige_referencia_qualificada(alteracao):
    from mente_laylay.memoria_mental.contexto_imediato import resolver_continuacao_operacional_confirmada
    estado = _volume_confirmado_para_continuacao()
    if alteracao == "vencido":
        estado["ultima_acao_ts"] = time.time() - 301
    elif alteracao == "sem_confirmacao":
        estado["ultima_acao_contrato"]["confirmado"] = False
    elif alteracao == "outro_dominio":
        estado = registrar_resultado_execucao(estado, ResultadoAcao(
            id_solicitacao="app-mais-recente", intent="APP_OPEN", status="aberto",
            alvo="calculadora", executou=True, confirmado=True, origem="executor",
            params={"nome_app": "calculadora"}), "abre a calculadora")
    else:
        estado = estado_mental_inicial()
    assert resolver_continuacao_operacional_confirmada(
        "aumenta para 100", estado, normalizar_texto=normalizar_texto) is None


@pytest.mark.parametrize("texto", [
    "não aumenta para 100", "como eu faria para aumentar para 100?",
    'o que significa "aumenta para 100"?', "ontem eu aumentei para 100",
])
def test_destino_numerico_sem_pedido_atual_nao_materializa_comando(texto):
    from mente_laylay.memoria_mental.contexto_imediato import resolver_continuacao_operacional_confirmada
    assert resolver_continuacao_operacional_confirmada(
        texto, _volume_confirmado_para_continuacao(), normalizar_texto=normalizar_texto) is None


@pytest.mark.parametrize("referencia", [
    {"tipo": "app", "alvo": "calculadora", "params": {"nome_app": "calculadora"}},
    {"tipo": "site", "alvo": "youtube", "params": {"alvo": "youtube"}},
    {"tipo": "playlist", "alvo": "rock", "params": {"nome_playlist": "rock"}},
    {"tipo": "arquivo", "alvo": "notas.txt", "params": {"caminho": "C:/temp/notas.txt"}},
])
@pytest.mark.parametrize("texto", [
    "abre o bloco de notas de novo", "abre o site github novamente",
    "coloca a playlist jazz outra vez", "abre firefox e deixa ele em foco de novo",
    "abre o arquivo dela de novo", "coloca uma musica dele", "fecha o arquivo dela",
])
def test_repeticao_com_alvo_nomeado_nao_herda_alvo_antigo(referencia, texto):
    # Não interpreta nem executa o novo alvo: deixa seu owner explícito agir.
    assert resolver_comando_acao_geral_contextual(texto, referencia) is None


@pytest.mark.parametrize("texto", [
    "abre ele de novo", "abre ele novamente", "abre esse app outra vez",
    "abre de novo", "abre ele e deixa em foco", "fecha ele",
    "fecha o programa que voce acabou de abrir",
])
def test_reuso_sem_alvo_novo_preserva_referencia_e_operacao(texto):
    r = resolver_comando_acao_geral_contextual(texto, {
        "tipo": "app", "alvo": "calculadora", "params": {"nome_app": "calculadora"}})
    assert r and r["params"]["nome_app"] == "calculadora"
    assert r["intent"] == ("CLOSE_APP" if texto.startswith("fecha") else "APP_OPEN")


@pytest.mark.parametrize("alteracao", ["nenhuma", "vencido", "nao_confirmado", "outro_dominio"])
def test_prioridade_de_continuacao_exige_referencia_vigente_e_pedido_direto(alteracao):
    from mente_laylay.memoria_mental import contexto_imediato
    resolver = getattr(contexto_imediato, "resolver_continuacao_operacional_confirmada", None)
    assert callable(resolver), "falta contrato compartilhado de precedência da continuidade"
    estado = _volume_confirmado_para_continuacao()
    if alteracao == "vencido": estado["ultima_acao_ts"] = time.time() - 301
    elif alteracao == "nao_confirmado": estado["ultima_acao_contrato"]["confirmado"] = None
    elif alteracao == "outro_dominio":
        estado = registrar_resultado_execucao(estado, ResultadoAcao(
            id_solicitacao="outro-dominio", intent="APP_OPEN", alvo="calculadora", status="aberto",
            executou=True, confirmado=True, origem="executor", params={"nome_app": "calculadora"}),
            "abre a calculadora")
    r = resolver("coloca em 40", estado, normalizar_texto=normalizar_texto)
    assert bool(r) is (alteracao == "nenhuma")


@pytest.mark.parametrize("texto", [
    "40", "como coloca em 40", "não coloca em 40", "se eu pedir, coloca em 40",
    '"coloca em 40" significa o quê?', "coloca a música adolescente de 40 anos",
    "coloca em 40 minutos", "me explica volume em 40",
])
def test_continuacao_confirmada_nao_empresta_autoridade_nem_troca_assunto(texto):
    from mente_laylay.memoria_mental import contexto_imediato
    resolver = getattr(contexto_imediato, "resolver_continuacao_operacional_confirmada", None)
    assert callable(resolver), "falta contrato compartilhado de precedência da continuidade"
    assert resolver(texto, _volume_confirmado_para_continuacao(), normalizar_texto=normalizar_texto) is None


def test_busca_musical_explicita_preserva_titulo_numerico_apos_volume():
    r = detectar_intencao_deterministica_mente("coloca a música adolescente de 40 anos", {
        "normalizar_texto": normalizar_texto, "mente_integrada_estado": _volume_confirmado_para_continuacao()})
    assert r and r["intent"] == "MUSIC_SEARCH"
    assert "adolescente de 40 anos" in r["params"]["query"]


@pytest.mark.parametrize("alteracao", ["vencido", "futuro", "nan", "id", "params", "sem_contexto"])
def test_ajuste_sem_vinculo_vigente_nao_cai_no_detector_de_titulo(alteracao):
    estado = _volume_confirmado_para_continuacao()
    if alteracao == "vencido": estado["ultima_acao_ts"] = time.time() - 301
    elif alteracao == "futuro": estado["ultima_acao_ts"] = time.time() + 100
    elif alteracao == "nan": estado["ultima_acao_ts"] = float("nan")
    elif alteracao == "id": estado["ultima_acao_contrato"]["id_solicitacao"] = "outra-ocorrencia"
    elif alteracao == "params": estado["ultima_acao_params"]["nivel_volume"] = 12
    else: estado = estado_mental_inicial()
    assert detectar_intencao_deterministica_mente("coloca em 40", {
        "normalizar_texto": normalizar_texto, "mente_integrada_estado": estado}) is None


@pytest.mark.parametrize("target", ["pc_a", "pc_b"])
@pytest.mark.parametrize("texto,nivel", [
    ("coloca em 40", 40), ("aumenta para 75", 75), ("diminui pra 25", 25),
])
def test_continuacao_preserva_destino_e_substitui_somente_nivel(target, texto, nivel):
    estado = registrar_resultado_execucao(estado_mental_inicial(), ResultadoAcao(
        id_solicitacao="volume-destino", intent="VOLUME", status="volume_ajustado",
        executou=True, confirmado=True, origem="executor",
        params={"acao": "set", "nivel_volume": 90, "target": target}), "coloca o volume em 90")
    r = detectar_intencao_deterministica_mente(texto, {
        "normalizar_texto": normalizar_texto, "mente_integrada_estado": estado})
    assert r == {"intent": "VOLUME", "params": {
        "acao": "set", "nivel_volume": nivel, "referencia_contextual": True, "target": target}}


def test_mesmo_owner_compartilhado_resolve_continuacao_em_outro_dominio():
    from mente_laylay.memoria_mental.contexto_imediato import resolver_continuacao_operacional_confirmada
    estado = registrar_resultado_execucao(estado_mental_inicial(), ResultadoAcao(
        id_solicitacao="app-continuacao", intent="APP_OPEN", alvo="calculadora", status="aberto",
        executou=True, confirmado=True, origem="executor", params={"nome_app": "calculadora"}),
        "abre a calculadora")
    r = resolver_continuacao_operacional_confirmada("fecha ele", estado, normalizar_texto=normalizar_texto)
    assert r and r["intent"] == "CLOSE_APP" and r["params"]["nome_app"] == "calculadora"
    assert r["params"]["referencia_contextual"] is True


def test_foco_conversacional_nao_apaga_identidade_da_operacao_confirmada():
    estado = _volume_confirmado_para_continuacao()
    slot = estado["continuidade_geral"]["dominios"]["sistema"]
    slot.update(evento="foco", origem="conversacional", id_solicitacao="", topico="VOLUME")
    r = detectar_intencao_deterministica_mente("coloca em 40", {
        "normalizar_texto": normalizar_texto, "mente_integrada_estado": estado})
    assert r and r["intent"] == "VOLUME" and r["params"]["nivel_volume"] == 40


@pytest.fixture(scope="module")
def continuacao_instalada():
    from scripts.analises.sonda_continuacao_operacional import coletar
    return coletar()


@pytest.mark.parametrize("indice", range(15))
def test_composicao_instalada_respeita_continuacao_sem_efeitos(continuacao_instalada, indice):
    r = continuacao_instalada
    assert r["fontes_estaveis"] and all(r["instalacao"].values())
    caso = r["resultados"][indice]
    assert caso["primeira_fronteira_red"] == "", caso
    assert caso["fixture_receipt"] is True
    assert not r["efeitos_externos_executados"] and not r["modelo_real_consultado"]
    assert not r["runtime_main_validado"] and not r["voz_validada"]
    if caso["esperado"]["intent"] == "VOLUME":
        assert caso["decisao"]["params"]["nivel_volume"] == caso["esperado"]["nivel_volume"]
        assert caso["porta_modelo_consultada"] == 0


@pytest.mark.parametrize("ident", ["invalido_composto", "invalido_decimal", "invalido_decimal_virgula",
    "invalido_unidade", "invalido_misto", "invalido_sem_relacao", "invalido_vencido", "invalido_nao_confirmado"])
def test_composicao_instalada_nao_resolve_nem_admite_propostas_para_quantidade_invalida(continuacao_instalada, ident):
    caso = next(c for c in continuacao_instalada["resultados"] if c["id"] == ident)
    assert not caso["primeira_fronteira_red"], caso
    assert caso["decisao"] is None and caso["porta_modelo_consultada"] == 0
    admissao = caso["admissao_quantitativa"]
    assert admissao["comandos"] == [] and len(admissao["rejeitados"]) == 3
    assert not continuacao_instalada["efeitos_externos_executados"]


@pytest.mark.parametrize("ident", ["conector_midia", "conector_iot", "conector_app", "conector_volume",
    "conector_site", "conector_literal", "conector_negacao", "conector_pergunta", "conector_condicao", "conector_capacidade"])
def test_conector_discursivo_no_detector_coordenador_e_admissao_instalados(continuacao_instalada, ident):
    r = continuacao_instalada
    caso = next(c for c in r["resultados"] if c["id"] == ident)
    assert r["fontes_estaveis"] and all(r["instalacao"].values())
    assert not caso["primeira_fronteira_red"]
    admissao = caso["admissao_quantitativa"]
    if caso["esperado"]["intent"]:
        assert caso["turno"]["autoriza_execucao"] is True
        assert admissao["comandos"] == [caso["decisao"]]
        if ident == "conector_literal":
            assert caso["decisao"]["params"]["query"] == "E Hoje"
    else:
        assert caso["turno"]["autoriza_execucao"] is False
        assert caso["decisao"] is None
        assert admissao["comandos"] == [] and len(admissao["rejeitados"]) == 3
    assert not r["runtime_main_validado"] and not r["efeitos_externos_executados"]


@pytest.mark.parametrize("ident", ["conector_elipse", "conector_destino", "conector_elipse_vencida", "conector_invalido_decimal"])
def test_elipse_com_conector_instalada_nao_empresta_referente_vencido_nem_muda_dominio(continuacao_instalada, ident):
    r = continuacao_instalada
    caso = next(c for c in r["resultados"] if c["id"] == ident)
    assert not caso["primeira_fronteira_red"]
    if caso["esperado"]["intent"]:
        assert caso["decisao"]["intent"] == "VOLUME"
        assert caso["decisao"]["params"]["nivel_volume"] == caso["esperado"]["nivel_volume"]
        assert caso["admissao_quantitativa"]["comandos"] == [caso["decisao"]]
    else:
        assert caso["decisao"] is None
        assert caso["admissao_quantitativa"]["comandos"] == []
        assert len(caso["admissao_quantitativa"]["rejeitados"]) == 3
    assert not caso["porta_modelo_consultada"]
    assert not r["efeitos_externos_executados"]


def test_falha_de_audio_no_runtime_instalado_nao_aciona_voz_local_implicita(continuacao_instalada):
    politica = continuacao_instalada["politica_voz_instalada"]
    assert politica["metodo_instalado"] is True
    assert politica["fallback_local_permitido"] is False
    assert politica["sucesso_audio"] is False and politica["chamadas_voz_local"] == 0
    assert politica["falhas"] == [{"dominio": "tts", "evento": "falha_audio",
        "fallback": "texto_preservado_sem_troca_de_voz"}]
    assert politica["sintese_real"] is False and politica["reproducao_fisica"] is False


def test_contraprovada_precedencia_no_detector_e_necessaria_mesmo_com_owner_contextual():
    from scripts.analises.sonda_continuacao_operacional import coletar
    r = coletar(contraprova_prioridade=True)
    assert r["fontes_estaveis"] and all(r["instalacao"].values())
    relato = r["resultados"][0]
    assert relato["decisao"] == {"intent": "MUSIC_SEARCH", "params": {"query": "em 40"}}
    assert relato["primeira_fronteira_red"] == "coordenador_divergiu_do_vinculo"
    assert not r["efeitos_externos_executados"]


@pytest.mark.parametrize("ident", ["agenda_parametro", "agenda_outro_dominio"])
def test_agendamento_instalado_admite_mesmo_efeito_sem_emprestar_rota_como_autoridade(continuacao_instalada, ident):
    r = continuacao_instalada
    assert r["fontes_estaveis"] and all(r["instalacao"].values())
    caso = next(c for c in r["resultados"] if c["id"] == ident)
    assert not caso["primeira_fronteira_red"], caso["primeira_fronteira_red"]
    assert caso["decisao"]["intent"] == caso["detector"]["intent"] == "AGENDAR_ACAO"
    assert caso["decisao"]["params"]["rota_original"] == "deterministico-explicito"
    assert caso["detector"]["params"]["rota_original"] == "deterministico"
    assert caso["admissao_quantitativa"]["comandos"] == [caso["decisao"]]
    controles = caso["controles_agendamento"]
    assert {c["nome"] for c in controles} == {"prazo", "acao", "alvo", "destino", "extra", "substituir", "rota_malformada"}
    assert all(c["correto"] for c in controles)
    assert all(c["validacao"]["comandos"] == [caso["decisao"]] for c in controles)
    assert all(len(c["validacao"]["rejeitados"]) == 2 for c in controles)
    assert not caso["porta_modelo_consultada"]
    assert not r["efeitos_externos_executados"] and not r["modelo_real_consultado"]
    assert not r["runtime_main_validado"] and not r["voz_validada"]


@pytest.mark.parametrize("texto", ["coloca em 40", "aumenta para 100", "reduz para 20",
    "coloca em quarenta", "aumenta para cem", "deixa em vinte e dois"])
def test_fallback_ai_nao_materializa_ajuste_sem_referente_como_titulo(texto):
    from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    chamadas = []
    def proposta_sem_referente(_texto):
        chamadas.append(_texto)
        return {"intent": "MUSIC_SEARCH", "params": {"query": "em 40"}}
    decisao, rota = resolver_intencao(texto, "teste", {
        "normalizar_texto": normalizar_texto,
        "turno_atual": classificar_modalidade_turno(texto),
        "detectar_intencao_deterministica": lambda *_: None,
        "tentar_intencao_ai_primeiro": proposta_sem_referente,
    })
    assert chamadas == [], "fallback não pode inventar o referente ausente"
    assert decisao is None and rota == "contexto_parametro_nao_resolvido"


@pytest.mark.parametrize("porta", ["resolver", "resolver_acao_geral"])
@pytest.mark.parametrize("texto,nivel", [("coloca em quarenta", 40), ("coloca em 40%", 40),
    ("coloca em -5", None), ("coloca em 5.5", None), ("aumenta para cem?", 100)])
def test_portas_contextuais_preservam_fonte_para_quantidade(porta, texto, nivel):
    from types import SimpleNamespace
    from mente_laylay.memoria_mental.contexto_imediato import ContextoImediatoRuntime
    estado = SimpleNamespace(mental=_volume_confirmado_para_continuacao(), musica_get=lambda _k: "")
    runtime = ContextoImediatoRuntime(estado_runtime_getter=lambda: estado, servicos_iniciais={
        "_normalizar_texto_com_apelidos": normalizar_texto,
        "_foco_vivo_atual": lambda **_k: {}, "_alvo_corrigido_atual": lambda: "",
        "_estrutura_arquivo_recente": lambda *_a: {},
    })
    candidato = getattr(runtime, porta)(texto)
    if nivel is None:
        assert candidato is None
    else:
        assert candidato and candidato["intent"] == "VOLUME"
        assert candidato["params"]["nivel_volume"] == nivel


@pytest.fixture(scope="module")
def contexto_cruzado_instalado():
    from scripts.analises.sonda_continuacao_operacional import coletar
    return coletar(painel_contexto=True, sondar_executor=True)


@pytest.mark.parametrize("indice", range(57))
def test_pedido_atual_e_reuso_no_painel_instalado(contexto_cruzado_instalado, indice):
    r = contexto_cruzado_instalado
    assert r["fontes_estaveis"] and all(r["instalacao"].values())
    caso = r["resultados"][indice]
    assert not caso["primeira_fronteira_red"], caso
    assert not r["modelo_real_consultado"] and not r["efeitos_externos_executados"]
    assert not r["runtime_main_validado"] and caso["fixture_receipt"]


def test_nome_de_playlist_atual_nao_e_substituido_por_playlist_anterior(contexto_cruzado_instalado):
    caso = next(c for c in contexto_cruzado_instalado["resultados"] if c["id"] == "playlist_novo_alvo")
    assert caso["decisao"]["intent"] == "PLAYLIST_PLAY"
    assert caso["decisao"]["params"]["nome_playlist"] == "jazz"


def test_contexto_volume_nao_sobrepoe_dominio_de_pedido_musical(contexto_cruzado_instalado):
    caso = next(c for c in contexto_cruzado_instalado["resultados"] if c["id"] == "volume_novo_assunto")
    assert caso["decisao"]["intent"] == "MUSIC_SEARCH"
    assert caso["decisao"]["params"]["query"] == "maximo respeito"


@pytest.mark.parametrize("ident", [
    "volume_novo_assunto", "musica_tipo", "musica_tipo_interno", "musica_literal",
    "musica_literal_extremo", "musica_literal_favorita", "musica_literal_som",
    "musica_nome_mudo", "musica_nome_pausa", "musica_nome_despausa", "musica_nome_volume",
])
def test_argumento_atravessa_executor_instalado_sem_reinterpretacao_e_sem_sucesso_falso(contexto_cruzado_instalado, ident):
    r = contexto_cruzado_instalado
    assert r["fontes_estaveis"] and all(r["instalacao"].values())
    caso = next(c for c in r["resultados"] if c["id"] == ident)
    execucao = caso["execucao_consulta"]
    assert execucao["executor_instalado_chamado"]
    assert execucao["consultas"] == [caso["decisao"]["params"]["query"]]
    assert execucao["normalizacoes_fala"] == []
    assert execucao["retorno"] is False and execucao["conclusoes"]
    assert execucao["busca_externa_substituida"] and not execucao["efeito_confirmado"]
    assert all(c["status"] == "musica_nao_resolvida" and c["executou"] is False
               and c["confirmado"] is False for c in execucao["conclusoes"])


def _pendencia(estado: dict) -> PendenciaAcaoRuntime:
    def atualizar(mutador):
        novo = mutador(dict(estado))
        estado.clear()
        estado.update(novo)
        return dict(estado)

    return PendenciaAcaoRuntime(
        estado_getter=lambda: estado,
        estado_atualizar=atualizar,
        log=lambda *_args: None,
    )


def test_fecha_programa_que_acabou_de_abrir_resolve_ultima_janela() -> None:
    estado = {
        "ultima_acao_intent": "APP_OPEN",
        "ultima_acao_params": {"nome_app": "bloco de notas"},
        "ultimo_app_janela": "bloco de notas",
    }

    assert resolver_comando_janela_contextual(
        "fecha o programa que voce acabou de abrir",
        mente_integrada_estado=estado,
    ) == {
        "intent": "CLOSE_APP",
        "params": {
            "nome_app": "bloco de notas",
            "referencia_contextual": True,
        },
    }


def test_detector_nao_trata_referencia_de_janela_como_nome_literal() -> None:
    assert detectar_fechar_alvo(
        "fecha o programa que voce acabou de abrir",
        params_cb=lambda **params: params,
        sites_diretos=set(),
        apps_map={},
    ) is None


def test_roteador_completo_bloqueia_iot_negado_mesmo_com_detector_permissivo() -> None:
    chamadas = []

    def detector(texto, _estado):
        chamadas.append(texto)
        return {"intent": "IOT_CONTROL", "params": {"acao": "desligar", "alvo": "lampada_quarto"}}

    ctx = {
        "detectar_intencao_iot": detector,
        "normalizar_texto": lambda texto: str(texto).casefold().strip(),
        "mente_integrada_estado": {},
    }
    assert detectar_intencao_deterministica_mente("não desliga a luz", ctx) is None
    assert chamadas


def test_roteador_completo_bloqueia_pergunta_sobre_como_controlar_iot() -> None:
    ctx = {
        "detectar_intencao_iot": lambda *_: {
            "intent": "IOT_CONTROL",
            "params": {"acao": "desligar", "alvo": "lampada_quarto"},
        },
        "normalizar_texto": lambda texto: str(texto).casefold().strip(),
        "mente_integrada_estado": {},
    }
    assert detectar_intencao_deterministica_mente(
        "como eu faria para desligar a luz?", ctx
    ) is None


def test_nome_da_faixa_resolve_pendencia_de_musica_sem_alvo() -> None:
    falas = []
    execucoes = []
    estado: dict = {}
    runtime = MusicaConversacionalRuntime(
        estado_mental_getter=lambda: estado,
        normalizar_texto=lambda texto: str(texto).casefold().strip(),
        falar=lambda fala, *_: falas.append(fala),
        registrar_mente_curta=lambda *_args, **_kwargs: None,
        executar_intencao=lambda resultado, texto: execucoes.append((resultado, texto)) or True,
        registrar_resultado_execucao=lambda *_args, **_kwargs: None,
        pendencia_runtime=_pendencia(estado),
    )

    assert runtime.responder_pedido_direcao("coloca uma música") is True
    assert runtime.processar_confirmacao("Remember The Time") is True
    assert execucoes[-1][0] == {
        "intent": "MUSIC_SEARCH",
        "params": {"query": "Remember The Time", "origem": "continuacao_busca"},
    }


def test_vontade_natural_de_ouvir_musica_cria_pendencia_sem_inventar_playlist() -> None:
    falas = []
    execucoes = []
    estado: dict = {}
    runtime = MusicaConversacionalRuntime(
        estado_mental_getter=lambda: estado,
        normalizar_texto=lambda texto: str(texto).casefold().strip(),
        falar=lambda fala, *_: falas.append(fala),
        registrar_mente_curta=lambda *_args, **_kwargs: None,
        executar_intencao=lambda resultado, texto: execucoes.append((resultado, texto)) or True,
        registrar_resultado_execucao=lambda *_args, **_kwargs: None,
        pendencia_runtime=_pendencia(estado),
    )

    assert runtime.responder_pedido_direcao("eu queria ouvir uma música na verdade") is True
    assert execucoes == []
    assert "qual" in falas[-1].casefold()

    assert runtime.processar_confirmacao("Remember The Time") is True
    assert execucoes[-1][0] == {
        "intent": "MUSIC_SEARCH",
        "params": {"query": "Remember The Time", "origem": "continuacao_busca"},
    }


def test_novo_comando_iot_nao_vira_titulo_de_musica_pendente() -> None:
    execucoes = []
    estado: dict = {}
    runtime = MusicaConversacionalRuntime(
        estado_mental_getter=lambda: estado,
        normalizar_texto=lambda texto: str(texto).casefold().strip(),
        falar=lambda *_: None,
        registrar_mente_curta=lambda *_args, **_kwargs: None,
        executar_intencao=lambda resultado, texto: execucoes.append((resultado, texto)) or True,
        registrar_resultado_execucao=lambda *_args, **_kwargs: None,
        pendencia_runtime=_pendencia(estado),
    )
    runtime.responder_pedido_direcao("coloca uma música")
    assert runtime.processar_confirmacao("liga a luz") is False
    assert execucoes == []


def test_agradecimento_nao_vira_titulo_de_musica_pendente() -> None:
    execucoes = []
    estado: dict = {}
    runtime = MusicaConversacionalRuntime(
        estado_mental_getter=lambda: estado,
        normalizar_texto=lambda texto: str(texto).casefold().strip(),
        falar=lambda *_: None,
        registrar_mente_curta=lambda *_args, **_kwargs: None,
        executar_intencao=lambda resultado, texto: execucoes.append((resultado, texto)) or True,
        registrar_resultado_execucao=lambda *_args, **_kwargs: None,
        pendencia_runtime=_pendencia(estado),
    )
    runtime.responder_pedido_direcao("coloca uma música")

    for agradecimento in ("obrigado lay", "valeu Laylay", "perfeito"):
        assert runtime.processar_confirmacao(agradecimento) is False
    assert execucoes == []


def test_execucao_musical_confirmada_invalida_copia_local_da_pendencia() -> None:
    estado = {}
    execucoes = []
    runtime = MusicaConversacionalRuntime(
        estado_mental_getter=lambda: estado,
        normalizar_texto=lambda texto: str(texto).casefold().strip(),
        falar=lambda *_: None,
        registrar_mente_curta=lambda *_args, **_kwargs: None,
        executar_intencao=lambda resultado, texto: execucoes.append((resultado, texto)) or True,
        registrar_resultado_execucao=lambda *_args, **_kwargs: None,
        pendencia_runtime=_pendencia(estado),
    )
    runtime.responder_pedido_direcao("coloca uma música")
    estado.update({
        "ultima_acao_intent": "MUSIC_SEARCH",
        "ultima_acao_ts": time.time(),
        "ultima_acao_contrato": {
            "intent": "MUSIC_SEARCH",
            "executou": True,
            "confirmado": True,
        },
    })

    assert runtime.processar_confirmacao("obrigado lay") is False
    assert estado.get(CHAVE_PENDENCIA_ACAO, {}) == {}
    assert execucoes == []


def test_mencao_iot_sem_autorizacao_delega_fala_sem_alcancar_roteador() -> None:
    falas = []
    chamadas_roteador = []
    namespace = {
        "falar_com_lipsync": lambda fala, *_: falas.append(fala),
        "detectar_intencao_deterministica": lambda texto: chamadas_roteador.append(texto),
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    # C13: esta porta é dona do veto, não de uma resposta fixa sobre a luz.
    # A conclusão observável é feita pelo fluxo de conversa, não por tratado=True.
    assert runtime.processar_prioritarios("como eu faria para desligar a luz?") is False
    assert falas == []
    assert chamadas_roteador == []

    assert runtime.processar_prioritarios("não desliga a luz") is False
    assert falas == []
    assert chamadas_roteador == []

    assert runtime.processar_prioritarios(
        "Talvez fosse legal desligar a luz."
    ) is False
    assert falas == []
    assert chamadas_roteador == []


def test_recusa_musical_e_instrucao_de_exclusao_nao_caem_na_llm() -> None:
    falas = []
    bloqueios = []
    namespace = {
        "falar_com_lipsync": lambda fala, *_: falas.append(fala),
        "_bloquear_playlist_temporariamente": lambda segundos: bloqueios.append(segundos),
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("Não coloca música agora.") is True
    assert falas[-1] == "Pode deixar, não vou tocar nada agora."
    assert bloqueios == [600.0]

    assert runtime.processar_prioritarios(
        "Como eu faria para apagar uma pasta?"
    ) is True
    assert "envio para a lixeira" in falas[-1]
    assert "restaurar" in falas[-1]
    assert "permanente" not in falas[-1]


def test_coordenador_nao_classifica_segmento_iot_amputado_da_fala_original() -> None:
    assert executar_fluxo_intencao(
        "desligar a luz",
        "pre-ia",
        {},
        texto_original="como eu faria para desligar a luz?",
    ) is False
