from __future__ import annotations

import re
import shutil
from pathlib import Path


QSS_MUSICA = r'''
                /* =========================================
                   HOME — CARD MÚSICA
                   ========================================= */

                #dashboardCard[railCard="music"] {{
                    background: #14191E;
                    border: 1px solid #2B3239;
                    border-radius: 14px;
                }}

                #dashboardCard[railCard="music"][musicState="playing"] {{
                    border-color: #5A3039;
                }}

                #dashboardCard[railCard="music"][musicState="stale"] {{
                    border-color: #54442D;
                }}

                #dashboardCard[railCard="music"][musicState="unavailable"] {{
                    border-color: #252B31;
                }}

                #dashboardCard[railCard="music"] #dashboardCardTitle {{
                    color: #F3EFF1;
                    font-size: 13px;
                    font-weight: 700;
                }}

                #railMusicBadge {{
                    background: #20262C;
                    border: 1px solid #323940;
                    border-radius: 7px;
                    padding: 3px 6px;
                    color: #858D96;
                    font-size: 8px;
                    font-weight: 700;
                }}

                #railMusicBadge[state="playing"] {{
                    background: #2A1A20;
                    border-color: #5B303B;
                    color: #FF6D82;
                }}

                #railMusicBadge[state="paused"] {{
                    background: #1B2025;
                    border-color: #333A42;
                    color: #A9B0B7;
                }}

                #railMusicBadge[state="ended"] {{
                    background: #1B2025;
                    border-color: #333A42;
                    color: #8C949C;
                }}

                #railMusicBadge[state="stale"] {{
                    background: #272116;
                    border-color: #5A4827;
                    color: #D3AA61;
                }}

                #railMusicBadge[state="unavailable"] {{
                    background: #181C20;
                    border-color: #282E34;
                    color: #646C74;
                }}

                #railMusicTitle {{
                    background: transparent;
                    border: 0;
                    color: #F1EDEF;
                    font-size: 11px;
                    font-weight: 700;
                }}

                #railMusicMeta {{
                    background: transparent;
                    border: 0;
                    color: #777F88;
                    font-size: 8px;
                }}

                #railMusicProgress {{
                    background: #242A30;
                    border: 0;
                    border-radius: 2px;
                    min-height: 4px;
                    max-height: 4px;
                }}

                #railMusicProgress::chunk {{
                    background: #D24A60;
                    border-radius: 2px;
                }}

                #railMusicTime {{
                    background: transparent;
                    border: 0;
                    color: #6F7780;
                    font-size: 8px;
                }}

                #dashboardCard[railCard="music"] #railMusicControl {{
                    background: #191E23;
                    border: 1px solid #30363D;
                    border-radius: 17px;
                    min-width: 34px;
                    max-width: 34px;
                    min-height: 34px;
                    max-height: 34px;
                }}

                #dashboardCard[railCard="music"] #railMusicControl:hover {{
                    background: #251C21;
                    border-color: #69404A;
                }}

                #dashboardCard[railCard="music"] #railMusicControl:pressed {{
                    background: #301D24;
                    border-color: #8D4250;
                }}

                #dashboardCard[railCard="music"] #railMusicControl:disabled {{
                    background: #171B1F;
                    border-color: #252B31;
                }}

                #dashboardCard[railCard="music"]
                #railMusicControl[primary="true"] {{
                    background: #B9384D;
                    border: 1px solid #EC5A70;
                    border-radius: 20px;
                    min-width: 40px;
                    max-width: 40px;
                    min-height: 40px;
                    max-height: 40px;
                }}

                #dashboardCard[railCard="music"]
                #railMusicControl[primary="true"]:hover {{
                    background: #D3455B;
                    border-color: #FF7488;
                }}

                #dashboardCard[railCard="music"]
                #railMusicControl[primary="true"]:disabled {{
                    background: #221C20;
                    border-color: #3C3035;
                }}

'''


NOVO_CARD_MUSICA = r'''        musica = CartaoDashboard(
            "Música"
        )
        musica.setProperty(
            "railCard",
            "music",
        )
        musica.setProperty(
            "musicState",
            "unavailable",
        )
        musica.layout_principal.setContentsMargins(
            14, 13, 14, 12
        )
        musica.layout_principal.setSpacing(8)
        self.musica_card = musica

        musica_topo = QHBoxLayout()
        musica_topo.setSpacing(10)

        self.musica_capa = CapaMusicaGenerica(
            64
        )

        musica_textos = QVBoxLayout()
        musica_textos.setSpacing(3)

        badge_linha = QHBoxLayout()
        badge_linha.setContentsMargins(
            0, 0, 0, 0
        )

        self.musica_estado_badge = QLabel(
            "OFFLINE"
        )
        self.musica_estado_badge.setObjectName(
            "railMusicBadge"
        )
        self.musica_estado_badge.setProperty(
            "state",
            "unavailable",
        )

        badge_linha.addWidget(
            self.musica_estado_badge,
            0,
            Qt.AlignLeft,
        )
        badge_linha.addStretch()

        self.musica_titulo = QLabel(
            "Nenhuma faixa confirmada"
        )
        self.musica_titulo.setObjectName(
            "railMusicTitle"
        )
        self.musica_titulo.setWordWrap(
            True
        )

        self.musica_detalhe = QLabel(
            "Player ainda não observado."
        )
        self.musica_detalhe.setObjectName(
            "railMusicMeta"
        )
        self.musica_detalhe.setWordWrap(
            True
        )

        musica_textos.addLayout(
            badge_linha
        )
        musica_textos.addWidget(
            self.musica_titulo
        )
        musica_textos.addWidget(
            self.musica_detalhe
        )
        musica_textos.addStretch()

        musica_topo.addWidget(
            self.musica_capa
        )
        musica_topo.addLayout(
            musica_textos,
            1,
        )

        self.musica_progresso = QProgressBar()
        self.musica_progresso.setObjectName(
            "railMusicProgress"
        )
        self.musica_progresso.setRange(
            0, 1000
        )
        self.musica_progresso.setValue(0)
        self.musica_progresso.setTextVisible(
            False
        )

        tempos = QHBoxLayout()
        tempos.setContentsMargins(
            1, 0, 1, 0
        )

        self.musica_posicao = QLabel("0:00")
        self.musica_duracao = QLabel("0:00")

        for tempo in (
            self.musica_posicao,
            self.musica_duracao,
        ):
            tempo.setObjectName(
                "railMusicTime"
            )

        tempos.addWidget(
            self.musica_posicao
        )
        tempos.addStretch()
        tempos.addWidget(
            self.musica_duracao
        )

        controles = QHBoxLayout()
        controles.setSpacing(8)
        controles.addStretch()

        self.musica_botoes: dict[
            str,
            QPushButton,
        ] = {}

        for (
            acao_id,
            icone,
            dica,
        ) in (
            (
                "media_previous",
                "previous",
                "Faixa anterior",
            ),
            (
                "media_toggle",
                "play",
                "Pausar ou continuar",
            ),
            (
                "media_next",
                "next",
                "Próxima faixa",
            ),
        ):
            botao = QPushButton()
            botao.setObjectName(
                "railMusicControl"
            )
            botao.setProperty(
                "primary",
                acao_id == "media_toggle",
            )
            botao.setIcon(
                icone_terminal(icone)
            )
            botao.setIconSize(
                QSize(
                    20, 20
                )
            )
            botao.setToolTip(dica)
            botao.setAccessibleName(
                dica
            )
            botao.setEnabled(False)
            botao.clicked.connect(
                lambda _v=False,
                aid=acao_id:
                self._solicitar_musica(
                    aid
                )
            )

            self.musica_botoes[
                acao_id
            ] = botao

            controles.addWidget(
                botao
            )

        controles.addStretch()

        musica.layout_principal.addLayout(
            musica_topo
        )
        musica.layout_principal.addWidget(
            self.musica_progresso
        )
        musica.layout_principal.addLayout(
            tempos
        )
        musica.layout_principal.addLayout(
            controles
        )

        layout.addWidget(musica)'''


HELPER_VISUAL = r'''    def _definir_visual_musica(
        self,
        estado: str,
        frescor: str = "fresh",
    ) -> None:
        estado = str(
            estado or "unavailable"
        )
        frescor = str(
            frescor or "unavailable"
        )

        if (
            estado == "unavailable"
            or frescor == "unavailable"
        ):
            visual = "unavailable"
            texto = "OFFLINE"

        elif frescor == "stale":
            visual = "stale"
            texto = "ANTIGO"

        else:
            visual = (
                estado
                if estado in {
                    "playing",
                    "paused",
                    "ended",
                }
                else "unknown"
            )

            texto = {
                "playing": "TOCANDO",
                "paused": "PAUSADA",
                "ended": "FINALIZADA",
                "unknown": "PLAYER",
            }.get(
                visual,
                "PLAYER",
            )

        self.musica_card.setProperty(
            "musicState",
            visual,
        )
        self.musica_estado_badge.setProperty(
            "state",
            visual,
        )
        self.musica_estado_badge.setText(
            texto
        )

        for widget in (
            self.musica_card,
            self.musica_estado_badge,
        ):
            widget.style().unpolish(
                widget
            )
            widget.style().polish(
                widget
            )

'''


NOVO_APLICAR_MUSICA = r'''        musica = dashboard.get(
            "music"
        )

        if (
            not isinstance(
                musica,
                dict,
            )
            or musica.get(
                "freshness"
            ) == "unavailable"
        ):
            self._estado_musica = (
                "unavailable"
            )
            self._controles_musica = False

            self.musica_titulo.setText(
                "Nenhuma faixa confirmada"
            )
            self.musica_detalhe.setText(
                "Player indisponível ou "
                "ainda não observado."
            )

            self.musica_capa.definir_titulo(
                ""
            )
            self.musica_capa.carregar(
                ""
            )

            self.musica_progresso.setValue(
                0
            )
            self.musica_posicao.setText(
                "0:00"
            )
            self.musica_duracao.setText(
                "0:00"
            )

            self._musica_posicao_base = 0.0
            self._musica_duracao_base = 0.0
            self._musica_observada_em = 0.0

            self._definir_visual_musica(
                "unavailable",
                "unavailable",
            )

        else:
            self._estado_musica = str(
                musica.get("state")
                or "unknown"
            )

            self._controles_musica = bool(
                musica.get(
                    "controls_available"
                )
            )

            titulo_musica = str(
                musica.get("title")
                or "Faixa sem título"
            )

            self.musica_titulo.setText(
                titulo_musica
            )

            self.musica_capa.definir_titulo(
                titulo_musica
            )
            self.musica_capa.carregar(
                str(
                    musica.get(
                        "artwork_url"
                    )
                    or ""
                )
            )

            estado = {
                "playing": "Tocando",
                "paused": "Pausada",
                "ended": "Finalizada",
                "unknown": (
                    "Estado não confirmado"
                ),
            }.get(
                self._estado_musica,
                "Estado não confirmado",
            )

            canal = str(
                musica.get("channel")
                or ""
            ).strip()

            antigo = (
                " · dados antigos"
                if musica.get(
                    "freshness"
                ) == "stale"
                else ""
            )

            self.musica_detalhe.setText(
                estado
                + (
                    f" · {canal}"
                    if canal
                    else ""
                )
                + antigo
            )

            posicao = float(
                musica.get(
                    "position_seconds"
                )
                or 0.0
            )
            duracao = float(
                musica.get(
                    "duration_seconds"
                )
                or 0.0
            )

            self._musica_posicao_base = (
                posicao
            )
            self._musica_duracao_base = (
                duracao
            )
            self._musica_observada_em = float(
                musica.get(
                    "observed_at"
                )
                or 0.0
            )

            self.musica_progresso.setValue(
                max(
                    0,
                    min(
                        1000,
                        int(
                            (
                                posicao
                                / duracao
                            )
                            * 1000
                        ),
                    ),
                )
                if duracao > 0
                else 0
            )

            self.musica_posicao.setText(
                _tempo_player(
                    posicao
                )
            )
            self.musica_duracao.setText(
                _tempo_player(
                    duracao
                )
            )

            self.musica_botoes[
                "media_toggle"
            ].setIcon(
                icone_terminal(
                    "pause"
                    if (
                        self._estado_musica
                        == "playing"
                    )
                    else "play"
                )
            )

            self._definir_visual_musica(
                self._estado_musica,
                str(
                    musica.get(
                        "freshness"
                    )
                    or "fresh"
                ),
            )

        self._atualizar_controles_musica()'''


NOVO_RESET_MUSICA = r'''        self.jogo_estado.setText(
            "Estado indisponível durante a reconexão"
        )

        self.musica_titulo.setText(
            "Nenhuma faixa confirmada"
        )
        self.musica_detalhe.setText(
            "Aguardando estado observado "
            "do player."
        )
        self.musica_capa.definir_titulo(
            ""
        )
        self.musica_capa.carregar(
            ""
        )

        self._estado_musica = (
            "unavailable"
        )
        self._controles_musica = False

        self.musica_progresso.setValue(
            0
        )
        self.musica_posicao.setText(
            "0:00"
        )
        self.musica_duracao.setText(
            "0:00"
        )

        self._musica_posicao_base = 0.0
        self._musica_duracao_base = 0.0
        self._musica_observada_em = 0.0

        self._definir_visual_musica(
            "unavailable",
            "unavailable",
        )

        self._atualizar_controles_musica()'''


def localizar_projeto() -> tuple[Path, Path, Path]:
    bases = [
        Path.cwd(),
        Path(__file__).resolve().parent,
    ]

    candidatos: list[Path] = []

    for base in bases:
        direto = (
            base
            / "cliente"
            / "terminal_2"
            / "dashboard.py"
        )

        if direto.is_file():
            candidatos.append(
                direto
            )

        for encontrado in base.glob(
            "*/cliente/terminal_2/dashboard.py"
        ):
            if encontrado.is_file():
                candidatos.append(
                    encontrado
                )

    vistos: set[Path] = set()

    for dashboard in candidatos:
        dashboard = dashboard.resolve()

        if dashboard in vistos:
            continue

        vistos.add(dashboard)

        raiz = dashboard.parents[2]
        terminal = (
            raiz
            / "cliente"
            / "terminal_laylay_2.py"
        )

        if terminal.is_file():
            return (
                raiz,
                dashboard,
                terminal,
            )

    raise FileNotFoundError(
        "Não encontrei o projeto Laylay. "
        "Execute este arquivo na pasta "
        "'projeto lay' ou dentro de "
        "'laylay'."
    )


def substituir_unico(
    texto: str,
    padrao: str,
    novo: str,
    descricao: str,
) -> str:
    resultado, quantidade = re.subn(
        padrao,
        novo,
        texto,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )

    if quantidade != 1:
        raise RuntimeError(
            f"Não consegui localizar "
            f"{descricao}. "
            f"Nenhum arquivo foi salvo."
        )

    return resultado


def main() -> None:
    (
        raiz,
        dashboard_path,
        terminal_path,
    ) = localizar_projeto()

    dashboard_original = (
        dashboard_path.read_text(
            encoding="utf-8"
        )
    )
    terminal_original = (
        terminal_path.read_text(
            encoding="utf-8"
        )
    )

    dashboard = dashboard_original
    terminal = terminal_original

    if (
        '"railCard",\n            "music"'
        in dashboard
        or "HOME — CARD MÚSICA"
        in terminal
    ):
        print(
            "O card Música já parece "
            "ter sido aplicado."
        )
        return

    padrao_card = (
        r'^        musica = '
        r'CartaoDashboard\("Música", '
        r'subtitulo="P4"\)\n'
        r'.*?'
        r'^        layout\.addWidget'
        r'\(musica\)'
    )

    dashboard = substituir_unico(
        dashboard,
        padrao_card,
        NOVO_CARD_MUSICA,
        "o card Música antigo",
    )

    ancora_helper = (
        "    def _solicitar_musica"
        "(self, acao_id: str) -> None:"
    )

    if ancora_helper not in dashboard:
        raise RuntimeError(
            "Não encontrei _solicitar_musica(). "
            "Nenhum arquivo foi salvo."
        )

    dashboard = dashboard.replace(
        ancora_helper,
        HELPER_VISUAL
        + ancora_helper,
        1,
    )

    padrao_aplicar = (
        r'^        musica = '
        r'dashboard\.get\("music"\)\n'
        r'.*?'
        r'^        self\._atualizar_controles_musica'
        r'\(\)'
    )

    dashboard = substituir_unico(
        dashboard,
        padrao_aplicar,
        NOVO_APLICAR_MUSICA,
        "a atualização do player "
        "na coluna direita",
    )

    inicio_lateral = dashboard.index(
        "class PainelLateralDashboard"
    )
    fim_lateral = dashboard.index(
        "\ndef _cabecalho_pagina",
        inicio_lateral,
    )

    parte_lateral = dashboard[
        inicio_lateral:fim_lateral
    ]

    padrao_reset = (
        r'^        self\.jogo_estado\.setText'
        r'\("Estado indisponível durante a reconexão"\)\n'
        r'^        self\.musica_titulo\.setText'
        r'\("Nenhuma faixa confirmada"\)\n'
        r'.*?'
        r'^        self\._atualizar_controles_musica'
        r'\(\)'
    )

    parte_lateral = substituir_unico(
        parte_lateral,
        padrao_reset,
        NOVO_RESET_MUSICA,
        "o reset do card Música",
    )

    dashboard = (
        dashboard[:inicio_lateral]
        + parte_lateral
        + dashboard[fim_lateral:]
    )

    ancora_qss = (
        '                #musicTitle '
        '{{ font-size: 13px; '
        'font-weight: 700; }}'
    )

    if ancora_qss not in terminal:
        raise RuntimeError(
            "Não encontrei a âncora "
            "#musicTitle no QSS. "
            "Nenhum arquivo foi salvo."
        )

    terminal = terminal.replace(
        ancora_qss,
        QSS_MUSICA + ancora_qss,
        1,
    )

    compile(
        dashboard,
        str(dashboard_path),
        "exec",
    )
    compile(
        terminal,
        str(terminal_path),
        "exec",
    )

    dashboard_backup = (
        dashboard_path.with_name(
            "dashboard.py.musica.bak"
        )
    )
    terminal_backup = (
        terminal_path.with_name(
            "terminal_laylay_2.py.musica.bak"
        )
    )

    shutil.copy2(
        dashboard_path,
        dashboard_backup,
    )
    shutil.copy2(
        terminal_path,
        terminal_backup,
    )

    dashboard_path.write_text(
        dashboard,
        encoding="utf-8",
    )
    terminal_path.write_text(
        terminal,
        encoding="utf-8",
    )

    print()
    print("CARD MÚSICA APLICADO COM SUCESSO")
    print("--------------------------------")
    print(f"Projeto:   {raiz}")
    print(f"Dashboard: {dashboard_path}")
    print(f"Terminal:  {terminal_path}")
    print()
    print("Backups:")
    print(f"  {dashboard_backup}")
    print(f"  {terminal_backup}")
    print()
    print(
        "Os dois arquivos passaram "
        "pela validação de sintaxe."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:
        print()
        print("ERRO:")
        print(erro)
        raise
