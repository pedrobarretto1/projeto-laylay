"""Rastreia metadados da sonda C3 no runtime real, sem alterar decisões.

Opt-in; requer a sessão anterior encerrada. Serviços/persistência normais.
Não registra prompts, credenciais ou contexto do usuário. Opcionalmente imprime
falas avaliadas das três perguntas fixas da sonda (não habilitar para outros usos).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import runpy
import sys
import threading
import unicodedata
from datetime import datetime

from mente_laylay.cognicao.estado_tecnico_llm import eh_estado_tecnico_llm
from roteiro_consulta_conteudo_c3 import COMANDOS


def metadados_texto(valor: object) -> dict:
    texto = str(valor or "").strip()
    dados = {"tipo": type(valor).__name__, "caracteres": len(texto),
             "palavras": len(texto.split()), "estado_tecnico": eh_estado_tecnico_llm(valor)}
    try:
        objeto = json.loads(texto)
    except (TypeError, ValueError):
        dados["json"] = False
    else:
        dados["json"] = True
        dados["json_tipo"] = type(objeto).__name__
        if isinstance(objeto, dict):
            dados["tem_fala"] = "fala" in objeto
            dados["fala_tipo"] = type(objeto.get("fala")).__name__
            dados["fala_caracteres"] = len(str(objeto.get("fala") or ""))
            dados["tem_comandos"] = bool(objeto.get("comandos"))
    return dados


def executar() -> None:
    raiz = Path(__file__).resolve().parent
    destino = raiz / "resultados_testes" / (
        "diagnostico_autoria_c3-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    )
    destino.mkdir(parents=True, exist_ok=False)
    lock = threading.Lock()
    def normalizar_sonda(texto):
        texto = unicodedata.normalize("NFKD", str(texto or "").casefold())
        return "".join(c for c in texto if c.isalnum())
    perguntas_sonda = [normalizar_sonda(texto) for texto in COMANDOS]
    alvos = {
        "autoria_conversacional.py": {"criar_fala_autoral", "_extrair_fala_autoral"},
        "registro_conversa_llm.py": {"enviar"},
        "resposta_llm.py": {"interpretar_payload_llm"},
        "orcamento_llm_turno.py": {"autorizar_chamada"},
        "qualidade_comunicacao.py": {"avaliar_qualidade_comunicacao"},
    }

    ativo = True
    with (destino / "fronteiras.jsonl").open("w", encoding="utf-8") as arquivo:
        def rastrear(frame, evento, retorno):
            if evento != "return" or not ativo:
                return
            nome = frame.f_code.co_name
            # Sem Path/IO para os demais frames do runtime.
            if nome not in {"criar_fala_autoral", "_extrair_fala_autoral", "enviar", "interpretar_payload_llm", "autorizar_chamada", "avaliar_qualidade_comunicacao"}:
                return
            modulo = os.path.basename(frame.f_code.co_filename)
            if nome not in alvos.get(modulo, set()):
                return
            registro = {"hora": datetime.now().isoformat(), "modulo": modulo,
                        "funcao": nome, "thread": threading.get_ident()}
            locais = frame.f_locals
            if nome == "autorizar_chamada":
                registro.update(permitida=getattr(retorno, "permitida", None),
                                motivo=getattr(retorno, "motivo", None),
                                tipo_chamada=getattr(retorno, "tipo_chamada", None))
            elif nome == "avaliar_qualidade_comunicacao" and isinstance(retorno, dict):
                registro.update({chave: retorno.get(chave) for chave in
                                 ("aceita", "problemas", "requer_reparo")})
                entrada_sonda = normalizar_sonda(locais.get("texto_usuario"))
                if os.environ.get("LAYLAY_DIAGNOSTICO_FALAS_SONDA") == "1" and entrada_sonda in perguntas_sonda:
                    registro["fala_sonda"] = str(locais.get("fala") or "")
                    sys.__stdout__.write("[SONDA:FALA_AVALIADA] " + json.dumps({
                        "turno": perguntas_sonda.index(entrada_sonda) + 1,
                        "fala": str(locais.get("fala") or ""),
                        "problemas": retorno.get("problemas"),
                    }, ensure_ascii=False) + "\n")
                    sys.__stdout__.flush()
            elif nome == "criar_fala_autoral":
                registro.update(usada_llm=getattr(retorno, "usada_llm", None),
                                motivo=getattr(retorno, "motivo_fallback", None))
            elif nome == "_extrair_fala_autoral":
                registro["entrada"] = metadados_texto(locais.get("valor"))
                if isinstance(retorno, tuple):
                    registro["saida"] = metadados_texto(retorno[0])
            else:
                registro["saida"] = metadados_texto(retorno)
                if nome == "enviar":
                    registro["tipo_chamada"] = getattr(locais.get("pedido"), "tipo_chamada", None)
                if nome == "interpretar_payload_llm":
                    escolha = dict(locais.get("escolha") or {})
                    mensagem = dict(locais.get("mensagem") or {})
                    registro["finish_reason"] = escolha.get("finish_reason")
                    registro["reasoning_caracteres"] = len(str(mensagem.get("reasoning") or mensagem.get("reasoning_content") or ""))
            with lock:
                if ativo:
                    arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
                    arquivo.flush()

        print(f"Diagnóstico C3 (metadados; falas sintéticas somente por opt-in): {destino}", flush=True)
        os.environ.update(LAYLAY_BRIEFING_INICIAL="0", LAYLAY_FALAS_INICIAIS="0", LAYLAY_TERMINAL_2="0")
        sys.argv = [str(raiz / "laylay.py"), "--roteiro", str(raiz / "roteiro_consulta_conteudo_c3.py")]
        sys.setprofile(rastrear)
        threading.setprofile(rastrear)
        try:
            runpy.run_path(str(raiz / "laylay.py"), run_name="__main__")
        finally:
            with lock:
                ativo = False
            sys.setprofile(None)
            threading.setprofile(None)


if __name__ == "__main__":
    executar()
