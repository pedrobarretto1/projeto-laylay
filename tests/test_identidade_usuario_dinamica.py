from __future__ import annotations

from memoria_sqlite import MemoriaSQLite
from mente_laylay.autonomia.pre_fluxo_contextual import processar_identidade_usuario
from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime
from mente_laylay.memoria_mental.contexto_compartilhado import estado_mental_inicial
from mente_laylay.memoria_mental.identidade_usuario import (
    carregar_nome_usuario_confirmado,
    contexto_identidade_usuario,
    salvar_nome_usuario_confirmado,
)


def test_estado_novo_nao_presume_nome() -> None:
    assert estado_mental_inicial()["nome_usuario"] == ""
    contexto = contexto_identidade_usuario("")
    assert "ainda não informou" in contexto
    assert "Pedro" not in contexto


def test_nome_confirmado_substitui_identidade_anterior_e_persiste(tmp_path) -> None:
    memoria = MemoriaSQLite(str(tmp_path / "mente.sqlite"))
    assert salvar_nome_usuario_confirmado(memoria, "Pedro", texto_original="meu nome é Pedro")
    assert carregar_nome_usuario_confirmado(memoria) == "Pedro"

    assert salvar_nome_usuario_confirmado(memoria, "bia", texto_original="pode me chamar de Bia")
    assert carregar_nome_usuario_confirmado(memoria) == "Bia"
    ativos = [
        item
        for item in memoria.listar_aprendizados_semanticos(limit=20)
        if item.get("chave_semantica") == "identidade:nome_usuario"
        and item.get("status") == "ativo"
    ]
    assert len(ativos) == 1
    assert ativos[0]["valor"] == "Bia"
    assert ativos[0]["confirmado_usuario"] is True


def test_nome_nao_confirmado_nao_vira_identidade(tmp_path) -> None:
    memoria = MemoriaSQLite(str(tmp_path / "mente.sqlite"))
    memoria.salvar_aprendizado_semantico(
        tipo="identidade",
        gatilho="nome do usuário",
        valor="Nome Inventado",
        regra="Talvez seja Nome Inventado.",
        status="ativo",
        confirmado_usuario=False,
    )
    assert carregar_nome_usuario_confirmado(memoria) == ""


def test_ensino_explicito_atualiza_estado_e_chama_persistencia() -> None:
    falas: list[str] = []
    persistidos: list[tuple[str, str]] = []
    mente = {"nome_usuario": ""}
    ctx = {
        "mente_integrada_estado": mente,
        "_normalizar_texto_com_apelidos": lambda texto: texto.casefold(),
        "_salvar_identidade_usuario": lambda nome, texto: persistidos.append((nome, texto)) or True,
        "_emitir_resposta_curta": lambda _texto, fala, **_kwargs: falas.append(fala),
    }

    tratado, etapa = processar_identidade_usuario(ctx, "pode me chamar de ana clara")

    assert tratado is True
    assert etapa == "identidade_usuario"
    assert mente["nome_usuario"] == "Ana Clara"
    assert persistidos == [("Ana Clara", "pode me chamar de ana clara")]
    assert "Ana Clara" in falas[-1]


def test_falha_de_persistencia_nao_finge_que_aprendeu() -> None:
    falas: list[str] = []
    mente = {"nome_usuario": ""}
    ctx = {
        "mente_integrada_estado": mente,
        "_normalizar_texto_com_apelidos": lambda texto: texto.casefold(),
        "_salvar_identidade_usuario": lambda _nome, _texto: False,
        "_emitir_resposta_curta": lambda _texto, fala, **_kwargs: falas.append(fala),
    }

    tratado, etapa = processar_identidade_usuario(ctx, "meu nome é carlos")

    assert tratado is True
    assert etapa == "identidade_usuario_falha_persistencia"
    assert mente["nome_usuario"] == ""
    assert "não consegui guardá-lo" in falas[-1]


def test_prompt_recebe_apenas_o_nome_dinamico_confirmado() -> None:
    runtime = ContextoPromptRuntime(
        memoria_sqlite=None,
        resumo_mente_integrada=lambda _texto: "",
        formatar_playlists=lambda: "",
        get_status_humor_prompt=lambda: "",
        base_system_prompt="Você é Laylay.",
        estado_getter=lambda: {
            "messages": [],
            "nome_usuario": "Beatriz",
            "turno_atual": {},
        },
    )

    mensagens, _retrato = runtime.preparar("oi")
    system = mensagens[0]["content"]
    assert "nome é Beatriz" in system
    assert "Pedro" not in system
