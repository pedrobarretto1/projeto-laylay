from __future__ import annotations

import ast
from pathlib import Path

from memoria_sqlite import MemoriaSQLite
from mente_laylay.integracao.registro_conversa_llm import EstadoConversaRuntime
from mente_laylay.memoria_mental.conversas_runtime import (
    GerenciadorConversasRuntime,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
)
from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
from mente_laylay.memoria_mental.estado_continuidades import (
    estado_continuidades_inicial,
)
from mente_laylay.memoria_mental.persistencia_memoria import (
    PersistenciaMemoriaRuntime,
)


PROMPT = "Você é a Laylay."


def _estado() -> EstadoCompartilhadoRuntime:
    return EstadoCompartilhadoRuntime(
        continuidades=estado_continuidades_inicial(),
        musical={},
        percepcao={},
        mental=criar_estado_mental_inicial(),
        conversacional={
            "current_emotion": "calma",
            "is_speaking": False,
            "topicos_conversa_recente": [],
            "ultimo_topico_conversa": "",
            "ultimo_topico_ts": 0.0,
        },
        memoria_conversa={
            "messages": [{"role": "system", "content": PROMPT}],
            "bordoes": [],
            "resumo_conversa": "",
            "memoria_fatos": [],
            "memoria_eventos": [],
            "historico_long_term": "",
        },
    )


def _gerenciador(tmp_path, estado=None):
    compartilhado = estado or _estado()
    memoria = MemoriaSQLite(str(tmp_path / "memoria.sqlite"))
    runtime = GerenciadorConversasRuntime(
        memoria_sqlite=memoria,
        estado_compartilhado=compartilhado,
        base_system_prompt=PROMPT,
        log=lambda *_args: None,
    )
    return memoria, compartilhado, runtime


def _conteudos(mensagens):
    return [
        str(item.get("content") or "")
        for item in mensagens
        if item.get("role") != "system"
    ]


def test_migra_historico_legado_uma_unica_vez(tmp_path) -> None:
    memoria, _estado_vivo, runtime = _gerenciador(tmp_path)
    legado = [
        {"role": "system", "content": "prompt antigo"},
        {"role": "user", "content": "Estamos falando do projeto Aurora"},
        {"role": "assistant", "content": "Entendi o projeto Aurora."},
    ]

    primeira = runtime.inicializar_legado(mensagens=legado, resumo="Aurora")
    segunda = runtime.inicializar_legado(
        mensagens=[{"role": "user", "content": "não deve duplicar"}],
        resumo="outro",
    )

    assert primeira["id"] == segunda["id"]
    assert primeira["titulo"] == "Conversa anterior"
    assert len(memoria.listar_conversas()) == 1
    assert _conteudos(runtime.mensagens()) == [
        "Estamos falando do projeto Aurora",
        "Entendi o projeto Aurora.",
    ]


def test_troca_isola_historico_referencias_pendencia_e_topico(tmp_path) -> None:
    _memoria, estado, runtime = _gerenciador(tmp_path)
    estado.atualizar_campos("mental", nome_usuario="Pedro")
    estado.atualizar_campos(
        "mental",
        ultimo_arquivo="aurora.py",
        ultimo_caminho_arquivo=r"C:\projetos\aurora.py",
        pendencia_acao_canonica={"intent": "DELETE_ITEM", "alvo": "aurora.py"},
        foco_conversacional_topico="projeto Aurora",
        foco_conversacional_ts=100.0,
    )
    estado.atualizar_campos(
        "conversacional",
        ultimo_topico_conversa="projeto Aurora",
        topicos_conversa_recente=["Aurora"],
    )
    conversa_a = runtime.inicializar_legado(
        mensagens=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": "Vamos trabalhar no Aurora"},
        ],
    )

    conversa_b = runtime.criar("Música")

    assert estado.mental["nome_usuario"] == "Pedro"
    assert estado.mental["ultimo_arquivo"] == ""
    assert dict(estado.mental["pendencia_acao_canonica"]) == {}
    assert estado.conversacional["ultimo_topico_conversa"] == ""
    estado.atualizar_campos(
        "mental",
        ultimo_arquivo="playlist.json",
        pendencia_acao_canonica={"intent": "PLAYLIST_ADD", "alvo": "rock"},
    )
    estado.atualizar_campos(
        "conversacional", ultimo_topico_conversa="música",
    )
    runtime.substituir_mensagens([
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": "Vamos falar de música"},
    ])

    assert runtime.selecionar(conversa_a["id"])
    assert estado.mental["nome_usuario"] == "Pedro"
    assert estado.mental["ultimo_arquivo"] == "aurora.py"
    assert dict(estado.mental["pendencia_acao_canonica"])["intent"] == "DELETE_ITEM"
    assert estado.conversacional["ultimo_topico_conversa"] == "projeto Aurora"
    assert _conteudos(runtime.mensagens()) == ["Vamos trabalhar no Aurora"]

    assert runtime.selecionar(conversa_b["id"])
    assert estado.mental["ultimo_arquivo"] == "playlist.json"
    assert dict(estado.mental["pendencia_acao_canonica"])["intent"] == "PLAYLIST_ADD"
    assert estado.conversacional["ultimo_topico_conversa"] == "música"
    assert _conteudos(runtime.mensagens()) == ["Vamos falar de música"]


def test_resposta_tardia_volta_ao_chat_em_que_o_turno_nasceu(tmp_path) -> None:
    _memoria, estado, runtime = _gerenciador(tmp_path)
    conversa_a = runtime.inicializar_legado(
        mensagens=[{"role": "system", "content": PROMPT}],
    )
    porta = EstadoConversaRuntime(
        getter=lambda: list(estado.memoria_conversa.get("messages") or []),
        setter=lambda mensagens: estado.atualizar_campos(
            "memoria_conversa", messages=mensagens,
        ),
        conversation_id_getter=runtime.id_ativo,
        getter_conversa=runtime.mensagens,
        setter_conversa=runtime.substituir_mensagens,
    )

    porta.iniciar_turno("turno-a", "Pergunta demorada do Aurora")
    conversa_b = runtime.criar("Conversa rápida")
    porta.concluir_turno("turno-a", "Resposta final do Aurora")

    assert _conteudos(runtime.mensagens(conversa_a["id"])) == [
        "Pergunta demorada do Aurora", "Resposta final do Aurora",
    ]
    assert _conteudos(runtime.mensagens(conversa_b["id"])) == []
    assert runtime.id_ativo() == conversa_b["id"]


def test_exclusao_apaga_contexto_e_impede_escrita_tardia(tmp_path) -> None:
    memoria, estado, runtime = _gerenciador(tmp_path)
    conversa = runtime.inicializar_legado(
        mensagens=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": "segredo só deste chat"},
        ],
    )
    estado.atualizar_campos("mental", nome_usuario="Pedro")
    estado.atualizar_campos("mental", ultimo_arquivo="segredo.txt")

    assert runtime.excluir(conversa["id"]) is True
    assert memoria.carregar_conversa(conversa["id"]) is None
    assert memoria.salvar_conversa(
        conversa["id"],
        mensagens=[{"role": "assistant", "content": "resposta atrasada"}],
        contexto={"mental": {"ultimo_arquivo": "ressuscitado.txt"}},
    ) is False
    assert estado.mental["nome_usuario"] == "Pedro"
    assert runtime.id_ativo() != conversa["id"]
    assert "segredo só deste chat" not in repr(runtime.mensagens())


def test_reinicio_reabre_somente_a_conversa_ativa_sem_remigrar_legado(
    tmp_path,
) -> None:
    _memoria, _estado_um, runtime_um = _gerenciador(tmp_path)
    conversa_a = runtime_um.inicializar_legado(
        mensagens=[{"role": "user", "content": "chat antigo"}],
    )
    conversa_b = runtime_um.criar("Chat ativo")
    runtime_um.substituir_mensagens([
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": "conteúdo do chat ativo"},
    ])
    runtime_um.salvar_ativa()

    _memoria_dois, _estado_dois, runtime_dois = _gerenciador(tmp_path, _estado())
    restaurada = runtime_dois.inicializar_legado(
        mensagens=[{"role": "user", "content": "legado não deve vencer"}],
    )

    assert restaurada["id"] == conversa_b["id"]
    assert restaurada["id"] != conversa_a["id"]
    assert _conteudos(runtime_dois.mensagens()) == ["conteúdo do chat ativo"]
    assert len(runtime_dois.listar()) == 2
    assert runtime_dois.diagnostico()["isolamento_contexto"] is True


def test_persistencia_principal_migra_e_salva_o_chat_ativo(tmp_path) -> None:
    memoria, estado, conversas = _gerenciador(tmp_path)
    memoria.salvar_estado(
        messages=[
            {"role": "system", "content": "prompt antigo"},
            {"role": "user", "content": "histórico vindo do estado legado"},
        ],
        resumo_conversa="resumo legado",
        current_emotion="irritada",
        nome_usuario="Pedro",
    )
    persistencia = PersistenciaMemoriaRuntime(
        memoria_sqlite=memoria,
        base_system_prompt=PROMPT,
        estado_obter=estado.obter,
        estado_atualizar=estado.atualizar_campos,
        conversas_runtime=conversas,
        log=lambda *_args: None,
    )

    persistencia.carregar()

    ativa_id = conversas.id_ativo()
    assert ativa_id
    assert _conteudos(conversas.mensagens()) == [
        "histórico vindo do estado legado",
    ]
    # O contexto migrado do chat vence a cópia conversacional global antiga.
    assert estado.conversacional["current_emotion"] == "calma"
    estado.atualizar_campos(
        "memoria_conversa",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": "mensagem depois da migração"},
        ],
    )

    assert persistencia.salvar() is True
    assert _conteudos(memoria.carregar_conversa(ativa_id)["mensagens"]) == [
        "mensagem depois da migração",
    ]


def test_composicao_real_liga_conversas_a_persistencia_e_aos_turnos() -> None:
    raiz = Path(__file__).resolve().parents[1] / "laylay.py"
    arvore = ast.parse(raiz.read_text(encoding="utf-8"))
    chamadas: dict[str, ast.Call] = {}
    for no in ast.walk(arvore):
        if not isinstance(no, ast.Assign) or len(no.targets) != 1:
            continue
        alvo = no.targets[0]
        if isinstance(alvo, ast.Name) and isinstance(no.value, ast.Call):
            chamadas[alvo.id] = no.value

    gerenciador = chamadas["_gerenciador_conversas_runtime"]
    persistencia = chamadas["_persistencia_memoria_runtime"]
    estado_conversa = chamadas["_estado_conversa_runtime"]
    kwargs_gerenciador = {item.arg for item in gerenciador.keywords}
    kwargs_persistencia = {item.arg for item in persistencia.keywords}
    kwargs_estado = {item.arg for item in estado_conversa.keywords}

    assert {
        "memoria_sqlite", "estado_compartilhado", "base_system_prompt",
    }.issubset(kwargs_gerenciador)
    assert "conversas_runtime" in kwargs_persistencia
    assert {
        "conversation_id_getter", "getter_conversa", "setter_conversa",
    }.issubset(kwargs_estado)
