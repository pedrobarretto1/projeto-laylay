"""Retornos atrasados no writer realmente instalado pelo composition root.

O subprocesso importa a composição e usa a mente e o validador instalados.
Somente transporte do modelo, execução externa e emissão de fala são portas
isoladas. Os receipts locais abaixo são sintéticos, sem prova de efeito físico.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


DOMINIOS = ("playlist", "iot", "app")


@pytest.fixture(scope="module")
def publicacoes_composicao() -> dict:
    codigo = textwrap.dedent(r'''
        import json
        import os
        import sys
        from types import SimpleNamespace
        from mente_laylay.integracao import instancia_unica

        adquirir_real = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda identificador, **kwargs: adquirir_real(
            str(identificador) + ".sonda-ocorrencia-" + str(os.getpid()), **kwargs,
        )
        import laylay as root
        from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
        from mente_laylay.integracao.registro_conversa_llm import PacotePrompt, ResultadoModelo

        estado = root._estado_compartilhado_runtime
        composicao = root._composicao_turno_runtime
        composicao._servicos["_coleta_entradas_neurais"] = None
        contexto = root._resposta_ia_runtime._contexto()
        validar = contexto["validar_comandos_planejados"]
        writer = contexto.get("atualizar_plano_proposta")
        semantica = contexto.get("registrar_leitura_proposta")
        atualizar_real = estado.atualizar
        transacoes = []

        def atualizar_transacao(dominio, atualizador, **campos):
            transacoes.append(dominio)
            return atualizar_real(dominio, atualizador, **campos)
        estado.atualizar = atualizar_transacao

        resultados = {
            "instalacao": {
                "writer": callable(writer), "semantica": callable(semantica),
                "writer_owner": getattr(writer, "__self__", None) is composicao,
                "semantica_owner": getattr(semantica, "__self__", None) is composicao,
                "estado_transacional": callable(atualizar_real),
            },
            "diretos": {}, "runtime": {},
        }
        casos = {
            "playlist": ("cria a playlist foco", "PLAYLIST_CREATE", {"nome_playlist": "foco"}),
            "iot": ("liga a lâmpada", "IOT_CONTROL", {"acao": "ligar", "alvo": "lampada_quarto"}),
            "app": ("abre a Calculadora", "APP_OPEN", {"nome_app": "Calculadora"}),
        }

        def publicar(fase, principal, **campos):
            if callable(writer):
                return writer(fase, principal, **campos)
            # O caminho anterior fica disponível para demonstrar o RED causal:
            # callback existente publica sobre o novo frame internamente coerente.
            return contexto["atualizar_plano_turno"](fase, **campos)

        for dominio, (texto, intent, params) in casos.items():
            turno = root._iniciar_planejamento_turno(texto, origem="teste_ocorrencia_composicao")
            principal = ContratoPropostaPrincipal(
                turno_id=turno["id"], texto_usuario=texto,
                resposta_bruta=json.dumps({"fala": "Vou verificar.", "comandos": []}),
            )
            recibo = {
                "intent": intent, "params": params, "status": "sucesso",
                "executou": True, "confirmado": True,
                "id_solicitacao": "receipt-local-" + dominio,
                "evidencia_confirmacao": "sonda local sem efeito externo",
            }
            transacoes.clear()
            publicado = publicar("executado", principal, comandos=[recibo])
            controle_transacional = "mental" in transacoes
            preservado = publicar("resposta_planejada", principal, comandos=[])
            novo_turno = root._iniciar_planejamento_turno(texto, origem="teste_ocorrencia_composicao")
            antes = estado.snapshot()
            transacoes.clear()
            tardio = publicar("executado", principal, comandos=[recibo], fala="feito")
            resultados["diretos"][dominio] = {
                "ids_distintos": turno["id"] != novo_turno["id"],
                "controle_publicado": publicado.get("id") == turno["id"],
                "controle_transacional": controle_transacional,
                "receipt_confirmado": bool(
                    len(publicado.get("comandos") or []) == 1
                    and all(publicado["comandos"][0].get(campo) == valor for campo, valor in recibo.items())
                ),
                "receipt_preservado": preservado.get("comandos") == publicado.get("comandos"),
                "tardio_recusado": tardio == {},
                "transacao_recusa": "mental" in transacoes,
                "novo_snapshot_preservado": estado.snapshot() == antes,
            }

            for momento in ("controle", "apos_validador", "durante_dispatch"):
                chamadas = []
                validacoes = []
                snapshots_novos = []
                ids = []
                propostas = []
                comando = {"intent": intent, "params": params}

                def iniciar(entrada, **kwargs):
                    atual = root._iniciar_planejamento_turno(entrada, **kwargs)
                    ids.append(atual["id"])
                    return atual

                def trocar():
                    atual = root._iniciar_planejamento_turno(texto, origem="teste_ocorrencia_concorrente")
                    ids.append(atual["id"])
                    snapshots_novos.append(estado.snapshot())

                def validar_e_trocar(comandos, principal, extracao=None):
                    propostas.append(principal)
                    validar_original = getattr(validar, "validar_proposta_original", None)
                    resultado = (
                        validar_original(comandos, principal, extracao)
                        if callable(validar_original) else validar.validar_proposta(comandos, principal)
                    )
                    # O dispatcher pode enriquecer a lista devolvida com um
                    # receipt. Congelar esta prova antes dessa próxima fronteira.
                    validacoes.append({
                        "ocorrencia_vinculada": resultado.get("ocorrencia_vinculada"),
                        "comando_validado": resultado.get("comandos") == [comando],
                    })
                    if momento == "apos_validador":
                        trocar()
                    return resultado

                class ValidadorComIntercalacao:
                    def __call__(self, comandos):
                        return validar(comandos)
                    def validar_proposta(self, comandos, principal):
                        return validar_e_trocar(comandos, principal)
                    def validar_proposta_original(self, comandos, principal, extracao):
                        return validar_e_trocar(comandos, principal, extracao)

                def emitir(pedido):
                    chamadas.append("modelo")
                    return ResultadoModelo(json.dumps({
                        "fala": "Vou verificar.", "comandos": [comando],
                        "leitura_turno": ["pedido_acao"],
                    }), True)

                def dispatch(_ctx, _texto, comandos, *_args):
                    chamadas.append("dispatch")
                    for item in comandos:
                        item.update(
                            status="sucesso", executou=True, confirmado=True,
                            evidencia_confirmacao="sonda local sem efeito externo",
                        )
                    if momento == "durante_dispatch":
                        trocar()
                    return {"erros": []}

                def finalizar(*_args):
                    chamadas.append("finalizacao")
                    return {"fala": "Resultado local confirmado."}

                ctx = {
                    "marcar_inicio_turno": iniciar,
                    "obter_turno_atual": contexto["obter_turno_atual"],
                    "usar_modo_rapido": lambda _texto: False,
                    "preparacao_conversa": SimpleNamespace(preparar_pacote=lambda _texto: PacotePrompt(())),
                    "modelo_llm": SimpleNamespace(executar=emitir),
                    "preparar_resposta": lambda _texto, bruto: json.loads(bruto),
                    "validar_comandos_planejados": ValidadorComIntercalacao(),
                    "atualizar_plano_turno": contexto["atualizar_plano_turno"],
                    "registrar_leitura_semantica_principal": contexto["registrar_leitura_semantica_principal"],
                    "contexto_dispatch_runtime": SimpleNamespace(montar=lambda: {}),
                    "executar_comandos_json": dispatch,
                    "contexto_finalizacao_runtime": SimpleNamespace(montar=lambda: {}),
                    "finalizar_execucao": finalizar,
                }
                if callable(writer):
                    ctx["atualizar_plano_proposta"] = writer
                if callable(semantica):
                    ctx["registrar_leitura_proposta"] = semantica
                transacoes.clear()
                # O runtime foi criado pelo composition root. Isolar suas
                # portas por este getter temporário não recompõe a cadeia.
                runtime = root._resposta_ia_runtime
                contexto_getter_real = runtime._contexto_getter
                try:
                    runtime._contexto_getter = lambda: ctx
                    runtime.processar(texto, origem="teste_runtime_ocorrencia")
                finally:
                    runtime._contexto_getter = contexto_getter_real
                plano = estado.obter_copia("mental", "plano_turno_atual")
                turno_final = estado.obter_copia("mental", "turno_atual")
                resultados["runtime"][dominio + ":" + momento] = {
                    "chamadas": chamadas,
                    "validado": bool(validacoes and validacoes[0].get("ocorrencia_vinculada")),
                    "comando_validado": bool(validacoes and validacoes[0].get("comando_validado")),
                    "fonte_capturada": bool(propostas and propostas[0].turno_id == str(ids[0])),
                    "ids_distintos": len(ids) == 2 and ids[0] != ids[1],
                    "novo_snapshot_preservado": bool(snapshots_novos and estado.snapshot() == snapshots_novos[-1]),
                    "fase": plano.get("fase"), "comandos": plano.get("comandos"),
                    "semantica_publicada": bool(turno_final.get("leitura_semantica_principal", {}).get("valida")),
                    "transacao_usada": "mental" in transacoes,
                }
        sys.__stdout__.write("OCORRENCIA_COMPOSICAO " + json.dumps(resultados, ensure_ascii=False) + "\n")
    ''')
    processo = subprocess.run(
        [sys.executable, "-c", codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING="utf-8"), capture_output=True,
        text=True, encoding="utf-8", timeout=60,
    )
    assert processo.returncode == 0, processo.stderr[-3000:]
    linhas = [
        linha.removeprefix("OCORRENCIA_COMPOSICAO ")
        for linha in processo.stdout.splitlines()
        if linha.startswith("OCORRENCIA_COMPOSICAO ")
    ]
    assert len(linhas) == 1, "a composição precisa publicar a evidência da sonda"
    return json.loads(linhas[0])


def test_composicao_instala_callbacks_vinculados_ao_owner_transacional(publicacoes_composicao: dict) -> None:
    assert all(publicacoes_composicao["instalacao"].values())


@pytest.mark.parametrize("dominio", DOMINIOS)
def test_writer_instalado_preserva_receipt_legitimo_e_recusa_ocorrencia_atrasada(
    publicacoes_composicao: dict, dominio: str,
) -> None:
    resultado = publicacoes_composicao["diretos"][dominio]
    assert resultado["controle_publicado"]
    assert resultado["controle_transacional"]
    assert resultado["receipt_confirmado"]
    assert resultado["receipt_preservado"]
    assert resultado["ids_distintos"]
    assert resultado["tardio_recusado"], "outro frame coerente com a mesma frase não é a ocorrência capturada"
    assert resultado["transacao_recusa"]
    assert resultado["novo_snapshot_preservado"]


@pytest.mark.parametrize("dominio", DOMINIOS)
def test_runtime_com_writer_instalado_conclui_controle_da_ocorrencia_legitima(
    publicacoes_composicao: dict, dominio: str,
) -> None:
    resultado = publicacoes_composicao["runtime"][dominio + ":controle"]
    assert resultado["validado"]
    assert resultado["comando_validado"]
    assert resultado["fonte_capturada"]
    assert resultado["chamadas"] == ["modelo", "dispatch", "finalizacao"]
    assert resultado["transacao_usada"]
    assert resultado["semantica_publicada"]
    assert resultado["fase"] == "executado"
    assert len(resultado["comandos"]) == 1
    assert resultado["comandos"][0]["id_solicitacao"]
    assert resultado["comandos"][0]["confirmado"] is True


@pytest.mark.parametrize("dominio", DOMINIOS)
@pytest.mark.parametrize("momento", ("apos_validador", "durante_dispatch"))
def test_runtime_instalado_interrompe_retornos_atrasados_e_preserva_novo_turno(
    publicacoes_composicao: dict, dominio: str, momento: str,
) -> None:
    resultado = publicacoes_composicao["runtime"][dominio + ":" + momento]
    assert resultado["validado"], "a ocorrência era válida antes da intercalação controlada"
    assert resultado["comando_validado"]
    assert resultado["fonte_capturada"]
    assert resultado["ids_distintos"]
    esperado = ["modelo"] if momento == "apos_validador" else ["modelo", "dispatch"]
    assert resultado["chamadas"] == esperado, "o retorno antigo não deve continuar após a recusa do writer"
    assert resultado["novo_snapshot_preservado"], "plano, receipts, semântica e trilha do novo turno devem permanecer intactos"
