"""Janela transparente e independente do avatar da Laylay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import socket
import sys
import time
from typing import Any

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from mente_laylay.personalidade.avatar_runtime import (  # noqa: E402
    calcular_deslocamento_avatar,
    descobrir_assets_avatar,
    processo_pai_esta_ativo,
    resolver_asset_avatar,
)


FPS_ANIMACAO = 15
INTERVALO_ANIMACAO_MS = round(1000 / FPS_ANIMACAO)


class JanelaAvatar:
    def __init__(
        self,
        *,
        porta: int,
        pasta_assets: Path,
        estado_path: Path,
        tamanho: int,
        parent_pid: int = 0,
        parent_started: float = 0.0,
    ) -> None:
        import tkinter as tk
        from PIL import Image, ImageTk

        self.tk = tk
        self.Image = Image
        self.ImageTk = ImageTk
        self.assets = descobrir_assets_avatar(pasta_assets)
        self.estado_path = estado_path
        self.tamanho = max(120, min(520, int(tamanho)))
        self.parent_pid = max(0, int(parent_pid or 0))
        self.parent_started = max(0.0, float(parent_started or 0.0))
        self._proxima_verificacao_pai = 0.0
        self.emocao = "calma"
        self.falando = False
        self._emocao_pendente = ""
        self._troca_emocao_agendada: str | None = None
        self._frame_atual = ""
        self._inicio_animacao = time.monotonic()
        self._inicio_arraste: tuple[int, int, int, int] | None = None
        self._imagens_tk: dict[tuple[str, int], Any] = {}

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("127.0.0.1", int(porta)))
        self.socket.setblocking(False)

        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("Avatar da Laylay")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.cor_transparente = "#010203"
        self.root.configure(bg=self.cor_transparente)
        try:
            self.root.wm_attributes("-transparentcolor", self.cor_transparente)
        except tk.TclError:
            pass

        self.canvas = tk.Canvas(
            self.root,
            width=self.tamanho,
            height=self.tamanho,
            bg=self.cor_transparente,
            highlightthickness=0,
            borderwidth=0,
        )
        self.canvas.pack()
        self.item_imagem = self.canvas.create_image(
            self.tamanho // 2,
            self.tamanho // 2,
            anchor="center",
        )
        self._criar_menu()
        self._vincular_eventos()
        self._posicionar()
        self._mostrar_frame(forcar=True)
        self.root.deiconify()
        self.root.after(50, self._ler_eventos)
        self.root.after(INTERVALO_ANIMACAO_MS, self._animar_movimento)

    def executar(self) -> None:
        try:
            self.root.mainloop()
        finally:
            self._salvar_estado()
            try:
                self.socket.close()
            except OSError:
                pass

    def _criar_menu(self) -> None:
        tk = self.tk
        self.sempre_visivel = tk.BooleanVar(value=True)
        self.movimento_sutil = tk.BooleanVar(value=True)
        self.opacidade = 1.0
        self.menu = tk.Menu(self.root, tearoff=False)
        self.menu.add_checkbutton(
            label="Sempre visível",
            variable=self.sempre_visivel,
            command=lambda: self.root.attributes("-topmost", self.sempre_visivel.get()),
        )
        submenu = tk.Menu(self.menu, tearoff=False)
        for tamanho in (180, 230, 300, 400):
            submenu.add_command(label=f"{tamanho} px", command=lambda valor=tamanho: self._redimensionar(valor))
        self.menu.add_cascade(label="Tamanho", menu=submenu)
        self.menu.add_checkbutton(
            label="Movimento sutil",
            variable=self.movimento_sutil,
            command=self._alternar_movimento,
        )
        submenu_opacidade = tk.Menu(self.menu, tearoff=False)
        for percentual in (100, 90, 80, 70):
            submenu_opacidade.add_command(
                label=f"{percentual}%",
                command=lambda valor=percentual: self._alterar_opacidade(valor / 100.0),
            )
        self.menu.add_cascade(label="Opacidade", menu=submenu_opacidade)
        self.menu.add_command(label="Voltar ao canto", command=self._voltar_ao_canto)
        self.menu.add_separator()
        self.menu.add_command(label="Fechar avatar", command=self._fechar)

    def _vincular_eventos(self) -> None:
        for alvo in (self.root, self.canvas):
            alvo.bind("<ButtonPress-1>", self._iniciar_arraste)
            alvo.bind("<B1-Motion>", self._arrastar)
            alvo.bind("<ButtonRelease-1>", self._terminar_arraste)
            alvo.bind("<Button-3>", self._abrir_menu)

    def _posicionar(self) -> None:
        estado = self._carregar_estado()
        tamanho_salvo = estado.get("size")
        if isinstance(tamanho_salvo, int) and 120 <= tamanho_salvo <= 520:
            self.tamanho = tamanho_salvo
            self.canvas.configure(width=self.tamanho, height=self.tamanho)
            self.canvas.coords(self.item_imagem, self.tamanho // 2, self.tamanho // 2)
        self.movimento_sutil.set(bool(estado.get("motion", True)))
        self._alterar_opacidade(estado.get("opacity", 1.0), salvar=False)
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        x_padrao = largura_tela - self.tamanho - 24
        y_padrao = altura_tela - self.tamanho - 64
        x = self._limitar(estado.get("x", x_padrao), 0, max(0, largura_tela - 40))
        y = self._limitar(estado.get("y", y_padrao), 0, max(0, altura_tela - 40))
        self.root.geometry(f"{self.tamanho}x{self.tamanho}+{x}+{y}")

    def _arquivo_frame(self) -> Path:
        return resolver_asset_avatar(self.assets, self.emocao, falando=self.falando)

    def _mostrar_frame(self, *, forcar: bool = False) -> None:
        caminho = self._arquivo_frame()
        chave_frame = f"{caminho}:{self.tamanho}"
        if not forcar and chave_frame == self._frame_atual:
            return
        chave_cache = (str(caminho), self.tamanho)
        imagem_tk = self._imagens_tk.get(chave_cache)
        if imagem_tk is None:
            imagem = self.Image.open(caminho).convert("RGBA")
            imagem.thumbnail((self.tamanho, self.tamanho), self.Image.Resampling.LANCZOS)
            imagem_tk = self.ImageTk.PhotoImage(imagem)
            self._imagens_tk[chave_cache] = imagem_tk
        self.canvas.itemconfigure(self.item_imagem, image=imagem_tk)
        self._frame_atual = chave_frame

    def _animar_movimento(self) -> None:
        try:
            deslocamento = calcular_deslocamento_avatar(
                time.monotonic() - self._inicio_animacao,
                falando=self.falando,
                movimento_ativo=bool(self.movimento_sutil.get()),
            )
            self.canvas.coords(
                self.item_imagem,
                self.tamanho // 2,
                self.tamanho // 2 + deslocamento,
            )
            self.root.after(INTERVALO_ANIMACAO_MS, self._animar_movimento)
        except self.tk.TclError:
            pass

    def _aplicar_estado_visual(self, emocao: str, falando: bool) -> None:
        emocao = str(emocao or "calma")
        if falando:
            # A emoção da voz tem prioridade e precisa aparecer junto do áudio.
            if self._troca_emocao_agendada is not None:
                try:
                    self.root.after_cancel(self._troca_emocao_agendada)
                except self.tk.TclError:
                    pass
                self._troca_emocao_agendada = None
            self._emocao_pendente = ""
            self.emocao = emocao
            self.falando = True
            self._mostrar_frame()
            return

        # Fecha a boca imediatamente. A expressão parada espera alguns
        # milissegundos para evitar flashes em mudanças emocionais consecutivas.
        self.falando = False
        self._mostrar_frame()
        if emocao == self.emocao:
            if self._troca_emocao_agendada is not None:
                try:
                    self.root.after_cancel(self._troca_emocao_agendada)
                except self.tk.TclError:
                    pass
                self._troca_emocao_agendada = None
            self._emocao_pendente = ""
            return
        self._emocao_pendente = emocao
        if self._troca_emocao_agendada is not None:
            try:
                self.root.after_cancel(self._troca_emocao_agendada)
            except self.tk.TclError:
                pass
        self._troca_emocao_agendada = self.root.after(180, self._confirmar_emocao_pendente)

    def _confirmar_emocao_pendente(self) -> None:
        self._troca_emocao_agendada = None
        if not self._emocao_pendente or self.falando:
            return
        self.emocao = self._emocao_pendente
        self._emocao_pendente = ""
        self._mostrar_frame()

    def _ler_eventos(self) -> None:
        agora = time.monotonic()
        if self.parent_pid and agora >= self._proxima_verificacao_pai:
            self._proxima_verificacao_pai = agora + 0.35
            if not processo_pai_esta_ativo(self.parent_pid, self.parent_started):
                self._fechar()
                return
        try:
            while True:
                dados, _origem = self.socket.recvfrom(8192)
                mensagem = json.loads(dados.decode("utf-8"))
                if mensagem.get("type") == "shutdown":
                    self._fechar()
                    return
                if mensagem.get("type") == "state":
                    self._aplicar_estado_visual(
                        str(mensagem.get("emotion") or "calma"),
                        bool(mensagem.get("speaking", False)),
                    )
        except BlockingIOError:
            pass
        except (OSError, ValueError, UnicodeError):
            pass
        self.root.after(50, self._ler_eventos)

    def _iniciar_arraste(self, evento: Any) -> None:
        self._inicio_arraste = (evento.x_root, evento.y_root, self.root.winfo_x(), self.root.winfo_y())

    def _arrastar(self, evento: Any) -> None:
        if self._inicio_arraste is None:
            return
        mouse_x, mouse_y, janela_x, janela_y = self._inicio_arraste
        self.root.geometry(f"+{janela_x + evento.x_root - mouse_x}+{janela_y + evento.y_root - mouse_y}")

    def _terminar_arraste(self, _evento: Any) -> None:
        self._inicio_arraste = None
        self._salvar_estado()

    def _abrir_menu(self, evento: Any) -> None:
        try:
            self.menu.tk_popup(evento.x_root, evento.y_root)
        finally:
            self.menu.grab_release()

    def _redimensionar(self, tamanho: int) -> None:
        self.tamanho = max(120, min(520, int(tamanho)))
        self.canvas.configure(width=self.tamanho, height=self.tamanho)
        self.canvas.coords(self.item_imagem, self.tamanho // 2, self.tamanho // 2)
        self.root.geometry(f"{self.tamanho}x{self.tamanho}")
        self._frame_atual = ""
        self._mostrar_frame(forcar=True)
        self._salvar_estado()

    def _alternar_movimento(self) -> None:
        if not self.movimento_sutil.get():
            self.canvas.coords(self.item_imagem, self.tamanho // 2, self.tamanho // 2)
        self._salvar_estado()

    def _alterar_opacidade(self, valor: Any, *, salvar: bool = True) -> None:
        try:
            self.opacidade = max(0.4, min(1.0, float(valor)))
        except (TypeError, ValueError):
            self.opacidade = 1.0
        try:
            self.root.attributes("-alpha", self.opacidade)
        except self.tk.TclError:
            pass
        if salvar:
            self._salvar_estado()

    def _voltar_ao_canto(self) -> None:
        x = self.root.winfo_screenwidth() - self.tamanho - 24
        y = self.root.winfo_screenheight() - self.tamanho - 64
        self.root.geometry(f"+{max(0, x)}+{max(0, y)}")
        self._salvar_estado()

    def _fechar(self) -> None:
        self._salvar_estado()
        try:
            self.root.destroy()
        except self.tk.TclError:
            pass

    def _carregar_estado(self) -> dict[str, Any]:
        try:
            dados = json.loads(self.estado_path.read_text(encoding="utf-8"))
            return dados if isinstance(dados, dict) else {}
        except (OSError, ValueError):
            return {}

    def _salvar_estado(self) -> None:
        try:
            dados = {
                "x": self.root.winfo_x(),
                "y": self.root.winfo_y(),
                "size": self.tamanho,
                "motion": bool(self.movimento_sutil.get()),
                "opacity": self.opacidade,
            }
            self.estado_path.parent.mkdir(parents=True, exist_ok=True)
            temporario = self.estado_path.with_suffix(".tmp")
            temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
            temporario.replace(self.estado_path)
        except (OSError, self.tk.TclError):
            pass

    @staticmethod
    def _limitar(valor: Any, minimo: int, maximo: int) -> int:
        try:
            return max(minimo, min(maximo, int(valor)))
        except (TypeError, ValueError):
            return minimo


def _argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Avatar de tela da Laylay")
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--assets", required=True, type=Path)
    parser.add_argument("--state-file", required=True, type=Path)
    parser.add_argument("--size", default=230, type=int)
    parser.add_argument("--parent-pid", default=0, type=int)
    parser.add_argument("--parent-started", default=0.0, type=float)
    return parser.parse_args()


def main() -> int:
    args = _argumentos()
    try:
        JanelaAvatar(
            porta=args.port,
            pasta_assets=args.assets,
            estado_path=args.state_file,
            tamanho=args.size,
            parent_pid=args.parent_pid,
            parent_started=args.parent_started,
        ).executar()
        return 0
    except Exception as erro:
        print(f"[AVATAR] Falha ao abrir interface: {erro}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
