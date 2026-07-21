"""Integracao Gmail da Laylay.

O modulo concentra IMAP, cache, silenciamento e falas de email. Ele recebe
callbacks do cerebro principal para continuar integrado ao contexto vivo.
"""

from __future__ import annotations

import email as _email_lib
import email.header as _email_header
from email.utils import parseaddr
import json
import os
import re
import time
from typing import Callable, Dict, Iterable, List

try:
    import imaplib
except ImportError:  # pragma: no cover - ambiente sem IMAP
    imaplib = None  # type: ignore


DEFAULT_GMAIL_PRIORITARIOS = [
    "banco", "bradesco", "itau", "nubank", "inter", "santander",
    "correios", "receita", "fazenda", "prefeitura", "detran",
    "serpro", "nfe", "amazon", "mercadopago", "paypal", "ifood", "rappi",
]

DEFAULT_GMAIL_PALAVRAS_URGENTES = [
    "boleto", "fatura", "vencimento", "vence", "prazo",
    "senha", "bloqueado", "bloqueio", "suspens", "cancelamento",
    "urgente", "importante", "atenção", "atencao",
    "pix", "transação", "transferência", "cobrança", "débito",
    "último aviso", "pendente", "irregularidade", "verificação",
    "confirmação", "confirmacao", "erro", "falha", "alerta",
]

DEFAULT_GMAIL_CATEGORIAS = {
    "financeiro": ["banco", "fatura", "boleto", "pix", "pagamento", "nubank", "itau", "itaú"],
    "compras": ["pedido", "entrega", "rastreio", "amazon", "mercadolivre", "shopee"],
    "estudo": ["senai", "curso", "prova", "atividade", "professor"],
    "seguranca": ["senha", "login", "acesso", "bloqueio", "verificacao", "verificação"],
}


class GmailMental:
    def __init__(
        self,
        *,
        arquivo_estado: str,
        usuario: str = "",
        app_password: str = "",
        intervalo_s: int = 300,
        max_lidos: int = 5,
        prioritarios: Iterable[str] | None = None,
        palavras_urgentes: Iterable[str] | None = None,
        continuidades_set: Callable[[str, object], None] | None = None,
        agendar_fala_proativa: Callable[[str, str, str, int], None] | None = None,
        is_speaking_getter: Callable[[], bool] | None = None,
        modo_jogo_getter: Callable[[], bool] | None = None,
        categorias: Dict[str, Iterable[str]] | None = None,
    ) -> None:
        self.arquivo_estado = arquivo_estado
        self.usuario = usuario
        self.app_password = app_password
        self.intervalo_s = int(intervalo_s or 300)
        self.max_lidos = int(max_lidos or 5)
        self.prioritarios = list(prioritarios or DEFAULT_GMAIL_PRIORITARIOS)
        self.palavras_urgentes = list(palavras_urgentes or DEFAULT_GMAIL_PALAVRAS_URGENTES)
        self.continuidades_set = continuidades_set
        self.agendar_fala_proativa = agendar_fala_proativa
        self.is_speaking_getter = is_speaking_getter
        self.modo_jogo_getter = modo_jogo_getter
        if categorias is None:
            try:
                configuradas = json.loads(os.getenv("GMAIL_CATEGORIAS_JSON", "") or "{}")
                categorias = configuradas if isinstance(configuradas, dict) and configuradas else None
            except json.JSONDecodeError:
                categorias = None
        self.categorias = {
            str(nome): [str(p).casefold() for p in palavras]
            for nome, palavras in (categorias or DEFAULT_GMAIL_CATEGORIAS).items()
        }
        self.ids_vistos: set[str] = set()
        self.ultimo_check: float = 0.0
        self.nao_lidos_cache: list = []
        self.remetentes_silenciados: set[str] = set()
        self._ultima_busca_falhou = False

    def decodificar_header(self, valor: str) -> str:
        if not valor:
            return ""
        try:
            partes = _email_header.decode_header(valor)
            resultado = []
            for parte, charset in partes:
                if isinstance(parte, bytes):
                    charset = charset or "utf-8"
                    try:
                        resultado.append(parte.decode(charset, errors="replace"))
                    except Exception:
                        resultado.append(parte.decode("utf-8", errors="replace"))
                else:
                    resultado.append(str(parte))
            return " ".join(resultado).strip()
        except Exception:
            return str(valor)

    def extrair_remetente(self, from_raw: str) -> str:
        decoded = self.decodificar_header(from_raw)
        m = re.match(r'^"?([^"<]+)"?\s*<', decoded)
        if m:
            return m.group(1).strip()
        m2 = re.match(r'([^@<]+)[@<]', decoded)
        if m2:
            return m2.group(1).strip()
        return decoded[:40]

    def analisar_remetente(self, from_raw: str, assunto: str, autenticacao: str = "", reply_to: str = "") -> dict:
        nome, endereco = parseaddr(self.decodificar_header(from_raw))
        dominio = endereco.rsplit("@", 1)[-1].casefold().strip(". ") if "@" in endereco else ""
        dominio_valido = bool(re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?\.[a-z]{2,63}", dominio))
        auth = str(autenticacao or "").casefold()
        passou_autenticacao = "spf=pass" in auth or "dkim=pass" in auth or "dmarc=pass" in auth
        autenticado = bool(passou_autenticacao and dominio and dominio in auth)
        reply_endereco = parseaddr(self.decodificar_header(reply_to))[1]
        reply_dominio = reply_endereco.rsplit("@", 1)[-1].casefold() if "@" in reply_endereco else ""
        texto = f"{nome} {assunto}".casefold()
        marcas = [p.casefold() for p in self.prioritarios if p]
        marca_alegada = next((marca for marca in marcas if marca in texto), "")
        marca_fora_dominio = bool(marca_alegada and marca_alegada.replace(" ", "") not in dominio.replace("-", ""))
        resposta_desalinhada = bool(reply_dominio and dominio and reply_dominio != dominio)
        possivel_golpe = bool(
            not dominio_valido or dominio.startswith("xn--") or resposta_desalinhada
            or (marca_fora_dominio and not autenticado)
            or (any(p in assunto.casefold() for p in self.palavras_urgentes) and not autenticado)
        )
        return {
            "nome": nome or self.extrair_remetente(from_raw),
            "endereco": endereco,
            "dominio": dominio,
            "dominio_valido": dominio_valido,
            "autenticado": autenticado,
            "possivel_golpe": possivel_golpe,
        }

    def classificar_categoria(self, remetente: str, assunto: str) -> str:
        texto = f"{remetente} {assunto}".casefold()
        return next((nome for nome, palavras in self.categorias.items() if any(p in texto for p in palavras)), "geral")

    def carregar_estado(self) -> None:
        try:
            if os.path.exists(self.arquivo_estado):
                with open(self.arquivo_estado, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                self.ids_vistos = set(dados.get("ids_vistos", []))
                rems = dados.get("remetentes_silenciados", [])
                if isinstance(rems, list):
                    self.remetentes_silenciados = {str(x).strip().lower() for x in rems if str(x).strip()}
        except Exception:
            pass

    def salvar_estado(self) -> None:
        try:
            ids_lista = list(self.ids_vistos)[-500:]
            silenciados = sorted(list(self.remetentes_silenciados))[:200]
            os.makedirs(os.path.dirname(self.arquivo_estado), exist_ok=True)
            temporario = f"{self.arquivo_estado}.tmp"
            with open(temporario, "w", encoding="utf-8") as f:
                json.dump({"ids_vistos": ids_lista, "remetentes_silenciados": silenciados}, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporario, self.arquivo_estado)
        except Exception:
            pass

    def silenciar_remetente(self, remetente: str) -> bool:
        rem = str(remetente or "").strip().lower()
        if not rem:
            return False
        self.remetentes_silenciados.add(rem)
        self.salvar_estado()
        return True

    def email_prioritario(self, remetente: str, assunto: str) -> bool:
        rem_lower = remetente.lower()
        if any(s in rem_lower for s in self.remetentes_silenciados):
            return False
        assunto_lower = assunto.lower()
        for p in self.prioritarios:
            if p.lower() in rem_lower:
                return True
        for palavra in self.palavras_urgentes:
            if palavra in assunto_lower:
                return True
        return False

    def buscar_nao_lidos(self) -> List[Dict[str, object]]:
        if not self.usuario or not self.app_password or "xxxx" in self.app_password or "seu.email" in self.usuario:
            return []
        if imaplib is None:
            print("⚠️ [Gmail] imaplib não disponível.")
            return []

        emails = []
        self._ultima_busca_falhou = False
        try:
            conn = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            conn.login(self.usuario, self.app_password)
            conn.select("INBOX", readonly=True)

            _, data = conn.search(None, "UNSEEN")
            ids_bytes = data[0].split() if data[0] else []
            ids_recentes = ids_bytes[-20:]

            for uid_bytes in reversed(ids_recentes):
                uid = uid_bytes.decode()
                _, msg_data = conn.fetch(uid_bytes, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT REPLY-TO AUTHENTICATION-RESULTS RETURN-PATH)])")
                if not msg_data or not msg_data[0]:
                    continue

                raw_header = bytes(msg_data[0][1])
                msg = _email_lib.message_from_bytes(raw_header)

                assunto = self.decodificar_header(msg.get("Subject", "(sem assunto)"))
                analise = self.analisar_remetente(
                    msg.get("From", ""), assunto, msg.get("Authentication-Results", ""), msg.get("Reply-To", "")
                )
                remetente = str(analise.get("nome") or "desconhecido")
                prioritario = self.email_prioritario(remetente, assunto)

                emails.append({
                    "uid": uid,
                    "remetente": remetente or "desconhecido",
                    "assunto": assunto or "(sem assunto)",
                    "prioritario": prioritario,
                    "silenciado": any(s in (remetente or "").lower() for s in self.remetentes_silenciados),
                    "endereco": analise.get("endereco", ""),
                    "dominio": analise.get("dominio", ""),
                    "dominio_valido": analise.get("dominio_valido", False),
                    "autenticado": analise.get("autenticado", False),
                    "possivel_golpe": analise.get("possivel_golpe", False),
                    "categoria": self.classificar_categoria(remetente, assunto),
                })

            conn.logout()
        except imaplib.IMAP4.error as e:
            self._ultima_busca_falhou = True
            print(f"⚠️ [Gmail] Erro IMAP (credenciais?): {e}")
        except OSError:
            self._ultima_busca_falhou = True
        except Exception as e:
            self._ultima_busca_falhou = True
            print(f"⚠️ [Gmail] Erro inesperado: {e}")

        return emails

    def _continuidades(self, chave: str, valor: object) -> None:
        if callable(self.continuidades_set):
            self.continuidades_set(chave, valor)

    def _fala_proativa(self, tipo: str, texto: str, emocao: str, nivel: int) -> None:
        if callable(self.agendar_fala_proativa):
            self.agendar_fala_proativa(tipo, texto, emocao, nivel)

    def falar_email(self, email_dict: dict, prefixo: str = "") -> None:
        rem = email_dict["remetente"]
        ass = email_dict["assunto"]
        if email_dict.get("silenciado"):
            return
        ass_curto = ass if len(ass) <= 60 else ass[:57] + "..."

        if email_dict.get("possivel_golpe"):
            texto = f"Atenção: possível golpe de {rem}: {ass_curto}. Não abra links antes de conferir o domínio."
            self._fala_proativa("emails", texto, "irritada", 2)
            return

        if email_dict["prioritario"]:
            texto = f"{prefixo}Email importante de {rem}: {ass_curto}."
            emocao = "debochada"
        else:
            texto = f"{prefixo}Email de {rem}: {ass_curto}."
            emocao = "calma"

        self._continuidades("email_sugestao_pendente", {"remetente": str(rem or "").strip(), "ts": time.time()})
        self._fala_proativa("emails", texto, emocao, 1)

    def falar_resumo_estiloso(
        self,
        emails: list,
        somente_prioritarios: bool = False,
        *,
        emitir_proativa: bool = True,
    ) -> str:
        emails = [e for e in (emails or []) if not (isinstance(e, dict) and e.get("silenciado"))]
        if not emails:
            texto = "Nada novo no email, Pedro. A caixa postal tá quieta por enquanto."
            self._continuidades("email_sugestao_pendente", None)
            if emitir_proativa:
                self._fala_proativa("emails", texto, "calma", 1)
            return texto

        selecionados = list(emails or [])[:self.max_lidos]
        prioritarios = [e for e in selecionados if e.get("prioritario")]
        normais = [e for e in selecionados if not e.get("prioritario")]

        def _limpar_assunto(s: str) -> str:
            s = re.sub(r"\s+", " ", str(s or "(sem assunto)").strip())
            s = s.replace("FW:", "").replace("Fwd:", "").strip()
            return s[:72] + "..." if len(s) > 75 else s

        def _resumo_email(e: dict) -> str:
            rem = str(e.get("remetente") or "alguém misterioso").strip()
            ass = _limpar_assunto(e.get("assunto") or "")
            return f"{rem}: {ass}"

        partes = []
        total = len(selecionados)
        if somente_prioritarios:
            abertura = f"Tem {total} email importante esperando tua atenção."
        elif prioritarios:
            abertura = f"Tem {total} email novo, sendo {len(prioritarios)} importante(s)."
        else:
            abertura = f"Tem {total} email novo."
        partes.append(abertura)

        destaques = prioritarios[:2] + normais[: max(0, 4 - len(prioritarios[:2]))]
        if destaques:
            partes.append("Resumo: " + "; ".join(_resumo_email(e) for e in destaques) + ".")

        restantes = total - len(destaques)
        if restantes > 0:
            partes.append(f"E ainda tem mais {restantes} aguardando na fila.")

        texto = " ".join(partes)
        self._continuidades("email_sugestao_pendente", {"remetente": "", "ts": time.time()})
        if emitir_proativa:
            self._fala_proativa("emails", texto, "debochada" if prioritarios else "calma", 1)
        return texto

    def resetar_check(self) -> None:
        self.ultimo_check = 0.0

    def daemon(self) -> None:
        self.carregar_estado()
        time.sleep(8)
        print(f"📧 [Gmail] Daemon iniciado — verificando a cada {self.intervalo_s // 60}min")

        falhas_consecutivas = 0
        while True:
            try:
                agora = time.time()
                if agora - self.ultimo_check < self.intervalo_s:
                    time.sleep(30)
                    continue

                self.ultimo_check = agora
                print("📧 [Gmail] Verificando caixa de entrada...")

                emails = self.buscar_nao_lidos()
                if self._ultima_busca_falhou:
                    falhas_consecutivas += 1
                    atraso = min(1800, 30 * (2 ** min(falhas_consecutivas - 1, 6)))
                    print(f"📧 [Gmail] Nova tentativa em {atraso}s.")
                    time.sleep(atraso)
                    continue
                falhas_consecutivas = 0
                if not emails:
                    time.sleep(30)
                    continue

                self.nao_lidos_cache[:] = emails
                novos = [e for e in emails if e["uid"] not in self.ids_vistos]
                if not novos:
                    print(f"📧 [Gmail] {len(emails)} não lidos, nenhum novo para anunciar")
                    time.sleep(30)
                    continue

                if callable(self.modo_jogo_getter) and self.modo_jogo_getter():
                    print("🎮 [Gmail] Novos emails guardados em silêncio durante o jogo.")
                    time.sleep(30)
                    continue

                if callable(self.is_speaking_getter) and self.is_speaking_getter():
                    time.sleep(10)
                    continue

                prioritarios = [e for e in novos if e["prioritario"]]
                normais = [e for e in novos if not e["prioritario"]]

                for e in prioritarios[:self.max_lidos]:
                    self.falar_email(e)
                    self.ids_vistos.add(e["uid"])
                    time.sleep(1.5)

                normais_novos = [e for e in normais if e["uid"] not in self.ids_vistos]
                if normais_novos:
                    n = len(normais_novos)
                    if n == 1:
                        self.falar_email(normais_novos[0])
                        self.ids_vistos.add(normais_novos[0]["uid"])
                    else:
                        self._continuidades("email_sugestao_pendente", {"remetente": "", "ts": time.time()})
                        self._fala_proativa(
                            "emails",
                            f"Você tem {n} emails novos. Fala 'lê os emails' pra ouvir.",
                            "calma",
                            1,
                        )
                        for e in normais_novos:
                            self.ids_vistos.add(e["uid"])

                self.salvar_estado()
            except Exception as e:
                print(f"❌ [Gmail] Erro no daemon: {e}")

            time.sleep(30)


class GmailRuntime:
    """Ponte fina entre o GmailMental e o cerebro principal da Laylay."""

    def __init__(self, mental: GmailMental) -> None:
        self.mental = mental
        self.mental.carregar_estado()
        self.nao_lidos_cache = self.mental.nao_lidos_cache

    def silenciar_remetente(self, remetente: str) -> bool:
        return self.mental.silenciar_remetente(remetente)

    def buscar_nao_lidos(self) -> list:
        emails = self.mental.buscar_nao_lidos()
        self.nao_lidos_cache[:] = emails
        return emails

    def falar_resumo_estiloso(
        self,
        emails: list,
        somente_prioritarios: bool = False,
        *,
        emitir_proativa: bool = True,
    ):
        return self.mental.falar_resumo_estiloso(
            emails,
            somente_prioritarios=somente_prioritarios,
            emitir_proativa=emitir_proativa,
        )

    def resetar_check(self) -> None:
        self.mental.resetar_check()

    def daemon(self) -> None:
        self.mental.daemon()


def criar_gmail_runtime(
    *,
    arquivo_estado: str,
    usuario: str = "",
    app_password: str = "",
    intervalo_s: int = 300,
    max_lidos: int = 5,
    prioritarios: Iterable[str] | None = None,
    palavras_urgentes: Iterable[str] | None = None,
    continuidades_set: Callable[[str, object], None] | None = None,
    agendar_fala_proativa: Callable[[str, str, str, int], None] | None = None,
    is_speaking_getter: Callable[[], bool] | None = None,
    modo_jogo_getter: Callable[[], bool] | None = None,
    categorias: Dict[str, Iterable[str]] | None = None,
) -> GmailRuntime:
    mental = GmailMental(
        arquivo_estado=arquivo_estado,
        usuario=usuario,
        app_password=app_password,
        intervalo_s=intervalo_s,
        max_lidos=max_lidos,
        prioritarios=prioritarios,
        palavras_urgentes=palavras_urgentes,
        continuidades_set=continuidades_set,
        agendar_fala_proativa=agendar_fala_proativa,
        is_speaking_getter=is_speaking_getter,
        modo_jogo_getter=modo_jogo_getter,
        categorias=categorias,
    )
    return GmailRuntime(mental)
