"""Contratos de identidade, conteúdo observado e operações de e-mail."""
from __future__ import annotations

import json
import time
import pytest

from mente_laylay.cognicao.linguagem_email import detectar_email
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno, autoriza_execucao_efetiva
from mente_laylay.especialistas.email_runtime import EmailRuntime
from mente_laylay.integracao.caixa_gmail import extrair_conteudo_mime
from mente_laylay.integracao.registro_conversa_llm import ResultadoModelo
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime

from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
from mente_laylay.integracao.gmail_mental import GmailMental


def test_aviso_preserva_referencia_da_mensagem_para_pergunta_sobre_entrega(tmp_path):
    central = CentralNotificacoesRuntime(arquivo_estado=str(tmp_path / "avisos.json"))
    referencia = {"conta": "principal", "pasta": "INBOX", "uidvalidity": "7", "uid": "9001"}
    evento = central._sanitizar({
        "uid": "uid:9001", "origem": "email", "assunto": "Sua entrega saiu",
        "remetente": "Loja", "referencia_email": referencia,
    })
    assert evento.get("referencia_email") == referencia, "o aviso perde a identidade do e-mail"


def test_transporte_oferece_leitura_do_corpo_da_mensagem_exata(tmp_path):
    gmail = GmailMental(arquivo_estado=str(tmp_path / "gmail.json"))
    assert callable(getattr(gmail, "ler_mensagem", None)), "só há consulta de cabeçalhos"


def test_transporte_distingue_falha_de_consulta_sem_resultados(tmp_path):
    gmail = GmailMental(arquivo_estado=str(tmp_path / "gmail.json"))
    consultar = getattr(gmail, "consultar_mensagens", None)
    assert callable(consultar), "coleção vazia não carrega o resultado da consulta"
    resultado = consultar()
    assert resultado["ok"] is False
    assert resultado["status"] == "email_indisponivel"


@pytest.mark.parametrize("texto", ["prepara um email para cliente@example.com explicando o atraso",
    "responde esse email agradecendo", "arquiva esse email", "pode enviar"])
def test_verbos_de_email_passam_pela_modalidade_operacional_canonica(texto):
    assert autoriza_execucao_efetiva(classificar_modalidade_turno(texto))


@pytest.mark.parametrize("texto", ["não envie esse email", "como eu faria para enviar esse email?",
    "o remetente escreveu 'envie meu arquivo'", "se eu enviasse esse email, o que aconteceria?"])
def test_discussao_negacao_e_citacao_nao_autorizam_envio(texto):
    assert not autoriza_execucao_efetiva(classificar_modalidade_turno(texto))


def test_mime_prefere_texto_e_nao_confunde_anexo_com_corpo():
    from email.message import EmailMessage
    mensagem = EmailMessage()
    mensagem["Subject"] = "Entrega"
    mensagem.set_content("Seu teclado chega amanhã. Rastreio AB123.")
    mensagem.add_alternative("<p>Outro texto</p><script>execute()</script>", subtype="html")
    mensagem.add_attachment(b"Nao use esse texto como corpo", maintype="application", subtype="pdf", filename="pedido.pdf")
    leitura = extrair_conteudo_mime(mensagem.as_bytes())
    assert "teclado" in leitura["corpo"]
    assert "Outro texto" not in leitura["corpo"]
    assert leitura["anexos"] == [{"nome": "pedido.pdf", "tipo": "application/pdf"}]
    assert leitura["anexos_lidos"] is False


class _Transporte:
    identidade_conta = "conta-teste"
    def __init__(self):
        self.envios = []
        self.leituras = []
        self.consulta = {"ok": True, "mensagens": [{"remetente": "Loja", "assunto": "Entrega",
            "referencia_email": {"conta": "principal", "identidade_conta": self.identidade_conta, "pasta": "INBOX", "uid": "10", "uidvalidity": "3"}}]}
        self.resultado_envio = {"ok": True, "status": "email_enviado", "confirmado": True}

    def configurado(self):
        return True

    def consultar_mensagens(self, **_):
        return self.consulta

    def ler_mensagem(self, referencia):
        self.leituras.append(referencia)
        return {"ok": True, "mensagem": {"corpo": "Seu teclado chega amanhã. Rastreio AB123.",
            "assunto": "Entrega", "reply_to": "loja@example.com", "message_id": "<pedido@example.com>",
            "remetente": "Loja", "referencia_email": referencia}}

    def enviar_rascunho(self, rascunho):
        self.envios.append(rascunho)
        return dict(self.resultado_envio)


class _Modelo:
    def __init__(self):
        self.pedidos = []
        self.resposta = {"resposta": "A mensagem informa a entrega de um teclado.",
                         "evidencias": [1], "ausente": False}
    def executar(self, pedido):
        self.pedidos.append(pedido)
        return ResultadoModelo(json.dumps(self.resposta), True)
    def diagnostico(self):
        return {"disponivel": True}


def _runtime(tmp_path):
    estado = EstadoCompartilhadoRuntime()
    pendencias = PendenciaAcaoRuntime(estado_getter=lambda: estado.mental,
        estado_atualizar=lambda f: estado.atualizar("mental", f), log=lambda _: None)
    transporte = _Transporte()
    modelo = _Modelo()
    runtime = EmailRuntime(transporte=transporte, estado=estado, pendencias=pendencias,
        arquivo_rascunhos=str(tmp_path / "rascunhos.sqlite3"), modelo_llm=modelo)
    return runtime, transporte, modelo, estado, pendencias


def test_pergunta_sobre_entrega_le_corpo_da_mensagem_e_conserva_evidencia(tmp_path):
    runtime, transporte, modelo, estado, _ = _runtime(tmp_path)
    assert runtime.executar("EMAIL_READ", {}, "lê meus emails")["confirmado"]
    comando = runtime.detectar("que tipo de entrega?")
    assert comando == {"intent": "EMAIL_READ", "params": {"modo": "conteudo", "pergunta": "que tipo de entrega?"}}
    resultado = runtime.executar(comando["intent"], comando["params"], "que tipo de entrega?")
    assert transporte.leituras == [transporte.consulta["mensagens"][0]["referencia_email"]]
    assert resultado["citacoes"] == ["Seu teclado chega amanhã."]
    assert "teclado" in resultado["fala"]
    assert modelo.pedidos[-1].com_tools is False
    assert modelo.pedidos[-1].contexto_fechado is True
    assert "corpo" not in json.dumps(estado.mental["email_contexto"])
    assert not list(tmp_path.glob("*.sqlite3")), "ler e-mail não deve persistir seu corpo"


def test_referencia_inventada_nao_e_publicada_como_compreensao(tmp_path):
    runtime, _, modelo, _, _ = _runtime(tmp_path)
    runtime.executar("EMAIL_READ", {}, "lê meus emails")
    modelo.resposta["evidencias"] = [999]
    modelo.resposta["resposta"] = "É um notebook."
    resultado = runtime.executar("EMAIL_READ", {"modo": "conteudo"}, "entrega de quê?")
    assert resultado["interpretacao_gerada"] is False
    assert "notebook" not in resultado["fala"]
    assert "Trecho original" in resultado["fala"]


def test_filtro_sem_resultados_nao_reutiliza_mensagens_de_outro_remetente(tmp_path):
    runtime, _, _, estado, _ = _runtime(tmp_path)
    resultado = runtime.executar("EMAIL_READ", {"remetente": "professor"}, "emails do professor")
    assert "Não encontrei" in resultado["fala"]
    assert estado.mental["email_contexto"]["mensagens"] == []


def _criar_rascunho(runtime):
    resultado = runtime.executar("EMAIL_DRAFT", {"para": ["cliente@example.com"], "assunto": "Prazo",
        "corpo": "O relatório será enviado na sexta."}, "cria um rascunho")
    assert resultado["confirmado"] is True
    return resultado


def test_envio_exige_revisao_e_confirmacao_da_versao_atual(tmp_path):
    runtime, transporte, _, _, pendencias = _runtime(tmp_path)
    criado = _criar_rascunho(runtime)
    assert runtime.executar("EMAIL_CONFIRM", {}, "sim")["ok"] is False
    assert transporte.envios == []
    revisao = runtime.executar("EMAIL_SEND", {}, "envia esse email")
    assert revisao["executou"] is False and revisao["status"] == "aguardando_confirmacao"
    assert "cliente@example.com" in revisao["fala"]
    assert "corpo" not in json.dumps(pendencias.obter()["metadados"])
    assert transporte.envios == []
    resultado = runtime.executar("EMAIL_CONFIRM", {}, "sim")
    assert resultado["status"] == "email_enviado" and resultado["confirmado"] is True
    assert len(transporte.envios) == 1
    assert runtime.rascunhos.obter(transporte.identidade_conta, criado["rascunho_id"])["estado"] == "enviado"
    assert runtime.executar("EMAIL_CONFIRM", {}, "sim")["ok"] is False
    assert len(transporte.envios) == 1


def test_editar_invalida_confirmacao_anterior_e_preserva_rascunho(tmp_path):
    runtime, transporte, _, _, pendencias = _runtime(tmp_path)
    criado = _criar_rascunho(runtime)
    runtime.executar("EMAIL_SEND", {}, "envia esse email")
    editado = runtime.executar("EMAIL_DRAFT", {"acao": "editar", "corpo": "O relatório será enviado na segunda."}, "troca o prazo")
    assert editado["versao"] == 2
    assert pendencias.obter() is None
    assert runtime.executar("EMAIL_CONFIRM", {}, "sim")["ok"] is False
    assert transporte.envios == []
    assert runtime.rascunhos.obter(transporte.identidade_conta, criado["rascunho_id"])["corpo"].endswith("segunda.")


def test_recusa_e_comando_novo_nao_enviam_rascunho(tmp_path):
    runtime, transporte, _, _, pendencias = _runtime(tmp_path)
    _criar_rascunho(runtime)
    runtime.executar("EMAIL_SEND", {}, "envia esse email")
    assert runtime.executar("EMAIL_CONFIRM", {}, "mostra minhas playlists")["ok"] is False
    assert pendencias.obter()["status"] == "ativa"
    assert runtime.executar("EMAIL_CONFIRM", {}, "não")["status"] == "email_cancelado"
    assert transporte.envios == []


@pytest.mark.parametrize("texto", ["pode abrir", "abre", "pode falar", "toca"])
def test_confirmacao_de_outro_verbo_nao_autoriza_envio(texto, tmp_path):
    runtime, transporte, _, _, pendencias = _runtime(tmp_path)
    _criar_rascunho(runtime)
    runtime.executar("EMAIL_SEND", {}, "envia esse email")
    resultado = runtime.executar("EMAIL_CONFIRM", {}, texto)
    assert resultado["ok"] is False
    assert transporte.envios == []
    assert pendencias.obter()["status"] == "ativa"


@pytest.mark.parametrize("texto", ["abre o Chrome", "apaga o arquivo teste.txt", "deixa o volume em 20",
    "manda tocar uma música", "cria uma pasta chamada emails"])
def test_rascunho_ativo_nao_captura_comando_independente(texto):
    assert detectar_email(texto, rascunho_ativo=True, contexto_ativo=True) is None


@pytest.mark.parametrize("texto", ["prepara um email para cliente@example.com para enviar amanhã",
    "cria um rascunho dizendo que vou enviar o relatório amanhã"])
def test_verbo_citado_no_conteudo_nao_muda_criacao_para_envio(texto):
    comando = detectar_email(texto, rascunho_ativo=True, contexto_ativo=True)
    assert comando["intent"] == "EMAIL_DRAFT"
    assert comando["params"]["acao"] == "criar"


@pytest.mark.parametrize("status,confirmado", [("email_envio_incerto", None), ("email_envio_parcial", False)])
def test_envio_incerto_ou_parcial_nao_pode_ser_repetido_automaticamente(tmp_path, status, confirmado):
    runtime, transporte, _, _, _ = _runtime(tmp_path)
    transporte.resultado_envio = {"ok": False, "status": status, "confirmado": confirmado}
    _criar_rascunho(runtime)
    runtime.executar("EMAIL_SEND", {}, "envia esse email")
    resultado = runtime.executar("EMAIL_CONFIRM", {}, "sim")
    assert resultado["status"] == status and resultado["confirmado"] is confirmado
    assert runtime.executar("EMAIL_SEND", {}, "envia de novo")["ok"] is False
    assert len(transporte.envios) == 1


def test_aviso_so_publica_referencia_depois_da_entrega(tmp_path):
    runtime, _, _, estado, _ = _runtime(tmp_path)
    callbacks = []
    central = CentralNotificacoesRuntime(arquivo_estado=str(tmp_path / "avisos.json"),
        agendar_fala_cb=lambda *_, **kw: callbacks.append(kw["ao_concluir"]) or True,
        contexto_atualizar_cb=lambda **campos: estado.atualizar_campos("mental", **campos))
    central.ingerir_emails([{"uid": "uid:55", "remetente": "Loja", "assunto": "Entrega",
        "prioritario": True, "referencia_email": {"conta": "principal", "uid": "55", "uidvalidity": "1"}}])
    assert "email_contexto" not in estado.mental
    callbacks[0](False, "falha_voz")
    assert "email_contexto" not in estado.mental
    callbacks[0](True, "voz_entregue")
    assert estado.mental["email_contexto"]["mensagens"][0]["referencia_email"]["uid"] == "55"
    assert runtime.contexto_ativo()


def test_anexo_usa_a_fronteira_compartilhada_de_leitura_de_arquivos(tmp_path):
    from mente_laylay.arquivos.pesquisa_semantica import PesquisaSemanticaArquivosRuntime
    arquivos = PesquisaSemanticaArquivosRuntime(raizes=[tmp_path])
    ler = getattr(arquivos, "ler_anexo", None)
    assert callable(ler), "falta receipt binário no owner compartilhado de arquivos"
    alvo = tmp_path / "relatorio.pdf"
    alvo.write_bytes(b"relatorio-de-teste")
    resultado = ler(str(alvo))
    assert resultado["ok"] and resultado["confirmado"]
    assert resultado["dados"] == b"relatorio-de-teste"
    assert resultado["manifesto"]["tamanho"] == len(resultado["dados"])


def _conectar_anexos(runtime, tmp_path):
    from mente_laylay.arquivos.pesquisa_semantica import PesquisaSemanticaArquivosRuntime
    from mente_laylay.integracao.registro_arquivos import registrar_arquivos_leitura
    from mente_laylay.autonomia.quadro_cooperacao import QuadroCooperacaoRuntime
    from mente_laylay.autonomia.orquestracao_cooperativa import OrquestradorCooperativoRuntime
    quadro = QuadroCooperacaoRuntime(log=lambda _: None)
    runtime.arquivos = registrar_arquivos_leitura(PesquisaSemanticaArquivosRuntime(raizes=[tmp_path]))
    runtime.cooperacao = OrquestradorCooperativoRuntime(quadro=quadro, clipboard_snapshot=lambda: {},
        clipboard_getter=lambda: "", executar_intencao=lambda *_: False, resolver_caminho=lambda v: v,
        falar=lambda *_: None, autorizar_acao=lambda _acao, texto, **k: {"permitido": k.get("confirmado")
            or autoriza_execucao_efetiva(classificar_modalidade_turno(texto))}, log=lambda _: None)
    return quadro


def test_cooperacao_valida_anexo_antes_do_rascunho_e_revalida_antes_do_envio(tmp_path):
    runtime, transporte, _, _, _ = _runtime(tmp_path)
    quadro = _conectar_anexos(runtime, tmp_path)
    arquivo = tmp_path / "relatorio.pdf"
    arquivo.write_bytes(b"conteudo-original")
    r = runtime.executar("EMAIL_DRAFT", {"para": ["cliente@example.com"], "assunto": "Relatório",
        "corpo": "Segue o relatório.", "anexos": [str(arquivo)]}, "cria um rascunho com anexo")
    assert r["ok"]
    assert "relatorio.pdf" in r["fala"]
    plano = quadro.snapshot()["planos_recentes"][-1]
    assert plano["estado"] == "confirmado"
    runtime.executar("EMAIL_SEND", {}, "envia o rascunho")
    resultado = runtime.executar("EMAIL_CONFIRM", {}, "sim")
    assert resultado["ok"]
    assert transporte.envios[0]["anexos_preparados"] == [{"nome": "relatorio.pdf", "dados": b"conteudo-original"}]


def test_anexo_alterado_bloqueia_envio_e_falha_parcial_nao_salva_rascunho(tmp_path):
    runtime, transporte, _, _, _ = _runtime(tmp_path)
    quadro = _conectar_anexos(runtime, tmp_path)
    arquivo = tmp_path / "relatorio.pdf"
    arquivo.write_bytes(b"primeiro")
    params = {"para": ["cliente@example.com"], "assunto": "Relatório", "corpo": "Segue relatório.", "anexos": [str(arquivo)]}
    assert runtime.executar("EMAIL_DRAFT", params, "cria um rascunho com anexo")["ok"]
    runtime.executar("EMAIL_SEND", {}, "envia o rascunho")
    arquivo.write_bytes(b"segundo")
    resultado = runtime.executar("EMAIL_CONFIRM", {}, "sim")
    assert resultado["status"] == "anexo_alterado"
    assert transporte.envios == []
    assert runtime.executar("EMAIL_DRAFT", {**params, "anexos": [str(arquivo), str(tmp_path / 'ausente.pdf')]}, "cria outro rascunho")["ok"] is False
    assert len(runtime.rascunhos.listar(transporte.identidade_conta)) == 1
    assert quadro.snapshot()["planos_recentes"][-1]["estado"] == "falhou"


def test_leitura_de_anexo_nao_contorna_raizes_e_credenciais(tmp_path):
    runtime, _, _, _, _ = _runtime(tmp_path)
    _conectar_anexos(runtime, tmp_path)
    segredo = tmp_path / "credenciais.env"
    segredo.write_text("fixture-sem-segredo")
    assert runtime.arquivos.ler_anexo(str(segredo))["ok"] is False
    assert runtime.arquivos.ler_anexo(str(tmp_path.parent / "fora.txt"))["ok"] is False


@pytest.mark.parametrize("texto", ["qual é a capital da França?", "o que é SQLite?", "quais meus emails?", "como eu faria para enviar esse email?"])
def test_email_ativo_nao_captura_assunto_novo_ou_inventario_como_pergunta_da_mensagem(texto):
    assert detectar_email(texto, contexto_ativo=True) is None


def test_selecao_preserva_lista_para_voltar_ao_email_anterior(tmp_path):
    runtime, transporte, _, estado, _ = _runtime(tmp_path)
    transporte.consulta["mensagens"].append({"remetente": "Outra pessoa", "assunto": "Outro assunto",
        "referencia_email": {**transporte.consulta["mensagens"][0]["referencia_email"], "uid": "11"}})
    runtime.executar("EMAIL_READ", {}, "lê meus emails")
    assert runtime.executar("EMAIL_READ", {"modo": "conteudo", "indice": 2}, "lê o segundo")["ok"]
    assert len(estado.mental["email_contexto"]["mensagens"]) == 2
    assert estado.mental["email_contexto"]["indice_atual"] == 2
    comando = runtime.detectar("volta ao anterior")
    assert runtime.executar(comando["intent"], comando["params"], "volta ao anterior")["ok"]
    assert transporte.leituras[-1]["uid"] == "10"


def _gmail_rede(tmp_path, monkeypatch, *, validade="7", search_status="OK"):
    from mente_laylay.integracao import gmail_mental
    chamadas = []
    raw = b"From: Loja <loja@example.com>\r\nSubject: Entrega\r\nContent-Type: text/plain\r\n\r\nSeu teclado chega amanha."
    class Conexao:
        def __init__(self, *a, **k): pass
        def login(self, *a): return "OK", []
        def capability(self): return "OK", [b"IMAP4rev1 X-GM-EXT-1"]
        def select(self, *a, **k):
            chamadas.append(("select", k))
            return "OK", [b"1"]
        def response(self, _): return "UIDVALIDITY", [validade.encode()]
        def uid(self, comando, *a):
            chamadas.append((comando, a))
            if comando == "search": return search_status, [b"10"]
            if a[-1] == "(RFC822.SIZE)": return "OK", [b"1 (RFC822.SIZE 120)"]
            return "OK", [(b"1 (UID 10 X-GM-MSGID 100 X-GM-THRID 90)", raw), b")"]
        def logout(self):
            chamadas.append(("logout",))
            return "BYE", []
    monkeypatch.setattr(gmail_mental.imaplib, "IMAP4_SSL", Conexao)
    gmail = GmailMental(arquivo_estado=str(tmp_path / "gmail.json"), usuario="fixture@example.com", app_password="fixture")
    return gmail, chamadas


def test_imap_le_corpo_sem_marcar_lido_e_preserva_conta_pasta_e_validade(tmp_path, monkeypatch):
    gmail, chamadas = _gmail_rede(tmp_path, monkeypatch)
    consulta = gmail.consultar_mensagens()
    ref = consulta["mensagens"][0]["referencia_email"]
    assert ref["conta"] == "principal" and ref["pasta"] == "INBOX" and ref["uidvalidity"] == "7"
    assert ref["gmail_id"] == "100" and ref["conversa_id"] == "90"
    leitura = gmail.ler_mensagem(ref)
    assert leitura["confirmado"] and "teclado" in leitura["mensagem"]["corpo"]
    assert all(c[1]["readonly"] for c in chamadas if c[0] == "select")
    assert any(c[0] == "fetch" and c[1][-1] == "(BODY.PEEK[])" for c in chamadas)
    assert not any(c[0] == "store" for c in chamadas)


@pytest.mark.parametrize("campo,valor", [("uidvalidity", "6"), ("identidade_conta", "outra"), ("uid", "1:*"), ("conta", "secundaria")])
def test_identidade_divergente_nao_le_ou_altera_outro_email(tmp_path, monkeypatch, campo, valor):
    gmail, chamadas = _gmail_rede(tmp_path, monkeypatch)
    ref = gmail.consultar_mensagens()["mensagens"][0]["referencia_email"]
    chamadas.clear()
    ref[campo] = valor
    assert gmail.ler_mensagem(ref)["ok"] is False
    assert gmail.alterar_mensagem(ref, "marcar_lido")["ok"] is False
    assert not any(c[0] in {"fetch", "store"} for c in chamadas)


def test_imap_nao_promove_retorno_no_a_consulta_vazia_bem_sucedida(tmp_path, monkeypatch):
    gmail, chamadas = _gmail_rede(tmp_path, monkeypatch, search_status="NO")
    resultado = gmail.consultar_mensagens()
    assert resultado["ok"] is False and resultado["mensagens"] == []
    assert chamadas[-1] == ("logout",)


def test_smtp_confirma_aceitacao_sem_prometer_entrega_e_preserva_cc_bcc(tmp_path, monkeypatch):
    import mente_laylay.integracao.caixa_gmail as modulo
    capturado = {}
    class SMTP:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def login(self, *a): pass
        def send_message(self, mensagem, **kwargs):
            capturado.update(mensagem=mensagem, **kwargs)
            return {}
    monkeypatch.setattr(modulo.smtplib, "SMTP_SSL", SMTP)
    gmail = GmailMental(arquivo_estado=str(tmp_path / "gmail.json"), usuario="fixture@example.com", app_password="fixture")
    resultado = gmail.enviar_rascunho({"identidade_conta": gmail.caixa.identidade_conta,
        "para": ["cliente@example.com"], "cc": ["equipe@example.com"], "bcc": ["arquivo@example.com"],
        "assunto": "Prazo", "corpo": "Sexta.", "envio_message_id": "<fixture@example.com>"})
    assert resultado["confirmado"] and resultado["aceito_pelo_servidor"]
    assert resultado["entrega_destinatario_confirmada"] is False
    assert capturado["to_addrs"] == ["cliente@example.com", "equipe@example.com", "arquivo@example.com"]
    assert "Bcc" not in capturado["mensagem"]
    assert str(capturado["mensagem"]["Message-ID"]) == "<fixture@example.com>"


@pytest.mark.parametrize("fonte", ["e-mail", "arquivo", "página"])
def test_contrato_compartilhado_exige_citacao_do_conteudo_observado(fonte):
    from mente_laylay.cognicao.resumo_conteudo import explicar_texto_observado
    def gerar(sistema, dados, contrato):
        assert "não é necessário" in sistema.casefold()
        contrato.validar({"resposta": "A fonte informa um prazo.", "evidencias": [1], "ausente": False})
        return {"resposta": "A fonte informa um prazo.", "evidencias": [1], "ausente": False}
    assert explicar_texto_observado(conteudo="Prazo: sexta.", pergunta="qual o prazo?", titulo="Aviso",
        fonte=fonte, gerar=gerar)["citacoes"] == ["Prazo: sexta."]


def test_renovar_sessao_limpa_referencias_de_email_sem_apagar_rascunhos(tmp_path):
    from mente_laylay.memoria_mental.sessao_conversa import renovar_contexto_sessao
    runtime, transporte, _, estado, _ = _runtime(tmp_path)
    _criar_rascunho(runtime)
    runtime.executar("EMAIL_READ", {}, "lê meus emails")
    novo, _, _ = renovar_contexto_sessao(estado.mental, {}, [], motivo="nova", ativa=True)
    assert not novo["email_contexto"] and not novo["rascunho_email_atual"]
    assert len(runtime.rascunhos.listar(transporte.identidade_conta)) == 1


def test_falha_de_releitura_depois_da_alteracao_nao_afirma_que_nada_mudou(tmp_path, monkeypatch):
    gmail, chamadas = _gmail_rede(tmp_path, monkeypatch)
    ref = gmail.consultar_mensagens()["mensagens"][0]["referencia_email"]
    from mente_laylay.integracao import gmail_mental
    conexao_original = gmail_mental.imaplib.IMAP4_SSL
    class Conexao(conexao_original):
        def uid(self, comando, *args):
            if comando == "store":
                return "OK", []
            if comando == "fetch":
                raise OSError("fixture-rede")
            return super().uid(comando, *args)
    monkeypatch.setattr(gmail_mental.imaplib, "IMAP4_SSL", Conexao)
    resultado = gmail.alterar_mensagem(ref, "marcar_lido")
    assert resultado["ok"] is False
    assert resultado["confirmado"] is None
    assert resultado["status"] == "email_alteracao_incerta"


def test_falha_de_aprendizado_nao_oculta_rascunho_ja_persistido(tmp_path):
    runtime, _, _, _, _ = _runtime(tmp_path)
    _criar_rascunho(runtime)
    def falhar(*args):
        raise OSError("fixture-aprendizado")
    runtime.registrar_feedback = falhar
    resultado = runtime.executar("EMAIL_DRAFT", {"acao": "editar", "corpo": "Prazo corrigido: segunda."}, "troca o prazo")
    assert resultado["ok"] and resultado["confirmado"] and resultado["versao"] == 2


def test_proposta_com_assinatura_inventada_nao_e_salva(tmp_path):
    runtime, _, modelo, _, _ = _runtime(tmp_path)
    modelo.resposta = {"assunto": "Prazo", "corpo": "O relatório sai sexta.\n[Seu Nome]"}
    resultado = runtime.executar("EMAIL_DRAFT", {"instrucao": "avise que o relatório sai sexta"}, "prepara um rascunho")
    assert resultado["ok"] is False and resultado["status"] == "rascunho_com_campos_inventados"
    assert runtime.rascunhos.listar(runtime.transporte.identidade_conta) == []


def test_enviar_email_novo_prepara_rascunho_e_revisao_sem_reusar_o_antigo(tmp_path):
    runtime, transporte, modelo, _, pendencias = _runtime(tmp_path)
    antigo = _criar_rascunho(runtime)
    modelo.resposta = {"assunto": "Reunião", "corpo": "A reunião ficou para segunda-feira."}
    comando = runtime.detectar("envia um email para equipe@example.com dizendo que a reunião ficou para segunda")
    assert comando["params"]["criar_rascunho"]
    resultado = runtime.executar(comando["intent"], comando["params"], "envia um email para equipe@example.com dizendo que a reunião ficou para segunda")
    assert resultado["status"] == "aguardando_confirmacao"
    assert "equipe@example.com" in resultado["fala"] and "cliente@example.com" not in resultado["fala"]
    assert pendencias.obter()["referencia"] != antigo["rascunho_id"]
    assert transporte.envios == []


@pytest.mark.parametrize("texto", ["lê ele", "explica melhor", "como assim?", "quando chega?"])
def test_continuacao_natural_consulta_a_mensagem_selecionada(texto, tmp_path):
    runtime, _, _, _, _ = _runtime(tmp_path)
    runtime.executar("EMAIL_READ", {}, "lê meus emails")
    comando = runtime.detectar(texto)
    assert comando and comando["intent"] == "EMAIL_READ" and comando["params"]["modo"] == "conteudo"


def test_feedback_de_email_usa_motor_compartilhado_sem_aprender_conteudo_da_mensagem(tmp_path):
    from memoria_sqlite import MemoriaSQLite
    from mente_laylay.memoria_mental.motor_aprendizado import MotorAprendizadoRuntime
    memoria = MemoriaSQLite(str(tmp_path / "mente.sqlite"))
    motor = MotorAprendizadoRuntime(memoria_sqlite=memoria, contexto_getter=lambda: {}, log=lambda *_: None)
    runtime, _, _, _, pendencias = _runtime(tmp_path)
    pendencias._evento_cb = motor.observar_evento_pendencia
    runtime.registrar_feedback = lambda tipo, ref: motor.registrar_feedback_contextual(
        tipo=tipo, aceito=None, resultado=tipo, origem="email", alvo=ref)
    r = _criar_rascunho(runtime)
    runtime.executar("EMAIL_SEND", {}, "envia esse email")
    runtime.executar("EMAIL_CONFIRM", {}, "não")
    registro = memoria.obter_hipotese_aprendizado("feedback_contextual:email:recusa:" + r["rascunho_id"])
    assert registro and "relatório" not in json.dumps(registro, ensure_ascii=False)
    assert registro["status"] != "ativa", "recusar envio não cria preferência permanente"
    editado = runtime.executar("EMAIL_DRAFT", {"acao": "editar", "corpo": "Prazo corrigido: segunda."}, "troca o prazo")
    assert editado["ok"]
    assert memoria.obter_hipotese_aprendizado("feedback_contextual:email:correcao:" + r["rascunho_id"])


def test_conversa_le_as_mensagens_do_mesmo_thread_sem_misturar_caixa(tmp_path):
    runtime, transporte, _, _, _ = _runtime(tmp_path)
    referencia = transporte.consulta["mensagens"][0]["referencia_email"]
    referencia["conversa_id"] = "90"
    runtime.executar("EMAIL_READ", {}, "lê meus emails")
    filtros = []
    consultar_original = transporte.consultar_mensagens
    transporte.consultar_mensagens = lambda **kwargs: filtros.append(kwargs) or consultar_original(**kwargs)
    comando = runtime.detectar("mostra a conversa desse email")
    assert comando["params"]["modo"] == "conversa"
    resultado = runtime.executar(comando["intent"], comando["params"], "mostra a conversa desse email")
    assert resultado["ok"]
    assert filtros == [{"conversa_id": "90", "limite": 5}]
    assert all(ref["uid"] == "10" for ref in transporte.leituras)


def test_smtp_falha_incerta_nao_e_retentada_pelo_transporte(tmp_path, monkeypatch):
    import mente_laylay.integracao.caixa_gmail as modulo
    chamadas = []
    class SMTP:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def login(self, *a): pass
        def send_message(self, *a, **k):
            chamadas.append("send")
            raise OSError("fixture-desconexao")
    monkeypatch.setattr(modulo.smtplib, "SMTP_SSL", SMTP)
    gmail = GmailMental(arquivo_estado=str(tmp_path / "gmail.json"), usuario="fixture@example.com", app_password="fixture")
    r = gmail.enviar_rascunho({"identidade_conta": gmail.caixa.identidade_conta,
        "para": ["cliente@example.com"], "assunto": "Relatório", "corpo": "Prazo: sexta."})
    assert r["status"] == "email_envio_incerto" and r["confirmado"] is None
    assert chamadas == ["send"]


def test_arquivamento_e_lixeira_releem_o_mesmo_gmail_id(tmp_path, monkeypatch):
    from mente_laylay.integracao import gmail_mental
    gmail, chamadas = _gmail_rede(tmp_path, monkeypatch)
    referencia = gmail.consultar_mensagens()["mensagens"][0]["referencia_email"]
    original = gmail_mental.imaplib.IMAP4_SSL
    class Conexao(original):
        def list(self):
            return "OK", [b'(\\All) "/" "[Gmail]/All Mail"', b'(\\Trash) "/" "[Gmail]/Trash"']
        def uid(self, comando, *a):
            chamadas.append((comando, a))
            if comando == "store": return "OK", []
            if comando == "search": return "OK", [b"12"]
            if comando == "fetch": return "OK", [b"12 (X-GM-LABELS ())"]
    monkeypatch.setattr(gmail_mental.imaplib, "IMAP4_SSL", Conexao)
    for acao in ("arquivar", "lixeira"):
        chamadas.clear()
        resultado = gmail.alterar_mensagem(referencia, acao)
        assert resultado["ok"] and resultado["confirmado"]
        assert any(c[0] == "search" and c[1][1:] == ("X-GM-MSGID", "100") for c in chamadas)


@pytest.mark.parametrize("acao", ["marcar_lido", "marcar_nao_lido", "arquivar", "lixeira"])
def test_alteracao_da_caixa_exige_confirmacao_do_alvo_exato(tmp_path, acao):
    runtime, transporte, _, _, pendencias = _runtime(tmp_path)
    efeitos = []
    transporte.alterar_mensagem = lambda referencia, operacao: efeitos.append((referencia, operacao)) or {
        "ok": True, "status": "email_alterado", "confirmado": True}
    runtime.executar("EMAIL_READ", {}, "lê meus emails")
    revisao = runtime.executar("EMAIL_MODIFY", {"acao": acao}, "altera esse email")
    assert revisao["status"] == "aguardando_confirmacao" and efeitos == []
    referencia = pendencias.obter()["metadados"]["referencia_email"]
    assert runtime.executar("EMAIL_CONFIRM", {}, "sim")["confirmado"]
    assert efeitos == [(referencia, acao)]


@pytest.mark.parametrize("verbo,intent,acao", [
    ("mostra", "EMAIL_DRAFT_READ", "mostrar"),
    ("edita", "EMAIL_DRAFT", "editar"),
    ("descarta", "EMAIL_DRAFT", "descartar"),
    ("envia", "EMAIL_SEND", None),
])
def test_id_explicito_de_rascunho_preserva_alvo_apesar_de_outro_ativo(verbo, intent, acao, tmp_path):
    runtime, _, _, _, _ = _runtime(tmp_path)
    alvo = _criar_rascunho(runtime)["rascunho_id"]
    ativo = _criar_rascunho(runtime)["rascunho_id"]
    comando = runtime.detectar(f"{verbo} o rascunho {alvo}")
    assert comando["intent"] == intent
    assert comando["params"].get("id") == alvo
    if acao:
        assert comando["params"]["acao"] == acao
    if verbo == "descarta":
        resultado = runtime.executar(intent, comando["params"], f"{verbo} o rascunho {alvo}")
        assert resultado["ok"]
        assert [r["id"] for r in runtime.rascunhos.listar(runtime.transporte.identidade_conta)] != [alvo]
        assert len(runtime.rascunhos.listar(runtime.transporte.identidade_conta)) == 1
        assert runtime._mental()["rascunho_email_atual"] == ativo


@pytest.mark.parametrize("texto", ["descarta o rascunho abc123", "envia o rascunho id inexistente"])
def test_id_invalido_nao_substitui_por_rascunho_ativo(texto, tmp_path):
    runtime, transporte, _, _, pendencias = _runtime(tmp_path)
    ativo = _criar_rascunho(runtime)["rascunho_id"]
    comando = runtime.detectar(texto)
    assert comando["params"].get("id"), "o alvo explícito foi perdido"
    resultado = runtime.executar(comando["intent"], comando["params"], texto)
    assert resultado["status"] == "rascunho_nao_encontrado"
    assert runtime.rascunhos.obter(transporte.identidade_conta, ativo)["estado"] == "rascunho"
    assert pendencias.obter() is None and transporte.envios == []


@pytest.mark.parametrize("texto", ["apaga esse email", "manda esse email para a lixeira", "manda para a lixeira esse email"])
def test_lixeira_da_mensagem_nao_revisa_envio_nem_cria_rascunho(texto):
    comando = detectar_email(texto, contexto_ativo=True, rascunho_ativo=True)
    assert comando == {"intent": "EMAIL_MODIFY", "params": {"acao": "lixeira"}}


@pytest.mark.parametrize("texto", [
    "cria um rascunho para cliente@example.com dizendo que vamos editar o prazo",
    "prepara um email para cliente@example.com explicando como descarta o arquivo",
    "cria um rascunho para cliente@example.com dizendo: troca o prazo para segunda-feira",
    "cria um rascunho para cliente@example.com dizendo: mostra o relatório na reunião",
])
def test_verbo_no_conteudo_nao_troca_operacao_de_criar_rascunho(texto):
    comando = detectar_email(texto, rascunho_ativo=True)
    assert comando["intent"] == "EMAIL_DRAFT" and comando["params"]["acao"] == "criar"


@pytest.mark.parametrize("texto", ["mostra o rascunho", "lê meu rascunho", "mostra o rascunho atual"])
def test_consulta_singular_resolve_rascunho_atual_em_vez_de_listar(texto):
    comando = detectar_email(texto, rascunho_ativo=True)
    assert comando == {"intent": "EMAIL_DRAFT_READ", "params": {"acao": "mostrar"}}


@pytest.mark.parametrize("espera,qualificado", [(301, False), (601, True)])
def test_silencio_na_revisao_usa_qualificacao_do_motor_compartilhado(espera, qualificado, tmp_path):
    from memoria_sqlite import MemoriaSQLite
    from mente_laylay.memoria_mental.motor_aprendizado import MotorAprendizadoRuntime
    memoria = MemoriaSQLite(str(tmp_path / "mente.sqlite"))
    motor = MotorAprendizadoRuntime(memoria_sqlite=memoria, contexto_getter=lambda: {}, log=lambda *_: None)
    runtime, transporte, _, _, pendencias = _runtime(tmp_path)
    agora = [1000.0]
    pendencias._agora = lambda: agora[0]
    pendencias._evento_cb = motor.observar_evento_pendencia
    criado = _criar_rascunho(runtime)
    assert runtime.executar("EMAIL_SEND", {}, "envia esse email")["status"] == "aguardando_confirmacao"
    agora[0] += espera
    assert pendencias.obter() is None and transporte.envios == []
    hipotese = memoria.obter_hipotese_aprendizado("feedback_contextual:email:silencio:" + criado["rascunho_id"])
    assert bool(hipotese) is qualificado
    if hipotese:
        assert hipotese["status"] != "ativa" and "relatório" not in json.dumps(hipotese, ensure_ascii=False)


@pytest.mark.parametrize("fonte", ["e-mail", "arquivo", "página"])
def test_modelo_referencia_trecho_e_host_materializa_citacao_literal(fonte):
    from mente_laylay.cognicao.resumo_conteudo import explicar_texto_observado
    texto = "Com o plano, voce aproveita 30% OFF\nno primeiro mes.\n\nCUPOM: CODIGO123"
    def gerar(sistema, dados, contrato):
        assert dados["trechos"][0]["texto"] == "Com o plano, voce aproveita 30% OFF\nno primeiro mes."
        proposta = {"resposta": "A fonte oferece desconto no primeiro mês.", "evidencias": [1], "ausente": False}
        contrato.validar(proposta)
        return proposta
    r = explicar_texto_observado(conteudo=texto, pergunta="o que diz?", titulo="Aviso", fonte=fonte, gerar=gerar)
    assert r["citacoes"] == ["Com o plano, voce aproveita 30% OFF\nno primeiro mes."]
    assert all(c in texto for c in r["citacoes"])


@pytest.mark.parametrize("evidencias", [[99], [True], [1.0], [1, 1], [1, 2, 3, 4, 5], []])
def test_referencia_de_evidencia_invalida_nao_materializa_texto(evidencias):
    from mente_laylay.cognicao.resumo_conteudo import explicar_texto_observado
    def gerar(sistema, dados, contrato):
        proposta = {"resposta": "Um relato.", "evidencias": evidencias, "ausente": False}
        contrato.validar(proposta)
        return proposta
    with pytest.raises(ValueError, match="interpretacao_conteudo_sem_evidencia"):
        explicar_texto_observado(conteudo="Um. Dois. Tres. Quatro. Cinco.", pergunta="o que diz?",
            titulo="Aviso", fonte="e-mail", gerar=gerar)


def test_citacao_autorada_pelo_modelo_nao_substitui_evidencia_do_host(tmp_path):
    runtime, _, modelo, _, _ = _runtime(tmp_path)
    runtime.executar("EMAIL_READ", {}, "lê meus emails")
    modelo.resposta["citacoes"] = ["Seu notebook chega sexta."]
    r = runtime.executar("EMAIL_READ", {"modo": "conteudo"}, "o que diz?")
    assert r["interpretacao_gerada"] is False and "notebook" not in r["fala"]


@pytest.mark.parametrize("conteudo", ["", " \n\t"])
def test_fonte_sem_texto_nao_chama_modelo(conteudo):
    from mente_laylay.cognicao.resumo_conteudo import explicar_texto_observado
    def gerar(*a):
        raise AssertionError("Fonte sem texto não deve consumir geração.")
    r = explicar_texto_observado(conteudo=conteudo, pergunta="o que diz?", titulo="Aviso", fonte="arquivo", gerar=gerar)
    assert r["ausente"] and r["citacoes"] == []


@pytest.mark.parametrize("texto", ["que desconto esse email oferece?", "qual o cupom desse email?", "o que pedem nele?"])
def test_consulta_de_conteudo_reusa_modalidade_e_referencia_canonicas(texto):
    cmd = detectar_email(texto, contexto_ativo=True)
    assert cmd == {"intent": "EMAIL_READ", "params": {"modo": "conteudo", "pergunta": texto}}


def test_falha_de_modelo_na_leitura_publica_diagnostico_sanitizado(tmp_path):
    runtime, _, _, _, _ = _runtime(tmp_path)
    erros = []
    runtime.registrar_falha = lambda *args, **kw: erros.append((args, kw))
    runtime.enviar_modelo = lambda *args, **kw: ""
    runtime.executar("EMAIL_READ", {}, "lê meus emails")
    r = runtime.executar("EMAIL_READ", {"modo": "conteudo"}, "o que diz?")
    assert r["confirmado"] and not r["interpretacao_gerada"]
    assert r["status_compreensao"] == "compreensao_email_indisponivel"
    assert erros[0][0] == ("email", "compreensao")
    assert "teclado" not in repr(erros) and "Rastreio" not in repr(erros)


@pytest.mark.parametrize("texto", ["le o segundo email", "lê ele", "lê esse email"])
def test_selecao_para_leitura_pede_sintese_e_nao_busca_frase_no_corpo(texto):
    cmd = detectar_email(texto, contexto_ativo=True)
    assert cmd["intent"] == "EMAIL_READ" and cmd["params"]["modo"] == "conteudo"
    assert cmd["params"]["pergunta"] == "Resuma o assunto e as informações principais da mensagem."


def test_pergunta_especifica_conserva_texto_do_usuario_para_compreensao():
    texto = "qual o cupom desse email?"
    assert detectar_email(texto, contexto_ativo=True)["params"]["pergunta"] == texto


def test_lista_registra_somente_cinco_itens_apresentados_sem_satisfazer_os_outros(tmp_path):
    runtime, transporte, _, _, _ = _runtime(tmp_path)
    transporte.consulta["mensagens"]=[{"uid":f"uid:{i}","remetente":"Pessoa","assunto":f"Aviso {i}",
        "referencia_email":{}} for i in range(1,7)]
    r=runtime.executar("EMAIL_READ",{},"le meus emails")
    assert [i["uid"] for i in r["itens_apresentados"]]==[f"uid:{i}" for i in range(1,6)]
    assert all(i["texto"] in r["fala"] for i in r["itens_apresentados"])
    assert "Aviso 6" not in r["fala"] and "Há mais 1" in r["fala"]
