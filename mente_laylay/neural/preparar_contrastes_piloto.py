"""Contrastes sintéticos revisados por IA, somente para desenvolvimento.

Não usa previsões como gold, não importa logs de origem desconhecida e não
gera partições de avaliação. Nomes são literais de teste, não prova de que
aplicativos, músicas ou arquivos existam. Nunca executa os pedidos escritos.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from .preparar_lote_relacional_v3 import preencher
from .protocolo_ajuste_supervisionado import auditar_corpus, validar_caso
from .qualidade import auditar_leakage_dataset
from .supervisao_relacoes_v4 import FLAGS


LINHAGEM = "curadoria_contrastes_piloto_20260913"
# Revisão lexical somente leitura do snapshot conhecido, não carregamento
# do perfil para treino nem revalidação de hashes do normalizador histórico.
# O parentesco conservador usa a mesma identidade da importação canônica v4.
REVISAO_HISTORICA = {
    "fonte": "memoria/neural/experimentos/expansao_relacoes_v4_20260908/lote.json",
    "sha256": "f389af34b78ecf540ce551867d27e21191d6855e8113410535a106392fb55a07",
    "casos": 1176, "limiar": 0.9, "pares_exatos": 0, "pares_proximos": 8,
    "caso_relacionado": "arquivo_nome_negado_recusa",
    "ancestral_canonico": "gerador_v4:vontade",
    "natureza": "registro_de_revisao_IA_20260913_nao_certifica_novidade",
}
# Cada trio contrasta a mesma entidade. Ato, verbo e alvo são anotações
# explícitas, não decisões do parser. Ordem: pedido, recusa, relato.
TRIOS = (
    ("app_direto", "APP_OPEN", "open", "Firefox", (
        ("{dono}{v} o {a}.", "Abre"),
        ("Não {dono}{v} o {a} agora.", "abra"),
        ("Ontem pedi para {dono}{v} o {a}; estou apenas relatando.", "abrir"))),
    ("app_cortesia", "APP_OPEN", "open", "Visual Studio Code", (
        ("Por favor, {dono}{v} o {a} para mim.", "abra"),
        ("Prefiro que você não {dono}{v} o {a} neste momento.", "abra"),
        ("Na reunião de ontem, eu tentei {dono}{v} o {a}.", "abrir"))),
    ("app_nome_negado", "APP_OPEN", "open", "Não Feche", (
        ('{dono}{v} o aplicativo "{a}".', "Abra"),
        ('Não quero que você {dono}{v} o aplicativo "{a}".', "abra"),
        ('Mais cedo consegui {dono}{v} o aplicativo "{a}".', "abrir"))),
    ("musica_direto", "MUSIC_SEARCH", "search", "Aquarela", (
        ("{dono}{v} a música {a}.", "Busque"),
        ("Não {dono}{v} a música {a} agora.", "busque"),
        ("Ontem pedi para {dono}{v} a música {a}; estou só contando.", "buscar"))),
    ("musica_cortesia", "MUSIC_SEARCH", "search", "Trem-Bala", (
        ("Por favor, {dono}{v} a faixa {a} para mim.", "procure"),
        ("Prefiro que você não {dono}{v} a faixa {a} neste momento.", "procure"),
        ("Na semana passada, tentei {dono}{v} a faixa {a}.", "procurar"))),
    ("musica_nome_negado", "MUSIC_SEARCH", "search", "Não Volte", (
        ('{dono}{v} a música "{a}".', "Busque"),
        ('Não quero que você {dono}{v} a música "{a}".', "busque"),
        ('Mais cedo consegui {dono}{v} a música "{a}".', "buscar"))),
    ("arquivo_direto", "FILE_READ", "read", "notas.txt", (
        ("{dono}{v} o arquivo {a}.", "Leia"),
        ("Não {dono}{v} o arquivo {a} agora.", "leia"),
        ("Ontem pedi para {dono}{v} o arquivo {a}; estou só relatando.", "ler"))),
    ("arquivo_cortesia", "FILE_READ", "read", "diário da oficina.txt", (
        ('Por favor, {dono}{v} o arquivo "{a}" para mim.', "leia"),
        ('Prefiro que você não {dono}{v} o arquivo "{a}" neste momento.', "leia"),
        ('Na semana passada, tentei {dono}{v} o arquivo "{a}".', "ler"))),
    ("arquivo_nome_negado", "FILE_READ", "read", "não apagar.txt", (
        ('{dono}{v} o arquivo "{a}".', "Leia"),
        ('Não quero que você {dono}{v} o arquivo "{a}".', "leia"),
        ('Mais cedo consegui {dono}{v} o arquivo "{a}".', "ler"))),
)

FORA_PERFIL = (
    ("abre_site", "Abra um site sobre motores elétricos.", "Navegação não é APP_OPEN."),
    ("capacidade", "Você consegue abrir aplicativos?", "Pergunta sobre capacidade, sem pedido nem alvo literal."),
    ("recusa_generica", "Não leia nenhum arquivo.", "Recusa válida no runtime, mas sem alvo literal neste perfil."),
    ("referencia", "Leia aquele de ontem.", "Referência depende de contexto; não fabricar nome de arquivo."),
    ("citacao", 'Compare as frases "abra o editor" e "não abra o editor", sem executar nenhuma.',
     "Análise metalinguística; as citações não são pedidos operacionais."),
    ("condicional", "Se eu pedir amanhã, procure a música Aquarela.",
     "Condição futura; não rotular como autorização presente nem como relato passado."),
)


def _base(identidade: str, grupo: str, texto: str) -> dict:
    ancestrais = [LINHAGEM]
    if identidade == REVISAO_HISTORICA["caso_relacionado"]:
        ancestrais.append(REVISAO_HISTORICA["ancestral_canonico"])
    return {"id": f"{LINHAGEM}_{identidade}", "texto": texto,
            "grupo": f"{LINHAGEM}_{grupo}", "ancestrais": ancestrais,
            "particao": "desenvolvimento", "origem_texto": "sintetico",
            "referencia_texto": f"{__name__}:{identidade}",
            "origem_rotulo": "curadoria_ia", "referencia_rotulo": f"{__name__}:{identidade}",
            "conhecido_no_desenvolvimento": True, "enquadramento": "supervisionado",
            "motivo_fora_perfil": None, "fonte_v4": None, **FLAGS}


def gerar_lote() -> list[dict]:
    """Transporta marcações explícitas pelo construtor canônico de spans."""
    casos = []
    for grupo, intent, action, alvo, formas in TRIOS:
        for ato, (molde, verbo) in zip(("pedido", "recusa", "relato"), formas, strict=True):
            texto, mencoes, inicio = preencher(molde, {"v": verbo, "a": alvo}, {"a": alvo})
            c = _base(f"{grupo}_{ato}", grupo, texto)
            c["fonte_v4"] = {"versao": 4, "texto_entrada": texto, "nos": [{
                "id": "n0", "intent": intent, "action": action, "ato": ato,
                "trecho": {"inicio": 0, "fim": len(texto), "texto": texto},
                "ancora": {"inicio": inicio, "fim": inicio + len(verbo), "texto": verbo},
                "alvos": [mencoes["a"]]}], "relacoes": [], **FLAGS}
            validar_caso(c)
            casos.append(c)
    for identidade, texto, motivo in FORA_PERFIL:
        c = _base(identidade, "fora_perfil", texto)
        c.update(enquadramento="fora_perfil", motivo_fora_perfil=motivo)
        validar_caso(c)
        casos.append(c)
    return casos


def executar(destino: Path) -> dict:
    """Exportação offline exclusiva; não sobrescreve lote nem prepara treino."""
    if destino.exists():
        raise FileExistsError("preservar lote anterior")
    casos = gerar_lote()
    auditoria = auditar_corpus(casos)
    classes = Counter(f"{n['intent']}|{n['action']}|{n['ato']}"
                      for c in casos if c["fonte_v4"] for n in c["fonte_v4"]["nos"])
    itens = [{"text": c["texto"], "family": c["grupo"]} for c in casos]
    lexical = auditar_leakage_dataset(itens, itens)
    pares = [{"a": casos[p["linha_dev"] - 1]["id"],
              "b": casos[p["linha_frozen"] - 1]["id"], "similaridade": p["similaridade"]}
             for p in lexical["duplicados_exatos"] + lexical["quase_duplicados"]
             if p["linha_dev"] < p["linha_frozen"]]
    payload = "".join(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n" for c in casos).encode("utf-8")
    resumo = {"total": len(casos), "cobertura_desenvolvimento": dict(sorted(classes.items())),
              "pares_lexicais_internos": pares, "linhagem_comum": LINHAGEM,
              "projecao": "offsets_brutos_anotados_sem_parser", "auditoria": auditoria,
              "corpus_sha256": hashlib.sha256(payload).hexdigest(),
              "gerador_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "avaliacao_independente": False, "revisao_historica_registrada": REVISAO_HISTORICA,
              "ganho_de_desempenho_medido": False, **FLAGS}
    destino.mkdir(parents=True, exist_ok=False)
    with (destino / "corpus.jsonl").open("xb") as f:
        f.write(payload)
    with (destino / "resumo.json").open("x", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)
    return resumo


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, required=True)
    print(json.dumps(executar(parser.parse_args().destino), ensure_ascii=False))
