"""Runner headless para diagnóstico do principal instalado, não replay de main.

Reutiliza o sequenciador do caos, modelo local configurado, prompt, validador,
dispatcher, memória compartilhada e publicação textual. Prioridade/prefluxo
ficam fora desta porta diagnóstica: isso é declarado no relatório. Sem áudio,
UI, background, memória pessoal ou respostas injetadas. Efeitos bloqueados
por padrão; execução opt-in exige pedidos canônicos permitidos por entrada.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from typing import Any

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))


def carregar_entradas(caminho: Path) -> list[dict]:
    """Dados somente; nunca importa/executa um roteiro Python fornecido."""
    documento = json.loads(caminho.read_text(encoding="utf-8-sig"))
    itens = documento.get("entradas") if isinstance(documento, dict) else documento
    if not isinstance(itens, list) or not 1 <= len(itens) <= 1000:
        raise ValueError("Informe uma lista com 1 a 1000 entradas.")
    entradas, ids = [], set()
    from mente_laylay.cognicao.escopo_autorizacao import _identidade_operacional
    for indice, item in enumerate(itens, 1):
        registro = {"texto": item} if isinstance(item, str) else item
        if not isinstance(registro, dict) or set(registro) - {"id", "texto", "expectativa", "permitidos"}:
            raise ValueError("Entrada exige texto, id opcional, expectativa e permitidos separados.")
        texto = registro.get("texto")
        ident = registro.get("id", f"entrada-{indice:03d}")
        if (not isinstance(texto, str) or not texto.strip() or len(texto) > 20000
            or not isinstance(ident, str) or not ident.strip() or ident in ids):
            raise ValueError("Texto/id vazio, duplicado ou fora dos limites.")
        expectativa, permitidos = registro.get("expectativa", {}), registro.get("permitidos", [])
        if not isinstance(expectativa, dict) or not isinstance(permitidos, list):
            raise ValueError("Expectativa deve ser objeto; permitidos deve ser lista.")
        if any(not isinstance(p, dict) or _identidade_operacional(p) is None for p in permitidos):
            raise ValueError("Permissões exigem intent/params canônicos, sem curingas.")
        entradas.append({"id": ident, "texto": texto, "expectativa": expectativa, "permitidos": permitidos})
        ids.add(ident)
    return entradas


def pedido_permitido(pedido: dict, entrada: dict, modo: str) -> bool:
    from mente_laylay.cognicao.escopo_autorizacao import _identidade_operacional
    if modo != "executar":
        return False
    identidade = _identidade_operacional(pedido)
    return identidade is not None and identidade in {
        _identidade_operacional(p) for p in entrada["permitidos"]}


def serializar_diagnostico(valor: Any) -> Any:
    """Projeções são somente artefatos; não voltam como autoridade ao runtime."""
    from scripts.analises.sonda_escopo_propostas_mistas import serializar_tipo_diagnostico
    from mente_laylay.cognicao.materializacao_contextual import ExecucaoContextualVinculada
    if type(valor) is ExecucaoContextualVinculada:
        return {"observacao": valor.observacao.como_dict(),
            "admissao": {"indice": valor.admissao.indice, "texto": valor.admissao.texto,
                "pedido": valor.admissao.pedido.como_dict()},
            "materializacao": valor.materializacao.como_dict(), "autoriza_execucao": False}
    try:
        return serializar_tipo_diagnostico(valor)
    except TypeError:
        from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA
        if type(valor) is SnapshotComandoIA:
            return valor.como_dict()
        if is_dataclass(valor):
            return asdict(valor)
        # Observabilidade não deve mudar um resultado legítimo por um DTO novo.
        return {"tipo_nao_serializado": type(valor).__name__}


class DiarioDiagnostico:
    """Journal incremental: se o filho travar, a última fronteira não se perde."""
    def __init__(self, caminho: Path) -> None:
        self.caminho = caminho
        self.indice: int | None = None
        self.eventos: list[dict] = []
        self.falhas: list[dict] = []
        self._lock = threading.RLock()

    def registrar(self, tipo: str, **dados: Any) -> bool:
        with self._lock:
            evento = {"sequencia": len(self.eventos) + 1, "entrada": self.indice,
                "tipo": tipo, "monotonic": time.monotonic(), **dados}
            # Fotografar agora, não guardar referências mutáveis do executor.
            integro = True
            try:
                linha = json.dumps(evento, ensure_ascii=False, default=serializar_diagnostico)
            except (TypeError, ValueError, RecursionError) as erro:
                self.falhas.append({"evento": tipo, "erro_tipo": type(erro).__name__})
                evento = {"sequencia": evento["sequencia"], "entrada": self.indice,
                    "tipo": "erro_serializacao_diagnostica", "evento_original": tipo}
                linha = json.dumps(evento)
                integro = False
            try:
                with self.caminho.open("a", encoding="utf-8") as arquivo:
                    arquivo.write(linha + "\n")
                    arquivo.flush()
            except OSError as erro:
                # Falha de observação após publicação não pode revogar o
                # receipt do executor nem provocar retry de efeito concluído.
                self.falhas.append({"evento": tipo, "erro_tipo": type(erro).__name__})
                integro = False
            self.eventos.append(json.loads(linha))
            return integro


def contexto_diagnostico(root: Any) -> dict:
    mental = root._estado_compartilhado_runtime.snapshot()["mental"]
    chaves = ("turno_atual", "plano_turno_atual", "retrato_turno_atual", "ultima_acao_contrato",
        "ultima_acao_ts", "ultimo_app_janela", "ultimo_site_aba", "ultimo_layout_janelas",
        "continuidades", "continuidade_geral")
    return {k: mental.get(k) for k in chaves}


def sintetizar_entrada(registro: dict) -> dict:
    """Índice de evidências para localizar uma fronteira, não diagnóstico causal automático."""
    eventos = registro.get("eventos", [])
    antes, depois = registro.get("contexto_antes", {}), registro.get("contexto_depois", {})
    plano = depois.get("plano_turno_atual") or {}
    avisos = []
    for evento in eventos:
        tipo = evento["tipo"]
        motivo = ""
        if tipo == "modelo_resultado" and evento.get("sucesso") is False:
            motivo = "geracao_sem_sucesso"
        elif tipo in {"modelo_erro", "executor_erro"}:
            motivo = tipo
        elif tipo == "executor_admissao_runner" and not evento.get("permitido"):
            motivo = "bloqueio_intencional_do_runner"
        elif tipo == "dispatch_bloqueado_runner" and evento.get("quantidade_comandos", 0):
            motivo = "bloqueio_intencional_do_runner"
        elif tipo == "receipt":
            if not evento.get("aceito"):
                motivo = "publicacao_recusada"
            elif evento["receipt"].get("confirmado") is not True:
                motivo = "resultado_sem_confirmacao"
        if motivo:
            avisos.append({"sequencia": evento["sequencia"], "fronteira": tipo, "motivo": motivo})
    return {"fase_final": plano.get("fase"), "erros_plano": plano.get("erros", []),
        "comandos_admitidos": [e.get("comandos", []) for e in eventos if e["tipo"] == "dispatch_admitido"],
        "rejeicoes_validador": [e["resultado"].get("rejeitados", []) for e in eventos
            if e["tipo"] == "validacao_proposta" and isinstance(e.get("resultado"), dict)],
        "chamadas_modelo": sum(e["tipo"] == "modelo_inicio" for e in eventos),
        "metricas": [e for e in eventos if e["tipo"] == "metrica"],
        "receipts": [e for e in eventos if e["tipo"] == "receipt"],
        "campos_contextuais_alterados": [k for k in set(antes) | set(depois) if antes.get(k) != depois.get(k)],
        "primeiro_alerta_observado": avisos[0] if avisos else None, "alertas": avisos,
        "raiz_causal": "não inferida automaticamente; revisar fonte, decisões e evidências"}


def executar_coleta(caminho: Path, pasta: Path, modo: str, timeout_turno: float,
                    continuar_sem_resposta: bool = False) -> None:
    if continuar_sem_resposta and modo != "planejar":
        raise ValueError("Continuar após silêncio só é permitido sem efeitos.")
    from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
    from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
    from mente_laylay.integracao.roteiro_teste_conversa import ConfiguracaoRoteiro, RoteiroTesteConversaRuntime
    from mente_laylay.autonomia import coordenador_intencao
    from mente_laylay.autonomia.dispatcher_comandos_json import normalizar_candidato_json_para_intencao
    import requests

    entradas = carregar_entradas(caminho)
    selecao = selecao_local()
    diario = DiarioDiagnostico(pasta / "eventos.jsonl")
    transportes: list[dict] = []
    memoria = pasta / "memoria_isolada"
    memoria.mkdir()
    http_original = requests.sessions.Session.request
    def http_sem_redirect(sessao: Any, method: str, url: str, *args: Any, **kwargs: Any) -> Any:
        kwargs["allow_redirects"] = False
        return http_original(sessao, method, url, *args, **kwargs)
    root = preparar_instalacao_isolada(memoria, requisicao_http=criar_guarda_http_local(
        selecao, transportes, http_sem_redirect))
    runtime = root._resposta_ia_runtime
    contexto_original = runtime._contexto_getter
    instalado = runtime._contexto()
    voz = root._voz_runtime
    voz.definir_modo_silencioso(True, origem="runner_diagnostico")
    fala = root._orquestrador_fala_runtime
    fala._observadores_fala_final = []  # nenhum observador periférico
    fala._observadores_texto_final = []
    configuracao = ConfiguracaoRoteiro(comandos=tuple(e["texto"] for e in entradas),
        timeout_resposta_s=timeout_turno, timeout_voz_s=1.0,
        silenciar_voz_durante_teste=True, parar_sem_resposta=not continuar_sem_resposta,
        expectativas_semanticas={i: e["expectativa"] for i, e in enumerate(entradas, 1)})
    resultados: list[dict] = []
    atual: dict = {}

    def enviar(texto: str) -> None:
        indice = len(resultados)
        diario.indice = indice + 1
        atual.clear()
        atual.update(entradas[indice])
        registro = {"indice": indice + 1, "id": atual["id"], "texto": texto,
            "contexto_antes": contexto_diagnostico(root), "inicio_monotonic": time.monotonic()}
        resultados.append(registro)
        diario.registrar("entrada", texto=texto, id=atual["id"])
        try:
            runtime.processar(texto, origem="runner_diagnostico_headless")
        finally:
            registro.update(contexto_depois=contexto_diagnostico(root),
                duracao_s=round(time.monotonic() - registro["inicio_monotonic"], 4))
            diario.registrar("processamento_retornou", duracao_s=registro["duracao_s"])

    roteiro = RoteiroTesteConversaRuntime(configuracao, enviar_entrada=enviar,
        resultado_getter=lambda: root._estado_compartilhado_runtime.obter_copia("mental", "plano_turno_atual"),
        voz_ocupada_getter=lambda: not voz.fila.empty(), diretorio_resultado=pasta / "roteiro")

    def publicar_texto(texto: str, emocao: str = "calma", nivel: int = 1, **dados: Any) -> bool:
        diario.registrar("texto_publicado", texto=texto, emocao=emocao, nivel=nivel,
            plano_id=(root._estado_compartilhado_runtime.mental.get("plano_turno_atual") or {}).get("id"))
        return roteiro.observar_resposta(texto, emocao, nivel, **dados)

    fala.registrar_observador_texto_final(publicar_texto)
    executar_modelo = root._cliente_llm_runtime.servico.cliente.executar

    def observar_modelo(pedido: Any) -> Any:
        inicio = time.monotonic()
        diario.registrar("modelo_inicio", tipo_chamada=getattr(pedido, "tipo_chamada", ""), pedido=pedido)
        try:
            resultado = executar_modelo(pedido)
            diario.registrar("modelo_resultado", sucesso=resultado.sucesso, texto=resultado.texto,
                duracao_s=round(time.monotonic() - inicio, 4))
            return resultado
        except Exception as erro:
            diario.registrar("modelo_erro", erro_tipo=type(erro).__name__)
            raise

    root._cliente_llm_runtime.servico.cliente.executar = observar_modelo
    executar_original = coordenador_intencao.executar_intencao

    def observar_executor(pedido: dict, texto: str, ctx: dict) -> bool:
        indice_invocacao = diario.indice
        permitido = pedido_permitido(pedido, atual, modo)
        if not diario.registrar("executor_admissao_runner", pedido=pedido, fonte=texto, permitido=permitido):
            raise RuntimeError("runner: journal indisponível; não iniciar efeito sem observabilidade")
        if not permitido:
            raise RuntimeError("runner: pedido fora das permissões exatas da entrada; efeito bloqueado")
        publicar_original = ctx.get("_registrar_resultado_execucao")
        if not callable(publicar_original):
            raise RuntimeError("runner: ausência de publicação canônica; não executar")

        def observar_receipt(receipt: Any, *args: Any, **kwargs: Any) -> Any:
            retorno = publicar_original(receipt, *args, **kwargs)
            diario.registrar("receipt", entrada=indice_invocacao, aceito=retorno is not False, receipt=receipt.como_dict())
            return retorno

        inicio = time.monotonic()
        try:
            retorno = executar_original(pedido, texto, {**ctx, "_registrar_resultado_execucao": observar_receipt})
            diario.registrar("executor_retornou", retorno_legado=bool(retorno),
                duracao_s=round(time.monotonic() - inicio, 4))
            return retorno
        except Exception as erro:
            diario.registrar("executor_erro", erro_tipo=type(erro).__name__)
            raise

    coordenador_intencao.executar_intencao = observar_executor
    dispatcher = instalado["executar_comandos_json"]
    validador = instalado["validar_comandos_planejados"]
    validar_original = validador._validar

    def observar_validacao(*args: Any, **kwargs: Any) -> Any:
        resultado = validar_original(*args, **kwargs)
        diario.registrar("validacao_proposta", resultado=resultado)
        return resultado

    validador._validar = observar_validacao

    def observar_dispatch(ctx: dict, texto: str, comandos: list, *args: Any) -> dict:
        diario.registrar("dispatch_admitido", comandos=comandos)
        # Só comandos canônicos chegam ao dispatcher que pode executar. A
        # interceptação cobre também chamadas legadas fora do ciclo central.
        bloqueado = modo != "executar" or any(
            normalizar_candidato_json_para_intencao(c) is None for c in comandos)
        if bloqueado:
            diario.registrar("dispatch_bloqueado_runner", quantidade_comandos=len(comandos),
                motivo="planejamento_sem_efeitos" if modo != "executar" else "acao_nao_canonica")
            return {"erros": ["runner: execução desabilitada"] if comandos else [],
                "fala_ja_emitida": False, "fala_emitida_por_acao": False, "fala_salva_no_inicio": False}
        resultado = dispatcher(ctx, texto, comandos, *args)
        diario.registrar("dispatch_resultado", resultado=resultado)
        return resultado

    def montar_contexto() -> dict:
        ctx = dict(contexto_original())
        ctx.update(processar_comandos_prioritarios=None, processar_inicio_fluxo=None,
            modo_chat_runtime=None, executar_comandos_json=observar_dispatch)
        metrica_original = ctx.get("registrar_metrica_diagnostico")
        if callable(metrica_original):
            def medir(componente: str, duracao_ms: float, sucesso: bool = True, **dados: Any) -> Any:
                retorno = metrica_original(componente, duracao_ms, sucesso, **dados)
                diario.registrar("metrica", componente=componente, duracao_ms=duracao_ms,
                    sucesso=sucesso, contexto=dados)
                return retorno
            ctx["registrar_metrica_diagnostico"] = medir
        # Só observação, chamando o writer original exatamente uma vez.
        for nome in ("marcar_inicio_turno", "atualizar_plano_proposta", "atualizar_plano_ocorrencia", "preparar_resposta"):
            original = ctx.get(nome)
            if callable(original):
                def observar(*args: Any, _original=original, _nome=nome, **kwargs: Any) -> Any:
                    retorno = _original(*args, **kwargs)
                    diario.registrar(_nome, resultado=retorno)
                    return retorno
                ctx[nome] = observar
        return ctx

    runtime._contexto_getter = montar_contexto
    sucesso = False
    try:
        sucesso = roteiro.executar()
    finally:
        coordenador_intencao.executar_intencao = executar_original
        validador._validar = validar_original
        runtime._contexto_getter = contexto_original
        checkpoint = json.loads(roteiro.checkpoint_path.read_text(encoding="utf-8"))
        for registro in resultados:
            registro["eventos"] = [e for e in diario.eventos if e["entrada"] == registro["indice"]]
            registro["roteiro"] = checkpoint["itens"][registro["indice"]-1]
            registro["diagnostico"] = sintetizar_entrada(registro)
        http_compacto = [{k: t.get(k) for k in ("url", "status", "segundos", "erro_tipo")}
            for t in transportes]
        relatorio = {"concluido": sucesso and not diario.falhas, "telemetria_integra": not diario.falhas,
            "falhas_telemetria": diario.falhas, "modo": modo, "entradas": resultados, "http": http_compacto,
            "modelo": selecao["LAYLAY_LLM_MODEL"], "main_iniciado": False,
            "modelo_real_consultado": any(t.get("status") == 200 for t in transportes),
            "respostas_injetadas": False, "audio_fisico": False,
            "voz_silenciosa": voz.modo_silencioso_ativo(), "worker_voz_iniciado": voz.worker_started,
            "limites": ["Porta principal diagnóstica: prioridade, prefluxo e modo-chat desativados.",
                "Memória limpa/temporária; não prova histórico pessoal nem toda persistência.",
                "Receipt aceito não substitui observação física independente.",
                "Expectativa é gold diagnóstico, não autorização nem instrução ao modelo.",
                "Efeitos reais autorizados podem permanecer depois do teste; sem desfazer automaticamente."]}
        with (pasta / "relatorio.json").open("x", encoding="utf-8") as arquivo:
            json.dump(relatorio, arquivo, ensure_ascii=False, indent=2, default=serializar_diagnostico)


def gerar_resumo(pasta: Path, estado_processo: str, codigo: int, baseline: dict) -> dict:
    """Produz saída útil mesmo após timeout/crash; não inventa resultados."""
    arquivo = pasta / "relatorio.json"
    relatorio = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {}
    eventos = []
    journal = pasta / "eventos.jsonl"
    if journal.exists():
        for linha in journal.read_text(encoding="utf-8").splitlines():
            try:
                eventos.append(json.loads(linha))
            except json.JSONDecodeError:
                break  # último evento parcialmente gravado não é evidência
    receipts = [e["receipt"] for e in eventos if e["tipo"] == "receipt" and e.get("aceito") is True]
    from mente_laylay.memoria_mental.resultado_acao import obter_id_solicitacao
    finais = {obter_id_solicitacao(r): r for r in receipts if obter_id_solicitacao(r)}
    avaliacoes = [(e.get("roteiro") or {}).get("avaliacao") or {} for e in relatorio.get("entradas", [])]
    resumo = {"estado_processo": estado_processo, "codigo": codigo,
        "coleta_concluida": codigo == 0 and relatorio.get("concluido") is True,
        "entradas_enviadas": sum(e["tipo"] == "entrada" for e in eventos),
        "textos_publicados": sum(e["tipo"] == "texto_publicado" for e in eventos),
        "receipts_aceitos": len(receipts),
        "solicitacoes_com_receipt": len(finais),
        "efeitos_confirmados_por_executor": sum(r.get("executou") is True and r.get("confirmado") is True for r in finais.values()),
        "bloqueios_runner": sum(e["tipo"] == "dispatch_bloqueado_runner" and e.get("quantidade_comandos", 0) > 0 or
            e["tipo"] == "executor_admissao_runner" and not e.get("permitido") for e in eventos),
        "ultima_fronteira_observada": eventos[-1] if eventos else None,
        "qualidade_semantica": "requer revisão; coleta concluída não significa interpretação correta",
        "falhas_geracao": sum(e["tipo"] == "modelo_resultado" and e.get("sucesso") is False for e in eventos),
        "avaliacoes_semanticas": {"passaram": sum(a.get("resultado_semantico") == "passou" for a in avaliacoes),
            "falharam": sum(a.get("resultado_semantico") == "falhou" for a in avaliacoes),
            "nao_avaliadas": sum(not a.get("semantica_avaliada") for a in avaliacoes)},
        "alertas_por_entrada": [{"id": r["id"], "primeiro_alerta": r.get("diagnostico", {}).get("primeiro_alerta_observado")}
            for r in relatorio.get("entradas", [])],
        "baseline": baseline}
    with (pasta / "resumo.json").open("x", encoding="utf-8") as arquivo_saida:
        json.dump(resumo, arquivo_saida, ensure_ascii=False, indent=2)
    linhas = ["# Diagnóstico headless — Laylay", "", f"Estado do processo: {estado_processo}; código {codigo}.",
        f"Entradas: {resumo['entradas_enviadas']}; textos: {resumo['textos_publicados']}; receipts aceitos: {len(receipts)}.",
        "", "Coleta não certifica qualidade semântica, efeito físico ou execução completa de main.", ""]
    for entrada in relatorio.get("entradas", []):
        plano = entrada.get("contexto_depois", {}).get("plano_turno_atual") or {}
        item = entrada.get("roteiro") or {}
        linhas += [f"## {entrada['indice']}. {entrada['id']}", "", entrada["texto"], "",
            f"Fase: {plano.get('fase')}; duração: {entrada.get('duracao_s')}s.", "",
            str(item.get("resposta") or "Sem publicação textual capturada."), "",
            "Erros do plano: " + json.dumps(plano.get("erros", []), ensure_ascii=False), "",
            "Primeiro alerta observado: " + json.dumps(entrada.get("diagnostico", {}).get("primeiro_alerta_observado"), ensure_ascii=False),
            "", "Avaliação do roteiro: " + json.dumps(item.get("avaliacao", {}), ensure_ascii=False), ""]
    with (pasta / "resumo.md").open("x", encoding="utf-8") as arquivo_saida:
        arquivo_saida.write("\n".join(linhas))
    return resumo


def comparar_coletas(anterior: Path, atual: Path) -> dict:
    """Diff por identidade e entrada literal; mudanças de condições não provam melhoria."""
    a = json.loads((anterior / "relatorio.json").read_text(encoding="utf-8"))
    b = json.loads((atual / "relatorio.json").read_text(encoding="utf-8"))
    entradas_a = {e["id"]: e for e in a["entradas"]}
    entradas_b = {e["id"]: e for e in b["entradas"]}
    diferencas = []
    for ident in sorted(set(entradas_a) & set(entradas_b)):
        ea, eb = entradas_a[ident], entradas_b[ident]
        diferencas.append({"id": ident, "mesma_entrada_literal": ea["texto"] == eb["texto"],
            "diagnostico_antes": ea.get("diagnostico"), "diagnostico_depois": eb.get("diagnostico"),
            "resposta_antes": (ea.get("roteiro") or {}).get("resposta"),
            "resposta_depois": (eb.get("roteiro") or {}).get("resposta")})
    return {"mesmo_modo": a.get("modo") == b.get("modo"), "mesmo_modelo": a.get("modelo") == b.get("modelo"),
        "diferencas": diferencas, "apenas_na_anterior": sorted(set(entradas_a) - set(entradas_b)),
        "apenas_na_atual": sorted(set(entradas_b) - set(entradas_a)),
        "melhoria_comprovada": False, "limite": "Diferenças de coleta não isolam causalidade nem qualidade semântica."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entradas", type=Path)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--modo", choices=("planejar", "executar"), default="planejar")
    parser.add_argument("--timeout-turno", type=float, default=120.0)
    parser.add_argument("--timeout-total", type=float, default=600.0)
    parser.add_argument("--continuar-sem-resposta", action="store_true",
        help="Coleta silenciosa continua após ausência de resposta; apenas em planejar.")
    args = parser.parse_args()
    if args.continuar_sem_resposta and args.modo != "planejar":
        parser.error("--continuar-sem-resposta só é permitido em planejar.")
    entradas = carregar_entradas(args.entradas)
    if any(not math.isfinite(v) or v <= 0 for v in (args.timeout_turno, args.timeout_total)):
        parser.error("Timeouts precisam ser positivos e finitos.")
    from scripts.analises.sonda_escopo_geracao_real import selecao_local
    from mente_laylay.integracao.instancia_unica import adquirir_instancia_unica
    selecao = selecao_local()  # não sobrescrever seleção/configuração do modelo
    pasta = args.saida.resolve()
    if not pasta.is_relative_to((RAIZ / "resultados_testes").resolve()) or pasta.exists():
        parser.error("Saída deve ser nova e estar dentro de resultados_testes.")
    instancia = adquirir_instancia_unica(RAIZ / "laylay.py")
    if not instancia.adquirida or os.name == "nt" and instancia.handle is None:
        instancia.liberar()
        print("Runner não iniciado: sessão ocupada ou trava indisponível.")
        return 73
    try:
        pasta.mkdir(parents=True, exist_ok=False)
        fontes = [RAIZ / "laylay.py", Path(__file__).resolve(),
            RAIZ / "scripts/analises/sonda_escopo_geracao_real.py",
            RAIZ / "scripts/analises/sonda_escopo_propostas_mistas.py",
            *sorted((RAIZ / "mente_laylay").rglob("*.py"))]
        hashes = lambda: {str(f.relative_to(RAIZ)): hashlib.sha256(f.read_bytes()).hexdigest() for f in fontes}
        antes = hashes()
        configuracao_antes = hashlib.sha256((RAIZ / "configuracao.env").read_bytes()).hexdigest()
        baseline = {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
            "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=RAIZ, text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], cwd=RAIZ, text=True),
            "instante_utc": datetime.now(timezone.utc).isoformat(), "modo": args.modo,
            "entradas_sha256": hashlib.sha256(args.entradas.read_bytes()).hexdigest(),
            "entradas": entradas, "selecao": selecao, "fontes_antes": antes,
            "continuar_sem_resposta": args.continuar_sem_resposta,
            "configuracao_antes": configuracao_antes}
        with (pasta / "baseline.json").open("x", encoding="utf-8") as arquivo:
            json.dump(baseline, arquivo, ensure_ascii=False, indent=2)
        env = dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_NEURAL_MODE="off",
            LAYLAY_NEURAL_COLETA_ENTRADAS="0", LAYLAY_IOT_MODO="simulado", LAYLAY_TERMINAL_2="0",
            LAYLAY_MICROFONE_ATIVO="0", LAYLAY_BRIEFING_INICIAL="0", LAYLAY_FALAS_INICIAIS="0",
            LAYLAY_PRESENCA="0", LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR="0",
            LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR="0", GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ")
        env["PYTHONUNBUFFERED"] = "1"
        codigo_filho = ("import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);"
            "from scripts.analises.runner_diagnostico_laylay import executar_coleta;"
            "executar_coleta(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4],float(sys.argv[5]),sys.argv[6]=='1')")
        estado = "finalizado"
        with (pasta / "runtime.log").open("x", encoding="utf-8") as log:
            filho = subprocess.Popen([sys.executable, "-c", codigo_filho, str(RAIZ),
                str(args.entradas.resolve()), str(pasta), args.modo, str(args.timeout_turno),
                "1" if args.continuar_sem_resposta else "0"],
                cwd=RAIZ, env=env, stdout=log, stderr=log)
            try:
                codigo = filho.wait(timeout=args.timeout_total)
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as erro:
                # Somente este subprocesso recém-criado; nunca processo do usuário.
                estado = "timeout" if isinstance(erro, subprocess.TimeoutExpired) else "interrompido"
                filho.kill()
                filho.wait()
                codigo = 124 if estado == "timeout" else 130
        baseline.update(fontes_depois=hashes(), configuracao_depois=hashlib.sha256(
            (RAIZ / "configuracao.env").read_bytes()).hexdigest())
        baseline["fontes_estaveis"] = antes == baseline["fontes_depois"]
        baseline["configuracao_preservada"] = configuracao_antes == baseline["configuracao_depois"]
        resumo = gerar_resumo(pasta, estado, codigo, baseline)
        print(json.dumps({k: resumo[k] for k in ("coleta_concluida", "entradas_enviadas",
            "receipts_aceitos", "bloqueios_runner", "falhas_geracao", "avaliacoes_semanticas")}, ensure_ascii=False))
        print(f"Relatório: {pasta / 'resumo.md'}")
        return codigo or int(not resumo["coleta_concluida"] or not baseline["fontes_estaveis"]
            or not baseline["configuracao_preservada"])
    finally:
        instancia.liberar()


if __name__ == "__main__":
    raise SystemExit(main())
