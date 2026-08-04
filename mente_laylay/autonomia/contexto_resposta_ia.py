"""Montagem de contexto e prompt para a resposta da IA da Laylay."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

from mente_laylay.integracao.registro_conversa_llm import PacotePrompt

from mente_laylay.cognicao.contrato_fala import formatar_contrato_fala_para_prompt
from mente_laylay.cognicao.guardiao_realidade_pessoal import (
    detectar_experiencia_pessoal_inventada,
)
from mente_laylay.memoria_mental.identidade_usuario import contexto_identidade_usuario
from mente_laylay.personalidade.perfil_amizade import (
    formatar_postura_para_prompt,
    selecionar_postura_amizade,
)


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def preparar_contexto_resposta_ia(
    ctx: Dict[str, Any],
    texto: str,
    mensagens: List[Dict[str, Any]],
    humor_level: int,
    base_system_prompt: str,
) -> Tuple[List[Dict[str, Any]], str]:
    t = str(texto or "").strip()
    mensagens = list(mensagens or [])

    memoria_sqlite = _get(ctx, "memoria_sqlite")
    aba_titulo_atual = str(_get(ctx, "aba_titulo_atual", "") or "")
    aba_url_atual = str(_get(ctx, "aba_url_atual", "") or "")
    current_emotion = str(_get(ctx, "current_emotion", "calma") or "")
    get_status_humor_prompt = _get(ctx, "get_status_humor_prompt")
    resumo_mente_integrada_para_prompt = _get(ctx, "_resumo_mente_integrada_para_prompt")
    retrato_mente_integrada = str(_get(ctx, "retrato_mente_integrada", "") or "").strip()
    formatar_playlists_para_prompt = _get(ctx, "_formatar_playlists_para_prompt")
    contexto_habilidades = str(_get(ctx, "contexto_habilidades", "") or "").strip()
    contexto_recursos = str(_get(ctx, "contexto_recursos", "") or "").strip()
    contexto_identidade = str(_get(ctx, "contexto_identidade", "") or "").strip()
    contexto_postura = str(_get(ctx, "contexto_postura", "") or "").strip()
    contexto_contrato_fala = str(_get(ctx, "contexto_contrato_fala", "") or "").strip()

    contaminantes = ["adicionar_a_playlist", "editar_playlist", "tocar_playlist", "organizar_desktop", "maximize_window", "persona"]

    def _contaminada(msg: dict) -> bool:
        if msg.get("role") not in ("assistant", "user"):
            return False
        c = str(msg.get("content", ""))
        if (
            msg.get("role") == "assistant"
            and detectar_experiencia_pessoal_inventada(c)
        ):
            # A fala pode continuar no log para auditoria, mas não volta ao
            # prompt como se a própria invenção da assistente fosse memória.
            return True
        if msg.get("role") == "user" and not c.startswith("System:"):
            return False
        return any(tok in c for tok in contaminantes)

    mensagens = [m for m in mensagens if not _contaminada(m)]

    contexto_extra = (
        f"\n\n--- CONTEXTO ATUAL ---\n"
        f"Aba Atual: {aba_titulo_atual}\n"
        f"URL Atual: {aba_url_atual}\n"
    )

    try:
        if callable(formatar_playlists_para_prompt):
            playlists_txt = formatar_playlists_para_prompt()
            if playlists_txt:
                contexto_extra += f"Playlists Disponíveis: {playlists_txt}\n"
    except Exception:
        pass

    # O retrato da mente integrada já seleciona os aprendizados duradouros
    # relevantes. Memória quente e tópicos da sessão vêm do estado vivo e das
    # próprias mensagens abaixo; reler o snapshot SQLite aqui poderia reabrir
    # uma sessão encerrada e ainda duplicava o peso dessas informações.
    if retrato_mente_integrada:
        contexto_extra += "\n" + retrato_mente_integrada + "\n"
    else:
        try:
            if callable(resumo_mente_integrada_para_prompt):
                mente_unica = resumo_mente_integrada_para_prompt(t)
                if mente_unica:
                    contexto_extra += "\n" + mente_unica + "\n"
        except Exception:
            pass

    if contexto_habilidades:
        contexto_extra += "\n" + contexto_habilidades + "\n"
    if contexto_recursos:
        contexto_extra += "\n" + contexto_recursos + "\n"
    if contexto_identidade:
        contexto_extra += "\n" + contexto_identidade + "\n"
    if contexto_contrato_fala:
        contexto_extra += "\n" + contexto_contrato_fala + "\n"
    if contexto_postura:
        contexto_extra += "\n" + contexto_postura + "\n"

    liberdade_conversacional = (
        "\n\n--- AUTORIA DA CONVERSA ---\n"
        "A fala conversacional será entregue com suas palavras. Use o contexto abaixo, "
        "mas não deixe lembranças antigas substituírem a mensagem atual. O código externo "
        "não completará nem reescreverá sua personalidade.\n"
    )

    prompt_com_contexto = base_system_prompt + liberdade_conversacional + contexto_extra

    try:
        if memoria_sqlite is not None:
            memoria_resumida = memoria_sqlite.formatar_memoria_para_prompt(max_eventos=0)
            if memoria_resumida:
                prompt_com_contexto = prompt_com_contexto + "\n\n" + memoria_resumida
    except Exception:
        pass

    try:
        if callable(get_status_humor_prompt):
            status_humor = get_status_humor_prompt()
            prompt_com_humor = prompt_com_contexto.replace("{status_humor}", status_humor).replace("{humor_level}", str(humor_level))
        else:
            prompt_com_humor = prompt_com_contexto
    except Exception:
        prompt_com_humor = prompt_com_contexto

    if not mensagens:
        mensagens.append({"role": "system", "content": prompt_com_humor})
    else:
        if mensagens[0].get("role") == "system":
            mensagens[0]["content"] = prompt_com_humor
        else:
            mensagens.insert(0, {"role": "system", "content": prompt_com_humor})

    return mensagens, prompt_com_humor


class ContextoPromptRuntime:
    """Prepara o prompt ativo usando o retrato vivo da mesma mente."""

    def __init__(
        self,
        *,
        memoria_sqlite: Any,
        resumo_mente_integrada: Callable[[str], str],
        formatar_playlists: Callable[[], str],
        get_status_humor_prompt: Callable[[], str],
        base_system_prompt: str,
        estado_getter: Callable[[], Dict[str, Any]],
        mapa_habilidades_prompt: Callable[..., str] | None = None,
        mapa_recursos_prompt: Callable[[str], str] | None = None,
        registrar_tamanho_prompt: Callable[[str, int], Any] | None = None,
    ) -> None:
        self.memoria_sqlite = memoria_sqlite
        self.resumo_mente_integrada = resumo_mente_integrada
        self.formatar_playlists = formatar_playlists
        self.get_status_humor_prompt = get_status_humor_prompt
        self.base_system_prompt = str(base_system_prompt or "")
        self.estado_getter = estado_getter
        self.mapa_habilidades_prompt = mapa_habilidades_prompt
        self.mapa_recursos_prompt = mapa_recursos_prompt
        self.registrar_tamanho_prompt = registrar_tamanho_prompt
        self._preparacoes = 0
        self._preparacoes_rapidas = 0
        self._falhas = 0

    def preparar(self, texto: str) -> Tuple[List[Dict[str, Any]], str]:
        try:
            estado = self.estado_getter() or {}
        except Exception:
            estado = {}
        estado = estado if isinstance(estado, dict) else {}
        t = str(texto or "").strip()
        turno_atual = dict(estado.get("turno_atual") or {}) if isinstance(estado.get("turno_atual"), dict) else {}
        modalidade_turno = str(
            turno_atual.get("modalidade_geral") or turno_atual.get("modalidade") or ""
        ).lower()
        prompt_base_turno = self.base_system_prompt
        if modalidade_turno == "misto":
            segmentos = [
                str(item.get("modalidade") or item.get("ato") or "conversa")
                for item in list(turno_atual.get("segmentos") or [])
                if isinstance(item, dict)
            ]
            prompt_base_turno = (
                "INSTRUÇÃO PRIORITÁRIA DO TURNO ATUAL: o planejador detectou mais de um ato "
                f"na mesma mensagem ({segmentos or ['conversa', 'pergunta']}). "
                "Responda a todos em uma única fala coesa e preencha leitura_turno como lista com um tipo "
                "por ato, na mesma ordem. Não execute nada que o porteiro não autorizou.\n\n"
                + prompt_base_turno
            )
        retrato = self.resumo_mente_integrada(t)
        contexto_habilidades = ""
        if callable(self.mapa_habilidades_prompt):
            try:
                contexto_habilidades = str(
                    self.mapa_habilidades_prompt(t, turno=turno_atual) or ""
                ).strip()
            except Exception:
                contexto_habilidades = ""
        contexto_identidade = contexto_identidade_usuario(
            estado.get("nome_usuario", "")
        )
        postura = selecionar_postura_amizade(
            t,
            estado_mental=estado,
            operacional=bool(
                dict(
                    dict(estado.get("especialistas_turno_atual") or {}).get("operacional")
                    or {}
                ).get("ativo")
            ),
        )
        contexto_postura = formatar_postura_para_prompt(postura)
        contexto_contrato_fala = formatar_contrato_fala_para_prompt(
            estado.get("contrato_fala_atual")
        )
        contexto_recursos = ""
        if callable(self.mapa_recursos_prompt):
            try:
                contexto_recursos = str(self.mapa_recursos_prompt(t) or "").strip()
            except Exception:
                contexto_recursos = ""
        contexto = {
            "memoria_sqlite": self.memoria_sqlite,
            "retrato_mente_integrada": retrato,
            "_resumo_mente_integrada_para_prompt": self.resumo_mente_integrada,
            "aba_titulo_atual": estado.get("aba_titulo_atual", ""),
            "aba_url_atual": estado.get("aba_url_atual", ""),
            "_formatar_playlists_para_prompt": self.formatar_playlists,
            "get_status_humor_prompt": self.get_status_humor_prompt,
            "contexto_habilidades": contexto_habilidades,
            "contexto_recursos": contexto_recursos,
            "contexto_identidade": contexto_identidade,
            "contexto_contrato_fala": contexto_contrato_fala,
            "contexto_postura": contexto_postura,
        }
        try:
            resultado = preparar_contexto_resposta_ia(
                contexto,
                t,
                estado.get("messages") or [],
                estado.get("humor_level", 0),
                prompt_base_turno,
            )
            if callable(self.registrar_tamanho_prompt):
                origens = {
                    "base": prompt_base_turno,
                    "mente": retrato,
                    "habilidades": contexto_habilidades,
                    "recursos": contexto_recursos,
                    "identidade": contexto_identidade,
                    "contrato_fala": contexto_contrato_fala,
                    "postura": contexto_postura,
                    "historico": estado.get("messages") or [],
                    "total": resultado[1],
                }
                for origem, conteudo in origens.items():
                    if isinstance(conteudo, list):
                        tamanho = sum(
                            len(str(item.get("content") or ""))
                            for item in conteudo if isinstance(item, dict)
                        )
                    else:
                        tamanho = len(str(conteudo or ""))
                    self.registrar_tamanho_prompt(f"prompt_{origem}", tamanho)
            self._preparacoes += 1
            return resultado
        except Exception:
            self._falhas += 1
            raise

    def preparar_pacote(self, texto: str) -> PacotePrompt:
        mensagens, prompt = self.preparar(texto)
        return PacotePrompt(
            mensagens=tuple(dict(item) for item in mensagens if isinstance(item, dict)),
            prompt_sistema=str(prompt or ""),
        )

    def preparar_instrucao_rapida(self, texto: str) -> str:
        """Entrega somente o contrato do turno para o payload rápido.

        O retorno é efêmero: não contém memória durável, não substitui o
        prompt-base e não autoriza ações. A resposta principal continua sendo
        produzida pela mesma LLM, sem uma chamada adicional.
        """
        try:
            estado = self.estado_getter() or {}
        except Exception:
            estado = {}
        estado = estado if isinstance(estado, dict) else {}
        try:
            instrucao = formatar_contrato_fala_para_prompt(
                estado.get("contrato_fala_atual"),
                compacto=True,
            )
            if instrucao and callable(self.registrar_tamanho_prompt):
                self.registrar_tamanho_prompt(
                    "prompt_contrato_fala_rapido", len(instrucao),
                )
            self._preparacoes_rapidas += 1
            return instrucao
        except Exception:
            self._falhas += 1
            raise

    def diagnostico(self) -> Dict[str, Any]:
        return {
            "disponivel": True,
            "preparacoes": self._preparacoes,
            "preparacoes_rapidas": self._preparacoes_rapidas,
            "falhas": self._falhas,
            "memoria_exposta": False,
            "autoriza_execucao": False,
        }


def criar_contexto_prompt_runtime(**kwargs: Any) -> ContextoPromptRuntime:
    return ContextoPromptRuntime(**kwargs)
