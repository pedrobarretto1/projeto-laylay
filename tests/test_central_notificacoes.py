from __future__ import annotations

import json
from pathlib import Path

from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime


def _runtime(tmp_path: Path, **kwargs) -> CentralNotificacoesRuntime:
    return CentralNotificacoesRuntime(
        str(tmp_path / "central.json"),
        log=lambda *_: None,
        **kwargs,
    )


def test_promocao_e_guardada_sem_falar_e_sem_duplicar(tmp_path: Path) -> None:
    falas = []
    central = _runtime(
        tmp_path,
        agendar_fala_cb=lambda *args: falas.append(args) or True,
        time_cb=lambda: 1000.0,
    )
    email = {
        "uid": "uid:1",
        "origem": "email",
        "remetente": "Loja",
        "assunto": "Oferta imperdível: 50% de desconto",
    }

    assert central.ingerir_emails([email]) == {"uid:1"}
    assert central.ingerir_emails([email]) == {"uid:1"}
    assert falas == []
    assert central.diagnostico()["eventos"] == 1
    assert "Agrupei 1 promoção" in central.resumo()


def test_seguranca_usa_fila_mesmo_durante_jogo(tmp_path: Path) -> None:
    falas = []
    central = _runtime(
        tmp_path,
        modo_jogo_getter=lambda: True,
        conversa_ativa_getter=lambda: True,
        agendar_fala_cb=lambda *args: falas.append(args) or True,
    )

    aceitos = central.ingerir_emails([{
        "uid": "uid:seg",
        "remetente": "Conta",
        "assunto": "Tentativa de login detectada",
        "possivel_golpe": True,
    }])

    assert aceitos == {"uid:seg"}
    assert len(falas) == 1
    assert falas[0][0] == "seguranca"
    assert "segurança" in falas[0][1].casefold()


def test_aviso_normal_fica_guardado_quando_contexto_esta_ocupado(tmp_path: Path) -> None:
    falas = []
    central = _runtime(
        tmp_path,
        modo_jogo_getter=lambda: True,
        agendar_fala_cb=lambda *args: falas.append(args) or True,
    )

    central.ingerir([{
        "id": "sistema:1",
        "origem": "sistema",
        "titulo": "Atualização concluída",
    }])

    assert falas == []
    assert "Atualização concluída" in central.resumo()


def test_preferencia_explicita_persiste(tmp_path: Path) -> None:
    caminho = tmp_path / "central.json"
    central = _runtime(tmp_path)

    ok, _ = central.definir_preferencia("compras", "silenciar")

    assert ok is True
    recarregada = CentralNotificacoesRuntime(str(caminho), log=lambda *_: None)
    assert recarregada.diagnostico()["preferencias"]["compras"] == "silenciar"
    assert json.loads(caminho.read_text(encoding="utf-8"))["preferencias"]["compras"] == "silenciar"


def test_linguagem_natural_controla_categoria_e_consulta(tmp_path: Path) -> None:
    central = _runtime(tmp_path)

    silenciar = central.detectar("não me avise mais sobre promoções")
    interromper = central.detectar("avisos de segurança podem me interromper")
    consulta = central.detectar("tem alguma notificação importante?")

    assert silenciar == {
        "intent": "NOTIFICATIONS",
        "params": {"acao": "silenciar", "categoria": "promocao"},
    }
    assert interromper == {
        "intent": "NOTIFICATIONS",
        "params": {"acao": "interromper", "categoria": "seguranca"},
    }
    assert consulta["params"]["acao"] == "importantes"


def test_resumo_reune_eventos_e_agenda_sem_payload_executavel(tmp_path: Path) -> None:
    central = _runtime(
        tmp_path,
        agenda_getter=lambda: [{
            "nome": "consulta amanhã",
            "ativo": True,
            "comandos_no_disparo": [{"acao": "lock_pc"}],
        }],
        modo_jogo_getter=lambda: True,
    )
    central.ingerir([{
        "id": "email:2",
        "origem": "email",
        "categoria": "financeiro",
        "titulo": "Fatura vence amanhã",
        "prioritario": True,
    }])

    texto = central.resumo()

    assert "Fatura vence amanhã" in texto
    assert "consulta amanhã" in texto
    assert "lock_pc" not in texto


def test_agendamento_e_aceito_e_passa_pela_fila(tmp_path: Path) -> None:
    falas = []
    central = _runtime(
        tmp_path,
        agendar_fala_cb=lambda *args: falas.append(args) or True,
        time_cb=lambda: 1200.0,
    )

    assert central.ingerir_agendamento({"id": "agua"}, "Hora de beber água") is True
    assert falas and "beber água" in falas[0][1]

