"""Interpretacao IA-first conectada ao estado compartilhado da Laylay."""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Dict

from mente_laylay.autonomia.coordenador_intencao import INTENTS_EXECUTAVEIS
from mente_laylay.autonomia.fluxos_conversa import usar_modo_rapido_conversa
from mente_laylay.autonomia.pre_fluxo_contextual import analisar_intencao_com_porteiro
from mente_laylay.autonomia.roteador_deterministico import (
    extrair_intencao_abrir_app as extrair_intencao_app_instalado,
    texto_expresso_melhor_no_deterministico,
)


PROMPT_INTERPRETACAO = """Você é o cérebro da assistente Laylay. Analise a frase do usuário e retorne apenas um JSON válido com:
intent: (PLAYLIST_ADD, PLAYLIST_PLAY, PLAYLIST_LIST, PLAYLIST_DELETE, LAYLAY_PLAYLIST_LIST, LAYLAY_PLAYLIST_COPY, MEDIA_CONTROL, CANCELAR_ACAO, CLOSE_TAB, CLOSE_APP, APP_OPEN, OPEN_URL, MAXIMIZE_WINDOW, VOLUME, MUSIC_SEARCH, SITE_ENTER, SEARCH, WEATHER, RESUMIR_PAGINA, CREATE_FOLDER, CREATE_FILE, DELETE_ITEM, LISTAR_PLAYLISTS, TOCAR_PLAYLIST, TOCAR_PLAYLIST_SHUFFLE, AGENDAR_LEMBRETE, AGENDAR_ACAO, LISTAR_AGENDAMENTOS, CANCELAR_AGENDAMENTO, IOT_CONTROL, IOT_STATUS, IOT_LIST, SUGGEST_ACTION)
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
- Pedido para executar uma ação no futuro usa AGENDAR_ACAO e preserva em params.acao_agendada a intenção prática completa.
- Pedido para apagar pasta ou arquivo usa DELETE_ITEM com apenas o nome real do alvo.
- Em pedido composto para apagar uma pasta e seu conteúdo, DELETE_ITEM deve mirar a pasta.
- Frases como entra em, vai para ou acessa um site devem resultar em OPEN_URL ou SITE_ENTER conforme o alvo.
- Fechar aba ou site usa CLOSE_TAB; fechar programa instalado usa CLOSE_APP.
- Ler, resumir ou explicar emails usa EMAIL_READ ou EMAIL_SYNC.
- Reclamação informal sobre remetente ou notificação deve preservar o tom e escolher ação útil de email/notificação.
- Pergunta de temperatura ou clima usa WEATHER com params.local.
- Pedido para resumir, explicar ou dizer o conteúdo da página ou vídeo atual usa RESUMIR_PAGINA.
- Ligar, desligar ou alternar aparelho da casa usa IOT_CONTROL com params.acao e params.alvo.
- Ajustar brilho da lâmpada usa IOT_CONTROL com acao="ajustar_brilho" e params.valor de 1 a 100.
- Ajustar uma cor RGB da lâmpada usa IOT_CONTROL com acao="ajustar_cor", params.cor e params.rgb.
- Preserve tonalidades pedidas: claro aproxima o RGB do branco, escuro reduz sua luminosidade e pastel suaviza a cor. Inclua params.tonalidade e o nome completo em params.cor.
- Frases como "agora mais clara" continuam a última cor da lâmpada em foco, sem virar música ou trocar de domínio.
- Quando não houver uma cor citada, "deixa a luz mais clara/escura" significa aumentar/diminuir o brilho com IOT_CONTROL e acao="ajustar_brilho". Nunca invente intents como dim_lighting.
- "Aumenta/diminui/abaixa o brilho dela" usa a lâmpada em foco e ajusta o brilho relativamente; não exige que o usuário diga uma porcentagem.
- Branco quente, neutro ou frio usa IOT_CONTROL com acao="ajustar_branco", params.cor, params.temperatura de 0 a 100 e, se citado, params.brilho.
- Se houver lâmpada em foco, um pedido curto de cor continua nesse dispositivo; não transforme "coloca um azul" ou "deixa rosa" em busca musical.
- Lâmpadas não emitem preto. Nesse caso, use SUGGEST_ACTION para explicar que preto é ausência de luz e perguntar se deve desligar a lâmpada.
- Perguntar se um dispositivo está ligado usa IOT_STATUS. Listar dispositivos inteligentes usa IOT_LIST.
- Nunca trate comentário casual sobre um aparelho como comando IoT; precisa haver pedido ou pergunta atual.
- Planos, propostas e comentários sobre uma habilidade futura da Laylay são conversa. Frases como 'vou te dar uma habilidade', 'você vai poder controlar a luz' e 'o que acha dessa capacidade?' devem retornar NONE.
- Referências como 'desliga ele' só continuam IoT quando o foco operacional recente for um dispositivo IoT.
- Quando o usuário expressar indiretamente uma necessidade que alguma habilidade pode resolver, use SUGGEST_ACTION. Não execute ainda.
- SUGGEST_ACTION usa params.acao_sugerida={"intent":"INTENT_REAL","params":{...}}, params.descricao e params.fala em forma de pergunta.
- Só sugira quando a relação entre necessidade e ação for clara. Comentários, opiniões e desabafos não exigem sugestão forçada.
- A ação sugerida deve usar um intent executável existente; nunca invente comandos ou afirme que já executou.
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
Usuário: 'desliga o ventilador daqui 10 minutos' -> {"intent":"AGENDAR_ACAO","params":{"minutos":10,"acao_agendada":{"intent":"IOT_CONTROL","params":{"acao":"desligar","alvo":"ventilador"}}}}
Usuário: 'apaga a pasta roberto' -> {"intent":"DELETE_ITEM","params":{"alvo":"roberto","tipo":"pasta"}}
Usuário: 'deixa pra lá' -> {"intent":"CANCELAR_ACAO","params":{}}
Usuário: 'liga o ventilador do quarto' -> {"intent":"IOT_CONTROL","params":{"acao":"ligar","alvo":"ventilador do quarto"}}
Usuário: 'deixa o brilho da lâmpada em 40%' -> {"intent":"IOT_CONTROL","params":{"acao":"ajustar_brilho","alvo":"lâmpada","valor":40}}
Usuário: 'coloca a luz azul' -> {"intent":"IOT_CONTROL","params":{"acao":"ajustar_cor","alvo":"luz","cor":"azul","rgb":[0,0,255]}}
Usuário: 'deixa a luz azul claro' -> {"intent":"IOT_CONTROL","params":{"acao":"ajustar_cor","alvo":"luz","cor":"azul claro","rgb":[115,115,255],"tonalidade":"claro"}}
Usuário: 'deixa ela roxo escuro' -> {"intent":"IOT_CONTROL","params":{"acao":"ajustar_cor","alvo":"ela","cor":"roxo escuro","rgb":[54,0,107],"tonalidade":"escuro"}}
Usuário: 'deixa a lâmpada em branco quente' -> {"intent":"IOT_CONTROL","params":{"acao":"ajustar_branco","alvo":"lâmpada","cor":"branco quente","temperatura":10,"brilho":70}}
Usuário: 'ele está ligado?' -> {"intent":"IOT_STATUS","params":{"acao":"status","alvo":"ele"}}
Usuário: 'quais dispositivos inteligentes eu tenho?' -> {"intent":"IOT_LIST","params":{}}
Usuário: 'estou com calor' -> {"intent":"SUGGEST_ACTION","params":{"acao_sugerida":{"intent":"IOT_CONTROL","params":{"acao":"ligar","alvo":"ventilador"}},"descricao":"ligar o ventilador","fala":"Tá quente por aí. Quer que eu ligue o ventilador?"}}
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


def sugestao_acao_valida(resultado: Any) -> bool:
    """Aceita apenas sugestões que apontem para uma ação prática executável."""
    if not isinstance(resultado, dict):
        return False
    params = resultado.get("params")
    if not isinstance(params, dict):
        return False
    acao_sugerida = params.get("acao_sugerida")
    if not isinstance(acao_sugerida, dict):
        return False
    intent_sugerido = str(acao_sugerida.get("intent") or "").upper().strip()
    return bool(intent_sugerido and intent_sugerido not in {"SUGGEST_ACTION", "CANCELAR_ACAO"})


def interpretar_comando_local_rapido(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str],
    texto_depende_de_contexto: Callable[[str], bool],
) -> Dict[str, Any] | None:
    """Interpreta foco/maximizacao explicitos sem consultar o modelo."""
    normalizado = normalizar_texto(texto) if callable(normalizar_texto) else str(texto or "")
    if not normalizado:
        return None
    if callable(texto_depende_de_contexto) and texto_depende_de_contexto(normalizado):
        return None

    aliases_apps = {
        "opera": {"opera", "ópera", "operagx", "opera gx"},
        "vscode": {"vscode", "vs code", "visual studio code", "code"},
        "chrome": {"chrome", "google chrome"},
        "edge": {"edge", "msedge", "microsoft edge"},
        "brave": {"brave", "brave browser"},
        "firefox": {"firefox", "mozilla firefox"},
    }
    app_encontrado = next(
        (app for app, aliases in aliases_apps.items() if any(alias in normalizado for alias in aliases)),
        None,
    )
    if not app_encontrado:
        return None

    verbos_foco = (
        "em foco", "traz", "traga", "deixa", "coloca", "bota",
        "maximiza", "maximizar", "na frente", "primeiro plano", "foco",
    )
    if not any(verbo in normalizado for verbo in verbos_foco):
        return None

    tela_cheia = any(
        trecho in normalizado
        for trecho in ("tela cheia", "fullscreen", "full screen", "tela cheia no")
    )
    if tela_cheia:
        return {"intent": "MAXIMIZE_WINDOW", "params": {"nome_app": app_encontrado}}
    return {"intent": "APP_OPEN", "params": {"nome_app": app_encontrado, "modo": "focus"}}


class AdaptadoresConversacionaisRuntime:
    """Reune decisoes locais leves que protegem a conversa antes da IA."""

    def __init__(
        self,
        *,
        normalizar_texto: Callable[[str], str],
        texto_depende_de_contexto: Callable[[str], bool],
        resolver_comando_contextual: Callable[[str], Any],
        limpar_destino: Callable[[str], str] | None = None,
        normalizar_query_musical: Callable[[str], str] | None = None,
        apps_map: Dict[str, Any] | None = None,
        sites_diretos: Dict[str, Any] | None = None,
    ) -> None:
        self._normalizar_texto = normalizar_texto
        self._texto_depende_de_contexto = texto_depende_de_contexto
        self._resolver_comando_contextual = resolver_comando_contextual
        self._limpar_destino = limpar_destino
        self._normalizar_query_musical = normalizar_query_musical
        self._apps_map = apps_map or {}
        self._sites_diretos = sites_diretos or {}
        self._cursores_estilo_musical: Dict[str, int] = {}

    def interpretar_comando_local(self, texto: str) -> Dict[str, Any] | None:
        return interpretar_comando_local_rapido(
            texto,
            normalizar_texto=self._normalizar_texto,
            texto_depende_de_contexto=self._texto_depende_de_contexto,
        )

    def usar_modo_rapido(self, texto: str) -> bool:
        return usar_modo_rapido_conversa(
            texto,
            normalizar_texto=self._normalizar_texto,
            interpretar_comando_local_rapido=self.interpretar_comando_local,
            resolver_comando_contextual=self._resolver_comando_contextual,
        )

    def ignorar_token_solto(self, texto: str) -> bool:
        normalizado = self._normalizar_texto(texto) if callable(self._normalizar_texto) else str(texto or "").lower()
        palavras = str(normalizado or "").strip().split()
        return len(palavras) == 1 and palavras[0] in {"coloca", "toca", "abre", "abra"}

    def texto_expresso_melhor_no_deterministico(self, texto: str) -> bool:
        return texto_expresso_melhor_no_deterministico(
            texto,
            normalizar_texto=self._normalizar_texto,
        )

    def extrair_intencao_abrir_app(self, texto: str) -> Dict[str, Any] | None:
        return extrair_intencao_app_instalado(
            texto,
            normalizar_texto=self._normalizar_texto,
            limpar_destino=self._limpar_destino or (lambda valor: valor),
            apps_map=self._apps_map,
            sites_diretos=self._sites_diretos,
        )

    def resolver_query_musical_por_estilo(self, query: str, texto_original: str = "") -> Dict[str, str]:
        bruto = query or texto_original
        normalizada = self._normalizar_query_musical(bruto) if callable(self._normalizar_query_musical) else str(bruto or "").strip()
        texto_base = self._normalizar_texto(f"{query} {texto_original}") if callable(self._normalizar_texto) else f"{query} {texto_original}".lower()
        catalogo = {
            "pesada": (
                "Sepultura - Roots Bloody Roots official video",
                "Slipknot - Duality official video",
                "System Of A Down - B.Y.O.B. official video",
                "Linkin Park - Given Up official audio",
                "Bring Me The Horizon - Shadow Moses official video",
            ),
            "alternativa": (
                "Tame Impala - The Less I Know The Better official video",
                "Boogarins - Infinu official audio",
                "Tagua Tagua - Inteiro Metade official video",
            ),
            "calma": (
                "Men I Trust - Show Me How official video",
                "Cigarettes After Sex - Apocalypse audio",
                "Khruangbin - Friday Morning official audio",
            ),
            "animada": (
                "Paramore - Still Into You official video",
                "The Strokes - Reptilia official video",
                "Franz Ferdinand - Take Me Out official video",
            ),
        }
        aliases = {
            "pesada": ("pesada", "pesado", "som pesado", "mais pesado", "heavy", "metal pesado", "rock pesado"),
            "alternativa": ("alternativa", "alternativo", "indie", "diferente"),
            "calma": ("calma", "calmo", "tranquila", "tranquilo", "relaxante", "suave"),
            "animada": ("animada", "animado", "agitada", "agitado", "pra cima", "para cima"),
        }
        estilo = next(
            (nome for nome, termos in aliases.items() if any(termo in texto_base for termo in termos)),
            "",
        )
        pedido_generico = normalizada in {
            "pesada", "pesado", "heavy", "metal pesado", "rock pesado",
            "alternativa", "alternativo", "indie", "diferente",
            "calma", "calmo", "tranquila", "tranquilo", "relaxante", "suave",
            "animada", "animado", "agitada", "agitado", "pra cima", "para cima",
        }
        if estilo and pedido_generico:
            opcoes = catalogo[estilo]
            indice = self._cursores_estilo_musical.get(estilo, 0) % len(opcoes)
            self._cursores_estilo_musical[estilo] = indice + 1
            return {
                "query": opcoes[indice],
                "origem": "estilo_curado",
                "estilo": estilo,
                "generica": "true",
            }
        return {"query": normalizada, "origem": "explicita", "generica": "false"}


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
        self._cache_analise: Dict[str, tuple[float, Dict[str, Any] | None]] = {}

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
        agora = time.monotonic()
        cache = self._cache_analise.get(original)
        if cache and agora - cache[0] <= 3.0:
            resultado_cache = cache[1]
            return dict(resultado_cache) if isinstance(resultado_cache, dict) else None
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
        try:
            raw = enviar(
                [
                    {"role": "system", "content": PROMPT_INTERPRETACAO},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                _com_tools=False,
                max_tokens=140,
                modo_rapido=True,
            )
        except Exception as exc:
            self._cache_analise[original] = (agora, None)
            self._log(f"⚠️ [IA-FIRST] analisador indisponível: {exc}")
            return None
        extrair = ctx.get("extrair_json_da_ia")
        texto_json = extrair(raw) if callable(extrair) else extrair_json_resposta(raw)
        if not texto_json:
            self._cache_analise[original] = (agora, None)
            return None
        try:
            resultado = json.loads(texto_json)
        except Exception:
            self._cache_analise[original] = (agora, None)
            return None
        if not isinstance(resultado, dict):
            self._cache_analise[original] = (agora, None)
            return None

        intent = str(resultado.get("intent") or "").upper().strip()
        if intent == "CANCELAR_ACAO" and not self._call(
            ctx, "texto_cancela_acao_agora", original, default=False
        ):
            self._cache_analise[original] = (agora, None)
            return None
        if intent == "SUGGEST_ACTION" and not sugestao_acao_valida(resultado):
            self._log("🧭 [IA-FIRST] sugestão sem ação prática ignorada; seguindo como conversa")
            self._cache_analise[original] = (agora, None)
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
                self._cache_analise[original] = (agora, None)
                return None
        self._cache_analise[original] = (agora, dict(resultado))
        if len(self._cache_analise) > 16:
            mais_antiga = min(self._cache_analise, key=lambda chave: self._cache_analise[chave][0])
            self._cache_analise.pop(mais_antiga, None)
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


def criar_adaptadores_conversacionais_runtime(
    *,
    normalizar_texto: Callable[[str], str],
    texto_depende_de_contexto: Callable[[str], bool],
    resolver_comando_contextual: Callable[[str], Any],
    limpar_destino: Callable[[str], str] | None = None,
    normalizar_query_musical: Callable[[str], str] | None = None,
    apps_map: Dict[str, Any] | None = None,
    sites_diretos: Dict[str, Any] | None = None,
) -> AdaptadoresConversacionaisRuntime:
    return AdaptadoresConversacionaisRuntime(
        normalizar_texto=normalizar_texto,
        texto_depende_de_contexto=texto_depende_de_contexto,
        resolver_comando_contextual=resolver_comando_contextual,
        limpar_destino=limpar_destino,
        normalizar_query_musical=normalizar_query_musical,
        apps_map=apps_map,
        sites_diretos=sites_diretos,
    )
