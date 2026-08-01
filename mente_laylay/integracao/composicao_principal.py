"""Pacote tipado dos registros centrais usados pela composição principal.

O pacote não cria runtimes nem concede autorização. Ele valida e reúne as
fronteiras públicas já construídas pelos domínios para que a raiz da aplicação
não precise redescobri-las em ``globals()`` a cada composição.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mente_laylay.integracao.registro_arquivos import (
    RegistroArquivosLeitura,
    registrar_arquivos_leitura,
)
from mente_laylay.integracao.registro_conversa_llm import (
    PortaEstadoConversa,
    RegistroModeloLLM,
    registrar_modelo_llm,
)
from mente_laylay.integracao.registro_iot import RegistroIoT, registrar_iot
from mente_laylay.integracao.registro_memoria_pessoas import (
    RegistroMemoriaPessoas,
    registrar_memoria_pessoas,
)
from mente_laylay.integracao.registro_musica import (
    RegistroMusicaLeitura,
    registrar_musica_leitura,
)
from mente_laylay.integracao.registro_mutacoes_arquivos import (
    RegistroArquivosMutacao,
    registrar_arquivos_mutacao,
)
from mente_laylay.integracao.registro_navegador import (
    RegistroNavegadorLeitura,
    RegistroNavegadorOperacoes,
    registrar_navegador_leitura,
    registrar_navegador_operacoes,
)
from mente_laylay.integracao.registro_operacoes_musicais import (
    RegistroOperacoesMusicais,
    registrar_operacoes_musicais,
)
from mente_laylay.integracao.registro_visao_jogo import (
    RegistroVisaoJogoAnalise,
    RegistroVisaoJogoLeitura,
    registrar_visao_jogo_analise,
    registrar_visao_jogo_leitura,
)


@dataclass(frozen=True, slots=True)
class RegistrosPrincipais:
    memoria_pessoas: RegistroMemoriaPessoas
    iot: RegistroIoT
    arquivos_leitura: RegistroArquivosLeitura
    arquivos_mutacao: RegistroArquivosMutacao
    musica_leitura: RegistroMusicaLeitura
    musica_operacoes: RegistroOperacoesMusicais
    navegador_leitura: RegistroNavegadorLeitura
    navegador_operacoes: RegistroNavegadorOperacoes
    visao_jogo_leitura: RegistroVisaoJogoLeitura
    visao_jogo_analise: RegistroVisaoJogoAnalise
    modelo_llm: RegistroModeloLLM
    estado_conversa: PortaEstadoConversa = field(repr=False)

    def diagnostico(self) -> dict[str, Any]:
        nomes = (
            "memoria_pessoas", "iot", "arquivos_leitura", "arquivos_mutacao",
            "musica_leitura", "musica_operacoes", "navegador_leitura",
            "navegador_operacoes", "visao_jogo_leitura", "visao_jogo_analise",
            "modelo_llm", "estado_conversa",
        )
        return {
            "disponivel": True,
            "registros": nomes,
            "quantidade": len(nomes),
            "namespace_global": False,
            "credencial_exposta": False,
            "autoriza_execucao": False,
        }


def criar_registros_principais(
    *,
    memoria_pessoas: Any,
    iot: Any,
    arquivos_leitura: Any,
    arquivos_mutacao: Any,
    musica_leitura: Any,
    musica_operacoes: Any,
    navegador_leitura: Any,
    navegador_operacoes: Any,
    visao_jogo_leitura: Any,
    visao_jogo_analise: Any,
    modelo_llm: Any,
    estado_conversa: Any,
) -> RegistrosPrincipais:
    if not isinstance(estado_conversa, PortaEstadoConversa):
        raise RuntimeError(
            "serviço de estado da conversa inválido na composição principal"
        )
    return RegistrosPrincipais(
        memoria_pessoas=registrar_memoria_pessoas(memoria_pessoas),
        iot=registrar_iot(iot),
        arquivos_leitura=registrar_arquivos_leitura(arquivos_leitura),
        arquivos_mutacao=registrar_arquivos_mutacao(arquivos_mutacao),
        musica_leitura=registrar_musica_leitura(musica_leitura),
        musica_operacoes=registrar_operacoes_musicais(musica_operacoes),
        navegador_leitura=registrar_navegador_leitura(navegador_leitura),
        navegador_operacoes=registrar_navegador_operacoes(navegador_operacoes),
        visao_jogo_leitura=registrar_visao_jogo_leitura(visao_jogo_leitura),
        visao_jogo_analise=registrar_visao_jogo_analise(visao_jogo_analise),
        modelo_llm=registrar_modelo_llm(modelo_llm),
        estado_conversa=estado_conversa,
    )
