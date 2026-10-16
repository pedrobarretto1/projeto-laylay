"""Mede produção semântica com modelo instalado, sem main ou efeitos.

Reutiliza composição e isolamento existentes. Só mensagens sintéticas vão
ao transporte local; não aciona conversa, executores, voz ou treino.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from copy import deepcopy
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parents[2]
CASOS = [
    "abre o aplicativo Calculadora",
    "liga a luz do quarto",
    "abre o aplicativo Calculadora; deixa ela à esquerda; não liga a luz",
    "cria o arquivo Resumo.md",
    "abre o aplicativo Calculadora e pausa a música",
    "abre o site Example.test/A e desliga o ventilador",
    'abre o arquivo "Resumo e Planos.txt" e pausa a música',
    "sobe o volume para 40 e abre o aplicativo Notepad",
]


def coletar_instalado(pasta: Path, modelo_real: bool, candidato: bool = False, fontes_estruturais: bool = False) -> dict:
    import requests
    from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
    request_original = requests.sessions.Session.request
    chamadas = []

    def somente_modelo_local(self, method, url, **kwargs):
        endereco = urlparse(url)
        if not modelo_real or endereco.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise AssertionError("sonda não autoriza acesso externo")
        if endereco.path != "/v1/chat/completions" or method.upper() != "POST":
            raise AssertionError("sonda só permite geração local, não outros serviços")
        chamadas.append({"modelo": kwargs.get("json", {}).get("model"),
                         "max_tokens": kwargs.get("json", {}).get("max_tokens"),
                         "formato_http": kwargs.get("json", {}).get("response_format", {}).get("type"),
                         "instrucao_tipificada_no_http": any("INTERPRETAÇÃO POR ATO" in m.get("content", "")
                             for m in kwargs.get("json", {}).get("messages", []) if m.get("role") == "system"),
                         "papeis_http": [m.get("role") for m in kwargs.get("json", {}).get("messages", [])]})
        resposta_http = request_original(self, method, url, **kwargs)
        if resposta_http.status_code == 200:
            choices = resposta_http.json().get("choices", [])
            if choices:
                chamadas[-1]["fim_geracao"] = choices[0].get("finish_reason")
                chamadas[-1]["emissao_bruta_sintetica"] = choices[0].get("message", {}).get("content", "")
        return resposta_http

    root = preparar_instalacao_isolada(pasta, requisicao_http=somente_modelo_local)
    root._contexto_prompt_runtime.servico.interpretacao_por_ato_ativa = candidato
    from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
    from mente_laylay.autonomia.processamento_resposta_ia import extrair_leitura_semantica_principal
    from mente_laylay.integracao.registro_conversa_llm import PedidoModelo
    from mente_laylay.personalidade.proporcao_resposta import limite_tokens_resposta
    from mente_laylay.cognicao.modalidade_turno import _segmentar_turno_misto
    from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada
    resultados = []
    for indice_caso, texto in enumerate(CASOS):
        turno = root._iniciar_planejamento_turno(texto, origem="sonda_produtor_por_ato")
        runtime = root._contexto_prompt_runtime
        mensagens = [{"role": "system", "content": runtime.servico.base_system_prompt},
                     {"role": "user", "content": texto}]
        pacote = runtime.preparar_envio_modelo(mensagens, turno_id=turno["id"])
        contrato = pacote.contrato_saida
        mensagens_envio = list(pacote.mensagens)
        fontes = []
        if fontes_estruturais:
            # Contraprova somente no subprocesso. Reusa o segmentador e
            # exige literais únicos; não corrige texto nem aplica autoridade.
            if contrato is None:
                raise ValueError("fontes estruturais exigem candidato negociado")
            fontes = _segmentar_turno_misto(texto)
            if any(texto.count(f) != 1 for f in fontes) or not 1 <= len(fontes) <= 8:
                raise ValueError("fontes diagnósticas sem vínculo literal inequívoco")
            schema = contrato.response_format["json_schema"]["schema"]
            item_ato = schema["properties"]["leitura_turno"]["items"]
            if "anyOf" in item_ato:
                # A composição atual já vincula fontes. Esta opção mantém a
                # contraprova histórica separada; não altera o owner instalado.
                item_ato = item_ato["anyOf"][0]
            ramos = []
            for fonte in fontes:
                ramo = deepcopy(item_ato)
                ramo["properties"]["conteudo"]["const"] = fonte
                ramo["properties"]["interpretacao"]["properties"]["texto_original"]["const"] = fonte
                if "intervalo" in ramo["properties"]["interpretacao"]["properties"]:
                    inicio = texto.index(fonte)
                    ramo["properties"]["interpretacao"]["properties"]["intervalo"]["const"] = [inicio, inicio + len(fonte)]
                ramos.append(ramo)
            schema["properties"]["leitura_turno"].update(items={"anyOf": ramos},
                minItems=len(fontes), maxItems=len(fontes))
            owner_original = contrato.validar
            def validar_fontes(dados):
                owner_original(dados)
                if [a["conteudo"] for a in dados["leitura_turno"]] != fontes:
                    raise ValueError("fontes_estruturais_sem_cobertura_ordenada")
            contrato = ContratoSaidaEstruturada("fontes_estruturais_diagnostico", "[FONTES_DIAGNOSTICO]", schema, validar_fontes)
            mensagens_envio.insert(len(mensagens_envio) - 1, {"role": "system", "content":
                "Fontes estruturais propostas para análise, não autorização. Um objeto por fonte, nesta ordem: "
                + json.dumps(fontes, ensure_ascii=False) + ". Preserve os trechos exatamente; avalie significado sem executar."})
        reserva = getattr(pacote, "reserva_saida_tokens", 0)
        limite = max(limite_tokens_resposta(texto, envelope_estruturado=True), reserva)
        item = {"texto": texto, "instrucao_tipificada": any(
            "INTERPRETAÇÃO POR ATO" in m.get("content", "") for m in pacote.mensagens if m.get("role") == "system"),
            "reserva_saida_tokens": reserva, "limite_saida_tokens": limite,
            "projecao_alterou_historico": mensagens[-1]["content"] != texto}
        item["frame_classificacao"] = {k: turno.get(k) for k in (
            "modalidade", "autoriza_execucao", "veto_execucao_operacional", "natureza_acao", "segmentos")}
        item["primeira_fronteira_observacional"] = (
            "classificacao_nao_publicou_ato_operacional" if candidato
            and turno.get("autoriza_execucao") is not True and turno.get("veto_execucao_operacional") is not True else "")
        item["fontes_estruturais_diagnosticas"] = fontes
        if modelo_real:
            inicio = time.monotonic()
            resposta = root._registro_modelo_llm_runtime.executar(PedidoModelo.criar(
                mensagens_envio, max_tokens=limite, timeout=55, com_tools=False,
                contrato_saida=contrato, reserva_saida_tokens=reserva,
                contexto_fechado=True, permitir_durante_interacao=True))
            proposta = ContratoPropostaPrincipal(turno_id=turno["id"], texto_usuario=texto,
                resposta_bruta=resposta.texto)
            leitura = extrair_leitura_semantica_principal(proposta, texto)
            registrada = root._composicao_turno_runtime.registrar_leitura_proposta(texto, leitura, proposta)
            dados = [ato["interpretacao"] for ato in leitura.get("atos", []) if ato.get("interpretacao")]
            item.update(resposta_bruta=resposta.texto, sucesso_transporte=resposta.sucesso,
                duracao_s=round(time.monotonic() - inicio, 3), leitura=leitura,
                registrada=bool(registrada), interpretacoes_vinculadas=len(dados),
                proposta_sem_autoridade=all(i["autoriza_execucao"] is False and i["comprova_efeito"] is False for i in dados))
            # Mede emissão/vínculo, não acerto de alvo, intenção ou execução.
            esperados = {2: 3, 4: 2, 5: 2, 6: 2, 7: 2}.get(indice_caso, 1)
            falhas = []
            if item["primeira_fronteira_observacional"]:
                falhas.append(item["primeira_fronteira_observacional"])
            if candidato and not item["instrucao_tipificada"]:
                falhas.append("instrucao_ausente_na_projecao")
            if candidato and len(dados) != esperados:
                falhas.append("emissao_tipificada_nao_vinculada")
            if candidato and not registrada:
                falhas.append("registro_semantico_recusado")
            item.update(falhas_candidato=falhas, primeira_fronteira_red=falhas[0] if falhas else "",
                        validade_semantica_comprovada=False, autoriza_execucao=False, comprova_efeito=False)
            if not resposta.sucesso and contrato is not None and chamadas:
                # Diagnóstico da emissão sintética; nunca substitui a saída
                # recusada da porta, nunca registra ou executa seus comandos.
                try:
                    contrato.decodificar_json(chamadas[-1].get("emissao_bruta_sintetica", ""))
                except (TypeError, ValueError) as erro:
                    item["motivo_recusa_owner"] = str(erro)
        resultados.append(item)
    return {"resultados": resultados, "chamadas_locais": chamadas,
        "modelo_real_consultado": modelo_real, "candidato_ativado_so_na_sonda": candidato,
        "runtime_main_validado": False,
        "efeitos_externos_executados": False,
        "limite": "projeção instalada e transporte real local, só mensagens sintéticas; não mede execução nem generalização"}


def coletar(modelo_real: bool, candidato: bool = False, fontes_estruturais: bool = False) -> dict:
    fontes = [Path(__file__).relative_to(RAIZ).as_posix(), "laylay.py",
        "mente_laylay/cognicao/contratos_turno.py", "mente_laylay/integracao/preparacao_llm.py",
        "mente_laylay/cognicao/modalidade_turno.py",
        "mente_laylay/cognicao/saida_interpretacao_principal.py", "mente_laylay/integracao/cliente_llm_runtime.py",
        "mente_laylay/integracao/contrato_saida_estruturada.py", "mente_laylay/integracao/preparador_requisicao_llm.py",
        "mente_laylay/autonomia/contexto_resposta_ia.py", "mente_laylay/autonomia/resposta_ia_runtime.py",
        "mente_laylay/cognicao/leitura_semantica_turno.py", "mente_laylay/integracao/registro_conversa_llm.py"]
    def hashes():
        return {p: hashlib.sha256((RAIZ / p).read_bytes()).hexdigest() for p in fontes}
    antes = hashes()
    base = {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=RAIZ, text=True).strip(),
        "worktree": subprocess.check_output(["git", "status", "--short"], cwd=RAIZ, text=True)}
    with tempfile.TemporaryDirectory(prefix="laylay_produtor_") as pasta:
        env = dict(os.environ, PYTHONIOENCODING="utf-8", LAYLAY_NEURAL_MODE="off",
            LAYLAY_NEURAL_COLETA_ENTRADAS="0", LAYLAY_IOT_MODO="simulado", LAYLAY_TERMINAL_2="0",
            LAYLAY_MICROFONE_ATIVO="0", LAYLAY_BRIEFING_INICIAL="0", LAYLAY_FALAS_INICIAIS="0",
            LAYLAY_PRESENCA="0", LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR="0",
            LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR="0", GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ")
        codigo = "import sys,json; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from scripts.analises.sonda_produtor_interpretacao_por_ato import coletar_instalado; r=coletar_instalado(Path(sys.argv[2]),sys.argv[3]=='1',sys.argv[4]=='1',sys.argv[5]=='1'); sys.__stdout__.write('PRODUTOR_JSON='+json.dumps(r,ensure_ascii=False)+'\\n')"
        processo = subprocess.run([sys.executable, "-c", codigo, str(RAIZ), pasta, "1" if modelo_real else "0", "1" if candidato else "0", "1" if fontes_estruturais else "0"],
            cwd=RAIZ, env=env, capture_output=True, text=True, encoding="utf-8", timeout=310)
    if processo.returncode:
        raise RuntimeError("sonda não alcançou a fronteira:\n" + processo.stderr[-2000:])
    linhas = [l for l in processo.stdout.splitlines() if l.startswith("PRODUTOR_JSON=")]
    if len(linhas) != 1:
        raise RuntimeError("resultado estruturado ausente")
    depois = hashes()
    return {**base, **json.loads(linhas[0].split("=", 1)[1]), "hashes_antes": antes,
        "hashes_depois": depois, "fontes_estaveis": antes == depois,
        "instante_utc": datetime.now(timezone.utc).isoformat()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--modelo-real", action="store_true")
    parser.add_argument("--candidato", action="store_true", help="ativa formato experimental só no subprocesso")
    parser.add_argument("--fontes-estruturais", action="store_true", help="contraprova do vínculo de fontes, só no subprocesso")
    args = parser.parse_args()
    destino = args.saida.resolve()
    if not destino.is_relative_to((RAIZ / "resultados_testes").resolve()) or destino.exists():
        parser.error("usar destino novo em resultados_testes")
    if args.fontes_estruturais and not args.candidato:
        parser.error("fontes estruturais exigem candidato explícito")
    resultado = coletar(args.modelo_real, args.candidato, args.fontes_estruturais)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("x", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, ensure_ascii=False, indent=2)
    for caso in resultado["resultados"]:
        print(json.dumps({k: caso.get(k) for k in ("texto", "instrucao_tipificada", "limite_saida_tokens",
            "sucesso_transporte", "interpretacoes_vinculadas", "registrada")}, ensure_ascii=False))
    return 0 if resultado["fontes_estaveis"] and not any(
        c.get("falhas_candidato") for c in resultado["resultados"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
