"""Uma consulta OpenRouter para a sonda P01, sem integrar o runtime.

Exemplo (na raiz do projeto):
    python -m scripts.analises.sonda_openrouter_fronteira --modelo provedor/modelo

A chave vem de OPENROUTER_API_KEY ou de uma leitura local sem eco. A sonda
envia somente um caso sintetico por execucao e nunca envia o gabarito.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
from typing import Callable, Mapping

import requests

from scripts.analises.sonda_avaliador_fronteira_independente import (
    SISTEMA_AMBIGUIDADE_EXPLICITA,
    carregar_painel_fronteira,
    propor,
)
from scripts.analises.sonda_viabilidade_particoes import propor_viabilidade
from mente_laylay.integracao.configuracao_aplicacao import (
    carregar_segredo_no_ambiente,
)


URL = "https://openrouter.ai/api/v1/chat/completions"


class ErroConsultaOpenRouter(Exception):
    """Falha de transporte ou formato, sem revelar a chave ou o corpo HTTP."""


def consultar_openrouter(
    sistema: str,
    entrada: Mapping[str, object],
    formato: Mapping[str, object],
    *,
    modelo: str,
    chave: str,
    temperatura: float | None = None,
    semente: int | None = None,
    provedor: str | None = None,
    enviar: Callable[..., object] = requests.post,
) -> tuple[object, dict[str, object]]:
    """Retorna proposta e metadados; nem uma nem outros autorizam efeito."""
    if not modelo or not modelo.strip() or not chave or not chave.strip():
        raise ValueError("modelo e chave sao obrigatorios")
    if temperatura is not None and not 0 <= temperatura <= 2:
        raise ValueError("temperatura deve estar entre 0 e 2")
    if provedor is not None and (not provedor or provedor != provedor.strip()):
        raise ValueError("provedor deve ser um slug nao vazio")
    corpo = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": sistema},
            {"role": "user", "content": json.dumps(
                entrada, ensure_ascii=False,
            )},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "fronteira_p01",
                "strict": True,
                "schema": formato,
            },
        },
        "provider": {"require_parameters": True},
        "max_tokens": 256,
        "stream": False,
    }
    if temperatura is not None:
        corpo["temperature"] = temperatura
    if semente is not None:
        corpo["seed"] = semente
    if provedor is not None:
        corpo["provider"].update({"only": [provedor],
                                  "allow_fallbacks": False})
    sha256_pedido = hashlib.sha256(json.dumps(
        corpo, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    try:
        resposta = enviar(
            URL,
            headers={"Authorization": f"Bearer {chave}",
                     "X-OpenRouter-Metadata": "enabled"},
            json=corpo,
            timeout=90,
        )
    except requests.RequestException as erro:
        raise ErroConsultaOpenRouter(type(erro).__name__) from None
    if resposta.status_code != 200:
        raise ErroConsultaOpenRouter(f"HTTP {resposta.status_code}")
    try:
        dados = resposta.json()
        conteudo = dados["choices"][0]["message"]["content"]
        if not isinstance(conteudo, str):
            raise TypeError("content nao textual")
        proposta = json.loads(conteudo)
    except (ValueError, KeyError, IndexError, TypeError):
        raise ErroConsultaOpenRouter("resposta_invalida") from None
    roteamento = dados.get("openrouter_metadata")
    endpoints = roteamento.get("endpoints") if isinstance(roteamento, dict) else None
    disponiveis = (endpoints.get("available")
                   if isinstance(endpoints, dict) else None)
    selecionado = next(
        (item.get("provider") for item in disponiveis
         if isinstance(item, dict) and item.get("selected") is True
         and isinstance(item.get("provider"), str)),
        None,
    ) if isinstance(disponiveis, list) else None
    return proposta, {
        "modelo_recebido": dados.get("model"),
        "uso": dados.get("usage"),
        "id_geracao": dados.get("id"),
        "fingerprint_sistema": dados.get("system_fingerprint"),
        "provedor_selecionado": selecionado,
        "motivo_termino": dados["choices"][0].get("finish_reason"),
        "sha256_pedido": sha256_pedido,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", required=True,
                        help="ID exato de modelo compativel com JSON Schema")
    parser.add_argument("--painel", type=int,
                        choices=(22, 23, 24, 25, 26, 27, 28),
                        default=22,
                        help="Painel sintetico; somente um caso por chamada")
    parser.add_argument("--caso", help="ID do caso; padrao: primeiro do painel")
    parser.add_argument("--instrucao", choices=("original", "ambiguidade_explicita"),
                        default="original")
    parser.add_argument("--contrato", choices=("citacao", "viabilidade"),
                        default="citacao")
    parser.add_argument("--temperatura", type=float,
                        help="Amostragem explicita (0 a 2); padrao do modelo se omitida")
    parser.add_argument("--semente", type=int,
                        help="Semente opcional se o modelo a aceitar")
    parser.add_argument("--provedor",
                        help="Slug de provedor fixo nesta sonda, sem fallback")
    args = parser.parse_args()
    if args.temperatura is not None and not 0 <= args.temperatura <= 2:
        parser.error("--temperatura deve estar entre 0 e 2")
    casos, _revisao_local = carregar_painel_fronteira(args.painel)
    id_caso = args.caso or casos[0]["id"]
    caso = next((item for item in casos if item["id"] == id_caso), None)
    if caso is None:
        parser.error("ID de caso desconhecido no painel solicitado")
    chave = os.environ.get("OPENROUTER_API_KEY")
    if not chave:
        carregar_segredo_no_ambiente()
        chave = os.environ.get("OPENROUTER_API_KEY")
    if not chave:
        chave = getpass.getpass("Chave OpenRouter (nao sera exibida): ")
    metadados: dict[str, object] = {}
    consultas: list[dict[str, object]] = []

    def consultar(sistema: str, entrada: Mapping[str, object],
                  formato: Mapping[str, object]) -> object:
        proposta, meta = consultar_openrouter(
            sistema, entrada, formato, modelo=args.modelo, chave=chave,
            **({"temperatura": args.temperatura}
               if args.temperatura is not None else {}),
            **({"semente": args.semente}
               if args.semente is not None else {}),
            **({"provedor": args.provedor}
               if args.provedor is not None else {}),
        )
        metadados.update(meta)
        consultas.append(meta)
        return proposta

    try:
        if args.contrato == "viabilidade":
            resultado = propor_viabilidade(caso, consultar)
        else:
            resultado = propor(
                caso, consultar,
                **({"sistema": SISTEMA_AMBIGUIDADE_EXPLICITA}
                   if args.instrucao == "ambiguidade_explicita" else {}),
            )
    except ErroConsultaOpenRouter as erro:
        resultado = {"estado": "erro_consulta", "motivo": str(erro),
                     "aprovado_para_producao": False, "autoriza_efeito": False}
    print(json.dumps({
        "caso": id_caso,
        "painel": {
            22: "v22_diagnostico_nao_holdout",
            23: "v23_primeira_medicao_parcialmente_invalida",
            24: "v24_diagnostico_ambiguo_pos_v23",
            25: "v25_primeira_medicao_instrucao_explicita",
            26: "v26_primeira_medicao_viabilidade_contextualizada",
            27: "v27_primeira_medicao_viabilidade_com_veto_semantico",
            28: "v28_primeira_medicao_contrato_completo_corrigido",
        }[args.painel],
        "instrucao": args.instrucao,
        "contrato": args.contrato,
        "temperatura": args.temperatura,
        "semente": args.semente,
        "provedor_solicitado": args.provedor,
        "modelo_solicitado": args.modelo,
        **metadados,
        "numero_consultas": len(consultas),
        "consultas": consultas,
        "custo_total_observado_usd": sum(
            float((meta.get("uso") or {}).get("cost") or 0)
            for meta in consultas
        ),
        "resultado": resultado,
        "aprovado_para_producao": False,
        "autoriza_efeito": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
