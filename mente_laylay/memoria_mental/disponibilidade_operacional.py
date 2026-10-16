"""Disponibilidade viva das habilidades, separada da saúde estrutural.

O runtime não executa probes nem ações. Ele consolida somente retratos já
produzidos pelos proprietários de cada capacidade e transforma pré-condições
observáveis em estados seguros para o mapa e para o diagnóstico.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping


class DisponibilidadeOperacionalRuntime:
    def __init__(
        self,
        *,
        navegador_leitura_getter: Callable[[], Mapping[str, Any]] | None = None,
        navegador_operacoes_getter: Callable[[], Mapping[str, Any]] | None = None,
        conversa_llm_getter: Callable[[], Mapping[str, Any]] | None = None,
        visao_leitura_getter: Callable[[], Mapping[str, Any]] | None = None,
        visao_analise_getter: Callable[[], Mapping[str, Any]] | None = None,
        area_transferencia_getter: Callable[[], Mapping[str, Any]] | None = None,
        caixa_entrada_getter: Callable[[], Mapping[str, Any]] | None = None,
        notificacoes_getter: Callable[[], Mapping[str, Any]] | None = None,
        gmail_getter: Callable[[], Mapping[str, Any]] | None = None,
        iot_getter: Callable[[], Mapping[str, Any]] | None = None,
        avatar_getter: Callable[[], Mapping[str, Any]] | None = None,
        rosto_oled_getter: Callable[[], Mapping[str, Any]] | None = None,
        corpo_motor_getter: Callable[[], Mapping[str, Any]] | None = None,
    ) -> None:
        self._getters = {
            "navegador_leitura": navegador_leitura_getter,
            "navegador_operacoes": navegador_operacoes_getter,
            "conversa_llm": conversa_llm_getter,
            "visao_leitura": visao_leitura_getter,
            "visao_analise": visao_analise_getter,
            "area_transferencia": area_transferencia_getter,
            "caixa_entrada": caixa_entrada_getter,
            "notificacoes": notificacoes_getter,
            "gmail": gmail_getter,
            "iot": iot_getter,
            "avatar": avatar_getter,
            "rosto_oled": rosto_oled_getter,
            "corpo_motor": corpo_motor_getter,
        }

    def _ler(self, nome: str) -> dict[str, Any]:
        getter = self._getters.get(nome)
        if not callable(getter):
            return {"_indisponivel": True, "_motivo": "diagnostico_ausente"}
        try:
            bruto = getter()
            return dict(bruto or {}) if isinstance(bruto, Mapping) else {}
        except Exception as erro:
            return {
                "_indisponivel": True,
                "_motivo": f"diagnostico_falhou:{type(erro).__name__.casefold()}",
            }

    @staticmethod
    def _registro(
        estado: str,
        *,
        motivo: str,
        ausentes: tuple[str, ...] = (),
        evidencia_recente: bool = False,
    ) -> dict[str, Any]:
        return {
            "estado": estado,
            "disponivel": estado in {"disponivel", "degradado"},
            "motivo": motivo,
            "ausentes": list(ausentes),
            "evidencia_recente": bool(evidencia_recente),
            "fonte": "diagnostico_runtime",
        }

    def snapshot(self) -> dict[str, Any]:
        leitura = self._ler("navegador_leitura")
        operacoes = self._ler("navegador_operacoes")
        conectado = bool(leitura.get("conectado"))
        browser_estrutural = bool(
            leitura.get("leitura_aba_disponivel")
            and leitura.get("listagem_disponivel")
            and operacoes.get("comandos_disponiveis")
            and operacoes.get("navegacao_disponivel")
        )
        if not browser_estrutural:
            navegador = self._registro(
                "indisponivel",
                motivo="contrato_navegador_incompleto",
                ausentes=("contrato_navegador",),
            )
        elif not conectado:
            navegador = self._registro(
                "indisponivel",
                motivo="chrome_desconectado",
                ausentes=("chrome_ws_conectado",),
            )
        else:
            navegador = self._registro(
                "disponivel", motivo="chrome_conectado", evidencia_recente=True,
            )

        llm = self._ler("conversa_llm")
        llm_estado = str(llm.get("estado") or "").casefold()
        modelo_ok = bool(llm.get("modelo_disponivel") and llm.get("estado_disponivel"))
        if not modelo_ok or llm_estado == "indisponivel":
            conversa = self._registro(
                "indisponivel",
                motivo="modelo_ou_provedor_indisponivel",
                ausentes=("modelo_ou_provedor",),
            )
        elif llm_estado == "degradado" or int(llm.get("falhas_consecutivas") or 0):
            conversa = self._registro(
                "degradado", motivo="backend_llm_degradado",
                evidencia_recente=bool(llm.get("requisicoes")),
            )
        else:
            conversa = self._registro(
                "disponivel", motivo="backend_llm_pronto",
                evidencia_recente=bool(llm.get("requisicoes")),
            )

        visao_leitura = self._ler("visao_leitura")
        visao_analise = self._ler("visao_analise")
        if not bool(visao_leitura.get("habilitado")):
            visao = self._registro(
                "indisponivel", motivo="visao_desabilitada",
                ausentes=("visao_habilitada",),
            )
        elif not bool(visao_leitura.get("credencial_disponivel")):
            visao = self._registro(
                "indisponivel", motivo="credencial_visao_ausente",
                ausentes=("credencial_visao",),
            )
        elif not bool(visao_analise.get("analise_disponivel")):
            visao = self._registro(
                "degradado", motivo="analise_visual_degradada",
                ausentes=("provedor_analise_visual",),
            )
        else:
            visao = self._registro(
                "disponivel", motivo="visao_configurada",
                evidencia_recente=bool(visao_leitura.get("analise_recente")),
            )

        clipboard_bruto = self._ler("area_transferencia")
        leitura_clipboard = bool(clipboard_bruto.get("leitura_disponivel"))
        clipboard = self._registro(
            "disponivel" if leitura_clipboard else "indisponivel",
            motivo="clipboard_pronto" if leitura_clipboard else "clipboard_sem_leitor",
            ausentes=() if leitura_clipboard else ("leitor_clipboard",),
            evidencia_recente=bool(clipboard_bruto.get("operacoes")),
        )

        caixa_bruta = self._ler("caixa_entrada")
        caixa_ok = bool(caixa_bruta.get("persistencia_disponivel"))
        caixa = self._registro(
            "disponivel" if caixa_ok else "indisponivel",
            motivo="caixa_persistente" if caixa_ok else "persistencia_caixa_indisponivel",
            ausentes=() if caixa_ok else ("persistencia_caixa",),
            evidencia_recente=bool(caixa_bruta.get("total")),
        )

        notificacoes_brutas = self._ler("notificacoes")
        notificacoes_ok = bool(notificacoes_brutas.get("persistencia_disponivel"))
        notificacoes = self._registro(
            "disponivel" if notificacoes_ok else "degradado",
            motivo=("central_notificacoes_persistente" if notificacoes_ok else "central_sem_persistencia_confirmada"),
            ausentes=() if notificacoes_ok else ("persistencia_notificacoes",),
            evidencia_recente=bool(notificacoes_brutas.get("eventos")),
        )
        gmail = self._ler("gmail")
        gmail_configurado = gmail.get("configurado") is True
        email = self._registro(
            "disponivel" if gmail_configurado else "indisponivel",
            motivo="gmail_configurado_sem_probe" if gmail_configurado else "gmail_sem_configuracao_confirmada",
            ausentes=() if gmail_configurado else ("configuracao_gmail",),
        )

        iot_bruto = self._ler("iot")
        iot_ok = bool(
            iot_bruto.get("configurado")
            and iot_bruto.get("provedor_disponivel")
            and int(iot_bruto.get("total_dispositivos") or 0) > 0
        )
        iot = self._registro(
            "disponivel" if iot_ok else "indisponivel",
            motivo="iot_configurado" if iot_ok else "iot_sem_precondicoes",
            ausentes=() if iot_ok else ("configuracao_ou_provedor_iot",),
            evidencia_recente=bool(iot_bruto.get("evidencia_recente")),
        )

        avatar_bruto = self._ler("avatar")
        preferencia = bool(avatar_bruto.get("preferencia_ativa"))
        recursos = bool(avatar_bruto.get("assets_disponiveis"))
        visual_ativo = bool(
            avatar_bruto.get("processo_ativo")
            or avatar_bruto.get("visual_externo_ativo")
        )
        if not preferencia:
            avatar = self._registro(
                "indisponivel", motivo="preferencia_desativada",
                ausentes=("preferencia_avatar_ativa",),
            )
        elif not recursos:
            avatar = self._registro(
                "indisponivel", motivo="assets_avatar_ausentes",
                ausentes=("assets_avatar",),
            )
        elif not visual_ativo:
            avatar = self._registro(
                "degradado", motivo="avatar_configurado_sem_processo",
                ausentes=("processo_ou_widget_avatar",),
            )
        else:
            avatar = self._registro(
                "disponivel", motivo="avatar_visual_ativo", evidencia_recente=True,
            )

        rosto_bruto = self._ler("rosto_oled")
        rosto_confirmado = rosto_bruto.get("aplicacao_confirmada") is True
        corpo_bruto = self._ler("corpo_motor")
        corpo_disponivel = corpo_bruto.get("disponivel") is True
        dominios = {
            "corpo_motor": {**self._registro(
                "disponivel" if corpo_disponivel else "indisponivel",
                motivo=str(corpo_bruto.get("motivo") or "requer_firmware_motor_habilitado_e_sessao_vigente"),
                evidencia_recente=corpo_disponivel,
            ), "companhia": dict(corpo_bruto.get("companhia") or {}), "experiencia": dict(corpo_bruto.get("experiencia") or {}),
                "rampa_suportada": corpo_bruto.get("rampa_suportada") is True,
                "sensores": dict(corpo_bruto.get("sensores") or {}),
                "imu": dict(corpo_bruto.get("imu") or {}),
                "saude":dict(corpo_bruto.get("saude") or {})},
            "rosto_oled": {**self._registro(
                "disponivel" if rosto_confirmado else "indisponivel",
                motivo=str(rosto_bruto.get("motivo") or "requer_porta_serial_e_ack_recente_do_firmware"),
                evidencia_recente=rosto_confirmado,
            ), "som": dict(rosto_bruto.get("som") or {}),
                "identidade_usb": dict(rosto_bruto.get("identidade_usb") or {}),
                "expressao": dict(rosto_bruto.get("expressao") or {})},
            "navegador": navegador,
            "conversa": conversa,
            "visao": visao,
            "area_transferencia": clipboard,
            "caixa_entrada": caixa,
            "email": email,
            "iot": iot,
            "avatar": avatar,
        }
        capacidades = {
            "EMAIL_DRAFT": self._registro(
                "disponivel" if gmail.get("rascunhos_locais") and gmail.get("modelo_disponivel") else "indisponivel",
                motivo="rascunhos_locais_com_modelo" if gmail.get("modelo_disponivel") else "modelo_email_indisponivel",
            ),
            "EMAIL_DRAFT_READ": self._registro(
                "disponivel" if gmail.get("rascunhos_locais") else "indisponivel",
                motivo="armazenamento_local_rascunhos",
            ),
            "CORPO_COMPANHIA": self._registro(
                "disponivel" if corpo_disponivel and (corpo_bruto.get("companhia") or {}).get("transporte_exigido") == "serial"
                and rosto_bruto.get("transporte") == "serial" else "indisponivel",
                motivo="companhia_exige_sessao_usb_pronta", evidencia_recente=corpo_disponivel,
            ),
            "RESUMIR_PAGINA": dict(navegador),
            "NOTIFICATIONS": dict(notificacoes),
        }
        return {
            "dominios": dominios,
            "capacidades": capacidades,
            "fonte": "diagnosticos_dos_runtimes",
            "probes_executados": False,
        }


def criar_disponibilidade_operacional_runtime(
    **kwargs: Any,
) -> DisponibilidadeOperacionalRuntime:
    return DisponibilidadeOperacionalRuntime(**kwargs)
