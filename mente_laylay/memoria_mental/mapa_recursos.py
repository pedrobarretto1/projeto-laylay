"""Catálogo seguro dos recursos internos conhecidos pela mente única.

O catálogo não entrega acesso livre ao sistema de arquivos. Cada recurso usa
um leitor específico, que decide quais dados podem entrar no prompt. Escritas
continuam pertencendo aos runtimes e executores responsáveis.
"""

from __future__ import annotations

import re
from threading import RLock
from typing import Any, Callable, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import (
    normalizar_texto_basico as _normalizar,
    texto_pede_opiniao,
)


class MapaRecursosRuntime:
    """Expõe somente retratos sanitizados de arquivos previamente registrados."""

    def __init__(self) -> None:
        self._recursos: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    @staticmethod
    def _termo_mencionado(consulta: str, termo: str) -> bool:
        """Aceita pequenas palavras de ligação dentro de um termo conhecido."""
        if termo in consulta:
            return True
        partes = termo.split()
        if len(partes) < 2:
            return False
        ligacao = r"(?:\s+(?:a|as|o|os|de|do|da|que|eu|estao|foram|minha|meu)){0,3}\s+"
        padrao = r"\b" + ligacao.join(re.escape(parte) for parte in partes) + r"\b"
        return bool(re.search(padrao, consulta))

    def registrar(
        self,
        nome: str,
        *,
        arquivo: str,
        descricao: str,
        termos: tuple[str, ...],
        leitor: Callable[[str], Mapping[str, Any]],
        escrita_via: str = "",
        intent_consulta: str = "",
        parametro_detalhe: str = "",
        executor_consulta: Callable[[dict[str, Any], str], bool] | None = None,
    ) -> None:
        chave = _normalizar(nome).replace(" ", "_")
        if not chave or not callable(leitor):
            raise ValueError("recurso interno inválido")
        with self._lock:
            self._recursos[chave] = {
                "nome": chave,
                "arquivo": str(arquivo or "").strip(),
                "descricao": str(descricao or "").strip(),
                "termos": tuple(_normalizar(item) for item in termos if _normalizar(item)),
                "leitor": leitor,
                "escrita_via": str(escrita_via or "").strip(),
                "intent_consulta": str(intent_consulta or "").upper().strip(),
                "parametro_detalhe": str(parametro_detalhe or "").strip(),
                "executor_consulta": executor_consulta if callable(executor_consulta) else None,
            }

    @staticmethod
    def _parece_pedido_de_dados(texto: str) -> bool:
        consulta = _normalizar(texto)
        if not consulta:
            return False
        # Um nome conhecido pelo catálogo (por exemplo, a playlist ``rock``)
        # não transforma uma pergunta de opinião numa consulta operacional.
        # Além de preservar a conversa, isto impede que o dado real citado
        # escolha silenciosamente uma habilidade só por compartilhar o nome.
        if texto_pede_opiniao(texto):
            return False
        # Negação, hipótese e perguntas sobre capacidade não autorizam nem
        # mesmo consultas locais. Elas pertencem à conversa/deliberação.
        if re.match(r"^(?:nao|nem)\s+(?:me\s+)?(?:fala|fale|diga|mostra|mostre|lista|liste)\b", consulta):
            return False
        if re.search(
            r"\b(?:voce|laylay|lay)\s+(?:consegue|pode|sabe|e capaz)\b|"
            r"\bse eu (?:pedir|mandar|quiser|quisesse)\b|"
            r"^(?:como|o que) (?:eu )?(?:faria|faco|posso|poderia)\b",
            consulta,
        ):
            return False
        return bool(
            "?" in str(texto or "")
            or re.search(
                r"^(?:o que|oque|quais?|quant[oa]s?|qual e|como esta|como ta|"
                r"mostra|mostre|lista|liste|fala|fale|diga|conte|"
                r"me mostra|me mostre|me lista|me liste|me fala|me fale|me diga|me conte|"
                r"quero ver|gostaria de ver|tem algo|ha algo)\b",
                consulta,
            )
        )

    def executar_consulta(self, resultado: Mapping[str, Any], texto: str) -> bool:
        """Executa um leitor registrado sem conhecer seu domínio concreto."""
        intent = str(resultado.get("intent") or "").upper().strip()
        if not intent:
            return False
        with self._lock:
            executores = [
                item.get("executor_consulta")
                for item in self._recursos.values()
                if str(item.get("intent_consulta") or "").upper().strip() == intent
                and callable(item.get("executor_consulta"))
            ]
        # Não escolhemos silenciosamente quando dois recursos afirmam executar
        # o mesmo intent. A ambiguidade deve seguir ao roteador normal.
        if len(executores) != 1:
            return False
        return bool(executores[0](dict(resultado), texto))

    def resolver_consulta(self, texto: str) -> dict[str, Any] | None:
        """Converte linguagem natural em consulta apenas com evidência real.

        Cada recurso registrado declara seu intent de leitura. Um nome citado
        só é aceito quando o leitor do próprio recurso o devolve em ``detalhe``.
        """
        if not self._parece_pedido_de_dados(texto):
            return None
        consulta = _normalizar(texto)
        with self._lock:
            recursos = [dict(item) for item in self._recursos.values()]
        detalhados: list[dict[str, Any]] = []
        gerais: list[tuple[int, dict[str, Any]]] = []
        for recurso in recursos:
            intent = str(recurso.get("intent_consulta") or "").upper().strip()
            if not intent:
                continue
            try:
                retrato = dict(recurso["leitor"](texto) or {})
            except Exception:
                continue
            parametros_retrato = retrato.get("parametros_consulta")
            parametros_retrato = (
                dict(parametros_retrato)
                if isinstance(parametros_retrato, Mapping) else {}
            )
            detalhe = retrato.get("detalhe") if isinstance(retrato.get("detalhe"), Mapping) else {}
            nome = str(detalhe.get("nome") or "").strip()
            if nome:
                params: dict[str, Any] = dict(parametros_retrato)
                parametro = str(recurso.get("parametro_detalhe") or "").strip()
                if parametro:
                    params[parametro] = nome
                detalhados.append({"intent": intent, "params": params})
                continue
            termos_encontrados = [
                termo for termo in recurso.get("termos") or ()
                if self._termo_mencionado(consulta, termo)
            ]
            if termos_encontrados:
                # Um termo específico ("playlists que você criou") precisa
                # vencer o termo genérico ("playlist") do recurso vizinho.
                # Empates continuam ambíguos e nunca escolhem silenciosamente.
                especificidade = max(
                    len(termo.split()) * 100 + len(termo)
                    for termo in termos_encontrados
                )
                gerais.append((
                    especificidade,
                    {"intent": intent, "params": parametros_retrato},
                ))
        # Um detalhe confirmado vence menções genéricas. Mais de um detalhe é
        # ambíguo e deve pedir esclarecimento, nunca escolher silenciosamente.
        if len(detalhados) == 1:
            return detalhados[0]
        if detalhados:
            return None
        if not gerais:
            return None
        melhor_pontuacao = max(pontuacao for pontuacao, _ in gerais)
        melhores = [resultado for pontuacao, resultado in gerais if pontuacao == melhor_pontuacao]
        return melhores[0] if len(melhores) == 1 else None

    @staticmethod
    def _formatar_retrato(retrato: Mapping[str, Any]) -> list[str]:
        linhas: list[str] = []
        playlists = retrato.get("playlists")
        if isinstance(playlists, list):
            partes = []
            for item in playlists[:30]:
                if not isinstance(item, Mapping):
                    continue
                nome = str(item.get("nome") or "").strip()
                total = int(item.get("total") or 0)
                if nome:
                    partes.append(f"{nome} ({total})")
            if partes:
                linhas.append("Conteúdo atual: " + ", ".join(partes) + ".")
        detalhe = retrato.get("detalhe")
        if isinstance(detalhe, Mapping):
            nome = str(detalhe.get("nome") or "").strip()
            titulos = [str(item).strip() for item in list(detalhe.get("titulos") or []) if str(item).strip()]
            if nome:
                linhas.append(
                    f"Detalhe confirmado de {nome}: "
                    + ("; ".join(titulos[:8]) if titulos else "nenhuma faixa cadastrada")
                    + "."
                )
        agendamentos = retrato.get("agendamentos")
        if isinstance(agendamentos, list):
            itens = []
            for item in agendamentos[:12]:
                if not isinstance(item, Mapping):
                    continue
                nome = str(item.get("nome") or "compromisso").strip()
                quando = str(item.get("quando") or "").strip()
                itens.append(f"{nome} — {quando}" if quando else nome)
            total = int(retrato.get("total_ativos") or len(itens))
            linhas.append(
                f"Agenda atual: {total} ativo(s)"
                + ("; " + "; ".join(itens) if itens else "")
                + "."
            )
        dispositivos = retrato.get("dispositivos")
        if isinstance(dispositivos, list):
            itens_iot = []
            for item in dispositivos[:20]:
                if not isinstance(item, Mapping):
                    continue
                nome = str(item.get("nome_amigavel") or item.get("nome") or "").strip()
                ambiente = str(item.get("ambiente") or "").strip()
                capacidades = [
                    str(valor).strip() for valor in item.get("capacidades") or ()
                    if str(valor).strip()
                ]
                if nome:
                    detalhe_iot = "; ".join(
                        trecho for trecho in (
                            ambiente,
                            "ações: " + ", ".join(capacidades) if capacidades else "",
                        ) if trecho
                    )
                    itens_iot.append(f"{nome} ({detalhe_iot})" if detalhe_iot else nome)
            linhas.append(
                "Dispositivos IoT configurados: "
                + ("; ".join(itens_iot) if itens_iot else "nenhum")
                + "."
            )
        notas = retrato.get("notas")
        if isinstance(notas, list):
            itens_notas = []
            for item in notas[:10]:
                if not isinstance(item, Mapping):
                    continue
                tipo = str(item.get("tipo") or "nota").replace("_", " ").strip()
                conteudo = re.sub(r"\s+", " ", str(item.get("conteudo") or "")).strip()
                if conteudo:
                    itens_notas.append(f"{tipo}: {conteudo[:240]}")
            linhas.append(
                "Caixa de entrada pessoal: "
                + ("; ".join(itens_notas) if itens_notas else "nenhuma nota ativa")
                + "."
            )
        pessoas = retrato.get("pessoas")
        if isinstance(pessoas, list):
            itens_pessoas = []
            for item in pessoas[:20]:
                if not isinstance(item, Mapping):
                    continue
                nome = str(item.get("nome") or "").strip()
                relacoes = [str(x).strip() for x in item.get("relacoes") or [] if str(x).strip()]
                if nome:
                    itens_pessoas.append(
                        f"{nome} ({', '.join(relacoes)})" if relacoes else nome
                    )
            linhas.append(
                "Pessoas lembradas: "
                + ("; ".join(itens_pessoas) if itens_pessoas else "nenhum perfil ativo")
                + "."
            )
        return linhas

    def contexto_para_prompt(self, texto: str) -> str:
        consulta = _normalizar(texto)
        pedido_catalogo = bool(re.search(
            r"\b(?:arquivos|recursos|dados) (?:internos|da laylay|da lay)\b",
            consulta,
        ))
        with self._lock:
            recursos = [dict(item) for item in self._recursos.values()]
        relevantes: list[tuple[dict[str, Any], Mapping[str, Any]]] = []
        pedido_dados = self._parece_pedido_de_dados(texto)
        for item in recursos:
            mencao_generica = any(
                self._termo_mencionado(consulta, termo)
                for termo in item.get("termos") or ()
            )
            retrato: Mapping[str, Any] = {}
            # Nomes como "trap" ou "kamaitachi" não carregam a palavra
            # "playlist". Numa pergunta de dados, deixamos o leitor controlado
            # confirmar se o nome pertence ao recurso antes de decidir a
            # relevância. Isso ancora o fallback da LLM nos dados verdadeiros.
            if pedido_catalogo or mencao_generica or pedido_dados:
                try:
                    retrato = item["leitor"](texto) or {}
                except Exception:
                    retrato = {}
            detalhe = retrato.get("detalhe") if isinstance(retrato, Mapping) else None
            detalhe_confirmado = bool(
                isinstance(detalhe, Mapping) and str(detalhe.get("nome") or "").strip()
            )
            if pedido_catalogo or mencao_generica or detalhe_confirmado:
                relevantes.append((item, retrato))
        if not relevantes:
            return ""
        linhas = [
            "--- RECURSOS INTERNOS RELEVANTES ---",
            "São fontes reais e controladas. Consulte o retrato abaixo; não invente conteúdo nem edite arquivos diretamente.",
        ]
        for recurso, retrato in relevantes[:5]:
            linhas.append(
                f"- {recurso['nome']} ({recurso['arquivo']}): {recurso['descricao']}."
            )
            if recurso.get("escrita_via"):
                linhas.append(
                    f"  Alterações somente pela habilidade {recurso['escrita_via']}, após o roteador autorizar."
                )
            linhas.extend("  " + linha for linha in self._formatar_retrato(retrato or {}))
        return "\n".join(linhas)

    def diagnostico(self) -> dict[str, Any]:
        with self._lock:
            recursos = list(self._recursos.values())
        return {
            "catalogados": len(recursos),
            "nomes": sorted(str(item.get("nome") or "") for item in recursos),
            "acesso_bruto": False,
        }


def criar_mapa_recursos_runtime() -> MapaRecursosRuntime:
    return MapaRecursosRuntime()
