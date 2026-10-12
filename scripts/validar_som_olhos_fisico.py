"""Demonstração controlada de olhos/bips na COM4; nunca envia MOTOR.

Usa a composição de produção e o estado causal real. Sucesso/falha no fim
são apenas padrões sonoros demonstrados, não receipts de ações externas.
"""
from pathlib import Path
import hashlib
import json
import sys
import time
from types import SimpleNamespace

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from mente_laylay.integracao.composicao_rosto_oled import criar_composicao_rosto_oled_runtime
from mente_laylay.memoria_mental.estado_compartilhado_runtime import criar_estado_compartilhado_runtime
from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.emocoes.estado_emocional import aplicar_evento_emocional

estado = criar_estado_compartilhado_runtime()
runtime = criar_composicao_rosto_oled_runtime(estado=estado,
    observabilidade=SimpleNamespace(relatar_falha=lambda *a, **k: None), porta="COM4")
passos = []
falha = ""

def manter(segundos: float) -> None:
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        assert runtime.sincronizar(), runtime.diagnostico()
        time.sleep(.18)

try:
    manter(2.3)
    assert runtime.diagnostico()["som"]["suportado"]
    passos.append({"evento": "acordar", "diagnostico": runtime.diagnostico()})
    for emocao in ("alegre", "triste", "brava", "envergonhada", "surpresa", "debochada", "irritada", "acalmando-se", "calma"):
        agora = time.time()
        evento = criar_evento_emocional_causal(origem="controle_rosto",
            causa="demonstracao expressamente solicitada", evidencia_ref="teste:olhos-som",
            natureza_evidencia="fato_observado", responsabilidade="usuario",
            confianca=.97, relevancia=.95, intensidade=2, permite_expressao=True,
            emocao=emocao, nivel=2, ts=agora, validade_s=120)
        estado.substituir("conversacional", aplicar_evento_emocional({}, evento, agora=agora))
        manter(2.3)
        passos.append({"emocao": emocao, "diagnostico": runtime.diagnostico()})
    # Demonstrar as melodias operacionais sem fabricar um sucesso de ação.
    for tipo in (1, 2):
        runtime._seq_som += 1
        campos = f"{runtime._sessao} {runtime._seq_som} {tipo}"
        runtime._escrever(f"SOUND 1 {campos}")
        assert runtime._esperar(f"SOUNDACK 1 {campos}", .5)
        passos.append({"melodia_demonstrada": tipo, "sequencia_aceita": True,
                       "acao_externa_executada": False})
        manter(2.3)
    runtime._seq_parada += 1
    campos = f"{runtime._sessao} {runtime._seq_parada}"
    runtime._escrever(f"STOP 1 {campos}")
    assert runtime._esperar(f"SACK 1 {campos}", .5)
except Exception as erro:
    falha = str(erro)
finally:
    runtime.encerrar()

fonte = RAIZ / "firmware/rosto_laylay/rosto_laylay.ino"
header = fonte.with_name("som_expressivo.h")
destino = RAIZ / "artifacts/rosto_oled/som_olhos/receipt_fisico.json"
dados = {"passos": passos, "fonte_sha256": hashlib.sha256(fonte.read_bytes()).hexdigest(),
         "som_sha256": hashlib.sha256(header.read_bytes()).hexdigest(), "movimento_enviado": False,
         "falha": falha,
         "audicao_humana": "pendente", "visual_humano": "pendente"}
destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"receipt": str(destino), "passos_confirmados": len(passos),
                  "movimento_enviado": False, "falha": falha}, ensure_ascii=False))
if falha:
    raise SystemExit(1)
