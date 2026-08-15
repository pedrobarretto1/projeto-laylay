#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0.2A v3.1 — preservação de subtipo navegador e repetição explícita de alvo.

Aplica uma correção estreita e reversível. Não inicia a Laylay e não executa
ações reais de abrir/fechar navegador; os testes embutidos são puramente locais.
"""

from __future__ import annotations

import argparse
import ast
import shutil
import subprocess
import sys
import time
from pathlib import Path

MARCADOR = "P0_NAVEGADOR_SUBTIPO_V3_1_20260815"

ARQUIVOS = {
    "contexto": Path("mente_laylay/memoria_mental/contexto_imediato.py"),
    "comandos": Path("mente_laylay/autonomia/comandos_imediatos.py"),
    "roteador": Path("mente_laylay/autonomia/roteador_deterministico.py"),
    "seletor": Path("mente_laylay/cognicao/seletor_contexto.py"),
    "teste": Path("tests/test_p0_2a_navegador_v3_1.py"),
}

CONTEXTO_ANTIGO = 'def _dominio_restrito_referencia(\n    texto: str,\n    estado: Dict[str, Any] | None,\n    *,\n    ttl_s: float = 300.0,\n) -> str:\n    explicito = _dominio_explicito_referencia(texto)\n    if explicito:\n        return explicito\n    if not _texto_referencia_curta_operacional(texto):\n        return ""\n    return _dominio_ativo_referencia(estado, ttl_s=ttl_s)\n'
CONTEXTO_NOVO = 'def _dominio_contrato_referencia(\n    estado: Dict[str, Any] | None,\n    *,\n    ttl_s: float = 300.0,\n) -> str:\n    """Retorna o domínio da última ação confirmada, se ela ainda for recente.\n\n    P0_NAVEGADOR_SUBTIPO_V3_1_20260815\n    Em referências curtas, o contrato operacional observado é evidência mais\n    forte que a janela física atualmente percebida. Assim, depois de OPEN_URL,\n    ``fecha essa`` continua sendo site/aba mesmo que o SO enxergue Opera.exe.\n    """\n    mente = dict(estado or {})\n    contrato = (\n        dict(mente.get("ultima_acao_contrato") or {})\n        if isinstance(mente.get("ultima_acao_contrato"), dict)\n        else {}\n    )\n    if not contrato:\n        return ""\n\n    try:\n        ts = float(mente.get("ultima_acao_ts") or 0.0)\n    except (TypeError, ValueError):\n        return ""\n    if not ts or time.time() - ts > ttl_s:\n        return ""\n\n    if contrato.get("executou") is not True or contrato.get("confirmado") is not True:\n        return ""\n\n    dominio = _normalizar_dominio_referencia(\n        str(contrato.get("dominio") or "")\n    )\n    if not dominio:\n        dominio = _dominio_intent_contextual(\n            str(contrato.get("intent") or "")\n        )\n    return dominio if dominio in _DOMINIOS_INTENT_CONTEXTO else ""\n\n\ndef _dominio_restrito_referencia(\n    texto: str,\n    estado: Dict[str, Any] | None,\n    *,\n    ttl_s: float = 300.0,\n) -> str:\n    explicito = _dominio_explicito_referencia(texto)\n    if explicito:\n        return explicito\n    if not _texto_referencia_curta_operacional(texto):\n        return ""\n\n    # P0_NAVEGADOR_SUBTIPO_V3_1_20260815\n    # Para dêiticos curtos, a última ação confirmada vence percepção/foco.\n    dominio_contrato = _dominio_contrato_referencia(estado, ttl_s=ttl_s)\n    if dominio_contrato:\n        return dominio_contrato\n    return _dominio_ativo_referencia(estado, ttl_s=ttl_s)\n'

CONTEXTO_CONTRATO_INTENTS_ANTIGO = '        and intent_contrato in {"OPEN_URL", "APP_OPEN", "MAXIMIZE_WINDOW"}\n'
CONTEXTO_CONTRATO_INTENTS_NOVO = '        and intent_contrato in {"OPEN_URL", "SWITCH_PREVIOUS_TAB", "APP_OPEN", "MAXIMIZE_WINDOW"}\n'
CONTEXTO_TIPO_CONTRATO_ANTIGO = '            tipo_contrato = "site" if intent_contrato == "OPEN_URL" else "app"\n'
CONTEXTO_TIPO_CONTRATO_NOVO = '            tipo_contrato = (\n                "site"\n                if intent_contrato in {"OPEN_URL", "SWITCH_PREVIOUS_TAB"}\n                else "app"\n            )\n'
CONTEXTO_SITE_RECENTE_ANTIGO = '    if ultima_acao_promovivel and ultima_intencao in {"OPEN_URL", "CLOSE_TAB", "SITE_ENTER"}:\n'
CONTEXTO_SITE_RECENTE_NOVO = '    if ultima_acao_promovivel and ultima_intencao in {"OPEN_URL", "CLOSE_TAB", "SWITCH_PREVIOUS_TAB", "SITE_ENTER"}:\n'

SELETOR_ANTIGO = '        r"\\b(?:ele|ela|isso|esse|essa|dele|dela|como assim|o que aconteceu|tipo o que|e depois|"\n        r"tem certeza|entao voce|então você|mas voce|mas você)\\b",\n'
SELETOR_NOVO = '        # P0_NAVEGADOR_SUBTIPO_V3_1_20260815\n        r"\\b(?:ele|ela|isso|esse|essa|dele|dela|anterior|de antes|como assim|o que aconteceu|tipo o que|e depois|"\n        r"tem certeza|entao voce|então você|mas voce|mas você)\\b",\n'
COMANDOS_INSERIR_ANTES = 'def segmentar_composto_caixa_agenda(texto: str) -> tuple[str, str] | None:\n'
COMANDOS_HELPER = 'def texto_referencia_tipificada_prioritaria(texto: str) -> bool:\n    """Molduras curtas que exigem resolver o referente antes de executar.\n\n    P0_NAVEGADOR_SUBTIPO_V3_1_20260815\n    A função só reconhece formas estreitas já suportadas pelo resolvedor\n    contextual; ela não cria intents nem concede autorização.\n    """\n    t = _texto_normalizado_local(texto).strip(" .,!?:;")\n    referencia_direta = bool(re.fullmatch(\n        r"(?:(?:fecha|feche|fechar)|(?:tenta\\s+)?(?:abre|abra|abrir))\\s+"\n        r"(?:ele|ela|isso|esse|essa|este|esta|"\n        r"(?:esse|este|o)\\s+arquivo|"\n        r"(?:essa|esta|a)\\s+(?:aba|guia)|"\n        r"(?:esse|este|o)\\s+site)",\n        t,\n    ))\n    voltar_anterior = bool(re.fullmatch(\n        r"(?:volta|volte|retorna|retorne|vai)\\s+"\n        r"(?:(?:para|pra)\\s+)?(?:a\\s+)?anterior",\n        t,\n    ))\n    return referencia_direta or voltar_anterior\n\n\n'
COMANDOS_GATE_ANTIGO = '        texto_referencia = _texto_normalizado_local(texto).strip(" .,!?:;")\n        if re.fullmatch(\n            r"(?:(?:fecha|feche|fechar)|(?:tenta\\s+)?(?:abre|abra|abrir))\\s+"\n            r"(?:ele|ela|isso|esse|essa|este|esta|"\n            r"(?:esse|este|o)\\s+arquivo|"\n            r"(?:essa|esta|a)\\s+(?:aba|guia)|"\n            r"(?:esse|este|o)\\s+site)",\n            texto_referencia,\n        ):\n'
COMANDOS_GATE_NOVO = '        # P0_NAVEGADOR_SUBTIPO_V3_1_20260815\n        if texto_referencia_tipificada_prioritaria(texto):\n'
COMANDOS_INTENTS_ANTIGO = '                "CLOSE_TAB", "CLOSE_APP", "FILE_OPEN_RESULT", "OPEN_URL",\n                "MEDIA_CONTROL", "PLAYLIST_PLAY",\n'
COMANDOS_INTENTS_NOVO = '                "CLOSE_TAB", "CLOSE_APP", "FILE_OPEN_RESULT", "OPEN_URL",\n                "SWITCH_PREVIOUS_TAB", "MEDIA_CONTROL", "PLAYLIST_PLAY",\n'
ROTEADOR_ANTIGO = '    nome = re.sub(r"\\s+(agora|aqui|ai|aí|por favor|pfv)$", "", nome).strip()\n    nome = re.sub(r"^(o|a|os|as|um|uma)\\s+", "", nome).strip()\n'
ROTEADOR_NOVO = '    nome = re.sub(r"\\s+(agora|aqui|ai|aí|por favor|pfv)$", "", nome).strip()\n    # P0_NAVEGADOR_SUBTIPO_V3_1_20260815\n    # "de novo" descreve repetição da ação; não faz parte do nome do alvo.\n    nome = re.sub(\n        r"(?:^|\\s)(?:de\\s+novo|novamente|outra\\s+vez)$",\n        "",\n        nome,\n        flags=re.IGNORECASE,\n    ).strip()\n    nome = re.sub(r"^(o|a|os|as|um|uma)\\s+", "", nome).strip()\n'
TESTE = '# -*- coding: utf-8 -*-\n"""Regressões puras da P0.2A v3.1; nenhum executor real é chamado."""\n\nfrom __future__ import annotations\n\nimport re\nimport time\nimport unicodedata\nimport unittest\n\nfrom mente_laylay.autonomia.comandos_imediatos import (\n    texto_referencia_tipificada_prioritaria,\n)\nfrom mente_laylay.autonomia.roteador_deterministico import (\n    extrair_intencao_abrir_app,\n)\nfrom mente_laylay.cognicao.seletor_contexto import selecionar_contexto_turno\nfrom mente_laylay.memoria_mental.contexto_imediato import (\n    _dominio_restrito_referencia,\n    referencia_contextual_imediata,\n    resolver_comando_acao_geral_contextual,\n)\n\n\nclass P02ANavegadorV3Tests(unittest.TestCase):\n    @staticmethod\n    def _normalizar_teste(valor):\n        base = unicodedata.normalize(\n            "NFKD", str(valor or "").casefold()\n        )\n        sem_acentos = "".join(\n            ch for ch in base if not unicodedata.combining(ch)\n        )\n        sem_pontuacao = re.sub(r"[^a-z0-9\\s]", " ", sem_acentos)\n        return re.sub(r"\\s+", " ", sem_pontuacao).strip()\n\n    def _estado_site_com_percepcao_app(self):\n        agora = time.time()\n        return {\n            "ultima_acao_ts": agora,\n            "ultima_acao_contrato": {\n                "intent": "OPEN_URL",\n                "dominio": "site",\n                "executou": True,\n                "confirmado": True,\n                "alvo": "prime video",\n            },\n            "continuidade_geral": {\n                "dominio_ativo": "app",\n                "dominios": {\n                    "app": {\n                        "ativa": True,\n                        "ts": agora,\n                        "expira_em": agora + 300.0,\n                    },\n                    "site": {\n                        "ativa": True,\n                        "ts": agora - 1.0,\n                        "expira_em": agora + 300.0,\n                    },\n                },\n            },\n        }\n\n    def test_contrato_web_confirmado_vence_janela_fisica_em_deitico(self):\n        estado = self._estado_site_com_percepcao_app()\n        self.assertEqual(\n            _dominio_restrito_referencia("Fecha essa.", estado),\n            "site",\n        )\n        self.assertEqual(\n            _dominio_restrito_referencia("Volta para a anterior.", estado),\n            "site",\n        )\n\n    def test_alvo_app_explicito_continua_vencendo_contrato_web(self):\n        estado = self._estado_site_com_percepcao_app()\n        self.assertEqual(\n            _dominio_restrito_referencia("Fecha o Opera.", estado),\n            "app",\n        )\n\n    def test_resolvedor_site_materializa_operacoes_de_aba(self):\n        contexto = {\n            "tipo": "site",\n            "alvo": "prime video",\n            "intencao": "OPEN_URL",\n            "params": {"alvo": "prime video"},\n        }\n        anterior = resolver_comando_acao_geral_contextual(\n            "Volta para a anterior.",\n            contexto,\n        )\n        fechar = resolver_comando_acao_geral_contextual(\n            "Fecha essa.",\n            contexto,\n        )\n        self.assertEqual(anterior["intent"], "SWITCH_PREVIOUS_TAB")\n        self.assertEqual(fechar["intent"], "CLOSE_TAB")\n        self.assertEqual(fechar["params"]["alvo"], "prime video")\n\n    def test_troca_observada_vira_referente_do_fecha_essa(self):\n        agora = time.time()\n        rotulo_observado = "Wikipédia — pt.wikipedia.org"\n        estado = {\n            "ts": agora,\n            "ultima_acao_ts": agora,\n            "ultima_acao_intent": "SWITCH_PREVIOUS_TAB",\n            "ultima_intencao": "SWITCH_PREVIOUS_TAB",\n            "ultima_acao_params": {"referencia_contextual": True},\n            "ultima_acao_promovivel": True,\n            "ultima_acao_contrato": {\n                "intent": "SWITCH_PREVIOUS_TAB",\n                "dominio": "site",\n                "executou": True,\n                "confirmado": True,\n                "alvo": rotulo_observado,\n            },\n            # Mantém um site antigo e uma janela física concorrentes de\n            # propósito: o contrato observado da troca deve vencer ambos.\n            "ultimo_site_aba": "prime video",\n            "ultimo_app_janela": "opera",\n        }\n        referencia = referencia_contextual_imediata(\n            mente_integrada_estado=estado,\n            foco_vivo={\n                "habilidade": "janela",\n                "alvo": "Opera",\n                "ts": agora,\n            },\n            texto_atual="Fecha essa.",\n            normalizar_texto=self._normalizar_teste,\n        )\n        self.assertEqual(referencia["tipo"], "site")\n        self.assertEqual(referencia["alvo"], rotulo_observado)\n\n        fechamento = resolver_comando_acao_geral_contextual(\n            "Fecha essa.",\n            referencia,\n        )\n        self.assertEqual(fechamento["intent"], "CLOSE_TAB")\n        self.assertEqual(fechamento["params"]["alvo"], rotulo_observado)\n\n    def test_porta_prioritaria_reconhece_volta_anterior(self):\n        self.assertTrue(\n            texto_referencia_tipificada_prioritaria("Volta para a anterior.")\n        )\n        self.assertTrue(\n            texto_referencia_tipificada_prioritaria("Fecha essa.")\n        )\n        self.assertFalse(\n            texto_referencia_tipificada_prioritaria("A anterior era melhor.")\n        )\n\n    def test_repeticao_nao_vira_parte_do_nome_do_site(self):\n        normalizar = self._normalizar_teste\n        limpar = lambda valor: str(valor or "").strip()\n        sites = {\n            "wikipedia": "https://pt.wikipedia.org/",\n            "prime video": "https://www.primevideo.com/",\n        }\n        apps = {\n            "opera": "opera.exe",\n            "calculadora": "calc.exe",\n        }\n\n        casos = {\n            "Abre a Wikipédia de novo.": ("OPEN_URL", "wikipedia"),\n            "Abre o Prime Video novamente.": ("OPEN_URL", "prime video"),\n            "Abre o Opera de novo.": ("APP_OPEN", "opera"),\n            "Abre a Calculadora outra vez.": ("APP_OPEN", "calculadora"),\n        }\n        for texto, esperado in casos.items():\n            with self.subTest(texto=texto):\n                resultado = extrair_intencao_abrir_app(\n                    texto,\n                    normalizar_texto=normalizar,\n                    limpar_destino=limpar,\n                    apps_map=apps,\n                    sites_diretos=sites,\n                )\n                self.assertIsInstance(resultado, dict)\n                self.assertEqual(resultado["intent"], esperado[0])\n                params = resultado["params"]\n                alvo = params.get("alvo") or params.get("nome_app")\n                self.assertEqual(alvo, esperado[1])\n\n    def test_repeticao_sem_alvo_nao_inventa_app(self):\n        for texto in (\n            "Abre de novo.",\n            "Abre novamente.",\n            "Abre outra vez.",\n        ):\n            with self.subTest(texto=texto):\n                resultado = extrair_intencao_abrir_app(\n                    texto,\n                    normalizar_texto=self._normalizar_teste,\n                    limpar_destino=lambda valor: str(valor or "").strip(),\n                    apps_map={"opera": "opera.exe"},\n                    sites_diretos={"wikipedia": "https://pt.wikipedia.org/"},\n                )\n                self.assertIsNone(resultado)\n\n    def test_seletor_central_trata_anterior_como_referencia(self):\n        agora = time.time()\n        mente = {\n            "continuidade_geral": {\n                "dominio_ativo": "site",\n                "dominios": {\n                    "site": {\n                        "ativa": True,\n                        "ts": agora,\n                        "expira_em": agora + 300.0,\n                    }\n                },\n            },\n            "focos_por_dominio": {\n                "site": {\n                    "alvo": "prime video",\n                    "topico": "prime video",\n                    "ts": agora,\n                }\n            },\n        }\n        resultado = selecionar_contexto_turno(\n            "Volta para a anterior.",\n            turno={\n                "texto_operacional": "volta para a anterior",\n                "modalidade": "comando",\n            },\n            mente=mente,\n            contexto_perceptivo={},\n        )\n        self.assertTrue(resultado["referencia_contextual"])\n\n\nif __name__ == "__main__":\n    unittest.main()\n'


def localizar_raiz(explicita: str | None) -> Path:
    candidatos: list[Path] = []
    if explicita:
        candidatos.append(Path(explicita).expanduser().resolve())
    script_dir = Path(__file__).resolve().parent
    cwd = Path.cwd().resolve()
    candidatos.extend([
        script_dir,
        script_dir.parent,
        cwd,
        cwd / "laylay",
        cwd / "projeto-laylay",
        cwd.parent,
    ])
    vistos: set[Path] = set()
    for candidato in candidatos:
        if candidato in vistos:
            continue
        vistos.add(candidato)
        if all(
            (candidato / rel).exists()
            for chave, rel in ARQUIVOS.items()
            if chave != "teste"
        ):
            return candidato
    raise FileNotFoundError(
        "Não encontrei a raiz do projeto. Use --root CAMINHO_DO_PROJETO."
    )


def ler(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8")


def escrever(caminho: Path, conteudo: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding="utf-8", newline="\n")


def substituir_unico(texto: str, antigo: str, novo: str, rotulo: str) -> str:
    n = texto.count(antigo)
    if n != 1:
        raise RuntimeError(
            f"Âncora '{rotulo}' esperada 1 vez, encontrada {n}."
        )
    return texto.replace(antigo, novo, 1)


def inserir_unico(texto: str, ancora: str, bloco: str, rotulo: str) -> str:
    n = texto.count(ancora)
    if n != 1:
        raise RuntimeError(
            f"Âncora de inserção '{rotulo}' esperada 1 vez, encontrada {n}."
        )
    return texto.replace(ancora, bloco + ancora, 1)


def validar_ast(caminho: Path) -> None:
    try:
        ast.parse(ler(caminho), filename=str(caminho))
    except SyntaxError as erro:
        raise RuntimeError(
            f"AST inválida em {caminho}: linha {erro.lineno}: {erro.msg}"
        ) from erro


def criar_backup(raiz: Path, caminhos: list[Path]) -> Path:
    destino = (
        raiz
        / "_backup_p0_2a_navegador_v3_1"
        / time.strftime("%Y%m%d-%H%M%S")
    )
    for caminho in caminhos:
        if caminho.exists():
            relativo = caminho.relative_to(raiz)
            alvo = destino / relativo
            alvo.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(caminho, alvo)
    return destino


def restaurar(
    raiz: Path,
    pasta_backup: Path,
    caminhos: list[Path],
    teste_existia: bool,
) -> None:
    for caminho in caminhos:
        relativo = caminho.relative_to(raiz)
        salvo = pasta_backup / relativo
        if salvo.exists():
            caminho.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(salvo, caminho)
        elif (
            caminho == raiz / ARQUIVOS["teste"]
            and not teste_existia
            and caminho.exists()
        ):
            caminho.unlink()


def validar_marcadores(raiz: Path) -> None:
    fontes = {nome: ler(raiz / rel) for nome, rel in ARQUIVOS.items()}
    obrigatorios = {
        "contexto": [
            "def _dominio_contrato_referencia(",
            "dominio_contrato = _dominio_contrato_referencia",
            '"SWITCH_PREVIOUS_TAB", "APP_OPEN"',
            '"OPEN_URL", "CLOSE_TAB", "SWITCH_PREVIOUS_TAB", "SITE_ENTER"',
            MARCADOR,
        ],
        "comandos": [
            "def texto_referencia_tipificada_prioritaria(",
            '"SWITCH_PREVIOUS_TAB", "MEDIA_CONTROL"',
            MARCADOR,
        ],
        "roteador": [
            r'(?:^|\s)(?:de\s+novo|novamente|outra\s+vez)',
            MARCADOR,
        ],
        "seletor": [
            "anterior|de antes|como assim",
            MARCADOR,
        ],
        "teste": [
            "test_contrato_web_confirmado_vence_janela_fisica_em_deitico",
            "test_repeticao_nao_vira_parte_do_nome_do_site",
            "test_repeticao_sem_alvo_nao_inventa_app",
            "test_troca_observada_vira_referente_do_fecha_essa",
        ],
    }
    for nome, tokens in obrigatorios.items():
        ausentes = [token for token in tokens if token not in fontes[nome]]
        if ausentes:
            raise RuntimeError(
                f"Validação estrutural falhou em {nome}: {ausentes!r}"
            )


def executar_testes_puros(raiz: Path) -> None:
    comando = [
        sys.executable,
        "-m",
        "unittest",
        "tests.test_p0_2a_navegador_v3_1",
        "-v",
    ]
    resultado = subprocess.run(
        comando,
        cwd=raiz,
        text=True,
        capture_output=True,
        timeout=90,
    )
    saida = (resultado.stdout or "") + (resultado.stderr or "")
    if saida.strip():
        print(saida.rstrip())
    if resultado.returncode != 0:
        raise RuntimeError(
            "Testes focados falharam; alterações serão revertidas."
        )


def aplicar(raiz: Path) -> None:
    fontes = [
        raiz / ARQUIVOS["contexto"],
        raiz / ARQUIVOS["comandos"],
        raiz / ARQUIVOS["roteador"],
        raiz / ARQUIVOS["seletor"],
    ]
    caminho_teste = raiz / ARQUIVOS["teste"]
    todos = fontes + [caminho_teste]
    teste_existia = caminho_teste.exists()

    ja_aplicado = (
        all(MARCADOR in ler(caminho) for caminho in fontes)
        and caminho_teste.exists()
        and "test_repeticao_nao_vira_parte_do_nome_do_site"
        in ler(caminho_teste)
        and "test_repeticao_sem_alvo_nao_inventa_app"
        in ler(caminho_teste)
    )
    if ja_aplicado:
        for caminho in todos:
            validar_ast(caminho)
        validar_marcadores(raiz)
        executar_testes_puros(raiz)
        print("✅ P0.2A v3.1 já estava aplicada e continua válida.")
        return

    pasta_backup = criar_backup(raiz, todos)
    print(f"📦 Backup: {pasta_backup}")

    try:
        contexto = ler(raiz / ARQUIVOS["contexto"])
        comandos = ler(raiz / ARQUIVOS["comandos"])
        roteador = ler(raiz / ARQUIVOS["roteador"])
        seletor = ler(raiz / ARQUIVOS["seletor"])

        for nome, conteudo in (
            ("contexto", contexto),
            ("comandos", comandos),
            ("roteador", roteador),
            ("seletor", seletor),
        ):
            if MARCADOR in conteudo:
                raise RuntimeError(
                    f"{nome} contém aplicação parcial da v3; "
                    "não vou completar um estado desconhecido."
                )

        contexto = substituir_unico(
            contexto, CONTEXTO_ANTIGO, CONTEXTO_NOVO,
            "dominio_restrito_referencia",
        )
        contexto = substituir_unico(
            contexto,
            CONTEXTO_CONTRATO_INTENTS_ANTIGO,
            CONTEXTO_CONTRATO_INTENTS_NOVO,
            "contrato web referenciavel",
        )
        contexto = substituir_unico(
            contexto,
            CONTEXTO_TIPO_CONTRATO_ANTIGO,
            CONTEXTO_TIPO_CONTRATO_NOVO,
            "tipo contrato navegador",
        )
        contexto = substituir_unico(
            contexto,
            CONTEXTO_SITE_RECENTE_ANTIGO,
            CONTEXTO_SITE_RECENTE_NOVO,
            "site recente inclui troca de aba",
        )
        seletor = substituir_unico(
            seletor, SELETOR_ANTIGO, SELETOR_NOVO,
            "referencia seletor central",
        )
        comandos = inserir_unico(
            comandos, COMANDOS_INSERIR_ANTES, COMANDOS_HELPER,
            "helper referencia tipada",
        )
        comandos = substituir_unico(
            comandos, COMANDOS_GATE_ANTIGO, COMANDOS_GATE_NOVO,
            "gate referencia tipada",
        )
        comandos = substituir_unico(
            comandos, COMANDOS_INTENTS_ANTIGO, COMANDOS_INTENTS_NOVO,
            "allowlist referencia tipada",
        )
        roteador = substituir_unico(
            roteador, ROTEADOR_ANTIGO, ROTEADOR_NOVO,
            "limpeza alvo abertura",
        )

        escrever(raiz / ARQUIVOS["contexto"], contexto)
        escrever(raiz / ARQUIVOS["comandos"], comandos)
        escrever(raiz / ARQUIVOS["roteador"], roteador)
        escrever(raiz / ARQUIVOS["seletor"], seletor)
        escrever(caminho_teste, TESTE)

        for caminho in todos:
            validar_ast(caminho)
        validar_marcadores(raiz)
        executar_testes_puros(raiz)

    except Exception:
        restaurar(raiz, pasta_backup, todos, teste_existia)
        print("↩️ Alterações revertidas a partir do backup.")
        raise

    print("✅ P0.2A v3.1 aplicada.")
    print("   - contrato web confirmado preserva site/aba")
    print("   - 'Volta para a anterior.' entra na referência tipada")
    print("   - 'Fecha essa.' não deve virar CLOSE_APP por causa do Opera")
    print("   - repetição não vira parte do nome do site/app")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aplica a correção P0.2A v3.1 do contexto de navegador."
    )
    parser.add_argument(
        "--root",
        help="Raiz do projeto Laylay; se omitido, tenta localizar.",
    )
    args = parser.parse_args()
    try:
        raiz = localizar_raiz(args.root)
        print(f"📁 Projeto: {raiz}")
        aplicar(raiz)
        return 0
    except Exception as erro:
        print(
            f"❌ P0.2A v3.1 não aplicada: "
            f"{type(erro).__name__}: {erro}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
