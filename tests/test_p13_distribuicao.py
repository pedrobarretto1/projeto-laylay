from __future__ import annotations

from pathlib import Path

from empacotamento.verificar_pacote import auditar_pacote, auditar_versionamento
from memoria_sqlite import MemoriaSQLite
from mente_laylay.integracao.smoke_distribuicao import executar_smoke_distribuicao


def _pacote_minimo(tmp_path: Path, *, com_modelo: bool = True) -> Path:
    pacote = tmp_path / "Laylay"
    pacote.mkdir()
    for nome in (
        "Laylay.exe",
        "AvatarLaylay.exe",
        "Iniciar Laylay.exe",
        "README_PORTATIL.md",
        "LICENCAS_TERCEIROS.md",
    ):
        (pacote / nome).write_bytes(b"MZ" if nome.endswith(".exe") else b"texto seguro")
    (pacote / "configuracao.env").write_text(
        "LAYLAY_LLM_BACKEND=portatil\n"
        "GROQ_API_KEY=\nGMAIL_USER=\nGMAIL_APP_PASSWORD=\n"
        "LAYLAY_IOT_MODO=simulado\nIOT_CONTROLE_FISICO_AUTORIZADO=NAO\n",
        encoding="utf-8",
    )
    (pacote / "avatar").mkdir()
    (pacote / "memoria").mkdir()
    servidor = pacote / "runtime_llm" / "cpu" / "llama-server.exe"
    servidor.parent.mkdir(parents=True)
    servidor.write_bytes(b"MZ")
    extensao = pacote / "extensao_chrome"
    extensao.mkdir()
    (extensao / "manifest.json").write_text("{}", encoding="utf-8")
    if com_modelo:
        modelos = pacote / "modelos"
        modelos.mkdir()
        (modelos / "laylay.gguf").write_bytes(b"GGUF")
    return pacote


def test_auditoria_aceita_pacote_limpo_e_completo(tmp_path: Path) -> None:
    relatorio = auditar_pacote(_pacote_minimo(tmp_path))

    assert relatorio["status"] == "ok"
    assert relatorio["modelo_incluido"] is True
    assert relatorio["memorias"] == 0
    assert relatorio["arquivos_privados"] == []


def test_auditoria_recusa_memoria_credencial_e_caminho_pessoal(tmp_path: Path) -> None:
    pacote = _pacote_minimo(tmp_path)
    (pacote / "memoria" / "conversa.txt").write_text("segredo pessoal", encoding="utf-8")
    (pacote / "devices.json").write_text("{}", encoding="utf-8")
    (pacote / "configuracao.env").write_text(
        "GROQ_API_KEY=segredo\nIOT_CONTROLE_FISICO_AUTORIZADO=SIM\n",
        encoding="utf-8",
    )
    (pacote / "README_PORTATIL.md").write_text(
        r"C:\Users\usuario-real\Downloads\Laylay", encoding="utf-8",
    )

    relatorio = auditar_pacote(pacote)

    assert relatorio["status"] == "falha"
    problemas = " ".join(relatorio["problemas"])
    assert "memória pessoal" in problemas
    assert "arquivos privados" in problemas
    assert "credenciais preenchidas" in problemas
    assert "IoT físico" in problemas
    assert "caminhos pessoais" in problemas


def test_pacote_sem_modelo_degrada_quando_explicitamente_permitido(tmp_path: Path) -> None:
    pacote = _pacote_minimo(tmp_path, com_modelo=False)

    rigoroso = auditar_pacote(pacote)
    degradado = auditar_pacote(pacote, exigir_modelo=False)

    assert rigoroso["status"] == "falha"
    assert degradado["status"] == "ok"
    assert degradado["avisos"] == ["modelo GGUF ausente; conversa local ficará degradada"]


def test_smoke_valida_componentes_sem_ollama_nem_rede(tmp_path: Path) -> None:
    pacote = _pacote_minimo(tmp_path, com_modelo=False)

    resultado = executar_smoke_distribuicao(
        pacote,
        ambiente={
            "LAYLAY_LLM_BACKEND": "portatil",
            "LAYLAY_SMOKE_EXIGIR_MODELO": "0",
        },
    )

    assert resultado["status"] == "ok"
    assert set(resultado["capacidades"].values()) == {"disponivel"}
    assert resultado["memoria_gravavel"] is True
    assert resultado["llm"] == {
        "backend": "portatil",
        "motor_presente": True,
        "modelo_presente": False,
        "degradacao_sem_ollama": True,
    }


def test_memoria_legada_json_migra_em_instalacao_nova(tmp_path: Path) -> None:
    pasta_memoria = tmp_path / "memoria"
    pasta_memoria.mkdir()
    legado = pasta_memoria / "laylay_memoria.json"
    legado.write_text(
        '{"resumo_conversa": "contexto migrado", "current_emotion": "feliz"}',
        encoding="utf-8",
    )

    memoria = MemoriaSQLite(str(pasta_memoria / "laylay_memoria.sqlite"))
    carregado = memoria.carregar_estado()

    assert carregado["resumo_conversa"] == "contexto migrado"
    assert carregado["current_emotion"] == "feliz"


def test_versionamento_real_nao_rastreia_dados_privados() -> None:
    raiz = Path(__file__).resolve().parents[1]

    relatorio = auditar_versionamento(raiz)

    assert relatorio["status"] == "ok"
    assert relatorio["proibidos"] == []


def test_build_limpa_saida_anterior_e_separa_memoria_de_credenciais() -> None:
    raiz = Path(__file__).resolve().parents[1]
    script = (raiz / "empacotamento" / "build_portatil.ps1").read_text(encoding="utf-8")

    assert "Remove-Item -LiteralPath $Resolvido -Recurse -Force" in script
    bloco_memoria, bloco_privado = script.split("if ($IncluirConfiguracoesPrivadas) {", 1)
    assert 'foreach ($Arquivo in @("playlists.json"))' in bloco_memoria
    assert "devices.json" not in bloco_memoria.split("if ($IncluirMemoriaPessoal) {", 1)[1]
    assert '"devices.json", "tinytuya.json", "snapshot.json", "tuya-raw.json"' in bloco_privado
    assert "verificar_pacote.py" in script
    assert "LAYLAY_SMOKE_DISTRIBUICAO" in script
