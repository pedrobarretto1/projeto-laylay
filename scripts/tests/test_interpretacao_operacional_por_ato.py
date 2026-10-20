"""Dados por ato sobrevivem ao transporte, sem virarem autoridade ou fatos."""
from copy import deepcopy
import json

import pytest

from mente_laylay.autonomia.processamento_resposta_ia import extrair_leitura_semantica_da_ia
from mente_laylay.cognicao.leitura_semantica_turno import normalizar_leitura_semantica
from mente_laylay.cognicao.contratos_turno import ContratoInterpretacaoAto, SnapshotComandoIA


def _prompt_para_turno(texto, *, candidato=True):
    from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT
    turno = classificar_modalidade_turno(texto)
    estado = {"turno_atual": turno}
    runtime = ContextoPromptRuntime(memoria_sqlite=None, resumo_mente_integrada=lambda _: "",
        formatar_playlists=lambda: "", get_status_humor_prompt=lambda: "",
        base_system_prompt=BASE_SYSTEM_PROMPT, estado_getter=lambda: estado,
        interpretacao_por_ato_ativa=candidato)
    return runtime, estado


@pytest.mark.parametrize("texto", [
    "abre o aplicativo Calculadora", "liga a luz do quarto",
    "toca a música Som do Silêncio", 'cria o arquivo "Resultado Final.md"',
    "abre o site example.test/A", "abre o aplicativo Calculadora; não liga a luz",
])
def test_projecao_principal_pede_interpretacao_vinculada_sem_mudar_historico_ou_autoridade(texto):
    runtime, estado = _prompt_para_turno(texto)
    antes = deepcopy(estado)
    mensagens = [{"role": "system", "content": runtime.base_system_prompt},
                 {"role": "user", "content": texto}]
    historico = deepcopy(mensagens)
    pacote = runtime.preparar_envio_modelo(mensagens, turno_id=estado["turno_atual"]["id"])
    instrucoes = [m["content"] for m in pacote.mensagens if m["role"] == "system"]
    assert any("INTERPRETAÇÃO POR ATO" in m for m in instrucoes), "primeira fronteira: produtor só recebe rótulos"
    assert pacote.reserva_saida_tokens >= 768, "formato maior não pode herdar teto curto da fala"
    assert pacote.mensagens[-1] == mensagens[-1]
    assert estado == antes and mensagens == historico
    from mente_laylay.integracao.registro_conversa_llm import registrar_preparacao_conversa
    registro = registrar_preparacao_conversa(runtime)
    copia = registro.preparar_envio_modelo(mensagens, turno_id=estado["turno_atual"]["id"])
    assert copia.reserva_saida_tokens == pacote.reserva_saida_tokens
    assert copia.mensagens == pacote.mensagens


@pytest.mark.parametrize("controle", ["conversa", "outra_fala", "outra_ocorrencia", "sem_frame"])
def test_instrucao_operacional_nao_vaza_para_conversa_ou_frame_alheio(controle):
    texto = "oi Laylay" if controle == "conversa" else "abre o aplicativo Calculadora"
    runtime, estado = _prompt_para_turno(texto)
    turno_id = estado["turno_atual"]["id"]
    if controle == "outra_fala":
        texto = "abre o aplicativo Opera"
    elif controle == "outra_ocorrencia":
        turno_id = "outra"
    elif controle == "sem_frame":
        estado.clear()
    mensagens = [{"role": "user", "content": texto}]
    pacote = runtime.preparar_envio_modelo(mensagens, turno_id=turno_id)
    if controle == "conversa":
        # A autoria agora exige suporte também em conversa; o contrato de
        # interpretação operacional continua sem vazar para este caso.
        assert not any("INTERPRETAÇÃO POR ATO" in m.get("content", "") for m in pacote.mensagens)
        assert pacote.mensagens[-1] == mensagens[-1]
        assert "suporte_proposicoes" in pacote.contrato_saida.response_format["json_schema"]["schema"]["required"]
    else:
        assert list(pacote.mensagens) == mensagens
        assert getattr(pacote, "reserva_saida_tokens", 0) == 0


def test_candidato_de_emissao_nao_altera_protocolo_diario_por_padrao():
    texto = "abre o aplicativo Calculadora"
    runtime, estado = _prompt_para_turno(texto, candidato=False)
    mensagens = [{"role": "user", "content": texto}]
    pacote = runtime.preparar_envio_modelo(mensagens, turno_id=estado["turno_atual"]["id"])
    assert pacote.mensagens[-1] == mensagens[-1]
    assert not any("INTERPRETAÇÃO POR ATO" in m.get("content", "") for m in pacote.mensagens)
    assert "leitura_turno" not in pacote.contrato_saida.response_format["json_schema"]["schema"]["required"]
    assert "suporte_proposicoes" in pacote.contrato_saida.response_format["json_schema"]["schema"]["required"]


def proposta_ato(texto, trecho, *, operacao="abrir", tipo="app", alvo="Calculadora", dependencias=()):
    inicio = texto.index(trecho)
    return {
        "tipo": "pedido_acao", "conteudo": trecho,
        "interpretacao": {
            "texto_original": trecho, "intervalo": [inicio, inicio + len(trecho)],
            "operacao": operacao, "tipo_recurso": tipo, "alvo": alvo,
            "parametros": {}, "destino": "pc_a", "referencias": [],
            "condicao": "", "dependencias": list(dependencias),
        },
    }


@pytest.mark.parametrize("forma", ["normalizador", "envelope_objeto", "envelope_lista"])
@pytest.mark.parametrize("trecho,operacao,tipo,alvo", [
    ("abre o aplicativo Calculadora", "abrir", "app", "Calculadora"),
    ("liga a luz do quarto", "ligar", "iot", "luz do quarto"),
    ("toca a música Som do Silêncio", "reproduzir", "musica", "Som do Silêncio"),
    ('cria o arquivo "Resultado Final.md"', "criar", "arquivo", "Resultado Final.md"),
    ("abre o site example.test/A", "abrir", "site", "example.test/A"),
])
def test_interpretacao_por_ato_nao_e_descartada_ou_convertida_em_rotulo(forma, trecho, operacao, tipo, alvo):
    texto = "Por favor, " + trecho
    ato = proposta_ato(texto, trecho, operacao=operacao, tipo=tipo, alvo=alvo)
    dados = {"atos": [ato], "modalidade_geral": "comando"}
    original = deepcopy(dados)
    if forma == "normalizador":
        leitura = normalizar_leitura_semantica(dados, texto=texto)
    else:
        leitura_turno = dados if forma == "envelope_objeto" else [ato]
        bruto = json.dumps({"fala": "Proposta apenas.", "leitura_turno": leitura_turno, "comandos": []})
        # Controle: o transporte JSON preservou os campos antes do decoder.
        assert json.loads(bruto)["leitura_turno"] == leitura_turno
        leitura = extrair_leitura_semantica_da_ia(bruto, texto)
    assert leitura["atos"][0]["tipo"] == "pedido_acao", "primeira fronteira: objeto de ato convertido em texto"
    interpretacao = leitura["atos"][0].get("interpretacao")
    assert interpretacao, "primeira fronteira: interpretação por ato perdida na normalização"
    assert leitura["fonte_textual"] == texto
    for campo, valor in ato["interpretacao"].items():
        assert interpretacao[campo] == valor
    assert interpretacao["indice_ato"] == 0
    assert interpretacao["autoriza_execucao"] is False
    assert interpretacao["comprova_efeito"] is False
    assert dados == original


def test_dados_independentes_parametros_e_referencias_nao_sao_um_operacional_global():
    texto = "abre o aplicativo Calculadora; deixa ela à esquerda; não liga a luz"
    a = proposta_ato(texto, "abre o aplicativo Calculadora")
    b = proposta_ato(texto, "deixa ela à esquerda", operacao="posicionar", alvo="", dependencias=[0])
    b["interpretacao"].update(referencias=["ela"], parametros={"lado": "esquerda"})
    c = proposta_ato(texto, "não liga a luz", operacao="ligar", tipo="iot", alvo="luz")
    c["tipo"] = "recusa"
    leitura = normalizar_leitura_semantica({"atos": [a, b, c]}, texto=texto)
    interpretacoes = [ato.get("interpretacao") for ato in leitura["atos"]]
    assert all(interpretacoes), "nenhum ato deve herdar a operação global"
    assert [i["indice_ato"] for i in interpretacoes] == [0, 1, 2]
    assert interpretacoes[1]["alvo"] == "" and interpretacoes[1]["referencias"] == ["ela"]
    assert interpretacoes[1]["dependencias"] == [0]
    assert all(i["autoriza_execucao"] is False for i in interpretacoes)


@pytest.mark.parametrize("texto,trecho", [
    ("abre o aplicativo Calculadora", "abre o aplicativo Calculadora"),
    ("por favor, liga a luz do quarto", "liga a luz do quarto"),
    ('cria o arquivo "Resumo.md"', 'cria o arquivo "Resumo.md"'),
    ("abre\t o aplicativo\nCalculadora", "abre\t o aplicativo\nCalculadora"),
])
def test_host_vincula_literal_unico_sem_exigir_contagem_de_caracteres_da_llm(texto, trecho):
    ato = proposta_ato(texto, trecho)
    ato["interpretacao"].pop("intervalo")
    leitura = normalizar_leitura_semantica({"atos": [ato]}, texto=texto)
    dados = leitura["atos"][0].get("interpretacao")
    assert dados, "primeira fronteira: literal inequívoco exige coordenada adivinhada pela LLM"
    assert dados["intervalo"] == [texto.index(trecho), texto.index(trecho) + len(trecho)]
    assert dados["autoriza_execucao"] is False and dados["comprova_efeito"] is False


@pytest.mark.parametrize("texto,trecho,intervalo", [
    ("abre; abre", "abre", None), ("ababa", "aba", None),
    ("Abre", "abre", None), ("abre", "fecha", None),
    ("abre", "abre", [0, 3]), ("abre", "abre", []),
])
def test_ancora_literal_nao_corrige_coordenada_falsa_nem_desambigua_repeticao(texto, trecho, intervalo):
    ato = proposta_ato("prefixo " + trecho, trecho)
    if intervalo is None:
        ato["interpretacao"].pop("intervalo")
    else:
        ato["interpretacao"]["intervalo"] = intervalo
    leitura = normalizar_leitura_semantica({"atos": [ato]}, texto=texto)
    assert not leitura["atos"][0].get("interpretacao")
    assert leitura["problemas_interpretacao"]


@pytest.mark.parametrize("alterar", [
    {"texto_original": "abre o Opera"}, {"intervalo": [True, 20]},
    {"intervalo": [-1, 20]}, {"intervalo": [0, 999]},
    {"dependencias": [0]}, {"dependencias": [True]},
    {"dependencias": [1]}, {"referencias": "ela"},
    {"parametros": {"valor": float("nan")}}, {"parametros": {"lado": (1, 2)}},
    {"autoriza_execucao": True}, {"confirmado": True},
])
def test_proposta_malformada_nao_recebe_vinculo_canonico(alterar):
    texto = "abre o aplicativo Calculadora"
    ato = proposta_ato(texto, texto)
    ato["interpretacao"].update(alterar)
    leitura = normalizar_leitura_semantica({"atos": [ato]}, texto=texto)
    assert not leitura["atos"][0].get("interpretacao")
    assert leitura.get("problemas_interpretacao"), "falha de contrato não deve desaparecer silenciosamente"
    assert leitura["somente_observacao"] is True


def test_rotulos_legados_nao_inventam_operacao_ou_trecho_literal():
    leitura = extrair_leitura_semantica_da_ia(json.dumps({"leitura_turno": ["pedido_acao", "recusa"]}), "abre; não liga")
    assert [a["tipo"] for a in leitura["atos"]] == ["pedido_acao", "recusa"]
    assert all("interpretacao" not in a for a in leitura["atos"])
    assert leitura["operacional"]["autoriza_execucao"] is False


def test_snapshot_isola_entrada_e_copias_sem_alterar_alvo_parametro_ou_autoridade():
    texto = 'abre o aplicativo "Arquivo Vivo"'
    dados = proposta_ato(texto, texto, alvo="Arquivo Vivo")["interpretacao"]
    dados["parametros"] = {"filtro": {"nomes": ["Arquivo Vivo"]}}
    contrato = ContratoInterpretacaoAto(0, texto, "llm_principal", SnapshotComandoIA(dados))
    dados["parametros"]["filtro"]["nomes"].append("Outro")
    copia = contrato.como_dict()
    copia["alvo"] = "Outro"
    copia["parametros"]["filtro"]["nomes"].clear()
    copia["autoriza_execucao"] = True
    intacto = contrato.como_dict()
    assert intacto["alvo"] == "Arquivo Vivo"
    assert intacto["parametros"] == {"filtro": {"nomes": ["Arquivo Vivo"]}}
    assert intacto["autoriza_execucao"] is False


def test_literal_longo_com_espacos_url_e_caixa_usa_fonte_integral_nao_resumo():
    trecho = 'abre  o site "https://example.test/A?x=1&y=2"'
    texto = "contexto " * 65 + trecho
    leitura = normalizar_leitura_semantica({"atos": [proposta_ato(texto, trecho, tipo="site")]}, texto=texto)
    proposta = leitura["atos"][0]["interpretacao"]
    assert proposta["intervalo"][0] > 500
    assert proposta["texto_original"] == trecho
    assert leitura["fonte_textual"][slice(*proposta["intervalo"])] == trecho
    assert len(leitura["texto"]) <= 500
    assert leitura["cobertura_interpretacao"] == "parcial"


@pytest.mark.parametrize("modo", ["sobreposicao", "invertido", "dependencia_sem_vinculo", "referencia_inventada"])
def test_relacoes_invalidas_nao_emprestam_vinculo_de_outro_ato(modo):
    texto = "abre o aplicativo Calculadora; deixa ela à esquerda"
    a = proposta_ato(texto, "abre o aplicativo Calculadora")
    b = proposta_ato(texto, "deixa ela à esquerda", dependencias=[0])
    if modo == "sobreposicao":
        b["interpretacao"].update(intervalo=a["interpretacao"]["intervalo"], texto_original=a["interpretacao"]["texto_original"])
    elif modo == "invertido":
        a, b = b, a
        a["interpretacao"]["dependencias"] = []
    elif modo == "dependencia_sem_vinculo":
        a.pop("interpretacao")
    else:
        b["interpretacao"]["referencias"] = ["aquele arquivo"]
    leitura = normalizar_leitura_semantica({"atos": [a, b]}, texto=texto)
    assert not leitura["atos"][1].get("interpretacao")
    assert leitura["problemas_interpretacao"]


def test_falha_em_um_ato_nao_elimina_ou_fabrica_interpretacao_no_outro():
    texto = "abre o aplicativo Calculadora; liga a luz"
    a = proposta_ato(texto, "abre o aplicativo Calculadora")
    a["interpretacao"]["intervalo"] = [0, 9999]
    b = proposta_ato(texto, "liga a luz", operacao="ligar", tipo="iot", alvo="luz")
    leitura = normalizar_leitura_semantica({"atos": [a, b]}, texto=texto)
    assert not leitura["atos"][0].get("interpretacao")
    assert leitura["atos"][1]["interpretacao"]["indice_ato"] == 1
    assert leitura["problemas_interpretacao"][0]["indice_ato"] == 0
