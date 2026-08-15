#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch P0_CADEIA_MULTIETAPAS_V1_20260815

Corrige a decomposição de comandos operacionais compostos da Laylay sem
adicionar regras específicas de IoT.

Mudanças:
- segmentar_comandos_em_cadeia passa a aceitar de 2 a 5 etapas;
- vírgula e ponto-e-vírgula podem separar etapas, mas somente quando os dois
  lados parecem ordens operacionais completas;
- preserva conectores naturais: "e", "e depois", "depois", "em seguida", "então";
- reconhece formas operacionais necessárias aos casos reais do teste:
  "deixa", "passa", "volta", "confirma", "consulta", "me diz", "me fala",
  "me mostra";
- processar_comandos_em_cadeia executa todas as etapas reconhecidas, em ordem;
- cadeias acima do limite são recusadas pelo segmentador em vez de serem
  executadas parcialmente.

O patch NÃO altera RuntimeIoT, executores físicos, credenciais ou arquivos Tuya.

Uso:
    python aplicar_correcao_cadeia_multietapas_v1.py --dry-run
    python aplicar_correcao_cadeia_multietapas_v1.py
    python aplicar_correcao_cadeia_multietapas_v1.py --rollback

Opcional:
    python aplicar_correcao_cadeia_multietapas_v1.py --skip-tests
"""

from __future__ import annotations

import argparse
import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path

PATCH_ID = "P0_CADEIA_MULTIETAPAS_V1_20260815"
MARKER = f"# {PATCH_ID}"

PROD_REL = Path("mente_laylay/autonomia/analise_comandos.py")
TEST_REL = Path("tests/test_cadeia_operacional_multietapas.py")
BACKUP_REL = Path("backups/patch_cadeia_multietapas_v1_20260815")

OLD_HEADER = r'''_INICIO_ETAPA_OPERACIONAL = re.compile(
    r"^(?:"
    r"abr(?:e|a)|fech(?:a|e)|maximiz(?:a|e)|minimiz(?:a|e)|"
    r"cri(?:a|e)|coloc(?:a|que)|bot(?:a|e)|toc(?:a|que)|"
    r"adicion(?:a|e)|salv(?:a|e)|guard(?:a|e)|anot(?:a|e)|"
    r"apag(?:a|ue)|exclu(?:i|a)|delet(?:a|e)|remov(?:e|a)|"
    r"encontr(?:a|e)|procur(?:a|e)|pesquis(?:a|e)|busc(?:a|que)|"
    r"copi(?:a|e)|escrev(?:e|a)|grav(?:a|e)|mov(?:e|a)|renomei(?:a|e)|mud(?:a|e)|"
    r"lig(?:a|ue)|deslig(?:a|ue)|paus(?:a|e)|continu(?:a|e)|"
    r"retom(?:a|e)|organiz(?:a|e)|agend(?:a|e)|cancel(?:a|e)|"
    r"(?:me\s+)?lembr(?:a|e)|resum(?:e|a)|explic(?:a|que)|"
    r"mostr(?:a|e)|list(?:a|e)|diz|diga|fal(?:a|e)"
    r")\b",
    flags=re.IGNORECASE,
)


def _parece_etapa_operacional(texto: str) -> bool:
    """Limita o ``e`` simples a duas ordens, sem cortar conversa comum."""
    return bool(_INICIO_ETAPA_OPERACIONAL.match(str(texto or "").strip()))
'''

NEW_HEADER = r'''# P0_CADEIA_MULTIETAPAS_V1_20260815
LIMITE_ETAPAS_CADEIA = 5

_INICIO_ETAPA_OPERACIONAL = re.compile(
    r"^(?:"
    r"abr(?:e|a)|fech(?:a|e)|maximiz(?:a|e)|minimiz(?:a|e)|"
    r"cri(?:a|e)|coloc(?:a|que)|bot(?:a|e)|toc(?:a|que)|"
    r"deix(?:a|e)|pass(?:a|e)|volt(?:a|e)|confirm(?:a|e)|consult(?:a|e)|"
    r"adicion(?:a|e)|salv(?:a|e)|guard(?:a|e)|anot(?:a|e)|"
    r"apag(?:a|ue)|exclu(?:i|a)|delet(?:a|e)|remov(?:e|a)|"
    r"encontr(?:a|e)|procur(?:a|e)|pesquis(?:a|e)|busc(?:a|que)|"
    r"copi(?:a|e)|escrev(?:e|a)|grav(?:a|e)|mov(?:e|a)|renomei(?:a|e)|mud(?:a|e)|"
    r"lig(?:a|ue)|deslig(?:a|ue)|paus(?:a|e)|continu(?:a|e)|"
    r"retom(?:a|e)|organiz(?:a|e)|agend(?:a|e)|cancel(?:a|e)|"
    r"(?:me\s+)?lembr(?:a|e)|resum(?:e|a)|explic(?:a|que)|"
    r"list(?:a|e)|(?:me\s+)?(?:mostr(?:a|e)|diz|diga|fal(?:a|e))"
    r")\b",
    flags=re.IGNORECASE,
)

_SEPARADOR_ETAPA_OPERACIONAL = re.compile(
    r"\be\s+depois\b|\bem\s+seguida\b|\bdepois\b|"
    r"\bent[aã]o\b|[,;]|\be\b",
    flags=re.IGNORECASE,
)


def _parece_etapa_operacional(texto: str) -> bool:
    """Aceita um corte somente quando o trecho começa como ordem operacional."""
    return bool(_INICIO_ETAPA_OPERACIONAL.match(str(texto or "").strip()))
'''

OLD_SEGMENTAR = r'''def segmentar_comandos_em_cadeia(
    texto: str,
    *,
    normalizar_texto: Optional[Callable[[str], str]] = None,
) -> List[str]:
    """Separa comandos naturais em até duas etapas encadeadas."""
    bruto = str(texto or "").strip()
    if not bruto:
        return []

    t = normalizar_texto(bruto) if callable(normalizar_texto) else bruto.lower()
    t = re.sub(r"[,\.!\?:;]+", " ", t)
    t = re.sub(r"\b(laylay|lay|por favor|pfv)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return []

    # Localizamos o conector na fala original. A cópia normalizada serve só
    # para reconhecer verbos; devolver seus segmentos destruiria argumentos
    # como ``resultado.md``, URLs, aspas e nomes com pontuação.
    bruto_operacional = re.sub(
        r"\b(laylay|lay|por favor|pfv)\b", " ", bruto,
        flags=re.IGNORECASE,
    )
    bruto_operacional = re.sub(r"\s+", " ", bruto_operacional).strip()
    for sep in (r"\be depois\b", r"\bem seguida\b", r"\bdepois\b", r"\bent[aã]o\b"):
        encontrado = re.search(sep, bruto_operacional, flags=re.IGNORECASE)
        if encontrado:
            partes_brutas = [
                bruto_operacional[:encontrado.start()].strip(" .,!?;:"),
                bruto_operacional[encontrado.end():].strip(" .,!?;:"),
            ]
            normalizar = normalizar_texto if callable(normalizar_texto) else str.lower
            partes_operacionais = [
                str(normalizar(parte) or "").strip(" .,!?;:")
                for parte in partes_brutas
            ]
            # ``depois`` também é marcador temporal em hipóteses e adiamentos.
            # Só existe cadeia quando os dois lados são ordens completas. Isso
            # impede que ``Talvez eu apague X depois.`` seja consumido como
            # uma execução e que o ponto final vire uma etapa fantasma.
            if (
                all(partes_brutas)
                and all(_parece_etapa_operacional(parte) for parte in partes_operacionais)
            ):
                return partes_brutas[:2]

    # O conectivo simples também forma uma cadeia quando ambos os lados são
    # ordens reconhecíveis ("cria a pasta e coloca um arquivo nela"). A
    # validação dos dois verbos impede falsos cortes em frases como
    # "você prefere rock e metal?" ou "liga a luz e o ventilador".
    for encontrado in re.finditer(r"\be\b", bruto_operacional, flags=re.IGNORECASE):
        esquerda_bruta = bruto_operacional[:encontrado.start()].strip(" ,!?;:")
        direita_bruta = bruto_operacional[encontrado.end():].strip(" ,!?;:")
        normalizar = normalizar_texto if callable(normalizar_texto) else str.lower
        esquerda = str(normalizar(esquerda_bruta) or "").strip()
        direita = str(normalizar(direita_bruta) or "").strip()
        if _parece_etapa_operacional(esquerda) and _parece_etapa_operacional(direita):
            return [esquerda_bruta, direita_bruta]

    return [t]
'''

NEW_SEGMENTAR = r'''def segmentar_comandos_em_cadeia(
    texto: str,
    *,
    normalizar_texto: Optional[Callable[[str], str]] = None,
) -> List[str]:
    """Separa uma cadeia curta de ordens sem transformar conjunções em ações."""
    bruto = str(texto or "").strip()
    if not bruto:
        return []

    t = normalizar_texto(bruto) if callable(normalizar_texto) else bruto.lower()
    t = re.sub(r"[,\.!\?:;]+", " ", t)
    t = re.sub(r"\b(laylay|lay|por favor|pfv)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return []

    # Os segmentos devolvidos continuam vindo da fala original: nomes,
    # resultado.md, URLs, aspas e pontuação interna não podem ser destruídos
    # pela cópia usada apenas para reconhecer o começo de cada ordem.
    bruto_operacional = re.sub(
        r"\b(laylay|lay|por favor|pfv)\b", " ", bruto,
        flags=re.IGNORECASE,
    )
    bruto_operacional = re.sub(r"\s+", " ", bruto_operacional).strip()
    normalizar = normalizar_texto if callable(normalizar_texto) else str.lower

    def normalizar_etapa(parte: str) -> str:
        return str(normalizar(parte) or "").strip(" .,!?;:")

    partes: List[str] = []
    inicio = 0

    # Um separador só vira fronteira quando o trecho acumulado à esquerda e o
    # restante à direita começam como ordens operacionais. Isso permite
    # "liga X, deixa azul e depois me diz..." sem cortar enumerações como
    # "liga a luz e o ventilador" ou "coloca vermelho, azul e verde".
    for encontrado in _SEPARADOR_ETAPA_OPERACIONAL.finditer(bruto_operacional):
        esquerda = bruto_operacional[inicio:encontrado.start()].strip(" .,!?;:")
        direita = bruto_operacional[encontrado.end():].strip(" .,!?;:")
        if not esquerda or not direita:
            continue
        if not _parece_etapa_operacional(normalizar_etapa(esquerda)):
            continue
        if not _parece_etapa_operacional(normalizar_etapa(direita)):
            continue

        # Nunca executamos somente o começo de uma cadeia longa. Acima do
        # limite, o texto volta inteiro ao fluxo normal para não haver sucesso
        # parcial silencioso.
        if len(partes) + 2 > LIMITE_ETAPAS_CADEIA:
            return [t]

        partes.append(esquerda)
        inicio = encontrado.end()

    if partes:
        final = bruto_operacional[inicio:].strip(" .,!?;:")
        if final and _parece_etapa_operacional(normalizar_etapa(final)):
            partes.append(final)
            if 2 <= len(partes) <= LIMITE_ETAPAS_CADEIA:
                return partes

    return [t]
'''

OLD_PROCESSAR = r'''def processar_comandos_em_cadeia(
    texto: str,
    origem: str = "",
    *,
    normalizar_texto: Optional[Callable[[str], str]] = None,
    segmentar: Callable[..., List[str]] = segmentar_comandos_em_cadeia,
    executar_trecho: Optional[Callable[[str, str], bool]] = None,
    relatar_falha: Optional[Callable[[str, int, int], object]] = None,
) -> bool:
    """Executa comandos naturais encadeados, mantendo compatibilidade com o fluxo antigo."""
    partes = segmentar(texto, normalizar_texto=normalizar_texto)
    if len(partes) < 2:
        return False

    tag = origem or "cadeia"
    for idx, parte in enumerate(partes[:2], start=1):
        executou = bool(
            callable(executar_trecho)
            and executar_trecho(parte, f"{tag}-{idx}")
        )
        if not executou:
            if callable(relatar_falha):
                relatar_falha(parte, idx, idx - 1)
            # Etapas posteriores podem depender do resultado que faltou. Não
            # avançamos nem declaramos o composto concluído pela metade.
            break

    # A cadeia foi reconhecida e consumida, mesmo quando uma etapa falhou. A
    # falha já foi relatada acima; devolver False faria o fluxo reprocessar a
    # frase inteira e poderia duplicar as etapas que tiveram sucesso.
    return True
'''

NEW_PROCESSAR = r'''def processar_comandos_em_cadeia(
    texto: str,
    origem: str = "",
    *,
    normalizar_texto: Optional[Callable[[str], str]] = None,
    segmentar: Callable[..., List[str]] = segmentar_comandos_em_cadeia,
    executar_trecho: Optional[Callable[[str, str], bool]] = None,
    relatar_falha: Optional[Callable[[str, int, int], object]] = None,
) -> bool:
    """Executa uma cadeia curta em ordem e interrompe na primeira falha."""
    partes = segmentar(texto, normalizar_texto=normalizar_texto)
    if len(partes) < 2 or len(partes) > LIMITE_ETAPAS_CADEIA:
        return False

    tag = origem or "cadeia"
    for idx, parte in enumerate(partes, start=1):
        executou = bool(
            callable(executar_trecho)
            and executar_trecho(parte, f"{tag}-{idx}")
        )
        if not executou:
            if callable(relatar_falha):
                relatar_falha(parte, idx, idx - 1)
            # Etapas posteriores podem depender do resultado que faltou. Não
            # avançamos nem declaramos o composto concluído pela metade.
            break

    # A cadeia foi reconhecida e consumida, mesmo quando uma etapa falhou. A
    # falha já foi relatada acima; devolver False faria o fluxo reprocessar a
    # frase inteira e poderia duplicar as etapas que tiveram sucesso.
    return True
'''

TEST_CONTENT = r'''from __future__ import annotations

from mente_laylay.autonomia.analise_comandos import (
    LIMITE_ETAPAS_CADEIA,
    processar_comandos_em_cadeia,
    segmentar_comandos_em_cadeia,
)
from mente_laylay.iot.runtime import RuntimeIoT


class MemoriaIoTFalsa:
    def __init__(self) -> None:
        self.dispositivos = {}
        self.historico = []

    def salvar_dispositivo_iot(self, dados):
        self.dispositivos[dados["nome"]] = dict(dados)
        return dict(dados)

    def listar_dispositivos_iot(self, ambiente="", *, somente_ativos=True):
        return [
            dict(item)
            for item in self.dispositivos.values()
            if (not ambiente or item["ambiente"] == ambiente)
            and (not somente_ativos or item.get("ativo", True))
        ]

    def atualizar_estado_iot(self, nome, estado, **kwargs):
        self.dispositivos[nome]["estado"] = dict(estado)
        return dict(estado)

    def registrar_historico_iot(self, nome, **dados):
        self.historico.append({"nome": nome, **dados})
        return self.historico[-1]


def test_turno_152_segmenta_em_tres_etapas_reais() -> None:
    texto = (
        "Liga a lâmpada do quarto, deixa azul e depois "
        "me diz como ela ficou."
    )

    assert segmentar_comandos_em_cadeia(texto) == [
        "Liga a lâmpada do quarto",
        "deixa azul",
        "me diz como ela ficou",
    ]


def test_variantes_reais_do_bloco_h_continuam_segmentadas() -> None:
    casos = (
        (
            "Mostra a playlist caos sonora e depois apaga ela.",
            ["Mostra a playlist caos sonora", "apaga ela"],
        ),
        (
            "Desliga a lâmpada e confirma o estado.",
            ["Desliga a lâmpada", "confirma o estado"],
        ),
        (
            "Volta para a aba anterior e depois me diz qual aba está aberta.",
            ["Volta para a aba anterior", "me diz qual aba está aberta"],
        ),
        (
            "Continua a música, passa para a próxima faixa e me diz qual está tocando.",
            [
                "Continua a música",
                "passa para a próxima faixa",
                "me diz qual está tocando",
            ],
        ),
        (
            "Abre a Wikipédia, pesquisa documentação oficial do Python "
            "e abre o primeiro resultado.",
            [
                "Abre a Wikipédia",
                "pesquisa documentação oficial do Python",
                "abre o primeiro resultado",
            ],
        ),
    )

    for texto, esperado in casos:
        assert segmentar_comandos_em_cadeia(texto) == esperado, texto


def test_conjuncoes_e_enumeracoes_nao_viram_execucao_multipla() -> None:
    frases = (
        "Liga a luz e o ventilador.",
        "Você prefere rock e metal?",
        "Talvez eu apague X depois.",
        "deixa para depois",
        "coloca vermelho, azul e verde",
        "me fala de rock e metal",
    )

    for texto in frases:
        assert len(segmentar_comandos_em_cadeia(texto)) == 1, texto


def test_cadeia_acima_do_limite_nao_e_executada_parcialmente() -> None:
    texto = ", ".join(
        f"abre o aplicativo {indice}"
        for indice in range(1, LIMITE_ETAPAS_CADEIA + 2)
    )

    assert len(segmentar_comandos_em_cadeia(texto)) == 1


def test_processador_executa_as_tres_etapas_na_ordem() -> None:
    texto = (
        "Liga a lâmpada do quarto, deixa azul e depois "
        "me diz como ela ficou."
    )
    chamadas = []

    def executar(trecho: str, origem: str) -> bool:
        chamadas.append((trecho, origem))
        return True

    assert processar_comandos_em_cadeia(
        texto,
        "regressao-152",
        executar_trecho=executar,
    ) is True
    assert chamadas == [
        ("Liga a lâmpada do quarto", "regressao-152-1"),
        ("deixa azul", "regressao-152-2"),
        ("me diz como ela ficou", "regressao-152-3"),
    ]


def test_processador_para_na_primeira_falha_sem_executar_dependentes() -> None:
    texto = "abre a Calculadora, maximiza ela e depois fecha ela"
    chamadas = []

    def executar(trecho: str, origem: str) -> bool:
        chamadas.append((trecho, origem))
        return len(chamadas) < 2

    assert processar_comandos_em_cadeia(
        texto,
        "falha-parcial",
        executar_trecho=executar,
    ) is True
    assert [item[0] for item in chamadas] == [
        "abre a Calculadora",
        "maximiza ela",
    ]


def test_turno_152_percorre_iot_simulado_ligar_cor_status() -> None:
    estado = {}
    runtime = RuntimeIoT(
        memoria_sqlite=MemoriaIoTFalsa(),
        falar=lambda *_: None,
        estado_mental_getter=lambda: estado,
        emitir_fala=False,
        modo="simulado",
        log=lambda *_: None,
    )
    texto = (
        "Liga a lâmpada do quarto, deixa azul e depois "
        "me diz como ela ficou."
    )
    observadas = []

    for trecho in segmentar_comandos_em_cadeia(texto):
        candidato = runtime.detectar(trecho, estado)
        assert candidato is not None, trecho
        observadas.append((
            candidato["intent"],
            candidato["params"]["acao"],
            candidato["params"]["alvo"],
        ))
        retorno = runtime.executar(candidato, trecho)
        assert retorno["handled"] is True
        assert retorno["ok"] is True
        assert retorno["confirmado"] is True

    assert observadas == [
        ("IOT_CONTROL", "ligar", "lampada_quarto"),
        ("IOT_CONTROL", "ajustar_cor", "lampada_quarto"),
        ("IOT_STATUS", "status", "lampada_quarto"),
    ]
    assert estado["ultimo_dispositivo_iot"] == "lampada_quarto"
    assert estado["ultima_habilidade"] == "iot"
'''


def encontrar_raiz(inicio: Path) -> Path:
    candidatos = [inicio.resolve(), *inicio.resolve().parents]
    script_dir = Path(__file__).resolve().parent
    candidatos.extend([script_dir, *script_dir.parents])
    vistos = set()
    for candidato in candidatos:
        chave = str(candidato)
        if chave in vistos:
            continue
        vistos.add(chave)
        if (candidato / PROD_REL).is_file() and (candidato / "pyproject.toml").is_file():
            return candidato
    raise SystemExit(
        "ERRO: não encontrei a raiz do projeto. Execute este patch dentro "
        "do repositório da Laylay."
    )


def substituir_unico(texto: str, antigo: str, novo: str, nome: str) -> str:
    quantidade = texto.count(antigo)
    if quantidade != 1:
        raise RuntimeError(
            f"âncora {nome!r} deveria aparecer exatamente 1 vez; apareceu {quantidade}. "
            "O arquivo mudou desde a análise e o patch recusou adivinhar."
        )
    return texto.replace(antigo, novo, 1)


def montar_novo_conteudo(conteudo: str) -> str:
    novo = substituir_unico(conteudo, OLD_HEADER, NEW_HEADER, "header/verbos")
    novo = substituir_unico(novo, OLD_SEGMENTAR, NEW_SEGMENTAR, "segmentador")
    novo = substituir_unico(novo, OLD_PROCESSAR, NEW_PROCESSAR, "executor da cadeia")
    ast.parse(novo, filename=str(PROD_REL))
    ast.parse(TEST_CONTENT, filename=str(TEST_REL))
    return novo


def preparar_backup(raiz: Path, prod: Path, teste: Path) -> Path:
    backup = raiz / BACKUP_REL
    backup_prod = backup / PROD_REL
    manifest = backup / "manifest.json"

    if backup_prod.is_file() and manifest.is_file():
        return backup

    backup_prod.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(prod, backup_prod)

    test_existed = teste.is_file()
    if test_existed:
        backup_test = backup / TEST_REL
        backup_test.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(teste, backup_test)

    manifest.write_text(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "production": str(PROD_REL).replace("\\", "/"),
                "test": str(TEST_REL).replace("\\", "/"),
                "test_existed": test_existed,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return backup


def rollback(raiz: Path) -> None:
    prod = raiz / PROD_REL
    teste = raiz / TEST_REL
    backup = raiz / BACKUP_REL
    backup_prod = backup / PROD_REL
    manifest_path = backup / "manifest.json"

    if not backup_prod.is_file() or not manifest_path.is_file():
        raise SystemExit("ERRO: não encontrei backup deste patch para restaurar.")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    shutil.copy2(backup_prod, prod)

    if bool(manifest.get("test_existed")):
        backup_test = backup / TEST_REL
        if not backup_test.is_file():
            raise SystemExit("ERRO: manifesto diz que o teste existia, mas o backup sumiu.")
        teste.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_test, teste)
    elif teste.is_file():
        teste.unlink()

    ast.parse(prod.read_text(encoding="utf-8"), filename=str(PROD_REL))
    print("ROLLBACK OK")
    print(f"Restaurado: {PROD_REL}")
    print(f"Teste restaurado/removido conforme manifesto: {TEST_REL}")


def escolher_python(raiz: Path) -> str:
    candidatos = (
        raiz / ".venv314" / "Scripts" / "python.exe",
        raiz / ".venv" / "Scripts" / "python.exe",
        raiz / ".venv314" / "bin" / "python",
        raiz / ".venv" / "bin" / "python",
    )
    for candidato in candidatos:
        if candidato.is_file():
            return str(candidato)
    return sys.executable


def rodar_testes(raiz: Path) -> None:
    python = escolher_python(raiz)
    comando = [
        python,
        "-m",
        "pytest",
        str(TEST_REL),
        "tests/test_composicao_ciclo_comandos.py",
        "-q",
    ]
    print("TESTE:", " ".join(comando))
    resultado = subprocess.run(
        comando,
        cwd=raiz,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(resultado.stdout)
    if resultado.returncode != 0:
        raise RuntimeError(f"pytest falhou com código {resultado.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    raiz = encontrar_raiz(Path.cwd())
    prod = raiz / PROD_REL
    teste = raiz / TEST_REL

    print(f"Raiz: {raiz}")
    print(f"Patch: {PATCH_ID}")

    if args.rollback:
        rollback(raiz)
        return 0

    conteudo = prod.read_text(encoding="utf-8")

    if MARKER in conteudo:
        print("Patch já aplicado; nenhuma alteração de produção foi feita.")
        if not teste.is_file():
            print(
                "AVISO: o arquivo de regressão não existe. "
                "Use --rollback e aplique novamente para reconstruir o pacote completo."
            )
            return 2
        if not args.skip_tests and not args.dry_run:
            rodar_testes(raiz)
        return 0

    try:
        novo = montar_novo_conteudo(conteudo)
    except Exception as erro:
        print(f"ERRO DE VALIDAÇÃO: {erro}")
        return 2

    if args.dry_run:
        print("DRY-RUN OK")
        print(f"Alteraria: {PROD_REL}")
        print(f"Criaria/substituiria teste: {TEST_REL}")
        print(f"Limite de etapas: {LIMITE_ETAPAS_CADEIA if 'LIMITE_ETAPAS_CADEIA' in globals() else 5}")
        print("Nenhum arquivo foi gravado.")
        return 0

    backup = preparar_backup(raiz, prod, teste)
    print(f"Backup: {backup.relative_to(raiz)}")

    try:
        prod.write_text(novo, encoding="utf-8", newline="\n")
        teste.parent.mkdir(parents=True, exist_ok=True)
        teste.write_text(TEST_CONTENT, encoding="utf-8", newline="\n")

        ast.parse(prod.read_text(encoding="utf-8"), filename=str(PROD_REL))
        ast.parse(teste.read_text(encoding="utf-8"), filename=str(TEST_REL))

        if not args.skip_tests:
            rodar_testes(raiz)
    except Exception as erro:
        print(f"ERRO: {erro}")
        print("Restaurando automaticamente o estado anterior...")
        rollback(raiz)
        return 1

    print("PATCH OK")
    print(f"Alterado: {PROD_REL}")
    print(f"Regressão criada: {TEST_REL}")
    print("RuntimeIoT não foi modificado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
