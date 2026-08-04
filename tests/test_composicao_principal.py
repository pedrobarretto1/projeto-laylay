from __future__ import annotations

from mente_laylay.integracao.composicao_principal import criar_registros_principais
from mente_laylay.integracao.registro_conversa_llm import (
    PedidoModelo,
    ResultadoModelo,
    criar_estado_conversa_runtime,
)


class _Servico:
    def __getattr__(self, _nome):
        return lambda *_args, **_kwargs: {}


class _Modelo:
    def executar(self, _pedido: PedidoModelo) -> ResultadoModelo:
        return ResultadoModelo("ok", True)

    def diagnostico(self):
        return {"disponivel": True, "credencial_exposta": False}


def _servico_com(*nomes: str):
    classe = type("ServicoComPortas", (), {})
    servico = classe()
    for nome in nomes:
        setattr(servico, nome, lambda *_args, **_kwargs: {})
    return servico


def _criar_pacote():
    mensagens = []
    estado = criar_estado_conversa_runtime(
        getter=lambda: mensagens,
        setter=lambda novas: mensagens.__setitem__(slice(None), novas),
    )
    return criar_registros_principais(
        memoria_pessoas=_servico_com("processar", "contexto_para_prompt", "diagnostico", "retrato_para_mente", "reexecutar"),
        iot=_servico_com("detectar", "executar", "retrato_para_mente"),
        arquivos_leitura=_servico_com("pesquisar", "abrir", "diagnostico"),
        arquivos_mutacao=_servico_com("resolver_caminho", "criar_pasta", "criar_arquivo", "escrever_texto_seguro", "mover_item", "transacionar", "buscar_itens", "solicitar_exclusao", "confirmar_exclusao", "cancelar_exclusao", "restaurar_ultimo", "diagnostico"),
        musica_leitura=_servico_com("listar_usuario", "consultar_usuario", "contar_usuario", "formatar_prompt", "retrato_usuario", "indice_usuario", "listar_laylay", "retrato_laylay", "estado", "diagnostico"),
        musica_operacoes=_servico_com("apagar_playlist", "adicionar_faixa", "mover_faixa", "tocar_playlist", "preparar_shuffle", "primeira_url", "avancar_proxima", "voltar_anterior", "definir_ultima_playlist", "definir_ultima_url", "faixa_atual", "copiar_curadoria", "estado", "diagnostico"),
        navegador_leitura=_servico_com("conectado", "aba_ativa", "listar_abas", "diagnostico"),
        navegador_operacoes=_servico_com("abrir_url", "pesquisar_youtube", "tocar_youtube", "tocar_youtube_detalhado", "controlar_youtube", "fechar_aba", "fechar_aba_atual", "fechar_abas", "recarregar_url", "fechar_aba_nativa", "fechar_abas_vazias", "clicar", "digitar", "pressionar", "diagnostico"),
        visao_jogo_leitura=_servico_com("em_andamento", "tem_analise_recente", "observar_texto_usuario", "perfil_atual", "diagnostico"),
        visao_jogo_analise=_servico_com("executar", "aplicar_referencia_item", "continuar_analise_recente", "continuar_pendencia", "processar_atualizacao_perfil", "diagnostico"),
        modelo_llm=_Modelo(),
        estado_conversa=estado,
    )


def test_pacote_principal_reune_registros_sem_namespace_global() -> None:
    pacote = _criar_pacote()

    diagnostico = pacote.diagnostico()

    assert diagnostico["disponivel"] is True
    assert diagnostico["quantidade"] == 12
    assert diagnostico["namespace_global"] is False
    assert diagnostico["credencial_exposta"] is False
    assert diagnostico["autoriza_execucao"] is False
    assert pacote.modelo_llm.enviar([{"role": "user", "content": "oi"}]) == "ok"


def test_pacote_principal_rejeita_estado_de_conversa_sem_contrato() -> None:
    try:
        criar_registros_principais(
            memoria_pessoas=_Servico(), iot=_Servico(),
            arquivos_leitura=_Servico(), arquivos_mutacao=_Servico(),
            musica_leitura=_Servico(), musica_operacoes=_Servico(),
            navegador_leitura=_Servico(), navegador_operacoes=_Servico(),
            visao_jogo_leitura=_Servico(), visao_jogo_analise=_Servico(),
            modelo_llm=_Modelo(), estado_conversa=object(),
        )
    except RuntimeError as erro:
        assert "estado da conversa inválido" in str(erro)
    else:
        raise AssertionError("estado sem contrato foi aceito")
