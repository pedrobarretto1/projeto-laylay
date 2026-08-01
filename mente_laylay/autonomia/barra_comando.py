"""Barra global e discreta para enviar comandos à mente única da Laylay."""

from __future__ import annotations

import os
import queue
import threading
import time
import unicodedata
from typing import Any, Callable


class CapturaTextoGlobal:
    """Captura uma linha sem transferir o foco para a sobreposição."""

    _MODIFICADORES = {
        "shift", "left shift", "right shift", "ctrl", "left ctrl", "right ctrl",
        "alt", "left alt", "right alt", "windows", "left windows", "right windows",
        "caps lock",
    }
    _SHIFT_SIMBOLOS = {
        "1": "!", "2": "@", "3": "#", "4": "$", "5": "%", "6": "¨",
        "7": "&", "8": "*", "9": "(", "0": ")", "-": "_", "=": "+",
        ",": "<", ".": ">", ";": ":", "/": "?", "\\": "|",
    }
    _ACENTOS_COMBINANTES = {
        "´": "\u0301", "`": "\u0300", "^": "\u0302", "~": "\u0303", "¨": "\u0308",
    }

    def __init__(
        self,
        *,
        keyboard_mod: Any,
        ao_atualizar: Callable[[str], Any],
        ao_enviar: Callable[[str], Any],
        ao_cancelar: Callable[[], Any],
        log: Callable[..., Any] = print,
        clock: Callable[[], float] = time.monotonic,
        intervalo_liberacao_s: float = 0.12,
        teclas_ativacao: tuple[str, ...] = ("ctrl", "shift", "space"),
        registrar_falha: Callable[..., Any] | None = None,
    ) -> None:
        self.keyboard = keyboard_mod
        self.ao_atualizar = ao_atualizar
        self.ao_enviar = ao_enviar
        self.ao_cancelar = ao_cancelar
        self.log = log
        self._clock = clock
        self._intervalo_liberacao_s = max(0.0, float(intervalo_liberacao_s))
        self._teclas_ativacao = tuple(
            dict.fromkeys(
                str(nome or "").strip().casefold()
                for nome in teclas_ativacao
                if str(nome or "").strip()
            )
        )
        self.texto = ""
        self._hook: Any = None
        self._lock = threading.RLock()
        self._shift = False
        self._teclas_liberadas_desde: float | None = None
        self._ultima_espera: tuple[str, ...] = ()
        self.registrar_falha = registrar_falha

    def _relatar(self, codigo: str, erro: BaseException) -> None:
        if callable(self.registrar_falha):
            self.registrar_falha("barra_comando", codigo, erro=erro)

    @property
    def ativa(self) -> bool:
        with self._lock:
            return self._hook is not None

    def _pressionada_no_windows(self, nome: str) -> bool | None:
        """Consulta o teclado físico sem depender do cache da biblioteca keyboard."""
        if os.name != "nt" or getattr(self.keyboard, "__name__", "") != "keyboard":
            return None
        try:
            import ctypes

            mapa_vks = {
                "ctrl": (0x11,),
                "control": (0x11,),
                "shift": (0x10,),
                "alt": (0x12,),
                "win": (0x5B, 0x5C),
                "windows": (0x5B, 0x5C),
                "space": (0x20,),
                "espaco": (0x20,),
                "espaço": (0x20,),
            }
            if nome.startswith("f") and nome[1:].isdigit():
                numero = int(nome[1:])
                if 1 <= numero <= 24:
                    mapa_vks[nome] = (0x70 + numero - 1,)
            elif len(nome) == 1 and nome.isalnum():
                mapa_vks[nome] = (ord(nome.upper()),)
            if nome not in mapa_vks:
                return None
            return any(
                bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)
                for vk in mapa_vks[nome]
            )
        except Exception:
            return None

    def _tecla_pressionada(self, nome: str) -> bool:
        estado_windows = self._pressionada_no_windows(nome)
        if estado_windows is not None:
            return estado_windows
        try:
            return bool(self.keyboard.is_pressed(nome))
        except Exception:
            # Backends/fakes antigos podem não oferecer is_pressed. O atraso
            # estável ainda reduz a chance de capturar o fim do próprio atalho.
            return False

    def teclas_ativacao_ativas(self) -> list[str]:
        """Lê modificadores e a tecla principal antes do hook supressor."""
        ativos = []
        for nome in self._teclas_ativacao:
            if self._tecla_pressionada(nome):
                ativos.append(nome)
        return ativos

    def modificadores_ativos(self) -> list[str]:
        """Compatibilidade para diagnósticos que consultam apenas modificadores."""
        return [
            nome for nome in self.teclas_ativacao_ativas()
            if nome not in {"space", "espaco", "espaço"}
        ]

    def iniciar(self) -> bool:
        with self._lock:
            if self._hook is not None:
                return True
            ativos = self.teclas_ativacao_ativas()
            if ativos:
                self._teclas_liberadas_desde = None
                assinatura = tuple(ativos)
                if assinatura != self._ultima_espera:
                    self.log(
                        "⌨️ [BARRA:JOGO] aguardando soltar teclas do atalho: "
                        + ", ".join(ativos)
                    )
                    self._ultima_espera = assinatura
                return False
            agora = float(self._clock())
            if self._teclas_liberadas_desde is None:
                self._teclas_liberadas_desde = agora
                self._ultima_espera = ()
                if self._intervalo_liberacao_s > 0:
                    return False
            if agora - self._teclas_liberadas_desde < self._intervalo_liberacao_s:
                return False
            self.texto = ""
            self._shift = False
            try:
                identificador = self.keyboard.hook(self.processar_evento, suppress=True)
                self._hook = identificador if identificador is not None else self.processar_evento
            except Exception as exc:
                self._hook = None
                self.log(f"⚠️ [BARRA:JOGO] captura global indisponível: {exc}")
                self._relatar("captura_global", exc)
                return False
        self.ao_atualizar("")
        return True

    def encerrar(self) -> None:
        with self._lock:
            hook, self._hook = self._hook, None
            self._shift = False
            self._teclas_liberadas_desde = None
            self._ultima_espera = ()
        if hook is not None:
            try:
                self.keyboard.unhook(hook)
            except Exception as erro:
                self._relatar("liberacao_hook", erro)

    def _caps_ativo(self) -> bool:
        try:
            return bool(self.keyboard.is_toggled("caps lock"))
        except Exception:
            return False

    def _caractere(self, nome: str) -> str:
        if len(nome) == 1:
            if nome.isalpha():
                maiuscula = bool(self._shift) ^ self._caps_ativo()
                return nome.upper() if maiuscula else nome.lower()
            return self._SHIFT_SIMBOLOS.get(nome, nome) if self._shift else nome
        aliases = {
            "space": " ", "decimal": ".", "comma": ",", "dot": ".",
            "minus": "_" if self._shift else "-", "plus": "+",
        }
        return aliases.get(nome, "")

    def processar_evento(self, evento: Any) -> None:
        nome = str(getattr(evento, "name", "") or "").casefold()
        tipo = str(getattr(evento, "event_type", "down") or "down").casefold()
        if nome in {"shift", "left shift", "right shift"}:
            with self._lock:
                self._shift = tipo == "down"
            return
        if tipo != "down" or nome in self._MODIFICADORES:
            return

        enviar = cancelar = False
        with self._lock:
            if self._hook is None:
                return
            if nome in {"enter", "return"}:
                enviar = True
                texto = self.texto
            elif nome in {"esc", "escape"}:
                cancelar = True
                texto = self.texto
            elif nome == "backspace":
                self.texto = self.texto[:-1]
                texto = self.texto
            else:
                caractere = self._caractere(nome)
                if not caractere:
                    return
                if self.texto and self.texto[-1] in self._ACENTOS_COMBINANTES and caractere.isalpha():
                    acento = self._ACENTOS_COMBINANTES[self.texto[-1]]
                    self.texto = self.texto[:-1] + unicodedata.normalize("NFC", caractere + acento)
                else:
                    self.texto += caractere
                texto = self.texto

        if enviar:
            self.encerrar()
            self.ao_enviar(texto)
        elif cancelar:
            self.encerrar()
            self.ao_cancelar()
        else:
            self.ao_atualizar(texto)


class BarraComandoRuntime:
    """Mantém uma única janela Tk e a controla por uma fila thread-safe."""

    def __init__(
        self,
        *,
        processar_texto: Callable[[str], Any],
        keyboard_mod: Any,
        hotkey: str = "ctrl+shift+space",
        log: Callable[..., Any] = print,
        tkinter_mod: Any = None,
        clock: Callable[[], float] = time.monotonic,
        intervalo_duplicata_s: float = 1.5,
        modo_jogo_ativo: Callable[[], bool] | None = None,
        sobreposicao_sem_foco_jogo: bool = True,
        timeout_sem_foco_s: float = 45.0,
        estado_visual_cb: Callable[[bool, str], Any] | None = None,
        visual_externo_disponivel: Callable[[], bool] | None = None,
        registrar_falha: Callable[..., Any] | None = None,
    ) -> None:
        self._processar_texto = processar_texto
        self._keyboard = keyboard_mod
        self.hotkey = str(hotkey or "ctrl+shift+space").strip()
        self._log = log
        self._tkinter_mod = tkinter_mod
        self._clock = clock
        self._intervalo_duplicata_s = max(0.0, float(intervalo_duplicata_s))
        self._modo_jogo_ativo = modo_jogo_ativo or (lambda: False)
        self._sobreposicao_sem_foco_jogo = bool(sobreposicao_sem_foco_jogo)
        self._timeout_sem_foco_s = max(5.0, float(timeout_sem_foco_s))
        self._estado_visual_cb = estado_visual_cb
        self._visual_externo_disponivel = visual_externo_disponivel or (lambda: False)
        self._registrar_falha = registrar_falha
        # Ações repetidas da mesma combinação de teclas representam uma única
        # abertura. Uma fila maior fazia a janela reabrir e apagar o texto.
        self._fila: queue.Queue[str] = queue.Queue(maxsize=1)
        self._fila_interface: queue.SimpleQueue[tuple[str, Any]] = queue.SimpleQueue()
        self._thread: threading.Thread | None = None
        self._pronta = threading.Event()
        # O chamador do encerramento nunca toca no Tk. A thread proprietária
        # confirma por este evento que saiu do mainloop e liberou a captura.
        self._interface_encerrada = threading.Event()
        self._interface_encerrada.set()
        self._falha = ""
        self._hotkey_registrada = False
        self._hotkey_nativa_thread: threading.Thread | None = None
        self._hotkey_nativa_id = 0
        self._hotkey_handle: Any = None
        self._estado_lock = threading.RLock()
        self._ultima_abertura_ts = float("-inf")
        self._ultima_entrada_assinatura = ""
        self._ultima_entrada_ts = float("-inf")

    def _relatar(self, codigo: str, erro: BaseException) -> None:
        if callable(self._registrar_falha):
            self._registrar_falha("barra_comando", codigo, erro=erro)

    def _publicar_estado_visual(self, visivel: bool, texto: str = "") -> None:
        if self._estado_visual_cb is None:
            return
        try:
            self._estado_visual_cb(bool(visivel), str(texto or ""))
        except Exception as exc:
            self._log(f"⚠️ [BARRA] estado visual externo indisponível: {exc}")
            self._relatar("estado_visual", exc)

    @staticmethod
    def normalizar_entrada(texto: str) -> str:
        return " ".join(str(texto or "").strip().split())

    def _despachar(self, texto: str) -> bool:
        entrada = self.normalizar_entrada(texto)
        if not entrada:
            return False
        self._log(f"⌨️ [BARRA] Usuário: {entrada}")
        try:
            self._processar_texto(entrada)
            return True
        except Exception as exc:
            self._log(f"⚠️ [BARRA] Não consegui enviar o comando: {exc}")
            self._relatar("envio_comando", exc)
            return False

    def enviar(self, texto: str) -> bool:
        entrada = self.normalizar_entrada(texto)
        if not entrada:
            return False
        assinatura = entrada.casefold()
        agora = float(self._clock())
        with self._estado_lock:
            if (
                assinatura == self._ultima_entrada_assinatura
                and agora - self._ultima_entrada_ts <= self._intervalo_duplicata_s
            ):
                self._log(f"⌨️ [BARRA] envio repetido ignorado: {entrada!r}")
                return False
            self._ultima_entrada_assinatura = assinatura
            self._ultima_entrada_ts = agora

        # O callback injetado é o agendador assíncrono da mente. Chamá-lo uma
        # vez aqui evita criar uma thread concorrente para cada pressão de Enter.
        ok = self._despachar(entrada)
        if not ok:
            with self._estado_lock:
                if self._ultima_entrada_assinatura == assinatura:
                    self._ultima_entrada_assinatura = ""
                    self._ultima_entrada_ts = float("-inf")
        return ok

    def _carregar_tk(self) -> Any:
        if self._tkinter_mod is not None:
            return self._tkinter_mod
        import tkinter  # import tardio: a Laylay continua iniciando se o Tk falhar

        return tkinter

    @staticmethod
    def _janela_ocupa_monitor(hwnd: int) -> bool:
        """Reconhece fullscreen/borderless sem depender do monitor de jogos."""
        if os.name != "nt" or not int(hwnd or 0):
            return False
        try:
            import ctypes
            from ctypes import wintypes

            class MonitorInfo(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT),
                    ("dwFlags", wintypes.DWORD),
                ]

            rect = wintypes.RECT()
            if not ctypes.windll.user32.GetWindowRect(int(hwnd), ctypes.byref(rect)):
                return False
            monitor = ctypes.windll.user32.MonitorFromWindow(int(hwnd), 2)
            info = MonitorInfo(cbSize=ctypes.sizeof(MonitorInfo))
            if not monitor or not ctypes.windll.user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
                return False
            tolerancia = 8
            return bool(
                abs(rect.left - info.rcMonitor.left) <= tolerancia
                and abs(rect.top - info.rcMonitor.top) <= tolerancia
                and abs(rect.right - info.rcMonitor.right) <= tolerancia
                and abs(rect.bottom - info.rcMonitor.bottom) <= tolerancia
            )
        except Exception:
            return False

    @staticmethod
    def _traduzir_hotkey_windows(hotkey: str) -> tuple[int, int] | None:
        partes = [p.strip().casefold() for p in str(hotkey or "").split("+") if p.strip()]
        modificadores = 0x4000  # MOD_NOREPEAT
        tecla = None
        mapa_mod = {
            "alt": 0x0001, "ctrl": 0x0002, "control": 0x0002,
            "shift": 0x0004, "win": 0x0008, "windows": 0x0008,
        }
        mapa_tecla = {"space": 0x20, "espaco": 0x20, "espaço": 0x20}
        for parte in partes:
            if parte in mapa_mod:
                modificadores |= mapa_mod[parte]
            elif parte in mapa_tecla:
                tecla = mapa_tecla[parte]
            elif len(parte) == 1 and parte.isalnum():
                tecla = ord(parte.upper())
            elif parte.startswith("f") and parte[1:].isdigit() and 1 <= int(parte[1:]) <= 24:
                tecla = 0x70 + int(parte[1:]) - 1
            else:
                return None
        return (modificadores, tecla) if tecla is not None else None

    @staticmethod
    def _teclas_hotkey(hotkey: str) -> tuple[str, ...]:
        aliases = {
            "control": "ctrl",
            "win": "windows",
            "espaco": "space",
            "espaço": "space",
        }
        partes = (
            parte.strip().casefold()
            for parte in str(hotkey or "").split("+")
        )
        return tuple(
            dict.fromkeys(
                aliases.get(parte, parte)
                for parte in partes
                if parte
            )
        )

    def _registrar_hotkey_nativo_windows(self) -> bool:
        """Usa WM_HOTKEY: bloqueia a combinação, mas preserva todos os key-ups."""
        if os.name != "nt" or getattr(self._keyboard, "__name__", "") != "keyboard":
            return False
        traducao = self._traduzir_hotkey_windows(self.hotkey)
        if not traducao:
            return False
        modificadores, tecla = traducao
        pronta = threading.Event()
        resultado = {"ok": False}
        hotkey_id = 0x4C41

        def loop_hotkey() -> None:
            user32 = None
            try:
                import ctypes
                from ctypes import wintypes

                user32 = ctypes.windll.user32
                self._hotkey_nativa_id = int(ctypes.windll.kernel32.GetCurrentThreadId())
                resultado["ok"] = bool(
                    user32.RegisterHotKey(None, hotkey_id, modificadores, tecla)
                )
                pronta.set()
                if not resultado["ok"]:
                    return
                mensagem = wintypes.MSG()
                while user32.GetMessageW(ctypes.byref(mensagem), None, 0, 0) > 0:
                    if int(mensagem.message) == 0x0312 and int(mensagem.wParam) == hotkey_id:
                        self.solicitar_abertura()
            except Exception as exc:
                self._log(f"⚠️ [BARRA] hotkey nativo encerrou: {exc}")
                self._relatar("hotkey_nativo", exc)
                pronta.set()
            finally:
                if user32 is not None:
                    try:
                        user32.UnregisterHotKey(None, hotkey_id)
                    except Exception:
                        pass
                self._hotkey_nativa_id = 0

        thread = threading.Thread(
            target=loop_hotkey, name="Laylay-Hotkey-Nativo", daemon=True,
        )
        thread.start()
        pronta.wait(1.0)
        if resultado["ok"]:
            self._hotkey_nativa_thread = thread
        return bool(resultado["ok"])

    def _executar_interface(self) -> None:
        captura_global: CapturaTextoGlobal | None = None
        try:
            tk = self._carregar_tk()
            root = tk.Tk()
            root.withdraw()
            root.title("Comando para Laylay")
            root.configure(bg="#171923")
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            try:
                root.attributes("-alpha", 0.97)
                root.wm_attributes("-toolwindow", True)
            except Exception:
                pass

            largura, altura = 680, 62
            frame = tk.Frame(
                root,
                bg="#171923",
                highlightbackground="#8b5cf6",
                highlightcolor="#a78bfa",
                highlightthickness=2,
                bd=0,
            )
            frame.pack(fill="both", expand=True)
            tk.Label(
                frame,
                text="◕‿◕",
                bg="#171923",
                fg="#c4b5fd",
                font=("Segoe UI", 15, "bold"),
                padx=16,
            ).pack(side="left")
            entrada = tk.Entry(
                frame,
                bg="#171923",
                fg="#f8fafc",
                insertbackground="#f8fafc",
                selectbackground="#7c3aed",
                relief="flat",
                bd=0,
                font=("Segoe UI", 15),
            )
            entrada.pack(side="left", fill="both", expand=True, padx=(0, 12), pady=12)
            tk.Label(
                frame,
                text="Enter envia  ·  Esc fecha",
                bg="#171923",
                fg="#7f8494",
                font=("Segoe UI", 9),
                padx=14,
            ).pack(side="right")

            janela_anterior = {"hwnd": 0}
            geracao_foco = {"valor": 0}
            modo_sem_foco = {"ativo": False}
            modo_externo = {"ativo": False}

            def hwnd_root() -> int:
                try:
                    import ctypes

                    hwnd = int(root.winfo_id() or 0)
                    pai = int(ctypes.windll.user32.GetParent(hwnd) or 0)
                    return pai or hwnd
                except Exception:
                    return 0

            def configurar_sem_ativar(ativo: bool) -> bool:
                try:
                    import ctypes

                    hwnd = hwnd_root()
                    if not hwnd:
                        return False
                    user32 = ctypes.windll.user32
                    get_style = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
                    set_style = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
                    estilo = int(get_style(hwnd, -20))
                    if ativo:
                        # WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST
                        estilo |= 0x08000000 | 0x00000080 | 0x00000008
                    else:
                        estilo &= ~0x08000000
                    set_style(hwnd, -20, estilo)
                    if ativo:
                        user32.ShowWindow(hwnd, 4)  # SW_SHOWNOACTIVATE
                        user32.SetWindowPos(
                            hwnd, -1, 0, 0, 0, 0,
                            0x0001 | 0x0002 | 0x0010 | 0x0040,
                        )
                    return True
                except Exception as exc:
                    if ativo:
                        self._log(f"⚠️ [BARRA:JOGO] janela sem ativação indisponível: {exc}")
                    return False

            def enfileirar_interface(acao: str, valor: Any = None) -> None:
                self._fila_interface.put((acao, valor))

            captura_global = CapturaTextoGlobal(
                keyboard_mod=self._keyboard,
                ao_atualizar=lambda texto: enfileirar_interface("texto_global", texto),
                ao_enviar=lambda texto: enfileirar_interface("enviar_global", texto),
                ao_cancelar=lambda: enfileirar_interface("fechar_global"),
                log=self._log,
                clock=self._clock,
                teclas_ativacao=self._teclas_hotkey(self.hotkey),
                registrar_falha=self._registrar_falha,
            )

            def obter_janela_ativa() -> int:
                try:
                    import ctypes

                    return int(ctypes.windll.user32.GetForegroundWindow())
                except Exception:
                    return 0

            def devolver_foco() -> None:
                hwnd = int(janela_anterior.get("hwnd") or 0)
                if not hwnd:
                    return
                try:
                    import ctypes

                    ctypes.windll.user32.SetForegroundWindow(hwnd)
                except Exception as erro:
                    self._relatar("restauracao_foco", erro)

            def ocultar(*, restaurar_foco: bool = True) -> None:
                geracao_foco["valor"] += 1
                captura_global.encerrar()
                entrada.delete(0, "end")
                root.withdraw()
                self._publicar_estado_visual(False, "")
                era_sem_foco = bool(modo_sem_foco["ativo"])
                modo_sem_foco["ativo"] = False
                modo_externo["ativo"] = False
                if restaurar_foco and not era_sem_foco:
                    root.after(30, devolver_foco)

            def ativar_captura_sem_foco(geracao: int, tentativa: int = 0) -> None:
                if (
                    geracao != geracao_foco["valor"]
                    or (root.state() == "withdrawn" and not modo_externo["ativo"])
                ):
                    return
                ativos = captura_global.teclas_ativacao_ativas()
                if ativos:
                    if tentativa >= 100:  # dois segundos: falha fechada, sem tecla presa
                        self._log(
                            "⚠️ [BARRA:JOGO] abertura cancelada porque os "
                            "botões do atalho não foram soltos"
                        )
                        ocultar(restaurar_foco=False)
                        return
                    root.after(
                        20,
                        lambda: ativar_captura_sem_foco(geracao, tentativa + 1),
                    )
                    return

                captura_pronta = captura_global.iniciar()
                if not captura_pronta:
                    root.after(
                        20,
                        lambda: ativar_captura_sem_foco(geracao, tentativa + 1),
                    )
                    return
                modo_sem_foco["ativo"] = True
                self._publicar_estado_visual(True, entrada.get())
                self._log("⌨️ [BARRA:JOGO] sobreposição aberta sem tirar o foco do jogo")

                def expirar_sem_foco() -> None:
                    if (
                        modo_sem_foco["ativo"]
                        and geracao == geracao_foco["valor"]
                        and (root.state() != "withdrawn" or modo_externo["ativo"])
                    ):
                        self._log("⌨️ [BARRA:JOGO] sobreposição fechada pelo tempo limite de segurança")
                        ocultar(restaurar_foco=False)

                root.after(int(self._timeout_sem_foco_s * 1000), expirar_sem_foco)

            def abrir() -> None:
                estava_oculta = root.state() == "withdrawn"
                geracao_foco["valor"] += 1
                if estava_oculta:
                    janela_anterior["hwnd"] = obter_janela_ativa()
                tela_w = int(root.winfo_screenwidth())
                x = max(0, (tela_w - largura) // 2)
                y = max(36, int(root.winfo_screenheight() * 0.12))
                root.geometry(f"{largura}x{altura}+{x}+{y}")
                # Repetição do atalho enquanto a barra está visível apenas
                # devolve o foco; nunca apaga o que o usuário já digitou.
                if estava_oculta:
                    entrada.delete(0, "end")
                usar_sem_foco = bool(
                    self._sobreposicao_sem_foco_jogo
                    and (
                        self._modo_jogo_ativo()
                        or self._janela_ocupa_monitor(janela_anterior["hwnd"])
                    )
                )
                usar_visual_externo = False
                if usar_sem_foco:
                    try:
                        usar_visual_externo = bool(self._visual_externo_disponivel())
                    except Exception as erro:
                        self._relatar("visual_externo", erro)
                        usar_visual_externo = False
                if usar_visual_externo:
                    root.withdraw()
                    modo_externo["ativo"] = True
                    geracao_abertura = geracao_foco["valor"]
                    root.after(20, lambda: ativar_captura_sem_foco(geracao_abertura))
                elif usar_sem_foco and configurar_sem_ativar(True):
                    modo_externo["ativo"] = False
                    root.deiconify()
                    configurar_sem_ativar(True)
                    geracao_abertura = geracao_foco["valor"]
                    # O callback do atalho pode ocorrer quando Espaço já subiu,
                    # mas Ctrl/Shift ainda não. Só o hook de texto é instalado
                    # depois que todas essas solturas chegaram ao Windows.
                    root.after(20, lambda: ativar_captura_sem_foco(geracao_abertura))
                else:
                    captura_global.encerrar()
                    configurar_sem_ativar(False)
                    modo_sem_foco["ativo"] = False
                    modo_externo["ativo"] = False
                    root.deiconify()
                    root.lift()
                    root.attributes("-topmost", True)
                    entrada.focus_force()

            def ao_enviar(_evento: Any = None) -> str:
                if root.state() == "withdrawn":
                    return "break"
                texto = entrada.get()
                ocultar()
                self.enviar(texto)
                return "break"

            def ocultar_sem_foco(geracao: int) -> None:
                try:
                    if (
                        geracao == geracao_foco["valor"]
                        and root.state() != "withdrawn"
                        and not modo_sem_foco["ativo"]
                        and root.focus_get() is None
                    ):
                        ocultar(restaurar_foco=False)
                except Exception as erro:
                    self._relatar("verificacao_foco", erro)

            def consumir_fila() -> None:
                try:
                    while True:
                        acao = self._fila.get_nowait()
                        if acao == "abrir":
                            abrir()
                        elif acao == "fechar":
                            ocultar()
                        elif acao == "encerrar":
                            captura_global.encerrar()
                            root.destroy()
                            return
                except queue.Empty:
                    pass
                while True:
                    try:
                        acao_ui, valor = self._fila_interface.get_nowait()
                    except queue.Empty:
                        break
                    if acao_ui == "texto_global" and modo_sem_foco["ativo"]:
                        entrada.delete(0, "end")
                        entrada.insert(0, str(valor or ""))
                        self._publicar_estado_visual(True, str(valor or ""))
                    elif acao_ui == "enviar_global" and modo_sem_foco["ativo"]:
                        texto = str(valor or "")
                        ocultar(restaurar_foco=False)
                        self.enviar(texto)
                    elif acao_ui == "fechar_global" and modo_sem_foco["ativo"]:
                        ocultar(restaurar_foco=False)
                root.after(40, consumir_fila)

            entrada.bind("<Return>", ao_enviar)
            entrada.bind("<Escape>", lambda _evento: (ocultar(), "break")[1])
            root.bind("<Escape>", lambda _evento: (ocultar(), "break")[1])
            root.bind(
                "<FocusOut>",
                lambda _evento: root.after(
                    160,
                    lambda geracao=geracao_foco["valor"]: ocultar_sem_foco(geracao),
                ),
            )
            self._pronta.set()
            root.after(40, consumir_fila)
            root.mainloop()
        except Exception as exc:
            self._falha = f"{type(exc).__name__}: {exc}"
            self._pronta.set()
            self._log(f"⚠️ [BARRA] Interface indisponível: {self._falha}")
            self._relatar("interface", exc)
        finally:
            if captura_global is not None:
                captura_global.encerrar()
            self._interface_encerrada.set()

    def iniciar(self) -> bool:
        with self._estado_lock:
            if self._thread is not None and self._thread.is_alive():
                return True
            self._pronta.clear()
            self._interface_encerrada.clear()
            self._falha = ""
            self._thread = threading.Thread(
                target=self._executar_interface,
                name="Laylay-Barra-Comando",
                daemon=True,
            )
            self._thread.start()
        self._pronta.wait(timeout=2.0)
        return bool(self._thread.is_alive() and not self._falha)

    def solicitar_abertura(self) -> bool:
        if not self.iniciar():
            return False
        agora = float(self._clock())
        with self._estado_lock:
            if agora - self._ultima_abertura_ts <= 0.25:
                return True
            self._ultima_abertura_ts = agora
        self._log("⌨️ [BARRA] atalho detectado; preparando abertura segura")
        try:
            self._fila.put_nowait("abrir")
        except queue.Full:
            # Vários eventos do mesmo atalho representam uma única abertura.
            pass
        return True

    def registrar_hotkey(self) -> bool:
        with self._estado_lock:
            if self._hotkey_registrada:
                return True
        if not self.iniciar():
            return False
        try:
            if self._registrar_hotkey_nativo_windows():
                with self._estado_lock:
                    self._hotkey_registrada = True
                self._log(
                    f"⌨️ [BARRA] Atalho nativo registrado sem repassar ao jogo: {self.hotkey}"
                )
                return True
            try:
                self._hotkey_handle = self._keyboard.add_hotkey(
                    self.hotkey,
                    self.solicitar_abertura,
                    # Suprimir a combinação podia engolir o key-up de Ctrl ou
                    # Shift no backend Windows e deixar o sistema inteiro em
                    # estado de modificador preso.
                    suppress=False,
                    # Dispara no key-down, que é confiável no backend Windows.
                    # A captura em si ainda aguarda todos os key-ups antes de
                    # instalar o hook supressor.
                    trigger_on_release=False,
                )
            except TypeError:
                try:
                    self._hotkey_handle = self._keyboard.add_hotkey(
                        self.hotkey, self.solicitar_abertura, suppress=False,
                    )
                except TypeError:
                    self._hotkey_handle = self._keyboard.add_hotkey(
                        self.hotkey, self.solicitar_abertura,
                    )
            with self._estado_lock:
                self._hotkey_registrada = True
            self._log(f"⌨️ [BARRA] Atalho global registrado: {self.hotkey}")
            return True
        except Exception as exc:
            self._log(f"⚠️ [BARRA] Não consegui registrar {self.hotkey}: {exc}")
            self._relatar("registro_hotkey", exc)
            return False

    def encerrar(self, timeout_s: float = 1.0) -> None:
        """Libera hotkeys e encerra a interface respeitando a thread do Tk."""
        with self._estado_lock:
            self._hotkey_registrada = False
            handle, self._hotkey_handle = self._hotkey_handle, None
            thread = self._thread
            thread_hotkey = self._hotkey_nativa_thread
            id_hotkey = int(self._hotkey_nativa_id or 0)
        if handle is not None and callable(getattr(self._keyboard, "remove_hotkey", None)):
            try:
                self._keyboard.remove_hotkey(handle)
            except Exception as erro:
                self._relatar("liberacao_hotkey", erro)
        if id_hotkey and os.name == "nt":
            try:
                import ctypes

                ctypes.windll.user32.PostThreadMessageW(id_hotkey, 0x0012, 0, 0)
            except Exception as erro:
                self._relatar("liberacao_hotkey_nativo", erro)
        try:
            self._fila.put_nowait("encerrar")
        except queue.Full:
            try:
                self._fila.get_nowait()
            except queue.Empty:
                pass
            try:
                self._fila.put_nowait("encerrar")
            except queue.Full:
                pass
        prazo = time.monotonic() + max(0.0, float(timeout_s))
        thread_ativa = bool(
            thread is not None
            and callable(getattr(thread, "is_alive", None))
            and thread.is_alive()
        )
        if thread_ativa and thread is not threading.current_thread():
            self._interface_encerrada.wait(
                timeout=max(0.0, prazo - time.monotonic()),
            )
        for candidato in (thread, thread_hotkey):
            if (
                candidato is not None
                and callable(getattr(candidato, "join", None))
                and candidato is not threading.current_thread()
            ):
                try:
                    candidato.join(timeout=max(0.0, prazo - time.monotonic()))
                except (RuntimeError, TypeError):
                    pass


def criar_barra_comando_runtime(**kwargs: Any) -> BarraComandoRuntime:
    return BarraComandoRuntime(**kwargs)
