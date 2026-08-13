from __future__ import annotations

import re
import shutil
from pathlib import Path


QSS_SISTEMA = r'''
                /* =========================================
                   HOME — CARD SISTEMA
                   ========================================= */

                #dashboardCard[railCard="system"] {{
                    background: #14191E;
                    border: 1px solid #2B3239;
                    border-radius: 14px;
                }}

                #dashboardCard[railCard="system"] #dashboardCardTitle {{
                    color: #F3EFF1;
                    font-size: 13px;
                    font-weight: 700;
                }}

                #dashboardCard[railCard="system"] #dashboardCardHint {{
                    background: #2A1A20;
                    border: 1px solid #55303A;
                    border-radius: 7px;
                    padding: 3px 6px;
                    color: #E96379;
                    font-size: 8px;
                    font-weight: 700;
                }}

                #railSystemMetric {{
                    background: #171C21;
                    border: 1px solid #292F36;
                    border-radius: 9px;
                }}

                #railSystemMetric[state="stale"] {{
                    background: #1C1B1B;
                    border-color: #54442D;
                }}

                #railSystemMetric[state="unavailable"] {{
                    background: #15191D;
                    border-color: #23292F;
                }}

                #railSystemMetricLabel {{
                    background: transparent;
                    border: 0;
                    color: #858D96;
                    font-size: 9px;
                    font-weight: 600;
                }}

                #railSystemMetricValue {{
                    background: transparent;
                    border: 0;
                    color: #F0ECEE;
                    font-size: 11px;
                    font-weight: 700;
                }}

                #railSystemMetricValue[state="stale"] {{
                    color: #D4AE6A;
                }}

                #railSystemMetricValue[state="unavailable"] {{
                    color: #5D656D;
                }}

                #railSystemProgress {{
                    background: #242A30;
                    border: 0;
                    border-radius: 2px;
                    min-height: 4px;
                    max-height: 4px;
                }}

                #railSystemProgress::chunk {{
                    background: #CF485E;
                    border-radius: 2px;
                }}

                #railSystemProgress[available="false"]::chunk {{
                    background: #343A40;
                }}

                #railSystemFooter {{
                    background: #171C21;
                    border: 1px solid #292F36;
                    border-radius: 9px;
                }}

                #railSystemFooter[state="stale"] {{
                    border-color: #54442D;
                }}

                #railSystemFooter[state="unavailable"] {{
                    background: #15191D;
                    border-color: #23292F;
                }}

                #railSystemFooterIcon {{
                    background: #241B20;
                    border: 1px solid #49313A;
                    border-radius: 11px;
                    color: #D35469;
                    font-size: 10px;
                }}

                #railSystemStatus {{
                    background: transparent;
                    border: 0;
                    padding: 2px 1px;
                    color: #737B84;
                    font-size: 8px;
                }}

                #railSystemStatus[state="ok"] {{
                    color: #68C79A;
                }}

                #railSystemStatus[state="partial"] {{
                    color: #C6A05E;
                }}

                #railSystemStatus[state="unavailable"] {{
                    color: #7A8189;
                }}

                #railSystemStatus[state="pending"] {{
                    color: #69717A;
                }}

'''


NOVO_CARD_SISTEMA = r'''        sistema = CartaoDashboard(
            "Sistema",
            subtitulo="AO VIVO",
        )
        sistema.setProperty(
            "railCard",
            "system",
        )
        sistema.layout_principal.setContentsMargins(
            14, 13, 14, 12
        )
        sistema.layout_principal.setSpacing(8)

        self.metricas: dict[str, QLabel] = {}
        self.barras_metricas: dict[str, QProgressBar] = {}
        self.metricas_linhas: dict[str, QFrame] = {}

        for chave, rotulo in (
            ("cpu", "CPU"),
            ("ram", "RAM"),
            ("temperatura", "Temperatura"),
            ("disco", "Disco"),
        ):
            bloco = QFrame()
            bloco.setObjectName(
                "railSystemMetric"
            )
            bloco.setProperty(
                "metric",
                chave,
            )
            bloco.setProperty(
                "state",
                "unavailable",
            )

            bloco_lay = QVBoxLayout(
                bloco
            )
            bloco_lay.setContentsMargins(
                9, 7, 9, 7
            )
            bloco_lay.setSpacing(5)

            topo = QHBoxLayout()
            topo.setContentsMargins(
                0, 0, 0, 0
            )
            topo.setSpacing(6)

            nome = QLabel(rotulo)
            nome.setObjectName(
                "railSystemMetricLabel"
            )

            valor = QLabel("—")
            valor.setObjectName(
                "railSystemMetricValue"
            )
            valor.setProperty(
                "state",
                "unavailable",
            )
            valor.setAlignment(
                Qt.AlignRight
                | Qt.AlignVCenter
            )

            topo.addWidget(nome)
            topo.addStretch()
            topo.addWidget(valor)

            barra = QProgressBar()
            barra.setObjectName(
                "railSystemProgress"
            )
            barra.setRange(0, 100)
            barra.setValue(0)
            barra.setTextVisible(False)
            barra.setProperty(
                "available",
                False,
            )

            bloco_lay.addLayout(topo)
            bloco_lay.addWidget(barra)

            self.metricas[chave] = valor
            self.barras_metricas[chave] = barra
            self.metricas_linhas[chave] = bloco

            sistema.layout_principal.addWidget(
                bloco
            )

        uptime = QFrame()
        uptime.setObjectName(
            "railSystemFooter"
        )
        uptime.setProperty(
            "state",
            "unavailable",
        )

        uptime_lay = QHBoxLayout(
            uptime
        )
        uptime_lay.setContentsMargins(
            9, 7, 9, 7
        )
        uptime_lay.setSpacing(8)

        uptime_icone = QLabel("◷")
        uptime_icone.setObjectName(
            "railSystemFooterIcon"
        )
        uptime_icone.setAlignment(
            Qt.AlignCenter
        )
        uptime_icone.setFixedSize(
            22, 22
        )

        uptime_nome = QLabel(
            "Tempo ligado"
        )
        uptime_nome.setObjectName(
            "railSystemMetricLabel"
        )

        uptime_valor = QLabel("—")
        uptime_valor.setObjectName(
            "railSystemMetricValue"
        )
        uptime_valor.setProperty(
            "state",
            "unavailable",
        )
        uptime_valor.setAlignment(
            Qt.AlignRight
            | Qt.AlignVCenter
        )

        uptime_lay.addWidget(
            uptime_icone
        )
        uptime_lay.addWidget(
            uptime_nome
        )
        uptime_lay.addStretch()
        uptime_lay.addWidget(
            uptime_valor
        )

        self.metricas[
            "uptime"
        ] = uptime_valor
        self.metricas_linhas[
            "uptime"
        ] = uptime

        sistema.layout_principal.addWidget(
            uptime
        )

        self.sistema_estado = QLabel(
            "Aguardando telemetria real da mente."
        )
        self.sistema_estado.setObjectName(
            "railSystemStatus"
        )
        self.sistema_estado.setProperty(
            "state",
            "pending",
        )
        self.sistema_estado.setWordWrap(
            True
        )

        sistema.layout_principal.addWidget(
            self.sistema_estado
        )
        layout.addWidget(sistema)'''


NOVO_APLICAR_SISTEMA = r'''        campos = {
            "cpu": (
                sistema.get("cpu_percent"),
                False,
            ),
            "ram": (
                sistema.get("ram_percent"),
                False,
            ),
            "disco": (
                sistema.get("disk_percent"),
                False,
            ),
            "temperatura": (
                sistema.get("temperature_c"),
                False,
            ),
            "uptime": (
                sistema.get("uptime_seconds"),
                True,
            ),
        }

        for chave, (
            metrica,
            uptime,
        ) in campos.items():
            valor_label = self.metricas[
                chave
            ]

            valor_label.setText(
                _texto_metrica(
                    metrica,
                    uptime=uptime,
                )
            )

            disponivel = (
                isinstance(metrica, dict)
                and metrica.get("value")
                is not None
            )

            frescor = (
                str(
                    metrica.get(
                        "freshness"
                    )
                    or "unavailable"
                )
                if isinstance(
                    metrica,
                    dict,
                )
                else "unavailable"
            )

            estado_linha = (
                "stale"
                if disponivel
                and frescor == "stale"
                else "fresh"
                if disponivel
                else "unavailable"
            )

            linha = (
                self.metricas_linhas.get(
                    chave
                )
            )

            if linha is not None:
                linha.setProperty(
                    "state",
                    estado_linha,
                )
                linha.style().unpolish(
                    linha
                )
                linha.style().polish(
                    linha
                )

            valor_label.setProperty(
                "state",
                estado_linha,
            )
            valor_label.style().unpolish(
                valor_label
            )
            valor_label.style().polish(
                valor_label
            )

            barra = (
                self.barras_metricas.get(
                    chave
                )
            )

            if barra is not None:
                try:
                    valor_barra = (
                        float(
                            metrica.get(
                                "value"
                            )
                        )
                        if isinstance(
                            metrica,
                            dict,
                        )
                        else 0.0
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    valor_barra = 0.0

                barra.setValue(
                    max(
                        0,
                        min(
                            100,
                            round(
                                valor_barra
                            ),
                        ),
                    )
                )
                barra.setProperty(
                    "available",
                    disponivel,
                )
                barra.style().unpolish(
                    barra
                )
                barra.style().polish(
                    barra
                )

        disponiveis = sum(
            valor.text() != "—"
            for valor
            in self.metricas.values()
        )

        if disponiveis == len(
            self.metricas
        ):
            estado_sistema = "ok"
            texto_sistema = (
                "●  Telemetria atualizada"
            )

        elif disponiveis:
            estado_sistema = "partial"
            texto_sistema = (
                "●  Telemetria parcial"
            )

        else:
            estado_sistema = (
                "unavailable"
            )
            texto_sistema = (
                "●  Telemetria indisponível"
            )

        self.sistema_estado.setText(
            texto_sistema
        )
        self.sistema_estado.setProperty(
            "state",
            estado_sistema,
        )
        self.sistema_estado.style().unpolish(
            self.sistema_estado
        )
        self.sistema_estado.style().polish(
            self.sistema_estado
        )'''


NOVO_INVALIDAR_SISTEMA = r'''        for chave, valor in self.metricas.items():
            valor.setText("—")
            valor.setProperty(
                "state",
                "unavailable",
            )
            valor.style().unpolish(
                valor
            )
            valor.style().polish(
                valor
            )

            linha = (
                self.metricas_linhas.get(
                    chave
                )
            )
            if linha is not None:
                linha.setProperty(
                    "state",
                    "unavailable",
                )
                linha.style().unpolish(
                    linha
                )
                linha.style().polish(
                    linha
                )

        for barra in (
            self.barras_metricas.values()
        ):
            barra.setValue(0)
            barra.setProperty(
                "available",
                False,
            )
            barra.style().unpolish(
                barra
            )
            barra.style().polish(
                barra
            )

        self.sistema_estado.setText(
            "Aguardando telemetria real da mente."
        )
        self.sistema_estado.setProperty(
            "state",
            "pending",
        )
        self.sistema_estado.style().unpolish(
            self.sistema_estado
        )
        self.sistema_estado.style().polish(
            self.sistema_estado
        )'''


def localizar_projeto() -> tuple[Path, Path, Path]:
    bases = [
        Path.cwd(),
        Path(__file__).resolve().parent,
    ]
    candidatos: list[Path] = []

    for base in bases:
        direto = base / "cliente" / "terminal_2" / "dashboard.py"
        if direto.is_file():
            candidatos.append(direto)

        for encontrado in base.glob("*/cliente/terminal_2/dashboard.py"):
            if encontrado.is_file():
                candidatos.append(encontrado)

    vistos: set[Path] = set()

    for dashboard in candidatos:
        dashboard = dashboard.resolve()
        if dashboard in vistos:
            continue
        vistos.add(dashboard)

        raiz = dashboard.parents[2]
        terminal = raiz / "cliente" / "terminal_laylay_2.py"

        if terminal.is_file():
            return raiz, dashboard, terminal

    raise FileNotFoundError(
        "Não encontrei o projeto Laylay. "
        "Execute este arquivo na pasta 'projeto lay' "
        "ou dentro da pasta 'laylay'."
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
            f"Não consegui localizar {descricao}. "
            f"Nenhum arquivo foi salvo."
        )

    return resultado


def main() -> None:
    raiz, dashboard_path, terminal_path = localizar_projeto()

    dashboard_original = dashboard_path.read_text(encoding="utf-8")
    terminal_original = terminal_path.read_text(encoding="utf-8")

    dashboard = dashboard_original
    terminal = terminal_original

    padrao_card = (
        r'^        sistema = '
        r'CartaoDashboard\("Sistema", '
        r'subtitulo="P2"\)\n'
        r'.*?'
        r'^        layout\.addWidget'
        r'\(sistema\)'
    )

    dashboard = substituir_unico(
        dashboard,
        padrao_card,
        NOVO_CARD_SISTEMA,
        "o card Sistema antigo",
    )

    padrao_aplicar = (
        r'^        campos = \{\n'
        r'.*?'
        r'^        contexto = '
        r'dashboard\.get\("context"\)'
    )

    dashboard = substituir_unico(
        dashboard,
        padrao_aplicar,
        NOVO_APLICAR_SISTEMA
        + '\n        contexto = dashboard.get("context")',
        "a atualização do card Sistema",
    )

    inicio_lateral = dashboard.index("class PainelLateralDashboard")
    fim_lateral = dashboard.index("\ndef _cabecalho_pagina", inicio_lateral)

    parte_lateral = dashboard[inicio_lateral:fim_lateral]

    padrao_invalidar = (
        r'^        for valor in '
        r'self\.metricas\.values\(\):\n'
        r'            valor\.setText\("—"\)\n'
        r'^        for barra in '
        r'self\.barras_metricas\.values\(\):\n'
        r'            barra\.setValue\(0\)\n'
        r'^        self\.sistema_estado\.setText'
        r'\("Aguardando telemetria real da mente\."\)'
    )

    parte_lateral = substituir_unico(
        parte_lateral,
        padrao_invalidar,
        NOVO_INVALIDAR_SISTEMA,
        "o reset do card Sistema",
    )

    dashboard = (
        dashboard[:inicio_lateral]
        + parte_lateral
        + dashboard[fim_lateral:]
    )

    marcador = "HOME — CARD SISTEMA"

    if marcador not in terminal:
        ancora = (
            '                #musicTitle '
            '{{ font-size: 13px; '
            'font-weight: 700; }}'
        )

        if ancora not in terminal:
            raise RuntimeError(
                "Não encontrei a âncora do QSS no "
                "terminal_laylay_2.py. Nenhum arquivo foi salvo."
            )

        terminal = terminal.replace(
            ancora,
            QSS_SISTEMA + ancora,
            1,
        )

    compile(dashboard, str(dashboard_path), "exec")
    compile(terminal, str(terminal_path), "exec")

    dashboard_backup = dashboard_path.with_name(
        "dashboard.py.sistema.bak"
    )
    terminal_backup = terminal_path.with_name(
        "terminal_laylay_2.py.sistema.bak"
    )

    shutil.copy2(dashboard_path, dashboard_backup)
    shutil.copy2(terminal_path, terminal_backup)

    dashboard_path.write_text(dashboard, encoding="utf-8")
    terminal_path.write_text(terminal, encoding="utf-8")

    print()
    print("CARD SISTEMA APLICADO COM SUCESSO")
    print("--------------------------------")
    print(f"Projeto:   {raiz}")
    print(f"Dashboard: {dashboard_path}")
    print(f"Terminal:  {terminal_path}")
    print()
    print("Backups:")
    print(f"  {dashboard_backup}")
    print(f"  {terminal_backup}")
    print()
    print("Os dois arquivos passaram pela validação de sintaxe.")


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:
        print()
        print("ERRO:")
        print(erro)
        raise
