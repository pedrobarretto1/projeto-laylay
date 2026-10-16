"""Transporte Gmail: identidade verificável, leitura sem efeito e receipts.

Reutiliza as credenciais do GmailMental. Conteúdo recebido é dado externo,
nunca instrução ou autorização. Não realiza retry de envio.
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import re
import smtplib
import ssl
import time
from contextlib import contextmanager
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import getaddresses, make_msgid, formatdate
from html.parser import HTMLParser
from typing import Any, Iterator, Mapping


class _TextoHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []
        self.oculto = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in {"script", "style", "head"}:
            self.oculto += 1
        elif tag in {"br", "p", "div", "li", "tr"} and not self.oculto:
            self.partes.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "head"}:
            self.oculto = max(0, self.oculto - 1)

    def handle_data(self, data: str) -> None:
        if not self.oculto:
            self.partes.append(data)


def extrair_conteudo_mime(raw: bytes, limite: int = 14000) -> dict[str, Any]:
    mensagem = BytesParser(policy=policy.default).parsebytes(raw)
    anexos = [{"nome": str(p.get_filename() or "anexo"), "tipo": p.get_content_type()}
              for p in mensagem.walk() if p.get_content_disposition() == "attachment" or p.get_filename()]
    parte = mensagem.get_body(preferencelist=("plain", "html"))
    texto = ""
    if parte is not None:
        try:
            texto = str(parte.get_content())
        except (LookupError, UnicodeError):
            texto = (parte.get_payload(decode=True) or b"").decode("utf-8", errors="replace")
        if parte.get_content_type() == "text/html":
            html = _TextoHTML()
            html.feed(texto)
            texto = "".join(html.partes)
    texto = re.sub(r"[ \t]+", " ", texto.replace("\r", "")).strip()
    return {"corpo": texto[:limite], "conteudo_truncado": len(texto) > limite,
            "anexos": anexos, "anexos_lidos": False,
            "message_id": str(mensagem.get("Message-ID") or ""),
            "references": str(mensagem.get("References") or ""),
            "reply_to": str(mensagem.get("Reply-To") or mensagem.get("From") or ""),
            "assunto": str(mensagem.get("Subject") or "(sem assunto)"),
            "remetente": str(mensagem.get("From") or ""),
            "data": str(mensagem.get("Date") or "")}


def enderecos_validos(valor: Any) -> list[str]:
    valores = valor if isinstance(valor, list) else [str(valor or "")]
    if any("\r" in str(v) or "\n" in str(v) for v in valores):
        raise ValueError("endereco_invalido")
    resultado = [endereco for _, endereco in getaddresses([str(v) for v in valores])]
    if not resultado or any(not re.fullmatch(r"[^\s<>@,;]+@[^\s<>@,;]+\.[^\s<>@,;]+", e) for e in resultado):
        raise ValueError("destinatario_ausente_ou_invalido")
    return list(dict.fromkeys(resultado))


class CaixaGmailRuntime:
    def __init__(self, mental: Any) -> None:
        self.mental = mental

    @property
    def identidade_conta(self) -> str:
        return hashlib.sha256(self.mental.usuario.strip().casefold().encode()).hexdigest()[:20]

    @contextmanager
    def _conexao(self) -> Iterator[Any]:
        if not self.mental.configurado():
            raise ValueError("email_indisponivel")
        # Resolve a fábrica na hora da chamada: conserva o mesmo transporte
        # usado pelo monitor e permite isolar só a rede nos testes.
        from mente_laylay.integracao import gmail_mental
        conexao = gmail_mental.imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=25)
        try:
            self._ok(conexao.login(self.mental.usuario, self.mental.app_password))
            capability = getattr(conexao, "capability", None)
            if callable(capability):
                resposta = self._ok(capability())
                conexao.capabilities = tuple(b" ".join(resposta).upper().split())
            yield conexao
        finally:
            try:
                conexao.logout()
            except Exception:
                pass

    @staticmethod
    def _ok(retorno: tuple) -> Any:
        if not retorno or str(retorno[0]).upper() != "OK":
            raise ValueError("consulta_recusada")
        return retorno[1]

    @staticmethod
    def _uidvalidity(conexao: Any) -> str:
        resposta = getattr(conexao, "response", None)
        if not callable(resposta):
            return ""
        _, valores = resposta("UIDVALIDITY")
        valor = valores[0] if valores else b""
        return valor.decode("ascii") if isinstance(valor, bytes) else str(valor or "")

    def _selecionar(self, conexao: Any, pasta: str, *, escrita: bool = False) -> str:
        if not pasta or any(c in pasta for c in "\r\n\x00"):
            raise ValueError("pasta_invalida")
        self._ok(conexao.select(pasta, readonly=not escrita))
        return self._uidvalidity(conexao)

    def _pasta_especial(self, conexao: Any, atributo: bytes) -> str:
        linhas = self._ok(conexao.list())
        for linha in linhas:
            if isinstance(linha, bytes) and atributo in linha:
                nome = re.search(rb'"([^"\r\n]+)"$', linha)
                if nome:
                    return '"' + nome[1].decode("ascii") + '"'
        raise ValueError("operacao_nao_suportada")

    def _validar_referencia(self, conexao: Any, referencia: Mapping[str, Any], *, escrita: bool = False) -> str:
        if referencia.get("conta") != "principal" or referencia.get("identidade_conta") != self.identidade_conta:
            raise ValueError("conta_divergente")
        uid = str(referencia.get("uid") or "")
        if not re.fullmatch(r"[1-9][0-9]*", uid):
            raise ValueError("referencia_email_invalida")
        atual = self._selecionar(conexao, str(referencia.get("pasta") or ""), escrita=escrita)
        if not atual or atual != str(referencia.get("uidvalidity") or ""):
            raise ValueError("referencia_email_expirada")
        return uid

    @staticmethod
    def _literal(dados: Any) -> tuple[bytes, bytes]:
        for item in dados or []:
            if isinstance(item, tuple) and len(item) == 2 and isinstance(item[1], bytes):
                return bytes(item[0]), item[1]
        raise ValueError("email_nao_encontrado")

    def _referencia(self, uid: bytes, pasta: str, validade: str, meta: bytes) -> dict[str, str]:
        referencia = {"conta": "principal", "identidade_conta": self.identidade_conta,
                      "pasta": pasta, "uidvalidity": validade, "uid": uid.decode("ascii")}
        for campo, atributo in (("gmail_id", "X-GM-MSGID"), ("conversa_id", "X-GM-THRID")):
            encontrado = re.search(rb"\b" + atributo.encode() + rb" (\d+)", meta)
            if encontrado:
                referencia[campo] = encontrado[1].decode()
        return referencia

    def _falha(self, erro: Exception) -> dict[str, Any]:
        codigos = {"email_indisponivel", "email_nao_encontrado", "referencia_email_expirada",
                   "referencia_email_invalida", "conta_divergente", "email_muito_grande",
                   "pasta_invalida", "consulta_recusada", "operacao_nao_suportada"}
        codigo = str(erro) if str(erro) in codigos else "falha_consulta_email"
        self.mental._falha(codigo, RuntimeError(type(erro).__name__))
        return {"ok": False, "status": codigo, "confirmado": False, "mensagens": []}

    def consultar_mensagens(self, *, nao_lidos: bool = False, query: str = "", limite: int = 20,
                           pasta: str = "", conversa_id: str = "") -> dict[str, Any]:
        mensagens: list[dict] = []
        try:
            with self._conexao() as conexao:
                pasta = pasta or (self._pasta_especial(conexao, b"\\All") if query or conversa_id else "INBOX")
                validade = self._selecionar(conexao, pasta)
                if conversa_id:
                    if not re.fullmatch(r"\d+", conversa_id):
                        raise ValueError("referencia_email_invalida")
                    dados = self._ok(conexao.uid("search", None, "X-GM-THRID", conversa_id))
                elif query:
                    if any(c in query for c in "\r\n\x00"):
                        raise ValueError("consulta_recusada")
                    dados = self._ok(conexao.uid("search", None, "X-GM-RAW", json.dumps(query, ensure_ascii=False).encode("utf-8")))
                else:
                    dados = self._ok(conexao.uid("search", None, "UNSEEN" if nao_lidos else "ALL"))
                ids = dados[0].split() if dados and dados[0] else []
                quantidade = max(1, min(int(limite), 50))
                extensao = b"X-GM-EXT-1" in getattr(conexao, "capabilities", ())
                atributos = "X-GM-MSGID X-GM-THRID " if extensao else ""
                for uid in reversed(ids[-quantidade:]):
                    meta, raw = self._literal(self._ok(conexao.uid("fetch", uid,
                        f"({atributos}BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE MESSAGE-ID REPLY-TO AUTHENTICATION-RESULTS)])")))
                    msg = BytesParser(policy=policy.default).parsebytes(raw)
                    assunto = str(msg.get("Subject") or "(sem assunto)")
                    analise = self.mental.analisar_remetente(str(msg.get("From") or ""), assunto,
                        str(msg.get("Authentication-Results") or ""), str(msg.get("Reply-To") or ""))
                    remetente = str(analise.get("nome") or "desconhecido")
                    referencia = self._referencia(uid, pasta, validade, meta)
                    identificador = ("gmail:" + self.identidade_conta + ":" + referencia["gmail_id"]
                        if referencia.get("gmail_id") else "email:" + self.identidade_conta + ":" + validade + ":" + uid.decode()
                        if validade else "uid:" + uid.decode())
                    mensagens.append({**analise, "uid": identificador, "remetente": remetente,
                        "assunto": assunto, "data": str(msg.get("Date") or ""),
                        "prioritario": self.mental.email_prioritario(remetente, assunto),
                        "silenciado": any(s in remetente.casefold() for s in self.mental.remetentes_silenciados),
                        "categoria": self.mental.classificar_categoria(remetente, assunto),
                        "referencia_email": referencia})
                return {"ok": True, "status": "emails_consultados", "confirmado": True,
                        "mensagens": mensagens, "total": len(ids), "limitado": len(ids) > quantidade,
                        "consultado_em": time.time(), "conta": "principal"}
        except Exception as erro:
            return {**self._falha(erro), "parcial": bool(mensagens)}

    def ler_mensagem(self, referencia: Mapping[str, Any]) -> dict[str, Any]:
        try:
            with self._conexao() as conexao:
                uid = self._validar_referencia(conexao, referencia)
                tamanhos = self._ok(conexao.uid("fetch", uid, "(RFC822.SIZE)"))
                tamanho = re.search(rb"RFC822.SIZE (\d+)", b" ".join(x for x in tamanhos if isinstance(x, bytes)))
                if not tamanho or int(tamanho[1]) > 2_000_000:
                    raise ValueError("email_muito_grande")
                _, raw = self._literal(self._ok(conexao.uid("fetch", uid, "(BODY.PEEK[])")))
                if len(raw) > 2_000_000:
                    raise ValueError("email_muito_grande")
                return {"ok": True, "status": "email_conteudo_lido", "confirmado": True,
                        "mensagem": {**extrair_conteudo_mime(raw), "referencia_email": dict(referencia)},
                        "consultado_em": time.time(), "autoriza_execucao": False}
        except Exception as erro:
            return self._falha(erro)

    def alterar_mensagem(self, referencia: Mapping[str, Any], acao: str) -> dict[str, Any]:
        efeito_iniciado = False
        try:
            with self._conexao() as conexao:
                uid = self._validar_referencia(conexao, referencia, escrita=True)
                def alterar(*args: str) -> None:
                    nonlocal efeito_iniciado
                    efeito_iniciado = True
                    resposta = conexao.uid("store", uid, *args)
                    if resposta and str(resposta[0]).upper() != "OK":
                        efeito_iniciado = False
                    self._ok(resposta)
                if acao in {"marcar_lido", "marcar_nao_lido"}:
                    alterar("+FLAGS" if acao == "marcar_lido" else "-FLAGS", "(\\Seen)")
                    dados = self._ok(conexao.uid("fetch", uid, "(FLAGS)"))
                    bruto = b" ".join(x for x in dados if isinstance(x, bytes))
                    if (b"\\Seen" in bruto) != (acao == "marcar_lido") or b"FLAGS" not in bruto:
                        raise ValueError("consulta_recusada")
                elif acao in {"arquivar", "lixeira"}:
                    if b"X-GM-EXT-1" not in getattr(conexao, "capabilities", ()) or not referencia.get("gmail_id"):
                        raise ValueError("operacao_nao_suportada")
                    if acao == "lixeira":
                        alterar("+X-GM-LABELS", "(\\Trash)")
                    else:
                        alterar("-X-GM-LABELS", "(\\Inbox)")
                    # UID da pasta original pode desaparecer. Confere o mesmo
                    # Gmail ID na pasta especial, descoberta pelo servidor.
                    linhas = self._ok(conexao.list())
                    atributo = b"\\Trash" if acao == "lixeira" else b"\\All"
                    pasta_destino = next((re.search(rb'"([^"\r\n]+)"$', x)[1].decode("ascii")
                        for x in linhas if isinstance(x, bytes) and atributo in x and re.search(rb'"([^"\r\n]+)"$', x)), "")
                    if not pasta_destino:
                        raise ValueError("consulta_recusada")
                    self._selecionar(conexao, '"' + pasta_destino + '"')
                    destino = self._ok(conexao.uid("search", None, "X-GM-MSGID", str(referencia["gmail_id"])))
                    if not destino or not destino[0]:
                        raise ValueError("consulta_recusada")
                    if acao == "arquivar":
                        dados = self._ok(conexao.uid("fetch", destino[0].split()[0], "(X-GM-LABELS)"))
                        bruto = b" ".join(x for x in dados if isinstance(x, bytes))
                        if b"X-GM-LABELS" not in bruto or b"\\Inbox" in bruto:
                            raise ValueError("consulta_recusada")
                else:
                    raise ValueError("operacao_nao_suportada")
                return {"ok": True, "status": "email_alterado", "confirmado": True,
                        "acao": acao, "referencia_email": dict(referencia)}
        except Exception as erro:
            resultado = self._falha(erro)
            return {**resultado, "status": "email_alteracao_incerta", "confirmado": None,
                    "executou": True} if efeito_iniciado else resultado

    def enviar_rascunho(self, rascunho: Mapping[str, Any]) -> dict[str, Any]:
        iniciou_envio = False
        try:
            if not self.mental.configurado() or rascunho.get("identidade_conta") != self.identidade_conta:
                raise ValueError("email_indisponivel")
            para = enderecos_validos(rascunho.get("para"))
            cc = enderecos_validos(rascunho["cc"]) if rascunho.get("cc") else []
            bcc = enderecos_validos(rascunho["bcc"]) if rascunho.get("bcc") else []
            msg = EmailMessage()
            msg["From"] = self.mental.usuario
            msg["To"] = ", ".join(para)
            if cc:
                msg["Cc"] = ", ".join(cc)
            msg["Subject"] = str(rascunho.get("assunto") or "")
            msg["Message-ID"] = str(rascunho.get("envio_message_id") or make_msgid())
            msg["Date"] = formatdate(localtime=False)
            if rascunho.get("in_reply_to"):
                msg["In-Reply-To"] = str(rascunho["in_reply_to"])
                msg["References"] = str(rascunho.get("references") or rascunho["in_reply_to"])
            msg.set_content(str(rascunho.get("corpo") or ""))
            for anexo in rascunho.get("anexos_preparados") or []:
                tipo = mimetypes.guess_type(anexo["nome"])[0] or "application/octet-stream"
                principal, subtipo = tipo.split("/", 1)
                msg.add_attachment(anexo["dados"], maintype=principal, subtype=subtipo, filename=anexo["nome"])
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=25, context=ssl.create_default_context()) as smtp:
                smtp.login(self.mental.usuario, self.mental.app_password)
                iniciou_envio = True
                recusados = smtp.send_message(msg, from_addr=self.mental.usuario, to_addrs=para + cc + bcc)
            return {"ok": not recusados, "status": "email_envio_parcial" if recusados else "email_enviado",
                    "confirmado": not recusados, "aceito_pelo_servidor": True,
                    "entrega_destinatario_confirmada": False, "recusados": len(recusados),
                    "message_id": str(msg["Message-ID"])}
        except smtplib.SMTPRecipientsRefused:
            return {"ok": False, "status": "email_envio_recusado", "confirmado": False}
        except Exception as erro:
            self.mental._falha("envio_email", RuntimeError(type(erro).__name__))
            return {"ok": False, "status": "email_envio_incerto" if iniciou_envio else "email_envio_recusado",
                    "confirmado": None if iniciou_envio else False}
