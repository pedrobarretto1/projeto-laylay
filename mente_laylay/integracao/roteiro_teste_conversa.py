"""Execução sequencial e persistente de roteiros conversacionais da Laylay.

O runtime usa a mesma entrada canônica dos terminais. Ele nunca interpreta nem
executa habilidades por conta própria: envia um texto, aguarda a fala final e
o resultado canônico do turno, e somente então libera o próximo texto.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import threading
import time
from typing import Any, Callable, Mapping, Sequence, TextIO

from mente_laylay.integracao.avaliador_roteiro_teste import (
    avaliar_turno_roteiro,
    gravar_relatorios_roteiro,
)
from mente_laylay.integracao.diagnostico_encerramento import (
    registrar_evento_encerramento,
)
# UPGRADE_TESTADOR_SEMANTICO_V32_20260814


_REFERENCIA_CONTEXTUAL = re.compile(
    r"\b(?:ele|ela|isso|aquilo|esse|essa|este|esta|"
    r"nele|nela|dele|dela)\b"
)
_ANCORA_EXPLICITA_NO_COMANDO = re.compile(
    r"\b(?:arquivo|arquivos|pasta|pastas|documento|documentos|"
    r"resultado|resultados|c[oó]digo|c[oó]digos|playlist|playlists|"
    r"m[uú]sica|m[uú]sicas|faixa|faixas|l[aâ]mpada|l[aâ]mpadas|"
    r"tomada|tomadas|aba|abas|janela|janelas|aplicativo|aplicativos|"
    r"app|apps|programa|programas|site|sites|navegador|navegadores|"
    r"opera|microsoft\s+store|prime\s+video|youtube|chrome|wikip[eé]dia)\b"
)


def _normalizar_expectativas_semanticas(
    valor: Any,
) -> dict[int | str, dict[str, Any]]:
    if valor is None:
        return {}
    if not isinstance(valor, Mapping):
        raise ValueError("EXPECTATIVAS_SEMANTICAS precisa ser um dicionário")
    resultado: dict[int | str, dict[str, Any]] = {}
    for chave, expectativa in valor.items():
        if isinstance(chave, bool):
            raise ValueError(
                "cada chave de EXPECTATIVAS_SEMANTICAS deve ser um turno "
                "positivo ou um comando textual"
            )
        if isinstance(chave, int):
            if chave < 1:
                raise ValueError(
                    "turnos de EXPECTATIVAS_SEMANTICAS começam em 1"
                )
            chave_normalizada: int | str = chave
        elif isinstance(chave, str) and chave.strip():
            chave_normalizada = chave.strip()
        else:
            raise ValueError(
                "cada chave de EXPECTATIVAS_SEMANTICAS deve ser um turno "
                "positivo ou um comando textual"
            )
        if not isinstance(expectativa, Mapping):
            raise ValueError(
                "cada expectativa semântica precisa ser um dicionário"
            )
        resultado[chave_normalizada] = dict(expectativa)
    return resultado


@dataclass(frozen=True)
class ConfiguracaoRoteiro:
    comandos: tuple[str, ...]
    atraso_inicial_s: float = 0.0
    timeout_resposta_s: float = 120.0
    timeout_voz_s: float = 240.0
    intervalo_comandos_s: float = 0.0
    parar_sem_resposta: bool = True
    encerrar_ao_final: bool = False
    silenciar_voz_durante_teste: bool = False
    aguardar_confirmacao_execucao: bool = False
    expectativas_semanticas: Mapping[int | str, Mapping[str, Any]] = field(
        default_factory=dict,
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "expectativas_semanticas",
            _normalizar_expectativas_semanticas(self.expectativas_semanticas),
        )


def _literal_por_nome(arvore: ast.Module, nome: str, padrao: Any) -> Any:
    for no in arvore.body:
        if not isinstance(no, (ast.Assign, ast.AnnAssign)):
            continue
        alvos = no.targets if isinstance(no, ast.Assign) else [no.target]
        if not any(isinstance(alvo, ast.Name) and alvo.id == nome for alvo in alvos):
            continue
        try:
            return ast.literal_eval(no.value)
        except (ValueError, TypeError, SyntaxError):
            raise ValueError(f"{nome} precisa conter apenas um valor Python literal")
    return padrao


def carregar_configuracao_roteiro(caminho: str | os.PathLike[str]) -> ConfiguracaoRoteiro:
    """Lê somente constantes literais do arquivo Python indicado."""

    arquivo = Path(caminho).expanduser().resolve()
    if not arquivo.is_file():
        raise FileNotFoundError(f"roteiro não encontrado: {arquivo}")
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"), filename=str(arquivo))
    bruto = _literal_por_nome(arvore, "COMANDOS", ())
    if isinstance(bruto, str):
        itens = bruto.splitlines()
    elif isinstance(bruto, (list, tuple)):
        itens = bruto
    else:
        raise ValueError("COMANDOS precisa ser uma lista, tupla ou texto com uma frase por linha")
    comandos = tuple(
        texto for item in itens
        if (texto := str(item or "").strip()) and not texto.startswith("#")
    )
    if not comandos:
        raise ValueError("o roteiro não contém comandos")
    return ConfiguracaoRoteiro(
        comandos=comandos,
        atraso_inicial_s=max(
            0.0, float(_literal_por_nome(arvore, "ATRASO_INICIAL_S", 10.0)),
        ),
        timeout_resposta_s=max(
            1.0, float(_literal_por_nome(arvore, "TIMEOUT_RESPOSTA_S", 120.0)),
        ),
        timeout_voz_s=max(
            1.0, float(_literal_por_nome(arvore, "TIMEOUT_VOZ_S", 240.0)),
        ),
        intervalo_comandos_s=max(
            0.0, float(_literal_por_nome(arvore, "INTERVALO_ENTRE_COMANDOS_S", 0.0)),
        ),
        parar_sem_resposta=bool(
            _literal_por_nome(arvore, "PARAR_SEM_RESPOSTA", True)
        ),
        encerrar_ao_final=bool(
            _literal_por_nome(arvore, "ENCERRAR_AO_FINAL", False)
        ),
        # Arquivos de roteiro reais são silenciosos por padrão. A dataclass
        # mantém False para runtimes programáticos e testes que exercitam a
        # sincronização de áudio explicitamente.
        silenciar_voz_durante_teste=bool(
            _literal_por_nome(arvore, "SILENCIAR_VOZ_DURANTE_TESTE", True)
        ),
        aguardar_confirmacao_execucao=bool(
            _literal_por_nome(arvore, "AGUARDAR_CONFIRMACAO_EXECUCAO", True)
        ),
        expectativas_semanticas=_literal_por_nome(
            arvore,
            "EXPECTATIVAS_SEMANTICAS",
            {},
        ),
    )


def assinatura_roteiro(
    comandos: Sequence[str],
    expectativas_semanticas: Mapping[int | str, Mapping[str, Any]] | None = None,
) -> str:
    expectativas = _normalizar_expectativas_semanticas(
        expectativas_semanticas,
    )
    carga: Any = list(comandos)
    if expectativas:
        expectativas_assinatura = [
            {
                "seletor": (
                    f"turno:{chave}"
                    if isinstance(chave, int)
                    else f"comando:{chave}"
                ),
                "expectativa": expectativa,
            }
            for chave, expectativa in sorted(
                expectativas.items(),
                key=lambda item: (
                    0 if isinstance(item[0], int) else 1,
                    str(item[0]).casefold(),
                ),
            )
        ]
        carga = {
            "comandos": list(comandos),
            "expectativas_semanticas": expectativas_assinatura,
        }
    conteudo = json.dumps(
        carga,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def preparar_diretorio_resultado(
    caminho_roteiro: str | os.PathLike[str],
    *,
    raiz: str | os.PathLike[str],
    retomar: bool = False,
) -> Path:
    base = Path(raiz).expanduser().resolve()
    base.mkdir(parents=True, exist_ok=True)
    nome = Path(caminho_roteiro).stem
    prefixo = f"{nome}-"
    if retomar:
        candidatos = sorted(
            (
                item for item in base.iterdir()
                if item.is_dir()
                and item.name.startswith(prefixo)
                and (item / "checkpoint.json").is_file()
            ),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        if candidatos:
            return candidatos[0]
    instante = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    destino = base / f"{prefixo}{instante}"
    destino.mkdir(parents=True, exist_ok=False)
    return destino


class EspelhoTerminalPersistente:
    """Replica stdout/stderr para disco e confirma cada linha fisicamente."""

    def __init__(self, original: TextIO, caminho: str | os.PathLike[str]) -> None:
        self.original = original
        self.arquivo = open(caminho, "a", encoding="utf-8", buffering=1)
        self._lock = threading.RLock()

    def write(self, texto: str) -> int:
        dado = str(texto or "")
        with self._lock:
            try:
                escrito = self.original.write(dado)
                self.original.flush()
            except (BrokenPipeError, OSError):
                escrito = len(dado)
            self.arquivo.write(dado)
            self.arquivo.flush()
            if "\n" in dado:
                os.fsync(self.arquivo.fileno())
            return int(escrito if escrito is not None else len(dado))

    def flush(self) -> None:
        with self._lock:
            try:
                self.original.flush()
            except (BrokenPipeError, OSError):
                pass
            self.arquivo.flush()

    def isatty(self) -> bool:
        return bool(getattr(self.original, "isatty", lambda: False)())

    @property
    def encoding(self) -> str:
        return str(getattr(self.original, "encoding", "utf-8") or "utf-8")

    def fechar(self) -> None:
        with self._lock:
            if not self.arquivo.closed:
                self.arquivo.flush()
                os.fsync(self.arquivo.fileno())
                self.arquivo.close()


class RoteiroTesteConversaRuntime:
    def __init__(
        self,
        configuracao: ConfiguracaoRoteiro,
        *,
        enviar_entrada: Callable[[str], Any],
        resultado_getter: Callable[[], Mapping[str, Any]] | None,
        voz_ocupada_getter: Callable[[], bool] | None = None,
        ativar_modo_chat: Callable[[], Any] | None = None,
        modo_chat_ativo_getter: Callable[[], bool] | None = None,
        diretorio_resultado: str | os.PathLike[str],
        retomar: bool = False,
        ao_finalizar: Callable[[bool], Any] | None = None,
        log: Callable[[str], Any] = print,
        clock: Callable[[], float] = time.time,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Any] = time.sleep,
    ) -> None:
        self.configuracao = configuracao
        self.enviar_entrada = enviar_entrada
        self.resultado_getter = resultado_getter
        self.voz_ocupada_getter = voz_ocupada_getter
        self.ativar_modo_chat = ativar_modo_chat
        self.modo_chat_ativo_getter = modo_chat_ativo_getter
        self.diretorio = Path(diretorio_resultado).resolve()
        self.diretorio.mkdir(parents=True, exist_ok=True)
        self.retomar = bool(retomar)
        self.ao_finalizar = ao_finalizar
        self.log = log
        self.clock, self.monotonic, self.sleep = clock, monotonic, sleep
        self.checkpoint_path = self.diretorio / "checkpoint.json"
        self.conversa_path = self.diretorio / "conversa.md"
        self.planos_path = self.diretorio / "planos.jsonl"
        self._lock = threading.RLock()
        self._resposta_event = threading.Event()
        self._indice_aguardado: int | None = None
        self._resposta_atual = ""
        self._plano_na_publicacao_resposta: dict[str, Any] = {}
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._estado = self._carregar_ou_criar_estado()

    def _criterio_conclusao(self) -> str:
        partes = ["transporte_resposta"]
        if self.configuracao.aguardar_confirmacao_execucao:
            partes.append("resultado_turno")
        if not self.configuracao.silenciar_voz_durante_teste:
            partes.append("voz")
        return "_e_".join(partes)

    def _estado_inicial(self) -> dict[str, Any]:
        return {
            "versao": 2,
            "assinatura": assinatura_roteiro(
                self.configuracao.comandos,
                self.configuracao.expectativas_semanticas,
            ),
            "criado_em": self.clock(),
            "atualizado_em": self.clock(),
            "concluido": False,
            "criterio_conclusao": self._criterio_conclusao(),
            "voz_silenciada_durante_teste": bool(
                self.configuracao.silenciar_voz_durante_teste
            ),
            "itens": [
                {
                    "indice": indice,
                    "comando": comando,
                    "status": "pendente",
                    "resposta": "",
                }
                for indice, comando in enumerate(self.configuracao.comandos)
            ],
        }

    def _carregar_ou_criar_estado(self) -> dict[str, Any]:
        esperado = assinatura_roteiro(
            self.configuracao.comandos,
            self.configuracao.expectativas_semanticas,
        )
        if self.retomar and self.checkpoint_path.is_file():
            try:
                estado = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as erro:
                raise ValueError("checkpoint do roteiro está ilegível") from erro
            if str(estado.get("assinatura") or "") != esperado:
                raise ValueError("o roteiro mudou; não é seguro retomar este checkpoint")
            # A política de áudio pode mudar entre a execução original e a
            # retomada sem alterar os comandos nem sua assinatura.
            estado["criterio_conclusao"] = self._criterio_conclusao()
            estado["voz_silenciada_durante_teste"] = bool(
                self.configuracao.silenciar_voz_durante_teste
            )
            return dict(estado)
        estado = self._estado_inicial()
        self._gravar_checkpoint(estado)
        if not self.conversa_path.exists():
            self._anexar_conversa(
                "# Teste automatizado da Laylay\n\n"
                f"Iniciado em {datetime.now().isoformat(timespec='seconds')}.\n\n"
            )
        return estado

    def _gravar_checkpoint(self, estado: Mapping[str, Any] | None = None) -> None:
        retrato = dict(estado or self._estado)
        retrato["atualizado_em"] = self.clock()
        temporario = self.checkpoint_path.with_suffix(".json.tmp")
        with open(temporario, "w", encoding="utf-8", newline="\n") as arquivo:
            json.dump(retrato, arquivo, ensure_ascii=False, indent=2)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, self.checkpoint_path)

    def _anexar_conversa(self, texto: str) -> None:
        with open(self.conversa_path, "a", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(str(texto or ""))
            arquivo.flush()
            os.fsync(arquivo.fileno())

    def _anexar_plano_bruto(
        self,
        *,
        indice: int,
        comando: str,
        plano: Mapping[str, Any] | None,
    ) -> None:
        registro = {
            "indice": int(indice),
            "comando": str(comando or ""),
            "observado_em": self.clock(),
            "plano": dict(plano or {}),
        }
        with open(self.planos_path, "a", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())

    @staticmethod
    def _avaliacao_mecanica(
        plano: Mapping[str, Any] | None,
        *,
        respondeu: bool,
    ) -> dict[str, Any]:
        retrato = dict(plano or {})
        comandos = [
            dict(item) for item in retrato.get("comandos") or []
            if isinstance(item, Mapping)
        ]
        execucoes = [item.get("executou") for item in comandos]
        confirmacoes = [item.get("confirmado") for item in comandos]

        def resumir(valores: list[Any], *, positivo: str, negativo: str) -> str:
            if not valores:
                return "sem_comando_observado"
            if any(valor is True for valor in valores):
                return positivo
            if all(valor is False for valor in valores):
                return negativo
            return "indeterminado"

        return {
            "respondeu": bool(respondeu),
            "plano_observado": bool(retrato),
            "quantidade_comandos": len(comandos),
            "execucao": resumir(
                execucoes,
                positivo="alguma_etapa_executada",
                negativo="nenhuma_etapa_executada",
            ),
            "confirmacao": resumir(
                confirmacoes,
                positivo="alguma_etapa_confirmada",
                negativo="nenhuma_etapa_confirmada",
            ),
            # O roteiro não conhece a expectativa semântica de cada frase. Dar
            # nota aqui seria repetir o antigo falso positivo de "respondido".
            "intencao_correta": "nao_avaliado",
            "fala_coerente": "nao_avaliado",
        }

    @staticmethod
    def _resumo_plano_markdown(plano: Mapping[str, Any] | None) -> str:
        retrato = dict(plano or {})
        comandos = [
            dict(item) for item in retrato.get("comandos") or []
            if isinstance(item, Mapping)
        ]
        if not retrato:
            return ""
        if not comandos:
            fase = str(retrato.get("fase") or "observado").strip()
            return f"**Plano observado:** {fase}; sem comando operacional.\n\n"
        itens = []
        for item in comandos[:8]:
            intent = str(item.get("intent") or "SEM_INTENT").strip()
            status = str(item.get("status") or "sem_status").strip()
            itens.append(
                f"`{intent}` → `{status}` "
                f"(executou={item.get('executou')!r}, "
                f"confirmado={item.get('confirmado')!r})"
            )
        sufixo = f"; e mais {len(comandos) - 8}" if len(comandos) > 8 else ""
        return "**Plano observado:** " + "; ".join(itens) + sufixo + ".\n\n"

    @staticmethod
    def _plano_compacto_checkpoint(
        plano: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        retrato = dict(plano or {})
        comandos = [
            dict(item) for item in retrato.get("comandos") or []
            if isinstance(item, Mapping)
        ]
        return {
            "fase": str(retrato.get("fase") or ""),
            "erros": [str(item)[:240] for item in retrato.get("erros") or []][:8],
            "comandos": [{
                chave: item.get(chave)
                for chave in (
                    "intent", "alvo", "status", "executou", "confirmado",
                    "confirmacao_oferecida", "evidencia_confirmacao",
                )
                if chave in item
            } for item in comandos[:12]],
            "plano_bruto": "planos.jsonl",
        }

    def _item(self, indice: int) -> dict[str, Any]:
        return dict(self._estado["itens"][indice])

    def _expectativa_semantica_local(
        self,
        indice: int,
        comando: str,
    ) -> dict[str, Any] | None:
        expectativas = self.configuracao.expectativas_semanticas
        por_turno = expectativas.get(indice + 1)
        if isinstance(por_turno, Mapping):
            return dict(por_turno)
        texto = re.sub(r"\s+", " ", str(comando or "")).strip().casefold()
        for chave, expectativa in expectativas.items():
            if not isinstance(chave, str):
                continue
            chave_textual = re.sub(r"\s+", " ", chave).strip().casefold()
            if chave_textual == texto and isinstance(expectativa, Mapping):
                return dict(expectativa)
        return None

    def _atualizar_item(self, indice: int, **campos: Any) -> None:
        # V32: ENRIQUECIMENTO_SEMANTICO_CENTRAL
        with self._lock:
            item = dict(self._estado["itens"][indice])
            plano_avaliacao_efemero = campos.pop("_plano_avaliacao", None)

            if isinstance(campos.get("avaliacao"), Mapping):
                avaliacao_mecanica = dict(campos.get("avaliacao") or {})
                plano_avaliacao = plano_avaliacao_efemero

                if not isinstance(plano_avaliacao, Mapping):
                    plano_avaliacao = campos.get("plano")
                if not isinstance(plano_avaliacao, Mapping):
                    plano_avaliacao = item.get("plano")
                if not isinstance(plano_avaliacao, Mapping):
                    plano_avaliacao = {}

                status_item = str(
                    campos.get("status")
                    or item.get("status")
                    or ""
                )
                respondeu = bool(
                    avaliacao_mecanica.get(
                        "respondeu",
                        status_item not in {"sem_resposta", "erro_envio"},
                    )
                )

                try:
                    campos["avaliacao"] = avaliar_turno_roteiro(
                        indice=indice,
                        comando=str(
                            campos.get("comando")
                            or item.get("comando")
                            or self.configuracao.comandos[indice]
                        ),
                        resposta=str(
                            campos.get(
                                "resposta",
                                item.get("resposta", ""),
                            )
                            or ""
                        ),
                        plano=plano_avaliacao,
                        respondeu=respondeu,
                        motivo_resultado=str(
                            campos.get("motivo_resultado")
                            or status_item
                            or ""
                        ),
                        enviado_em=(
                            campos.get("enviado_em")
                            if campos.get("enviado_em") is not None
                            else item.get("enviado_em")
                        ),
                        finalizado_em=campos.get("finalizado_em"),
                        avaliacao_mecanica=avaliacao_mecanica,
                        expectativa_local=self._expectativa_semantica_local(
                            indice,
                            str(
                                campos.get("comando")
                                or item.get("comando")
                                or self.configuracao.comandos[indice]
                            ),
                        ),
                    )
                except Exception as erro:
                    avaliacao_mecanica["avaliador_erro"] = type(erro).__name__
                    campos["avaliacao"] = avaliacao_mecanica
                    self.log(
                        "⚠️ [ROTEIRO:AVALIADOR] falha ao avaliar turno "
                        f"{indice + 1:03d} | tipo={type(erro).__name__}"
                    )

            item.update(campos)
            self._estado["itens"][indice] = item
            self._gravar_checkpoint()

            if isinstance(campos.get("avaliacao"), Mapping):
                try:
                    gravar_relatorios_roteiro(
                        self._estado,
                        self.diretorio,
                    )
                except Exception as erro:
                    self.log(
                        "⚠️ [ROTEIRO:RELATORIO] atualização indisponível "
                        f"| tipo={type(erro).__name__}"
                    )

    def observar_resposta(
        self,
        texto: str,
        _emocao: str = "calma",
        _nivel: int = 1,
        **dados: Any,
    ) -> bool:
        if bool(dados.get("proativa")):
            return True
        fala = str(texto or "").strip()
        if not fala:
            return False
        # A fala é publicada depois da verificação final do turno. Capturar o
        # plano no mesmo instante evita perder esse contrato caso outra tarefa
        # de cauda limpe ou substitua o estado antes de o roteiro acordar.
        plano_publicado = self._plano_atual()
        with self._lock:
            if self._indice_aguardado is None:
                return True
            self._resposta_atual = fala
            self._plano_na_publicacao_resposta = plano_publicado
            self._resposta_event.set()
        return True

    @staticmethod
    def _aguardar_processamento(
        retorno: Any,
        prazo: float,
        monotonic,
        sleep=time.sleep,
    ) -> bool:
        # RT1-H1: resposta publicada/plano terminal nao provam fim do worker.
        # Retornos nao aguardaveis representam senders sincronos.
        if isinstance(retorno, threading.Thread):
            while retorno.is_alive() and monotonic() < prazo:
                retorno.join(
                    timeout=min(0.1, max(0.0, prazo - monotonic()))
                )
            return not retorno.is_alive()

        result = getattr(retorno, "result", None)
        if callable(result):
            restante = max(0.0, prazo - monotonic())
            try:
                result(timeout=restante)
                return True
            except TimeoutError:
                return False
            except TypeError:
                # Future/Task sem result(timeout): so libera com prova done().
                done = getattr(retorno, "done", None)
                if not callable(done):
                    return False
                while monotonic() < prazo:
                    try:
                        if bool(done()):
                            return True
                    except Exception:
                        return False
                    sleep(min(0.05, max(0.0, prazo - monotonic())))
                try:
                    return bool(done())
                except Exception:
                    return False
            except Exception:
                # Excecao da tarefa prova terminalidade. O resultado
                # operacional continua sendo julgado pelo plano do turno.
                return True

        return True

    def _plano_atual(self) -> dict[str, Any]:
        if not callable(self.resultado_getter):
            return {}
        try:
            resultado = self.resultado_getter()
            return dict(resultado or {}) if isinstance(resultado, Mapping) else {}
        except Exception:
            return {}

    @staticmethod
    def _texto_plano(texto: Any) -> str:
        return re.sub(r"\s+", " ", str(texto or "")).strip().casefold()

    @classmethod
    def _plano_corresponde_ao_turno(
        cls,
        plano: Mapping[str, Any] | None,
        *,
        comando: str,
        plano_id_anterior: Any,
    ) -> bool:
        retrato = dict(plano or {})
        if not retrato:
            return False
        if cls._texto_plano(retrato.get("texto_usuario")) != cls._texto_plano(comando):
            return False
        plano_id = retrato.get("id")
        if plano_id_anterior not in (None, "") and plano_id == plano_id_anterior:
            return False
        return True

    @classmethod
    def _resultado_turno_terminal(
        cls,
        plano: Mapping[str, Any] | None,
        *,
        comando: str,
        plano_id_anterior: Any,
    ) -> tuple[bool, str]:
        """Reconhece o contrato final do turno sem exigir falso sucesso.

        Uma falha observada e um pedido de confirmação também encerram o
        comando atual. Isso permite que o roteiro envie, respectivamente, o
        próximo caso ou o ``Sim``/``Não`` que resolve a pendência. Estados
        intermediários nunca liberam a fila.
        """

        if not cls._plano_corresponde_ao_turno(
            plano,
            comando=comando,
            plano_id_anterior=plano_id_anterior,
        ):
            return False, "plano_de_outro_turno"
        retrato = dict(plano or {})
        comandos = [
            dict(item) for item in retrato.get("comandos") or []
            if isinstance(item, Mapping)
        ]
        if not comandos:
            if retrato.get("erros"):
                return True, "erro_publicado"
            if not bool(retrato.get("requer_execucao")):
                return True, "resposta_sem_execucao"
            decisao = (
                dict(retrato.get("decisao_turno") or {})
                if isinstance(retrato.get("decisao_turno"), Mapping)
                else {}
            )
            if decisao and decisao.get("permite_acao") is False:
                return True, "execucao_nao_autorizada"
            if retrato.get("autoriza_execucao") is False:
                return True, "execucao_nao_autorizada"
            if str(retrato.get("fase") or "").strip().casefold() in {
                "executado", "falha_execucao", "fala_verificada",
                "tratado_prioritario", "tratado_pre_fluxo",
            }:
                # O turno acabou, porém nenhuma habilidade publicou contrato.
                # Isso é uma falha observável do teste, não uma execução ainda
                # em andamento; registrar e avançar evita um falso travamento.
                return True, "execucao_nao_publicada"
            return False, "execucao_sem_resultado"

        estados_intermediarios = {
            "", "pendente", "planejado", "solicitado", "enviado",
            "em_execucao", "executando", "processando",
        }
        contrato_incompleto = False
        for item in comandos:
            status = str(item.get("status") or "").strip().casefold()
            if (
                not str(item.get("intent") or "").strip()
                or status in estados_intermediarios
                or "executou" not in item
                or "confirmado" not in item
            ):
                contrato_incompleto = True
                break
        if contrato_incompleto:
            fase = str(retrato.get("fase") or "").strip().casefold()
            if fase in {
                "executado", "falha_execucao", "fala_verificada",
                "tratado_prioritario", "tratado_pre_fluxo",
            }:
                # A fase terminal prova que o executor já devolveu o controle.
                # Um status vazio/sem confirmação não vai amadurecer depois:
                # é quebra do contrato operacional. O roteiro registra a falha
                # e continua, em vez de consumir todo o timeout e congelar.
                return True, "contrato_operacional_incompleto"
            return False, "comando_ainda_em_execucao"
        if any(
            str(item.get("status") or "").strip().casefold()
            in {"aguardando_confirmacao", "confirmacao_pendente"}
            for item in comandos
        ):
            return True, "aguardando_confirmacao_usuario"
        # Um no-op idempotente é representado corretamente como
        # ``executou=False`` e ``confirmado=True``: o executor não repetiu a
        # ação porque o estado desejado já estava observado. A confirmação
        # precisa vencer a heurística de falha, inclusive em planos compostos
        # com uma etapa já satisfeita e outra efetivamente executada.
        if any(item.get("confirmado") is True for item in comandos):
            return True, "execucao_confirmada"
        if any(item.get("executou") is False for item in comandos):
            return True, "falha_confirmada"
        return True, "resultado_final_sem_observacao_externa"

    def _aguardar_resultado_turno(
        self,
        *,
        comando: str,
        plano_id_anterior: Any,
        prazo: float,
        plano_inicial: Mapping[str, Any] | None = None,
    ) -> tuple[bool, str, dict[str, Any]]:
        ultimo_plano = dict(plano_inicial or {})
        ultimo_motivo = "plano_ausente"
        while not self._stop.is_set():
            concluido, ultimo_motivo = self._resultado_turno_terminal(
                ultimo_plano,
                comando=comando,
                plano_id_anterior=plano_id_anterior,
            )
            if concluido:
                return True, ultimo_motivo, ultimo_plano
            ultimo_plano = self._plano_atual()
            if self.monotonic() >= prazo:
                break
            self.sleep(min(0.05, max(0.0, prazo - self.monotonic())))
        return False, ultimo_motivo, ultimo_plano

    def _voz_ocupada(self) -> bool:
        if self.configuracao.silenciar_voz_durante_teste:
            return False
        if not callable(self.voz_ocupada_getter):
            return False
        try:
            return bool(self.voz_ocupada_getter())
        except Exception:
            # Uma leitura incerta nunca libera outro comando por engano.
            return True

    def _aguardar_voz_concluir(self) -> tuple[bool, bool]:
        """Espera fila e reprodução ficarem ociosas de forma estável.

        A fala final textual é publicada antes de o worker de áudio retirar o
        pedido da fila. Exigir alguns ciclos ociosos consecutivos elimina essa
        corrida e também o pequeno intervalo entre dois segmentos de voz.
        """

        if self.configuracao.silenciar_voz_durante_teste:
            return True, False
        if not callable(self.voz_ocupada_getter):
            return True, False
        prazo = self.monotonic() + self.configuracao.timeout_voz_s
        observou_voz = False
        ocioso_desde: float | None = None
        estabilidade_s = 0.45
        while not self._stop.is_set() and self.monotonic() < prazo:
            agora = self.monotonic()
            if self._voz_ocupada():
                observou_voz = True
                ocioso_desde = None
            else:
                if ocioso_desde is None:
                    ocioso_desde = agora
                if agora - ocioso_desde >= estabilidade_s:
                    return True, observou_voz
            self.sleep(0.05)
        return False, observou_voz

    def iniciar(self) -> threading.Thread:
        if self._thread and self._thread.is_alive():
            return self._thread
        self._thread = threading.Thread(
            target=self.executar,
            name="Laylay-Roteiro-Teste",
            daemon=True,
        )
        self._thread.start()
        return self._thread

    def parar(self) -> None:
        self._stop.set()
        self._resposta_event.set()

    def _preparar_inicio(self) -> bool:
        atraso = float(self.configuracao.atraso_inicial_s)
        if atraso > 0:
            self.log(
                "🧪 [ROTEIRO] aguardando inicialização antes do teste "
                f"| segundos={atraso:g}"
            )
            prazo = self.monotonic() + atraso
            while not self._stop.is_set() and self.monotonic() < prazo:
                self.sleep(min(0.1, max(0.0, prazo - self.monotonic())))
        if self._stop.is_set():
            return False
        if callable(self.ativar_modo_chat):
            try:
                retorno = self.ativar_modo_chat()
                if retorno is False:
                    raise RuntimeError("a porta do modo chat recusou a ativação")
            except Exception as erro:
                self._estado["preparacao"] = {
                    "status": "falha_modo_chat",
                    "erro": type(erro).__name__,
                }
                self._gravar_checkpoint()
                self.log(
                    "❌ [ROTEIRO] não foi possível ativar o modo chat "
                    f"| tipo={type(erro).__name__}"
                )
                return False
        if callable(self.modo_chat_ativo_getter):
            confirmado = False
            prazo_confirmacao = self.monotonic() + 3.0
            while not self._stop.is_set() and self.monotonic() < prazo_confirmacao:
                try:
                    confirmado = bool(self.modo_chat_ativo_getter())
                except Exception:
                    confirmado = False
                if confirmado:
                    break
                self.sleep(0.05)
            if not confirmado:
                self._estado["preparacao"] = {
                    "status": "modo_chat_nao_confirmado",
                }
                self._gravar_checkpoint()
                self.log(
                    "❌ [ROTEIRO] o modo chat não foi confirmado; "
                    "nenhum comando foi enviado"
                )
                return False
        self._estado["preparacao"] = {
            "status": "modo_chat_confirmado",
            "atraso_inicial_s": atraso,
            "voz_silenciada": bool(
                self.configuracao.silenciar_voz_durante_teste
            ),
        }
        self._gravar_checkpoint()
        self.log("🧪 [ROTEIRO] modo chat confirmado; iniciando os comandos")
        return True

    @staticmethod
    def _comando_depende_de_contexto(texto: str) -> bool:
        normalizado = str(texto or "").strip().casefold()
        referencia_externa = any(
            not _ANCORA_EXPLICITA_NO_COMANDO.search(
                normalizado[:referencia.start()]
            )
            for referencia in _REFERENCIA_CONTEXTUAL.finditer(normalizado)
        )
        return bool(
            referencia_externa
            or re.fullmatch(
                r"(?:tenta|tente|faz|faça|repete|repita)\s+(?:de\s+novo|outra\s+vez)[.!?]*",
                normalizado,
            )
            or re.fullmatch(
                r"(?:sim|confirmo|pode|pode sim|n[aã]o|cancela|cancelar)[.!?]*",
                normalizado,
            )
        )

    @staticmethod
    def _comando_seguro_para_reconstruir(texto: str) -> bool:
        normalizado = str(texto or "").strip().casefold()
        if not normalizado:
            return False
        # A retomada pode repetir consultas e aberturas, mas jamais refaz
        # mutações, confirmações, IoT ou controles de mídia para reconstruir
        # contexto. Nesses casos ela para e pede uma retomada manual explícita.
        return not bool(re.search(
            r"\b(?:sim|confirmo|apaga|apague|deleta|delete|exclui|exclua|"
            r"remove|remova|move|mova|renomeia|renomeie|cria|crie|escreve|"
            r"escreva|grava|grave|coloca|coloque|liga|ligue|desliga|desligue|"
            r"pausa|pause|continua|continue|pr[oó]xima|anterior|volume|"
            r"lixeira|restaura|restaure)\b",
            normalizado,
        ))

    def _preparar_retomada_contextual(self) -> bool:
        if not self.retomar:
            return True
        itens = list(self._estado.get("itens") or [])
        primeiro = next(
            (
                indice for indice, item in enumerate(itens)
                if str(item.get("status") or "") != "respondido"
            ),
            None,
        )
        if primeiro is None:
            return True
        comando = str(itens[primeiro].get("comando") or "")
        if not self._comando_depende_de_contexto(comando):
            return True

        ancora: int | None = None
        indice = primeiro - 1
        while indice >= 0 and str(itens[indice].get("status") or "") == "respondido":
            candidato = str(itens[indice].get("comando") or "")
            if not self._comando_seguro_para_reconstruir(candidato):
                break
            ancora = indice
            if not self._comando_depende_de_contexto(candidato):
                break
            indice -= 1
        if ancora is None or self._comando_depende_de_contexto(
            str(itens[ancora].get("comando") or "")
        ):
            self._estado["retomada_contexto"] = {
                "status": "contexto_nao_reconstruivel_com_seguranca",
                "indice": primeiro,
                "comando": comando,
            }
            self._gravar_checkpoint()
            self.log(
                "❌ [ROTEIRO:RETOMADA] o primeiro comando depende de contexto "
                "que não pode ser reconstruído sem repetir uma ação sensível"
            )
            return False

        for posicao in range(ancora, primeiro):
            item = dict(self._estado["itens"][posicao])
            item["status"] = "pendente_reconstrucao"
            item["reexecutado_para_contexto"] = True
            self._estado["itens"][posicao] = item
        item_pendente = dict(self._estado["itens"][primeiro])
        item_pendente["status"] = "pendente"
        self._estado["itens"][primeiro] = item_pendente
        self._estado["retomada_contexto"] = {
            "status": "reconstrucao_programada",
            "inicio": ancora,
            "fim": primeiro,
        }
        self._gravar_checkpoint()
        self._anexar_conversa(
            "## Retomada contextual\n\n"
            f"Reexecutando os itens {ancora + 1} a {primeiro + 1} para "
            "reconstruir uma referência efêmera com segurança.\n\n"
        )
        self.log(
            "⚠️ [ROTEIRO:RETOMADA] reconstruindo contexto antes do comando "
            f"{primeiro + 1:03d} | reinicio={ancora + 1:03d}"
        )
        return True

    def executar(self) -> bool:
        sucesso_total = True
        self.log(
            "🧪 [ROTEIRO] teste iniciado | "
            f"comandos={len(self.configuracao.comandos)} pasta={self.diretorio}"
        )
        if not self._preparar_inicio():
            with self._lock:
                self._estado["concluido"] = False
                self._estado["finalizado_em"] = self.clock()
                self._gravar_checkpoint()
            if callable(self.ao_finalizar):
                self.ao_finalizar(False)
            return False
        if not self._preparar_retomada_contextual():
            with self._lock:
                self._estado["concluido"] = False
                self._estado["finalizado_em"] = self.clock()
                self._gravar_checkpoint()
            if callable(self.ao_finalizar):
                self.ao_finalizar(False)
            return False
        for indice, comando in enumerate(self.configuracao.comandos):
            if self._stop.is_set():
                sucesso_total = False
                break
            item = self._item(indice)
            if self.retomar and item.get("status") == "respondido":
                continue
            numero = indice + 1
            if self._voz_ocupada():
                voz_anterior_concluida, _ = self._aguardar_voz_concluir()
                if not voz_anterior_concluida:
                    self._atualizar_item(
                        indice,
                        status="aguardando_voz_anterior",
                    )
                    self._anexar_conversa(
                        f"## {numero:03d}. Você\n\n{comando}\n\n"
                        "> ⚠️ O comando não foi enviado porque a voz anterior "
                        "ainda não terminou.\n\n"
                    )
                    self.log(
                        f"⚠️ [ROTEIRO:{numero:03d}] comando bloqueado: "
                        "a voz anterior ainda está ativa"
                    )
                    sucesso_total = False
                    break
            self._resposta_event.clear()
            with self._lock:
                self._indice_aguardado = indice
                self._resposta_atual = ""
                self._plano_na_publicacao_resposta = {}
            enviado_em = self.clock()
            self._atualizar_item(
                indice,
                status="enviado",
                enviado_em=enviado_em,
                resposta="",
            )
            self._anexar_conversa(
                f"## {numero:03d}. Você\n\n{comando}\n\n"
                f"_Enviado em {datetime.fromtimestamp(enviado_em).isoformat(timespec='seconds')}._\n\n"
            )
            # O roteiro entra pela mesma porta da conversa, mas não passa pelo
            # leitor interativo que normalmente desenha este bloco no console.
            # Exibi-lo antes do envio mantém a pergunta junto dos logs técnicos
            # do respectivo turno e o espelho persistente grava a mesma visão.
            # São duas emissões de propósito: o console da aplicação filtra
            # cada chamada de ``print`` pelo prefixo. Um único texto iniciado
            # por quebra de linha era descartado antes de chegar ao terminal.
            self.log("💬 Você:")
            self.log(f"> {comando}")
            self.log(f"🧪 [ROTEIRO:{numero:03d}] enviando: {comando}")
            plano_anterior = self._plano_atual()
            plano_id_anterior = plano_anterior.get("id")
            prazo = self.monotonic() + self.configuracao.timeout_resposta_s
            try:
                retorno = self.enviar_entrada(comando)
                if retorno is False:
                    raise RuntimeError("a entrada canônica recusou o comando")
            except Exception as erro:
                self._atualizar_item(
                    indice,
                    status="erro_envio",
                    erro=type(erro).__name__,
                )
                self._anexar_conversa(
                    f"> **Erro de envio:** {type(erro).__name__}.\n\n"
                )
                sucesso_total = False
                if self.configuracao.parar_sem_resposta:
                    break
                continue
            restante = max(0.0, prazo - self.monotonic())
            respondeu = self._resposta_event.wait(restante)
            with self._lock:
                resposta = self._resposta_atual
                plano_publicado = dict(self._plano_na_publicacao_resposta)
                self._indice_aguardado = None
            if not respondeu or not resposta:
                plano_sem_resposta = self._plano_atual()
                self._anexar_plano_bruto(
                    indice=indice,
                    comando=comando,
                    plano=plano_sem_resposta,
                )
                self._atualizar_item(
                    indice,
                    status="sem_resposta",
                    finalizado_em=self.clock(),
                    plano=self._plano_compacto_checkpoint(plano_sem_resposta),
                    _plano_avaliacao=plano_sem_resposta,
                    avaliacao=self._avaliacao_mecanica(
                        plano_sem_resposta,
                        respondeu=False,
                    ),
                )
                self._anexar_conversa(
                    "### Laylay\n\n> ⚠️ Nenhuma resposta foi observada dentro "
                    f"de {self.configuracao.timeout_resposta_s:g} segundos.\n\n"
                )
                self.log(f"⚠️ [ROTEIRO:{numero:03d}] sem resposta; checkpoint salvo")
                sucesso_total = False
                if self.configuracao.parar_sem_resposta:
                    break
                continue
            plano = plano_publicado or self._plano_atual()
            resultado_turno_concluido = True
            motivo_resultado = "barreira_desativada"
            if self.configuracao.aguardar_confirmacao_execucao:
                (
                    resultado_turno_concluido,
                    motivo_resultado,
                    plano,
                ) = self._aguardar_resultado_turno(
                    comando=comando,
                    plano_id_anterior=plano_id_anterior,
                    prazo=prazo,
                    plano_inicial=plano_publicado,
                )
            if not resultado_turno_concluido:
                self._anexar_plano_bruto(
                    indice=indice,
                    comando=comando,
                    plano=plano,
                )
                self._atualizar_item(
                    indice,
                    status="resultado_nao_finalizado",
                    resposta=resposta,
                    finalizado_em=self.clock(),
                    plano=self._plano_compacto_checkpoint(plano),
                    _plano_avaliacao=plano,
                    avaliacao=self._avaliacao_mecanica(plano, respondeu=True),
                    resultado_turno_concluido=False,
                    motivo_resultado=motivo_resultado,
                )
                self._anexar_conversa(
                    f"### Laylay\n\n{resposta}\n\n"
                    "> ⚠️ A resposta apareceu, mas o plano deste turno não "
                    "publicou um resultado final. O próximo comando não foi "
                    "enviado.\n\n"
                )
                self.log(
                    f"⚠️ [ROTEIRO:{numero:03d}] resultado não finalizado "
                    f"| motivo={motivo_resultado}; sequência interrompida"
                )
                sucesso_total = False
                break

            # RT1-H1 — BARREIRA DO WORKER CANONICO
            # N+1 nao ganha autoridade de captura enquanto o worker N vive.
            processamento_concluido = self._aguardar_processamento(
                retorno,
                prazo,
                self.monotonic,
                self.sleep,
            )
            if not processamento_concluido:
                self._anexar_plano_bruto(
                    indice=indice,
                    comando=comando,
                    plano=plano,
                )
                self._atualizar_item(
                    indice,
                    status="processamento_nao_finalizado",
                    resposta=resposta,
                    finalizado_em=self.clock(),
                    plano=self._plano_compacto_checkpoint(plano),
                    _plano_avaliacao=plano,
                    avaliacao=self._avaliacao_mecanica(
                        plano,
                        respondeu=True,
                    ),
                    resultado_turno_concluido=resultado_turno_concluido,
                    motivo_resultado=motivo_resultado,
                    processamento_concluido=False,
                )
                self._anexar_conversa(
                    f"### Laylay\n\n{resposta}\n\n"
                    "> ⚠️ A resposta e o plano apareceram, mas o worker "
                    "canonico deste turno ainda estava vivo no fim do prazo. "
                    "O proximo comando nao foi enviado.\n\n"
                )
                self.log(
                    f"⚠️ [ROTEIRO:{numero:03d}] worker canonico nao "
                    "finalizado; sequencia interrompida com seguranca"
                )
                sucesso_total = False
                break

            voz_concluida, voz_observada = self._aguardar_voz_concluir()
            if not voz_concluida:
                self._anexar_plano_bruto(
                    indice=indice,
                    comando=comando,
                    plano=plano,
                )
                self._atualizar_item(
                    indice,
                    status="voz_nao_finalizada",
                    resposta=resposta,
                    finalizado_em=self.clock(),
                    plano=self._plano_compacto_checkpoint(plano),
                    _plano_avaliacao=plano,
                    avaliacao=self._avaliacao_mecanica(
                        plano,
                        respondeu=True,
                    ),
                    voz_observada=voz_observada,
                )
                self._anexar_conversa(
                    f"### Laylay\n\n{resposta}\n\n"
                    "> ⚠️ A voz não terminou dentro do limite; o próximo "
                    "comando não foi enviado.\n\n"
                )
                self.log(
                    f"⚠️ [ROTEIRO:{numero:03d}] voz não finalizada; "
                    "sequência interrompida com segurança"
                )
                sucesso_total = False
                break
            finalizado_em = self.clock()
            avaliacao = self._avaliacao_mecanica(plano, respondeu=True)
            self._anexar_plano_bruto(
                indice=indice,
                comando=comando,
                plano=plano,
            )
            self._atualizar_item(
                indice,
                status="respondido",
                resposta=resposta,
                finalizado_em=finalizado_em,
                plano=self._plano_compacto_checkpoint(plano),
                _plano_avaliacao=plano,
                avaliacao=avaliacao,
                voz_concluida=True,
                voz_observada=voz_observada,
                voz_silenciada=bool(
                    self.configuracao.silenciar_voz_durante_teste
                ),
                resultado_turno_concluido=resultado_turno_concluido,
                motivo_resultado=motivo_resultado,
                processamento_concluido=True,
            )
            bloco_plano = self._resumo_plano_markdown(plano)
            self._anexar_conversa(
                f"### Laylay\n\n{resposta}\n\n{bloco_plano}---\n\n"
            )
            estado_voz = (
                "voz desativada pelo roteiro"
                if self.configuracao.silenciar_voz_durante_teste
                else ("voz concluída" if voz_observada else "sem voz pendente")
            )
            self.log(
                (
                    f"⚠️ [ROTEIRO:{numero:03d}] resposta final sem contrato "
                    "operacional; falha registrada; avançando"
                    if motivo_resultado in {
                        "execucao_nao_publicada",
                        "contrato_operacional_incompleto",
                    }
                    else f"✅ [ROTEIRO:{numero:03d}] resposta e resultado salvos "
                    f"| resultado={motivo_resultado}; {estado_voz}; avançando"
                )
            )
            if self.configuracao.intervalo_comandos_s:
                self.sleep(self.configuracao.intervalo_comandos_s)
        with self._lock:
            self._indice_aguardado = None
            self._estado["concluido"] = bool(sucesso_total)
            self._estado["finalizado_em"] = self.clock()
            self._gravar_checkpoint()
        estado = "concluído" if sucesso_total else "interrompido"
        self._anexar_conversa(f"## Roteiro {estado}\n")
        # V32: RESUMO_SEMANTICO_FINAL
        # P0_DIAGNOSTICO_FINALIZACAO_ROTEIRO_V1_20260815
        registrar_evento_encerramento(
            self.diretorio, "relatorio_final_iniciado", componente="roteiro",
            sucesso=bool(sucesso_total),
        )
        try:
            resumo_semantico = gravar_relatorios_roteiro(
                self._estado,
                self.diretorio,
            )
            registrar_evento_encerramento(
                self.diretorio, "relatorio_final_concluido", componente="roteiro",
            )
            self.log(
                "📊 [ROTEIRO:RESUMO] "
                f"avaliados={resumo_semantico.get('avaliados_semanticamente')} | "
                f"passaram={resumo_semantico.get('passaram')} | "
                f"falharam={resumo_semantico.get('falharam')} | "
                f"alertas={resumo_semantico.get('alertas')} | "
                f"p95={(resumo_semantico.get('latencia_s') or {}).get('p95')}s"
            )
            registrar_evento_encerramento(
                self.diretorio, "resumo_impresso", componente="roteiro",
            )
        except Exception as erro:
            registrar_evento_encerramento(
                self.diretorio, "relatorio_final_falhou", componente="roteiro",
                erro_tipo=type(erro).__name__,
            )
            self.log(
                "⚠️ [ROTEIRO:RELATORIO] relatório final indisponível "
                f"| tipo={type(erro).__name__}"
            )

        registrar_evento_encerramento(
            self.diretorio, "log_final_iniciado", componente="roteiro",
        )
        self.log(
            f"🧪 [ROTEIRO] {estado} | conversa={self.conversa_path} "
            f"checkpoint={self.checkpoint_path}"
        )
        registrar_evento_encerramento(
            self.diretorio, "log_final_concluido", componente="roteiro",
        )
        if callable(self.ao_finalizar):
            registrar_evento_encerramento(
                self.diretorio, "callback_iniciado", componente="roteiro",
            )
            self.ao_finalizar(sucesso_total)
            registrar_evento_encerramento(
                self.diretorio, "callback_concluido", componente="roteiro",
            )
        return sucesso_total


def instalar_espelho_terminal(diretorio: str | os.PathLike[str]) -> tuple[Any, Any]:
    """Instala espelhos independentes para stdout e stderr."""

    pasta = Path(diretorio).resolve()
    pasta.mkdir(parents=True, exist_ok=True)
    saida = EspelhoTerminalPersistente(sys.stdout, pasta / "terminal.log")
    erro = EspelhoTerminalPersistente(sys.stderr, pasta / "terminal.log")
    sys.stdout, sys.stderr = saida, erro
    return saida, erro
