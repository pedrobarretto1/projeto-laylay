"""Coordenação isolada da visão no modo jogo."""

from __future__ import annotations

import re
import hashlib
import threading
import time
from typing import Any, Callable, Mapping

from mente_laylay.pesquisa_jogos.contratos import extrair_item_da_resposta_visual
from mente_laylay.percepcao.imagens_multimodais import (
    desempacotar_imagens,
    selecionar_recorte_detalhe,
)

from .habilidade import extrair_habilidade_da_resposta_visual, parecer_local_habilidade
from .confirmacao_item import (
    montar_prompt_confirmacao_item,
    precisa_confirmar_item,
    reconciliar_leituras_item,
)
from .inventario import extrair_dados_inventario
from .presenca_visual import extrair_presenca_visual

from .captura_janela import capturar_janela_jogo_base64
from .sessao_jogo import (
    ContextoSessoesJogo,
    confirmar_contexto_janela_sistema,
    extrair_perfil_build,
    identificar_jogo,
)


from .analise_visual import (
    _COMANDO_FORA_DA_VISAO,
    _PEDIDO_NOVA_CAPTURA,
    _montar_prompt,
    _normalizar_chave,
    aplicar_perfil_confirmado_na_resposta,
    higienizar_alegacoes_visao,
    higienizar_inspecao_personagem,
    resposta_contradiz_estado_tela,
    resposta_contradiz_identidade_sistema,
    resposta_inventa_falha_da_laylay,
    resposta_pede_complemento,
)
from .pesquisa_sintese import (
    evidencia_pesquisa_para_prompt as _evidencia_pesquisa_para_prompt,
    pesquisar_e_sintetizar_item,
)


def _posicao_cursor_sistema() -> tuple[int, int] | None:
    try:
        import pyautogui

        posicao = pyautogui.position()
        return int(posicao.x), int(posicao.y)
    except Exception:
        return None


class VisaoJogoRuntime:
    """Aceita uma análise por vez e nunca persiste a captura."""

    def __init__(
        self,
        *,
        contexto_jogo: Callable[[], Mapping[str, Any]],
        analisar_imagem: Callable[[str, str], str],
        falar: Callable[..., Any],
        habilitado: bool = True,
        credencial_disponivel: bool = True,
        capturar: Callable[[Mapping[str, Any]], str] = capturar_janela_jogo_base64,
        obter_cursor: Callable[[], tuple[int, int] | None] = _posicao_cursor_sistema,
        sessoes: ContextoSessoesJogo | None = None,
        memoria_jogos: Any = None,
        confirmar_contexto: Callable[[Mapping[str, Any]], Mapping[str, Any]] = confirmar_contexto_janela_sistema,
        registrar_analise_cb: Callable[[Mapping[str, Any]], Any] | None = None,
        pesquisar_item: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]] | None = None,
        sintetizar_texto: Callable[[str], str] | None = None,
        ao_mapear_inventario: Callable[[Mapping[str, Any], Mapping[str, Any], str, bool], Any] | None = None,
        processar_sugestao_proativa: Callable[[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]], Any] | None = None,
        progresso_cooperativo_cb: Callable[[Mapping[str, Any]], Any] | None = None,
        esperar_tooltip_s: float = 0.20,
        esperar_recaptura_s: float = 0.12,
        sleep: Callable[[float], Any] = time.sleep,
        thread_factory: Callable[..., Any] = threading.Thread,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.contexto_jogo = contexto_jogo
        self.analisar_imagem = analisar_imagem
        self.falar = falar
        self.habilitado = bool(habilitado)
        self.credencial_disponivel = bool(credencial_disponivel)
        self.capturar = capturar
        self.obter_cursor = obter_cursor
        self.sessoes = sessoes or ContextoSessoesJogo(memoria=memoria_jogos)
        self.memoria_jogos = memoria_jogos
        self.confirmar_contexto = confirmar_contexto
        self.registrar_analise_cb = registrar_analise_cb
        self.pesquisar_item = pesquisar_item
        self.sintetizar_texto = sintetizar_texto
        self.ao_mapear_inventario = ao_mapear_inventario
        self.processar_sugestao_proativa = processar_sugestao_proativa
        self.progresso_cooperativo_cb = progresso_cooperativo_cb
        self.esperar_tooltip_s = max(0.0, float(esperar_tooltip_s))
        self.esperar_recaptura_s = max(0.0, float(esperar_recaptura_s))
        self.sleep = sleep
        self.thread_factory = thread_factory
        self.log = log
        self._lock = threading.Lock()
        self._em_andamento = False
        self._ultimas_analises: dict[str, dict[str, Any]] = {}
        self._assinaturas_quadros: dict[str, str] = {}
        self._estados_tela: dict[str, dict[str, Any]] = {}

    def _observar_estado_tela(
        self,
        identidade: Mapping[str, Any],
        texto: str,
    ) -> dict[str, Any]:
        """Guarda só em RAM o estado de tela explicitamente dito pelo usuário."""
        chave = str(identidade.get("chave") or "jogo")
        normalizado = _normalizar_chave(texto).strip(" ?!.,")
        estado = ""
        if re.search(
            r"\b(?:ainda\s+)?(?:estou|to|tou|tô)\s+(?:no|na)\s+"
            r"(?:menu|tela\s+inicial)(?:\s+do\s+jogo)?\b",
            normalizado,
        ):
            estado = "menu"
        elif re.search(r"\b(?:jogo\s+)?(?:esta|ta|tá)\s+carregando\b|\bloading\b", normalizado):
            estado = "carregando"
        elif re.search(
            r"\b(?:entrei|ja\s+entrei|comecei)\s+(?:no\s+)?jogo\b|"
            r"\b(?:agora\s+)?(?:estou|to|tô)\s+jogando\b|\bja\s+carregou\b",
            normalizado,
        ):
            estado = "jogando"
        if estado:
            registro = {
                "estado": estado,
                "origem": "fala_do_usuario",
                "texto": str(texto or "").strip()[:180],
                "ts": time.time(),
            }
            self._estados_tela[chave] = registro
            self.log(f"🎮 [VISÃO:ESTADO] {chave} -> {estado} | origem=usuário")
            return dict(registro)
        return {}

    def _estado_tela_atual(
        self,
        identidade: Mapping[str, Any],
        contexto: Mapping[str, Any],
        *,
        max_idade_s: float = 300.0,
    ) -> dict[str, Any]:
        """Combina fala recente com sinais transitórios do título da janela."""
        titulo = _normalizar_chave(contexto.get("titulo") or identidade.get("titulo") or "")
        if re.search(r"\b(?:loading|carregando|inicializando)\b", titulo):
            return {
                "estado": "carregando",
                "origem": "titulo_da_janela",
                "texto": str(contexto.get("titulo") or "")[:180],
                "ts": time.time(),
            }
        chave = str(identidade.get("chave") or "jogo")
        registro = dict(self._estados_tela.get(chave) or {})
        if registro and time.time() - float(registro.get("ts") or 0.0) <= max_idade_s:
            return registro
        if registro:
            self._estados_tela.pop(chave, None)
        return {}

    def _notificar_cooperacao(
        self,
        plano_id: str,
        fase: str,
        **dados: Any,
    ) -> None:
        """Publica apenas progresso sanitizado; nunca envia imagem ou texto do item."""
        if not plano_id or not callable(self.progresso_cooperativo_cb):
            return
        evento = {
            "plano_id": str(plano_id),
            "fase": str(fase or "").strip().casefold(),
        }
        evento.update({
            str(chave)[:60]: valor
            for chave, valor in dados.items()
            if isinstance(valor, (str, int, float, bool, type(None)))
        })
        try:
            self.progresso_cooperativo_cb(evento)
        except Exception as erro:
            self.log(
                "⚠️ [VISÃO:COOPERAÇÃO] progresso isolado | "
                f"erro={type(erro).__name__}"
            )

    @staticmethod
    def _assinatura_imagem(imagem: str) -> str:
        return hashlib.sha256(str(imagem or "").encode("ascii", "ignore")).hexdigest()[:12]

    def _capturar_quadro_atual(
        self,
        contexto: Mapping[str, Any],
        identidade: Mapping[str, Any],
    ) -> str:
        """Captura sempre e confirma quando o backend devolve o quadro anterior."""
        chave = str(identidade.get("chave") or "jogo")
        imagem = str(self.capturar(contexto) or "")
        if not imagem:
            return ""
        assinatura = self._assinatura_imagem(imagem)
        anterior = self._assinaturas_quadros.get(chave, "")
        repetido = bool(anterior and assinatura == anterior)
        if repetido:
            self.log(
                f"⚠️ [VISÃO:QUADRO] captura idêntica à anterior ({assinatura}); recapturando."
            )
            if self.esperar_recaptura_s:
                self.sleep(self.esperar_recaptura_s)
            segunda = str(self.capturar(contexto) or "")
            if segunda:
                segunda_assinatura = self._assinatura_imagem(segunda)
                if segunda_assinatura != assinatura:
                    imagem = segunda
                    assinatura = segunda_assinatura
                    repetido = False
        self._assinaturas_quadros[chave] = assinatura
        self.log(
            f"🎮 [VISÃO:QUADRO] assinatura={assinatura} "
            f"estado={'ainda_idêntico' if repetido else 'atual'}"
        )
        return imagem

    def _contexto_confirmado(self) -> dict[str, Any]:
        contexto = dict(self.contexto_jogo() or {})
        if callable(self.confirmar_contexto):
            try:
                confirmado = self.confirmar_contexto(contexto)
                if confirmado:
                    contexto = dict(confirmado)
            except Exception:
                pass
        return contexto

    def _analisar_com_identidade(
        self,
        imagem: str,
        prompt: str,
        identidade: Mapping[str, Any],
        estado_tela: Mapping[str, Any] | None = None,
    ) -> str:
        resposta = str(self.analisar_imagem(imagem, prompt) or "").strip()
        contradiz_jogo = resposta_contradiz_identidade_sistema(resposta, identidade)
        inventa_falha = resposta_inventa_falha_da_laylay(resposta)
        contradiz_tela = resposta_contradiz_estado_tela(resposta, estado_tela)
        if not contradiz_jogo and not inventa_falha and not contradiz_tela:
            return resposta
        estado = str(dict(estado_tela or {}).get("estado") or "").strip().casefold()
        if contradiz_tela:
            self.log(
                f"⚠️ [VISÃO:ESTADO] resposta inventou gameplay durante {estado}; bloqueando."
            )
            if estado == "carregando":
                return "O jogo ainda está carregando. Vou esperar a cena aparecer antes de comentar o que você está fazendo."
            return "Você ainda está no menu do jogo. Vou esperar a partida aparecer antes de comentar a cena."
        jogo = str(identidade.get("nome_candidato") or "o jogo em execução").strip()
        self.log(
            f"⚠️ [VISÃO:IDENTIDADE] resposta contradisse processo confirmado ({jogo}); corrigindo."
        )
        prompt_correcao = (
            prompt
            + "\nCORREÇÃO OBRIGATÓRIA: o rascunho abaixo contradisse a identidade confirmada pelo "
            f"sistema. O jogo é {jogo}. Refaça a análise sem tentar identificar outro jogo, sem "
            "diagnosticar que a Laylay caiu e sem discutir lançamento ou disponibilidade. "
            "Se o conteúdo visual não estiver claro, admita "
            "somente a dúvida sobre o conteúdo.\nRascunho rejeitado: "
            + resposta[:700]
        )
        corrigida = str(self.analisar_imagem(imagem, prompt_correcao) or "").strip()
        if (
            corrigida
            and not resposta_contradiz_identidade_sistema(corrigida, identidade)
            and not resposta_inventa_falha_da_laylay(corrigida)
        ):
            return corrigida
        return (
            f"O processo em foco confirma que o jogo é {jogo}, mas a imagem não me deu segurança "
            "para identificar isso sem confundir o conteúdo com o de outro jogo."
        )

    @property
    def em_andamento(self) -> bool:
        with self._lock:
            return self._em_andamento

    def tem_analise_recente(self, max_idade_s: float = 900.0) -> bool:
        """Indica continuidade visual real sem tornar toda repetição um comando."""
        try:
            contexto = self._contexto_confirmado()
            if not bool(contexto.get("ativo")):
                return False
            identidade = identificar_jogo(contexto)
            anterior = dict(self._ultimas_analises.get(str(identidade.get("chave") or "")) or {})
            return bool(
                anterior
                and time.time() - float(anterior.get("ts") or 0.0) <= max(0.0, float(max_idade_s))
            )
        except Exception:
            return False

    def observar_texto_usuario(self, texto: str) -> dict[str, Any]:
        """Observa perfil e estado efêmero da tela durante a sessão de jogo."""
        contexto = self._contexto_confirmado()
        if not bool(contexto.get("ativo")):
            return {}
        identidade = identificar_jogo(contexto)
        self._observar_estado_tela(identidade, str(texto or ""))
        return self.sessoes.observar(identidade, str(texto or ""))

    def processar_atualizacao_perfil(self, texto: str) -> bool:
        """Confirma localmente um dado puro de personagem, sem chamar LLM."""
        original = str(texto or "").strip()
        normalizado = _normalizar_chave(original).strip(" ?!.,")
        puro = re.fullmatch(
            r"(?:(?:so|só)\s+(?:um\s+)?aviso\s*[,;:]?\s*)?"
            r"(?:(?:agora\s+)?(?:eu\s+)?)?"
            r"(?:(?:estou|to|tô|cheguei)\s+(?:no\s+)?nivel\s*\d{1,4}|"
            r"meu\s+nivel\s+(?:e|eh)\s*\d{1,4}|"
            r"(?:minha\s+classe\s+(?:e|eh)|sou|estou\s+jogando\s+de|to\s+de)\s+"
            r"[a-z0-9 _-]{2,35}|"
            r"minha\s+build\s+(?:e|eh|de|focada\s+em)\s+[a-z0-9 _-]{2,40})",
            normalizado,
        )
        novos = extrair_perfil_build(original)
        if not puro or not novos:
            return False
        contexto = self._contexto_confirmado()
        if not contexto.get("ativo"):
            return False
        identidade = identificar_jogo(contexto)
        perfil = self.sessoes.observar(identidade, original)
        partes = []
        if "nivel" in novos:
            partes.append(f"nível {int(novos['nivel'])}")
        if novos.get("classe"):
            partes.append(f"classe {novos['classe']}")
        if novos.get("build"):
            partes.append(f"build {novos['build']}")
        jogo = str(identidade.get("nome_candidato") or "este jogo")
        self.falar(
            f"Anotado: em {jogo}, seu perfil agora registra "
            f"{', '.join(partes)}. Vou usar isso nas próximas análises.",
            "calma", 1,
        )
        self.log(f"⚡ [VISÃO:PERFIL] atualização local={novos} | perfil={perfil}")
        return True

    def aplicar_referencia_item(self, texto: str) -> bool:
        """Transforma correções naturais em estado do equipamento atual."""
        normalizado = _normalizar_chave(texto).strip(" ?!.,")
        if not re.search(
            r"\b(?:esse|essa|este|esta|ele|ela)\b.{0,35}"
            r"\b(?:meu|minha|atual|equipad[oa]|estou usando|to usando|uso agora)\b",
            normalizado,
        ):
            return False
        contexto = self._contexto_confirmado()
        if not contexto.get("ativo") or self.memoria_jogos is None:
            return False
        identidade = identificar_jogo(contexto)
        anterior = dict(self._ultimas_analises.get(str(identidade.get("chave") or "")) or {})
        item = dict(anterior.get("item") or {})
        if not item.get("nome") or not (item.get("slot") or item.get("categoria")):
            return False
        perfil = self.sessoes.perfil(identidade)
        inventario_atual = self.memoria_jogos.carregar_inventario(identidade)
        personagem = str(
            perfil.get("personagem") or inventario_atual.get("personagem") or "padrao"
        )
        item.update(estado="equipado", equipado=True)
        if not self.memoria_jogos.definir_item_equipado(
            identidade, item, personagem=personagem,
        ):
            return False
        anterior["item"] = item
        self._ultimas_analises[str(identidade.get("chave") or "")] = anterior
        slot = str(item.get("slot") or item.get("categoria") or "esse espaço")
        self.falar(
            f"Entendi. Marquei {item.get('nome')} como seu item atual em {slot}; "
            "nas próximas comparações vou usar ele como referência.",
            "calma", 1,
        )
        return True

    def _registrar_analise(
        self, *, identidade: Mapping[str, Any], tipo: str, pergunta: str,
        resposta: str, perfil: Mapping[str, Any], solicita_complemento: bool,
        pesquisa: Mapping[str, Any] | None = None,
    ) -> None:
        if self.memoria_jogos is not None:
            try:
                self.memoria_jogos.registrar_observacao(
                    identidade, tipo=tipo, pergunta=pergunta,
                    observacao=resposta, perfil=perfil,
                )
            except Exception as erro:
                self.log(f"⚠️ [VISÃO:MEMÓRIA] persistência ignorada: {type(erro).__name__}")
        if callable(self.registrar_analise_cb):
            self.registrar_analise_cb({
                "identidade": dict(identidade), "tipo": tipo,
                "pergunta": pergunta, "resposta": resposta,
                "perfil": dict(perfil),
                "solicita_complemento": bool(solicita_complemento),
                "pesquisa": dict(pesquisa or {}),
            })

    def continuar_pendencia(self, texto: str, pendencia: Mapping[str, Any] | None) -> bool:
        """Retoma a última dúvida visual com qualquer complemento contextual."""
        pendente = dict(pendencia or {})
        if (
            pendente.get("status") != "ativa"
            or str(pendente.get("origem") or "") != "visao_jogo"
            or str(pendente.get("dominio") or "") != "jogo"
        ):
            return False
        contexto = self._contexto_confirmado()
        if not contexto.get("ativo"):
            return False
        identidade = identificar_jogo(contexto)
        chave = str(identidade.get("chave") or "")
        opcoes = list(pendente.get("opcoes") or [])
        dados_pendencia = dict(opcoes[0] or {}) if opcoes and isinstance(opcoes[0], dict) else {}
        if dados_pendencia.get("jogo_chave") and dados_pendencia.get("jogo_chave") != chave:
            return False
        anterior = dict(self._ultimas_analises.get(chave) or {})
        if not anterior or time.time() - float(anterior.get("ts") or 0.0) > 900.0:
            return False
        complemento = str(texto or "").strip()
        if not complemento:
            return False
        # Pedidos de reanálise pertencem ao detector visual, que captura um
        # quadro novo. Eles não são dados complementares da imagem anterior.
        if _PEDIDO_NOVA_CAPTURA.match(complemento):
            return False
        # Uma pergunta visual pendente jamais ganha prioridade sobre um novo
        # comando de outro domínio. Esta é a barreira defensiva caso o árbitro
        # superior classifique o turno de forma imprecisa.
        if _COMANDO_FORA_DA_VISAO.match(complemento):
            return False
        perfil = self.sessoes.observar(identidade, complemento)
        with self._lock:
            if self._em_andamento:
                return False
            self._em_andamento = True

        def trabalhar() -> None:
            try:
                memoria = ""
                if self.memoria_jogos is not None:
                    memoria = self.memoria_jogos.resumo_para_prompt(identidade)
                prompt = _montar_prompt(
                    str(anterior.get("pergunta") or pendente.get("conteudo") or ""),
                    dict(anterior.get("contexto") or contexto),
                    str(anterior.get("tipo") or "avaliacao_item"),
                    identidade=identidade, perfil=perfil,
                    memoria_jogo=memoria, complemento=complemento,
                )
                resposta_anterior = str(
                    pendente.get("conteudo") or anterior.get("resposta") or ""
                ).strip()
                pesquisa_anterior = dict(anterior.get("pesquisa") or {})
                item_anterior = dict(anterior.get("item") or {})
                prompt_textual = (
                    "Você é a Laylay concluindo uma avaliação de item já lida anteriormente. "
                    "Não há uma imagem nova e você não deve fingir que olhou novamente. Cruze somente "
                    "a leitura anterior, o novo dado do usuário, o perfil da sessão e a evidência externa "
                    "já obtida. Responda em português brasileiro natural, diretamente, em até três frases. "
                    "Se o novo dado ainda não bastar, diga exatamente o que continua faltando. "
                    "Não devolva JSON, URL nem marcadores internos.\n"
                    f"Jogo confirmado: {identidade.get('nome_candidato')}.\n"
                    f"Pergunta original: {anterior.get('pergunta') or ''}\n"
                    f"Leitura anterior: {resposta_anterior[:1200]}\n"
                    f"Item estruturado: {item_anterior}\n"
                    f"Perfil atual da sessão: {perfil}\n"
                    f"Novo dado informado pelo usuário: {complemento}\n"
                    + _evidencia_pesquisa_para_prompt(pesquisa_anterior)
                )
                inicio = time.perf_counter()
                resposta = (
                    str(self.sintetizar_texto(prompt_textual) or "").strip()
                    if callable(self.sintetizar_texto) else ""
                )
                if resposta:
                    self.log(
                        f"⚡ [VISÃO:CONTINUIDADE] síntese_textual="
                        f"{(time.perf_counter() - inicio) * 1000:.0f}ms"
                    )
                else:
                    # Compatibilidade: sem sintetizador textual disponível, a
                    # leitura visual anterior ainda pode concluir o mesmo fio.
                    resposta = self._analisar_com_identidade(
                        str(anterior.get("imagem") or ""), prompt, identidade,
                    )
                if not resposta:
                    self.falar("Eu guardei o contexto, mas a continuação visual não respondeu direito agora.", "calma", 1)
                    return
                solicita = resposta_pede_complemento(resposta)
                self.falar(resposta[:600], "curiosa", 2)
                self._registrar_analise(
                    identidade=identidade, tipo=str(anterior.get("tipo") or "avaliacao_item"),
                    pergunta=str(anterior.get("pergunta") or ""), resposta=resposta[:1200],
                    perfil=perfil, solicita_complemento=solicita,
                    pesquisa=pesquisa_anterior,
                )
            finally:
                with self._lock:
                    self._em_andamento = False

        try:
            self.thread_factory(target=trabalhar, daemon=True).start()
            return True
        except Exception:
            with self._lock:
                self._em_andamento = False
            return False

    def continuar_analise_recente(self, texto: str) -> bool:
        """Dá um veredito curto usando a última leitura, sem nova visão ou LLM local."""
        normalizado = _normalizar_chave(texto).strip(" ?!.,")
        if not re.fullmatch(
            r"(?:mas\s+)?(?:(?:ela|ele|isso|isto|esse\s+no|essa\s+habilidade)\s+)?(?:"
            r"vale\s+a\s+pena\s+(?:pega(?:r)?|usar|ativar|escolher)(?:\s+(?:ela|ele|isso))?|"
            r"(?:e|eh)\s+(?:uma\s+)?boa\s+(?:pega(?:r)?|escolha)(?:\s+(?:ela|ele|isso))?|"
            r"(?:e|eh)\s+bom\s+(?:pega(?:r)?|usar|ativar)(?:\s+(?:ela|ele|isso))?|"
            r"(?:devo|eu\s+devo)\s+(?:pega(?:r)?|usar|ativar)(?:\s+(?:ela|ele|isso))?"
            r")",
            normalizado,
        ):
            return False
        contexto = self._contexto_confirmado()
        if not contexto.get("ativo"):
            return False
        identidade = identificar_jogo(contexto)
        chave = str(identidade.get("chave") or "")
        anterior = dict(self._ultimas_analises.get(chave) or {})
        if not anterior or time.time() - float(anterior.get("ts") or 0.0) > 900.0:
            return False
        habilidade = dict(anterior.get("habilidade") or {})
        item = dict(anterior.get("item") or {})
        resposta_anterior = str(anterior.get("resposta") or "").strip()
        perfil = self.sessoes.perfil(identidade)
        if habilidade:
            resposta = parecer_local_habilidade(habilidade, perfil)
        elif item:
            nome = str(item.get("nome") or "esse item")
            if re.search(r"\b(?:nao pode|não pode|incompativel|incompatível|pior|fraco|ruim)\b", resposta_anterior, re.I):
                resposta = f"Eu não pegaria {nome} agora. Pela leitura anterior, ele não resolve bem a sua necessidade atual."
            elif re.search(r"\b(?:bom|boa|forte|melhor|util|útil|vale)\b", resposta_anterior, re.I):
                resposta = f"Sim, {nome} parece valer a pena pelo que consegui ler, desde que não custe um upgrade mais importante para sua build."
            else:
                resposta = (
                    f"Ainda não tenho evidência suficiente para dizer que {nome} vale o investimento. "
                    "Eu compararia o ganho visível com o item atual antes de pegar."
                )
        elif resposta_anterior:
            habilidade_inferida = {
                "nome": "essa escolha",
                "efeito": resposta_anterior[:420],
                "beneficios": [],
                "custo_pontos": None,
            }
            resposta = parecer_local_habilidade(habilidade_inferida, perfil)
        else:
            return False
        anterior["resposta"] = resposta
        anterior["ts"] = time.time()
        self._ultimas_analises[chave] = anterior
        self.log(f"⚡ [VISÃO:CONTINUIDADE] veredito local imediato | jogo={identidade.get('nome_candidato')}")
        self.falar(resposta[:600], "curiosa", 2)
        self._registrar_analise(
            identidade=identidade,
            tipo="continuacao_visual",
            pergunta=str(texto or ""),
            resposta=resposta,
            perfil=perfil,
            solicita_complemento=False,
            pesquisa=dict(anterior.get("pesquisa") or {}),
        )
        return True

    def executar(self, params: Mapping[str, Any] | None) -> bool:
        dados = dict(params or {})
        plano_cooperativo_id = str(dados.get("_plano_cooperativo_id") or "").strip()
        pergunta = str(dados.get("pergunta") or "").strip()
        contexto = self._contexto_confirmado()
        if not bool(contexto.get("ativo")) or not pergunta:
            self._notificar_cooperacao(
                plano_cooperativo_id, "falha", status="contexto_jogo_indisponivel",
            )
            return False
        tipo = str(dados.get("tipo") or "")
        if tipo == "continuacao_visual" and self.continuar_analise_recente(pergunta):
            return True
        if not self.habilitado:
            self._notificar_cooperacao(
                plano_cooperativo_id, "falha", status="visao_desativada",
            )
            self.falar("A visão do modo jogo está desativada nas configurações.", "calma", 1)
            return True
        if not self.credencial_disponivel:
            self._notificar_cooperacao(
                plano_cooperativo_id, "falha", status="credencial_visual_ausente",
            )
            self.falar("A visão do jogo ainda precisa da chave do serviço visual nas configurações.", "calma", 1)
            return True
        proativo = bool(dados.get("_proativo"))
        identidade = identificar_jogo(contexto)
        estado_tela = self._estado_tela_atual(identidade, contexto)
        if proativo and str(estado_tela.get("estado") or "") in {"menu", "carregando"}:
            self.log(
                "🎮 [VISÃO:PRESENÇA] observação adiada | "
                f"estado={estado_tela.get('estado')} origem={estado_tela.get('origem')}"
            )
            return True
        if tipo == "complemento_visual":
            chave = str(identidade.get("chave") or "")
            anterior = dict(self._ultimas_analises.get(chave) or {})
            if anterior and time.time() - float(anterior.get("ts") or 0.0) <= 900.0:
                pergunta_anterior = str(anterior.get("pergunta") or "").strip()
                resposta_anterior = str(anterior.get("resposta") or "").strip()
                pergunta = (
                    f"Retome a dúvida anterior: {pergunta_anterior}. "
                    f"A leitura anterior concluiu: {resposta_anterior[:700]}. "
                    f"O usuário agora mostrou na tela a informação que faltava ({pergunta}). "
                    "Use obrigatoriamente o quadro novo, confira os atributos visíveis e dê "
                    "um veredito atualizado sem pedir os mesmos dados novamente."
                )
                self.log("🎮 [VISÃO:CONTINUIDADE] complemento visual com nova captura.")
            else:
                tipo = "inspecao_personagem"
                pergunta = (
                    "Leia no quadro atual os atributos, status e informações visíveis do "
                    "personagem. Resuma os valores com precisão, identifique a classe ou build "
                    "somente se houver evidência e guarde esses dados para comparações posteriores."
                )
                self.log("🎮 [VISÃO] ficha do personagem apresentada sem análise anterior.")
        if tipo == "reanalise":
            chave = str(identidade.get("chave") or "")
            anterior = dict(self._ultimas_analises.get(chave) or {})
            if anterior and time.time() - float(anterior.get("ts") or 0.0) <= 900.0:
                pergunta_anterior = str(anterior.get("pergunta") or "").strip()
                tipo_anterior = str(anterior.get("tipo") or "observacao").strip()
                if pergunta_anterior:
                    pergunta = pergunta_anterior
                tipo = tipo_anterior if tipo_anterior != "reanalise" else "observacao"
                self.log(
                    f"🎮 [VISÃO:CONTINUIDADE] nova captura para tipo={tipo} "
                    f"| pergunta={pergunta[:100]}"
                )
            else:
                tipo = "observacao"
                pergunta = (
                    "Observe novamente o quadro atual do jogo e descreva com precisão "
                    "o que está visível agora."
                )
        perfil = self.sessoes.observar(identidade, pergunta)
        with self._lock:
            if self._em_andamento:
                if not proativo:
                    self.falar("Ainda tô olhando a imagem anterior. Só um instante.", "calma", 1)
                return bool(proativo)
            self._em_andamento = True

        def trabalhar() -> None:
            inicio_cooperativo = time.perf_counter()
            try:
                contexto_captura = dict(contexto)
                if tipo in {"avaliacao_item", "avaliacao_habilidade", "avaliacao_entidade"}:
                    if self.esperar_tooltip_s:
                        self.sleep(self.esperar_tooltip_s)
                    posicao = self.obter_cursor() if callable(self.obter_cursor) else None
                    limites = dict(contexto.get("limites") or {})
                    if posicao:
                        x, y = int(posicao[0]), int(posicao[1])
                        left = int(limites.get("left") or 0)
                        top = int(limites.get("top") or 0)
                        width = int(limites.get("width") or 0)
                        height = int(limites.get("height") or 0)
                        dentro = left <= x < left + width and top <= y < top + height
                        contexto_captura["cursor"] = {"x": x, "y": y}
                        contexto_captura["cursor_dentro_janela"] = dentro
                    else:
                        dentro = False
                        contexto_captura["cursor_dentro_janela"] = False
                    if not dentro:
                        self._notificar_cooperacao(
                            plano_cooperativo_id, "falha", status="cursor_fora_do_item",
                        )
                        self.falar(
                            "Deixa o mouse sobre o item dentro da janela do jogo e me pergunta de novo. Assim eu sei exatamente qual comparar.",
                            "calma", 1,
                        )
                        return
                imagem_pre_capturada = str(dados.get("_imagem_pre_capturada") or "")
                if imagem_pre_capturada:
                    imagem = imagem_pre_capturada
                    self.log("🎮 [VISÃO] Usando quadro atual pré-validado pelo observador.")
                else:
                    self.log("🎮 [VISÃO] Capturando somente a janela do jogo...")
                    imagem = self._capturar_quadro_atual(contexto_captura, identidade)
                if not imagem:
                    self._notificar_cooperacao(
                        plano_cooperativo_id, "falha", status="captura_indisponivel",
                    )
                    if not proativo:
                        self.falar(
                            "Não consegui enxergar a janela do jogo agora. Se ele estiver em tela cheia exclusiva, tenta mudar para janela sem borda.",
                            "calma", 1,
                        )
                    return
                imagens_entrada = desempacotar_imagens(imagem)
                if len(imagens_entrada) > 1:
                    dimensoes = ",".join(
                        f"{item.get('width')}x{item.get('height')}"
                        for item in imagens_entrada
                    )
                    self.log(
                        f"🎮 [VISÃO:CAPTURA] multirrecorte={len(imagens_entrada)} "
                        f"dimensões={dimensoes}"
                    )
                prompt = _montar_prompt(
                    pergunta,
                    contexto_captura,
                    tipo,
                    identidade=identidade,
                    perfil=perfil,
                    memoria_jogo=(
                        self.memoria_jogos.resumo_para_prompt(
                            identidade, incluir_observacoes=False,
                        )
                        if self.memoria_jogos is not None else ""
                    ),
                    estado_tela=estado_tela,
                )
                inicio_leitura = time.perf_counter()
                resposta_bruta = self._analisar_com_identidade(
                    imagem, prompt, identidade, estado_tela,
                )
                try:
                    tamanho_kb = len(imagem) * 3 / 4 / 1024
                except TypeError:
                    tamanho_kb = 0.0
                self.log(
                    f"⚡ [VISÃO:LATÊNCIA] leitura="
                    f"{(time.perf_counter() - inicio_leitura) * 1000:.0f}ms "
                    f"imagem={tamanho_kb:.0f}KB"
                )
                inventario_visual: dict[str, Any] = {}
                sugestao_proativa: dict[str, Any] = {}
                habilidade_visual: dict[str, Any] = {}
                if tipo in {"inspecao_inventario", "observacao_inventario_proativa"}:
                    resposta, inventario_visual, sugestao_proativa = extrair_dados_inventario(
                        resposta_bruta
                    )
                    item_visual = {}
                elif tipo == "observacao_presenca_proativa":
                    resposta, sugestao_proativa = extrair_presenca_visual(resposta_bruta)
                    item_visual = {}
                elif tipo in {"avaliacao_habilidade", "avaliacao_entidade", "analise_build"}:
                    resposta, habilidade_visual = extrair_habilidade_da_resposta_visual(
                        resposta_bruta
                    )
                    item_visual = {}
                    if tipo == "avaliacao_entidade" and not habilidade_visual:
                        resposta, item_visual = extrair_item_da_resposta_visual(resposta)
                else:
                    resposta, item_visual = extrair_item_da_resposta_visual(resposta_bruta)
                diagnostico_confirmacao: dict[str, Any] = {}
                if tipo == "avaliacao_item" and precisa_confirmar_item(
                    item_visual, multiplas_imagens=len(imagens_entrada) > 1,
                ):
                    recorte_detalhe = selecionar_recorte_detalhe(imagem)
                    if recorte_detalhe:
                        inicio_confirmacao = time.perf_counter()
                        prompt_confirmacao = montar_prompt_confirmacao_item(
                            item_visual,
                            jogo=str(identidade.get("nome_candidato") or ""),
                        )
                        resposta_confirmacao = self._analisar_com_identidade(
                            recorte_detalhe, prompt_confirmacao, identidade,
                        )
                        _fala_confirmacao, segunda_leitura = extrair_item_da_resposta_visual(
                            resposta_confirmacao
                        )
                        item_visual, diagnostico_confirmacao = reconciliar_leituras_item(
                            item_visual, segunda_leitura,
                        )
                        self.log(
                            f"🔍 [VISÃO:CONFIRMAÇÃO] "
                            f"status={diagnostico_confirmacao.get('status')} "
                            f"conflitos={diagnostico_confirmacao.get('conflitos') or []} "
                            f"latência={(time.perf_counter() - inicio_confirmacao) * 1000:.0f}ms"
                        )
                        if diagnostico_confirmacao.get("status") == "conflito":
                            resposta = (
                                "O texto do item ficou diferente entre duas leituras do recorte, "
                                "então não vou cravar o nome nem pesquisar como se ele estivesse confirmado. "
                                "Se você mantiver o tooltip aberto, eu posso conferir outra vez."
                            )
                        elif (
                            diagnostico_confirmacao.get("status") == "recuperada_por_recorte"
                            and (item_visual.get("nome") or item_visual.get("base"))
                        ):
                            nome_recuperado = str(
                                item_visual.get("nome") or item_visual.get("base")
                            )
                            resposta = (
                                f"No recorte aproximado consegui ler {nome_recuperado}, mas essa "
                                "identificação ainda tem confiança moderada. Vou usar a pesquisa "
                                "somente como apoio, sem tratar o nome como certeza."
                            )
                resposta = aplicar_perfil_confirmado_na_resposta(resposta, perfil)
                resposta = higienizar_alegacoes_visao(
                    resposta,
                    tipo=tipo,
                    contexto=contexto_captura,
                    identidade=identidade,
                )
                if tipo == "inspecao_personagem":
                    resposta = higienizar_inspecao_personagem(resposta, perfil)
                if (not resposta and not inventario_visual and not sugestao_proativa) or re.search(
                    r"não consegui analisar|groq (?:tá|esta) lotado|^(?:erro|falha)(?:\b|:)",
                    resposta or "",
                    re.I,
                ):
                    self._notificar_cooperacao(
                        plano_cooperativo_id, "falha", status="leitura_visual_invalida",
                    )
                    if not proativo:
                        self.falar("Eu consegui olhar, mas a análise visual não respondeu direito agora.", "calma", 1)
                    return
                if tipo == "avaliacao_item":
                    self._notificar_cooperacao(
                        plano_cooperativo_id,
                        "leitura_visual",
                        status=("item_lido" if item_visual else "item_nao_identificado"),
                        item_identificado=bool(item_visual),
                        confianca=float(dict(item_visual or {}).get("confianca") or 0.0),
                        duracao_ms=int((time.perf_counter() - inicio_cooperativo) * 1000),
                    )
                pesquisa: dict[str, Any] = {}
                if tipo == "avaliacao_item" and item_visual and callable(self.pesquisar_item):
                    pesquisa, resposta = pesquisar_e_sintetizar_item(
                        item_visual=item_visual,
                        identidade=identidade,
                        perfil=perfil,
                        pergunta=pergunta,
                        prompt=prompt,
                        resposta_visual=resposta,
                        imagem=imagem,
                        pesquisar_item=self.pesquisar_item,
                        sintetizar_texto=self.sintetizar_texto,
                        analisar_imagem=self._analisar_com_identidade,
                        log=self.log,
                    )
                if tipo == "avaliacao_item":
                    self._notificar_cooperacao(
                        plano_cooperativo_id,
                        "pesquisa",
                        status=(
                            "evidencia_externa_encontrada"
                            if pesquisa.get("ok") else "sem_evidencia_externa"
                        ),
                        pesquisa_ok=bool(pesquisa.get("ok")),
                        fontes=len(list(pesquisa.get("fontes") or [])),
                        cache=bool(pesquisa.get("cache")),
                        duracao_ms=int((time.perf_counter() - inicio_cooperativo) * 1000),
                    )
                resposta = aplicar_perfil_confirmado_na_resposta(resposta, perfil)
                resposta = higienizar_alegacoes_visao(
                    resposta,
                    tipo=tipo,
                    contexto=contexto_captura,
                    identidade=identidade,
                )[:1200]
                if inventario_visual and self.memoria_jogos is not None:
                    if proativo:
                        anterior_inventario = self.memoria_jogos.carregar_inventario(identidade)
                        if anterior_inventario:
                            esquema = dict(anterior_inventario.get("esquema") or {})
                            esquema.update(dict(inventario_visual.get("esquema") or {}))
                            equipados = dict(anterior_inventario.get("equipados") or {})
                            equipados.update(dict(inventario_visual.get("equipados") or {}))
                            inventario_visual = {
                                **anterior_inventario, **inventario_visual,
                                "esquema": esquema, "equipados": equipados,
                            }
                    self.memoria_jogos.salvar_inventario(identidade, inventario_visual)
                    self.log(
                        f"🧠 [INVENTÁRIO JOGO] slots={len(inventario_visual.get('esquema') or {})} "
                        f"equipados={sum(len(v) for v in dict(inventario_visual.get('equipados') or {}).values())} "
                        f"confiança={float(inventario_visual.get('confianca') or 0.0):.2f}"
                    )
                    if callable(self.ao_mapear_inventario):
                        self.ao_mapear_inventario(
                            identidade, inventario_visual, imagem, proativo,
                        )
                if item_visual and self.memoria_jogos is not None:
                    inventario_atual = self.memoria_jogos.carregar_inventario(identidade)
                    personagem = str(
                        perfil.get("personagem") or inventario_atual.get("personagem") or "padrao"
                    )
                    self.memoria_jogos.registrar_item_visual(
                        identidade, item_visual, personagem=personagem,
                    )
                # Uma observação espontânea pode soar curiosa e terminar em
                # pergunta, mas nunca deve prender o diálogo esperando uma
                # resposta. O diretor aprende silêncio separadamente após a
                # janela de feedback; pendência visual pertence só a pedidos
                # iniciados pelo usuário.
                solicita = resposta_pede_complemento(resposta) and not proativo
                if tipo == "avaliacao_item" and resposta:
                    self._notificar_cooperacao(
                        plano_cooperativo_id,
                        "parecer_final",
                        status="parecer_pronto",
                        memoria_atualizada=bool(item_visual and self.memoria_jogos is not None),
                        solicita_complemento=bool(solicita),
                        duracao_ms=int((time.perf_counter() - inicio_cooperativo) * 1000),
                    )
                if not proativo and resposta:
                    self.falar(resposta[:600], "curiosa", 2)
                elif (
                    proativo and sugestao_proativa.get("relevante")
                    and callable(self.processar_sugestao_proativa)
                ):
                    self.processar_sugestao_proativa(
                        sugestao_proativa, identidade, perfil,
                    )
                self._ultimas_analises[str(identidade.get("chave") or "")] = {
                    "imagem": imagem, "pergunta": pergunta, "tipo": tipo,
                    "contexto": contexto_captura, "item": item_visual,
                    "habilidade": habilidade_visual,
                    "entidade": habilidade_visual or item_visual,
                    "resposta": resposta,
                    "inventario": inventario_visual, "sugestao": sugestao_proativa,
                    "pesquisa": pesquisa, "ts": time.time(),
                    "confirmacao_item": diagnostico_confirmacao,
                }
                self._registrar_analise(
                    identidade=identidade, tipo=tipo, pergunta=pergunta,
                    resposta=resposta, perfil=perfil,
                    solicita_complemento=solicita,
                    pesquisa=pesquisa,
                )
            except Exception as erro:
                self.log(f"⚠️ [VISÃO JOGO] {type(erro).__name__}: {erro}")
                self._notificar_cooperacao(
                    plano_cooperativo_id, "falha", status="falha_interna_visao",
                )
                if not proativo:
                    self.falar("Deu um tropeço quando fui olhar o jogo. Não mexi em nada.", "calma", 1)
            finally:
                with self._lock:
                    self._em_andamento = False

        try:
            self.thread_factory(target=trabalhar, daemon=True).start()
        except Exception:
            with self._lock:
                self._em_andamento = False
            return False
        return True


def criar_visao_jogo_runtime(**kwargs: Any) -> VisaoJogoRuntime:
    return VisaoJogoRuntime(**kwargs)
