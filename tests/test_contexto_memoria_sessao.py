from __future__ import annotations

import os
import tempfile

from memoria_sqlite import MemoriaSQLite
from mente_laylay.autonomia.contexto_resposta_ia import preparar_contexto_resposta_ia
from mente_laylay.memoria_mental.contexto_integrado import montar_resumo_mente_integrada_com_extras


def test_prompt_nao_reabre_conversa_transitoria_salva_no_sqlite() -> None:
    with tempfile.TemporaryDirectory() as pasta:
        memoria = MemoriaSQLite(os.path.join(pasta, "memoria.sqlite"))
        memoria.salvar_estado(
            messages=[
                {"role": "system", "content": "prompt antigo"},
                {"role": "user", "content": "qual a receita da coxinha?"},
                {"role": "assistant", "content": "Use farinha e caldo."},
            ],
            ultimo_topico_conversa="receita de coxinha",
            topicos_conversa_recente=["coxinha"],
        )
        mensagens, prompt = preparar_contexto_resposta_ia(
            {
                "memoria_sqlite": memoria,
                "retrato_mente_integrada": "--- MENTE INTEGRADA ---\nSessão atual sem tópico ativo.",
            },
            "oi lay",
            [{"role": "system", "content": "prompt atual"}],
            0,
            "Você é a Laylay. {status_humor}",
        )

        assert "coxinha" not in prompt.casefold()
        assert "farinha" not in prompt.casefold()
        assert mensagens[0]["content"] == prompt


def test_retrato_integrado_recupera_duravel_uma_vez_e_nao_rele_snapshot_de_sessao() -> None:
    class MemoriaEspia:
        relevantes = 0

        def formatar_aprendizados_relevantes_para_prompt(self, texto: str, limit: int = 4) -> str:
            self.relevantes += 1
            return "MEMÓRIA DURÁVEL RELEVANTE"

        def formatar_memoria_quente_para_prompt(self, *args, **kwargs):
            raise AssertionError("memória quente persistida não deve ser consultada")

        def formatar_topicos_conversa_para_prompt(self, *args, **kwargs):
            raise AssertionError("tópicos persistidos não devem ser consultados")

    memoria = MemoriaEspia()
    resumo = montar_resumo_mente_integrada_com_extras(
        texto_usuario="qual é minha preferência?",
        ctx={"periodo": "tarde", "emocao": "calma", "nivel_emocao": 1, "humor": 0},
        percepcao={},
        mente={},
        memoria_sqlite=memoria,
    )

    assert memoria.relevantes == 1
    assert resumo.count("MEMÓRIA DURÁVEL RELEVANTE") == 1
