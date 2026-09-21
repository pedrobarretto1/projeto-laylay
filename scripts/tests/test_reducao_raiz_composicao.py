from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from mente_laylay.integracao.ponte_clipboard_aplicacao import (
    criar_ponte_clipboard_aplicacao_runtime,
)
from mente_laylay.integracao.ponte_cooperacao_aplicacao import (
    criar_ponte_cooperacao_aplicacao_runtime,
)
from mente_laylay.integracao.ponte_iniciativa_aplicacao import (
    criar_ponte_iniciativa_aplicacao_runtime,
)
from mente_laylay.integracao.registro_servicos_aplicacao import (
    RegistroServicosAplicacaoRuntime,
)


class _Pendencias:
    def __init__(self) -> None:
        self.atual = None
        self.conclusoes = []

    def obter(self):
        return self.atual

    def registrar(self, **dados):
        self.atual = {"id": "p1", **dados}
        return self.atual

    def concluir(self, identificador, status):
        self.conclusoes.append((identificador, status))
        self.atual = None

    def resolver(self, texto, *, classificar_dominio, **_kwargs):
        return {
            "tratado": True,
            "status": classificar_dominio(texto),
            "pendencia": dict(self.atual or {}),
        }


def test_registro_allowlist_nao_vaza_namespace_e_falha_cedo() -> None:
    salvar = lambda: None
    registro = RegistroServicosAplicacaoRuntime(
        {"salvar_memoria": salvar, "credencial_privada": "segredo"},
        permitidos=("salvar_memoria", "servico_obrigatorio"),
    )

    assert registro.snapshot() == {"salvar_memoria": salvar}
    assert "credencial_privada" not in registro.nomes
    with pytest.raises(RuntimeError, match="servico_obrigatorio"):
        registro.snapshot(obrigatorios=("servico_obrigatorio",))
    with pytest.raises(RuntimeError, match="fora do contrato"):
        registro.publicar(outro_servico=object())


def test_ponte_clipboard_publica_pergunta_na_memoria_compartilhada() -> None:
    pendencias = _Pendencias()
    mental = {}
    mensagens = []
    ponte = criar_ponte_clipboard_aplicacao_runtime(
        pendencias=pendencias,
        estado_mental_getter=lambda: mental,
        estado_mental_atualizar=lambda **campos: mental.update(campos),
        memoria_conversa_getter=lambda: mensagens,
        memoria_conversa_setter=lambda novas: mensagens.extend(novas[len(mensagens):]),
        pendencia_protegida_getter=lambda _estado: None,
        oferta_deve_ceder=lambda *_args, **_kwargs: False,
        texto_tem_comando_explicito=lambda _texto: False,
        classificar_resposta=lambda _texto: "aceitar",
        classificar_confirmacao=lambda _texto, **_kwargs: "aceitar",
        area_transferencia=SimpleNamespace(snapshot_passivo=lambda: {}),
        caixa_entrada_getter=lambda: None,
        falar=lambda *_args: None,
        clock=lambda: 42.0,
        log=lambda _texto: None,
    )

    ponte.registrar_oferta_entregue({
        "acao_sugerida": "resumir_texto",
        "fala": "Quer que eu resuma?",
        "assinatura": "abc",
    })

    assert pendencias.atual["origem"] == "observador_area_transferencia"
    assert mental["ultima_fala_emitida_ts"] == 42.0
    assert mensagens[-1] == {"role": "assistant", "content": "Quer que eu resuma?"}


def test_recusa_clipboard_silencia_a_mesma_acao_temporariamente() -> None:
    pendencias = _Pendencias()
    mental = {}
    falas = []
    ponte = criar_ponte_clipboard_aplicacao_runtime(
        pendencias=pendencias,
        estado_mental_getter=lambda: mental,
        estado_mental_atualizar=lambda **campos: mental.update(campos),
        memoria_conversa_getter=lambda: [],
        memoria_conversa_setter=lambda _novas: None,
        pendencia_protegida_getter=lambda _estado: None,
        oferta_deve_ceder=lambda *_args, **_kwargs: False,
        texto_tem_comando_explicito=lambda _texto: False,
        classificar_resposta=lambda _texto: "recusar",
        classificar_confirmacao=lambda _texto, **_kwargs: "recusar",
        area_transferencia=SimpleNamespace(snapshot_passivo=lambda: {}),
        caixa_entrada_getter=lambda: None,
        falar=lambda fala, *_args: falas.append(fala),
        clock=lambda: 100.0,
        log=lambda _texto: None,
    )
    pendencias.registrar(
        origem="observador_area_transferencia",
        acao="resumir_texto",
        metadados={},
    )

    assert ponte.processar_oferta_pendente("não precisa") is True
    assert mental["clipboard_ofertas_silenciadas"] == {
        "resumir_texto": 700.0,
    }
    assert falas == ["Tudo bem, deixo quieto."]


def test_ponte_iniciativa_exige_conexao_e_monta_contexto() -> None:
    mental = {"plano_turno_atual": {"fase": "executado"}, "ultima_entrada_ts": 5}
    ponte = criar_ponte_iniciativa_aplicacao_runtime(
        estado_mental_getter=lambda: mental,
        percepcao_getter=lambda _chave, _padrao: {
            "assunto": "programação", "title": "Editor",
        },
        conversa_getter=lambda chave, padrao: {"modo_chat": True}.get(chave, padrao),
        modo_jogo=SimpleNamespace(ativo=False),
        visao_leitura_getter=lambda: None,
        identificar_jogo=lambda _contexto: {},
        salvar_memoria=lambda: None,
        falar=lambda *_args: None,
        env_getter=lambda _chave, padrao: padrao,
        log=lambda _texto: None,
    )

    assert ponte.contexto()["modo_foco"] is True
    assert ponte.contexto()["turno_ativo"] is False
    with pytest.raises(RuntimeError, match="ainda não foi conectada"):
        ponte.preparar_autonomia_segura_padrao()


def test_ponte_cooperacao_tolera_orquestrador_ainda_nao_montado() -> None:
    ponte = criar_ponte_cooperacao_aplicacao_runtime(
        orquestrador_getter=lambda: None,
        visao_analise_getter=lambda: None,
        visao_leitura_getter=lambda: None,
        pendencia_jogo_getter=lambda: None,
        contexto_jogo_getter=lambda: {},
        detectar_pedido_visao=lambda _texto, _contexto: None,
        registrar_evidencia=lambda **_dados: {},
        estado_mental_atualizar=lambda _atualizador: None,
        registrar_evento_continuidade=lambda estado, **_dados: estado,
        quadro_getter=lambda: None,
    )

    assert ponte.registrar_progresso_visao({"estado": "pronto"}) is False
    assert ponte.registrar_aprendizado({}, "desconhecido") is False


def test_raiz_nao_contem_mais_regras_extraidas_nem_conexoes_globais() -> None:
    raiz = Path(__file__).resolve().parents[1] / "laylay.py"
    codigo = raiz.read_text(encoding="utf-8")

    assert "def _processar_oferta_area_transferencia_pendente" not in codigo
    assert "def _processar_governanca_iniciativa" not in codigo
    assert "def _registrar_aprendizado_cooperativo" not in codigo
    assert "servicos=globals()" not in codigo
    assert "conectar_servicos(globals())" not in codigo
    assert codigo.count("globals()") == 1
