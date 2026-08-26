"""Execucao de intents de arquivos da Laylay.

Mantem a execucao de CREATE_FOLDER, CREATE_FILE e DELETE_ITEM fora do roteador principal.
O modulo recebe callbacks do contexto vivo para preservar a regra de mente unica.
"""

from __future__ import annotations

import os
import time
from typing import Any, Callable, Dict

from mente_laylay.personalidade.falas_variadas import escolher as _escolher_fala_variada
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao, inferir_confirmacao
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao
from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_llm
from mente_laylay.integracao.registro_arquivos import PortaArquivosLeitura
from mente_laylay.integracao.registro_mutacoes_arquivos import PortaArquivosMutacao
from mente_laylay.autonomia.executor_comum import relatar_falha_ctx


def _get(ctx: Dict[str, Any], nome: str, default=None):
    return ctx.get(nome, default)


def _focar_janela_do_arquivo(
    ctx: Dict[str, Any],
    *,
    caminho: str,
    nome: str,
) -> bool:
    """Traz para frente o aplicativo que acabou de abrir o arquivo.

    ``os.startfile`` (usado pela porta de arquivos) confirma apenas que o
    Windows aceitou a abertura. O aplicativo associado pode levar alguns
    instantes para criar sua janela. Reaproveitamos o gerenciador oficial de
    janelas e procuramos pelo nome do arquivo, nunca pela janela que estava em
    foco antes do pedido.
    """

    focar = _get(ctx, "focar_janela_app")
    if not callable(focar):
        return False

    nome_publicado = str(nome or "").strip().replace("/", os.sep)
    alvo = str(
        os.path.basename(nome_publicado) or os.path.basename(caminho) or ""
    ).strip()
    if not alvo:
        return False
    aguardar = _get(ctx, "_aguardar_foco_arquivo", time.sleep)
    if not callable(aguardar):
        aguardar = time.sleep

    # A primeira tentativa é imediata; as seguintes cobrem o tempo de criação
    # da janela do aplicativo associado sem impor uma espera fixa ao sucesso.
    esperas = (0.0, 0.08, 0.14, 0.22, 0.32, 0.45)
    for espera_s in esperas:
        if espera_s:
            aguardar(espera_s)
        try:
            if bool(focar(alvo)):
                return True
        except Exception as erro:
            relatar_falha_ctx(
                ctx,
                "executor_arquivos",
                "falha_foco_arquivo",
                erro=erro,
                classe="degradacao",
                impacto="comando",
                fallback="arquivo_aberto_sem_foco",
                dominio="arquivos",
                fase="focar_arquivo_aberto",
            )
            return False
    return False


def executar_intencao_arquivos(
    intent: str,
    params: Dict[str, Any],
    destino_val: str,
    ctx: Dict[str, Any],
    *,
    texto_original: str = "",
    marcar_resultado: Callable[[str, bool | None], None],
    registrar_arquivo: Callable[[str, str], None],
    item_local_existe: Callable[[str, str], bool],
    resolver_caminho_local: Callable[[str], str],
    resolver_referencia_arquivo_contextual: Callable[[str, str], str],
    arquivos_leitura: PortaArquivosLeitura | None = None,
    arquivos_mutacao: PortaArquivosMutacao | None = None,
) -> bool:
    falar_original = _get(ctx, "falar_com_lipsync")
    criar_pasta = getattr(arquivos_mutacao, "criar_pasta", None)
    criar_ou_editar_arquivo = getattr(arquivos_mutacao, "criar_arquivo", None)
    escrever_arquivo_texto_seguro = getattr(arquivos_mutacao, "escrever_texto_seguro", None)
    resolver_referencia_cooperativa = _get(ctx, "_resolver_referencia_cooperativa")
    mover_arquivo = getattr(arquivos_mutacao, "mover_item", None)
    resolver_caminho = getattr(arquivos_mutacao, "resolver_caminho", None)
    ultima_pasta_contextual = _get(ctx, "ultima_pasta_contextual")
    registrar_estrutura_arquivo_recente = _get(ctx, "_registrar_estrutura_arquivo_recente")
    _enviar_pc_b = _get(ctx, "_enviar_pc_b")
    marcar_resultado_original = marcar_resultado
    resultado_fala: Dict[str, Any] = {"status": "", "executou": None}
    alvo_planejado = str(
        params.get("alvo") or params.get("nome") or params.get("pasta") or params.get("arquivo") or "arquivo"
    ).strip()

    def _marcar_resultado(
        status: str,
        executou: bool | None,
        *,
        alvo_resolvido: str = "",
        params_resolvidos: Dict[str, Any] | None = None,
        confirmado: bool | None = None,
    ) -> None:
        resultado_fala["status"] = str(status or "")
        resultado_fala["executou"] = executou
        resultado_fala["confirmado"] = confirmado
        if alvo_resolvido:
            resultado_fala["alvo"] = str(alvo_resolvido)
        if isinstance(params_resolvidos, dict):
            resultado_fala["params_resolvidos"] = dict(params_resolvidos)
        kwargs: Dict[str, Any] = {}
        if alvo_resolvido:
            kwargs["alvo_resolvido"] = str(alvo_resolvido)
        if isinstance(params_resolvidos, dict):
            kwargs["params_resolvidos"] = dict(params_resolvidos)
        if confirmado is not None:
            kwargs["confirmado"] = confirmado
        try:
            marcar_resultado_original(status, executou, **kwargs)
        except TypeError:
            marcar_resultado_original(status, executou)

    marcar_resultado = _marcar_resultado

    def falar(texto: str, emocao: str = "calma", nivel: int = 1) -> None:
        if not callable(falar_original):
            return
        status = str(resultado_fala.get("status") or "")
        if not status:
            falar_original(texto, emocao, nivel)
            return
        contrato = ResultadoAcao(
            intent=intent,
            status=status,
            alvo=str(resultado_fala.get("alvo") or alvo_planejado),
            params={
                **params,
                **(
                    dict(resultado_fala.get("params_resolvidos") or {})
                    if isinstance(resultado_fala.get("params_resolvidos"), dict)
                    else {}
                ),
            },
            executou=resultado_fala.get("executou"),
            confirmado=(
                resultado_fala.get("confirmado")
                if resultado_fala.get("confirmado") is not None
                else inferir_confirmacao(status, resultado_fala.get("executou"))
            ),
            texto_usuario=texto_original,
            contexto={"destino": destino_val},
        )
        plano = planejar_resposta_acao(
            contrato,
            texto,
            emocao_preferida=emocao,
            nivel_preferido=nivel,
        )
        modo_jogo = _get(ctx, "modo_jogo_ativo", False)
        try:
            modo_jogo_ativo = bool(modo_jogo() if callable(modo_jogo) else modo_jogo)
        except Exception:
            modo_jogo_ativo = False
        confirmacao = personalizar_confirmacao_llm(
            contrato,
            plano.fala,
            classe=plano.classe,
            emocao=plano.emocao,
            nivel=plano.nivel,
            enviar_mensagem=_get(ctx, "enviar_mensagem"),
            contexto={
                "current_emotion": _get(ctx, "current_emotion", "calma"),
                "modo_jogo_ativo": modo_jogo_ativo,
            },
        )
        resultado_fala["status"] = ""
        resultado_fala["executou"] = None
        resultado_fala["confirmado"] = None
        falar_resultado = _get(ctx, "_falar_resultado_operacional")
        if callable(falar_resultado):
            falar_resultado(
                contrato,
                confirmacao.fala,
                confirmacao.emocao,
                confirmacao.nivel,
            )
        else:
            falar_original(confirmacao.fala, confirmacao.emocao, confirmacao.nivel)

    if intent == "FILE_READ":
        ler_texto = getattr(arquivos_leitura, "ler_texto", None)
        caminho = str(params.get("caminho") or "").strip()
        nome = str(
            params.get("alvo") or os.path.basename(caminho) or "arquivo"
        ).strip()
        if not caminho or not callable(ler_texto):
            marcar_resultado("indisponivel", False, confirmado=False)
            falar("A leitura desse arquivo não está disponível agora.", "calma", 1)
            return True
        try:
            leitura = dict(ler_texto(caminho, limite=4000) or {})
        except Exception as erro:
            relatar_falha_ctx(
                ctx,
                "executor_arquivos",
                "falha_leitura_texto",
                erro=erro,
                impacto="comando",
                fallback="falha_leitura",
                dominio="arquivos",
                fase="ler_texto",
            )
            leitura = {"ok": False, "status": "falha_leitura"}
        if leitura.get("ok") is not True:
            status = str(leitura.get("status") or "falha_leitura")
            marcar_resultado(status, False, confirmado=False)
            mensagens = {
                "arquivo_sensivel": "Não vou ler esse arquivo em voz alta porque ele parece conter credenciais.",
                "formato_nao_textual": "Esse arquivo não é texto legível por esta rota.",
                "arquivo_muito_grande": "Esse arquivo é grande demais para eu ler inteiro com segurança.",
                "arquivo_indisponivel": "Esse arquivo não está mais disponível nesse caminho.",
            }
            falar(mensagens.get(status, "Não consegui ler esse arquivo agora."), "calma", 1)
            return True
        conteudo = str(leitura.get("conteudo") or "").strip()
        truncado = leitura.get("truncado") is True
        marcar_resultado(
            "conteudo_lido",
            True,
            alvo_resolvido=caminho,
            confirmado=True,
        )
        registrar_arquivo(caminho, "arquivos")
        if callable(registrar_estrutura_arquivo_recente):
            registrar_estrutura_arquivo_recente({
                "tipo": "arquivo",
                "arquivo_nome": nome,
                "caminho": caminho,
                "target": destino_val,
            })
        if not conteudo:
            falar(f"{nome} está vazio.", "calma", 1)
        else:
            sufixo = " Parei no limite seguro de leitura." if truncado else ""
            falar(f"O conteúdo de {nome} é: {conteudo}{sufixo}", "calma", 1)
        return True

    if intent == "FILE_SEARCH":
        pesquisar = getattr(arquivos_leitura, "pesquisar", None)
        referencia_caminho = str(params.get("referencia_caminho") or "").strip()
        if referencia_caminho:
            confirmado = os.path.isfile(referencia_caminho)
            marcar_resultado("caminho_encontrado" if confirmado else "resultado_expirado", confirmado)
            if confirmado:
                registrar_arquivo(referencia_caminho, "arquivos")
                falar(
                    f"O arquivo fica em {referencia_caminho}.",
                    "calma", 1,
                )
            else:
                falar("Esse resultado não está mais disponível nesse caminho.", "calma", 1)
            return True
        consulta = str(params.get("query") or params.get("tema") or params.get("alvo") or "").strip()
        if not consulta:
            marcar_resultado("consulta_vazia", False)
            falar("O que você quer que eu procure nos seus arquivos?", "calma", 1)
            return True
        if not callable(pesquisar):
            marcar_resultado("indisponivel", False)
            falar("A pesquisa nos arquivos não está disponível agora.", "calma", 1)
            return True
        try:
            pesquisa = dict(pesquisar(
                consulta,
                limite=int(params.get("limite") or 5),
                forcar_indice=bool(params.get("forcar_indice")),
                somente_projeto=bool(params.get("somente_projeto")),
            ) or {})
        except Exception as erro:
            relatar_falha_ctx(
                ctx,
                "executor_arquivos",
                "falha_pesquisa",
                erro=erro,
                impacto="comando",
                fallback="resultado_falha_execucao",
                dominio="arquivos",
                fase="pesquisar",
            )
            log = _get(ctx, "print") or _get(ctx, "log")
            if callable(log):
                log(f"⚠️ [ARQUIVOS:PESQUISA] falha isolada: {type(erro).__name__}")
            pesquisa = {"ok": False, "status": "falha_execucao", "resultados": []}
        resultados_brutos = [
            dict(item)
            for item in list(pesquisa.get("resultados") or [])
            if isinstance(item, dict)
        ]
        resultados = []
        caminhos_vistos: set[str] = set()
        for item in resultados_brutos:
            caminho_item = str(item.get("caminho") or "").strip()
            if caminho_item:
                chave = os.path.normcase(os.path.abspath(caminho_item))
            else:
                chave = f"nome:{str(item.get('nome') or '').strip().casefold()}"
            if chave in caminhos_vistos:
                continue
            caminhos_vistos.add(chave)
            resultados.append(item)
        if not pesquisa.get("ok"):
            marcar_resultado(str(pesquisa.get("status") or "falha_execucao"), False)
            falar("Não consegui concluir essa busca nos arquivos agora.", "calma", 1)
            return True
        if not resultados:
            marcar_resultado("sem_resultados", True)
            falar(f"Procurei por {consulta}, mas não encontrei um arquivo relacionado.", "calma", 1)
            return True
        caminhos = [str(item.get("caminho") or "") for item in resultados if item.get("caminho")]
        nomes = [str(item.get("nome") or os.path.basename(str(item.get("caminho") or ""))) for item in resultados]
        if params.get("abrir_resultado_exato"):
            consulta_nome = os.path.basename(consulta.replace("/", os.sep)).casefold()

            def nome_equivalente(nome: str) -> bool:
                candidato = os.path.basename(str(nome or "").replace("/", os.sep)).casefold()
                if candidato == consulta_nome:
                    return True
                raiz_consulta, ext_consulta = os.path.splitext(consulta_nome)
                raiz_candidato, ext_candidato = os.path.splitext(candidato)
                return bool(
                    raiz_consulta == raiz_candidato
                    and {ext_consulta, ext_candidato} == {"", ".txt"}
                )

            exatos = [
                (caminho, nome)
                for caminho, nome in zip(caminhos, nomes)
                if caminho and nome_equivalente(nome or caminho)
            ]
            if len(exatos) == 1:
                caminho_exato, nome_exato = exatos[0]
                return executar_intencao_arquivos(
                    "FILE_OPEN_RESULT",
                    {
                        "caminho": caminho_exato,
                        "alvo": nome_exato,
                        **(
                            {"modo": "focus", "referencia_contextual": True}
                            if str(params.get("modo") or "").casefold() == "focus"
                            else {}
                        ),
                    },
                    destino_val,
                    ctx,
                    texto_original=texto_original,
                    marcar_resultado=marcar_resultado_original,
                    registrar_arquivo=registrar_arquivo,
                    item_local_existe=item_local_existe,
                    resolver_caminho_local=resolver_caminho_local,
                    resolver_referencia_arquivo_contextual=(
                        resolver_referencia_arquivo_contextual
                    ),
                    arquivos_leitura=arquivos_leitura,
                    arquivos_mutacao=arquivos_mutacao,
                )
        if callable(registrar_estrutura_arquivo_recente):
            registrar_estrutura_arquivo_recente({
                "tipo": "pesquisa_semantica",
                "consulta": consulta[:240],
                "resultados": caminhos[:5],
                "nomes": nomes[:5],
                "somente_projeto": bool(params.get("somente_projeto")),
            })
        registrar_arquivo(caminhos[0], "arquivos")
        aprender = _get(ctx, "_aprender_pesquisa_semantica_arquivos")
        if callable(aprender):
            try:
                aprender(consulta, resultados)
            except Exception as erro:
                relatar_falha_ctx(
                    ctx,
                    "executor_arquivos",
                    "falha_aprendizado_pesquisa",
                    erro=erro,
                    classe="degradacao",
                    impacto="servico",
                    fallback="pesquisa_sem_aprendizado",
                    dominio="arquivos",
                    fase="pos_pesquisa",
                )
        marcar_resultado("arquivos_encontrados", True)
        if len(resultados) == 1:
            motivos = ", ".join(resultados[0].get("motivos") or [])
            complemento = f" Ele apareceu por {motivos}." if motivos else ""
            falar(f"Encontrei {nomes[0]}.{complemento}", "feliz", 1)
        else:
            lista = "; ".join(f"{indice + 1}: {nome}" for indice, nome in enumerate(nomes[:3]))
            restante = len(resultados) - 3
            sufixo = f" E mais {restante}." if restante > 0 else ""
            falar(
                f"Encontrei {len(resultados)} arquivos relacionados: {lista}.{sufixo} "
                "Você pode pedir para abrir o primeiro, o segundo ou o terceiro.",
                "feliz", 1,
            )
        return True

    if intent == "FILE_OPEN_RESULT":
        abrir = getattr(arquivos_leitura, "abrir", None)
        caminho = str(params.get("caminho") or "").strip()
        nome_publicado = str(params.get("alvo") or "").strip().replace("/", os.sep)
        nome = str(
            os.path.basename(nome_publicado)
            or os.path.basename(caminho)
            or "arquivo"
        ).strip()
        sucesso = bool(abrir(caminho)) if callable(abrir) and caminho else False
        if sucesso:
            registrar_arquivo(caminho, "arquivos")
            if callable(registrar_estrutura_arquivo_recente):
                registrar_estrutura_arquivo_recente({
                    "tipo": "arquivo",
                    "arquivo_nome": nome,
                    "caminho": caminho,
                    "target": destino_val,
                })
            pediu_foco = str(params.get("modo") or "").strip().casefold() == "focus"
            if pediu_foco:
                foco_confirmado = _focar_janela_do_arquivo(
                    ctx,
                    caminho=caminho,
                    nome=nome,
                )
                if foco_confirmado:
                    marcar_resultado(
                        "arquivo_aberto_focado",
                        True,
                        alvo_resolvido=caminho,
                        confirmado=True,
                    )
                    falar(f"Abri {nome} e deixei a janela na frente.", "feliz", 1)
                else:
                    marcar_resultado(
                        "arquivo_aberto_sem_foco",
                        True,
                        alvo_resolvido=caminho,
                        confirmado=False,
                    )
                    falar(
                        f"Abri {nome}, mas não consegui confirmar a janela na frente.",
                        "calma",
                        1,
                    )
            else:
                marcar_resultado(
                    "arquivo_aberto",
                    True,
                    alvo_resolvido=caminho,
                    params_resolvidos={"caminho": caminho, "alvo": nome},
                    confirmado=True,
                )
                falar(f"Abri {nome} para você.", "feliz", 1)
        else:
            marcar_resultado("falha_abertura", False)
            falar(f"Encontrei {nome}, mas não consegui abri-lo agora.", "calma", 1)
        return True

    if intent == "FILE_TRANSACTION":
        transacionar = getattr(arquivos_mutacao, "transacionar", None)
        if not callable(transacionar):
            marcar_resultado("indisponivel", False)
            falar("As alterações de arquivos não estão disponíveis agora.", "calma", 1)
            return True
        params_transacao = dict(params or {})
        operacao = str(params_transacao.get("operacao") or "").strip().casefold()
        if operacao == "mover":
            origem = resolver_referencia_arquivo_contextual(
                str(params_transacao.get("origem") or ""), "arquivo",
            )
            destino = resolver_referencia_arquivo_contextual(
                str(params_transacao.get("destino") or ""), "pasta",
            )
            params_transacao["origem"] = resolver_caminho_local(origem)
            params_transacao["destino"] = resolver_caminho_local(destino)
        resultado = transacionar(params_transacao)
        marcar_resultado(
            resultado.status if resultado.sucesso else str(resultado.status or "falha_execucao"),
            resultado.sucesso,
            alvo_resolvido=str(resultado.destino or resultado.origem or ""),
            params_resolvidos=params_transacao,
            confirmado=bool(resultado.sucesso),
        )
        if resultado.sucesso:
            registrar_arquivo(resultado.destino or resultado.origem, "arquivos")
            if callable(registrar_estrutura_arquivo_recente):
                caminho_atual = str(resultado.destino or resultado.origem or "")
                registrar_estrutura_arquivo_recente({
                    "tipo": "pasta" if os.path.isdir(caminho_atual) else "arquivo",
                    "caminho": caminho_atual,
                    "arquivo_nome": (
                        os.path.basename(caminho_atual)
                        if not os.path.isdir(caminho_atual) else ""
                    ),
                    "nome": (
                        os.path.basename(caminho_atual)
                        if os.path.isdir(caminho_atual) else ""
                    ),
                    "target": destino_val,
                })
        if callable(falar):
            if resultado.sucesso:
                falas = {
                    "movido": (
                        f"Coloquei {os.path.basename(resultado.destino)} dentro de "
                        f"{os.path.dirname(resultado.destino)} e conferi o resultado."
                    ),
                    "renomeado": f"Corrigi o nome e confirmei: agora é {os.path.basename(resultado.destino)}.",
                    "ja_com_mesmo_nome": (
                        f"{os.path.basename(resultado.origem)} já está com esse nome e tipo. "
                        "Não precisei alterar nada."
                    ),
                    "conteudo_atualizado": f"Corrigi o conteúdo de {os.path.basename(resultado.origem)} e conferi o arquivo.",
                }
                falar(falas.get(resultado.status, "Corrigi o arquivo e confirmei o resultado."), "calma", 1)
            else:
                origem_nome = os.path.basename(
                    str(resultado.origem or params_transacao.get("origem") or "arquivo")
                )
                destino_nome = os.path.basename(
                    str(resultado.destino or params_transacao.get("destino") or "pasta")
                )
                falas_falha = {
                    "origem_nao_encontrada": (
                        f"Não encontrei {origem_nome}, então não movi nada."
                    ),
                    "destino_nao_encontrado": (
                        f"Não encontrei a pasta {destino_nome}, então não movi nada."
                    ),
                    "destino_ja_existe": (
                        f"Já existe um item chamado {origem_nome} em {destino_nome}; "
                        "não sobrescrevi nada."
                    ),
                    "destino_bloqueado": (
                        f"Não movi {origem_nome}: esse destino está protegido."
                    ),
                    "validacao_falhou": (
                        f"Tentei mover {origem_nome}, mas a conferência final falhou."
                    ),
                }
                falar(
                    falas_falha.get(
                        str(resultado.status or ""),
                        f"Não consegui mover {origem_nome}; nada foi confirmado.",
                    ),
                    "calma",
                    1,
                )
        return True

    if intent == "CANCEL_DELETE_ITEM":
        cancelar = getattr(arquivos_mutacao, "cancelar_exclusao", None)
        if not callable(cancelar):
            marcar_resultado("indisponivel", False)
            falar("A lixeira da Laylay não está disponível agora.", "calma", 1)
            return True
        cancelar()
        # Cancelar é uma não ação deliberada: nada foi apagado, mas o estado
        # pedido pelo usuário foi confirmado. Sem esse terceiro campo o
        # roteiro classificava a recusa segura como falha operacional.
        marcar_resultado("exclusao_cancelada", False, confirmado=True)
        if callable(falar):
            falar("Certo, cancelei a exclusão. Não mexi em nada.", "calma", 1)
        return True

    if intent == "CONFIRM_DELETE_ITEM":
        confirmar = getattr(arquivos_mutacao, "confirmar_exclusao", None)
        if not callable(confirmar):
            marcar_resultado("indisponivel", False)
            falar("A lixeira da Laylay não está disponível agora.", "calma", 1)
            return True
        resultado = confirmar()
        marcar_resultado(
            resultado.status,
            resultado.sucesso,
            alvo_resolvido=str(resultado.caminho or ""),
            params_resolvidos={"alvo": str(resultado.caminho or "")},
            confirmado=bool(resultado.sucesso),
        )
        if callable(falar):
            if resultado.sucesso:
                falar(
                    f"Confirmado. Enviei {resultado.caminho} para a lixeira. "
                    "Ainda dá para desfazer.",
                    "calma",
                    1,
                )
            else:
                falar("A confirmação expirou ou não havia exclusão esperando.", "calma", 1)
        return True

    if intent == "RESTORE_DELETED_ITEM":
        restaurar = getattr(arquivos_mutacao, "restaurar_ultimo", None)
        if not callable(restaurar):
            marcar_resultado("indisponivel", False)
            falar("A restauração de arquivos não está disponível agora.", "calma", 1)
            return True
        alvo_exclusao = str(params.get("alvo") or "").strip()
        referencia_confirmada = params.get("referencia_exclusao_confirmada") is True
        if not alvo_exclusao or not referencia_confirmada:
            marcar_resultado(
                "referencia_exclusao_ausente",
                False,
                confirmado=False,
            )
            falar(
                "Não encontrei uma exclusão confirmada recente para restaurar.",
                "calma",
                1,
            )
            return True
        resultado = restaurar(alvo_exclusao)
        marcar_resultado(
            resultado.status,
            resultado.sucesso,
            alvo_resolvido=str(resultado.caminho or alvo_exclusao),
            params_resolvidos={"alvo": alvo_exclusao},
            confirmado=bool(resultado.sucesso),
        )
        if callable(falar):
            if resultado.sucesso:
                falar(f"Desfeito. Restaurei {resultado.caminho}.", "calma", 1)
            elif resultado.status == "destino_ja_existe":
                falar(f"Não restaurei porque já existe outro item em {resultado.caminho}.", "calma", 1)
            else:
                falar("Não encontrei uma exclusão recente que eu pudesse desfazer.", "calma", 1)
        return True

    if intent == "CREATE_FOLDER":
        nome = str(params.get("nome") or params.get("pasta") or params.get("alvo") or "").strip()
        pasta_pai = str(params.get("pasta_pai") or params.get("parent") or "").strip()
        pasta_interna = str(params.get("pasta_interna") or params.get("subpasta") or "").strip()
        mover_item = str(params.get("mover_item") or params.get("mover_pasta") or params.get("item_para_mover") or "").strip()
        arquivo_nome = str(params.get("arquivo_nome") or params.get("nome_arquivo") or params.get("arquivo") or "").strip()
        arquivo_conteudo = str(params.get("arquivo_conteudo") or params.get("conteudo") or params.get("texto") or "").strip()

        def registrar_contexto_criado(caminho_criado: str = "") -> None:
            if not callable(registrar_estrutura_arquivo_recente):
                return
            try:
                dados_contexto = {
                    "nome": nome,
                    "pasta_pai": pasta_pai,
                    "pasta_interna": pasta_interna,
                    "mover_item": mover_item,
                    "arquivo_nome": arquivo_nome,
                    "arquivo_conteudo": arquivo_conteudo,
                    "target": destino_val,
                    "tipo": "pasta",
                }
                if caminho_criado:
                    dados_contexto["caminho"] = caminho_criado
                registrar_estrutura_arquivo_recente(dados_contexto)
            except Exception as erro:
                relatar_falha_ctx(
                    ctx,
                    "executor_arquivos",
                    "falha_registro_contexto_pasta",
                    erro=erro,
                    classe="degradacao",
                    impacto="servico",
                    fallback="pasta_criada_sem_contexto",
                    dominio="arquivos",
                    fase="pos_criacao",
                )
        if pasta_pai.lower() in {"ela", "nela", "essa", "essa pasta", "dela", "dentro dela"} and callable(ultima_pasta_contextual):
            pasta_pai = str(ultima_pasta_contextual() or "").strip()
        if not nome:
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Criar qual pasta? Me dá o nome.",
                    "Qual pasta você quer criar?",
                    "Me fala o nome da pasta.",
                ]), "calma", 1)
            return True
        pasta_ok = False
        if destino_val == "pc_b" and callable(_enviar_pc_b):
            alvo_pc_b = os.path.join(pasta_pai, nome) if pasta_pai else nome
            _enviar_pc_b({"action": "criar_pasta", "alvo": alvo_pc_b})
            pasta_ok = True
            marcar_resultado("pasta_criada_pc_b", True)
            registrar_contexto_criado()
            if callable(falar) and not (pasta_interna or mover_item or arquivo_nome):
                falar(_escolher_fala_variada([f"Pasta {nome} criada no PC B.", f"Criei {nome} no PC B.", f"PC B recebeu a pasta {nome}."]), "calma", 1)
        else:
            nome_resolvido = os.path.join(resolver_caminho(pasta_pai), nome) if pasta_pai and callable(resolver_caminho) else (os.path.join(pasta_pai, nome) if pasta_pai else nome)
            sucesso = bool(criar_pasta(nome_resolvido)) if callable(criar_pasta) else False
            if sucesso:
                sucesso = item_local_existe(nome_resolvido, "pasta")
            pasta_ok = bool(sucesso)
            if sucesso:
                registrar_arquivo(nome_resolvido, "pasta")
                marcar_resultado("pasta_criada", True)
                caminho_criado = resolver_caminho_local(nome_resolvido)
                registrar_contexto_criado(caminho_criado)
            else:
                marcar_resultado("falha_execucao", False)
            # Em um pedido composto, o componente interno confirma o resultado
            # completo. Se a pasta falhar, a falha ainda precisa ser dita aqui.
            if callable(falar) and (not sucesso or not (pasta_interna or mover_item or arquivo_nome)):
                falar(
                    _escolher_fala_variada([f"Pasta {nome} criada.", f"Criei a pasta {nome}.", f"Beleza, pasta {nome} pronta."])
                    if sucesso
                    else _escolher_fala_variada([f"Não consegui criar a pasta {nome}.", f"A pasta {nome} não quis nascer.", f"Deu ruim criando {nome}."]),
                    "calma" if sucesso else "irritada",
                    1 if sucesso else 2,
                )
        if pasta_ok and pasta_interna and callable(criar_pasta) and not destino_val == "pc_b":
            base_principal = os.path.join(pasta_pai, nome) if pasta_pai else nome
            caminho_interno = os.path.join(resolver_caminho(base_principal), pasta_interna) if callable(resolver_caminho) else os.path.join(base_principal, pasta_interna)
            interna_ok = bool(criar_pasta(caminho_interno))
            if interna_ok:
                interna_ok = item_local_existe(caminho_interno, "pasta")
            if interna_ok:
                registrar_arquivo(caminho_interno, "arquivos")
                marcar_resultado("subpasta_criada", True)
            else:
                marcar_resultado("falha_execucao", False)
            if callable(falar):
                falar(
                    _escolher_fala_variada([
                        f"Também encaixei a pasta {pasta_interna} dentro de {nome}.",
                        f"Pronto, {pasta_interna} já está dentro de {nome}.",
                        f"Organizei {pasta_interna} lá dentro de {nome}.",
                    ]) if interna_ok else _escolher_fala_variada([
                        f"Criei {nome}, mas a pasta {pasta_interna} lá dentro não foi.",
                        f"{nome} nasceu, mas a subpasta {pasta_interna} resistiu.",
                        f"Deu certo com {nome}, mas a interna {pasta_interna} emperrou.",
                    ]),
                    "calma" if interna_ok else "irritada",
                    1 if interna_ok else 2,
                )
        if pasta_ok and mover_item and callable(mover_arquivo) and not destino_val == "pc_b":
            pasta_alvo = os.path.join(pasta_pai, nome) if pasta_pai else nome
            pasta_base = resolver_caminho(pasta_alvo) if callable(resolver_caminho) else pasta_alvo
            mover_ok = bool(mover_arquivo(mover_item, pasta_base))
            if mover_ok:
                destino_movido = os.path.join(pasta_base, os.path.basename(str(mover_item).strip("/\\ ")))
                mover_ok = item_local_existe(destino_movido, "")
                if mover_ok:
                    registrar_arquivo(destino_movido, "arquivos")
                    marcar_resultado("item_movido_para_pasta", True)
                else:
                    marcar_resultado("falha_execucao", False)
            if callable(falar):
                falar(
                    _escolher_fala_variada([
                        f"Também coloquei {mover_item} dentro de {nome}.",
                        f"Pronto, {mover_item} foi pra dentro de {nome}.",
                        f"Encaixei {mover_item} lá dentro de {nome}.",
                    ]) if mover_ok else _escolher_fala_variada([
                        f"Criei {nome}, mas não consegui mover {mover_item} pra dentro.",
                        f"{nome} ficou pronta, mas {mover_item} não quis entrar nela.",
                        f"Consegui criar {nome}, mas a mudança de {mover_item} falhou.",
                    ]),
                    "calma" if mover_ok else "irritada",
                    1 if mover_ok else 2,
                )
        if pasta_ok and arquivo_nome and callable(criar_ou_editar_arquivo) and not destino_val == "pc_b":
            pasta_alvo = os.path.join(pasta_pai, nome) if pasta_pai else nome
            pasta_base = resolver_caminho(pasta_alvo) if callable(resolver_caminho) else pasta_alvo
            arquivo_limpo = arquivo_nome.strip().strip("/\\")
            if not arquivo_limpo.lower().endswith(".txt"):
                arquivo_limpo = f"{arquivo_limpo}.txt"
            caminho_arquivo = os.path.join(pasta_base, arquivo_limpo)
            arquivo_ok = bool(criar_ou_editar_arquivo(caminho_arquivo, arquivo_conteudo or "", "w"))
            if arquivo_ok:
                arquivo_ok = item_local_existe(caminho_arquivo, "arquivo")
                if arquivo_ok:
                    registrar_arquivo(caminho_arquivo, "arquivos")
                    marcar_resultado("arquivo_criado", True)
                else:
                    marcar_resultado("falha_execucao", False)
            if callable(falar):
                falar(
                    _escolher_fala_variada([
                        f"Criei a pasta {nome} e o arquivo {arquivo_limpo} dentro dela.",
                        f"Pronto: a pasta {nome} e o arquivo {arquivo_limpo} já estão criados.",
                        f"Tudo certo: criei {nome} com {arquivo_limpo} lá dentro.",
                    ]) if arquivo_ok else _escolher_fala_variada([
                        f"Criei {nome}, mas o arquivo {arquivo_limpo} não saiu direito.",
                        f"A pasta {nome} foi, mas o arquivo {arquivo_limpo} emperrou.",
                        f"{nome} nasceu, mas {arquivo_limpo} não quis aparecer lá dentro.",
                    ]),
                    "calma" if arquivo_ok else "irritada",
                    1 if arquivo_ok else 2,
                )
        if pasta_ok and arquivo_nome and destino_val == "pc_b":
            if callable(falar):
                falar(_escolher_fala_variada([
                    f"A pasta {nome} foi criada no PC B, mas o arquivo interno eu ainda não envio por lá.",
                    f"Criei a pasta {nome} no PC B. O arquivo interno fica para o PC local.",
                    f"Pasta pronta no PC B. O arquivo interno ainda é meu lado local.",
                ]), "calma", 1)
        return True

    if intent == "CREATE_FILE":
        alvo = str(
            params.get("alvo")
            or params.get("nome")
            or params.get("nome_arquivo")
            or params.get("arquivo_nome")
            or params.get("arquivo")
            or ""
        ).strip()
        pasta = str(
            params.get("pasta")
            or params.get("pasta_pai")
            or params.get("diretorio")
            or params.get("diretório")
            or ""
        ).strip()
        if pasta.casefold() in {
            "dela", "dele", "nela", "nele", "essa", "esse",
            "essa pasta", "aquela pasta", "a pasta",
        }:
            marcar_resultado("referencia_nao_resolvida", False)
            if callable(falar):
                falar("Eu entendi que é dentro de uma pasta anterior, mas perdi qual era. Me diz o nome dela.", "calma", 1)
            return True
        tipo_arquivo = str(params.get("tipo_arquivo") or params.get("tipo") or "").strip().casefold()
        conteudo_ref = str(params.get("conteudo_ref") or "").strip()
        conteudo_hash = str(params.get("conteudo_hash") or "").strip()
        sobrescrever_confirmado = params.get("sobrescrever_confirmado") is True
        editar_existente = params.get("editar_existente") is True
        modo_escrita = str(params.get("modo_escrita") or "overwrite").strip().casefold()
        conteudo = str(params.get("conteudo") or params.get("texto") or "")
        if conteudo_ref:
            if not callable(resolver_referencia_cooperativa):
                marcar_resultado("referencia_indisponivel", False)
                if callable(falar):
                    falar("A referência temporária ao texto não está disponível. Não criei o arquivo.", "calma", 1)
                return True
            try:
                referencia = dict(resolver_referencia_cooperativa(
                    conteudo_ref, hash_esperado=conteudo_hash,
                ) or {})
            except Exception as erro:
                relatar_falha_ctx(
                    ctx,
                    "executor_arquivos",
                    "falha_referencia_cooperativa",
                    erro=erro,
                    impacto="comando",
                    fallback="referencia_indisponivel",
                    dominio="arquivos",
                    fase="resolver_referencia",
                )
                referencia = {"ok": False, "status": "referencia_indisponivel"}
            if not referencia.get("ok"):
                marcar_resultado(str(referencia.get("status") or "referencia_expirada"), False)
                if callable(falar):
                    falar("A referência temporária ao texto expirou. Copie novamente antes de criar o arquivo.", "calma", 1)
                return True
            conteudo = str(referencia.get("conteudo") or "")
            if conteudo_hash and str(referencia.get("hash") or "") != conteudo_hash:
                marcar_resultado("referencia_divergente", False)
                if callable(falar):
                    falar("O conteúdo temporário mudou. Por segurança, não criei o arquivo.", "calma", 1)
                return True
        if not alvo:
            marcar_resultado("alvo_ausente", False)
            if callable(falar):
                falar("Qual arquivo você quer criar?", "calma", 1)
            return True
        if destino_val == "pc_b":
            if callable(falar):
                falar("Ainda não envio arquivo de texto direto para o PC B.", "calma", 1)
            marcar_resultado("arquivo_pc_b_nao_suportado", False)
            return True
        arquivo_limpo = alvo.strip().strip("/\\")
        if tipo_arquivo in {"texto", "txt", "arquivo de texto"} and not arquivo_limpo.lower().endswith(".txt"):
            arquivo_limpo = f"{arquivo_limpo}.txt"
        if pasta:
            pasta_base = resolver_caminho_local(pasta)
            caminho = os.path.join(pasta_base, arquivo_limpo)
        else:
            caminho = resolver_caminho_local(arquivo_limpo)
        if editar_existente and not item_local_existe(caminho, "arquivo"):
            marcar_resultado(
                "arquivo_nao_encontrado",
                False,
                alvo_resolvido=caminho,
                params_resolvidos={"alvo": caminho, "caminho": caminho},
                confirmado=False,
            )
            if callable(falar):
                falar(
                    f"Não encontrei {os.path.basename(caminho) or arquivo_limpo} para escrever nele.",
                    "calma",
                    1,
                )
            return True
        resultado_seguro = {}
        if conteudo_ref:
            if callable(escrever_arquivo_texto_seguro):
                resultado_seguro = dict(escrever_arquivo_texto_seguro(
                    caminho, conteudo, sobrescrever=sobrescrever_confirmado,
                ) or {})
            sucesso = bool(
                resultado_seguro.get("ok")
                and resultado_seguro.get("confirmado") is True
                and (not conteudo_hash or resultado_seguro.get("hash") == conteudo_hash)
            )
        elif editar_existente and modo_escrita == "append":
            try:
                with open(caminho, "r", encoding="utf-8") as stream:
                    conteudo_anterior = stream.read()
            except (OSError, UnicodeError) as erro:
                relatar_falha_ctx(
                    ctx,
                    "executor_arquivos",
                    "falha_leitura_antes_append",
                    erro=erro,
                    impacto="comando",
                    fallback="append_cancelado_sem_alteracao",
                    dominio="arquivos",
                    fase="pre_append",
                )
                conteudo_anterior = ""
                sucesso = False
                resultado_seguro = {"status": "falha_leitura_arquivo"}
            else:
                separador = "" if not conteudo_anterior or conteudo_anterior.endswith("\n") else "\n"
                trecho_append = f"{separador}{conteudo}"
                sucesso = bool(
                    criar_ou_editar_arquivo(caminho, trecho_append, "a")
                ) if callable(criar_ou_editar_arquivo) else False
                if sucesso:
                    try:
                        with open(caminho, "r", encoding="utf-8") as stream:
                            relido = stream.read()
                        sucesso = relido == f"{conteudo_anterior}{trecho_append}"
                    except (OSError, UnicodeError):
                        sucesso = False
                resultado_seguro = {
                    "status": "conteudo_acrescentado" if sucesso else "conteudo_nao_confirmado",
                }
        else:
            sucesso = bool(criar_ou_editar_arquivo(caminho, conteudo, "w")) if callable(criar_ou_editar_arquivo) else False
            if sucesso:
                sucesso = item_local_existe(caminho, "arquivo")
        if sucesso:
            registrar_arquivo(caminho, "arquivo")
            nome_arquivo = os.path.basename(caminho) or os.path.basename(arquivo_limpo)
            if callable(registrar_estrutura_arquivo_recente):
                try:
                    registrar_estrutura_arquivo_recente({
                        "arquivo_nome": nome_arquivo,
                        "caminho": caminho,
                        "pasta": pasta,
                        "tipo": "arquivo",
                        "tipo_arquivo": tipo_arquivo,
                        "target": destino_val,
                    })
                except Exception as erro:
                    relatar_falha_ctx(
                        ctx,
                        "executor_arquivos",
                        "falha_registro_contexto_arquivo",
                        erro=erro,
                        classe="degradacao",
                        impacto="servico",
                        fallback="arquivo_criado_sem_contexto",
                        dominio="arquivos",
                        fase="pos_criacao",
                    )
            status_sucesso = (
                "conteudo_acrescentado"
                if editar_existente and modo_escrita == "append"
                else "conteudo_atualizado"
                if editar_existente
                else "arquivo_criado"
            )
            marcar_resultado(
                status_sucesso,
                True,
                alvo_resolvido=caminho,
                params_resolvidos={
                    "alvo": caminho,
                    "caminho": caminho,
                    "nome_arquivo": nome_arquivo,
                    "tipo": "arquivo",
                },
                confirmado=True,
            )
        else:
            marcar_resultado(
                str(resultado_seguro.get("status") or "falha_execucao"), False,
            )
        if callable(falar):
            falar(
                (
                    f"Acrescentei o texto em {os.path.basename(caminho) or arquivo_limpo} e conferi o arquivo."
                    if editar_existente and modo_escrita == "append" and sucesso
                    else f"Escrevi o texto em {os.path.basename(caminho) or arquivo_limpo} e conferi o arquivo."
                    if editar_existente and sucesso
                    else _escolher_fala_variada([
                    f"Criei {arquivo_limpo} dentro de {pasta}.",
                    f"Pronto, {arquivo_limpo} já está em {pasta}.",
                ] if pasta else [
                    f"Arquivo {arquivo_limpo} criado.",
                    f"Pronto, {arquivo_limpo} já existe.",
                    f"Criei {arquivo_limpo}.",
                ]) if sucesso else _escolher_fala_variada([
                    f"Não consegui criar {arquivo_limpo}.",
                    f"O arquivo {arquivo_limpo} não saiu direito.",
                ])
                ),
                "calma" if sucesso else "irritada",
                1 if sucesso else 2,
            )
        return True

    if intent == "DELETE_ITEM":
        alvo = str(
            params.get("alvo")
            or params.get("item")
            or params.get("nome")
            or params.get("pasta")
            or params.get("arquivo")
            or ""
        ).strip()
        tipo = str(params.get("tipo") or "").strip().lower()
        alvo = resolver_referencia_arquivo_contextual(alvo, tipo)
        if not alvo:
            marcar_resultado("alvo_ausente", False)
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Apagar o quê? Me dá o nome certinho.",
                    "Faltou o alvo. Eu não saio apagando no escuro.",
                    "Me fala o que eu devo apagar antes de eu virar uma tragédia ambulante.",
                ]), "calma", 1)
            return True

        if destino_val == "pc_b" and callable(_enviar_pc_b):
            confirmado_remoto = bool(_enviar_pc_b({"action": "deletar_item", "alvo": alvo}))
            marcar_resultado("item_deletado_pc_b" if confirmado_remoto else "pc_b_sem_confirmacao", confirmado_remoto)
            if callable(falar):
                if confirmado_remoto:
                    falar(f"O PC B confirmou que enviou {alvo} para a lixeira.", "calma", 1)
                else:
                    falar(f"Enviei o pedido ao PC B, mas ele não confirmou a exclusão de {alvo}.", "calma", 1)
            return True

        tipo_alvo = tipo
        if not tipo_alvo:
            caminho_alvo = resolver_caminho_local(alvo)
            try:
                if caminho_alvo and os.path.isdir(caminho_alvo):
                    tipo_alvo = "pasta"
                elif caminho_alvo and os.path.isfile(caminho_alvo):
                    tipo_alvo = "arquivo"
            except Exception:
                tipo_alvo = tipo_alvo or ""
        buscar_itens = getattr(arquivos_mutacao, "buscar_itens", None)
        candidatos = list(buscar_itens(alvo) or ()) if callable(buscar_itens) else []
        if len(candidatos) > 1:
            marcar_resultado("alvo_ambiguo", False)
            if callable(falar):
                caminhos_texto = "; ".join(candidatos[:3])
                falar(
                    "Encontrei mais de um item com esse nome e não apaguei "
                    f"nenhum. Diga o caminho completo: {caminhos_texto}.",
                    "calma",
                    1,
                )
            return True
        caminho_resolvido = candidatos[0] if len(candidatos) == 1 else resolver_caminho_local(alvo)
        solicitar_exclusao = getattr(arquivos_mutacao, "solicitar_exclusao", None)
        if not callable(solicitar_exclusao):
            marcar_resultado("indisponivel", False)
            falar("A lixeira da Laylay não está disponível agora.", "calma", 1)
            return True
        resultado_lixeira = solicitar_exclusao(caminho_resolvido)
        if resultado_lixeira.requer_confirmacao:
            marcar_resultado(
                "aguardando_confirmacao",
                False,
                alvo_resolvido=resultado_lixeira.caminho or caminho_resolvido,
                params_resolvidos={
                    "alvo": resultado_lixeira.caminho or caminho_resolvido,
                    "caminho": resultado_lixeira.caminho or caminho_resolvido,
                    "tipo": tipo_alvo,
                },
            )
            if callable(falar):
                falar(
                    f"Confirma que quer enviar esse item para a lixeira? O caminho completo é {resultado_lixeira.caminho}.",
                    "calma",
                    1,
                )
            return True
        sucesso = resultado_lixeira.sucesso
        if sucesso:
            sucesso = not item_local_existe(alvo, tipo_alvo)
        if sucesso:
            registrar_arquivo(alvo, "arquivos")
            marcar_resultado("item_deletado", True)
        else:
            marcar_resultado("falha_execucao", False)
        if callable(falar):
            if sucesso:
                fala = _escolher_fala_variada([
                    f"Apaguei {alvo}. Foi pro limbo, com recibo.",
                    f"{alvo} apagado. Sem palestra de CMD dessa vez.",
                    f"Pronto, removi {alvo}.",
                ])
            else:
                detalhe = f"a {tipo} " if tipo else ""
                fala = _escolher_fala_variada([
                    f"Não consegui apagar {detalhe}{alvo}.",
                    f"Tentei remover {alvo}, mas não achei ou o Windows fez corpo mole.",
                    f"{alvo} resistiu à limpeza. Não consegui apagar agora.",
                ])
            falar(fala, "calma" if sucesso else "irritada", 1 if sucesso else 2)
        return True

    return False
