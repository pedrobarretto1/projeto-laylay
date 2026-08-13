from __future__ import annotations

import re
import shutil
from pathlib import Path


QSS_ULTIMOS = r'''
                /* =========================================
                   HOME — ROTINAS + MODO JOGO
                   ========================================= */

                #dashboardCard[railCard="routines"],
                #dashboardCard[railCard="game"] {{
                    background: #14191E;
                    border: 1px solid #2B3239;
                    border-radius: 14px;
                }}

                #dashboardCard[railCard="routines"][routineState="active"],
                #dashboardCard[railCard="game"][gameState="active"] {{
                    border-color: #57303A;
                }}

                #dashboardCard[railCard="routines"][routineState="stale"],
                #dashboardCard[railCard="game"][gameState="stale"] {{
                    border-color: #574728;
                }}

                #dashboardCard[railCard="routines"][routineState="unavailable"],
                #dashboardCard[railCard="game"][gameState="unavailable"] {{
                    border-color: #252B31;
                }}

                #dashboardCard[railCard="routines"] #dashboardCardTitle,
                #dashboardCard[railCard="game"] #dashboardCardTitle {{
                    color: #F3EFF1;
                    font-size: 13px;
                    font-weight: 700;
                }}

                /* Rotinas */

                #railRoutineBadge {{
                    background: #20262C;
                    border: 1px solid #323940;
                    border-radius: 7px;
                    padding: 3px 6px;
                    color: #858D96;
                    font-size: 8px;
                    font-weight: 700;
                }}

                #railRoutineBadge[state="active"] {{
                    background: #2A1A20;
                    border-color: #5B303B;
                    color: #FF6D82;
                }}

                #railRoutineBadge[state="empty"] {{
                    background: #1B2025;
                    border-color: #333A42;
                    color: #929AA2;
                }}

                #railRoutineBadge[state="stale"] {{
                    background: #272116;
                    border-color: #5A4827;
                    color: #D3AA61;
                }}

                #railRoutineBadge[state="unavailable"] {{
                    background: #181C20;
                    border-color: #282E34;
                    color: #646C74;
                }}

                #railRoutineRow {{
                    background: #171C21;
                    border: 1px solid #292F36;
                    border-radius: 9px;
                }}

                #railRoutineRow:hover {{
                    background: #1C2127;
                    border-color: #3C343A;
                }}

                #railRoutineIcon {{
                    background: #241B20;
                    border: 1px solid #49313A;
                    border-radius: 12px;
                    color: #D35469;
                    font-size: 11px;
                    font-weight: 700;
                }}

                #railRoutineName {{
                    background: transparent;
                    border: 0;
                    color: #DDD9DB;
                    font-size: 9px;
                    font-weight: 650;
                }}

                #railRoutineMeta {{
                    background: transparent;
                    border: 0;
                    color: #747C85;
                    font-size: 8px;
                }}

                #railRoutineEmpty {{
                    background: #171C21;
                    border: 1px solid #292F36;
                    border-radius: 9px;
                    padding: 8px 10px;
                    color: #777F88;
                    font-size: 8px;
                }}

                /* Modo jogo */

                #railGamePanel {{
                    background: #171C21;
                    border: 1px solid #292F36;
                    border-radius: 10px;
                }}

                #railGamePanel[state="active"] {{
                    background: #20191D;
                    border-color: #493039;
                }}

                #railGamePanel[state="stale"] {{
                    background: #1E1B16;
                    border-color: #514326;
                }}

                #railGamePanel[state="unavailable"] {{
                    background: #15191D;
                    border-color: #252B31;
                }}

                #railGameIcon {{
                    background: #20262C;
                    border: 1px solid #30373E;
                    border-radius: 14px;
                    color: #69717A;
                    font-size: 12px;
                    font-weight: 700;
                }}

                #railGameIcon[state="active"] {{
                    background: #382027;
                    border-color: #67313C;
                    color: #FF7186;
                }}

                #railGameIcon[state="stale"] {{
                    background: #342B19;
                    border-color: #66532D;
                    color: #D5AD62;
                }}

                #railGameTitle {{
                    background: transparent;
                    border: 0;
                    color: #E5E1E3;
                    font-size: 10px;
                    font-weight: 700;
                }}

                #railGameMeta {{
                    background: transparent;
                    border: 0;
                    color: #747C85;
                    font-size: 8px;
                }}

                #railGameBadge {{
                    background: #1B2025;
                    border: 1px solid #323940;
                    border-radius: 7px;
                    padding: 3px 6px;
                    color: #858D96;
                    font-size: 8px;
                    font-weight: 700;
                }}

                #railGameBadge[state="active"] {{
                    background: #2A1A20;
                    border-color: #5B303B;
                    color: #FF6D82;
                }}

                #railGameBadge[state="inactive"] {{
                    background: #1B2025;
                    border-color: #333A42;
                    color: #8E969E;
                }}

                #railGameBadge[state="stale"] {{
                    background: #272116;
                    border-color: #5A4827;
                    color: #D3AA61;
                }}

                #railGameBadge[state="unavailable"] {{
                    background: #181C20;
                    border-color: #282E34;
                    color: #646C74;
                }}

'''


NOVOS_CARDS = r'''        rotinas = CartaoDashboard(
            "Rotinas"
        )
        rotinas.setProperty(
            "railCard",
            "routines",
        )
        rotinas.setProperty(
            "routineState",
            "unavailable",
        )
        rotinas.layout_principal.setContentsMargins(
            14, 13, 14, 12
        )
        rotinas.layout_principal.setSpacing(7)
        self.rotinas_card = rotinas

        rotinas_status = QHBoxLayout()
        rotinas_status.setContentsMargins(
            0, 0, 0, 0
        )

        self.rotinas_badge = QLabel(
            "OFFLINE"
        )
        self.rotinas_badge.setObjectName(
            "railRoutineBadge"
        )
        self.rotinas_badge.setProperty(
            "state",
            "unavailable",
        )

        rotinas_status.addWidget(
            self.rotinas_badge,
            0,
            Qt.AlignLeft,
        )
        rotinas_status.addStretch()

        rotinas.layout_principal.addLayout(
            rotinas_status
        )

        self.rotinas_estado = QLabel(
            "Aguardando rotinas confirmadas "
            "pela agenda."
        )
        self.rotinas_estado.setObjectName(
            "railRoutineEmpty"
        )
        self.rotinas_estado.setWordWrap(
            True
        )

        rotinas.layout_principal.addWidget(
            self.rotinas_estado
        )

        self.rotinas_linhas: list[
            tuple[
                QFrame,
                QLabel,
                QLabel,
            ]
        ] = []

        for _ in range(3):
            linha = QFrame()
            linha.setObjectName(
                "railRoutineRow"
            )
            linha.hide()

            linha_lay = QHBoxLayout(
                linha
            )
            linha_lay.setContentsMargins(
                8, 7, 8, 7
            )
            linha_lay.setSpacing(8)

            icone = QLabel("◷")
            icone.setObjectName(
                "railRoutineIcon"
            )
            icone.setAlignment(
                Qt.AlignCenter
            )
            icone.setFixedSize(
                24, 24
            )

            textos = QVBoxLayout()
            textos.setContentsMargins(
                0, 0, 0, 0
            )
            textos.setSpacing(2)

            nome = QLabel("Rotina")
            nome.setObjectName(
                "railRoutineName"
            )
            nome.setWordWrap(True)

            detalhe = QLabel("—")
            detalhe.setObjectName(
                "railRoutineMeta"
            )
            detalhe.setWordWrap(True)

            textos.addWidget(nome)
            textos.addWidget(detalhe)

            linha_lay.addWidget(
                icone,
                0,
                Qt.AlignTop,
            )
            linha_lay.addLayout(
                textos,
                1,
            )

            rotinas.layout_principal.addWidget(
                linha
            )

            self.rotinas_linhas.append(
                (
                    linha,
                    nome,
                    detalhe,
                )
            )

        layout.addWidget(rotinas)

        jogo = CartaoDashboard(
            "Modo jogo"
        )
        jogo.setProperty(
            "railCard",
            "game",
        )
        jogo.setProperty(
            "gameState",
            "unavailable",
        )
        jogo.layout_principal.setContentsMargins(
            14, 13, 14, 12
        )
        jogo.layout_principal.setSpacing(7)
        self.jogo_card = jogo

        jogo_painel = QFrame()
        jogo_painel.setObjectName(
            "railGamePanel"
        )
        jogo_painel.setProperty(
            "state",
            "unavailable",
        )
        self.jogo_painel = jogo_painel

        jogo_lay = QHBoxLayout(
            jogo_painel
        )
        jogo_lay.setContentsMargins(
            9, 8, 9, 8
        )
        jogo_lay.setSpacing(9)

        self.jogo_icone = QLabel("◉")
        self.jogo_icone.setObjectName(
            "railGameIcon"
        )
        self.jogo_icone.setProperty(
            "state",
            "unavailable",
        )
        self.jogo_icone.setAlignment(
            Qt.AlignCenter
        )
        self.jogo_icone.setFixedSize(
            28, 28
        )

        jogo_textos = QVBoxLayout()
        jogo_textos.setContentsMargins(
            0, 0, 0, 0
        )
        jogo_textos.setSpacing(2)

        self.jogo_estado = QLabel(
            "Estado indisponível"
        )
        self.jogo_estado.setObjectName(
            "railGameTitle"
        )
        self.jogo_estado.setWordWrap(True)

        self.jogo_detalhe = QLabel(
            "Detecção automática"
        )
        self.jogo_detalhe.setObjectName(
            "railGameMeta"
        )
        self.jogo_detalhe.setWordWrap(True)

        jogo_textos.addWidget(
            self.jogo_estado
        )
        jogo_textos.addWidget(
            self.jogo_detalhe
        )

        self.jogo_badge = QLabel(
            "OFFLINE"
        )
        self.jogo_badge.setObjectName(
            "railGameBadge"
        )
        self.jogo_badge.setProperty(
            "state",
            "unavailable",
        )

        jogo_lay.addWidget(
            self.jogo_icone,
            0,
            Qt.AlignTop,
        )
        jogo_lay.addLayout(
            jogo_textos,
            1,
        )
        jogo_lay.addWidget(
            self.jogo_badge,
            0,
            Qt.AlignTop,
        )

        jogo.layout_principal.addWidget(
            jogo_painel
        )

        layout.addWidget(jogo)'''


HELPERS = r'''    def _aplicar_rotinas(
        self,
        rotinas: object,
    ) -> None:
        frescor = (
            str(
                rotinas.get("freshness")
                or "unavailable"
            )
            if isinstance(
                rotinas,
                dict,
            )
            else "unavailable"
        )

        itens = (
            [
                item
                for item
                in list(
                    rotinas.get("items")
                    or ()
                )[:3]
                if isinstance(
                    item,
                    dict,
                )
            ]
            if (
                isinstance(
                    rotinas,
                    dict,
                )
                and frescor
                != "unavailable"
            )
            else []
        )

        if frescor == "unavailable":
            visual = "unavailable"
            badge = "OFFLINE"
            vazio = (
                "Rotinas indisponíveis."
            )

        elif frescor == "stale":
            visual = "stale"
            badge = "ANTIGO"
            vazio = (
                "Nenhuma rotina recente "
                "confirmada."
            )

        elif itens:
            visual = "active"
            quantidade = len(itens)
            badge = (
                f"{quantidade} ATIVA"
                if quantidade == 1
                else f"{quantidade} ATIVAS"
            )
            vazio = ""

        else:
            visual = "empty"
            badge = "VAZIO"
            vazio = (
                "Nenhuma rotina recorrente "
                "confirmada."
            )

        self.rotinas_card.setProperty(
            "routineState",
            visual,
        )
        self.rotinas_badge.setProperty(
            "state",
            visual,
        )
        self.rotinas_badge.setText(
            badge
        )

        for widget in (
            self.rotinas_card,
            self.rotinas_badge,
        ):
            widget.style().unpolish(
                widget
            )
            widget.style().polish(
                widget
            )

        if not itens:
            self.rotinas_estado.setText(
                vazio
            )
            self.rotinas_estado.show()

            for (
                linha,
                _nome,
                _detalhe,
            ) in self.rotinas_linhas:
                linha.hide()

            return

        self.rotinas_estado.hide()

        for indice, (
            linha,
            nome_label,
            detalhe_label,
        ) in enumerate(
            self.rotinas_linhas
        ):
            if indice >= len(itens):
                linha.hide()
                continue

            item = itens[indice]

            nome = str(
                item.get("name")
                or "Rotina"
            ).strip()

            horario = str(
                item.get("time")
                or "—"
            ).strip()

            dias_brutos = item.get(
                "days"
            )

            dias = (
                ", ".join(
                    str(dia)
                    for dia in dias_brutos
                    if str(dia).strip()
                )
                if isinstance(
                    dias_brutos,
                    (list, tuple),
                )
                else ""
            )

            detalhe = (
                horario
                + (
                    f" · {dias}"
                    if dias
                    else ""
                )
            )

            if frescor == "stale":
                detalhe += (
                    " · dados antigos"
                )

            nome_label.setText(
                nome
            )
            detalhe_label.setText(
                detalhe
            )
            linha.show()

    def _aplicar_modo_jogo(
        self,
        contexto: object,
    ) -> None:
        frescor = (
            str(
                contexto.get("freshness")
                or "unavailable"
            )
            if isinstance(
                contexto,
                dict,
            )
            else "unavailable"
        )

        if frescor == "unavailable":
            visual = "unavailable"
            badge = "OFFLINE"
            titulo = (
                "Estado indisponível"
            )
            detalhe = (
                "Detecção automática"
            )

        elif (
            isinstance(
                contexto,
                dict,
            )
            and contexto.get(
                "game_active"
            ) is True
        ):
            nome = str(
                contexto.get("game_name")
                or "Jogo detectado"
            )

            visual = (
                "stale"
                if frescor == "stale"
                else "active"
            )
            badge = (
                "ANTIGO"
                if visual == "stale"
                else "ATIVO"
            )
            titulo = nome
            detalhe = (
                "Dados antigos"
                if visual == "stale"
                else "Modo jogo detectado "
                     "automaticamente"
            )

        else:
            visual = (
                "stale"
                if frescor == "stale"
                else "inactive"
            )
            badge = (
                "ANTIGO"
                if visual == "stale"
                else "DESATIVADO"
            )
            titulo = (
                "Nenhum jogo detectado"
            )
            detalhe = (
                "Dados antigos"
                if visual == "stale"
                else "Detecção automática"
            )

        self.jogo_card.setProperty(
            "gameState",
            visual,
        )
        self.jogo_painel.setProperty(
            "state",
            visual,
        )
        self.jogo_icone.setProperty(
            "state",
            visual,
        )
        self.jogo_badge.setProperty(
            "state",
            visual,
        )

        self.jogo_badge.setText(
            badge
        )
        self.jogo_estado.setText(
            titulo
        )
        self.jogo_detalhe.setText(
            detalhe
        )

        for widget in (
            self.jogo_card,
            self.jogo_painel,
            self.jogo_icone,
            self.jogo_badge,
        ):
            widget.style().unpolish(
                widget
            )
            widget.style().polish(
                widget
            )

'''


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
        '"railCard",\n            "routines"'
        in dashboard
        or "HOME — ROTINAS + MODO JOGO"
        in terminal
    ):
        print(
            "Rotinas + Modo jogo já parecem "
            "ter sido aplicados."
        )
        return

    # -------------------------------------------------
    # 1. Troca os dois cards antigos
    # -------------------------------------------------
    padrao_cards = (
        r'^        rotinas = '
        r'CartaoDashboard\("Rotinas", '
        r'subtitulo="P4"\)\n'
        r'.*?'
        r'^        layout\.addWidget\(jogo\)'
    )

    dashboard = substituir_unico(
        dashboard,
        padrao_cards,
        NOVOS_CARDS,
        "os cards Rotinas e Modo jogo",
    )

    # -------------------------------------------------
    # 2. Helpers visuais / de dados
    # -------------------------------------------------
    ancora_helpers = (
        "    def _definir_visual_musica("
    )

    if ancora_helpers not in dashboard:
        raise RuntimeError(
            "Não encontrei "
            "_definir_visual_musica(). "
            "Nenhum arquivo foi salvo."
        )

    dashboard = dashboard.replace(
        ancora_helpers,
        HELPERS + ancora_helpers,
        1,
    )

    # -------------------------------------------------
    # 3. Modo jogo no aplicar_dashboard
    # -------------------------------------------------
    padrao_jogo = (
        r'^        contexto = '
        r'dashboard\.get\("context"\)\n'
        r'^        frescor = \(\n'
        r'.*?'
        r'^            \)\n'
        r'^        musica = dashboard\.get\(\n'
    )

    dashboard = substituir_unico(
        dashboard,
        padrao_jogo,
        '        self._aplicar_modo_jogo(\n'
        '            dashboard.get("context")\n'
        '        )\n'
        '        musica = dashboard.get(\n',
        "a atualização antiga do Modo jogo",
    )

    # -------------------------------------------------
    # 4. Rotinas no aplicar_dashboard
    # -------------------------------------------------
    padrao_rotinas = (
        r'^        rotinas = '
        r'dashboard\.get\("routines"\)\n'
        r'.*?'
        r'^            \)\n'
        r'(?=\n    def invalidar_dashboard)'
    )

    dashboard = substituir_unico(
        dashboard,
        padrao_rotinas,
        '        self._aplicar_rotinas(\n'
        '            dashboard.get("routines")\n'
        '        )\n',
        "a atualização antiga de Rotinas",
    )

    # -------------------------------------------------
    # 5. Reset do Modo jogo
    # -------------------------------------------------
    dashboard = dashboard.replace(
        '        self.jogo_estado.setText(\n'
        '            "Estado indisponível durante a reconexão"\n'
        '        )\n',
        '        self._aplicar_modo_jogo(None)\n',
        1,
    )

    # -------------------------------------------------
    # 6. Reset das Rotinas
    # -------------------------------------------------
    dashboard = dashboard.replace(
        '        self.rotinas_estado.setText('
        '"Aguardando rotinas confirmadas pela agenda.")\n',
        '        self._aplicar_rotinas(None)\n',
        1,
    )

    # -------------------------------------------------
    # 7. QSS
    # -------------------------------------------------
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
        QSS_ULTIMOS + ancora_qss,
        1,
    )

    # -------------------------------------------------
    # 8. Validação de sintaxe
    # -------------------------------------------------
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

    # -------------------------------------------------
    # 9. Backups + escrita
    # -------------------------------------------------
    dashboard_backup = (
        dashboard_path.with_name(
            "dashboard.py.ultimos_cards.bak"
        )
    )
    terminal_backup = (
        terminal_path.with_name(
            "terminal_laylay_2.py."
            "ultimos_cards.bak"
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
    print(
        "ROTINAS + MODO JOGO "
        "APLICADOS COM SUCESSO"
    )
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
