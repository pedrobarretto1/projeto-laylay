"""Diagnóstico local: captura o payload real sem alterar decisões ou respostas.

Artefatos podem conter contexto pessoal; ficam em resultados_testes, não publicar.
"""
from pathlib import Path
from datetime import datetime
import json
import os
import runpy
import sys
import threading
import argparse
import functools
import hashlib
import time
import uuid
import subprocess
from collections import Counter
from dataclasses import asdict, is_dataclass
from urllib.parse import urlsplit
import requests

# A sonda pode ser iniciada diretamente, inclusive fora da raiz do projeto.
RAIZ_PROJETO = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(RAIZ_PROJETO))


def _instalar_observacao_p16(
    pasta: Path, chamada: threading.local, *, isolar_pessoas: bool = False,
) -> list:
    """Observa os objetos instalados; não fornece proposta, prova ou receipt."""
    from memoria_sqlite import MemoriaSQLite
    from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
    from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
    from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM
    from mente_laylay.cognicao.decisao_turno import ValidadorComandosTurnoRuntime
    from mente_laylay.cognicao.composicao_turno import ComposicaoTurnoRuntime
    from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime
    from mente_laylay.iot.runtime import RuntimeIoT
    from mente_laylay.autonomia import dispatcher_comandos_json, finalizacao_execucao_ia

    restauracoes = []
    lock = threading.Lock()
    sqlite = pasta / "sqlite_proprio"
    sqlite.mkdir(exist_ok=False)

    def registrar(etapa, **campos):
        # Uma falha de observação deixa a coleta incompleta, sem alterar o turno.
        try:
            linha = json.dumps(dict(etapa=etapa, ts=time.time(),
                thread=threading.current_thread().name, **campos), ensure_ascii=False,
                default=lambda valor: asdict(valor) if is_dataclass(valor) else str(type(valor)))
            with lock, (pasta / "p16.jsonl").open("a", encoding="utf-8") as arquivo:
                arquivo.write(linha + "\n")
        except (OSError, TypeError, ValueError):
            pass

    def substituir(owner, nome, criar):
        original = getattr(owner, nome)
        setattr(owner, nome, functools.wraps(original)(criar(original)))
        restauracoes.append((owner, nome, original))

    def memoria(original):
        def iniciar(self, db_path=None):
            alvo = sqlite / Path(db_path or "laylay_memoria.sqlite").name
            retorno = original(self, str(alvo))
            registrar("sqlite_proprio", caminho=str(alvo))
            return retorno
        return iniciar

    def resumo_diario(original):
        def iniciar(self, *, pasta_memoria, **opcoes):
            retorno = original(self, pasta_memoria=str(pasta / "resumo_proprio"), **opcoes)
            registrar("resumo_proprio", caminho=self.arquivo_diario)
            return retorno
        return iniciar

    def pessoas(original):
        def iniciar(self, *, caminho, **opcoes):
            retorno = original(self, caminho=pasta / "pessoas_proprias.json", **opcoes)
            registrar("pessoas_proprias", caminho=str(self.caminho))
            return retorno
        return iniciar

    def observar_pessoas(original):
        def ler(self):
            try:
                conteudo = self.caminho.read_bytes()
                return hashlib.sha256(conteudo).hexdigest(), json.loads(conteudo)
            except (OSError, ValueError):
                return None, None

        def processar(self, texto):
            antes, _ = ler(self)
            retorno = original(self, texto)
            depois, dados = ler(self)
            registrar("pessoas_observacao", texto=texto, tratado=retorno,
                antes_sha256=antes, depois_sha256=depois, dados=dados)
            return retorno
        return processar

    def modelo(original):
        def executar(self, pedido):
            # O registro diferido delega a outro RegistroModeloLLM. Ambos usam
            # o mesmo pedido; apenas a chamada externa representa uma geração.
            if getattr(chamada, "id", None):
                return original(self, pedido)
            identificador = uuid.uuid4().hex
            chamada.id = identificador
            registrar("modelo_entrada", chamada_id=identificador,
                tipo_chamada=pedido.tipo_chamada, pedido_objeto=id(pedido))
            try:
                resultado = original(self, pedido)
                registrar("modelo_retorno", chamada_id=identificador,
                    tipo_chamada=pedido.tipo_chamada, sucesso=resultado.sucesso,
                    texto=resultado.texto)
                if pedido.tipo_chamada == "principal":
                    chamada.ultima_principal = identificador
                return resultado
            except BaseException as erro:
                registrar("modelo_excecao", chamada_id=identificador, erro_tipo=type(erro).__name__)
                raise
            finally:
                chamada.id = None
        return executar

    def validar(original):
        def conferir(self, comandos, principal, extracao):
            mental = self._estado_runtime.snapshot()["mental"]
            retorno = original(self, comandos, principal, extracao)
            registrar("validacao_original", chamada_id=getattr(chamada, "ultima_principal", None),
                principal_objeto=id(principal), extracao_objeto=id(extracao),
                principal=principal, extracao=extracao,
                frame={nome: mental.get(nome) for nome in (
                    "turno_atual", "plano_turno_atual", "retrato_turno_atual")},
                comandos_recebidos=comandos, resultado=retorno)
            return retorno
        return conferir

    def publicar(original):
        def chamar(self, prova, principal, extracao, **opcoes):
            retorno = original(self, prova, principal, extracao, **opcoes)
            snapshot = self._estado().snapshot()
            registrar("publicacao_erro", principal_objeto=id(principal), extracao_objeto=id(extracao),
                prova=prova, principal=principal, evento=retorno,
                plano=snapshot["mental"].get("plano_turno_atual"),
                episodio=snapshot["conversacional"].get("episodio_emocional"))
            return retorno
        return chamar

    def leitura_semantica(original):
        def chamar(self, texto, leitura, principal):
            estado = self._servicos['_estado_compartilhado_runtime']
            try:
                antes = estado.snapshot()
            except Exception:
                antes = {}
            retorno = original(self, texto, leitura, principal)
            try:
                depois = estado.snapshot()
                campos = ("current_emotion", "emotion_level", "episodio_emocional")
                registrar("publicacao_leitura", chamada_id=getattr(chamada, "ultima_principal", None),
                    principal=principal, leitura_recebida=leitura, leitura_publicada=retorno,
                    evento_antes=(antes["mental"].get("plano_turno_atual") or {}).get("evento_emocional_causal"),
                    frame={nome: depois["mental"].get(nome) for nome in (
                        "turno_atual", "plano_turno_atual", "retrato_turno_atual")},
                    conversacional_antes={nome: antes["conversacional"].get(nome) for nome in campos},
                    conversacional_depois={nome: depois["conversacional"].get(nome) for nome in campos})
            except Exception as erro:
                registrar("observacao_leitura_incompleta", erro_tipo=type(erro).__name__)
            return retorno
        return chamar

    def confirmar(original):
        def chamar(self, prova, principal, extracao, evento, **opcoes):
            retorno = original(self, prova, principal, extracao, evento, **opcoes)
            registrar("confirmacao_erro", principal_objeto=id(principal), extracao_objeto=id(extracao),
                principal=principal, prova=prova, evento=evento, confirmado=retorno)
            return retorno
        return chamar

    def finalizar(original):
        def chamar(ctx, *args, **kwargs):
            retorno = original(ctx, *args, **kwargs)
            fonte = ctx.get("erro_proposta_confirmado") or {}
            registrar("finalizacao", principal_objeto=id(fonte.get("principal")),
                comandos=args[0] if args else kwargs.get("comandos"),
                erro_confirmado=bool(fonte), resultado=retorno)
            return retorno
        return chamar

    def despachar(original):
        def chamar(ctx, texto, comandos, *args, **kwargs):
            retorno = original(ctx, texto, comandos, *args, **kwargs)
            registrar("dispatcher", comandos=comandos, resultado=retorno)
            return retorno
        return chamar

    def iot(original):
        def executar(self, *args, **kwargs):
            registrar("executor_iot_entrada", modo=self.modo)
            retorno = original(self, *args, **kwargs)
            registrar("executor_iot_retorno", modo=self.modo, resultado=retorno)
            return retorno
        return executar

    substituir(MemoriaSQLite, "__init__", memoria)
    substituir(MemoriaLaylay, "__init__", resumo_diario)
    if isolar_pessoas:
        substituir(MemoriaPessoasRuntime, "__init__", pessoas)
        substituir(MemoriaPessoasRuntime, "processar", observar_pessoas)
    substituir(RegistroModeloLLM, "executar", modelo)
    substituir(ValidadorComandosTurnoRuntime, "validar_proposta_original", validar)
    substituir(ComposicaoTurnoRuntime, "registrar_leitura_proposta", leitura_semantica)
    substituir(EstadoContextoRuntime, "publicar_erro_proposta", publicar)
    substituir(EstadoContextoRuntime, "confirmar_erro_proposta", confirmar)
    substituir(finalizacao_execucao_ia, "finalizar_execucao_resposta_ia", finalizar)
    substituir(dispatcher_comandos_json, "executar_comandos_json", despachar)
    substituir(RuntimeIoT, "executar", iot)
    return restauracoes


def _gravar_resumo_p16(pasta: Path, codigo_saida: int | str) -> dict:
    """Separa coleta e prova: ausência de geração válida nunca recebe GREEN."""
    registros = [json.loads(linha) for linha in (pasta / "p16.jsonl").read_text(
        encoding="utf-8").splitlines() if linha.strip()]
    validacoes = [item for item in registros if item["etapa"] == "validacao_original"]
    fontes = Counter(item["principal"]["estado"] for item in validacoes)
    resumo = {
        "status": ("coleta_disponivel_para_auditoria" if fontes.get("recebida")
                   else "fonte_tecnica_insuficiente" if validacoes
                   else "coleta_incompleta"),
        "codigo_saida": codigo_saida,
        "etapas": dict(Counter(item["etapa"] for item in registros)),
        "fontes_originais": dict(fontes),
        "violacoes_observadas": sum(len(item["resultado"]["violacoes_proposta_original"])
                                   for item in validacoes),
        "comandos_no_dispatcher": sum(len(item["comandos"]) for item in registros
                                      if item["etapa"] == "dispatcher"),
        "positivo_p16_status": "pendente_auditoria" if fontes.get("recebida") else "nao_comprovado",
        "limite": "O placar mínimo do roteiro não comprova autoria, efeito físico ou conclusão da P16.",
    }
    (pasta / "coleta_p16.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    return resumo


def main() -> None:
    raiz = RAIZ_PROJETO
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roteiro", choices=(
        "roteiro_p0_leitura_sem_autorizacao.py", "roteiro_fonte_textual_ausente.py",
        "roteiro_neural_dialogo_controlado_50_v1.py",
        "roteiro_transformacao_conversacional.py",
        "roteiro_recomendacao_contextual.py",
        "roteiro_site_por_assunto.py",
        "roteiro_reparo_parcial_conversa.py",
        "roteiro_ensino_divisao.py",
        "roteiro_ensino_multidominio.py",
        "roteiro_ensino_cenario_sensor_sombra.py",
        "roteiro_confirmacoes_recusas.py",
        "roteiro_recusas_autoria.py",
        "roteiro_explicacao_capacidades.py",
        "roteiro_iot_explicacoes.py",
        "roteiro_personalidade_p16_vetos_iot.py",
        "roteiro_personalidade_p16_voz_avatar.py",
        "roteiro_personalidade_p16_relato_temporal.py",
        "roteiro_memoria_pessoas_identidade.py",
    ), default="roteiro_p0_leitura_sem_autorizacao.py")
    parser.add_argument("--capturar-chrome", action="store_true",
                        help="Registra o retorno detalhado real, sem alterar o comando ou recibo")
    parser.add_argument("--capturar-preparacao", action="store_true",
                        help="Compara o pedido e o payload preparado com o envio HTTP real")
    parser.add_argument("--capturar-p16", action="store_true",
                        help="Observa a fonte original nos controles P16 permitidos, com persistência própria e sem replay")
    parser.add_argument("--isolar-pessoas", action="store_true",
                        help="Com captura P16, conserva o serviço real com um arquivo de pessoas próprio da coleta")
    parser.add_argument("--replay-captura", type=Path,
                        help="Reapresenta uma resposta HTTP gravada; NÃO é geração real nesse turno")
    parser.add_argument("--replay-texto",
                        help="Entrada exata com uma única resposta na captura; exige --replay-captura")
    parser.add_argument("--falhas-controladas", action="store_true",
                        help="Injeta timeout/conexão/ocupação uma vez em perguntas da sonda de capacidades; não são falhas espontâneas")
    parser.add_argument("--reparo-vazio", action="store_true",
                        help="Com replay, substitui o primeiro reparo desse pedido por {}; orçamento real permanece intacto")
    argumentos = parser.parse_args()
    if argumentos.roteiro == "roteiro_memoria_pessoas_identidade.py" and not argumentos.isolar_pessoas:
        parser.error("roteiro de identidade exige --capturar-p16 --isolar-pessoas")
    if argumentos.isolar_pessoas and not argumentos.capturar_p16:
        parser.error("isolamento de pessoas exige captura P16")
    if bool(argumentos.replay_captura) != bool(argumentos.replay_texto):
        parser.error("replay exige captura e texto juntos")
    if argumentos.reparo_vazio and not argumentos.replay_captura:
        parser.error("reparo vazio exige replay explícito")
    if argumentos.falhas_controladas and (argumentos.replay_captura or argumentos.roteiro != "roteiro_explicacao_capacidades.py"):
        parser.error("falhas controladas exigem roteiro de capacidades sem replay")
    if argumentos.capturar_p16 and (argumentos.replay_captura or argumentos.falhas_controladas
                                   or argumentos.roteiro not in {
                                       "roteiro_iot_explicacoes.py",
                                       "roteiro_personalidade_p16_vetos_iot.py",
                                       "roteiro_personalidade_p16_voz_avatar.py",
                                       "roteiro_personalidade_p16_relato_temporal.py",
                                       "roteiro_memoria_pessoas_identidade.py",
                                   }):
        parser.error("captura P16 exige roteiro permitido sem replay ou falhas injetadas")
    replay_resposta = None
    if argumentos.replay_captura:
        origem_replay = argumentos.replay_captura.resolve(strict=True)
        if not origem_replay.is_relative_to((raiz / "resultados_testes").resolve()):
            parser.error("a captura de replay precisa estar em resultados_testes")
        candidatas, alvo_replay = [], False
        for linha in origem_replay.read_text(encoding="utf-8").splitlines():
            evento = json.loads(linha)
            if evento.get("etapa") == "envio":
                usuario = next((m.get("content") for m in reversed(evento["payload"]["messages"])
                                if m.get("role") == "user"), "")
                alvo_replay = usuario == argumentos.replay_texto
            elif evento.get("etapa") == "resposta" and alvo_replay:
                if evento.get("status") == 200:
                    candidatas.append(evento["texto"])
                alvo_replay = False
        if len(candidatas) != 1:
            parser.error("replay exige exatamente uma resposta HTTP 200 para a entrada")
        replay_resposta = candidatas[0]
        json.loads(replay_resposta)  # aborta captura inválida antes de abrir a Laylay
    roteiro = argumentos.roteiro
    voz_avatar_p16 = argumentos.capturar_p16 and roteiro == "roteiro_personalidade_p16_voz_avatar.py"
    pasta = raiz / "resultados_testes" / ("transporte_evidencia-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    pasta.mkdir(parents=True, exist_ok=False)
    if argumentos.capturar_p16:
        (pasta / "baseline_p16.json").write_text(json.dumps({
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=raiz, text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=raiz, text=True).strip(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "replay": False, "falha_injetada": False, "sqlite_proprio": True,
            "resumo_diario_proprio": True,
            "pessoas_proprias": argumentos.isolar_pessoas,
            "voz_avatar_habilitados": voz_avatar_p16,
            "limite_isolamento": ("SQLite, resumo diário e pessoas próprios; "
                if argumentos.isolar_pessoas else "SQLite e resumo diário próprios; ")
                + "não declara isolamento de todo estado do runtime.",
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    for chave, valor in {
        "GMAIL_USER": " ", "GMAIL_APP_PASSWORD": " ",
        "LAYLAY_IOT_MODO": "simulado", "LAYLAY_TERMINAL_2": "0",
        "LAYLAY_MICROFONE_ATIVO": "0", "LAYLAY_BRIEFING_INICIAL": "0",
        "LAYLAY_FALAS_INICIAIS": "0", "LAYLAY_PRESENCA": "0",
        "LAYLAY_MODO_JOGO_AUTO": "0", "LAYLAY_LOG_VERBOSE": "1",
    }.items():
        os.environ[chave] = valor
    if roteiro == "roteiro_ensino_cenario_sensor_sombra.py":
        os.environ["LAYLAY_CENARIO_DIDATICO_DEBUG"] = "1"
        os.environ["LAYLAY_AUDITORIA_ENSINO_SOMBRA_DEBUG"] = "1"
    original = requests.post
    lock = threading.Lock()
    chamada = threading.local()
    restauracoes_p16 = _instalar_observacao_p16(
        pasta, chamada, isolar_pessoas=argumentos.isolar_pessoas,
    ) if argumentos.capturar_p16 else []
    replay_usado = False
    reparo_vazio_usado = False
    falhas_pendentes = {
        "como eu poderia pausar a música?": "timeout",
        "como eu poderia retomar a música?": "conexao",
        "como eu poderia abrir a calculadora?": "ocupacao",
    } if argumentos.falhas_controladas else {}

    def observar(url, *args, **kwargs):
        nonlocal replay_usado, reparo_vazio_usado
        dados = kwargs.get("json")
        captura = isinstance(dados, dict) and "messages" in dados
        if captura and urlsplit(str(url)).hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise RuntimeError("Sonda permitida somente com modelo local")
        if captura:
            with lock, (pasta / "transporte.jsonl").open("a", encoding="utf-8") as arquivo:
                arquivo.write(json.dumps({"etapa": "envio", "payload": dados,
                    **({"chamada_id": getattr(chamada, "id", None)} if argumentos.capturar_p16 else {})}, ensure_ascii=False) + "\n")
        usuario = next((m.get("content") for m in reversed(dados["messages"])
                        if m.get("role") == "user"), "") if captura else ""
        injetar_vazio = False
        if argumentos.reparo_vazio and replay_usado and not reparo_vazio_usado:
            try:
                pedido_reparo = json.loads(usuario)
            except (TypeError, ValueError):
                pedido_reparo = {}
            if (isinstance(pedido_reparo, dict)
                    and pedido_reparo.get("mensagem_atual") == argumentos.replay_texto
                    and pedido_reparo.get("contrato_de_reparo")):
                reparo_vazio_usado = injetar_vazio = True
                with lock, (pasta / "transporte.jsonl").open("a", encoding="utf-8") as arquivo:
                    arquivo.write(json.dumps({"etapa": "reparo_vazio_injetado", "geracao_real": False}) + "\n")
        with lock:
            falha_injetada = falhas_pendentes.pop(usuario, "")
            if falha_injetada:
                with (pasta / "transporte.jsonl").open("a", encoding="utf-8") as arquivo:
                    arquivo.write(json.dumps({"etapa": "falha_injetada", "categoria": falha_injetada,
                                              "texto_usuario": usuario, "espontanea": False}, ensure_ascii=False) + "\n")
        if falha_injetada == "timeout":
            raise requests.exceptions.ReadTimeout("Sonda F3: timeout controlado")
        if falha_injetada == "conexao":
            raise requests.exceptions.ConnectionError("Sonda F3: conexão controlada")
        if falha_injetada == "ocupacao":
            resposta = requests.Response()
            resposta.status_code = 200
            resposta._content = json.dumps({"choices": [{"message": {"content": "__LAYLAY_LLM_OCUPADA__"}}]}).encode("utf-8")
            resposta.encoding = "utf-8"
            return resposta
        usar_replay = False
        if replay_resposta and usuario == argumentos.replay_texto:
            with lock:
                if not replay_usado:
                    replay_usado, usar_replay = True, True
                    with (pasta / "transporte.jsonl").open("a", encoding="utf-8") as arquivo:
                        arquivo.write(json.dumps({"etapa": "replay", "origem": str(origem_replay),
                                                  "texto_usuario": usuario,
                                                  "geracao_real": False}, ensure_ascii=False) + "\n")
        if injetar_vazio:
            resposta = requests.Response()
            resposta.status_code = 200
            resposta._content = json.dumps({"choices": [{"message": {"content": "{}"}}]}).encode("utf-8")
            resposta.encoding = "utf-8"
        elif usar_replay:
            print("SONDA REPLAY: resposta gravada; demais fronteiras do runtime preservadas.", flush=True)
            resposta = requests.Response()
            resposta.status_code = 200
            resposta._content = replay_resposta.encode("utf-8")
            resposta.encoding = "utf-8"
        else:
            resposta = original(url, *args, **kwargs)
        if captura:
            with lock, (pasta / "transporte.jsonl").open("a", encoding="utf-8") as arquivo:
                arquivo.write(json.dumps({"etapa": "resposta", "status": resposta.status_code, "texto": resposta.text,
                    **({"chamada_id": getattr(chamada, "id", None),
                        "sha256": hashlib.sha256(resposta.content).hexdigest()} if argumentos.capturar_p16 else {})}, ensure_ascii=False) + "\n")
        return resposta

    requests.post = observar
    from mente_laylay.integracao.preparador_requisicao_llm import PreparadorRequisicaoLLMRuntime
    preparar_original = PreparadorRequisicaoLLMRuntime.preparar

    def observar_preparacao(self, pedido):
        requisicao = preparar_original(self, pedido)
        with lock, (pasta / "transporte.jsonl").open("a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps({
                "etapa": "preparacao", "tipo_chamada": pedido.tipo_chamada,
                "modo_rapido": pedido.modo_rapido,
                "mensagens_pedido": list(pedido.mensagens),
                "payload": dict(requisicao.payload),
            }, ensure_ascii=False) + "\n")
        return requisicao

    if argumentos.capturar_preparacao:
        PreparadorRequisicaoLLMRuntime.preparar = observar_preparacao
    from mente_laylay.integracao.chrome_comandos import ChromeComandosRuntime
    enviar_original = ChromeComandosRuntime.enviar_detalhado

    def observar_chrome(self, action=None, payload=None):
        retorno = enviar_original(self, action, payload)
        # O artefato é local e contém o recibo da mesma chamada, não uma
        # reconsulta ao último estado global após outra operação.
        with lock, (pasta / "recibos_chrome.jsonl").open("a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps({"action": action, "payload": payload,
                                      "retorno": retorno}, ensure_ascii=False) + "\n")
        return retorno

    if argumentos.capturar_chrome:
        ChromeComandosRuntime.enviar_detalhado = observar_chrome
    print("CAPTURA_LOCAL:", pasta, flush=True)
    sys.argv = [str(raiz / "laylay.py"), "--roteiro", str(raiz / "scripts" / "roteiros" / roteiro)]
    if argumentos.capturar_p16:
        os.environ["LAYLAY_MASCOT_ENABLED"] = "1" if voz_avatar_p16 else "0"
        os.environ["LAYLAY_AVATAR_ATIVO"] = "1" if voz_avatar_p16 else "0"
        os.environ["IOT_CONTROLE_FISICO_AUTORIZADO"] = "NAO"
        sys.argv.extend(["--resultado-raiz", str(pasta / "runtime")])
    codigo_saida = 0
    try:
        runpy.run_path(str(raiz / "laylay.py"), run_name="__main__")
    except SystemExit as erro:
        codigo_saida = erro.code if erro.code is not None else 0
        raise
    except BaseException:
        codigo_saida = 1
        raise
    finally:
        requests.post = original
        PreparadorRequisicaoLLMRuntime.preparar = preparar_original
        ChromeComandosRuntime.enviar_detalhado = enviar_original
        for owner, nome, metodo in reversed(restauracoes_p16):
            setattr(owner, nome, metodo)
        if argumentos.capturar_p16:
            try:
                resumo = _gravar_resumo_p16(pasta, codigo_saida)
                print("COLETA_P16:", resumo["status"], resumo["fontes_originais"], flush=True)
            except (OSError, ValueError, KeyError, TypeError) as erro:
                print("COLETA_P16: incompleta", type(erro).__name__, flush=True)


if __name__ == "__main__":
    main()
