from __future__ import annotations

import asyncio
import json
from pathlib import Path

from mente_laylay.arquivos.arquivos_sistema import (
    resolver_caminho,
    verificar_trava_seguranca,
)
from mente_laylay.cognicao.fundamentacao_factual import validar_fala_com_fundamentacao
from mente_laylay.integracao.chrome_ws_server import ws_handler_modular
from mente_laylay.especialistas.operacional import (
    anexar_resultados_operacionais,
    avaliar_candidato_operacional,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.persistencia_memoria import compactar_historico_mensagens


class _WebSocketFalso:
    def __init__(self, primeira: dict, remoto: str) -> None:
        self._primeira = json.dumps(primeira)
        self.remote_address = (remoto, 50000)
        self.fechado = False

    async def recv(self) -> str:
        return self._primeira

    async def close(self) -> None:
        self.fechado = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration


def test_websocket_rejeita_cliente_generico_e_extensao_remota() -> None:
    generico = _WebSocketFalso({"type": "PAGE_DATA"}, "127.0.0.1")
    remota = _WebSocketFalso({"type": "EXTENSION_HELLO"}, "192.168.1.50")
    contexto = {"connected_extensions": set(), "connected_pc_b_clients": set()}

    asyncio.run(ws_handler_modular(generico, contexto))
    asyncio.run(ws_handler_modular(remota, contexto))

    assert generico.fechado is True
    assert remota.fechado is True
    assert not contexto["connected_extensions"]


def test_websocket_aceita_extensao_local_com_handshake() -> None:
    local = _WebSocketFalso({"type": "EXTENSION_HELLO"}, "127.0.0.1")
    mensagens = []
    contexto = {
        "connected_extensions": set(),
        "connected_pc_b_clients": set(),
        "_ws_dispatch_data": mensagens.append,
    }

    asyncio.run(ws_handler_modular(local, contexto))

    assert local.fechado is False
    assert mensagens == [{"type": "EXTENSION_HELLO"}]


def test_arquivos_resolvem_caminho_e_bloqueiam_fora_da_pasta_pessoal() -> None:
    permitido = resolver_caminho("teste-seguro.txt")
    fora = str(Path.home().anchor + "Windows")

    assert Path(permitido).is_absolute()
    assert verificar_trava_seguranca(permitido) is True
    assert verificar_trava_seguranca(fora) is False


def test_snapshot_nao_vaza_objetos_aninhados_da_mente() -> None:
    runtime = EstadoCompartilhadoRuntime(
        mental={"foco": {"entidade": {"nome": "Soulframe"}}},
    )
    snapshot = runtime.snapshot()
    snapshot["mental"]["foco"]["entidade"]["nome"] = "outro"

    assert runtime.obter_copia("mental", "foco")["entidade"]["nome"] == "Soulframe"


def test_historico_persistido_e_compactado_preservando_sistema() -> None:
    mensagens = [{"role": "system", "content": "identidade"}] + [
        {"role": "user", "content": str(numero)} for numero in range(30)
    ]
    compactado = compactar_historico_mensagens(mensagens, limite=20)

    assert len(compactado) == 20
    assert compactado[0]["role"] == "system"
    assert compactado[-1]["content"] == "29"


def test_fundamentacao_bloqueia_preferencia_e_genero_inventados() -> None:
    resultado = validar_fala_com_fundamentacao(
        "Eu adoro o estilo dele! Tenho medo de ele começar a fazer axé.",
        fundamentacao={"tema": "Rodrigo Zin", "confiavel": False},
        texto_usuario="o que você acha do Rodrigo Zin?",
    )

    assert resultado["acao"] == "ajustada"
    assert "familiaridade_inventada" in resultado["problemas"]
    assert "caracteristica_sem_evidencia" in resultado["problemas"]


def test_politica_operacional_separa_preparacao_de_efeito_sensivel() -> None:
    avaliacao = avaliar_candidato_operacional(
        {"autoriza_execucao": True, "confianca": 0.98},
        "DELETE_ITEM",
        confianca_candidato=0.98,
    )

    assert avaliacao["permitido"] is True
    assert avaliacao["requer_confirmacao"] is True
    assert avaliacao["efeito_autorizado"] is False


def test_operacional_nao_autoriza_falar_conclusao_sem_confirmacao_real() -> None:
    atualizado, possui_resultado = anexar_resultados_operacionais({}, [{
        "intent": "MEDIA_CONTROL",
        "status": "midia_next",
        "executou": True,
        "confirmado": None,
    }])

    assert possui_resultado is True
    assert atualizado["resultado_confirmado"] is False
    assert atualizado["pode_afirmar_conclusao"] is False
