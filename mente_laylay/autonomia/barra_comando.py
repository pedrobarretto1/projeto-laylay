"""Barra global e discreta para enviar comandos à mente única da Laylay."""

from __future__ import annotations

import queue
import threading
from typing import Any, Callable


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
    ) -> None:
        self._processar_texto = processar_texto
        self._keyboard = keyboard_mod
        self.hotkey = str(hotkey or "ctrl+shift+space").strip()
        self._log = log
        self._tkinter_mod = tkinter_mod
        self._fila: queue.Queue[str] = queue.Queue(maxsize=4)
        self._thread: threading.Thread | None = None
        self._pronta = threading.Event()
        self._falha = ""
        self._hotkey_registrada = False

    @staticmethod
    def normalizar_entrada(texto: str) -> str:
        return " ".join(str(texto or "").strip().split())

    def _despachar(self, texto: str) -> bool:
        entrada = self.normalizar_entrada(texto)
        if not entrada:
            return False
        self._log(f"⌨️ [BARRA] Pedro: {entrada}")
        try:
            self._processar_texto(entrada)
            return True
        except Exception as exc:
            self._log(f"⚠️ [BARRA] Não consegui enviar o comando: {exc}")
            return False

    def enviar(self, texto: str) -> bool:
        entrada = self.normalizar_entrada(texto)
        if not entrada:
            return False
        threading.Thread(
            target=self._despachar,
            args=(entrada,),
            name="Laylay-Barra-Comando-Envio",
            daemon=True,
        ).start()
        return True

    def _carregar_tk(self) -> Any:
        if self._tkinter_mod is not None:
            return self._tkinter_mod
        import tkinter  # import tardio: a Laylay continua iniciando se o Tk falhar

        return tkinter

    def _executar_interface(self) -> None:
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
                except Exception:
                    pass

            def ocultar(*, restaurar_foco: bool = True) -> None:
                entrada.delete(0, "end")
                root.withdraw()
                if restaurar_foco:
                    root.after(30, devolver_foco)

            def abrir() -> None:
                if root.state() == "withdrawn":
                    janela_anterior["hwnd"] = obter_janela_ativa()
                tela_w = int(root.winfo_screenwidth())
                x = max(0, (tela_w - largura) // 2)
                y = max(36, int(root.winfo_screenheight() * 0.12))
                root.geometry(f"{largura}x{altura}+{x}+{y}")
                entrada.delete(0, "end")
                root.deiconify()
                root.lift()
                root.attributes("-topmost", True)
                entrada.focus_force()

            def ao_enviar(_evento: Any = None) -> str:
                texto = entrada.get()
                ocultar()
                self.enviar(texto)
                return "break"

            def ocultar_sem_foco() -> None:
                try:
                    if root.state() != "withdrawn" and root.focus_get() is None:
                        ocultar(restaurar_foco=False)
                except Exception:
                    pass

            def consumir_fila() -> None:
                try:
                    while True:
                        acao = self._fila.get_nowait()
                        if acao == "abrir":
                            abrir()
                        elif acao == "fechar":
                            ocultar()
                except queue.Empty:
                    pass
                root.after(40, consumir_fila)

            entrada.bind("<Return>", ao_enviar)
            entrada.bind("<Escape>", lambda _evento: (ocultar(), "break")[1])
            root.bind("<Escape>", lambda _evento: (ocultar(), "break")[1])
            root.bind("<FocusOut>", lambda _evento: root.after(160, ocultar_sem_foco))
            self._pronta.set()
            root.after(40, consumir_fila)
            root.mainloop()
        except Exception as exc:
            self._falha = f"{type(exc).__name__}: {exc}"
            self._pronta.set()
            self._log(f"⚠️ [BARRA] Interface indisponível: {self._falha}")

    def iniciar(self) -> bool:
        if self._thread is not None and self._thread.is_alive():
            return True
        self._pronta.clear()
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
        try:
            self._fila.put_nowait("abrir")
        except queue.Full:
            # Vários eventos do mesmo atalho representam uma única abertura.
            pass
        return True

    def registrar_hotkey(self) -> bool:
        if self._hotkey_registrada:
            return True
        if not self.iniciar():
            return False
        try:
            try:
                self._keyboard.add_hotkey(
                    self.hotkey,
                    self.solicitar_abertura,
                    suppress=True,
                    trigger_on_release=True,
                )
            except TypeError:
                self._keyboard.add_hotkey(self.hotkey, self.solicitar_abertura)
            self._hotkey_registrada = True
            self._log(f"⌨️ [BARRA] Atalho global registrado: {self.hotkey}")
            return True
        except Exception as exc:
            self._log(f"⚠️ [BARRA] Não consegui registrar {self.hotkey}: {exc}")
            return False


def criar_barra_comando_runtime(**kwargs: Any) -> BarraComandoRuntime:
    return BarraComandoRuntime(**kwargs)
