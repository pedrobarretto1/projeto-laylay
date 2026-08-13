from __future__ import annotations

import ast
import shutil
from pathlib import Path


CSS_RAW = r"""
/* =========================================
   P10.2 — SISTEMA FASE 4
   ========================================= */

#systemPhase4Row {
    background: transparent;
    border: 0;
}

#systemAudioCard,
#systemActionsCard,
#systemAlertsCard {
    background: #11161B;
    border: 1px solid #282F36;
    border-radius: 13px;
}

#systemAudioCard #dashboardCardTitle,
#systemActionsCard #dashboardCardTitle,
#systemAlertsCard #dashboardCardTitle {
    color: #F0ECEE;
    font-size: 13px;
    font-weight: 700;
}

#systemAudioStatus {
    background: #171C21;
    border: 1px solid #2B3239;
    border-radius: 8px;
    padding: 7px 9px;
    color: #858D96;
    font-size: 9px;
    font-weight: 650;
}

#systemAudioStatus[state="ok"] {
    background: #17201C;
    border-color: #294838;
    color: #72C99D;
}

#systemAudioStatus[state="pending"] {
    background: #1B1C1C;
    border-color: #4E432D;
    color: #C5A05D;
}

#systemAudioStatus[state="error"] {
    background: #21171B;
    border-color: #5C3039;
    color: #E67386;
}

#systemAudioStatus[state="unavailable"] {
    background: #15191D;
    border-color: #252B31;
    color: #707880;
}

#systemAudioRow {
    background: #151A1F;
    border: 1px solid #232A31;
    border-radius: 8px;
}

#systemAudioRow #dashboardMetricLabel {
    background: transparent;
    border: 0;
    padding: 6px 8px;
    color: #858D96;
    font-size: 8px;
    font-weight: 600;
}

#systemAudioRow #dashboardMetricValue {
    background: transparent;
    border: 0;
    padding: 6px 8px;
    color: #ECE8EA;
    font-size: 9px;
    font-weight: 650;
}

#systemAudioLevelHeader {
    background: transparent;
    border: 0;
}

#systemAudioLevelLabel {
    background: transparent;
    border: 0;
    color: #858D96;
    font-size: 8px;
    font-weight: 600;
}

#systemAudioLevelValue {
    background: transparent;
    border: 0;
    color: #F0ECEE;
    font-size: 9px;
    font-weight: 700;
}

#systemAudioLevel {
    background: #242A30;
    border: 0;
    border-radius: 2px;
    min-height: 5px;
    max-height: 5px;
}

#systemAudioLevel::chunk {
    background: #68C79A;
    border-radius: 2px;
}

QPushButton[systemQuickAction="true"] {
    background: #151A1F;
    border: 1px solid #292F36;
    border-radius: 9px;
    min-height: 34px;
    padding: 7px 10px;
    text-align: left;
    color: #C7C3C6;
    font-size: 9px;
    font-weight: 600;
}

QPushButton[systemQuickAction="true"]:hover {
    background: #241A1F;
    border-color: #713541;
    color: #FFF3F5;
}

QPushButton[systemQuickAction="true"]:pressed {
    background: #2D1C22;
    border-color: #A54355;
    color: #FF7588;
}

#systemActionsHint {
    background: #14191E;
    border: 1px solid #252C33;
    border-radius: 8px;
    padding: 7px 9px;
    color: #707881;
    font-size: 8px;
}

#systemAlertStatus {
    background: #171C21;
    border: 1px solid #2B3239;
    border-radius: 8px;
    padding: 8px 9px;
    color: #858D96;
    font-size: 9px;
    font-weight: 650;
}

#systemAlertStatus[state="ok"] {
    background: #17201C;
    border-color: #294838;
    color: #72C99D;
}

#systemAlertStatus[state="warning"] {
    background: #201C16;
    border-color: #59462A;
    color: #D1A660;
}

#systemAlertItem {
    background: #151A1F;
    border: 1px solid #252C33;
    border-radius: 8px;
    padding: 7px 9px;
    color: #A8AEB4;
    font-size: 8px;
}

#systemAlertItem[kind="warning"] {
    background: #1E1A16;
    border-color: #4F402B;
    color: #C9A15E;
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
            if dashboard.is_file() and terminal.is_file():
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

    if "P10.2 — SISTEMA FASE 4" in terminal_original:
        print("O P10.2 já está aplicado.")
        return

    if (
        "P10.1 — Fase 3: Modelo local + armazenamento."
        not in dashboard_original
    ):
        raise RuntimeError(
            "A Fase 3 precisa estar aplicada antes."
        )

    texto = dashboard_original

    # --------------------------------------------------
    # 1. Signal da página Sistema.
    # --------------------------------------------------
    ancora_classe = """class PaginaSistema(QWidget):
    def __init__(self) -> None:
"""

    if ancora_classe not in texto:
        raise RuntimeError(
            "Não encontrei a classe PaginaSistema."
        )

    texto = texto.replace(
        ancora_classe,
        """class PaginaSistema(QWidget):
    acao_solicitada = Signal(str, str)

    def __init__(self) -> None:
""",
        1,
    )

    # --------------------------------------------------
    # 2. Terceira faixa visual.
    # --------------------------------------------------
    ancora_fase4 = """        externo.addLayout(
            linha_inferior,
            2,
        )

    @staticmethod
"""

    if ancora_fase4 not in texto:
        raise RuntimeError(
            "Não encontrei o final da Fase 3."
        )

    bloco_fase4 = """        externo.addLayout(
            linha_inferior,
            2,
        )

        # P10.2 — Fase 4: áudio, ações e alertas.
        fase4 = QHBoxLayout()
        fase4.setObjectName(
            "systemPhase4Row"
        )
        fase4.setContentsMargins(
            0, 0, 0, 0
        )
        fase4.setSpacing(12)

        # ----------------------------------------------
        # Áudio e entrada
        # ----------------------------------------------
        self.audio_card = CartaoDashboard(
            "Áudio e entrada",
            subtitulo="estado observado",
        )
        self.audio_card.setObjectName(
            "systemAudioCard"
        )

        self.audio_status = QLabel(
            "Aguardando microfone"
        )
        self.audio_status.setObjectName(
            "systemAudioStatus"
        )
        self.audio_status.setProperty(
            "state",
            "pending",
        )
        self.audio_card.layout_principal.addWidget(
            self.audio_status
        )

        self.audio_valores: dict[
            str, QLabel
        ] = {}

        for chave, rotulo in (
            ("health", "Microfone"),
            ("mode", "Modo atual"),
            ("capture", "Captura de voz"),
            ("freshness", "Frescor"),
        ):
            linha, valor = _linha_valor(
                rotulo
            )
            linha.setObjectName(
                "systemAudioRow"
            )
            self.audio_card.layout_principal.addWidget(
                linha
            )
            self.audio_valores[
                chave
            ] = valor

        nivel_topo = QWidget()
        nivel_topo.setObjectName(
            "systemAudioLevelHeader"
        )
        nivel_topo_lay = QHBoxLayout(
            nivel_topo
        )
        nivel_topo_lay.setContentsMargins(
            1, 2, 1, 0
        )
        nivel_topo_lay.setSpacing(6)

        nivel_nome = QLabel(
            "Nível de entrada"
        )
        nivel_nome.setObjectName(
            "systemAudioLevelLabel"
        )

        self.audio_nivel_valor = QLabel(
            "—"
        )
        self.audio_nivel_valor.setObjectName(
            "systemAudioLevelValue"
        )

        nivel_topo_lay.addWidget(
            nivel_nome
        )
        nivel_topo_lay.addStretch()
        nivel_topo_lay.addWidget(
            self.audio_nivel_valor
        )

        self.audio_nivel = QProgressBar()
        self.audio_nivel.setObjectName(
            "systemAudioLevel"
        )
        self.audio_nivel.setRange(
            0, 100
        )
        self.audio_nivel.setValue(0)
        self.audio_nivel.setTextVisible(
            False
        )

        self.audio_card.layout_principal.addWidget(
            nivel_topo
        )
        self.audio_card.layout_principal.addWidget(
            self.audio_nivel
        )

        # ----------------------------------------------
        # Ações rápidas
        # ----------------------------------------------
        self.acoes_card = CartaoDashboard(
            "Ações rápidas",
            subtitulo="via mente canônica",
        )
        self.acoes_card.setObjectName(
            "systemActionsCard"
        )

        acoes_validas = [
            item
            for item in ACOES_RAPIDAS_TERMINAL
            if str(
                item.get("request")
                or ""
            ).strip()
        ]

        for definicao in acoes_validas:
            acao_id = str(
                definicao.get("id")
                or ""
            )
            pedido = str(
                definicao.get("request")
                or ""
            )
            rotulo = str(
                definicao.get("label")
                or acao_id
            )

            botao = QPushButton(
                rotulo
            )
            botao.setProperty(
                "systemQuickAction",
                True,
            )
            botao.clicked.connect(
                lambda _checked=False,
                aid=acao_id,
                req=pedido:
                self.acao_solicitada.emit(
                    aid,
                    req,
                )
            )
            self.acoes_card.layout_principal.addWidget(
                botao
            )

        acoes_hint = QLabel(
            "Esses botões enviam o mesmo pedido "
            "textual usado pela conversa."
        )
        acoes_hint.setObjectName(
            "systemActionsHint"
        )
        acoes_hint.setWordWrap(True)
        self.acoes_card.layout_principal.addWidget(
            acoes_hint
        )

        # ----------------------------------------------
        # Alertas
        # ----------------------------------------------
        self.alertas_card = CartaoDashboard(
            "Alertas",
            subtitulo="dashboard local",
        )
        self.alertas_card.setObjectName(
            "systemAlertsCard"
        )

        self.alerta_status = QLabel(
            "Aguardando dashboard"
        )
        self.alerta_status.setObjectName(
            "systemAlertStatus"
        )
        self.alerta_status.setProperty(
            "state",
            "pending",
        )
        self.alertas_card.layout_principal.addWidget(
            self.alerta_status
        )

        self.alerta_itens: list[
            QLabel
        ] = []

        for _ in range(3):
            item = QLabel("")
            item.setObjectName(
                "systemAlertItem"
            )
            item.setWordWrap(True)
            item.hide()
            self.alerta_itens.append(
                item
            )
            self.alertas_card.layout_principal.addWidget(
                item
            )

        self.alertas_card.layout_principal.addStretch()

        fase4.addWidget(
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
        self,
        modo: str,
        voz_disponivel: bool,
        nivel: float,
    ) -> None:
        modo = str(
            modo or "chat"
        ).casefold()

        self.audio_valores[
            "mode"
        ].setText(
            "Voz"
            if modo == "voice"
            else "Chat"
        )

        self.audio_valores[
            "capture"
        ].setText(
            "Disponível"
            if voz_disponivel
            else "Indisponível"
        )

        try:
            numero = float(nivel)
        except (
            TypeError,
            ValueError,
        ):
            numero = 0.0

        # O estado pode chegar normalizado (0–1)
        # ou já em percentual.
        if 0.0 <= numero <= 1.0:
            numero *= 100.0

        numero = max(
            0.0,
            min(
                100.0,
                numero,
            ),
        )

        self.audio_nivel.setValue(
            int(numero)
        )
        self.audio_nivel_valor.setText(
            f"{numero:.0f}%"
            if voz_disponivel
            else "—"
        )

    def _definir_alertas(
        self,
        alertas: list[str],
    ) -> None:
        alertas = [
            str(item).strip()
            for item in alertas
            if str(item).strip()
        ]

        if alertas:
            self.alerta_status.setText(
                f"{len(alertas)} aviso"
                if len(alertas) == 1
                else f"{len(alertas)} avisos"
            )
            self.alerta_status.setProperty(
                "state",
                "warning",
            )
        else:
            self.alerta_status.setText(
                "Nenhum alerta observado"
            )
            self.alerta_status.setProperty(
                "state",
                "ok",
            )

        self.alerta_status.style().unpolish(
            self.alerta_status
        )
        self.alerta_status.style().polish(
            self.alerta_status
        )

        for indice, label in enumerate(
            self.alerta_itens
        ):
            if indice < len(alertas):
                label.setText(
                    alertas[indice]
                )
                label.setProperty(
                    "kind",
                    "warning",
                )
                label.show()
                label.style().unpolish(
                    label
                )
                label.style().polish(
                    label
                )
            else:
                label.hide()

    @staticmethod
"""

    texto = texto.replace(
        ancora_fase4,
        bloco_fase4,
        1,
    )

    # --------------------------------------------------
    # 3. Atualiza áudio + alertas no dashboard.
    # --------------------------------------------------
    ancora_health = """        llm = (
            saude.get("llm")
            if isinstance(
                saude.get("llm"),
                dict,
            )
            else {}
        )
"""

    if ancora_health not in texto:
        raise RuntimeError(
            "Não encontrei health.llm da Fase 3."
        )

    bloco_health = ancora_health + """
        microfone = (
            saude.get("microphone")
            if isinstance(
                saude.get("microphone"),
                dict,
            )
            else {}
        )

        mic_estado = str(
            microfone.get("state")
            or "unavailable"
        )
        mic_rotulo = str(
            microfone.get("label")
            or "Indisponível"
        )
        mic_frescor = str(
            microfone.get("freshness")
            or "unavailable"
        )

        self.audio_valores[
            "health"
        ].setText(
            mic_rotulo
        )

        nomes_frescor_audio = {
            "fresh": "Atual",
            "stale": "Antigo",
            "unavailable": "Indisponível",
        }

        self.audio_valores[
            "freshness"
        ].setText(
            nomes_frescor_audio.get(
                mic_frescor,
                mic_frescor or "—",
            )
        )

        audio_visual = {
            "online": "ok",
            "ready": "ok",
            "paused": "pending",
            "degraded": "error",
            "unavailable": "unavailable",
        }.get(
            mic_estado,
            "pending",
        )

        if mic_frescor == "stale":
            audio_visual = "pending"
        elif mic_frescor == "unavailable":
            audio_visual = "unavailable"

        self.audio_status.setText(
            mic_rotulo
        )
        self.audio_status.setProperty(
            "state",
            audio_visual,
        )
        self.audio_status.style().unpolish(
            self.audio_status
        )
        self.audio_status.style().polish(
            self.audio_status
        )
"""

    texto = texto.replace(
        ancora_health,
        bloco_health,
        1,
    )

    ancora_alertas = """        download = _texto_metrica(
            sistema.get("download_mbps")
        )
"""

    if ancora_alertas not in texto:
        raise RuntimeError(
            "Não encontrei o ponto dos alertas."
        )

    bloco_alertas = """        alertas: list[str] = []

        nomes_saude = {
            "llm": "Modelo local",
            "memory": "Memória",
            "microphone": "Microfone",
        }

        for chave_saude, nome_saude in nomes_saude.items():
            item_saude = (
                saude.get(chave_saude)
                if isinstance(
                    saude.get(chave_saude),
                    dict,
                )
                else {}
            )

            estado_item = str(
                item_saude.get("state")
                or "unavailable"
            )
            frescor_item = str(
                item_saude.get("freshness")
                or "unavailable"
            )

            if estado_item == "degraded":
                alertas.append(
                    f"{nome_saude}: estado degradado."
                )
            elif estado_item == "unavailable":
                alertas.append(
                    f"{nome_saude}: indisponível."
                )
            elif frescor_item == "stale":
                alertas.append(
                    f"{nome_saude}: dados antigos."
                )
            elif frescor_item == "unavailable":
                alertas.append(
                    f"{nome_saude}: sem telemetria atual."
                )

        if ausentes:
            alertas.append(
                "Sistema: telemetria parcial."
            )

        self._definir_alertas(
            alertas[:3]
        )

        download = _texto_metrica(
            sistema.get("download_mbps")
        )
"""

    texto = texto.replace(
        ancora_alertas,
        bloco_alertas,
        1,
    )

    # --------------------------------------------------
    # 4. Invalidação.
    # --------------------------------------------------
    ancora_invalidar = """        for chave in self.recursos_valores:
"""

    if ancora_invalidar not in texto:
        raise RuntimeError(
            "Não encontrei invalidar() atual."
        )

    bloco_invalidar = """        self.audio_status.setText(
            "Aguardando microfone"
        )
        self.audio_status.setProperty(
            "state",
            "pending",
        )
        self.audio_status.style().unpolish(
            self.audio_status
        )
        self.audio_status.style().polish(
            self.audio_status
        )

        self.audio_valores[
            "health"
        ].setText("—")
        self.audio_valores[
            "freshness"
        ].setText("—")
        self.audio_valores[
            "mode"
        ].setText("—")
        self.audio_valores[
            "capture"
        ].setText("—")
        self.audio_nivel.setValue(0)
        self.audio_nivel_valor.setText(
            "—"
        )

        self._definir_alertas(
            [
                "Dashboard ainda não disponível."
            ]
        )

        for chave in self.recursos_valores:
"""

    texto = texto.replace(
        ancora_invalidar,
        bloco_invalidar,
        1,
    )

    validar_dashboard(texto)
    compile(
        texto,
        str(dashboard_path),
        "exec",
    )

    # --------------------------------------------------
    # 5. Terminal: conecta ações.
    # --------------------------------------------------
    terminal_novo = terminal_original

    ancora_connect = """        self.pagina_memoria = PaginaMemoria()
        self.pagina_sistema = PaginaSistema()
        self.paginas.addWidget(self.pagina_automacao)
"""

    if ancora_connect not in terminal_novo:
        raise RuntimeError(
            "Não encontrei criação da PaginaSistema."
        )

    terminal_novo = terminal_novo.replace(
        ancora_connect,
        """        self.pagina_memoria = PaginaMemoria()
        self.pagina_sistema = PaginaSistema()
        self.pagina_sistema.acao_solicitada.connect(
            self.enviar_acao_rapida
        )
        self.paginas.addWidget(self.pagina_automacao)
""",
        1,
    )

    # --------------------------------------------------
    # 6. Terminal: entrega modo/voz/nível à página.
    # --------------------------------------------------
    ancora_estado = """        try:
            self._nivel_microfone = float(estado.get("microphone_level") or 0.0)
        except (TypeError, ValueError):
            self._nivel_microfone = 0.0
        if not self._dashboard_recebido:
"""

    if ancora_estado not in terminal_novo:
        raise RuntimeError(
            "Não encontrei estado do microfone."
        )

    terminal_novo = terminal_novo.replace(
        ancora_estado,
        """        try:
            self._nivel_microfone = float(estado.get("microphone_level") or 0.0)
        except (TypeError, ValueError):
            self._nivel_microfone = 0.0

        self.pagina_sistema.definir_estado_audio(
            self._modo,
            self._voz_disponivel,
            self._nivel_microfone,
        )

        if not self._dashboard_recebido:
""",
        1,
    )

    # --------------------------------------------------
    # 7. CSS — escapa automaticamente para f-string.
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

    if ancora_css not in terminal_novo:
        raise RuntimeError(
            "Não encontrei âncora CSS."
        )

    terminal_novo = terminal_novo.replace(
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
    # 8. Backups e escrita.
    # --------------------------------------------------
    backup_dashboard = dashboard_path.with_name(
        "dashboard.py.sistema_p102.bak"
    )
    backup_terminal = terminal_path.with_name(
        "terminal_laylay_2.py.sistema_p102.bak"
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
    print("P10.2 — SISTEMA FASE 4 APLICADA")
    print("--------------------------------")
    print(f"Projeto: {raiz}")
    print()
    print("Adicionado:")
    print("  ✓ Áudio e entrada")
    print("  ✓ saúde real do microfone")
    print("  ✓ modo Chat/Voz")
    print("  ✓ disponibilidade de captura")
    print("  ✓ nível observado")
    print("  ✓ ações rápidas reais")
    print("  ✓ alertas derivados do dashboard")
    print()
    print("Ações disponíveis:")
    print("  ✓ Abrir VS Code")
    print("  ✓ Organizar desktop")
    print("  ✓ Briefing")
    print()
    print("CSS validado dentro do f-string.")
    print("Nenhum dado fictício foi adicionado.")


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:
        print()
        print("ERRO:")
        print(erro)
        raise
