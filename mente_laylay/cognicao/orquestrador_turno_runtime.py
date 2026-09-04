"""Orquestração do plano, estado e verificação de cada turno."""

from __future__ import annotations

import time
import re
from typing import Any, Mapping

from mente_laylay.cognicao.contrato_fala import (
    construir_contrato_semantico_evento,
    construir_contrato_semantico_fala,
)
from mente_laylay.cognicao.contratos_turno import (
    normalizar_evento_cognitivo,
    texto_evento_cognitivo,
)
from mente_laylay.cognicao.leitura_semantica_turno import (
    aplicar_leitura_conversacional,
    comparar_com_legado,
)
from mente_laylay.cognicao.intencao_visual_jogo import (
    aplicar_pedido_visual_ao_turno,
    detectar_pedido_visao_jogo,
)
from mente_laylay.cognicao.fundamentacao_factual import (
    extrair_tema_recomendacao_contextual,
    extrair_titulos_citados,
)
from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno
from mente_laylay.cognicao.modalidade_turno import (
    aplicar_veto_canonico,
    autoriza_execucao_efetiva,
    turno_tem_veto_execucao,
)
from mente_laylay.memoria_mental.referencia_fala import extrair_referencia_musical_verificada
from mente_laylay.memoria_mental.memoria_confiavel import (
    extrair_aprendizados_pessoais_explicitos,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    descrever_quarentena_referencia_app,
)
from mente_laylay.memoria_mental.contexto_imediato import (
    referencia_app_quarentenavel_c1d,
)
from mente_laylay.memoria_mental.compatibilidade_contexto import (
    classificar_repeticao_curta,
)
from mente_laylay.memoria_mental.politica_reexecucao import (
    intents_compativeis_repeticao,
)

# ROOT_R1_V2_FAIL_CLOSED_TIPADO_20260826
from mente_laylay.emocoes.leitura_usuario import analisar_intencao_emocional
from mente_laylay.emocoes.contrato_causal import (
    criar_evento_leitura_emocional_usuario,
    criar_evento_leitura_semantica_usuario,
)
from mente_laylay.memoria_mental.eventos_emocionais import (
    publicar_evento_emocional_causal,
)


def observar_especialista_neural_turno(
    ns: Mapping[str, Any],
    texto: str,
    turno: Mapping[str, Any],
) -> dict[str, Any]:
    """Anexa telemetria neural sem conceder autoridade ou alterar o legado."""
    resultado = dict(turno or {})
    especialista = ns.get("_especialista_neural_comandos_runtime")
    if especialista is None:
        return resultado
    try:
        previsao = especialista.observar(texto, turno_legado=dict(resultado))
    except Exception as erro:
        logger = ns.get("print")
        if callable(logger):
            logger(f"⚠️ [NEURAL:COMANDOS] sombra isolada: {type(erro).__name__}")
        return resultado
    if previsao:
        resultado["previsao_neural"] = dict(previsao)
    return resultado


def finalizar_especialista_neural_turno(
    ns: Mapping[str, Any],
    texto: str,
    turno: Mapping[str, Any],
) -> dict[str, Any]:
    """Fecha a telemetria contra o turno final sem reclassificar a entrada."""
    resultado = dict(turno or {})
    especialista = ns.get("_especialista_neural_comandos_runtime")
    finalizar = getattr(especialista, "finalizar_observacao_turno", None)
    if not callable(finalizar):
        return resultado
    try:
        previsao = finalizar(texto, dict(resultado))
    except Exception as erro:
        logger = ns.get("print")
        if callable(logger):
            logger(f"⚠️ [NEURAL:SHADOW] fechamento isolado: {type(erro).__name__}")
        return resultado
    if previsao:
        resultado["previsao_neural"] = dict(previsao)
    return resultado


def registrar_metrica_opcional(ns: dict, componente: str, duracao_ms: float, sucesso: bool) -> None:
    """Registra telemetria sem depender de variáveis do escopo chamador."""
    observabilidade = ns.get('_observabilidade_mente_runtime') if isinstance(ns, dict) else None
    if observabilidade is None:
        return
    try:
        observabilidade.registrar_metrica(componente, duracao_ms, sucesso)
    except Exception:
        # Telemetria nunca pode interromper uma conversa.
        return


def registrar_falha_opcional(
    ns: dict,
    componente: str,
    codigo: str,
    erro: BaseException,
    *,
    classe: str,
    impacto: str,
    fallback: str,
) -> None:
    """Torna uma degradação visível no diagnóstico sem quebrar o turno.

    O objeto de observabilidade sanitiza o erro: mensagem, caminhos e conteúdo
    do usuário não são persistidos. Se a própria telemetria falhar, o fluxo
    principal continua intacto.
    """
    observabilidade = ns.get('_observabilidade_mente_runtime') if isinstance(ns, dict) else None
    registrar = getattr(observabilidade, 'registrar_falha', None)
    if not callable(registrar):
        return
    try:
        registrar(
            componente,
            codigo,
            erro=erro,
            classe=classe,
            impacto=impacto,
            fallback=fallback,
        )
    except Exception:
        # Observabilidade nunca pode ser uma nova causa de falha do turno.
        return


def consultar_repeticao_operacional_classificada_segura(
    ns: dict,
    texto: str,
) -> dict:
    """Preserva classificação, resultado e saúde da consulta separadamente.

    ``None`` não volta a carregar dois significados arquiteturais. O turno pode
    distinguir "não houve operação compatível" de "o resolvedor não respondeu"
    sem criar uma segunda gramática de repetição.
    """
    classificacao: dict = {}
    normalizar = ns.get('_normalizar_texto_com_apelidos')
    estado_classificacao = 'indisponivel'

    if callable(normalizar):
        try:
            classificacao = dict(
                classificar_repeticao_curta(texto, normalizar) or {}
            )
            estado_classificacao = 'ok'
        except Exception as erro:
            estado_classificacao = 'erro'
            registrar_falha_opcional(
                ns,
                'continuidade_turno',
                'falha_classificar_repeticao',
                erro,
                classe='defeito',
                impacto='turno',
                fallback='classificacao_repeticao_indisponivel',
            )

    resolver = ns.get('_resolver_repeticao_ultima_acao')
    if not callable(resolver):
        return {
            'estado': 'resolver_indisponivel',
            'estado_classificacao': estado_classificacao,
            'classificacao': classificacao,
            'repeticao': None,
        }

    try:
        repeticao_bruta = resolver(texto)
    except Exception as erro:
        registrar_falha_opcional(
            ns,
            'continuidade_turno',
            'falha_resolver_repeticao',
            erro,
            classe='defeito',
            impacto='turno',
            fallback='conversa_sem_repeticao',
        )
        return {
            'estado': 'resolver_erro',
            'estado_classificacao': estado_classificacao,
            'classificacao': classificacao,
            'repeticao': None,
        }

    return {
        'estado': 'ok',
        'estado_classificacao': estado_classificacao,
        'classificacao': classificacao,
        'repeticao': (
            dict(repeticao_bruta)
            if isinstance(repeticao_bruta, dict)
            else None
        ),
    }


def resolver_repeticao_operacional_segura(ns: dict, texto: str) -> dict | None:
    """Compatibilidade pública: devolve só a operação recuperada."""
    consulta = consultar_repeticao_operacional_classificada_segura(ns, texto)
    repeticao = consulta.get('repeticao')
    return dict(repeticao) if isinstance(repeticao, dict) else None


def obter_contexto_jogo_seguro(ns: dict) -> dict:
    """Obtém o modo de jogo sem esconder a perda de contexto perceptivo."""
    modo_jogo = ns.get('_modo_jogo_runtime')
    obter_contexto = getattr(modo_jogo, 'contexto_atual', None)
    if not callable(obter_contexto):
        return {}
    try:
        return dict(obter_contexto() or {})
    except Exception as erro:
        registrar_falha_opcional(
            ns,
            'contexto_jogo',
            'falha_contexto_atual',
            erro,
            classe='degradacao',
            impacto='turno',
            fallback='turno_sem_contexto_jogo',
        )
        return {}


def anexar_estado_visual_recente_seguro(ns: dict, jogo_contexto: dict) -> dict:
    """Anexa a recência visual ou registra por que ela não pôde ser usada."""
    contexto = dict(jogo_contexto or {})
    visao_jogo = ns.get('_registro_visao_jogo_leitura_runtime')
    verificar = getattr(visao_jogo, 'tem_analise_recente', None)
    if not callable(verificar):
        return contexto
    try:
        contexto['analise_visual_recente'] = bool(verificar())
    except Exception as erro:
        contexto['analise_visual_recente'] = False
        registrar_falha_opcional(
            ns,
            'contexto_visual_jogo',
            'falha_verificar_analise_recente',
            erro,
            classe='degradacao',
            impacto='turno',
            fallback='turno_sem_memoria_visual_recente',
        )
    return contexto


def aplicar_repeticao_operacional_ao_turno(turno: dict, repeticao: object) -> dict:
    """Autoriza uma repetição somente quando a mente recuperou uma ação real.

    A frase curta por si só continua ambígua. A autorização nasce do contrato
    persistido da última ação reexecutável, não de palavras-chave isoladas.
    """
    resultado = dict(turno or {})
    if not isinstance(repeticao, dict):
        return resultado
    intent = str(repeticao.get("intent") or "").strip().upper()
    params = repeticao.get("params")
    if not intent or not isinstance(params, dict):
        return resultado
    resultado.update(
        modalidade="comando",
        modalidade_geral="comando",
        ato_principal="comando",
        texto_operacional=str(resultado.get("texto") or "").strip(),
        confianca=max(0.97, float(resultado.get("confianca") or 0.0)),
        motivo="repetição explícita de ação reexecutável recuperada da mente",
        motivo_decisao="repetição explícita de ação reexecutável recuperada da mente",
        acao_explicita=True,
        autoriza_execucao=True,
        requer_esclarecimento=False,
        depende_contexto=True,
        natureza_acao="repeticao_operacional",
        repeticao_operacional={"intent": intent, "params": dict(params)},
    )
    return resultado


def aplicar_contrato_repeticao_classificada_ao_turno(
    turno: dict,
    *,
    texto: str,
    consulta: object,
) -> dict:
    """Congela a restrição lexical antes que contexto posterior a amplie.

    Repetições genéricas mantêm o comportamento legado. Uma repetição tipada
    só autoriza intents declaradas pela política semântica canônica. Quando a
    fala foi tipada mas nenhum resultado autorizável existe, o turno ganha um
    veto operacional sticky: contexto continua útil para conversa, nunca para
    trocar LER por outro domínio.
    """
    resultado = dict(turno or {})
    if turno_tem_veto_execucao(resultado):
        return resultado

    dados = dict(consulta or {}) if isinstance(consulta, dict) else {}
    classificacao = dict(dados.get('classificacao') or {})
    repeticao = (
        dict(dados.get('repeticao') or {})
        if isinstance(dados.get('repeticao'), dict)
        else None
    )

    if str(classificacao.get('tipo') or '') != 'tipada':
        return aplicar_repeticao_operacional_ao_turno(resultado, repeticao)

    acao_semantica = str(
        classificacao.get('acao_semantica') or ''
    ).strip().upper()
    permitidos = intents_compativeis_repeticao(acao_semantica)
    intent = str(
        (repeticao or {}).get('intent') or ''
    ).strip().upper()
    params = (repeticao or {}).get('params')

    if (
        bool(permitidos)
        and intent in permitidos
        and isinstance(params, dict)
    ):
        return aplicar_repeticao_operacional_ao_turno(
            resultado,
            {'intent': intent, 'params': dict(params)},
        )

    estado_consulta = str(dados.get('estado') or '').strip().casefold()
    if estado_consulta == 'resolver_erro':
        motivo = (
            'repetição tipada reconhecida, mas o resolvedor falhou antes de '
            'produzir operação semanticamente compatível'
        )
    elif estado_consulta == 'resolver_indisponivel':
        motivo = (
            'repetição tipada reconhecida, mas o resolvedor de continuidade '
            'está indisponível'
        )
    elif not permitidos:
        motivo = (
            'repetição tipada reconhecida sem política semântica de intents '
            'compatíveis'
        )
    elif repeticao:
        motivo = (
            'repetição tipada produziu operação incompatível com a restrição '
            f'{acao_semantica or "tipada"}'
        )
    else:
        motivo = (
            'repetição tipada sem operação reexecutável semanticamente '
            'compatível'
        )

    return aplicar_veto_canonico(
        resultado,
        texto=texto,
        modalidade='comando',
        natureza='repeticao_tipificada_sem_operacao_compativel',
        motivo=motivo,
        requer_esclarecimento=False,
        origem_veto='repeticao_tipificada_fail_closed',
    )


def _catalogo_apps_retarget_c1d(apps_map: object) -> dict[str, tuple[str, object]]:
    catalogo: dict[str, tuple[str, object]] = {}
    for chave, destino in dict(apps_map or {}).items():
        alias = re.sub(r"\s+", " ", str(chave or "")).strip()
        if not alias:
            continue
        destino_txt = str(destino or "").strip().casefold()
        if destino_txt.startswith(("http://", "https://")):
            continue
        catalogo[alias.casefold()] = (alias, destino)
    return catalogo


def _contexto_janela_ativo_retarget_c1d(mente: dict) -> bool:
    estado = dict(mente or {})
    return bool(
        str(estado.get("ultimo_app_janela") or "").strip()
        and str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").upper().strip()
        in {"APP_OPEN", "MAXIMIZE_WINDOW", "ORGANIZAR_DESKTOP"}
    )


def _detectar_retarget_app_receipt_c1d(texto: str, *, apps_map: object) -> dict | None:
    bruto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not bruto or "?" in bruto or any(ch in bruto for ch in ('"', "'", "“", "”", "‘", "’")):
        return None
    achado = re.fullmatch(
        r"agora\s+(?:(?:o|a)\s+)?(?P<nome>[A-Za-zÀ-ÿ0-9_. -]{2,80})[.!]*",
        bruto,
        flags=re.IGNORECASE,
    )
    if not achado:
        return None
    nome = re.sub(r"\s+", " ", str(achado.group("nome") or "")).strip(" .!")
    encontrado = _catalogo_apps_retarget_c1d(apps_map).get(nome.casefold())
    if not encontrado:
        return None
    alias, _destino = encontrado
    return {
        "tipo": "app",
        "nome": alias,
        "origem": "retarget_operacional_explicito",
        "somente_alvo": True,
        "autoriza_execucao": False,
    }


def aplicar_retarget_operacional_receipt_ao_turno(
    texto: str,
    *,
    turno: dict,
    mente: dict,
    apps_map: object,
    pendencia_turno: object = None,
) -> dict:
    leitura = dict(turno or {})
    if bool(leitura.get("autoriza_execucao")):
        return leitura
    if _pendencia_veta_elipse_espacial(pendencia_turno):
        return leitura
    if not _contexto_janela_ativo_retarget_c1d(mente):
        return leitura
    retarget = _detectar_retarget_app_receipt_c1d(texto, apps_map=apps_map)
    if not retarget:
        return leitura
    recibo = dict(retarget)
    recibo["retarget_turno_id"] = leitura.get("id")
    leitura["retarget_operacional"] = recibo
    return leitura

def _forma_elipse_espacial_exata(texto: str) -> str:
    bruto = str(texto or "").casefold().strip()
    if bruto == "esquerda":
        return "left"
    if bruto == "direita":
        return "right"
    return ""


def _pendencia_veta_elipse_espacial(pendencia: object) -> bool:
    """Uma fala curta ambígua nunca fura uma pendência ativa já falada."""
    p = dict(pendencia or {}) if isinstance(pendencia, dict) else {}
    if not p:
        return False
    status = str(p.get("status") or "").casefold()
    foi_falada = p.get("foi_falada")
    # No ciclo real `pendencia_turno` já veio de `pendencia_ativa`, mas esta
    # guarda local mantém o helper fail-closed quando chamado isoladamente.
    return bool(
        status in {"", "ativa"}
        and foi_falada is not False
        and (p.get("id") or p.get("tipo") or p.get("origem"))
    )


def aplicar_elipse_espacial_autorizada_ao_turno(
    texto: str,
    *,
    turno: dict,
    pendencia_turno: object = None,
) -> dict:
    leitura = dict(turno or {})
    direcao = _forma_elipse_espacial_exata(texto)
    if not direcao:
        return leitura
    if _pendencia_veta_elipse_espacial(pendencia_turno):
        return leitura
    leitura.update(
        modalidade="comando",
        modalidade_geral="comando",
        ato_principal="comando",
        texto_operacional="esquerda" if direcao == "left" else "direita",
        confianca=max(0.98, float(leitura.get("confianca") or 0.0)),
        motivo="direção espacial elíptica explicitamente pedida",
        motivo_decisao="direção espacial elíptica explicitamente pedida",
        acao_explicita=True,
        autoriza_execucao=True,
        requer_esclarecimento=True,
        depende_contexto=True,
        natureza_acao="pedido_direto",
        elipse_operacional={"tipo": "posicionamento_janela", "direcao": direcao, "alvo_requerido": "app"},
    )
    return leitura


def reconciliar_alvo_eliptico_janela_confirmado(
    texto: str,
    *,
    turno: dict,
    retrato: dict,
    mente: dict,
) -> tuple[dict, dict]:
    leitura = dict(turno or {})
    snapshot = dict(retrato or {})
    forma_max = str(texto or "").casefold().strip(" \t\r\n.,!?;:")
    forma_espacial = _forma_elipse_espacial_exata(texto)
    elipse = dict(leitura.get("elipse_operacional") or {})
    eh_maximiza = forma_max == "maximiza"
    eh_espacial = bool(
        forma_espacial
        and str(elipse.get("tipo") or "") == "posicionamento_janela"
        and str(elipse.get("direcao") or "") == forma_espacial
        and str(elipse.get("alvo_requerido") or "") == "app"
    )
    if not (eh_maximiza or eh_espacial):
        return leitura, snapshot
    if not bool(leitura.get("autoriza_execucao")) or not bool(leitura.get("requer_esclarecimento")):
        return leitura, snapshot

    if eh_espacial and forma_espacial == "right":
        anterior = dict(dict(mente or {}).get("turno_atual") or {})
        retarget = dict(anterior.get("retarget_operacional") or {})
        chaves = {"tipo", "nome", "origem", "somente_alvo", "autoriza_execucao", "retarget_turno_id"}
        if set(retarget) != chaves or bool(anterior.get("autoriza_execucao")):
            return leitura, snapshot
        if retarget.get("autoriza_execucao") is not False or retarget.get("somente_alvo") is not True:
            return leitura, snapshot
        if retarget.get("retarget_turno_id") != anterior.get("id"):
            return leitura, snapshot
        if str(retarget.get("tipo") or "").casefold() != "app" or str(retarget.get("origem") or "") != "retarget_operacional_explicito":
            return leitura, snapshot
        nome = str(retarget.get("nome") or "").strip()
        if not nome:
            return leitura, snapshot
        referencia = {
            "tipo": "app",
            "nome": nome,
            "origem": "retarget_operacional_explicito",
            "ts": float(anterior.get("ts") or time.time()),
            "dados": {"somente_alvo": True, "autoriza_execucao": False, "retarget_turno_id": anterior.get("id")},
        }
        snapshot["referencia_tipo"] = "app"
        snapshot["referencia_resolvida"] = referencia
        leitura["requer_esclarecimento"] = False
        leitura["depende_contexto"] = True
        leitura["referencia_resolvida"] = referencia
        leitura["alvo_contextual_resolvido"] = {"tipo": "app", "nome": nome, "origem": "elipse_operacional_retarget_confirmado"}
        return leitura, snapshot

    ultimo_app = str(dict(mente or {}).get("ultimo_app_janela") or "").strip()
    entidade_app = dict(dict(snapshot.get("entidades") or {}).get("app") or {})
    nome_app = str(entidade_app.get("nome") or "").strip()
    if not ultimo_app or not nome_app or ultimo_app.casefold() != nome_app.casefold():
        return leitura, snapshot
    referencia = dict(entidade_app)
    snapshot["referencia_tipo"] = "app"
    snapshot["referencia_resolvida"] = referencia
    leitura["requer_esclarecimento"] = False
    leitura["depende_contexto"] = True
    leitura["referencia_resolvida"] = referencia
    leitura["alvo_contextual_resolvido"] = {
        "tipo": "app",
        "nome": nome_app,
        "origem": "elipse_operacional_maximiza_confirmada" if eh_maximiza else "elipse_operacional_espacial_confirmada",
    }
    return leitura, snapshot

_ORIGENS_ENTRADA_VALIDAS = {
    'terminal', 'voz', 'modo_jogo', 'barra', 'api', 'presenca', 'desconhecida',
}


def _normalizar_origem_entrada(origem: object) -> str:
    valor = str(origem or 'desconhecida').strip().casefold()
    return valor if valor in _ORIGENS_ENTRADA_VALIDAS else 'desconhecida'


# P0_REVISAO_INTRA_TURNO_B1_2_1_20260816
def alinhar_identidade_plano_revisao(
    plano: dict,
    *,
    texto_original: str,
    texto_operacional_efetivo: str = '',
    revisao_intra_turno: dict | None = None,
) -> dict:
    """Separa a identidade pública do turno de sua visão operacional revisada.

    O planejador deve continuar recebendo a proposta final consolidada para não
    reintroduzir ações/alvos descartados. Depois do planejamento, porém,
    ``texto_usuario`` volta a representar a fala que realmente originou o
    turno. A visão operacional fica em um campo próprio e auditável.
    """
    resultado = dict(plano or {})
    resultado['texto_usuario'] = str(texto_original or '').strip()[:500]

    revisao = dict(revisao_intra_turno or {})
    if bool(revisao.get('detectada')):
        resultado['texto_operacional_efetivo'] = str(
            texto_operacional_efetivo or ''
        ).strip()[:500]
        resultado['revisao_intra_turno'] = revisao

    return resultado


def _iniciar_planejamento_evento(
    namespace_getter,
    evento: Mapping[str, Any],
    *,
    origem: str = 'presenca',
) -> dict:
    """Planeja evidência ambiental sem criar uma utterance artificial."""
    ns = namespace_getter()
    mente_antes_turno = dict(ns['_estado_compartilhado_runtime'].mental)
    entrada_cognitiva = dict(evento)
    texto_cognitivo = texto_evento_cognitivo(entrada_cognitiva)
    if not texto_cognitivo:
        texto_cognitivo = str(
            entrada_cognitiva.get('tipo') or 'evento observado'
        ).strip()

    turno = ns['_classificar_modalidade_turno_mente'](
        texto_cognitivo,
        normalizar_texto=ns['_normalizar_texto_com_apelidos'],
        texto_tem_comando_explicito=ns['_texto_tem_comando_explicito'],
        confirmacao_contextual_valida=False,
    )
    turno = aplicar_veto_canonico(
        turno,
        texto=texto_cognitivo,
        modalidade='conversa',
        natureza='evento_observado',
        motivo='evento observado não é utterance nem permissão do usuário',
        requer_esclarecimento=False,
        origem_veto='evento_sem_autoridade_usuario',
    )
    identidade_turno = {
        'falante': None,
        'interlocutor': None,
        'fonte_evidencia': str(entrada_cognitiva.get('origem') or 'percepcao'),
        'usuario_eu': False,
        'pedro_eu': False,
        'laylay_eu': False,
        'referencia_usuario': False,
        'referencia_pedro': False,
        'referencia_laylay': False,
    }
    funcao_comunicativa = {
        'funcao': 'evento_observado',
        'objetivo': 'interpretar o acontecimento e considerar uma reação comunicativa',
        'postura_esperada': 'natural',
        'permite_pergunta': False,
    }
    turno.update({
        'natureza_entrada': 'evento',
        'origem_entrada': _normalizar_origem_entrada(origem),
        'entrada_cognitiva': entrada_cognitiva,
        'texto_evidencia': texto_cognitivo,
        'identidade': identidade_turno,
        'funcao_comunicativa': funcao_comunicativa,
        'aprendizados_explicitos': [],
        'autoridade_usuario': False,
        'permissao_execucao': False,
        'autoriza_execucao': False,
        'texto_operacional': '',
    })

    jogo_contexto = obter_contexto_jogo_seguro(ns)
    jogo_contexto = anexar_estado_visual_recente_seguro(ns, jogo_contexto)
    retrato_turno, entidades_recentes = ns['_construir_retrato_turno_mente'](
        texto_cognitivo,
        turno=turno,
        mente=mente_antes_turno,
        contexto_perceptivo=ns['_obter_contexto_perceptivo'](),
        playlist_state=ns['playlist_state'],
        jogo_contexto=jogo_contexto,
    )
    turno['retrato_id'] = retrato_turno.get('id')
    turno['entidades'] = dict(retrato_turno.get('entidades') or {})
    turno['referencia_resolvida'] = dict(
        retrato_turno.get('referencia_resolvida') or {}
    )
    turno['operacao_explicita'] = ''
    especialistas = ns['_construir_parecer_especialistas_mente'](
        texto_cognitivo,
        turno=turno,
        funcao_comunicativa=funcao_comunicativa,
        retrato=retrato_turno,
        saude=ns['_saude_mente_runtime'].snapshot(),
    )
    turno['especialistas'] = especialistas
    plano = ns['_planejar_turno_mente'](
        texto_cognitivo,
        turno=turno,
        mente=mente_antes_turno,
        periodo=ns['_contexto_horario_atual'](),
    )
    contexto_necessario = [
        'evento_atual' if item == 'fala_atual' else item
        for item in list(plano.get('contexto_necessario') or [])
    ]
    plano.update({
        'natureza_entrada': 'evento',
        'origem_entrada': turno['origem_entrada'],
        'entrada_cognitiva': entrada_cognitiva,
        'texto_evidencia': texto_cognitivo,
        'texto_usuario': '',
        'contexto_necessario': list(dict.fromkeys(contexto_necessario)),
        'requer_execucao': False,
        'autoriza_execucao': False,
        'turno_sem_autorizacao': True,
        'texto_operacional': '',
        'resposta_esperada': (
            'interpretar o evento e formular apenas uma proposta comunicativa segura'
        ),
    })

    mensagens_recentes = list(
        getattr(ns['_estado_compartilhado_runtime'], 'memoria_conversa', {}).get(
            'messages', []
        )
        or []
    )
    falas_recentes = [
        str(item.get('content') or '').strip()
        for item in mensagens_recentes
        if isinstance(item, dict)
        and str(item.get('role') or '').casefold() == 'assistant'
    ][-3:]
    contrato_fala = construir_contrato_semantico_evento(
        entrada_cognitiva,
        turno=turno,
        plano=plano,
        mente=mente_antes_turno,
        falas_recentes=falas_recentes,
    )
    turno['contrato_fala'] = contrato_fala
    plano['contrato_fala'] = contrato_fala

    ns['_estado_compartilhado_runtime'].atualizar_campos(
        'mental',
        evento_cognitivo_atual=entrada_cognitiva,
        turno_atual=turno,
        plano_turno_atual=plano,
        contrato_fala_atual=contrato_fala,
        identidade_turno_atual=identidade_turno,
        identidade_turno_resumo=(
            'Entrada cognitiva de evento observado; não existe falante discursivo '
            'nem autoridade do usuário.'
        ),
        funcao_comunicativa_atual=funcao_comunicativa,
        retrato_turno_atual=retrato_turno,
        entidades_recentes=entidades_recentes,
        especialistas_turno_atual=especialistas,
    )
    ns['print'](
        '🧠 [PLANO:EVENTO] '
        f"tipo={entrada_cognitiva.get('tipo') or '-'} | "
        'execucao=False | proposta_comunicativa=True'
    )
    return turno


def iniciar_planejamento_turno(
    namespace_getter,
    texto: str | Mapping[str, Any],
    *,
    origem: str = 'desconhecida',
) -> dict:
    inicio_diagnostico = time.perf_counter()
    sucesso = False
    ns = namespace_getter()
    observabilidade = ns.get('_observabilidade_mente_runtime')
    try:
        evento = normalizar_evento_cognitivo(texto, origem=origem)
        if evento:
            resultado = _iniciar_planejamento_evento(
                namespace_getter,
                evento,
                origem=origem,
            )
        elif isinstance(texto, Mapping):
            raise ValueError(
                "entrada estruturada precisa declarar natureza='evento'"
            )
        else:
            resultado = _iniciar_planejamento_turno(
                namespace_getter,
                str(texto or ''),
                origem=origem,
            )
        sucesso = True
        return resultado
    except Exception as erro:
        if observabilidade is not None:
            observabilidade.registrar_falha('interpretacao', 'falha_planejamento', erro=erro)
        raise
    finally:
        if observabilidade is not None:
            observabilidade.registrar_metrica(
                'interpretacao', (time.perf_counter() - inicio_diagnostico) * 1000.0, sucesso,
            )


def _iniciar_planejamento_turno(
    namespace_getter,
    texto: str,
    *,
    origem: str = 'desconhecida',
) -> dict:
    ns = namespace_getter()
    mente_antes_turno = dict(ns['_estado_compartilhado_runtime'].mental)
    pendencia_turno = ns['_pendencia_ativa_turno_mente'](mente_antes_turno) or {}
    confirmacao_contextual_valida = bool(pendencia_turno.get('intencao') and (str(pendencia_turno.get('resposta_esperada') or '') == 'sim_ou_nao' or str(pendencia_turno.get('tipo') or '') in {'confirmacao', 'escolha'}))

    # P0_REVISAO_INTRA_TURNO_V1_1_20260816
    # Revisões dentro da própria fala são consolidadas antes do primeiro
    # detector operacional. O texto original continua auditável; apenas a
    # visão cognitiva/operacional recebe a última proposta válida.
    revisao_intra_turno = resolver_revisao_intra_turno(texto)
    revisao_detectada = bool(revisao_intra_turno.get('detectada'))
    revisao_resolvida = bool(revisao_intra_turno.get('resolvida'))
    revisao_cancelada = bool(revisao_intra_turno.get('cancelada'))
    texto_efetivo = str(
        revisao_intra_turno.get('texto_operacional_efetivo') or ''
    ).strip()
    texto_cognitivo = (
        texto_efetivo
        if revisao_detectada and revisao_resolvida and not revisao_cancelada and texto_efetivo
        else texto
    )

    turno = ns['_classificar_modalidade_turno_mente'](texto_cognitivo, normalizar_texto=ns['_normalizar_texto_com_apelidos'], texto_tem_comando_explicito=ns['_texto_tem_comando_explicito'], confirmacao_contextual_valida=confirmacao_contextual_valida)
    turno = observar_especialista_neural_turno(ns, texto_cognitivo, turno)
    turno['origem_entrada'] = _normalizar_origem_entrada(origem)
    if revisao_detectada:
        turno['texto_original'] = str(texto or '')[:500]
        turno['texto'] = str(texto or '')[:500]
        turno['revisao_intra_turno'] = dict(revisao_intra_turno)
        turno['texto_operacional_efetivo'] = texto_efetivo
        if not revisao_resolvida:
            motivo_revisao = str(
                revisao_intra_turno.get('motivo')
                or 'revisão interna detectada sem resolução operacional segura'
            )
            turno = aplicar_veto_canonico(
                turno,
                texto=texto,
                modalidade='correcao',
                natureza='revisao_ambigua',
                motivo=motivo_revisao,
                requer_esclarecimento=True,
                origem_veto='revisao_ambigua',
            )
        elif revisao_cancelada:
            turno = aplicar_veto_canonico(
                turno,
                texto=texto,
                modalidade='recusa',
                natureza='cancelamento_revisao',
                motivo=str(
                    revisao_intra_turno.get('motivo')
                    or 'usuário cancelou a proposta antes da execução'
                ),
                requer_esclarecimento=False,
                origem_veto='revisao_cancelada',
            )
        else:
            turno['texto_operacional'] = (
                texto_efetivo if autoriza_execucao_efetiva(turno) else ''
            )
            ns['print'](
                '🧠 [REVISÃO:TURNO] '
                f"tipo={revisao_intra_turno.get('tipo')} | "
                f"efetivo={texto_efetivo!r}"
            )

    # C1-D/D1: novo app isolado vira somente receipt target-only.
    if not turno_tem_veto_execucao(turno):
        turno = aplicar_retarget_operacional_receipt_ao_turno(
            texto_cognitivo,
            turno=turno,
            mente=mente_antes_turno,
            apps_map=ns.get("APPS_MAP", {}),
            pendencia_turno=pendencia_turno,
        )

    # C1-C: a direção atual pode conceder autoridade estreita por si.
    # Qualquer pendência ativa já falada veta esta elipse ambígua; contexto só
    # reduz autoridade e nunca fornece a permissão operacional da fala atual.
    if not turno_tem_veto_execucao(turno):
        turno = aplicar_elipse_espacial_autorizada_ao_turno(
            texto,
            turno=turno,
            pendencia_turno=pendencia_turno,
        )

    # Uma revisão atual não pode ser reinterpretada como repetição da ação
    # anterior só porque a proposta final contém "continua", "de novo" etc.
    consulta_repeticao = (
        {
            'estado': 'suprimida_revisao',
            'estado_classificacao': 'suprimida_revisao',
            'classificacao': {},
            'repeticao': None,
        }
        if revisao_detectada
        else consultar_repeticao_operacional_classificada_segura(ns, texto)
    )
    repeticao_operacional = consulta_repeticao.get('repeticao')
    if not turno_tem_veto_execucao(turno):
        turno = aplicar_contrato_repeticao_classificada_ao_turno(
            turno,
            texto=texto,
            consulta=consulta_repeticao,
        )
    if repeticao_operacional and not turno_tem_veto_execucao(turno):
        ns['print'](
            f"🔁 [TURNO] repetição operacional autorizada | "
            f"intent={str(repeticao_operacional.get('intent') or '-')}"
        )
    elif (
        str(dict(consulta_repeticao.get('classificacao') or {}).get('tipo') or '')
        == 'tipada'
        and turno_tem_veto_execucao(turno)
        and str(turno.get('origem_veto_execucao_operacional') or '')
        == 'repeticao_tipificada_fail_closed'
    ):
        ns['print'](
            "🛡️ [TURNO] repetição tipada sem operação compatível | "
            f"estado={consulta_repeticao.get('estado') or '-'}"
        )
    jogo_contexto = obter_contexto_jogo_seguro(ns)
    visao_jogo_runtime = ns.get('_registro_visao_jogo_leitura_runtime')
    jogo_contexto = anexar_estado_visual_recente_seguro(ns, jogo_contexto)
    if jogo_contexto.get('ativo') and callable(getattr(visao_jogo_runtime, 'observar_texto_usuario', None)):
        try:
            visao_jogo_runtime.observar_texto_usuario(texto)
        except Exception as erro:
            ns['print'](f"⚠️ [VISÃO:SESSÃO] contexto ignorado: {type(erro).__name__}")
    pedido_visao_jogo = detectar_pedido_visao_jogo(texto_cognitivo, jogo_contexto)
    if pedido_visao_jogo and not turno_tem_veto_execucao(turno):
        turno = aplicar_pedido_visual_ao_turno(turno, pedido_visao_jogo)
        ns['print'](
            f"🎮 [VISÃO:PEDIDO] tipo={pedido_visao_jogo['params'].get('tipo')} "
            f"| jogo={pedido_visao_jogo['params'].get('jogo') or '-'}"
        )
    # A leitura nova nasce como observadora. Ela é persistida para comparação,
    # mas não substitui modalidade, planejamento nem autorização de execução.
    leitura_semantica = {}
    interpretador_semantico = ns.get('_interpretador_semantico_runtime')
    modo_semantico = str(getattr(interpretador_semantico, 'modo', 'off') or 'off').lower()
    if modo_semantico == 'main':
        # A leitura virá junto da resposta principal; não faça uma segunda
        # chamada ao modelo antes do turno.
        leitura_semantica = {}
    elif modo_semantico == 'shadow' and callable(getattr(interpretador_semantico, 'observar', None)):
        try:
            interpretador_semantico.observar(texto_cognitivo, turno_legado=dict(turno))
        except Exception as erro:
            ns['print'](f"⚠️ [SEMÂNTICA] falha isolada ao agendar observação: {type(erro).__name__}")
    elif modo_semantico == 'conversation' and bool(turno.get('autoriza_execucao')):
        # A migração atual não toca em pedidos que o porteiro legado autorizou.
        leitura_semantica = {}
    elif interpretador_semantico is not None and callable(getattr(interpretador_semantico, 'analisar', None)):
        try:
            leitura_semantica = dict(interpretador_semantico.analisar(texto_cognitivo, turno_legado=turno) or {})
        except Exception as erro:
            ns['print'](f"⚠️ [SEMÂNTICA] falha isolada no modo observador: {type(erro).__name__}")
    if leitura_semantica:
        if modo_semantico == 'conversation' and not turno_tem_veto_execucao(turno):
            turno = aplicar_leitura_conversacional(turno, leitura_semantica)
            if str(turno.get('origem_modalidade') or '') == 'semantica_conversacional':
                ns['print'](
                    f"🧠 [SEMÂNTICA:APLICADA] modalidade={turno.get('modalidade_geral')} "
                    f"| atos={[item.get('ato') for item in turno.get('segmentos') or []]}"
                )
        else:
            turno['leitura_semantica_shadow'] = leitura_semantica
    identidade_turno = ns['_analisar_identidade_turno_mente'](texto, falante='pedro')
    funcao_comunicativa = ns['_analisar_funcao_comunicativa_mente'](texto_cognitivo)
    leitura_emocional_usuario = analisar_intencao_emocional(
        texto_cognitivo,
        normalizar_texto=lambda valor: ns['_normalizar_texto_com_apelidos'](valor),
    )
    encerramento_assunto = ns['_classificar_encerramento_assunto_mente'](texto, mente_antes_turno)
    correcao_duravel = ns['_extrair_correcao_duravel_mente'](texto, estado_mental=mente_antes_turno)
    correcao_interpretacao = ns['_abrir_correcao_interpretacao_mente'](mente_antes_turno, texto, eh_correcao=str(funcao_comunicativa.get('funcao') or '') == 'correcao')
    turno['identidade'] = identidade_turno
    turno['funcao_comunicativa'] = funcao_comunicativa
    turno['encerramento_assunto'] = encerramento_assunto
    retrato_turno, entidades_recentes = ns['_construir_retrato_turno_mente'](texto_cognitivo, turno=turno, mente=mente_antes_turno, contexto_perceptivo=ns['_obter_contexto_perceptivo'](), playlist_state=ns['playlist_state'], jogo_contexto=jogo_contexto)
    quarentena_app = descrever_quarentena_referencia_app(mente_antes_turno)
    if quarentena_app and referencia_app_quarentenavel_c1d(texto_cognitivo):
        retrato_turno = dict(retrato_turno)
        retrato_turno['referencia_tipo'] = 'app'
        retrato_turno['referencia_resolvida'] = {}
        retrato_turno['referencia_quarentenada'] = dict(quarentena_app)

    if not turno_tem_veto_execucao(turno):
        turno, retrato_turno = reconciliar_alvo_eliptico_janela_confirmado(
            texto_cognitivo, turno=turno, retrato=retrato_turno, mente=mente_antes_turno,
        )
    atualidade_factual = dict(retrato_turno.get('atualidade_factual') or {})
    turno['atualidade_factual'] = atualidade_factual
    if atualidade_factual.get('depende_atualidade'):
        ns['print'](
            f"🕒 [ATUALIDADE] classe={atualidade_factual.get('classe')} | "
            f"validade_sugerida={float(atualidade_factual.get('validade_sugerida_s') or 0.0):.0f}s | "
            f"confiança={float(atualidade_factual.get('confianca') or 0.0):.2f}"
        )
    limpeza_pergunta_turno = {}
    entidade_explicita = dict(retrato_turno.get('entidade_explicita') or {})
    topico_pendente = str(mente_antes_turno.get('pergunta_aberta_topico') or '').strip()
    nome_explicito = str(entidade_explicita.get('nome') or '').strip()
    funcao_atual = str(funcao_comunicativa.get('funcao') or '')
    topico_incompativel = bool(nome_explicito and topico_pendente and (nome_explicito.casefold() not in topico_pendente.casefold()) and (topico_pendente.casefold() not in nome_explicito.casefold()))
    if funcao_atual == 'correcao' or topico_incompativel:
        mente_limpa = ns['_limpar_pergunta_aberta_estado_mente'](mente_antes_turno)
        chaves_limpeza = ('pergunta_aberta_texto', 'pergunta_aberta_topico', 'pergunta_aberta_origem', 'pergunta_aberta_tipo', 'pergunta_aberta_proposito', 'pergunta_aberta_resposta_esperada', 'pergunta_aberta_ts', 'pendencia_atual', 'historico_pendencias')
        limpeza_pergunta_turno = {chave: mente_limpa.get(chave) for chave in chaves_limpeza if chave in mente_limpa}
        mente_antes_turno = mente_limpa
    registro_semantico = ns['_atualizar_registro_turno_mente'](mente_antes_turno.get('registro_semantico'), texto, retrato=retrato_turno, funcao=funcao_atual, encerramento=encerramento_assunto)
    mente_antes_turno['registro_semantico'] = registro_semantico
    candidatos_referencia = list(retrato_turno.get('referencia_candidatos') or [])
    if candidatos_referencia:
        resumo_candidatos = ', '.join((f"{item.get('nome')}:{float(item.get('pontuacao') or 0.0):.2f}" for item in candidatos_referencia[:3]))
        escolhida = dict(retrato_turno.get('referencia_resolvida') or {})
        ns['print'](f"🧠 [REFERÊNCIA] candidatos=[{resumo_candidatos}] | escolhido={escolhida.get('nome') or '-'} | operacao={retrato_turno.get('operacao_explicita') or '-'}")
    fundamentacao_factual = {}
    aprendizados_explicitos = extrair_aprendizados_pessoais_explicitos(texto)
    turno['aprendizados_explicitos'] = aprendizados_explicitos
    tema_factual = ns['_extrair_tema_fundamentacao_mente'](
        texto_cognitivo, retrato=retrato_turno, registro_semantico=registro_semantico,
    )
    # Uma declaração pessoal pode ativar memória e pesquisa ao mesmo tempo.
    # A memória guarda a preferência confirmada; a pesquisa apenas enriquece
    # a conversa. Nenhuma das duas substitui a resposta humana do turno.
    if not tema_factual and aprendizados_explicitos:
        tema_factual = str(aprendizados_explicitos[0].get('valor') or '').strip()[:160]
    turno['tema_factual'] = tema_factual
    recomendacao_contextual = bool(
        tema_factual
        and extrair_tema_recomendacao_contextual(
            texto_cognitivo,
            registro_semantico,
        ) == tema_factual
    )
    turno['continuidade_recomendacao'] = recomendacao_contextual
    if tema_factual and (not dict(retrato_turno.get('referencia_resolvida') or {}).get('nome')):
        registro_semantico = ns['_atualizar_registro_turno_mente'](registro_semantico, texto, retrato={'entidade_explicita': {'tipo': 'tema', 'nome': tema_factual, 'origem': 'tema_pesquisavel'}}, funcao=funcao_atual, encerramento=encerramento_assunto)
        mente_antes_turno['registro_semantico'] = registro_semantico
    turno_operacional = bool(retrato_turno.get('operacao_explicita')) or str(turno.get('modalidade_geral') or turno.get('modalidade') or '') == 'comando'
    if tema_factual and (not turno_operacional):
        inicio_pesquisa = time.perf_counter()
        pesquisa_runtime = ns['_pesquisa_contextual_runtime']
        modalidade_pesquisa = str(turno.get('modalidade_geral') or turno.get('modalidade') or '').casefold()
        pendencia_factual = dict(mente_antes_turno.get('pendencia_atual') or {})
        continuacao_recomendacao = bool(
            recomendacao_contextual
            or (
                pendencia_factual.get('status') == 'ativa'
                and (
                    str(pendencia_factual.get('dominio') or '').casefold()
                    == 'recomendacao'
                    or str(pendencia_factual.get('tipo') or '').casefold()
                    == 'preferencia_recomendacao'
                )
            )
        )
        pedido_recomendacao = bool(re.search(
            r'\b(?:recomenda|recomende|recomendar|indica|indique|sugere|sugira)\b',
            str(texto_cognitivo or ''),
            flags=re.IGNORECASE,
        ))
        exige_resposta_factual_agora = bool(
            atualidade_factual.get('depende_atualidade')
            or modalidade_pesquisa in {'pergunta', 'misto'}
            or funcao_atual == 'correcao'
            or pedido_recomendacao
            or continuacao_recomendacao
        )
        try:
            if exige_resposta_factual_agora:
                pesquisar_recomendacoes = getattr(
                    pesquisa_runtime,
                    'pesquisar_recomendacoes_tema',
                    None,
                )
                if (
                    (pedido_recomendacao or continuacao_recomendacao)
                    and callable(pesquisar_recomendacoes)
                ):
                    pesquisa_factual = pesquisar_recomendacoes(tema_factual)
                    if not pesquisa_factual.get('ok'):
                        pesquisa_factual = pesquisa_runtime.pesquisar_contexto_tema(
                            tema_factual,
                        )
                else:
                    pesquisa_factual = pesquisa_runtime.pesquisar_contexto_tema(tema_factual)
            else:
                pesquisa_factual = pesquisa_runtime.obter_contexto_cache(tema_factual)
                if not pesquisa_factual:
                    pesquisa_runtime.precarregar_contexto_tema(tema_factual)
                    pesquisa_factual = {
                        'ok': False,
                        'tema': tema_factual,
                        'motivo': 'pesquisa_em_background',
                    }
                    ns['print'](f"🔎 [FUNDAMENTAÇÃO] pesquisa de {tema_factual!r} iniciada em segundo plano.")
        except Exception as erro:
            pesquisa_factual = {'ok': False, 'motivo': f"falha_pesquisa:{type(erro).__name__}"}
        registrar_metrica_opcional(
            ns,
            'pesquisa_factual',
            (time.perf_counter() - inicio_pesquisa) * 1000.0,
            bool(pesquisa_factual.get('ok')),
        )
        fundamentacao_factual = ns['_montar_fundamentacao_mente'](
            tema_factual,
            pesquisa_factual,
            atualidade=atualidade_factual,
        )
        fundamentacao_factual.update({
            'papel_cooperativo': 'enriquecimento_auxiliar',
            'nao_substitui_resposta_principal': True,
            'declaracao_pessoal_explicita': bool(aprendizados_explicitos),
        })
        ns['print'](f"🔎 [FUNDAMENTAÇÃO] tema={tema_factual!r} | confiavel={fundamentacao_factual.get('confiavel')} | fonte={fundamentacao_factual.get('fonte') or '-'} | confianca={float(fundamentacao_factual.get('confianca') or 0.0):.2f}")
    mente_antes_turno['fundamentacao_factual_turno'] = fundamentacao_factual
    turno['retrato_id'] = retrato_turno.get('id')
    turno['entidades'] = dict(retrato_turno.get('entidades') or {})
    turno['referencia_resolvida'] = dict(retrato_turno.get('referencia_resolvida') or {})
    turno['operacao_explicita'] = str(retrato_turno.get('operacao_explicita') or '')
    especialistas = ns['_construir_parecer_especialistas_mente'](texto_cognitivo, turno=turno, funcao_comunicativa=funcao_comunicativa, retrato=retrato_turno, saude=ns['_saude_mente_runtime'].snapshot())
    deliberacao = dict(especialistas.get('deliberacao') or {})
    orquestrador_cooperativo = ns.get('_orquestrador_cooperativo_runtime')
    registrar_consenso = getattr(orquestrador_cooperativo, 'registrar_deliberacao_turno', None)
    if deliberacao and callable(registrar_consenso):
        try:
            publicacao_consenso = dict(registrar_consenso(deliberacao) or {})
        except Exception as erro:
            publicacao_consenso = {
                'publicado': False,
                'motivo': f'falha_publicacao:{type(erro).__name__}',
            }
            ns['print'](
                f"⚠️ [COOPERAÇÃO:CONSENSO] publicação isolada falhou: {type(erro).__name__}"
            )
        deliberacao['quadro_canonico'] = publicacao_consenso
        especialistas['deliberacao'] = deliberacao
    turno['especialistas'] = especialistas
    assunto_estruturado = ns['_atualizar_assunto_estruturado_mente'](mente_antes_turno.get('assunto_estruturado_atual') if isinstance(mente_antes_turno.get('assunto_estruturado_atual'), dict) else {}, texto, turno=turno, retrato=retrato_turno, encerramento=encerramento_assunto)
    plano = ns['_planejar_turno_mente'](texto_cognitivo, turno=turno, mente=mente_antes_turno, periodo=ns['_contexto_horario_atual']())
    # O plano nasce semanticamente da proposta final, mas sua identidade pública
    # pertence à fala original. Não confundir conteúdo operacional com RG do turno.
    plano = alinhar_identidade_plano_revisao(
        plano,
        texto_original=texto,
        texto_operacional_efetivo=texto_efetivo,
        revisao_intra_turno=revisao_intra_turno,
    )
    evento_emocional_causal = criar_evento_leitura_emocional_usuario(
        leitura_emocional_usuario,
        turno_id=str(plano.get('id') or turno.get('id') or time.time_ns()),
    )
    if evento_emocional_causal:
        turno['evento_emocional_causal'] = dict(evento_emocional_causal)
        plano['evento_emocional_causal'] = dict(evento_emocional_causal)
    evidencia_habilidades_getter = ns.get('_evidencia_habilidades_turno_mente')
    if callable(evidencia_habilidades_getter):
        try:
            evidencia_habilidades = evidencia_habilidades_getter(texto_cognitivo, turno=turno)
        except Exception:
            evidencia_habilidades = {}
        if isinstance(evidencia_habilidades, dict):
            plano['evidencia_capacidades'] = dict(evidencia_habilidades)
    plano['fundamentacao_factual'] = fundamentacao_factual
    plano['atualidade_factual'] = atualidade_factual
    plano['deliberacao_habilidades'] = dict(especialistas.get('deliberacao') or {})
    mensagens_recentes = list(
        getattr(ns['_estado_compartilhado_runtime'], 'memoria_conversa', {}).get('messages', [])
        or []
    )
    falas_recentes = [
        str(item.get('content') or '').strip()
        for item in mensagens_recentes
        if isinstance(item, dict) and str(item.get('role') or '').casefold() == 'assistant'
    ][-3:]
    contrato_fala = construir_contrato_semantico_fala(
        texto,
        turno=turno,
        plano=plano,
        funcao_comunicativa=funcao_comunicativa,
        mente=mente_antes_turno,
        falas_recentes=falas_recentes,
    )
    turno['contrato_fala'] = contrato_fala
    plano['contrato_fala'] = contrato_fala
    turno = finalizar_especialista_neural_turno(ns, texto_cognitivo, turno)
    atualizacoes_turno = {'ultima_entrada': str(texto or '').strip()[:500], 'ultima_entrada_ts': ns['time'].time(), 'turno_atual': turno, 'plano_turno_atual': plano, 'contrato_fala_atual': contrato_fala, 'identidade_turno_atual': identidade_turno, 'identidade_turno_resumo': ns['_resumo_identidade_turno_mente'](identidade_turno), 'funcao_comunicativa_atual': funcao_comunicativa, 'retrato_turno_atual': retrato_turno, 'entidades_recentes': entidades_recentes, 'especialistas_turno_atual': especialistas, 'assunto_estruturado_atual': assunto_estruturado, 'registro_semantico': registro_semantico, 'fundamentacao_factual_turno': fundamentacao_factual, **limpeza_pergunta_turno}
    if evento_emocional_causal:
        atualizacoes_turno['eventos_emocionais_causais'] = publicar_evento_emocional_causal(
            mente_antes_turno.get('eventos_emocionais_causais'),
            evento_emocional_causal,
        )
    if leitura_semantica:
        atualizacoes_turno['leitura_semantica_turno'] = leitura_semantica
    if correcao_interpretacao:
        atualizacoes_turno['correcao_interpretacao_pendente'] = correcao_interpretacao
    if encerramento_assunto == 'topico':
        atualizacoes_turno.update(encerramento_assunto_pendente='topico', encerramento_assunto_motivo=str(texto or '').strip()[:300])
    if str(funcao_comunicativa.get('funcao') or '') == 'correcao':
        atualizacoes_turno.update(ultima_correcao_conversacional=str(texto or '').strip()[:500], ultima_correcao_conversacional_ts=ns['time'].time())
    if correcao_duravel:
        chave_correcao = f"{correcao_duravel.get('tipo')}|{correcao_duravel.get('gatilho')}|{correcao_duravel.get('valor')}".casefold()
        if chave_correcao != str(mente_antes_turno.get('ultima_correcao_persistida_chave') or ''):
            try:
                if ns['_persistir_correcao_duravel_mente'](ns['MEMORIA_SQLITE'], correcao_duravel, texto):
                    atualizacoes_turno.update(ultima_correcao_persistida_chave=chave_correcao, ultima_correcao_persistida=correcao_duravel, ultima_correcao_persistida_ts=ns['time'].time())
                    ns['print'](f"🧠 [MEMÓRIA] correção do usuário persistida: {correcao_duravel.get('regra')}")
            except Exception as erro:
                ns['print'](f"⚠️ [MEMÓRIA] não consegui persistir a correção: {erro}")
    ns['_estado_compartilhado_runtime'].atualizar_campos('mental', **atualizacoes_turno)
    ns['print'](f"🧠 [PLANO:TURNO] modalidade={plano.get('modalidade')} | dominio={plano.get('dominio')} | execucao={plano.get('requer_execucao')} | coordenacao={plano.get('modo_coordenacao')} | contexto={plano.get('contexto_necessario')}")
    return turno


def registrar_leitura_semantica_principal(namespace_getter, texto: str, leitura: dict | None) -> dict:
    """Registra a leitura da resposta principal sem alterar sua autorização."""
    ns = namespace_getter()
    semantica = dict(leitura or {})
    if not semantica.get('valida'):
        return {}
    mente = dict(ns['_estado_compartilhado_runtime'].mental)
    turno = dict(mente.get('turno_atual') or {})
    comparacao = comparar_com_legado(semantica, turno)
    semantica.update(
        modo='main',
        comparacao_legado=comparacao,
        somente_observacao=True,
    )
    # Copia apenas para observabilidade/contexto futuro. Campos de decisão,
    # plano e autorização do turno atual permanecem exatamente como estavam.
    turno['leitura_semantica_principal'] = semantica
    plano = dict(mente.get('plano_turno_atual') or {})
    evento = criar_evento_leitura_semantica_usuario(
        semantica,
        turno_id=str(plano.get('id') or turno.get('id') or time.time_ns()),
    )
    campos_semanticos = {
        'turno_atual': turno,
        'leitura_semantica_turno': semantica,
    }
    if evento:
        turno['evento_emocional_causal'] = dict(evento)
        if plano:
            plano['evento_emocional_causal'] = dict(evento)
            campos_semanticos['plano_turno_atual'] = plano
        campos_semanticos['eventos_emocionais_causais'] = (
            publicar_evento_emocional_causal(
                mente.get('eventos_emocionais_causais'),
                evento,
            )
        )
    ns['_estado_compartilhado_runtime'].atualizar_campos(
        'mental',
        **campos_semanticos,
    )
    atos = [str(item.get('tipo') or '') for item in semantica.get('atos') or [] if isinstance(item, dict)]
    ns['print'](
        f"🧠 [SEMÂNTICA:PRINCIPAL] atos={atos or ['-']} | "
        f"modalidade={semantica.get('modalidade_geral') or '-'} | "
        f"confiança={float(semantica.get('confianca') or 0.0):.2f} | "
        f"divergências={comparacao.get('divergencias') or []}"
    )
    return semantica

def atualizar_planejamento_turno(namespace_getter, fase: str, *, comandos=(), erros=(), fala: str='') -> dict:
    ns = namespace_getter()
    atual = dict(ns['_estado_compartilhado_runtime'].mental.get('plano_turno_atual') or {})
    comandos_atuais = list(atual.get('comandos') or [])
    comandos_novos = [dict(item) for item in comandos or () if isinstance(item, dict)]
    comandos_finais = list(comandos_atuais)
    if comandos_novos:
        por_intent = {str(item.get('intent') or item.get('acao') or '').upper(): dict(item) for item in comandos_atuais if str(item.get('intent') or item.get('acao') or '').strip()}
        ordem = list(por_intent)
        for item in comandos_novos:
            chave = str(item.get('intent') or item.get('acao') or '').upper()
            anterior = dict(por_intent.get(chave) or {})
            mesclado = dict(anterior)
            mesclado.update(item)
            for campo in (
                'status', 'executou', 'confirmado',
                'confirmacao_oferecida', 'evidencia_confirmacao',
            ):
                if item.get(campo) in (None, '') and anterior.get(campo) not in (None, ''):
                    mesclado[campo] = anterior[campo]
            por_intent[chave] = mesclado
            if chave not in ordem:
                ordem.append(chave)
        comandos_finais = [por_intent[chave] for chave in ordem]
    novo = ns['_atualizar_plano_turno_mente'](atual, fase=fase, comandos=comandos_finais, erros=erros, fala=fala)
    ns['_estado_compartilhado_runtime'].atualizar_campos('mental', plano_turno_atual=novo)
    trilha = ns['_registrar_etapa_turno_mente'](ns['_estado_compartilhado_runtime'].mental.get('trilha_decisoes_turno') or [], novo, fase=fase)
    ns['_estado_compartilhado_runtime'].atualizar_campos('mental', trilha_decisoes_turno=trilha)
    ns['print'](f"🧠 [PLANO:FASE] fase={novo.get('fase')} | comandos={novo.get('comandos') or []} | erros={novo.get('erros') or []}")
    return novo

def verificar_fala_do_turno(namespace_getter, fala: str, *, origem: str='conversa') -> dict:
    ns = namespace_getter()
    mente = ns['_estado_compartilhado_runtime'].mental
    plano_verificado = dict(mente.get('plano_turno_atual') or {})
    argumentos = {
        'plano': plano_verificado,
        'periodo': ns['_contexto_horario_atual'](),
        'ultima_resposta': str(mente.get('ultima_resposta') or ''),
        'origem': origem,
    }
    verificacao = ns['_verificar_fala_turno_mente'](fala, **argumentos)
    problemas_iniciais = set(verificacao.get('problemas') or [])
    titulos_candidatos = extrair_titulos_citados(fala)
    pesquisa_runtime = ns.get('_pesquisa_contextual_runtime')
    montar_fundamentacao = ns.get('_montar_fundamentacao_mente')
    if (
        'obra_sem_evidencia' in problemas_iniciais
        and titulos_candidatos
        and not list(plano_verificado.get('comandos') or [])
        and callable(getattr(pesquisa_runtime, 'pesquisar_contexto_tema', None))
        and callable(montar_fundamentacao)
    ):
        titulo_candidato = titulos_candidatos[0]
        try:
            pesquisa_candidata = pesquisa_runtime.pesquisar_contexto_tema(
                titulo_candidato,
            )
            fundamentacao_candidata = montar_fundamentacao(
                titulo_candidato,
                pesquisa_candidata,
            )
        except Exception as erro:
            fundamentacao_candidata = {}
            ns['print'](
                '⚠️ [FUNDAMENTAÇÃO] falha ao verificar título candidato | '
                f'tipo={type(erro).__name__}'
            )
        if fundamentacao_candidata.get('confiavel'):
            plano_candidato = dict(plano_verificado)
            plano_candidato['fundamentacao_factual'] = fundamentacao_candidata
            argumentos['plano'] = plano_candidato
            verificacao_candidata = ns['_verificar_fala_turno_mente'](
                fala,
                **argumentos,
            )
            if 'obra_sem_evidencia' not in set(
                verificacao_candidata.get('problemas') or []
            ):
                verificacao = verificacao_candidata
                plano_verificado = plano_candidato
                ns['print'](
                    '🔎 [FUNDAMENTAÇÃO] título candidato confirmado antes da fala | '
                    f'titulo={titulo_candidato!r} '
                    f'fonte={fundamentacao_candidata.get("fonte") or "-"}'
                )
    plano = dict(plano_verificado)
    plano['fase'] = 'fala_verificada'
    plano['ultima_verificacao'] = dict(verificacao)
    avaliacoes = list(mente.get('avaliacoes_turno') or [])
    avaliacoes.append({'plano_id': plano.get('id'), 'origem': str(origem or 'conversa'), 'pontuacao': float(verificacao.get('pontuacao') or 0.0), 'problemas': list(verificacao.get('problemas') or []), 'acao': str(verificacao.get('acao') or ''), 'ts': ns['time'].time()})
    metricas = dict(mente.get('metricas_verificador') or {})
    metricas['falas_verificadas'] = int(metricas.get('falas_verificadas') or 0) + 1
    aderencia_contrato = dict(verificacao.get('aderencia_contrato') or {})
    if aderencia_contrato.get('avaliado'):
        metricas['contratos_verificados'] = int(metricas.get('contratos_verificados') or 0) + 1
        estrategia = str(aderencia_contrato.get('estrategia') or 'resposta_direta')[:64]
        chave_estrategia = f'estrategia:{estrategia}'
        metricas[chave_estrategia] = int(metricas.get(chave_estrategia) or 0) + 1
        if not verificacao.get('aceita', True):
            metricas['contratos_rejeitados'] = int(metricas.get('contratos_rejeitados') or 0) + 1
        else:
            metricas['contratos_aprovados'] = int(metricas.get('contratos_aprovados') or 0) + 1
            if aderencia_contrato.get('problemas'):
                metricas['contratos_com_observacoes'] = int(
                    metricas.get('contratos_com_observacoes') or 0
                ) + 1
    if verificacao.get('problemas'):
        metricas['falas_ajustadas'] = int(metricas.get('falas_ajustadas') or 0) + 1
        for problema in verificacao.get('problemas') or []:
            chave = f'problema:{problema}'
            metricas[chave] = int(metricas.get(chave) or 0) + 1
    ns['_estado_compartilhado_runtime'].atualizar_campos('mental', plano_turno_atual=plano, avaliacoes_turno=avaliacoes[-50:], metricas_verificador=metricas)
    referencia_musical = extrair_referencia_musical_verificada(str(verificacao.get('fala') or ''), plano)
    if referencia_musical:
        agora = ns['time'].time()
        entidades = dict(mente.get('entidades_recentes') or {})
        entidades['musica'] = {'tipo': 'musica', 'nome': referencia_musical, 'origem': 'fala_verificada', 'ts': agora}
        ns['_estado_compartilhado_runtime'].atualizar_campos(
            'mental',
            ultima_musica_mencionada={'titulo': referencia_musical, 'origem': 'fala_verificada', 'ts': agora},
            entidades_recentes=entidades,
        )
    if verificacao.get('problemas'):
        casos = list(mente.get('casos_regressao_candidatos') or [])[-29:]
        casos.append({'origem': 'verificador_fala', 'texto': str(plano.get('texto_usuario') or '')[:500], 'fala': str(verificacao.get('fala') or '')[:500], 'problemas': list(verificacao.get('problemas') or []), 'plano_id': plano.get('id'), 'ts': ns['time'].time()})
        ns['_estado_compartilhado_runtime'].atualizar_campos('mental', casos_regressao_candidatos=casos)
        ns['print'](f"🛡️ [VERIFICADOR:FALA] origem={origem} | acao={verificacao.get('acao')} | problemas={verificacao.get('problemas')}")
    return verificacao
