from __future__ import annotations

import json
import time

from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.autonomia.processamento_resposta_ia import (
    preparar_resposta_para_execucao,
)
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.cognicao.contrato_fala import (
    ContratoSemanticoFala,
    construir_contrato_semantico_fala,
    formatar_contrato_fala_para_prompt,
)
from mente_laylay.cognicao.geracao_concreta import (
    normalizar_roteiro_geracao_concreta,
)
from mente_laylay.cognicao.validacao_contrato_fala import (
    validar_aderencia_contrato_fala,
)
from mente_laylay.cognicao.orquestrador_turno_runtime import (
    iniciar_planejamento_turno,
    verificar_fala_do_turno as verificar_fala_publicada,
)
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.qualidade_comunicacao import (
    avaliar_qualidade_comunicacao,
    montar_mensagens_reparo_comunicacao,
)
from mente_laylay.memoria_mental.diagnostico_mente import construir_diagnostico_mente
from mente_laylay.memoria_mental.formatacao_diagnostico import (
    formatar_diagnostico_terminal,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
)
from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
from mente_laylay.memoria_mental.sessao_conversa import renovar_contexto_sessao
from mente_laylay.integracao.registro_conversa_llm import (
    EstadoConversaRuntime,
    PedidoModelo,
    RegistroPreparacaoConversa,
    ResultadoModelo,
)
from mente_laylay.integracao.preparacao_llm import preparar_payload_llm


def _plano(*, atos=("conversa",), referente="", execucao=False, permite_pergunta=True):
    return {
        "id": 42,
        "ato_principal": atos[0],
        "atos": [
            {"ordem": indice, "tipo": ato, "objetivo": f"objetivo {ato}"}
            for indice, ato in enumerate(atos)
        ],
        "resposta_esperada": "responder à fala atual",
        "referencia_resolvida": {"nome": referente} if referente else {},
        "requer_execucao": execucao,
        "permite_pergunta": permite_pergunta,
        "deliberacao_habilidades": {"decisao": "consenso"},
    }


def test_saudacao_nao_autoriza_inferencia_oculta() -> None:
    contrato = construir_contrato_semantico_fala(
        "Oi Lay",
        plano=_plano(),
        funcao_comunicativa={"funcao": "informacao"},
    )

    assert "saudacao" in contrato["atos"]
    assert contrato["max_frases"] == 2
    assert contrato["permite_metafora"] is False
    assert contrato["autoriza_execucao"] is False
    assert any("sinal oculto" in item for item in contrato["inferencias_proibidas"])
    assert contrato["roteiro_concreto"]["estrategia"] == "saudacao_simples"
    assert "humor não declarado" in contrato["roteiro_concreto"]["nucleo_resposta"]


def test_opiniao_exige_posicao_e_razao_concretas() -> None:
    contrato = construir_contrato_semantico_fala(
        "O que você acha de rock?",
        plano=_plano(atos=("pergunta",)),
        funcao_comunicativa={"funcao": "informacao"},
    )

    assert "opiniao" in contrato["atos"]
    assert contrato["referente"] == "rock"
    assert any("posição clara sobre rock" in item for item in contrato["conteudos_obrigatorios"])
    assert any("razão concreta" in item for item in contrato["conteudos_obrigatorios"])
    assert any("abstração vaga" in item for item in contrato["inferencias_proibidas"])
    roteiro = contrato["roteiro_concreto"]
    assert roteiro["estrategia"] == "opiniao_com_criterio"
    assert roteiro["ancora_literal"] == "rock"
    assert "posição clara sobre rock" in roteiro["nucleo_resposta"]
    assert any("aspecto concreto" in item for item in roteiro["sequencia"])


def test_esclarecimento_carrega_fala_anterior_e_bloqueia_nova_metafora() -> None:
    anterior = "Eu prefiro rock porque ele costuma variar mais de clima."
    contrato = construir_contrato_semantico_fala(
        "Como assim?",
        plano=_plano(atos=("pergunta",)),
        funcao_comunicativa={"funcao": "informacao"},
        mente={"ultima_resposta": anterior},
    )

    assert "esclarecimento" in contrato["atos"]
    assert contrato["fala_anterior_relevante"] == anterior
    assert contrato["permite_humor"] is False
    assert contrato["permite_metafora"] is False
    assert any("explicar literalmente" in item for item in contrato["conteudos_obrigatorios"])
    roteiro = contrato["roteiro_concreto"]
    assert roteiro["estrategia"] == "esclarecimento_literal"
    assert roteiro["ancora_literal"] == anterior
    assert roteiro["sequencia"][:2] == [
        "reformular literalmente a ideia anterior",
        "dar a razão concreta que sustenta essa ideia",
    ]


def test_bem_estar_nao_permita_corpo_fome_ou_sono_inventados() -> None:
    contrato = construir_contrato_semantico_fala(
        "Como você vai?",
        plano=_plano(atos=("pergunta",)),
        funcao_comunicativa={"funcao": "informacao"},
    )

    assert "bem_estar" in contrato["atos"]
    assert contrato["max_frases"] == 2
    assert any("corpo, fome, sono" in item for item in contrato["inferencias_proibidas"])
    roteiro = contrato["roteiro_concreto"]
    assert roteiro["estrategia"] == "reciprocidade_social"
    assert "presença digital" in roteiro["nucleo_resposta"]


def test_estado_pessoal_exige_reconhecimento_literal_e_sem_deboche() -> None:
    contrato = construir_contrato_semantico_fala(
        "Hoje eu tô meio cansado",
        plano=_plano(),
        funcao_comunicativa={"funcao": "desabafo"},
    )

    assert "estado_pessoal" in contrato["atos"]
    assert contrato["permite_humor"] is False
    assert any("estado que o usuário informou" in item for item in contrato["conteudos_obrigatorios"])
    assert contrato["roteiro_concreto"]["estrategia"] == "acolhimento_literal"


def test_turno_misto_preserva_os_dois_atos_na_mesma_fala() -> None:
    contrato = construir_contrato_semantico_fala(
        "Tá tudo bem sim, você prefere rock ou metal?",
        plano=_plano(atos=("conversa", "pergunta")),
        funcao_comunicativa={"funcao": "informacao"},
    )

    assert "estado_pessoal" in contrato["atos"]
    assert "opiniao" in contrato["atos"]
    assert contrato["referente"] == "rock ou metal"
    assert any("todos os atos" in item for item in contrato["conteudos_obrigatorios"])
    roteiro = contrato["roteiro_concreto"]
    assert roteiro["estrategia"] == "resposta_multiacto"
    assert roteiro["sequencia"][:2] == [
        "reconhecer literalmente o estado informado pelo usuário",
        "declarar a posição e dar um critério concreto",
    ]


def test_pedido_criativo_e_unica_excecao_para_metafora() -> None:
    contrato = construir_contrato_semantico_fala(
        "Escreve uma descrição artística com metáfora para o avatar",
        plano=_plano(),
        funcao_comunicativa={"funcao": "informacao"},
    )

    assert contrato["permite_metafora"] is True
    assert contrato["max_frases"] == 6


def test_contrato_de_comando_permanece_sem_autoridade() -> None:
    contrato = construir_contrato_semantico_fala(
        "Liga a luz",
        plano=_plano(atos=("comando",), execucao=True, permite_pergunta=False),
        funcao_comunicativa={"funcao": "informacao"},
    )

    assert contrato["max_frases"] == 2
    assert contrato["permite_pergunta"] is False
    assert contrato["autoriza_execucao"] is False
    assert ContratoSemanticoFala(autoriza_execucao=True).autoriza_execucao is False
    roteiro = contrato["roteiro_concreto"]
    assert roteiro["estrategia"] == "resultado_observado"
    assert "realmente observado" in roteiro["nucleo_resposta"]
    assert roteiro["autoriza_execucao"] is False


def test_roteiro_externo_nao_consegue_criar_autorizacao() -> None:
    roteiro = normalizar_roteiro_geracao_concreta({
        "estrategia": "resultado_observado",
        "autoriza_execucao": True,
        "origem": "executor_privado",
        "primeira_frase_responde_nucleo": False,
    })
    contrato = ContratoSemanticoFala(
        roteiro_concreto={"autoriza_execucao": True, "origem": "fora"},
    ).como_dict()

    assert roteiro["autoriza_execucao"] is False
    assert roteiro["origem"] == "mente_unica"
    assert roteiro["primeira_frase_responde_nucleo"] is True
    assert contrato["roteiro_concreto"]["autoriza_execucao"] is False


def test_roteiro_so_permite_fundamentacao_factual_confiavel_e_valida() -> None:
    plano_sem_fonte = _plano(atos=("pergunta",))
    plano_sem_fonte["fundamentacao_factual"] = {
        "confiavel": False,
        "resumo": "conteúdo não confirmado",
    }
    contrato_sem_fonte = construir_contrato_semantico_fala(
        "O que você acha de rock?",
        plano=plano_sem_fonte,
        funcao_comunicativa={"funcao": "informacao"},
    )
    plano_com_fonte = _plano(atos=("pergunta",))
    plano_com_fonte["fundamentacao_factual"] = {
        "confiavel": True,
        "evidencia_dentro_validade": True,
        "resumo": "base confirmada",
    }
    contrato_com_fonte = construir_contrato_semantico_fala(
        "O que você acha de rock?",
        plano=plano_com_fonte,
        funcao_comunicativa={"funcao": "informacao"},
    )

    bases_sem = contrato_sem_fonte["roteiro_concreto"]["base_permitida"]
    bases_com = contrato_com_fonte["roteiro_concreto"]["base_permitida"]
    assert not any("fundamentação factual" in item for item in bases_sem)
    assert any("fundamentação factual" in item for item in bases_com)


def test_p4_rejeita_opiniao_vaga_e_aceita_criterio_concreto() -> None:
    texto = "O que você acha de rock?"
    contrato = construir_contrato_semantico_fala(
        texto,
        plano=_plano(atos=("pergunta",)),
        funcao_comunicativa={"funcao": "informacao"},
    )

    vaga = validar_aderencia_contrato_fala(
        texto,
        "Eu gosto de rock. É energia.",
        contrato_fala=contrato,
    )
    concreta = validar_aderencia_contrato_fala(
        texto,
        "Eu gosto de rock porque as guitarras variam entre sons limpos e distorcidos.",
        contrato_fala=contrato,
    )

    assert "opiniao_sem_criterio_concreto" in vaga["problemas"]
    assert "abstracao_sem_apoio_concreto" in vaga["problemas"]
    assert concreta["aceita"] is True


def test_p4_exige_que_esclarecimento_use_a_fala_anterior() -> None:
    anterior = "Eu prefiro rock porque ele varia mais entre melodias leves e riffs pesados."
    contrato = construir_contrato_semantico_fala(
        "Como assim?",
        plano=_plano(atos=("pergunta",)),
        funcao_comunicativa={"funcao": "informacao"},
        mente={"ultima_resposta": anterior},
    )

    solta = validar_aderencia_contrato_fala(
        "Como assim?",
        "Pra quê?",
        contrato_fala=contrato,
        ultima_resposta=anterior,
    )
    literal = validar_aderencia_contrato_fala(
        "Como assim?",
        "Quis dizer que o rock alterna melhor entre melodias leves e riffs pesados.",
        contrato_fala=contrato,
        ultima_resposta=anterior,
    )

    assert "esclarecimento_sem_explicacao" in solta["problemas"]
    assert "esclarecimento_sem_ancora_anterior" in solta["problemas"]
    assert literal["aceita"] is True


def test_p4_rejeita_leitura_oculta_na_saudacao_e_corpo_no_bem_estar() -> None:
    saudacao = construir_contrato_semantico_fala(
        "Oi Lay",
        plano=_plano(),
        funcao_comunicativa={"funcao": "informacao"},
    )
    bem_estar = construir_contrato_semantico_fala(
        "Como você vai?",
        plano=_plano(atos=("pergunta",)),
        funcao_comunicativa={"funcao": "informacao"},
    )

    leitura_oculta = validar_aderencia_contrato_fala(
        "Oi Lay",
        "Você me deixou com a sensação de que não está muito bem.",
        contrato_fala=saudacao,
    )
    corpo = validar_aderencia_contrato_fala(
        "Como você vai?",
        "Tô com fome, mas ainda estou aqui.",
        contrato_fala=bem_estar,
    )

    assert "saudacao_inferiu_estado_oculto" in leitura_oculta["problemas"]
    assert "bem_estar_com_experiencia_fisica" in corpo["problemas"]


def test_p4_turno_misto_exige_os_dois_atos_na_ordem_planejada() -> None:
    texto = "Tá tudo bem sim, você prefere rock ou metal?"
    contrato = construir_contrato_semantico_fala(
        texto,
        plano=_plano(atos=("conversa", "pergunta")),
        funcao_comunicativa={"funcao": "informacao"},
    )

    incompleta = validar_aderencia_contrato_fala(
        texto,
        "Eu prefiro rock porque as guitarras costumam variar mais.",
        contrato_fala=contrato,
    )
    invertida = validar_aderencia_contrato_fala(
        texto,
        "Eu prefiro rock porque as guitarras costumam variar mais. Que bom saber.",
        contrato_fala=contrato,
    )
    correta = validar_aderencia_contrato_fala(
        texto,
        "Que bom saber. Eu prefiro rock porque as guitarras costumam variar mais.",
        contrato_fala=contrato,
    )

    assert "ato_estado_pessoal_nao_reconhecido" in incompleta["problemas"]
    assert "ordem_multiacto_invertida" in invertida["problemas"]
    assert correta["aceita"] is True


def test_p4_avaliador_canonico_e_reparo_recebem_o_mesmo_contrato() -> None:
    texto = "O que você acha de rock?"
    contrato = construir_contrato_semantico_fala(
        texto,
        plano=_plano(atos=("pergunta",)),
        funcao_comunicativa={"funcao": "informacao"},
    )
    plano = {
        **_plano(atos=("pergunta",)),
        "texto_usuario": texto,
        "contrato_fala": contrato,
    }
    avaliacao = avaliar_qualidade_comunicacao(
        texto,
        "Eu gosto de rock.",
        plano=plano,
    )
    mensagens = montar_mensagens_reparo_comunicacao(
        texto,
        "Eu gosto de rock.",
        avaliacao,
    )
    payload = json.loads(mensagens[-1]["content"])

    assert avaliacao["aderencia_contrato"]["avaliado"] is True
    assert "opiniao_sem_criterio_concreto" in avaliacao["problemas"]
    assert payload["contrato_de_reparo"]["estrategia"] == "opiniao_com_criterio"
    assert payload["contrato_de_reparo"]["autoriza_execucao"] is False
    assert "cumpra o núcleo já na primeira frase" in mensagens[0]["content"]


def test_p4_caminho_real_repara_rascunho_antes_de_voz_e_memoria() -> None:
    texto = "O que você acha de rock?"
    contrato = construir_contrato_semantico_fala(
        texto,
        plano=_plano(atos=("pergunta",)),
        funcao_comunicativa={"funcao": "informacao"},
    )
    plano = {
        **_plano(atos=("pergunta",)),
        "texto_usuario": texto,
        "contrato_fala": contrato,
    }
    pedidos = []

    def reparar(mensagens, **_kwargs):
        pedidos.append(mensagens)
        return json.dumps({
            "fala": (
                "Eu gosto de rock porque as guitarras podem alternar entre "
                "sons limpos e distorcidos."
            ),
            "comandos": [],
        }, ensure_ascii=False)

    resposta = preparar_resposta_para_execucao(
        texto,
        '{"fala":"Eu gosto de rock. É energia.","comandos":[]}',
        enviar_mensagem_cb=reparar,
        limpar_texto_fala_cb=lambda fala: fala,
        fallback_fala="fallback",
        memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": plano, "mensagens": []},
        log=lambda _texto: None,
    )

    assert len(pedidos) == 1
    assert "guitarras" in resposta["fala"]
    assert "É energia" not in resposta["fala"]


def test_p4_nao_cria_atalho_de_execucao_operacional() -> None:
    texto = "Liga a luz"
    contrato = construir_contrato_semantico_fala(
        texto,
        plano=_plano(atos=("comando",), execucao=True),
        funcao_comunicativa={"funcao": "informacao"},
    )
    resultado = verificar_fala_turno(
        "Liguei a luz.",
        plano={
            **_plano(atos=("comando",), execucao=True),
            "texto_usuario": texto,
            "contrato_fala": contrato,
            "comandos": [],
        },
        origem="ia_final",
    )

    assert "comando_sem_execucao_confirmada" in resultado["problemas"]
    assert resultado["aderencia_contrato"]["autoriza_execucao"] is False
    assert "não executei nem confirmei" in resultado["fala"]


def test_p4_diagnostico_expoe_resultado_sem_vazar_ancora_literal() -> None:
    contrato = construir_contrato_semantico_fala(
        "O que você acha de rock?",
        plano=_plano(atos=("pergunta",)),
        funcao_comunicativa={"funcao": "informacao"},
    )
    aderencia = validar_aderencia_contrato_fala(
        "O que você acha de rock?",
        "Eu gosto de rock.",
        contrato_fala=contrato,
    )
    diagnostico = construir_diagnostico_mente({
        "mental": {
            "contrato_fala_atual": contrato,
            "plano_turno_atual": {"ultima_verificacao": {
                "aderencia_contrato": aderencia,
            }},
            "metricas_verificador": {
                "falas_verificadas": 3,
                "contratos_verificados": 2,
                "contratos_aprovados": 1,
                "contratos_rejeitados": 1,
            },
        },
    }, {})
    texto = formatar_diagnostico_terminal(diagnostico)

    assert diagnostico["verificador_fala"]["contratos_verificados"] == 2
    assert diagnostico["verificador_fala"]["ultima_estrategia"] == "opiniao_com_criterio"
    assert "opiniao_sem_criterio_concreto" in texto
    assert "ancora_literal" not in texto
    assert "O que você acha de rock?" not in texto


def test_p4_caminho_composto_publica_metricas_do_contrato() -> None:
    texto = "O que você acha de rock?"
    contrato = construir_contrato_semantico_fala(
        texto,
        plano=_plano(atos=("pergunta",)),
        funcao_comunicativa={"funcao": "informacao"},
    )
    estado = EstadoCompartilhadoRuntime(mental={
        "plano_turno_atual": {
            **_plano(atos=("pergunta",)),
            "texto_usuario": texto,
            "contrato_fala": contrato,
        },
        "contrato_fala_atual": contrato,
        "metricas_verificador": {},
    })
    ns = {
        "_estado_compartilhado_runtime": estado,
        "_contexto_horario_atual": lambda: "noite",
        "_verificar_fala_turno_mente": verificar_fala_turno,
        "time": time,
        "print": lambda *_args, **_kwargs: None,
    }

    resultado = verificar_fala_publicada(
        lambda: ns,
        "Eu gosto de rock.",
        origem="ia_final",
    )
    metricas = dict(estado.mental.get("metricas_verificador") or {})

    assert resultado["aceita"] is False
    assert metricas["contratos_verificados"] == 1
    assert metricas["contratos_rejeitados"] == 1
    assert metricas["estrategia:opiniao_com_criterio"] == 1


def test_prompt_real_recebe_contrato_da_mente_compartilhada() -> None:
    contrato = construir_contrato_semantico_fala(
        "Você prefere rock ou metal?",
        plano=_plano(atos=("pergunta",)),
        funcao_comunicativa={"funcao": "informacao"},
        falas_recentes=("Eu prefiro rock porque ele é mais versátil.",),
    )
    runtime = ContextoPromptRuntime(
        memoria_sqlite=None,
        resumo_mente_integrada=lambda _texto: "",
        formatar_playlists=lambda: "",
        get_status_humor_prompt=lambda: "calma",
        base_system_prompt="BASE",
        estado_getter=lambda: {
            "messages": [],
            "turno_atual": {"modalidade": "pergunta"},
            "contrato_fala_atual": contrato,
        },
    )

    _mensagens, prompt = runtime.preparar("Você prefere rock ou metal?")

    assert "CONTRATO SEMÂNTICO DA FALA DESTE TURNO" in prompt
    assert "Referente concreto: rock ou metal" in prompt
    assert "Evite repetir:" in prompt
    assert "Roteiro concreto: estratégia=opiniao_com_criterio" in prompt
    assert "Abstrações que exigem explicação concreta" in prompt
    assert "Base permitida para afirmar:" in prompt
    assert "nunca cria, autoriza, executa ou confirma comandos" in prompt


def test_formatacao_vazia_nao_infla_prompt() -> None:
    assert formatar_contrato_fala_para_prompt({}) == ""


def test_caminho_real_do_turno_publica_contrato_na_mente_e_no_plano() -> None:
    estado_mental = criar_estado_mental_inicial()
    estado_mental["ultima_resposta"] = "Eu prefiro rock porque ele é mais versátil."
    estado = EstadoCompartilhadoRuntime(
        mental=estado_mental,
        memoria_conversa={
            "messages": [
                {"role": "assistant", "content": estado_mental["ultima_resposta"]},
            ]
        },
    )

    class _Saude:
        @staticmethod
        def snapshot():
            return {}

    ns = {
        "_estado_compartilhado_runtime": estado,
        "_pendencia_ativa_turno_mente": lambda _mente: {},
        "_classificar_modalidade_turno_mente": lambda _texto, **_kwargs: {
            "id": 77,
            "modalidade": "pergunta",
            "modalidade_geral": "pergunta",
            "ato_principal": "pergunta",
            "segmentos": [{"modalidade": "pergunta", "texto": "Como assim?"}],
            "autoriza_execucao": False,
        },
        "_texto_tem_comando_explicito": lambda _texto: False,
        "_normalizar_texto_com_apelidos": lambda texto: texto.casefold(),
        "_resolver_repeticao_ultima_acao": lambda _texto: None,
        "_modo_jogo_runtime": None,
        "_registro_visao_jogo_leitura_runtime": None,
        "_interpretador_semantico_runtime": None,
        "_analisar_identidade_turno_mente": lambda _texto, **_kwargs: {},
        "_analisar_funcao_comunicativa_mente": lambda _texto: {
            "funcao": "informacao", "permite_pergunta": True,
        },
        "_classificar_encerramento_assunto_mente": lambda *_args: "",
        "_extrair_correcao_duravel_mente": lambda *_args, **_kwargs: {},
        "_abrir_correcao_interpretacao_mente": lambda *_args, **_kwargs: {},
        "_construir_retrato_turno_mente": lambda *_args, **_kwargs: (
            {"id": 1, "referencia_candidatos": [], "referencia_resolvida": {}}, []
        ),
        "_obter_contexto_perceptivo": lambda: {},
        "playlist_state": {},
        "_atualizar_registro_turno_mente": lambda *_args, **_kwargs: {},
        "_extrair_tema_fundamentacao_mente": lambda *_args, **_kwargs: "",
        "_construir_parecer_especialistas_mente": lambda *_args, **_kwargs: {
            "deliberacao": {"decisao": "responder"}
        },
        "_saude_mente_runtime": _Saude(),
        "_orquestrador_cooperativo_runtime": None,
        "_atualizar_assunto_estruturado_mente": lambda *_args, **_kwargs: {},
        "_planejar_turno_mente": planejar_turno,
        "_contexto_horario_atual": lambda: "noite",
        "_resumo_identidade_turno_mente": lambda _identidade: "",
        "_observabilidade_mente_runtime": None,
        "MEMORIA_SQLITE": None,
        "print": lambda *_args, **_kwargs: None,
        "time": time,
    }

    turno = iniciar_planejamento_turno(lambda: ns, "Como assim?", origem="terminal")
    contrato = dict(estado.mental.get("contrato_fala_atual") or {})

    assert turno["contrato_fala"] == contrato
    assert estado.mental["plano_turno_atual"]["contrato_fala"] == contrato
    assert contrato["fala_anterior_relevante"].startswith("Eu prefiro rock")
    assert contrato["cooperacao_considerada"] is True
    assert contrato["autoriza_execucao"] is False


def test_contrato_e_efemero_e_aparece_no_diagnostico() -> None:
    contrato = construir_contrato_semantico_fala(
        "O que você acha de rock?",
        plano=_plano(atos=("pergunta",)),
        funcao_comunicativa={"funcao": "informacao"},
    )
    diagnostico = construir_diagnostico_mente(
        {"mental": {"contrato_fala_atual": contrato}},
        {},
    )
    mental, _conversa, _mensagens = renovar_contexto_sessao(
        {"contrato_fala_atual": contrato}, {}, [], motivo="teste", ativa=True,
    )

    assert diagnostico["contrato_fala"]["ativo"] is True
    assert diagnostico["contrato_fala"]["autoriza_execucao"] is False
    assert diagnostico["contrato_fala"]["estrategia_concreta"] == "opiniao_com_criterio"
    assert diagnostico["contrato_fala"]["primeira_frase_responde_nucleo"] is True
    assert "ancora_literal" not in diagnostico["contrato_fala"]
    assert mental["contrato_fala_atual"] == {}


def test_instrucao_rapida_e_compacta_sem_memoria_ou_autorizacao() -> None:
    contrato = construir_contrato_semantico_fala(
        "Como você vai?",
        plano=_plano(atos=("pergunta",)),
        funcao_comunicativa={"funcao": "informacao"},
    )
    medidas = []
    runtime = ContextoPromptRuntime(
        memoria_sqlite=None,
        resumo_mente_integrada=lambda _texto: "MEMÓRIA QUE NÃO DEVE ENTRAR",
        formatar_playlists=lambda: "playlist privada",
        get_status_humor_prompt=lambda: "calma",
        base_system_prompt="BASE COMPLETA",
        estado_getter=lambda: {"contrato_fala_atual": contrato},
        registrar_tamanho_prompt=lambda origem, chars: medidas.append((origem, chars)),
    )

    instrucao = runtime.preparar_instrucao_rapida("Como você vai?")

    assert "CONTRATO SEMÂNTICO EFÊMERO DA FALA" in instrucao
    assert "corpo, fome, sono" in instrucao
    assert "Geração concreta: estratégia=reciprocidade_social" in instrucao
    assert "Termos abstratos só podem aparecer" in instrucao
    assert "MEMÓRIA QUE NÃO DEVE ENTRAR" not in instrucao
    assert "playlist privada" not in instrucao
    assert "não autoriza, executa nem confirma ações" in instrucao
    assert runtime.diagnostico()["preparacoes_rapidas"] == 1
    assert dict(medidas)["prompt_contrato_fala_rapido"] == len(instrucao)


def test_modo_rapido_recebe_contrato_sem_persisti_lo_no_historico() -> None:
    contrato = construir_contrato_semantico_fala(
        "O que você acha de rock?",
        plano=_plano(atos=("pergunta",)),
        funcao_comunicativa={"funcao": "informacao"},
    )
    historico = [{"role": "system", "content": "PERSONALIDADE BASE"}]
    estado = EstadoConversaRuntime(
        getter=lambda: historico,
        setter=lambda novas: historico.__setitem__(slice(None), novas),
    )
    prompt = ContextoPromptRuntime(
        memoria_sqlite=None,
        resumo_mente_integrada=lambda _texto: "",
        formatar_playlists=lambda: "",
        get_status_humor_prompt=lambda: "calma",
        base_system_prompt="BASE",
        estado_getter=lambda: {"contrato_fala_atual": contrato},
    )

    class _Modelo:
        def __init__(self):
            self.pedidos: list[PedidoModelo] = []

        def executar(self, pedido: PedidoModelo) -> ResultadoModelo:
            self.pedidos.append(pedido)
            return ResultadoModelo(
                '{"fala":"Prefiro rock pela variedade.","comandos":[]}', True,
            )

    class _Contexto:
        @staticmethod
        def montar():
            return {}

    modelo = _Modelo()
    runtime = RespostaIARuntime(
        contexto_getter=lambda: {
            "marcar_inicio_turno": lambda *_args, **_kwargs: None,
            "obter_turno_atual": lambda: {"id": 991, "modalidade": "pergunta"},
            "processar_comandos_prioritarios": lambda _texto: False,
            "contexto_inicio": lambda: {},
            "processar_inicio_fluxo": lambda *_args: False,
            "usar_modo_rapido": lambda _texto: True,
            "texto_depende_de_contexto": lambda _texto: False,
            "modo_jogo_ativo": lambda: False,
            "preparacao_conversa": RegistroPreparacaoConversa.criar(prompt),
            "estado_conversa": estado,
            "modelo_llm": modelo,
            "preparar_resposta": lambda *_args: {
                "resposta_bruta": "{}",
                "fala": "Prefiro rock pela variedade.",
                "comandos": [],
                "tipo_interacao": "conversa",
                "leitura_semantica": {},
            },
            "contexto_dispatch_runtime": _Contexto(),
            "executar_comandos_json": lambda *_args, **_kwargs: {
                "erros": [],
                "fala_ja_emitida": False,
                "fala_emitida_por_acao": False,
                "fala_salva_no_inicio": False,
            },
            "contexto_finalizacao_runtime": _Contexto(),
            "finalizar_execucao": lambda *_args, **_kwargs: {
                "fala": "Prefiro rock pela variedade.",
                "registrar_no_historico": True,
            },
        },
        log=lambda *_args, **_kwargs: None,
    )

    runtime.processar("O que você acha de rock?", origem="terminal")

    assert len(modelo.pedidos) == 1
    pedido = modelo.pedidos[0]
    assert pedido.modo_rapido is True
    assert pedido.mensagens[-2]["role"] == "system"
    assert "CONTRATO SEMÂNTICO EFÊMERO" in pedido.mensagens[-2]["content"]
    assert "estratégia=opiniao_com_criterio" in pedido.mensagens[-2]["content"]
    assert "posição clara sobre rock" in pedido.mensagens[-2]["content"]
    assert pedido.mensagens[-1] == {
        "role": "user", "content": "O que você acha de rock?",
    }
    assert all(
        "CONTRATO SEMÂNTICO EFÊMERO" not in str(item.get("content") or "")
        for item in historico
    )
    assert historico[-1] == {
        "role": "assistant", "content": "Prefiro rock pela variedade.",
    }


def test_transporte_rapido_preserva_contrato_efemero_sob_compactacao() -> None:
    mensagens = [
        {"role": "system", "content": "PERSONALIDADE BASE"},
        {"role": "user", "content": "fala antiga 1"},
        {"role": "assistant", "content": "resposta antiga 1"},
        {"role": "user", "content": "fala antiga 2"},
        {"role": "assistant", "content": "resposta antiga 2"},
        {
            "role": "system",
            "content": "--- CONTRATO SEMÂNTICO EFÊMERO DA FALA ---\nNão autoriza ações.",
        },
        {"role": "user", "content": "Como você vai?"},
    ]

    payload = preparar_payload_llm(
        mensagens,
        model="teste",
        modo_rapido=True,
    )

    enviados = list(payload["messages"])
    assert enviados[0]["content"] == "PERSONALIDADE BASE"
    assert any(
        "CONTRATO SEMÂNTICO EFÊMERO" in str(item.get("content") or "")
        for item in enviados
    )
    assert enviados[-1] == {"role": "user", "content": "Como você vai?"}
