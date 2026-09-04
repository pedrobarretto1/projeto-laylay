"""Gera comandos fora do catálogo para calibrar rejeição, nunca para treino."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


OPERACOES_FORA_CATALOGO: dict[tuple[str, str], tuple[str, ...]] = {
    ("email_send", "email"): (
        "envia um email para a Ana",
        "manda o relatório por email para o financeiro",
        "responde o email do João",
        "encaminha essa mensagem para a equipe",
        "escreve um email avisando que vou atrasar",
    ),
    ("email_archive", "email"): (
        "arquiva o email da imobiliária",
        "marca essa mensagem como não lida",
        "move o email do banco para spam",
        "apaga os emails promocionais",
        "coloca uma estrela no email da viagem",
    ),
    ("calendar_create", "calendar"): (
        "cria uma reunião amanhã às nove",
        "agenda dentista para sexta-feira",
        "marca uma conversa com a equipe à tarde",
        "adiciona meu aniversário no calendário",
        "reserva meia hora para estudar Python",
    ),
    ("calendar_cancel", "calendar"): (
        "cancela a reunião de amanhã",
        "remove o dentista do calendário",
        "adia o compromisso para segunda-feira",
        "exclui o evento do almoço",
        "desmarca a conversa com a equipe",
    ),
    ("reminder_create", "reminder"): (
        "me lembra de pagar a conta amanhã",
        "cria um lembrete para beber água",
        "avisa quando for hora do remédio",
        "lembra de ligar para minha mãe à noite",
        "anota um lembrete para renovar o domínio",
    ),
    ("timer_start", "timer"): (
        "inicia um cronômetro de vinte minutos",
        "coloca um timer de cinco minutos",
        "conta dez minutos a partir de agora",
        "começa uma contagem de meia hora",
        "dispara um temporizador de quarenta segundos",
    ),
    ("alarm_set", "alarm"): (
        "coloca um alarme para sete horas",
        "me acorda amanhã às seis",
        "ativa um alarme para o meio-dia",
        "muda meu despertador para oito e meia",
        "cancela o alarme de domingo",
    ),
    ("note_create", "notes"): (
        "cria uma nota com a lista do mercado",
        "anota que o servidor vence em outubro",
        "salva uma nota chamada ideias do projeto",
        "registra esse endereço nas minhas notas",
        "escreve uma nota com os pontos da reunião",
    ),
    ("note_delete", "notes"): (
        "apaga a nota da lista antiga",
        "remove minhas anotações de teste",
        "exclui a nota sobre a viagem",
        "limpa o conteúdo da nota temporária",
        "renomeia a nota ideias para backlog",
    ),
    ("message_send", "messaging"): (
        "manda uma mensagem para o Pedro",
        "responde a Júlia dizendo que já cheguei",
        "envia um oi no grupo da família",
        "avisa o Carlos que a reunião mudou",
        "compartilha esse texto com a equipe",
    ),
    ("phone_call", "phone"): (
        "liga para a Ana",
        "faz uma chamada para o consultório",
        "telefona para minha mãe",
        "retorna a ligação do escritório",
        "inicia uma chamada de vídeo com a equipe",
    ),
    ("wifi_control", "system"): (
        "desliga o wi-fi",
        "conecta na rede da sala",
        "esquece a rede do vizinho",
        "liga o wi-fi do computador",
        "troca para a rede de cinco gigahertz",
    ),
    ("bluetooth_control", "system"): (
        "ativa o bluetooth",
        "pareia meus fones de ouvido",
        "desconecta a caixa de som bluetooth",
        "remove esse controle dos dispositivos pareados",
        "procura dispositivos bluetooth próximos",
    ),
    ("brightness_control", "system"): (
        "aumenta o brilho da tela",
        "reduz a luminosidade do monitor",
        "coloca o brilho em cinquenta por cento",
        "ativa o brilho automático",
        "deixa a tela menos clara",
    ),
    ("screenshot_capture", "system"): (
        "tira uma captura de tela",
        "faz um print da janela atual",
        "captura somente esta área da tela",
        "salva uma imagem do que está aparecendo",
        "fotografa a tela inteira",
    ),
    ("session_control", "system"): (
        "bloqueia o computador",
        "reinicia o Windows",
        "desliga o computador",
        "encerra minha sessão",
        "coloca o notebook para dormir",
    ),
    ("file_delete", "files"): (
        "apaga o arquivo temporário",
        "remove a planilha antiga",
        "exclui a pasta de testes",
        "manda esse documento para a lixeira",
        "limpa os arquivos de cache",
    ),
    ("file_move", "files"): (
        "move o relatório para a pasta projetos",
        "copia a planilha para o pendrive",
        "transfere as fotos para a pasta viagens",
        "leva esse documento para a área de trabalho",
        "duplica o arquivo de configuração",
    ),
    ("file_rename", "files"): (
        "renomeia o relatório para versão final",
        "muda o nome da pasta para arquivos antigos",
        "chama essa planilha de orçamento dois",
        "troca o nome do documento para contrato revisado",
        "altera o nome do arquivo de configuração",
    ),
    ("browser_bookmark", "browser"): (
        "adiciona esta página aos favoritos",
        "remove o site dos favoritos",
        "salva este endereço nos marcadores",
        "cria uma pasta de favoritos chamada trabalho",
        "exporta meus favoritos do navegador",
    ),
}

MOLDURAS_HOLDOUT = (
    "por favor, {texto}",
    "{texto}, por gentileza",
    "se puder, {texto}",
    "quando puder, {texto}",
    "{texto} agora, por favor",
)


def gerar_exemplos() -> list[dict[str, Any]]:
    exemplos: list[dict[str, Any]] = []
    for (familia, dominio), frases in OPERACOES_FORA_CATALOGO.items():
        for indice, texto in enumerate(frases):
            base = {
                "family": f"ood_v0_{familia}",
                "domain": dominio,
                "expected_ood": True,
                "source": "OOD_CURATED",
            }
            exemplos.append({**base, "text": texto, "partition": "calibration"})
            exemplos.append(
                {
                    **base,
                    "text": MOLDURAS_HOLDOUT[indice].format(texto=texto),
                    "partition": "evaluation",
                }
            )
    return exemplos


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", base)).strip()


def validar_lote(exemplos: Iterable[dict[str, Any]]) -> dict[str, int]:
    itens = [dict(item) for item in exemplos]
    textos = [_normalizar(item.get("text", "")) for item in itens]
    familias = Counter(str(item.get("family") or "") for item in itens)
    particoes = Counter(str(item.get("partition") or "") for item in itens)
    if len(textos) != len(set(textos)):
        raise ValueError("dataset OOD contém textos duplicados")
    if any(item.get("expected_ood") is not True for item in itens):
        raise ValueError("todo exemplo precisa declarar expected_ood=true")
    resumo = {
        "total": len(itens),
        "familias": len(familias),
        "calibration": particoes["calibration"],
        "evaluation": particoes["evaluation"],
        "max_exemplos_por_familia": max(familias.values(), default=0),
    }
    esperado = {
        "total": 200,
        "familias": 20,
        "calibration": 100,
        "evaluation": 100,
        "max_exemplos_por_familia": 10,
    }
    if resumo != esperado:
        raise ValueError(f"cobertura OOD inesperada: {resumo}")
    return resumo


def gravar(destino: str | Path) -> dict[str, int]:
    exemplos = gerar_exemplos()
    resumo = validar_lote(exemplos)
    caminho = Path(destino)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_text(
        "".join(
            json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n"
            for item in exemplos
        ),
        encoding="utf-8",
    )
    temporario.replace(caminho)
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destino",
        default=str(Path(__file__).with_name("ood_calibracao_v0.jsonl")),
    )
    args = parser.parse_args()
    print(json.dumps(gravar(args.destino), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
