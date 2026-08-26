"""Transporte de buscas e URLs musicais entre o PC local e o PC B."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
from urllib.parse import urlparse

from mente_laylay.percepcao.modo_jogo import pedido_foco_explicito


@dataclass(slots=True)
class RotaMusical:
    ctx: Dict[str, Any]
    destino: str = "pc_a"
    texto_original: str = ""

    def abrir(self, url: str, *, query: str = "") -> bool:
        return bool(self.abrir_detalhado(url, query=query).get("ok"))

    @staticmethod
    def _preservar_entrega_video(
        retorno: dict[str, Any], url: str,
    ) -> dict[str, Any]:
        """Separa navegação confirmada de reprodução confirmada.

        ``autoplay_blocked`` é emitido pela extensão somente depois que a aba
        terminou de abrir o vídeo e ela tentou iniciar o player. Logo, existe
        execução parcial observável mesmo sem confirmação de áudio.
        """
        resultado = dict(retorno or {})
        status = str(resultado.get("status") or "").strip()
        if status == "autoplay_blocked":
            resultado["ok"] = True
            # A navegação foi observada, mas o estado final do áudio não.
            # ``False`` significaria falha total para o contrato da mente;
            # ``None`` conserva corretamente uma execução parcial.
            resultado["confirmado"] = None
            resultado["status"] = "video_aberto_sem_confirmacao"
            resultado.setdefault(
                "message", "O vídeo abriu, mas o player não confirmou o áudio",
            )
        resultado.setdefault("url", url)
        return resultado

    def abrir_detalhado(self, url: str, *, query: str = "") -> dict[str, Any]:
        """Executa a rota preservando confirmação e evidência do navegador."""
        url_limpa = str(url or "").strip()
        if not url_limpa:
            return {
                "ok": False, "confirmado": False, "status": "url_ausente",
            }
        enviar_pc_b = self.ctx.get("_enviar_pc_b")
        navegador = self.ctx.get("_registro_navegador_operacoes_runtime")
        permitir_foco = pedido_foco_explicito(self.texto_original)

        if self.destino == "pc_b" and callable(enviar_pc_b):
            enviar_pc_b({"action": "open_url", "url": url_limpa})
            return {
                "ok": True,
                "confirmado": None,
                "status": "enviado_pc_b",
                "url": url_limpa,
            }

        eh_video_youtube = self._eh_video_youtube(url_limpa)

        if self.destino == "ambos":
            ok_local = False
            evidencia_local: dict[str, Any] = {}
            if eh_video_youtube and navegador is not None:
                tocar_detalhado = getattr(
                    navegador, "tocar_youtube_detalhado", None,
                )
                if callable(tocar_detalhado):
                    evidencia_local = self._preservar_entrega_video(
                        dict(tocar_detalhado(
                            url_limpa, permitir_foco=permitir_foco,
                        ) or {}),
                        url_limpa,
                    )
                    ok_local = bool(evidencia_local.get("ok"))
                else:
                    ok_local = bool(navegador.tocar_youtube(
                        url_limpa, permitir_foco=permitir_foco,
                    ))
            elif query and navegador is not None:
                ok_local = bool(navegador.pesquisar_youtube(
                    query, permitir_foco=permitir_foco,
                ))
            elif navegador is not None:
                try:
                    retorno = navegador.abrir_url(
                        url_limpa,
                        auto_click=False,
                        permitir_foco=permitir_foco,
                    )
                    ok_local = retorno is not False
                except Exception:
                    ok_local = False
            if callable(enviar_pc_b):
                enviar_pc_b({"action": "open_url", "url": url_limpa})
            return {
                **evidencia_local,
                "ok": ok_local,
                # O resultado conjunto não pode ser confirmado apenas pelo
                # player local enquanto o PC remoto permanece sem retorno.
                "confirmado": None,
                "status": str(
                    evidencia_local.get("status") or "enviado_ambos"
                ),
                "url": url_limpa,
            }

        if eh_video_youtube and navegador is not None:
            tocar_detalhado = getattr(navegador, "tocar_youtube_detalhado", None)
            if callable(tocar_detalhado):
                return self._preservar_entrega_video(
                    dict(tocar_detalhado(
                        url_limpa, permitir_foco=permitir_foco,
                    ) or {}),
                    url_limpa,
                )
            ok = bool(navegador.tocar_youtube(
                url_limpa, permitir_foco=permitir_foco,
            ))
            return {
                "ok": ok,
                "confirmado": True if ok else False,
                "status": "confirmacao_legada" if ok else "falha_execucao",
                "url": url_limpa,
            }
        if query and navegador is not None:
            ok = bool(navegador.pesquisar_youtube(
                query, permitir_foco=permitir_foco,
            ))
            return {
                "ok": ok,
                "confirmado": False,
                "status": "pagina_busca_aberta" if ok else "falha_execucao",
                "url": url_limpa,
            }
        if navegador is not None:
            try:
                retorno = navegador.abrir_url(
                    url_limpa,
                    auto_click=False,
                    permitir_foco=permitir_foco,
                )
                ok = retorno is not False
                return {
                    "ok": ok,
                    "confirmado": None if ok else False,
                    "status": "url_enviada" if ok else "falha_execucao",
                    "url": url_limpa,
                }
            except Exception:
                return {
                    "ok": False, "confirmado": False,
                    "status": "falha_execucao", "url": url_limpa,
                }
        return {
            "ok": False, "confirmado": False,
            "status": "navegador_indisponivel", "url": url_limpa,
        }

    @staticmethod
    def _eh_video_youtube(url: str) -> bool:
        try:
            parsed = urlparse(str(url or ""))
            host = parsed.netloc.casefold().removeprefix("www.")
            return (
                host == "youtu.be"
                or (host.endswith("youtube.com") and parsed.path.startswith("/watch"))
            )
        except Exception:
            return False
