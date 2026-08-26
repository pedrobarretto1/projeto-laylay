from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path.cwd()
ALVO = ROOT / "mente_laylay" / "integracao" / "roteiro_teste_conversa.py"
BACKUP_DIR = ROOT / ".rt1_h1_backup_pre_candidato"
BACKUP = BACKUP_DIR / "roteiro_teste_conversa.py"


def falhar(msg: str) -> None:
    raise SystemExit("\n❌ RT1-H1 V1 abortado: " + msg + "\n")


if not ALVO.is_file():
    falhar(f"arquivo não encontrado: {ALVO}")

if BACKUP_DIR.exists():
    falhar(
        f"backup já existe: {BACKUP_DIR}\n"
        "Isso normalmente significa que o candidato já foi aplicado ou tentado. "
        "Não vou sobrescrever a baseline."
    )

texto = ALVO.read_text(encoding="utf-8")

helper_antigo = '    @staticmethod\n    def _aguardar_processamento(retorno: Any, prazo: float, monotonic) -> None:\n        if isinstance(retorno, threading.Thread):\n            while retorno.is_alive() and monotonic() < prazo:\n                retorno.join(timeout=min(0.1, max(0.0, prazo - monotonic())))\n            return\n        result = getattr(retorno, "result", None)\n        if callable(result):\n            try:\n                result(timeout=max(0.0, prazo - monotonic()))\n            except TimeoutError:\n                pass\n'
helper_novo = '    @staticmethod\n    def _aguardar_processamento(\n        retorno: Any,\n        prazo: float,\n        monotonic,\n        sleep=time.sleep,\n    ) -> bool:\n        # RT1-H1: resposta publicada/plano terminal nao provam fim do worker.\n        # Retornos nao aguardaveis representam senders sincronos.\n        if isinstance(retorno, threading.Thread):\n            while retorno.is_alive() and monotonic() < prazo:\n                retorno.join(\n                    timeout=min(0.1, max(0.0, prazo - monotonic()))\n                )\n            return not retorno.is_alive()\n\n        result = getattr(retorno, "result", None)\n        if callable(result):\n            restante = max(0.0, prazo - monotonic())\n            try:\n                result(timeout=restante)\n                return True\n            except TimeoutError:\n                return False\n            except TypeError:\n                # Future/Task sem result(timeout): so libera com prova done().\n                done = getattr(retorno, "done", None)\n                if not callable(done):\n                    return False\n                while monotonic() < prazo:\n                    try:\n                        if bool(done()):\n                            return True\n                    except Exception:\n                        return False\n                    sleep(min(0.05, max(0.0, prazo - monotonic())))\n                try:\n                    return bool(done())\n                except Exception:\n                    return False\n            except Exception:\n                # Excecao da tarefa prova terminalidade. O resultado\n                # operacional continua sendo julgado pelo plano do turno.\n                return True\n\n        return True\n'
marcador_antigo = '                sucesso_total = False\n                break\n            voz_concluida, voz_observada = self._aguardar_voz_concluir()\n'
marcador_novo = '                sucesso_total = False\n                break\n\n            # RT1-H1 — BARREIRA DO WORKER CANONICO\n            # N+1 nao ganha autoridade de captura enquanto o worker N vive.\n            processamento_concluido = self._aguardar_processamento(\n                retorno,\n                prazo,\n                self.monotonic,\n                self.sleep,\n            )\n            if not processamento_concluido:\n                self._anexar_plano_bruto(\n                    indice=indice,\n                    comando=comando,\n                    plano=plano,\n                )\n                self._atualizar_item(\n                    indice,\n                    status="processamento_nao_finalizado",\n                    resposta=resposta,\n                    finalizado_em=self.clock(),\n                    plano=self._plano_compacto_checkpoint(plano),\n                    _plano_avaliacao=plano,\n                    avaliacao=self._avaliacao_mecanica(\n                        plano,\n                        respondeu=True,\n                    ),\n                    resultado_turno_concluido=resultado_turno_concluido,\n                    motivo_resultado=motivo_resultado,\n                    processamento_concluido=False,\n                )\n                self._anexar_conversa(\n                    f"### Laylay\\n\\n{resposta}\\n\\n"\n                    "> ⚠️ A resposta e o plano apareceram, mas o worker "\n                    "canonico deste turno ainda estava vivo no fim do prazo. "\n                    "O proximo comando nao foi enviado.\\n\\n"\n                )\n                self.log(\n                    f"⚠️ [ROTEIRO:{numero:03d}] worker canonico nao "\n                    "finalizado; sequencia interrompida com seguranca"\n                )\n                sucesso_total = False\n                break\n\n            voz_concluida, voz_observada = self._aguardar_voz_concluir()\n'
campo_antigo = '                resultado_turno_concluido=resultado_turno_concluido,\n                motivo_resultado=motivo_resultado,\n            )\n'
campo_novo = '                resultado_turno_concluido=resultado_turno_concluido,\n                motivo_resultado=motivo_resultado,\n                processamento_concluido=True,\n            )\n'

if texto.count(helper_antigo) != 1:
    falhar(
        "helper _aguardar_processamento não corresponde exatamente à baseline "
        f"esperada (ocorrências={texto.count(helper_antigo)}). "
        "Nenhuma alteração aplicada."
    )

texto_novo = texto.replace(helper_antigo, helper_novo, 1)

if texto_novo.count(marcador_antigo) != 1:
    falhar(
        "fronteira resultado→voz não corresponde exatamente à baseline "
        f"esperada (ocorrências={texto_novo.count(marcador_antigo)}). "
        "Nenhuma alteração aplicada."
    )

texto_novo = texto_novo.replace(marcador_antigo, marcador_novo, 1)

qtd = texto_novo.count(campo_antigo)
if qtd != 1:
    falhar(
        "gravação final do turno não corresponde à baseline esperada "
        f"(ocorrências={qtd}). Nenhuma alteração aplicada."
    )

texto_novo = texto_novo.replace(campo_antigo, campo_novo, 1)

BACKUP_DIR.mkdir(parents=True, exist_ok=False)
shutil.copy2(ALVO, BACKUP)

tmp = ALVO.with_suffix(ALVO.suffix + ".rt1_h1.tmp")
tmp.write_text(texto_novo, encoding="utf-8")
tmp.replace(ALVO)

print("✅ Candidato RT1-H1 V1 aplicado com sucesso.")
print(f"  * {ALVO}")
print(f"Backup da baseline local: {BACKUP_DIR}")
print()
print("Alteração limitada ao harness de roteiro.")
print("R1, árbitro, coordenador, executores e avaliador sem mudanças.")
