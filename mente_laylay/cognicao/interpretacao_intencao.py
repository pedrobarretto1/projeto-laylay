"""Interpretacao IA-first conectada ao estado compartilhado da Laylay."""

from __future__ import annotations

import json
from typing import Any, Callable, Dict

from mente_laylay.autonomia.coordenador_intencao import INTENTS_EXECUTAVEIS
from mente_laylay.autonomia.pre_fluxo_contextual import analisar_intencao_com_porteiro


PROMPT_INTERPRETACAO = """Você é o cérebro da assistente Laylay. Analise a frase do usuário e retorne apenas um JSON válido com:
intent: (PLAYLIST_ADD, PLAYLIST_PLAY, PLAYLIST_LIST, PLAYLIST_DELETE, LAYLAY_PLAYLIST_LIST, LAYLAY_PLAYLIST_COPY, MEDIA_CONTROL, CANCELAR_ACAO, CLOSE_TAB, CLOSE_APP, APP_OPEN, OPEN_URL, MAXIMIZE_WINDOW, VOLUME, MUSIC_SEARCH, SITE_ENTER, SEARCH, WEATHER, CREATE_FOLDER, DELETE_ITEM, LISTAR_PLAYLISTS, TOCAR_PLAYLIST, TOCAR_PLAYLIST_SHUFFLE, AGENDAR_LEMBRETE, LISTAR_AGENDAMENTOS, CANCELAR_AGENDAMENTO)
params: (dicionário com nome_playlist, nome_app, nivel_volume, query, acao, etc)
Regras:
- Retorne SOMENTE o JSON (sem markdown, sem texto extra).
- Corrija mentalmente erros leves de pronuncia, transcricao e ortografia antes de decidir a intencao.
- Trate apelidos ensinados como equivalentes do nome real quando fizer sentido.
- Use a memória curta da mente inteira quando a frase estiver incompleta. Se houver um alvo recente, reutilize-o quando fizer sentido.
- Saudações, agradecimentos, risadas e conversa social curta NUNCA viram playlist, música, site, arquivo ou comando por causa de contexto antigo.
- Se a frase depender do contexto recente, do que foi dito agora pouco ou de um alvo implícito, interprete isso como continuidade do mesmo cérebro e não como um pedido fragmentado.
- Use a memória de curto prazo da última playlist real quando o assunto atual for música e o usuário disser coisas como 'coloca essa também' e não citar playlist.
- Se o assunto atual for email, agenda, notificação ou sistema, ignore pistas musicais antigas como ultima_playlist, playlist_ativa ou ultima_url_playlist.
- Ao listar playlists, use as playlists que estão no contexto 'playlists_disponiveis'.
- Música e playlist NUNCA devem ser executadas só por rotina antiga, ultima_playlist ou padrão aprendido. Para tocar algo, precisa haver pedido atual claro do usuário ou confirmação clara de uma sugestão recém-feita.
- Em começo de conversa, saudações e perguntas sobre bem-estar, não ofereça nem execute playlist. Responda como conversa normal.
- Se o bem-estar do Pedro sugerir música, no máximo pergunte antes; nunca toque sem confirmação.
- Se o usuário pedir para colocar um app em foco, maximizar, tela cheia ou trazer para frente, trate como APP_OPEN/MAXIMIZE, nunca como SEARCH nem como OPEN_SITE.
- Frases como 'coloca o Opera em foco', 'deixa o Opera em tela cheia', 'maximiza o Opera' devem virar foco da janela do Opera, não pesquisa no navegador.
- Frases como 'deixa o Opera em foco' ou 'coloca ele em tela cheia' NÃO são cancelamento; são comando de janela.
- Se o usuário pedir para fechar um programa real, como Steam, Opera, VS Code ou Spotify, prefira CLOSE_APP.
- Se o usuário pedir para fechar aba, site ou janela do navegador, prefira CLOSE_TAB.
- Se o usuário pedir para abrir um site conhecido, URL, domínio ou destino web explícito, use OPEN_URL.
- Para playlist, site e foco de janela, interprete a frase inteira e o contexto recente antes de decidir; não use apenas um verbo ou um nome isolado como gatilho principal.
- Se o usuário estiver pedindo para TOCAR/COLOCAR música ou pedindo um gênero/artista, a intenção OBRIGATÓRIA é MUSIC_SEARCH com params.query.
- Se o usuário pedir recomendação musical vaga, como 'me recomenda uma música', NÃO use MUSIC_SEARCH. Isso é conversa, não comando.
- Para MUSIC_SEARCH, NUNCA use Google; o destino é sempre YouTube.
- Se a frase curta bater com o nome de uma playlist salva, só trate como PLAYLIST_PLAY se houver verbo atual de ação ou pergunta pendente sobre playlist.
- Se a frase mencionar playlist e pedir quais, mostrar ou listar, use PLAYLIST_LIST.
- Se a frase mencionar playlist e pedir apagar, deletar, remover ou excluir, use PLAYLIST_DELETE.
- Se a frase mencionar playlist, NUNCA retorne SEARCH.
- Só use CANCELAR_ACAO para desistência explícita. Correções e conversa com 'não' não são cancelamento automático.
- Mensagem curta pode continuar a ação recente somente quando o assunto atual ainda combina com ela.
- Nunca use ultima_playlist para cumprimentos, elogios ou perguntas de bem-estar.
- Pedido para tocar uma playlist salva deve usar PLAYLIST_PLAY, nunca criar pasta ou responder como conversa genérica.
- Nunca invente estrutura de arquivos quando o assunto for playlist, música ou artista.
- Pedido para lembrar algo deve usar AGENDAR_LEMBRETE; pergunta sobre compromissos usa LISTAR_AGENDAMENTOS.
- Pedido para apagar pasta ou arquivo usa DELETE_ITEM com apenas o nome real do alvo.
- Em pedido composto para apagar uma pasta e seu conteúdo, DELETE_ITEM deve mirar a pasta.
- Frases como entra em, vai para ou acessa um site devem resultar em OPEN_URL ou SITE_ENTER conforme o alvo.
- Fechar aba ou site usa CLOSE_TAB; fechar programa instalado usa CLOSE_APP.
- Ler, resumir ou explicar emails usa EMAIL_READ ou EMAIL_SYNC.
- Reclamação informal sobre remetente ou notificação deve preservar o tom e escolher ação útil de email/notificação.
- Pergunta de temperatura ou clima usa WEATHER com params.local.
- Pedido sobre playlists da própria Laylay usa LAYLAY_PLAYLIST_LIST ou LAYLAY_PLAYLIST_COPY.
- SEARCH é para perguntas factuais que realmente exigem pesquisa.
- A decisão deve vir de uma única mente: combine contexto, memória curta, rotina, emoção e percepção viva.
- Em conflito, priorize o sinal mais recente, concreto e coerente.
Exemplos:
Usuário: 'coloca um rock' -> {"intent":"MUSIC_SEARCH","params":{"query":"rock"}}
Usuário: 'coloca essa música na playlist kamai' -> {"intent":"PLAYLIST_ADD","params":{"nome_playlist":"kamaitachi"}}
Usuário: 'coloca a brisa da madrugada' -> {"intent":"PLAYLIST_PLAY","params":{"nome_playlist":"brisa da madrugada"}}
Usuário: 'coloca o Opera em foco' -> {"intent":"APP_OPEN","params":{"nome_app":"opera"}}
Usuário: 'deixa o Opera em tela cheia' -> {"intent":"APP_OPEN","params":{"nome_app":"opera","modo":"fullscreen"}}
Usuário: 'fecha a Steam' -> {"intent":"CLOSE_APP","params":{"nome_app":"steam"}}
Usuário: 'fecha o site do ifood' -> {"intent":"CLOSE_TAB","params":{"alvo":"ifood"}}
Usuário: 'entra no instagram' -> {"intent":"OPEN_URL","params":{"alvo":"instagram"}}
Usuário: 'me fale dos emails' -> {"intent":"EMAIL_READ","params":{}}
Usuário: 'quantos graus tá em Boituva?' -> {"intent":"WEATHER","params":{"local":"Boituva"}}
Usuário: 'me lembra de 12:30 ir para o senai' -> {"intent":"AGENDAR_LEMBRETE","params":{"hora_alvo":"12:30","descricao":"ir para o senai"}}
Usuário: 'apaga a pasta roberto' -> {"intent":"DELETE_ITEM","params":{"alvo":"roberto","tipo":"pasta"}}
Usuário: 'deixa pra lá' -> {"intent":"CANCELAR_ACAO","params":{}}
"""


def extrair_json_resposta(texto: str) -> str:
    conteudo = str(texto or "").strip()
    if not conteudo:
        return ""
    if conteudo.startswith("```"):
        import re

        conteudo = re.sub(r"^```(?:json)?\s*", "", conteudo, flags=re.IGNORECASE)
        conteudo = re.sub(r"\s*```$", "", conteudo).strip()
    inicio = conteudo.find("{")
    fim = conteudo.rfind("}")
    if inicio == -1 or fim == -1 or fim <= inicio:
        return ""
    return conteudo[inicio : fim + 1].strip()


class InterpretacaoIntencaoRuntime:
    """Interpreta comandos usando o retrato atual da mente compartilhada."""

    def __init__(
        self,
        *,
        contexto_getter: Callable[[], Dict[str, Any]],
        log: Callable[..., Any] = print,
    ) -> None:
        self._contexto_getter = contexto_getter
        self._log = log

    def _contexto(self) -> Dict[str, Any]:
        try:
            contexto = self._contexto_getter()
            return contexto if isinstance(contexto, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _call(ctx: Dict[str, Any], nome: str, *args: Any, default: Any = None, **kwargs: Any) -> Any:
        funcao = ctx.get(nome)
        if callable(funcao):
            return funcao(*args, **kwargs)
        return default

    def analisar(self, texto: str) -> Dict[str, Any] | None:
        ctx = self._contexto()
        original = str(texto or "").strip()
        if not original:
            return None
        if self._call(ctx, "texto_cancela_acao_agora", original, default=False):
            return {"intent": "CANCELAR_ACAO", "params": {}}
        if self._call(ctx, "texto_bloqueia_playlist_agora", original, default=False):
            return None
        if self._call(ctx, "texto_social_curto", original, default=False):
            return None

        normalizar = ctx.get("normalizar_texto")
        corrigido = normalizar(original) if callable(normalizar) else original
        estado = ctx.get("estado") or {}
        mente = dict(estado.get("mente_integrada_estado") or {})
        playlist_state = estado.get("playlist_state") or {}
        ultima_playlist = self._call(ctx, "musica_estado_get", "ultima_playlist", default="")
        contexto_playlist = {
            "ultima_playlist": ultima_playlist,
            "playlist_ativa": str(playlist_state.get("name") or "").strip(),
            "ultima_url_playlist": str(playlist_state.get("last_url") or "").strip(),
        }

        historico = []
        for mensagem in list(estado.get("messages") or [])[-12:]:
            if not isinstance(mensagem, dict):
                continue
            role = str(mensagem.get("role") or "")
            content = str(mensagem.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                historico.append({"role": role, "content": content[:400]})

        payload = {
            "texto_original": original,
            "texto_corrigido": corrigido,
            "retrato_mente_integrada": self._call(
                ctx, "resumo_mente_integrada_para_prompt", original, default=""
            ),
            "contexto_conversas": {
                **contexto_playlist,
                "mente_curta": mente,
                "autoaprimoramento": self._call(
                    ctx, "resumo_autoaprimoramento_para_prompt", limit=6, default=""
                ),
                "agendamentos_ativos": self._call(
                    ctx, "resumo_agendamentos_para_prompt", limit=6, default=""
                ),
                "historico": historico,
                "playlists_disponiveis": list((estado.get("playlists_carregadas") or {}).keys()),
            },
        }
        enviar = ctx.get("enviar_mensagem")
        if not callable(enviar):
            return None
        raw = enviar(
            [
                {"role": "system", "content": PROMPT_INTERPRETACAO},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            _com_tools=False,
            max_tokens=140,
            modo_rapido=True,
        )
        extrair = ctx.get("extrair_json_da_ia")
        texto_json = extrair(raw) if callable(extrair) else extrair_json_resposta(raw)
        if not texto_json:
            return None
        try:
            resultado = json.loads(texto_json)
        except Exception:
            return None
        if not isinstance(resultado, dict):
            return None

        intent = str(resultado.get("intent") or "").upper().strip()
        if intent == "CANCELAR_ACAO" and not self._call(
            ctx, "texto_cancela_acao_agora", original, default=False
        ):
            return None
        intents_playlist = {
            "PLAYLIST_ADD",
            "PLAYLIST_PLAY",
            "PLAYLIST_LIST",
            "TOCAR_PLAYLIST",
            "TOCAR_PLAYLIST_SHUFFLE",
        }
        if self._call(ctx, "playlist_bloqueada_agora", default=False) and intent in intents_playlist:
            if not self._call(ctx, "texto_pede_playlist_explicitamente", original, default=False):
                self._log("🎵 [PLAYLIST] Intenção musical bloqueada: contexto antigo tentou puxar playlist.")
                return None
        return resultado

    def tentar_ai_primeiro(self, texto: str) -> Dict[str, Any] | None:
        ctx = self._contexto()
        bruto = str(texto or "").strip()
        if not bruto:
            return None
        if self._call(ctx, "texto_conversa_casual_sem_acao", bruto, default=False):
            return None
        if self._call(ctx, "texto_social_curto", bruto, default=False):
            return None
        if self._call(ctx, "texto_bloqueia_playlist_agora", bruto, default=False):
            return None

        normalizar = ctx.get("normalizar_texto")
        normalizado = normalizar(bruto) if callable(normalizar) else bruto
        if not normalizado:
            return None
        if self._call(ctx, "texto_pede_direcao_musical_generica", normalizado, default=False):
            return None
        if self._call(ctx, "texto_expresso_melhor_no_deterministico", normalizado, default=False):
            return None

        deve_tentar = bool(
            self._call(ctx, "contexto_mental_ativo", default=False)
            or self._call(ctx, "texto_depende_de_contexto", normalizado, default=False)
            or self._call(ctx, "texto_parece_navegacao_ou_janela_ia", normalizado, default=False)
            or self._call(ctx, "fluxo_prioritario_da_ia", normalizado, default=False)
            or (len(normalizado.split()) <= 12 and not normalizado.endswith("?"))
        )
        if not deve_tentar:
            return None

        status, resultado = analisar_intencao_com_porteiro(
            {
                "_texto_tem_comando_explicito": ctx.get("texto_tem_comando_explicito"),
                "_texto_social_curto": ctx.get("texto_social_curto"),
                "_texto_conversa_casual_sem_acao": ctx.get("texto_conversa_casual_sem_acao"),
                "_texto_conversa_contextual_sem_comando": ctx.get("texto_conversa_contextual_sem_comando"),
                "analisar_intencao": self.analisar,
            },
            bruto,
        )
        if status == "falha":
            self._log("⚠️ [IA-FIRST] falha ao analisar intenção pelo porteiro")
            return None
        if status != "ok" or not isinstance(resultado, dict):
            return None

        intent = str(resultado.get("intent") or "").upper().strip()
        if intent == "CANCELAR_ACAO" and not self._call(
            ctx, "texto_cancela_acao_agora", bruto, default=False
        ):
            return None
        if intent == "MEDIA_CONTROL":
            acao = str((resultado.get("params") or {}).get("acao") or "").strip().lower()
            permitidas = {
                "play", "pause", "next", "prev", "replay", "pause_play", "toggle",
                "resume", "retomar", "retoma", "continuar", "continua", "despausa", "despausar",
            }
            if acao and acao not in permitidas:
                return None
        if intent not in INTENTS_EXECUTAVEIS:
            return None
        return resultado


def criar_interpretacao_intencao_runtime(
    *,
    contexto_getter: Callable[[], Dict[str, Any]],
    log: Callable[..., Any] = print,
) -> InterpretacaoIntencaoRuntime:
    return InterpretacaoIntencaoRuntime(contexto_getter=contexto_getter, log=log)
