"""Renderer oficial da interface aprovada, sobre o cliente canônico existente.

O HTML empacotado apresenta fatos e solicita operações ao mesmo controlador
PySide6. ID de envio, confirmação de entrada e confirmação de efeito continuam
sendo evidências distintas. Este módulo não interpreta linguagem nem executa
comandos da mente.
"""

from __future__ import annotations

from collections import deque
import json
import os
from pathlib import Path
import re
from typing import Any, TYPE_CHECKING
import uuid

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QObject, QPoint, QRect, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QImage
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings, QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo, QWebEngineUrlScheme, QWebEngineUrlSchemeHandler, QWebEngineUrlRequestJob
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QDialog, QFileDialog, QHBoxLayout, QMainWindow

from mente_laylay.integracao.desktop_bridge import (
    ErroProtocoloDesktop, TIPOS_BACKEND, validar_mensagem_cliente,
)
from mente_laylay.integracao.acoes_terminal import IDS_ACOES_RAPIDAS

if TYPE_CHECKING:
    from cliente.terminal_laylay_2 import JanelaLaylay, PonteWorker


_CHAVES_PRIVADAS = frozenset({"token", "api_key", "authorization", "password", "secret", "credentials", "access_token", "refresh_token"})
_PAGINAS = frozenset({"home", "chat", "music", "system", "settings", "automation", "memory", "streaming", "developer", "lamp", "dev", "inicio", "conversa", "musica", "sistema", "configuracoes", "automacao", "memoria", "desenvolvedor"})
_ESQUEMA_CAPA = b"laylay-playlist-artwork"
_TOKEN_CAPA = re.compile(r"laylay-playlist-artwork://([a-f0-9]{24}\.png)")

# O entrypoint importa este módulo antes de criar QApplication. O esquema
# transporta somente tokens de capas já materializadas pelo owner nativo.
if not QWebEngineUrlScheme.schemeByName(_ESQUEMA_CAPA).name():
    esquema = QWebEngineUrlScheme(_ESQUEMA_CAPA)
    esquema.setSyntax(QWebEngineUrlScheme.Syntax.Host)
    esquema.setFlags(QWebEngineUrlScheme.SecureScheme | QWebEngineUrlScheme.LocalScheme | QWebEngineUrlScheme.LocalAccessAllowed)
    QWebEngineUrlScheme.registerScheme(esquema)


class CapasLocaisV1(QWebEngineUrlSchemeHandler):
    """A mesma cache de capas nativa, sem acesso a caminhos fornecidos pelo JS."""

    def __init__(self, parent: QObject, diretorio: Path | None = None) -> None:
        super().__init__(parent)
        self.diretorio = diretorio or Path.home() / ".laylay" / "playlist_artwork"

    def png(self, url: QUrl) -> bytes:
        token = _TOKEN_CAPA.fullmatch(url.toString())
        if token is None:
            return b""
        try:
            caminho = (self.diretorio / token.group(1)).resolve()
            if not caminho.is_relative_to(self.diretorio.resolve()) or caminho.stat().st_size > 8_000_000:
                return b""
            imagem = QImage(str(caminho))
            if imagem.isNull() or imagem.width() * imagem.height() > 16_000_000:
                return b""
            imagem = imagem.scaled(640, 640, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            dados = QByteArray()
            buffer = QBuffer(dados)
            buffer.open(QIODevice.WriteOnly)
            imagem.save(buffer, "PNG")
            buffer.close()
            return bytes(dados)
        except (OSError, ValueError):
            return b""

    def requestStarted(self, pedido: QWebEngineUrlRequestJob) -> None:  # noqa: N802
        dados = self.png(pedido.requestUrl())
        if not dados or bytes(pedido.requestMethod()) != b"GET":
            pedido.fail(QWebEngineUrlRequestJob.RequestDenied)
            return
        buffer = QBuffer(pedido)
        buffer.setData(dados)
        buffer.open(QIODevice.ReadOnly)
        pedido.reply(b"image/png", buffer)


def _publico(valor: Any) -> Any:
    """Última barreira de segredo; a ponte de runtime já sanitiza os fatos."""
    if isinstance(valor, dict):
        return {str(chave): _publico(item) for chave, item in valor.items()
                if str(chave).casefold() not in _CHAVES_PRIVADAS}
    if isinstance(valor, (list, tuple)):
        return [_publico(item) for item in valor]
    if isinstance(valor, (str, int, float, bool)) or valor is None:
        return valor
    return str(valor)


def _arquivo_bundle(url: QUrl, diretorio: Path) -> bool:
    if not url.isLocalFile():
        return False
    try:
        caminho = Path(url.toLocalFile()).resolve()
        return caminho.is_file() and caminho.is_relative_to(diretorio.resolve())
    except (OSError, ValueError):
        return False


class PoliticaRecursosV1(QWebEngineUrlRequestInterceptor):
    """Somente bundle local, canal Qt e miniaturas públicas do YouTube."""

    def __init__(self, diretorio: Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.diretorio = diretorio

    def permitido(self, url: QUrl, recurso: QWebEngineUrlRequestInfo.ResourceType) -> bool:
        if url.scheme() == "file":
            return _arquivo_bundle(url, self.diretorio)
        if url.scheme() == "qrc":
            return url.path() == "/qtwebchannel/qwebchannel.js"
        if recurso == QWebEngineUrlRequestInfo.ResourceTypeImage:
            if _TOKEN_CAPA.fullmatch(url.toString()):
                return True
            if url.scheme() == "https" and url.host() == "i.ytimg.com" and not url.userInfo():
                return True
            if url.scheme() == "data":
                return url.toString().startswith(("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/webp;base64,"))
        return False

    def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:  # noqa: N802
        info.block(not self.permitido(info.requestUrl(), info.resourceType()))


class PaginaLocalV1(QWebEnginePage):
    def __init__(self, perfil: QWebEngineProfile, diretorio: Path, parent: QObject | None = None) -> None:
        super().__init__(perfil, parent)
        self.diretorio = diretorio
        self.featurePermissionRequested.connect(
            lambda origem, recurso: self.setFeaturePermission(origem, recurso, QWebEnginePage.PermissionDeniedByUser)
        )

    def acceptNavigationRequest(self, url: QUrl, tipo, principal: bool) -> bool:  # noqa: N802
        # Nenhum iframe/navegação remota pode herdar a ponte privilegiada.
        if not principal:
            return False
        return _arquivo_bundle(url, self.diretorio) and Path(url.toLocalFile()).resolve() == (self.diretorio / "index.html").resolve()

    def createWindow(self, tipo):  # noqa: N802
        return None

    def javaScriptConsoleMessage(self, nivel, mensagem, linha, origem) -> None:  # noqa: N802
        # O formulário contém uma credencial transitória. Não copiar o console
        # do renderer para stdout/logs da aplicação.
        return None


class PonteInterfaceWebV1(QObject):
    evento = Signal(str)

    def __init__(self, janela: JanelaInterfaceWebV1, controlador: JanelaLaylay) -> None:
        super().__init__(janela)
        self.janela = janela
        self.controlador = controlador
        self._pronta = False
        self._sequencia = 0
        self._snapshot: tuple[int, dict] | None = None
        self._eventos: deque[tuple[int, dict]] = deque(maxlen=500)
        self._ultimos: dict[str, tuple[int, dict]] = {}
        self._pendentes: dict[str, dict] = {}
        self._ultimo_envio = ""
        self._falhas: deque[str] = deque(maxlen=256)
        controlador.enviar_json.connect(self._registrar_envio)
        controlador.worker.mensagem.connect(self.receber)
        controlador.worker.conectado.connect(self.conexao)
        controlador.worker.falha.connect(lambda _detalhe: self._erro("conexao", "A conexão com a Laylay foi interrompida."))

    def _registrar_envio(self, mensagem: dict) -> None:
        self._ultimo_envio = str(mensagem.get("id") or "")

    def _emitir(self, mensagem: dict) -> None:
        self.evento.emit(json.dumps(_publico(mensagem), ensure_ascii=False, allow_nan=False))

    def publicar(self, mensagem: dict, *, guardar: bool = True) -> None:
        mensagem = _publico(mensagem)
        self._sequencia += 1
        item = (self._sequencia, mensagem)
        tipo = str(mensagem.get("type") or "")
        if guardar:
            if tipo == "snapshot":
                self._snapshot = item
                self._eventos.clear()
                self._ultimos.clear()
            elif tipo in {"state", "dashboard_state", "music_meter", "settings_state", "conexao", "preferencias_ui", "avatar_ui"}:
                self._ultimos[tipo] = item
            elif tipo == "action_state":
                self._ultimos[f"action_state:{mensagem.get('action', mensagem.get('id', ''))}"] = item
            else:
                self._eventos.append(item)
        if self._pronta:
            self._emitir(mensagem)

    @Slot(dict)
    def receber(self, mensagem: dict) -> None:
        if not isinstance(mensagem, dict) or mensagem.get("type") not in TIPOS_BACKEND:
            return
        mensagem_id = str(mensagem.get("id") or "")
        tipo = mensagem.get("type")
        if tipo == "error":
            self._falhas.append(mensagem_id)
        terminal_acao = tipo == "action_state" and mensagem.get("state") in {"confirmed", "partial", "failed"}
        if terminal_acao or tipo == "assistant_message" or (tipo == "input_ack" and not mensagem.get("accepted")) or tipo in {"mode_state", "settings_state", "playlist_result", "settings_result", "restart_result", "dev_query_result", "dev_control_result", "conversations_state", "error"}:
            self._pendentes.pop(mensagem_id, None)
        elif tipo == "input_ack" and mensagem_id in self._pendentes:
            self._pendentes[mensagem_id]["accepted"] = bool(mensagem.get("accepted"))
            self._observar_timeout(mensagem_id)
        self.publicar(mensagem)

    @Slot(bool)
    def conexao(self, conectado: bool) -> None:
        if not conectado:
            for mensagem_id in tuple(self._pendentes):
                self.publicar({"type": "error", "id": mensagem_id, "code": "connection_lost", "message": "A conexão caiu antes da conclusão. Consulte o estado antes de tentar novamente."})
            self._pendentes.clear()
        self.publicar({"type": "conexao", "connected": bool(conectado)})

    @Slot()
    def pronto(self) -> None:
        self._pronta = True
        itens = list(self._eventos) + list(self._ultimos.values())
        self._emitir(self._retrato_atual())
        for _sequencia, mensagem in sorted(itens, key=lambda item: item[0]):
            # O feed e a conversa projetados acima já contêm o histórico
            # atual completo. Não reintroduzir falas de outra conversa nem
            # reaplicar uma listagem antiga por causa do limite do cache.
            if mensagem.get("type") in {"assistant_message", "conversations_state", "pedido_enviado"}:
                continue
            self._emitir(mensagem)
        for mensagem in self._pendentes.values():
            self._emitir(mensagem)
        self._emitir({"type": "conexao", "connected": self.controlador._conectado})
        self._emitir({"type": "preferencias_ui", **self.janela.preferencias_publicas()})
        self._emitir({"type": "apresentacao", "mode": self.janela.modo_apresentacao})
        self.janela.publicar_avatar()

    def _retrato_atual(self) -> dict:
        from cliente.terminal_laylay_2 import MensagemWidget

        retrato = dict(self._snapshot[1]) if self._snapshot is not None else {"type": "snapshot"}
        mensagens = []
        for indice in range(self.controlador.feed_lay.count()):
            linha = self.controlador.feed_lay.itemAt(indice).widget()
            if linha is None:
                continue
            for mensagem in linha.findChildren(MensagemWidget):
                mensagens.append({"role": mensagem.papel, "text": mensagem.texto,
                                  "id": mensagem.mensagem_id, "status": mensagem.status.property("delivery") or "accepted"})
        retrato["messages"] = mensagens
        retrato["state"] = dict(self.controlador._estado_mais_recente or retrato.get("state") or {})
        retrato["dashboard"] = dict(self.controlador._dashboard_mais_recente or {})
        retrato["settings"] = dict(self.controlador.configuracoes._estado or retrato.get("settings") or {})
        conversas = dict(retrato.get("conversations") or {})
        conversas.update(active_id=self.controlador._conversa_ativa_id, items=list(self.controlador._conversas))
        retrato["conversations"] = conversas
        return _publico(retrato)

    def _observar_timeout(self, mensagem_id: str) -> None:
        timer = self.controlador._timeouts_envio.get(mensagem_id)
        if timer is None or timer.property("v1Observado"):
            return
        timer.setProperty("v1Observado", True)
        timer.timeout.connect(lambda mid=mensagem_id: self._timeout_observado(mid))

    def _timeout_observado(self, mensagem_id: str) -> None:
        if mensagem_id not in self._pendentes:
            return
        self._pendentes.pop(mensagem_id, None)
        self.publicar({"type": "error", "id": mensagem_id, "code": "ui_timeout", "message": "O pedido excedeu o tempo de espera. Confira o estado antes de tentar novamente."})

    @Slot(str)
    def apresentar(self, modo: str) -> None:
        self.janela.apresentar(modo)

    @Slot()
    def arrastar(self) -> None:
        """Gesto de janela, solicitado pela área livre do cabeçalho compacto."""
        if self.janela.modo_apresentacao != "full":
            handle = self.janela.windowHandle()
            if handle is not None:
                handle.startSystemMove()

    def _erro(self, tipo: str, mensagem: str) -> str:
        self.publicar({"type": "erro_interface", "tipo": tipo, "message": mensagem}, guardar=False)
        return ""

    @staticmethod
    def _validar(mensagem: dict) -> dict:
        return validar_mensagem_cliente(mensagem, token="", autenticado=True)

    @Slot(str, str, result=str)
    def solicitar(self, tipo: str, dados_json: str) -> str:
        try:
            if len(dados_json) > 65536:
                raise ValueError("Pedido acima do limite.")
            dados = json.loads(dados_json)
            if not isinstance(dados, dict):
                raise ValueError("O pedido precisa ser um objeto.")
            permitidos = {
                "texto": {"text"}, "voz": {"mode"}, "acao": {"action", "request", "payload"},
                "playlist": {"operation", "playlist", "query", "offset", "limit", "video_id", "revision", "destination", "destinations", "url"},
                "configuracao_obter": set(), "configuracao_salvar": {"provider", "model", "api_key_action", "api_key", "mascot_enabled"},
                "reiniciar": set(), "conversa": {"operation", "conversation_id", "title", "pinned"},
                "dev_consulta": {"command"}, "dev_controle": {"command"},
                "pagina": {"name"}, "preferencia": {"name", "value"}, "streaming": {"operation"},
            }
            if tipo not in permitidos or set(dados) - permitidos[tipo]:
                raise ValueError("Pedido ou campos não reconhecidos pela interface.")
            if tipo in {"pagina", "preferencia", "streaming"}:
                return self._local(tipo, dados)
            if not self.controlador._conectado:
                raise ValueError("A Laylay está reconectando. Aguarde a conexão para enviar.")
            self._ultimo_envio = ""
            anteriores = set(self.controlador._envios) | set(self.controlador._acoes_por_envio)
            resultado = self._operacional(tipo, dados)
            novos = (set(self.controlador._envios) | set(self.controlador._acoes_por_envio)) - anteriores
            requisicao_id = resultado or self._ultimo_envio or (next(iter(novos)) if novos else "")
            if requisicao_id in self._falhas:
                return ""
            if requisicao_id:
                pedido = {"type": "pedido_enviado", "id": requisicao_id, "kind": tipo, "conversation_id": self.controlador._conversa_ativa_id}
                if tipo == "texto":
                    pedido["text"] = str(dados.get("text") or "")
                if tipo == "acao":
                    pedido["action"] = str(dados.get("action") or "")
                self._pendentes[requisicao_id] = pedido
                self._observar_timeout(requisicao_id)
                self.publicar(pedido)
            return requisicao_id
        except (ValueError, TypeError, KeyError, ErroProtocoloDesktop):
            # Nunca incluir dados_json em erro: pode conter uma API key.
            return self._erro(tipo, "O pedido não foi enviado. Verifique os campos e a conexão com a Laylay.")

    def _operacional(self, tipo: str, dados: dict) -> str:
        controlador = self.controlador
        if tipo == "texto":
            validado = self._validar({"type": "input_submit", "kind": "chat", "text": dados.get("text")})
            controlador.enviar_texto(validado["text"])
        elif tipo == "voz":
            validado = self._validar({"type": "mode_set", "mode": dados.get("mode")})
            if validado["mode"] == "voice" and not controlador._voz_disponivel:
                raise ValueError("Voz indisponível.")
            controlador.solicitar_modo(validado["mode"])
        elif tipo == "acao":
            rapida = dados.get("action") in IDS_ACOES_RAPIDAS
            if rapida and dados.get("payload"):
                raise ValueError("Ação rápida não recebe parâmetros de painel.")
            validado = self._validar({"type": "input_submit", "kind": "quick_action" if rapida else "panel_action", "action": dados.get("action"), "text": dados.get("request"), "payload": dados.get("payload", {})})
            if rapida:
                controlador.enviar_acao_rapida(validado["action"], validado["text"])
            else:
                controlador.enviar_acao_painel_com_dados(validado["action"], validado["text"], validado["payload"])
        elif tipo == "playlist":
            parametros = dict(dados)
            if parametros.get("operation") == "set_artwork":
                caminho, _filtro = QFileDialog.getOpenFileName(self.janela, "Escolher capa da playlist", "", "Imagens (*.png *.jpg *.jpeg *.webp)")
                if not caminho:
                    return ""
                parametros["path"] = caminho
            requisicao_id = uuid.uuid4().hex
            validado = self._validar({"type": "playlist_request", "id": requisicao_id, **parametros})
            controlador.enviar_requisicao_playlist({chave: valor for chave, valor in validado.items() if chave != "type"})
            return requisicao_id
        elif tipo == "configuracao_obter":
            controlador.enviar_json.emit({"type": "settings_get", "id": uuid.uuid4().hex})
        elif tipo == "configuracao_salvar":
            if dados.get("provider") not in {"ollama", "portatil", "openrouter"} or dados.get("api_key_action", "preserve") not in {"preserve", "replace", "remove"}:
                raise ValueError("Configuração inválida.")
            validado = self._validar({"type": "settings_update", "settings": dados})
            controlador.salvar_configuracoes(validado["settings"])
        elif tipo == "reiniciar":
            controlador.reiniciar_laylay()
        elif tipo == "conversa":
            operacao = str(dados.get("operation") or "")
            nomes = {"create": "conversation_create", "select": "conversation_select", "rename": "conversation_rename", "pin": "conversation_pin", "archive": "conversation_archive", "unarchive": "conversation_unarchive", "delete": "conversation_delete"}
            validado = self._validar({"type": nomes[operacao], **{chave: valor for chave, valor in dados.items() if chave != "operation"}})
            conversa_id = validado.get("conversation_id", "")
            if operacao == "create":
                controlador._enviar_requisicao_conversa("conversation_create", title=validado.get("title") or "Nova conversa")
            elif operacao == "select":
                controlador.selecionar_conversa(conversa_id)
            elif operacao == "rename":
                controlador._enviar_requisicao_conversa("conversation_rename", conversation_id=conversa_id, title=validado["title"])
            elif operacao == "pin":
                controlador.fixar_conversa(conversa_id, validado["pinned"])
            elif operacao == "archive":
                controlador.arquivar_conversa(conversa_id)
            elif operacao == "unarchive":
                controlador.restaurar_conversa(conversa_id)
            else:
                controlador.excluir_conversa_confirmada(conversa_id)
        elif tipo in {"dev_consulta", "dev_controle"}:
            comando = str(dados.get("command") or "")
            protocolo = "dev_query" if tipo == "dev_consulta" else "dev_control"
            validado = self._validar({"type": protocolo, "command": comando, "authorized": tipo == "dev_controle"})
            controlador._garantir_pagina_carregada("desenvolvedor")
            if tipo == "dev_consulta":
                controlador.enviar_consulta_desenvolvedor(validado["command"])
            else:
                controlador.enviar_controle_desenvolvedor(validado["command"])
        return ""

    def _local(self, tipo: str, dados: dict) -> str:
        if tipo == "pagina":
            nome = str(dados.get("name") or "")
            if nome not in _PAGINAS:
                raise ValueError("Página desconhecida.")
            if nome != "streaming":
                self.janela.parar_streaming()
            if nome in {"settings", "configuracoes"} and self.controlador._conectado:
                self.controlador.enviar_json.emit({"type": "settings_get", "id": uuid.uuid4().hex})
            return uuid.uuid4().hex
        if tipo == "preferencia":
            self.janela.definir_preferencia(str(dados.get("name") or ""), dados.get("value"))
            return uuid.uuid4().hex
        operacao = str(dados.get("operation") or "")
        if operacao in {"abrir", "open"}:
            self.janela.abrir_streaming()
        elif operacao in {"parar", "stop", "fechar", "close"}:
            self.janela.parar_streaming()
        else:
            raise ValueError("Operação local desconhecida.")
        return uuid.uuid4().hex


class JanelaInterfaceWebV1(QMainWindow):
    def __init__(self, worker: PonteWorker, raiz: Path, *, session_id: str = "", parent_pid: int = 0, diretorio_web: Path | None = None) -> None:
        super().__init__()
        # Importação tardia evita ciclo: o entrypoint existente importa esta
        # janela somente depois de definir seu controlador canônico.
        from cliente.terminal_laylay_2 import JanelaLaylay

        self.worker = worker
        self.controlador = JanelaLaylay(worker, raiz, session_id=session_id, parent_pid=parent_pid)
        self.controlador.hide()
        self.preferencias = self.controlador.preferencias
        self.diretorio_web = (diretorio_web or Path(__file__).with_name("web_v1")).resolve()
        self._streaming_dialogo: QDialog | None = None
        self._streaming_pagina = None
        self._fechada = False
        self.modo_apresentacao = "full"
        self._geometria_completa = QRect(100, 100, 1440, 900)
        self._estado_completo = Qt.WindowNoState
        self._flags_completa = self.windowFlags()
        self.setWindowTitle("Laylay — Interface 1.0")
        self.setMinimumSize(375, 620)
        self.resize(1440, 900)
        self.web = QWebEngineView(self)
        self.web.setContextMenuPolicy(Qt.NoContextMenu)
        self.setCentralWidget(self.web)
        self.perfil = QWebEngineProfile(self)
        self.perfil.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        self.perfil.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
        self.capas_locais = CapasLocaisV1(self.perfil)
        self.perfil.installUrlSchemeHandler(_ESQUEMA_CAPA, self.capas_locais)
        self.politica_recursos = PoliticaRecursosV1(self.diretorio_web, self.perfil)
        self.perfil.setUrlRequestInterceptor(self.politica_recursos)
        self.perfil.downloadRequested.connect(lambda download: download.cancel())
        self.pagina_web = PaginaLocalV1(self.perfil, self.diretorio_web, self.web)
        self.web.setPage(self.pagina_web)
        self.canal = QWebChannel(self.pagina_web)
        self.ponte_web = PonteInterfaceWebV1(self, self.controlador)
        self.canal.registerObject("laylay", self.ponte_web)
        self.pagina_web.setWebChannel(self.canal)
        configuracoes = self.pagina_web.settings()
        for atributo in (QWebEngineSettings.JavascriptCanOpenWindows, QWebEngineSettings.JavascriptCanAccessClipboard, QWebEngineSettings.LocalStorageEnabled, QWebEngineSettings.PluginsEnabled, QWebEngineSettings.FullScreenSupportEnabled):
            configuracoes.setAttribute(atributo, False)
        configuracoes.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        # O interceptor permite exclusivamente miniaturas; scripts, frames,
        # fetch/XHR e demais origens remotas continuam bloqueados.
        configuracoes.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        self.web.loadStarted.connect(self._carregando)
        self.web.setUrl(QUrl.fromLocalFile(str(self.diretorio_web / "index.html")))

    def _carregando(self) -> None:
        self.ponte_web._pronta = False

    def preferencias_publicas(self) -> dict:
        ambiente = os.environ.get("LAYLAY_REDUZIR_MOVIMENTO", "").casefold() in {"1", "true", "sim", "yes", "on"}
        return {"reduced": ambiente or bool(self.preferencias.value("v1/reduzir_movimento", False, type=bool)),
                "mascot": bool(self.preferencias.value("v1/mascote_integrado", True, type=bool)),
                "accent": str(self.preferencias.value("v1/cor", "violet")),
                "sidebar": bool(self.preferencias.value("sidebar_expandida", True, type=bool))}

    def definir_preferencia(self, nome: str, valor: Any) -> None:
        chaves = {"reduzir_movimento": "v1/reduzir_movimento", "mascote": "v1/mascote_integrado", "cor": "v1/cor", "sidebar": "sidebar_expandida"}
        if nome == "avatar" and valor == "selecionar":
            self.controlador.configuracoes._selecionar_avatar()
            self.publicar_avatar()
            return
        if nome not in chaves or (nome == "cor" and valor not in {"violet", "cyan", "rose"}) or (nome != "cor" and not isinstance(valor, bool)):
            raise ValueError("Preferência desconhecida.")
        self.preferencias.setValue(chaves[nome], valor)
        self.preferencias.sync()
        self.ponte_web.publicar({"type": "preferencias_ui", **self.preferencias_publicas()})

    def publicar_avatar(self) -> None:
        caminho = self.controlador._avatar_usuario_path
        if not caminho:
            return
        imagem = QImage(caminho)
        if imagem.isNull():
            return
        imagem = imagem.scaled(192, 192, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        dados = QByteArray()
        buffer = QBuffer(dados)
        buffer.open(QIODevice.WriteOnly)
        imagem.save(buffer, "PNG")
        buffer.close()
        self.ponte_web.publicar({"type": "avatar_ui", "data_url": "data:image/png;base64," + bytes(dados.toBase64()).decode("ascii")})

    @Slot(str)
    def apresentar(self, modo: str) -> None:
        if modo not in {"full", "quick", "island"} or modo == self.modo_apresentacao:
            return
        visivel = self.isVisible()
        if self.modo_apresentacao == "full":
            self._geometria_completa = QRect(self.normalGeometry() if self.isMaximized() else self.geometry())
            self._estado_completo = self.windowState()
            self._flags_completa = self.windowFlags()
        self.parar_streaming()
        self.modo_apresentacao = modo
        flags = self._flags_completa if modo == "full" else self._flags_completa | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setWindowState(Qt.WindowNoState)
        disponivel = self.screen().availableGeometry()
        if modo == "full":
            self.setMinimumSize(375, 620)
            desejada = QRect(self._geometria_completa)
        else:
            self.setMinimumSize(240, 70) if modo == "island" else self.setMinimumSize(320, 420)
            largura, altura = (330, 86) if modo == "island" else (450, 700)
            desejada = QRect(disponivel.center().x() - largura // 2, disponivel.top() + 10, largura, altura)
        largura, altura = min(desejada.width(), disponivel.width()), min(desejada.height(), disponivel.height())
        x = min(max(desejada.x(), disponivel.left()), disponivel.right() - largura + 1)
        y = min(max(desejada.y(), disponivel.top()), disponivel.bottom() - altura + 1)
        self.setGeometry(QRect(x, y, largura, altura))
        if visivel:
            self.showMaximized() if modo == "full" and self._estado_completo & Qt.WindowMaximized else self.show()
        self.ponte_web.publicar({"type": "apresentacao", "mode": modo})

    def abrir_streaming(self) -> None:
        if self._streaming_dialogo is None:
            from cliente.terminal_2.streaming import PaginaStreaming
            self._streaming_dialogo = QDialog(self)
            self._streaming_dialogo.setWindowTitle("Laylay — Player de Streaming local")
            self._streaming_dialogo.resize(1100, 730)
            lay = QHBoxLayout(self._streaming_dialogo)
            lay.setContentsMargins(0, 0, 0, 0)
            self._streaming_pagina = PaginaStreaming(self._streaming_dialogo)
            lay.addWidget(self._streaming_pagina)
            self._streaming_dialogo.finished.connect(lambda _codigo: self._streaming_pagina.encerrar())
        self._streaming_dialogo.show()
        self._streaming_dialogo.raise_()
        self._streaming_dialogo.activateWindow()

    def parar_streaming(self) -> None:
        if self._streaming_dialogo is not None:
            self._streaming_pagina.encerrar()
            self._streaming_dialogo.hide()

    def closeEvent(self, evento) -> None:  # noqa: N802
        if not self._fechada:
            self._fechada = True
            if self._streaming_pagina is not None:
                self._streaming_pagina.fechar()
                self._streaming_dialogo.close()
            self.ponte_web._pronta = False
            self.web.stop()
            self.pagina_web.setWebChannel(None)
            self.controlador.close()
        evento.accept()
