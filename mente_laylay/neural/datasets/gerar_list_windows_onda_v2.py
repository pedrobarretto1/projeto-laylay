"""Gera a segunda onda contrastiva de LIST_WINDOWS para extensão aditiva.

O lote é completo e substitui a onda v1 no experimento. Exclui os textos do
caos v27 conhecido, que é regressão de desenvolvimento, não holdout independente.
Não treina command e não concede autoridade operacional.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata
from typing import Any, Iterable

from .gerar_list_windows_onda_v1 import gerar_exemplos as gerar_base_v1


APLICATIVOS_NOVOS = (
    ("o GIMP", "aberto"),
    ("a Cortana", "aberta"),
    ("o Winamp", "aberto"),
    ("a Xbox Game Bar", "aberta"),
    ("o Audacity", "aberto"),
    ("a Epic Games", "aberta"),
    ("o DaVinci Resolve", "aberto"),
    ("a Ubisoft Connect", "aberta"),
    ("o PowerShell", "aberto"),
    ("a Lenovo Vantage", "aberta"),
    ("o Blender", "aberto"),
    ("a Amazon Music", "aberta"),
    ("o Inkscape", "aberto"),
    ("a Microsoft Teams", "aberta"),
    ("o Firefox Developer", "aberto"),
    ("a Radeon Software", "aberta"),
)

MOLDES_CONSULTA_ALVO = (
    ("permanece", "{alvo} permanece {estado}?"),
    ("duvida", "será mesmo que {alvo} está {estado}?"),
    ("gentileza", "por gentileza, verifica se {alvo} continua {estado}?"),
    ("contar", "consegue me contar se {alvo} está {estado}?"),
    ("conferida", "dá uma conferida se {alvo} segue {estado}?"),
    ("confirmar", "eu queria confirmar se {alvo} ficou {estado}?"),
    ("consulta", "consulta aí se {alvo} continua {estado}?"),
    ("execucao", "{alvo} está em execução?"),
    ("necessidade", "só preciso saber se {alvo} está {estado}?"),
    ("verificar", "vê para mim se {alvo} ainda está {estado}?"),
)

CONSULTAS_INVENTARIO = (
    "quais softwares estão abertos neste momento?",
    "enumera os aplicativos em execução",
    "exibe os programas que estão rodando",
    "pode me contar quais softwares seguem abertos?",
    "eu gostaria de ver as janelas dos programas",
    "há algum aplicativo rodando agora?",
    "quantas janelas de programas estão visíveis?",
    "o que continua em execução no computador?",
    "mostre somente os softwares com janela",
    "confere a lista dos apps abertos",
    "informa quais processos possuem janela",
    "quero saber os programas abertos neste instante",
    "lista para mim os softwares visíveis",
    "tem programas rodando por aí?",
    "exibe tudo que está aberto na área de trabalho",
)

CONSULTAS_CONTEXTO = (
    "confere se ele ainda está em execução?",
    "vê se ela permaneceu aberta?",
    "consulta se ele continua rodando?",
    "me conta se ela ficou aberta?",
    "pode confirmar se ele segue aberto?",
    "verifica se ela ainda está rodando?",
)

ENTIDADES_NAO_APLICATIVO = (
    ("a cancela", "aberta"),
    ("o cadastro", "aberto"),
    ("a candidatura", "aberta"),
    ("meu protocolo", "aberto"),
    ("a discussão", "aberta"),
    ("o documento", "aberto"),
    ("a guia do manual", "aberta"),
    ("o inventário da partida", "aberto"),
    ("a matrícula", "aberta"),
    ("o processo seletivo", "aberto"),
    ("a janela da cozinha", "aberta"),
    ("o chamado técnico", "aberto"),
    ("a garagem", "aberta"),
    ("o portão", "aberto"),
    ("a loja", "aberta"),
    ("o prazo", "aberto"),
    ("a conta bancária", "aberta"),
    ("o tópico", "aberto"),
    ("a sessão", "aberta"),
    ("o edital", "aberto"),
    ("a vaga", "aberta"),
    ("o pedido", "aberto"),
    ("a conversa", "aberta"),
    ("o ferimento", "aberto"),
)

MOLDES_NAO_APLICATIVO = (
    ("direta", "{alvo} está {estado}?"),
    ("continua", "{alvo} continua {estado}?"),
    ("permanece", "{alvo} permanece {estado}?"),
    ("duvida", "será mesmo que {alvo} está {estado}?"),
    ("confere", "confere se {alvo} segue {estado}?"),
    ("ainda", "{alvo} ainda está {estado}?"),
)

# Textos do caos conhecido ficam fora do treino; ele já orientou a pesquisa.
# A chave preserva os contrastes de interrogação final e citação total.
FRASES_CAOS_RESERVADAS = (
    "O Opera está aberto?", "A Calculadora continua aberta?",
    "O VLC ainda está aberto?", "O Discord ainda está rodando?",
    "A Microsoft Store ainda está aberta?", "O OBS Studio tá rodando?",
    "A Ferramenta de Recortes permanece aberta?", "O editor Krita segue aberto?",
    "O Notepad++ está em execução?", "O cliente Steam continua rodando?",
    "O Explorador de Arquivos ainda tá aberto?", "A janela do Spotify está aberta?",
    "O Painel de Controle está aberto?", "O Visual Studio Code continua aberto?",
    "O Gerenciador de Tarefas ainda está rodando?", "O aplicativo Fotos tá aberto?",
    "O navegador Brave permanece aberto?", "O terminal Windows segue rodando?",
    "Será que o Opera está aberto?", "Por acaso a Calculadora continua aberta?",
    "Você pode me dizer se o VLC está aberto?", "Me diz se o Discord está rodando?",
    "Só quero saber se a Microsoft Store está aberta.",
    "Confere para mim se o OBS Studio continua aberto.",
    "Dá uma olhada se o Krita ainda está aberto.", "O Opera está aberto???",
    "\"O Opera está aberto?\"", "O OPERA ESTÁ ABERTO?", "opera tá aberto?",
    "calculadora continua aberta", "O VLC está aberto?", "Ele continua aberto?",
    "Confere se ele ficou aberto.", "A Calculadora está aberta?",
    "Ela ainda está aberta?", "Confirma se ela continua aberta.",
    "Quais programas estão abertos?", "Quais aplicativos estão rodando?",
    "Lista as janelas abertas.", "Mostra os apps em execução.",
    "Que processos estão rodando?", "Pode listar os programas abertos?",
    "Eu queria saber quais janelas estão abertas.",
    "Quantos programas estão abertos?", "Tem alguma janela aberta?",
    "O que está aberto no computador?",
    "Mostra só os aplicativos com janela visível.",
    "Quais programas continuam abertos agora?", "O Opera está aberto.",
    "Eu deixei o Opera aberto.", "A porta está aberta?",
    "A inscrição continua aberta?", "Meu chamado ainda está aberto?",
    "O assunto continua aberto.", "Estou aberto a sugestões.",
    "O arquivo relatório está aberto?", "A aba da documentação está aberta?",
    "O menu do jogo está aberto?", "Não quero saber se o Opera está aberto.",
    "Nem precisa verificar se a Calculadora está aberta.",
    "Não confira se o VLC continua aberto.",
    "Eu não perguntei se o Discord está aberto.",
    "A frase \"o Opera está aberto?\" é apenas um exemplo.",
    "Como eu perguntaria se o Opera está aberto?",
    "Você consegue verificar programas abertos?",
    "Abrir o Opera deixaria ele mais rápido?",
    "Não feche o Opera só porque ele está aberto.",
    "Se eu disser \"o Opera está aberto?\", isso é uma consulta.",
    "A palavra aberto aparece aqui, mas não consulte nada.",
    "Não liste os programas abertos.",
)


def _normalizar(texto: object) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", base)).strip()


def _chave_texto(texto: object) -> str:
    bruto = str(texto or "").strip()
    citacao_total = bool(
        len(bruto) >= 2
        and (
            (bruto.startswith("\"") and bruto.endswith("\""))
            or (bruto.startswith("“") and bruto.endswith("”"))
            or (bruto.startswith("'") and bruto.endswith("'"))
            or (bruto.startswith("‘") and bruto.endswith("’"))
        )
    )
    return "|".join((
        _normalizar(bruto),
        "interrogacao" if bruto.endswith("?") else "sem_interrogacao",
        "citacao" if citacao_total else "sem_citacao",
    ))


def _exemplo(
    texto: str,
    *,
    positivo: bool,
    familia: str,
    grupo: str,
    entidade: str,
    negado: bool = False,
    escopo_negativo: str = "contraste",
    ato_consulta: bool | None = None,
    dominio_app: bool | None = None,
) -> dict[str, Any]:
    fator_ato = positivo if ato_consulta is None else bool(ato_consulta)
    fator_dominio = positivo if dominio_app is None else bool(dominio_app)
    return {
        "text": texto,
        "intent": "LIST_WINDOWS" if positivo else "NONE",
        "is_command": positivo,
        "negated": bool(negado),
        "action": "list" if positivo else "none",
        "family": familia,
        "validation_group": grupo,
        "validation_entity_group": entidade,
        "extension_scope": "consulta_ativa" if positivo else escopo_negativo,
        "source": "MANUAL_PARAPHRASE" if positivo else "HARD_NEGATIVE",
        "domain": "app",
        "training_heads": (
            ["action", "intent", "intent_gate"]
            if positivo
            else ["intent", "intent_gate"]
        ),
        "extension_factors": {
            "ato_consulta": fator_ato,
            "dominio_app": fator_dominio,
        },
    }


def gerar_exemplos() -> list[dict[str, Any]]:
    reservadas = {_chave_texto(texto) for texto in FRASES_CAOS_RESERVADAS}
    exemplos: list[dict[str, Any]] = []
    for original in gerar_base_v1():
        if _chave_texto(original["text"]) in reservadas:
            continue
        positivo = bool(
            original.get("intent") == "LIST_WINDOWS"
            and not original.get("negated")
        )
        item = dict(original)
        item.update({
            "intent": "LIST_WINDOWS" if positivo else "NONE",
            "is_command": positivo,
            "negated": bool(original.get("negated")),
            "action": "list" if positivo else "none",
            "extension_scope": (
                "consulta_ativa" if positivo else "contraste_base_v1"
            ),
            "source": "MANUAL_PARAPHRASE" if positivo else "HARD_NEGATIVE",
            "training_heads": (
                ["action", "intent", "intent_gate"]
                if positivo
                else ["intent", "intent_gate"]
            ),
            "extension_factors": {
                "ato_consulta": positivo,
                "dominio_app": True,
            },
        })
        exemplos.append(item)

    for mecanismo, molde in MOLDES_CONSULTA_ALVO:
        grupo = f"list_windows_v2_consulta_{mecanismo}"
        for indice, (alvo, estado) in enumerate(APLICATIVOS_NOVOS):
            exemplos.append(_exemplo(
                molde.format(alvo=alvo, estado=estado),
                positivo=True,
                familia=f"{grupo}_{indice // 2}",
                grupo=grupo,
                entidade=f"app:{_normalizar(alvo)}",
            ))

    for indice, texto in enumerate(CONSULTAS_INVENTARIO):
        exemplos.append(_exemplo(
            texto,
            positivo=True,
            familia=f"list_windows_v2_inventario_{indice}",
            grupo=f"list_windows_v2_inventario_mecanismo_{indice}",
            entidade=f"inventario:{indice // 3}",
        ))

    for indice, texto in enumerate(CONSULTAS_CONTEXTO):
        exemplos.append(_exemplo(
            texto,
            positivo=True,
            familia=f"list_windows_v2_contexto_{indice}",
            grupo=f"list_windows_v2_contexto_{indice // 2}",
            entidade="referente:pronome",
        ))

    for indice, (alvo, estado) in enumerate(APLICATIVOS_NOVOS):
        entidade = f"app:{_normalizar(alvo)}"
        for mecanismo, molde in (
            ("afirmacao", "{alvo} está {estado}."),
            ("crenca", "acho que {alvo} continua {estado}."),
            ("permanencia", "{alvo} permanece {estado}."),
            ("passado", "ontem {alvo} estava {estado}."),
            ("citacao", "\"{alvo} está {estado}?\""),
            ("metalinguagem", "como se escreve a pergunta se {alvo} está {estado}?"),
            ("descricao_frase", "a frase {alvo} está {estado} é uma pergunta"),
            ("hipotese_estado", "se {alvo} estivesse {estado}, seria melhor?"),
            ("hipotese_abrir", "abrir {alvo} faria ele ficar mais rápido?"),
            ("recusa_saber", "não quero confirmar se {alvo} está {estado}."),
            ("recusa_verificar", "não precisa consultar se {alvo} continua {estado}."),
        ):
            grupo = f"list_windows_v2_negativo_{mecanismo}"
            exemplos.append(_exemplo(
                molde.format(alvo=alvo, estado=estado),
                positivo=False,
                familia=f"{grupo}_{indice // 2}",
                grupo=grupo,
                entidade=entidade,
                negado=mecanismo.startswith("recusa_"),
                escopo_negativo=f"contraste_{mecanismo}",
                ato_consulta=False,
                dominio_app=True,
            ))

    for mecanismo, molde in MOLDES_NAO_APLICATIVO:
        grupo = f"list_windows_v2_fora_app_{mecanismo}"
        for indice, (alvo, estado) in enumerate(ENTIDADES_NAO_APLICATIVO):
            exemplos.append(_exemplo(
                molde.format(alvo=alvo, estado=estado),
                positivo=False,
                familia=f"{grupo}_{indice // 2}",
                grupo=grupo,
                entidade=f"fora_app:{_normalizar(alvo)}",
                escopo_negativo="contraste_entidade",
                ato_consulta=True,
                dominio_app=False,
            ))

    for indice, texto in enumerate((
        "qual planilha está aberta?",
        "exibe as guias abertas do navegador",
        "o painel da corrida está visível?",
        "quais candidaturas continuam abertas?",
        "enumera os documentos abertos",
        "que debates seguem em aberto?",
        "a janela do quarto está aberta?",
        "a entrada lateral continua aberta?",
        "o inventário da fase está aberto?",
    )):
        exemplos.append(_exemplo(
            texto,
            positivo=False,
            familia=f"list_windows_v2_operacao_vizinha_{indice}",
            grupo=f"list_windows_v2_operacao_vizinha_{indice}",
            entidade=f"operacao_vizinha:{indice}",
            escopo_negativo="contraste_operacao_vizinha",
            ato_consulta=True,
            dominio_app=False,
        ))
    return exemplos


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, int]:
    itens = [dict(item) for item in exemplos]
    textos = [_chave_texto(item.get("text")) for item in itens]
    repetidos = [texto for texto, total in Counter(textos).items() if total > 1]
    if repetidos:
        raise ValueError(f"o lote v2 contém textos duplicados: {repetidos[:3]}")
    reservadas = {_chave_texto(texto) for texto in FRASES_CAOS_RESERVADAS}
    if reservadas & set(textos):
        raise ValueError("o caos reservado entrou no treino v2")
    if any("command" in item.get("training_heads", ()) for item in itens):
        raise ValueError("o lote v2 não pode treinar command")
    if any("autoriza_execucao" in item for item in itens):
        raise ValueError("dataset não pode conceder autoridade")
    if any(not item.get("validation_group") for item in itens):
        raise ValueError("todo exemplo precisa de validation_group")
    if any(not item.get("validation_entity_group") for item in itens):
        raise ValueError("todo exemplo precisa de validation_entity_group")
    if any(
        set(item.get("extension_factors") or {})
        != {"ato_consulta", "dominio_app"}
        for item in itens
    ):
        raise ValueError("todo exemplo precisa dos dois fatores da extensão")
    positivos = [item for item in itens if item.get("intent") == "LIST_WINDOWS"]
    negativos = [item for item in itens if item.get("intent") == "NONE"]
    if any(item.get("extension_scope") != "consulta_ativa" for item in positivos):
        raise ValueError("positivo fora do escopo consulta_ativa")
    resumo = {
        "total": len(itens),
        "positivos": len(positivos),
        "negativos": len(negativos),
        "familias": len({item["family"] for item in itens}),
        "grupos_validacao": len({item["validation_group"] for item in itens}),
        "grupos_entidade": len({item["validation_entity_group"] for item in itens}),
        "colisoes_caos": len(reservadas & set(textos)),
        "treina_command": sum(
            "command" in item.get("training_heads", ()) for item in itens
        ),
        "ato_consulta_positivo": sum(
            item["extension_factors"]["ato_consulta"] for item in itens
        ),
        "dominio_app_positivo": sum(
            item["extension_factors"]["dominio_app"] for item in itens
        ),
    }
    if resumo["positivos"] < 250 or resumo["negativos"] < 300:
        raise ValueError(f"cobertura insuficiente: {resumo!r}")
    return resumo


def escrever_lote(destino: str | Path) -> dict[str, int]:
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    caminho = Path(destino)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conteudo = "".join(
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
        for item in exemplos
    )
    descritor, temporario = tempfile.mkstemp(
        prefix=f".{caminho.name}.", suffix=".tmp", dir=str(caminho.parent)
    )
    try:
        with os.fdopen(descritor, "w", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(conteudo)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        Path(temporario).replace(caminho)
    except Exception:
        Path(temporario).unlink(missing_ok=True)
        raise
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default=(
            "mente_laylay/neural/datasets/candidatos/"
            "list_windows_onda_v2.jsonl"
        ),
    )
    args = parser.parse_args()
    resumo = escrever_lote(args.destino)
    print(json.dumps({"destino": args.destino, **resumo}, ensure_ascii=False))


if __name__ == "__main__":
    main()
