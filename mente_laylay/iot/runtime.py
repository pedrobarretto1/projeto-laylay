"""Integração do subsistema IoT com intenção, memória e fala da Laylay."""

from __future__ import annotations

import re
import time
from typing import Any, Callable, Dict

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.cognicao.evidencia_operacional import (
    bloqueia_controle_iot_por_modalidade,
    detectar_consulta_lista_iot,
)
from mente_laylay.iot.controlador import ControladorIoT
from mente_laylay.iot.configuracao import ler_variavel_ambiente
from mente_laylay.iot.persistencia import PersistenciaIoT
from mente_laylay.iot.protocolos.simulado import ProtocoloSimulado
from mente_laylay.iot.protocolos.tuya import ProtocoloTuya
from mente_laylay.iot.registro import criar_dispositivo_lampada, criar_dispositivo_ventilador
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao
from mente_laylay.cognicao.identidade_conversacional import remover_vocativo_laylay


class RuntimeIoT:
    """Mantém IoT ligado à mesma memória sem expor detalhes de protocolo."""

    def __init__(
        self,
        *,
        memoria_sqlite: Any,
        falar: Callable[[str, str, int], Any],
        estado_mental_getter: Callable[[], Dict[str, Any]],
        definir_emocao: Callable[[str, int, str], Any] | None = None,
        emitir_fala: bool = True,
        modo: str | None = None,
        resolver_cor: Callable[[str], Any] | None = None,
        log: Callable[..., Any] = print,
    ) -> None:
        self.falar = falar
        self.estado_mental_getter = estado_mental_getter
        self.definir_emocao = definir_emocao
        self.emitir_fala = bool(emitir_fala)
        self.resolver_cor = resolver_cor
        self._cache_cores_resolvidas: dict[str, tuple[int, int, int]] = {}
        self.log = log
        self.persistencia = PersistenciaIoT(memoria_sqlite)

        modo_solicitado = str(modo or ler_variavel_ambiente("LAYLAY_IOT_MODO", "simulado")).strip().lower()
        autorizado = ler_variavel_ambiente("IOT_CONTROLE_FISICO_AUTORIZADO").strip().upper() == "SIM"
        self.modo = "tuya" if modo_solicitado == "tuya" and autorizado else "simulado"
        if modo_solicitado == "tuya" and not autorizado:
            self.log("🏠 [IOT:SEGURANCA] Tuya solicitado sem autorização explícita; usando simulador.")

        dispositivos = (
            criar_dispositivo_ventilador(protocolo=self.modo),
            criar_dispositivo_lampada(protocolo=self.modo),
        )
        self.persistencia.sincronizar(dispositivos)
        self.registro = self.persistencia.carregar_registro()
        self.simulador = ProtocoloSimulado()
        protocolos = []
        for item in self.registro.listar():
            if item.protocolo == "simulado":
                self.simulador.configurar(item.nome, estado=False, disponivel=True)
        if self.modo == "simulado":
            protocolos.append(self.simulador)
        else:
            protocolos.append(ProtocoloTuya())
        self.controlador = ControladorIoT(
            self.registro,
            protocolos,
            persistencia=self.persistencia,
        )
        nomes = ",".join(item.nome for item in dispositivos)
        self.log(f"🏠 [IOT:INICIO] modo={self.modo} dispositivos={nomes}")
        catalogados = self.registro.listar()
        self.log(
            "🧠 [IOT:MENTE] consulta_lista=prioritaria dispositivos="
            + ",".join(item.nome for item in catalogados)
        )

    def _aliases(self) -> list[tuple[str, str]]:
        aliases: list[tuple[str, str]] = []
        for dispositivo in self.registro.listar():
            for alias in {dispositivo.nome, dispositivo.nome_amigavel, *dispositivo.aliases}:
                alias_norm = normalizar_texto(alias)
                if alias_norm:
                    aliases.append((alias_norm, dispositivo.nome))
        return sorted(aliases, key=lambda item: len(item[0]), reverse=True)

    def retrato_para_mente(self, texto: str = "") -> dict[str, Any]:
        """Expõe o catálogo IoT sem credenciais, chaves ou configuração Tuya."""
        consulta = detectar_consulta_lista_iot(texto) or {}
        params = consulta.get("params") if isinstance(consulta, dict) else {}
        ambiente = str((params or {}).get("ambiente") or "").strip()
        dispositivos = self.registro.listar(ambiente)
        return {
            "dispositivos": [
                {
                    "nome": item.nome,
                    "nome_amigavel": item.nome_amigavel,
                    "tipo": item.tipo,
                    "ambiente": item.ambiente,
                    "capacidades": sorted(item.capacidades),
                }
                for item in dispositivos
            ],
            "total_dispositivos": len(dispositivos),
            "parametros_consulta": {"ambiente": ambiente},
        }

    @staticmethod
    def _nome_com_artigo(nome: str) -> str:
        nome = re.sub(r"\s+", " ", str(nome or "").strip())
        if not nome or re.match(
            r"^(?:o|a|os|as|um|uma|esse|essa|este|esta|aquele|aquela)\s+",
            nome,
            re.IGNORECASE,
        ):
            return nome
        primeiro = normalizar_texto(nome).split(" ", 1)[0]
        artigo = "a" if primeiro in {"lampada", "luz", "tomada"} else "o"
        return f"{artigo} {nome}"

    @staticmethod
    def _nome_com_de(nome: str) -> str:
        trocas = {"a ": "da ", "o ": "do ", "as ": "das ", "os ": "dos "}
        nome_norm = str(nome or "").strip()
        for inicio, contracao in trocas.items():
            if nome_norm.casefold().startswith(inicio):
                return contracao + nome_norm[len(inicio):]
        if nome_norm.casefold().startswith("esse "):
            return "desse " + nome_norm[5:]
        if nome_norm.casefold().startswith("essa "):
            return "dessa " + nome_norm[5:]
        return f"de {nome_norm}"

    @staticmethod
    def _nome_com_em(nome: str) -> str:
        trocas = {"a ": "na ", "o ": "no ", "as ": "nas ", "os ": "nos "}
        nome_norm = str(nome or "").strip()
        for inicio, contracao in trocas.items():
            if nome_norm.casefold().startswith(inicio):
                return contracao + nome_norm[len(inicio):]
        return f"em {nome_norm}"

    @staticmethod
    def _aplicar_tonalidade_rgb(rgb: Any, tonalidade: str) -> tuple[int, int, int]:
        valores = tuple(max(0, min(255, int(item))) for item in rgb)
        if len(valores) != 3:
            raise ValueError("RGB inválido para tonalidade")
        tom = str(tonalidade or "").casefold()
        if tom == "escuro":
            return tuple(round(item * 0.42) for item in valores)
        # "Claro" deve preservar a identidade e a saturação da cor. Uma mistura
        # maior fica reservada ao pastel, cuja intenção é realmente suavizá-la.
        mistura_branco = 0.65 if tom == "pastel" else 0.25 if tom == "claro" else 0.0
        if mistura_branco:
            return tuple(round(item + (255 - item) * mistura_branco) for item in valores)
        return valores

    @staticmethod
    def _validar_rgb(rgb: Any) -> tuple[int, int, int] | None:
        if not isinstance(rgb, (tuple, list)) or len(rgb) != 3:
            return None
        try:
            valores = tuple(int(item) for item in rgb)
        except (TypeError, ValueError):
            return None
        return valores if all(0 <= item <= 255 for item in valores) else None

    @staticmethod
    def _misturar_cores(cores: list[tuple[int, int, int]]) -> tuple[int, int, int]:
        quantidade = len(cores)
        return tuple(round(sum(cor[canal] for cor in cores) / quantidade) for canal in range(3))

    def _pesquisar_cor(self, nome: str) -> tuple[int, int, int] | None:
        chave = normalizar_texto(nome)
        if not chave or self.resolver_cor is None:
            return None
        if chave in self._cache_cores_resolvidas:
            return self._cache_cores_resolvidas[chave]
        try:
            resolvida = self.resolver_cor(nome)
        except Exception as exc:
            self.log(f"⚠️ [IOT:COR] não foi possível resolver '{nome}': {exc}")
            return None
        rgb_bruto = resolvida.get("rgb") if isinstance(resolvida, dict) else resolvida
        rgb = self._validar_rgb(rgb_bruto)
        if rgb:
            self._cache_cores_resolvidas[chave] = rgb
        return rgb

    def _extrair_nome_cor_pedido(self, texto: str, alvo: str) -> tuple[str, bool]:
        """Extrai o trecho de cor e informa se o dispositivo foi citado explicitamente."""
        t = normalizar_texto(texto)
        candidatos = [alias for alias, nome in self._aliases() if nome == alvo]
        for alias in candidatos:
            encontrado = re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", t)
            if encontrado:
                restante = t[encontrado.end():]
                restante = re.sub(r"^\s*(?:na|no|em|com|para|pra|de)?\s*(?:a\s+)?cor(?:\s+de)?\s+", "", restante)
                restante = re.sub(r"^\s*(?:em|na|no|de|cor)\s+", "", restante)
                return restante.strip(), True
        encontrado_cor = re.search(r"\bcor(?:\s+de)?\s+(.+)$", t)
        if encontrado_cor:
            return encontrado_cor.group(1).strip(), True
        restante = re.sub(
            r"^(?:pode\s+)?(?:deixa|deixe|deixar|coloca|coloque|colocar|bota|bote|botar|poe|muda|mude|mudar|ajusta|ajuste|ajustar|define|defina|definir|torna|torne|tornar|quero)\s+",
            "",
            t,
        )
        restante = re.sub(r"^(?:ela|ele|isso)\s+(?:em\s+)?", "", restante)
        return restante.strip(), False

    @staticmethod
    def _cor_feminina(cor: str) -> str:
        flexoes = {
            "vermelho": "vermelha", "amarelo": "amarela", "roxo": "roxa",
            "ciano": "ciana", "dourado": "dourada", "claro": "clara",
            "escuro": "escura",
        }
        return " ".join(flexoes.get(parte.casefold(), parte) for parte in str(cor or "").split())

    @staticmethod
    def _parametros_anteriores(estado: Dict[str, Any], alvo: str) -> Dict[str, Any]:
        por_dispositivo = estado.get("parametros_iot_por_dispositivo")
        por_dispositivo = por_dispositivo if isinstance(por_dispositivo, dict) else {}
        anteriores = por_dispositivo.get(alvo)
        if not isinstance(anteriores, dict):
            anteriores = estado.get("ultimos_parametros_iot")
        return dict(anteriores) if isinstance(anteriores, dict) else {}

    @staticmethod
    def _alvo_iot_recente(estado: Dict[str, Any], ttl_s: float = 300.0) -> str:
        intent = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").upper().strip()
        habilidade = str(estado.get("ultima_habilidade") or "").lower().strip()
        if not intent.startswith("IOT_") and habilidade != "iot":
            return ""
        try:
            ts = max(
                float(estado.get("ts") or 0.0),
                float(estado.get("foco_operacional_ts") or 0.0),
            )
        except Exception:
            ts = 0.0
        if ts and time.time() - ts > max(1.0, float(ttl_s)):
            return ""
        return str(
            estado.get("ultimo_dispositivo_iot")
            or (estado.get("ultima_acao_params") or {}).get("alvo")
            or ""
        ).strip()

    def _resolver_alvo_texto(self, texto: str, estado: Dict[str, Any]) -> str:
        t = normalizar_texto(texto)
        for alias, nome in self._aliases():
            if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", t):
                return nome

        if re.search(r"\b(ele|ela|dele|dela|isso|esse|essa|dispositivo)\b", t):
            return str(
                estado.get("ultimo_dispositivo_iot")
                or (
                    (estado.get("ultima_acao_params") or {}).get("alvo")
                    if str(estado.get("ultima_acao_intent") or "").upper().startswith("IOT_")
                    else ""
                )
                or ""
            ).strip()

        comando_eliptico = re.fullmatch(
            r"(?:pode\s+)?(?:liga|ligar|ligue|acende|desliga|desligar|desligue|apaga|apagar|alterna|alternar)"
            r"(?:\s+(?:agora|ja|novamente|de\s+novo|por\s+favor))?",
            t,
        )
        if comando_eliptico:
            return self._alvo_iot_recente(estado)

        encontrado = re.search(
            r"\b(?:liga|ligar|ligue|acende|desliga|desligar|desligue|apaga|apagar|alterna|alternar)\s+"
            r"(?:o|a|os|as|um|uma)?\s*(.+)$",
            t,
        )
        if encontrado:
            return re.sub(r"\s+(?:agora|por favor|pra mim|para mim)$", "", encontrado.group(1)).strip()
        return ""

    def detectar(self, texto: str, estado_mental: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
        texto_operacional = remover_vocativo_laylay(texto)
        consulta_lista = detectar_consulta_lista_iot(texto_operacional)
        if consulta_lista:
            return consulta_lista
        texto_bruto = str(texto_operacional or "").casefold().strip()
        t = normalizar_texto(texto_operacional)
        if not t:
            return None
        if bloqueia_controle_iot_por_modalidade(texto_operacional):
            return None
        # Horários pertencem à agenda. O IoT só deve receber a parte da ação
        # depois que o orquestrador separar "desliga a luz" de "às 23:27".
        # Sem esta barreira, o primeiro número era confundido com brilho.
        if re.search(
            r"\b(?:às|as|a)\s+\d{1,2}\s*(?::|h|\s)\s*\d{2}\s*$",
            texto_bruto,
        ):
            return None
        estado = estado_mental if isinstance(estado_mental, dict) else self.estado_mental_getter() or {}

        tonalidade = ""
        if re.search(r"\bpastel\b", t):
            tonalidade = "pastel"
        elif re.search(r"\bclar[oa]\b", t):
            tonalidade = "claro"
        elif re.search(r"\bescur[oa]\b", t):
            tonalidade = "escuro"

        alvo_parametro = self._resolver_alvo_texto(t, estado)
        # Consultar estado é leitura e tem precedência sobre qualquer palavra
        # que também possa parecer uma descrição de cor. Em particular,
        # "como está a lâmpada?" nunca deve mandar "está" ao resolvedor livre
        # de cores nem herdar um ajuste cromático anterior.
        foco_iot_recente = bool(estado.get("ultimo_dispositivo_iot"))
        pergunta_estado = bool(
            re.search(r"\b(?:esta|ta|ficou|continua)\s+(?:ligad[oa]|desligad[oa])\b", t)
            or (
                re.search(
                    r"\b(?:como\s+(?:(?:ele|ela|isso|esse|essa)\s+)?"
                    r"(?:esta|ta|ficou|continua)|"
                    r"qual(?:\s+e)?\s+(?:o\s+)?(?:status|estado)|"
                    r"ver|ve|consulta|status|estado)\b",
                    t,
                )
                and (
                    re.search(
                        r"\b(?:dispositivo|aparelho|tomada|ventilador|lampada|luz|iot)\b",
                        t,
                    )
                    or foco_iot_recente
                    and re.search(r"\b(?:ele|ela|dele|dela|disso)\b", t)
                )
            )
        )
        if pergunta_estado and alvo_parametro:
            return {
                "intent": "IOT_STATUS",
                "params": {"acao": "status", "alvo": alvo_parametro},
            }
        # Desligar/apagar é uma ação completa e vence qualquer resíduo textual.
        # Assim, vocativos, ditado imperfeito ou adjetivos posteriores nunca
        # transformam "desliga a luz" em uma pesquisa de cor.
        pedido_desligar = bool(re.search(
            r"\b(?:desliga|desligar|desligue|apaga|apagar)\b",
            t,
        ))
        negou_desligar = bool(re.search(
            r"\bnao\s+(?:desliga|desligar|desligue|apaga|apagar)\b",
            t,
        ))
        alvo_e_iot_explicito = bool(re.search(
            r"\b(?:luz|lampada|dispositivo|aparelho|tomada|ventilador|iot)\b",
            t,
        )) or self.registro.resolver(alvo_parametro) is not None
        if (
            alvo_parametro
            and pedido_desligar
            and not negou_desligar
            and alvo_e_iot_explicito
        ):
            return {
                "intent": "IOT_CONTROL",
                "params": {"acao": "desligar", "alvo": alvo_parametro},
            }
        valor_eliptico = re.fullmatch(
            r"(?:pode\s+)?(?:coloca|coloque|deixa|deixe|bota|bote|poe|põe|ajusta|ajuste|define|defina)"
            r"(?:\s+(?:ela|ele|isso))?\s+(?:em|para|pra)\s+(\d{1,3})(?:\s*(?:%|por cento))?",
            t,
        )
        if not alvo_parametro and valor_eliptico:
            alvo_parametro = self._alvo_iot_recente(estado)
        if not alvo_parametro and re.search(
            r"\b(brilho|cor|clar[oa]|escur[oa]|pastel|branc[oa]|pret[oa]|cinza|marrom|vermelh[oa]|verde|azul|amarel[oa]|rox[oa]|rosa|laranja|cian[oa]|violeta|lilas|turquesa|dourad[oa]|magenta|coral)\b",
            t,
        ):
            alvo_parametro = self._alvo_iot_recente(estado)
        pedido_parametro = bool(re.search(
            r"\b(?:deixa|deixe|deixar|coloca|coloque|colocar|bota|bote|botar|poe|muda|mude|mudar|ajusta|ajuste|ajustar|define|defina|definir|torna|torne|tornar|quero)\b",
            t,
        ))

        ajuste_brilho_relativo = ""
        if re.search(r"\b(?:aumenta|aumentar|aumente|sobe|subir|suba|eleva|elevar|eleve)\b", t):
            ajuste_brilho_relativo = "aumentar"
        elif re.search(r"\b(?:diminui|diminuir|diminua|abaixa|abaixar|abaixe|reduz|reduzir|reduza|baixa|baixar|baixe)\b", t):
            ajuste_brilho_relativo = "diminuir"
        # Um número ligado explicitamente ao brilho representa o valor final,
        # mesmo quando a frase também usa "aumenta" ou "diminui".
        # Ex.: "aumenta o brilho para 100" significa 100, não +20.
        brilho_explicito = re.search(
            r"\b(?:brilho(?:\s+(?:da|do)\s+(?:lampada|luz))?[^\d]{0,20}|(?:lampada|luz)[^\d]{0,20})"
            r"(\d{1,3})(?:\s*(?:%|por cento))?\b",
            t,
        )
        if brilho_explicito and alvo_parametro:
            valor = int(brilho_explicito.group(1))
            if 1 <= valor <= 100:
                return {
                    "intent": "IOT_CONTROL",
                    "params": {"acao": "ajustar_brilho", "alvo": alvo_parametro, "valor": valor},
                }

        if valor_eliptico and alvo_parametro:
            valor = int(valor_eliptico.group(1))
            propriedade_anterior = str(estado.get("ultima_propriedade_iot") or "").strip()
            parametros_anteriores = self._parametros_anteriores(estado, alvo_parametro)
            contexto_brilho = propriedade_anterior == "ajustar_brilho" or "brilho" in parametros_anteriores
            if contexto_brilho and 1 <= valor <= 100:
                return {
                    "intent": "IOT_CONTROL",
                    "params": {
                        "acao": "ajustar_brilho", "alvo": alvo_parametro, "valor": valor,
                        "referencia_contextual": True,
                    },
                }

        if alvo_parametro and re.search(r"\bbrilho\b", t) and ajuste_brilho_relativo:
            anteriores = self._parametros_anteriores(estado, alvo_parametro)
            try:
                brilho_atual = int(anteriores.get("brilho", 70))
            except (TypeError, ValueError):
                brilho_atual = 70
            passo = 10 if re.search(r"\b(?:um pouco|pouquinho)\b", t) else 30 if re.search(r"\b(?:muito|bastante)\b", t) else 20
            delta = passo if ajuste_brilho_relativo == "aumentar" else -passo
            return {
                "intent": "IOT_CONTROL",
                "params": {
                    "acao": "ajustar_brilho", "alvo": alvo_parametro,
                    "valor": max(1, min(100, brilho_atual + delta)),
                    "ajuste_relativo": ajuste_brilho_relativo,
                    "referencia_contextual": True,
                },
            }

        if alvo_parametro and pedido_parametro and re.search(r"\bpret[oa]\b", t):
            dispositivo_cor = self.registro.resolver(alvo_parametro)
            if dispositivo_cor is not None and str(dispositivo_cor.tipo).startswith("lampada"):
                nome_cor_fala = self._nome_com_artigo(dispositivo_cor.nome_amigavel)
                return {
                    "intent": "SUGGEST_ACTION",
                    "params": {
                        "acao_sugerida": {
                            "intent": "IOT_CONTROL",
                            "params": {"acao": "desligar", "alvo": alvo_parametro},
                        },
                        "descricao": f"apagar {nome_cor_fala} para representar preto",
                        "fala": (
                            "Uma lâmpada não consegue emitir preto, porque preto é ausência de luz. "
                            f"Quer que eu apague {nome_cor_fala}?"
                        ),
                        "origem": "cor_iot_sem_emissao",
                    },
                }

        brancos = {
            "branco quente": (("branco quente", "branca quente"), 10),
            "branco neutro": (("branco neutro", "branca neutra"), 50),
            "branco frio": (("branco frio", "branca fria"), 100),
        }
        for nome_cor, (variantes, temperatura) in brancos.items():
            padrao_cor = "|".join(re.escape(item) for item in variantes)
            resposta_curta = bool(re.fullmatch(rf"(?:em\s+)?(?:{padrao_cor})", t))
            if re.search(rf"\b(?:{padrao_cor})\b", t) and alvo_parametro and (pedido_parametro or resposta_curta):
                return {
                    "intent": "IOT_CONTROL",
                    "params": {
                        "acao": "ajustar_branco", "alvo": alvo_parametro,
                        "cor": nome_cor, "temperatura": temperatura, "brilho": 70,
                    },
                }

        if alvo_parametro and pedido_parametro and re.search(r"\bbranc[oa]\b", t):
            return {
                "intent": "IOT_CONTROL",
                "params": {
                    "acao": "ajustar_branco", "alvo": alvo_parametro,
                    "cor": "branco neutro", "temperatura": 50, "brilho": 70,
                },
            }

        cores = {
            "vermelho": (("vermelho", "vermelha"), (255, 0, 0)),
            "verde": (("verde",), (0, 255, 0)),
            "azul": (("azul",), (0, 0, 255)),
            "amarelo": (("amarelo", "amarela"), (255, 255, 0)),
            "roxo": (("roxo", "roxa"), (128, 0, 255)),
            "rosa": (("rosa",), (255, 80, 160)),
            "laranja": (("laranja",), (255, 128, 0)),
            "ciano": (("ciano", "ciana"), (0, 255, 255)),
            "violeta": (("violeta",), (138, 43, 226)),
            "lilás": (("lilas",), (200, 162, 200)),
            "turquesa": (("turquesa",), (64, 224, 208)),
            "dourado": (("dourado", "dourada"), (255, 180, 0)),
            "magenta": (("magenta",), (255, 0, 255)),
            "coral": (("coral",), (255, 127, 80)),
            "marrom": (("marrom",), (150, 75, 0)),
            "cinza": (("cinza",), (128, 128, 128)),
        }

        # Nomes compostos precisam ser avaliados inteiros. Antes, "azul ciano"
        # parava em "azul" por ser a primeira chave encontrada no dicionário.
        nome_pedido, alvo_explicito = self._extrair_nome_cor_pedido(t, alvo_parametro)
        nome_sem_tom = re.sub(r"\b(?:claro|clara|escuro|escura|pastel)\b", "", nome_pedido)
        nome_sem_tom = re.sub(r"\s+", " ", nome_sem_tom).strip(" .,!?;:")
        encontradas: list[tuple[int, str, tuple[int, int, int]]] = []
        for nome_cor, (variantes, rgb) in cores.items():
            ocorrencias = [
                re.search(rf"(?<!\w){re.escape(variante)}(?!\w)", nome_sem_tom)
                for variante in variantes
            ]
            ocorrencia = next((item for item in ocorrencias if item), None)
            if ocorrencia:
                encontradas.append((ocorrencia.start(), nome_cor, rgb))
        encontradas.sort(key=lambda item: item[0])

        if alvo_parametro and (pedido_parametro or bool(re.fullmatch(r"(?:em\s+)?[\w\s-]+", t))):
            if len(encontradas) >= 2:
                nomes = [item[1] for item in encontradas]
                rgb_misto = self._misturar_cores([item[2] for item in encontradas])
                rgb_final = self._aplicar_tonalidade_rgb(rgb_misto, tonalidade)
                cor_final = f"{' '.join(nomes)} {tonalidade}".strip()
                return {
                    "intent": "IOT_CONTROL",
                    "params": {
                        "acao": "ajustar_cor", "alvo": alvo_parametro,
                        "cor": cor_final, "rgb": rgb_final,
                        "cor_composta": True,
                        **({"tonalidade": tonalidade} if tonalidade else {}),
                    },
                }

            palavras_ignoradas = {"um", "uma", "o", "a", "por", "favor", "agora"}
            palavras_cor = [p for p in nome_sem_tom.split() if p not in palavras_ignoradas]
            tem_descricao_livre = len(palavras_cor) > 1 or (not encontradas and bool(palavras_cor))
            pesquisa_autorizada = alvo_explicito or bool(encontradas)
            if tem_descricao_livre and pesquisa_autorizada:
                nome_livre = " ".join(palavras_cor)
                rgb_pesquisado = self._pesquisar_cor(nome_livre)
                if rgb_pesquisado:
                    rgb_final = self._aplicar_tonalidade_rgb(rgb_pesquisado, tonalidade)
                    cor_final = f"{nome_livre} {tonalidade}".strip()
                    return {
                        "intent": "IOT_CONTROL",
                        "params": {
                            "acao": "ajustar_cor", "alvo": alvo_parametro,
                            "cor": cor_final, "rgb": rgb_final,
                            "cor_pesquisada": True,
                            **({"tonalidade": tonalidade} if tonalidade else {}),
                        },
                    }

        for nome_cor, (variantes, rgb) in cores.items():
            padrao_cor = "|".join(re.escape(item) for item in variantes)
            resposta_curta = bool(re.fullmatch(rf"(?:em\s+)?(?:{padrao_cor})", t))
            if re.search(rf"\b(?:{padrao_cor})\b", t) and alvo_parametro and (pedido_parametro or resposta_curta):
                rgb_final = self._aplicar_tonalidade_rgb(rgb, tonalidade)
                cor_final = f"{nome_cor} {tonalidade}".strip()
                return {
                    "intent": "IOT_CONTROL",
                    "params": {
                        "acao": "ajustar_cor", "alvo": alvo_parametro,
                        "cor": cor_final, "rgb": rgb_final,
                        **({"tonalidade": tonalidade} if tonalidade else {}),
                    },
                }

        resposta_tonalidade = bool(re.fullmatch(
            r"(?:agora\s+)?(?:um\s+)?(?:pouco\s+)?(?:mais|maus)\s+(?:clar[oa]|escur[oa])|pastel",
            t,
        ))
        if tonalidade and alvo_parametro and (pedido_parametro or resposta_tonalidade):
            anteriores = self._parametros_anteriores(estado, alvo_parametro)
            rgb_anterior = anteriores.get("rgb") or anteriores.get("cor_rgb")
            try:
                rgb_final = self._aplicar_tonalidade_rgb(rgb_anterior, tonalidade)
            except (TypeError, ValueError):
                rgb_final = ()
            if rgb_final:
                cor_anterior = re.sub(
                    r"\s+(?:claro|clara|escuro|escura|pastel)$",
                    "",
                    str(anteriores.get("cor") or "cor atual").strip(),
                    flags=re.IGNORECASE,
                )
                return {
                    "intent": "IOT_CONTROL",
                    "params": {
                        "acao": "ajustar_cor", "alvo": alvo_parametro,
                        "cor": f"{cor_anterior} {tonalidade}", "rgb": rgb_final,
                        "tonalidade": tonalidade, "referencia_contextual": True,
                    },
                }
            if tonalidade in {"claro", "escuro"}:
                try:
                    brilho_atual = int(anteriores.get("brilho", 70))
                except (TypeError, ValueError):
                    brilho_atual = 70
                delta = 20 if tonalidade == "claro" else -20
                brilho_novo = max(1, min(100, brilho_atual + delta))
                return {
                    "intent": "IOT_CONTROL",
                    "params": {
                        "acao": "ajustar_brilho", "alvo": alvo_parametro,
                        "valor": brilho_novo,
                        "ajuste_relativo": "aumentar" if delta > 0 else "diminuir",
                        "referencia_contextual": True,
                    },
                }

        acoes = (
            (r"\b(desliga|desligar|desligue|apaga|apagar)\b", "desligar"),
            (r"\b(liga|ligar|ligue|acende)\b", "ligar"),
            (r"\b(alterna|alternar|troca o estado|muda o estado)\b", "alternar"),
        )
        acao = ""
        if not acao:
            for padrao, nome_acao in acoes:
                if re.search(padrao, t):
                    acao = nome_acao
                    break
        if not acao:
            return None

        alvo = self._resolver_alvo_texto(t, estado)
        if not alvo:
            return None
        # "Apaga" é ambíguo: pode significar excluir um arquivo/pasta. Um
        # nome arbitrário só pertence ao IoT quando está cadastrado ou quando
        # a frase declara que se trata de luz/aparelho. Isso impede que
        # "apaga o Antonio" vire uma tentativa de desligar um dispositivo.
        if (
            re.search(r"\b(?:apaga|apagar)\b", t)
            and not re.search(
                r"\b(?:luz|lampada|dispositivo|aparelho|tomada|ventilador|iot)\b",
                t,
            )
            and self.registro.resolver(alvo) is None
        ):
            return None
        deliberativo = bool(re.search(
            r"\b(?:acho que (?:eu )?vou|talvez (?:eu )?|to pensando em|tô pensando em|estou pensando em)\b",
            t,
        ))
        if deliberativo and acao != "status":
            dispositivo = self.registro.resolver(alvo)
            nome_alvo = dispositivo.nome_amigavel if dispositivo is not None else alvo
            return {
                "intent": "SUGGEST_ACTION",
                "params": {
                    "acao_sugerida": {"intent": "IOT_CONTROL", "params": {"acao": acao, "alvo": alvo}},
                    "descricao": f"{acao} {nome_alvo}",
                    "fala": f"Você tá pensando em {acao} {nome_alvo}. Quer que eu faça?",
                    "origem": "intencao_deliberativa",
                },
            }
        intent = "IOT_STATUS" if acao == "status" else "IOT_CONTROL"
        return {"intent": intent, "params": {"acao": acao, "alvo": alvo}}

    def executar(self, resultado: Dict[str, Any], texto_original: str = "") -> Dict[str, Any]:
        intent = str(resultado.get("intent") or "").upper().strip()
        params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}

        if intent == "IOT_LIST":
            ambiente = str(params.get("ambiente") or "").strip()
            dispositivos = self.controlador.listar(ambiente)
            if dispositivos:
                nomes = ", ".join(
                    f"{item.nome_amigavel} ({item.ambiente})" for item in dispositivos
                )
                fala = f"Tenho estes dispositivos no radar: {nomes}."
                status = "dispositivos_listados"
            else:
                fala = f"Não tenho dispositivo cadastrado em {ambiente}." if ambiente else "Ainda não tenho dispositivo IoT cadastrado."
                status = "nenhum_dispositivo"
            contrato = ResultadoAcao(
                intent=intent, status=status, alvo=ambiente or "dispositivos IoT",
                executou=True, confirmado=True, texto_usuario=texto_original,
            )
            plano = planejar_resposta_acao(contrato, fala, emocao_preferida="calma")
            if self.emitir_fala:
                self.falar(plano.fala, plano.emocao, plano.nivel)
            return {
                "handled": True, "ok": bool(dispositivos), "status": status, "alvo": ambiente,
                "resultado_acao": contrato,
                "plano_resposta": {"fala": plano.fala, "emocao": plano.emocao, "nivel": plano.nivel},
            }

        if intent not in {"IOT_CONTROL", "IOT_STATUS"}:
            return {"handled": False, "ok": False, "status": "intent_invalida"}

        acao = "status" if intent == "IOT_STATUS" else str(params.get("acao") or "").strip().lower()
        alvo = str(params.get("alvo") or params.get("dispositivo") or "").strip()
        ambiente = str(params.get("ambiente") or "").strip()
        origem = str(params.get("origem") or "usuario").strip().lower()
        confirmado = bool(params.get("confirmado", False))
        resposta = self.controlador.executar(
            acao,
            alvo,
            ambiente=ambiente,
            origem=origem,
            confirmado=confirmado,
            parametros=params,
        )
        estado_mental = self.estado_mental_getter()
        if isinstance(estado_mental, dict) and resposta.dispositivo:
            estado_mental["ultimo_dispositivo_iot"] = resposta.dispositivo
            estado_mental["ultimo_ambiente_iot"] = resposta.ambiente
            estado_mental["ultimo_estado_iot"] = resposta.estado_atual
            estado_mental["ultima_habilidade"] = "iot"
            estado_mental["ultima_propriedade_iot"] = acao
            estado_mental["foco_operacional_ts"] = time.time()
            if resposta.status in {"brilho_ajustado", "cor_ajustada", "branco_ajustado"} and resposta.detalhes:
                por_dispositivo = estado_mental.get("parametros_iot_por_dispositivo")
                por_dispositivo = dict(por_dispositivo) if isinstance(por_dispositivo, dict) else {}
                anteriores = por_dispositivo.get(resposta.dispositivo)
                anteriores = dict(anteriores) if isinstance(anteriores, dict) else {}
                anteriores.update(dict(resposta.detalhes))
                por_dispositivo[resposta.dispositivo] = anteriores
                estado_mental["parametros_iot_por_dispositivo"] = por_dispositivo
                estado_mental["ultimos_parametros_iot"] = dict(anteriores)
        dispositivo_resolvido = self.registro.resolver(resposta.dispositivo or alvo, resposta.ambiente or ambiente)
        nome = (
            dispositivo_resolvido.nome_amigavel
            if dispositivo_resolvido is not None
            else resposta.dispositivo or alvo or "esse dispositivo"
        )
        nome_fala = self._nome_com_artigo(nome)
        nome_com_de = self._nome_com_de(nome_fala)
        nome_com_em = self._nome_com_em(nome_fala)
        prefixo_modo = "No simulador, " if self.modo == "simulado" else ""
        falas = {
            "ligado": f"{prefixo_modo}pronto, liguei {nome_fala}.",
            "desligado": f"{prefixo_modo}pronto, desliguei {nome_fala}.",
            "ja_estava_ligado": f"{prefixo_modo}{nome_fala} já estava ligado.",
            "ja_estava_desligado": f"{prefixo_modo}{nome_fala} já estava desligado.",
            "estado_desconhecido": f"{nome_fala} respondeu, mas não consegui identificar se está ligado ou desligado.",
            "indisponivel": f"{nome_fala} não respondeu agora. Posso tentar de novo depois.",
            "nao_encontrado": f"Não encontrei nenhum dispositivo chamado {alvo}.",
            "protocolo_indisponivel": f"{nome_fala} está cadastrado, mas o protocolo dele não está disponível.",
            "confirmacao_necessaria": f"Essa ação para {nome_fala} precisa da sua confirmação antes de eu mexer no mundo físico.",
            "bloqueado_por_seguranca": f"Não executei esse comando para {nome_fala}: a regra de segurança bloqueou.",
            "falha_execucao": f"Tentei mexer {nome_com_em}, mas o dispositivo não confirmou a ação.",
            "falha_validacao": f"O comando foi enviado para {nome_fala}, mas eu não consegui confirmar a mudança.",
            "falha_consulta": f"Não consegui confirmar o estado atual {nome_com_de}.",
            "acao_invalida": "Esse comando IoT escapou do contrato. Não executei nada.",
        }
        if resposta.status == "brilho_ajustado":
            valor = resposta.detalhes.get("brilho", params.get("valor", ""))
            fala = f"{prefixo_modo}pronto, deixei o brilho {nome_com_de} em {valor} por cento."
        elif resposta.status == "cor_ajustada":
            cor = resposta.detalhes.get("cor") or params.get("cor") or "na cor pedida"
            cor_fala = self._cor_feminina(str(cor))
            fala = f"{prefixo_modo}pronto, deixei {nome_fala} {cor_fala}."
        elif resposta.status == "branco_ajustado":
            cor = resposta.detalhes.get("cor") or params.get("cor") or "em branco"
            fala = f"{prefixo_modo}pronto, deixei {nome_fala} em {cor}."
        elif resposta.status in {"ligado", "desligado"} and acao == "status":
            fala = f"{prefixo_modo}{nome_fala} está {resposta.status}."
        else:
            fala = falas.get(resposta.status, f"Não consegui concluir a ação em {nome}.")
        plano_fala = planejar_resposta_acao(
            ResultadoAcao(
                intent=intent,
                status=resposta.status,
                alvo=nome_fala,
                executou=bool(resposta.ok),
                confirmado=bool(resposta.confirmado),
                detalhe=resposta.erro or str(resposta.detalhes or ""),
                texto_usuario=texto_original,
                contexto={"modo": self.modo, "ambiente": resposta.ambiente},
            ),
            fala,
            emocao_preferida="calma",
        )
        fala = plano_fala.fala
        emocao_resultado = plano_fala.emocao
        nivel_resultado = plano_fala.nivel
        if callable(self.definir_emocao):
            self.definir_emocao(emocao_resultado, nivel_resultado, f"resultado IoT: {resposta.status}")
        if self.emitir_fala:
            self.falar(fala, emocao_resultado, nivel_resultado)
        self.log(
            f"🏠 [IOT:RESULTADO] modo={self.modo} dispositivo={nome} acao={acao} "
            f"status={resposta.status} confirmado={resposta.confirmado}"
        )
        return {
            "handled": True,
            "ok": bool(resposta.ok),
            "status": resposta.status,
            "alvo": nome,
            "ambiente": resposta.ambiente,
            "estado_anterior": resposta.estado_anterior,
            "estado": resposta.estado_atual,
            "confirmado": resposta.confirmado,
            "erro": resposta.erro,
            "detalhes": dict(resposta.detalhes or {}),
            "modo": self.modo,
            "resultado_acao": ResultadoAcao(
                intent=intent,
                status=resposta.status,
                alvo=nome_fala,
                params=params,
                executou=bool(resposta.ok),
                confirmado=bool(resposta.confirmado),
                detalhe=resposta.erro or str(resposta.detalhes or ""),
                texto_usuario=texto_original,
                contexto={"modo": self.modo, "ambiente": resposta.ambiente},
            ),
            "plano_resposta": {"fala": fala, "emocao": emocao_resultado, "nivel": nivel_resultado},
        }


def criar_runtime_iot(**kwargs: Any) -> RuntimeIoT:
    return RuntimeIoT(**kwargs)
