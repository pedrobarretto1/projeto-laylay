from mente_laylay.cognicao.identidade_conversacional import (
    ajustar_autorreferencia_assistente,
    analisar_identidade_turno,
    remover_vocativo_laylay,
    resumo_identidade_turno,
)
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.memoria_mental.contexto_integrado import resumo_mente_integrada_para_prompt
import time
from mente_laylay.emocoes.leitura_usuario import analisar_funcao_comunicativa
from mente_laylay.personalidade.conversa_natural import (
    _fala_extrapola_fatos_disponiveis,
    classificar_conversa_curta_local,
    construir_fala_conversa,
    parece_elogio_ou_agradecimento_curto,
    resposta_curta_contextual,
    tipo_reconhecimento_afetivo,
)
from mente_laylay.personalidade.ritmo_natural import ajustar_encerramento_organico


def test_codigo_da_laylay_e_relacao_com_a_propria_assistente() -> None:
    analise = analisar_identidade_turno("Vai mexer no código da Laylay hoje também?")
    assert analise["referencia_laylay"]
    assert analise["relacao_com_laylay"] == "codigo"
    assert not analise["objeto_laylay_py"]
    assert "primeira pessoa" in resumo_identidade_turno(analise)


def test_laylay_py_e_arquivo_sem_deixar_de_reconhecer_o_nome() -> None:
    analise = analisar_identidade_turno("Abre o Laylay.py")
    assert analise["objeto_laylay_py"]
    assert not analise["vocativo_laylay"]
    assert remover_vocativo_laylay("Laylay, abre o Laylay.py") == "abre o Laylay.py"


def test_fala_da_laylay_converte_terceira_para_primeira_pessoa() -> None:
    assert ajustar_autorreferencia_assistente("O código da Laylay está melhorando.") == "meu código está melhorando."
    assert ajustar_autorreferencia_assistente("A Laylay pode aprender isso.") == "Posso aprender isso."
    assert ajustar_autorreferencia_assistente("Abra o Laylay.py.") == "Abra o Laylay.py."


def test_funcao_humana_reconhece_conquista_correcao_e_encerramento() -> None:
    assert analisar_funcao_comunicativa("tirei nota máxima na prova")["funcao"] == "conquista"
    assert analisar_funcao_comunicativa("não Lay, eu quis dizer outra coisa")["funcao"] == "correcao"
    assert analisar_funcao_comunicativa("obrigado, era só isso")["funcao"] == "encerramento"


def test_plano_prioriza_reconhecer_conquista() -> None:
    texto = "tirei nota máxima na prova"
    turno = classificar_modalidade_turno(texto)
    turno["identidade"] = analisar_identidade_turno(texto)
    turno["funcao_comunicativa"] = analisar_funcao_comunicativa(texto)
    plano = planejar_turno(texto, turno=turno, mente={})
    assert plano["funcao_comunicativa"] == "conquista"
    assert "reconhecer a conquista" in plano["resposta_esperada"]


def test_elogio_em_terceira_pessoa_e_recebido_pela_laylay() -> None:
    ctx = {
        "mente_integrada_estado": {},
        "_normalizar_texto_curto": lambda texto: texto.casefold(),
        "_normalizar_texto_com_apelidos": lambda texto: texto.casefold(),
    }
    assert parece_elogio_ou_agradecimento_curto(ctx, "a Laylay é incrível")
    assert tipo_reconhecimento_afetivo("a Laylay é incrível") == "elogio_pessoal"


def test_gosto_por_terceiro_nao_vira_elogio_para_laylay() -> None:
    ctx = {
        # Simula inclusive uma correção fonética agressiva do perfil de voz.
        "_normalizar_texto_com_apelidos": lambda texto: texto.casefold().replace("gosto", "gostei"),
    }
    assert not parece_elogio_ou_agradecimento_curto(
        ctx, "maldade kkkk, eu gosto bastante dele"
    )


def test_opiniao_bloqueia_biografia_que_nao_existe_nos_fatos() -> None:
    fatos = "Tim Maia foi um cantor e compositor brasileiro conhecido por sua contribuição à música popular."
    assert _fala_extrapola_fatos_disponiveis(
        "Tim Maia chegou a ser deputado federal por um partido em 1995.", fatos
    )
    assert not _fala_extrapola_fatos_disponiveis(
        "Tim Maia foi um cantor de muita personalidade.", fatos
    )


def test_contestacao_pede_revisao_em_vez_de_fallback_generico() -> None:
    ctx = {
        "mente_integrada_estado": {
            "ultima_resposta": "Tim Maia teve um papel político importante.",
            "retrato_turno_atual": {
                "referencia_resolvida": {"tipo": "referencia_nomeada", "nome": "Tim Maia"}
            },
            "assunto_estruturado_atual": {"titulo": "Tim Maia"},
        },
        "_normalizar_texto_com_apelidos": lambda texto: texto.casefold(),
    }
    fala = resposta_curta_contextual(
        ctx, "kkk que papo é esse que o Tim Maia foi para a política?", "QUESTION"
    )
    assert "razão de estranhar" in fala
    assert "sem ter base segura" in fala
    assert "não peguei com segurança" not in fala.casefold()


def test_preferencia_por_referente_ativo_responde_sem_inventar_titulo() -> None:
    ctx = {
        "mente_integrada_estado": {
            "retrato_turno_atual": {
                "referencia_resolvida": {"tipo": "artista", "nome": "Rodrigo Zin"}
            },
            "assunto_estruturado_atual": {"titulo": "Rodrigo Zin"},
        },
        "_normalizar_texto_com_apelidos": lambda texto: texto.casefold(),
    }
    fala = resposta_curta_contextual(
        ctx, "qual sua música favorita dele?", "QUESTION"
    )
    assert "ainda não tenho uma favorita de rodrigo zin" in fala.casefold()
    assert "me indica uma boa porta de entrada" in fala.casefold()
    assert "não peguei com segurança" not in fala.casefold()


def test_pergunta_local_nao_compreendida_segue_para_ia_principal() -> None:
    ctx = {
        "mente_integrada_estado": {},
        "_normalizar_texto_com_apelidos": lambda texto: texto.casefold(),
        "_fala_e_fallback_neutro": lambda _fala: True,
    }
    fala = construir_fala_conversa(
        ctx,
        "Não peguei com segurança o referente.",
        "por que isso aconteceu daquela forma?",
        "conversa",
        [],
    )
    assert fala == ""


def test_repeticao_util_nao_vira_comentario_sobre_o_sistema() -> None:
    fala = "Ainda não tenho uma favorita de Rodrigo Zin. Me indica uma boa porta de entrada."
    resultado = verificar_fala_turno(
        fala,
        plano={"texto_usuario": "qual sua música favorita dele?"},
        ultima_resposta=fala,
    )
    assert resultado["fala"] == fala
    assert "repeticao_exata" in resultado["problemas"]
    assert "eu ia repetir" not in resultado["fala"].casefold()


def test_alegacao_contestada_entra_no_prompt_como_nao_confiavel() -> None:
    prompt = resumo_mente_integrada_para_prompt(
        texto_usuario="fiquei curioso sobre isso",
        ctx={},
        percepcao={},
        mente={"alegacao_contestada": {
            "texto": "Tim Maia foi deputado federal.",
            "contestacao": "que papo é esse?",
            "status": "nao_confiavel_ate_verificacao",
            "ts": time.time(),
        }},
    )
    assert "ALEGAÇÃO CONTESTADA" in prompt
    assert "Não repita nem desenvolva essa alegação como fato" in prompt


def test_pergunta_sobre_laylay_em_terceira_pessoa_e_bem_estar() -> None:
    ctx = {
        "mente_integrada_estado": {},
        "_normalizar_texto_curto": lambda texto: texto.casefold(),
        "_normalizar_texto_com_apelidos": lambda texto: texto.casefold(),
    }
    resultado = classificar_conversa_curta_local(ctx, "como a Laylay está?")
    assert resultado["tipo"] == "WELLBEING"


def test_resposta_de_baixa_demanda_nao_termina_com_oferta_generica() -> None:
    fala = "Tudo bem, um pouco de sossego também vale. Posso te ajudar em mais alguma coisa?"
    assert ajustar_encerramento_organico(fala, "agora nada demais") == "Tudo bem, um pouco de sossego também vale."


def test_identidade_e_funcao_entram_no_prompt_integrado() -> None:
    identidade = analisar_identidade_turno("vou melhorar o código da Laylay")
    funcao = analisar_funcao_comunicativa("vou melhorar o código da Laylay")
    prompt = resumo_mente_integrada_para_prompt(
        texto_usuario="vou melhorar o código da Laylay",
        ctx={},
        percepcao={},
        mente={
            "identidade_turno_resumo": resumo_identidade_turno(identidade),
            "funcao_comunicativa_atual": funcao,
        },
    )
    assert "quem responde e Laylay" in prompt
    assert "Função humana da fala atual" in prompt


def test_verificador_reconhece_conquista_antes_de_continuar() -> None:
    texto = "tirei nota máxima na prova"
    turno = classificar_modalidade_turno(texto)
    turno["funcao_comunicativa"] = analisar_funcao_comunicativa(texto)
    plano = planejar_turno(texto, turno=turno)
    resultado = verificar_fala_turno("Sobre o que era a prova?", plano=plano)
    assert "parabéns" in resultado["fala"].casefold()
    assert "conquista_sem_reconhecimento" in resultado["problemas"]
