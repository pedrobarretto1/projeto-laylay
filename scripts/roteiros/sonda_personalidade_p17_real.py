"""Observa a coleta finita P17; não fabrica entrada, receipt ou decisão.

Inicia laylay.py com o roteiro canônico. Preserva retornos e exceções dos
owners; interrompe os próximos turnos na primeira fronteira RED. SQLite,
resumo e pessoas são próprios; não declara isolamento de todo estado.
Artefatos pessoais ficam em resultados_testes e não devem ser publicados.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
import argparse
import functools
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import threading
import time
from typing import Any, Mapping
from urllib.parse import urlsplit
import uuid

RAIZ = Path(__file__).resolve().parents[2]
ROTEIRO = RAIZ / "scripts/roteiros/roteiro_personalidade_p17_encerramento.py"
if __package__ in (None, ""):
    sys.path.insert(0, str(RAIZ))


def _copia(valor: Any) -> Any:
    def serializar(item: Any) -> Any:
        if is_dataclass(item):
            return asdict(item)
        raise TypeError(f"objeto sem representação observável: {type(item).__name__}")
    return json.loads(json.dumps(valor, ensure_ascii=False, default=serializar))


def _player_valido(player: Mapping[str, Any], *, agora: float) -> bool:
    return bool(
        player.get("video_id") and isinstance(player.get("tab_id"), int)
        and not isinstance(player.get("tab_id"), bool)
        and isinstance(player.get("repeat_enabled"), bool)
        and player.get("state") in {"playing", "paused"}
        and 0 <= agora - float(player.get("observed_at") or 0) <= 12
    )


def conferir_turno(
    numero: int, item: Mapping[str, Any], plano: Mapping[str, Any],
    registros: list[dict], antes: Mapping[str, Any], depois: Mapping[str, Any],
    anteriores: Mapping[int, Mapping[str, Any]],
    *, verificar_autoria: bool = True,
) -> None:
    """Asserções ordenadas por receipt → causa → autoria → efeito → fala."""
    from mente_laylay.personalidade.guarda_ataque_pessoal import contem_ataque_pessoal

    assert item.get("status") == "respondido", "turno sem conclusão textual"
    assert item.get("processamento_concluido") is True, "worker não concluiu"
    assert item.get("resultado_turno_concluido") is True, "resultado incompleto"
    comandos = list(plano.get("comandos") or [])
    locais = [r for r in registros if r.get("turno") == numero]
    publicacoes = [r for r in locais if r["etapa"] == "fala_publicada"]
    toggles = [r for r in locais if r["etapa"] == "chrome_entrada"
               and (r.get("payload") or {}).get("command") == "repeat_toggle"]
    fala = str(item.get("resposta") or "")
    assert fala and not contem_ataque_pessoal(fala), "fala ausente ou ataque pessoal"
    assert len(publicacoes) == 1, "turno precisa de uma publicação final"
    assert publicacoes[0]["mensagem_id"] == "turno:" + depois["turno_id"], "fala de outro turno"

    if numero in {1, 2, 3, 4, 5, 8}:
        assert len(comandos) == 1, "abertura precisa de um receipt único"
        receipt = comandos[0]
        assert receipt.get("intent") == "APP_OPEN", "intent de app divergente"
        assert receipt.get("origem") == "executor", "receipt não veio do executor"
        assert receipt.get("confirmado") is True, "app não confirmado"
        identidade = receipt.get("id_solicitacao")
        assert isinstance(identidade, str) and identidade, "receipt sem ocorrência"
        if numero != 1:
            assert receipt.get("status") == "ja_aberto_focado", "redundância não observada"
            avaliacoes = [r for r in locais if r["etapa"] == "evento"
                         and r["resultado"].get("id_solicitacao") == identidade]
            assert len(avaliacoes) == 1, "evento sem receipt da mesma ocorrência"
            evento = avaliacoes[0]["retorno"]
            assert evento.get("evidencia_ref") == identidade, "causa sem vínculo"
            assert evento.get("responsabilidade") == "usuario", "responsabilidade divergente"
            assert evento.get("natureza_evidencia") == "fato_observado", "causa inferida"
            if numero in {5, 8}:
                assert (evento.get("emocao"), evento.get("nivel")) == ("brava", 3), "bronca sem causa forte"
                estado = plano.get("estado_emocional_observado") or {}
                assert (estado.get("emocao"), estado.get("nivel")) == ("brava", 3), "causa não publicada"
                assert estado.get("episodio_evidencia_ref") == identidade, "publicação trocou ocorrência"
        if numero == 5 and verificar_autoria:
            # A preparação também pode ser redundante se o app já está em
            # foco. A prova pertence à causa forte, não a um número de turno.
            candidatos = {**anteriores, numero: {"item": item, "plano": plano, "depois": depois}}
            prova = None
            for n, candidato in candidatos.items():
                observado = candidato["plano"].get("estado_emocional_observado") or {}
                if (observado.get("emocao"), observado.get("nivel")) != ("brava", 3):
                    continue
                ident = candidato["plano"]["comandos"][0]["id_solicitacao"]
                aprovadas = [r for r in registros if r.get("turno") == n and r["etapa"] == "autoria"
                             and r["resultado"].get("id_solicitacao") == ident
                             and r["retorno"].get("usada_llm") is True]
                if aprovadas:
                    prova = (n, candidato, ident, aprovadas)
                    break
            assert prova, "bronca sem autoria LLM aprovada"
            n, candidato, ident, autorias = prova
            causal = [r["retorno"] for r in registros if r.get("turno") == n and r["etapa"] == "evento"
                      and r["resultado"].get("id_solicitacao") == ident]
            assert len(causal) == 1 and (causal[0].get("emocao"), causal[0].get("nivel")) == ("brava", 3), "amostra da autoria sem causa forte"
            assert candidato["plano"]["estado_emocional_observado"].get("episodio_evidencia_ref") == ident, "amostra da autoria perdeu ocorrência causal"
            assert len(autorias) == 1 and autorias[0]["retorno"].get("usada_llm") is True, "bronca sem autoria LLM aprovada"
            assert autorias[0]["retorno"]["fala"].strip() == candidato["item"]["resposta"].strip(), "fala entregue diverge da autoria"
            prova_locais = [r for r in registros if r.get("turno") == n]
            modelos = [r for r in prova_locais if r["etapa"] == "modelo_retorno" and r.get("ocorrencia") == ident]
            assert any(r["tipo"] == "autoria_operacional" and r["sucesso"] is True for r in modelos), "autoria sem geração correlacionada"
            ids = {r["chamada_id"] for r in modelos}
            orcamentos = [r["retorno"] for r in prova_locais if r["etapa"] == "orcamento"
                          and r.get("chamada_id") in ids and r["retorno"].get("permitida") is True]
            assert 1 <= len(orcamentos) <= 2, "geração excedeu orçamento de chamadas"
            assert all(r.get("turno_id") == candidato["depois"]["trace_id"] and
                       0 < float(r.get("timeout_s") or 0) <= 8 for r in orcamentos), "geração sem orçamento rápido do mesmo turno"
            http = [r for r in prova_locais if r["etapa"] == "http_retorno" and r.get("chamada_id") in ids]
            assert any(r["status"] == 200 and r["corpo"].get("choices") for r in http), "geração sem resposta real do backend"
        if numero == 5:
            assert _player_valido(depois.get("player") or {}, agora=time.time()), "player real sem estado fresco de repetição"

    if numero in {6, 9}:
        assert not toggles, "oferta executou antes de aceite"
        assert len(comandos) == 1 and comandos[0].get("status") == "aguardando_confirmacao", "adiamento não publicado no plano"
        assert comandos[0].get("origem") != "executor" and comandos[0].get("origem"), "adiamento atribuído ao executor"
        assert comandos[0].get("executou") is False and comandos[0].get("confirmado") is False, "adiamento promovido a efeito"
        assert item.get("motivo_resultado") == "aguardando_confirmacao_usuario", "barreira não reconheceu adiamento"
        assert _player_valido(antes.get("player") or {}, agora=item["enviado_em"]), "player inicial sem observação fresca"
        assert _player_valido(depois.get("player") or {}, agora=time.time()), "player da oferta sem observação fresca"
        pendencia = depois.get("pendencia") or {}
        assert pendencia.get("origem") == "resistencia_personalidade", "oferta não criou pendência canônica"
        assert pendencia.get("status") == "ativa", "oferta não está ativa"
        assert (pendencia.get("metadados") or {}).get("acao") == "repeat_toggle", "ação pendente divergente"
        anterior = anteriores[5 if numero == 6 else 8]
        identidade = anterior["plano"]["comandos"][0]["id_solicitacao"]
        assert (pendencia.get("metadados") or {}).get("evento_ref") == identidade, "oferta não usa nova causa"
        assert "?" in fala, "oferta sem pergunta observável"
        assert antes["player"]["repeat_enabled"] == depois["player"]["repeat_enabled"], "oferta alterou repetição"
        if numero == 9:
            assert pendencia.get("id") != anteriores[6]["depois"]["pendencia"]["id"], "oferta reutilizou ocorrência recusada"

    if numero == 7:
        assert not toggles, "recusa despachou efeito"
        assert _player_valido(depois.get("player") or {}, agora=time.time()), "recusa sem estado fresco do player"
        assert not depois.get("pendencia"), "recusa deixou oferta ativa"
        resolucoes = [r for r in locais if r["etapa"] == "pendencia_resolver"]
        assert any(r["retorno"].get("status") == "recusar" and
                   r["retorno"]["pendencia"]["id"] == anteriores[6]["depois"]["pendencia"]["id"]
                   for r in resolucoes), "recusa não resolveu a oferta certa"
        assert antes["player"]["repeat_enabled"] == depois["player"]["repeat_enabled"], "recusa alterou repetição"

    if numero in {10, 11}:
        from mente_laylay.memoria_mental.resultado_acao import normalizar_resultado_acao
        from mente_laylay.personalidade.confirmacao_llm import _motivo_contrato_invalido
        if numero == 10:
            assert antes.get("pendencia", {}).get("id") == anteriores[9]["depois"]["pendencia"]["id"], "aceite perdeu a oferta"
        assert len(toggles) == 1, "alternância exige um despacho"
        respostas = [r for r in locais if r["etapa"] == "chrome_retorno"
                     and (r.get("payload") or {}).get("command") == "repeat_toggle"]
        assert len(respostas) == 1, "alternância sem receipt de transporte único"
        receipt_chrome = respostas[0]["retorno"]
        assert receipt_chrome.get("ok") is True and receipt_chrome.get("confirmado") is True, "extensão não confirmou efeito"
        assert receipt_chrome.get("request_id"), "extensão sem requestId"
        assert len(comandos) == 1 and comandos[0].get("status") == "midia_repeat_toggle", "receipt operacional de mídia divergente"
        assert comandos[0].get("origem") == "executor" and comandos[0].get("confirmado") is True, "efeito não confirmado pelo executor"
        contrato = normalizar_resultado_acao(comandos[0])
        motivo = _motivo_contrato_invalido(
            fala, resultado=contrato, classe="sucesso",
            status_declarado=contrato.status, alvo_declarado=contrato.alvo,
        )
        assert not motivo, "fala de mídia viola receipt: " + motivo
        assert not depois.get("pendencia"), "aceite não concluiu pendência"
        p0, p1 = antes["player"], depois["player"]
        assert _player_valido(p1, agora=time.time()), "player final sem observação fresca"
        assert (p0["video_id"], p0["tab_id"]) == (p1["video_id"], p1["tab_id"]), "alternância mudou alvo"
        assert p1["observed_at"] >= respostas[0]["iniciado_em"], "observação anterior ao efeito"
        assert p0["repeat_enabled"] is not p1["repeat_enabled"], "repetição não mudou no player"
        assert p0["state"] == p1["state"], "alternância mudou reprodução/pausa"
        if numero == 11:
            assert p1["repeat_enabled"] == anteriores[9]["antes"]["player"]["repeat_enabled"], "estado original não restaurado"

    assert item.get("voz_silenciada") is False, "voz silenciada na coleta física"
    assert item.get("voz_observada") is True and item.get("voz_concluida") is True, "voz não observada/concluída no software"
    nascimentos = [r for r in locais if r["etapa"] == "trace_iniciado"]
    assert len(nascimentos) == 1 and nascimentos[0]["retorno"].get("turno_id") == depois["trace_id"], "telemetria sem nascimento deste turno"
    traces = [r for r in depois.get("traces") or [] if r.get("turno_id") == depois["trace_id"]]
    assert len(traces) == 1 and (traces[0].get("etapas", {}).get("tts_total") or {}).get("sucesso") is True, "TTS desta fala sem sucesso observado"
    assert (item.get("avaliacao") or {}).get("resultado_semantico") != "falhou", "avaliador canônico manteve RED: " + str((item.get("avaliacao") or {}).get("erros_semanticos"))


class ObservacaoP17:
    def __init__(self, pasta: Path, *, somente_politica: bool = False) -> None:
        self.pasta = pasta
        self.registros: list[dict] = []
        self.turnos: dict[int, dict] = {}
        self.erros: list[str] = []
        self.restauracoes: list[tuple[Any, str, Any]] = []
        self.lock = threading.RLock()
        self.local = threading.local()
        self.turno = 0
        self.antes: dict = {}
        self.primeiro_red: dict = {}
        self.traces: dict[int, str] = {}
        self.somente_politica = somente_politica

    def registrar(self, etapa: str, **campos: Any) -> None:
        try:
            registro = _copia(dict(etapa=etapa, turno=self.turno, ts=time.time(), **campos))
            with self.lock:
                self.registros.append(registro)
                with (self.pasta / "observacoes.jsonl").open("a", encoding="utf-8") as arq:
                    arq.write(json.dumps(registro, ensure_ascii=False) + "\n")
        except Exception as erro:
            self.erros.append(f"{etapa}:{type(erro).__name__}")

    def substituir(self, owner: Any, nome: str, criar: Any) -> None:
        original = getattr(owner, nome)
        setattr(owner, nome, functools.wraps(original)(criar(original)))
        self.restauracoes.append((owner, nome, original))

    def estado(self, runtime: Any) -> dict:
        namespace = runtime.resultado_getter.__globals__
        snapshot = namespace["_estado_compartilhado_runtime"].snapshot()
        conversa = snapshot["conversacional"]
        pendencia = snapshot["mental"].get("pendencia_acao_canonica") or {}
        player = (snapshot["musical"].get("playlist_state") or {}).get("player") or {}
        return _copia({"player": player,
                       "pendencia": pendencia,
                       "turno_id": str((snapshot["mental"].get("turno_atual") or {}).get("id") or ""),
                       "trace_id": self.traces.get(self.turno, ""),
                       "traces": snapshot["mental"].get("diagnostico_traces_turno") or [],
                       "episodio": conversa.get("episodio_emocional") or {}})

    def instalar(self) -> None:
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
        from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
        from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime
        from mente_laylay.memoria_mental.observabilidade import ObservabilidadeMenteRuntime
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM
        from mente_laylay.integracao.orcamento_llm_turno import OrcamentoLLMTurnoRuntime
        from mente_laylay.integracao.chrome_comandos import ChromeComandosRuntime
        from mente_laylay.integracao.roteiro_teste_conversa import RoteiroTesteConversaRuntime
        from mente_laylay.emocoes.avaliador_eventos import AvaliadorEventosEmocionaisRuntime
        from mente_laylay.personalidade import confirmacao_llm
        import requests

        sqlite = self.pasta / "sqlite_proprio"
        sqlite.mkdir()

        def memoria(original):
            def iniciar(obj, db_path=None):
                return original(obj, str(sqlite / Path(db_path or "laylay_memoria.sqlite").name))
            return iniciar

        def resumo(original):
            def iniciar(obj, *, pasta_memoria, **opcoes):
                return original(obj, pasta_memoria=str(self.pasta / "resumo_proprio"), **opcoes)
            return iniciar

        def pessoas(original):
            def iniciar(obj, *, caminho, **opcoes):
                return original(obj, caminho=self.pasta / "pessoas_proprias.json", **opcoes)
            return iniciar

        def modelo(original):
            def executar(obj, pedido):
                if getattr(self.local, "chamada", None):
                    return original(obj, pedido)
                identidade = uuid.uuid4().hex
                self.local.chamada = identidade
                inicio = time.time()
                self.registrar("modelo_entrada", chamada_id=identidade, tipo=pedido.tipo_chamada,
                               ocorrencia=getattr(self.local, "ocorrencia", ""))
                try:
                    retorno = original(obj, pedido)
                    self.registrar("modelo_retorno", chamada_id=identidade, tipo=pedido.tipo_chamada,
                                   ocorrencia=getattr(self.local, "ocorrencia", ""),
                                   duracao_s=time.time() - inicio, sucesso=retorno.sucesso, texto=retorno.texto)
                    return retorno
                finally:
                    self.local.chamada = None
            return executar

        def autoria(original):
            def chamar(resultado, fala_segura, **opcoes):
                anterior = getattr(self.local, "ocorrencia", "")
                self.local.ocorrencia = resultado.id_solicitacao
                try:
                    retorno = original(resultado, fala_segura, **opcoes)
                finally:
                    self.local.ocorrencia = anterior
                self.registrar("autoria", resultado=resultado.como_dict(),
                               evento=(opcoes.get("contexto") or {}).get("avaliacao_evento"),
                               retorno=retorno)
                return retorno
            return chamar

        def orcamento(original):
            def autorizar(obj, **opcoes):
                retorno = original(obj, **opcoes)
                self.registrar("orcamento", chamada_id=getattr(self.local, "chamada", None), retorno=retorno)
                return retorno
            return autorizar

        def trace(original):
            def iniciar(obj, *args, **opcoes):
                retorno = original(obj, *args, **opcoes)
                self.traces[self.turno] = str(retorno.get("turno_id") or "")
                self.registrar("trace_iniciado", retorno=retorno)
                return retorno
            return iniciar

        def http(original):
            def enviar(url, *args, **opcoes):
                chamada = getattr(self.local, "chamada", None)
                payload = opcoes.get("json") or {}
                captura = chamada and isinstance(payload, dict) and "messages" in payload
                if captura:
                    self.registrar("http_entrada", chamada_id=chamada, hostname=urlsplit(str(url)).hostname,
                                   modelo=payload.get("model"), timeout=opcoes.get("timeout"))
                retorno = original(url, *args, **opcoes)
                if captura:
                    try:
                        corpo = retorno.json()
                    except ValueError:
                        corpo = {"texto": retorno.text}
                    self.registrar("http_retorno", chamada_id=chamada, status=retorno.status_code, corpo=corpo)
                return retorno
            return enviar

        def fala_publicada(original):
            def observar(obj, texto, emocao="calma", nivel=1, **dados):
                retorno = original(obj, texto, emocao, nivel, **dados)
                if not dados.get("proativa"):
                    self.registrar("fala_publicada", texto=texto, emocao=emocao, nivel=nivel,
                                   mensagem_id=dados.get("mensagem_id"), observada=retorno)
                return retorno
            return observar

        def evento(original):
            def avaliar(obj, resultado):
                retorno = original(obj, resultado)
                self.registrar("evento", resultado=resultado.como_dict(), retorno=retorno)
                return retorno
            return avaliar

        def chrome(original):
            def enviar(obj, action=None, payload=None):
                inicio = time.time()
                self.registrar("chrome_entrada", action=action, payload=payload)
                retorno = original(obj, action, payload)
                self.registrar("chrome_retorno", action=action, payload=payload,
                               iniciado_em=inicio, retorno=retorno)
                return retorno
            return enviar

        def pendencia(nome):
            def criar(original):
                def chamar(obj, *args, **opcoes):
                    retorno = original(obj, *args, **opcoes)
                    self.registrar("pendencia_" + nome, retorno=retorno, args=args,
                                   id_esperado=opcoes.get("id_esperado"))
                    return retorno
                return chamar
            return criar

        def atualizar(original):
            def chamar(obj, indice, **campos):
                if campos.get("status") == "enviado":
                    self.turno = indice + 1
                    try:
                        self.antes = self.estado(obj)
                    except Exception as erro:
                        self.antes = {}
                        self.erros.append(f"estado_inicial:{type(erro).__name__}")
                retorno = original(obj, indice, **campos)
                if campos.get("status") not in {"respondido", "sem_resposta", "erro_envio",
                                               "processamento_nao_finalizado", "resultado_nao_finalizado",
                                               "voz_nao_finalizada"}:
                    return retorno
                numero = indice + 1
                item = obj._item(indice)
                plano = campos.get("_plano_avaliacao") or obj._plano_atual()
                try:
                    depois = self.estado(obj)
                    assert not self.erros, "observação incompleta: " + str(self.erros)
                    conferir_turno(numero, item, plano, self.registros,
                                   self.antes, depois, self.turnos,
                                   verificar_autoria=not self.somente_politica)
                    veredito = "GREEN_SOFTWARE"
                except Exception as erro:
                    depois = locals().get("depois", {})
                    veredito = "RED"
                    self.primeiro_red = {"turno": numero, "motivo": str(erro), "tipo": type(erro).__name__}
                    obj.parar()
                self.turnos[numero] = _copia(dict(item=item, plano=plano, antes=self.antes,
                                                depois=depois, veredito=veredito))
                self.registrar("turno_final", numero=numero, **self.turnos[numero])
                print(f"P17_FRONTEIRA turno={numero} {veredito} {self.primeiro_red}", flush=True)
                return retorno
            return chamar

        self.substituir(MemoriaSQLite, "__init__", memoria)
        self.substituir(MemoriaLaylay, "__init__", resumo)
        self.substituir(MemoriaPessoasRuntime, "__init__", pessoas)
        self.substituir(RegistroModeloLLM, "executar", modelo)
        self.substituir(OrcamentoLLMTurnoRuntime, "autorizar_chamada", orcamento)
        self.substituir(ObservabilidadeMenteRuntime, "iniciar_trace_turno", trace)
        self.substituir(requests, "post", http)
        self.substituir(confirmacao_llm, "personalizar_confirmacao_llm", autoria)
        # Cobrir os imports vinculados antes da instalação, sem observar duas vezes.
        from mente_laylay.autonomia import adaptador_resultado, controle_midia
        for modulo in (adaptador_resultado, controle_midia):
            original = modulo.personalizar_confirmacao_llm
            modulo.personalizar_confirmacao_llm = confirmacao_llm.personalizar_confirmacao_llm
            self.restauracoes.append((modulo, "personalizar_confirmacao_llm", original))
        self.substituir(AvaliadorEventosEmocionaisRuntime, "avaliar", evento)
        self.substituir(ChromeComandosRuntime, "enviar_detalhado", chrome)
        for nome in ("registrar", "resolver", "concluir"):
            self.substituir(PendenciaAcaoRuntime, nome, pendencia(nome))
        self.substituir(RoteiroTesteConversaRuntime, "_atualizar_item", atualizar)
        self.substituir(RoteiroTesteConversaRuntime, "observar_resposta", fala_publicada)

    def restaurar(self) -> None:
        for owner, nome, original in reversed(self.restauracoes):
            setattr(owner, nome, original)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--somente-politica", action="store_true",
                        help="aferir efeito/continuidade; exige prova de autoria separada para encerrar P17")
    opcoes = parser.parse_args()
    from mente_laylay.integracao.instancia_unica import adquirir_instancia_unica
    trava = adquirir_instancia_unica(RAIZ / "laylay.py")
    if not trava.adquirida:
        print("P17 não iniciada: encerre normalmente a sessão atual da Laylay.", flush=True)
        return 73
    trava.liberar()
    pasta = RAIZ / "resultados_testes" / ("p17_real_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    pasta.mkdir(parents=True, exist_ok=False)
    baseline = {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=RAIZ, text=True).strip(),
        "status": subprocess.check_output(["git", "status", "--short"], cwd=RAIZ, text=True),
        "roteiro_sha256": hashlib.sha256(ROTEIRO.read_bytes()).hexdigest(),
        "sonda_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "escopo": "APP_OPEN e repeat_toggle reais; modelo e voz reais; audição humana pendente",
        "autoria_exigida_no_veredito": not opcoes.somente_politica,
        "isolamento": "SQLite, resumo e pessoas próprios; demais estado e executores reais",
    }
    (pasta / "baseline.json").write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")
    ambiente = {
        "GMAIL_USER": " ", "GMAIL_APP_PASSWORD": " ",
        "LAYLAY_IOT_MODO": "simulado", "IOT_CONTROLE_FISICO_AUTORIZADO": "NAO",
        "LAYLAY_TERMINAL_2": "0", "LAYLAY_MICROFONE_ATIVO": "0",
        "LAYLAY_BRIEFING_INICIAL": "0", "LAYLAY_FALAS_INICIAIS": "0",
        "LAYLAY_PRESENCA": "0", "LAYLAY_MODO_JOGO_AUTO": "0",
        "LAYLAY_MASCOT_ENABLED": "0", "LAYLAY_AVATAR_ATIVO": "0",
    }
    anteriores = {k: os.environ.get(k) for k in ambiente}
    argumentos = sys.argv[:]
    observacao = ObservacaoP17(pasta, somente_politica=opcoes.somente_politica)
    codigo = 0
    print("P17_CAPTURA_LOCAL:", pasta, flush=True)
    try:
        os.environ.update(ambiente)
        observacao.instalar()
        sys.argv = [str(RAIZ / "laylay.py"), "--roteiro", str(ROTEIRO),
                    "--resultado-raiz", str(pasta / "runtime")]
        runpy.run_path(str(RAIZ / "laylay.py"), run_name="__main__")
    except SystemExit as erro:
        codigo = erro.code if isinstance(erro.code, int) else 1
    except BaseException:
        codigo = 1
        raise
    finally:
        observacao.restaurar()
        sys.argv = argumentos
        for chave, valor in anteriores.items():
            if valor is None:
                os.environ.pop(chave, None)
            else:
                os.environ[chave] = valor
        green = len(observacao.turnos) == 11 and not observacao.primeiro_red and not observacao.erros and codigo == 0
        resumo = {"codigo_saida": codigo, "turnos_concluidos": len(observacao.turnos),
                  "primeiro_red": observacao.primeiro_red, "erros_observacao": observacao.erros,
                  "software": ("GREEN_POLITICA" if opcoes.somente_politica else "GREEN") if green else "INCOMPLETO_OU_RED",
                  "autoria": "exige_prova_separada" if opcoes.somente_politica else "aferida_no_roteiro" if green else "incompleta",
                  "audicao_fisica": "aguardando_confirmacao_humana",
                  "estado_original_restaurado": green}
        (pasta / "veredito.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
        print("P17_VEREDITO:", json.dumps(resumo, ensure_ascii=False), flush=True)
    return codigo or (0 if green else 1)


if __name__ == "__main__":
    raise SystemExit(main())
