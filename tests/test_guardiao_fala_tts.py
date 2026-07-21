from __future__ import annotations

import threading

from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.personalidade.oralidade import preparar_texto_para_tts
from mente_laylay.personalidade.voz_runtime import VozRuntime


def test_promessa_de_acompanhamento_sem_mecanismo_e_corrigida() -> None:
    resultado = validar_alegacoes_da_fala(
        "Vou te manter atualizado sobre o lançamento quando sair.",
        plano={"comandos": []}, origem="resposta_ia",
    )

    assert "promessa_sem_mecanismo" in resultado["problemas"]
    assert "não acompanho novidades sozinha" in resultado["fala"]


def test_oferta_de_play_by_play_futuro_sem_monitoramento_e_bloqueada() -> None:
    resultado = validar_alegacoes_da_fala(
        "Quer um play-by-play das novidades quando sair?",
        plano={"comandos": []}, origem="resposta_ia",
    )

    assert "promessa_sem_mecanismo" in resultado["problemas"]


def test_companhia_emocional_sem_promessa_tecnica_e_permitida() -> None:
    fala = "Vou te acompanhar nessa expectativa e torcer junto."
    resultado = validar_alegacoes_da_fala(
        fala, plano={"comandos": []}, origem="resposta_ia",
    )

    assert resultado["problemas"] == []
    assert resultado["fala"] == fala


def test_lembrete_real_confirmado_permite_promessa_correspondente() -> None:
    resultado = validar_alegacoes_da_fala(
        "Vou te avisar quando chegar a hora.",
        plano={"comandos": [{
            "intent": "AGENDAR_LEMBRETE", "executou": True, "confirmado": True,
        }]},
        origem="resposta_ia",
    )

    assert resultado["problemas"] == []
    assert resultado["fala"] == "Vou te avisar quando chegar a hora."


def test_estado_do_pc_sem_leitura_real_e_bloqueado() -> None:
    resultado = validar_alegacoes_da_fala(
        "A CPU está em 35 por cento e a memória está normal.",
        plano={"comandos": []}, origem="resposta_ia",
    )

    assert "estado_real_sem_leitura" in resultado["problemas"]
    assert "ainda não consultei" in resultado["fala"]


def test_estado_confirmado_por_executor_e_preservado() -> None:
    fala = "A lâmpada está desligada."
    resultado = validar_alegacoes_da_fala(
        fala,
        plano={"comandos": [{
            "intent": "IOT_STATUS", "executou": True,
            "confirmado": True, "status": "desligado",
        }]},
        origem="resposta_ia",
    )

    assert resultado["problemas"] == []
    assert resultado["fala"] == fala


def test_estado_subjetivo_da_personalidade_continua_permitido() -> None:
    fala = "Fiquei curiosa para ver como esse projeto vai evoluir."
    resultado = validar_alegacoes_da_fala(
        fala, plano={"comandos": []}, origem="resposta_ia",
    )

    assert resultado["problemas"] == []
    assert resultado["fala"] == fala


def test_verificador_final_aplica_guardiao_de_promessas() -> None:
    resultado = verificar_fala_turno(
        "Vou acompanhar as novidades e te avisar quando sair.",
        plano={"texto_usuario": "estou animado para o lançamento", "comandos": []},
        origem="ia_final",
    )

    assert "promessa_sem_mecanismo" in resultado["problemas"]
    assert "não acompanho novidades sozinha" in resultado["fala"]


def test_clima_compacto_ganha_conectores_apenas_para_tts() -> None:
    escrito = "Ensolarado 17 graus Celsius, umidade em 52% e vento de 10 quilômetros por hora."
    falado = preparar_texto_para_tts(escrito)

    assert escrito == "Ensolarado 17 graus Celsius, umidade em 52% e vento de 10 quilômetros por hora."
    assert "Ensolarado, com 17 graus Celsius" in falado
    assert "com umidade em 52 por cento" in falado


def test_horario_url_e_metricas_ficam_pronunciaveis() -> None:
    falado = preparar_texto_para_tts(
        "Às 17:30, CPU em 82%. Veja https://www.exemplo.com/status."
    )

    assert "17 horas e 30 minutos" in falado
    assert "o processador em 82 por cento" in falado
    assert "exemplo ponto com" in falado
    assert "https" not in falado


def test_apenas_ultima_pergunta_mantem_entonacao_interrogativa() -> None:
    falado = preparar_texto_para_tts("Tudo bem? Quer conversar? Como foi seu dia?")

    assert falado.count("?") == 1
    assert falado.endswith("?")


def test_runtime_exibe_original_e_envia_versao_oral_ao_tts() -> None:
    logs = []

    class Edge:
        ultimo_texto = ""

        class Communicate:
            def __init__(self, texto, **_kwargs):
                Edge.ultimo_texto = texto

            async def save(self, _caminho):
                return None

    class SoundFile:
        @staticmethod
        def read(_caminho):
            return [], 16000

    class Stream:
        active = False

    class SoundDevice:
        @staticmethod
        def play(*_args, **_kwargs):
            return None

        @staticmethod
        def get_stream():
            return Stream()

    runtime = VozRuntime(
        fallback_fala="fallback", voice="voz",
        edge_tts_mod=Edge, sounddevice_mod=SoundDevice,
        soundfile_mod=SoundFile, pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        preparar_tts_cb=preparar_texto_para_tts,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("", "", ""),
        compor_fala_proativa_cb=lambda _itens: ("", "calma", 1),
        ajustar_estado_fala_cb=lambda *_args: None,
        interrupt_event=threading.Event(),
        log=lambda mensagem: logs.append(mensagem),
    )
    escrito = "Ensolarado 17 graus Celsius, umidade em 52%."

    runtime.reproduzir_fala(escrito, "calma", 1)

    assert escrito in logs
    assert "Ensolarado, com 17 graus Celsius" in Edge.ultimo_texto
    assert Edge.ultimo_texto != escrito
