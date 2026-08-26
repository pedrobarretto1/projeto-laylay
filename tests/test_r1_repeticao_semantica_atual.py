"""
ROOT R1 — repetição perde a semântica da fala atual.

Prova arquitetural:
- "tenta/de novo" continua sendo repetição operacional genérica;
- "leia/lê/ler ... de novo" continua sendo reconhecido como repetição,
  mas o verbo atual restringe a seleção a uma leitura compatível;
- um domínio ativo mais recente (ex.: IoT) não pode transformar
  "Leia de novo." em IOT_CONTROL;
- se não existe leitura reexecutável compatível, a rota falha fechada.

Este arquivo é RED contra o HEAD anterior à correção da R1.
Não altera produção e não depende do turno histórico 070 para expressar a raiz.
"""

from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
    resolver_repeticao_ultima_acao,
    texto_pede_repeticao_curta,
)


def _normalizar(texto: str) -> str:
    return str(texto or "").casefold().strip()


def _registrar_leitura(estado, caminho: str = r"C:\tmp\caos seguro.txt"):
    return registrar_resultado_execucao(
        estado,
        {
            "intent": "FILE_READ",
            "params": {
                "caminho": caminho,
                "alvo": "caos seguro.txt",
            },
            "status": "arquivo_lido",
            "executou": True,
            "confirmado": True,
        },
        "Leia o caos seguro.txt.",
        origem="arquivos",
    )


def _registrar_iot(estado):
    return registrar_resultado_execucao(
        estado,
        {
            "intent": "IOT_CONTROL",
            "params": {
                "acao": "desligar",
                "alvo": "lampada_quarto",
            },
            "status": "dispositivo_desligado",
            "executou": True,
            "confirmado": True,
        },
        "Desliga a lâmpada.",
        origem="iot",
    )


def _estado_leitura_depois_iot():
    estado = estado_mental_inicial()
    estado = _registrar_leitura(estado)
    estado = _registrar_iot(estado)
    return estado


# ---------------------------------------------------------------------------
# Guards: comportamento genérico existente continua soberano.
# ---------------------------------------------------------------------------


def test_r1_guard_leia_de_novo_continua_sendo_detectado_como_repeticao():
    assert texto_pede_repeticao_curta("Leia de novo.", _normalizar) is True
    assert texto_pede_repeticao_curta("Lê novamente.", _normalizar) is True
    assert texto_pede_repeticao_curta("ler outra vez", _normalizar) is True


def test_r1_guard_tenta_de_novo_continua_repetindo_dominio_ativo():
    estado = _estado_leitura_depois_iot()

    resultado = resolver_repeticao_ultima_acao(
        "tenta de novo",
        estado,
        _normalizar,
    )

    assert resultado == {
        "intent": "IOT_CONTROL",
        "params": {
            "acao": "desligar",
            "alvo": "lampada_quarto",
        },
    }


def test_r1_guard_de_novo_sem_verbo_continua_repeticao_generica():
    estado = _estado_leitura_depois_iot()

    resultado = resolver_repeticao_ultima_acao(
        "de novo",
        estado,
        _normalizar,
    )

    assert resultado == {
        "intent": "IOT_CONTROL",
        "params": {
            "acao": "desligar",
            "alvo": "lampada_quarto",
        },
    }


# ---------------------------------------------------------------------------
# REDs: a fala atual contém semântica de leitura e precisa restringir a busca.
# ---------------------------------------------------------------------------


def test_r1_leia_de_novo_nao_pode_ser_roubado_por_iot_mais_recente():
    estado = _estado_leitura_depois_iot()

    resultado = resolver_repeticao_ultima_acao(
        "Leia de novo.",
        estado,
        _normalizar,
    )

    assert resultado == {
        "intent": "FILE_READ",
        "params": {
            "caminho": r"C:\tmp\caos seguro.txt",
            "alvo": "caos seguro.txt",
        },
    }


def test_r1_le_novamente_preserva_dominio_de_leitura():
    estado = _estado_leitura_depois_iot()

    resultado = resolver_repeticao_ultima_acao(
        "Lê novamente.",
        estado,
        _normalizar,
    )

    assert resultado is not None
    assert resultado["intent"] == "FILE_READ"
    assert resultado["params"]["alvo"] == "caos seguro.txt"


def test_r1_ler_outra_vez_preserva_dominio_de_leitura():
    estado = _estado_leitura_depois_iot()

    resultado = resolver_repeticao_ultima_acao(
        "ler outra vez",
        estado,
        _normalizar,
    )

    assert resultado is not None
    assert resultado["intent"] == "FILE_READ"
    assert resultado["params"]["alvo"] == "caos seguro.txt"


def test_r1_leia_de_novo_sem_leitura_compativel_falha_fechado():
    estado = _registrar_iot(estado_mental_inicial())

    resultado = resolver_repeticao_ultima_acao(
        "Leia de novo.",
        estado,
        _normalizar,
    )

    assert resultado is None

def _registrar_append(estado):
    return registrar_resultado_execucao(
        estado,
        {
            "intent": "CREATE_FILE",
            "params": {
                "alvo": "caos seguro.txt",
                "caminho": r"C:\tmp\caos seguro.txt",
                "conteudo": "segunda linha",
                "modo_escrita": "append",
            },
            "status": "conteudo_acrescentado",
            "executou": True,
            "confirmado": True,
        },
        "Acrescente segunda linha.",
        origem="arquivos",
    )


def test_r1_red_fluxo_causal_leitura_append_nao_pode_cair_em_iot():
    """
    Reprodução arquitetural do formato do chaos:

    IoT antigo
      → FILE_READ
      → append no mesmo arquivo
      → "Leia de novo."

    O append pode substituir o foco corrente do domínio arquivos,
    mas não pode apagar a operação de leitura semanticamente pedida.
    """
    estado = estado_mental_inicial()

    # IoT existe antes e continua reexecutável.
    estado = _registrar_iot(estado)

    # Depois o usuário entra claramente no domínio de arquivos.
    estado = _registrar_leitura(estado)

    # Uma mutação intermediária no MESMO arquivo não transforma
    # "Leia de novo" em repetição da operação IoT antiga.
    estado = _registrar_append(estado)

    resultado = resolver_repeticao_ultima_acao(
        "Leia de novo.",
        estado,
        _normalizar,
    )

    assert resultado == {
        "intent": "FILE_READ",
        "params": {
            "caminho": r"C:\tmp\caos seguro.txt",
            "alvo": "caos seguro.txt",
        },
    }
