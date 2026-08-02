"""P12: persistência degradável e concorrência entre serviços da mente."""

from __future__ import annotations

import threading

from mente_laylay.autonomia.servicos_background import GerenciadorServicosBackground
from mente_laylay.memoria_mental.persistencia_memoria import (
    carregar_memoria,
    registrar_autocorrecao_virtual,
    salvar_memoria,
    sanitizar_aprendizado_oportunidades,
)


class _MemoriaFake:
    def __init__(self, estado=None, aprendizados=None) -> None:
        self.estado = estado
        self.aprendizados = aprendizados or []
        self.salvo = None

    def carregar_estado(self):
        return self.estado

    def listar_aprendizados_semanticos(self, **_kwargs):
        return self.aprendizados

    def salvar_estado(self, **dados) -> None:
        self.salvo = dados


class _MemoriaFalha:
    def registrar_eventos(self, _eventos) -> None:
        raise OSError("indisponível")

    def salvar_resumo(self, *_args, **_kwargs) -> None:
        raise OSError("indisponível")

    def salvar_aprendizado_semantico(self, **_kwargs) -> None:
        raise OSError("indisponível")

    def salvar_preferencia(self, *_args) -> None:
        raise OSError("indisponível")


def test_aprendizado_persistido_remove_texto_livre_e_normaliza_contadores() -> None:
    resultado = sanitizar_aprendizado_oportunidades({
        "aprendizado": {
            "musica": {
                "aceitas": 2,
                "status": "maduro",
                "texto_usuario": "segredo que não deve persistir",
                "decisao_recente": {"fala": "privada"},
            },
        },
        "contadores": {"feedbacks": "3", "recusadas": -4, "silencios": "inválido"},
    })

    assert resultado["aprendizado"] == {"musica": {"aceitas": 2, "status": "maduro"}}
    assert resultado["contadores"]["feedbacks"] == 3
    assert resultado["contadores"]["recusadas"] == 0
    assert resultado["contadores"]["silencios"] == 0
    assert "segredo" not in str(resultado)


def test_carregamento_substitui_prompt_antigo_e_descarta_mensagem_invalida() -> None:
    memoria = _MemoriaFake(
        estado={
            "messages": [
                {"role": "system", "content": "prompt antigo"},
                {"role": "user", "content": "oi"},
                {"content": "sem papel"},
            ],
            "coordenador_oportunidades": {"contadores": {"feedbacks": 1}},
        },
        aprendizados=[{
            "status": "ativo",
            "confirmado_usuario": True,
            "chave_semantica": "identidade:nome_usuario",
            "valor": "Ana",
        }],
    )

    carregado = carregar_memoria(memoria, "prompt atual")

    assert carregado["messages"] == [
        {"role": "system", "content": "prompt atual"},
        {"role": "user", "content": "oi"},
    ]
    assert carregado["nome_usuario"] == "Ana"
    assert carregado["coordenador_oportunidades"]["contadores"]["feedbacks"] == 1


def test_carregamento_corrompido_degrada_para_estado_minimo() -> None:
    carregado = carregar_memoria(_MemoriaFake(estado="corrompido"), "identidade")
    assert carregado["messages"] == [{"role": "system", "content": "identidade"}]
    assert carregado["nome_usuario"] == ""


def test_salvar_memoria_delega_snapshot_sem_mutar_entrada() -> None:
    memoria = _MemoriaFake()
    dados = {"current_emotion": "calma", "messages": [{"role": "user", "content": "oi"}]}
    salvar_memoria(memoria, dados)

    assert memoria.salvo == dados
    assert memoria.salvo is not dados


def test_autocorrecao_preserva_estado_mesmo_com_persistencia_indisponivel() -> None:
    estado = {"_autocorrecao_eventos": [{"id": numero} for numero in range(25)]}
    atualizado = registrar_autocorrecao_virtual(
        _MemoriaFalha(),
        estado,
        "teste",
        "resposta errada",
        "resposta corrigida",
        ajustar_humor_cb=lambda *_args: (_ for _ in ()).throw(RuntimeError("humor")),
        registrar_autoaprimoramento_cb=lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("aprendizado")),
    )

    assert atualizado["_autocorrecao_total"] == 1
    assert atualizado["_cookie_virtual_total"] == 1
    assert len(atualizado["_autocorrecao_eventos"]) == 20
    assert atualizado["_autocorrecao_eventos"][-1]["correcao"] == "resposta corrigida"


def test_chat_voz_proatividade_e_visao_iniciam_conjuntamente_sem_duplicar() -> None:
    nomes = ("Chat", "Voz", "Proatividade", "Visao")
    barreira = threading.Barrier(len(nomes))
    concluidos = threading.Event()
    lock = threading.Lock()
    executados: list[str] = []

    def servico(nome: str):
        def executar() -> None:
            barreira.wait(timeout=2)
            with lock:
                executados.append(nome)
                if len(executados) == len(nomes):
                    concluidos.set()
        return executar

    gerente = GerenciadorServicosBackground(log=lambda _texto: None)
    resultados = gerente.iniciar_varios({nome: servico(nome) for nome in nomes})

    assert resultados == {nome: True for nome in nomes}
    assert concluidos.wait(2)
    assert sorted(executados) == sorted(nomes)
    gerente.encerrar(timeout_s=1)


def test_queda_de_um_servico_nao_cancela_os_demais() -> None:
    bom_finalizou = threading.Event()
    falhas: list[tuple[str, str]] = []
    gerente = GerenciadorServicosBackground(
        log=lambda _texto: None,
        registrar_falha=lambda modulo, codigo, **_kw: falhas.append((modulo, codigo)),
    )

    resultados = gerente.iniciar_varios({
        "Falho": lambda: (_ for _ in ()).throw(RuntimeError("quebrou")),
        "Saudavel": bom_finalizou.set,
    })

    assert resultados == {"Falho": True, "Saudavel": True}
    assert bom_finalizou.wait(2)
    limite = threading.Event()
    for _ in range(100):
        if falhas:
            break
        limite.wait(0.01)
    assert falhas == [("servico_Falho", "queda_background")]
    gerente.encerrar(timeout_s=1)

