from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from mente_laylay.autonomia.agendamento_mental import extrair_agendamento_local
from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
from mente_laylay.autonomia.execucao_ia import CoordenadorExecRuntime
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.porteiro_acoes import (
    texto_conversa_casual_sem_acao,
    texto_social_curto,
)
from mente_laylay.autonomia.resposta_ia_runtime import RespostaIARuntime
from mente_laylay.autonomia.roteador_deterministico import (
    texto_expresso_melhor_no_deterministico,
)
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.iot.runtime import RuntimeIoT
from mente_laylay.memoria_mental.contexto_compartilhado import (
    registrar_resultado_execucao,
    texto_depende_de_contexto,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
)
from mente_laylay.memoria_mental.mapa_recursos import MapaRecursosRuntime
from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime
from mente_laylay.percepcao.observador_area_transferencia import (
    classificar_resposta_oferta,
    oferta_deve_ceder_a_novo_comando,
)


SENTINELAS_TECNICAS = (
    "LAYLAY_LLM_INDISPONIVEL",
    "HTTPConnectionPool(",
    "Traceback (most recent call last)",
)


class _MemoriaIoT:
    def __init__(self) -> None:
        self.dispositivos: dict[str, dict[str, Any]] = {}

    def salvar_dispositivo_iot(self, dados):
        self.dispositivos[dados["nome"]] = dict(dados)
        return dict(dados)

    def listar_dispositivos_iot(self, ambiente="", *, somente_ativos=True):
        return [
            dict(item)
            for item in self.dispositivos.values()
            if (not ambiente or item.get("ambiente") == ambiente)
            and (not somente_ativos or item.get("ativo", True))
        ]

    def atualizar_estado_iot(self, nome, estado, **_kwargs):
        self.dispositivos[nome]["estado"] = dict(estado)
        return dict(estado)

    def registrar_historico_iot(self, nome, **dados):
        return {"nome": nome, **dados}


class _ContextoVazio:
    @staticmethod
    def montar() -> dict[str, Any]:
        return {}


class _MatrizUsoDiario:
    """Passa entradas reais pelo coordenador e pela resposta canônica.

    Os efeitos externos são simulados, mas a criação do turno, a arbitragem,
    os detectores, a continuidade e a decisão de chamar ou não a LLM são os
    mesmos componentes usados pela aplicação.
    """

    def __init__(self, tmp_path) -> None:
        self.relogio = [100.0]
        self.estado = EstadoCompartilhadoRuntime(mental={})
        self.origem = "desconhecida"
        self.turno: dict[str, Any] = {}
        self.acoes: list[dict[str, Any]] = []
        self.chamadas_llm: list[str] = []
        self.falas: list[str] = []
        self.logs: list[str] = []
        self.fases: list[str] = []

        self.pendencias = PendenciaAcaoRuntime(
            estado_getter=lambda: self.estado.mental,
            estado_atualizar=lambda atualizar: self.estado.atualizar(
                "mental", atualizar
            ),
            agora=lambda: self.relogio[0],
            log=lambda mensagem: self.logs.append(str(mensagem)),
        )
        self.iot = RuntimeIoT(
            memoria_sqlite=_MemoriaIoT(),
            falar=lambda *_args: None,
            estado_mental_getter=lambda: self.estado.mental,
            emitir_fala=False,
            modo="simulado",
            log=lambda mensagem: self.logs.append(str(mensagem)),
        )
        self.pessoas = MemoriaPessoasRuntime(
            caminho=tmp_path / "pessoas.json",
            falar=lambda fala, *_args: self.falas.append(str(fala)),
            pendencia_runtime=self.pendencias,
            registrar_resultado=self._registrar_resultado_pessoa,
            estado_getter=lambda: self.estado.mental,
            estado_atualizar=lambda atualizar: self.estado.atualizar(
                "mental", atualizar
            ),
            log=lambda mensagem: self.logs.append(str(mensagem)),
        )
        self.pessoas.processar("Eu tenho uma namorada e o nome dela é Nanda.")
        self.acoes.clear()
        self.falas.clear()
        self.recursos = self._criar_mapa_recursos()

        contexto = {
            "marcar_inicio_turno": self._marcar_inicio_turno,
            "obter_turno_atual": lambda: dict(self.turno),
            "atualizar_plano_turno": lambda fase, **_kwargs: self.fases.append(fase),
            "processar_comandos_prioritarios": self._processar_prioritario,
            "usar_modo_rapido": lambda _texto: True,
            "texto_depende_de_contexto": lambda texto: texto_depende_de_contexto(
                texto, normalizar_texto
            ),
            "modo_jogo_ativo": lambda: self.origem == "modo_jogo",
            "modelo_llm": SimpleNamespace(executar=self._responder_sem_comando),
            "preparar_resposta": self._preparar_resposta,
            "contexto_dispatch_runtime": _ContextoVazio(),
            "executar_comandos_json": lambda *_args, **_kwargs: {
                "erros": [],
                "fala_ja_emitida": False,
                "fala_emitida_por_acao": False,
                "fala_salva_no_inicio": False,
            },
            "contexto_finalizacao_runtime": _ContextoVazio(),
            "finalizar_execucao": self._finalizar_conversa,
            "fallback_fala": "Tô aqui.",
        }
        self.resposta = RespostaIARuntime(
            contexto_getter=lambda: contexto,
            log=lambda mensagem: self.logs.append(str(mensagem)),
        )
        self.coordenador = CoordenadorExecRuntime(
            contexto_exec_getter=lambda: None,
            resposta_ia_getter=lambda: self.resposta,
            loop_getter=lambda: None,
            log=lambda mensagem: self.logs.append(str(mensagem)),
        )

    @staticmethod
    def _criar_mapa_recursos() -> MapaRecursosRuntime:
        mapa = MapaRecursosRuntime()
        mapa.registrar(
            "caixa_entrada",
            arquivo="memoria/caixa_entrada.json",
            descricao="ideias e notas pessoais",
            termos=("minhas ideias", "minhas notas", "caixa de entrada"),
            leitor=lambda _texto: {
                "notas": [{"tipo": "ideia", "conteudo": "melhorar o avatar"}]
            },
            intent_consulta="INBOX_LIST",
        )
        mapa.registrar(
            "area_transferencia",
            arquivo="temporario",
            descricao="texto copiado temporário",
            termos=("o que eu copiei", "texto copiado", "area de transferencia"),
            leitor=lambda _texto: {"status": "texto_disponivel"},
            intent_consulta="CLIPBOARD_READ",
        )
        return mapa

    def _marcar_inicio_turno(self, texto: str, *, origem="desconhecida") -> None:
        self.origem = str(origem)
        self.turno = classificar_modalidade_turno(texto)
        self.turno["origem_entrada"] = self.origem

    def _contexto_detector(self) -> dict[str, Any]:
        return {
            "normalizar_texto": normalizar_texto,
            "texto_conversa_casual_sem_acao": texto_conversa_casual_sem_acao,
            "texto_bloqueia_playlist_agora": lambda _texto: False,
            "texto_social_curto": texto_social_curto,
            "ignorar_token_solto": lambda _texto: False,
            "fluxo_prioritario_da_ia": lambda _texto: True,
            "texto_expresso_melhor_no_deterministico": lambda texto: (
                texto_expresso_melhor_no_deterministico(
                    texto, normalizar_texto=normalizar_texto
                )
            ),
            "texto_depende_de_contexto": lambda texto: texto_depende_de_contexto(
                texto, normalizar_texto
            ),
            "limpar_destino_pc_b": lambda texto: texto,
            "target_from_params": lambda _params, _texto: "pc_a",
            "detectar_intencao_iot": self.iot.detectar,
            "detectar_sugestao_indireta": lambda *_args: None,
            "resolver_consulta_recurso_local": self.recursos.resolver_consulta,
            "mente_integrada_estado": self.estado.mental,
            "limpar_nome_playlist": lambda texto: str(texto).strip(" ?!.,"),
            "extrair_nome_playlist": lambda _texto: "",
            "detectar_playlist_nome_direto": lambda _texto: "",
            "normalizar_query_musical": lambda texto: str(texto).strip(),
            "contexto_musical_ativo": lambda: True,
            "modo_jogo_contexto": lambda: {
                "ativo": self.origem == "modo_jogo",
                "titulo": "Path of Exile 2" if self.origem == "modo_jogo" else "",
                "processo": "PathOfExileSteam.exe" if self.origem == "modo_jogo" else "",
            },
            "visao_jogo_tem_analise_recente": lambda: False,
            "sites_diretos": {},
            "apps_map": {},
        }

    def _resolver(self, texto: str) -> tuple[dict[str, Any] | None, str]:
        return resolver_intencao(
            texto,
            self.origem,
            {
                "normalizar_texto": normalizar_texto,
                "refinar_contexto_mental": lambda _texto: None,
                "extrair_agendamento": lambda valor: extrair_agendamento_local(
                    valor, normalizar_texto
                ),
                "extrair_acao_agendada": lambda _texto: None,
                "texto_cancela_acao_agora": lambda _texto: False,
                "texto_depende_de_contexto": lambda valor: texto_depende_de_contexto(
                    valor, normalizar_texto
                ),
                "detectar_intencao_deterministica": lambda valor: (
                    detectar_intencao_deterministica_mente(
                        valor, self._contexto_detector()
                    )
                ),
                "resolver_comando_contextual_forcado": lambda _texto: None,
                "resolver_repeticao_ultima_acao": lambda _texto: None,
                "tentar_intencao_ai_primeiro": lambda _texto: None,
                "registrar_arbitragem_turno": lambda *_args: None,
                "turno_atual": dict(self.turno),
                "retrato_turno_atual": {},
                "continuidade_geral": dict(
                    self.estado.mental.get("continuidade_geral") or {}
                ),
            },
        )

    def _registrar_acao(self, intent: dict[str, Any], texto: str, rota: str) -> None:
        params = dict(intent.get("params") or {})
        nome = str(intent.get("intent") or "").upper()
        alvo = str(
            params.get("alvo")
            or params.get("nome_playlist")
            or params.get("nome")
            or params.get("query")
            or params.get("local")
            or ""
        )
        evento = {
            "intent": nome,
            "params": params,
            "alvo": alvo,
            "status": f"{nome.casefold()}_confirmado",
            "executou": True,
            "confirmado": True,
            "origem": self.origem,
            "rota": rota,
        }
        self.acoes.append(evento)
        novo = registrar_resultado_execucao(
            self.estado.mental,
            evento,
            texto,
            True,
        )
        self.estado.substituir("mental", novo)

    def _registrar_resultado_pessoa(
        self,
        resultado: dict[str, Any],
        texto: str,
        _sucesso: bool,
        **_kwargs,
    ) -> None:
        self._registrar_acao(resultado, texto, "memoria_pessoas")

    def _processar_pendencia(self, texto: str) -> bool:
        pendencia = self.pendencias.obter()
        if not pendencia:
            return False
        if oferta_deve_ceder_a_novo_comando(
            texto,
            str(pendencia.get("acao") or ""),
            texto_tem_comando_explicito=lambda valor: bool(
                classificar_modalidade_turno(valor).get("autoriza_execucao")
            ),
        ):
            self.pendencias.concluir(str(pendencia.get("id") or ""), "cedida")
            return False
        resultado = self.pendencias.resolver(
            texto,
            classificar_dominio=classificar_resposta_oferta,
        )
        status = str(resultado.get("status") or "")
        if status == "aceitar":
            atual = dict(resultado.get("pendencia") or {})
            self._registrar_acao(
                {"intent": "CLIPBOARD_INVESTIGATE", "params": {"alvo": "erro_copiado"}},
                texto,
                "pendencia",
            )
            self.pendencias.concluir(str(atual.get("id") or ""), "concluida")
            return True
        if status == "recusar":
            atual = dict(resultado.get("pendencia") or {})
            self.pendencias.concluir(str(atual.get("id") or ""), "recusada")
            return True
        return bool(resultado.get("tratado"))

    def _processar_prioritario(self, texto: str) -> bool:
        if self._processar_pendencia(texto):
            return True
        if self.pessoas.processar(texto):
            return True
        intent, rota = self._resolver(texto)
        if not isinstance(intent, dict):
            return False
        self._registrar_acao(intent, texto, rota)
        return True

    def _responder_sem_comando(self, _pedido):
        self.chamadas_llm.append(self.turno.get("texto") or "conversa_protegida")
        return SimpleNamespace(texto='{"fala":"Entendi sem executar nada.","comandos":[]}')

    @staticmethod
    def _preparar_resposta(_texto: str, _bruto: str) -> dict[str, Any]:
        return {
            "fala": "Entendi sem executar nada.",
            "comandos": [],
            "tipo_interacao": "conversa",
        }

    def _finalizar_conversa(
        self,
        _contexto,
        _comandos,
        _erros,
        fala,
        *_args,
    ) -> None:
        self.falas.append(str(fala))

    def enviar(self, texto: str, origem: str) -> list[dict[str, Any]]:
        inicio = len(self.acoes)
        self.coordenador.processar_sync(texto, origem=origem)
        return self.acoes[inicio:]


MATRIZ_COTIDIANA = (
    ("quais compromissos tenho na agenda?", "LISTAR_AGENDAMENTOS", ""),
    ("quais dispositivos estão disponíveis?", "IOT_LIST", ""),
    ("como está a lâmpada do quarto?", "IOT_STATUS", "lampada_quarto"),
    ("coloca uma música para jogar minecraft", "MUSIC_SEARCH", "musica para jogar minecraft"),
    ("vai chover hoje?", "WEATHER", ""),
    ("me fale minhas ideias", "INBOX_LIST", ""),
    ("o que eu copiei?", "CLIPBOARD_READ", ""),
    ("quem é Nanda?", "PEOPLE_QUERY", "Nanda"),
    ("encontra o código que controla a lâmpada", "FILE_SEARCH", "codigo que controla a lampada"),
)


@pytest.mark.parametrize("origem", ["terminal", "voz"])
def test_p20_conversa_longa_preserva_contratos_em_terminal_e_voz(
    tmp_path, origem: str
) -> None:
    matriz = _MatrizUsoDiario(tmp_path)

    for texto, intent, alvo in MATRIZ_COTIDIANA:
        novas = matriz.enviar(texto, origem)
        assert len(novas) == 1, texto
        assert novas[0]["intent"] == intent, texto
        assert novas[0]["alvo"] == alvo, texto
        assert novas[0]["origem"] == origem

    assert matriz.chamadas_llm == []
    assert all(item["confirmado"] is True for item in matriz.acoes)
    assert not any(
        sentinela in "\n".join((*matriz.logs, *matriz.falas))
        for sentinela in SENTINELAS_TECNICAS
    )


def test_p20_terminal_voz_e_jogo_produzem_mesmo_contrato_operacional(tmp_path) -> None:
    resultados: dict[str, list[tuple[str, str]]] = {}
    for origem in ("terminal", "voz", "modo_jogo"):
        matriz = _MatrizUsoDiario(tmp_path / origem)
        contratos = []
        for texto in (
            "coloca uma música para jogar minecraft",
            "como está a lâmpada do quarto?",
            "quais compromissos tenho na agenda?",
        ):
            novas = matriz.enviar(texto, origem)
            assert len(novas) == 1
            contratos.append((novas[0]["intent"], novas[0]["alvo"]))
        resultados[origem] = contratos

    assert resultados["terminal"] == resultados["voz"] == resultados["modo_jogo"]


def test_p20_modo_jogo_nao_engole_comando_forte_nem_cruza_alvo_visual(tmp_path) -> None:
    matriz = _MatrizUsoDiario(tmp_path)

    visual = matriz.enviar("olha meus atributos", "modo_jogo")
    musica = matriz.enviar("coloca uma música para jogar minecraft", "modo_jogo")
    luz = matriz.enviar("liga a luz", "modo_jogo")

    assert visual[0]["intent"] == "GAME_VISION"
    assert visual[0]["params"]["jogo"] == "Path of Exile 2"
    assert musica[0]["intent"] == "MUSIC_SEARCH"
    assert musica[0]["alvo"] == "musica para jogar minecraft"
    assert luz[0]["intent"] == "IOT_CONTROL"
    assert luz[0]["alvo"] == "lampada_quarto"
    assert "Path of Exile" not in luz[0]["alvo"]
    assert matriz.chamadas_llm == []


@pytest.mark.parametrize(
    "texto",
    [
        "não desliga a luz",
        "como eu faria para desligar a luz?",
        "você consegue apagar uma pasta?",
        "se eu pedir para fechar o navegador, você consegue?",
    ],
)
def test_p20_molduras_sem_autorizacao_nunca_executam(tmp_path, texto: str) -> None:
    matriz = _MatrizUsoDiario(tmp_path)

    assert matriz.enviar(texto, "terminal") == []
    assert matriz.acoes == []
    assert matriz.falas == ["Entendi sem executar nada."]


def test_p20_pendencia_aceita_recusa_expira_e_cede_de_forma_observavel(tmp_path) -> None:
    matriz = _MatrizUsoDiario(tmp_path)

    aceita = matriz.pendencias.registrar(
        origem="observador_area_transferencia",
        acao="investigar_erro",
        pergunta="Quer que eu investigue?",
        referencia="hash-1",
        ttl_s=20,
    )
    assert matriz.enviar("quero sim", "terminal")[0]["intent"] == "CLIPBOARD_INVESTIGATE"
    assert matriz.pendencias.obter() is None

    recusada = matriz.pendencias.registrar(
        origem="observador_area_transferencia",
        acao="resumir_texto",
        pergunta="Quer que eu faça um resumo?",
        referencia="hash-2",
        ttl_s=20,
    )
    assert matriz.enviar("agora não", "voz") == []
    assert matriz.pendencias.obter() is None

    expirada = matriz.pendencias.registrar(
        origem="observador_area_transferencia",
        acao="explicar_codigo",
        pergunta="Quer que eu explique?",
        referencia="hash-3",
        ttl_s=5,
    )
    matriz.relogio[0] += 6
    assert matriz.pendencias.obter() is None

    cedida = matriz.pendencias.registrar(
        origem="observador_area_transferencia",
        acao="resumir_texto",
        pergunta="Quer que eu faça um resumo?",
        referencia="hash-4",
        ttl_s=20,
    )
    nova = matriz.enviar("como está a lâmpada do quarto?", "modo_jogo")
    assert nova[0]["intent"] == "IOT_STATUS"
    assert matriz.pendencias.obter() is None

    encerramentos = "\n".join(matriz.logs)
    for pendencia, status in (
        (aceita, "concluida"),
        (recusada, "recusada"),
        (expirada, "expirada"),
        (cedida, "cedida"),
    ):
        assert f"id={pendencia['id']} status={status}" in encerramentos


def test_p20_requalificacao_nao_produz_contrato_contraditorio(tmp_path) -> None:
    matriz = _MatrizUsoDiario(tmp_path)
    for origem in ("terminal", "voz", "modo_jogo"):
        for texto, _intent, _alvo in MATRIZ_COTIDIANA:
            matriz.enviar(texto, origem)

    for evento in matriz.acoes:
        assert evento["executou"] is True
        assert evento["confirmado"] is True
        assert evento["status"].endswith("_confirmado")
        if evento["intent"].startswith("IOT_") and evento["intent"] != "IOT_LIST":
            assert evento["alvo"] == "lampada_quarto"
        if evento["intent"] == "PEOPLE_QUERY":
            assert evento["alvo"] == "Nanda"
        if evento["intent"] == "FILE_SEARCH":
            assert "lampada" in normalizar_texto(evento["alvo"])
