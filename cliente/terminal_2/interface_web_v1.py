"""Renderer oficial da interface aprovada, sobre o cliente canônico existente.

O HTML empacotado apresenta fatos e solicita operações ao mesmo controlador
PySide6. ID de envio, confirmação de entrada e confirmação de efeito continuam
sendo evidências distintas. Este módulo não interpreta linguagem nem executa
comandos da mente.
"""

from __future__ import annotations

from collections import deque
import json
import math
import os
from pathlib import Path
import re
from typing import Any, TYPE_CHECKING
import uuid

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QObject, QPoint, QRect, Qt, QUrl, QUrlQuery, Signal, Slot, QTimer, QPropertyAnimation, QEasingCurve, QEvent
from PySide6.QtGui import QImage, QColor, QCursor, QPainterPath, QRegion, QIcon, QPixmap, QPainter, QAction, QGuiApplication
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings, QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo, QWebEngineUrlScheme, QWebEngineUrlSchemeHandler, QWebEngineUrlRequestJob
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QDialog, QFileDialog, QMainWindow, QSystemTrayIcon, QMenu, QApplication, QScrollArea, QWidget, QLabel, QPushButton

from cliente.terminal_2.apresentacao_desktop import geometria_desktop, permitir_ativacao_desktop, botao_esquerdo_pressionado
from cliente.terminal_2.material_windows import aplicar_material_windows, restaurar_material_windows

from mente_laylay.integracao.desktop_bridge import (
    ErroProtocoloDesktop, TIPOS_BACKEND, validar_mensagem_cliente,
)
from mente_laylay.integracao.acoes_terminal import IDS_ACOES_RAPIDAS

if TYPE_CHECKING:
    from cliente.terminal_laylay_2 import JanelaLaylay, PonteWorker


_CHAVES_PRIVADAS = frozenset({"token", "api_key", "authorization", "password", "secret", "credentials", "access_token", "refresh_token"})
_PAGINAS = frozenset({"home", "chat", "music", "system", "settings", "automation", "memory", "streaming", "developer", "lamp", "dev", "inicio", "conversa", "musica", "sistema", "configuracoes", "automacao", "memoria", "desenvolvedor"})
_PAGINAS_DESKTOP = {nome: nome for nome in ('home', 'chat', 'music', 'system', 'settings', 'memory', 'streaming', 'lamp', 'dev')}
_PAGINAS_DESKTOP.update(inicio='home', conversa='chat', musica='music', sistema='system', configuracoes='settings', memoria='memory', automacao='lamp', automation='lamp', desenvolvedor='dev', developer='dev')
_ESQUEMA_CAPA = b"laylay-playlist-artwork"
# Chromium normaliza o host com caminho raiz; ambas as formas são o mesmo
# token fechado. Caminhos adicionais, query e fragmento continuam recusados.
_TOKEN_CAPA = re.compile(r"laylay-playlist-artwork://([a-f0-9]{24}\.png)/?")


def _preferencia_inicio(valor: Any) -> dict:
    """Preferência visual não é alvo autorizado nem comando operacional."""
    if (not isinstance(valor, dict)
            or set(valor) != {'version', 'period_days', 'pinned_ids', 'hidden_ids'}
            or type(valor['version']) is not int or valor['version'] != 1
            or type(valor['period_days']) is not int or valor['period_days'] not in {7, 30}):
        raise ValueError('Preferência do Início inválida.')
    resultado = {'version': 1, 'period_days': valor['period_days']}
    for chave in ('pinned_ids', 'hidden_ids'):
        itens = valor[chave]
        if not isinstance(itens, list) or len(itens) > 32:
            raise ValueError('Lista de preferências inválida.')
        if any(not isinstance(item, str) or not 1 <= len(item) <= 180
               or item != item.strip() or re.search(r'[\x00-\x1f\x7f]', item)
               or not ((item.startswith('playlist:') and item[9:].strip())
                       or (item.startswith('action:') and item[7:].strip())
                       or item == 'moment:context_music') for item in itens):
            raise ValueError('Referência visual inválida.')
        resultado[chave] = list(dict.fromkeys(itens))
    return resultado

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
            elif tipo in {"state", "dashboard_state", "music_meter", "settings_state", "conexao", "preferencias_ui", "avatar_ui", "apresentacao"}:
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
        self._emitir(self.janela.apresentacao_publica())
        self.janela.publicar_avatar()
        self.janela.renderer_pronto()

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

    @Slot(str)
    def navegar_desktop(self, pagina: str) -> None:
        if pagina in _PAGINAS:
            self._local('pagina', {'name': pagina})

    @Slot(str)
    def gesto_desktop(self, gesto: str) -> None:
        if gesto == 'streaming-voltar':
            self.janela._ampliar_streaming(False)
            return
        if self.janela.modo_apresentacao != 'desktop':
            return
        if gesto == 'expandir':
            if self.janela.desktop_pagina is None:
                self.janela.selecionar_pagina_desktop('home')
            else:
                self.janela.expandir_desktop(fixar=True)
            self.janela.ativar_desktop()
        elif gesto == 'recolher':
            self.janela.recolher_desktop()
        elif gesto == 'interagir':
            self.janela._desktop_transitorio = False
            self.janela._recolher_desktop_timer.stop()
            self.janela.ativar_desktop()
        elif gesto == 'resumo':
            self.janela.desktop_pagina = None
            self.janela.expandir_desktop(fixar=True)

    @Slot(bool)
    def edicao_desktop(self, ocupada: bool) -> None:
        self.janela._desktop_edicao = ocupada

    @Slot(str)
    def atividade_desktop(self, tipo: str) -> None:
        if tipo in {'pointerdown', 'pointermove', 'wheel', 'keydown', 'input', 'compositionstart', 'compositionend'}:
            self.janela.registrar_atividade_desktop()

    @Slot(bool)
    def composicao_desktop(self, ativa: bool) -> None:
        self.janela._desktop_compondo = ativa

    @Slot(str, result=bool)
    def viewport_streaming(self, dados: str) -> bool:
        return self.janela.definir_viewport_streaming(dados)

    @Slot(int, int, int)
    def transicao_pronta(self, sequencia: int, largura: int, altura: int) -> None:
        self.janela.confirmar_transicao_desktop(sequencia, largura, altura)

    @Slot()
    def arrastar(self) -> None:
        """Gesto de janela, solicitado pela área livre do cabeçalho compacto."""
        if self.janela.modo_apresentacao == 'desktop':
            self.arrastar_desktop()
            return
        if self.janela.modo_apresentacao != "full":
            handle = self.janela.windowHandle()
            if handle is not None:
                handle.startSystemMove()

    @Slot()
    @Slot(int, int)
    def arrastar_desktop(self, deslocamento_x: int = 0, deslocamento_y: int = 0) -> None:
        if not botao_esquerdo_pressionado():
            return
        self.janela.iniciar_arrasto_desktop()
        if self.janela._arrastando_desktop:
            self.janela._arrasto_cursor_origem -= QPoint(deslocamento_x, deslocamento_y)
            self.janela.atualizar_arrasto_desktop()

    @Slot()
    def finalizar_arrasto_desktop(self) -> None:
        self.janela.finalizar_arrasto_desktop()

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
            self.janela._pagina_web_ativa = _PAGINAS_DESKTOP[nome]
            if nome != "streaming":
                self.janela.parar_streaming()
            if nome in {"settings", "configuracoes"} and self.controlador._conectado:
                self.controlador.enviar_json.emit({"type": "settings_get", "id": uuid.uuid4().hex})
            if self.janela.modo_apresentacao == 'desktop':
                self.janela.selecionar_pagina_desktop(nome)
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
    encerrada = Signal()

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
        self._streaming_host: QScrollArea | None = None
        self._streaming_aberto = False
        self._streaming_ampliado = False
        self._pagina_web_ativa = 'home'
        self._fechada = False
        self.modo_apresentacao = "full"
        self._registro_posicao_desktop = self._ler_posicao_desktop()
        self._ancora_desktop: QPoint | None = None
        self._arrastando_desktop = False
        self._arrasto_cursor_origem = QPoint()
        self._arrasto_geometria_origem = QRect()
        self._arrasto_mudou = False
        self._arrasto_tela: dict | None = None
        self._arrasto_timer = QTimer(self)
        self._arrasto_timer.setInterval(16)
        self._arrasto_timer.setTimerType(Qt.PreciseTimer)
        self._arrasto_timer.timeout.connect(self.atualizar_arrasto_desktop)
        self._geometria_completa = QRect(100, 100, 1440, 900)
        self._estado_completo = Qt.WindowNoState
        self._flags_completa = self.windowFlags()
        self.estado_desktop = 'compact'
        self.desktop_pagina: str | None = None
        self.desktop_fixado = False
        self._desktop_transitorio = False
        self._desktop_edicao = False
        self._desktop_compondo = False
        self._desktop_adiamentos = 0
        self._desktop_dentro = False
        self._ultimo_cursor_desktop = None
        self._ultimo_cursor_global = None
        self._telas_observadas = set()
        self._animacao_desktop = QPropertyAnimation(self, b'geometry', self)
        self._animacao_desktop.setEasingCurve(QEasingCurve.OutCubic)
        self._animacao_desktop.setDuration(230)
        self._animacao_desktop.finished.connect(self._geometria_desktop_concluida)
        self._desktop_fase = 'idle'
        self._desktop_sequencia = 0
        self._desktop_destino = QRect()
        self._transicao_cobertura: QLabel | None = None
        # A cobertura já esconde a WebView no resize; não gastar pintura de
        # Chromium em cada tamanho intermediário da janela.
        self._web_pintura_congelada = False
        self._entrada_pendente = False
        self._entrada_exibida = False
        self._desktop_entrada_ativa = False
        self._entrada_visual_timer = QTimer(self)
        self._entrada_visual_timer.setSingleShot(True)
        self._entrada_visual_timer.setInterval(840)
        self._entrada_visual_timer.timeout.connect(self._concluir_entrada_visual)
        self._erro_entrada: QPushButton | None = None
        self._prazo_entrada = QTimer(self)
        self._prazo_entrada.setSingleShot(True)
        self._prazo_entrada.setInterval(5000)
        self._prazo_entrada.timeout.connect(self._entrada_indisponivel)
        self._animacao_entrada = QPropertyAnimation(self, b'windowOpacity', self)
        self._animacao_entrada.setDuration(235)
        self._animacao_entrada.setEasingCurve(QEasingCurve.OutCubic)
        self._foco_desktop_observado = False
        self._recolher_foco_timer = QTimer(self)
        self._recolher_foco_timer.setSingleShot(True)
        self._recolher_foco_timer.setInterval(350)
        self._recolher_foco_timer.timeout.connect(self._recolher_por_perda_de_foco)
        self._inatividade_desktop_timer = QTimer(self)
        self._inatividade_desktop_timer.setSingleShot(True)
        self._inatividade_desktop_timer.setInterval(20_000)
        self._inatividade_desktop_timer.setTimerType(Qt.PreciseTimer)
        self._inatividade_desktop_timer.timeout.connect(self._recolher_por_inatividade)
        self._recolher_desktop_timer = QTimer(self)
        self._recolher_desktop_timer.setSingleShot(True)
        self._recolher_desktop_timer.setInterval(750)
        self._recolher_desktop_timer.timeout.connect(self._recolher_desktop_transitorio)
        self._abrir_desktop_timer = QTimer(self)
        self._abrir_desktop_timer.setSingleShot(True)
        self._abrir_desktop_timer.setInterval(200)
        # Mantido como handle local legado; hover não possui transição de abrir.
        self._cursor_desktop_timer = QTimer(self)
        self._cursor_desktop_timer.setInterval(40)
        self._cursor_desktop_timer.timeout.connect(self._observar_cursor_desktop)
        self._tray = None
        self._material_desktop = 'fallback'
        # A ilha compacta precisa de transparência; o painel expandido, não.
        # Pintar o fundo do painel também no host evita blocos do Windows atrás
        # vazarem durante frames atrasados do WebEngine acelerado por GPU.
        self._fundo_desktop_opaco = False
        self._cor_fundo_desktop = QColor('#10141b')
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("Laylay — Interface 1.0")
        self.setMinimumSize(375, 620)
        self.resize(1440, 900)
        self.web = QWebEngineView(self)
        self.web.setAttribute(Qt.WA_TranslucentBackground, True)
        self.web.setStyleSheet('background:transparent')
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
        self.pagina_web.setBackgroundColor(QColor(Qt.transparent))
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
        self.web.loadFinished.connect(lambda ok: self._entrada_indisponivel() if not ok and self._entrada_pendente else None)
        QApplication.instance().installEventFilter(self)
        QGuiApplication.instance().screenAdded.connect(self._tela_desktop_adicionada)
        QGuiApplication.instance().screenRemoved.connect(lambda _tela: self._reancorar_desktop())
        QTimer.singleShot(0, self._carregar_interface)

    def _carregar_interface(self) -> None:
        if self._fechada:
            return
        endereco = QUrl.fromLocalFile(str(self.diretorio_web / 'index.html'))
        query = QUrlQuery()
        query.addQueryItem('presentation', self.modo_apresentacao)
        endereco.setQuery(query)
        self.web.setUrl(endereco)

    def _carregando(self) -> None:
        self.ponte_web._pronta = False

    def _ler_posicao_desktop(self) -> dict | None:
        try:
            registro = json.loads(str(self.preferencias.value('v1/desktop_posicao', '') or ''))
            if not isinstance(registro, dict) or type(registro.get('version')) is not int or registro.get('version') != 1:
                return None
            tela, offsets = registro['screen'], registro['offsets']
            if not isinstance(tela, dict) or any(not isinstance(tela.get(k), str) or len(tela[k]) > 256 for k in ('name', 'manufacturer', 'model', 'serial')):
                return None
            valores = [offsets[k] for k in ('center_x', 'top_y')]
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or abs(v) > 1_000_000 for v in valores):
                return None
            return registro
        except (ValueError, TypeError, KeyError, OverflowError):
            return None

    @staticmethod
    def _identidade_tela(tela) -> dict:
        return {'name': tela.name(), 'manufacturer': tela.manufacturer(), 'model': tela.model(), 'serial': tela.serialNumber()}

    def _resolver_tela_desktop(self):
        telas = list(QGuiApplication.screens())
        if not telas:
            return None
        identidade = self._arrasto_tela if self._arrastando_desktop else (self._registro_posicao_desktop or {}).get('screen')
        if identidade:
            def pontuar(tela):
                atual = self._identidade_tela(tela)
                return sum(peso for chave, peso in [('serial', 8), ('name', 4), ('manufacturer', 1), ('model', 1)] if identidade.get(chave) and atual.get(chave) == identidade[chave])
            escolhida = max(telas, key=pontuar)
            if pontuar(escolhida):
                return escolhida
        primaria = QGuiApplication.primaryScreen()
        return primaria if primaria in telas else telas[0]

    @property
    def ancora_desktop(self) -> QPoint:
        if self._ancora_desktop is not None:
            return QPoint(self._ancora_desktop)
        tela = self._resolver_tela_desktop()
        area = tela.availableGeometry() if tela is not None else QRect(0, 0, 800, 600)
        if self._registro_posicao_desktop:
            offsets = self._registro_posicao_desktop['offsets']
            return QPoint(area.left() + round(offsets['center_x']), area.top() + round(offsets['top_y']))
        compacta = geometria_desktop(area)
        return QPoint(compacta.center().x(), compacta.top())

    @ancora_desktop.setter
    def ancora_desktop(self, ponto: QPoint) -> None:
        self._ancora_desktop = QPoint(ponto)

    def _ancora_para_geometria(self) -> QPoint | None:
        return self.ancora_desktop if self._ancora_desktop is not None or self._registro_posicao_desktop is not None else None

    def iniciar_apresentacao(self) -> None:
        """Entrada única: nenhuma moldura antiga fica visível antes do renderer."""
        if self.modo_apresentacao != 'desktop' or self._entrada_exibida:
            self.show()
            return
        self._entrada_pendente = True
        self._desktop_fase = 'starting'
        self._desktop_destino = QRect(self.geometry())
        self._desktop_sequencia += 1
        self.setWindowOpacity(0)
        self.show()
        self._prazo_entrada.start()
        if self.ponte_web._pronta:
            self.renderer_pronto()

    def renderer_pronto(self) -> None:
        if self._entrada_pendente:
            self.ponte_web.publicar(self.apresentacao_publica())

    def _entrada_indisponivel(self) -> None:
        if not self._entrada_pendente or self._fechada:
            return
        self._entrada_pendente = False
        self._prazo_entrada.stop()
        self.setWindowOpacity(1)
        self._desktop_fase = 'idle'
        if self._erro_entrada is None:
            self._erro_entrada = QPushButton('Interface indisponível · Tentar novamente', self)
            self._erro_entrada.setStyleSheet('background:#11151e;color:#d5c0ed;border:1px solid #4d3b61;border-radius:20px;font-size:10px')
            self._erro_entrada.clicked.connect(self._tentar_entrada_novamente)
        self._erro_entrada.setGeometry(self.rect())
        self._erro_entrada.show()
        self._erro_entrada.raise_()

    def _tentar_entrada_novamente(self) -> None:
        if self._erro_entrada is not None:
            self._erro_entrada.hide()
        self._entrada_pendente = True
        self._desktop_fase = 'starting'
        self._desktop_sequencia += 1
        self.setWindowOpacity(0)
        self._prazo_entrada.start()
        self.web.reload()

    def preferencias_publicas(self) -> dict:
        ambiente = os.environ.get("LAYLAY_REDUZIR_MOVIMENTO", "").casefold() in {"1", "true", "sim", "yes", "on"}
        home = {'version': 1, 'period_days': 30, 'pinned_ids': [], 'hidden_ids': []}
        try:
            home = _preferencia_inicio(json.loads(str(self.preferencias.value('v1/inicio_inteligente', '') or '')))
        except (ValueError, TypeError, KeyError):
            pass
        return {"reduced": ambiente or bool(self.preferencias.value("v1/reduzir_movimento", False, type=bool)),
                "mascot": bool(self.preferencias.value("v1/mascote_integrado", True, type=bool)),
                "accent": str(self.preferencias.value("v1/cor", "violet")),
                "desktop_start": bool(self.preferencias.value("v1/iniciar_no_desktop", True, type=bool)),
                "sidebar": bool(self.preferencias.value("sidebar_expandida", True, type=bool)),
                "home": home}

    def definir_preferencia(self, nome: str, valor: Any) -> None:
        if nome == 'inicio_inteligente':
            inicio = _preferencia_inicio(valor)
            self.preferencias.setValue('v1/inicio_inteligente', json.dumps(inicio, ensure_ascii=False, separators=(',', ':')))
            self.preferencias.sync()
            self.ponte_web.publicar({'type': 'preferencias_ui', **self.preferencias_publicas()})
            return
        chaves = {"reduzir_movimento": "v1/reduzir_movimento", "mascote": "v1/mascote_integrado", "cor": "v1/cor", "sidebar": "sidebar_expandida", "iniciar_no_desktop": "v1/iniciar_no_desktop"}
        if nome == "avatar" and valor == "selecionar":
            self.controlador.configuracoes._selecionar_avatar()
            self.publicar_avatar()
            return
        if nome not in chaves or (nome == "cor" and valor not in {"violet", "cyan", "rose"}) or (nome != "cor" and not isinstance(valor, bool)):
            raise ValueError("Preferência desconhecida.")
        self.preferencias.setValue(chaves[nome], valor)
        self.preferencias.sync()
        self.ponte_web.publicar({"type": "preferencias_ui", **self.preferencias_publicas()})
        if nome == 'reduzir_movimento' and self.modo_apresentacao == 'desktop':
            self._animar_geometria_desktop()

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

    def apresentacao_publica(self) -> dict:
        tela = self._resolver_tela_desktop()
        disponivel = tela.availableGeometry() if tela is not None else QRect(0, 0, 800, 600)
        return {
            "type": "apresentacao", "mode": self.modo_apresentacao,
            "native_window": True,
            "available_width": disponivel.width(),
            "available_height": disponivel.height(),
            "desktop_state": self.estado_desktop,
            "desktop_material": self._material_desktop if self.modo_apresentacao == "desktop" else "fallback",
            "desktop_entry": self._desktop_entrada_ativa,
            "desktop_pinned": self.desktop_fixado,
            "desktop_page": self.desktop_pagina,
            "desktop_view": 'page' if self.desktop_pagina else 'overview',
            "desktop_phase": self._desktop_fase,
            "desktop_transition": self._desktop_sequencia,
            "desktop_target_width": self._desktop_destino.width() or self.width(),
            "desktop_target_height": self._desktop_destino.height() or self.height(),
            "streaming_open": self._streaming_aberto,
            "streaming_expanded": self._streaming_ampliado,
            "desktop_position_saved": self._registro_posicao_desktop is not None,
            "visible": self.isVisible(),
        }

    def _definir_fundo_desktop(self, opaco: bool) -> None:
        # Somente a cor do canvas WebEngine muda; nenhum HWND, ponte, sessão,
        # gesto ou widget é recriado. O modo compacto segue com alpha zero.
        opaco = bool(opaco)
        if self._fundo_desktop_opaco == opaco:
            return
        self._fundo_desktop_opaco = opaco
        self.pagina_web.setBackgroundColor(
            QColor(self._cor_fundo_desktop) if opaco else QColor(Qt.transparent))
        self.update()

    def paintEvent(self, evento) -> None:  # noqa: N802
        super().paintEvent(evento)
        if getattr(self, '_fundo_desktop_opaco', False):
            pintor = QPainter(self)
            pintor.fillRect(evento.rect(), self._cor_fundo_desktop)
            pintor.end()

    @Slot(str)
    def apresentar(self, modo: str) -> None:
        if modo not in {"full", "quick", "island", "desktop"} or modo == self.modo_apresentacao:
            return
        visivel = self.isVisible()
        if self.modo_apresentacao == "full":
            self._geometria_completa = QRect(self.normalGeometry() if self.isMaximized() else self.geometry())
            self._estado_completo = self.windowState()
            self._flags_completa = self.windowFlags()
        self.parar_streaming()
        self._animacao_desktop.stop()
        self._retomar_pintura_web_desktop()
        self._cancelar_arrasto_desktop()
        self._inatividade_desktop_timer.stop()
        self._remover_cobertura_transicao()
        self._desktop_fase = 'idle'
        if modo != 'desktop':
            self._animacao_entrada.stop()
            self._entrada_pendente = False
            self._prazo_entrada.stop()
            self.setWindowOpacity(1)
        self._cursor_desktop_timer.stop()
        self._recolher_desktop_timer.stop()
        self._abrir_desktop_timer.stop()
        self.clearMask()
        # Restaurar o canvas transparente ao voltar para a ilha compacta,
        # tela cheia ou outras apresentações.
        self._definir_fundo_desktop(False)
        self.setAttribute(Qt.WA_ShowWithoutActivating, modo == 'desktop')
        if self.modo_apresentacao == 'desktop':
            permitir_ativacao_desktop(int(self.winId()), True)
            restaurar_material_windows(int(self.winId()))
            self._material_desktop = 'fallback'
        self.modo_apresentacao = modo
        flags = self._flags_completa if modo == "full" else self._flags_completa | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        if modo == 'desktop':
            flags = Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setWindowState(Qt.WindowNoState)
        tela = self._resolver_tela_desktop()
        disponivel = tela.availableGeometry() if tela is not None else QRect(0, 0, 800, 600)
        if modo == "full":
            self.setMinimumSize(375, 620)
            desejada = QRect(self._geometria_completa)
        elif modo == 'desktop':
            self.setMinimumSize(1, 1)
            if tela is not None:
                self._observar_tela_desktop(tela)
            self.estado_desktop = 'compact'
            self.desktop_fixado = False
            self._desktop_transitorio = False
            self._desktop_dentro = False
            desejada = geometria_desktop(disponivel, ancora=self._ancora_para_geometria())
        else:
            self.setMinimumSize(240, 70) if modo == "island" else self.setMinimumSize(320, 420)
            largura, altura = (330, 86) if modo == "island" else (425, 720)
            desejada = QRect(disponivel.center().x() - largura // 2, disponivel.top() + 10, largura, altura)
        largura, altura = min(desejada.width(), disponivel.width()), min(desejada.height(), disponivel.height())
        x = min(max(desejada.x(), disponivel.left()), disponivel.right() - largura + 1)
        y = min(max(desejada.y(), disponivel.top()), disponivel.bottom() - altura + 1)
        self.setGeometry(QRect(x, y, largura, altura))
        if visivel:
            self.showMaximized() if modo == "full" and self._estado_completo & Qt.WindowMaximized else self.show()
        if modo == 'desktop':
            permitir_ativacao_desktop(int(self.winId()), False)
            self._material_desktop = aplicar_material_windows(int(self.winId()))
            if self._material_desktop == 'fallback':
                # Sem o backdrop retangular do DWM: Qt/CSS desenha só a cápsula.
                restaurar_material_windows(int(self.winId()))
            self._atualizar_mascara_desktop()
            self._cursor_desktop_timer.start()
            self._garantir_tray()
        self.ponte_web.publicar(self.apresentacao_publica())

    def _garantir_tray(self) -> None:
        if self._tray is not None or not QSystemTrayIcon.isSystemTrayAvailable():
            return
        desenho = QPixmap(32, 32)
        desenho.fill(Qt.transparent)
        pintor = QPainter(desenho)
        pintor.setRenderHint(QPainter.Antialiasing)
        pintor.setBrush(QColor('#c8a5f8'))
        pintor.setPen(Qt.NoPen)
        pintor.drawRoundedRect(4, 5, 24, 23, 9, 9)
        pintor.setBrush(QColor('#34234f'))
        pintor.drawEllipse(10, 14, 3, 5)
        pintor.drawEllipse(20, 14, 3, 5)
        pintor.end()
        self._tray = QSystemTrayIcon(QIcon(desenho), self)
        self._tray.setToolTip('Laylay · por perto')
        menu = QMenu(self)
        for titulo, callback in [('Mostrar no desktop', self._mostrar_desktop), ('Abrir interface completa', self._mostrar_completa), ('Recolher', self.recolher_desktop), ('Sair da interface', self.close)]:
            acao = QAction(titulo, menu)
            acao.triggered.connect(callback)
            menu.addAction(acao)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(lambda motivo: self._mostrar_desktop() if motivo == QSystemTrayIcon.Trigger else None)
        self._tray.show()

    def _observar_tela_desktop(self, tela) -> None:
        identidade = id(tela)
        if identidade in self._telas_observadas:
            return
        self._telas_observadas.add(identidade)
        tela.availableGeometryChanged.connect(lambda _area: self._reancorar_desktop())
        tela.logicalDotsPerInchChanged.connect(lambda _dpi: self._reancorar_desktop())
        tela.destroyed.connect(lambda _obj: self._telas_observadas.discard(identidade))

    def _tela_desktop_adicionada(self, tela) -> None:
        if not self._fechada:
            self._observar_tela_desktop(tela)
            self._reancorar_desktop()

    def _reancorar_desktop(self) -> None:
        if self.modo_apresentacao == 'desktop' and not self._fechada:
            if self._arrastando_desktop:
                return
            self._animar_geometria_desktop()

    def _mostrar_desktop(self) -> None:
        self.apresentar('desktop')
        self.show()

    def _mostrar_completa(self) -> None:
        if self.modo_apresentacao == 'desktop':
            self.selecionar_pagina_desktop(self.desktop_pagina or 'home')
        else:
            self.apresentar('full')
        self.show()
        self.raise_()
        self.activateWindow()

    def selecionar_pagina_desktop(self, pagina: str) -> None:
        """Uma decisão de navegação local preserva HWND, flags e transporte."""
        normalizada = _PAGINAS_DESKTOP.get(str(pagina))
        if self.modo_apresentacao != 'desktop' or normalizada is None:
            return
        if normalizada != 'streaming':
            self.parar_streaming()
        self.desktop_pagina = normalizada
        self._pagina_web_ativa = normalizada
        self.expandir_desktop(fixar=True)

    def ativar_desktop(self) -> None:
        if self.modo_apresentacao == 'desktop':
            permitir_ativacao_desktop(int(self.winId()), True)
            self.raise_()
            self.activateWindow()

    def iniciar_arrasto_desktop(self) -> None:
        if self._fechada or self.modo_apresentacao != 'desktop' or self._arrastando_desktop:
            return
        self._animacao_desktop.stop()
        self._retomar_pintura_web_desktop()
        self._desktop_sequencia += 1
        self._desktop_destino = QRect(self.geometry())
        self._desktop_fase = 'committing'
        self._inatividade_desktop_timer.stop()
        self._arrastando_desktop = True
        self._arrasto_cursor_origem = QCursor.pos()
        self._arrasto_geometria_origem = QRect(self.geometry())
        self._arrasto_ancora_anterior = QPoint(self._ancora_desktop) if self._ancora_desktop is not None else None
        tela = QGuiApplication.screenAt(self._arrasto_cursor_origem) or self._resolver_tela_desktop()
        self._arrasto_tela = self._identidade_tela(tela) if tela is not None else None
        self._arrasto_mudou = False
        self._arrasto_timer.start()
        self.ponte_web.publicar({'type': 'arrasto_desktop', 'active': True}, guardar=False)
        self.ponte_web.publicar(self.apresentacao_publica())

    def _aplicar_deslocamento_arrasto(self) -> None:
        if not self._arrastando_desktop:
            return
        cursor = QCursor.pos()
        delta = cursor - self._arrasto_cursor_origem
        if not self._arrasto_mudou and delta.manhattanLength() < 6:
            return
        tela = QGuiApplication.screenAt(cursor) or self._resolver_tela_desktop()
        if tela is None:
            return
        self._arrasto_tela = self._identidade_tela(tela)
        area = tela.availableGeometry()
        desejada = self._arrasto_geometria_origem.translated(delta)
        largura, altura = min(desejada.width(), area.width()), min(desejada.height(), area.height())
        x = min(max(desejada.x(), area.left()), area.right() - largura + 1)
        y = min(max(desejada.y(), area.top()), area.bottom() - altura + 1)
        limitada = QRect(x, y, largura, altura)
        if limitada != self._arrasto_geometria_origem:
            self._arrasto_mudou = True
        self._ancora_desktop = QPoint(limitada.center().x(), limitada.top())
        if limitada.size() != self.size():
            self._cobrir_transicao()
        self.setGeometry(limitada)
        self._desktop_destino = QRect(limitada)

    def atualizar_arrasto_desktop(self) -> None:
        if not self._arrastando_desktop:
            return
        # O último deslocamento pertence ao gesto mesmo se a soltura aconteceu
        # fora da janela entre dois ticks. Primeiro aplicar; depois concluir.
        self._aplicar_deslocamento_arrasto()
        if not botao_esquerdo_pressionado():
            self.finalizar_arrasto_desktop()

    def finalizar_arrasto_desktop(self) -> None:
        if not self._arrastando_desktop:
            return
        self._aplicar_deslocamento_arrasto()
        tela = self._resolver_tela_desktop()
        if self._arrasto_mudou and tela is not None:
            area = tela.availableGeometry()
            ancora = QPoint(self.geometry().center().x(), self.geometry().top())
            registro = {'version': 1, 'screen': self._identidade_tela(tela),
                        'offsets': {'center_x': ancora.x() - area.left(), 'top_y': ancora.y() - area.top()}}
            self.preferencias.setValue('v1/desktop_posicao', json.dumps(registro, ensure_ascii=False, separators=(',', ':')))
            self.preferencias.sync()
            self._registro_posicao_desktop = registro
            self._ancora_desktop = None
        else:
            self._ancora_desktop = self._arrasto_ancora_anterior
        self._arrasto_timer.stop()
        self._arrastando_desktop = False
        self._arrasto_tela = None
        self.ponte_web.publicar({'type': 'arrasto_desktop', 'active': False}, guardar=False)
        self.registrar_atividade_desktop()
        self._animar_geometria_desktop()

    def _cancelar_arrasto_desktop(self) -> None:
        self._arrasto_timer.stop()
        if self._arrastando_desktop:
            self._ancora_desktop = self._arrasto_ancora_anterior
            self._arrastando_desktop = False
            self._arrasto_tela = None
            self.ponte_web.publicar({'type': 'arrasto_desktop', 'active': False}, guardar=False)

    def expandir_desktop(self, fixar: bool = False) -> None:
        if self.modo_apresentacao != 'desktop':
            return
        self._recolher_desktop_timer.stop()
        self.desktop_fixado = self.desktop_fixado or bool(fixar)
        self._desktop_transitorio = not self.desktop_fixado
        self.estado_desktop = 'expanded'
        # O compositor recebe pixels opacos antes de aumentar o HWND.
        self._definir_fundo_desktop(True)
        # A ativação pode anteceder a troca da apresentação completa para a ilha.
        # Não depender de um segundo WindowActivate para observar o foco real.
        self._foco_desktop_observado = self._foco_desktop_observado or self._desktop_em_foco()
        self._recolher_foco_timer.stop()
        self.registrar_atividade_desktop()
        self._animar_geometria_desktop()

    def recolher_desktop(self) -> None:
        if self.modo_apresentacao != 'desktop':
            return
        self._cancelar_arrasto_desktop()
        self._recolher_desktop_timer.stop()
        self._abrir_desktop_timer.stop()
        self.desktop_fixado = False
        self._desktop_transitorio = False
        self.estado_desktop = 'compact'
        self._desktop_edicao = False
        self._inatividade_desktop_timer.stop()
        self._recolher_foco_timer.stop()
        self.parar_streaming()
        permitir_ativacao_desktop(int(self.winId()), False)
        self._animar_geometria_desktop()

    def _recolher_desktop_transitorio(self) -> None:
        if self._desktop_transitorio and not self.desktop_fixado and not self._desktop_edicao and not self._desktop_dentro:
            self.recolher_desktop()

    def registrar_atividade_desktop(self) -> None:
        """Só gestos humanos locais renovam o único prazo de inatividade."""
        if self.modo_apresentacao == 'desktop' and self.estado_desktop == 'expanded' and not self._fechada and not self._arrastando_desktop:
            self._desktop_adiamentos = 0
            self._inatividade_desktop_timer.start(20_000)

    def _desktop_em_foco(self) -> bool:
        return self.isActiveWindow()

    def _fala_em_andamento(self) -> bool:
        estado = getattr(self.controlador, '_estado_mais_recente', None) or {}
        return isinstance(estado, dict) and estado.get('activity') == 'speaking'

    def _streaming_em_transmissao(self) -> bool:
        return bool(self._streaming_aberto and self._pagina_web_ativa == 'streaming'
                    and self._streaming_pagina is not None
                    and self._streaming_pagina.captura.estado == 'transmitindo')

    def _recolher_por_perda_de_foco(self) -> None:
        if (self.modo_apresentacao != 'desktop' or self.estado_desktop != 'expanded'
                or self._fechada or self._arrastando_desktop or not self._foco_desktop_observado):
            return
        if self._desktop_em_foco():
            return
        # Nunca interromper uma frase, uma transmissão observada ou diálogos Qt.
        if (self._fala_em_andamento() or self._streaming_em_transmissao()
                or self._desktop_compondo or QApplication.activeModalWidget() is not None
                or QApplication.activePopupWidget() is not None):
            self._recolher_foco_timer.start(750)
            return
        self.recolher_desktop()

    def event(self, evento):  # noqa: N802
        # Perda real de foco, não heartbeat, cursor parado ou pintura, governa recolhimento.
        if evento.type() == QEvent.WindowActivate and getattr(self,'modo_apresentacao',None) == 'desktop':
            self._foco_desktop_observado = True
            if hasattr(self,'_recolher_foco_timer'):
                self._recolher_foco_timer.stop()
        elif evento.type() == QEvent.WindowDeactivate and getattr(self,'_foco_desktop_observado',False):
            if (getattr(self,'modo_apresentacao',None) == 'desktop'
                    and getattr(self,'estado_desktop',None) == 'expanded'
                    and not getattr(self,'_fechada',True)):
                self._recolher_foco_timer.start(350)
        return super().event(evento)

    def _recolher_por_inatividade(self) -> None:
        if self.modo_apresentacao != 'desktop' or self.estado_desktop != 'expanded' or self._fechada or self._arrastando_desktop:
            return
        # A janela em uso permanece aberta: sem recolher no meio da digitação.
        if self._desktop_em_foco():
            self._inatividade_desktop_timer.start(20_000)
            return
        # Fala e transmissão ativa são exceções mesmo quando outro app recebe foco.
        if self._fala_em_andamento() or self._streaming_em_transmissao():
            self._inatividade_desktop_timer.start(20_000)
            return
        if self._foco_desktop_observado:
            self._recolher_por_perda_de_foco()
            return
        # Não recolher antes de observar o primeiro foco real da janela.
        self._inatividade_desktop_timer.start(20_000)
        return

    def eventFilter(self, objeto, evento) -> bool:  # noqa: N802
        if self.modo_apresentacao == 'desktop' and self.estado_desktop == 'expanded' and not self._fechada:
            dentro = isinstance(objeto, QWidget) and (objeto is self or self.isAncestorOf(objeto))
            if dentro:
                tipo = evento.type()
                if tipo in {QEvent.MouseButtonPress, QEvent.MouseButtonRelease, QEvent.MouseButtonDblClick, QEvent.Wheel, QEvent.KeyPress, QEvent.KeyRelease, QEvent.TouchBegin, QEvent.TouchUpdate}:
                    self.registrar_atividade_desktop()
                elif tipo == QEvent.InputMethod:
                    self._desktop_compondo = bool(evento.preeditString())
                    self.registrar_atividade_desktop()
                if tipo == QEvent.KeyPress and evento.key() == Qt.Key_Escape and self._streaming_ampliado:
                    self._ampliar_streaming(False)
                    return True
        return super().eventFilter(objeto, evento)

    def _pausar_pintura_web_desktop(self) -> None:
        if self._transicao_cobertura is not None and not self._web_pintura_congelada:
            self.web.setUpdatesEnabled(False)
            self._web_pintura_congelada = True

    def _retomar_pintura_web_desktop(self) -> None:
        if self._web_pintura_congelada:
            self._web_pintura_congelada = False
            self.web.setUpdatesEnabled(True)
            self.web.update()

    def _animar_geometria_desktop(self) -> None:
        tela = self._resolver_tela_desktop()
        if tela is None:
            return
        self._observar_tela_desktop(tela)
        destino = geometria_desktop(tela.availableGeometry(), self.estado_desktop == 'expanded', self.desktop_pagina, self._ancora_para_geometria())
        if self._desktop_destino == destino and self._animacao_desktop.state() == QPropertyAnimation.Running:
            self.ponte_web.publicar(self.apresentacao_publica())
            return
        if destino == self.geometry() and self._animacao_desktop.state() != QPropertyAnimation.Running:
            self._desktop_destino = destino
            if self._transicao_cobertura is not None:
                self._desktop_sequencia += 1
                self._desktop_fase = 'committing'
            self.ponte_web.publicar(self.apresentacao_publica())
            return
        self._animacao_desktop.stop()
        self._retomar_pintura_web_desktop()
        self._desktop_destino = destino
        self._desktop_sequencia += 1
        if self.isVisible() and self.ponte_web._pronta:
            self._cobrir_transicao()
        self._desktop_fase = 'resizing'
        self.ponte_web.publicar(self.apresentacao_publica())
        if self.preferencias_publicas()['reduced']:
            self.setGeometry(destino)
            self._geometria_desktop_concluida()
        else:
            self._pausar_pintura_web_desktop()
            self._animacao_desktop.setStartValue(self.geometry())
            self._animacao_desktop.setEndValue(destino)
            self._animacao_desktop.start()

    def _cobrir_transicao(self) -> None:
        if self._transicao_cobertura is not None:
            return
        # A textura WebEngine chega depois da geometria HWND. Congelar o
        # quadro anterior sobre fundo opaco impede buracos e reflow aparente.
        quadro = self.web.grab()
        cobertura = QLabel(self)
        cobertura.setObjectName('desktopTransitionCover')
        cobertura.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        cobertura.setStyleSheet('background:#0b0d12;border:0')
        cobertura.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        cobertura.setPixmap(quadro)
        cobertura.setGeometry(self.rect())
        self._transicao_cobertura = cobertura
        cobertura.show()
        cobertura.raise_()

    def _remover_cobertura_transicao(self) -> None:
        cobertura, self._transicao_cobertura = self._transicao_cobertura, None
        if cobertura is not None:
            cobertura.hide()
            cobertura.deleteLater()

    def _geometria_desktop_concluida(self) -> None:
        self._retomar_pintura_web_desktop()
        if self.modo_apresentacao != 'desktop' or self._fechada:
            return
        self._desktop_fase = 'committing'
        self.ponte_web.publicar(self.apresentacao_publica())

    def confirmar_transicao_desktop(self, sequencia: int, largura: int, altura: int) -> None:
        if self._fechada or self.modo_apresentacao != 'desktop' or sequencia != self._desktop_sequencia:
            return
        if self._animacao_desktop.state() == QPropertyAnimation.Running or (largura, altura) != (self.web.width(), self.web.height()):
            return
        if self._desktop_fase not in {'committing', 'starting'}:
            return
        self._remover_cobertura_transicao()
        # Manter opaco durante todo o shrink, inclusive frames intermediários.
        # Só a geometria compacta confirmada volta ao canvas transparente.
        if self.estado_desktop == 'compact':
            self._definir_fundo_desktop(False)
        if self._entrada_pendente:
            self._prazo_entrada.stop()
            self._entrada_pendente = False
            self._entrada_exibida = True
            if self.preferencias_publicas()['reduced']:
                self.setWindowOpacity(1)
            else:
                self._desktop_entrada_ativa = True
                self._entrada_visual_timer.start()
                self._animacao_entrada.setStartValue(0)
                self._animacao_entrada.setEndValue(1)
                self._animacao_entrada.start()
        self._desktop_fase = 'idle'
        self.ponte_web.publicar(self.apresentacao_publica())

    def _concluir_entrada_visual(self) -> None:
        self._entrada_visual_timer.stop()
        if self._desktop_entrada_ativa:
            self._desktop_entrada_ativa = False
            if not self._fechada:
                self.ponte_web.publicar(self.apresentacao_publica())

    def _atualizar_mascara_desktop(self) -> None:
        if self.modo_apresentacao != 'desktop':
            return
        forma = QPainterPath()
        forma.addRoundedRect(0, 0, self.width(), self.height(), 24, 24)
        self.setMask(QRegion(forma.toFillPolygon().toPolygon()))

    def resizeEvent(self, evento) -> None:  # noqa: N802
        super().resizeEvent(evento)
        self._atualizar_mascara_desktop()
        if self._transicao_cobertura is not None:
            self._transicao_cobertura.setGeometry(self.rect())
        if self._erro_entrada is not None and self._erro_entrada.isVisible():
            self._erro_entrada.setGeometry(self.rect())

    def showEvent(self, evento) -> None:  # noqa: N802
        super().showEvent(evento)
        if self.modo_apresentacao == 'desktop':
            self._cursor_desktop_timer.start()
            permitir_ativacao_desktop(int(self.winId()), False)
            # Algumas trocas de flags recriam o HWND: reaplicar só à janela atual.
            self._material_desktop = aplicar_material_windows(int(self.winId()))
            if self._material_desktop == 'fallback':
                # Sem o backdrop retangular do DWM: Qt/CSS desenha só a cápsula.
                restaurar_material_windows(int(self.winId()))

    def hideEvent(self, evento) -> None:  # noqa: N802
        self._cursor_desktop_timer.stop()
        self._abrir_desktop_timer.stop()
        self._recolher_desktop_timer.stop()
        self._inatividade_desktop_timer.stop()
        self._cancelar_arrasto_desktop()
        super().hideEvent(evento)

    def _observar_cursor_desktop(self) -> None:
        if self.modo_apresentacao != 'desktop' or not self.isVisible() or self._fechada:
            self._cursor_desktop_timer.stop()
            return
        global_cursor = QCursor.pos()
        ponto = self.mapFromGlobal(global_cursor)
        dentro = self.rect().contains(ponto) and self.mask().contains(ponto)
        self._desktop_dentro = dentro
        cursor_global = (global_cursor.x(), global_cursor.y())
        if self._ultimo_cursor_global is not None and cursor_global != self._ultimo_cursor_global and dentro:
            self.registrar_atividade_desktop()
        self._ultimo_cursor_global = cursor_global
        cursor = (ponto.x(), ponto.y(), dentro)
        if cursor != self._ultimo_cursor_desktop and not self.preferencias_publicas()['reduced']:
            self._ultimo_cursor_desktop = cursor
            self.ponte_web.publicar({'type': 'cursor_desktop', 'x': ponto.x(), 'y': ponto.y(), 'inside': dentro, 'visible': True}, guardar=False)

    def abrir_streaming(self) -> None:
        if self._streaming_pagina is None:
            from cliente.terminal_2.streaming import PaginaStreaming
            self._streaming_host = QScrollArea(self.web)
            self._streaming_host.setObjectName('streamingIntegrado')
            self._streaming_host.setWidgetResizable(True)
            self._streaming_host.setFrameShape(QScrollArea.NoFrame)
            self._streaming_host.setStyleSheet('QScrollArea#streamingIntegrado,QScrollArea#streamingIntegrado>QWidget>QWidget{background:#111620;border:0}')
            self._streaming_pagina = PaginaStreaming(self._streaming_host, expandir_no_host=lambda _cheia: self._ampliar_streaming(not self._streaming_ampliado))
            self._streaming_host.setWidget(self._streaming_pagina)
            self._streaming_host.hide()
        self._streaming_aberto = True
        self._pagina_web_ativa = 'streaming'
        self.registrar_atividade_desktop()
        self.ponte_web.publicar(self.apresentacao_publica())

    def definir_viewport_streaming(self, dados: str) -> bool:
        """DOM só fornece geometria local; frames e captura pertencem ao Qt."""
        if not self._streaming_aberto or self._streaming_host is None or self._pagina_web_ativa != 'streaming' or (self.modo_apresentacao == 'desktop' and self.estado_desktop != 'expanded'):
            if self._streaming_host is not None:
                self._streaming_pagina.encerrar()
                self._streaming_host.hide()
            return False
        try:
            entrada = json.loads(dados)
            if not isinstance(entrada, dict) or set(entrada) != {'x', 'y', 'width', 'height'}:
                raise ValueError('Geometria inválida')
            valores = [entrada[k] for k in ('x', 'y', 'width', 'height')]
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in valores):
                raise ValueError('Geometria inválida')
            x, y, largura, altura = valores
            if largura <= 0 or altura <= 0 or x < 0 or y < 0 or x + largura > self.web.width() + 1 or y + altura > self.web.height() + 1:
                raise ValueError('Fora do viewport')
            retangulo = QRect(round(x), round(y), round(largura), round(altura)).intersected(self.web.rect())
            if retangulo.isEmpty():
                raise ValueError('Viewport vazio')
            self._streaming_host.setGeometry(retangulo)
            if self._desktop_fase == 'idle':
                self._streaming_host.show()
                self._streaming_host.raise_()
            return True
        except (ValueError, TypeError, json.JSONDecodeError):
            self._streaming_pagina.encerrar()
            self._streaming_host.hide()
            return False

    def _ampliar_streaming(self, ativo: bool) -> None:
        if self._streaming_pagina is None or not self._streaming_aberto:
            return
        self._streaming_ampliado = bool(ativo)
        self._streaming_pagina.ampliar_integrado(bool(ativo))
        self.registrar_atividade_desktop()
        self.ponte_web.publicar(self.apresentacao_publica())

    def parar_streaming(self) -> None:
        estava_aberto = self._streaming_aberto
        self._streaming_aberto = False
        self._streaming_ampliado = False
        if self._streaming_pagina is not None:
            self._streaming_pagina.ampliar_integrado(False)
            self._streaming_pagina.encerrar()
            self._streaming_host.hide()
        if estava_aberto and not self._fechada:
            self.ponte_web.publicar(self.apresentacao_publica())

    def closeEvent(self, evento) -> None:  # noqa: N802
        encerrando = not self._fechada
        if encerrando:
            self._fechada = True
            self._animacao_desktop.stop()
            self._animacao_entrada.stop()
            self._prazo_entrada.stop()
            self._arrasto_timer.stop()
            self._remover_cobertura_transicao()
            self._inatividade_desktop_timer.stop()
            self._recolher_foco_timer.stop()
            QApplication.instance().removeEventFilter(self)
            self._cursor_desktop_timer.stop()
            self._recolher_desktop_timer.stop()
            self._abrir_desktop_timer.stop()
            if self._tray is not None:
                self._tray.hide()
            if self._streaming_pagina is not None:
                self._streaming_pagina.fechar()
                self._streaming_host.close()
            self.ponte_web._pronta = False
            self.web.stop()
            self.pagina_web.setWebChannel(None)
            self.controlador.close()
        evento.accept()
        if encerrando:
            self.encerrada.emit()
