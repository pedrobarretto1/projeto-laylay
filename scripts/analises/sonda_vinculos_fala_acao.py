"""Observa vínculos atuais sem alterar produção ou consultar a LLM.

Executar da raiz com:
    .venv314/Scripts/python.exe -m scripts.analises.sonda_vinculos_fala_acao

Usa os owners reais de memória/corpo e a composição de teste já existente.
O transporte serial é simulado: nenhum dispositivo, voz, conta ou rede é usado.
Não mede compreensão do modelo nem constitui validação do runtime completo.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from mente_laylay.cognicao.decisao_corporal import IntencaoCorporal
from mente_laylay.cognicao.modelo_corporal import formatar_realidade_corporal
from mente_laylay.memoria_mental.contexto_compartilhado import (
    registrar_mente_curta,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.registro_semantico import (
    estado_registro_semantico_inicial,
    registrar_interacao_semantica,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from scripts.tests.test_companhia_corporal import ativar, emocao, montar, motores


def observar_memoria_da_fala() -> dict[str, Any]:
    """Distingue ausência de indexação de perda de texto ou receipt."""
    exemplos: dict[str, Any] = {}
    for fala in (
        "Tim Maia foi um cantor brasileiro.",
        "Pausei a música.",
        "Liguei a lâmpada do quarto.",
    ):
        registro = registrar_interacao_semantica(
            estado_registro_semantico_inicial(),
            resposta_laylay=fala, assunto="controle", agora=100.0,
        )
        exemplos[fala] = [
            {"texto": a["texto"], "status": a["status"]}
            for a in registro["alegacoes"]
        ]
    receipt = ResultadoAcao(
        intent="MEDIA_CONTROL", status="pausado", alvo="música",
        params={"acao": "pause"}, ok=True, executou=True, confirmado=True,
        origem="executor", id_solicitacao="sonda-pausa-1",
        evidencia_confirmacao="estado_reprodutor_pausado",
    )
    mental = registrar_resultado_execucao({}, receipt)
    mental = registrar_mente_curta(
        mental, texto_usuario="pausa a música", resposta_ia="Pausei a música.",
        intencao="MEDIA_CONTROL", alvo="música", habilidade="musica",
        log=lambda _: None,
    )
    assert mental["ultima_resposta"] == "Pausei a música.", "Texto não preservado"
    assert mental["ultima_acao_contrato"]["id_solicitacao"] == receipt.id_solicitacao
    assert mental["ultima_acao_contrato"]["confirmado"] is True
    return {
        "exemplos": exemplos,
        "memoria_integrada": {
            "ultima_resposta": mental["ultima_resposta"],
            "receipt_id": mental["ultima_acao_contrato"]["id_solicitacao"],
            "confirmado": mental["ultima_acao_contrato"]["confirmado"],
            "alegacoes": mental["registro_semantico"]["alegacoes"],
        },
        "limite": "Sem geração, publicação, consulta posterior ou composição main.",
    }


def observar_decisao_e_experiencia() -> dict[str, Any]:
    """Captura a decisão antes do efeito e acompanha a projeção posterior."""
    estado, esp, rosto, corpo, _quadro, _clock = montar()
    iniciar_original = corpo.experiencias.iniciar
    aguardar_original = corpo.companhia._aguardar_gesto
    capturas: list[dict[str, Any]] = []

    def observar_inicio(**campos: Any) -> dict[str, Any]:
        # Usar o owner de cópia: os domínios vivos carregam locks internos.
        decisao = estado.obter_copia("mental", "intencao_corporal", {})
        ocorrencia = iniciar_original(**campos)
        capturas.append({"decisao": decisao, "ocorrencia": dict(ocorrencia)})
        return ocorrencia

    try:
        estado.atualizar_campos("mental", turno_atual={"id": "sonda-origem"})
        assert ativar(corpo)["ok"], "Concessão de teste não foi instalada"
        corpo.experiencias.iniciar = observar_inicio
        # Só a espera física é controlada; a validação real continua exigida.
        corpo.companhia._aguardar_gesto = lambda ms, validar: validar()
        emocao(estado, rosto, "alegre")
        retorno = corpo.companhia.processar()
        assert retorno["ok"], retorno
        experiencia = estado.obter_copia("mental", "experiencia_corporal", {})
        decisao, ocorrencia = capturas[-1]["decisao"], capturas[-1]["ocorrencia"]
        assert experiencia["intencao_id"] == decisao["id"]
        assert experiencia["confirmado"] is True
        quantidade = len(motores(esp))

        corpo.companhia._registrar_intencao(
            IntencaoCorporal("atenta", "atividade_pc_em_andamento", 100, 0, 1)
        )
        modelo = corpo.modelo_para_mente("sonda-seguinte")
        bloco = formatar_realidade_corporal(modelo).splitlines()[1]
        projecao = json.loads(bloco)
        atual = estado.obter_copia("mental", "experiencia_corporal", {})
        assert atual == experiencia, "Decisão seguinte alterou experiência antiga"
        assert modelo["ultima_experiencia"]["id"] == experiencia["id"]
        assert len(motores(esp)) == quantidade, "Consulta gerou nova ação"
        return {
            "decisao_anterior": {
                k: decisao.get(k) for k in ("nome", "motivo", "estado")
            },
            "vinculo_intencao_preservado_na_experiencia": (
                experiencia["intencao_id"] == decisao["id"]
            ),
            "motivo_decisao_presente_na_ocorrencia": any(
                k in ocorrencia for k in ("motivo_decisao", "decisao", "decisao_origem")
            ),
            "motivo_decisao_anterior": decisao.get("motivo"),
            "motivo_resultado_experiencia": experiencia.get("motivo"),
            "decisao_atual": {
                k: modelo["intencao_em_curso"].get(k) for k in ("nome", "motivo")
            },
            "experiencia_anterior_preservada": atual == experiencia,
            "intencao_id_disponivel_no_modelo": bool(
                modelo["ultima_experiencia"].get("intencao_id")
            ),
            "intencao_id_disponivel_na_projecao_llm": bool(
                projecao["ultima_experiencia"].get("intencao_id")
            ),
            "motivo_anterior_no_prompt": decisao["motivo"] in bloco,
            "mesmo_objetivo_apos_atencao": (
                modelo["intencao_em_curso"].get("objetivo_id") == decisao["objetivo_id"]
            ),
            "autoriza_execucao": modelo["autoriza_execucao"],
            "prova_deslocamento": experiencia["prova_deslocamento"],
            "frames_motor_somente_no_serial_simulado": quantidade,
            "limite": "Sem hardware, LLM, voz ou prova de resposta incorreta.",
        }
    finally:
        corpo.experiencias.iniciar = iniciar_original
        corpo.companhia._aguardar_gesto = aguardar_original
        rosto.encerrar()


def executar_sonda() -> dict[str, Any]:
    return {
        "nivel": "integração de componentes reais com serial simulado",
        "fala": observar_memoria_da_fala(),
        "corpo": observar_decisao_e_experiencia(),
        "interpretacao": (
            "Saída diagnóstica, não GREEN do plano: a ausência de indexação não "
            "prova perda global de memória; motivo de decisão e resultado são "
            "conceitos distintos, e falta medir sua recuperação no caminho real."
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, help="Arquivo novo para a evidência JSON")
    args = parser.parse_args()
    resultado = executar_sonda()
    texto = json.dumps(resultado, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.saida:
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        # Não sobrescrever evidência anterior de outra execução.
        with args.saida.open("x", encoding="utf-8") as arquivo:
            arquivo.write(texto)
    print(texto, end="")
