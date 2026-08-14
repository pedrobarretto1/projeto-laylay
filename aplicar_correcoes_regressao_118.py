#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aplicador das correções reproduzidas pelo roteiro de 118 turnos da Laylay.

Corrige:
1) "O Opera continua aberto?" -> consulta somente leitura antes do roteador operacional.
2) "Essa também." -> preserva operações aditivas referenciáveis no histórico,
   mesmo após MEDIA_CONTROL sobrescrever o foco do domínio música.
3) lembrete_ja_agendado -> no-op confirmado, sem fala contraditória de falha/incerteza.

O script valida todos os alvos antes de escrever, cria backup, compila os
arquivos alterados e tenta executar testes focados quando pytest está disponível.
"""

from __future__ import annotations

import argparse
import ast
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable


ARQUIVOS_OBRIGATORIOS = (
    Path("mente_laylay/autonomia/comandos_imediatos.py"),
    Path("mente_laylay/memoria_mental/continuidade_geral.py"),
    Path("mente_laylay/memoria_mental/resultado_acao.py"),
    Path("mente_laylay/autonomia/adaptador_resultado.py"),
    Path("mente_laylay/personalidade/planejador_resposta.py"),
    Path("mente_laylay/personalidade/confirmacao_llm.py"),
)
ARQUIVO_TESTE = Path("tests/test_regressoes_roteiro_118.py")
MARCADOR_VERSAO = "REGRESSAO_118_V1_20260814"


class ErroAplicacao(RuntimeError):
    pass


@dataclass
class Mudanca:
    caminho: Path
    descricao: str
    transformador: Callable[[str], tuple[str, bool]]


def tem_raiz_laylay(raiz: Path) -> bool:
    return raiz.is_dir() and all((raiz / rel).is_file() for rel in ARQUIVOS_OBRIGATORIOS)


def _candidatos_raiz(inicio: Path):
    vistos: set[Path] = set()
    inicio = inicio.resolve()
    for candidato in (inicio, *inicio.parents):
        if candidato not in vistos:
            vistos.add(candidato)
            yield candidato
    for base in (inicio, inicio.parent):
        try:
            filhos = list(base.iterdir())
        except OSError:
            continue
        for filho in filhos:
            if filho.is_dir() and filho not in vistos:
                vistos.add(filho)
                yield filho


def localizar_raiz(root_arg: str | None) -> Path:
    if root_arg:
        raiz = Path(root_arg).expanduser().resolve()
        if not tem_raiz_laylay(raiz):
            raise ErroAplicacao(f"A pasta informada não parece ser a raiz da Laylay: {raiz}")
        return raiz
    for origem in (Path.cwd(), Path(__file__).resolve().parent):
        for candidato in _candidatos_raiz(origem):
            if tem_raiz_laylay(candidato):
                return candidato
    raise ErroAplicacao(
        "Não encontrei automaticamente a raiz da Laylay.\n"
        "Coloque este arquivo na raiz do projeto ou execute com:\n"
        '  python aplicar_correcoes_regressao_118.py --root "C:\\caminho\\projeto-laylay"'
    )


def substituir_exato(texto: str, antigo: str, novo: str, *, nome_patch: str) -> tuple[str, bool]:
    quantidade = texto.count(antigo)
    if quantidade != 1:
        raise ErroAplicacao(
            f"{nome_patch}: esperava exatamente 1 bloco-alvo, encontrei {quantidade}. "
            "O código pode ter mudado; por segurança nada será escrito."
        )
    return texto.replace(antigo, novo, 1), True


def patch_prioridade_consulta_app(texto: str) -> tuple[str, bool]:
    if "PRIORIDADE:SISTEMA:LEITURA" in texto:
        return texto, False
    antigo = '''        # Uma frase pode pedir duas habilidades cooperando no mesmo turno.
        # O ciclo canônico já sabia segmentar e executar a cadeia, mas essa
        # porta nunca era chamada pela fase prioritária; por isso o texto
        # inteiro escapava para a conversa e a Laylay às vezes confirmava uma
        # etapa inexistente. Cada trecho volta ao mesmo resolvedor canônico e
        # mantém suas próprias evidências, permissões e resultados.
        processar_cadeia = ns.get("processar_comandos_em_cadeia")
'''
    novo = '''        # Consultas locais de estado são somente leitura e precisam vencer
        # o roteador operacional genérico. Sem esta barreira, perguntas como
        # "O Opera continua aberto?" podem ser consumidas como APP_OPEN antes
        # de processar_consulta_sistema_local ter chance de responder.
        # REGRESSAO_118_V1_20260814 | PRIORIDADE:SISTEMA:LEITURA
        try:
            tratado_sistema, rota_sistema = processar_consulta_sistema_local(
                contexto_prioritario, texto
            )
        except Exception as erro:
            print(
                "⚠️ [PRIORIDADE:SISTEMA:LEITURA] consulta local falhou sem "
                f"bloquear o turno: {type(erro).__name__}: {erro}"
            )
        else:
            if tratado_sistema:
                print(
                    "⚡ [PRIORIDADE:SISTEMA:LEITURA] "
                    f"rota={rota_sistema or 'consulta_sistema_local'}"
                )
                return True

        # Uma frase pode pedir duas habilidades cooperando no mesmo turno.
        # O ciclo canônico já sabia segmentar e executar a cadeia, mas essa
        # porta nunca era chamada pela fase prioritária; por isso o texto
        # inteiro escapava para a conversa e a Laylay às vezes confirmava uma
        # etapa inexistente. Cada trecho volta ao mesmo resolvedor canônico e
        # mantém suas próprias evidências, permissões e resultados.
        processar_cadeia = ns.get("processar_comandos_em_cadeia")
'''
    return substituir_exato(texto, antigo, novo, nome_patch="prioridade read-only de aplicativos")


def patch_historico_continuacao_aditiva(texto: str) -> tuple[str, bool]:
    mudou = False
    if "historico_operacao_referenciavel" not in texto:
        antigo = '''        candidatos.append({**item, "dominio": dominio, "idade_s": max(0.0, idade)})

    # O contrato atomico do ultimo resultado e a segunda fonte oficial. Ele
'''
        novo = '''        candidatos.append({**item, "dominio": dominio, "idade_s": max(0.0, idade)})

    # Uma ação posterior do mesmo domínio não pode apagar uma operação que
    # continua semanticamente referenciável. Ex.: PLAYLIST_ADD -> MEDIA_CONTROL
    # -> "Essa também.". O foco vivo de música vira MEDIA_CONTROL, mas o último
    # PLAYLIST_ADD confirmado ainda precisa fornecer o destino da playlist.
    # REGRESSAO_118_V1_20260814 | historico_operacao_referenciavel
    for bruto_historico in reversed(list(continuidade.get("historico") or [])):
        item_historico = dict(bruto_historico or {})
        intent_historico = str(item_historico.get("intent") or "").upper().strip()
        if intent_historico not in _POLITICAS_CONTINUACAO_ADITIVA:
            continue
        try:
            idade_historico = agora - float(item_historico.get("ts") or 0.0)
        except (TypeError, ValueError):
            continue
        if idade_historico > ttl_s:
            continue
        params_historico = dict(item_historico.get("params") or {})
        if not params_historico:
            # Históricos antigos não tinham params; não reconstruímos por adivinhação.
            continue
        candidatos.append({
            **item_historico,
            "params": params_historico,
            "idade_s": max(0.0, idade_historico),
            "fonte": "historico_operacao_referenciavel",
        })

    # O contrato atomico do ultimo resultado e a segunda fonte oficial. Ele
'''
        texto, alterou = substituir_exato(
            texto, antigo, novo, nome_patch="recuperação histórica da continuação aditiva"
        )
        mudou = mudou or alterou

    if "resumo_historico_referenciavel" not in texto:
        antigo = '''    dominios[dominio_norm] = item
    historico = list(continuidade.get("historico") or [])
    historico.append({chave: item.get(chave) for chave in ("evento", "dominio", "intent", "alvo", "status", "ts")})
    continuidade.update({
'''
        novo = '''    dominios[dominio_norm] = item
    historico = list(continuidade.get("historico") or [])
    resumo_historico_referenciavel = {
        chave: item.get(chave)
        for chave in ("evento", "dominio", "intent", "alvo", "status", "ts")
    }
    # Params só entram no histórico para operações que declararam política
    # aditiva; os valores já passaram por _params_seguros.
    # REGRESSAO_118_V1_20260814 | resumo_historico_referenciavel
    if str(item.get("intent") or "").upper() in _POLITICAS_CONTINUACAO_ADITIVA:
        resumo_historico_referenciavel["params"] = dict(item.get("params") or {})
    historico.append(resumo_historico_referenciavel)
    continuidade.update({
'''
        texto, alterou = substituir_exato(
            texto, antigo, novo, nome_patch="persistência de params referenciáveis"
        )
        mudou = mudou or alterou
    return texto, mudou


def patch_status_lembrete_duplicado(texto: str) -> tuple[str, bool]:
    if '"lembrete_ja_agendado"' in texto:
        return texto, False
    antigo = '''    "playlist_ja_existia", "playlist_musica_ja_existia",
    "nota_ja_guardada",
}'''
    novo = '''    "playlist_ja_existia", "playlist_musica_ja_existia",
    "nota_ja_guardada", "lembrete_ja_agendado",
}'''
    return substituir_exato(texto, antigo, novo, nome_patch="estado central do lembrete duplicado")


def patch_fala_lembrete_duplicado(texto: str) -> tuple[str, bool]:
    if 'status_norm == "lembrete_ja_agendado"' in texto:
        return texto, False
    antigo = '''            elif status_norm == "playlist_ja_existia":
                fala_base = f"A playlist {objeto} já existia; não criei outra."
            else:
                fala_base = f"{objeto} já estava como você pediu; não repeti a ação."
'''
    novo = '''            elif status_norm == "playlist_ja_existia":
                fala_base = f"A playlist {objeto} já existia; não criei outra."
            elif status_norm == "lembrete_ja_agendado":
                fala_base = (
                    f"O lembrete de {objeto} já estava agendado; "
                    "mantive uma só cópia."
                )
            else:
                fala_base = f"{objeto} já estava como você pediu; não repeti a ação."
'''
    return substituir_exato(texto, antigo, novo, nome_patch="fala segura do lembrete duplicado")


def patch_ancora_lembrete_duplicado(texto: str) -> tuple[str, bool]:
    if 'status == "lembrete_ja_agendado"' in texto:
        return texto, False
    antigo = '''        if status == "ja_estava_desligado":
            return f"{objeto.capitalize()} já está desligado; não repeti o comando."
        return f"{objeto.capitalize()} já estava como você pediu; não repeti a ação."
'''
    novo = '''        if status == "ja_estava_desligado":
            return f"{objeto.capitalize()} já está desligado; não repeti o comando."
        if status == "lembrete_ja_agendado":
            return (
                f"O lembrete de {objeto} já estava agendado; "
                "mantive uma só cópia."
            )
        return f"{objeto.capitalize()} já estava como você pediu; não repeti a ação."
'''
    return substituir_exato(texto, antigo, novo, nome_patch="âncora do lembrete duplicado")


def patch_validacao_llm_lembrete_duplicado(texto: str) -> tuple[str, bool]:
    if '"lembrete_ja_agendado":' in texto:
        return texto, False
    antigo = '''    "lembrete_agendado": ("agend", "lembrete"),
    "agendamento_cancelado": ("cancel", "agenda"),
'''
    novo = '''    "lembrete_agendado": ("agend", "lembrete"),
    "lembrete_ja_agendado": ("ja", "agend", "marcad", "duplic", "mantive"),
    "agendamento_cancelado": ("cancel", "agenda"),
'''
    return substituir_exato(texto, antigo, novo, nome_patch="validação LLM do lembrete duplicado")


TESTE_REGRESSAO = r'''# -*- coding: utf-8 -*-
"""Regressões reproduzidas pelo roteiro automatizado de 118 turnos."""

from mente_laylay.autonomia.pre_fluxo_contextual import processar_consulta_sistema_local
from mente_laylay.memoria_mental.continuidade_geral import (
    registrar_evento_continuidade,
    resolver_continuacao_aditiva,
)
from mente_laylay.memoria_mental.resultado_acao import (
    ResultadoAcao,
    STATUS_RESULTADO_JA_SATISFEITO,
)
from mente_laylay.personalidade.planejador_resposta import (
    classificar_resultado,
    planejar_resposta_acao,
)


def test_consulta_app_eh_read_only():
    falas = []
    registros = []

    tratado, rota = processar_consulta_sistema_local(
        {
            "_resolver_alvo_ambiente": lambda nome: {
                "programa_aberto": True,
                "programa_em_foco": False,
            },
            "_emitir_resposta_curta": lambda _texto, fala, **_kwargs: falas.append(fala),
            "_registrar_resultado_execucao": (
                lambda *args, **kwargs: registros.append((args, kwargs))
            ),
            "mente_integrada_estado": {},
        },
        "O Opera continua aberto?",
    )

    assert tratado is True
    assert rota == "consulta_estado_programa"
    assert falas == ["Opera está aberto, mas não está em foco."]
    contrato = registros[-1][0][0]
    assert contrato["intent"] == "LIST_WINDOWS"
    assert contrato["status"] == "estado_app_consultado"


def test_prioridade_read_only_fica_antes_da_cadeia_generica():
    import inspect
    from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime

    fonte = inspect.getsource(ComandosImediatosRuntime.processar_prioritarios)
    assert fonte.index("PRIORIDADE:SISTEMA:LEITURA") < fonte.index(
        'ns.get("processar_comandos_em_cadeia")'
    )


def test_essa_tambem_sobrevive_ao_media_control_do_mesmo_dominio():
    estado = {}
    estado = registrar_evento_continuidade(
        estado,
        evento="resultado",
        intent="PLAYLIST_ADD",
        alvo="auditoria sonora",
        params={"nome_playlist": "auditoria sonora"},
        status="playlist_musica_adicionada",
        origem="teste_regressao",
    )
    estado = registrar_evento_continuidade(
        estado,
        evento="resultado",
        intent="MEDIA_CONTROL",
        alvo="proxima faixa",
        params={"acao": "next"},
        status="midia_next_playlist",
        origem="teste_regressao",
    )

    assert resolver_continuacao_aditiva(estado, texto="Essa também.") == {
        "intent": "PLAYLIST_ADD",
        "params": {
            "nome_playlist": "auditoria sonora",
            "referencia_contextual": True,
        },
    }


def test_lembrete_duplicado_e_noop_confirmado_e_nao_incerteza():
    assert "lembrete_ja_agendado" in STATUS_RESULTADO_JA_SATISFEITO
    resultado = ResultadoAcao(
        intent="AGENDAR_LEMBRETE",
        status="lembrete_ja_agendado",
        alvo="revisar a interface da aba Sistema amanhã às 15:20",
        executou=False,
        confirmado=True,
    )
    assert classificar_resultado(resultado) == "sem_acao"

    plano = planejar_resposta_acao(
        resultado,
        "Enviei o comando, mas não consegui confirmar o resultado.",
    )
    fala = plano.fala.casefold()
    assert plano.classe == "sem_acao"
    assert "não consegui confirmar" not in fala
    assert "nao consegui confirmar" not in fala
    assert "já" in fala or "ja" in fala
'''


def validar_python(caminho: Path) -> None:
    try:
        ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    except Exception as exc:
        raise ErroAplicacao(f"Falha de sintaxe em {caminho}: {exc}") from exc


def criar_backup(raiz: Path, caminhos: list[Path]) -> Path:
    pasta = raiz / "_backup_regressao_118" / datetime.now().strftime("%Y%m%d-%H%M%S")
    for caminho in caminhos:
        if not caminho.exists():
            continue
        destino = pasta / caminho.relative_to(raiz)
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(caminho, destino)
    return pasta


def restaurar_backup(raiz: Path, backup: Path, caminhos: list[Path]) -> None:
    for caminho in caminhos:
        origem = backup / caminho.relative_to(raiz)
        if origem.exists():
            caminho.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origem, caminho)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", help="raiz do projeto Laylay")
    parser.add_argument("--sem-testes", action="store_true", help="não executa pytest")
    args = parser.parse_args()

    try:
        raiz = localizar_raiz(args.root)
        print(f"[OK] Raiz da Laylay: {raiz}")
        mudancas = [
            Mudanca(raiz / "mente_laylay/autonomia/comandos_imediatos.py", "consulta read-only antes da cadeia genérica", patch_prioridade_consulta_app),
            Mudanca(raiz / "mente_laylay/memoria_mental/continuidade_geral.py", "histórico referenciável para 'Essa também'", patch_historico_continuacao_aditiva),
            Mudanca(raiz / "mente_laylay/memoria_mental/resultado_acao.py", "lembrete duplicado como estado já satisfeito", patch_status_lembrete_duplicado),
            Mudanca(raiz / "mente_laylay/autonomia/adaptador_resultado.py", "fala segura para lembrete duplicado", patch_fala_lembrete_duplicado),
            Mudanca(raiz / "mente_laylay/personalidade/planejador_resposta.py", "âncora semântica para lembrete duplicado", patch_ancora_lembrete_duplicado),
            Mudanca(raiz / "mente_laylay/personalidade/confirmacao_llm.py", "validação da autoria LLM", patch_validacao_llm_lembrete_duplicado),
        ]

        # Primeiro simula TUDO em memória. Se um alvo não bater, não escreve nada.
        preparados: dict[Path, str] = {}
        alterados: list[Path] = []
        print("[1/4] Validando pontos de aplicação...")
        for mudanca in mudancas:
            original = mudanca.caminho.read_text(encoding="utf-8")
            novo, mudou = mudanca.transformador(original)
            preparados[mudanca.caminho] = novo
            print(f"  - {'ALTERAR' if mudou else 'já aplicado'}: {mudanca.descricao}")
            if mudou:
                alterados.append(mudanca.caminho)

        teste_path = raiz / ARQUIVO_TESTE
        teste_conteudo = f"# {MARCADOR_VERSAO}\n" + TESTE_REGRESSAO
        teste_precisa = not teste_path.exists() or MARCADOR_VERSAO not in teste_path.read_text(
            encoding="utf-8", errors="replace"
        )

        if not alterados and not teste_precisa:
            print("\n[OK] As correções já estão aplicadas. Nada foi alterado.")
            return 0

        caminhos_backup = list(alterados)
        if teste_path.exists() and teste_precisa:
            caminhos_backup.append(teste_path)
        backup = criar_backup(raiz, caminhos_backup)
        print(f"[2/4] Backup criado em: {backup}")

        for caminho in alterados:
            caminho.write_text(preparados[caminho], encoding="utf-8", newline="\n")
        if teste_precisa:
            teste_path.parent.mkdir(parents=True, exist_ok=True)
            teste_path.write_text(teste_conteudo, encoding="utf-8", newline="\n")

        validar = list(alterados)
        if teste_precisa:
            validar.append(teste_path)
        print("[3/4] Validando sintaxe...")
        try:
            for caminho in validar:
                validar_python(caminho)
                print(f"  - OK: {caminho.relative_to(raiz)}")
        except Exception:
            print("[ERRO] Validação falhou; restaurando backup automaticamente...")
            restaurar_backup(raiz, backup, caminhos_backup)
            if teste_precisa and not (backup / ARQUIVO_TESTE).exists():
                teste_path.unlink(missing_ok=True)
            raise

        print("[4/4] Teste focalizado...")
        if args.sem_testes:
            print("  - pulado por --sem-testes")
        else:
            try:
                import pytest  # noqa: F401
            except ImportError:
                print("  - pytest não está instalado neste Python; a validação de sintaxe passou.")
                print("    Depois: python -m pytest tests/test_regressoes_roteiro_118.py -q")
            else:
                processo = subprocess.run(
                    [sys.executable, "-m", "pytest", str(ARQUIVO_TESTE), "-q"],
                    cwd=str(raiz),
                )
                if processo.returncode != 0:
                    print("\n[ATENÇÃO] Sintaxe OK, mas o teste focalizado falhou.")
                    print(f"Backup preservado em: {backup}")
                    return processo.returncode

        print("\n" + "=" * 68)
        print("CORREÇÕES APLICADAS COM SUCESSO")
        print("=" * 68)
        print("1. Consulta de estado de app usa rota read-only antes de APP_OPEN.")
        print("2. 'Essa também' recupera o PLAYLIST_ADD elegível após MEDIA_CONTROL.")
        print("3. Lembrete duplicado vira no-op confirmado, não falha/incerteza.")
        print(f"Backup: {backup}")
        print("\nPróximo passo: rode exatamente o mesmo roteiro de 118 turnos.")
        return 0
    except ErroAplicacao as exc:
        print(f"\n[ERRO] {exc}")
        return 2
    except Exception as exc:
        print(f"\n[ERRO INESPERADO] {type(exc).__name__}: {exc}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
