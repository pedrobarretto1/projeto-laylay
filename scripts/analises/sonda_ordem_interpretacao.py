"""Compara resolução instalada e antecipação diagnóstica do analisador.

Não modifica política em produção. O contraste chama o analisador instalado,
resolve referências e passa no árbitro real; NÃO equivale ao pipeline completo
nem concede autoridade. Nenhum executor, voz, main ou memória pessoal participa.
Modelo real é opt-in, somente local, e recusa sessão Laylay aberta.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))


def painel() -> list[dict]:
    def cmd(intent, **params):
        return {"intent":intent, "params":params}
    volume = cmd("VOLUME", acao="set", nivel_volume=40)
    pausa = cmd("MEDIA_CONTROL", acao="pause")
    app = cmd("APP_OPEN", nome_app="Calculadora")
    itens = [
        ("direto", "coloca o volume em 40", "", [volume]),
        ("elipse_volume", "coloca em 40", "volume", [volume]),
        ("variante_volume", "deixa o som do computador em quarenta por cento", "", [volume]),
        ("direto_app", "abre a calculadora", "", [app]),
        ("referencia_app", "fecha ela", "app", [cmd("CLOSE_APP", nome_app="Calculadora")]),
        ("negacao", "não coloca o volume em 40", "volume", []),
        ("capacidade", "você consegue colocar o volume em 40?", "volume", []),
        ("consulta", "o que significa pausar a música?", "", []),
        ("condicao", "quando eu confirmar, pausa a música", "", []),
        ("composto", "abre a calculadora e pausa a música", "", [app, pausa]),
        ("misto", "abre a calculadora; quando eu confirmar, pausa a música", "", [app]),
        ("remocao_contextual", "tira essa musica da playlist", "playlist", []),
        ("remocao_explicita", "tira Esse JOGO ficou PERDIDO por 9 ANOS da playlist novidades", "playlist", []),
        ("objeto_versus_colecao", "remove essa faixa da playlist novidades", "playlist", []),
    ]
    return [{"id":ident,"texto":texto,"contexto":contexto,"esperados":gold,
        "remocao_nao_conectada":ident.startswith("remocao") or ident == "objeto_versus_colecao"}
        for ident,texto,contexto,gold in itens]


def avaliar_campos(esperados: list[dict], decisoes: list[dict]) -> dict:
    """Gold só na avaliação. Aderência de campos NÃO prova autorização/efeito."""
    restantes = deepcopy(esperados)
    indevidos = []
    for decisao in decisoes:
        if str(decisao.get("intent") or "").upper() in {"", "NONE"}:
            continue
        encontrados = [i for i, gold in enumerate(restantes)
            if decisao.get("intent") == gold["intent"] and all(
                str(decisao.get("params", {}).get(k)).casefold() == str(v).casefold()
                for k,v in gold["params"].items())]
        if encontrados:
            restantes.pop(encontrados[0])
        else:
            indevidos.append(decisao)
    return {"ausentes":restantes,"indevidos":indevidos,
        "aderencia_campos":not restantes and not indevidos,
        "prova_autorizacao":False,"prova_efeito":False}


def projetar_contexto_diagnostico(ctx: dict) -> dict:
    """Ablacão observacional, NÃO patch: retira árvores duplicadas do prompt.

    Conserva referências/receipt/continuidade e identidade do frame. Não altera
    estado real, catálogo, regras, autorização nem o contexto do árbitro.
    """
    novo = dict(ctx)
    estado = dict(ctx.get("estado") or {})
    mental = dict(estado.get("mente_integrada_estado") or {})
    campos = ("ultima_acao_contrato", "ultima_acao_params", "ultima_acao_intent",
        "ultima_acao_alvo", "ultima_acao_status", "ultima_acao_confirmada", "ultima_acao_ok",
        "ultima_acao_ts", "ultima_intencao", "ultimo_alvo", "ultima_habilidade", "ultimo_escopo",
        "retrato_turno_atual", "continuidade_geral", "pendencia_acao_canonica", "pendencia_atual",
        "esclarecimento_operacional", "foco_vivo", "ultimo_app_janela", "ultimo_site_aba")
    projetado = {k:deepcopy(mental[k]) for k in campos if k in mental}
    turno = mental.get("turno_atual") or {}
    projetado["turno_atual"] = {k:deepcopy(turno[k]) for k in (
        "id", "texto", "texto_original", "retrato_id", "modalidade", "modalidade_geral",
        "autoriza_execucao", "veto_execucao_operacional") if k in turno}
    estado["mente_integrada_estado"] = projetado
    novo["estado"] = estado
    return novo


def decodificar_resultado_tipificado(contrato, texto: str) -> dict:
    # ClienteLLMRuntime._validar_contrato_saida devolve JSON validado, não
    # o framing da preparação conversacional. Não procurar JSON na prosa.
    return contrato.decodificar_json(texto)


def _medir_por_ato(root, texto: str, turno: dict, fonte: dict, *,
                   modelo_real: bool, indicios_pos: dict | None = None) -> dict:
    """Ablacão diagnóstica, não candidato operacional ou novo interpretador."""
    from scripts.analises.avaliacao_interpretacao_natural import preparar_mensagens
    from mente_laylay.cognicao.saida_interpretacao_principal import criar_contrato_saida_interpretacao_principal
    from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
    from mente_laylay.integracao.registro_conversa_llm import PedidoModelo
    from mente_laylay.autonomia.processamento_resposta_ia import extrair_leitura_semantica_principal
    contexto = {k: deepcopy(fonte[k]) for k in (
        "ultima_acao_contrato", "ultima_acao_params", "ultima_acao_intent", "ultima_acao_alvo",
        "ultima_acao_confirmada", "ultima_acao_status") if k in fonte}
    if isinstance(contexto.get("ultima_acao_contrato"), dict):
        contexto["ultima_acao_contrato"] = {k: v for k, v in contexto["ultima_acao_contrato"].items()
            if k in {"intent", "alvo", "status", "dominio", "executou", "confirmado", "origem"}}
    contexto["procedencia"] = "fixture_diagnostica_sem_efeito_real"
    ctx_interpretacao = root._interpretacao_intencao_runtime._contexto()
    catalogo_fn = ctx_interpretacao.get("mapa_habilidades_prompt")
    catalogo = str(catalogo_fn(texto) or "") if callable(catalogo_fn) else ""
    mensagens = preparar_mensagens(texto, contexto, indicios_pos=indicios_pos, catalogo=catalogo)
    resultado = {"proposta": None, "propostos": [], "atos": [], "admitidos": [],
        "contexto_modelo": contexto, "mensagens_diagnosticas": mensagens,
        "estado_geracao": "nao_executada", "semantica_avaliavel": False,
        "autoriza_execucao": False, "comprova_efeito": False,
        "pos_segundos_precomputados": indicios_pos.get("segundos") if indicios_pos else None,
        "custo_pos_incluido_na_latencia": False}
    if not modelo_real:
        return resultado
    contrato = criar_contrato_saida_interpretacao_principal(texto)
    resposta = root._registro_modelo_llm_runtime.executar(PedidoModelo.criar(
        mensagens, max_tokens=1536, timeout=55, com_tools=False,
        contrato_saida=contrato, reserva_saida_tokens=1536,
        contexto_fechado=True, permitir_durante_interacao=True))
    resultado.update(resposta_bruta=resposta.texto, sucesso_modelo=resposta.sucesso)
    if not resposta.sucesso:
        return {**resultado, "estado_geracao": "falha_modelo_ou_contrato"}
    try:
        dados = decodificar_resultado_tipificado(contrato, resposta.texto)
    except (TypeError, ValueError) as erro:
        return {**resultado, "estado_geracao": "formato_recusado", "motivo": str(erro)}
    proposta = ContratoPropostaPrincipal(turno_id=turno["id"], texto_usuario=texto,
        resposta_bruta=resposta.texto)
    leitura = extrair_leitura_semantica_principal(proposta, texto)
    registrada = root._composicao_turno_runtime.registrar_leitura_proposta(texto, leitura, proposta)
    validacao = root._validador_comandos_turno_runtime.validar_proposta(dados["comandos"], proposta)
    return {**resultado, "estado_geracao": "concluida", "semantica_avaliavel": True,
        "proposta": dados, "propostos": dados["comandos"], "atos": leitura.get("atos", []),
        "leitura_registrada": bool(registrada), "validacao": validacao,
        "admitidos": validacao.get("comandos", [])}


def coletar_instalado(pasta: Path, modelo_real: bool, contexto_projetado: bool = False, limite: int = 14,
                     corpus: str = "", por_ato: bool = False, indicios_pos: str = "",
                     journal: str = "") -> dict:
    import requests
    from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
    from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
    from scripts.analises.sonda_execucao_contextual_windows import verificar_sessao
    from mente_laylay.cognicao.arbitro_turno import arbitrar_turno, CandidatoDecisao
    from mente_laylay.autonomia.coordenador_intencao import resolver_referencias_da_intencao
    from mente_laylay.memoria_mental.contexto_compartilhado import estado_mental_inicial
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
    transportes = []
    selecao = selecao_local() if modelo_real else None
    http = None
    if modelo_real:
        # A guarda do destino original também precisa valer após um redirect.
        original_http = requests.sessions.Session.request
        def sem_redirect(sessao, method, url, *args, **kwargs):
            kwargs["allow_redirects"] = False
            return original_http(sessao, method, url, *args, **kwargs)
        http = criar_guarda_http_local(selecao, transportes, sem_redirect)
    root = preparar_instalacao_isolada(pasta, requisicao_http=http)
    from scripts.analises.avaliacao_interpretacao_natural import (
        carregar_corpus, avaliar_atos, avaliar_comandos, validar_indicios_pos,
    )
    casos = carregar_corpus(Path(corpus))["casos"] if corpus else painel()
    pacotes_pos = {}
    if indicios_pos:
        pacote = json.loads(Path(indicios_pos).read_text(encoding="utf-8"))
        if not corpus or pacote.get("corpus_sha256") != hashlib.sha256(Path(corpus).read_bytes()).hexdigest():
            raise ValueError("indícios POS pertencem a outro corpus")
        if not pacote.get("config_spacy_sha256"):
            raise ValueError("configuração POS não identificada")
        pacotes_pos = {c["id"]: validar_indicios_pos(c["texto"], pacote["pacotes"][c["id"]])
                       for c in casos[:limite]}
    tentativas_efeito = []
    def efeito_proibido(*args, **kwargs):
        tentativas_efeito.append("executor_ou_dispatcher")
        raise AssertionError("comparação não autoriza chamar executor ou dispatcher")
    # Defesa adicional às portas de resolução: não fabrica receipt nem sucesso.
    root._ciclo_comandos_runtime.executar_intencao = efeito_proibido
    root.executar_intencao = efeito_proibido
    root.executar_comandos_json = efeito_proibido
    runtime = root._interpretacao_intencao_runtime
    contexto_original = runtime._contexto_getter
    if contexto_projetado:
        def contexto():
            ctx = contexto_original()
            # Snapshot público evita copiar locks presentes nas coleções vivas.
            ctx = dict(ctx)
            estado_ctx = dict(ctx.get("estado") or {})
            estado_ctx["mente_integrada_estado"] = root._estado_compartilhado_runtime.retrato_dominio("mental")
            ctx["estado"] = estado_ctx
            return projetar_contexto_diagnostico(ctx)
        runtime._contexto_getter = contexto
    ciclo = root._ciclo_comandos_runtime
    enviar_original = runtime._enviar_mensagem
    brutas = []
    def enviar(*args, **kwargs):
        if modelo_real:
            verificar_sessao()
            raw = enviar_original(*args, **kwargs)
        else:
            raw = '{"intent":"NONE","params":{}}'
        brutas.append(str(raw))
        return raw
    runtime._enviar_mensagem = enviar
    resultados = []
    for caso in casos[:limite]:
        ramos = {}
        bracos = ("ordem_atual", "qwen_por_ato") if por_ato else ("ordem_atual", "analisador_antecipado")
        if por_ato and indicios_pos:
            # Alterna ordem dos candidatos para não aquecer sempre o mesmo braço.
            bracos = (("ordem_atual", "qwen_por_ato", "qwen_por_ato_pos") if len(resultados) % 2 == 0
                      else ("ordem_atual", "qwen_por_ato_pos", "qwen_por_ato"))
        for ramo in bracos:
            estado = root._estado_compartilhado_runtime
            estado.substituir("mental", estado_mental_inicial())
            estado.substituir("memoria_conversa", {"messages":[]})
            estado.substituir("conversacional", {"current_emotion":"calma"})
            estado.substituir("musical", {})
            contexto = caso["contexto"]
            if contexto:
                intent, alvo, params = {
                    "volume":("VOLUME","",{"acao":"set","nivel_volume":90}),
                    "app":("APP_OPEN","Calculadora",{"nome_app":"Calculadora"}),
                    "playlist":("PLAYLIST_ADD","novidades",{"nome_playlist":"novidades"}),
                }[contexto]
                texto_anterior = {"volume":"coloca o volume em 90", "app":"abre a calculadora",
                    "playlist":"coloca na playlist novidades"}[contexto]
                root._iniciar_planejamento_turno(texto_anterior, origem="sonda_ordem")
                root._registrar_resultado_execucao_base(ResultadoAcao(intent=intent, alvo=alvo,
                    params=params, status={"volume":"volume_ajustado","app":"aberto","playlist":"playlist_musica_adicionada"}[contexto],
                    executou=True, confirmado=True, origem="fixture_diagnostica", id_solicitacao="fixture-"+caso["id"]),
                    texto_anterior)
                if contexto == "playlist": root._musica_estado_set("ultima_playlist", "novidades")
            turno = root._iniciar_planejamento_turno(caso["texto"], origem="sonda_ordem")
            runtime._cache_analise.clear()
            ctx = ciclo._montar_contexto_resolucao()
            fonte = estado.retrato_dominio("mental")
            inicio, indice, transporte_inicio = time.monotonic(), len(brutas), len(transportes)
            if ramo == "ordem_atual":
                decisao, rota = root.resolver_comando_natural(caso["texto"], "sonda_ordem")
                proposta, resolvida, arbitragem = None, None, None
                medicao = {}
            elif ramo == "analisador_antecipado":
                proposta = runtime.analisar(caso["texto"])
                resolvida = resolver_referencias_da_intencao(proposta, fonte.get("retrato_turno_atual"))
                candidatos = [CandidatoDecisao(tipo="comando_explicito",valor=resolvida,
                    origem="sonda-analisador-antecipado",confianca=0.84)] if resolvida else []
                arbitragem = arbitrar_turno(caso["texto"], candidatos, turno=turno,
                    retrato=fonte.get("retrato_turno_atual"))
                decisao, rota = arbitragem.get("decisao"), "contraste-diagnostico"
                medicao = {}
            else:
                medicao = _medir_por_ato(root, caso["texto"], turno, fonte, modelo_real=modelo_real,
                    indicios_pos=pacotes_pos.get(caso["id"]) if ramo.endswith("_pos") else None)
                decisao, rota = None, "diagnostico_por_ato_sem_executor"
                proposta, resolvida, arbitragem = medicao.get("proposta"), None, None
            ramos[ramo] = {"decisao":decisao,"rota":rota,"proposta":proposta,
                "referencia_resolvida":resolvida,"arbitragem":arbitragem,
                "respostas_brutas":brutas[indice:],
                "chamadas_modelo":len(transportes)-transporte_inicio if modelo_real else 0,
                "unidade_chamadas_modelo":"requisicoes_http_incluindo_retentativas",
                "analisador_substituido_por_none_no_smoke":not modelo_real,
                "segundos":round(time.monotonic()-inicio,3),"turno":turno,
                "referencia_resolvida_antes":deepcopy((fonte.get("retrato_turno_atual") or {}).get("referencia_resolvida")),
                "transportes":transportes[transporte_inicio:],
                "transporte_modelo_confirmado":any(t.get("status") == 200 for t in transportes[transporte_inicio:]),
                "avaliacao":avaliar_campos(caso["esperados"], [decisao] if decisao else [])}
            if ramo.startswith("qwen_"):
                ramos[ramo].pop("avaliacao")
                ramos[ramo].update(medicao)
                # Falha técnica/contrato nunca vira lista vazia semanticamente correta.
                if medicao["semantica_avaliavel"]:
                    ramos[ramo]["avaliacao_atos"] = avaliar_atos(caso.get("atos_esperados", []), medicao["atos"])
                    ramos[ramo]["avaliacao_proposta"] = avaliar_comandos(caso["esperados"], medicao["propostos"])
                    ramos[ramo]["avaliacao_admissao"] = avaliar_comandos(caso["esperados"], medicao["admitidos"])
            else:
                ramos[ramo]["avaliacao_decisao_singular"] = avaliar_comandos(caso["esperados"], [decisao] if decisao else [])
            if tentativas_efeito:
                raise AssertionError("sentinela de efeito acionada; coleta recusada")
            if journal:
                from scripts.analises.sonda_escopo_propostas_mistas import serializar_tipo_diagnostico
                with Path(journal).open("a", encoding="utf-8") as arquivo:
                    arquivo.write(json.dumps({"id": caso["id"], "ramo": ramo, "resultado": ramos[ramo]},
                        ensure_ascii=False, default=serializar_tipo_diagnostico) + "\n")
            sys.__stdout__.write(f"ORDEM_PROGRESSO={caso['id']}:{ramo}\n")
            sys.__stdout__.flush()
        resultados.append({"caso":caso, **ramos})
    return {"resultados":resultados,"modelo_real":modelo_real,"selecao":selecao,
        "contexto_projetado_diagnostico":contexto_projetado,
        "runtime_main_validado":False,"efeitos_externos_executados":False,
        "politica_producao_alterada":False,
        "tentativas_efeito": tentativas_efeito, "corpus_externo": bool(corpus),
        "por_ato_diagnostico": por_ato,
        "limites":"Rota de decisão singular, não cobertura do pipeline composto. Contraste não é candidato instalado. Fixtures não são receipts de efeitos reais. Gold não entra no modelo. Uma amostra por ramo, sem controle de aquecimento."}


def coletar(modelo_real: bool, contexto_projetado: bool = False, limite: int = 14,
            corpus: str = "", por_ato: bool = False, indicios_pos: str = "", journal: str = "") -> dict:
    from scripts.analises.sonda_execucao_contextual_windows import verificar_sessao
    if modelo_real: verificar_sessao()
    fontes = [Path(__file__).relative_to(RAIZ).as_posix(), "scripts/analises/avaliacao_interpretacao_natural.py", "laylay.py"] + sorted(
        p.relative_to(RAIZ).as_posix() for p in (RAIZ/"mente_laylay").rglob("*.py"))
    def hashes(): return {p:hashlib.sha256((RAIZ/p).read_bytes()).hexdigest() for p in fontes}
    antes = hashes()
    arquivos_entrada = [RAIZ / "configuracao.env"] + [Path(p) for p in (corpus, indicios_pos) if p]
    entradas_antes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in arquivos_entrada}
    base = {"head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=RAIZ,text=True).strip(),
        "branch":subprocess.check_output(["git","branch","--show-current"],cwd=RAIZ,text=True).strip(),
        "worktree":subprocess.check_output(["git","status","--short"],cwd=RAIZ,text=True),
        "fontes_antes": antes, "entradas_antes": entradas_antes,
        "instante_inicio_utc": datetime.now(timezone.utc).isoformat()}
    if journal:
        with Path(journal).with_suffix(".baseline.json").open("x", encoding="utf-8") as arquivo:
            json.dump(base, arquivo, ensure_ascii=False, indent=2)
    with tempfile.TemporaryDirectory(prefix="laylay_ordem_") as pasta:
        env = dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_NEURAL_MODE="off",
            LAYLAY_NEURAL_COLETA_ENTRADAS="0", LAYLAY_IOT_MODO="simulado", LAYLAY_TERMINAL_2="0",
            LAYLAY_MICROFONE_ATIVO="0", LAYLAY_BRIEFING_INICIAL="0", LAYLAY_FALAS_INICIAIS="0",
            LAYLAY_PRESENCA="0", LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR="0",
            LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR="0", GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ")
        codigo = "import sys,json; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from scripts.analises.sonda_ordem_interpretacao import coletar_instalado; from scripts.analises.sonda_escopo_propostas_mistas import serializar_tipo_diagnostico; r=coletar_instalado(Path(sys.argv[2]),sys.argv[3]=='1',sys.argv[4]=='1',int(sys.argv[5]),sys.argv[6],sys.argv[7]=='1',sys.argv[8],sys.argv[9]); sys.__stdout__.write('ORDEM_JSON='+json.dumps(r,ensure_ascii=False,default=serializar_tipo_diagnostico)+'\\n')"
        processo = subprocess.run([sys.executable,"-c",codigo,str(RAIZ),pasta,"1" if modelo_real else "0", "1" if contexto_projetado else "0", str(limite), corpus, "1" if por_ato else "", indicios_pos, journal],
            cwd=RAIZ,env=env,capture_output=True,text=True,encoding="utf-8",timeout=max(340, limite * 180))
    if processo.returncode: raise RuntimeError("Sonda não alcançou fronteira:\n"+processo.stderr[-4000:])
    linhas = [l for l in processo.stdout.splitlines() if l.startswith("ORDEM_JSON=")]
    if len(linhas) != 1: raise RuntimeError("Resultado estruturado ausente")
    depois = hashes()
    entradas_depois = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in arquivos_entrada}
    return {**base, **json.loads(linhas[0].split("=",1)[1]),"hashes_antes":antes,
        "hashes_depois":depois,"fontes_estaveis":antes==depois,
        "entradas_depois": entradas_depois, "entradas_estaveis": entradas_antes == entradas_depois,
        "corpus_sha256": hashlib.sha256(Path(corpus).read_bytes()).hexdigest() if corpus else None,
        "indicios_pos_sha256": hashlib.sha256(Path(indicios_pos).read_bytes()).hexdigest() if indicios_pos else None,
        "configuracao_sha256": hashlib.sha256((RAIZ / "configuracao.env").read_bytes()).hexdigest(),
        "instante_utc":datetime.now(timezone.utc).isoformat()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida",type=Path,required=True)
    parser.add_argument("--modelo-real",action="store_true")
    parser.add_argument("--contexto-projetado",action="store_true",help="ablação de árvores duplicadas, só no subprocesso")
    parser.add_argument("--limite",type=int,default=14)
    parser.add_argument("--corpus", type=Path, help="corpus de desenvolvimento com gold só no avaliador")
    parser.add_argument("--por-ato", action="store_true", help="contraste diagnóstico, não altera produção")
    parser.add_argument("--indicios-pos", type=Path, help="tokens externos vinculados ao hash do corpus")
    args = parser.parse_args()
    if not 1 <= args.limite <= (250 if args.corpus else 14): parser.error("limite fora do corpus")
    if args.por_ato and not args.corpus or args.indicios_pos and not args.por_ato:
        parser.error("por-ato exige corpus; indícios POS exigem por-ato")
    destino = args.saida.resolve()
    if not destino.is_relative_to((RAIZ/"resultados_testes").resolve()) or destino.exists():
        parser.error("usar destino novo em resultados_testes")
    destino.parent.mkdir(parents=True,exist_ok=True)
    journal = destino.with_suffix(".eventos.jsonl")
    if journal.exists(): parser.error("journal já existe; usar destino novo")
    from mente_laylay.integracao.instancia_unica import adquirir_instancia_unica
    instancia = adquirir_instancia_unica(RAIZ / "laylay.py")
    if not instancia.adquirida or os.name == "nt" and instancia.handle is None:
        instancia.liberar()
        print("Sonda não iniciada: sessão Laylay ocupada ou trava indisponível.")
        return 73
    try:
        resultado = coletar(args.modelo_real, args.contexto_projetado, args.limite,
            str(args.corpus.resolve()) if args.corpus else "", args.por_ato,
            str(args.indicios_pos.resolve()) if args.indicios_pos else "", str(journal))
    finally:
        instancia.liberar()
    from scripts.analises.sonda_escopo_propostas_mistas import serializar_tipo_diagnostico
    with destino.open("x",encoding="utf-8") as arquivo:
        json.dump(resultado,arquivo,ensure_ascii=False,indent=2,default=serializar_tipo_diagnostico)
    print(json.dumps({"casos":len(resultado["resultados"]),"modelo_real":args.modelo_real,
        "fontes_estaveis":resultado["fontes_estaveis"]},ensure_ascii=False))
    return 0 if resultado["fontes_estaveis"] and resultado["entradas_estaveis"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
