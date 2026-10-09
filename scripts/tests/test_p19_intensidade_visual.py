"""Contrato de intensidade nos consumidores visuais, sem abrir janela externa.

Os métodos reais da janela recebem um canvas de captura. Isso prova consumo
local do retrato recebido; não prova pixels da janela instalada ou som físico.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

import pytest
from PIL import Image

from cliente.avatar_laylay import JanelaAvatar
from mente_laylay.integracao.gamebar_bridge import GameBarBridgeRuntime
from mente_laylay.personalidade.avatar_runtime import (
    calcular_deslocamento_avatar,
    normalizar_estado_avatar,
)


class _Canvas:
    def __init__(self) -> None:
        self.posicoes: dict[str, tuple[float, ...]] = {}
        self.configuracoes: dict[str, dict] = {}

    def coords(self, item: str, *posicao: float) -> None:
        self.posicoes[item] = posicao

    def itemconfigure(self, item: str, **campos) -> None:
        self.configuracoes.setdefault(item, {}).update(campos)


def _janela_recebendo_retrato(
    monkeypatch, *, emocao: str, nivel: int, falando: bool = True,
    atividade: str = "speaking", movimento: bool = True,
) -> JanelaAvatar:
    janela = JanelaAvatar.__new__(JanelaAvatar)
    janela.canvas = _Canvas()
    janela.root = SimpleNamespace(after=lambda *_: None)
    janela.tk = SimpleNamespace(TclError=RuntimeError)
    janela.movimento_sutil = SimpleNamespace(get=lambda: movimento)
    janela.tamanho = 230
    janela.emocao = "calma"
    janela.falando = False
    janela.atividade = "idle"
    janela.intensidade = 0.33
    janela._reacao_id = ""
    janela._inicio_reacao = 0.0
    janela._inicio_animacao = 0.0
    janela._emocao_pendente = ""
    janela._troca_emocao_agendada = None
    janela._mostrar_frame = lambda **_: None
    monkeypatch.setattr("cliente.avatar_laylay.time.monotonic", lambda: 0.0)
    retrato = normalizar_estado_avatar({
        "emotion": emocao, "level": nivel, "speaking": falando,
        "activity": atividade,
    })
    janela._aplicar_estado_visual(
        retrato["emotion"], retrato["speaking"], retrato["activity"],
        retrato["intensity"], retrato["reaction_id"],
    )
    return janela


def _movimentos(monkeypatch, janela: JanelaAvatar) -> list[tuple[float, ...]]:
    posicoes = []
    for indice in range(30):
        instante = indice / 30
        monkeypatch.setattr(
            "cliente.avatar_laylay.time.monotonic", lambda t=instante: t,
        )
        janela._animar_movimento()
        posicoes.append(janela.canvas.posicoes[janela.item_imagem])
    return posicoes


def _atribuir_itens(janela: JanelaAvatar) -> JanelaAvatar:
    janela.item_imagem = "imagem"
    janela.item_aura = "aura"
    janela.item_estado = "estado"
    return janela


def test_avatar_recebe_intensidade_sem_escolher_outra_emocao(monkeypatch) -> None:
    leve = _janela_recebendo_retrato(monkeypatch, emocao="irritada", nivel=1)
    forte = _janela_recebendo_retrato(monkeypatch, emocao="brava", nivel=3)

    assert leve.emocao == forte.emocao == "brava"
    assert leve.intensidade == pytest.approx(0.333)
    assert forte.intensidade == 1.0
    assert leve.falando and forte.falando


def test_troca_visual_parada_conserva_emocao_e_intensidade_do_mesmo_retrato(
    monkeypatch,
) -> None:
    janela = _janela_recebendo_retrato(monkeypatch, emocao="irritada", nivel=1)
    janela._aplicar_estado_visual("feliz", False, "idle", 1.0)

    assert janela.emocao == "brava"
    assert janela.intensidade == pytest.approx(0.333), (
        "imagem antiga recebeu a intensidade do retrato ainda pendente"
    )
    janela._confirmar_emocao_pendente()
    assert janela.emocao == "feliz"
    assert janela.intensidade == 1.0


def test_intensidade_do_retrato_deve_chegar_ao_movimento_nativo(monkeypatch) -> None:
    leve = _atribuir_itens(_janela_recebendo_retrato(
        monkeypatch, emocao="irritada", nivel=1,
    ))
    forte = _atribuir_itens(_janela_recebendo_retrato(
        monkeypatch, emocao="brava", nivel=3,
    ))

    assert _movimentos(monkeypatch, leve) != _movimentos(monkeypatch, forte), (
        "o avatar recebeu intensidades distintas mas desenhou o mesmo movimento"
    )


@pytest.mark.parametrize("falando", [False, True])
def test_helper_default_preserva_movimento_e_intensidade_nao_amplifica(falando) -> None:
    padrao = [calcular_deslocamento_avatar(i / 30, falando=falando) for i in range(120)]
    explicito = [
        calcular_deslocamento_avatar(i / 30, falando=falando, intensidade=1.0)
        for i in range(120)
    ]
    excedente = [
        calcular_deslocamento_avatar(i / 30, falando=falando, intensidade=9.0)
        for i in range(120)
    ]

    assert padrao == explicito == excedente
    assert max(map(abs, padrao)) <= 2


@pytest.mark.parametrize("intensidade", [0, -1, "invalida", None, float("nan"), float("inf")])
def test_helper_intensidade_ausente_ou_invalida_nao_produz_movimento(intensidade) -> None:
    assert all(
        calcular_deslocamento_avatar(i / 30, falando=True, intensidade=intensidade) == 0
        for i in range(120)
    )


@pytest.mark.parametrize("atividade", ["idle", "listening", "thinking", "executing", "success", "error"])
def test_movimentos_operacionais_continuam_contidos(monkeypatch, atividade) -> None:
    janela = _atribuir_itens(_janela_recebendo_retrato(
        monkeypatch, emocao="brava", nivel=3, falando=False, atividade=atividade,
    ))
    posicoes = _movimentos(monkeypatch, janela)

    assert all(abs(x - 115) <= 5 and abs(y - 115) <= 10 for x, y in posicoes)


@pytest.mark.parametrize("intensidade", ["invalida", None, float("nan"), float("inf")])
def test_avatar_nativo_nao_amplifica_intensidade_malformada(monkeypatch, intensidade) -> None:
    janela = _janela_recebendo_retrato(monkeypatch, emocao="irritada", nivel=1)
    janela._aplicar_estado_visual("brava", True, "speaking", intensidade)

    assert janela.emocao == "brava"
    assert janela.intensidade == 0.0


def test_desativar_movimento_tambem_deve_imobilizar_aura_nativa(monkeypatch) -> None:
    janela = _atribuir_itens(_janela_recebendo_retrato(
        monkeypatch, emocao="brava", nivel=3, falando=False,
        atividade="listening", movimento=False,
    ))
    janela._atualizar_indicador_atividade(0.0)
    antes = (
        janela.canvas.posicoes["aura"],
        dict(janela.canvas.configuracoes["aura"]),
    )
    janela._atualizar_indicador_atividade(0.31)
    depois = (
        janela.canvas.posicoes["aura"],
        dict(janela.canvas.configuracoes["aura"]),
    )

    assert antes == depois, "movimento desativado ainda deixa a aura pulsar"
    assert janela.canvas.configuracoes["estado"]["fill"]


def test_intensidade_conserva_pista_estatica_quando_movimento_esta_desativado(
    monkeypatch, tmp_path,
) -> None:
    caminho = tmp_path / "brava.png"
    Image.new("RGBA", (512, 512), (80, 30, 45, 255)).save(caminho)
    leve = _atribuir_itens(_janela_recebendo_retrato(
        monkeypatch, emocao="irritada", nivel=1, movimento=False,
    ))
    forte = _atribuir_itens(_janela_recebendo_retrato(
        monkeypatch, emocao="brava", nivel=3, movimento=False,
    ))
    for janela in (leve, forte):
        janela.assets = {"brava": caminho, "brava_falando": caminho}
        janela.Image = Image
        janela.ImageTk = SimpleNamespace(
            PhotoImage=lambda imagem: SimpleNamespace(tamanho=imagem.size),
        )
        janela._imagens_tk = {}
        janela._frame_atual = ""
        del janela._mostrar_frame
        janela._mostrar_frame()

    assert leve._arquivo_frame() == forte._arquivo_frame() == caminho
    assert leve.canvas.configuracoes["imagem"]["image"].tamanho != (
        forte.canvas.configuracoes["imagem"]["image"].tamanho
    ), "desativar movimento apagou toda distinção visual de intensidade"


def test_gamebar_transporta_intensidade_do_mesmo_retrato_sem_mudar_causa() -> None:
    fonte = {"emotion": "irritada", "level": 1, "speaking": True}
    runtime = GameBarBridgeRuntime(estado_getter=lambda: fonte)
    leve = runtime.estado_atual()
    fonte.update(emotion="brava", level=3)
    forte = runtime.estado_atual()

    assert leve["emotion"] == forte["emotion"] == "brava"
    assert leve["intensity"] == pytest.approx(0.333)
    assert forte["intensity"] == 1.0
    assert fonte == {"emotion": "brava", "level": 3, "speaking": True}


@pytest.fixture(scope="module")
def quadros_gamebar(tmp_path_factory):
    """Executa o corpo C# real com relógio fixo e elementos UWP de captura.

    O build UWP continua uma validação separada. Esta prova local não abre o
    widget e não substitui aferição dos pixels na Game Bar instalada.
    """
    powershell = shutil.which("powershell")
    if not powershell:
        pytest.skip("PowerShell com compilador C# indisponível")
    raiz = Path(__file__).resolve().parents[2]
    fonte = (raiz / "cliente/gamebar_laylay/LaylayWidget.xaml.cs").read_text(
        encoding="utf-8",
    )
    inicio = fonte.index("private void Animate(")
    abre = fonte.index("{", inicio)
    profundidade = 1
    fim = abre + 1
    while profundidade:
        profundidade += (fonte[fim] == "{") - (fonte[fim] == "}")
        fim += 1
    metodo = fonte[inicio:fim].replace("DateTimeOffset.Now", "_agora")
    codigo = """
using System;
public sealed class Valor {
    public double X, Y, ScaleX, ScaleY, Opacity;
}
public sealed class Preferencias {
    public double MotionIntensity = 1.0, AvatarOpacity = 1.0;
    public bool SmoothTransitions = true, SpeakingMotion = true;
    public bool IdleMotion = true, ReactiveMotion = true, ActivityIndicator = true;
}
public sealed class ConsumoGameBar {
    private DateTimeOffset _agora = new DateTimeOffset(2026, 10, 6, 12, 0, 0, TimeSpan.Zero);
    private DateTimeOffset _animationStarted, _imageChangedAt, _reactionStarted;
    private int _animationFrame;
    private bool _speaking;
    private string _activity;
    private double _intensity;
    private Preferencias _preferences = new Preferencias();
    private Valor AvatarImage = new Valor(), AvatarMove = new Valor();
    private Valor AvatarScale = new Valor(), ActivityAura = new Valor(), ActivityDot = new Valor();
    private void ApplyPreferences() {}
    public static double[] Quadro(double strength, double seconds, double motion, bool speaking, bool semMovimento = false) {
        var alvo = new ConsumoGameBar();
        alvo._animationStarted = alvo._agora.AddSeconds(-seconds);
        alvo._imageChangedAt = alvo._agora.AddSeconds(-seconds);
        alvo._reactionStarted = alvo._agora.AddSeconds(-seconds);
        alvo._intensity = strength;
        alvo._preferences.MotionIntensity = motion;
        if (semMovimento) {
            alvo._preferences.IdleMotion = false;
            alvo._preferences.SpeakingMotion = false;
            alvo._preferences.ReactiveMotion = false;
        }
        alvo._speaking = speaking;
        alvo._activity = speaking ? "speaking" : "listening";
        alvo.Animate(null, null);
        return new[] { alvo.AvatarMove.X, alvo.AvatarMove.Y, alvo.AvatarScale.ScaleX,
            alvo.AvatarScale.ScaleY, alvo.ActivityAura.Opacity, alvo.AvatarImage.Opacity };
    }
METODO
}
""".replace("METODO", metodo)
    caminho = tmp_path_factory.mktemp("p19_csharp") / "quadros.ps1"
    caminho.write_text(
        "$ErrorActionPreference = 'Stop'\nAdd-Type -TypeDefinition @'\n"
        + codigo + "\n'@\n"
        + "@{ leve = [ConsumoGameBar]::Quadro(0.333, 0.11, 1.0, $true); "
        + "forte = [ConsumoGameBar]::Quadro(1.0, 0.11, 1.0, $true); "
        + "estatico_leve = [ConsumoGameBar]::Quadro(0.333, 0.11, 0.0, $true); "
        + "estatico_forte = [ConsumoGameBar]::Quadro(1.0, 0.11, 0.0, $true); "
        + "sem_movimento_a = [ConsumoGameBar]::Quadro(1.0, 0.01, 0.0, $false); "
        + "sem_movimento_b = [ConsumoGameBar]::Quadro(1.0, 0.14, 0.0, $false); "
        + "preferencias_off_a = [ConsumoGameBar]::Quadro(1.0, 0.01, 1.0, $false, $true); "
        + "preferencias_off_b = [ConsumoGameBar]::Quadro(1.0, 0.14, 1.0, $false, $true); "
        + "movimento_maximo = [ConsumoGameBar]::Quadro(1.0, 0.11, 2.0, $true) "
        + "} | ConvertTo-Json -Compress\n",
        encoding="utf-8-sig",
    )
    resultado = subprocess.run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(caminho)],
        capture_output=True, text=True, timeout=30,
    )
    assert resultado.returncode == 0, resultado.stderr
    return json.loads(resultado.stdout)


def test_gamebar_consumidor_usa_intensidade_na_fala(quadros_gamebar) -> None:
    assert quadros_gamebar["leve"][:4] != quadros_gamebar["forte"][:4], (
        "widget recebeu intensidades distintas mas moveu/escalou a mesma fala"
    )


def test_gamebar_conserva_intensidade_estatica_sem_movimento(quadros_gamebar) -> None:
    assert quadros_gamebar["estatico_leve"][2:4] != (
        quadros_gamebar["estatico_forte"][2:4]
    ), "movimento zero apagou a distinção de intensidade da expressão"


def test_gamebar_movimento_zero_imobiliza_aura_e_transicao(quadros_gamebar) -> None:
    assert quadros_gamebar["sem_movimento_a"] == quadros_gamebar["sem_movimento_b"], (
        "movimento zero ainda muda aura ou opacidade de transição"
    )


def test_gamebar_preferencias_sem_movimento_imobilizam_aura_e_transicao(quadros_gamebar) -> None:
    assert quadros_gamebar["preferencias_off_a"] == quadros_gamebar["preferencias_off_b"]
    assert quadros_gamebar["preferencias_off_a"][:2] == [0, 0]


def test_gamebar_preferencia_maxima_mantem_fala_contida(quadros_gamebar) -> None:
    x, y, escala_x, escala_y = quadros_gamebar["movimento_maximo"][:4]
    assert abs(x) <= 5 and abs(y) <= 10
    assert 0.9 <= escala_x <= 1.06
    assert 0.9 <= escala_y <= 1.06
