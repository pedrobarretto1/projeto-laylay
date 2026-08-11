from __future__ import annotations

from pathlib import Path

import pytest

from mente_laylay.arquivos.lixeira_laylay import LixeiraLaylay
from mente_laylay.arquivos.mutacoes import criar_arquivos_mutacao_runtime
from mente_laylay.integracao.registro_mutacoes_arquivos import (
    registrar_arquivos_mutacao,
)
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime


def _pendencia_runtime() -> PendenciaAcaoRuntime:
    estado: dict = {}

    def atualizar(mutador):
        novo = mutador(dict(estado))
        estado.clear()
        estado.update(novo)
        return dict(estado)

    return PendenciaAcaoRuntime(
        estado_getter=lambda: estado,
        estado_atualizar=atualizar,
        log=lambda *_args: None,
    )


def _registro_real(tmp_path: Path):
    lixeira = LixeiraLaylay(
        str(tmp_path / ".lixeira_teste"),
        pendencia_runtime=_pendencia_runtime(),
    )
    runtime = criar_arquivos_mutacao_runtime(
        solicitar_exclusao_cb=lixeira.mover,
        confirmar_exclusao_cb=lixeira.confirmar_pendente,
        cancelar_exclusao_cb=lixeira.cancelar_pendente,
        restaurar_ultimo_cb=lixeira.restaurar_ultimo,
        exclusao_pendente_cb=lixeira.tem_confirmacao_pendente,
    )
    return registrar_arquivos_mutacao(runtime), lixeira


def test_registro_preserva_escrita_segura_confirmacao_lixeira_e_restauracao(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LAYLAY_ARQUIVOS_RAIZES_PERMITIDAS", str(tmp_path))
    registro, lixeira = _registro_real(tmp_path)
    arquivo = tmp_path / "nota.txt"

    criado = registro.escrever_texto_seguro(str(arquivo), "primeira versão")
    bloqueado = registro.escrever_texto_seguro(str(arquivo), "segunda versão")
    substituido = registro.escrever_texto_seguro(
        str(arquivo), "segunda versão", sobrescrever=True,
    )

    assert criado["ok"] is True and criado["confirmado"] is True
    assert bloqueado["status"] == "arquivo_existente_requer_confirmacao"
    assert substituido["ok"] is True and substituido["confirmado"] is True
    assert "conteudo" not in substituido
    assert arquivo.read_text(encoding="utf-8") == "segunda versão"

    solicitado = registro.solicitar_exclusao(str(arquivo))
    assert solicitado.requer_confirmacao is True
    assert arquivo.is_file()
    assert lixeira.tem_confirmacao_pendente() is True

    confirmado = registro.confirmar_exclusao()
    assert confirmado.sucesso is True
    assert arquivo.exists() is False
    restaurado = registro.restaurar_ultimo()
    assert restaurado.sucesso is True
    assert arquivo.read_text(encoding="utf-8") == "segunda versão"


def test_registro_mantem_trava_de_seguranca_para_raiz_do_disco(tmp_path: Path) -> None:
    registro, _ = _registro_real(tmp_path)
    raiz = str(Path(tmp_path.anchor))

    retorno = registro.escrever_texto_seguro(raiz, "nunca escrever aqui")

    assert retorno["ok"] is False
    assert retorno["status"] == "acesso_negado"
    assert retorno["confirmado"] is False


def test_registro_sanitiza_diagnostico_e_nao_expoe_runtime() -> None:
    class _Servico:
        def resolver_caminho(self, valor): return valor
        def criar_pasta(self, _caminho): return True
        def criar_arquivo(self, _caminho, _conteudo, _modo="w"): return True
        def escrever_texto_seguro(self, *_args, **_kwargs):
            return {"ok": True, "conteudo": "privado", "conteudo_anterior": "privado"}
        def mover_item(self, _origem, _destino): return True
        def transacionar(self, params): return params
        def buscar_itens(self, _alvo): return []
        def solicitar_exclusao(self, caminho): return caminho
        def confirmar_exclusao(self): return True
        def cancelar_exclusao(self): return None
        def restaurar_ultimo(self): return True
        def diagnostico(self):
            return {
                "lixeira_reversivel": True,
                "confirmacao_exclusao_pendente": False,
                "raiz_interna": "C:/privado",
                "segredo": "não expor",
            }

    registro = registrar_arquivos_mutacao(_Servico())

    assert registro.escrever_texto_seguro("nota.txt", "privado") == {"ok": True}
    assert registro.diagnostico() == {
        "lixeira_reversivel": True,
        "confirmacao_exclusao_pendente": False,
    }
    assert "privado" not in repr(registro)


def test_registro_rejeita_servico_incompleto_na_composicao() -> None:
    class _Incompleto:
        def resolver_caminho(self, valor): return valor

    with pytest.raises(RuntimeError, match="serviço de mutação de arquivos inválido"):
        registrar_arquivos_mutacao(_Incompleto())
