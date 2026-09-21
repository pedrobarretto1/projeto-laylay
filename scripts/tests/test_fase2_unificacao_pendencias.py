from __future__ import annotations

from mente_laylay.memoria_mental.ciclo_vida_contexto import aplicar_ciclo_vida_contexto
from mente_laylay.memoria_mental.pendencia_acao import (
    CHAVE_PENDENCIA_ACAO,
    PendenciaAcaoRuntime,
)
from mente_laylay.memoria_mental.sessao_conversa import renovar_contexto_sessao
from mente_laylay.especialistas.area_transferencia import AreaTransferenciaRuntime
from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime


def _pendencia(expira_em: float = 200.0) -> dict:
    return {
        "id": "pendencia-1",
        "origem": "teste",
        "acao": "confirmar_teste",
        "status": "ativa",
        "criada_em": 100.0,
        "expira_em": expira_em,
    }


def _runtime_pendencia(estado: dict, agora=lambda: 100.0) -> PendenciaAcaoRuntime:
    def atualizar(transformar):
        novo = transformar(dict(estado))
        estado.clear()
        estado.update(novo)
        return dict(estado)

    return PendenciaAcaoRuntime(
        estado_getter=lambda: estado,
        estado_atualizar=atualizar,
        agora=agora,
        log=lambda *_args: None,
    )


def test_renovar_sessao_descarta_pendencia_canonica_sem_apagar_fatos() -> None:
    mental, _conversa, _mensagens = renovar_contexto_sessao(
        {
            CHAVE_PENDENCIA_ACAO: _pendencia(),
            "pessoas": {"nanda": {"relacao": "namorada"}},
            "ultimo_app_janela": "opera",
            "ultimo_site_aba": "prime video",
            "ultima_estrutura_arquivo_params": {"caminho": "C:/antigo.txt"},
            "ultima_estrutura_arquivo_ts": 149.0,
            "continuidade_geral": {
                "dominio_ativo": "musica",
                "dominios": {"musica": {"intent": "PLAYLIST_ADD"}},
            },
        },
        {},
        [],
        motivo="chat_reaberto",
        ativa=True,
        agora=150.0,
    )

    assert mental[CHAVE_PENDENCIA_ACAO] == {}
    assert mental["pessoas"] == {"nanda": {"relacao": "namorada"}}
    assert mental["ultimo_app_janela"] == ""
    assert mental["ultimo_site_aba"] == ""
    assert mental["ultima_estrutura_arquivo_params"] == {}
    assert mental["continuidade_geral"]["modo"] == "oficial"
    assert mental["continuidade_geral"]["dominios"] == {}


def test_ciclo_global_expira_pendencia_canonica_sem_esperar_obter() -> None:
    estado = aplicar_ciclo_vida_contexto(
        {CHAVE_PENDENCIA_ACAO: _pendencia(expira_em=105.0)},
        agora=106.0,
    )

    assert estado[CHAVE_PENDENCIA_ACAO] == {}
    assert estado["ultima_pendencia_acao"]["id"] == "pendencia-1"
    assert estado["ultima_pendencia_acao"]["status"] == "expirada"
    assert CHAVE_PENDENCIA_ACAO in estado["contextos_expirados_ultimo_ciclo"]


def test_clipboard_publica_so_referencia_hash_operacao_e_ttl() -> None:
    estado: dict = {}
    pendencias = _runtime_pendencia(estado)
    clipboard = {"texto": "segredo pessoal do teste"}
    runtime = AreaTransferenciaRuntime(
        falar=lambda *_args: None,
        leitor=lambda: clipboard["texto"],
        escritor=lambda texto: clipboard.__setitem__("texto", texto),
        pendencia_runtime=pendencias,
        relogio=lambda: 100.0,
        log=lambda *_args: None,
    )

    assert runtime.processar("coloca o que eu copiei em letras maiúsculas") is True
    publicada = dict(estado[CHAVE_PENDENCIA_ACAO])
    serializada = str(publicada)
    assert publicada["origem"] == "area_transferencia"
    assert publicada["dominio"] == "area_transferencia"
    assert publicada["acao"] == "copiar_resultado"
    assert publicada["expira_em"] == 700.0
    assert set(publicada["metadados"]) == {
        "operacao", "original_hash", "resultado_hash", "tamanho_resultado",
    }
    assert "segredo pessoal" not in serializada.casefold()

    assert runtime.processar("copia o resultado") is True
    assert clipboard["texto"] == "SEGREDO PESSOAL DO TESTE"
    desfazer = dict(estado[CHAVE_PENDENCIA_ACAO])
    assert desfazer["acao"] == "desfazer_clipboard"
    assert "segredo pessoal" not in str(desfazer).casefold()


def test_troca_de_dominio_encerra_pendencia_musical_generica() -> None:
    estado: dict = {}
    pendencias = _runtime_pendencia(estado)
    pendencias.registrar(
        origem="musica_conversacional",
        dominio="musica",
        acao="confirmar_sugestao_musical",
        pergunta="Quer que eu toque?",
        referencia="faixa-1",
        metadados={"titulo": "Faixa 1"},
    )

    class Contexto:
        def montar(self):
            return {
                "_pendencia_acao_runtime": pendencias,
                "turno_atual": {
                    "id": "troca-musica-app",
                    "modalidade": "comando",
                    "modalidade_geral": "comando",
                    "autoriza_execucao": True,
                },
                "retrato_turno_atual": {},
                "registrar_arbitragem_turno": lambda *_args: None,
            }

    interpretador = type(
        "Interpretador",
        (),
        {
            "tentar_ai_primeiro": lambda _self, _texto: {
                "intent": "APP_OPEN",
                "params": {"nome_app": "opera"},
            },
        },
    )()
    servicos = {
        "_interpretacao_intencao_runtime": interpretador,
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        "_texto_depende_de_contexto": lambda _texto: False,
        "_refinar_contexto_mental": lambda _texto: None,
        "_texto_cancela_acao_agora": lambda _texto: False,
        "_resolver_comando_midia_contextual_forcado": lambda _texto: None,
        "_resolver_comando_contextual_forcado": lambda _texto: None,
        "_resolver_comando_acao_geral_contextual_forcado": lambda _texto: None,
        "_resolver_repeticao_ultima_acao": lambda _texto: None,
        "detectar_intencao_deterministica": lambda _texto: None,
        "_extrair_agendamento_local": lambda _texto: None,
        "_extrair_acao_agendada_local": lambda _texto: None,
        "_texto_parece_consulta_operacional": lambda _texto: True,
    }
    ciclo = CicloComandosRuntime(
        namespace_getter=lambda: servicos,
        contexto_intencao_runtime=Contexto(),
        log=lambda *_args: None,
    )

    resultado, _rota = ciclo.resolver_comando_natural("abre o opera", "terminal")

    assert resultado and resultado["intent"] == "APP_OPEN"
    assert pendencias.obter() is None
    assert estado["ultima_pendencia_acao"]["status"] == "substituida_por_troca_dominio"
