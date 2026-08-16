"""Fase operacional prioritária do turno canônico da Laylay.

Esta camada recebe o turno já criado, resolve uma única vez habilidades e
linguagem natural e só então libera a conversa livre para a IA.
"""

from __future__ import annotations

import asyncio
import re
import unicodedata
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any, Callable, Dict
from mente_laylay.integracao.registro_memoria_pessoas import PortaMemoriaPessoas
from mente_laylay.integracao.registro_iot import PortaIoT
from mente_laylay.autonomia.pre_fluxo_contextual import (
    processar_aprendizado_apelido,
    processar_consulta_sistema_local,
    processar_esclarecimento_operacional,
    processar_pedido_direcao_musical,
    processar_identidade_usuario,
    processar_sugestao_indireta,
)
from mente_laylay.especialistas.capacidades import (
    intents_registradas,
)
from mente_laylay.cognicao.evidencia_operacional import (
    bloqueia_controle_iot_por_modalidade,
    detectar_consulta_lista_iot,
)
from mente_laylay.percepcao.ritmo_circadiano import (
    agora_no_fuso,
    detectar_consulta_horario,
    responder_consulta_horario,
)
from mente_laylay.memoria_mental.continuidade_geral import (
    resolver_continuacao_aditiva,
    texto_e_continuacao_aditiva,
)
from mente_laylay.cognicao.esclarecimento_operacional import (
    detectar_esclarecimento_operacional,
    limpar_esclarecimento_operacional,
)
from mente_laylay.cognicao.modalidade_turno import (
    bloqueia_execucao_operacional_prioritaria,
    classificar_modalidade_turno,
)
from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.autonomia.analise_comandos import segmentar_comandos_em_cadeia
from mente_laylay.memoria_mental.contexto_imediato import (
    _dominio_restrito_referencia,
    _resultado_compativel_com_dominio,
)


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def texto_pede_resumo_pagina(texto: str) -> bool:
    """Reconhece um pedido real de resumo, nunca mera menção ou hipótese."""
    t = str(texto or "").strip().lower()
    t = "".join(ch for ch in unicodedata.normalize("NFD", t) if unicodedata.category(ch) != "Mn")
    alvos = ("pagina", "site", "video", "aba")
    pedidos = ("resume", "resuma", "resumir", "explica", "explique", "o que essa", "o que esta")
    if not (any(alvo in t for alvo in alvos) and any(pedido in t for pedido in pedidos)):
        return False
    turno = classificar_modalidade_turno(texto)
    return bool(
        turno.get("autoriza_execucao")
        and str(turno.get("modalidade") or "") in {"comando", "misto"}
    )


def _texto_normalizado_local(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    sem_acentos = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", sem_acentos).strip()


def texto_recusa_musica_agora(texto: str) -> bool:
    """Reconhece uma recusa atual sem convertê-la em comando musical."""
    t = _texto_normalizado_local(texto)
    return bool(
        re.search(
            r"\bnao\s+(?:coloca|coloque|bota|toque|toca|abre|inicia|inicie)\s+"
            r"(?:uma\s+)?(?:musica|playlist|som|faixa)\b",
            t,
        )
        or re.search(r"\bsem\s+(?:musica|playlist|som)\s+agora\b", t)
    )


def texto_pede_continuacao_musical_curta(texto: str) -> bool:
    """Seleciona apenas elipses que exigem um contexto musical real."""
    t = _texto_normalizado_local(texto).strip(" .,!?:;")
    return bool(re.fullmatch(
        r"(?:(?:tenta|manda|coloca|toca)\s+outr[ao](?:\s+(?:musica|faixa))?|"
        r"(?:continua|continue)(?:\s+(?:a|essa|ela|musica|tocando))?|"
        r"(?:pausa|pause)|"
        r"(?:a\s+)?(?:proxima|proximo|pula|pule)|"
        r"(?:a\s+)?anterior|"
        r"volta\s+(?:para|pra)\s+(?:a\s+)?anterior)",
        t,
    ))


def texto_pergunta_como_apagar_item(texto: str) -> bool:
    """Separa pedido de instrução de uma exclusão realmente autorizada."""
    t = _texto_normalizado_local(texto)
    return bool(
        re.match(
            r"^(?:como\s+(?:eu\s+)?(?:faria|faco|posso|poderia)|"
            r"o\s+que\s+(?:eu\s+)?(?:faria|faco))\b",
            t,
        )
        and re.search(r"\b(?:apagar|excluir|deletar|remover)\b", t)
        and re.search(r"\b(?:arquivo|pasta|item|documento)\b", t)
    )


def texto_referencia_tipificada_prioritaria(texto: str) -> bool:
    """Molduras curtas que exigem resolver o referente antes de executar.

    P0_NAVEGADOR_SUBTIPO_V3_1_20260815
    A função só reconhece formas estreitas já suportadas pelo resolvedor
    contextual; ela não cria intents nem concede autorização.
    """
    t = _texto_normalizado_local(texto).strip(" .,!?:;")
    referencia_direta = bool(re.fullmatch(
        r"(?:(?:fecha|feche|fechar)|(?:tenta\s+)?(?:abre|abra|abrir))\s+"
        r"(?:ele|ela|isso|esse|essa|este|esta|"
        r"(?:esse|este|o)\s+arquivo|"
        r"(?:essa|esta|a)\s+(?:aba|guia)|"
        r"(?:esse|este|o)\s+site)",
        t,
    ))
    voltar_anterior = bool(re.fullmatch(
        r"(?:volta|volte|retorna|retorne|vai)\s+"
        r"(?:(?:para|pra)\s+)?(?:a\s+)?anterior",
        t,
    ))
    return referencia_direta or voltar_anterior


def segmentar_composto_caixa_agenda(texto: str) -> tuple[str, str] | None:
    """Reconhece a cooperação explícita entre uma ideia e seu lembrete.

    O primeiro trecho pertence à caixa de entrada, que é uma habilidade
    prioritária e não passa pelo executor genérico de intents. Por isso esta
    combinação precisa ser coordenada antes da cadeia comum. A detecção é
    estreita: não transforma uma conversa com ``e`` em duas ações.
    """
    partes = segmentar_comandos_em_cadeia(texto)
    if len(partes) != 2:
        return None
    primeira, segunda = partes
    a = _texto_normalizado_local(primeira)
    b = _texto_normalizado_local(segunda)
    guarda_ideia = bool(
        re.search(r"\b(?:guarda|guarde|salva|salve|anota|anote)\b", a)
        and re.search(r"\b(?:ideia|nota|sugestao|sugestoes|discussao)\b", a)
    )
    cria_lembrete = bool(
        re.search(r"\b(?:(?:me\s+)?lembra|lembre|agenda|agende)\b", b)
    )
    return (primeira, segunda) if guarda_ideia and cria_lembrete else None


class ComandosImediatosRuntime:
    def __init__(
        self,
        *,
        namespace_getter: Callable[[], Dict[str, Any]],
        loop_getter: Callable[[], Any],
        memoria_pessoas: PortaMemoriaPessoas | None = None,
        iot: PortaIoT | None = None,
    ) -> None:
        self.namespace_getter = namespace_getter
        self.loop_getter = loop_getter
        self.memoria_pessoas = memoria_pessoas
        self.iot = iot

    def _processar_resumo_pagina(
        self,
        texto: str,
        ns: Dict[str, Any],
    ) -> bool:
        """Executa ou recusa o resumo com um resultado observável.

        O resumo usa o loop do WebSocket porque a resposta da extensão chega
        nele. Ainda assim, o turno que recebeu o pedido não pode terminar
        antes dessa tarefa: isso publicava ``tratado_prioritario`` com plano
        vazio e, na prática, fazia o comando parecer ignorado. Fora da própria
        thread do loop, aguardamos a conclusão e registramos exatamente um
        resultado. A forma assíncrona fica reservada ao caso raro em que esta
        função já é chamada pelo loop do navegador, evitando deadlock.
        """
        if not texto_pede_resumo_pagina(texto):
            return False
        print("⚡ [PRIORIDADE:RESUMO] leitura da página atual")
        intencao_resumo = {"intent": "RESUMIR_PAGINA", "params": {}}
        registrar = ns.get("_registrar_resultado_execucao")
        resumir = ns.get("resumir_pagina_ou_video")
        loop = self.loop_getter()

        def registrar_conclusao(executou: bool, status: str) -> None:
            if callable(registrar):
                registrar(
                    intencao_resumo,
                    texto,
                    executou,
                    origem="prioritario_resumo_pagina",
                    status=status,
                )

        loop_fechado = getattr(loop, "is_closed", None)
        loop_rodando = getattr(loop, "is_running", None)
        indisponivel = (
            not callable(resumir)
            or loop is None
            or (callable(loop_fechado) and loop_fechado())
            or (callable(loop_rodando) and not loop_rodando())
        )
        if indisponivel:
            registrar_conclusao(False, "executor_indisponivel")
            falar = ns.get("falar_com_lipsync")
            if callable(falar):
                falar(
                    "Não consigo ler a página porque o navegador não está conectado agora.",
                    "calma",
                    1,
                )
            return True

        corrotina = None
        try:
            corrotina = resumir()
            futuro = asyncio.run_coroutine_threadsafe(corrotina, loop)
        except Exception as erro:
            if corrotina is not None and callable(getattr(corrotina, "close", None)):
                corrotina.close()
            print(
                "⚠️ [PRIORIDADE:RESUMO] executor não iniciou: "
                f"{type(erro).__name__}"
            )
            registrar_conclusao(False, "falha_execucao")
            falar = ns.get("falar_com_lipsync")
            if callable(falar):
                falar("Não consegui iniciar a leitura desta página.", "calma", 1)
            return True

        def concluir_resumo(tarefa: Any) -> None:
            try:
                executou = bool(tarefa.result())
            except Exception as erro:
                print(
                    "⚠️ [PRIORIDADE:RESUMO] executor falhou: "
                    f"{type(erro).__name__}"
                )
                executou = False
            registrar_conclusao(
                executou,
                "resumo_concluido" if executou else "falha_execucao",
            )

        try:
            loop_atual = asyncio.get_running_loop()
        except RuntimeError:
            loop_atual = None

        if loop_atual is loop:
            # Nunca bloqueia a thread que precisa receber PAGE_DATA. Esse ramo
            # não é usado pelo terminal/voz, mas preserva a ponte WebSocket se
            # uma origem futura entregar o turno pelo próprio loop.
            futuro.add_done_callback(concluir_resumo)
            return True

        try:
            executou = bool(futuro.result(timeout=45.0))
        except FutureTimeoutError:
            futuro.cancel()
            print("⚠️ [PRIORIDADE:RESUMO] leitura excedeu 45s e foi cancelada")
            registrar_conclusao(False, "timeout_execucao")
            falar = ns.get("falar_com_lipsync")
            if callable(falar):
                falar(
                    "A página demorou demais para responder. Não vou fingir "
                    "que consegui resumir.",
                    "calma",
                    1,
                )
            return True
        except Exception as erro:
            print(
                "⚠️ [PRIORIDADE:RESUMO] executor falhou: "
                f"{type(erro).__name__}"
            )
            registrar_conclusao(False, "falha_execucao")
            falar = ns.get("falar_com_lipsync")
            if callable(falar):
                falar("Não consegui concluir a leitura desta página.", "calma", 1)
            return True

        registrar_conclusao(
            executou,
            "resumo_concluido" if executou else "falha_execucao",
        )
        return True

    def _processar_busca_arquivo_e_abrir_resultado(
        self,
        texto: str,
        ns: Dict[str, Any],
        estado_runtime: Any,
    ) -> bool:
        """Executa busca e seleção ordinal como duas etapas observáveis."""
        normalizar = ns.get("_normalizar_texto_com_apelidos")
        partes = segmentar_comandos_em_cadeia(
            texto,
            normalizar_texto=normalizar if callable(normalizar) else None,
        )
        if len(partes) != 2:
            return False

        def detectar(trecho: str) -> dict[str, Any] | None:
            candidato = detectar_intencao_arquivos(
                trecho,
                params_cb=lambda **kwargs: kwargs,
                estado_mental=getattr(estado_runtime, "mental", {}),
                normalizar_texto=normalizar,
            )
            return candidato if isinstance(candidato, dict) else None

        primeira = detectar(partes[0])
        if str((primeira or {}).get("intent") or "").upper() != "FILE_SEARCH":
            return False

        # A segunda parte precisa ser realmente uma seleção ordinal. Não
        # promovemos outros compostos de arquivo por esta rota estreita.
        segunda_norm = _texto_normalizado_local(partes[1]).strip(" .,!?:;")
        if not re.fullmatch(
            r"(?:abre|abra|abrir)\s+(?:(?:o|a)\s+)?"
            r"(?:primeir[oa]|segund[oa]|terceir[oa]|quart[oa]|quint[oa]|"
            r"sext[oa]|s[eé]tim[oa]|oitav[oa]|non[oa]|d[eé]cim[oa]|\d{1,2})"
            r"(?:\s+resultado)?",
            segunda_norm,
        ):
            return False

        executar = ns.get("executar_intencao")
        registrar = ns.get("_registrar_resultado_execucao")
        falar = ns.get("falar_com_lipsync")
        if not callable(executar):
            return False

        try:
            busca_executada = bool(executar(primeira, partes[0]))
        except Exception as erro:
            print(
                "⚠️ [PRIORIDADE:ARQUIVOS] busca composta falhou: "
                f"{type(erro).__name__}: {erro}"
            )
            busca_executada = False
        if callable(registrar):
            registrar(
                primeira,
                partes[0],
                busca_executada,
                origem="prioritario_cooperativo_busca_arquivo:1",
            )
        if not busca_executada:
            if callable(falar):
                falar(
                    "Não consegui concluir a busca, então não tentei abrir um "
                    "resultado que não foi confirmado.",
                    "calma",
                    1,
                )
            return True

        # O executor da busca publica os resultados na mente compartilhada
        # antes de retornar. Relê-la agora é o que permite ao mesmo detector
        # resolver naturalmente ``o primeiro resultado``.
        segunda = detectar(partes[1])
        if str((segunda or {}).get("intent") or "").upper() != "FILE_OPEN_RESULT":
            if callable(falar):
                falar(
                    "A busca terminou, mas não apareceu um primeiro resultado "
                    "válido para eu abrir.",
                    "calma",
                    1,
                )
            return True
        try:
            abertura_executada = bool(executar(segunda, partes[1]))
        except Exception as erro:
            print(
                "⚠️ [PRIORIDADE:ARQUIVOS] abertura composta falhou: "
                f"{type(erro).__name__}: {erro}"
            )
            abertura_executada = False
        if callable(registrar):
            registrar(
                segunda,
                partes[1],
                abertura_executada,
                origem="prioritario_cooperativo_busca_arquivo:2",
            )
        print(
            "⚡ [PRIORIDADE:ARQUIVOS] busca+abertura tratadas | "
            f"busca={busca_executada} abertura={abertura_executada}"
        )
        return True

    def processar_prioritarios(self, texto: str) -> bool:
        """Resolve habilidades pelo turno canônico antes da conversa livre."""
        ns = self.namespace_getter() or {}
        estado_runtime = ns.get("_estado_compartilhado_runtime")

        # P0_REVISAO_INTRA_TURNO_V1_1_20260816
        # Todo detector prioritário recebe a mesma proposta final que planejou
        # o turno. A fala original permanece na memória e nos logs do turno.
        mente_prioritaria = getattr(estado_runtime, "mental", {})
        turno_prioritario = (
            dict(mente_prioritaria.get("turno_atual") or {})
            if isinstance(mente_prioritaria, dict)
            else {}
        )
        revisao_prioritaria = (
            dict(turno_prioritario.get("revisao_intra_turno") or {})
            if isinstance(turno_prioritario.get("revisao_intra_turno"), dict)
            else {}
        )
        if (
            revisao_prioritaria.get("detectada") is True
            and revisao_prioritaria.get("resolvida") is True
            and revisao_prioritaria.get("cancelada") is not True
        ):
            texto_final = str(
                turno_prioritario.get("texto_operacional_efetivo")
                or revisao_prioritaria.get("texto_operacional_efetivo")
                or ""
            ).strip()
            if texto_final:
                print(
                    "🧠 [REVISÃO:PRIORIDADE] usando proposta final -> "
                    f"{texto_final!r}"
                )
                texto = texto_final

        contexto_prioritario = dict(ns)
        contexto_prioritario["mente_integrada_estado"] = getattr(
            estado_runtime, "mental", {},
        )

        # P0_AUTORIZACAO_MODALIDADE_20260814
        # Consultas locais canônicas de estado são somente leitura. Elas podem
        # vencer a barreira de mutação, mas apenas pela habilidade read-only já
        # existente. Assim "O Opera continua aberto?" não é confundido com o
        # comando musical "continua".
        try:
            tratado_readonly_p0, rota_readonly_p0 = processar_consulta_sistema_local(
                contexto_prioritario, texto
            )
        except Exception as erro:
            print(
                "⚠️ [P0:READ-ONLY] consulta local falhou sem liberar mutação | "
                f"{type(erro).__name__}: {erro}"
            )
        else:
            if tratado_readonly_p0:
                print(
                    "🔎 [P0:READ-ONLY] consulta segura tratada antes da barreira | "
                    f"rota={rota_readonly_p0 or 'consulta_sistema_local'}"
                )
                return True

        # P0_CAPACIDADE_READONLY_A1_20260816
        # Perguntas sobre o que a Laylay consegue fazer continuam SEM autorizar
        # a ação mencionada. O catálogo vivo é somente leitura e precisa poder
        # responder antes da barreira de mutação; caso contrário, a própria
        # proteção P0 devolve o turno à conversa e a LLM pode inventar uma
        # incapacidade. Um turno já autorizado nunca é consumido por esta porta.
        mente_atual = getattr(estado_runtime, "mental", {})
        turno_atual = (
            dict(mente_atual.get("turno_atual") or {})
            if isinstance(mente_atual, dict)
            else {}
        )
        responder_capacidade = ns.get("_responder_pergunta_capacidade_local")
        fala_capacidade = ""
        if (
            turno_atual.get("autoriza_execucao") is not True
            and callable(responder_capacidade)
        ):
            try:
                fala_capacidade = str(responder_capacidade(texto) or "").strip()
            except Exception as erro:
                print(
                    "⚠️ [P0:CAPACIDADE] consulta read-only falhou sem liberar "
                    f"mutação | {type(erro).__name__}: {erro}"
                )
        if fala_capacidade:
            print("🔎 [P0:CAPACIDADE] consulta segura tratada antes da barreira")
            falar = ns.get("falar_com_lipsync")
            if callable(falar):
                falar(fala_capacidade, "calma", 1)
            return True

        # Detectar uma intent não concede permissão para executá-la. Esta
        # barreira faz a rota determinística usar o mesmo dono do turno da LLM.
        normalizar_turno = ns.get("_normalizar_texto_com_apelidos")
        texto_tem_comando = ns.get("_texto_tem_comando_explicito")
        if bloqueia_execucao_operacional_prioritaria(
            texto,
            classificacao=turno_atual or None,
            normalizar_texto=(normalizar_turno if callable(normalizar_turno) else None),
            texto_tem_comando_explicito=(
                texto_tem_comando if callable(texto_tem_comando) else None
            ),
        ):
            modalidade_p0 = str(
                turno_atual.get("modalidade_geral")
                or turno_atual.get("modalidade")
                or "conversa"
            )
            motivo_p0 = str(
                turno_atual.get("motivo_decisao")
                or turno_atual.get("motivo")
                or "sem autorização operacional"
            )
            print(
                "🛡️ [P0:AUTORIZAÇÃO] rota operacional imediata bloqueada | "
                f"modalidade={modalidade_p0} motivo={motivo_p0}"
            )
            return False

        # Comandos internos iniciados por barra nunca são respostas naturais
        # a uma oferta pendente. O diagnóstico precisa vencer clipboard,
        # cooperação e conversa para que "/diagnostico mente" não seja lido
        # como "sim, resuma o texto copiado".
        detectar_diagnostico = ns.get("_detectar_pedido_diagnostico_mente")
        if callable(detectar_diagnostico) and detectar_diagnostico(texto):
            print("⚡ [PRIORIDADE:DIAGNÓSTICO] retrato da mente única")
            mostrar_diagnostico = ns.get("_mostrar_diagnostico_mente")
            if callable(mostrar_diagnostico):
                mostrar_diagnostico()
            return True

        # Continuação operacional curta é resolvida diretamente pela fonte
        # canônica antes de clipboard, cooperação ou LLM. O coordenador geral
        # continua sendo a rota para todo o restante; esta barreira cobre
        # apenas políticas aditivas explicitamente seguras, como manter a
        # playlist e usar a nova faixa atual em ``essa também``.
        if texto_e_continuacao_aditiva(texto):
            continuidade_aditiva = resolver_continuacao_aditiva(
                getattr(estado_runtime, "mental", {}),
                texto=texto,
            )
            if continuidade_aditiva:
                executar = ns.get("executar_intencao")
                if callable(executar):
                    try:
                        executou = bool(executar(continuidade_aditiva, texto))
                    except Exception as erro:
                        print(
                            "⚠️ [PRIORIDADE:CONTINUIDADE] falha isolada: "
                            f"{type(erro).__name__}: {erro}"
                        )
                        return True
                    registrar = ns.get("_registrar_resultado_execucao")
                    if callable(registrar):
                        registrar(
                            continuidade_aditiva,
                            texto,
                            executou,
                            origem="prioritario_continuidade_aditiva",
                        )
                    print(
                        "⚡ [PRIORIDADE:CONTINUIDADE] "
                        f"intent={continuidade_aditiva.get('intent')}"
                    )
                    return True

        # Repetições explícitas usam a mesma fonte canônica que planejou o
        # turno. A lista de operações reexecutáveis permanece centralizada em
        # ``contexto_compartilhado.intencao_reexecutavel``; esta barreira não
        # mantém vocabulário, destinos ou estados paralelos. Assim pedidos
        # como ``tenta de novo`` refazem um PLAYLIST_ADD que falhou sem cair na
        # conversa livre e sem adivinhar outra playlist.
        resolver_repeticao = ns.get("_resolver_repeticao_ultima_acao")
        try:
            repeticao_canonica = (
                resolver_repeticao(texto)
                if callable(resolver_repeticao)
                else None
            )
        except Exception as erro:
            print(
                "⚠️ [PRIORIDADE:REPETIÇÃO] falha isolada: "
                f"{type(erro).__name__}: {erro}"
            )
            repeticao_canonica = None
        if isinstance(repeticao_canonica, dict):
            executar = ns.get("executar_intencao")
            if callable(executar):
                try:
                    executou = bool(executar(repeticao_canonica, texto))
                except Exception as erro:
                    print(
                        "⚠️ [PRIORIDADE:REPETIÇÃO] execução falhou: "
                        f"{type(erro).__name__}: {erro}"
                    )
                    return True
                registrar = ns.get("_registrar_resultado_execucao")
                if callable(registrar):
                    registrar(
                        repeticao_canonica,
                        texto,
                        executou,
                        origem="prioritario_repeticao_canonica",
                    )
                print(
                    "⚡ [PRIORIDADE:REPETIÇÃO] "
                    f"intent={repeticao_canonica.get('intent')}"
                )
                return True

        # Uma entrada de barra é um comando interno ou uma tentativa dele;
        # nunca representa "sim" para uma pergunta aberta. Isso evita que um
        # typo ou a saída concorrente do terminal entregue o clipboard para
        # resumo por engano.
        if str(texto or "").lstrip().startswith("/"):
            print("⚠️ [COMANDO INTERNO] comando de barra não reconhecido")
            return True

        # É uma leitura explícita da aba atual. Ela precisa vencer caixa de
        # entrada, clipboard e especialistas genéricos; nenhum deles deve
        # consumir o pedido e deixar um plano vazio.
        if self._processar_resumo_pagina(texto, ns):
            return True

        # Curadorias próprias têm identidade e ordinal próprios. Consultamos o
        # detector canônico diretamente nesta barreira para que ``sua primeira
        # playlist`` não seja rebaixada a conversa ou confundida com uma lista
        # do usuário por classificadores genéricos executados mais adiante.
        detectar_deterministico = ns.get("detectar_intencao_deterministica")
        texto_curadoria = _texto_normalizado_local(texto)
        menciona_curadoria = bool(re.search(
            r"\b(?:sua|suas|dela|da\s+laylay)\s+"
            r"(?:(?:primeira|segunda|terceira|quarta|quinta|\d+[ªa]?)\s+)?"
            r"playlists?\b|"
            r"\bplaylists?\s+(?:da\s+laylay|dela|que\s+(?:voce|você)\s+"
            r"(?:criou|fez|montou|separou|organizou|preparou))\b",
            texto_curadoria,
        ))
        try:
            curadoria = (
                detectar_deterministico(texto)
                if menciona_curadoria and callable(detectar_deterministico)
                else None
            )
        except Exception as erro:
            print(
                "⚠️ [PRIORIDADE:CURADORIA] detecção falhou sem bloquear o "
                f"turno: {type(erro).__name__}: {erro}"
            )
            curadoria = None
        intent_curadoria = str(
            (curadoria or {}).get("intent")
            if isinstance(curadoria, dict) else ""
        ).upper().strip()
        if intent_curadoria in {
            "LAYLAY_PLAYLIST_PLAY", "LAYLAY_PLAYLIST_LIST", "LAYLAY_PLAYLIST_COPY",
        }:
            executar = ns.get("executar_intencao")
            if not callable(executar):
                return False
            try:
                executou = bool(executar(curadoria, texto))
            except Exception as erro:
                print(
                    "⚠️ [PRIORIDADE:CURADORIA] execução falhou: "
                    f"{type(erro).__name__}: {erro}"
                )
                return True
            registrar = ns.get("_registrar_resultado_execucao")
            if callable(registrar):
                registrar(
                    curadoria,
                    texto,
                    executou,
                    origem="prioritario_curadoria_laylay",
                )
            print(
                "⚡ [PRIORIDADE:CURADORIA] "
                f"intent={intent_curadoria} executou={executou}"
            )
            return True

        # Um pedido operacional novo (inclusive uma nova frase vaga como
        # "queria ouvir uma música") substitui uma pergunta antiga de campo
        # faltante. Isso evita que, depois de trocar de assunto, uma palavra
        # curta seja acidentalmente usada para completar o comando anterior.
        texto_tem_comando = ns.get("_texto_tem_comando_explicito")
        try:
            novo_comando = bool(texto_tem_comando(texto)) if callable(texto_tem_comando) else False
        except Exception:
            novo_comando = False
        if novo_comando or detectar_esclarecimento_operacional(texto):
            if callable(getattr(estado_runtime, "substituir", None)):
                estado_runtime.substituir(
                    "mental",
                    limpar_esclarecimento_operacional(
                        getattr(estado_runtime, "mental", {}),
                        motivo="substituida",
                    ),
                )

        caixa_entrada = ns.get("_caixa_entrada_pessoal_runtime")
        composto_caixa_agenda = segmentar_composto_caixa_agenda(texto)
        if (
            composto_caixa_agenda
            and callable(getattr(caixa_entrada, "processar", None))
        ):
            primeira, segunda = composto_caixa_agenda
            falar = ns.get("falar_com_lipsync")
            primeira_norm = _texto_normalizado_local(primeira).strip(" .,!?:;")
            referencia_generica = bool(re.fullmatch(
                r"(?:guarda|guarde|salva|salve|anota|anote)\s+"
                r"(?:(?:essa|esta|a|minha)\s+)?ideia",
                primeira_norm,
            ))
            item_salvo = None

            # Em uma composição como "guarda essa ideia e me lembra dela",
            # a referência só é válida quando a caixa publicou um item tipado
            # que acabou de criar. Não deixamos a própria caixa procurar uma
            # fala histórica: isso já fez uma pergunta de conhecimento virar
            # conteúdo de lembrete.
            obter_item_criado = getattr(caixa_entrada, "ultimo_item_criado", None)
            if referencia_generica and callable(obter_item_criado):
                try:
                    candidato = obter_item_criado()
                except Exception:
                    candidato = None
                tipo_candidato = str(
                    (candidato or {}).get("tipo") if isinstance(candidato, dict) else ""
                ).casefold().strip()
                if isinstance(candidato, dict) and tipo_candidato in {
                    "ideia", "ideia_discutida",
                }:
                    item_salvo = dict(candidato)
                    guardou = True
                else:
                    guardou = False
            else:
                try:
                    guardou = bool(caixa_entrada.processar(primeira))
                except Exception as erro:
                    print(
                        "⚠️ [PRIORIDADE:COOPERAÇÃO] caixa de entrada falhou: "
                        f"{type(erro).__name__}: {erro}"
                    )
                    guardou = False
            if not guardou:
                if callable(falar):
                    if referencia_generica and callable(obter_item_criado):
                        falar(
                            "Não tenho uma ideia recém-guardada para ligar a esse "
                            "lembrete. Me diga qual ideia você quis dizer.",
                            "calma",
                            1,
                        )
                    else:
                        falar(
                            "Não consegui guardar a ideia, então não criei um lembrete "
                            "solto sem o contexto dela.",
                            "calma",
                            1,
                        )
                return True

            resolver = ns.get("resolver_comando_natural")
            try:
                resolucao = (
                    resolver(segunda, "prioritario-cooperativo-caixa-agenda")
                    if callable(resolver)
                    else (None, "")
                )
            except Exception as erro:
                print(
                    "⚠️ [PRIORIDADE:COOPERAÇÃO] agenda não foi resolvida: "
                    f"{type(erro).__name__}: {erro}"
                )
                resolucao = (None, "")
            comando_agenda = (
                resolucao[0]
                if isinstance(resolucao, tuple) and len(resolucao) == 2
                else None
            )
            obter_item_salvo = getattr(caixa_entrada, "ultimo_item_salvo", None)
            if item_salvo is None and callable(obter_item_salvo):
                try:
                    item_salvo = obter_item_salvo()
                except Exception:
                    item_salvo = None
            if isinstance(comando_agenda, dict) and isinstance(item_salvo, dict):
                comando_agenda = {
                    **comando_agenda,
                    "params": dict(comando_agenda.get("params") or {}),
                }
                descricao_nota = str(
                    item_salvo.get("titulo")
                    or item_salvo.get("ideia_original")
                    or item_salvo.get("conteudo")
                    or ""
                ).strip()
                if descricao_nota:
                    comando_agenda["params"]["descricao"] = descricao_nota[:500]
                nota_id = str(item_salvo.get("id") or "").strip()
                if nota_id:
                    comando_agenda["params"]["referencia_nota"] = nota_id
            intent_agenda = str(
                (comando_agenda or {}).get("intent")
                if isinstance(comando_agenda, dict)
                else ""
            ).upper().strip()
            executou_agenda = False
            orquestrador = ns.get("_orquestrador_cooperativo_runtime")
            cooperar_caixa_agenda = getattr(
                orquestrador, "processar_caixa_para_agenda", None,
            )
            if (
                intent_agenda in {"AGENDAR_LEMBRETE", "SCHEDULE"}
                and isinstance(item_salvo, dict)
                and callable(cooperar_caixa_agenda)
            ):
                try:
                    resultado_cooperativo = dict(cooperar_caixa_agenda(
                        item_salvo=item_salvo,
                        comando_agenda=comando_agenda,
                        texto_agenda=segunda,
                    ) or {})
                    executou_agenda = bool(resultado_cooperativo.get("ok"))
                except Exception as erro:
                    print(
                        "⚠️ [PRIORIDADE:COOPERAÇÃO] agenda falhou: "
                        f"{type(erro).__name__}: {erro}"
                    )
            elif intent_agenda in {"AGENDAR_LEMBRETE", "SCHEDULE"}:
                print(
                    "⚠️ [PRIORIDADE:COOPERAÇÃO] governança caixa+agenda "
                    "indisponível; agenda não executada"
                )
            if isinstance(comando_agenda, dict):
                registrar = ns.get("_registrar_resultado_execucao")
                if callable(registrar):
                    registrar(
                        comando_agenda,
                        segunda,
                        executou_agenda,
                        origem="prioritario_cooperativo_caixa_agenda",
                    )
            if not executou_agenda and callable(falar):
                falar(
                    "Guardei a ideia, mas não consegui criar nem confirmar o "
                    "lembrete. A nota continua salva.",
                    "calma",
                    1,
                )
            print(
                "⚡ [PRIORIDADE:COOPERAÇÃO] caixa+agenda | "
                f"nota=True agenda={executou_agenda}"
            )
            return True

        if self._processar_busca_arquivo_e_abrir_resultado(
            texto,
            ns,
            estado_runtime,
        ):
            return True

        # Consultas locais de estado são somente leitura e precisam vencer
        # o roteador operacional genérico. Sem esta barreira, perguntas como
        # "O Opera continua aberto?" podem ser consumidas como APP_OPEN antes
        # de processar_consulta_sistema_local ter chance de responder.
        # REGRESSAO_118_V1_20260814 | PRIORIDADE:SISTEMA:LEITURA
        try:
            tratado_sistema, rota_sistema = processar_consulta_sistema_local(
                contexto_prioritario, texto
            )
        except Exception as erro:
            print(
                "⚠️ [PRIORIDADE:SISTEMA:LEITURA] consulta local falhou sem "
                f"bloquear o turno: {type(erro).__name__}: {erro}"
            )
        else:
            if tratado_sistema:
                print(
                    "⚡ [PRIORIDADE:SISTEMA:LEITURA] "
                    f"rota={rota_sistema or 'consulta_sistema_local'}"
                )
                return True

        # Uma frase pode pedir duas habilidades cooperando no mesmo turno.
        # O ciclo canônico já sabia segmentar e executar a cadeia, mas essa
        # porta nunca era chamada pela fase prioritária; por isso o texto
        # inteiro escapava para a conversa e a Laylay às vezes confirmava uma
        # etapa inexistente. Cada trecho volta ao mesmo resolvedor canônico e
        # mantém suas próprias evidências, permissões e resultados.
        processar_cadeia = ns.get("processar_comandos_em_cadeia")
        if callable(processar_cadeia):
            try:
                if processar_cadeia(texto, "prioritario-cooperativo"):
                    print("⚡ [PRIORIDADE:COOPERAÇÃO] cadeia natural tratada")  # P0_CADEIA_CONTEXTO_VIVO_V2_20260815
                    return True
            except Exception as erro:
                print(
                    "⚠️ [PRIORIDADE:COOPERAÇÃO] cadeia natural falhou sem "
                    f"bloquear o turno: {type(erro).__name__}: {erro}"
                )

        # Elipses musicais curtas precisam usar o estado real da última ação,
        # antes que a conversa livre tente lhes dar outro significado. O
        # resolvedor contextual só devolve candidato quando existe música
        # recente; por isso um ``continua`` fora desse domínio segue o fluxo
        # normal. A execução e o registro permanecem inteiramente canônicos.
        if texto_pede_continuacao_musical_curta(texto):
            resolver_midia = ns.get("_resolver_comando_midia_contextual_forcado")
            try:
                continuacao_musical = (
                    resolver_midia(texto) if callable(resolver_midia) else None
                )
            except Exception as erro:
                print(
                    "⚠️ [PRIORIDADE:MÚSICA] continuidade falhou sem bloquear "
                    f"o turno: {type(erro).__name__}: {erro}"
                )
                continuacao_musical = None
            intent_musical = str(
                (continuacao_musical or {}).get("intent")
                if isinstance(continuacao_musical, dict) else ""
            ).upper().strip()
            if intent_musical in {"MUSIC_SEARCH", "MEDIA_CONTROL"}:
                executar = ns.get("executar_intencao")
                if not callable(executar):
                    return False
                try:
                    executou = bool(executar(continuacao_musical, texto))
                except Exception as erro:
                    print(
                        "⚠️ [PRIORIDADE:MÚSICA] execução contextual falhou: "
                        f"{type(erro).__name__}: {erro}"
                    )
                    return True
                registrar = ns.get("_registrar_resultado_execucao")
                if callable(registrar):
                    registrar(
                        continuacao_musical,
                        texto,
                        executou,
                        origem="prioritario_continuidade_musical",
                    )
                print(
                    "⚡ [PRIORIDADE:MÚSICA] continuidade contextual tratada | "
                    f"intent={intent_musical}"
                )
                return True

        if texto_recusa_musica_agora(texto):
            bloquear = ns.get("_bloquear_playlist_temporariamente")
            if callable(bloquear):
                try:
                    bloquear(600.0)
                except Exception:
                    pass
            falar = ns.get("falar_com_lipsync")
            if callable(falar):
                falar("Pode deixar, não vou tocar nada agora.", "calma", 1)
            print("🛡️ [PRIORIDADE:MÚSICA] recusa atual respeitada; nenhum comando criado")
            return True

        if texto_pergunta_como_apagar_item(texto):
            falar = ns.get("falar_com_lipsync")
            if callable(falar):
                falar(
                    "Você pode apagar pelo Explorador de Arquivos. Se pedir para mim, "
                    "eu confirmo o item antes e o envio para a lixeira, onde ainda dá "
                    "para restaurar.",
                    "calma",
                    1,
                )
            print("🛡️ [PRIORIDADE:ARQUIVOS] explicação segura sem executar exclusão")
            return True

        orquestrador_cooperativo = ns.get("_orquestrador_cooperativo_runtime")
        if callable(getattr(orquestrador_cooperativo, "processar", None)):
            try:
                if orquestrador_cooperativo.processar(texto):
                    print("⚡ [PRIORIDADE:COOPERAÇÃO] plano entre habilidades tratado")
                    return True
            except Exception as erro:
                print(
                    "⚠️ [COOPERAÇÃO] falha isolada: "
                    f"{type(erro).__name__}: {erro}"
                )
        processar_oferta_clipboard = ns.get("_processar_oferta_area_transferencia_pendente")
        if callable(processar_oferta_clipboard):
            try:
                if processar_oferta_clipboard(texto):
                    print("⚡ [PRIORIDADE:ÁREA DE TRANSFERÊNCIA] resposta natural à oferta tratada")
                    return True
            except Exception as erro:
                print(
                    "⚠️ [ÁREA DE TRANSFERÊNCIA] resposta à oferta isolada: "
                    f"{type(erro).__name__}: {erro}"
                )
        # Estas habilidades eram atalhos do pré-fluxo. Agora pertencem à fase
        # operacional única, depois da criação do turno e antes da conversa.
        habilidades_prioritarias = (
            processar_identidade_usuario,
            processar_consulta_sistema_local,
            processar_pedido_direcao_musical,
            processar_esclarecimento_operacional,
            processar_sugestao_indireta,
            processar_aprendizado_apelido,
        )
        for habilidade in habilidades_prioritarias:
            try:
                tratada, rota = habilidade(contexto_prioritario, texto)
            except Exception as erro:
                print(
                    "⚠️ [PRIORIDADE:HABILIDADE] falha isolada em "
                    f"{habilidade.__name__}: {type(erro).__name__}: {erro}"
                )
                continue
            if tratada:
                print(
                    "⚡ [PRIORIDADE:HABILIDADE] "
                    f"rota={rota or habilidade.__name__}"
                )
                return True
        memoria_pessoas = self.memoria_pessoas
        if callable(getattr(memoria_pessoas, "processar", None)):
            try:
                if memoria_pessoas.processar(texto):
                    print("⚡ [PRIORIDADE:MEMÓRIA DE PESSOAS] pedido tratado")
                    return True
            except Exception as erro:
                print(
                    "⚠️ [MEMÓRIA:PESSOAS] falha isolada: "
                    f"{type(erro).__name__}: {erro}"
                )
        central_notificacoes = ns.get("_central_notificacoes_runtime")
        detectar_notificacao = getattr(central_notificacoes, "detectar", None)
        if callable(detectar_notificacao):
            try:
                comando_notificacao = detectar_notificacao(texto)
            except Exception as erro:
                print(
                    "⚠️ [CENTRAL DE NOTIFICAÇÕES] falha isolada: "
                    f"{type(erro).__name__}: {erro}"
                )
                comando_notificacao = None
            if isinstance(comando_notificacao, dict):
                executar = ns.get("executar_intencao")
                if callable(executar):
                    executou = bool(executar(comando_notificacao, texto))
                    registrar = ns.get("_registrar_resultado_execucao")
                    if callable(registrar):
                        registrar(
                            comando_notificacao,
                            texto,
                            executou,
                            origem="prioritario_central_notificacoes",
                        )
                    print("⚡ [PRIORIDADE:NOTIFICAÇÕES] pedido tratado pela central")
                    return True
        area_transferencia = ns.get("_area_transferencia_runtime")
        if callable(getattr(area_transferencia, "processar", None)):
            try:
                if area_transferencia.processar(texto):
                    print("⚡ [PRIORIDADE:ÁREA DE TRANSFERÊNCIA] pedido temporário tratado")
                    return True
            except Exception as erro:
                print(
                    "⚠️ [ÁREA DE TRANSFERÊNCIA] falha isolada: "
                    f"{type(erro).__name__}: {erro}"
                )
        if callable(getattr(caixa_entrada, "processar", None)):
            try:
                if caixa_entrada.processar(texto):
                    print("⚡ [PRIORIDADE:CAIXA DE ENTRADA] pedido pessoal tratado")
                    return True
            except Exception as erro:
                print(
                    "⚠️ [CAIXA DE ENTRADA] falha isolada: "
                    f"{type(erro).__name__}: {erro}"
                )

        # Continuacoes web, navegacao de abas e controles explicitos precisam
        # vencer a porta de arquivos abaixo. Em especial, ``abre o primeiro
        # resultado`` pode parecer uma referencia a uma busca local antiga,
        # embora o contrato vivo mais recente seja uma SEARCH web. Reusamos o
        # detector canonico e promovemos somente intents estreitas; nenhuma
        # segunda gramatica ou autorizacao nasce aqui.
        detectar_deterministico = ns.get("detectar_intencao_deterministica")
        texto_iot_previo = str(texto or "")
        menciona_iot_protegido = bool(re.search(
            r"\b(?:luz|luzes|lampada|lâmpada|ventilador|tomada|dispositivo|aparelho|iot)\b",
            texto_iot_previo,
            flags=re.IGNORECASE,
        )) and bloqueia_controle_iot_por_modalidade(texto_iot_previo)
        if menciona_iot_protegido:
            # A resposta instrucional/negada é tratada pela barreira própria
            # logo abaixo. Nem sequer consultamos o detector operacional.
            candidato_imediato = None
        else:
            try:
                candidato_imediato = (
                    detectar_deterministico(texto)
                    if callable(detectar_deterministico)
                    else None
                )
            except Exception as erro:
                print(
                    "⚠️ [PRIORIDADE:DETERMINÍSTICO] detecção isolada falhou: "
                    f"{type(erro).__name__}: {erro}"
                )
                candidato_imediato = None
        # P0_DEITICOS_DOMINIO_20260814
        # O determinístico detecta; o domínio atual decide se ele pode agir.
        dominio_contextual_p0 = _dominio_restrito_referencia(
            texto,
            getattr(estado_runtime, "mental", {}),
            ttl_s=300.0,
        )
        if (
            isinstance(candidato_imediato, dict)
            and dominio_contextual_p0
            and not _resultado_compativel_com_dominio(
                candidato_imediato,
                dominio_contextual_p0,
            )
        ):
            print(
                "🛡️ [P0:CONTEXTO] determinístico descartado por domínio | "
                f"dominio={dominio_contextual_p0} "
                f"intent={candidato_imediato.get('intent')}"
            )
            candidato_imediato = None

        intent_imediato = str(
            (candidato_imediato or {}).get("intent")
            if isinstance(candidato_imediato, dict) else ""
        ).upper().strip()
        params_imediatos = dict(
            (candidato_imediato or {}).get("params") or {}
        ) if isinstance(candidato_imediato, dict) else {}
        continuacao_web = bool(
            intent_imediato == "SEARCH"
            and params_imediatos.get("origem") == "continuacao_resultado_web"
        )
        if continuacao_web or intent_imediato in {
            "SWITCH_PREVIOUS_TAB", "MEDIA_CONTROL", "MUSIC_STATUS",
            "IOT_CONTROL",
        }:
            executar = ns.get("executar_intencao")
            if not callable(executar):
                return False
            try:
                executou = bool(executar(candidato_imediato, texto))
            except Exception as erro:
                print(
                    "⚠️ [PRIORIDADE:DETERMINÍSTICO] execução falhou: "
                    f"{type(erro).__name__}: {erro}"
                )
                return True
            registrar = ns.get("_registrar_resultado_execucao")
            if callable(registrar):
                registrar(
                    candidato_imediato,
                    texto,
                    executou,
                    origem="prioritario_deterministico_contextual",
                )
            print(
                "⚡ [PRIORIDADE:DETERMINÍSTICO] "
                f"intent={intent_imediato} executou={executou}"
            )
            return True

        # Busca e restauração local de arquivos não devem
        # depender da classificação da LLM. O coordenador canônico continua
        # responsável pela linguagem natural geral, mas esta porta garante
        # que pedidos explícitos como "encontra o código que controla X"
        # cheguem ao executor mesmo se o detector composto estiver degradado
        # ou o retrato de modalidade do turno tiver sido classificado cedo
        # demais. O próprio detector bloqueia perguntas de capacidade,
        # hipóteses e negações. FILE_SEARCH e FILE_OPEN_RESULT são leituras;
        # RESTORE_DELETED_ITEM é uma mutação reversível, mas só nasce de uma
        # referência explícita ao último item enviado à lixeira.
        normalizar = ns.get("_normalizar_texto_com_apelidos")
        try:
            candidato_arquivo = detectar_intencao_arquivos(
                texto,
                params_cb=lambda **kwargs: kwargs,
                estado_mental=getattr(estado_runtime, "mental", {}),
                normalizar_texto=normalizar,
            )
        except Exception as erro:
            print(
                "⚠️ [PRIORIDADE:ARQUIVOS] detecção de leitura falhou: "
                f"{type(erro).__name__}: {erro}"
            )
            candidato_arquivo = None
        intent_arquivo = str(
            (candidato_arquivo or {}).get("intent")
            if isinstance(candidato_arquivo, dict) else ""
        ).upper()
        params_arquivo = dict(
            (candidato_arquivo or {}).get("params") or {}
        ) if isinstance(candidato_arquivo, dict) else {}
        operacao_arquivo_prioritaria = (
            intent_arquivo in {
                "FILE_SEARCH", "FILE_READ", "FILE_OPEN_RESULT",
                "RESTORE_DELETED_ITEM",
            }
            or (intent_arquivo == "CREATE_FILE" and bool(params_arquivo.get("editar_existente")))
        )
        if isinstance(candidato_arquivo, dict) and operacao_arquivo_prioritaria:
            executar = ns.get("executar_intencao")
            if not callable(executar):
                return False
            try:
                executou = bool(executar(candidato_arquivo, texto))
            except Exception as erro:
                print(
                    "⚠️ [PRIORIDADE:ARQUIVOS] busca falhou: "
                    f"{type(erro).__name__}: {erro}"
                )
                return True
            registrar = ns.get("_registrar_resultado_execucao")
            if callable(registrar):
                registrar(
                    candidato_arquivo,
                    texto,
                    executou,
                    origem="prioritario_busca_arquivos",
                )
            print(
                "⚡ [PRIORIDADE:ARQUIVOS] operação contextual tratada | "
                f"intent={str(candidato_arquivo.get('intent') or '').upper()}"
            )
            return True

        # Referências curtas precisam consultar a entidade tipada publicada
        # pelo último executor antes da conversa livre. Esta é a rota real de
        # ``fecha ele`` após abrir um site, arquivo ou aplicativo. Limitamos a
        # barreira a molduras referenciais inequívocas e aceitamos somente
        # intents que o resolvedor canônico já autorizou.
        # P0_NAVEGADOR_SUBTIPO_V3_1_20260815
        if texto_referencia_tipificada_prioritaria(texto):
            resolver_contextual = ns.get("_resolver_comando_contextual_forcado")
            try:
                comando_contextual = (
                    resolver_contextual(texto)
                    if callable(resolver_contextual)
                    else None
                )
            except Exception as erro:
                print(
                    "⚠️ [PRIORIDADE:REFERÊNCIA] resolução falhou: "
                    f"{type(erro).__name__}: {erro}"
                )
                comando_contextual = None
            intent_contextual = str(
                (comando_contextual or {}).get("intent")
                if isinstance(comando_contextual, dict) else ""
            ).upper()
            if intent_contextual in {
                "CLOSE_TAB", "CLOSE_APP", "FILE_OPEN_RESULT", "OPEN_URL",
                "SWITCH_PREVIOUS_TAB", "MEDIA_CONTROL", "PLAYLIST_PLAY",
            }:
                executar = ns.get("executar_intencao")
                if not callable(executar):
                    return False
                try:
                    executou = bool(executar(comando_contextual, texto))
                except Exception as erro:
                    print(
                        "⚠️ [PRIORIDADE:REFERÊNCIA] execução falhou: "
                        f"{type(erro).__name__}: {erro}"
                    )
                    return True
                registrar = ns.get("_registrar_resultado_execucao")
                if callable(registrar):
                    registrar(
                        comando_contextual,
                        texto,
                        executou,
                        origem="prioritario_referencia_tipificada",
                    )
                print(
                    "⚡ [PRIORIDADE:REFERÊNCIA] "
                    f"intent={intent_contextual} executou={executou}"
                )
                return True
        resolver_repeticao = ns.get("_resolver_repeticao_ultima_acao")
        if callable(resolver_repeticao) and callable(getattr(caixa_entrada, "reexecutar", None)):
            try:
                repeticao = resolver_repeticao(texto)
            except Exception:
                repeticao = None
            if (
                isinstance(repeticao, dict)
                and str(repeticao.get("intent") or "").upper() == "INBOX_LIST"
                and caixa_entrada.reexecutar(repeticao, texto)
            ):
                print("⚡ [PRIORIDADE:CAIXA DE ENTRADA] consulta repetida pela continuidade oficial")
                return True
        texto_iot = str(texto or "")
        menciona_iot = bool(re.search(
            r"\b(?:luz|luzes|lampada|lâmpada|ventilador|tomada|dispositivo|aparelho|iot)\b",
            texto_iot,
            flags=re.IGNORECASE,
        ))
        if menciona_iot and bloqueia_controle_iot_por_modalidade(texto_iot):
            # É instrução, dúvida ou recusa sobre uma ação, não uma ação. Uma
            # resposta local curta evita LLM e impede que os roteadores sejam
            # chamados novamente no pós-processamento.
            pergunta_como = bool(re.search(
                r"^(?:como\s+(?:eu\s+)?(?:faria|faço|faco|posso|poderia)|"
                r"o\s+que\s+(?:eu\s+)?(?:faria|faço|faco))\b",
                texto_iot.strip(),
                flags=re.IGNORECASE,
            ))
            if pergunta_como:
                fala = (
                    "É só me pedir diretamente para desligar a luz. "
                    "Como você perguntou apenas como fazer, não alterei nada agora."
                )
            elif re.search(r"\btalvez\b", texto_iot, flags=re.IGNORECASE):
                fala = (
                    "Pode ser uma boa. Como você falou como possibilidade, deixei a "
                    "luz como está. Quando quiser executar, é só pedir diretamente."
                )
            else:
                fala = "Pode deixar. Não vou alterar a luz."
            print("🛡️ [PRIORIDADE:IOT] menção sem autorização; nenhum comando foi criado")
            falar = ns.get("falar_com_lipsync")
            if callable(falar):
                falar(fala, "calma", 1)
            return True
        # Consultas de estado são somente leitura. Elas precisam chegar ao
        # runtime IoT antes que "como ele está?" seja confundido com conversa.
        detectar_iot = getattr(self.iot, "detectar", None)
        estado_runtime = ns.get("_estado_compartilhado_runtime")
        mente_iot = getattr(estado_runtime, "mental", {})
        candidato_iot = (
            detectar_iot(texto, mente_iot)
            if callable(detectar_iot)
            else None
        )
        if isinstance(candidato_iot, dict) and str(candidato_iot.get("intent") or "").upper() == "IOT_STATUS":
            print("⚡ [PRIORIDADE:IOT] consulta contextual de estado")
            executar = ns.get("executar_intencao")
            if callable(executar):
                executou = bool(executar(candidato_iot, texto))
                registrar = ns.get("_registrar_resultado_execucao")
                if callable(registrar):
                    registrar(candidato_iot, texto, executou, origem="prioritario_iot_status")
                return True

        # Hipóteses e proibições com verbo operacional já foram barradas
        # pela modalidade canônica. Respondê-las localmente evita que a LLM
        # invente indisponibilidade e deixa explícito que nada foi executado.
        turno_protegido = classificar_modalidade_turno(texto)
        natureza_protegida = str(turno_protegido.get("natureza_acao") or "")
        moldura_hipotese_local = bool(re.match(
            r"^(?:talvez|estou\s+pensando\s+em|to\s+pensando\s+em|"
            r"seria\s+(?:bom|legal)|quem\s+sabe|tenho\s+vontade\s+de)\b",
            _texto_normalizado_local(texto),
        ))
        if (
            not turno_protegido.get("autoriza_execucao")
            and natureza_protegida in {"hipotetica", "cancelamento"}
            and (
                natureza_protegida == "cancelamento"
                or moldura_hipotese_local
            )
            and re.search(
                r"\b(?:abrir|abre|abra|fechar|fecha|feche|criar|cria|crie|"
                r"apagar|apaga|apague|excluir|remover|tocar|toca|toque|"
                r"ligar|liga|ligue|desligar|desliga|desligue|mover|move|"
                r"renomear|renomeia|organizar|organiza|pesquisar|pesquisa)\b",
                _texto_normalizado_local(texto),
            )
        ):
            fala = (
                "Ficou como uma possibilidade; não executei nem preparei essa ação."
                if natureza_protegida == "hipotetica"
                else "Pode deixar. Não executei essa ação."
            )
            print(
                "🛡️ [PRIORIDADE:MODALIDADE] menção operacional sem "
                "autorização; nenhum comando foi criado"
            )
            falar = ns.get("falar_com_lipsync")
            if callable(falar):
                falar(fala, "calma", 1)
            return True

        consulta_iot = detectar_consulta_lista_iot(texto)
        if consulta_iot:
            print("⚡ [PRIORIDADE:IOT] listagem objetiva de dispositivos")
            executar = ns.get("executar_intencao")
            if not callable(executar):
                return False
            try:
                executou = bool(executar(consulta_iot, texto))
            except Exception as erro:
                print(
                    "⚠️ [PRIORIDADE:IOT] falha ao listar: "
                    f"{type(erro).__name__}: {erro}"
                )
                return False
            registrar = ns.get("_registrar_resultado_execucao")
            if callable(registrar):
                registrar(
                    consulta_iot, texto, executou, origem="prioritario_iot_lista",
                )
            return True

        # Web e visão usam os detectores e executores canônicos, mas precisam
        # vencer a conversa genérica. A barreira fica depois das portas de
        # clipboard e IoT para não consultar roteadores paralelos quando uma
        # habilidade mais específica já consumiu o turno.
        detectar_deterministico = ns.get("detectar_intencao_deterministica")
        try:
            leitura_deterministica = (
                detectar_deterministico(texto)
                if callable(detectar_deterministico)
                else None
            )
        except Exception as erro:
            print(
                "⚠️ [PRIORIDADE:LEITURA] detecção falhou sem bloquear o "
                f"turno: {type(erro).__name__}: {erro}"
            )
            leitura_deterministica = None
        intent_leitura = str(
            (leitura_deterministica or {}).get("intent")
            if isinstance(leitura_deterministica, dict) else ""
        ).upper().strip()
        if intent_leitura in {"SEARCH", "VISION_QUERY"}:
            executar = ns.get("executar_intencao")
            if not callable(executar):
                return False
            try:
                executou = bool(executar(leitura_deterministica, texto))
            except Exception as erro:
                print(
                    "⚠️ [PRIORIDADE:LEITURA] execução falhou: "
                    f"{type(erro).__name__}: {erro}"
                )
                return True
            registrar = ns.get("_registrar_resultado_execucao")
            if callable(registrar):
                registrar(
                    leitura_deterministica,
                    texto,
                    executou,
                    origem="prioritario_leitura_deterministica",
                )
            print(
                "⚡ [PRIORIDADE:LEITURA] "
                f"intent={intent_leitura} executou={executou}"
            )
            return True

        if detectar_consulta_horario(texto):
            agora_cb = ns.get("_agora_temporal_cb")
            agora = agora_cb() if callable(agora_cb) else agora_no_fuso()
            fala = responder_consulta_horario(agora)
            print("⚡ [PRIORIDADE:RELÓGIO] consulta local objetiva")
            falar = ns.get("falar_com_lipsync")
            if callable(falar):
                falar(fala, "calma", 1)
            return True
        detectar_governanca = ns.get("_detectar_comando_governanca_iniciativa")
        pedido_governanca = (
            detectar_governanca(texto) if callable(detectar_governanca) else None
        )
        if pedido_governanca:
            print("⚡ [PRIORIDADE:AUTONOMIA] configuração explícita")
            processar_governanca = ns.get("_processar_governanca_iniciativa")
            if callable(processar_governanca):
                processar_governanca(pedido_governanca)
            return True
        detectar_saude = ns.get("detectar_comando_saude")
        if callable(detectar_saude) and detectar_saude(texto):
            print("⚡ [PRIORIDADE:SAÚDE] consulta objetiva do computador")
            falar_saude = ns.get("_falar_status_saude")
            if callable(falar_saude):
                falar_saude()
            return True
        # Última barreira antes da conversa: usa o coordenador canônico inteiro,
        # não só o detector de frases literais. Esse único caminho combina
        # linguagem natural, catálogo de habilidades, contexto, referências e
        # o árbitro de segurança. Ele também evita chamar o roteador uma vez
        # aqui e outra no fluxo principal.
        resolver_natural = ns.get("resolver_comando_natural")
        try:
            resolucao = (
                resolver_natural(texto, "prioritario-linguagem-natural")
                if callable(resolver_natural)
                else (None, "")
            )
        except Exception as erro:
            print(
                "⚠️ [PRIORIDADE:LINGUAGEM NATURAL] resolução falhou: "
                f"{type(erro).__name__}: {erro}"
            )
            resolucao = (None, "")
        detectada, rota = (
            resolucao
            if isinstance(resolucao, tuple) and len(resolucao) == 2
            else (None, "")
        )
        intent_detectada = str(
            (detectada or {}).get("intent") if isinstance(detectada, dict) else ""
        ).upper().strip()
        if (
            isinstance(detectada, dict)
            and intent_detectada in set(intents_registradas())
            and intent_detectada != "SUGGEST_ACTION"
        ):
            # Um comando novo e completo vence a pergunta anterior. Sem essa
            # limpeza, uma resposta curta futura poderia completar uma ação
            # que o usuário já abandonou ao formular o novo pedido.
            if callable(getattr(estado_runtime, "substituir", None)):
                estado_runtime.substituir(
                    "mental",
                    limpar_esclarecimento_operacional(
                        getattr(estado_runtime, "mental", {}),
                        motivo="substituida",
                    ),
                )
            print(
                "⚡ [PRIORIDADE:LINGUAGEM NATURAL] "
                f"intent={intent_detectada} | rota={rota or 'coordenador'}"
            )
            executar = ns.get("executar_intencao")
            if not callable(executar):
                return False
            try:
                executou = bool(executar(detectada, texto))
            except Exception as erro:
                print(
                    "⚠️ [PRIORIDADE:LINGUAGEM NATURAL] falha ao executar: "
                    f"{type(erro).__name__}: {erro}"
                )
                falar_falha = ns.get("_falar_falha_contextual")
                if callable(falar_falha):
                    falar_falha("execucao", texto)
                # A frase já foi compreendida; não a devolva à conversa para
                # inventar incapacidade, sucesso ou um pedido de repetição.
                return True
            registrar = ns.get("_registrar_resultado_execucao")
            if callable(registrar):
                registrar(
                    detectada,
                    texto,
                    executou,
                    origem=f"prioritario_linguagem_natural:{rota or 'coordenador'}",
                )
            autoaprimorar = ns.get("_registrar_autoaprimoramento")
            if executou and callable(autoaprimorar):
                autoaprimorar(
                    detectada,
                    texto,
                    True,
                    contexto=f"linguagem natural:{rota or 'coordenador'}",
                    origem="prioritario_linguagem_natural",
                )
            # Resultado indisponível também é um turno tratado. O executor do
            # domínio é quem relata a falha real, sem fallback conversacional.
            return True
        return False


def criar_comandos_imediatos_runtime(**kwargs: Any) -> ComandosImediatosRuntime:
    return ComandosImediatosRuntime(**kwargs)
