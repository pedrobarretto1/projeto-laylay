from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from mente_laylay.percepcao.ouvido_whisper import (
    OuvidoWhisperRuntime,
    extrair_comando_com_ativacao,
    limpar_diccao_e_ruido,
)
from mente_laylay.percepcao.normalizacao_fonetica import (
    corrigir_entrada_fonetica,
    extrair_ensino_pronuncia,
)
from mente_laylay.percepcao.dispositivos_audio import selecionar_dispositivo_audio


class ModeloFalso:
    def __init__(self, texto="Oi Laylay") -> None:
        self.texto = texto
        self.chamadas = []

    def transcribe(self, audio, **kwargs):
        self.chamadas.append((audio, kwargs))
        return [SimpleNamespace(text=self.texto)], SimpleNamespace()


class ModeloFalsoComRetry(ModeloFalso):
    def transcribe(self, audio, **kwargs):
        self.chamadas.append((audio, kwargs))
        texto = "" if len(self.chamadas) == 1 else "Lay, desliga o ventilador"
        return [SimpleNamespace(text=texto)], SimpleNamespace()


class SoundDeviceFalso:
    def __init__(self, chunks=None) -> None:
        self.default = SimpleNamespace(device=(1, 4))
        self.chunks = list(chunks or [])
        self.pos = 0
        self.configuracao_stream = {}

    def query_devices(self):
        return [
            {"name": "Steam Streaming Microphone", "max_input_channels": 1, "default_samplerate": 48000},
            {"name": "Microfone Realtek", "max_input_channels": 2, "default_samplerate": 48000},
            {"name": "Alto-falantes", "max_input_channels": 0, "default_samplerate": 48000},
        ]

    def check_input_settings(self, **kwargs):
        return None

    def InputStream(self, **kwargs):
        self.configuracao_stream = dict(kwargs)
        owner = self

        class Stream:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self, _bloco):
                chunk = owner.chunks[owner.pos]
                owner.pos += 1
                return chunk.reshape(-1, 1), False

        return Stream()


def test_audio_seleciona_entrada_e_saida_padrao_do_sistema():
    sd = SoundDeviceFalso()
    sd.query_devices = lambda: [
        {"name": "Microfone USB", "max_input_channels": 1, "max_output_channels": 0},
        {"name": "Microfone Realtek", "max_input_channels": 2, "max_output_channels": 0},
        {"name": "Monitor HDMI", "max_input_channels": 0, "max_output_channels": 2},
        {"name": "Headset padrão", "max_input_channels": 0, "max_output_channels": 2},
        {"name": "Alto-falantes", "max_input_channels": 0, "max_output_channels": 2},
    ]
    sd.default.device = (1, 4)

    entrada = selecionar_dispositivo_audio(sd, "entrada")
    saida = selecionar_dispositivo_audio(sd, "saida")

    assert entrada == (1, sd.query_devices()[1], "padrão do sistema")
    assert saida == (4, sd.query_devices()[4], "padrão do sistema")


def test_ouvido_seleciona_entrada_padrao_e_transcreve_em_portugues():
    sd = SoundDeviceFalso()
    modelo = ModeloFalso("  Oi   Laylay  ")
    factory_args = []
    ouvido = OuvidoWhisperRuntime(
        processar_texto=lambda _: None,
        esta_falando=lambda: False,
        sounddevice_mod=sd,
        numpy_mod=np,
        model_factory=lambda *args, **kwargs: factory_args.append((args, kwargs)) or modelo,
        log=lambda *_: None,
    )

    indice, info = ouvido.selecionar_dispositivo()
    texto = ouvido.transcrever(np.ones(1600, dtype=np.float32) * 0.1)

    assert indice == 1
    assert info["name"] == "Microfone Realtek"
    assert texto == "oi laylay"
    assert factory_args[0][0] == ("turbo",)
    assert modelo.chamadas[0][1]["language"] == "pt"


def test_ouvido_detecta_fala_e_entrega_ao_mesmo_fluxo_do_chat():
    ambiente = [np.zeros(1600, dtype=np.float32) for _ in range(10)]
    voz = [np.ones(1600, dtype=np.float32) * 0.1 for _ in range(3)]
    silencio = [np.zeros(1600, dtype=np.float32) for _ in range(10)]
    sd = SoundDeviceFalso(ambiente + voz + silencio)
    entregues = []
    ouvido = OuvidoWhisperRuntime(
        processar_texto=entregues.append,
        esta_falando=lambda: False,
        sounddevice_mod=sd,
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: ModeloFalso("Lay, liga a luz"),
        deve_continuar=lambda: sd.pos < len(sd.chunks),
        entrega_assincrona=False,
        log=lambda *_: None,
    )

    ouvido.executar()

    assert entregues == ["liga a luz"]
    assert sd.configuracao_stream["device"] == 1
    assert sd.configuracao_stream["samplerate"] == 16000


def test_ouvido_calibra_ruido_alto_sem_engolir_a_voz():
    ambiente = [np.ones(1600, dtype=np.float32) * 0.02 for _ in range(10)]
    voz = [np.ones(1600, dtype=np.float32) * 0.08 for _ in range(3)]
    silencio = [np.ones(1600, dtype=np.float32) * 0.02 for _ in range(10)]
    sd = SoundDeviceFalso(ambiente + voz + silencio)
    entregues = []
    logs = []
    ouvido = OuvidoWhisperRuntime(
        processar_texto=entregues.append,
        esta_falando=lambda: False,
        sounddevice_mod=sd,
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: ModeloFalso("Lay, liga a luz"),
        deve_continuar=lambda: sd.pos < len(sd.chunks),
        entrega_assincrona=False,
        log=logs.append,
    )

    ouvido.executar()

    assert entregues == ["liga a luz"]
    assert any("calibrado ruído=0.0200" in mensagem for mensagem in logs)
    assert any("Voz detectada" in mensagem for mensagem in logs)


def test_ouvido_pode_ser_desativado_sem_abrir_dispositivo():
    sd = SoundDeviceFalso()
    logs = []
    ouvido = OuvidoWhisperRuntime(
        processar_texto=lambda _: None,
        esta_falando=lambda: False,
        sounddevice_mod=sd,
        numpy_mod=np,
        env_getter=lambda nome, padrao="": "0" if nome == "LAYLAY_MICROFONE_ATIVO" else padrao,
        log=logs.append,
    )

    ouvido.executar()

    assert sd.configuracao_stream == {}
    assert any("desativado" in mensagem for mensagem in logs)


def test_ouvido_refaz_transcricao_curta_quando_vad_do_whisper_retorna_vazio():
    modelo = ModeloFalsoComRetry()
    ouvido = OuvidoWhisperRuntime(
        processar_texto=lambda _: None,
        esta_falando=lambda: False,
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: modelo,
        entrega_assincrona=False,
        log=lambda *_: None,
    )

    texto, _ = ouvido.transcrever_com_confianca(np.ones(1600, dtype=np.float32))

    assert texto == "lay, desliga o ventilador"
    assert len(modelo.chamadas) == 2
    assert modelo.chamadas[1][1]["vad_filter"] is False
    assert ouvido._ultima_metricas_transcricao["reprocessado"] is True


def test_correcao_operacional_de_dicao_nao_envia_verbo_errado_para_ia():
    assert limpar_diccao_e_ruido("Lica a luis") == "liga a luz"
    assert limpar_diccao_e_ruido("desligo ventilador") == "desliga ventilador"


def test_ouvido_descarta_transcricao_quando_modo_chat_esta_ativo():
    entregues = []
    modelo_criado = []
    ouvido = OuvidoWhisperRuntime(
        processar_texto=entregues.append,
        esta_falando=lambda: False,
        escuta_permitida=lambda: False,
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: modelo_criado.append(True) or ModeloFalso(),
        entrega_assincrona=False,
        log=lambda *_: None,
    )

    ouvido._entregar(np.ones(1600, dtype=np.float32) * 0.1)

    assert entregues == []
    assert modelo_criado == []


def test_ouvido_ignora_fala_sem_palavra_de_ativacao():
    entregues = []
    ouvido = OuvidoWhisperRuntime(
        processar_texto=entregues.append,
        esta_falando=lambda: False,
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: ModeloFalso("liga a luz"),
        entrega_assincrona=False,
        log=lambda *_: None,
    )
    ouvido._entregar(np.ones(1600, dtype=np.float32))
    assert entregues == []


def test_ouvido_aceita_comando_apos_ativacao_isolada():
    entregues = []
    agora = [10.0]
    modelo = ModeloFalso("Lay")
    ouvido = OuvidoWhisperRuntime(
        processar_texto=entregues.append,
        esta_falando=lambda: False,
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: modelo,
        entrega_assincrona=False,
        monotonic=lambda: agora[0],
        log=lambda *_: None,
    )
    audio = np.ones(1600, dtype=np.float32)
    ouvido._entregar(audio)
    modelo.texto = "liga a luz"
    agora[0] = 14.0
    ouvido._entregar(audio)
    assert entregues == ["liga a luz"]


def test_ouvido_descarta_baixa_confianca():
    class ModeloBaixaConfianca(ModeloFalso):
        def transcribe(self, audio, **kwargs):
            return [SimpleNamespace(text="Lay, liga a luz", avg_logprob=-3.0)], SimpleNamespace()

    entregues = []
    ouvido = OuvidoWhisperRuntime(
        processar_texto=entregues.append,
        esta_falando=lambda: False,
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: ModeloBaixaConfianca(),
        entrega_assincrona=False,
        log=lambda *_: None,
    )
    ouvido._entregar(np.ones(1600, dtype=np.float32))
    assert entregues == []


def test_modo_jogo_aceita_comando_curto_e_rejeita_conversa_longa():
    entregues = []
    modelo = ModeloFalso("Lay, liga a luz")
    ouvido = OuvidoWhisperRuntime(
        processar_texto=entregues.append,
        esta_falando=lambda: False,
        modo_jogo_ativo=lambda: True,
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: modelo,
        entrega_assincrona=False,
        log=lambda *_: None,
    )
    audio = np.ones(1600, dtype=np.float32)
    ouvido._entregar(audio)
    modelo.texto = "Lay, queria conversar sobre como foi o meu dia no campeonato"
    ouvido._entregar(audio)
    assert entregues == ["liga a luz"]


def test_ouvido_descarta_eco_recente_da_laylay():
    entregues = []
    agora = [20.0]
    ouvido = OuvidoWhisperRuntime(
        processar_texto=entregues.append,
        esta_falando=lambda: False,
        ultima_fala_laylay=lambda: "Lay, liguei a luz do quarto para você.",
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: ModeloFalso("Lay, liguei a luz do quarto para você"),
        entrega_assincrona=False,
        monotonic=lambda: agora[0],
        log=lambda *_: None,
    )
    ouvido._ultima_fala_laylay_ts = 19.0
    ouvido._entregar(np.ones(1600, dtype=np.float32))
    assert entregues == []


def test_corretor_estatico_nao_corrompe_palavras_legitimas():
    assert limpar_diccao_e_ruido("eu troco o coco depois") == "eu troco o coco depois"
    assert limpar_diccao_e_ruido("coloco música agora") == "coloco música agora"
    assert limpar_diccao_e_ruido("obrigado") == "obrigado"


def test_normalizacao_fonetica_so_aproxima_entidade_conhecida():
    corrigido, alteracoes = corrigir_entrada_fonetica(
        "abre fragponk",
        entidades=["FragPunk", "Steam"],
    )
    assert corrigido == "abre FragPunk"
    assert alteracoes[0]["motivo"] == "entidade_conhecida"
    intacto, _ = corrigir_entrada_fonetica("comi coco", entidades=["código"])
    assert intacto == "comi coco"


def test_pronuncia_confirmada_tem_prioridade_e_pode_ser_ensinada():
    assert extrair_ensino_pronuncia("quando eu falar freguipanque quero dizer FragPunk") == (
        "freguipanque", "FragPunk",
    )
    corrigido, alteracoes = corrigir_entrada_fonetica(
        "abre freguipanque",
        pronuncias={"freguipanque": "FragPunk"},
    )
    assert corrigido == "abre FragPunk"
    assert alteracoes[0]["motivo"] == "pronuncia_aprendida"


def test_palavra_de_ativacao_aceita_variacoes_foneticas_conservadoras():
    assert extrair_comando_com_ativacao("Lai, liga a luz") == (True, "liga a luz")
    assert extrair_comando_com_ativacao("Leilei abre a Steam") == (True, "abre a steam")
    assert extrair_comando_com_ativacao("lei municipal") == (False, "")
    assert extrair_comando_com_ativacao("Lelei, aumenta o brilho") == (True, "aumenta o brilho")
    assert extrair_comando_com_ativacao("Lê, lê, desliga a luz") == (True, "desliga a luz")
    assert extrair_comando_com_ativacao("Le-lei, continua a música") == (True, "continua a música")
    assert extrair_comando_com_ativacao("Leilí, abre o navegador") == (True, "abre o navegador")


def test_modelo_acustico_pessoal_repara_comando_mal_transcrito():
    entregues = []
    ouvido = OuvidoWhisperRuntime(
        processar_texto=entregues.append,
        esta_falando=lambda: False,
        reconhecer_comando_pessoal=lambda *_: {
            "aceito": True,
            "comando": "deixa a luz vermelha",
            "distancia": 0.16,
            "margem": 0.06,
        },
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: ModeloFalso("Lelei, deixa a luz sem medo"),
        entrega_assincrona=False,
        log=lambda *_: None,
    )

    ouvido._entregar(np.ones(1600, dtype=np.float32))

    assert entregues == ["deixa a luz vermelha"]


def test_modelo_acustico_pessoal_rejeitado_nao_forca_conversa_em_comando():
    entregues = []
    ouvido = OuvidoWhisperRuntime(
        processar_texto=entregues.append,
        esta_falando=lambda: False,
        reconhecer_comando_pessoal=lambda *_: {
            "aceito": False,
            "comando": "deixa a luz azul",
            "distancia": 0.31,
            "margem": 0.002,
        },
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: ModeloFalso("Laylay, fala sobre a luz"),
        entrega_assincrona=False,
        log=lambda *_: None,
    )

    ouvido._entregar(np.ones(1600, dtype=np.float32))

    assert entregues == ["fala sobre a luz"]


def test_confianca_media_pede_confirmacao_e_sim_executa_original():
    class ModeloMedio(ModeloFalso):
        def transcribe(self, audio, **kwargs):
            return [SimpleNamespace(text=self.texto, avg_logprob=-0.7, no_speech_prob=0.02)], SimpleNamespace(language_probability=0.99)

    modelo = ModeloMedio("Lay, abre o fragpunk")
    entregues = []
    perguntas = []
    agora = [10.0]
    ouvido = OuvidoWhisperRuntime(
        processar_texto=entregues.append,
        esta_falando=lambda: False,
        solicitar_confirmacao=lambda fala, *_args: perguntas.append(fala),
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: modelo,
        entrega_assincrona=False,
        monotonic=lambda: agora[0],
        log=lambda *_: None,
    )
    audio = np.ones(1600, dtype=np.float32)
    ouvido._entregar(audio)
    assert entregues == []
    assert "abre o fragpunk" in perguntas[0].casefold()
    modelo.texto = "Lay, sim"
    agora[0] = 11.0
    ouvido._entregar(audio)
    assert entregues == ["abre o fragpunk"]


def test_repetir_comando_de_confianca_media_confirma_sem_criar_loop():
    class ModeloMedio(ModeloFalso):
        def transcribe(self, audio, **kwargs):
            return [
                SimpleNamespace(text=self.texto, avg_logprob=-0.7, no_speech_prob=0.02)
            ], SimpleNamespace(language_probability=0.99)

    modelo = ModeloMedio("Lay, liga a luz")
    entregues = []
    perguntas = []
    agora = [10.0]
    ouvido = OuvidoWhisperRuntime(
        processar_texto=entregues.append,
        esta_falando=lambda: False,
        solicitar_confirmacao=lambda fala, *_args: perguntas.append(fala),
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: modelo,
        entrega_assincrona=False,
        monotonic=lambda: agora[0],
        log=lambda *_: None,
    )
    audio = np.ones(1600, dtype=np.float32)

    ouvido._entregar(audio)
    agora[0] = 11.0
    ouvido._entregar(audio)

    assert len(perguntas) == 1
    assert entregues == ["liga a luz"]


def test_resultado_vazio_do_whisper_aparece_no_terminal():
    logs = []
    ouvido = OuvidoWhisperRuntime(
        processar_texto=lambda _: None,
        esta_falando=lambda: False,
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: ModeloFalso(""),
        entrega_assincrona=False,
        log=logs.append,
    )

    ouvido._entregar(np.ones(1600, dtype=np.float32))

    assert any("Whisper não formou texto" in mensagem for mensagem in logs)


def test_comando_sensivel_de_voz_exige_confirmacao_mesmo_com_confianca_alta():
    perguntas = []
    entregues = []
    ouvido = OuvidoWhisperRuntime(
        processar_texto=entregues.append,
        esta_falando=lambda: False,
        solicitar_confirmacao=lambda fala, *_args: perguntas.append(fala),
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: ModeloFalso("Lay, apaga a pasta testes"),
        entrega_assincrona=False,
        log=lambda *_: None,
    )
    ouvido._entregar(np.ones(1600, dtype=np.float32))
    assert entregues == []
    assert perguntas


def test_comando_de_voz_duplicado_em_janela_curta_e_descartado():
    entregues = []
    agora = [20.0]
    ouvido = OuvidoWhisperRuntime(
        processar_texto=entregues.append,
        esta_falando=lambda: False,
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: ModeloFalso("Lay, liga a luz"),
        entrega_assincrona=False,
        monotonic=lambda: agora[0],
        log=lambda *_: None,
    )
    audio = np.ones(1600, dtype=np.float32)
    ouvido._entregar(audio)
    agora[0] = 20.8
    ouvido._entregar(audio)
    assert entregues == ["liga a luz"]


def test_vocabulario_dinamico_entra_no_prompt_do_whisper():
    modelo = ModeloFalso("Lay, abre o FragPunk")
    ouvido = OuvidoWhisperRuntime(
        processar_texto=lambda _: None,
        esta_falando=lambda: False,
        vocabulario_dinamico=lambda: ["FragPunk", "música brasileira"],
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: modelo,
        entrega_assincrona=False,
        log=lambda *_: None,
    )
    ouvido.transcrever(np.ones(1600, dtype=np.float32))
    prompt = modelo.chamadas[0][1]["initial_prompt"]
    assert "FragPunk" in prompt
    assert "música brasileira" in prompt


def test_terminal_mostra_texto_original_entendido_pelo_whisper():
    logs = []
    ouvido = OuvidoWhisperRuntime(
        processar_texto=lambda _: None,
        esta_falando=lambda: False,
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: ModeloFalso("Lay, liga a luz"),
        entrega_assincrona=False,
        log=logs.append,
    )
    ouvido._entregar(np.ones(1600, dtype=np.float32))
    assert "🗣️ [VOCÊ DISSE] Lay, liga a luz" in logs


def test_ensino_de_pronuncia_e_interceptado_e_persistido():
    salvos = []
    falas = []
    ouvido = OuvidoWhisperRuntime(
        processar_texto=lambda _: None,
        esta_falando=lambda: False,
        salvar_pronuncia=lambda ouvido, correto: salvos.append((ouvido, correto)) or True,
        solicitar_confirmacao=lambda fala, *_args: falas.append(fala),
        sounddevice_mod=SoundDeviceFalso(),
        numpy_mod=np,
        model_factory=lambda *_args, **_kwargs: ModeloFalso(
            "Lay, quando eu falar freguipanque quero dizer FragPunk"
        ),
        entrega_assincrona=False,
        log=lambda *_: None,
    )
    ouvido._entregar(np.ones(1600, dtype=np.float32))
    assert salvos == [("freguipanque", "fragpunk")]
    assert falas
