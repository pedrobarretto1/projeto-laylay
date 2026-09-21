from copy import deepcopy

import pytest

from mente_laylay.integracao.chrome_ws_handlers import dispatch_event, handle_action


@pytest.mark.parametrize("action", ["active_tab_changed", "url_update", "desconhecido"])
def test_evento_mantem_dados_operacionais_mas_nao_imprime_segredos(action, capsys):
    url = "http://usuario:senha-ficticia@localhost:1455/success?id_token=token-ficticio&code=codigo-ficticio#refresh_token=renovacao-ficticia"
    dados = {"action": action, "tabId": 7, "url": url,
             "title": "Login", "payload": {"password": "segredo-aninhado"}}
    antes = deepcopy(dados)
    recebidos = []
    def handler(evento):
        recebidos.append(deepcopy(evento))
        return handle_action(evento, {})
    resultado = dispatch_event(dados, {"action": handler})
    log = capsys.readouterr().out
    for segredo in ("senha-ficticia", "token-ficticio", "codigo-ficticio", "renovacao-ficticia", "segredo-aninhado"):
        assert segredo not in log
    assert dados == antes and recebidos == [antes]
    if action != "desconhecido":
        assert resultado["aba_url_atual"] == url
        assert "Aba Ativa" in log


@pytest.mark.parametrize("action, campo", [("title_update", "title"), ("error", "message")])
def test_textos_de_evento_sao_sanitizados_antes_do_stdout(action, campo, capsys):
    handle_action({"action": action, campo: "https://localhost/callback?id_token=segredo-ficticio"}, {})
    assert "segredo-ficticio" not in capsys.readouterr().out
