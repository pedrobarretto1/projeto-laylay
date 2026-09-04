from __future__ import annotations

import time

import pytest

from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.fundamentacao_factual import (
    extrair_tema_fundamentacao,
    extrair_tema_recomendacao_contextual,
    montar_fundamentacao,
    validar_fala_com_fundamentacao,
)
from mente_laylay.cognicao.orquestrador_turno_runtime import (
    iniciar_planejamento_turno,
    verificar_fala_do_turno,
)
from mente_laylay.cognicao.pesquisa_contextual import (
    pesquisar_recomendacoes_tema,
)
from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.memoria_mental.contexto_compartilhado import (
    criar_estado_mental_inicial,
)
from mente_laylay.memoria_mental.continuidade_contexto import (
    classificar_pergunta_com_proposito,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
)
from mente_laylay.memoria_mental.contexto_integrado import (
    compactar_contexto_integrado_para_prompt,
    resumo_mente_integrada_para_prompt,
)


def _plano_pergunta() -> dict:
    return {
        "id": 42,
        "ato_principal": "pergunta",
        "atos": [{
            "ordem": 0,
            "tipo": "pergunta",
            "objetivo": "responder diretamente à pergunta atual",
        }],
        "resposta_esperada": "responder diretamente à pergunta atual",
        "requer_execucao": False,
    }


def test_saudacao_com_recomendacao_preserva_os_dois_atos() -> None:
    contrato = construir_contrato_semantico_fala(
        "oi lay, pode me recomendar um filme?",
        plano=_plano_pergunta(),
    )

    assert contrato["atos"] == ["pergunta", "saudacao"]
    roteiro = contrato["roteiro_concreto"]
    assert roteiro["estrategia"] == "resposta_multiacto"
    assert any("pergunta" in passo for passo in roteiro["sequencia"])
    assert any("opção concreta" in passo for passo in roteiro["sequencia"])


def test_followup_de_recomendacao_exige_titulo_concreto_da_evidencia() -> None:
    contrato = construir_contrato_semantico_fala(
        "quero um de romance",
        plano={
            **_plano_pergunta(),
            "dominio": "recomendacao",
            "fundamentacao_factual": {
                "tema": "filme de romance",
                "resumo": "Uma Linda Mulher; Titanic; Jerry Maguire.",
                "confiavel": True,
            },
        },
    )

    roteiro = contrato["roteiro_concreto"]
    assert roteiro["estrategia"] == "recomendacao_fundamentada"
    assert "evidência" in roteiro["nucleo_resposta"].casefold()
    assert roteiro["sequencia"][0].startswith("escolher uma opção concreta")


def test_prompt_rapido_entrega_candidatos_pesquisados_ao_modelo() -> None:
    fundamentacao = {
        "tema": "filme de romance",
        "titulo": "Candidatos de filme de romance",
        "resumo": "Uma Linda Mulher; Titanic; Jerry Maguire.",
        "fonte": "wikipedia_pt",
        "confiavel": True,
        "evidencia_dentro_validade": True,
    }
    plano = {
        **_plano_pergunta(),
        "dominio": "recomendacao",
        "fundamentacao_factual": fundamentacao,
        "evidencia_capacidades": {
            "fonte": "catalogo_vivo",
            "possui_capacidades_locais": True,
            "dominios_confirmados": [
                "musica", "sistema", "navegador", "visao", "agenda",
                "arquivos", "email", "iot", "area_transferencia",
                "caixa_entrada", "pessoas", "memoria", "cooperacao",
            ],
        },
    }
    contrato = construir_contrato_semantico_fala(
        "quero um de romance",
        plano=plano,
    )
    runtime = ContextoPromptRuntime(
        memoria_sqlite=None,
        resumo_mente_integrada=lambda _texto: "MEMÓRIA QUE NÃO DEVE ENTRAR",
        formatar_playlists=lambda: "playlist privada",
        get_status_humor_prompt=lambda: "calma",
        base_system_prompt="BASE",
        estado_getter=lambda: {
            "contrato_fala_atual": contrato,
            "fundamentacao_factual_turno": fundamentacao,
        },
    )

    instrucao = runtime.preparar_instrucao_rapida("quero um de romance")

    assert "EVIDÊNCIA FACTUAL EFÊMERA" in instrucao
    assert "Uma Linda Mulher; Titanic; Jerry Maguire" in instrucao
    assert "escolha somente entre os títulos" in instrucao.casefold()
    assert "pesquisa contextual da laylay já foi executada" in instrucao.casefold()
    assert "não alegue falta de acesso" in instrucao.casefold()
    assert instrucao.rfind("EVIDÊNCIA FACTUAL EFÊMERA") > instrucao.rfind(
        "RETRATO EXPRESSIVO EFÊMERO"
    )
    assert "Capacidades locais confirmadas:" not in instrucao
    assert "MEMÓRIA QUE NÃO DEVE ENTRAR" not in instrucao


def test_transporte_rapido_preserva_instrucao_system_do_turno_atual() -> None:
    instrucao_turno = (
        "--- EVIDÊNCIA FACTUAL EFÊMERA DO TURNO ---\n"
        + ("contrato contextual " * 100)
        + "\nCandidatos confirmados: Uma Linda Mulher; Titanic; Jerry Maguire."
    )

    payload = preparar_payload_llm(
        [
            {
                "role": "system",
                "content": (
                    "Você é Laylay. Retorne somente JSON válido. "
                    "FORMATO ESTRUTURAL OBRIGATÓRIO DO JSON."
                ),
            },
            {"role": "assistant", "content": "Conversa anterior irrelevante."},
            {"role": "system", "content": instrucao_turno},
            {"role": "user", "content": "quero um filme de romance"},
        ],
        model="qwen3:4b-instruct",
        max_tokens=256,
        modo_rapido=True,
        endpoint_local=True,
    )

    mensagens = list(payload["messages"])
    assert any(
        item.get("role") == "system"
        and "Candidatos confirmados: Uma Linda Mulher" in item.get("content", "")
        for item in mensagens
    )


def test_prompt_completo_confirma_capacidade_de_pesquisa_do_turno() -> None:
    contexto = resumo_mente_integrada_para_prompt(
        texto_usuario="quero um filme de romance",
        ctx={},
        percepcao={},
        mente={
            "fundamentacao_factual_turno": {
                "tema": "filme de romance",
                "titulo": "Candidatos de filme de romance",
                "resumo": "Uma Linda Mulher; Titanic; Jerry Maguire.",
                "candidatos": ["Uma Linda Mulher", "Titanic", "Jerry Maguire"],
                "fonte": "wikipedia_pt",
                "confiavel": True,
                "evidencia_dentro_validade": True,
            },
        },
    )

    assert "CAPACIDADE FACTUAL CONFIRMADA NESTE TURNO" in contexto
    assert "pesquisa contextual da Laylay já foi executada" in contexto
    assert "não alegue falta de acesso a dados" in contexto


def test_prompt_normal_prioriza_lista_factual_sem_catalogo_concorrente() -> None:
    fundamentacao = {
        "tema": "filme de romance",
        "titulo": "Candidatos de filme de romance",
        "resumo": "Uma Linda Mulher; Titanic; Jerry Maguire.",
        "candidatos": ["Uma Linda Mulher", "Titanic", "Jerry Maguire"],
        "fonte": "wikipedia_pt",
        "confiavel": True,
        "evidencia_dentro_validade": True,
    }
    runtime = ContextoPromptRuntime(
        memoria_sqlite=None,
        resumo_mente_integrada=lambda _texto: "RETRATO GLOBAL POLUÍDO",
        formatar_playlists=lambda: "PLAYLIST PRIVADA",
        get_status_humor_prompt=lambda: "calma",
        base_system_prompt="Você é Laylay. Retorne somente JSON válido.",
        estado_getter=lambda: {
            "messages": [],
            "fundamentacao_factual_turno": fundamentacao,
            "contrato_fala_atual": {},
        },
        mapa_habilidades_prompt=lambda *_args, **_kwargs: "CATÁLOGO GLOBAL POLUÍDO",
        mapa_recursos_prompt=lambda _texto: "RECURSOS GLOBAIS POLUÍDOS",
    )

    _mensagens, prompt = runtime.preparar("quero um filme de romance")

    assert "EVIDÊNCIA FACTUAL EFÊMERA DO TURNO" in prompt
    assert "Uma Linda Mulher; Titanic; Jerry Maguire" in prompt
    assert "RETRATO GLOBAL POLUÍDO" not in prompt
    assert "CATÁLOGO GLOBAL POLUÍDO" not in prompt
    assert "RECURSOS GLOBAIS POLUÍDOS" not in prompt


def test_compactacao_preserva_receipt_de_capacidade_factual() -> None:
    contexto = resumo_mente_integrada_para_prompt(
        texto_usuario="quero um filme de romance",
        ctx={},
        percepcao={},
        mente={
            "fundamentacao_factual_turno": {
                "tema": "filme de romance",
                "titulo": "Candidatos de filme de romance",
                "resumo": "Uma Linda Mulher; Titanic; Jerry Maguire.",
                "candidatos": ["Uma Linda Mulher", "Titanic", "Jerry Maguire"],
                "fonte": "wikipedia_pt",
                "confiavel": True,
                "evidencia_dentro_validade": True,
            },
        },
    )
    contexto_longo = contexto + "\n" + "\n".join(
        f"Ruído secundário sem relação {indice}." for indice in range(200)
    )

    compacto = compactar_contexto_integrado_para_prompt(
        contexto_longo,
        texto_usuario="quero um filme de romance",
        limite_chars=900,
    )

    assert "CAPACIDADE FACTUAL CONFIRMADA NESTE TURNO" in compacto
    assert "pesquisa contextual da Laylay já foi executada" in compacto


def test_pergunta_de_genero_abre_continuidade_de_recomendacao() -> None:
    classificacao = classificar_pergunta_com_proposito(
        "Você quer um filme de comédia?"
    )

    assert classificacao == {
        "pergunta": "Você quer um filme de comédia?",
        "proposito": "preferencia_recomendacao",
        "resposta_esperada": "preferencia",
    }


def test_resposta_de_genero_nao_herda_pendencia_musical_incompativel() -> None:
    plano = planejar_turno(
        "quero um de romance",
        turno={"ato_principal": "conversa", "modalidade": "conversa"},
        mente={
            "pendencia_atual": {
                "status": "ativa",
                "dominio": "musica",
                "resposta_esperada": "sim_ou_nao",
            }
        },
    )

    assert plano["dominio"] == "conversa"


def test_referencia_nomeada_generica_nao_vira_musica() -> None:
    plano = planejar_turno(
        "quero um de romance",
        turno={
            "ato_principal": "conversa",
            "referencia_resolvida": {
                "tipo": "referencia_nomeada",
                "nome": "romance",
            },
        },
        mente={},
    )

    assert plano["dominio"] == "conversa"


def test_recomendacao_e_followup_extraem_tema_factual_do_filme() -> None:
    assert extrair_tema_fundamentacao(
        "oi lay, pode me recomendar um filme?"
    ) == "filme"

    registro = {
        "entidade_ativa_id": "tema:filme",
        "entidades": {
            "tema:filme": {"tipo": "tema", "nome": "filme"},
        },
    }
    assert extrair_tema_fundamentacao(
        "quero um de romance",
        registro_semantico=registro,
    ) == "filme de romance"


def test_fallback_factual_preserva_assunto_em_vez_de_inventar_musica() -> None:
    resultado = verificar_fala_turno(
        'Recomendo o filme "Diário de uma Paixão", de 2004.',
        plano={
            "texto_usuario": "quero um de romance",
            "dominio": "conversa",
            "comandos": [],
        },
        origem="resposta_ia",
    )

    assert "obra_sem_evidencia" in resultado["problemas"]
    assert "música" not in resultado["fala"].casefold()
    assert "romance" in resultado["fala"].casefold()


def test_titulo_em_italico_sem_evidencia_tambem_e_bloqueado() -> None:
    resultado = validar_fala_com_fundamentacao(
        "Recomendo *A Cor do Céu*, um romance bem delicado.",
        fundamentacao={
            "tema": "filme de romance",
            "titulo": "filme de romance",
            "resumo": "Filmes de romance contam histórias amorosas.",
            "confiavel": True,
        },
        texto_usuario="quero um filme de romance",
    )

    assert "obra_sem_evidencia" in resultado["problemas"]


def test_recomendacao_inventada_e_substituida_por_candidato_pesquisado() -> None:
    resultado = validar_fala_com_fundamentacao(
        (
            "Recomendo *A Cor de Rosas*, de 2023. Tem um final surpreendente "
            "e um romance delicado."
        ),
        fundamentacao={
            "tema": "filme de romance",
            "titulo": "Candidatos de filme de romance",
            "resumo": "Uma Linda Mulher; Titanic; Jerry Maguire.",
            "candidatos": ["Uma Linda Mulher", "Titanic", "Jerry Maguire"],
            "confiavel": True,
        },
        texto_usuario="quero um filme de romance",
    )

    assert "obra_sem_evidencia" in resultado["problemas"]
    assert "A Cor de Rosas" not in resultado["fala"]
    assert resultado["fala"].startswith("Eu iria de Uma Linda Mulher")


def test_resposta_sem_titulo_vira_recomendacao_pesquisada_concreta() -> None:
    resultado = verificar_fala_turno(
        "Qual gênero você prefere?",
        plano={
            "texto_usuario": "quero um filme de romance",
            "dominio": "recomendacao",
            "comandos": [],
            "fundamentacao_factual": {
                "tema": "filme de romance",
                "titulo": "Candidatos de filme de romance",
                "resumo": "Uma Linda Mulher; Titanic; Jerry Maguire.",
                "candidatos": ["Uma Linda Mulher", "Titanic", "Jerry Maguire"],
                "confiavel": True,
            },
        },
        origem="resposta_ia",
    )

    assert "recomendacao_sem_opcao_concreta" in resultado["problemas"]
    assert resultado["fala"].startswith("Eu iria de Uma Linda Mulher")


def test_negacao_falsa_de_capacidade_vira_resultado_pesquisado() -> None:
    resultado = verificar_fala_turno(
        (
            "Não posso sugerir filmes porque não tenho acesso a uma base de "
            "dados atualizada."
        ),
        plano={
            "texto_usuario": "quero um filme de romance",
            "dominio": "recomendacao",
            "comandos": [],
            "fundamentacao_factual": {
                "tema": "filme de romance",
                "titulo": "Candidatos de filme de romance",
                "resumo": "Uma Linda Mulher; Titanic; Jerry Maguire.",
                "candidatos": ["Uma Linda Mulher", "Titanic", "Jerry Maguire"],
                "fonte": "wikipedia_pt",
                "confiavel": True,
                "evidencia_dentro_validade": True,
            },
        },
        origem="resposta_ia",
    )

    assert "negacao_capacidade_contradiz_pesquisa" in resultado["problemas"]
    assert resultado["fala"].startswith("Eu iria de Uma Linda Mulher")
    assert "não posso" not in resultado["fala"].casefold()
    assert "não tenho acesso" not in resultado["fala"].casefold()


def test_lista_de_candidatos_nao_autoriza_sinopse_inventada_pelo_qwen() -> None:
    resultado = verificar_fala_turno(
        (
            "Título: *Jerry Maguire*. É um romance de amor com um tom direto e "
            "emocional, baseado em uma história real de um jogador de futebol "
            "que se apaixona por uma mulher e decide mudar tudo por ela. "
            "Você prefere algo mais leve ou mais intenso?"
        ),
        plano={
            "texto_usuario": "quero um de romance",
            "dominio": "recomendacao",
            "comandos": [],
            "fundamentacao_factual": {
                "tema": "filme de romance",
                "titulo": "Candidatos de filme de romance",
                "resumo": "Uma Linda Mulher; Titanic; Jerry Maguire.",
                "candidatos": ["Uma Linda Mulher", "Titanic", "Jerry Maguire"],
                "fonte": "wikipedia_pt",
                "confiavel": True,
                "evidencia_dentro_validade": True,
            },
        },
        origem="resposta_ia",
    )

    assert "descricao_obra_sem_evidencia" in resultado["problemas"]
    assert "Jerry Maguire" in resultado["fala"]
    assert "história real" not in resultado["fala"].casefold()
    assert "jogador de futebol" not in resultado["fala"].casefold()


def test_lista_de_candidatos_nao_comprova_justificativa_generica_da_obra() -> None:
    resultado = verificar_fala_turno(
        (
            "Uma Linda Mulher. É um dos clássicos do gênero, com um roteiro que "
            "mistura intimidade e drama de forma natural."
        ),
        plano={
            "texto_usuario": "pode me recomendar um filme de romance?",
            "dominio": "recomendacao",
            "comandos": [],
            "fundamentacao_factual": {
                "tema": "filme de romance",
                "titulo": "Candidatos de filme de romance",
                "resumo": "Uma Linda Mulher; Titanic; Jerry Maguire.",
                "candidatos": ["Uma Linda Mulher", "Titanic", "Jerry Maguire"],
                "fonte": "wikipedia_pt",
                "confiavel": True,
                "evidencia_dentro_validade": True,
            },
        },
        origem="resposta_ia",
    )

    assert "descricao_obra_sem_evidencia" in resultado["problemas"]
    assert resultado["fala"].startswith("Eu iria de Uma Linda Mulher")
    assert "clássicos" not in resultado["fala"].casefold()
    assert "roteiro" not in resultado["fala"].casefold()


def test_pesquisa_de_recomendacao_extrai_candidatos_reais_da_fonte() -> None:
    html = """
    <h2>Filmes do gênero romance mais bem sucedidos</h2>
    <ol>
      <li><i><a rel="mw:WikiLink" href="/wiki/Pretty_Woman">Uma Linda Mulher</a></i></li>
      <li><i><a rel="mw:WikiLink" href="/wiki/Titanic_(1997)">Titanic</a></i></li>
      <li><i><a rel="mw:WikiLink" href="/wiki/The_Notebook">Diário de uma Paixão</a></i></li>
    </ol>
    """

    class _Resposta:
        status_code = 200
        text = html

        @staticmethod
        def raise_for_status() -> None:
            return None

    resultado = pesquisar_recomendacoes_tema(
        "filme de romance",
        requests_get=lambda *_args, **_kwargs: _Resposta(),
        clock=lambda: 100.0,
    )

    assert resultado["ok"] is True
    assert resultado["candidatos"] == [
        "Uma Linda Mulher", "Titanic", "Diário de uma Paixão",
    ]
    assert "Diário de uma Paixão" in resultado["resumo"]


@pytest.mark.parametrize(
    ("categoria", "fala", "tema_esperado"),
    [
        ("filme", "prefiro um de suspense", "filme de suspense"),
        ("filme", "de romance", "filme de romance"),
        ("livro", "pode ser de fantasia", "livro de fantasia"),
        ("música", "quero uma de romance", ""),
    ],
)
def test_preferencia_eliptica_reusa_apenas_referente_de_recomendacao(
    categoria: str,
    fala: str,
    tema_esperado: str,
) -> None:
    registro = {
        "entidade_ativa_id": f"tema:{categoria}",
        "entidades": {
            f"tema:{categoria}": {"tipo": "tema", "nome": categoria},
        },
    }

    assert extrair_tema_recomendacao_contextual(fala, registro) == tema_esperado


def test_preferencia_eliptica_sem_referente_nao_inventa_categoria() -> None:
    assert extrair_tema_recomendacao_contextual(
        "quero um de romance",
        {},
    ) == ""


@pytest.mark.parametrize(
    "pendencia",
    [
        {
            "status": "ativa",
            "origem": "pergunta_aberta",
            "tipo": "preferencia_recomendacao",
            "dominio": "recomendacao",
            "resposta_esperada": "preferencia",
        },
        {
            "status": "ativa",
            "origem": "pergunta_aberta",
            "tipo": "resposta_curta",
            "dominio": "conversa",
            "resposta_esperada": "detalhe",
        },
    ],
    ids=("pendencia_recomendacao", "fallback_generico"),
)
def test_composicao_pesquisa_recomendacao_antes_de_responder_followup(
    pendencia: dict,
) -> None:
    estado_mental = criar_estado_mental_inicial()
    estado_mental.update({
        "pendencia_atual": pendencia,
        "registro_semantico": {
            "entidade_ativa_id": "tema:filme",
            "entidades": {
                "tema:filme": {"tipo": "tema", "nome": "filme"},
            },
        },
    })
    estado = EstadoCompartilhadoRuntime(
        mental=estado_mental,
        memoria_conversa={"messages": []},
    )
    chamadas: list[tuple[str, str]] = []

    class _Pesquisa:
        def pesquisar_recomendacoes_tema(self, tema: str) -> dict:
            chamadas.append(("recomendar", tema))
            return {
                "ok": True,
                "titulo": "candidatos de filme de romance",
                "resumo": "Uma Linda Mulher; Titanic; Diário de uma Paixão.",
                "candidatos": [
                    "Uma Linda Mulher", "Titanic", "Diário de uma Paixão",
                ],
                "fonte": "wikipedia_pt",
                "confianca": 0.9,
            }

        def pesquisar_contexto_tema(self, tema: str) -> dict:
            chamadas.append(("pesquisar", tema))
            return {
                "ok": True,
                "titulo": "filme de romance",
                "resumo": "Diário de uma Paixão é um filme de romance.",
                "fonte": "fonte_teste",
                "confianca": 0.9,
            }

        def obter_contexto_cache(self, tema: str) -> dict:
            chamadas.append(("cache", tema))
            return {}

        def precarregar_contexto_tema(self, tema: str) -> None:
            chamadas.append(("precarregar", tema))

    class _Saude:
        @staticmethod
        def snapshot() -> dict:
            return {}

    registro = estado_mental["registro_semantico"]
    ns = {
        "_estado_compartilhado_runtime": estado,
        "_pendencia_ativa_turno_mente": lambda mente: dict(
            mente.get("pendencia_atual") or {}
        ),
        "_classificar_modalidade_turno_mente": lambda *_args, **_kwargs: {
            "id": 91,
            "modalidade": "conversa",
            "modalidade_geral": "conversa",
            "ato_principal": "resposta_social",
            "segmentos": [{"modalidade": "conversa", "texto": "quero um de romance"}],
            "autoriza_execucao": False,
        },
        "_texto_tem_comando_explicito": lambda _texto: False,
        "_normalizar_texto_com_apelidos": lambda texto: texto.casefold(),
        "_resolver_repeticao_ultima_acao": lambda _texto: None,
        "_modo_jogo_runtime": None,
        "_registro_visao_jogo_leitura_runtime": None,
        "_interpretador_semantico_runtime": None,
        "_analisar_identidade_turno_mente": lambda *_args, **_kwargs: {},
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
        "_atualizar_registro_turno_mente": lambda *_args, **_kwargs: registro,
        "_extrair_tema_fundamentacao_mente": extrair_tema_fundamentacao,
        "_pesquisa_contextual_runtime": _Pesquisa(),
        "_montar_fundamentacao_mente": montar_fundamentacao,
        "_construir_parecer_especialistas_mente": lambda *_args, **_kwargs: {
            "deliberacao": {"decisao": "responder"},
        },
        "_saude_mente_runtime": _Saude(),
        "_orquestrador_cooperativo_runtime": None,
        "_atualizar_assunto_estruturado_mente": lambda *_args, **_kwargs: {},
        "_planejar_turno_mente": planejar_turno,
        "_evidencia_habilidades_turno_mente": lambda *_args, **_kwargs: {
            "fonte": "catalogo_vivo",
            "dominios_confirmados": [],
            "dominios_relevantes": [],
            "possui_capacidades_locais": True,
            "autoriza_execucao": False,
        },
        "_contexto_horario_atual": lambda: "noite",
        "_resumo_identidade_turno_mente": lambda _identidade: "",
        "_observabilidade_mente_runtime": None,
        "MEMORIA_SQLITE": None,
        "print": lambda *_args, **_kwargs: None,
        "time": time,
    }

    iniciar_planejamento_turno(
        lambda: ns, "quero um de romance", origem="terminal",
    )

    assert chamadas == [("recomendar", "filme de romance")]
    fundamentacao = estado.mental["fundamentacao_factual_turno"]
    plano = estado.mental["plano_turno_atual"]
    assert fundamentacao["confiavel"] is True
    assert fundamentacao["tema"] == "filme de romance"
    assert fundamentacao["candidatos"][0] == "Uma Linda Mulher"
    assert plano["dominio"] == "recomendacao"
    assert plano["fundamentacao_factual"] == fundamentacao


def test_guardiao_pesquisa_e_confirma_titulo_candidato_antes_da_fala() -> None:
    chamadas: list[str] = []
    estado = EstadoCompartilhadoRuntime(
        mental={
            "plano_turno_atual": {
                "id": 92,
                "texto_usuario": "quero um filme de romance",
                "dominio": "recomendacao",
                "comandos": [],
                "fundamentacao_factual": {
                    "tema": "filme de romance",
                    "titulo": "Romance (cinema)",
                    "resumo": "Filmes de romance contam histórias amorosas.",
                    "confiavel": True,
                },
            },
            "ultima_resposta": "",
        },
        memoria_conversa={"messages": []},
    )

    class _Pesquisa:
        def pesquisar_contexto_tema(self, tema: str) -> dict:
            chamadas.append(tema)
            return {
                "ok": True,
                "tema": tema,
                "titulo": "Diário de uma Paixão",
                "resumo": "Diário de uma Paixão é um filme de drama romântico.",
                "fonte": "wikipedia_pt",
                "confianca": 0.95,
            }

    ns = {
        "_estado_compartilhado_runtime": estado,
        "_contexto_horario_atual": lambda: "noite",
        "_verificar_fala_turno_mente": verificar_fala_turno,
        "_pesquisa_contextual_runtime": _Pesquisa(),
        "_montar_fundamentacao_mente": montar_fundamentacao,
        "time": time,
        "print": lambda *_args, **_kwargs: None,
    }

    verificacao = verificar_fala_do_turno(
        lambda: ns,
        "Recomendo *Diário de uma Paixão*.",
        origem="resposta_ia",
    )

    assert chamadas == ["Diário de uma Paixão"]
    assert verificacao["aceita"] is True
    assert verificacao["problemas"] == []
    assert "Diário de uma Paixão" in verificacao["fala"]
