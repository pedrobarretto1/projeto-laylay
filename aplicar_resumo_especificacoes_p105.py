from __future__ import annotations

import ast
import shutil
from pathlib import Path


CSS_RAW = r'''
/* =========================================
   P10.5 — RESUMO COM ESPECIFICAÇÕES REAIS
   ========================================= */

#systemSpecRow {
    background: transparent;
    border: 0;
    border-bottom: 1px solid #252C33;
    min-height: 42px;
}

#systemSpecIcon {
    background: #171C21;
    border: 1px solid #2A3138;
    border-radius: 7px;
    color: #AEB5BC;
    font-size: 12px;
    font-weight: 700;
}

#systemSpecTitle {
    background: transparent;
    border: 0;
    color: #9BA2AA;
    font-size: 9px;
    font-weight: 650;
}

#systemSpecValue {
    background: transparent;
    border: 0;
    color: #F2EEF0;
    font-size: 10px;
    font-weight: 720;
}

#systemSpecDetail {
    background: transparent;
    border: 0;
    color: #777F88;
    font-size: 8px;
    font-weight: 600;
}

#systemSectionCard[summaryCard="true"] {
    background: #11161B;
    border: 1px solid #282F36;
    border-radius: 14px;
}
'''


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
            arquivos = {
                "gpu": raiz / "mente_laylay" / "percepcao" / "telemetria_gpu.py",
                "dashboard_runtime": raiz / "mente_laylay" / "integracao" / "dashboard_terminal.py",
                "bridge": raiz / "mente_laylay" / "integracao" / "desktop_bridge.py",
                "dashboard_ui": raiz / "cliente" / "terminal_2" / "dashboard.py",
                "terminal": raiz / "cliente" / "terminal_laylay_2.py",
            }
            if all(
                caminho.is_file()
                for caminho in arquivos.values()
            ):
                return raiz.resolve(), {
                    chave: caminho.resolve()
                    for chave, caminho in arquivos.items()
                }

    raise FileNotFoundError(
        "Não encontrei a estrutura atual do projeto Laylay."
    )


def substituir_uma_vez(
    texto: str,
    antigo: str,
    novo: str,
    descricao: str,
) -> str:
    if antigo not in texto:
        raise RuntimeError(
            f"Não encontrei a âncora: {descricao}"
        )
    return texto.replace(
        antigo,
        novo,
        1,
    )


def validar_python(
    caminho: Path,
    texto: str,
) -> None:
    compile(
        texto,
        str(caminho),
        "exec",
    )
    ast.parse(texto)


def patch_gpu(texto: str) -> str:
    if "P10.5 — metadados estáticos de GPU" in texto:
        return texto

    cache_antigo = '''        self._cache: dict[str, Any] = {
            "gpu_percent": None,
            "vram_percent": None,
            "source": "",
        }
'''
    cache_novo = '''        self._cache: dict[str, Any] = {
            "gpu_percent": None,
            "vram_percent": None,
            "gpu_name": "",
            "driver_version": "",
            "vram_total_mb": None,
            "source": "",
        }
        # P10.5 — metadados estáticos de GPU.
        # Coletados uma vez e reaproveitados.
        self._metadata_cache: dict[str, Any] = {
            "gpu_name": "",
            "driver_version": "",
            "vram_total_mb": None,
        }
'''
    texto = substituir_uma_vez(
        texto,
        cache_antigo,
        cache_novo,
        "cache da GPU",
    )

    retorno_antigo = '''        return {**escolhido, "source": "nvidia-smi"}

    def _coletar_windows(self) -> dict[str, Any]:
'''
    retorno_novo = '''        metadata = self._coletar_nvidia_metadata(
            executavel
        )
        return {
            **escolhido,
            **metadata,
            "source": "nvidia-smi",
        }

    def _coletar_nvidia_metadata(
        self,
        executavel: str,
    ) -> dict[str, Any]:
        if self._metadata_cache.get("gpu_name"):
            return deepcopy(
                self._metadata_cache
            )

        try:
            resultado = self.run(
                [
                    executavel,
                    "--query-gpu=name,driver_version,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=1.2,
                check=False,
            )
        except Exception:
            return deepcopy(
                self._metadata_cache
            )

        if int(
            getattr(
                resultado,
                "returncode",
                1,
            )
        ) != 0:
            return deepcopy(
                self._metadata_cache
            )

        candidatos: list[
            dict[str, Any]
        ] = []

        for linha in str(
            getattr(
                resultado,
                "stdout",
                "",
            )
            or ""
        ).splitlines():
            partes = [
                parte.strip()
                for parte in linha.split(",")
            ]
            if len(partes) != 3:
                continue

            nome = str(
                partes[0] or ""
            ).strip()[:160]
            driver = str(
                partes[1] or ""
            ).strip()[:80]
            total = _numero_positivo(
                partes[2]
            )

            if nome:
                candidatos.append(
                    {
                        "gpu_name": nome,
                        "driver_version": driver,
                        "vram_total_mb": total,
                    }
                )

        if candidatos:
            escolhido = max(
                candidatos,
                key=lambda item: float(
                    item.get(
                        "vram_total_mb"
                    )
                    or 0.0
                ),
            )
            self._metadata_cache = dict(
                escolhido
            )

        return deepcopy(
            self._metadata_cache
        )

    def _coletar_windows(self) -> dict[str, Any]:
'''
    texto = substituir_uma_vez(
        texto,
        retorno_antigo,
        retorno_novo,
        "retorno NVIDIA",
    )
    return texto


def patch_dashboard_runtime(
    texto: str,
) -> str:
    if "P10.5 — especificações reais do sistema" in texto:
        return texto

    texto = substituir_uma_vez(
        texto,
        "import os\nimport re\n",
        "import os\nimport platform\nimport re\n",
        "imports do dashboard runtime",
    )

    texto = substituir_uma_vez(
        texto,
        '''        self._falhas = 0
        self._fontes_pendentes: dict[
''',
        '''        self._falhas = 0
        # P10.5 — especificações reais do sistema.
        # Inventário estático coletado uma vez.
        self._system_info_cache: dict[str, Any] = {}
        self._fontes_pendentes: dict[
''',
        "cache das especificações",
    )

    metodo = r'''
    @staticmethod
    def _capacidade_bytes(
        valor: Any,
    ) -> str:
        try:
            total = max(
                0.0,
                float(valor),
            )
        except (
            TypeError,
            ValueError,
        ):
            return "—"

        if total <= 0:
            return "—"

        gib = total / (1024 ** 3)

        if gib >= 1024:
            texto = (
                f"{gib / 1024:.1f} TB"
            )
            return texto.replace(
                ".0 TB",
                " TB",
            )

        return f"{gib:.0f} GB"

    def _info_sistema(
        self,
        gpu: Mapping[str, Any],
        raiz: str,
    ) -> dict[str, Any]:
        if not self._system_info_cache:
            sistema = str(
                platform.system() or ""
            ).strip()
            arquitetura = str(
                platform.machine() or ""
            ).strip()

            arquitetura_rotulo = (
                "64-bit"
                if "64" in arquitetura
                else arquitetura or "—"
            )

            if sistema.casefold() == "windows":
                versao_bruta = str(
                    platform.version() or ""
                )
                try:
                    build = int(
                        versao_bruta.split(
                            "."
                        )[-1]
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    build = 0

                versao = (
                    "11"
                    if build >= 22000
                    else str(
                        platform.release()
                        or ""
                    ).strip()
                )

                edicao = ""
                try:
                    edicao = str(
                        platform.win32_edition()
                        or ""
                    ).strip()
                except Exception:
                    edicao = ""

                if edicao.casefold().startswith(
                    "professional"
                ):
                    edicao = "Pro"

                partes_so = [
                    f"Windows {versao}".strip(),
                    edicao,
                    arquitetura_rotulo,
                ]
                sistema_operacional = " ".join(
                    parte
                    for parte in partes_so
                    if parte
                    and parte != "—"
                )
            else:
                sistema_operacional = " ".join(
                    parte
                    for parte in (
                        sistema,
                        str(
                            platform.release()
                            or ""
                        ).strip(),
                        arquitetura_rotulo,
                    )
                    if parte
                    and parte != "—"
                )

            cpu_nome = str(
                platform.processor()
                or ""
            ).strip()

            if os.name == "nt":
                try:
                    import winreg

                    with winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
                    ) as chave:
                        (
                            cpu_registro,
                            _,
                        ) = winreg.QueryValueEx(
                            chave,
                            "ProcessorNameString",
                        )

                    if str(
                        cpu_registro
                        or ""
                    ).strip():
                        cpu_nome = str(
                            cpu_registro
                        ).strip()
                except Exception:
                    pass

            if not cpu_nome:
                cpu_nome = str(
                    os.environ.get(
                        "PROCESSOR_IDENTIFIER",
                        "",
                    )
                ).strip()

            try:
                fisicos = self.psutil.cpu_count(
                    logical=False
                )
            except Exception:
                fisicos = None

            try:
                logicos = self.psutil.cpu_count(
                    logical=True
                )
            except Exception:
                logicos = None

            detalhes_cpu = []
            if fisicos:
                detalhes_cpu.append(
                    f"{int(fisicos)} núcleos"
                )
            if logicos:
                detalhes_cpu.append(
                    f"{int(logicos)} threads"
                )

            try:
                ram_total = (
                    self.psutil
                    .virtual_memory()
                    .total
                )
            except Exception:
                ram_total = 0

            try:
                disco_total = (
                    self.psutil
                    .disk_usage(raiz)
                    .total
                )
            except Exception:
                disco_total = 0

            self._system_info_cache = {
                "os": {
                    "value": _texto(
                        sistema_operacional,
                        160,
                    )
                    or "—",
                    "detail": "",
                },
                "cpu": {
                    "value": _texto(
                        cpu_nome,
                        180,
                    )
                    or "—",
                    "detail": " / ".join(
                        detalhes_cpu
                    ),
                },
                "gpu": {
                    "value": "—",
                    "detail": "",
                },
                "ram": {
                    "value": self._capacidade_bytes(
                        ram_total
                    ),
                    "detail": "Memória física",
                },
                "vram": {
                    "value": "—",
                    "detail": "",
                },
                "disk": {
                    "value": self._capacidade_bytes(
                        disco_total
                    ),
                    "detail": "Unidade do sistema",
                },
            }

        info = deepcopy(
            self._system_info_cache
        )

        gpu_nome = _texto(
            gpu.get("gpu_name"),
            180,
        )
        driver = _texto(
            gpu.get("driver_version"),
            80,
        )

        if gpu_nome:
            info["gpu"] = {
                "value": gpu_nome,
                "detail": (
                    f"Driver {driver}"
                    if driver
                    else ""
                ),
            }

        try:
            vram_mb = float(
                gpu.get("vram_total_mb")
            )
        except (
            TypeError,
            ValueError,
        ):
            vram_mb = 0.0

        if vram_mb > 0:
            gib = vram_mb / 1024.0
            valor_vram = (
                f"{gib:.1f} GB"
            ).replace(
                ".0 GB",
                " GB",
            )
            info["vram"] = {
                "value": valor_vram,
                "detail": "Memória dedicada",
            }

        return info

'''
    ancora = (
        "    def _sistema("
        "self, agora: float, anterior: Mapping[str, Any]"
        ") -> dict[str, Any]:\n"
    )
    if ancora not in texto:
        raise RuntimeError(
            "Não encontrei _sistema()."
        )

    texto = texto.replace(
        ancora,
        metodo + ancora,
        1,
    )

    texto = substituir_uma_vez(
        texto,
        '''        return {
            "cpu_percent": self._metrica(
''',
        '''        return {
            "info": self._info_sistema(
                gpu,
                raiz,
            ),
            "cpu_percent": self._metrica(
''',
        "payload system.info",
    )

    return texto


def patch_bridge(texto: str) -> str:
    if "P10.5 — allowlist de especificações" in texto:
        return texto

    helper = r'''
# P10.5 — allowlist de especificações públicas do computador.
def _info_sistema_dashboard(
    valor: Any,
) -> dict[str, dict[str, str]]:
    bruto = (
        dict(valor)
        if isinstance(
            valor,
            Mapping,
        )
        else {}
    )

    resultado: dict[
        str,
        dict[str, str],
    ] = {}

    for chave in (
        "os",
        "cpu",
        "gpu",
        "ram",
        "vram",
        "disk",
    ):
        item = (
            dict(
                bruto.get(chave)
                or {}
            )
            if isinstance(
                bruto.get(chave),
                Mapping,
            )
            else {}
        )

        resultado[chave] = {
            "value": _texto_publico_dashboard(
                item.get("value"),
                180,
                fallback="—",
            ),
            "detail": _texto_publico_dashboard(
                item.get("detail"),
                120,
                fallback="",
            ),
        }

    return resultado


'''
    ancora = "def sanitizar_dashboard_estado(\n"

    if ancora not in texto:
        raise RuntimeError(
            "Não encontrei sanitizar_dashboard_estado()."
        )

    texto = texto.replace(
        ancora,
        helper + ancora,
        1,
    )

    texto = substituir_uma_vez(
        texto,
        '''        "system": {
            "cpu_percent": _metrica_dashboard(
''',
        '''        "system": {
            "info": _info_sistema_dashboard(
                sistema.get("info")
            ),
            "cpu_percent": _metrica_dashboard(
''',
        "allowlist system.info",
    )

    return texto


def patch_dashboard_ui(
    texto: str,
) -> str:
    if "class LinhaResumoSistema(QFrame):" in texto:
        return texto

    classe = r'''
class LinhaResumoSistema(QFrame):
    # Linha visual para uma especificação estática.

    def __init__(
        self,
        icone: str,
        titulo: str,
    ) -> None:
        super().__init__()
        self.setObjectName(
            "systemSpecRow"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            8, 6, 8, 6
        )
        layout.setSpacing(8)

        simbolo = QLabel(icone)
        simbolo.setObjectName(
            "systemSpecIcon"
        )
        simbolo.setFixedSize(
            24, 24
        )
        simbolo.setAlignment(
            Qt.AlignCenter
        )

        nome = QLabel(titulo)
        nome.setObjectName(
            "systemSpecTitle"
        )

        textos = QVBoxLayout()
        textos.setContentsMargins(
            0, 0, 0, 0
        )
        textos.setSpacing(1)

        self.valor = QLabel("—")
        self.valor.setObjectName(
            "systemSpecValue"
        )
        self.valor.setWordWrap(True)
        self.valor.setAlignment(
            Qt.AlignRight
            | Qt.AlignVCenter
        )

        self.detalhe = QLabel("")
        self.detalhe.setObjectName(
            "systemSpecDetail"
        )
        self.detalhe.setWordWrap(True)
        self.detalhe.setAlignment(
            Qt.AlignRight
            | Qt.AlignVCenter
        )
        self.detalhe.hide()

        textos.addWidget(
            self.valor
        )
        textos.addWidget(
            self.detalhe
        )

        layout.addWidget(
            simbolo
        )
        layout.addWidget(
            nome
        )
        layout.addStretch()
        layout.addLayout(
            textos,
            1,
        )

    def definir(
        self,
        valor: str,
        detalhe: str = "",
    ) -> None:
        valor = str(
            valor or "—"
        ).strip() or "—"
        detalhe = str(
            detalhe or ""
        ).strip()

        self.valor.setText(
            valor
        )
        self.detalhe.setText(
            detalhe
        )
        self.detalhe.setVisible(
            bool(detalhe)
        )


'''
    ancora = "class MiniMetricaSistema(QFrame):\n"

    if ancora not in texto:
        raise RuntimeError(
            "Não encontrei MiniMetricaSistema."
        )

    texto = texto.replace(
        ancora,
        classe + ancora,
        1,
    )

    inicio = texto.find(
        '        self.resumo = CartaoDashboard(\n'
        '            "Resumo do sistema"\n'
    )
    fim = texto.find(
        "        desempenho = CartaoDashboard(\n",
        inicio,
    )

    if inicio < 0 or fim < 0:
        raise RuntimeError(
            "Não encontrei o bloco atual do resumo."
        )

    resumo_novo = r'''        self.resumo = CartaoDashboard(
            "Resumo do sistema"
        )
        self.resumo.setObjectName(
            "systemSectionCard"
        )
        self.resumo.setProperty(
            "summaryCard",
            True,
        )
        self.resumo.setMinimumWidth(315)
        self.resumo.setMaximumWidth(390)
        self.resumo.layout_principal.setSpacing(
            0
        )

        self.resumo_linhas: dict[
            str, LinhaResumoSistema
        ] = {}

        for chave, icone, rotulo in (
            ("os", "⊞", "Sistema operacional"),
            ("cpu", "◉", "CPU"),
            ("gpu", "▱", "GPU"),
            ("ram", "▤", "RAM"),
            ("vram", "▧", "VRAM"),
            ("disk", "▰", "Disco principal"),
            ("uptime", "◷", "Uptime"),
            ("temperature", "♨", "Temperatura média"),
        ):
            linha = LinhaResumoSistema(
                icone,
                rotulo,
            )
            self.resumo_linhas[
                chave
            ] = linha
            self.resumo.layout_principal.addWidget(
                linha
            )

'''

    texto = (
        texto[:inicio]
        + resumo_novo
        + texto[fim:]
    )

    texto = texto.replace(
        '''                self.resumo_valores[
                    chave
                ].setText("—")
''',
        "",
    )

    texto = texto.replace(
        '''            self.resumo_valores[
                chave
            ].setText(texto)
''',
        "",
    )

    texto = texto.replace(
        '''                self.resumo_valores[
                    chave
                ].text()
''',
        '''                self.valores[
                    chave
                ].text()
''',
    )

    ancora_specs = '''        # P10.1 — replica somente métricas confirmadas
        # para o card de armazenamento/memória.
'''

    if ancora_specs not in texto:
        raise RuntimeError(
            "Não encontrei o ponto de atualização do resumo."
        )

    atualizar_specs = r'''        info_sistema = (
            sistema.get("info")
            if isinstance(
                sistema.get("info"),
                dict,
            )
            else {}
        )

        for chave in (
            "os",
            "cpu",
            "gpu",
            "ram",
            "vram",
            "disk",
        ):
            item = (
                info_sistema.get(chave)
                if isinstance(
                    info_sistema.get(chave),
                    dict,
                )
                else {}
            )
            self.resumo_linhas[
                chave
            ].definir(
                str(
                    item.get("value")
                    or "—"
                ),
                str(
                    item.get("detail")
                    or ""
                ),
            )

        self.resumo_linhas[
            "uptime"
        ].definir(
            _texto_metrica(
                sistema.get(
                    "uptime_seconds"
                ),
                uptime=True,
            )
        )

        self.resumo_linhas[
            "temperature"
        ].definir(
            _texto_metrica(
                sistema.get(
                    "temperature_c"
                )
            )
        )

'''

    texto = texto.replace(
        ancora_specs,
        atualizar_specs + ancora_specs,
        1,
    )

    inicio_status = texto.find(
        '''        self.temperatura.setText(
            "Temperatura · "
'''
    )
    fim_status = texto.find(
        "\n    def invalidar(self) -> None:\n",
        inicio_status,
    )

    if inicio_status < 0 or fim_status < 0:
        raise RuntimeError(
            "Não encontrei o status antigo do resumo."
        )

    novo_status = r'''        if ausentes:
            self.atualizacao.setText(
                "Atualização parcial"
            )
        else:
            self.atualizacao.setText(
                "Atualizado agora"
            )
'''

    texto = (
        texto[:inicio_status]
        + novo_status
        + texto[fim_status:]
    )

    texto = texto.replace(
        '''            self.resumo_valores[
                chave
            ].setText("—")
''',
        "",
    )

    ancora_invalidar = '''    def invalidar(self) -> None:
        for chave in self.valores:
'''

    if ancora_invalidar not in texto:
        raise RuntimeError(
            "Não encontrei invalidar()."
        )

    texto = texto.replace(
        ancora_invalidar,
        '''    def invalidar(self) -> None:
        for linha in self.resumo_linhas.values():
            linha.definir("—")

        for chave in self.valores:
''',
        1,
    )

    texto = texto.replace(
        '''        self.temperatura.setText(
            "Temperatura · —"
        )
        self.uptime.setText(
            "Tempo ligado · —"
        )

''',
        "",
        1,
    )

    bloco_estado_antigo = '''        self.estado.setText(
            "Aguardando telemetria"
        )
        self.estado.setProperty(
            "state",
            "pending",
        )
        self.atualizacao.setText(
            "Aguardando telemetria"
        )

        self.estado.style().unpolish(
            self.estado
        )
        self.estado.style().polish(
            self.estado
        )
'''

    if bloco_estado_antigo in texto:
        texto = texto.replace(
            bloco_estado_antigo,
            '''        self.atualizacao.setText(
            "Aguardando telemetria"
        )
''',
            1,
        )

    # Se o P10.4.1 responsivo já estiver localmente aplicado,
    # atualiza a largura restaurada no breakpoint grande.
    texto = texto.replace(
        '''            self.resumo.setMinimumWidth(275)
            self.resumo.setMaximumWidth(355)
''',
        '''            self.resumo.setMinimumWidth(315)
            self.resumo.setMaximumWidth(390)
''',
        1,
    )

    return texto


def patch_terminal(texto: str) -> str:
    if (
        "P10.5 — RESUMO COM ESPECIFICAÇÕES REAIS"
        in texto
    ):
        return texto

    css = (
        CSS_RAW
        .replace("{", "{{")
        .replace("}", "}}")
    )

    ancora = (
        "                #pageTitle "
        "{{ font-size: 28px; "
    )

    if ancora not in texto:
        raise RuntimeError(
            "Não encontrei a âncora CSS."
        )

    return texto.replace(
        ancora,
        css + ancora,
        1,
    )


def main() -> None:
    raiz, arquivos = localizar_projeto()

    originais = {
        chave: caminho.read_text(
            encoding="utf-8"
        )
        for chave, caminho
        in arquivos.items()
    }

    novos = {
        "gpu": patch_gpu(
            originais["gpu"]
        ),
        "dashboard_runtime": patch_dashboard_runtime(
            originais["dashboard_runtime"]
        ),
        "bridge": patch_bridge(
            originais["bridge"]
        ),
        "dashboard_ui": patch_dashboard_ui(
            originais["dashboard_ui"]
        ),
        "terminal": patch_terminal(
            originais["terminal"]
        ),
    }

    # Validação completa antes de escrever qualquer arquivo.
    for chave, texto in novos.items():
        validar_python(
            arquivos[chave],
            texto,
        )

    backups = {}

    for chave, caminho in arquivos.items():
        backup = caminho.with_name(
            caminho.name + ".p105.bak"
        )
        shutil.copy2(
            caminho,
            backup,
        )
        backups[chave] = backup

    for chave, texto in novos.items():
        arquivos[chave].write_text(
            texto,
            encoding="utf-8",
        )

    print()
    print("P10.5 — RESUMO DO SISTEMA REFINADO")
    print("-----------------------------------")
    print(f"Projeto: {raiz}")
    print()
    print("Resumo agora mostra:")
    print("  ✓ Sistema operacional")
    print("  ✓ CPU + núcleos/threads")
    print("  ✓ GPU + driver")
    print("  ✓ RAM total")
    print("  ✓ VRAM total")
    print("  ✓ Disco principal / capacidade")
    print("  ✓ Uptime")
    print("  ✓ Temperatura")
    print()
    print("Uso percentual ficou somente em:")
    print("  ✓ Desempenho em tempo real")
    print("  ✓ Armazenamento e memória")
    print()
    print(
        "Nenhuma especificação de DDR, velocidade "
        "da RAM, tipo NVMe/SSD ou saúde do disco "
        "é inventada quando não houver fonte confiável."
    )
    print()
    print("Backups:")
    for backup in backups.values():
        print(f"  {backup}")


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:
        print()
        print("ERRO:")
        print(erro)
        raise
