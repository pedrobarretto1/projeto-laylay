from __future__ import annotations

from types import SimpleNamespace

import pytest

from mente_laylay.arquivos.execucao_arquivos import executar_intencao_arquivos
from mente_laylay.arquivos.pesquisa_semantica import PesquisaSemanticaArquivosRuntime
from mente_laylay.arquivos.roteador_arquivos import (
    detectar_intencao_arquivos,
    extrair_delete_pasta_arquivo,
)
from mente_laylay.autonomia.agendamento_mental import (
    AgendaRuntime,
    extrair_agendamento_local,
    extrair_parametros_temporais_lembrete,
)
from mente_laylay.autonomia.executor_agenda import (
    DependenciasExecutorAgenda,
    executar_intencao_agenda,
)
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.pre_fluxo_contextual import (
    processar_consulta_sistema_local,
)
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.roteador_deterministico import detectar_volume_ou_midia
from mente_laylay.cognicao.memoria_visual import MemoriaVisualRuntime
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.confirmacao_llm import _motivo_contrato_invalido
from mente_laylay.personalidade.higiene_fala import limpar_fala_operacional
from mente_laylay.integracao.adaptadores_aplicacao_runtime import (
    AdaptadoresAplicacaoRuntime,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.contexto_imediato import (
    referencia_contextual_imediata,
    resolver_comando_acao_geral_contextual,
)
from mente_laylay.integracao.registro_arquivos import registrar_arquivos_leitura
from mente_laylay.iot.runtime import RuntimeIoT
from mente_laylay.memoria_mental.continuidade_geral import (
    registrar_evento_continuidade,
    resolver_continuacao_aditiva,
)


class _MemoriaIoTEmMemoria:
    def __init__(self) -> None:
        self.dispositivos: dict[str, dict] = {}

    def salvar_dispositivo_iot(self, dados):
        self.dispositivos[dados["nome"]] = dict(dados)
        return dict(dados)

    def listar_dispositivos_iot(self, ambiente="", *, somente_ativos=True):
        return [
            dict(item)
            for item in self.dispositivos.values()
            if (not ambiente or item["ambiente"] == ambiente)
            and (not somente_ativos or item.get("ativo", True))
        ]

    def atualizar_estado_iot(self, nome, estado, **_kwargs):
        self.dispositivos[nome]["estado"] = dict(estado)
        return dict(estado)

    def registrar_historico_iot(self, nome, **dados):
        return {"nome": nome, **dados}


def _contexto_deterministico(estado: dict | None = None) -> dict:
    return {
        "normalizar_texto": lambda texto: str(texto).casefold(),
        "texto_conversa_casual_sem_acao": lambda _texto: False,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: False,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "limpar_nome_playlist": lambda texto: str(texto).strip(),
        "extrair_nome_playlist": lambda _texto: "",
        "detectar_playlist_nome_direto": lambda _texto: "",
        "normalizar_query_musical": lambda texto: str(texto).strip(),
        "extrair_intencao_abrir_app": lambda _texto: None,
        "sites_diretos": {},
        "apps_map": {},
        "mente_integrada_estado": dict(estado or {}),
    }


def test_fecha_essa_aba_usa_open_url_confirmado_em_vez_de_musica_antiga() -> None:
    estado = registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "OPEN_URL",
            "params": {"alvo": "Prime Video", "url": "https://primevideo.com"},
            "status": "site_aberto",
            "executou": True,
            "confirmado": True,
        },
        "Abre o Prime Video.",
    )
    estado["ultimo_site_aba"] = "Saturno"

    referencia = referencia_contextual_imediata(
        mente_integrada_estado=estado,
        foco_vivo={"tipo": "musica", "alvo": "Saturno"},
        texto_atual="Fecha essa aba.",
        normalizar_texto=lambda valor: str(valor).casefold(),
    )

    assert referencia["tipo"] == "site"
    assert referencia["alvo"] == "Prime Video"
    assert referencia["origem_continuidade"] == "contrato_confirmado"
    assert resolver_comando_acao_geral_contextual(
        "Fecha essa aba.", referencia
    ) == {
        "intent": "CLOSE_TAB",
        "params": {"alvo": "Prime Video"},
    }


def test_primeiro_resultado_web_vence_resultado_local_antigo() -> None:
    estado = {
        "ultima_acao_intent": "SEARCH",
        "ultima_acao_status": "busca_aberta",
        "ultima_acao_confirmada": True,
        "ultima_acao_params": {"query": "documentação oficial do Python"},
        "ultima_estrutura_arquivo_params": {
            "arquivo_nome": "auditoria gaivota.txt",
            "caminho": r"C:\\tmp\\auditoria gaivota.txt",
        },
        "resultados_arquivo_recentes": [
            {"nome": "auditoria gaivota.txt", "caminho": r"C:\\tmp\\auditoria gaivota.txt"}
        ],
    }

    assert detectar_intencao_deterministica_mente(
        "Abre o primeiro resultado.",
        _contexto_deterministico(estado),
    ) == {
        "intent": "SEARCH",
        "params": {
            "query": "documentação oficial do Python",
            "abrir_resultado": 1,
            "origem": "continuacao_resultado_web",
        },
    }


def test_apaga_novamente_nao_inclui_marcador_no_nome() -> None:
    assert extrair_delete_pasta_arquivo(
        "Apaga novamente o arquivo auditoria gaivota.txt."
    ) == {
        "alvo": "auditoria gaivota.txt",
        "tipo": "arquivo",
    }


def test_horario_natural_com_e_preserva_hora_e_minuto() -> None:
    assert extrair_parametros_temporais_lembrete(
        "Me lembra de beber água amanhã às 10 e 37."
    ) == {
        "data_hora": "amanhã",
        "hora_alvo": "10:37",
    }
    assert extrair_parametros_temporais_lembrete(
        "Guarda essa ideia e me lembra dela amanhã às 15 e 20."
    ) == {
        "data_hora": "amanhã",
        "hora_alvo": "15:20",
    }
    assert extrair_agendamento_local(
        "Me lembra de beber água amanhã às 10 e 37.",
        lambda valor: str(valor).casefold(),
    ) == {
        "intent": "AGENDAR_LEMBRETE",
        "params": {
            "descricao": "beber água",
            "data_hora": "amanhã",
            "hora_alvo": "10:37",
        },
    }


def test_cancelar_nao_reconfirma_lembrete_que_ja_estava_inativo() -> None:
    agenda = [{
        "id": "agua-antigo",
        "nome": "beber água",
        "descricao": "beber água",
        "ativo": False,
    }]
    eventos: list[tuple] = []

    def transacionar(mutador):
        mutador(agenda)
        return True

    deps = DependenciasExecutorAgenda(
        marcar_resultado=lambda status, **kwargs: eventos.append(
            (status, kwargs)
        ),
        falar_por_status=lambda *_args, **_kwargs: None,
    )
    executar_intencao_agenda(
        "CANCELAR_AGENDAMENTO",
        {"alvo": "beber água"},
        "Cancela o lembrete de beber água.",
        {"_agendamentos_transacionar": transacionar},
        deps,
    )

    assert agenda[0]["ativo"] is False
    assert eventos == [(
        "falha_execucao",
        {"executou": False, "confirmado": False},
    )]


def test_leia_conteudo_dele_e_novamente_usa_leitura_local_segura(tmp_path) -> None:
    arquivo = tmp_path / "auditoria gaivota.txt"
    arquivo.write_text("primeira linha\nsegunda linha", encoding="utf-8")
    estado = {
        "ultima_estrutura_arquivo_params": {
            "tipo": "arquivo",
            "arquivo_nome": arquivo.name,
            "caminho": str(arquivo),
        },
    }
    esperado = {
        "intent": "FILE_READ",
        "params": {
            "caminho": str(arquivo),
            "alvo": arquivo.name,
            "referencia_contextual": True,
        },
    }
    for frase in ("Leia o conteúdo dele.", "Leia esse arquivo novamente."):
        assert detectar_intencao_arquivos(
            frase,
            params_cb=lambda **kwargs: kwargs,
            estado_mental=estado,
            normalizar_texto=lambda valor: str(valor).casefold(),
        ) == esperado

    porta = registrar_arquivos_leitura(PesquisaSemanticaArquivosRuntime(
        raizes=[tmp_path],
        log=lambda *_args: None,
    ))
    falas: list[str] = []
    resultados: list[tuple] = []
    assert executar_intencao_arquivos(
        "FILE_READ",
        esperado["params"],
        "pc_a",
        {"falar_com_lipsync": lambda fala, *_args: falas.append(fala)},
        texto_original="Leia o conteúdo dele.",
        marcar_resultado=lambda status, executou, **kwargs: resultados.append(
            (status, executou, kwargs)
        ),
        registrar_arquivo=lambda *_args: None,
        item_local_existe=lambda *_args: True,
        resolver_caminho_local=lambda valor: valor,
        resolver_referencia_arquivo_contextual=lambda valor, *_args: valor,
        arquivos_leitura=porta,
    ) is True

    assert resultados == [(
        "conteudo_lido",
        True,
        {
            "alvo_resolvido": str(arquivo),
            "confirmado": True,
        },
    )]
    assert len(falas) == 1
    assert "primeira linha" in falas[0]
    assert "segunda linha" in falas[0]


def test_fecha_esse_arquivo_preserva_referencia_apos_leitura() -> None:
    caminho = r"C:\Users\pbarr\Downloads\auditoria gaivota.txt"
    estado = registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "FILE_READ",
            "params": {"caminho": caminho, "alvo": "auditoria gaivota.txt"},
            "status": "conteudo_lido",
            "executou": True,
            "confirmado": True,
        },
        "Leia o conteúdo dele.",
    )
    estado["ultima_estrutura_arquivo_params"] = {
        "tipo": "arquivo",
        "arquivo_nome": "auditoria gaivota.txt",
        "caminho": caminho,
    }

    referencia = referencia_contextual_imediata(
        mente_integrada_estado=estado,
        foco_vivo={},
        texto_atual="Fecha esse arquivo.",
        normalizar_texto=lambda valor: str(valor).casefold(),
    )

    assert referencia["tipo"] == "arquivo"
    assert resolver_comando_acao_geral_contextual(
        "Fecha esse arquivo.", referencia,
    ) == {
        "intent": "CLOSE_APP",
        "params": {
            "nome_app": "auditoria gaivota.txt",
            "janela_titulo": "auditoria gaivota.txt",
            "referencia_arquivo": True,
        },
    }


def test_deixa_ela_azul_herda_lampada_apos_consulta_iot_falhar() -> None:
    estado = registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "IOT_STATUS",
            "params": {"acao": "status", "alvo": "lampada_quarto"},
            "status": "falha_execucao",
            "executou": False,
            "confirmado": False,
        },
        "Como ela está agora?",
    )
    assert estado["ultimo_dispositivo_iot"] == "lampada_quarto"
    runtime = RuntimeIoT(
        memoria_sqlite=_MemoriaIoTEmMemoria(),
        falar=lambda *_args: None,
        estado_mental_getter=lambda: estado,
        emitir_fala=False,
        modo="simulado",
        log=lambda *_args: None,
    )

    resultado = runtime.detectar("Deixa ela azul.", estado)

    assert resultado["intent"] == "IOT_CONTROL"
    assert resultado["params"]["acao"] == "ajustar_cor"
    assert resultado["params"]["alvo"] == "lampada_quarto"
    assert resultado["params"]["cor"] == "azul"


def test_essa_tambem_reavalia_faixa_ausente_sem_cair_na_llm() -> None:
    estado = registrar_evento_continuidade(
        estado_mental_inicial(),
        evento="acao",
        intent="PLAYLIST_ADD",
        alvo="roteiro teste",
        params={"nome_playlist": "roteiro teste"},
        status="faixa_atual_indisponivel",
    )

    assert resolver_continuacao_aditiva(estado, texto="Essa também.") == {
        "intent": "PLAYLIST_ADD",
        "params": {
            "nome_playlist": "roteiro teste",
            "referencia_contextual": True,
        },
    }


def test_controles_e_estado_musical_naturais_nao_caem_na_conversa() -> None:
    casos = {
        "Qual é o estado da música agora?": {
            "intent": "MUSIC_STATUS",
            "params": {
                "acao": "status",
                "platform": "music",
                "somente_leitura": True,
            },
        },
        "Vai para a próxima faixa.": {
            "intent": "MEDIA_CONTROL",
            "params": {"acao": "next"},
        },
        "Volta para a faixa anterior.": {
            "intent": "MEDIA_CONTROL",
            "params": {"acao": "prev"},
        },
    }
    for frase, esperado in casos.items():
        assert detectar_volume_ou_midia(
            frase.casefold(),
            params_cb=lambda **kwargs: kwargs,
        ) == esperado


def test_orquestrador_promove_controles_de_faixa_antes_do_filtro_conversacional() -> None:
    contexto = _contexto_deterministico({
        "ultima_acao_intent": "MUSIC_STATUS",
        "ultima_acao_status": "midia_status_consultado",
    })
    # Reproduz a classificação que causou a falha real: o atalho genérico
    # preferia a IA, mas o controle explícito ainda precisa vencer.
    contexto["fluxo_prioritario_da_ia"] = lambda _texto: True
    contexto["contexto_musical_ativo"] = lambda: True

    assert detectar_intencao_deterministica_mente(
        "Vai para a próxima faixa.", contexto,
    ) == {"intent": "MEDIA_CONTROL", "params": {"acao": "next"}}
    assert detectar_intencao_deterministica_mente(
        "Volta para a faixa anterior.", contexto,
    ) == {"intent": "MEDIA_CONTROL", "params": {"acao": "prev"}}
    assert detectar_intencao_deterministica_mente(
        "Talvez eu vá para a próxima faixa.", contexto,
    ) is None


def test_consulta_de_app_observa_sem_puxar_janela_para_foco() -> None:
    falas: list[str] = []
    registros: list[tuple] = []
    consultas: list[str] = []

    tratado, rota = processar_consulta_sistema_local({
        "_resolver_alvo_ambiente": lambda nome: (
            consultas.append(nome)
            or {"programa_aberto": True, "programa_em_foco": False}
        ),
        "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        "_registrar_resultado_execucao": (
            lambda *args, **kwargs: registros.append((args, kwargs))
        ),
    }, "O Opera continua aberto?")

    assert tratado is True
    assert rota == "consulta_estado_programa"
    assert consultas == ["opera"]
    assert falas == ["Opera está aberto, mas não está em foco."]
    assert registros[-1][0][0]["intent"] == "LIST_WINDOWS"


def test_higiene_operacional_nao_separa_hora_e_minuto() -> None:
    assert limpar_fala_operacional(
        "Anotado. Vou te lembrar amanhã às 10: 37."
    ) == "Anotado. Vou te lembrar amanhã às 10:37."


@pytest.mark.parametrize(
    ("texto", "comando"),
    (
        (
            "Abre o primeiro resultado.",
            {
                "intent": "SEARCH",
                "params": {
                    "query": "documentação oficial do Python",
                    "abrir_resultado": 1,
                    "origem": "continuacao_resultado_web",
                },
            },
        ),
        (
            "Volta para a aba anterior.",
            {"intent": "SWITCH_PREVIOUS_TAB", "params": {}},
        ),
        (
            "Vai para a próxima faixa.",
            {"intent": "MEDIA_CONTROL", "params": {"acao": "next"}},
        ),
        (
            "Volta para a faixa anterior.",
            {"intent": "MEDIA_CONTROL", "params": {"acao": "prev"}},
        ),
        (
            "Deixa ela azul.",
            {
                "intent": "IOT_CONTROL",
                "params": {
                    "acao": "ajustar_cor",
                    "alvo": "lampada_quarto",
                    "cor": "azul",
                },
            },
        ),
    ),
)
def test_porta_prioritaria_entrega_continuacoes_ao_executor_antes_de_arquivo_e_llm(
    texto: str,
    comando: dict,
) -> None:
    execucoes: list[tuple[dict, str]] = []
    registros: list[tuple] = []
    estado = SimpleNamespace(mental={
        "ultima_estrutura_arquivo_params": {
            "arquivo_nome": "auditoria gaivota.txt",
            "caminho": r"C:\\tmp\\auditoria gaivota.txt",
        },
        "resultados_arquivo_recentes": [{
            "nome": "auditoria gaivota.txt",
            "caminho": r"C:\\tmp\\auditoria gaivota.txt",
        }],
    })
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "detectar_intencao_deterministica": lambda recebido: (
                comando if recebido == texto else None
            ),
            "executar_intencao": lambda detectado, original: (
                execucoes.append((detectado, original)) or True
            ),
            "_registrar_resultado_execucao": (
                lambda *args, **kwargs: registros.append((args, kwargs))
            ),
            "resolver_comando_natural": lambda *_args: (_ for _ in ()).throw(
                AssertionError("a continuação canônica não pode cair na LLM")
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios(texto) is True
    assert execucoes == [(comando, texto)]
    assert registros[0][1]["origem"] == "prioritario_deterministico_contextual"


def test_resultado_operacional_limpa_pergunta_casual_anterior() -> None:
    class _Estado:
        def __init__(self) -> None:
            self.mental = {"plano_turno_atual": {"fase": "executado", "comandos": []}}

        def atualizar_campos(self, secao: str, **campos) -> None:
            assert secao == "mental"
            self.mental.update(campos)

    estado = _Estado()
    limpezas: list[bool] = []
    namespace = {
        "_registrar_resultado_execucao_base": lambda *_args, **_kwargs: None,
        "_limpar_pergunta_aberta": lambda: limpezas.append(True),
        "_estado_compartilhado_runtime": estado,
        "_atualizar_plano_turno_mente": lambda plano, **kwargs: {
            **plano, "comandos": kwargs["comandos"],
        },
        "_concluir_correcao_interpretacao_mente": lambda *_args, **_kwargs: {},
        "print": lambda *_args: None,
    }

    AdaptadoresAplicacaoRuntime(lambda: namespace).registrar_resultado_execucao(
        {"intent": "PLAYLIST_DELETE", "params": {"nome_playlist": "roteiro teste"}},
        "Apaga a playlist roteiro teste.",
        True,
    )

    assert limpezas == [True]


def test_saudacao_com_nome_de_terceiro_e_bloqueante_para_entrega() -> None:
    contrato = construir_contrato_semantico_fala(
        "Oi, Lay.",
        plano={"atos": [{"tipo": "saudacao"}]},
        funcao_comunicativa={"funcao": "saudacao"},
    )
    qualidade = avaliar_qualidade_comunicacao(
        "Oi, Lay.",
        "Oi, Nanda! Como vai?",
        plano={"contrato_fala": contrato},
    )

    assert qualidade["aceita"] is False
    assert "saudacao_inventou_vocativo" in qualidade["problemas_bloqueantes"]


def test_lembrete_identico_ativo_nao_e_duplicado() -> None:
    instante = 1_800_000_000.0
    agenda = [{
        "id": "existente",
        "tipo": "once",
        "ts_execucao": instante,
        "descricao": "revisar a interface da Laylay",
        "ativo": True,
        "comandos_no_disparo": [],
    }]
    resultados: list[tuple] = []
    falas: list[tuple] = []

    def transacionar(mutador):
        mutador(agenda)
        return True

    executar_intencao_agenda(
        "AGENDAR_LEMBRETE",
        {
            "descricao": "revisar a interface da Laylay",
            "atraso_segundos": 300,
        },
        "Me lembra de revisar a interface da Laylay daqui a cinco minutos.",
        {
            "_agendamentos_transacionar": transacionar,
        },
        DependenciasExecutorAgenda(
            marcar_resultado=lambda status, **kwargs: resultados.append(
                (status, kwargs)
            ),
            falar_por_status=lambda *args, **kwargs: falas.append((args, kwargs)),
        ),
    )

    # O relógio do executor é real; reposicionamos a entrada ao instante que
    # ele acabou de calcular e repetimos para provar a deduplicação temporal.
    assert len(agenda) == 2
    agenda[0]["ts_execucao"] = agenda[1]["ts_execucao"]
    agenda.pop()
    resultados.clear()
    falas.clear()
    executar_intencao_agenda(
        "AGENDAR_LEMBRETE",
        {
            "descricao": "  Revisar   a Interface da Laylay ",
            "atraso_segundos": 300,
        },
        "Me lembra disso outra vez.",
        {"_agendamentos_transacionar": transacionar},
        DependenciasExecutorAgenda(
            marcar_resultado=lambda status, **kwargs: resultados.append(
                (status, kwargs)
            ),
            falar_por_status=lambda *args, **kwargs: falas.append((args, kwargs)),
        ),
    )

    assert len(agenda) == 1
    assert resultados == [(
        "lembrete_ja_agendado",
        {"executou": False, "confirmado": True},
    )]
    assert "não dupliquei" in falas[0][0][1] or "Mantive só um" in falas[0][0][1]


def test_morfologia_corrompida_em_memoria_de_pessoa_e_reparada() -> None:
    contrato = construir_contrato_semantico_fala(
        "Nanda é minha amiga.",
        plano={"atos": [{"tipo": "informacao"}]},
        funcao_comunicativa={"funcao": "informacao"},
    )
    resultado = verificar_fala_turno(
        "Pegue-ia: Nanda é sua amiga.",
        plano={
            "texto_usuario": "Nanda é minha amiga.",
            "contrato_fala": contrato,
            "comandos": [{"intent": "PEOPLE_REMEMBER"}],
        },
    )

    assert resultado["aceita"] is False
    assert resultado["acao"] == "reparar"
    assert "morfologia_corrompida" in resultado["problemas"]
    assert "Nanda" in resultado["fala_contingencia"]


def test_confirmacao_operacional_preserva_horario_sem_espaco_interno() -> None:
    resultado = verificar_fala_turno(
        "Vou te lembrar amanhã às 10: 37.",
        plano={
            "texto_usuario": "Me lembra amanhã às 10 e 37.",
            "comandos": [{
                "intent": "AGENDAR_LEMBRETE",
                "status": "lembrete_agendado",
                "executou": True,
                "confirmado": True,
            }],
        },
    )

    assert resultado["fala"] == "Vou te lembrar amanhã às 10:37."


def test_autoria_de_fechamento_nao_inventa_abertura_nem_ano_de_filme() -> None:
    falha_fechar = ResultadoAcao(
        intent="CLOSE_APP",
        status="nao_encontrado",
        alvo="Aplicativo Totalmente Imaginário",
        executou=False,
        confirmado=False,
    )
    aba_fechada = ResultadoAcao(
        intent="CLOSE_TAB",
        status="aba_fechada",
        alvo="Prime Video",
        executou=True,
        confirmado=True,
    )

    assert _motivo_contrato_invalido(
        "Não achei o Aplicativo Totalmente Imaginário; não tem como abrir.",
        resultado=falha_fechar,
        classe="falha",
        status_declarado="nao_encontrado",
        alvo_declarado="Aplicativo Totalmente Imaginário",
    ) == "verbo_operacional_divergente"
    assert _motivo_contrato_invalido(
        "Fechei a aba do Prime Video, aquele filme de 2023.",
        resultado=aba_fechada,
        classe="sucesso",
        status_declarado="aba_fechada",
        alvo_declarado="Prime Video",
    ) == "detalhe_temporal_nao_evidenciado"


def test_listagem_da_agenda_prefere_descricao_integral_ao_nome_truncado(
    tmp_path,
) -> None:
    runtime = AgendaRuntime(
        str(tmp_path / "agenda.json"),
        falar_cb=lambda *_args: None,
        abrir_programa_cb=lambda *_args: None,
        enviar_pc_b_cb=lambda *_args: None,
        enviar_chrome_local_cb=lambda *_args: None,
        executar_comando_conteudo_cb=lambda *_args: None,
        log=lambda *_args: None,
    )
    item = {
        "nome": "revisar a interface da aba Sis",
        "descricao": "revisar a interface da aba Sistema",
        "hora": "10:37",
        "ativo": True,
    }

    fala = runtime.fala_estilosa([item])
    runtime.save([item])
    retrato = runtime.retrato_para_mente()

    assert "revisar a interface da aba Sistema às 10:37" in fala
    assert "aba Sis às" not in fala
    assert retrato["agendamentos"][0]["nome"] == "revisar a interface da aba Sistema"


def test_autoria_nao_inventa_hoje_ao_cancelar_lembrete_de_amanha() -> None:
    resultado = ResultadoAcao(
        intent="CANCELAR_AGENDAMENTO",
        status="agendamento_cancelado",
        alvo="revisar a interface da aba Sistema amanhã às 10:37",
        executou=True,
        confirmado=True,
    )

    assert _motivo_contrato_invalido(
        (
            "Cancelei revisar a interface da aba Sistema amanhã às 10:37. "
            "O seu compromisso de hoje perdeu a vez."
        ),
        resultado=resultado,
        classe="sucesso",
        status_declarado="agendamento_cancelado",
        alvo_declarado=resultado.alvo,
    ) == "detalhe_temporal_nao_evidenciado"


def test_autoria_nao_diz_que_playlist_aberta_ja_esta_audivel() -> None:
    resultado = ResultadoAcao(
        intent="LAYLAY_PLAYLIST_PLAY",
        status="playlist_aberta",
        alvo="vmz",
        executou=True,
        confirmado=True,
    )

    assert _motivo_contrato_invalido(
        "A playlist VMZ abriu e a primeira faixa está sendo ouvida pelo mundo inteiro.",
        resultado=resultado,
        classe="sucesso",
        status_declarado="playlist_aberta",
        alvo_declarado="vmz",
    ) == "audio_nao_observado"


def test_volta_para_aba_anterior_tem_intencao_canônica() -> None:
    assert detectar_intencao_deterministica_mente(
        "Volta para a aba anterior.",
        _contexto_deterministico(),
    ) == {
        "intent": "SWITCH_PREVIOUS_TAB",
        "params": {},
    }


def test_continua_daquele_ponto_reutiliza_resultado_visual_recente() -> None:
    runtime = MemoriaVisualRuntime(namespace_getter=lambda: {})
    runtime._registrar_resultado({
        "ok": True,
        "descricao": "A tela mostra o ChatGPT e uma conversa ativa…",
        "descricao_completa": (
            "A tela mostra o ChatGPT e uma conversa ativa sobre a Laylay. "
            "Na lateral aparecem outros tópicos recentes."
        ),
        "origem": "pc_a",
    })

    comando = detectar_intencao_deterministica_mente(
        "Continua daquele ponto.",
        _contexto_deterministico(),
    )
    consulta = runtime.consultar_ultimo(modo="continuar")

    assert comando == {
        "intent": "VISION_QUERY",
        "params": {
            "acao": "consultar_contexto_visual",
            "modo": "continuar",
        },
    }
    assert consulta["ok"] is True
    assert "Na lateral" in consulta["descricao"]
    assert consulta["descricao"] != "A tela mostra o ChatGPT e uma conversa ativa…"
