"""A observação P16 conserva os serviços e isola seus dados persistentes."""

from datetime import datetime
from pathlib import Path
import hashlib
import json
import threading
import subprocess
import sys

import pytest

from memoria_sqlite import MemoriaSQLite
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.composicao_turno import ComposicaoTurnoRuntime
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.autonomia.processamento_resposta_ia import extrair_leitura_semantica_principal
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.integracao.roteiro_teste_conversa import carregar_configuracao_roteiro
from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime
from scripts.roteiros.roteiro_personalidade_p16_vetos_iot import COMANDOS
from scripts.roteiros.sonda_transporte_evidencia import _gravar_resumo_p16, _instalar_observacao_p16


def test_controle_p16_deve_carregar_expectativas_pelo_loader_usado_no_main() -> None:
    roteiro = Path(__file__).resolve().parents[1] / "roteiros" / "roteiro_personalidade_p16_vetos_iot.py"
    configuracao = carregar_configuracao_roteiro(roteiro)
    assert configuracao.comandos == COMANDOS
    assert set(configuracao.expectativas_semanticas) == set(range(1, len(COMANDOS) + 1))
    assert all(item["sem_comando"] is True for item in configuracao.expectativas_semanticas.values())
    assert configuracao.silenciar_voz_durante_teste is True


def test_controle_fisico_p16_deve_preservar_barreiras_de_voz_e_execucao() -> None:
    roteiro = Path(__file__).resolve().parents[1] / "roteiros" / "roteiro_personalidade_p16_voz_avatar.py"
    configuracao = carregar_configuracao_roteiro(roteiro)
    assert configuracao.silenciar_voz_durante_teste is False
    assert configuracao.aguardar_confirmacao_execucao is True
    assert configuracao.parar_sem_resposta is True


def test_controle_temporal_p16_deve_carregar_seis_relatos_sem_efeito() -> None:
    roteiro = Path(__file__).resolve().parents[1] / "roteiros" / "roteiro_personalidade_p16_relato_temporal.py"
    configuracao = carregar_configuracao_roteiro(roteiro)
    assert len(configuracao.comandos) == 6
    assert set(configuracao.expectativas_semanticas) == set(range(1, 7))
    assert all(item["sem_comando"] for item in configuracao.expectativas_semanticas.values())
    assert configuracao.silenciar_voz_durante_teste is True


def test_controle_identidade_carrega_negativos_nomeacao_e_consulta_pelo_loader_real() -> None:
    roteiro = Path(__file__).resolve().parents[1] / "roteiros" / "roteiro_memoria_pessoas_identidade.py"
    configuracao = carregar_configuracao_roteiro(roteiro)
    assert len(configuracao.comandos) == 8
    assert configuracao.comandos[0] == "Meu irmão está bravo. Eu me sinto culpado."
    assert configuracao.expectativas_semanticas[4]["alvos_any"] == ("Esta",)
    assert configuracao.expectativas_semanticas[6]["intents_any"] == ("PEOPLE_QUERY",)
    assert configuracao.expectativas_semanticas[8]["alvos_any"] == ("Ana",)
    assert configuracao.silenciar_voz_durante_teste is True


def test_sonda_identidade_aborta_sem_isolamento_antes_de_abrir_runtime():
    sonda = Path(__file__).resolve().parents[1] / "roteiros" / "sonda_transporte_evidencia.py"
    retorno = subprocess.run([sys.executable, str(sonda), "--roteiro",
        "roteiro_memoria_pessoas_identidade.py", "--capturar-p16"],
        capture_output=True, text=True, timeout=10)
    assert retorno.returncode == 2
    assert "roteiro de identidade exige" in retorno.stderr
    assert "CAPTURA_LOCAL:" not in retorno.stdout


@pytest.mark.parametrize("isolar", [False, True])
def test_isolamento_opcional_de_pessoas_preserva_servico_e_arquivo_pessoal(tmp_path, isolar):
    pessoal = tmp_path / "pessoas_pessoais.json"
    pessoal.write_text('{"sentinela": "preservar"}', encoding="utf-8")
    anterior = pessoal.read_bytes()
    coleta = tmp_path / "coleta"
    coleta.mkdir()
    receipts = []
    callback = lambda *args, **kwargs: receipts.append((args, kwargs))
    estado = {}
    pendencia = PendenciaAcaoRuntime(
        estado_getter=lambda: estado,
        estado_atualizar=lambda atualizar: estado.update(atualizar(dict(estado))) or estado,
        log=lambda *_args: None,
    )
    restauracoes = _instalar_observacao_p16(coleta, threading.local(), isolar_pessoas=isolar)
    try:
        servico = MemoriaPessoasRuntime(
            caminho=pessoal, falar=lambda *_args: None, pendencia_runtime=pendencia,
            registrar_resultado=callback, log=lambda *_args: None,
        )
        assert servico.caminho == (coleta / "pessoas_proprias.json" if isolar else pessoal)
        assert servico.registrar_resultado is callback
        if isolar:
            assert servico.processar("Meu irmão se chama Esta.") is False
            dados = json.loads(servico.caminho.read_bytes())
            assert dados["pessoas"][0]["nome"] == "Esta"
            assert receipts[0][0][0]["confirmado"] is True
            assert servico.processar("Meu irmão estava bravo.") is False
            eventos = [json.loads(s) for s in (coleta / "p16.jsonl").read_text(encoding="utf-8").splitlines()]
            negativos = [e for e in eventos if e["etapa"] == "pessoas_observacao"][-1]
            assert negativos["antes_sha256"] == negativos["depois_sha256"]
            assert negativos["tratado"] is False
        assert pessoal.read_bytes() == anterior
    finally:
        for owner, nome, metodo in reversed(restauracoes):
            setattr(owner, nome, metodo)


def test_observacao_semantica_preserva_retorno_evento_e_estado_do_publicador(tmp_path: Path) -> None:
    texto = "antes eu estava triste, mas agora estou aliviado"
    turno = classificar_modalidade_turno(texto)
    retrato, _ = construir_retrato_turno(texto, turno=turno, mente={}, contexto_perceptivo={})
    turno["retrato_id"] = retrato["id"]
    estado = EstadoCompartilhadoRuntime(mental={
        "turno_atual": turno,
        "plano_turno_atual": planejar_turno(texto, turno=turno),
        "retrato_turno_atual": retrato,
    })
    composicao = ComposicaoTurnoRuntime(servicos={
        "_estado_compartilhado_runtime": estado, "print": lambda *_: None,
    })
    principal = ContratoPropostaPrincipal(
        turno_id=turno["id"], texto_usuario=texto,
        resposta_bruta=json.dumps({"fala": "Entendi.", "comandos": [], "leitura_turno": ["relato"],
            "leitura_emocional": {"estado_usuario": "alivio", "intensidade": 1,
                "trecho_evidencia": "agora estou aliviado", "causa_expressa": "agora estou aliviado",
                "confianca": 0.99}}, ensure_ascii=False),
    )
    leitura = extrair_leitura_semantica_principal(principal, texto)
    snapshot = estado.snapshot()
    esperada = composicao.registrar_leitura_proposta(texto, leitura, principal)
    assert esperada["leitura_emocional"]["estado_usuario"] == "alivio"
    final_esperado = estado.snapshot()
    estado.substituir("mental", snapshot["mental"])
    restauracoes = _instalar_observacao_p16(tmp_path, threading.local())
    try:
        publicada = composicao.registrar_leitura_proposta(texto, leitura, principal)
    finally:
        for owner, nome, metodo in reversed(restauracoes):
            setattr(owner, nome, metodo)
    assert publicada == esperada
    # O evento usa o relógio real; sua identidade temporal pode variar.
    atual = estado.snapshot()
    assert atual["conversacional"] == final_esperado["conversacional"]
    evento = atual["mental"]["plano_turno_atual"]["evento_emocional_causal"]
    anterior = final_esperado["mental"]["plano_turno_atual"]["evento_emocional_causal"]
    for chave in ("origem", "causa", "evidencia_ref", "permite_expressao", "autoriza_execucao"):
        assert evento[chave] == anterior[chave]
    captura = json.loads((tmp_path / "p16.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert captura["etapa"] == "publicacao_leitura"
    assert captura["leitura_publicada"] == publicada
    assert captura["frame"]["plano_turno_atual"]["evento_emocional_causal"] == evento


@pytest.mark.parametrize("texto", COMANDOS)
def test_controle_de_veto_iot_nao_deve_autorizar_efeito_pelo_classificador_real(texto: str) -> None:
    turno = classificar_modalidade_turno(texto, normalizar_texto=normalizar_texto)
    assert turno["autoriza_execucao"] is False
    assert turno["veto_execucao_operacional"] is True
    assert turno["requer_esclarecimento"] is False
    plano = planejar_turno(texto, turno=turno)
    assert plano["autoriza_execucao"] is False
    assert plano["requer_execucao"] is False


def test_sonda_p16_deve_isolar_sqlite_e_resumo_diario_sem_tocar_dados_anteriores(tmp_path: Path) -> None:
    pessoal = tmp_path / "memoria pessoal"
    pessoal.mkdir()
    agora = datetime(2026, 10, 1, 20, 0)
    diario = pessoal / f"memoria_{agora.strftime('%d-%m-%Y')}.txt"
    anterior = f"RESUMO DO DIA {agora.strftime('%d-%m-%Y')}:\n\nCONTROLE ANTERIOR"
    diario.write_text(anterior, encoding="utf-8")
    pasta = tmp_path / "coleta"
    pasta.mkdir()
    restauracoes = _instalar_observacao_p16(pasta, threading.local())
    try:
        banco = MemoriaSQLite(str(pessoal / "controle.sqlite"))
        assert Path(banco.db_path).parent == pasta / "sqlite_proprio"
        assert not (pessoal / "controle.sqlite").exists()
        memoria = MemoriaLaylay(
            pasta_memoria=str(pessoal), enviar_mensagem=lambda mensagens: "",
            log=lambda texto: None, agora=lambda: agora,
        )
        assert Path(memoria.arquivo_diario).parent == pasta / "resumo_proprio"
        assert memoria.resumo_do_dia == "" and memoria.historico_recente == []
        memoria.adicionar_interacao("como eu poderia desligar a lâmpada?", "Explicação sem executar.")
        assert "Explicação sem executar." in Path(memoria.arquivo_diario).read_text(encoding="utf-8")
        assert diario.read_text(encoding="utf-8") == anterior
    finally:
        for owner, nome, metodo in reversed(restauracoes):
            setattr(owner, nome, metodo)


def test_coleta_sem_geracao_valida_nao_deve_promover_placar_a_prova_positiva(tmp_path: Path) -> None:
    captura = tmp_path / "p16.jsonl"
    registros = [
        {"etapa": "validacao_original", "principal": {"estado": "falha_tecnica"},
         "resultado": {"violacoes_proposta_original": []}},
        {"etapa": "dispatcher", "comandos": []},
    ]
    captura.write_text("\n".join(json.dumps(item) for item in registros), encoding="utf-8")
    hash_antes = hashlib.sha256(captura.read_bytes()).hexdigest()
    resumo = _gravar_resumo_p16(tmp_path, 0)
    assert resumo["status"] == "fonte_tecnica_insuficiente"
    assert resumo["positivo_p16_status"] == "nao_comprovado"
    assert hashlib.sha256(captura.read_bytes()).hexdigest() == hash_antes


def test_ausencia_de_validacao_nao_deve_contar_como_controle_negativo(tmp_path: Path) -> None:
    (tmp_path / "p16.jsonl").write_text("", encoding="utf-8")
    resumo = _gravar_resumo_p16(tmp_path, 0)
    assert resumo["status"] == "coleta_incompleta"
    assert resumo["positivo_p16_status"] == "nao_comprovado"
