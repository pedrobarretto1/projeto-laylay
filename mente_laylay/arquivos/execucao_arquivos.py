"""Execucao de intents de arquivos da Laylay.

Mantem a execucao de CREATE_FOLDER, CREATE_FILE e DELETE_ITEM fora do roteador principal.
O modulo recebe callbacks do contexto vivo para preservar a regra de mente unica.
"""

from __future__ import annotations

import os
from typing import Any, Callable, Dict

from mente_laylay.personalidade.falas_variadas import escolher as _escolher_fala_variada
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao, inferir_confirmacao
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao
from mente_laylay.arquivos.transacao_arquivos import executar_transacao_arquivo
from mente_laylay.arquivos.lixeira_laylay import (
    cancelar_exclusao_pendente,
    confirmar_exclusao_pendente,
    mover_para_lixeira,
    restaurar_ultimo_item,
)
from mente_laylay.arquivos.arquivos_sistema import buscar_itens_com_nome


def _get(ctx: Dict[str, Any], nome: str, default=None):
    return ctx.get(nome, default)


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
) -> bool:
    falar_original = _get(ctx, "falar_com_lipsync")
    criar_pasta = _get(ctx, "criar_pasta")
    criar_ou_editar_arquivo = _get(ctx, "criar_ou_editar_arquivo")
    mover_arquivo = _get(ctx, "mover_arquivo")
    deletar_item = _get(ctx, "deletar_item")
    resolver_caminho = _get(ctx, "resolver_caminho")
    ultima_pasta_contextual = _get(ctx, "ultima_pasta_contextual")
    registrar_estrutura_arquivo_recente = _get(ctx, "_registrar_estrutura_arquivo_recente")
    _enviar_pc_b = _get(ctx, "_enviar_pc_b")
    marcar_resultado_original = marcar_resultado
    resultado_fala: Dict[str, Any] = {"status": "", "executou": None}
    alvo_planejado = str(
        params.get("alvo") or params.get("nome") or params.get("pasta") or params.get("arquivo") or "arquivo"
    ).strip()

    def marcar_resultado(status: str, executou: bool | None) -> None:
        resultado_fala["status"] = str(status or "")
        resultado_fala["executou"] = executou
        marcar_resultado_original(status, executou)

    def falar(texto: str, emocao: str = "calma", nivel: int = 1) -> None:
        if not callable(falar_original):
            return
        status = str(resultado_fala.get("status") or "")
        if not status:
            falar_original(texto, emocao, nivel)
            return
        plano = planejar_resposta_acao(
            ResultadoAcao(
                intent=intent,
                status=status,
                alvo=alvo_planejado,
                executou=resultado_fala.get("executou"),
                confirmado=inferir_confirmacao(status, resultado_fala.get("executou")),
                texto_usuario=texto_original,
                contexto={"destino": destino_val},
            ),
            texto,
            emocao_preferida=emocao,
            nivel_preferido=nivel,
        )
        resultado_fala["status"] = ""
        resultado_fala["executou"] = None
        falar_original(plano.fala, plano.emocao, plano.nivel)

    if intent == "FILE_TRANSACTION":
        resultado = executar_transacao_arquivo(params)
        marcar_resultado(resultado.status if resultado.sucesso else "falha_execucao", resultado.sucesso)
        if resultado.sucesso:
            registrar_arquivo(resultado.destino or resultado.origem, "arquivos")
        if callable(falar):
            if resultado.sucesso:
                falas = {
                    "movido": f"Corrigi o destino e confirmei: agora está em {resultado.destino}.",
                    "renomeado": f"Corrigi o nome e confirmei: agora é {os.path.basename(resultado.destino)}.",
                    "conteudo_atualizado": f"Corrigi o conteúdo de {os.path.basename(resultado.origem)} e conferi o arquivo.",
                }
                falar(falas.get(resultado.status, "Corrigi o arquivo e confirmei o resultado."), "calma", 1)
            else:
                falar(
                    f"Entendi a correção, mas não alterei o arquivo porque a transação falhou: {resultado.status}.",
                    "irritada",
                    2,
                )
        return True

    if intent == "CANCEL_DELETE_ITEM":
        cancelar_exclusao_pendente()
        marcar_resultado("exclusao_cancelada", False)
        if callable(falar):
            falar("Certo, cancelei a exclusão. Não mexi em nada.", "calma", 1)
        return True

    if intent == "CONFIRM_DELETE_ITEM":
        resultado = confirmar_exclusao_pendente()
        marcar_resultado(resultado.status, resultado.sucesso)
        if callable(falar):
            if resultado.sucesso:
                falar(f"Confirmado. Enviei {resultado.caminho} para a lixeira; ainda dá para desfazer.", "calma", 1)
            else:
                falar("A confirmação expirou ou não havia exclusão esperando.", "calma", 1)
        return True

    if intent == "RESTORE_DELETED_ITEM":
        resultado = restaurar_ultimo_item()
        marcar_resultado(resultado.status, resultado.sucesso)
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

        def registrar_contexto_criado() -> None:
            if not callable(registrar_estrutura_arquivo_recente):
                return
            try:
                registrar_estrutura_arquivo_recente({
                    "nome": nome,
                    "pasta_pai": pasta_pai,
                    "pasta_interna": pasta_interna,
                    "mover_item": mover_item,
                    "arquivo_nome": arquivo_nome,
                    "arquivo_conteudo": arquivo_conteudo,
                    "target": destino_val,
                })
            except Exception:
                pass
        if pasta_pai.lower() in {"ela", "nela", "essa", "essa pasta", "dela", "dentro dela"} and callable(ultima_pasta_contextual):
            pasta_pai = str(ultima_pasta_contextual() or "").strip()
        if not nome:
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Criar qual pasta, Pedro? Me dá o nome.",
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
                registrar_arquivo(nome_resolvido, "arquivos")
                marcar_resultado("pasta_criada", True)
                registrar_contexto_criado()
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
        alvo = str(params.get("alvo") or params.get("nome") or params.get("arquivo") or "").strip()
        conteudo = str(params.get("conteudo") or params.get("texto") or "")
        if not alvo:
            if callable(falar):
                falar("Qual arquivo você quer criar, Pedro?", "calma", 1)
            return True
        if destino_val == "pc_b":
            if callable(falar):
                falar("Ainda não envio arquivo de texto direto para o PC B.", "calma", 1)
            marcar_resultado("arquivo_pc_b_nao_suportado", False)
            return True
        caminho = resolver_caminho_local(alvo)
        sucesso = bool(criar_ou_editar_arquivo(caminho, conteudo, "w")) if callable(criar_ou_editar_arquivo) else False
        if sucesso:
            sucesso = item_local_existe(caminho, "arquivo")
        if sucesso:
            registrar_arquivo(caminho, "arquivos")
            marcar_resultado("arquivo_criado", True)
            if callable(registrar_estrutura_arquivo_recente):
                try:
                    registrar_estrutura_arquivo_recente({"arquivo_nome": alvo, "target": destino_val})
                except Exception:
                    pass
        else:
            marcar_resultado("falha_execucao", False)
        if callable(falar):
            falar(
                _escolher_fala_variada([f"Arquivo {alvo} criado.", f"Pronto, {alvo} já existe.", f"Criei {alvo}."])
                if sucesso else _escolher_fala_variada([f"Não consegui criar {alvo}.", f"O arquivo {alvo} não saiu direito."]),
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
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Apagar o quê, Pedro? Me dá o nome certinho.",
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
        candidatos = buscar_itens_com_nome(alvo)
        if len(candidatos) > 1:
            marcar_resultado("alvo_ambiguo", False)
            if callable(falar):
                caminhos = "; ".join(candidatos[:3])
                falar(
                    f"Encontrei mais de um item com esse nome e não apaguei nenhum. Diga o caminho completo: {caminhos}.",
                    "calma",
                    1,
                )
            return True
        caminho_resolvido = candidatos[0] if len(candidatos) == 1 else resolver_caminho_local(alvo)
        resultado_lixeira = mover_para_lixeira(caminho_resolvido)
        if resultado_lixeira.requer_confirmacao:
            marcar_resultado("aguardando_confirmacao", False)
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
