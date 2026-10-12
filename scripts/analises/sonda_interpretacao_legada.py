"""Pressiona contratos de interpretação, sem modelo neural ou executores.

O painel é diagnóstico, não holdout nem estimativa de acurácia em produção.
RED significa divergência na fronteira examinada, não efeito externo ocorrido.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from mente_laylay.autonomia.analise_comandos import segmentar_comandos_em_cadeia
from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import (
    autoriza_execucao_efetiva,
    bloqueia_execucao_operacional_prioritaria,
    classificar_modalidade_turno,
)
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto


@dataclass(frozen=True)
class Caso:
    id: str
    familia: str
    dominio: str
    texto: str
    autoriza_agora: bool | None
    operacoes_presentes: tuple[str, ...] = ()
    operacoes_ausentes: tuple[str, ...] = ()
    literais_indivisiveis: tuple[str, ...] = ()


def painel() -> list[Caso]:
    """Expectativas declaradas antes da execução; pares mínimos por domínio."""
    dominios = (
        ("app", "abre a calculadora", "abrir a calculadora", "abra a calculadora", "abrisse a calculadora", "abri a calculadora"),
        ("midia", "pausa a música", "pausar a música", "pause a música", "pausasse a música", "pausei a música"),
        ("iot", "liga a luz", "ligar a luz", "ligue a luz", "ligasse a luz", "liguei a luz"),
        ("arquivo", "apaga o arquivo notas.txt", "apagar o arquivo notas.txt", "apague o arquivo notas.txt", "apagasse o arquivo notas.txt", "apaguei o arquivo notas.txt"),
    )
    moldes = (
        ("direto", "{cmd}.", True),
        ("polido", "Pode {inf}", True),
        ("polido", "Pode {inf}?", True),
        ("polido", "Você poderia {inf} para mim?", True),
        ("pedido_subordinado", "Quero que você {subj}.", True),
        ("pedido_subordinado", "Queria que você {passado}.", True),
        ("pedido_subordinado", "Preciso que você {subj}.", True),
        ("pedido_indireto", "Dá para você {inf} agora?", True),
        ("pedido_indireto", "Tem como você {inf} agora?", True),
        ("ensino", "Como posso {inf}", False),
        ("capacidade", "Você sabe {inf}?", False),
        ("relato", "Eu já {feito}.", False),
        ("recusa", "Não {cmd}.", False),
        ("citacao", 'A frase "{cmd}" é um exemplo de comando.', False),
        ("condicao_prefixada", "Quando eu disser pronto, {cmd}.", False),
        ("condicao_prefixada", "Quando eu disser pronto {cmd}.", False),
        ("condicao_posposta", "{cmd} só se eu confirmar depois.", False),
        ("metalinguagem", "Pode {inf} significa o quê?", False),
    )
    casos = []
    for dominio, cmd, inf, subj, passado, feito in dominios:
        for indice, (familia, molde, autoriza) in enumerate(moldes, 1):
            casos.append(Caso(
                f"{dominio}_{indice:02d}", familia, dominio,
                molde.format(cmd=cmd, inf=inf, subj=subj, passado=passado, feito=feito),
                autoriza,
            ))
    conjuntos = (
        ("duas_ordens", "Abre a calculadora e fecha o navegador.", True, ("abre a calculadora", "fecha o navegador"), (), ()),
        ("tres_ordens", "Abre a calculadora, fecha o navegador e pausa a música.", True, ("abre a calculadora", "fecha o navegador", "pausa a música"), (), ()),
        ("sequencia", "Abre a calculadora; depois pausa a música.", True, ("abre a calculadora", "pausa a música"), (), ()),
        ("polidez_compartilhada", "Pode abrir a calculadora e pausar a música?", True, ("abrir a calculadora", "pausar a música"), (), ()),
        ("polidez_compartilhada", "Pode ligar a luz e desligar o ventilador?", True, ("ligar a luz", "desligar o ventilador"), (), ()),
        ("polidez_compartilhada", "Pode abrir o arquivo notas.txt e ler o arquivo exemplo.txt?", True, ("abrir o arquivo notas.txt", "ler o arquivo exemplo.txt"), (), ()),
        ("polidez_compartilhada", "Abre a calculadora e depois pode pausar a música?", True, ("abre a calculadora", "pausar a música"), (), ()),
        ("negacao_escopo", "Não fecha o navegador, abre a calculadora e pausa a música.", True, ("abre a calculadora", "pausa a música"), ("fecha o navegador",), ()),
        ("negacao_escopo", "Abre a calculadora, mas não fecha o navegador.", True, ("abre a calculadora",), ("fecha o navegador",), ()),
        ("negacao_escopo", "Abre a calculadora e não fecha o navegador.", True, ("abre a calculadora",), ("fecha o navegador",), ()),
        ("negacao_escopo", "Não abre a calculadora; pausa a música.", True, ("pausa a música",), ("abre a calculadora",), ()),
        ("negacao_escopo", "Não liga a luz, desliga o ventilador.", True, ("desliga o ventilador",), ("liga a luz",), ()),
        ("negacao_escopo", "Não precisa conversar, só abre a calculadora.", True, ("abre a calculadora",), (), ()),
        ("negacao_escopo", "Não precisa abrir o navegador de novo, só pausa a música.", True, ("pausa a música",), ("abrir o navegador",), ()),
        ("condicao_conjunto", "Quando eu disser pronto, abre a calculadora e pausa a música.", False, (), (), ()),
        ("condicao_conjunto", "Só quando eu confirmar, liga a luz e desliga o ventilador.", False, (), (), ()),
        ("condicao_local", "Abre a calculadora agora; quando eu confirmar, pausa a música.", True, ("abre a calculadora agora",), ("pausa a música",), ()),
        ("condicao_local", "Abre a calculadora. Se eu confirmar depois, fecha o navegador.", True, ("abre a calculadora",), ("fecha o navegador",), ()),
        ("literal", 'Escreve "abre a calculadora e apaga o arquivo notas.txt" no arquivo exemplo.txt.', True, (), (), ('"abre a calculadora e apaga o arquivo notas.txt"',)),
        ("literal", 'Cria uma playlist chamada "pausa a música e fecha o navegador".', True, (), (), ('"pausa a música e fecha o navegador"',)),
        ("literal", 'Abre o arquivo "teste, fecha o navegador.txt" e pausa a música.', True, ("pausa a música",), (), ('"teste, fecha o navegador.txt"',)),
        ("enumeracao", "Liga a luz e o ventilador.", True, (), (), ()),
        ("enumeracao", "Pesquisa por arquitetura e engenharia.", True, (), (), ()),
        ("relato_conjunto", "O professor disse: abre a calculadora e fecha o navegador.", False, (), (), ()),
        ("recusa_conjunto", "Não abra a calculadora nem feche o navegador.", False, (), (), ()),
        ("misto", "Estou cansado, pausa a música e liga a luz.", True, ("pausa a música", "liga a luz"), (), ()),
        ("capacidade_conjunto", "Você sabe abrir a calculadora e fechar o navegador?", False, (), (), ()),
        ("ensino_conjunto", "Me ensina como abrir a calculadora e fechar o navegador.", False, (), (), ()),
    )
    for indice, (familia, texto, auth, presentes, ausentes, literais) in enumerate(conjuntos, 1):
        casos.append(Caso(f"conjunto_{indice:02d}", familia, "composto", texto, auth, presentes, ausentes, literais))
    return casos


def avaliar(caso: Caso, *, usar_normalizador: bool = False, usar_detector: bool = True) -> dict:
    turno = classificar_modalidade_turno(
        caso.texto,
        normalizar_texto=normalizar_texto if usar_normalizador else None,
        texto_tem_comando_explicito=texto_tem_comando_explicito if usar_detector else None,
    )
    auth = autoriza_execucao_efetiva(turno)
    operacional = str(turno.get("texto_operacional") or "").casefold()
    segmentos = [str(s.get("texto") or "").casefold() for s in turno.get("segmentos", [])]
    cadeia = segmentar_comandos_em_cadeia(caso.texto)
    falhas = []
    if caso.autoriza_agora is not None and auth != caso.autoriza_agora:
        falhas.append("autoridade_indevida" if auth else "pedido_bloqueado")
    for trecho in caso.operacoes_presentes:
        if trecho.casefold() not in operacional:
            falhas.append("operacao_pedida_ausente:" + trecho)
    for trecho in caso.operacoes_ausentes:
        if trecho.casefold() in operacional:
            falhas.append("operacao_nao_autorizada_presente:" + trecho)
    for literal in caso.literais_indivisiveis:
        for fronteira, partes in (("modalidade", segmentos), ("cadeia", cadeia)):
            if not any(literal.casefold() in parte.casefold() for parte in partes):
                falhas.append("literal_fragmentado:" + fronteira)
    # Captura as duas portas reais de interpretação sem chamar executores.
    return {
        "caso": asdict(caso), "falhas": falhas,
        "normalizador_injetado": usar_normalizador, "detector_injetado": usar_detector,
        "autoriza_efetiva": auth,
        "bloqueia_prioritario": bloqueia_execucao_operacional_prioritaria(caso.texto, classificacao=turno),
        "turno": {k: v for k, v in turno.items() if k not in {"id", "ts"}},
        "cadeia": cadeia, "efeito_externo_testado": False,
    }


def coletar() -> dict:
    fontes = (
        Path(__file__).relative_to(RAIZ).as_posix(),
        "mente_laylay/cognicao/modalidade_turno.py",
        "mente_laylay/cognicao/normalizacao_linguagem.py",
        "mente_laylay/autonomia/porteiro_acoes.py",
        "mente_laylay/autonomia/analise_comandos.py",
        "mente_laylay/cognicao/gramatica_corpo.py",
    )
    hashes = {p: hashlib.sha256((RAIZ / p).read_bytes()).hexdigest() for p in fontes}
    resultados = [avaliar(c, usar_normalizador=n, usar_detector=d) for c in painel() for n, d in ((False, True), (True, True), (False, False))]
    base = [r for r in resultados if not r["normalizador_injetado"] and r["detector_injetado"]]
    resumo = {
        "casos": len(base), "leituras": len(resultados),
        "casos_red": sum(bool(r["falhas"]) for r in base),
        "autoridade_indevida": sum("autoridade_indevida" in r["falhas"] for r in base),
        "pedidos_bloqueados": sum("pedido_bloqueado" in r["falhas"] for r in base),
        "familias_com_red": dict(Counter(r["caso"]["familia"] for r in base if r["falhas"])),
    }
    atuais = {p: hashlib.sha256((RAIZ / p).read_bytes()).hexdigest() for p in fontes}
    return {
        "instante_utc": datetime.now(timezone.utc).isoformat(),
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=RAIZ, text=True).strip(),
        "worktree": subprocess.check_output(["git", "status", "--short"], cwd=RAIZ, text=True),
        "hashes_antes": hashes, "hashes_depois": atuais, "fontes_estaveis": hashes == atuais,
        "resumo": resumo, "resultados": resultados,
        "runtime_real_validado": False, "rede_utilizada": False,
        "efeitos_externos_executados": False, "holdout": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    destino = args.saida.resolve()
    if not destino.is_relative_to((RAIZ / "resultados_testes").resolve()):
        parser.error("artefato deve ficar em resultados_testes")
    if destino.exists():
        parser.error("artefato existente não será sobrescrito")
    relatorio = coletar()
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("x", encoding="utf-8") as arquivo:
        json.dump(relatorio, arquivo, ensure_ascii=False, indent=2)
    print(json.dumps(relatorio["resumo"], ensure_ascii=False))
    print("Artefato:", destino)
    return 1 if relatorio["resumo"]["casos_red"] or not relatorio["fontes_estaveis"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
