"""Composição instalada sem main/voz/rede de e-mail; modelo real é opcional.

Usa memória temporária. A porta IMAP tem mensagens sintéticas; SMTP nunca é
chamado. Não comprova a sessão desktop nem entrega de e-mail a terceiros.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))


def coletar(pasta: Path, modelo_real: bool = False) -> dict:
    if (pasta / "relatorio.json").exists():
        raise ValueError("A coleta já existe; use outra pasta para preservar a evidência anterior.")
    pasta.mkdir(parents=True, exist_ok=True)
    os.environ.update(GMAIL_USER=" ", GMAIL_APP_PASSWORD=" ", LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR="0")
    from memoria_sqlite import MemoriaSQLite
    from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
    from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
    from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
    from mente_laylay.integracao import instancia_unica
    sqlite = MemoriaSQLite.__init__
    MemoriaSQLite.__init__ = lambda self, caminho=None: sqlite(self, str(pasta / Path(caminho or "memoria.sqlite").name))
    resumo = MemoriaLaylay.__init__
    MemoriaLaylay.__init__ = lambda self, *, pasta_memoria, **k: resumo(self, pasta_memoria=str(pasta / "resumo"), **k)
    pessoas = MemoriaPessoasRuntime.__init__
    MemoriaPessoasRuntime.__init__ = lambda self, *, caminho, **k: pessoas(self, caminho=pasta / "pessoas.json", **k)
    central = CentralNotificacoesRuntime.__init__
    CentralNotificacoesRuntime.__init__ = lambda self, arquivo_estado, **k: central(self, str(pasta / "central.json"), **k)
    adquirir = instancia_unica.adquirir_instancia_unica
    instancia_unica.adquirir_instancia_unica = lambda ident, **k: adquirir(str(ident) + ".email-sonda-" + str(os.getpid()), **k)
    import laylay as root
    from mente_laylay.integracao import gmail_mental
    from mente_laylay.integracao.registro_conversa_llm import ResultadoModelo
    from mente_laylay.memoria_mental.rascunhos_email import RascunhosEmailRuntime
    root._email_runtime.rascunhos = RascunhosEmailRuntime(str(pasta / "rascunhos.sqlite3"))
    root._email_runtime.registrar_feedback = None
    root._email_runtime.pendencias._evento_cb = None
    mental = root._estado_compartilhado_runtime
    ns = dict(root._adaptadores_aplicacao_runtime._ns())
    ns["salvar_memoria"] = lambda: None
    for nome in ("_especialista_neural_comandos_runtime", "_motor_aprendizado_runtime", "_rede_associativa_runtime"):
        ns[nome] = None
    root._adaptadores_aplicacao_runtime._namespace_getter = lambda: ns
    for nome in ("_coleta_entradas_neurais", "_especialista_neural_comandos_runtime", "_interpretador_semantico_runtime", "_pesquisa_contextual_runtime"):
        root._composicao_turno_runtime._servicos[nome] = None
    falas: list[str] = []
    vozes: list[str] = []
    root._voz_runtime.falar = lambda texto, *_a, **_k: vozes.append(texto) or True
    root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda texto, *_a, **_k: falas.append(texto))
    raw = b"From: Loja <loja@example.com>\r\nSubject: Sua entrega\r\nMessage-ID: <pedido@example.com>\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nSeu teclado chega amanha. Rastreio AB123."
    chamadas: list[str] = []
    class IMAP:
        capabilities = (b"X-GM-EXT-1",)
        def __init__(self, *a, **k): pass
        def login(self, *a): return "OK", []
        def capability(self): return "OK", [b"IMAP4rev1 X-GM-EXT-1"]
        def select(self, *a, **k):
            assert k.get("readonly") is True
            return "OK", [b"1"]
        def response(self, _): return "UIDVALIDITY", [b"7"]
        def uid(self, comando, *a):
            chamadas.append(comando)
            if comando == "search": return "OK", [b"10"]
            assert comando == "fetch", "nenhuma mutação é permitida nesta sonda"
            if a[-1] == "(RFC822.SIZE)": return "OK", [b"1 (RFC822.SIZE 220)"]
            return "OK", [(b"1 (UID 10 X-GM-MSGID 100 X-GM-THRID 90)", raw), b")"]
        def logout(self): return "BYE", []
    gmail_mental.imaplib.IMAP4_SSL = IMAP
    root._gmail_runtime.runtime.mental.usuario = "fixture@example.com"
    root._gmail_runtime.runtime.mental.app_password = "fixture-local"
    if not modelo_real:
        class Modelo:
            def executar(self, pedido):
                if pedido.contrato_saida and pedido.contrato_saida.nome == "autoria_rascunho_email":
                    dados = {"assunto": "Prazo do relatório", "corpo": "O relatório será enviado na sexta."}
                else:
                    dados = {"resposta": "A mensagem informa a entrega de um teclado.", "evidencias": [1], "ausente": False}
                return ResultadoModelo(json.dumps(dados), True)
            def diagnostico(self): return {"disponivel": True}
        object.__setattr__(root._registro_modelo_llm_runtime, "servico", Modelo())
    traces = []
    original_modelo = root._email_runtime.enviar_modelo
    def observar_modelo(mensagens, **opcoes):
        resposta = original_modelo(mensagens, **opcoes)
        traces.append({"contrato": opcoes["_contrato_saida"].nome, "mensagens": mensagens, "resposta": resposta})
        return resposta
    root._email_runtime.enviar_modelo = observar_modelo
    envios = []
    root._gmail_runtime.enviar_rascunho = lambda r: envios.append({"id": r["id"], "versao": r["versao"],
        "para": r["para"], "corpo": r["corpo"]}) or {"ok": True, "status": "email_enviado", "confirmado": True}
    exec_ctx = root._contexto_intencao_runtime.montar()
    dispatch_ctx = root._contexto_dispatcher_runtime.montar()
    saida = {"instalacao": {
        "contexto_executor": exec_ctx.get("_email_executar").__self__ is root._email_runtime,
        "contexto_dispatcher": dispatch_ctx.get("_email_executar").__self__ is root._email_runtime,
        "contexto_detector": root._composicao_entrada_interacao_runtime._snapshot_deteccao().get("_email_detectar").__self__ is root._email_runtime,
        "estado_unico": root._email_runtime.estado is mental,
        "pendencia_unica": root._email_runtime.pendencias is root._pendencia_acao_runtime,
    }, "modelo_real": modelo_real, "casos": []}
    root._email_runtime.executar("EMAIL_READ", {}, "lê meus emails")
    for texto in ("que tipo de entrega?", "tem código de rastreio?", "lê ele", "explica melhor"):
        antes = len(falas)
        antes_voz = len(vozes)
        root._composicao_turno_runtime.iniciar(texto, origem="sonda_email")
        comando = root.detectar_intencao_deterministica(texto)
        tratado = root._processar_comandos_prioritarios(texto)
        saida["casos"].append({"texto": texto, "comando": comando,
            "tratado": tratado, "falas": falas[antes:], "vozes": vozes[antes_voz:],
            "status": mental.mental.get("ultima_acao_status")})
    leitura = root._email_runtime.executar("EMAIL_READ", {"modo": "conteudo"}, "entrega de quê?")
    saida["conteudo"] = {k: leitura.get(k) for k in ("status", "fala", "interpretacao_gerada", "citacoes")}
    rascunho = root._email_runtime.executar("EMAIL_DRAFT", {"para": ["cliente@example.com"], "instrucao": "Prepare um e-mail dizendo que o relatório será enviado na sexta."}, "prepara um email")
    saida["rascunho"] = {k: rascunho.get(k) for k in ("ok", "status", "fala")}
    saida["operacoes"] = []
    for texto in ("prepara um email para cliente@example.com dizendo que o relatório será enviado na sexta",
                  "deixa mais formal", "envia esse email", "pode abrir", "sim", "sim"):
        antes = len(falas)
        antes_envios = len(envios)
        root._composicao_turno_runtime.iniciar(texto, origem="sonda_email")
        comando = root.detectar_intencao_deterministica(texto)
        tratado = root._processar_comandos_prioritarios(texto)
        saida["operacoes"].append({"texto": texto, "comando": comando, "tratado": tratado,
            "falas": falas[antes:], "novos_envios": len(envios) - antes_envios,
            "pendencia": bool(root._pendencia_acao_runtime.obter()), "status": mental.mental.get("ultima_acao_status")})
    saida["envios_sinteticos"] = envios
    # Um alvo explícito continua exato mesmo com outro rascunho selecionado.
    outro = root._email_runtime.executar("EMAIL_DRAFT", {"para": ["outro@example.com"],
        "assunto": "Outro rascunho", "corpo": "Mensagem sintética distinta."}, "cria um rascunho")
    saida["identidade_rascunhos"] = []
    for texto in (f"descarta o rascunho {rascunho['rascunho_id']}",
                  "envia o rascunho id inexistente", f"mostra o rascunho {outro['rascunho_id']}"):
        antes_envios = len(envios)
        root._composicao_turno_runtime.iniciar(texto, origem="sonda_email")
        comando = root.detectar_intencao_deterministica(texto)
        tratado = root._processar_comandos_prioritarios(texto)
        saida["identidade_rascunhos"].append({"texto": texto, "comando": comando, "tratado": tratado,
            "status": mental.mental.get("ultima_acao_status"), "novos_envios": len(envios) - antes_envios,
            "ativo": mental.mental.get("rascunho_email_atual"), "outro_id": outro["rascunho_id"],
            "pendencia": bool(root._pendencia_acao_runtime.obter())})
    saida["somente_leitura_imap"] = set(chamadas) <= {"search", "fetch"}
    saida["catalogo"] = root._mapa_habilidades_runtime.responder_pergunta_capacidade("você consegue entender e responder meus emails?")
    class TimerControlado:
        def __init__(self,*a): self.daemon=False
        def is_alive(self): return False
        def start(self): pass
    root._voz_runtime.timer_factory=TimerControlado
    root._voz_runtime.avaliar_proatividade_cb=lambda **kw: {"acao":"emitir"}
    root._voz_runtime.proativa_buffer=[]
    root._voz_runtime.proativa_timer=None
    root._voz_runtime._ultima_fala_normal_ts=0
    amostra=root._gmail_runtime.consultar_mensagens(nao_lidos=True)["mensagens"][0]
    root._central_notificacoes_runtime.ingerir_emails([amostra])
    agendado_antes=bool(root._voz_runtime.proativa_buffer)
    antes=len(falas)
    root._composicao_turno_runtime.iniciar("le meus emails",origem="sonda_email")
    tratado=root._processar_comandos_prioritarios("le meus emails")
    resposta_manual=len(falas)-antes
    antes_flush=len(falas)
    for item in root._voz_runtime.proativa_buffer: item["nao_antes_ts"]=0
    root._voz_runtime.flush_fala_proativa()
    repetidos_antes=len(falas)-antes_flush
    pendentes_depois=root._central_notificacoes_runtime.diagnostico()["pendentes"]
    # Consulta antes da captura pelo monitor também deve satisfazer o aviso.
    root._central_notificacoes_runtime.ingerir_emails([{**amostra,"uid":amostra["uid"]}])
    repetido_depois=bool(root._voz_runtime.proativa_buffer)
    root._central_notificacoes_runtime.ingerir_emails([{**amostra,"uid":"fixture:novo", "assunto":"Outra mensagem nova", "referencia_email":{}}])
    novo_agendado=bool(root._voz_runtime.proativa_buffer)
    for item in root._voz_runtime.proativa_buffer: item["nao_antes_ts"]=0
    root._voz_runtime.flush_fala_proativa()
    saida["notificacao_apos_consulta"]={"agendado_antes":agendado_antes,"tratado":tratado,
        "respostas_manuais":resposta_manual,"repetidos_apos_flush":repetidos_antes,
        "pendentes_depois":pendentes_depois,"repetido_agendado_depois":repetido_depois,
        "novo_agendado":novo_agendado,"novos_textos":falas[antes_flush:]}
    saida["modelo_traces"] = traces
    return saida


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--saida", required=True, type=Path)
    parser.add_argument("--modelo-real", action="store_true")
    args = parser.parse_args()
    resultado = coletar(args.saida, args.modelo_real)
    (args.saida / "relatorio.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.__stdout__.write("EMAIL_SONDA " + json.dumps(resultado, ensure_ascii=False) + "\n")
