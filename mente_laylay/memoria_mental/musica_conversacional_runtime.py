"""Runtime da conversa musical da Laylay.

Mantem a opiniao musical conversacional ligada ao mesmo estado mental, sem
transformar recomendacao vaga em comando tecnico automaticamente.
"""

from __future__ import annotations

import json
import random
import re
import time
from typing import Any, Callable, Dict

from mente_laylay.memoria_mental.musica_conversacional import (
    sugestao_musical_nova_conversacional,
    texto_pede_direcao_musical_generica,
)


class MusicaConversacionalRuntime:
    def __init__(
        self,
        *,
        estado_mental_getter: Callable[[], Dict[str, Any]],
        normalizar_texto: Callable[[str], str],
        falar: Callable[[str, str, int], Any],
        registrar_mente_curta: Callable[..., Any],
        executar_intencao: Callable[[dict, str], bool],
        registrar_resultado_execucao: Callable[..., Any],
        registrar_autoaprimoramento: Callable[..., Any] | None = None,
        enviar_mensagem: Callable[..., Any] | None = None,
        log: Callable[[str], None] | None = None,
    ) -> None:
        self.estado_mental_getter = estado_mental_getter
        self.normalizar_texto = normalizar_texto
        self.falar = falar
        self.registrar_mente_curta = registrar_mente_curta
        self.executar_intencao = executar_intencao
        self.registrar_resultado_execucao = registrar_resultado_execucao
        self.registrar_autoaprimoramento = registrar_autoaprimoramento
        self.enviar_mensagem = enviar_mensagem
        self.log = log or print
        self._sugestao_pendente: Dict[str, Any] = {}

    def _estado(self) -> Dict[str, Any]:
        try:
            estado = self.estado_mental_getter()
            return dict(estado or {}) if isinstance(estado, dict) else {}
        except Exception:
            return {}

    def texto_pede_direcao(self, texto: str) -> bool:
        return texto_pede_direcao_musical_generica(
            texto,
            estado_mental=self._estado(),
            normalizar_texto=self.normalizar_texto,
        )

    def texto_pede_opiniao_atual(self, texto: str) -> bool:
        t = self.normalizar_texto(texto)
        pede_opiniao = any(p in t for p in [
            "o que voce acha", "o que você acha", "o que achou", "voce achou", "você achou",
            "voce gostou", "você gostou", "sua opiniao", "sua opinião", "o que pensa",
        ])
        referencia_musica = any(p in t for p in [
            "dessa musica", "dessa música", "da musica", "da música", "desse som",
            "dessa faixa", "musica que ta tocando", "música que tá tocando", "isso que ta tocando",
        ])
        return bool(pede_opiniao and referencia_musica)

    @staticmethod
    def _extrair_fala_json(resposta: Any) -> str:
        bruto = str(resposta or "").strip()
        try:
            dados = json.loads(bruto)
            return str(dados.get("fala") or "").strip() if isinstance(dados, dict) else ""
        except Exception:
            achado = re.search(r"\{.*\}", bruto, re.DOTALL)
            if not achado:
                return ""
            try:
                dados = json.loads(achado.group(0))
                return str(dados.get("fala") or "").strip() if isinstance(dados, dict) else ""
            except Exception:
                return ""

    def responder_opiniao_atual(self, texto: str = "") -> bool:
        estado = self._estado()
        titulo = re.sub(r"^\(\d+\)\s*", "", str(estado.get("musica_atual_titulo") or "")).strip()
        titulo = titulo.replace(" - YouTube", "").strip()
        if not titulo:
            fala = "Eu entendi que você quer minha opinião, mas o título da faixa não chegou até mim. Não vou fingir que sei qual é."
        else:
            fala = ""
            if callable(self.enviar_mensagem):
                prompt = (
                    "Você é a Laylay e recebeu apenas o título/metadado da faixa atual, não o áudio. "
                    "Dê uma opinião curta e natural em português sobre a música somente se reconhecer título e artista. "
                    "Se não reconhecer com segurança, diga isso sem inventar características sonoras. "
                    "Não fale sobre ser IA, não analise a pergunta do usuário, não ofereça comandos e não termine com pergunta. "
                    "Use no máximo duas frases. Responda só JSON válido: {\"fala\":\"...\"}.\n"
                    f"Título atual: {titulo!r}"
                )
                try:
                    bruto = self.enviar_mensagem(
                        [{"role": "system", "content": prompt}],
                        _com_tools=False,
                        max_tokens=150,
                        modo_rapido=True,
                    )
                    fala = self._extrair_fala_json(bruto)
                except Exception:
                    fala = ""
            if not fala:
                fala = f"A que está tocando é {titulo}. Pelo título sozinho eu não vou inventar detalhes do som, então minha opinião ainda seria meio no escuro."
        self.falar(fala, "calma", 1)
        self.registrar_mente_curta(
            texto,
            fala,
            intencao="MUSIC_OPINION_CHAT",
            alvo=titulo or "musica_atual",
            habilidade="musica",
        )
        return True

    def sugestao_nova(self, texto: str = "") -> str:
        return sugestao_musical_nova_conversacional(
            texto,
            normalizar_texto=self.normalizar_texto,
            estado_mental=self._estado(),
        )

    def responder_pedido_direcao(self, texto: str = "") -> bool:
        t = self.normalizar_texto(texto)
        quer_nova = any(p in t for p in [
            "nao tenho ouvido antes", "não tenho ouvido antes",
            "nao ouvi antes", "não ouvi antes",
            "uma que nao ouvi", "uma que não ouvi",
            "uma nova", "musica nova", "música nova",
        ])
        sugestao = self.sugestao_nova(t)
        if quer_nova:
            fala = random.choice([
                f"Então eu arrisco uma fora da tua prateleira: {sugestao}. Não toquei nada, só tô te dando um palpite novo.",
                f"Beleza, sem reciclar playlist. Meu chute com coragem é {sugestao}. Se quiser outro clima, eu viro a esquina.",
                f"Uma nova pra testar teu ouvido: {sugestao}. Pode ser que bata, pode ser que apanhe, mas é uma aposta honesta.",
            ])
        else:
            fala = random.choice([
                f"Eu iria de {sugestao}. Não veio da tua playlist; é um palpite meu pra você testar.",
                f"Minha aposta agora é {sugestao}. Se não bater, eu troco o tempero sem drama.",
                f"Vou te jogar uma nova na mesa: {sugestao}. Não executei nada, só recomendei mesmo.",
                f"Tá, eu arrisco: {sugestao}. Tem cara de música que pode te pegar de lado.",
            ])
        self.falar(fala, "calma", 1)
        self.registrar_mente_curta(
            texto,
            fala,
            intencao="MUSIC_OPINION_CHAT",
            alvo=sugestao,
            habilidade="musica",
        )
        self._sugestao_pendente = {"titulo": sugestao, "ts": time.time()}
        return True

    def processar_confirmacao(self, texto: str = "") -> bool:
        """Continua uma recomendacao conversacional sem recriar habilidade antiga."""
        t = self.normalizar_texto(texto)
        if not t:
            return False

        confirma = any(p in t for p in [
            "quero ouvir", "quero escutar", "quero sim", "quero ver",
            "eu quero", "quero a musica", "quero a música",
            "pode ser", "pode colocar", "pode tocar", "coloca", "toca",
            "manda", "bora", "vai nessa", "essa mesmo", "essa aí", "essa ai",
        ])
        pedir_entrega = any(p in t for p in [
            "entao me fala", "então me fala", "me fala entao", "me fala então",
            "entao fala", "então fala", "me fala",
            "me diga", "me diz", "fala uma", "me da outra", "me dá outra",
        ])
        pede_outra = any(p in t for p in [
            "outra", "diferente", "nao gostei", "não gostei",
            "quero outra", "manda outra", "me da outra", "me dá outra",
            "troca", "troca o clima", "outro clima", "outro estilo",
            "mais pesado", "mais pesada", "mais leve", "mais calmo", "mais calma",
            "mais alternativo", "mais alternativa", "mais rock", "mais metal",
            "mais geek", "mais nerd", "mais gamer", "mais eletronica", "mais eletrônica",
        ])
        if not (confirma or pedir_entrega):
            if not pede_outra:
                return False

        estado = self._estado()
        pendente = dict(self._sugestao_pendente or {})
        try:
            pendente_valida = bool(pendente.get("titulo")) and time.time() - float(pendente.get("ts") or 0.0) <= 420
        except Exception:
            pendente_valida = False
        if not pendente_valida:
            if str(estado.get("ultima_intencao") or "").upper() != "MUSIC_OPINION_CHAT":
                return False
            if str(estado.get("ultima_habilidade") or "").lower() != "musica":
                return False
        sugestao = str(pendente.get("titulo") if pendente_valida else estado.get("ultimo_alvo") or "").strip()
        if not sugestao or self.normalizar_texto(sugestao) in {"musica_nova", "musica", "música"}:
            return False

        if pede_outra:
            nova = self.sugestao_nova(t)
            tentativas = 0
            while self.normalizar_texto(nova) == self.normalizar_texto(sugestao) and tentativas < 4:
                nova = self.sugestao_nova(t + f" alternativa {tentativas}")
                tentativas += 1
            fala = random.choice([
                f"Tá, viro a esquina: {nova}. Essa tem outro cheiro.",
                f"Fechado, sem insistir na mesma tecla. Eu tentaria {nova}.",
                f"Então troca o tempero: {nova}. Vamos ver se essa conversa melhor com teu ouvido.",
            ])
            self.registrar_mente_curta(
                texto,
                fala,
                intencao="MUSIC_OPINION_CHAT",
                alvo=nova,
                habilidade="musica",
            )
            self._sugestao_pendente = {"titulo": nova, "ts": time.time()}
            self.falar(fala, "calma", 1)
            return True

        if pedir_entrega and not confirma:
            fala = random.choice([
                f"Então toma: {sugestao}. Essa foi a que eu escolhi pra você agora.",
                f"Tá, sem enrolar: {sugestao}. Essa é minha aposta do momento.",
                f"Fechado. A música que eu tô te indicando é {sugestao}.",
            ])
            self.registrar_mente_curta(
                texto,
                fala,
                intencao="MUSIC_OPINION_CHAT",
                alvo=sugestao,
                habilidade="musica",
            )
            self.falar(fala, "calma", 1)
            return True

        resultado = {"intent": "MUSIC_SEARCH", "params": {"query": sugestao, "origem": "sugestao_conversacional"}}
        self.log(f"⚡ [ROTEADOR SUGESTAO-MUSICAL [chat]] {resultado}")
        texto_execucao = f"toca {sugestao}"
        executou = bool(self.executar_intencao(resultado, texto_execucao))
        self.registrar_resultado_execucao(resultado, texto, executou, origem="confirmacao_sugestao_musical")
        if executou:
            self._sugestao_pendente = {}
            self.registrar_mente_curta(
                texto,
                f"Colocando {sugestao} pra tocar.",
                intencao="MUSIC_SEARCH",
                alvo=sugestao,
                habilidade="musica",
            )
            if callable(self.registrar_autoaprimoramento):
                try:
                    self.registrar_autoaprimoramento(
                        resultado,
                        texto,
                        True,
                        contexto="confirmacao de sugestao musical",
                        origem="chat",
                    )
                except Exception as e_auto:
                    self.log(f"⚠️ [AUTOAPRENDIZADO] falha ao registrar sugestao musical: {e_auto}")
        else:
            # A confirmacao foi compreendida, mesmo que o executor nao tenha
            # confirmado a abertura. Nao deixe a frase cair no IA-first e
            # virar um comando sem relacao com a musica.
            self.log(f"⚠️ [MÚSICA:SUGESTÃO] execução não confirmada para {sugestao!r}")
        return True


def criar_musica_conversacional_runtime(**kwargs: Any) -> MusicaConversacionalRuntime:
    return MusicaConversacionalRuntime(**kwargs)
