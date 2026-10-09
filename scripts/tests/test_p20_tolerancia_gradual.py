"""P20: evidência literal, agregação contextual e precedência sem perfil pessoal."""
from copy import deepcopy
from datetime import datetime
import time

import pytest

from memoria_sqlite import MemoriaSQLite
from mente_laylay.memoria_mental.motor_aprendizado import MotorAprendizadoRuntime
from mente_laylay.cognicao.preferencia_humor import (
    extrair_preferencia_humor, selecionar_preferencia_humor,
)
from mente_laylay.cognicao.interpretador_continuidade import qualificar_feedback_humor


@pytest.fixture
def motor(tmp_path):
    return MotorAprendizadoRuntime(memoria_sqlite=MemoriaSQLite(str(tmp_path / "p20.sqlite")),
        contexto_getter=lambda: {"assunto": "estado atual não decide contexto entregue"},
        log=lambda *_a: None)


def _amostra(motor, identidade, contexto="jogo", texto="Não, Lay. Essa piada passou do ponto.",
             *, idade=0.0, alterar=None):
    agora = time.time() - idade
    humor = qualificar_feedback_humor(texto)
    tipo = humor.get("tipo", "correcao")
    fonte = {"id_entrega": identidade, "dominio": contexto, "categoria": "resposta",
        "origem_produtor": "orquestrador_fala", "alvo": identidade,
        "entregue": True, "entrega_ts": agora - 1, "observado_ts": agora,
        "contexto_humor": contexto, "canal_entrega": "texto_publicado",
        "feedback_humor": humor}
    fonte.update(alterar or {})
    return motor.registrar_feedback_contextual(tipo=tipo,
        aceito=True if tipo == "aceitacao" else False if tipo == "recusa" else None,
        resultado=texto, origem="presenca", alvo=identidade, id_evento=identidade, proveniencia=fonte)


@pytest.mark.parametrize("contexto", ["jogo", "conversa", "comandos"])
@pytest.mark.parametrize("texto,direcao", [
    ("Não, Lay. Essa piada passou do ponto.", "leve"),
    ("Gostei dessa piada.", "mais_humor"),
])
def test_tres_entregas_distintas_antes_de_preferencia_contextual(motor, contexto, texto, direcao):
    chave = f"personalidade:tolerancia_humor_implicita:{contexto}"
    for numero in range(3):
        assert _amostra(motor, str(numero), contexto, texto) is not None
        eventos = motor.memoria.listar_eventos_aprendizado(chave)
        assert len(eventos) == numero + 1, "primeira fronteira é persistir a qualificação"
        assert all(e["confirmado_usuario"] is False for e in eventos)
        preferencia = motor.carregar_preferencia_humor_duravel(contexto)
        if numero < 2:
            assert preferencia == {}
        else:
            assert preferencia["direcao"] == direcao
            assert preferencia["contexto"] == contexto
            assert preferencia["origem"] == "tolerancia_implicita"
            assert preferencia["autoriza_execucao"] is False
            assert preferencia["duravel"] is False
            assert len(preferencia["evidencias_refs"]) == 3
    assert motor.carregar_preferencia_humor_duravel("geral") == {}
    for vizinho in {"jogo", "conversa", "comandos"} - {contexto}:
        assert motor.carregar_preferencia_humor_duravel(vizinho) == {}


def test_replay_nao_soma_amostras_e_fonte_divergente_nao_substitui(motor):
    # Uma repetição de transporte tem exatamente a mesma proveniência.
    agora = time.time()
    fonte = {"id_entrega": "unica", "dominio": "jogo", "categoria": "resposta",
        "origem_produtor": "orquestrador_fala", "alvo": "unica", "entregue": True,
        "entrega_ts": agora - 1, "observado_ts": agora, "contexto_humor": "jogo",
        "feedback_humor": qualificar_feedback_humor("Gostei dessa piada.")}
    kwargs = dict(tipo="aceitacao", aceito=True, resultado="Gostei dessa piada.",
        origem="presenca", id_evento="unica", proveniencia=fonte)
    for _ in range(5):
        motor.registrar_feedback_contextual(**kwargs)
    chave = "personalidade:tolerancia_humor_implicita:jogo"
    assert len(motor.memoria.listar_eventos_aprendizado(chave)) == 1
    assert motor.carregar_preferencia_humor_duravel("jogo") == {}
    antes = deepcopy(motor.memoria.listar_eventos_aprendizado(chave))
    motor.registrar_feedback_contextual(**{**kwargs, "resultado": "Não gostei dessa piada."})
    assert motor.memoria.listar_eventos_aprendizado(chave) == antes


@pytest.mark.parametrize("alterar", [
    {"entregue": False}, {"contexto_humor": "geral"}, {"feedback_humor": {}},
    {"observado_ts": float("nan")}, {"entrega_ts": float("inf")},
    {"entrega_ts": time.time() + 1000}, {"id_entrega": "diferente"},
])
def test_proveniencia_invalida_nao_cria_amostra(motor, alterar):
    for n in range(3):
        try:
            _amostra(motor, str(n), alterar=alterar)
        except ValueError:
            pass  # Guarda histórica de identidade anterior ao aprendizado.
    assert motor.memoria.listar_eventos_aprendizado("personalidade:tolerancia_humor_implicita:jogo") == []
    assert motor.carregar_preferencia_humor_duravel("jogo") == {}


@pytest.mark.parametrize("texto", ["Não, Lay. O número da dica está errado.",
    'Crie um arquivo chamado "Gostei dessa piada".', "Não precisa comentar.",
    '"Essa piada passou do ponto."', "Estou triste, essa piada passou do ponto."])
def test_feedback_generico_nao_vira_tolerancia(motor, texto):
    for n in range(3):
        _amostra(motor, str(n), texto=texto)
    assert motor.carregar_preferencia_humor_duravel("jogo") == {}
    assert motor.memoria.listar_eventos_aprendizado("personalidade:tolerancia_humor_implicita:jogo") == []


def test_correcao_de_estilo_pesa_mais_que_recusa_sem_mudar_feedback_generico(motor):
    for n, texto in enumerate(["Essa piada passou do ponto.", "Não gostei dessa piada.", "Gostei dessa piada."]):
        _amostra(motor, str(n), texto=texto)
    estilos = motor.memoria.listar_eventos_aprendizado("personalidade:tolerancia_humor_implicita:jogo")
    pesos = {e["valor"]["evento"]: abs(e["sinal"]) for e in estilos}
    assert pesos["correcao"] > pesos["recusa"]
    genericos = motor.memoria.listar_eventos_aprendizado("feedback_contextual:presenca:correcao:jogo:0")
    assert genericos[0]["sinal"] == -0.35
    # Evidências mistas ainda não autorizam preferência: falta predominância.
    assert motor.carregar_preferencia_humor_duravel("jogo") == {}


def test_explicita_vigente_vence_implicita_mais_recente(motor):
    explicita = extrair_preferencia_humor("pode me zoar mais hoje", turno_id="pedido", agora=time.time() - 100)
    for n in range(3):
        _amostra(motor, str(n))
    implicita = motor.carregar_preferencia_humor_duravel("jogo")
    assert implicita and implicita["direcao"] == "leve"
    assert selecionar_preferencia_humor({"geral": explicita, "jogo": implicita}, contexto="jogo") == explicita


def test_reinicio_reconstroi_de_evidencias_e_expira_sem_reforco(motor):
    for n in range(3):
        _amostra(motor, str(n))
    novo = MotorAprendizadoRuntime(memoria_sqlite=motor.memoria, contexto_getter=lambda: {}, log=lambda *_a: None)
    antes = novo.carregar_preferencia_humor_duravel("jogo")
    assert antes["direcao"] == "leve"
    novo.maturidade.agora = lambda: datetime.fromtimestamp(time.time() + 15 * 86400)
    assert novo.carregar_preferencia_humor_duravel("jogo") == {}


def test_evidencias_velhas_nao_sao_rejuvenescidas_por_uma_nova(motor):
    for n in range(3):
        _amostra(motor, str(n), idade=16 * 86400)
    _amostra(motor, "recente")
    assert motor.carregar_preferencia_humor_duravel("jogo") == {}


def test_falha_persistencia_nao_publica_preferencia(motor, monkeypatch):
    def falhar(**_k):
        raise OSError("controle SQLite")
    monkeypatch.setattr(motor.memoria, "registrar_evidencia_aprendizado", falhar)
    for n in range(3):
        assert _amostra(motor, str(n)) is None
    assert motor.carregar_preferencia_humor_duravel("jogo") == {}


def test_silencio_qualificado_enfraquece_sem_criar_ou_inverter_direcao(motor):
    for n in range(3):
        _amostra(motor, str(n), texto="Gostei dessa piada.")
    antes = motor.maturidade.avaliar_tolerancia_humor("jogo")
    agora = time.time()
    fonte = {"id_entrega": "silencio", "dominio": "jogo", "categoria": "resposta",
        "origem_produtor": "orquestrador_fala", "alvo": "silencio", "entregue": True,
        "entrega_ts": agora-600, "observado_ts": agora, "contexto_humor": "jogo",
        "solicitacao_feedback_humor": True, "texto_solicitacao_humor": "Essa piada foi pesada?",
        "feedback_humor": {"alvo_feedback": "humor", "tipo": "silencio", "direcao": "neutro", "evidencia_literal": "silencio"}}
    motor.registrar_feedback_contextual(tipo="silencio",aceito=None,resultado="silencio",
        origem="presenca",id_evento="silencio",proveniencia=fonte)
    depois = motor.maturidade.avaliar_tolerancia_humor("jogo")
    assert depois["amostras_distintas"] == antes["amostras_distintas"] == 3
    assert depois["silencios_qualificados"] == 1
    assert depois["influencia_media"] < antes["influencia_media"]
    assert depois["direcao"] == antes["direcao"] == "mais_humor"


def test_baixa_confianca_nao_alimenta_tolerancia(motor):
    agora = time.time()
    for n in range(3):
        fonte = {"id_entrega": str(n), "dominio": "jogo", "categoria": "resposta",
            "origem_produtor": "orquestrador_fala", "alvo": str(n), "entregue": True,
            "entrega_ts": agora-1, "observado_ts": agora, "contexto_humor": "jogo",
            "feedback_humor": qualificar_feedback_humor("Gostei dessa piada.")}
        motor.registrar_feedback_contextual(tipo="aceitacao",aceito=True,resultado="Gostei dessa piada.",
            origem="presenca",id_evento=str(n),proveniencia=fonte, confianca=0.6)
    assert motor.memoria.listar_eventos_aprendizado("personalidade:tolerancia_humor_implicita:jogo") == []


@pytest.mark.parametrize("pergunta", ["Você consegue aprender minha tolerância ao humor?",
    "Você aprende se eu gosto das suas brincadeiras?", "Você respeita minha preferência de humor?"])
def test_catalogo_vivo_explica_limites_do_aprendizado_gradual(pergunta):
    from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
    mapa = MapaHabilidadesRuntime()
    for texto in (mapa.contexto_para_prompt(pergunta), mapa.responder_pergunta_capacidade(pergunta)):
        assert "três entregas distintas no mesmo contexto" in texto
        assert "Correção de estilo pesa mais que recusa" in texto
        assert "correção de fatos não calibra humor" in texto
        assert "preferência explícita vigente prevalece" in texto
        assert "não autoriza ações" in texto


def test_diagnostico_publico_expoe_suficiencia_sem_evidencia_pessoal(motor):
    from mente_laylay.memoria_mental.formatacao_diagnostico import formatar_diagnostico_terminal
    for n in range(3):
        _amostra(motor, str(n))
    diagnostico = motor.diagnostico_tolerancia_humor()
    texto = formatar_diagnostico_terminal({"memoria_aprendizado": {"tolerancia_humor": diagnostico}})
    assert "tolerância de humor: contexto=jogo amostras=3 aplicável=True direção=leve" in texto
    assert "Essa piada" not in texto
    assert "autoriza_execução=False" in texto
