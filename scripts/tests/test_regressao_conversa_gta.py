from __future__ import annotations

import json
import os
import tempfile
import threading
import time

from memoria_sqlite import MemoriaSQLite
from mente_laylay.autonomia.execucao_ia import CoordenadorExecRuntime
from mente_laylay.autonomia.processamento_resposta_ia import (
    limpar_resposta_da_ia,
    salvar_aprendizados_da_ia,
)
from mente_laylay.cognicao.fundamentacao_factual import (
    classificar_atualidade_factual,
    extrair_tema_fundamentacao,
    montar_fundamentacao,
    validar_fala_com_fundamentacao,
)
from mente_laylay.personalidade.higiene_fala import remover_residuos_operacionais
from mente_laylay.personalidade.conversa_natural import fala_e_fallback_neutro


def test_metadados_em_colchetes_nao_chegam_a_fala() -> None:
    bruta = (
        "Ô, que legal! Você deve estar louco pra ver onde levam a série agora. "
        '[fala]: "Você já tem alguma teoria?" '
        "[tipo_interacao]: pergunta [leitura_turno]: [\"pergunta\"] "
        "[comandos]: [aprendizados]:"
    )

    fala, comandos = limpar_resposta_da_ia(bruta)

    assert fala == "Ô, que legal! Você deve estar louco pra ver onde levam a série agora."
    assert comandos == []
    assert "tipo_interacao" not in fala
    assert "[fala]" not in fala


def test_formula_com_chaves_nao_e_cortada_como_se_fosse_json(capsys) -> None:
    bruta = (
        r"Vamos resolver: \(x = \frac{50 - 7}{3}\). "
        r"Logo, o resultado continua na resposta."
    )

    fala, comandos = limpar_resposta_da_ia(bruta)

    assert comandos == []
    assert r"\frac{50 - 7}{3}" in fala
    assert "resultado continua" in fala
    assert "malformada" not in capsys.readouterr().out.casefold()


def test_objeto_estrutural_embutido_e_removido_sem_apagar_formula() -> None:
    bruta = (
        r"A conta \(x = \frac{12}{3}\) dá quatro. "
        r'{"acao": "open_app", "alvo": "calculadora"}'
    )

    fala, comandos = limpar_resposta_da_ia(bruta)

    assert comandos
    assert r"\frac{12}{3}" in fala
    assert "dá quatro" in fala
    assert '"acao"' not in fala


def test_prefixo_fala_repetido_nao_vaza_para_usuario() -> None:
    fala, comandos = limpar_resposta_da_ia("fala:fala:O resultado é vinte.")

    assert comandos == []
    assert fala == "O resultado é vinte."


def test_saida_malformada_remove_loop_textual_sem_truncar_conclusao() -> None:
    bruta = (
        'fala:"É como se eu fosse uma amiga que aprende com o que você diz e '
        'entende melhor o que você quer, sem pensar, só ouvir e responder com o '
        'que acho mais natural. Não tenho cére do que você diz, só ouvir e '
        'responder com o que acho mais natural. Não tenho cérebro, mas consigo entender."'
    )

    fala, comandos = limpar_resposta_da_ia(bruta)

    assert comandos == []
    assert fala.count("só ouvir e responder") == 1
    assert "Não tenho cére do que você diz" not in fala
    assert fala.endswith("Não tenho cérebro, mas consigo entender.")


def test_fala_rica_com_to_aqui_nao_e_confundida_com_fallback() -> None:
    normalizar = lambda texto: str(texto or "").casefold().strip()
    fala = (
        "Tudo certo aqui, graças a Deus! E você? "
        "É que tô aqui pra escutar como foi sua noite."
    )

    assert fala_e_fallback_neutro(fala, normalizar) is False
    assert fala_e_fallback_neutro("Tô aqui. Pode falar.", normalizar) is True


def test_resposta_malformada_recuperada_preserva_fala_social_completa() -> None:
    bruta = (
        'fala:"Tudo certo aqui! É que tô aqui pra escutar você também." '
        'tipo_interacao:"conversa" comandos:[]'
    )

    fala, comandos = limpar_resposta_da_ia(bruta)

    assert fala == "Tudo certo aqui! É que tô aqui pra escutar você também."
    assert comandos == []


def test_json_textual_escapado_e_truncado_libera_a_fala_conversacional() -> None:
    bruta = r'{\"fala\":\"Oi, Pedro! Tudo bem aqui, só esperando você aparecer...'

    fala, comandos = limpar_resposta_da_ia(bruta)

    assert fala == "Oi, Pedro! Tudo bem aqui, só esperando você aparecer."
    assert comandos == []


def test_contaminacao_cjk_no_final_e_removida_sem_perder_a_resposta() -> None:
    fala = remover_residuos_operacionais(
        "Eu fico animada só de pensar nos novos cenários. 🚀游戏技巧时间！"
    )
    assert fala == "Eu fico animada só de pensar nos novos cenários. 🚀"


def test_higiene_remove_cauda_tecnica_da_visao_mesmo_truncada() -> None:
    fala = remover_residuos_operacionais(
        'Essas botas parecem úteis. DADOS_ITEM_JSON: {"slot":"botas", "atributos":'
    )

    assert fala == "Essas botas parecem úteis."


def test_higiene_remove_letra_isolada_de_resposta_interrompida() -> None:
    fala = remover_residuos_operacionais(
        "Dreamcore mistura lugares familiares com uma nostalgia estranha. H."
    )

    assert fala == "Dreamcore mistura lugares familiares com uma nostalgia estranha."


def test_favorito_explicito_e_aprendido_mesmo_com_lista_vazia_do_modelo() -> None:
    with tempfile.TemporaryDirectory() as pasta:
        memoria = MemoriaSQLite(os.path.join(pasta, "memoria.sqlite"))
        resposta = json.dumps({"fala": "Que história boa.", "comandos": [], "aprendizados": []})

        salvos = salvar_aprendizados_da_ia(
            resposta,
            memoria,
            "estou muito empolgado, eu jogava GTA 5 desde os meus 8 anos, um dos meus jogos favoritos",
        )

        assert len(salvos) == 1
        assert salvos[0]["tipo"] == "preferencia"
        assert salvos[0]["valor"] == "GTA 5"
        assert "jogos favoritos" in salvos[0]["gatilho"]
        assert "GTA 5" in memoria.formatar_aprendizados_relevantes_para_prompt("quero jogar GTA 5")


def test_correcao_de_plataforma_dispara_fundamentacao_do_jogo() -> None:
    texto = "mas o GTA6 é nova geração então não vai ter para o PS4"
    atualidade = classificar_atualidade_factual(texto)

    assert atualidade["depende_atualidade"] is True
    assert atualidade["classe"] == "agenda_ou_disponibilidade"
    assert extrair_tema_fundamentacao(texto) == "GTA 6"


def test_numero_em_charada_nao_vira_titulo_para_pesquisa() -> None:
    charada = (
        "Caminhando ao fim da tarde, uma senhora contou 20 casas à sua direita. "
        "No regresso, contou 20 casas à esquerda. Quantas casas ela viu?"
    )
    assert extrair_tema_fundamentacao(charada) == ""
    assert extrair_tema_fundamentacao(
        charada,
        retrato={"referencia_resolvida": {"tipo": "tema", "nome": "contou 20"}},
    ) == ""


def test_plataforma_nao_sustentada_pela_fonte_nao_e_inventada() -> None:
    base = montar_fundamentacao(
        "GTA 6",
        {
            "ok": True,
            "titulo": "Grand Theft Auto VI",
            "resumo": "O jogo foi anunciado para PlayStation 5 e Xbox Series X e Series S.",
            "fonte": "fonte_oficial",
            "confianca": 0.98,
        },
    )

    resultado = validar_fala_com_fundamentacao(
        "GTA 6 vai render muitas noites de diversão no seu PS4.",
        fundamentacao=base,
        texto_usuario="pena que não tenho um PS5",
    )

    assert resultado["acao"] == "ajustada"
    assert "plataforma_sem_evidencia" in resultado["problemas"]
    assert "PS4" not in resultado["fala"]


def test_nova_entrada_invalida_resposta_anterior_ainda_em_geracao() -> None:
    iniciou_primeira = threading.Event()
    liberar_primeira = threading.Event()
    concluidas: list[tuple[str, bool]] = []

    class RuntimeFalso:
        def processar(self, texto: str, ainda_atual_cb=None):
            if texto == "primeira":
                iniciou_primeira.set()
                liberar_primeira.wait(timeout=2)
            vigente = True if ainda_atual_cb is None else bool(ainda_atual_cb())
            concluidas.append((texto, vigente))

    runtime = RuntimeFalso()
    coordenador = CoordenadorExecRuntime(
        contexto_exec_getter=lambda: None,
        resposta_ia_getter=lambda: runtime,
        loop_getter=lambda: None,
        log=lambda *_args: None,
    )

    primeira = coordenador.agendar("primeira")
    assert iniciou_primeira.wait(timeout=1)
    segunda = coordenador.agendar("segunda")
    liberar_primeira.set()
    primeira.join(timeout=2)
    segunda.join(timeout=2)

    por_texto = dict(concluidas)
    assert por_texto["primeira"] is False
    assert por_texto["segunda"] is True
