"""Continuidade no detector/coordenador instalados; sem executar efeitos ou IA."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from scripts.analises.sonda_escopo_propostas_mistas import RAIZ, preparar_instalacao_isolada


def coletar_instalado(pasta: Path, *, contraprova_prioridade: bool = False, painel_contexto: bool = False) -> dict:
    from mente_laylay.memoria_mental.contexto_compartilhado import estado_mental_inicial
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
    root = preparar_instalacao_isolada(pasta)
    if contraprova_prioridade:
        # Somente neste subprocesso: retirar o consumo prioritário, mantendo
        # o owner contextual. Não é replay de HEAD nem candidato de produção.
        from mente_laylay.autonomia import orquestrador_deterministico as detector
        detector.resolver_continuacao_operacional_confirmada = lambda *_a, **_k: None
        detector.texto_pede_ajuste_numerico_contextual = lambda *_a, **_k: False
    ciclo = root._composicao_ciclo_comandos_runtime.ciclo
    chamadas_modelo = []
    # Porta não consultará rede nem gerará comandos para compensar o detector.
    ciclo.tentar_intencao_ai_primeiro = lambda texto: chamadas_modelo.append(texto) or None
    resultados = []
    casos = [
        ("relato", "coloca em 40", "vigente", "VOLUME", 40),
        ("outro_nivel", "coloca em 25", "vigente", "VOLUME", 25),
        ("outro_verbo", "deixa em 40", "vigente", "VOLUME", 40),
        ("controle_explicito", "coloca o volume em 40", "vigente", "VOLUME", 40),
        ("vencido", "coloca em 40", "vencido", "", None),
        ("nao_confirmado", "coloca em 40", "nao_confirmado", "", None),
        ("pergunta", "como coloca em 40", "vigente", "", None),
        ("negacao", "não coloca em 40", "vigente", "", None),
        ("titulo_numerico", "coloca a música adolescente de 40 anos", "vigente", "MUSIC_SEARCH", None),
    ]
    antecedentes = {}
    if painel_contexto:
        # Gold diagnóstico, nunca injetado no detector/coordenador. Os mesmos
        # callbacks instalados recebem diferentes domínios e pedidos atuais.
        casos = []
        for dominio, primeiro, intent, alvo, status, params, pedidos in [
            ("app", "abre a calculadora", "APP_OPEN", "calculadora", "aberto",
             {"nome_app": "calculadora"}, [
                 ("pronome", "fecha ele", "CLOSE_APP", {"nome_app": "calculadora"}),
                 ("novo_alvo", "abre o bloco de notas de novo", "APP_OPEN", {"nome_app": "bloco de notas"}),
                 ("troca_dominio", "abre o site github de novo", "OPEN_URL", {"alvo": "github"}),
                 ("explicito", "fecha o bloco de notas", "CLOSE_APP", {"nome_app": "bloco de notas"}),
                 ("negacao", "não fecha ele", "", {}),
                 ("pergunta", "como eu faria para fechar ele?", "", {}),
             ]),
            ("site", "abre o site youtube", "OPEN_URL", "youtube", "aberto",
             {"alvo": "youtube"}, [
                 ("pronome", "fecha essa", "CLOSE_TAB", {"alvo": "youtube"}),
                 ("novo_alvo", "abre o site github de novo", "OPEN_URL", {"alvo": "github"}),
                 ("troca_dominio", "abre a calculadora de novo", "APP_OPEN", {"nome_app": "calculadora"}),
                 ("aba", "fecha essa aba", "CLOSE_TAB", {"alvo": "youtube"}),
                 ("negacao", "não fecha essa", "", {}),
                 ("pergunta", "como eu faria para fechar essa?", "", {}),
             ]),
            ("playlist", "coloca a playlist rock", "PLAYLIST_PLAY", "rock", "playlist_reproduzindo",
             {"nome_playlist": "rock"}, [
                 ("pronome", "coloca ela de novo", "MEDIA_CONTROL", {"acao": "replay"}),
                 ("novo_alvo", "coloca a playlist jazz de novo", "PLAYLIST_PLAY", {"nome_playlist": "jazz"}),
                 ("troca_dominio", "abre a calculadora de novo", "APP_OPEN", {"nome_app": "calculadora"}),
                 ("explicito", "fecha a calculadora", "CLOSE_APP", {"nome_app": "calculadora"}),
                 ("negacao", "não coloca ela de novo", "", {}),
                 ("pergunta", "como eu faria para colocar ela de novo?", "", {}),
             ]),
            ("volume", "coloca o volume em 90", "VOLUME", "", "volume_ajustado",
             {"acao": "set", "nivel_volume": 90}, [
                 ("parametro", "coloca em 40", "VOLUME", {"nivel_volume": 40}),
                 ("novo_assunto", "coloca a música máximo respeito", "MUSIC_SEARCH", {"query": "maximo respeito"}),
                 ("aula", "me explica o máximo divisor comum", "", {}),
             ]),
        ]:
            for nome, texto, esperado, esperado_params in pedidos:
                ident = dominio + "_" + nome
                antecedentes[ident] = (primeiro, intent, alvo, status, params, esperado_params)
                casos.append((ident, texto, "vigente", esperado, None))
    for ident, texto, variante, esperado, nivel in casos:
        root._estado_compartilhado_runtime.substituir("mental", estado_mental_inicial())
        primeiro, intent_inicial, alvo, status, params, esperado_params = antecedentes.get(
            ident, ("coloca o volume em 90", "VOLUME", "", "volume_ajustado", None, {}))
        root._iniciar_planejamento_turno(primeiro, origem="sonda_continuacao")
        inicial = root.detectar_intencao_deterministica(primeiro)
        if not inicial or inicial["intent"] != intent_inicial:
            raise RuntimeError("não alcançou o primeiro ajuste explícito")
        # Fixture declarada, publicada pela BASE realmente instalada no adaptador.
        # Não representa uma releitura material do Windows.
        root._registrar_resultado_execucao_base(ResultadoAcao(
            id_solicitacao="sonda-contexto-" + ident, intent=intent_inicial, alvo=alvo, status=status,
            executou=True, confirmado=True, origem="executor", params=dict(params or inicial["params"])), primeiro)
        if variante == "vencido":
            root._estado_compartilhado_runtime.mental["ultima_acao_ts"] = time.time() - 301
        elif variante == "nao_confirmado":
            root._estado_compartilhado_runtime.mental["ultima_acao_contrato"]["confirmado"] = None
        antes = root._estado_compartilhado_runtime.snapshot()["mental"]
        turno = root._iniciar_planejamento_turno(texto, origem="sonda_continuacao")
        detector = root.detectar_intencao_deterministica(texto)
        ctx = ciclo._montar_contexto_resolucao()
        detector_ctx = ctx["detectar_intencao_deterministica"](texto)
        modelo_antes = len(chamadas_modelo)
        decisao, rota = root.resolver_comando_natural(texto, "sonda_continuacao")
        estado_depois = root._estado_compartilhado_runtime.snapshot()["mental"]
        intent = str((decisao or {}).get("intent") or "")
        parametros = dict((decisao or {}).get("params") or {})
        red = ("coordenador_divergiu_do_vinculo" if intent != esperado else
               "nivel_novo_nao_preservado" if nivel is not None and parametros.get("nivel_volume") != nivel else
               "argumento_atual_substituido" if any(parametros.get(k) != v for k, v in esperado_params.items()) else "")
        resultados.append({"id": ident, "texto_inicial": primeiro, "texto": texto,
            "fixture_receipt": True, "estado_antes": antes, "turno": turno,
            "detector": detector, "decisao": decisao, "rota": rota,
            "detector_contexto": detector_ctx,
            "arbitragem": estado_depois.get("historico_arbitragem", [])[-1:],
            "contrato_depois": estado_depois.get("ultima_acao_contrato"),
            "params_depois": estado_depois.get("ultima_acao_params"),
            "operacoes_depois": estado_depois.get("continuidade_geral", {}).get("operacoes_reexecutaveis"),
            "retrato": estado_depois.get("retrato_turno_atual", {}),
            "porta_modelo_consultada": len(chamadas_modelo) - modelo_antes,
            "esperado": {"intent": esperado, "nivel_volume": nivel, "params": esperado_params}, "primeira_fronteira_red": red})
    return {"resultados": resultados, "contraprova_prioridade": contraprova_prioridade, "instalacao": {
        "detector": root.detectar_intencao_deterministica == root._deteccao_deterministica_runtime.detectar,
        "coordenador": root.resolver_comando_natural == root._composicao_ciclo_comandos_runtime.resolver_comando_natural,
        "publicador_base": root._registrar_resultado_execucao_base == root._estado_contexto_runtime.registrar_resultado_execucao,
        "contexto": root._resolver_comando_contextual_forcado == root._contexto_imediato_runtime.resolver},
        "modelo_real_consultado": False, "runtime_main_validado": False,
        "efeitos_externos_executados": False, "voz_validada": False}


def coletar(*, contraprova_prioridade: bool = False, painel_contexto: bool = False) -> dict:
    fontes = ["laylay.py", "mente_laylay/memoria_mental/contexto_imediato.py",
        "mente_laylay/memoria_mental/contexto_compartilhado.py", "mente_laylay/memoria_mental/continuidade_geral.py",
        "mente_laylay/autonomia/orquestrador_deterministico.py", "mente_laylay/autonomia/coordenador_intencao.py",
        "mente_laylay/cognicao/modalidade_turno.py", "mente_laylay/integracao/estado_contexto_runtime.py",
        "mente_laylay/cognicao/referencias_linguagem.py", "mente_laylay/cognicao/retrato_turno.py",
        "mente_laylay/memoria_mental/registro_semantico.py", "mente_laylay/memoria_mental/continuidade_semantica.py",
        "scripts/analises/sonda_continuacao_operacional.py", "scripts/analises/sonda_escopo_propostas_mistas.py"]
    def hashes():
        return {p: hashlib.sha256((RAIZ / p).read_bytes()).hexdigest() for p in fontes}
    antes = hashes()
    base = {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=RAIZ, text=True).strip(),
        "worktree": subprocess.check_output(["git", "status", "--short"], cwd=RAIZ, text=True)}
    with tempfile.TemporaryDirectory(prefix="laylay_continuacao_") as pasta:
        env = dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_NEURAL_MODE="off",
            LAYLAY_NEURAL_COLETA_ENTRADAS="0", LAYLAY_IOT_MODO="simulado", LAYLAY_TERMINAL_2="0",
            LAYLAY_MICROFONE_ATIVO="0", LAYLAY_BRIEFING_INICIAL="0", LAYLAY_FALAS_INICIAIS="0",
            LAYLAY_PRESENCA="0", LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR="0",
            LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR="0", GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ")
        codigo = ("import sys,json; from pathlib import Path; "
            "from scripts.analises.sonda_continuacao_operacional import coletar_instalado; "
            "r=coletar_instalado(Path(sys.argv[1]),contraprova_prioridade=sys.argv[2]=='1',painel_contexto=sys.argv[3]=='1'); sys.__stdout__.write('CONTINUIDADE_JSON='+json.dumps(r,ensure_ascii=False)+'\\n')")
        p = subprocess.run([sys.executable, "-c", codigo, pasta, "1" if contraprova_prioridade else "0", "1" if painel_contexto else "0"], cwd=RAIZ, env=env,
            capture_output=True, text=True, encoding="utf-8", timeout=60)
    linhas = [l for l in p.stdout.splitlines() if l.startswith("CONTINUIDADE_JSON=")]
    if p.returncode or len(linhas) != 1:
        raise RuntimeError("sonda não alcançou a fronteira: " + p.stderr[-3000:] + p.stdout[-2000:])
    depois = hashes()
    return {**base, **json.loads(linhas[0].split("=", 1)[1]), "hashes_antes": antes,
        "hashes_depois": depois, "fontes_estaveis": antes == depois,
        "logs": "\n".join(l for l in p.stdout.splitlines() if not l.startswith("CONTINUIDADE_JSON=")),
        "stderr": p.stderr, "limite": "resolução instalada; receipts fixtures, base real, sem pipeline de execução/entrega"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--contraprova-prioridade", action="store_true")
    parser.add_argument("--painel-contexto", action="store_true")
    args = parser.parse_args()
    destino = args.saida.resolve()
    if destino.exists() or not destino.is_relative_to((RAIZ / "resultados_testes").resolve()):
        parser.error("saída nova dentro de resultados_testes")
    r = coletar(contraprova_prioridade=args.contraprova_prioridade, painel_contexto=args.painel_contexto)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("x", encoding="utf-8") as arquivo:
        json.dump(r, arquivo, ensure_ascii=False, indent=2)
    print(json.dumps([{ "id": c["id"], "decisao": c["decisao"], "red": c["primeira_fronteira_red"]}
        for c in r["resultados"]], ensure_ascii=False))
    return int(not r["fontes_estaveis"] or not all(r["instalacao"].values())
               or any(c["primeira_fronteira_red"] for c in r["resultados"]))


if __name__ == "__main__":
    raise SystemExit(main())
