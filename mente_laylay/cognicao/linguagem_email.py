"""Verbos e entidades de e-mail; modalidade e confirmação têm owners comuns."""
from __future__ import annotations

import re

from mente_laylay.cognicao.modalidade_turno import (
    classificar_modalidade_turno, autoriza_execucao_efetiva,
    turno_tem_veto_execucao, extrair_nucleo_pedido_operacional,
)
from mente_laylay.cognicao.gramatica_operacional import tipo_recurso_pedido_direto
from mente_laylay.cognicao.referencias_linguagem import extrair_indice_referencia_ordinal, texto_tem_referencia_contextual
from mente_laylay.memoria_mental.aprendizado_rotina_musica import classificar_confirmacao_local
from mente_laylay.memoria_mental.memoria_confiavel import normalizar_texto
from mente_laylay.arquivos.nome_natural import caminho_absoluto_literal


def _campos_email(texto: str) -> dict:
    campos: dict = {}
    for endereco in re.finditer(r"[^\s<>@,;]+@[^\s<>@,;]+\.[^\s<>@,;]+", texto):
        prefixo = normalizar_texto(texto[:endereco.start()])
        rotulos = list(re.finditer(r"\b(?:para|pra|cc|bcc|copia oculta|com copia|em copia)\b", prefixo))
        if rotulos:
            rotulo = rotulos[-1][0]
            campo = "bcc" if rotulo in {"bcc", "copia oculta"} else "cc" if rotulo in {"cc", "com copia", "em copia"} else "para"
            campos.setdefault(campo, []).append(endereco[0].rstrip(".!?"))
    if re.search(r"\b(?:anexa|anexe|anexar|anexo|anexos)\b", normalizar_texto(texto)):
        caminhos = [caminho_absoluto_literal(t) for t in re.findall(r'"[^"\r\n]+"|[^\s]+', texto)]
        campos["anexos"] = [c for c in caminhos if c]
        campos["anexo_pedido"] = True
    return campos


def _alvo_rascunho(texto: str) -> dict:
    """Preserva referência explícita, inclusive inválida, para lookup exato."""
    referencia = re.search(r"\brascunho\s+(?:(id)\s+)?([a-z0-9_-]+)\b", texto)
    if not referencia:
        return {}
    if not referencia[1] and referencia[2] in {
        "atual", "local", "para", "pra", "com", "mais", "menos", "dizendo",
        "informando", "explicando", "avisando", "deixando",
    }:
        return {}
    return {"id": referencia[2]}


def detectar_email(texto: str, *, contexto_ativo: bool = False, rascunho_ativo: bool = False,
                   confirmacao_pendente: bool = False) -> dict | None:
    t = normalizar_texto(texto).strip(" .,!?:;")
    if confirmacao_pendente and classificar_confirmacao_local(texto, somente_aceite_generico=True) is not None:
        return {"intent": "EMAIL_CONFIRM", "params": {}}
    turno = classificar_modalidade_turno(texto)
    if turno_tem_veto_execucao(turno) or turno.get("natureza_acao") in {"hipotetica", "mencao_operacional", "capacidade"}:
        return None
    permitido = autoriza_execucao_efetiva(turno)
    nucleo = normalizar_texto(extrair_nucleo_pedido_operacional(texto) or texto).strip(" .,!?:;")
    tipo = tipo_recurso_pedido_direto(texto)
    if tipo and tipo != "email":
        return None
    menciona = bool(re.search(r"\b(?:e-?mails?|gmail|rascunhos?)\b", t))
    if "rascunho" in t and re.match(r"^(?:tem|quais|lista|liste|listar|mostra|mostre|le|leia)\b", nucleo):
        identificador = _alvo_rascunho(t)
        leitura_singular = bool(re.match(r"^(?:mostra|mostre|le|leia)\b", nucleo)
            and re.search(r"\brascunho\b", nucleo))
        return {"intent": "EMAIL_DRAFT_READ", "params": {
            "acao": "mostrar" if identificador or leitura_singular else "listar",
            **identificador,
        }}
    indice = extrair_indice_referencia_ordinal(texto) if contexto_ativo else None
    params = {"indice": indice + 1} if indice is not None else {}
    remetente = re.search(r"\b(?:e-?mails?|mensagens?)\s+(?:do|da|de)\s+(.+)$", t)
    if remetente and (turno.get("modalidade_geral") == "pergunta" or permitido):
        return {"intent": "EMAIL_READ", "params": {"remetente": remetente[1], "todos": True}}
    busca = re.search(r"\b(?:busca|busque|procura|procure|pesquisa|pesquise)\s+(?:os?\s+)?(?:e-?mails?|mensagens?)\s+(?:sobre\s+)?(.+)$", t)
    if busca and permitido:
        return {"intent": "EMAIL_READ", "params": {"query": busca[1], "todos": True}}
    if contexto_ativo and re.fullmatch(r"(?:volta|volte|le|leia|mostra|mostre)\s+(?:ao?\s+|o\s+)?(?:email\s+)?anterior", t):
        return {"intent": "EMAIL_READ", "params": {"modo": "conteudo", "deslocamento": -1, "pergunta": "Explique o conteúdo da mensagem."}}
    if permitido and (menciona or rascunho_ativo or contexto_ativo):
        lixeira = bool(re.match(r"^(?:envia|envie|manda|mande)\b", nucleo)
            and re.search(r"\b(?:para|pra)\s+(?:a\s+)?lixeira\b", nucleo))
        if lixeira and "rascunho" not in t:
            return {"intent": "EMAIL_MODIFY", "params": {**params, "acao": "lixeira"}}
        envio_referencial = bool(re.fullmatch(r"(?:envia|envie|enviar|manda|mande)(?:\s+(?:isso|ele|esse))?", nucleo))
        if re.match(r"^(?:envia|envie|enviar|manda|mande)\b", nucleo) and not lixeira and (
            menciona or (rascunho_ativo and envio_referencial)
        ):
            # Um verbo explícito de domínio pode confirmar somente a mesma
            # operação vigente, nunca substituir seu alvo ou seu conteúdo.
            if confirmacao_pendente and re.fullmatch(r"(?:pode\s+)?(?:enviar|envia|envie)(?:\s+(?:esse|o)\s+(?:email|e-mail|rascunho))?", t):
                return {"intent": "EMAIL_CONFIRM", "params": {}}
            campos = _campos_email(texto)
            if campos.get("para") or re.search(r"\b(?:dizendo|informando|explicando|avisando)\b", t):
                return {"intent": "EMAIL_SEND", "params": {**campos, "instrucao": texto, "criar_rascunho": True}}
            return {"intent": "EMAIL_SEND", "params": _alvo_rascunho(nucleo)}
        operacao_rascunho = re.match(r"^(prepara|prepare|redige|redija|escreve|escreva|cria|crie|"
            r"edita|edite|altera|altere|troca|troque|muda|mude|descarta|descarte|apaga|apague)\s+"
            r"(?:(?:o|a|um|uma|esse|essa|este|esta|meu|minha)\s+)?(e-?mail|rascunho)\b", nucleo)
        if menciona and operacao_rascunho and not (
            operacao_rascunho[1] in {"descarta", "descarte", "apaga", "apague"}
            and operacao_rascunho[2] != "rascunho"
        ):
            acao = "criar"
            if operacao_rascunho[1] in {"descarta", "descarte", "apaga", "apague"}:
                acao = "descartar"
            elif operacao_rascunho[1] in {"edita", "edite", "altera", "altere", "troca", "troque", "muda", "mude"}:
                acao = "editar"
            return {"intent": "EMAIL_DRAFT", "params": {"acao": acao, "instrucao": texto,
                **_campos_email(texto), **(_alvo_rascunho(nucleo) if acao != "criar" else {})}}
        if contexto_ativo and re.match(r"^(?:responde|responda|responder|encaminha|encaminhe|encaminhar)\b", nucleo):
            return {"intent": "EMAIL_DRAFT", "params": {**params,
                "acao": "encaminhar" if "encaminh" in t else "responder", "instrucao": texto, **_campos_email(texto)}}
        edicao_eliptica = re.match(r"^(?:deixa|deixe|troca|troque|muda|mude|edita|edite|altera|altere)\s+"
            r"(?:(?:o|a|esse|essa|este|esta)\s+)?(?:mais\s+|menos\s+)?"
            r"(?:formal|informal|curto|curta|direto|direta|texto|trecho|prazo|assunto|destinatario|tom|paragrafo)\b", nucleo)
        if rascunho_ativo and (edicao_eliptica or re.match(r"^(?:anexa|anexe)\b", nucleo)):
            return {"intent": "EMAIL_DRAFT", "params": {"acao": "editar", "instrucao": texto, **_campos_email(texto)}}
        if contexto_ativo or menciona:
            acao = ""
            if re.match(r"^(?:arquiva|arquive|arquivar)\b", nucleo):
                acao = "arquivar"
            elif re.match(r"^(?:apaga|apague|exclui|exclua|manda\s+(?:para\s+|pra\s+)?a?\s*lixeira)\b", nucleo):
                acao = "lixeira"
            elif re.match(r"^(?:marca|marque)\b.*\b(?:lido|lida)\b", nucleo):
                acao = "marcar_nao_lido" if "nao lid" in t else "marcar_lido"
            if acao:
                return {"intent": "EMAIL_MODIFY", "params": {**params, "acao": acao}}
    # Conteúdo é consultado apenas quando o contexto vivo é e-mail ou o
    # usuário explicita uma mensagem singular. Outros assuntos não herdam
    # silenciosamente a mensagem anunciada.
    singular = bool(re.search(r"\b(?:esse|este|o|aquele)\s+(?:email|e-mail)\b", t))
    if contexto_ativo and menciona and re.search(r"\b(?:conversa|historico|respostas anteriores)\b", t) and (permitido or turno.get("modalidade_geral") == "pergunta"):
        return {"intent": "EMAIL_READ", "params": {**params, "modo": "conversa", "pergunta": texto}}
    pergunta = turno.get("modalidade_geral") == "pergunta" or turno.get("natureza_acao") == "consulta"
    inventario = bool(re.search(r"\b(?:emails|e-mails|rascunhos)\b", t) and not singular)
    campo_email = bool(re.search(r"\b(?:entrega|pedido|rastreio|remetente|destinatario|prazo|anexo|anexos|assunto|cobranca)\b", t))
    referencia = texto_tem_referencia_contextual(t)
    elipse = bool(re.fullmatch(r"(?:quando\s+(?:chega|vence)|explica\s+melhor|como\s+assim|o\s+que\s+(?:pedem|querem)|preciso\s+fazer\s+alguma\s+coisa)", t))
    leitura_referencial = bool(re.fullmatch(r"(?:le|leia|ler|explica|explique|resume|resuma)\s+(?:ele|ela|isso|esse|essa)", nucleo))
    if (contexto_ativo and not inventario and ((pergunta and (campo_email or referencia)) or elipse or leitura_referencial or indice is not None)) or (singular and re.search(r"\b(?:le|leia|ler|explica|explique|resume|resuma)\b", t)):
        if re.search(r"\b(?:musica|playlist|clima|tempo agora|lampada|janela|programa)\b", t) and not menciona:
            return None
        leitura_simples = indice is not None or leitura_referencial or bool(re.fullmatch(
            r"(?:le|leia|ler|resume|resuma)\s+(?:(?:o|esse|este|aquele|meu)\s+)?(?:email|e-mail)", nucleo))
        consulta_conteudo = "Resuma o assunto e as informações principais da mensagem." if leitura_simples else texto
        return {"intent": "EMAIL_READ", "params": {**params, "modo": "conteudo", "pergunta": consulta_conteudo}}
    return None
