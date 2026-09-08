"""Complemento contrastivo experimental; não substitui a prova v2 nem o runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .gerar_list_windows_onda_v2 import (
    APLICATIVOS_NOVOS, FRASES_CAOS_RESERVADAS, _chave_texto,
    _exemplo, _normalizar, gerar_exemplos as gerar_ancora,
)


# Variantes do mesmo mecanismo mantêm o grupo histórico: nunca poderão
# reaparecer no treino quando esse mecanismo estiver na prova agrupada.
MOLDES = (
    ("list_windows_v2_negativo_hipotese_estado", False, "imagine que {alvo} estivesse {estado}; isso ajudaria?"),
    ("list_windows_v2_negativo_hipotese_estado", False, "se {alvo} continuasse {estado}, consumiria memória?"),
    ("list_windows_v2_negativo_hipotese_abrir", False, "se eu abrisse {alvo}, o computador ficaria lento?"),
    ("list_windows_v2_negativo_hipotese_abrir", False, "iniciar {alvo} aumentaria o consumo de bateria?"),
    ("list_windows_v2_negativo_metalinguagem", False, "como formular uma pergunta sobre {alvo} continuar {estado}?"),
    ("list_windows_v2_negativo_metalinguagem", False, "reescreva a pergunta: {alvo} está {estado}?"),
    ("list_windows_v2_negativo_descricao_frase", False, "o exemplo de pergunta fala sobre {alvo} estar {estado}."),
    ("list_windows_v2_negativo_descricao_frase", False, "no diálogo fictício perguntaram se {alvo} segue {estado}."),
    ("list_windows_v2_negativo_permanencia", False, "{alvo} permanece {estado} desde ontem."),
    ("list_windows_v2_negativo_afirmacao", False, "{alvo} segue {estado}."),
    ("list_windows_v2_negativo_afirmacao", False, "{alvo} continua em execução."),
    ("list_windows_v2_negativo_passado", False, "eu deixei {alvo} funcionando e só estou comentando."),
    ("list_windows_v2_consulta_permanece", True, "{alvo} permanece em execução?"),
    ("list_windows_v3_consulta_segue", True, "{alvo} segue {estado}?"),
    ("list_windows_v3_consulta_continua", True, "{alvo} continua em execução?"),
    ("list_windows_v2_consulta_verificar", True, "verifique se {alvo} permanece {estado}."),
    ("list_windows_v2_consulta_confirmar", True, "confirme agora se {alvo} segue {estado}."),
    ("list_windows_v2_consulta_necessidade", True, "preciso saber agora se {alvo} permanece {estado}."),
    ("list_windows_v2_consulta_contar", True, "me diga se {alvo} continua em execução."),
    ("list_windows_v2_consulta_conferida", True, "confere o estado de {alvo} pra mim."),
)


def gerar_exemplos() -> list[dict[str, Any]]:
    """Produz contrastes rotulados manualmente, sem consultar previsões."""
    exemplos = []
    for numero, (grupo, positivo, molde) in enumerate(MOLDES):
        for alvo, estado in APLICATIVOS_NOVOS:
            exemplos.append(_exemplo(
                molde.format(alvo=alvo, estado=estado), positivo=positivo,
                familia=f"{grupo}_complemento_{numero}", grupo=grupo,
                entidade=f"app:{_normalizar(alvo)}", ato_consulta=positivo,
                dominio_app=True, escopo_negativo="contraste_ato",
            ))
    return exemplos


def validar_lote(exemplos: list[dict[str, Any]]) -> dict[str, int]:
    from ..dataset import validar_exemplo

    reserva = json.loads(Path(__file__).with_name("reservas").joinpath(
        "list_windows_ato_v1.json",
    ).read_text(encoding="utf-8"))
    proibidos = {_chave_texto(x["text"]) for x in gerar_ancora()}
    proibidos.update(_chave_texto(x) for x in FRASES_CAOS_RESERVADAS)
    proibidos.update(_chave_texto(x["text"]) for x in reserva["exemplos"])
    vistos: set[str] = set()
    for item in exemplos:
        validar_exemplo(item, intents_permitidas={"LIST_WINDOWS"})
        chave = _chave_texto(item["text"])
        if chave in proibidos or chave in vistos:
            raise ValueError("colisão com âncora, reserva, caos ou complemento")
        vistos.add(chave)
        if "command" in item["training_heads"] or "autoriza_execucao" in item:
            raise ValueError("complemento não pode mudar command ou autoridade")
    return {
        "total": len(exemplos),
        "positivos": sum(x["intent"] == "LIST_WINDOWS" for x in exemplos),
        "negativos": sum(x["intent"] == "NONE" for x in exemplos),
        "grupos": len({x["validation_group"] for x in exemplos}),
        "entidades": len({x["validation_entity_group"] for x in exemplos}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as destino:
        destino.write("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in exemplos))
    print(json.dumps({"saida": str(args.saida), **resumo}, ensure_ascii=False))


if __name__ == "__main__":
    main()
