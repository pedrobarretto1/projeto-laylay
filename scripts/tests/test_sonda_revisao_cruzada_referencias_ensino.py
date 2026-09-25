"""O revisor auxiliar não vê diagnósticos nem vira gabarito."""

import json

import scripts.analises.sonda_revisao_cruzada_referencias_ensino as sonda
from scripts.analises.revisao_referencias_ensino import carregar_painel
from scripts.analises.sonda_revisao_cruzada_referencias_ensino import revisar_caso


def test_revisor_recebe_so_cenario_cego_e_nao_aprova_ensino() -> None:
    caso = next(item for item in carregar_painel() if item["id"] == "REF-01")
    enviado = {}

    class Resposta:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {"message": {"content": json.dumps({
                "referente": "indeterminado", "leitura": "afirmada",
                "evidencia": "o sensor leu 15% de umidade",
                "justificativa": "A frase afirma leitura sem identificar o meio.",
            })}}

    def post(_url: str, **kwargs):
        enviado.update(kwargs)
        return Resposta()

    resultado = revisar_caso(caso, post=post)
    entrada = json.loads(enviado["json"]["messages"][1]["content"])
    assert set(entrada) == {"definicao", "exemplo", "contexto"}
    assert enviado["json"]["think"] is False
    assert "diagnostico" not in json.dumps(enviado["json"], ensure_ascii=False)
    assert resultado["revisao"]["referente"] == "indeterminado"
    assert resultado["revisao_humana_confirmada"] is False
    assert resultado["aprovado_para_treino"] is False
    assert resultado["aprovado_para_compor"] is False


def test_revisor_com_evidencia_inventada_nao_entrega_rotulo() -> None:
    caso = next(item for item in carregar_painel() if item["id"] == "REF-01")

    class Resposta:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {"message": {"content": json.dumps({
                "referente": "mesmo", "leitura": "afirmada",
                "evidencia": "sensor oceânico mágico",
                "justificativa": "A resposta tentou usar um sensor ausente.",
            })}}

    resultado = revisar_caso(caso, post=lambda *_args, **_kwargs: Resposta())
    assert resultado["erro"] == "revisao_invalida"
    assert resultado["revisao"] == {}


def test_painel_interrompe_apos_primeiro_erro_de_modelo(monkeypatch, capsys) -> None:
    chamadas = []

    def revisar(caso):
        chamadas.append(caso["id"])
        return {"id": caso["id"], "erro": "ReadTimeout"}

    monkeypatch.setattr(sonda, "revisar_caso", revisar)
    monkeypatch.setattr("sys.argv", ["sonda_revisao_cruzada_referencias_ensino.py"])
    sonda.main()
    assert chamadas == ["REF-01"]
    assert "ReadTimeout" in capsys.readouterr().out
