"""Lote sintético de desenvolvimento: supervisão explícita, sem fit ou reserva.

O marcador vazio de dono é escrito no molde, antes do verbo da ação anotada.
Ele apenas transporta sua posição para o segmento canônico correspondente:
modalidade, veto e previsões nunca escolhem o rótulo ou o dono esperado.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from string import Formatter

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from .qualidade import auditar_leakage_dataset
from .revisar_vinculos_segmentos import vincular_plano_manual

PARES = (("zafrin", "pelvora"), ("mezdar", "tuvlen"))
MOLDES = (
    ("pedido_apos_exclusao", "pedido", "não {verbo} {b}; {dono}{verbo} {a}"),
    ("pedido_antes_exclusao", "pedido", "{dono}{verbo} {a}; não {verbo} {b}"),
    ("pedido_escolha", "pedido", "{b} fica fora da escolha; {dono}{verbo} {a}"),
    ("pedido_correcao", "pedido", "{dono}{verbo} {a}; {b} não é o que pedi"),
    ("recusa_estado", "recusa", "não {dono}{verbo} {a}; estou pedindo para deixar tudo como está"),
    ("recusa_apos_estado", "recusa", "a minha orientação é manter tudo como está; não {dono}{verbo} {a}"),
    ("recusa_vontade", "recusa", "por enquanto não quero que você {dono}{verbo} {a}"),
    ("recusa_cancelamento", "recusa", "cancele a ideia de {dono}{infinitivo} {a}"),
    ("relato_passado", "relato", "ela contou que ontem tentou {dono}{infinitivo} {a}; estou só relatando o ocorrido"),
    ("relato_lembranca", "relato", "isto é uma lembrança e não um pedido: ontem pedi para {dono}{infinitivo} {a}"),
    ("relato_registro", "relato", "no registro consta que alguém foi {dono}{infinitivo} {a}; não execute nada agora"),
    ("relato_teste", "relato", "o teste de ontem incluía a instrução de {dono}{infinitivo} {a}"),
)
VARIANTES = {("APP_OPEN", "open"), ("MUSIC_SEARCH", "search"), ("FILE_READ", "read")}


def preencher(molde: str, valores: dict[str, str], alvos: dict[str, str]) -> tuple[str, dict, int]:
    """Offsets por construção do texto, sem procurar ou adivinhar entidades."""
    texto, mencoes, dono = "", {}, None
    for literal, campo, formato, conversao in Formatter().parse(molde):
        texto += literal
        if campo is None:
            continue
        if formato or conversao:
            raise ValueError("molde não permite transformação implícita")
        if campo == "dono":
            if dono is not None:
                raise ValueError("dono duplicado")
            dono = len(texto)
            continue
        valor = valores[campo]
        if campo in alvos:
            if campo in mencoes or valor.count(alvos[campo]) != 1:
                raise ValueError("slot repetido ou ambíguo")
            inicio = len(texto) + valor.index(alvos[campo])
            mencoes[campo] = {"inicio": inicio, "fim": inicio + len(alvos[campo]), "texto": alvos[campo]}
        texto += valor
    if dono is None or not 0 <= dono < len(texto):
        raise ValueError("molde sem âncora explícita de dono")
    return texto, mencoes, dono


def gerar_lote() -> list[dict]:
    casos = []
    for entidade, (a, b) in enumerate(PARES):
        dominios = (
            ("apps", "APP_OPEN", "open", "abra", "abrir", "o aplicativo", a, b),
            ("musica", "MUSIC_SEARCH", "search", "toque", "tocar", "a faixa", f"não volte {a}", f"não volte {b}"),
            ("arquivos", "FILE_READ", "read", "leia", "ler", "o arquivo", f"não apagar {a}.txt", f"não apagar {b}.txt"),
        )
        for dominio, intent, action, verbo, infinitivo, objeto, alvo_a, alvo_b in dominios:
            for aspas in (False, True):
                for familia, ato, molde in MOLDES:
                    nomes = {"a": alvo_a, "b": alvo_b}
                    valores = {k: objeto + " " + ('"' + v + '"' if aspas else v) for k, v in nomes.items()}
                    texto, mencoes, dono = preencher(molde, {**valores, "verbo": verbo, "infinitivo": infinitivo}, nomes)
                    acao = {"intent": intent, "action": action, "ato": ato,
                            "resolucao_alvo": "explicito" if ato == "pedido" else "nao_aplicavel",
                            "alvos_solicitados": [mencoes["a"]] if ato == "pedido" else [],
                            "alvos_excluidos": [mencoes["b" if ato == "pedido" else "a"]] if ato != "relato" else [],
                            "alvos_mencionados": [mencoes["a"]] if ato == "relato" else []}
                    casos.append({"id": f"estr_v3_{familia}_{dominio}_e{entidade}_q{int(aspas)}",
                                  "particao": "desenvolvimento", "dominio": dominio,
                                  "grupo_construcao": familia, "grupo_entidades": f"rel_v2_e{entidade}",
                                  "grupo_contraste": f"estr_v3_{familia}_{dominio}_e{entidade}",
                                  "ato": ato, "texto_entrada": texto, "ancora_dono": dono,
                                  "segmentos": [{"indice": 0, "texto": texto, "acoes": [acao]}]})
    return casos


def alinhar(caso: dict) -> dict:
    texto = caso["texto_entrada"]
    turno = classificar_modalidade_turno(texto, texto_tem_comando_explicito=texto_tem_comando_explicito)
    intervalos, fim_anterior = {}, 0
    for s in turno["segmentos"]:
        # Apenas correspondência literal única e monotônica; nunca fuzzy.
        if texto.count(s["texto"]) != 1:
            raise ValueError("segmento não possui posição literal única")
        inicio = texto.index(s["texto"])
        if inicio < fim_anterior:
            raise ValueError("segmentação sobreposta ou fora de ordem")
        fim_anterior = inicio + len(s["texto"])
        intervalos[s["indice"]] = (inicio, fim_anterior)
    donos = [i for i, (a, b) in intervalos.items() if a <= caso["ancora_dono"] < b]
    if len(donos) != 1:
        raise ValueError("âncora de autoria não chegou a um segmento único")
    a = caso["segmentos"][0]["acoes"][0]
    r = vincular_plano_manual(caso, turno, intervalos=intervalos,
                              donos={(a["intent"], a["action"]): donos[0]},
                              variantes_permitidas=VARIANTES)
    r.update(papel_dataset="desenvolvimento", revisao_semantica="moldes_assistidos_por_ia_sem_scores",
             ancora_dono_fonte=caso["ancora_dono"])
    return r


def agrupar_sem_leakage(casos: list[dict]) -> tuple[dict[str, str], dict]:
    itens = [{"text": c["texto_entrada"], "family": c["grupo_construcao"]} for c in casos]
    auditoria = auditar_leakage_dataset(itens, itens, limiar_similaridade=0.9)
    pais = {c["grupo_construcao"]: c["grupo_construcao"] for c in casos}

    def raiz(g):
        while pais[g] != g:
            g = pais[g]
        return g

    pares = []
    for p in auditoria["duplicados_exatos"] + auditoria["quase_duplicados"]:
        i, j = p["linha_dev"] - 1, p["linha_frozen"] - 1
        if i >= j:
            continue
        a, b = casos[i]["grupo_construcao"], casos[j]["grupo_construcao"]
        if a != b:
            pares.append({"id_a": casos[i]["id"], "id_b": casos[j]["id"], "similaridade": p["similaridade"]})
            ra, rb = sorted((raiz(a), raiz(b)))
            pais[rb] = ra
    grupos = {c["id"]: "estr_v3_" + raiz(c["grupo_construcao"]) for c in casos}
    # A autoauditoria é um grafo de proximidade, NÃO prova de holdout independente.
    return grupos, {"limiar": 0.9, "pares_entre_moldes": pares,
                    "grupos_finais": dict(Counter(grupos.values())),
                    "independencia_semantica_certificada": False}


def executar(destino: Path) -> dict:
    casos = gerar_lote()
    destino.mkdir(parents=True, exist_ok=False)
    flags = {"treino_permitido": False, "autoriza_execucao": False, "autoriza_promocao": False}
    with (destino / "lote_fonte.json").open("x", encoding="utf-8") as f:
        json.dump({"casos": casos, **flags}, f, ensure_ascii=False, indent=2)
    raiz = Path(__file__).parent
    fontes = [Path(__file__), raiz / "qualidade.py", raiz / "revisar_vinculos_segmentos.py",
              raiz / "anotacao_escopo.py", raiz.parent / "cognicao/modalidade_turno.py",
              raiz.parent / "autonomia/porteiro_acoes.py", destino / "lote_fonte.json"]
    protocolo = {"moldes": MOLDES, "total": len(casos), "limiar": 0.9,
                 "agrupamento": "família inteira + fecho transitivo de proximidade lexical >= 0.9",
                 "fontes": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in fontes},
                 "reserva_usada": False, "modelo_consultado": False, **flags}
    with (destino / "protocolo.json").open("x", encoding="utf-8") as f:
        json.dump(protocolo, f, ensure_ascii=False, indent=2)
    grupos, auditoria = agrupar_sem_leakage(casos)
    alinhados, falhas = [], []
    for c in casos:
        try:
            a = alinhar(c)
            a.update(grupo_validacao=grupos[c["id"]], grupo_construcao=c["grupo_construcao"],
                     grupo_entidades=c["grupo_entidades"], grupo_contraste=c["grupo_contraste"])
            alinhados.append(a)
        except ValueError as exc:
            falhas.append({"id": c["id"], "erro": str(exc)})
    suportes = []
    for g in sorted(set(grupos.values())):
        treino = [a for a in alinhados if a["grupo_validacao"] != g]
        suportes.append({"teste_grupo": g, "casos_treino": len(treino),
                         "atos_treino": dict(Counter(acao["ato"] for a in treino
                            for s in a["anotacao"]["segmentos"] for acao in s["acoes"])),
                         "donos_treino": dict(Counter(s["indice"] for a in treino
                            for s in a["anotacao"]["segmentos"] for acao in s["acoes"]))})
    r = {"total": len(casos), "alinhados": len(alinhados), "falhas": falhas,
         "casos": alinhados, "agrupamento": auditoria, "suporte_leave_group_out": suportes,
         "modelo_avaliado": False, "reserva_usada": False, **flags}
    with (destino / "auditoria.json").open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, required=True)
    r = executar(parser.parse_args().destino)
    print(json.dumps({k: r[k] for k in ("total", "alinhados", "falhas", "agrupamento", "suporte_leave_group_out")}, ensure_ascii=False))
