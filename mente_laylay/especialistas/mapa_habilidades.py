"""Mapa vivo das habilidades conhecidas pela mente única.

O mapa informa à camada conversacional o que existe e o que está disponível,
mas nunca autoriza execução. A autorização e a execução continuam pertencendo
ao porteiro, aos roteadores e aos executores determinísticos.
"""

from __future__ import annotations

import re
import time
import unicodedata
from threading import RLock
from typing import Any, Callable, Mapping

from mente_laylay.especialistas.capacidades import CAPACIDADES, consultar_capacidade


_DESCRICAO_DOMINIO = {
    "musica": (
        "buscar e controlar música; criar, listar, tocar e editar playlists do usuário; "
        "montar curadorias próprias com o histórico confirmado e copiar uma faixa "
        "delas somente quando o usuário pedir"
    ),
    "sistema": (
        "abrir, fechar e maximizar programas; ajustar volume; organizar janelas visíveis "
        "automaticamente por foco, áudio, uso recente e tempo aberto, ou posicionar "
        "aplicativos específicos à esquerda e à direita"
    ),
    "navegador": (
        "consultar a aba ativa e as abas abertas; abrir sites, pesquisar, controlar mídia, "
        "resumir o conteúdo da página atual, interagir com controles identificados de páginas, "
        "fechar abas e capturar a tela. "
        "A leitura não autoriza ações e comandos arbitrários de página não são expostos"
    ),
    "visao": (
        "observar a tela do jogo; para itens, ler o quadro atual, pesquisar evidências "
        "confiáveis e cruzar o resultado com a build e o inventário conhecidos"
    ),
    "agenda": (
        "criar, listar e cancelar lembretes ou ações agendadas; completar naturalmente "
        "horário ou data pendentes, persistir antes de confirmar e entregar lembretes pela "
        "central de notificações"
    ),
    "arquivos": (
        "pesquisar arquivos localmente por nome, caminho, conteúdo, tipo, significado e data; "
        "abrir um resultado escolhido; criar, mover, renomear, restaurar ou enviar itens à lixeira. "
        "Trocar uma extensão textual, como .txt por .md, é uma renomeação do arquivo e não "
        "uma conversão automática do conteúdo"
    ),
    "email": (
        "sincronizar e consultar emails; reunir emails, agenda, lembretes e alertas "
        "internos numa central que prioriza, agrupa e silencia categorias"
    ),
    "iot": "listar, consultar e controlar dispositivos inteligentes configurados",
    "area_transferencia": (
        "observar localmente conteúdo copiado relevante; ler e transformar textos ou links; "
        "oferecer investigação de mensagens de erro e, após aceitação, pesquisar internamente "
        "e explicar o resultado sem abrir o navegador; guardar conteúdo na memória somente "
        "quando o usuário pedir explicitamente"
    ),
    "caixa_entrada": (
        "guardar, classificar e consultar ideias, notas, links e tarefas pessoais; "
        "resumir uma discussão separando a ideia do usuário e as sugestões da Laylay"
    ),
    "pessoas": (
        "aprender pessoas e relações afirmadas explicitamente pelo usuário; consultar quem são, "
        "recordar fatos confirmados com proveniência, corrigir relações antigas e esquecer um "
        "perfil somente após confirmação"
    ),
    "memoria": (
        "consultar aprendizados persistentes e locais sobre o usuário; distinguir o que foi "
        "confirmado diretamente, o que é apenas um padrão maduro e o que veio de registros "
        "antigos; omitir hipóteses fracas, contraditas ou não verificadas"
    ),
    "cooperacao": (
        "combinar habilidades por um plano único; compartilhar referências temporárias sem "
        "expor o conteúdo bruto; executar cada etapa pelos porteiros normais e confirmar o "
        "resultado final. Os fluxos ativos cobrem texto copiado em arquivo, organização "
        "inteligente de janelas, avaliação contextual de itens no jogo e curadoria musical "
        "que relaciona playlists reais ao histórico confirmado"
    ),
    "avatar": (
        "possuir um avatar visual com emoções e animações; conversar sobre skins e designs. "
        "Alterações nos arquivos só são reais depois que o código executor as confirmar"
    ),
    "conversa": "conversar, explicar, raciocinar, consultar clima e sugerir ações",
}

_TERMOS_DOMINIO = {
    "musica": ("musica", "som", "faixa", "playlist", "tocar", "pausar", "youtube", "spotify"),
    "sistema": (
        "programa", "aplicativo", "app", "janela", "janelas", "volume", "computador", "pc",
        "area de trabalho", "desktop", "organiza a tela", "na esquerda", "na direita",
        "posiciona", "dividir a tela",
    ),
    "navegador": ("site", "pagina", "navegador", "aba", "url", "pesquis", "chrome"),
    "visao": ("tela", "imagem", "item", "inventario", "atributo", "build", "jogo", "olha", "veja"),
    "agenda": ("lembrete", "agenda", "agendar", "compromisso", "horario"),
    "arquivos": (
        "arquivo", "pasta", "lixeira", "renome", "mover", "documento",
        "codigo", "código", "projeto laylay",
        "extensao", "extensão", "formato", ".txt", ".md", "markdown",
        "encontra o arquivo", "procura nos arquivos", "codigo que controla",
        "arquivos falam", "imagem que usei",
    ),
    "email": (
        "email", "gmail", "mensagem nova", "caixa de entrada", "notificacao",
        "notificacoes", "aviso", "avisos", "alerta", "alertas",
    ),
    "iot": ("luz", "lampada", "ventilador", "tomada", "brilho", "dispositivo"),
    "area_transferencia": (
        "area de transferencia", "clipboard", "texto copiado", "conteudo copiado",
        "link copiado", "erro copiado", "mensagem de erro", "investigar erro",
        "detectar erro", "o que copiei",
    ),
    "caixa_entrada": (
        "caixa de entrada", "anotacao", "anotacoes", "anota", "nota pessoal",
        "guarda essa ideia", "minhas ideias", "ideias salvas", "ideias anotadas",
        "nossa discussao", "nossa conversa",
        "o que discutimos", "salva nossa ideia",
    ),
    "pessoas": (
        "pessoa", "pessoas", "quem e", "quem é", "quem sao", "quem são",
        "o que sabe sobre", "o que lembra sobre", "minha irma", "meu irmao",
        "minha amiga", "meu amigo", "minha mae", "meu pai", "esquece sobre",
        "minha namorada", "meu namorado", "minha esposa", "meu marido",
    ),
    "memoria": (
        "memoria sobre mim", "memória sobre mim", "consulta sua memoria",
        "consulta sua memória", "aprendeu comigo",
        "aprendeu sobre mim", "guardou sobre mim", "lembra sobre mim",
        "lembra que eu", "o que eu te ensinei", "o que eu te contei",
        "seus aprendizados", "aprendizados sobre mim",
    ),
    "cooperacao": (
        "combinar habilidades", "usar habilidades juntas", "orquestracao",
        "texto copiado em arquivo", "conteudo copiado em arquivo",
        "o que copiei em um arquivo",
    ),
    "avatar": ("avatar", "skin", "skins", "png", "emocao visual", "animação do avatar"),
    "conversa": ("clima", "tempo", "convers", "explica", "duvida", "acha"),
}

_PEDIDO_CAPACIDADES = (
    "o que voce faz", "o que voce consegue", "suas habilidades",
    "quais habilidades", "que habilidades", "seus comandos",
    "do que voce e capaz", "o que pode fazer", "o que da para voce fazer",
)

_ROTULO_CAPACIDADE_NATURAL = {
    "arquivos": "criar, procurar e organizar arquivos",
    "sistema": "abrir programas e organizar janelas",
    "navegador": "trabalhar com sites, abas e páginas",
    "musica": "buscar e controlar músicas e playlists",
    "agenda": "cuidar de lembretes e compromissos",
    "memoria": "lembrar fatos confirmados sobre você",
    "pessoas": "recordar pessoas e relações que você me contou",
    "iot": "controlar os dispositivos da casa que estiverem configurados",
    "email": "consultar emails e notificações",
    "area_transferencia": "entender e transformar o que você copiou",
    "caixa_entrada": "guardar ideias e notas pessoais",
    "visao": "analisar o que aparece na tela durante um jogo",
    "avatar": "usar meu avatar e pensar em novos visuais",
    "conversa": "conversar, explicar e raciocinar com você",
}

_STATUS_INDISPONIVEIS = {
    "indisponivel", "nao_configurado", "sem_configuracao", "sem_suporte",
    "protocolo_indisponivel", "servico_indisponivel", "dependencia_ausente",
}
_STATUS_RECUPERADOS = {
    "sucesso", "executado", "confirmado", "aberto", "concluido", "ok",
    "playlist_aberta", "cor_ajustada", "branco_ajustado", "ligado", "desligado",
    "arquivo_criado", "pasta_criada", "arquivos_encontrados", "arquivo_aberto",
    "resumo_concluido",
}

_MODULO_SAUDE_POR_DOMINIO = {
    "email": "gmail",
    "navegador": "navegador",
    "iot": "iot",
    "visao": "visao_jogo",
    "conversa": "llm",
    "cooperacao": "orquestracao_cooperativa",
    "pessoas": "memoria_pessoas",
    "agenda": "agenda",
}

_DOMINIOS_CONVERSACIONAIS_DISPONIVEIS = frozenset({"avatar", "conversa"})


def _normalizar(texto: Any) -> str:
    base = unicodedata.normalize("NFKD", str(texto or ""))
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", base.casefold()).strip()


def _texto_pergunta_capacidade(texto: str) -> bool:
    """Reconhece capacidade e hipótese sem conceder autorização."""
    t = _normalizar(texto)
    if not t:
        return False
    if any(frase in t for frase in _PEDIDO_CAPACIDADES):
        return True
    return bool(re.search(
        r"\b(?:voce|laylay|lay)\s+(?:consegue|pode|sabe|e capaz)\b|"
        r"^(?:e\s+|mas\s+|entao\s+)?se eu\s+"
        r"(?:pedir|mandar|falar|disser)(?:\s+(?:para|pra)\s+voce)?\b|"
        r"\b(?:voce|laylay|lay)\s+(?:vai|iria|faria)\s+"
        r"(?:criar|abrir|fechar|apagar|tocar|ligar|desligar|mexer)\b|"
        r"\b(?:voce|laylay|lay)\s+mexe\s+(?:no|na|em)\b",
        t,
    ))


def _contexto_conversacional_texto(contexto: Mapping[str, Any] | None) -> str:
    """Extrai apenas pistas recentes; nunca usa o histórico como autorização."""
    dados = dict(contexto or {})
    partes: list[str] = []
    for chave in ("ultima_fala_usuario", "assunto", "foco"):
        valor = str(dados.get(chave) or "").strip()
        if valor:
            partes.append(valor[:500])
    mensagens = dados.get("mensagens")
    if isinstance(mensagens, list):
        for item in mensagens[-6:]:
            if not isinstance(item, Mapping):
                continue
            if str(item.get("role") or "").casefold() != "user":
                continue
            valor = str(item.get("content") or "").strip()
            if valor:
                partes.append(valor[:500])
    return _normalizar(" ".join(partes[-3:]))


def _dominios_mencionados(texto: str) -> list[str]:
    normalizado = _normalizar(texto)
    return [
        dominio
        for dominio, termos in _TERMOS_DOMINIO.items()
        if any(termo in normalizado for termo in termos)
    ]


class MapaHabilidadesRuntime:
    """Catálogo canônico enriquecido por saúde e resultados recentes."""

    def __init__(
        self,
        *,
        saude_getter: Callable[[], Mapping[str, Any]] | None = None,
        operacional_getter: Callable[[], Mapping[str, Any]] | None = None,
        relogio: Callable[[], float] = time.time,
        ttl_indisponivel_s: float = 120.0,
        ttl_observacao_s: float = 300.0,
    ) -> None:
        self._saude_getter = saude_getter
        self._operacional_getter = operacional_getter
        self._relogio = relogio
        self._ttl_indisponivel_s = max(1.0, float(ttl_indisponivel_s))
        self._ttl_observacao_s = max(self._ttl_indisponivel_s, float(ttl_observacao_s))
        self._observacoes: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def conectar_disponibilidade_operacional(
        self, getter: Callable[[], Mapping[str, Any]],
    ) -> None:
        """Conecta tardiamente o retrato vivo sem criar outro catálogo."""
        self._operacional_getter = getter

    def _operacional(self) -> dict[str, Any]:
        if not callable(self._operacional_getter):
            return {}
        try:
            return dict(self._operacional_getter() or {})
        except Exception:
            return {}

    def _saude(self) -> dict[str, Any]:
        if not callable(self._saude_getter):
            return {}
        try:
            return dict(self._saude_getter() or {})
        except Exception:
            return {}

    def registrar_resultado(
        self,
        resultado: Any = None,
        *,
        intent: str = "",
        status: str = "",
        executou: Any = None,
        confirmado: Any = None,
    ) -> None:
        if isinstance(resultado, Mapping):
            intent = intent or str(resultado.get("intent") or resultado.get("acao") or "")
            status = status or str(resultado.get("status") or "")
            executou = resultado.get("executou") if executou is None else executou
            confirmado = resultado.get("confirmado") if confirmado is None else confirmado
        elif resultado is not None:
            intent = intent or str(getattr(resultado, "intent", "") or getattr(resultado, "acao", ""))
            status = status or str(getattr(resultado, "status", "") or "")
            executou = getattr(resultado, "executou", None) if executou is None else executou
            confirmado = getattr(resultado, "confirmado", None) if confirmado is None else confirmado

        nome = str(intent or "").strip().upper()
        if nome not in CAPACIDADES:
            return
        status_norm = _normalizar(status).replace(" ", "_")
        if status_norm in _STATUS_INDISPONIVEIS:
            estado = "indisponivel"
            ttl = self._ttl_indisponivel_s
        elif status_norm in _STATUS_RECUPERADOS or confirmado is True:
            estado = "disponivel"
            ttl = self._ttl_observacao_s
        elif executou is False:
            # Um alvo inexistente ou um pedido inválido não prova que toda a
            # habilidade caiu; marca degradação sem anunciar indisponibilidade.
            estado = "degradado"
            ttl = self._ttl_indisponivel_s
        else:
            return
        agora = self._relogio()
        with self._lock:
            self._observacoes[nome] = {
                "estado": estado,
                "status": status_norm or "sem_status",
                "ts": agora,
                "expira_em": agora + ttl,
            }

    def snapshot(self) -> dict[str, Any]:
        agora = self._relogio()
        saude = self._saude()
        operacional = self._operacional()
        operacional_dominios = dict(operacional.get("dominios") or {})
        operacional_capacidades = dict(operacional.get("capacidades") or {})
        capacidades: dict[str, dict[str, Any]] = {}
        with self._lock:
            expiradas = [
                nome for nome, obs in self._observacoes.items()
                if float(obs.get("expira_em") or 0.0) <= agora
            ]
            for nome in expiradas:
                self._observacoes.pop(nome, None)
            observacoes = {nome: dict(obs) for nome, obs in self._observacoes.items()}

        for nome in sorted(CAPACIDADES):
            dominio_catalogo = str(CAPACIDADES[nome].get("dominio") or "")
            modulo_saude = _MODULO_SAUDE_POR_DOMINIO.get(dominio_catalogo, dominio_catalogo)
            saude_consulta = dict(saude)
            if dominio_catalogo not in saude_consulta and modulo_saude in saude:
                saude_consulta[dominio_catalogo] = saude[modulo_saude]
            registro = consultar_capacidade(nome, saude=saude_consulta)
            observacao = observacoes.get(nome, {})
            if observacao.get("estado") == "indisponivel":
                registro.update(
                    disponivel=False,
                    estado="indisponivel",
                    motivo=f"resultado_recente:{observacao.get('status')}",
                )
            elif observacao.get("estado") == "degradado":
                registro.update(estado="degradado", ultimo_status=observacao.get("status"))
            else:
                registro["estado"] = "disponivel" if registro.get("disponivel") else "indisponivel"
                if observacao:
                    registro["ultimo_status"] = observacao.get("status")
            estado_operacional = dict(
                operacional_capacidades.get(nome)
                or operacional_dominios.get(dominio_catalogo)
                or {}
            )
            if estado_operacional:
                estado_vivo = str(estado_operacional.get("estado") or "").strip()
                if estado_vivo == "indisponivel":
                    registro.update(
                        disponivel=False,
                        estado="indisponivel",
                        motivo=str(
                            estado_operacional.get("motivo")
                            or "precondicao_operacional_ausente"
                        ),
                        ausentes=list(estado_operacional.get("ausentes") or []),
                    )
                elif estado_vivo == "degradado":
                    registro.update(
                        estado="degradado",
                        motivo=str(
                            estado_operacional.get("motivo")
                            or "capacidade_operacional_degradada"
                        ),
                        ausentes=list(estado_operacional.get("ausentes") or []),
                    )
                elif estado_vivo == "disponivel":
                    registro.update(
                        estado="disponivel",
                        disponivel=True,
                        motivo=str(estado_operacional.get("motivo") or "operacional"),
                        ausentes=[],
                    )
                registro["evidencia_operacional_recente"] = bool(
                    estado_operacional.get("evidencia_recente")
                )
            capacidades[nome] = registro

        dominios: dict[str, dict[str, Any]] = {}
        for dominio, descricao in _DESCRICAO_DOMINIO.items():
            itens = [item for item in capacidades.values() if item.get("dominio") == dominio]
            disponiveis = sum(bool(item.get("disponivel")) for item in itens)
            estado_operacional = dict(operacional_dominios.get(dominio) or {})
            estado_calculado = (
                "disponivel" if disponiveis == len(itens)
                else "indisponivel" if not disponiveis else "parcial"
            )
            if not itens and dominio in _DOMINIOS_CONVERSACIONAIS_DISPONIVEIS:
                estado_calculado = "disponivel"
            if estado_operacional.get("estado"):
                estado_calculado = str(estado_operacional.get("estado"))
            dominios[dominio] = {
                "descricao": descricao,
                "total": len(itens),
                "disponiveis": disponiveis,
                "estado": estado_calculado,
                "intents": [item["intent"] for item in itens],
                "motivo": str(estado_operacional.get("motivo") or ""),
                "ausentes": list(estado_operacional.get("ausentes") or []),
                "evidencia_operacional_recente": bool(
                    estado_operacional.get("evidencia_recente")
                ),
            }
        return {"dominios": dominios, "capacidades": capacidades, "observacoes_ativas": len(observacoes)}

    def consultar(self, intent: str) -> dict[str, Any]:
        """Consulta viva de uma capacidade sem expor o restante do catálogo."""
        nome = str(intent or "").strip().upper()
        return dict(self.snapshot().get("capacidades", {}).get(nome) or {
            "intent": nome,
            "dominio": "desconhecido",
            "disponivel": False,
            "estado": "desconhecido",
            "motivo": "capacidade_nao_registrada",
        })

    def evidencia_conversacional(
        self,
        texto: str,
        *,
        turno: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Projeta somente a evidência necessária para a identidade da fala.

        A projeção não expõe intents, dependências ou nomes internos e nunca
        autoriza execução. Ela permite ao contrato distinguir um limite real
        de uma negação falsa de todas as capacidades locais.
        """
        mapa = self.snapshot()
        dominios = dict(mapa.get("dominios") or {})
        disponiveis = tuple(
            nome
            for nome in _DESCRICAO_DOMINIO
            if nome not in {"conversa", "avatar"}
            and str(dict(dominios.get(nome) or {}).get("estado") or "")
            in {"disponivel", "parcial", "degradado"}
        )
        relevantes = tuple(
            nome
            for nome in self.dominios_relevantes(texto, turno=turno)
            if nome in disponiveis
        )
        return {
            "fonte": "catalogo_vivo",
            "dominios_confirmados": list(disponiveis),
            "dominios_relevantes": list(relevantes),
            "possui_capacidades_locais": bool(disponiveis),
            "autoriza_execucao": False,
        }

    def dominios_relevantes(
        self,
        texto: str,
        *,
        turno: Mapping[str, Any] | None = None,
    ) -> tuple[str, ...]:
        normalizado = _normalizar(texto)
        if any(frase in normalizado for frase in _PEDIDO_CAPACIDADES):
            return tuple(_DESCRICAO_DOMINIO)
        encontrados: list[str] = []
        for dominio, termos in _TERMOS_DOMINIO.items():
            if any(termo in normalizado for termo in termos):
                encontrados.append(dominio)
        if (
            re.search(r"\b(?:guardar|guarda|anotar|anota|salvar|salva|registrar|registra)\b", normalizado)
            and re.search(r"\b(?:ideia|ideias|nota|notas|tarefa|tarefas|pensamento|pensamentos)\b", normalizado)
            and "caixa_entrada" not in encontrados
        ):
            encontrados.append("caixa_entrada")
        dados_turno = dict(turno or {})
        for comando in list(dados_turno.get("comandos") or []):
            if not isinstance(comando, Mapping):
                continue
            intent = str(comando.get("intent") or "").upper()
            dominio = str(CAPACIDADES.get(intent, {}).get("dominio") or "")
            if dominio and dominio not in encontrados:
                encontrados.append(dominio)
        return tuple(encontrados[:4] or ("conversa",))

    def parece_consulta_operacional(self, texto: str) -> bool:
        """Reconhece perguntas que pedem dados reais de uma habilidade.

        Perguntar se a Laylay *consegue* fazer algo é conversa sobre capacidade;
        perguntar quais dados existem ou qual é o estado atual é uma consulta.
        """
        normalizado = _normalizar(texto)
        if not normalizado:
            return False
        if _texto_pergunta_capacidade(normalizado) or re.search(
            r"^(?:nao|não)\s+(?:encontra|procura|busca|pesquisa|localiza)\b",
            normalizado,
        ):
            return False
        pede_dados = bool(
            "?" in str(texto or "")
            or re.search(
                r"^(?:o que|oque|quais?|quant[oa]s?|como esta|como ta|qual e|"
                r"mostra|mostre|lista|liste|me fala|me diga|tem algo)\b",
                normalizado,
            )
            or re.search(
                r"^(?:encontra|encontre|acha|ache|procura|procure|busca|busque|"
                r"pesquisa|pesquise|localiza|localize)\b.*\b(?:arquivo|arquivos|"
                r"documento|documentos|codigo|script|imagem|imagens|foto|fotos|projeto)\b",
                normalizado,
            )
        )
        if not pede_dados:
            return False
        return any(
            termo in normalizado
            for termos in _TERMOS_DOMINIO.values()
            for termo in termos
        )

    def responder_pergunta_capacidade(
        self,
        texto: str,
        *,
        turno: Mapping[str, Any] | None = None,
        contexto: Mapping[str, Any] | None = None,
    ) -> str:
        """Responde sobre capacidade real sem executar a ação mencionada."""
        t = _normalizar(texto)
        # "O que você sabe/lembra sobre X?" pede dados da memória, não pergunta
        # se a Laylay possui a habilidade. O runtime de pessoas ou o mapa de
        # recursos deve responder com evidência real.
        if re.search(
            r"\bo que (?:voce|laylay|lay) (?:sabe|lembra) (?:sobre|da|do)\b",
            t,
        ):
            return ""
        if not _texto_pergunta_capacidade(t):
            return ""
        leitura_turno = dict(turno or {})
        # Esta porta explica capacidades. Um pedido que o turno canônico
        # autorizou pertence ao roteador/executor e nunca é consumido aqui.
        if leitura_turno.get("autoriza_execucao") is True:
            return ""
        mapa = self.snapshot()
        dominios = self.dominios_relevantes(t, turno=leitura_turno)
        disponivel = any(
            str((mapa.get("dominios") or {}).get(dominio, {}).get("estado") or "")
            in {"disponivel", "parcial", "degradado"}
            for dominio in dominios
        )
        if not disponivel:
            return "Essa habilidade não está disponível nesta instalação agora."
        pergunta_geral = any(frase in t for frase in _PEDIDO_CAPACIDADES)
        if pergunta_geral:
            dominios_vivos = dict(mapa.get("dominios") or {})
            ordem = tuple(_ROTULO_CAPACIDADE_NATURAL)
            contexto_texto = _contexto_conversacional_texto(contexto)
            relacionados = [
                dominio
                for dominio in _dominios_mencionados(contexto_texto)
                if dominio in ordem
                and str(dominios_vivos.get(dominio, {}).get("estado") or "")
                in {"disponivel", "parcial", "degradado"}
            ]
            ordem = tuple(dict.fromkeys([*relacionados, *ordem]))
            itens = [
                _ROTULO_CAPACIDADE_NATURAL[dominio]
                for dominio in ordem
                if str(dominios_vivos.get(dominio, {}).get("estado") or "")
                in {"disponivel", "parcial", "degradado"}
            ]
            if not itens:
                return "Agora minhas habilidades práticas estão indisponíveis, mas ainda consigo conversar com você."
            # Uma pergunta geral pede orientação, não a leitura do catálogo
            # inteiro. Mantemos os domínios ligados ao papo na frente e damos
            # uma amostra curta das demais capacidades.
            rotulos_relacionados = {
                _ROTULO_CAPACIDADE_NATURAL[item]
                for item in relacionados[:2]
            }
            itens_complementares = [
                item for item in itens if item not in rotulos_relacionados
            ]
            principais = itens_complementares[:4] if relacionados else itens[:5]
            if len(principais) == 1:
                lista = principais[0]
            else:
                lista = ", ".join(principais[:-1]) + " e " + principais[-1]
            complemento = (
                " Tenho outras habilidades menores também. Se você perguntar por uma, "
                "eu confiro como ela está agora."
                if len(itens) > len(principais)
                else ""
            )
            abertura = (
                "Pelo assunto que a gente estava falando, eu começaria por "
                f"{', '.join(_ROTULO_CAPACIDADE_NATURAL[item] for item in relacionados[:2])}. "
                if relacionados
                else ""
            )
            return (
                f"{abertura}No geral, consigo {lista}."
                f"{complemento} Eu só mexo de verdade quando você pede. Perguntar não executa nada."
            )
        if "arquivos" in dominios and re.search(
            r"\b(?:cri|faz|mont)\w*\b.*\b(?:arquivo|pasta)\b|"
            r"\b(?:arquivo|pasta)\b.*\b(?:cri|faz|mont)\w*\b",
            t,
        ):
            return (
                "Consigo, sim. Se você me pedir de verdade e disser o nome, eu crio o arquivo "
                "ou a pasta. Como agora você só perguntou, não fiz nada."
            )
        if "arquivos" in dominios and re.search(r"\b(?:apag|exclu|delet|remov)\w*\b", t):
            return "Consigo. Quando você pedir de verdade, confirmo o alvo e envio o arquivo ou a pasta para a lixeira."
        if "arquivos" in dominios and re.search(r"\b(?:encontr|procur|busc|localiz|pesquis)\w*\b", t):
            return (
                "Consigo pesquisar localmente por nome, pasta, conteúdo, tipo, significado e data. "
                "O índice fica só na memória, não envia seus arquivos para a internet e a busca não altera nada. "
                "Depois você pode pedir naturalmente para abrir um dos resultados."
            )
        if "arquivos" in dominios and re.search(
            r"\b(?:renome|mud|troc|alter)\w*\b.*\b(?:nome|tipo|extensao|formato)\b|"
            r"\b(?:extensao|formato)\b.*\b(?:renome|mud|troc|alter)\w*\b",
            t,
        ):
            return (
                "Consigo renomear um arquivo recente e trocar extensões textuais conhecidas, "
                "como .txt por .md. Isso muda o nome e o tipo indicado pela extensão, mas não "
                "converte o conteúdo. O executor confere o caminho de origem e o novo nome antes "
                "de eu confirmar o resultado."
            )
        if ("sistema" in dominios or "navegador" in dominios) and re.search(r"\b(?:fech|encerr)\w*\b", t):
            return "Consigo. Posso fechar o programa, navegador ou aba quando você fizer o pedido direto."
        if "navegador" in dominios:
            return (
                "Consigo consultar a aba ativa e as abas abertas, resumir a página atual, abrir sites, "
                "pesquisar, controlar mídia e interagir com controles de página que a habilidade "
                "reconheça. A leitura do "
                "navegador não autoriza uma ação por conta própria, e eu não exponho um comando "
                "arbitrário de página; cada ação real continua passando pelo porteiro e pelo executor."
            )
        if "sistema" in dominios and re.search(
            r"\b(?:organiz|posicion|divid|esquerda|direita|janela)\w*\b", t,
        ):
            return (
                "Consigo organizar as janelas visíveis automaticamente. Nesse modo, priorizo o "
                "programa em foco e combino áudio ativo, uso recente, frequência de uso e tempo "
                "aberto para escolher o secundário. Também posso colocar um aplicativo específico "
                "na esquerda ou na direita. Eu movo somente os lados pedidos e releio a geometria "
                "final antes de dizer que deu certo."
            )
        if "sistema" in dominios:
            return (
                "Consigo mexer em partes do seu computador quando você pede: abrir e fechar "
                "programas, organizar janelas e ajustar o volume, por exemplo. Eu não ajo por "
                "conta própria e só confirmo o que o computador realmente mostrou."
            )
        if "visao" in dominios:
            return (
                "Consigo analisar o item visível no jogo. Eu uso o quadro atual, tento ler nome, "
                "atributos e requisitos, busco evidência externa quando houver identificação "
                "confiável e cruzo tudo com a build e o inventário que conheço daquela sessão. "
                "A captura é transitória, não fica persistida e observar o jogo não autoriza uma "
                "nova análise por conta própria. "
                "Para avaliar um item específico, mantenha o tooltip aberto e o mouse sobre ele; "
                "se a imagem ou a fonte não forem suficientes, eu explico o limite em vez de inventar."
            )
        if "iot" in dominios:
            return "Consigo consultar e controlar os dispositivos inteligentes que estiverem configurados e online."
        if "musica" in dominios:
            return (
                "Consigo buscar e controlar músicas, além de criar, listar, tocar e editar suas playlists. "
                "Também monto curadorias minhas usando apenas suas playlists e o histórico musical "
                "confirmado. Posso mostrar essas seleções e copiar uma faixa para uma playlist sua "
                "quando você pedir; não invento músicas nem reproduzo ou copio algo sozinha."
            )
        if "agenda" in dominios:
            return (
                "Consigo criar, listar e cancelar lembretes e ações agendadas. Se faltar o horário, "
                "eu mantenho uma pendência temporária e você pode completar naturalmente, por exemplo "
                "com '14:30' ou 'em 15 minutos'. Só digo que ficou marcado depois de confirmar a "
                "persistência local; a entrega passa pela central de notificações."
            )
        if "email" in dominios:
            return (
                "Consigo consultar emails e reunir avisos de email, agenda, lembretes e alertas internos. "
                "A central prioriza o importante, agrupa repetições e aprende quais categorias devem "
                "interromper, entrar no resumo ou ficar em silêncio."
            )
        if "area_transferencia" in dominios:
            return (
                "Consigo observar localmente quando você copia um conteúdo relevante. Se for uma mensagem de erro, "
                "posso oferecer ajuda e, quando você aceitar, pesquisar internamente, analisar e resumir a causa sem "
                "abrir uma aba. Também consigo ler, resumir, corrigir, explicar e traduzir texto copiado, além de abrir "
                "ou pesquisar links. Não guardo o texto automaticamente e só substituo o conteúdo com confirmação."
            )
        if "caixa_entrada" in dominios:
            return (
                "Consigo guardar e classificar ideias, tarefas, pensamentos, links e notas na sua caixa de entrada. "
                "Também consigo resumir uma discussão, separando sua ideia das minhas sugestões, listar o que foi "
                "anotado e transformar uma nota em lembrete; alterações pedem confirmação."
            )
        if "pessoas" in dominios:
            return (
                "Consigo lembrar pessoas e relações que você me contar explicitamente, consultar fatos "
                "confirmados sobre elas e corrigir uma relação antiga sem manter as duas como verdade. "
                "Esses perfis ficam locais, não são enviados para fora e eu só os esqueço após sua confirmação."
            )
        if "memoria" in dominios:
            return (
                "Consigo consultar o que aprendi sobre você na memória persistente local. Eu separo "
                "o que você confirmou diretamente de padrões que só amadureceram com evidências e "
                "de registros antigos; hipóteses fracas, contraditas ou não verificadas não viram "
                "fatos na resposta. O contexto desta conversa é temporário e não é automaticamente "
                "uma memória durável. Consultar essa memória é somente leitura e não autoriza ações."
            )
        if "cooperacao" in dominios:
            return (
                "Consigo combinar habilidades por um único plano. No primeiro fluxo ativo, uso uma "
                "referência temporária ao texto copiado para criar um arquivo, sem guardar o texto no "
                "plano, e só digo que terminou depois de reler o arquivo. Cada etapa tem dependências, "
                "orçamento de tempo, cancelamento, evidência e uma política segura para falhas parciais. "
                "Sobrescrita pede confirmação."
            )
        if "avatar" in dominios:
            return (
                "Tenho um avatar visual com emoções e animações. Posso ajudar a imaginar skins e designs; "
                "uma mudança nos PNGs ou no código só conta como feita depois que o executor confirmar."
            )
        if "conversa" in dominios:
            return (
                "Consigo conversar, explicar e raciocinar com você usando o modelo de linguagem "
                "disponível. Também mantenho o contexto da "
                "conversa separado das lembranças duráveis: conversar comigo não salva tudo nem "
                "autoriza uma ação no computador."
            )
        return "Consigo, desde que essa habilidade esteja configurada e você faça o pedido de execução diretamente."

    def contexto_para_prompt(
        self,
        texto: str,
        *,
        turno: Mapping[str, Any] | None = None,
    ) -> str:
        mapa = self.snapshot()
        dominios = dict(mapa.get("dominios") or {})
        relevantes = self.dominios_relevantes(texto, turno=turno)
        linhas = [
            "--- HABILIDADES REAIS RELEVANTES ---",
            "Este mapa informa capacidade, não autoriza ações. Só declare execução após o roteador/executor confirmar.",
        ]
        for dominio in relevantes:
            registro = dict(dominios.get(dominio) or {})
            estado = str(registro.get("estado") or "indisponivel")
            linhas.append(f"- {dominio} [{estado}]: {registro.get('descricao') or ''}.")
        indisponiveis = [
            item for item in mapa.get("capacidades", {}).values()
            if item.get("dominio") in relevantes and not item.get("disponivel")
        ]
        if indisponiveis:
            nomes = ", ".join(str(item.get("intent")) for item in indisponiveis[:8])
            linhas.append(f"Indisponíveis agora: {nomes}. Não prometa que foram executadas.")
        linhas.append(
            "Pedidos práticos continuam sendo decididos pelo porteiro e pelos roteadores; não invente comandos, resultados ou acesso externo."
        )
        return "\n".join(linhas)

    def diagnostico(self) -> dict[str, Any]:
        mapa = self.snapshot()
        dominios = dict(mapa.get("dominios") or {})
        return {
            "catalogadas": len(mapa.get("capacidades") or {}),
            "dominios": len(dominios),
            "disponiveis": sum(
                bool(item.get("disponivel")) for item in mapa.get("capacidades", {}).values()
            ),
            "indisponiveis": sum(
                not bool(item.get("disponivel")) for item in mapa.get("capacidades", {}).values()
            ),
            "parciais": sorted(nome for nome, item in dominios.items() if item.get("estado") == "parcial"),
            "observacoes_ativas": int(mapa.get("observacoes_ativas") or 0),
            "autoriza_execucao": False,
        }


def criar_mapa_habilidades_runtime(**kwargs: Any) -> MapaHabilidadesRuntime:
    return MapaHabilidadesRuntime(**kwargs)
