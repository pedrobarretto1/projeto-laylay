"""Coordenação entre análises visuais de jogo e a mente compartilhada."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, Mapping


class CoordenadorVisaoJogoRuntime:
    """Converte eventos visuais em memória, pendências e presença proativa."""

    def __init__(
        self,
        *,
        memoria_jogos: Any,
        observador_inventario_getter: Callable[[], Any],
        diretor_presenca_getter: Callable[[], Any],
        recomendar_playlist: Callable[[str], str],
        registrar_oportunidade: Callable[[Mapping[str, Any]], Any],
        decisao_permite_emissao: Callable[[Any], bool],
        agendar_fala: Callable[..., Any],
        registrar_mente_curta: Callable[..., Any],
        estado_mental_getter: Callable[[], Dict[str, Any]],
        estado_mental_substituir: Callable[[Dict[str, Any]], Any],
        criar_pendencia: Callable[..., Dict[str, Any]],
        registrar_pendencia: Callable[..., Dict[str, Any]],
        pendencia_ativa: Callable[..., Any],
        limpar_pendencia: Callable[..., Dict[str, Any]],
        salvar_memoria: Callable[[], Any],
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.memoria_jogos = memoria_jogos
        self.observador_inventario_getter = observador_inventario_getter
        self.diretor_presenca_getter = diretor_presenca_getter
        self.recomendar_playlist = recomendar_playlist
        self.registrar_oportunidade = registrar_oportunidade
        self.decisao_permite_emissao = decisao_permite_emissao
        self.agendar_fala = agendar_fala
        self.registrar_mente_curta = registrar_mente_curta
        self.estado_mental_getter = estado_mental_getter
        self.estado_mental_substituir = estado_mental_substituir
        self.criar_pendencia = criar_pendencia
        self.registrar_pendencia = registrar_pendencia
        self.pendencia_ativa = pendencia_ativa
        self.limpar_pendencia = limpar_pendencia
        self.salvar_memoria = salvar_memoria
        self.clock = clock

    def processar_sugestao_proativa(
        self,
        sugestao: Mapping[str, Any],
        identidade: Mapping[str, Any],
        perfil: Mapping[str, Any],
    ) -> bool:
        dados = dict(sugestao or {})
        identidade = dict(identidade or {})
        perfil = dict(perfil or {})
        fala = str(dados.get("fala") or "").strip()
        confianca = float(dados.get("confianca") or 0.0)
        categoria = str(dados.get("categoria") or "dica").strip().casefold()
        if categoria == "musica":
            fala = self.recomendar_playlist(
                str(dados.get("clima_musical") or "foco")
            )
        if not dados.get("relevante") or not fala or confianca < 0.72:
            return False

        chave = (
            f"inventario:{identidade.get('chave')}:{dados.get('slot')}:"
            f"{dados.get('item')}:{dados.get('motivo')}"
        )
        diretor = self.diretor_presenca_getter()
        if diretor is not None:
            evidencias = [
                str(dados.get(nome) or "").strip()
                for nome in ("item", "slot", "motivo")
                if str(dados.get(nome) or "").strip()
            ]
            evidencias.extend(
                str(item).strip() for item in list(dados.get("evidencias") or [])
                if str(item).strip()
            )
            evidencias = list(dict.fromkeys(evidencias))[:5]
            resultado = diretor.considerar({
                "origem": "visao_inventario_jogo",
                "dominio": "jogo",
                "categoria": categoria,
                "fala": fala,
                "confianca": confianca,
                "utilidade": 92 if str(dados.get("prioridade") or "").casefold()
                in {"alta", "urgente", "critica"} else 78,
                "evidencias": evidencias,
                "fundamentada": categoria != "dica" or len(evidencias) >= 2,
                "momento_seguro": bool(dados.get("momento_seguro", True)),
                "chave": chave,
                "emocao": "animada"
                if categoria in {"motivacao", "celebracao"} else "curiosa",
                "nivel": 2,
            })
            return str(resultado.get("status") or "") == "emitida"

        prioridade = str(dados.get("prioridade") or "normal").casefold()
        decisao = self.registrar_oportunidade({
            "origem": "visao_inventario_jogo",
            "tipo": "observacao",
            "dominio": "jogo",
            "objetivo": "melhorar_build_atual",
            "tags": [
                "jogo", "melhorar_build_atual", dados.get("slot"),
                perfil.get("classe"), perfil.get("build"),
            ],
            "item": dados.get("item"),
            "slot": dados.get("slot"),
            "confianca": confianca,
            "chave": chave,
            "utilidade": 92 if prioridade in {"alta", "urgente", "critica"} else 76,
            "risco": "baixo",
            "momento_seguro": True,
            "validade_s": 180.0,
        })
        if not self.decisao_permite_emissao(decisao):
            return False
        return bool(self.agendar_fala(
            "visao_jogo", fala, "curiosa", 2, mesclar_turno=True,
        ))

    def ao_mapear_inventario(
        self,
        identidade: Mapping[str, Any],
        inventario: Mapping[str, Any],
        imagem: str,
        proativo: bool,
    ) -> None:
        dados = dict(inventario or {})
        observador = self.observador_inventario_getter()
        if proativo:
            if not dados.get("tela_inventario_ativa"):
                observador.desarmar("inventário fechado")
            return
        if (
            dados.get("tela_inventario_ativa")
            and float(dados.get("confianca") or 0.0) >= 0.55
        ):
            observador.armar(
                jogo_chave=str(dict(identidade or {}).get("chave") or ""),
                imagem=str(imagem or ""),
            )

    def registrar_analise(self, evento: Mapping[str, Any]) -> None:
        dados = dict(evento or {})
        identidade = dict(dados.get("identidade") or {})
        perfil = dict(dados.get("perfil") or {})
        pergunta = str(dados.get("pergunta") or "").strip()
        resposta = str(dados.get("resposta") or "").strip()
        jogo = str(identidade.get("nome_candidato") or "jogo atual").strip()
        if not resposta:
            return
        self.registrar_mente_curta(
            pergunta,
            resposta,
            intencao="GAME_VISION",
            alvo=jogo,
            escopo="jogo",
            habilidade="visao_jogo",
        )
        estado_mental = dict(self.estado_mental_getter() or {})
        chave = str(identidade.get("chave") or "")
        estado_mental["contexto_jogo_atual"] = {
            "chave": chave,
            "jogo": jogo,
            "perfil": perfil,
            "ultima_duvida": pergunta[:500],
            "ultima_observacao": resposta[:1000],
            "memorias_recentes": self.memoria_jogos.listar_recentes(
                identidade, limite=5,
            ),
            "ts": self.clock(),
        }
        if bool(dados.get("solicita_complemento")):
            pendencia = self.criar_pendencia(
                origem="visao_jogo",
                tipo="complemento_visual",
                dominio="jogo",
                conteudo=resposta,
                resposta_esperada="detalhes_livres_do_jogo",
                intencao="GAME_VISION_CONTINUE",
                opcoes=[{"jogo_chave": chave, "jogo": jogo, "pergunta": pergunta}],
                ttl_s=900.0,
                foi_falada=True,
            )
            estado_mental = self.registrar_pendencia(estado_mental, pendencia)
        else:
            atual = self.pendencia_ativa(estado_mental, dominio="jogo")
            if atual and str(atual.get("origem") or "") == "visao_jogo":
                estado_mental = self.limpar_pendencia(
                    estado_mental, motivo="resolvida_por_complemento",
                )
        self.estado_mental_substituir(estado_mental)
        self.salvar_memoria()


def criar_coordenador_visao_jogo_runtime(**kwargs: Any) -> CoordenadorVisaoJogoRuntime:
    return CoordenadorVisaoJogoRuntime(**kwargs)
