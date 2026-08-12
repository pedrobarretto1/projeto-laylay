from __future__ import annotations

from mente_laylay.cognicao.fundamentacao_factual import (
    avaliar_validade_fundamentacao,
    classificar_atualidade_factual,
    extrair_tema_fundamentacao,
    montar_fundamentacao,
    validar_fala_com_fundamentacao,
)
from mente_laylay.cognicao.proveniencia_informacao import classificar_proveniencia_informacao
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.memoria_mental.contexto_integrado import resumo_mente_integrada_para_prompt


def _sem_fonte(tema: str) -> dict:
    return montar_fundamentacao(tema, {"ok": False, "motivo": "nao_encontrado"}, agora=100.0)


def _com_fonte(tema: str, resumo: str) -> dict:
    return montar_fundamentacao(tema, {
        "ok": True,
        "titulo": tema,
        "resumo": resumo,
        "fonte": "fonte_teste",
        "confianca": 0.95,
    }, agora=100.0)


def test_recomendacao_conversacional_nao_inventa_titulo_sem_fundamentacao() -> None:
    resultado = verificar_fala_turno(
        'Tá, vou sugerir: "A Night in the Garden" de The Killers.',
        plano={
            "texto_usuario": "quero sim",
            "dominio": "conversa",
            "comandos": [],
        },
        origem="resposta_ia",
    )

    assert "obra_sem_evidencia" in resultado["problemas"]
    assert "A Night in the Garden" not in resultado["fala"]


def test_followup_encontra_tema_na_entidade_resolvida() -> None:
    tema = extrair_tema_fundamentacao(
        "eu também gosto das músicas dele",
        retrato={"referencia_resolvida": {"tipo": "artista", "nome": "Rodrigo Zin"}},
    )
    assert tema == "Rodrigo Zin"


def test_tema_geral_sem_categoria_tambem_e_extraido() -> None:
    assert extrair_tema_fundamentacao("o que você acha de Python?") == "Python"
    assert extrair_tema_fundamentacao("me explica sobre fotossíntese") == "fotossíntese"


def test_preferencia_da_laylay_nao_dispara_pesquisa_factual() -> None:
    assert extrair_tema_fundamentacao("você gosta de Slipknot?") == ""
    assert extrair_tema_fundamentacao("você prefere rock ou metal?") == ""


def test_preferencia_declarada_pelo_usuario_pode_ativar_pesquisa_auxiliar() -> None:
    assert extrair_tema_fundamentacao("eu gosto de rock") == "rock"
    assert extrair_tema_fundamentacao(
        "faz sentido kkk, eu também gosto de programação"
    ) == "programação"


def test_instrucao_de_estilo_nao_vira_assunto_de_pesquisa() -> None:
    assert extrair_tema_fundamentacao("explique de um jeito simples") == ""


def test_atualidade_combina_consulta_tempo_e_dominio_mutavel() -> None:
    clima = classificar_atualidade_factual("como está o clima agora em Boituva?")
    lancamento = classificar_atualidade_factual("quando vai sair o GTA 6?")
    cargo = classificar_atualidade_factual("quem é o presidente do Brasil?")

    assert clima["depende_atualidade"] and clima["classe"] == "tempo_real"
    assert lancamento["depende_atualidade"] and lancamento["classe"] == "agenda_ou_disponibilidade"
    assert cargo["depende_atualidade"] and cargo["classe"] == "estado_mutavel"


def test_atualidade_nao_confunde_fatos_estaveis_pessoais_ou_matematica() -> None:
    assert not classificar_atualidade_factual("o que é fotossíntese?")["depende_atualidade"]
    assert classificar_atualidade_factual("quem foi presidente em 2002?")["classe"] == "historica"
    assert classificar_atualidade_factual("quanto é 50 + 50?")["classe"] == "estavel"
    assert classificar_atualidade_factual("como você está agora?")["classe"] == "contexto_pessoal"


def test_fundamentacao_carrega_classificacao_de_atualidade_para_o_prompt() -> None:
    atualidade = classificar_atualidade_factual("qual é a versão atual do Python?")
    base = montar_fundamentacao(
        "Python",
        {"ok": False, "motivo": "nao_encontrado"},
        agora=100.0,
        atualidade=atualidade,
    )
    prompt = resumo_mente_integrada_para_prompt(
        texto_usuario="qual é a versão atual do Python?",
        ctx={},
        percepcao={},
        mente={"fundamentacao_factual_turno": base},
    )

    assert base["requer_evidencia_recente"] is True
    assert "ATUALIDADE FACTUAL DO TURNO" in prompt
    assert "memória antiga" in prompt


def test_atualidade_chega_ao_prompt_mesmo_sem_tema_de_pesquisa_extraido() -> None:
    atualidade = classificar_atualidade_factual("quando vai sair o GTA 6?")
    prompt = resumo_mente_integrada_para_prompt(
        texto_usuario="quando vai sair o GTA 6?",
        ctx={},
        percepcao={},
        mente={"retrato_turno_atual": {"atualidade_factual": atualidade}},
    )

    assert "ATUALIDADE FACTUAL DO TURNO" in prompt
    assert "agenda_ou_disponibilidade" in prompt


def test_fundamentacao_guarda_data_validade_e_origem_de_cache() -> None:
    atualidade = classificar_atualidade_factual("como está o clima agora?")
    base = montar_fundamentacao(
        "clima",
        {
            "ok": True,
            "titulo": "Clima",
            "resumo": "Boituva está com céu limpo.",
            "fonte": "fonte_teste",
            "confianca": 0.95,
            "evidencia_obtida_em": 100.0,
            "evidencia_validade_s": 1800.0,
            "evidencia_cache": True,
        },
        agora=200.0,
        atualidade=atualidade,
    )

    assert base["evidencia_obtida_em"] == 100.0
    assert base["evidencia_validade_s"] == 900.0
    assert base["evidencia_expira_em"] == 1000.0
    assert base["evidencia_idade_s"] == 100.0
    assert base["evidencia_dentro_validade"] is True
    assert base["evidencia_cache"] is True
    assert base["evidencia_obtida_em_iso"].startswith("1970-01-01T00:01:40")
    assert base["proveniencia"]["tipo"] == "informacao_externa"
    assert base["proveniencia"]["origem"] == "fonte_teste"
    assert base["proveniencia"]["pode_sustentar_fato_externo"] is True


def test_evidencia_temporal_expirada_perde_conteudo_e_confianca() -> None:
    atualidade = classificar_atualidade_factual("quem é o presidente atual?")
    base = montar_fundamentacao(
        "presidente",
        {
            "ok": True,
            "titulo": "Presidência",
            "resumo": "Uma pessoa ocupa atualmente o cargo.",
            "fonte": "fonte_antiga",
            "confianca": 0.95,
            "evidencia_obtida_em": 100.0,
            "evidencia_validade_s": 60.0,
        },
        agora=161.0,
        atualidade=atualidade,
    )

    assert base["evidencia_expirada"] is True
    assert base["evidencia_dentro_validade"] is False
    assert base["confiavel"] is False
    assert base["resumo"] == ""
    assert base["fonte"] == ""
    assert base["motivo"] == "evidencia_temporal_expirada"
    assert base["proveniencia"]["tipo"] == "informacao_externa"
    assert base["proveniencia"]["pode_sustentar_fato_externo"] is False


def test_proveniencia_separa_memoria_opiniao_e_fonte_externa() -> None:
    memoria = classificar_proveniencia_informacao({
        "origem": "usuario",
        "confirmado_usuario": True,
        "texto": "Pedro prefere luz roxa.",
    })
    opiniao = classificar_proveniencia_informacao({
        "tipo": "opiniao",
        "autor": "laylay",
        "status": "opiniao",
        "texto": "Roxo parece aconchegante.",
    })
    externa = classificar_proveniencia_informacao({
        "fonte": "fonte_teste",
        "confiavel": True,
        "evidencia_dentro_validade": True,
    }, contexto="fundamentacao_factual")

    assert memoria["tipo"] == "memoria_usuario"
    assert memoria["pode_sustentar_contexto_pessoal"] is True
    assert memoria["pode_sustentar_fato_externo"] is False
    assert opiniao["tipo"] == "opiniao"
    assert opiniao["subtipo"] == "opiniao_laylay"
    assert opiniao["pode_sustentar_fato_externo"] is False
    assert externa["tipo"] == "informacao_externa"
    assert externa["pode_sustentar_fato_externo"] is True


def test_validade_vencida_nao_apaga_fato_estavel() -> None:
    base = montar_fundamentacao(
        "fotossíntese",
        {
            "ok": True,
            "titulo": "Fotossíntese",
            "resumo": "Fotossíntese é um processo biológico.",
            "fonte": "fonte_estavel",
            "confianca": 0.95,
            "evidencia_obtida_em": 100.0,
            "evidencia_validade_s": 60.0,
        },
        agora=10000.0,
        atualidade=classificar_atualidade_factual("o que é fotossíntese?"),
    )

    assert base["confiavel"] is True
    assert base["resumo"]


def test_verificador_recalcula_validade_antes_de_deixar_fato_temporal_sair() -> None:
    base = {
        "tema": "Presidência",
        "titulo": "Presidência",
        "resumo": "Fulano ocupa o cargo.",
        "fonte": "fonte_teste",
        "confianca": 0.95,
        "confiavel": True,
        "requer_evidencia_recente": True,
        "atualidade": {"depende_atualidade": True},
        "evidencia_obtida_em": 100.0,
        "evidencia_expira_em": 110.0,
    }

    resultado = validar_fala_com_fundamentacao(
        "Fulano é o presidente e ocupa atualmente o cargo.",
        fundamentacao=base,
        texto_usuario="quem é o presidente atual?",
        agora=111.0,
    )

    assert "Fulano é o presidente" not in resultado["fala"]
    assert "alegacao_especifica_sem_fonte" in resultado["problemas"]


def test_fundamentacao_temporal_sem_data_e_bloqueada_por_validade_desconhecida() -> None:
    base = avaliar_validade_fundamentacao({
        "tema": "versão atual",
        "resumo": "Versão X é a atual.",
        "fonte": "memoria_antiga",
        "confiavel": True,
        "requer_evidencia_recente": True,
    }, agora=500.0)

    assert base["confiavel"] is False
    assert base["motivo"] == "validade_evidencia_desconhecida"


def test_rodrigo_zin_nao_recebe_musica_ou_generos_inventados() -> None:
    fala = (
        'Isso é ótimo! Rodrigo Zin tem um estilo que combina MPB, jazz e pop. '
        'Uma das músicas mais conhecidas dele, "Só o Ritmo Sente", é um clássico.'
    )
    resultado = validar_fala_com_fundamentacao(
        fala,
        fundamentacao=_sem_fonte("Rodrigo Zin"),
        texto_usuario="eu também gosto das músicas dele",
    )
    assert "Só o Ritmo Sente" not in resultado["fala"]
    assert "jazz" not in resultado["fala"].casefold()
    assert "obra_sem_evidencia" in resultado["problemas"]
    assert "caracteristica_sem_evidencia" in resultado["problemas"]


def test_obra_citada_na_fonte_pode_ser_mencionada() -> None:
    base = _com_fonte(
        "Artista Exemplo",
        'Artista Exemplo lançou a canção "Caminho Azul" em seu primeiro trabalho.',
    )
    resultado = validar_fala_com_fundamentacao(
        'Eu começaria por "Caminho Azul", que aparece entre os trabalhos dele.',
        fundamentacao=base,
        texto_usuario="qual música você recomenda?",
    )
    assert resultado["acao"] == "aceita"
    assert resultado["problemas"] == []


def test_data_de_filme_sem_evidencia_e_removida() -> None:
    resultado = validar_fala_com_fundamentacao(
        "Esse filme foi lançado em 2019 e ganhou vários prêmios.",
        fundamentacao=_sem_fonte("Filme Exemplo"),
        texto_usuario="o que acha desse filme?",
    )
    assert "2019" not in resultado["fala"]
    assert "data_sem_evidencia" in resultado["problemas"]
    assert "caracteristica_sem_evidencia" in resultado["problemas"]


def test_especificacao_tecnica_sem_evidencia_e_removida() -> None:
    resultado = validar_fala_com_fundamentacao(
        "Esse aparelho tem 16 GB de RAM e processador de oito núcleos.",
        fundamentacao=_sem_fonte("Aparelho Exemplo"),
        texto_usuario="esse aparelho é bom?",
    )
    assert "16 GB" not in resultado["fala"]
    assert "medida_sem_evidencia" in resultado["problemas"]


def test_laylay_nao_finge_ter_consumido_catalogo() -> None:
    resultado = validar_fala_com_fundamentacao(
        "Eu sou fã dele e já ouvi todo o catálogo.",
        fundamentacao=_com_fonte("Artista Exemplo", "Artista Exemplo é músico."),
        texto_usuario="você gosta dele?",
    )
    assert "sou fã" not in resultado["fala"].casefold()
    assert "familiaridade_inventada" in resultado["problemas"]


def test_opiniao_subjetiva_sem_detalhe_continua_permitida() -> None:
    resultado = validar_fala_com_fundamentacao(
        "Pelo que você contou, ele me parece interessante e eu fiquei curiosa.",
        fundamentacao=_sem_fonte("Tema Exemplo"),
        texto_usuario="eu gosto bastante dele",
    )
    assert resultado["acao"] == "aceita"


def test_pesquisa_auxiliar_sem_fonte_nao_sequestra_preferencia_declarada() -> None:
    base = _sem_fonte("rock")
    base.update({
        "papel_cooperativo": "enriquecimento_auxiliar",
        "nao_substitui_resposta_principal": True,
        "declaracao_pessoal_explicita": True,
    })
    resultado = validar_fala_com_fundamentacao(
        "Rock, boa. Isso já me dá uma pista melhor do seu gosto.",
        fundamentacao=base,
        texto_usuario="eu gosto de rock",
    )

    assert resultado["acao"] == "aceita"
    assert "não encontrei" not in resultado["fala"].casefold()


def test_afirmacao_declarativa_sobre_qualquer_tema_exige_base() -> None:
    resultado = validar_fala_com_fundamentacao(
        "Empresa Exemplo fabrica carros elétricos em três países.",
        fundamentacao=_sem_fonte("Empresa Exemplo"),
        texto_usuario="o que acha da Empresa Exemplo?",
    )
    assert "fabrica carros" not in resultado["fala"]
    assert "alegacao_especifica_sem_fonte" in resultado["problemas"]


def test_verificador_final_aplica_fundamentacao() -> None:
    verificacao = verificar_fala_turno(
        'Uma obra famosa dele é "Título Inventado".',
        plano={
            "texto_usuario": "eu gosto das obras dele",
            "ato_principal": "conversa",
            "fundamentacao_factual": _sem_fonte("Autor Exemplo"),
        },
    )
    assert "Título Inventado" not in verificacao["fala"]
    assert "obra_sem_evidencia" in verificacao["problemas"]


def test_fundamentacao_entra_no_prompt_como_limite_fechado() -> None:
    prompt = resumo_mente_integrada_para_prompt(
        texto_usuario="fala sobre ele",
        ctx={},
        percepcao={},
        mente={"fundamentacao_factual_turno": _com_fonte(
            "Tema Exemplo", "Tema Exemplo é descrito pela fonte desta forma."
        )},
    )
    assert "FUNDAMENTAÇÃO FACTUAL FECHADA DO TURNO" in prompt
    assert "A evidência é um limite" in prompt
    assert "PROVENIÊNCIA DA INFORMAÇÃO DO TURNO" in prompt
    assert "tipo=informacao_externa" in prompt
    assert "REGRA DE PROVENIÊNCIA" in prompt
