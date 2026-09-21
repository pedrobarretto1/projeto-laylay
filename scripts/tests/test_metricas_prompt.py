from __future__ import annotations

from mente_laylay.autonomia.contexto_resposta_ia import ContextoPromptRuntime


class _MemoriaVazia:
    def formatar_memoria_para_prompt(self, **_kwargs):
        return ""


def test_prompt_registra_tamanho_por_origem_sem_expor_conteudo():
    medidas = []
    runtime = ContextoPromptRuntime(
        memoria_sqlite=_MemoriaVazia(),
        resumo_mente_integrada=lambda _texto: "memória selecionada",
        formatar_playlists=lambda: "",
        get_status_humor_prompt=lambda: "calma",
        base_system_prompt="personalidade base",
        estado_getter=lambda: {"messages": [{"role": "user", "content": "antes"}]},
        mapa_habilidades_prompt=lambda *_args, **_kwargs: "habilidade relevante",
        mapa_recursos_prompt=lambda _texto: "recurso relevante",
        registrar_tamanho_prompt=lambda origem, chars: medidas.append((origem, chars)),
    )

    pacote = runtime.preparar_pacote("agora")
    por_origem = dict(medidas)

    assert pacote.prompt_sistema
    assert por_origem["prompt_base"] == len("personalidade base")
    assert por_origem["prompt_mente"] == len("memória selecionada")
    assert por_origem["prompt_habilidades"] == len("habilidade relevante")
    assert por_origem["prompt_total"] == len(pacote.prompt_sistema)
