from pathlib import Path
import threading
import time

from cliente.avatar_laylay import FPS_ANIMACAO, INTERVALO_ANIMACAO_MS
from mente_laylay.personalidade.avatar_runtime import (
    AvatarRuntime,
    calcular_deslocamento_avatar,
    descobrir_assets_avatar,
    normalizar_emocao_avatar,
    normalizar_estado_avatar,
    normalizar_atividade_avatar,
    normalizar_nome_asset,
    processo_pai_esta_ativo,
    resolver_asset_avatar,
    verificar_quadros_avatar,
)
from mente_laylay.personalidade.voz_runtime import VozRuntime


def test_normaliza_nome_de_asset_com_acentos_e_separadores():
    assert normalizar_nome_asset("Laylay_Envergonháda Falando") == "laylay_envergonhada_falando"


def test_movimento_visual_e_sutil_e_pode_ser_desativado():
    repouso = [calcular_deslocamento_avatar(i / 10, falando=False) for i in range(50)]
    fala = [calcular_deslocamento_avatar(i / 20, falando=True) for i in range(50)]

    assert min(repouso) >= -2 and max(repouso) <= 2
    assert min(fala) >= -2 and max(fala) <= 2
    assert len(set(repouso)) > 1
    assert len(set(fala)) > 1
    assert calcular_deslocamento_avatar(1.25, falando=True, movimento_ativo=False) == 0


def test_avatar_anima_em_trinta_frames_por_segundo():
    assert FPS_ANIMACAO == 30
    assert INTERVALO_ANIMACAO_MS == 33


def test_supervisor_reconhece_processo_pai_e_pid_reutilizado():
    class Processo:
        def is_running(self):
            return True

        def status(self):
            return "running"

        def create_time(self):
            return 1234.5

    class Psutil:
        STATUS_ZOMBIE = "zombie"

        @staticmethod
        def pid_exists(pid):
            return pid == 77

        @staticmethod
        def Process(_pid):
            return Processo()

    assert processo_pai_esta_ativo(77, 1234.5, psutil_mod=Psutil)
    assert not processo_pai_esta_ativo(77, 999.0, psutil_mod=Psutil)
    assert not processo_pai_esta_ativo(88, 1234.5, psutil_mod=Psutil)


def test_descobre_neutra_falando_e_emocao_futura(tmp_path: Path):
    neutra = tmp_path / "laylay_neutra_512_transparente.png"
    falando = tmp_path / "laylay_falando_512_transparente.png"
    feliz = tmp_path / "laylay_feliz.png"
    for arquivo in (neutra, falando, feliz):
        arquivo.touch()

    assets = descobrir_assets_avatar(tmp_path)

    assert assets["neutra"] == neutra.resolve()
    assert assets["falando"] == falando.resolve()
    assert assets["feliz"] == feliz.resolve()


def test_catalogo_reconhece_os_nomes_completos_dos_novos_pngs(tmp_path: Path):
    nomes = (
        "laylay_animada_512_transparente_real.png",
        "laylay_brava_512_transparente_real.png",
        "laylay_calma_512_transparente_real_corrigida.png",
        "laylay_envergonhada_512_transparente.png",
        "laylay_feliz_boca_fechada_512_RGBA.png",
        "laylay_surpresa_512_transparente_real.png",
        "laylay_triste_512_transparente_real.png",
        "laylay_neutra_512_transparente.png",
        "laylay_falando_512_transparente.png",
    )
    for nome in nomes:
        (tmp_path / nome).touch()

    assets = descobrir_assets_avatar(tmp_path)

    for emocao in ("animada", "brava", "calma", "envergonhada", "feliz", "surpresa", "triste"):
        assert emocao in assets
    assert {"neutra", "falando"} <= set(assets)


def test_catalogo_reconhece_cada_emocao_falando_em_sua_pasta(tmp_path: Path):
    esperados = {}
    for emocao in ("animada", "brava", "calma", "envergonhada", "feliz", "surpresa", "triste"):
        pasta_emocao = tmp_path / emocao
        pasta_emocao.mkdir()
        parada = pasta_emocao / f"laylay_{emocao}_512_transparente.png"
        falando = pasta_emocao / f"laylay_{emocao}_falando_512_transparente.png"
        parada.touch()
        falando.touch()
        esperados[emocao] = (parada.resolve(), falando.resolve())

    assets = descobrir_assets_avatar(tmp_path)

    for emocao, (parada, falando) in esperados.items():
        assert assets[emocao] == parada
        assert assets[f"{emocao}_falando"] == falando
        assert resolver_asset_avatar(assets, emocao) == parada
        assert resolver_asset_avatar(assets, emocao, falando=True) == falando
    assert "falando" not in assets
    assert verificar_quadros_avatar(assets) == (True, True)


def test_boca_emocional_nao_vira_fallback_generico_de_outra_emocao(tmp_path: Path):
    pasta_brava = tmp_path / "brava"
    pasta_calma = tmp_path / "calma"
    pasta_brava.mkdir()
    pasta_calma.mkdir()
    brava_falando = pasta_brava / "laylay_brava_falando.png"
    calma = pasta_calma / "laylay_calma.png"
    brava_falando.touch()
    calma.touch()

    assets = descobrir_assets_avatar(tmp_path)

    assert "falando" not in assets
    assert resolver_asset_avatar(assets, "calma", falando=True) == assets["calma"]
    assert resolver_asset_avatar(assets, "brava", falando=True) == brava_falando.resolve()


def test_sinonimos_da_mente_usam_a_expressao_visual_correta():
    assert normalizar_emocao_avatar("irritada") == "brava"
    assert normalizar_emocao_avatar("nervosa") == "brava"
    assert normalizar_emocao_avatar("alegre") == "feliz"
    assert normalizar_emocao_avatar("debochada") == "animada"
    assert normalizar_emocao_avatar("tímida") == "envergonhada"
    assert normalizar_emocao_avatar("decepcionada") == "triste"
    assert normalizar_emocao_avatar("curiosa") == "surpresa"
    assert normalizar_emocao_avatar("focada") == "calma"


def test_resolucao_prioriza_emocao_parada_e_fala_especifica_ou_generica(tmp_path: Path):
    assets = {
        "neutra": tmp_path / "neutra.png",
        "calma": tmp_path / "calma.png",
        "brava": tmp_path / "brava.png",
        "falando": tmp_path / "falando.png",
        "brava_falando": tmp_path / "brava_falando.png",
    }

    assert resolver_asset_avatar(assets, "irritada") == assets["brava"]
    assert resolver_asset_avatar(assets, "irritada", falando=True) == assets["brava_falando"]
    assert resolver_asset_avatar(assets, "feliz", falando=True) == assets["falando"]
    assert resolver_asset_avatar(assets, "emoção futura") == assets["calma"]


def test_normaliza_estado_visual_sem_vazar_objetos_internos():
    estado = normalizar_estado_avatar({"emocao": "Animáda", "nivel": "9", "falando": 1})

    assert estado == {
        "type": "state",
        "emotion": "animada",
        "level": 3,
        "speaking": True,
        "activity": "speaking",
        "intensity": 1.0,
        "reaction_id": "",
    }

    irritada = normalizar_estado_avatar({"emotion": "irritada", "level": 2})
    assert irritada["emotion"] == "brava"


def test_normaliza_atividade_visual_e_mantem_compatibilidade():
    assert normalizar_atividade_avatar("ouvindo") == "listening"
    assert normalizar_atividade_avatar("pensando") == "thinking"
    assert normalizar_atividade_avatar("executando") == "executing"
    assert normalizar_atividade_avatar("concluído") == "success"
    assert normalizar_atividade_avatar("falha") == "error"
    assert normalizar_atividade_avatar("estado desconhecido") == "idle"

    estado = normalizar_estado_avatar({
        "emotion": "feliz",
        "activity": "sucesso",
        "intensity": 9,
        "reaction_id": "turno-42",
    })
    assert estado["activity"] == "success"
    assert estado["intensity"] == 1.0
    assert estado["reaction_id"] == "turno-42"


def test_avatar_desativado_nao_abre_processo(tmp_path: Path):
    chamadas = []
    runtime = AvatarRuntime(
        raiz_projeto=tmp_path,
        estado_getter=lambda: {},
        env_getter=lambda nome, padrao="": "0" if nome == "LAYLAY_AVATAR_ATIVO" else padrao,
        popen=lambda *args, **kwargs: chamadas.append((args, kwargs)),
        log=lambda _texto: None,
    )

    assert runtime.iniciar() is False
    assert chamadas == []


def test_assets_ausentes_nao_impedem_a_assistente(tmp_path: Path):
    logs = []
    runtime = AvatarRuntime(
        raiz_projeto=tmp_path,
        estado_getter=lambda: {},
        popen=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("não deveria abrir")),
        log=logs.append,
    )

    assert runtime.iniciar() is False
    assert any("recurso ausente" in mensagem for mensagem in logs)


def test_avatar_encaminha_falha_de_abertura_sem_parar_a_assistente(tmp_path: Path):
    pasta_avatar = tmp_path / "avatar" / "calma"
    pasta_avatar.mkdir(parents=True)
    (pasta_avatar / "laylay_calma.png").touch()
    (pasta_avatar / "laylay_calma_falando.png").touch()
    pasta_cliente = tmp_path / "cliente"
    pasta_cliente.mkdir()
    (pasta_cliente / "avatar_laylay.py").touch()
    falhas = []
    runtime = AvatarRuntime(
        raiz_projeto=tmp_path,
        estado_getter=lambda: {},
        popen=lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("sem processo")),
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
        log=lambda _texto: None,
    )

    assert runtime.iniciar() is False
    assert falhas[0][0] == ("avatar", "abertura_janela")
    assert isinstance(falhas[0][1]["erro"], OSError)


def test_widget_fixado_impede_avatar_python_e_fallback_volta(tmp_path: Path):
    pasta_avatar = tmp_path / "avatar" / "calma"
    pasta_avatar.mkdir(parents=True)
    (pasta_avatar / "laylay_calma.png").write_bytes(b"")
    (pasta_avatar / "laylay_calma_falando.png").write_bytes(b"")
    pasta_cliente = tmp_path / "cliente"
    pasta_cliente.mkdir()
    (pasta_cliente / "avatar_laylay.py").write_text("", encoding="utf-8")
    externo = [True]
    processos = []

    class Processo:
        def __init__(self):
            self.encerrado = False

        def poll(self):
            return 0 if self.encerrado else None

        def wait(self, timeout=None):
            self.encerrado = True
            return 0

        def terminate(self):
            self.encerrado = True

    def abrir(*_args, **_kwargs):
        processo = Processo()
        processos.append(processo)
        return processo

    runtime = AvatarRuntime(
        raiz_projeto=tmp_path,
        estado_getter=lambda: {},
        visual_externo_disponivel=lambda: externo[0],
        popen=abrir,
        intervalo=0.05,
        log=lambda _texto: None,
    )

    assert runtime.iniciar() is True
    assert processos == []
    externo[0] = False
    for _ in range(20):
        if processos:
            break
        time.sleep(0.03)
    try:
        assert len(processos) == 1
    finally:
        runtime.parar()


def test_avatar_comeca_a_falar_somente_depois_do_play():
    eventos = []

    class Edge:
        class Communicate:
            def __init__(self, *_args, **_kwargs):
                pass

            async def save(self, _caminho):
                eventos.append("sintese_concluida")

    class SoundFile:
        @staticmethod
        def read(_caminho):
            eventos.append("audio_lido")
            return [], 16000

    class Stream:
        active = False

    class SoundDevice:
        class default:
            device = (0, 0)

        @staticmethod
        def query_devices():
            return [{"name": "Saída de teste", "max_output_channels": 2}]

        @staticmethod
        def play(*_args, **_kwargs):
            eventos.append("play")

        @staticmethod
        def get_stream():
            return Stream()

    runtime = VozRuntime(
        fallback_fala="fallback",
        voice="voz",
        edge_tts_mod=Edge,
        sounddevice_mod=SoundDevice,
        soundfile_mod=SoundFile,
        pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("", "", ""),
        compor_fala_proativa_cb=lambda _itens: ("", "calma", 1),
        ajustar_estado_fala_cb=lambda chave, valor: eventos.append((chave, valor)),
        interrupt_event=threading.Event(),
        log=lambda _mensagem: None,
    )

    runtime.reproduzir_fala("Olá", "calma", 1)

    indice_play = eventos.index("play")
    indice_avatar = eventos.index(("audio_playing", True))
    assert indice_avatar > indice_play
    assert ("audio_playing", True) not in eventos[:indice_play]
    assert eventos[-2:] == [("audio_playing", False), ("is_speaking", False)]
