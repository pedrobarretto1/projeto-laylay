"""Persistência principal da memória da Laylay."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from mente_laylay.memoria_mental.identidade_usuario import (
    carregar_nome_usuario_confirmado,
    normalizar_nome_usuario,
)


POLITICA_PERSISTENCIA_MENTE = {
    "duravel": (
        "memoria_conversa",
        "estado_emocional",
        "topicos_recentes",
        "autoaprimoramento",
        "consciencia_temporal",
        "aprendizado_continuidade",
        "preferencias_musicais",
        "registro_semantico",
        "perfil_proatividade",
        "iniciativa_autonoma",
        "coordenador_oportunidades",
    ),
    "sessao": (
        "estado_musical",
        "percepcao",
        "conteudo_atual",
        "focos_por_dominio",
        "continuidade_geral",
    ),
    "efemero": (
        "continuidades",
        "promessas",
        "perguntas_abertas",
        "ultima_acao",
    ),
}


def sanitizar_aprendizado_oportunidades(valor: Any) -> Dict[str, Any]:
    """Persiste só os sinais agregados; decisões e textos da sessão ficam fora."""
    bruto = dict(valor or {}) if isinstance(valor, dict) else {}
    perfis_brutos = bruto.get("aprendizado")
    perfis: Dict[str, Any] = {}
    campos_numericos = (
        "aceitas", "recusadas", "silencios", "correcoes", "amostras",
        "dominancia", "sinal", "ajuste_utilidade", "ultima_resposta_ts",
    )
    if isinstance(perfis_brutos, dict):
        for chave, registro in list(perfis_brutos.items())[-40:]:
            if not isinstance(registro, dict):
                continue
            chave_limpa = str(chave or "").strip()[:120]
            if not chave_limpa:
                continue
            seguro: Dict[str, Any] = {}
            for campo in campos_numericos:
                valor_campo = registro.get(campo)
                if isinstance(valor_campo, (int, float)) and not isinstance(valor_campo, bool):
                    seguro[campo] = valor_campo
            for campo in ("status", "tipo", "ultima_resposta"):
                texto = str(registro.get(campo) or "").strip()[:40]
                if texto:
                    seguro[campo] = texto
            perfis[chave_limpa] = seguro

    contadores_brutos = bruto.get("contadores")
    contadores = {}
    if isinstance(contadores_brutos, dict):
        for campo in ("feedbacks", "aceitas", "recusadas", "silencios", "correcoes"):
            try:
                contadores[campo] = max(0, int(contadores_brutos.get(campo) or 0))
            except (TypeError, ValueError):
                contadores[campo] = 0
    return {"versao": 1, "aprendizado": perfis, "contadores": contadores}


def compactar_historico_mensagens(
    mensagens: Any,
    *,
    limite: int | None = None,
) -> list[Dict[str, Any]]:
    """Limita o histórico durável sem remover o contrato de sistema atual."""
    if limite is None:
        try:
            limite = int(os.environ.get("LAYLAY_MEMORIA_MAX_MENSAGENS", "240"))
        except ValueError:
            limite = 240
    limite = max(20, min(int(limite), 2000))
    validas = [
        dict(item)
        for item in (mensagens or [])
        if isinstance(item, dict) and str(item.get("role") or "").strip()
    ]
    sistemas = [item for item in validas if str(item.get("role")).casefold() == "system"]
    conversa = [item for item in validas if str(item.get("role")).casefold() != "system"]
    reserva = 1 if sistemas else 0
    return ([sistemas[-1]] if sistemas else []) + conversa[-max(1, limite - reserva):]


def carregar_memoria(memoria_sqlite, base_system_prompt: str):
    data = memoria_sqlite.carregar_estado()
    if not isinstance(data, dict):
        data = {}

    estado_auto = data.get("autoaprimoramento_estado")
    topicos_conversa_recente = [
        str(t).strip()
        for t in (data.get("topicos_conversa_recente") or [])
        if str(t).strip()
    ]
    ultimo_topico_conversa = str(data.get("ultimo_topico_conversa") or "").strip()
    try:
        ultimo_topico_ts = float(data.get("ultimo_topico_ts") or 0.0)
    except Exception:
        ultimo_topico_ts = 0.0
    mensagens = data.get("messages", [{"role": "system", "content": base_system_prompt}])
    if not isinstance(mensagens, list) or not mensagens:
        mensagens = [{"role": "system", "content": base_system_prompt}]
    mensagens = compactar_historico_mensagens(mensagens)
    if not mensagens:
        mensagens = [{"role": "system", "content": base_system_prompt}]
    # O contrato atual da mente sempre vence uma cópia antiga persistida. Sem
    # isso, melhorias no prompt só aparecem em instalações sem histórico.
    mensagens = [m for m in mensagens if str(m.get("role") or "").lower() != "system"]
    mensagens.insert(0, {"role": "system", "content": base_system_prompt})

    nome_usuario = carregar_nome_usuario_confirmado(memoria_sqlite)
    return {
        "messages": mensagens,
        "bordoes": data.get("bordoes", []),
        "resumo_conversa": data.get("resumo_conversa", ""),
        "memoria_fatos": data.get("memoria_fatos", []),
        "memoria_eventos": data.get("memoria_eventos", []),
        "historico_long_term": data.get("historico_long_term", ""),
        "current_emotion": data.get("current_emotion", data.get("emocao_atual", "calma")),
        "emotion_level": data.get("emotion_level", data.get("nivel_emocao", 1)),
        "emotion_cause": data.get("emotion_cause", "memória carregada"),
        "emotion_started_at": data.get("emotion_started_at", 0.0),
        "emotion_duration_s": data.get("emotion_duration_s", 0.0),
        "emotion_interactions_total": data.get("emotion_interactions_total", 0),
        "emotion_interactions_left": data.get("emotion_interactions_left", 0),
        "emotion_last_decay_at": data.get("emotion_last_decay_at", 0.0),
        "autoaprimoramento_estado": estado_auto if isinstance(estado_auto, dict) else None,
        "topicos_conversa_recente": topicos_conversa_recente,
        "ultimo_topico_conversa": ultimo_topico_conversa,
        "ultimo_topico_ts": ultimo_topico_ts,
        "consciencia_temporal": data.get("consciencia_temporal", {}),
        "aprendizado_continuidade": data.get("aprendizado_continuidade", {}),
        "preferencias_musicais": data.get("preferencias_musicais", {}),
        "registro_semantico": data.get("registro_semantico", {}),
        "perfil_proatividade": data.get("perfil_proatividade", {}),
        "iniciativa_autonoma": data.get("iniciativa_autonoma", {}),
        "coordenador_oportunidades": sanitizar_aprendizado_oportunidades(
            data.get("coordenador_oportunidades", {})
        ),
        "nome_usuario": nome_usuario,
    }


def salvar_memoria(memoria_sqlite, dados: Dict[str, Any]) -> None:
    memoria_sqlite.salvar_estado(**dict(dados))


def registrar_autocorrecao_virtual(
    memoria_sqlite,
    estado: Dict[str, Any],
    origem: str,
    erro: str,
    correcao: str,
    contexto: str = "",
    ajustar_humor_cb: Optional[Callable[[int, str], None]] = None,
    registrar_autoaprimoramento_cb: Optional[Callable[..., None]] = None,
) -> Dict[str, Any]:
    origem_limpa = str(origem or "desconhecido").strip()
    erro_limpo = str(erro or "").strip()
    correcao_limpa = str(correcao or "").strip()
    contexto_limpo = str(contexto or "").strip()

    if not erro_limpo and not correcao_limpa:
        return estado

    estado = dict(estado or {})
    estado["_autocorrecao_total"] = int(estado.get("_autocorrecao_total") or 0) + 1
    estado["_cookie_virtual_total"] = int(estado.get("_cookie_virtual_total") or 0) + 1
    eventos = list(estado.get("_autocorrecao_eventos") or [])
    evento = {
        "ts": datetime.now().isoformat(" "),
        "origem": origem_limpa,
        "erro": erro_limpo[:180],
        "correcao": correcao_limpa[:220],
        "contexto": contexto_limpo[:220],
        "cookie": estado["_cookie_virtual_total"],
    }
    eventos.append(evento)
    if len(eventos) > 20:
        eventos = eventos[-20:]
    estado["_autocorrecao_eventos"] = eventos

    resumo = (
        f"Autocorrecao #{estado['_autocorrecao_total']} em {origem_limpa}: "
        f"erro='{erro_limpo[:120]}' -> correcao='{correcao_limpa[:160]}'"
    )
    if contexto_limpo:
        resumo += f" | contexto={contexto_limpo[:120]}"

    try:
        memoria_sqlite.registrar_eventos([resumo])
    except Exception as e:
        print(f"⚠️ [AUTOCORREÇÃO] falha ao registrar evento: {e}")

    try:
        memoria_sqlite.salvar_resumo(f"{resumo} | cookie_virtual={estado['_cookie_virtual_total']}", tipo="autocorrecao")
    except Exception as e:
        print(f"⚠️ [AUTOCORREÇÃO] falha ao salvar resumo: {e}")

    try:
        memoria_sqlite.salvar_aprendizado_semantico(
            tipo="autocorrecao",
            gatilho=erro_limpo[:140] or origem_limpa,
            valor=correcao_limpa[:180],
            regra="Quando perceber um erro próprio, corrigir a resposta e tornar a correção visível.",
            texto_original=f"{origem_limpa}: {erro_limpo} => {correcao_limpa}",
            confianca=0.92,
            origem="autocorrecao_sistema",
            evidencia=f"{erro_limpo} => {correcao_limpa}",
            status="ativo",
        )
    except Exception as e:
        print(f"⚠️ [AUTOCORREÇÃO] falha ao salvar aprendizado: {e}")

    try:
        memoria_sqlite.salvar_aprendizado_semantico(
            tipo="correcao",
            gatilho=origem_limpa or erro_limpo[:120],
            valor=correcao_limpa[:180],
            regra="A correção ensinada pelo usuário deve ser reaproveitada em próximas respostas semelhantes.",
            texto_original=f"{origem_limpa}: {erro_limpo} => {correcao_limpa}",
            confianca=0.95,
            origem="autocorrecao_sistema",
            evidencia=f"{erro_limpo} => {correcao_limpa}",
            status="ativo",
        )
    except Exception as e:
        print(f"⚠️ [AUTOCORREÇÃO] falha ao salvar correção aprendida: {e}")

    try:
        memoria_sqlite.salvar_preferencia("laylay_cookie_virtual_total", str(estado["_cookie_virtual_total"]))
    except Exception:
        pass

    if callable(ajustar_humor_cb):
        try:
            ajustar_humor_cb(+1, "cookie virtual por autocorreção")
        except Exception:
            pass

    if callable(registrar_autoaprimoramento_cb):
        try:
            registrar_autoaprimoramento_cb(
                {},
                f"{origem_limpa} {erro_limpo} {correcao_limpa}",
                True,
                erro=erro_limpo,
                contexto=contexto_limpo,
                origem=origem_limpa,
            )
        except Exception as e:
            print(f"⚠️ [AUTOCORREÇÃO] falha ao registrar autoaprimoramento: {e}")

    print(f"🍪 [AUTOCORREÇÃO] cookie virtual #{estado['_cookie_virtual_total']} concedido para a Laylay.")
    return estado


class PersistenciaMemoriaRuntime:
    """Coordena SQLite e os domínios vivos da memória compartilhada."""

    def __init__(
        self,
        *,
        memoria_sqlite: Any,
        base_system_prompt: str,
        estado_obter: Callable[[str, str, Any], Any],
        estado_atualizar: Callable[..., Any],
        ajustar_humor_cb: Optional[Callable[[int, str], None]] = None,
        registrar_autoaprimoramento_cb: Optional[Callable[..., None]] = None,
        log: Callable[..., Any] = print,
    ) -> None:
        self.memoria_sqlite = memoria_sqlite
        self.base_system_prompt = str(base_system_prompt or "")
        self.estado_obter = estado_obter
        self.estado_atualizar = estado_atualizar
        self.ajustar_humor_cb = ajustar_humor_cb
        self.registrar_autoaprimoramento_cb = registrar_autoaprimoramento_cb
        self.log = log

    def _obter(self, dominio: str, chave: str, padrao: Any = None) -> Any:
        return self.estado_obter(dominio, chave, padrao)

    def _atualizar(self, dominio: str, **campos: Any) -> None:
        self.estado_atualizar(dominio, **campos)

    def carregar(self) -> tuple:
        data = carregar_memoria(self.memoria_sqlite, self.base_system_prompt)
        estado_auto = data.get("autoaprimoramento_estado")
        if isinstance(estado_auto, dict):
            self._atualizar("mental", autoaprimoramento_estado=estado_auto)
        estado_temporal = data.get("consciencia_temporal")
        if isinstance(estado_temporal, dict):
            self._atualizar("mental", consciencia_temporal=estado_temporal)
        preferencias_musicais = data.get("preferencias_musicais")
        if isinstance(preferencias_musicais, dict):
            self._atualizar("mental", preferencias_musicais=preferencias_musicais)
        aprendizado_continuidade = data.get("aprendizado_continuidade")
        if isinstance(aprendizado_continuidade, dict):
            self._atualizar(
                "mental",
                aprendizado_continuidade=aprendizado_continuidade,
                ultima_decisao_semantica={},
            )
        registro_semantico = data.get("registro_semantico")
        if isinstance(registro_semantico, dict):
            self._atualizar("mental", registro_semantico=registro_semantico)
        perfil_proatividade = data.get("perfil_proatividade")
        if isinstance(perfil_proatividade, dict):
            self._atualizar("mental", perfil_proatividade=perfil_proatividade)
        iniciativa_autonoma = data.get("iniciativa_autonoma")
        if isinstance(iniciativa_autonoma, dict):
            self._atualizar("mental", iniciativa_autonoma=iniciativa_autonoma)
        coordenador_oportunidades = data.get("coordenador_oportunidades")
        if isinstance(coordenador_oportunidades, dict):
            self._atualizar(
                "mental", coordenador_oportunidades=coordenador_oportunidades,
            )
        self._atualizar(
            "mental",
            nome_usuario=normalizar_nome_usuario(data.get("nome_usuario")),
        )

        self._atualizar(
            "conversacional",
            current_emotion=str(data.get("current_emotion") or "calma"),
            emotion_level=int(data.get("emotion_level") or 1),
            emotion_cause=str(data.get("emotion_cause") or "memória carregada"),
            emotion_started_at=float(data.get("emotion_started_at") or 0.0),
            emotion_duration_s=float(data.get("emotion_duration_s") or 0.0),
            emotion_interactions_total=int(data.get("emotion_interactions_total") or 0),
            emotion_interactions_left=int(data.get("emotion_interactions_left") or 0),
            emotion_last_decay_at=float(data.get("emotion_last_decay_at") or 0.0),
            topicos_conversa_recente=list(data.get("topicos_conversa_recente") or []),
            ultimo_topico_conversa=str(data.get("ultimo_topico_conversa") or "").strip(),
            ultimo_topico_ts=float(data.get("ultimo_topico_ts") or 0.0),
        )
        self._atualizar(
            "memoria_conversa",
            messages=data.get("messages", [{"role": "system", "content": self.base_system_prompt}]),
            bordoes=data.get("bordoes", []),
            resumo_conversa=data.get("resumo_conversa", ""),
            memoria_fatos=data.get("memoria_fatos", []),
            memoria_eventos=data.get("memoria_eventos", []),
            historico_long_term=data.get("historico_long_term", ""),
        )
        return (
            data.get("messages", [{"role": "system", "content": self.base_system_prompt}]),
            data.get("bordoes", []),
            data.get("resumo_conversa", ""),
            data.get("memoria_fatos", []),
            data.get("memoria_eventos", []),
            data.get("historico_long_term", ""),
            data.get("current_emotion", "calma"),
            data.get("emotion_level", 1),
        )

    def snapshot(self) -> Dict[str, Any]:
        return {
            "politica_persistencia_versao": 1,
            "messages": compactar_historico_mensagens(
                self._obter("memoria_conversa", "messages", [])
            ),
            "bordoes": self._obter("memoria_conversa", "bordoes", []),
            "resumo_conversa": self._obter("memoria_conversa", "resumo_conversa", ""),
            "memoria_fatos": self._obter("memoria_conversa", "memoria_fatos", []),
            "memoria_eventos": self._obter("memoria_conversa", "memoria_eventos", []),
            "historico_long_term": self._obter("memoria_conversa", "historico_long_term", ""),
            "current_emotion": self._obter("conversacional", "current_emotion", "calma"),
            "emotion_level": self._obter("conversacional", "emotion_level", 1),
            "emotion_cause": self._obter("conversacional", "emotion_cause", ""),
            "emotion_started_at": self._obter("conversacional", "emotion_started_at", 0.0),
            "emotion_duration_s": self._obter("conversacional", "emotion_duration_s", 0.0),
            "emotion_interactions_total": self._obter("conversacional", "emotion_interactions_total", 0),
            "emotion_interactions_left": self._obter("conversacional", "emotion_interactions_left", 0),
            "emotion_last_decay_at": self._obter("conversacional", "emotion_last_decay_at", 0.0),
            "humor_level": self._obter("conversacional", "humor_level", 0),
            "topicos_conversa_recente": self._obter("conversacional", "topicos_conversa_recente", []),
            "ultimo_topico_conversa": self._obter("conversacional", "ultimo_topico_conversa", ""),
            "ultimo_topico_ts": self._obter("conversacional", "ultimo_topico_ts", 0.0),
            "autoaprimoramento_estado": self._obter("mental", "autoaprimoramento_estado", {}),
            "consciencia_temporal": self._obter("mental", "consciencia_temporal", {}),
            "aprendizado_continuidade": self._obter(
                "mental", "aprendizado_continuidade", {}
            ),
            "preferencias_musicais": self._obter("mental", "preferencias_musicais", {}),
            "registro_semantico": self._obter("mental", "registro_semantico", {}),
            "perfil_proatividade": self._obter("mental", "perfil_proatividade", {}),
            "iniciativa_autonoma": self._obter("mental", "iniciativa_autonoma", {}),
            "coordenador_oportunidades": sanitizar_aprendizado_oportunidades(
                self._obter("mental", "coordenador_oportunidades", {})
            ),
            # Cópia de conveniência. A fonte de confiança continua sendo o
            # aprendizado semântico confirmado, carregado acima.
            "nome_usuario": normalizar_nome_usuario(
                self._obter("mental", "nome_usuario", "")
            ),
        }

    def salvar(self) -> bool:
        try:
            salvar_memoria(self.memoria_sqlite, self.snapshot())
            return True
        except Exception as erro:
            self.log(f"❌ Erro ao salvar memória: {erro}")
            return False

    def registrar_autocorrecao(self, origem: str, erro: str, correcao: str, contexto: str = "") -> None:
        estado = registrar_autocorrecao_virtual(
            self.memoria_sqlite,
            self._obter("mental", "autoaprimoramento_estado", {}),
            origem,
            erro,
            correcao,
            contexto=contexto,
            ajustar_humor_cb=self.ajustar_humor_cb,
            registrar_autoaprimoramento_cb=self.registrar_autoaprimoramento_cb,
        )
        self._atualizar("mental", autoaprimoramento_estado=estado)


def criar_persistencia_memoria_runtime(**kwargs: Any) -> PersistenciaMemoriaRuntime:
    return PersistenciaMemoriaRuntime(**kwargs)


def init_memoria_contexto_diaria(arquivo: str) -> Optional[str]:
    if not os.path.exists(arquivo):
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump({"data": str(datetime.now().date()), "bom_dia_dito": False}, f, ensure_ascii=False, indent=2)
        return "Bom dia. Pronta para mais um dia de dominação digital."

    with open(arquivo, "r", encoding="utf-8") as f:
        try:
            contexto = json.load(f)
        except Exception:
            contexto = {}

    hoje = str(datetime.now().date())
    if not isinstance(contexto, dict):
        contexto = {}
    if contexto.get("data") != hoje:
        contexto = {"data": hoje, "bom_dia_dito": False}
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(contexto, f, ensure_ascii=False, indent=2)
        return "Bom dia. Pronta para mais um dia de dominação digital."

    if not bool(contexto.get("bom_dia_dito", False)):
        contexto["bom_dia_dito"] = True
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(contexto, f, ensure_ascii=False, indent=2)
        return "Bom dia. Pronta para mais um dia de dominação digital."
    return None
