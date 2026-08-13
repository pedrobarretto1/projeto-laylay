from __future__ import annotations

import ast
import shutil
from pathlib import Path

CLASSES_P10 = '\nclass MiniMetricaSistema(QFrame):\n    # Métrica compacta da página Sistema.\n\n    def __init__(\n        self,\n        titulo: str,\n        *,\n        destaque: str = "",\n    ) -> None:\n        super().__init__()\n        self.setObjectName("systemMetricCard")\n        if destaque:\n            self.setProperty(\n                "metricTone",\n                destaque,\n            )\n\n        layout = QVBoxLayout(self)\n        layout.setContentsMargins(\n            12, 11, 12, 10\n        )\n        layout.setSpacing(7)\n\n        topo = QHBoxLayout()\n        topo.setContentsMargins(0, 0, 0, 0)\n        topo.setSpacing(8)\n\n        self.titulo = QLabel(titulo)\n        self.titulo.setObjectName(\n            "systemMetricTitle"\n        )\n\n        self.valor = QLabel("—")\n        self.valor.setObjectName(\n            "systemMetricValue"\n        )\n        self.valor.setAlignment(\n            Qt.AlignRight | Qt.AlignVCenter\n        )\n\n        topo.addWidget(self.titulo)\n        topo.addStretch()\n        topo.addWidget(self.valor)\n\n        self.barra = QProgressBar()\n        self.barra.setObjectName(\n            "systemMetricProgress"\n        )\n        self.barra.setRange(0, 100)\n        self.barra.setValue(0)\n        self.barra.setTextVisible(False)\n\n        self.grafico = QLabel("—")\n        self.grafico.setObjectName(\n            "systemMetricSparkline"\n        )\n        self.grafico.setMinimumHeight(24)\n        self.grafico.setAlignment(\n            Qt.AlignLeft | Qt.AlignVCenter\n        )\n\n        self.rodape = QLabel("")\n        self.rodape.setObjectName(\n            "systemMetricFooter"\n        )\n        self.rodape.hide()\n\n        layout.addLayout(topo)\n        layout.addWidget(self.barra)\n        layout.addWidget(self.grafico)\n        layout.addWidget(self.rodape)\n\n    def definir_rodape(\n        self,\n        texto: str,\n    ) -> None:\n        texto = str(texto or "").strip()\n        self.rodape.setText(texto)\n        self.rodape.setVisible(bool(texto))\n\n\nclass PaginaSistema(QWidget):\n    def __init__(self) -> None:\n        super().__init__()\n        self.setObjectName("systemPage")\n\n        self._historico: dict[\n            str, deque[float]\n        ] = {\n            chave: deque(maxlen=24)\n            for chave in (\n                "cpu",\n                "gpu",\n                "ram",\n                "vram",\n                "network",\n                "disk",\n            )\n        }\n\n        externo = QVBoxLayout(self)\n        externo.setContentsMargins(\n            32, 24, 32, 30\n        )\n        externo.setSpacing(12)\n\n        # Cabeçalho.\n        cabecalho = QFrame()\n        cabecalho.setObjectName("systemHero")\n\n        hero_lay = QHBoxLayout(cabecalho)\n        hero_lay.setContentsMargins(\n            18, 14, 18, 14\n        )\n        hero_lay.setSpacing(12)\n\n        textos = QVBoxLayout()\n        textos.setContentsMargins(0, 0, 0, 0)\n        textos.setSpacing(2)\n\n        titulo = QLabel("Sistema ✦")\n        titulo.setObjectName(\n            "systemHeroTitle"\n        )\n\n        descricao = QLabel(\n            "Desempenho, recursos e estado "\n            "local da Laylay."\n        )\n        descricao.setObjectName(\n            "systemHeroDescription"\n        )\n\n        textos.addWidget(titulo)\n        textos.addWidget(descricao)\n\n        self.atualizacao = QLabel(\n            "Aguardando telemetria"\n        )\n        self.atualizacao.setObjectName(\n            "systemUpdated"\n        )\n        self.atualizacao.setAlignment(\n            Qt.AlignRight | Qt.AlignVCenter\n        )\n\n        hero_lay.addLayout(textos, 1)\n        hero_lay.addWidget(self.atualizacao)\n\n        externo.addWidget(cabecalho)\n\n        # Corpo: resumo + desempenho.\n        corpo = QHBoxLayout()\n        corpo.setContentsMargins(0, 0, 0, 0)\n        corpo.setSpacing(12)\n\n        self.resumo = CartaoDashboard(\n            "Resumo do sistema"\n        )\n        self.resumo.setObjectName(\n            "systemSectionCard"\n        )\n        self.resumo.setMinimumWidth(275)\n        self.resumo.setMaximumWidth(355)\n\n        self.resumo_valores: dict[\n            str, QLabel\n        ] = {}\n\n        for chave, rotulo in (\n            ("cpu", "CPU"),\n            ("gpu", "GPU"),\n            ("ram", "Memória RAM"),\n            ("vram", "Memória VRAM"),\n            ("disk", "Disco"),\n            ("network", "Rede"),\n        ):\n            linha, valor = _linha_valor(\n                rotulo\n            )\n            linha.setObjectName(\n                "systemSummaryRow"\n            )\n            self.resumo.layout_principal.addWidget(\n                linha\n            )\n            self.resumo_valores[\n                chave\n            ] = valor\n\n        separador = QFrame()\n        separador.setObjectName(\n            "systemSummarySeparator"\n        )\n        separador.setFixedHeight(1)\n\n        self.resumo.layout_principal.addWidget(\n            separador\n        )\n\n        self.temperatura = QLabel(\n            "Temperatura · —"\n        )\n        self.temperatura.setObjectName(\n            "systemSummarySensor"\n        )\n\n        self.uptime = QLabel(\n            "Tempo ligado · —"\n        )\n        self.uptime.setObjectName(\n            "systemSummarySensor"\n        )\n\n        self.estado = QLabel(\n            "Aguardando telemetria"\n        )\n        self.estado.setObjectName(\n            "systemSummaryState"\n        )\n        self.estado.setWordWrap(True)\n\n        self.resumo.layout_principal.addWidget(\n            self.temperatura\n        )\n        self.resumo.layout_principal.addWidget(\n            self.uptime\n        )\n        self.resumo.layout_principal.addWidget(\n            self.estado\n        )\n        self.resumo.layout_principal.addStretch()\n\n        desempenho = CartaoDashboard(\n            "Desempenho em tempo real",\n            subtitulo="24 amostras",\n        )\n        desempenho.setObjectName(\n            "systemSectionCard"\n        )\n\n        grade = QGridLayout()\n        grade.setContentsMargins(0, 2, 0, 0)\n        grade.setHorizontalSpacing(8)\n        grade.setVerticalSpacing(8)\n\n        self.metricas: dict[\n            str, MiniMetricaSistema\n        ] = {}\n\n        definicoes = (\n            ("cpu", "CPU", "cpu"),\n            ("gpu", "GPU", "gpu"),\n            ("ram", "RAM", "ram"),\n            ("vram", "VRAM", "vram"),\n            ("network", "Rede", "network"),\n            ("disk", "Disco", "disk"),\n        )\n\n        for indice, (\n            chave,\n            titulo_metrica,\n            tom,\n        ) in enumerate(definicoes):\n            card = MiniMetricaSistema(\n                titulo_metrica,\n                destaque=tom,\n            )\n            self.metricas[chave] = card\n\n            grade.addWidget(\n                card,\n                indice // 3,\n                indice % 3,\n            )\n\n        desempenho.layout_principal.addLayout(\n            grade\n        )\n\n        self.valores = {\n            chave: card.valor\n            for chave, card\n            in self.metricas.items()\n        }\n        self.barras = {\n            chave: card.barra\n            for chave, card\n            in self.metricas.items()\n        }\n        self.graficos = {\n            chave: card.grafico\n            for chave, card\n            in self.metricas.items()\n        }\n\n        self.rede_taxas = self.metricas[\n            "network"\n        ].rodape\n\n        corpo.addWidget(self.resumo, 3)\n        corpo.addWidget(desempenho, 7)\n\n        externo.addLayout(corpo, 1)\n\n    @staticmethod\n    def _sparkline(\n        valores: deque[float],\n    ) -> str:\n        blocos = "▁▂▃▄▅▆▇█"\n\n        return "".join(\n            blocos[\n                min(\n                    7,\n                    max(\n                        0,\n                        int(v / 12.5),\n                    ),\n                )\n            ]\n            for v in valores\n        ) or "—"\n\n    def aplicar_dashboard(\n        self,\n        dashboard: dict,\n    ) -> None:\n        sistema = (\n            dashboard.get("system")\n            if isinstance(\n                dashboard.get("system"),\n                dict,\n            )\n            else {}\n        )\n\n        campos = (\n            ("cpu", "cpu_percent"),\n            ("gpu", "gpu_percent"),\n            ("ram", "ram_percent"),\n            ("vram", "vram_percent"),\n            ("network", "network_percent"),\n            ("disk", "disk_percent"),\n        )\n\n        ausentes = 0\n\n        for chave, campo in campos:\n            metrica = (\n                sistema.get(campo)\n                if isinstance(\n                    sistema.get(campo),\n                    dict,\n                )\n                else {}\n            )\n\n            valor = metrica.get("value")\n\n            if valor is None:\n                ausentes += 1\n\n                self.valores[\n                    chave\n                ].setText("—")\n                self.barras[\n                    chave\n                ].setValue(0)\n                self.graficos[\n                    chave\n                ].setText(\n                    self._sparkline(\n                        self._historico[chave]\n                    )\n                )\n                self.resumo_valores[\n                    chave\n                ].setText("—")\n                continue\n\n            numero = max(\n                0.0,\n                min(\n                    100.0,\n                    float(valor),\n                ),\n            )\n\n            freshness = str(\n                metrica.get("freshness")\n                or ""\n            )\n\n            if freshness == "fresh":\n                self._historico[\n                    chave\n                ].append(numero)\n\n            sufixo = (\n                " · antigo"\n                if freshness == "stale"\n                else ""\n            )\n\n            texto = (\n                f"{numero:.0f}%{sufixo}"\n            )\n\n            self.valores[\n                chave\n            ].setText(texto)\n            self.barras[\n                chave\n            ].setValue(int(numero))\n            self.graficos[\n                chave\n            ].setText(\n                self._sparkline(\n                    self._historico[chave]\n                )\n            )\n            self.resumo_valores[\n                chave\n            ].setText(texto)\n\n        download = _texto_metrica(\n            sistema.get("download_mbps")\n        )\n        upload = _texto_metrica(\n            sistema.get("upload_mbps")\n        )\n\n        self.metricas[\n            "network"\n        ].definir_rodape(\n            f"↓ {download}   ·   ↑ {upload}"\n        )\n\n        self.temperatura.setText(\n            "Temperatura · "\n            + _texto_metrica(\n                sistema.get(\n                    "temperature_c"\n                )\n            )\n        )\n\n        self.uptime.setText(\n            "Tempo ligado · "\n            + _texto_metrica(\n                sistema.get(\n                    "uptime_seconds"\n                ),\n                uptime=True,\n            )\n        )\n\n        if ausentes:\n            self.estado.setText(\n                "Telemetria parcial · sensores "\n                "ausentes aparecem como —."\n            )\n            self.estado.setProperty(\n                "state",\n                "partial",\n            )\n            self.atualizacao.setText(\n                "Atualização parcial"\n            )\n        else:\n            self.estado.setText(\n                "Sistema observado normalmente."\n            )\n            self.estado.setProperty(\n                "state",\n                "ok",\n            )\n            self.atualizacao.setText(\n                "Atualizado agora"\n            )\n\n        self.estado.style().unpolish(\n            self.estado\n        )\n        self.estado.style().polish(\n            self.estado\n        )\n\n    def invalidar(self) -> None:\n        for chave in self.valores:\n            self.valores[\n                chave\n            ].setText("—")\n            self.barras[\n                chave\n            ].setValue(0)\n            self.graficos[\n                chave\n            ].setText("—")\n            self.resumo_valores[\n                chave\n            ].setText("—")\n\n        self.temperatura.setText(\n            "Temperatura · —"\n        )\n        self.uptime.setText(\n            "Tempo ligado · —"\n        )\n\n        self.metricas[\n            "network"\n        ].definir_rodape(\n            "↓ —   ·   ↑ —"\n        )\n\n        self.estado.setText(\n            "Aguardando telemetria"\n        )\n        self.estado.setProperty(\n            "state",\n            "pending",\n        )\n        self.atualizacao.setText(\n            "Aguardando telemetria"\n        )\n\n        self.estado.style().unpolish(\n            self.estado\n        )\n        self.estado.style().polish(\n            self.estado\n        )\n\n\n'
CSS_P10 = '\n/* =========================================\n   P10 — NOVA ABA SISTEMA\n   ========================================= */\n\n#systemPage {{\n    background: transparent;\n}}\n\n#systemHero {{\n    background: #10151A;\n    border: 1px solid #272E35;\n    border-radius: 14px;\n}}\n\n#systemHeroTitle {{\n    background: transparent;\n    border: 0;\n    color: #F7F3F5;\n    font-size: 24px;\n    font-weight: 720;\n}}\n\n#systemHeroDescription {{\n    background: transparent;\n    border: 0;\n    color: #8D949C;\n    font-size: 11px;\n}}\n\n#systemUpdated {{\n    background: transparent;\n    border: 0;\n    color: #777F88;\n    font-size: 9px;\n    padding: 4px 2px;\n}}\n\n#systemSectionCard {{\n    background: #11161B;\n    border: 1px solid #282F36;\n    border-radius: 13px;\n}}\n\n#systemSectionCard #dashboardCardTitle {{\n    color: #F0ECEE;\n    font-size: 13px;\n    font-weight: 700;\n}}\n\n#systemSectionCard #dashboardCardHint {{\n    background: transparent;\n    border: 0;\n    color: #68717A;\n    font-size: 8px;\n}}\n\n#systemSummaryRow {{\n    background: #151A1F;\n    border: 1px solid #232A31;\n    border-radius: 8px;\n}}\n\n#systemSummaryRow #dashboardMetricLabel {{\n    background: transparent;\n    border: 0;\n    padding: 7px 9px;\n    color: #8D949C;\n    font-size: 9px;\n    font-weight: 600;\n}}\n\n#systemSummaryRow #dashboardMetricValue {{\n    background: transparent;\n    border: 0;\n    padding: 7px 9px;\n    color: #F0ECEE;\n    font-size: 10px;\n    font-weight: 700;\n}}\n\n#systemSummarySeparator {{\n    background: #252C33;\n    border: 0;\n}}\n\n#systemSummarySensor {{\n    background: transparent;\n    border: 0;\n    padding: 2px 3px;\n    color: #BBB7BB;\n    font-size: 10px;\n}}\n\n#systemSummaryState {{\n    background: #171C21;\n    border: 1px solid #292F36;\n    border-radius: 8px;\n    padding: 8px 9px;\n    color: #777F88;\n    font-size: 8px;\n}}\n\n#systemSummaryState[state="ok"] {{\n    border-color: #315242;\n    color: #79CFA4;\n}}\n\n#systemSummaryState[state="partial"] {{\n    border-color: #51452F;\n    color: #C6A05E;\n}}\n\n#systemMetricCard {{\n    background: #151A1F;\n    border: 1px solid #282F36;\n    border-radius: 10px;\n    min-width: 125px;\n}}\n\n#systemMetricCard:hover {{\n    background: #181D22;\n    border-color: #40343A;\n}}\n\n#systemMetricTitle {{\n    background: transparent;\n    border: 0;\n    color: #AAAEB4;\n    font-size: 9px;\n    font-weight: 650;\n}}\n\n#systemMetricValue {{\n    background: transparent;\n    border: 0;\n    color: #F4F0F2;\n    font-size: 15px;\n    font-weight: 720;\n}}\n\n#systemMetricProgress {{\n    background: #242A30;\n    border: 0;\n    border-radius: 2px;\n    min-height: 4px;\n    max-height: 4px;\n}}\n\n#systemMetricProgress::chunk {{\n    background: #D94C63;\n    border-radius: 2px;\n}}\n\n#systemMetricCard[metricTone="gpu"] #systemMetricProgress::chunk {{\n    background: #65B978;\n}}\n\n#systemMetricCard[metricTone="ram"] #systemMetricProgress::chunk {{\n    background: #D68A35;\n}}\n\n#systemMetricCard[metricTone="vram"] #systemMetricProgress::chunk {{\n    background: #9A58D2;\n}}\n\n#systemMetricCard[metricTone="network"] #systemMetricProgress::chunk {{\n    background: #48AFC0;\n}}\n\n#systemMetricCard[metricTone="disk"] #systemMetricProgress::chunk {{\n    background: #4F8CC9;\n}}\n\n#systemMetricSparkline {{\n    background: transparent;\n    border: 0;\n    color: #D94C63;\n    font-family: \'Cascadia Code\';\n    font-size: 16px;\n}}\n\n#systemMetricCard[metricTone="gpu"] #systemMetricSparkline {{\n    color: #65B978;\n}}\n\n#systemMetricCard[metricTone="ram"] #systemMetricSparkline {{\n    color: #D68A35;\n}}\n\n#systemMetricCard[metricTone="vram"] #systemMetricSparkline {{\n    color: #9A58D2;\n}}\n\n#systemMetricCard[metricTone="network"] #systemMetricSparkline {{\n    color: #48AFC0;\n}}\n\n#systemMetricCard[metricTone="disk"] #systemMetricSparkline {{\n    color: #4F8CC9;\n}}\n\n#systemMetricFooter {{\n    background: #12171C;\n    border: 1px solid #252C33;\n    border-radius: 7px;\n    padding: 5px 7px;\n    color: #7EABB3;\n    font-size: 8px;\n}}\n\n'


def localizar_projeto():
    bases = [
        Path.cwd(),
        Path(__file__).resolve().parent,
    ]

    for base in bases:
        candidatos = [base]

        try:
            candidatos.extend(
                caminho
                for caminho in base.iterdir()
                if caminho.is_dir()
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


def validar_dashboard(texto):
    arvore = ast.parse(texto)

    classes = {
        no.name
        for no in arvore.body
        if isinstance(no, ast.ClassDef)
    }

    obrigatorias = {
        "PaginaSistema",
        "MiniMetricaSistema",
        "PaginaModulo",
    }

    faltando = obrigatorias - classes

    if faltando:
        raise RuntimeError(
            "Estrutura inválida no dashboard: "
            + ", ".join(sorted(faltando))
        )


def main():
    raiz, dashboard_path, terminal_path = (
        localizar_projeto()
    )

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

    if "P10 — NOVA ABA SISTEMA" in terminal_original:
        print("O P10 já parece ter sido aplicado.")
        return

    inicio = dashboard_original.find(
        "class PaginaSistema(QWidget):\n"
    )
    fim = dashboard_original.find(
        "class PaginaModulo(QWidget):\n",
        inicio,
    )

    if inicio < 0 or fim < 0:
        raise RuntimeError(
            "Não encontrei a PaginaSistema atual."
        )

    dashboard_novo = (
        dashboard_original[:inicio]
        + CLASSES_P10
        + dashboard_original[fim:]
    )

    validar_dashboard(dashboard_novo)

    compile(
        dashboard_novo,
        str(dashboard_path),
        "exec",
    )

    ancora = (
        "                #pageTitle "
        "{{ font-size: 28px; "
    )

    if ancora not in terminal_original:
        raise RuntimeError(
            "Não encontrei a âncora de estilos."
        )

    terminal_novo = terminal_original.replace(
        ancora,
        CSS_P10 + ancora,
        1,
    )

    compile(
        terminal_novo,
        str(terminal_path),
        "exec",
    )

    backup_dashboard = dashboard_path.with_name(
        "dashboard.py.sistema_p10.bak"
    )
    backup_terminal = terminal_path.with_name(
        "terminal_laylay_2.py.sistema_p10.bak"
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
        dashboard_novo,
        encoding="utf-8",
    )
    terminal_path.write_text(
        terminal_novo,
        encoding="utf-8",
    )

    print()
    print("P10 — NOVA ABA SISTEMA APLICADA")
    print("--------------------------------")
    print(f"Projeto: {raiz}")
    print()
    print("Alterado:")
    print("  ✓ cabeçalho Sistema")
    print("  ✓ Resumo do sistema")
    print("  ✓ Desempenho em tempo real")
    print("  ✓ CPU / GPU / RAM / VRAM")
    print("  ✓ Rede / Disco")
    print("  ✓ download e upload")
    print("  ✓ coleta existente preservada")
    print()
    print("Backups:")
    print(f"  {backup_dashboard}")
    print(f"  {backup_terminal}")


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:
        print()
        print("ERRO:")
        print(erro)
        raise
