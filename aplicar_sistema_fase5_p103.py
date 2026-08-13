from __future__ import annotations

import ast
import shutil
from pathlib import Path


CSS_RAW = r"""
/* =========================================
   P10.3 — SISTEMA FASE 5 / RIGHT RAIL
   ========================================= */

#systemWorkbench {
    background: transparent;
    border: 0;
}

#systemMainColumn,
#systemRightRail {
    background: transparent;
    border: 0;
}

#systemLaylayCard {
    background: #12161B;
    border: 1px solid #60313B;
    border-radius: 14px;
}

#systemLaylayCard #dashboardCardTitle {
    color: #F4F0F2;
    font-size: 14px;
    font-weight: 720;
}

#systemLaylayCard #dashboardCardHint {
    background: #2A1A20;
    border: 1px solid #55303A;
    border-radius: 7px;
    padding: 3px 6px;
    color: #E96379;
    font-size: 8px;
    font-weight: 700;
}

#systemLaylayStatus {
    background: #17201C;
    border: 1px solid #315442;
    border-radius: 9px;
    padding: 8px 9px;
    color: #78CFA4;
    font-size: 9px;
    font-weight: 700;
}

#systemLaylayStatus[state="partial"] {
    background: #201C16;
    border-color: #59462A;
    color: #D1A660;
}

#systemLaylayStatus[state="unavailable"] {
    background: #17191C;
    border-color: #292F36;
    color: #747C84;
}

#systemLaylayRow {
    background: #171C21;
    border: 1px solid #292F36;
    border-radius: 8px;
}

#systemLaylayRow #dashboardMetricLabel {
    background: transparent;
    border: 0;
    padding: 6px 8px;
    color: #818992;
    font-size: 8px;
    font-weight: 600;
}

#systemLaylayRow #dashboardMetricValue {
    background: transparent;
    border: 0;
    padding: 6px 8px;
    color: #ECE8EA;
    font-size: 9px;
    font-weight: 650;
}

#systemLaylayPulse {
    background: #181D22;
    border: 1px solid #2B3239;
    border-radius: 9px;
    padding: 7px 9px;
    color: #9BA2A9;
    font-size: 8px;
}

#systemRightRail #systemActionsCard,
#systemRightRail #systemAlertsCard {
    background: #12171C;
    border-color: #292F36;
}

#systemRightRail QPushButton[systemQuickAction="true"] {
    min-height: 31px;
    padding: 6px 9px;
}

#systemRightRail #systemAlertItem {
    padding: 6px 8px;
}

#systemMainColumn #systemAudioCard {
    min-height: 170px;
}
"""


def localizar_projeto():
    bases = [
        Path.cwd(),
        Path(__file__).resolve().parent,
    ]

    for base in bases:
        candidatos = [base]
        try:
            candidatos.extend(
                p for p in base.iterdir()
                if p.is_dir()
            )
        except OSError:
            pass

        for raiz in candidatos:
            dashboard = (
                raiz
                / "cliente"
                / "terminal_2"
                / "dashboard.py"
            )
            terminal = (
                raiz
                / "cliente"
                / "terminal_laylay_2.py"
            )

            if (
                dashboard.is_file()
                and terminal.is_file()
            ):
                return (
                    raiz.resolve(),
                    dashboard.resolve(),
                    terminal.resolve(),
                )

    raise FileNotFoundError(
        "Não encontrei o projeto Laylay."
    )


def validar_dashboard(texto: str) -> None:
    arvore = ast.parse(texto)

    pagina = next(
        (
            no
            for no in arvore.body
            if isinstance(no, ast.ClassDef)
            and no.name == "PaginaSistema"
        ),
        None,
    )

    if pagina is None:
        raise RuntimeError(
            "PaginaSistema não encontrada."
        )

    metodos = {
        no.name
        for no in pagina.body
        if isinstance(no, ast.FunctionDef)
    }

    obrigatorios = {
        "__init__",
        "aplicar_dashboard",
        "invalidar",
        "definir_estado_audio",
        "_definir_alertas",
        "_atualizar_status_laylay",
    }

    faltando = obrigatorios - metodos

    if faltando:
        raise RuntimeError(
            "PaginaSistema perdeu métodos: "
            + ", ".join(sorted(faltando))
        )


def main() -> None:
    raiz, dashboard_path, terminal_path = (
        localizar_projeto()
    )

    dashboard_original = dashboard_path.read_text(
        encoding="utf-8"
    )
    terminal_original = terminal_path.read_text(
        encoding="utf-8"
    )

    if (
        "P10.3 — SISTEMA FASE 5 / RIGHT RAIL"
        in terminal_original
    ):
        print("O P10.3 já está aplicado.")
        return

    if (
        "P10.2 — Fase 4: áudio, ações e alertas."
        not in dashboard_original
    ):
        raise RuntimeError(
            "A Fase 4 precisa estar aplicada antes."
        )

    texto = dashboard_original

    # --------------------------------------------------
    # 1. Corpo e linha inferior deixam de entrar
    #    diretamente no layout externo. Serão montados
    #    na nova coluna principal ao final.
    # --------------------------------------------------
    antigo_corpo = """        externo.addLayout(corpo, 3)

        # P10.1 — Fase 3: Modelo local + armazenamento.
"""
    novo_corpo = """        # P10.3: corpo será inserido na coluna principal.

        # P10.1 — Fase 3: Modelo local + armazenamento.
"""

    if antigo_corpo not in texto:
        raise RuntimeError(
            "Não encontrei a montagem do corpo P10."
        )

    texto = texto.replace(
        antigo_corpo,
        novo_corpo,
        1,
    )

    antigo_inferior = """        externo.addLayout(
            linha_inferior,
            2,
        )

        # P10.2 — Fase 4: áudio, ações e alertas.
"""
    novo_inferior = """        # P10.3: linha inferior será inserida
        # na coluna principal ao final.

        # P10.2 — Fase 4: áudio, ações e alertas.
"""

    if antigo_inferior not in texto:
        raise RuntimeError(
            "Não encontrei a linha inferior P10.1."
        )

    texto = texto.replace(
        antigo_inferior,
        novo_inferior,
        1,
    )

    # --------------------------------------------------
    # 2. Substitui o fechamento da Fase 4 pela nova
    #    arquitetura principal + lateral.
    # --------------------------------------------------
    antigo_fim_fase4 = """        fase4.addWidget(
            self.audio_card,
            1,
        )
        fase4.addWidget(
            self.acoes_card,
            1,
        )
        fase4.addWidget(
            self.alertas_card,
            1,
        )

        externo.addLayout(
            fase4,
            2,
        )

    def definir_estado_audio(
"""

    if antigo_fim_fase4 not in texto:
        raise RuntimeError(
            "Não encontrei o final visual da Fase 4."
        )

    novo_fim_fase4 = """        # P10.3 — Fase 5: workbench principal
        # com uma lateral compacta à direita.
        workbench = QHBoxLayout()
        workbench.setObjectName(
            "systemWorkbench"
        )
        workbench.setContentsMargins(
            0, 0, 0, 0
        )
        workbench.setSpacing(12)

        principal = QVBoxLayout()
        principal.setObjectName(
            "systemMainColumn"
        )
        principal.setContentsMargins(
            0, 0, 0, 0
        )
        principal.setSpacing(12)

        principal.addLayout(
            corpo,
            3,
        )
        principal.addLayout(
            linha_inferior,
            2,
        )
        principal.addWidget(
            self.audio_card,
            2,
        )

        lateral = QVBoxLayout()
        lateral.setObjectName(
            "systemRightRail"
        )
        lateral.setContentsMargins(
            0, 0, 0, 0
        )
        lateral.setSpacing(10)

        # ----------------------------------------------
        # Card Laylay
        # ----------------------------------------------
        self.laylay_card = CartaoDashboard(
            "Laylay",
            subtitulo="estado vivo",
        )
        self.laylay_card.setObjectName(
            "systemLaylayCard"
        )
        self.laylay_card.setMinimumWidth(
            220
        )
        self.laylay_card.setMaximumWidth(
            270
        )

        self.laylay_status = QLabel(
            "Aguardando estado"
        )
        self.laylay_status.setObjectName(
            "systemLaylayStatus"
        )
        self.laylay_status.setProperty(
            "state",
            "unavailable",
        )
        self.laylay_card.layout_principal.addWidget(
            self.laylay_status
        )

        self.laylay_valores: dict[
            str, QLabel
        ] = {}

        for chave, rotulo in (
            ("mind", "Mente"),
            ("memory", "Memória"),
            ("voice", "Voz"),
            ("mode", "Interação"),
        ):
            linha, valor = _linha_valor(
                rotulo
            )
            linha.setObjectName(
                "systemLaylayRow"
            )
            self.laylay_card.layout_principal.addWidget(
                linha
            )
            self.laylay_valores[
                chave
            ] = valor

        self.laylay_pulso = QLabel(
            "✦ aguardando dashboard"
        )
        self.laylay_pulso.setObjectName(
            "systemLaylayPulse"
        )
        self.laylay_pulso.setWordWrap(
            True
        )
        self.laylay_card.layout_principal.addWidget(
            self.laylay_pulso
        )

        self.acoes_card.setMinimumWidth(
            220
        )
        self.acoes_card.setMaximumWidth(
            270
        )
        self.alertas_card.setMinimumWidth(
            220
        )
        self.alertas_card.setMaximumWidth(
            270
        )

        lateral.addWidget(
            self.laylay_card
        )
        lateral.addWidget(
            self.acoes_card
        )
        lateral.addWidget(
            self.alertas_card
        )
        lateral.addStretch()

        workbench.addLayout(
            principal,
            1,
        )
        workbench.addLayout(
            lateral,
            0,
        )

        externo.addLayout(
            workbench,
            1,
        )

    def _atualizar_status_laylay(
        self,
        saude: dict,
    ) -> None:
        llm = (
            saude.get("llm")
            if isinstance(
                saude.get("llm"),
                dict,
            )
            else {}
        )
        memoria = (
            saude.get("memory")
            if isinstance(
                saude.get("memory"),
                dict,
            )
            else {}
        )
        microfone = (
            saude.get("microphone")
            if isinstance(
                saude.get("microphone"),
                dict,
            )
            else {}
        )

        self.laylay_valores[
            "mind"
        ].setText(
            str(
                llm.get("label")
                or "—"
            )
        )
        self.laylay_valores[
            "memory"
        ].setText(
            str(
                memoria.get("label")
                or "—"
            )
        )
        self.laylay_valores[
            "voice"
        ].setText(
            str(
                microfone.get("label")
                or "—"
            )
        )

        criticos = 0
        parciais = 0

        for item in (
            llm,
            memoria,
            microfone,
        ):
            estado_item = str(
                item.get("state")
                or "unavailable"
            )
            frescor_item = str(
                item.get("freshness")
                or "unavailable"
            )

            if (
                estado_item
                in {
                    "unavailable",
                    "degraded",
                }
                or frescor_item
                == "unavailable"
            ):
                criticos += 1
            elif frescor_item == "stale":
                parciais += 1

        if criticos:
            self.laylay_status.setText(
                "Operação parcial"
            )
            self.laylay_status.setProperty(
                "state",
                "partial",
            )
            self.laylay_pulso.setText(
                "✦ alguns módulos não estão "
                "confirmados agora"
            )
        elif parciais:
            self.laylay_status.setText(
                "Operacional · dados antigos"
            )
            self.laylay_status.setProperty(
                "state",
                "partial",
            )
            self.laylay_pulso.setText(
                "✦ módulos ativos, aguardando "
                "telemetria mais recente"
            )
        else:
            self.laylay_status.setText(
                "Operacional"
            )
            self.laylay_status.setProperty(
                "state",
                "ok",
            )
            self.laylay_pulso.setText(
                "✦ mente, memória e voz "
                "observadas"
            )

        self.laylay_status.style().unpolish(
            self.laylay_status
        )
        self.laylay_status.style().polish(
            self.laylay_status
        )

    def definir_estado_audio(
"""

    texto = texto.replace(
        antigo_fim_fase4,
        novo_fim_fase4,
        1,
    )

    # --------------------------------------------------
    # 3. Modo de interação alimenta também a lateral.
    # --------------------------------------------------
    ancora_modo = """        self.audio_valores[
            "mode"
        ].setText(
            "Voz"
            if modo == "voice"
            else "Chat"
        )
"""

    if ancora_modo not in texto:
        raise RuntimeError(
            "Não encontrei o modo de áudio."
        )

    texto = texto.replace(
        ancora_modo,
        ancora_modo
        + """
        self.laylay_valores[
            "mode"
        ].setText(
            "Voz"
            if modo == "voice"
            else "Chat"
        )
""",
        1,
    )

    # --------------------------------------------------
    # 4. Dashboard alimenta a lateral Laylay.
    # --------------------------------------------------
    ancora_saude = """        llm = (
            saude.get("llm")
            if isinstance(
                saude.get("llm"),
                dict,
            )
            else {}
        )

        microfone = (
"""

    if ancora_saude not in texto:
        raise RuntimeError(
            "Não encontrei health.llm da página."
        )

    texto = texto.replace(
        ancora_saude,
        """        self._atualizar_status_laylay(
            saude
        )

""" + ancora_saude,
        1,
    )

    # --------------------------------------------------
    # 5. Invalidação da lateral.
    # --------------------------------------------------
    ancora_invalidar = """        self.audio_status.setText(
            "Aguardando microfone"
        )
"""

    if ancora_invalidar not in texto:
        raise RuntimeError(
            "Não encontrei invalidar() Fase 4."
        )

    texto = texto.replace(
        ancora_invalidar,
        """        self.laylay_status.setText(
            "Aguardando estado"
        )
        self.laylay_status.setProperty(
            "state",
            "unavailable",
        )
        self.laylay_pulso.setText(
            "✦ aguardando dashboard"
        )

        for valor in self.laylay_valores.values():
            valor.setText("—")

        self.laylay_status.style().unpolish(
            self.laylay_status
        )
        self.laylay_status.style().polish(
            self.laylay_status
        )

        self.audio_status.setText(
            "Aguardando microfone"
        )
""",
        1,
    )

    validar_dashboard(
        texto
    )

    compile(
        texto,
        str(dashboard_path),
        "exec",
    )

    # --------------------------------------------------
    # 6. CSS — escapa para o f-string do terminal.
    # --------------------------------------------------
    css_escapado = (
        CSS_RAW
        .replace("{", "{{")
        .replace("}", "}}")
    )

    ancora_css = (
        "                #pageTitle "
        "{{ font-size: 28px; "
    )

    if ancora_css not in terminal_original:
        raise RuntimeError(
            "Não encontrei a âncora CSS."
        )

    terminal_novo = terminal_original.replace(
        ancora_css,
        css_escapado + ancora_css,
        1,
    )

    compile(
        terminal_novo,
        str(terminal_path),
        "exec",
    )

    # --------------------------------------------------
    # 7. Backups + escrita.
    # --------------------------------------------------
    backup_dashboard = dashboard_path.with_name(
        "dashboard.py.sistema_p103.bak"
    )
    backup_terminal = terminal_path.with_name(
        "terminal_laylay_2.py.sistema_p103.bak"
    )

    shutil.copy2(
        dashboard_path,
        backup_dashboard,
    )
    shutil.copy2(
        terminal_path,
        backup_terminal,
    )

    dashboard_path.write_text(
        texto,
        encoding="utf-8",
    )
    terminal_path.write_text(
        terminal_novo,
        encoding="utf-8",
    )

    print()
    print("P10.3 — SISTEMA FASE 5 APLICADA")
    print("--------------------------------")
    print(f"Projeto: {raiz}")
    print()
    print("Mudanças:")
    print("  ✓ coluna principal")
    print("  ✓ lateral direita compacta")
    print("  ✓ card Laylay")
    print("  ✓ mente / memória / voz")
    print("  ✓ modo Chat/Voz")
    print("  ✓ ações rápidas movidas à lateral")
    print("  ✓ alertas movidos à lateral")
    print("  ✓ áudio permanece no painel principal")
    print()
    print(
        "Tudo usa apenas estados já observados "
        "pelo dashboard."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:
        print()
        print("ERRO:")
        print(erro)
        raise
