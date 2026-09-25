"""Resultado confirmado deve ser publicado antes da conclusão observável."""
import time

import pytest

from mente_laylay.autonomia.fluxos_conversa import handle_feedback_pendente


class MusicaControlada:
    def __init__(self, eventos, caso):
        self.eventos, self.caso = eventos, caso

    def faixa_atual(self):
        return {} if self.caso == "sem_faixa" else {
            "url": "https://www.youtube.com/watch?v=aaaaaaaaaaa",
            "title": "Faixa de teste", "canal": "Teste",
        }

    def criar_playlist(self, nome):
        self.eventos.append("create")
        return {"ok": self.caso != "falha_create", "criada": self.caso == "nova",
                "status": "falha_persistencia" if self.caso == "falha_create" else "playlist_criada"}

    def adicionar_faixa_resultado(self, *args):
        self.eventos.append("add")
        return {"ok": self.caso != "falha_add", "added": self.caso != "duplicada",
                "duplicated": self.caso == "duplicada"}

    def definir_ultima_playlist(self, nome):
        self.eventos.append("ultima")


def montar(caso, publicacao="ok", nome="estudos"):
    eventos, receipts, falas = [], [], []

    def registrar(receipt, *args, **kwargs):
        eventos.append("receipt")
        if publicacao == "excecao":
            raise RuntimeError("registrador indisponível")
        if publicacao == "negada":
            return False
        receipts.append(receipt)

    def falar(fala, *args):
        eventos.append("fala")
        falas.append(fala)

    contexto = {
        "_playlist_sugestao_pendente": {"playlist": nome, "ts": time.time()},
        "_classificar_confirmacao_local": lambda texto: True,
        "_registro_musica_operacoes_runtime": MusicaControlada(eventos, caso),
        "_registrar_resultado_execucao": registrar if publicacao != "ausente" else None,
        "falar_com_lipsync": falar,
    }
    return contexto, eventos, receipts, falas


@pytest.mark.parametrize("caso", ["nova", "existente", "duplicada", "falha_create", "falha_add", "sem_faixa"])
@pytest.mark.parametrize("nome", ["vmz", "estudos da tarde"])
def test_resultado_publicado_antes_da_unica_conclusao(caso, nome, monkeypatch):
    monkeypatch.setattr("mente_laylay.autonomia.fluxos_conversa._escolher_fala_variada", lambda itens: itens[0])
    ctx, eventos, receipts, falas = montar(caso, nome=nome)
    assert handle_feedback_pendente(ctx, "pode sim") is True
    assert len(receipts) == 1
    assert eventos.index("receipt") < eventos.index("fala")
    assert len(falas) == 1
    assert ctx["_playlist_sugestao_pendente"] is None
    sucesso = caso in {"nova", "existente", "duplicada"}
    assert receipts[0]["confirmado"] is sucesso
    if caso in {"falha_create", "sem_faixa"}:
        assert "add" not in eventos
    if caso == "duplicada":
        assert receipts[0]["executou"] is False
        assert "já estava" in falas[0]
    if caso == "existente":
        assert "criei" not in falas[0]


@pytest.mark.parametrize("publicacao", ["ausente", "excecao", "negada"])
def test_falha_de_publicacao_nao_anuncia_sucesso_nem_repete_efeito(publicacao):
    ctx, eventos, receipts, falas = montar("nova", publicacao)
    assert handle_feedback_pendente(ctx, "sim") is True
    assert eventos.count("create") == eventos.count("add") == 1
    assert not receipts
    assert len(falas) == 1
    assert "registrar" in falas[0]
    assert not any(termo in falas[0].casefold() for termo in ("salvei", "criei", "pronto", "salvamento falhou"))
    assert ctx["_playlist_sugestao_pendente"] is None


def test_root_publica_receipt_antes_da_fala_com_persistencia_real(tmp_path, monkeypatch):
    """Composição importada de produção, disco temporário e saída capturada.

    Não inicia main/voz/Chrome; observadores de aprendizado ficam desligados.
    Não substitui feedback, operações, armazenamento ou registrador canônico.
    """
    import importlib
    import json

    root = importlib.import_module("laylay")
    estado = root._estado_compartilhado_runtime
    for dominio in ("mental", "continuidades", "musical", "conversacional", "memoria_conversa"):
        monkeypatch.setattr(estado, dominio, {})
    estado.mental.update({"ultima_entrada": "sim", "plano_turno_atual": {
        "id": "teste-publicacao", "texto_usuario": "sim", "comandos": [],
    }})
    for nome in ("_especialista_neural_comandos_runtime", "_motor_aprendizado_runtime",
                 "_mapa_habilidades_runtime", "_rede_associativa_runtime"):
        monkeypatch.setattr(root, nome, None)
    for nome in ("_registrar_feedback_proatividade", "_limpar_pergunta_aberta", "_suspender_topico_conversacional"):
        monkeypatch.setattr(root, nome, lambda *a, **k: None)
    monkeypatch.setattr(root._adaptadores_aplicacao_runtime, "registrar_feedback_contextual", lambda *a, **k: None)

    store = root._playlist_runtime
    monkeypatch.setattr(store, "state_file", str(tmp_path / "playlists.json"))
    monkeypatch.setattr(store, "legacy_file", str(tmp_path / "legacy.json"))
    monkeypatch.setattr(store, "cache", {})
    monkeypatch.setattr(store, "playlist_state", {})
    monkeypatch.setattr(store, "sincronizar_playlists_laylay", None)
    monkeypatch.setattr(store, "artwork_dir", tmp_path / "artwork")
    monkeypatch.setattr(root._operacoes_musicais_runtime, "playlist_state", {"player": {
        "url": "https://www.youtube.com/watch?v=aaaaaaaaaaa", "title": "Faixa Teste",
        "channel": "Teste", "state": "playing", "observed_at": time.time(),
    }})

    falas = []

    def capturar(fala, *args):
        comandos = estado.mental["plano_turno_atual"]["comandos"]
        assert len(comandos) == 1
        assert comandos[0]["intent"] == "PLAYLIST_ADD"
        assert comandos[0]["confirmado"] is True
        assert comandos[0]["alvo"] == "teste receipt"
        assert json.loads((tmp_path / "playlists.json").read_text(encoding="utf-8"))
        falas.append(fala)

    monkeypatch.setattr(root, "falar_com_lipsync", capturar)
    for _ in range(2):
        root._continuidades_update(playlist_sugestao_pendente={"playlist": "teste receipt", "ts": time.time()})
        assert root._handle_feedback_pendente("sim") is True
        assert root._continuidades_get("playlist_sugestao_pendente") is None
    assert len(falas) == 2
    assert "já estava" in falas[-1]
    conteudo = store.load()
    assert len(conteudo["teste receipt"]) == 1
