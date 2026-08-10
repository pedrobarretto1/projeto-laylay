from __future__ import annotations

import threading

from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.personalidade.oralidade import preparar_texto_para_tts
from mente_laylay.personalidade.proporcao_resposta import (
    ajustar_proporcao_resposta,
    classificar_proporcao,
    limite_tokens_resposta,
    parece_pedido_reexplicacao,
)
from mente_laylay.personalidade.voz_runtime import VozRuntime


def test_promessa_de_acompanhamento_sem_mecanismo_e_corrigida() -> None:
    resultado = validar_alegacoes_da_fala(
        "Vou te manter atualizado sobre o lançamento quando sair.",
        plano={"comandos": []}, origem="resposta_ia",
    )

    assert "promessa_sem_mecanismo" in resultado["problemas"]
    assert "não acompanho novidades sozinha" in resultado["fala"]


def test_oferta_de_play_by_play_futuro_sem_monitoramento_e_bloqueada() -> None:
    resultado = validar_alegacoes_da_fala(
        "Quer um play-by-play das novidades quando sair?",
        plano={"comandos": []}, origem="resposta_ia",
    )

    assert "promessa_sem_mecanismo" in resultado["problemas"]


def test_promessa_de_pensar_e_responder_depois_e_bloqueada() -> None:
    resultado = validar_alegacoes_da_fala(
        "É uma charada interessante. Vou pensar um pouco mais antes de responder para garantir.",
        plano={"comandos": []},
        origem="resposta_ia",
    )

    assert "promessa_sem_mecanismo" in resultado["problemas"]
    assert "vou pensar" not in resultado["fala"].casefold()


def test_companhia_emocional_sem_promessa_tecnica_e_permitida() -> None:
    fala = "Vou te acompanhar nessa expectativa e torcer junto."
    resultado = validar_alegacoes_da_fala(
        fala, plano={"comandos": []}, origem="resposta_ia",
    )

    assert resultado["problemas"] == []
    assert resultado["fala"] == fala


def test_promessa_operacional_fisica_sem_comando_e_bloqueada() -> None:
    resultado = validar_alegacoes_da_fala(
        "Vou liberar o comando pra você aquecer seu strogonoff no fogão.",
        plano={
            "texto_usuario": "já tem strogonoff pronto",
            "ato_principal": "conversa",
            "requer_execucao": False,
            "comandos": [],
        },
        origem="resposta_ia",
    )

    assert "promessa_operacional_sem_comando" in resultado["problemas"]
    assert "fogão" not in resultado["fala"]
    assert "comando" not in resultado["fala"]
    assert resultado["fala"] == "Entendi. Então essa parte já está resolvida por aí."


def test_lembrete_real_confirmado_permite_promessa_correspondente() -> None:
    resultado = validar_alegacoes_da_fala(
        "Vou te avisar quando chegar a hora.",
        plano={"comandos": [{
            "intent": "AGENDAR_LEMBRETE", "executou": True, "confirmado": True,
        }]},
        origem="resposta_ia",
    )

    assert resultado["problemas"] == []
    assert resultado["fala"] == "Vou te avisar quando chegar a hora."


def test_estado_do_pc_sem_leitura_real_e_bloqueado() -> None:
    resultado = validar_alegacoes_da_fala(
        "A CPU está em 35 por cento e a memória está normal.",
        plano={"comandos": []}, origem="resposta_ia",
    )

    assert "estado_real_sem_leitura" in resultado["problemas"]
    assert "ainda não consultei" in resultado["fala"]


def test_estado_confirmado_por_executor_e_preservado() -> None:
    fala = "A lâmpada está desligada."
    resultado = validar_alegacoes_da_fala(
        fala,
        plano={"comandos": [{
            "intent": "IOT_STATUS", "executou": True,
            "confirmado": True, "status": "desligado",
        }]},
        origem="resposta_ia",
    )

    assert resultado["problemas"] == []
    assert resultado["fala"] == fala


def test_estado_subjetivo_da_personalidade_continua_permitido() -> None:
    fala = "Fiquei curiosa para ver como esse projeto vai evoluir."
    resultado = validar_alegacoes_da_fala(
        fala, plano={"comandos": []}, origem="resposta_ia",
    )

    assert resultado["problemas"] == []
    assert resultado["fala"] == fala


def test_verificador_final_aplica_guardiao_de_promessas() -> None:
    resultado = verificar_fala_turno(
        "Vou acompanhar as novidades e te avisar quando sair.",
        plano={"texto_usuario": "estou animado para o lançamento", "comandos": []},
        origem="ia_final",
    )

    assert "promessa_sem_mecanismo" in resultado["problemas"]
    assert "não acompanho novidades sozinha" in resultado["fala"]


def test_clima_compacto_ganha_conectores_apenas_para_tts() -> None:
    escrito = "Ensolarado 17 graus Celsius, umidade em 52% e vento de 10 quilômetros por hora."
    falado = preparar_texto_para_tts(escrito)

    assert escrito == "Ensolarado 17 graus Celsius, umidade em 52% e vento de 10 quilômetros por hora."
    assert "Ensolarado, com 17 graus Celsius" in falado
    assert "com umidade em 52 por cento" in falado


def test_horario_url_e_metricas_ficam_pronunciaveis() -> None:
    falado = preparar_texto_para_tts(
        "Às 17:30, CPU em 82%. Veja https://www.exemplo.com/status."
    )

    assert "17 horas e 30 minutos" in falado
    assert "o processador em 82 por cento" in falado
    assert "exemplo ponto com" in falado
    assert "https" not in falado


def test_apenas_ultima_pergunta_mantem_entonacao_interrogativa() -> None:
    falado = preparar_texto_para_tts("Tudo bem? Quer conversar? Como foi seu dia?")

    assert falado.count("?") == 1
    assert falado.endswith("?")


def test_runtime_exibe_original_e_envia_versao_oral_ao_tts() -> None:
    logs = []

    class Edge:
        ultimo_texto = ""

        class Communicate:
            def __init__(self, texto, **_kwargs):
                Edge.ultimo_texto = texto

            async def save(self, _caminho):
                return None

    class SoundFile:
        @staticmethod
        def read(_caminho):
            return [], 16000

    class Stream:
        active = False

    class SoundDevice:
        @staticmethod
        def play(*_args, **_kwargs):
            return None

        @staticmethod
        def get_stream():
            return Stream()

    runtime = VozRuntime(
        fallback_fala="fallback", voice="voz",
        edge_tts_mod=Edge, sounddevice_mod=SoundDevice,
        soundfile_mod=SoundFile, pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        preparar_tts_cb=preparar_texto_para_tts,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("", "", ""),
        compor_fala_proativa_cb=lambda _itens: ("", "calma", 1),
        ajustar_estado_fala_cb=lambda *_args: None,
        interrupt_event=threading.Event(),
        log=lambda mensagem: logs.append(mensagem),
    )
    escrito = "Ensolarado 17 graus Celsius, umidade em 52%."

    runtime.reproduzir_fala(escrito, "calma", 1)

    assert escrito in logs
    assert "Ensolarado, com 17 graus Celsius" in Edge.ultimo_texto
    assert Edge.ultimo_texto != escrito


def test_runtime_normaliza_volume_neutro_antes_do_edge_tts() -> None:
    parametros = {}

    class Edge:
        class Communicate:
            def __init__(self, _texto, **kwargs):
                parametros.update(kwargs)

            async def save(self, _caminho):
                return None

    class SoundFile:
        @staticmethod
        def read(_caminho):
            return [], 16000

    class Stream:
        active = False

    class SoundDevice:
        @staticmethod
        def play(*_args, **_kwargs):
            return None

        @staticmethod
        def get_stream():
            return Stream()

    runtime = VozRuntime(
        fallback_fala="fallback", voice="voz",
        edge_tts_mod=Edge, sounddevice_mod=SoundDevice,
        soundfile_mod=SoundFile, pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("0%", "+0Hz", "0%"),
        compor_fala_proativa_cb=lambda _itens: ("", "calma", 1),
        ajustar_estado_fala_cb=lambda *_args: None,
        interrupt_event=threading.Event(),
        log=lambda _mensagem: None,
    )

    runtime.reproduzir_fala("Olá", "atenta", 1)

    assert parametros["rate"] == "+0%"
    assert parametros["volume"] == "+0%"


def test_fallback_tts_quebrado_e_desativado_apos_primeira_falha() -> None:
    chamadas = []
    logs = []

    class PyttsxQuebrado:
        @staticmethod
        def init():
            chamadas.append("init")
            raise IndentationError("cache COM inválido")

    runtime = VozRuntime(
        fallback_fala="fallback", voice="voz",
        edge_tts_mod=None, sounddevice_mod=None,
        soundfile_mod=None, pyttsx3_mod=PyttsxQuebrado,
        limpar_para_voz_cb=lambda texto: texto,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("+0%", "+0Hz", "+0%"),
        compor_fala_proativa_cb=lambda _itens: ("", "calma", 1),
        ajustar_estado_fala_cb=lambda *_args: None,
        interrupt_event=threading.Event(),
        log=logs.append,
    )

    assert runtime.fallback_pyttsx("Oi", "calma") is False
    assert runtime.fallback_pyttsx("Oi de novo", "calma") is False
    assert chamadas == ["init"]
    assert sum("fallback local desativado" in log for log in logs) == 1


def test_cache_com_quebrado_migra_para_sapi_nativo_sem_repetir_pyttsx() -> None:
    chamadas: list[str] = []

    class PyttsxQuebrado:
        @staticmethod
        def init():
            chamadas.append("pyttsx")
            raise IndentationError("cache COM inválido")

    class SoundFile:
        @staticmethod
        def read(_caminho):
            return [0.0], 16000

    class SoundDevice:
        @staticmethod
        def play(*_args, **_kwargs):
            chamadas.append("play")

        @staticmethod
        def wait():
            return None

    runtime = VozRuntime(
        fallback_fala="fallback", voice="voz",
        edge_tts_mod=None, sounddevice_mod=SoundDevice,
        soundfile_mod=SoundFile, pyttsx3_mod=PyttsxQuebrado,
        limpar_para_voz_cb=lambda texto: texto,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("+0%", "+0Hz", "+0%"),
        compor_fala_proativa_cb=lambda _itens: ("", "calma", 1),
        ajustar_estado_fala_cb=lambda *_args: None,
        interrupt_event=threading.Event(),
        log=lambda *_args: None,
    )
    runtime._sintetizar_sapi_windows = lambda *_args, **_kwargs: True
    runtime._selecionar_saida_audio = lambda: 0

    assert runtime.fallback_pyttsx("Oi", "calma") is True
    assert runtime.fallback_pyttsx("Oi de novo", "calma") is True
    assert chamadas.count("pyttsx") == 1
    assert chamadas.count("play") == 2


def test_fala_inicial_pendente_e_cancelada_se_conversa_comecou() -> None:
    conclusoes = []
    falas = []

    runtime = VozRuntime(
        fallback_fala="fallback", voice="voz",
        edge_tts_mod=None, sounddevice_mod=None,
        soundfile_mod=None, pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("+0%", "+0Hz", "+0%"),
        compor_fala_proativa_cb=lambda itens: (itens[0]["texto"], "calma", 1),
        ajustar_estado_fala_cb=lambda *_args: None,
        proativa_permitida_cb=lambda: False,
        interrupt_event=threading.Event(),
        log=lambda _mensagem: None,
    )
    runtime.falar = lambda *args, **kwargs: falas.append((args, kwargs)) or True
    runtime.proativa_buffer = [{
        "tipo": "abertura", "texto": "Boa tarde!", "emocao": "calma",
        "nivel": 1, "forcar_inicio": True,
        "ao_concluir": lambda ok, motivo: conclusoes.append((ok, motivo)),
    }]

    runtime.flush_fala_proativa()

    assert falas == []
    assert conclusoes == [(False, "interacao_iniciada")]


def test_briefing_preservado_espera_turno_e_depois_ignora_bloqueio_do_chat() -> None:
    conclusoes = []
    falas = []

    runtime = VozRuntime(
        fallback_fala="fallback", voice="voz",
        edge_tts_mod=None, sounddevice_mod=None,
        soundfile_mod=None, pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("+0%", "+0Hz", "+0%"),
        compor_fala_proativa_cb=lambda itens: (itens[0]["texto"], "calma", 1),
        ajustar_estado_fala_cb=lambda *_args: None,
        proativa_permitida_cb=lambda: False,
        interrupt_event=threading.Event(),
        log=lambda _mensagem: None,
    )
    runtime.falar = lambda *args, **kwargs: falas.append((args, kwargs)) or True
    runtime.proativa_buffer = [{
        "tipo": "briefing", "texto": "Seu briefing de hoje.",
        "emocao": "calma", "nivel": 1, "forcar_inicio": False,
        "preservar_ate_entrega": True,
        "ao_concluir": lambda ok, motivo: conclusoes.append((ok, motivo)),
    }]

    runtime._turno_resposta_ativo = True
    runtime.flush_fala_proativa()
    assert falas == []
    assert len(runtime.proativa_buffer) == 1

    runtime._turno_resposta_ativo = False
    runtime.proativa_buffer[0]["nao_antes_ts"] = 0.0
    runtime.flush_fala_proativa()

    assert len(falas) == 1
    assert conclusoes == [(True, "entregue")]


def test_contexto_proativo_e_ativado_antes_de_a_fala_comecar() -> None:
    eventos = []
    runtime = VozRuntime(
        fallback_fala="fallback", voice="voz",
        edge_tts_mod=None, sounddevice_mod=None,
        soundfile_mod=None, pyttsx3_mod=None,
        limpar_para_voz_cb=lambda texto: texto,
        formatar_mensagem_cb=lambda texto, **_kwargs: texto,
        ducking_volume_cb=lambda _ativo: None,
        modular_audio_params_cb=lambda *_args: ("+0%", "+0Hz", "+0%"),
        compor_fala_proativa_cb=lambda itens: (itens[0]["texto"], "calma", 1),
        ajustar_estado_fala_cb=lambda *_args: None,
        interrupt_event=threading.Event(),
        log=lambda _mensagem: None,
    )

    def falar(*_args, **_kwargs):
        assert eventos == ["contexto"]
        eventos.append("fala")
        return True

    runtime.falar = falar
    runtime.proativa_buffer = [{
        "tipo": "assistencia_clipboard",
        "texto": "Quer que eu investigue?",
        "emocao": "calma",
        "nivel": 1,
        "forcar_inicio": False,
        "preservar_ate_entrega": True,
        "ao_iniciar": lambda: eventos.append("contexto"),
        "ao_concluir": lambda ok, _motivo: eventos.append("fim" if ok else "falha"),
    }]

    runtime.flush_fala_proativa()

    assert eventos == ["contexto", "fala", "fim"]


def test_inventario_de_playlists_preserva_escrita_e_simplifica_a_voz() -> None:
    escrito = "Suas playlists são: alternativo (3), anime (24), rock (3), vibes (1)."

    falado = preparar_texto_para_tts(escrito)

    assert escrito == "Suas playlists são: alternativo (3), anime (24), rock (3), vibes (1)."
    assert falado == "Você tem 4 playlists: alternativo, anime, rock e vibes."
    assert "(3)" not in falado


def test_titulos_de_playlist_soam_como_artista_e_musica_sem_rotulos_do_youtube() -> None:
    escrito = (
        "A playlist Rock é curtinha: 3 músicas. As principais são "
        "Guns N' Roses - Sweet Child O' Mine (Official Music Video). "
        "Sepultura - Roots Bloody Roots OFFICIAL VIDEO. "
        "Slipknot - Sulfur OFFICIAL VIDEO HD."
    )

    falado = preparar_texto_para_tts(escrito)

    assert "Guns N' Roses, com Sweet Child O' Mine" in falado
    assert "Sepultura, com Roots Bloody Roots" in falado
    assert "Slipknot, com Sulfur" in falado
    assert "Official" not in falado
    assert "HD" not in falado


def test_hifen_entre_artista_e_musica_nao_vira_marcador_markdown() -> None:
    falado = preparar_texto_para_tts(
        "A playlist Rock tem Guns N' Roses - Sweet Child O' Mine."
    )

    assert "Guns N' Roses, com Sweet Child O' Mine" in falado


def test_formula_e_oralizada_sem_alterar_texto_exibido() -> None:
    escrito = r"A equação é \(y + 7 = 2x - 5\)."

    falado = preparar_texto_para_tts(escrito)

    assert escrito == r"A equação é \(y + 7 = 2x - 5\)."
    assert "y mais 7 é igual a 2 x menos 5" in falado.casefold()
    assert "+" not in falado
    assert "=" not in falado
    assert r"\(" not in falado


def test_equacao_nao_perde_operadores_antes_da_oralizacao() -> None:
    from mente_laylay.emocoes.perfil_emocional import limpar_para_voz

    limpa = limpar_para_voz("Temos 2x - 19 = 6x - 5.")
    falada = preparar_texto_para_tts(limpa)

    assert "=" in limpa
    assert "2 x menos 19 é igual a 6 x menos 5" in falada.casefold()


def test_travesso_matematico_e_pronunciado_como_menos() -> None:
    from mente_laylay.emocoes.perfil_emocional import limpar_para_voz

    limpa = limpar_para_voz("3(2x – 5) – 4(x + 1) = 6x – 5")
    falada = preparar_texto_para_tts(limpa)

    assert "–" not in limpa
    assert "2 x menos 5" in falada.casefold()
    assert "6 x menos 5" in falada.casefold()


def test_numero_da_equacao_nao_vira_numero_de_etapa() -> None:
    falada = preparar_texto_para_tts(
        "O lado direito fica 6x - 14 + 9. Na segunda etapa, juntamos os termos."
    )

    assert "Na etapa 9" not in falada


def test_fracao_latex_e_lida_como_divisao() -> None:
    falado = preparar_texto_para_tts(r"Temos \(x = \frac{12}{3}\).")

    assert "x é igual a 12 dividido por 3" in falado.casefold()


def test_equacao_compacta_recebe_perfil_matematico() -> None:
    equacao = "3(2x-5)-4(x+1)=2(3x-7)+9"

    assert classificar_proporcao(equacao) == "matematica"
    assert limite_tokens_resposta(equacao) == 800


def test_conversa_casual_curta_recebe_resposta_proporcional() -> None:
    resposta = " ".join([
        "Tô inspirada hoje, deixa comigo.",
        "Essa combinação parece divertida.",
        "Eu ainda inventaria mais três sabores e faria um menu inteiro.",
        "Depois contaria uma longa história sobre cada um deles.",
    ])

    ajustada = ajustar_proporcao_resposta(
        resposta,
        "tá sabendo das ideias kkkk",
        "conversa",
    )

    assert len(ajustada) <= 220
    assert "longa história" not in ajustada


def test_resolucao_matematica_nao_perde_a_conclusao_por_ser_entrada_curta() -> None:
    equacao = "3(2x-5)-4(x+1)=2(3x-7)+9"
    resposta = " ".join([
        "Vamos resolver com calma.",
        "Primeiro, distribuímos os termos.",
        "O lado esquerdo fica 6x menos 15 menos 4x menos 4.",
        "Isso resulta em 2x menos 19.",
        "O lado direito fica 6x menos 14 mais 9.",
        "Isso resulta em 6x menos 5.",
        "Agora igualamos os dois lados.",
        "Temos 2x menos 19 igual a 6x menos 5.",
        "Passando os termos, menos 14 é igual a 4x.",
        "Portanto, x é igual a menos 3,5.",
    ])

    ajustada = ajustar_proporcao_resposta(resposta, equacao, "conversa")

    assert ajustada == resposta
    assert ajustada.endswith("x é igual a menos 3,5.")


def test_nao_entendi_pede_reexplicacao_em_vez_de_resposta_curta() -> None:
    resposta = " ".join([
        "Vamos refazer de outro jeito.",
        "Primeiro distribuímos os números.",
        "Depois juntamos os termos semelhantes.",
        "Em seguida isolamos a variável.",
        "Por fim conferimos na expressão original.",
        "O resultado é x igual a menos 3,5.",
    ])

    assert parece_pedido_reexplicacao("não entendi") is True
    assert classificar_proporcao("não entendi") == "explicativa"
    assert ajustar_proporcao_resposta(resposta, "não entendi", "conversa") == resposta


def test_estrutura_da_resposta_impede_corte_mesmo_sem_frase_especial() -> None:
    resposta = " ".join([
        "Vou reorganizar a ideia.",
        "1. Primeiro identificamos a causa.",
        "2. Depois separamos os efeitos.",
        "3. Em seguida comparamos as alternativas.",
        "4. Por fim chegamos à conclusão correta.",
    ])

    ajustada = ajustar_proporcao_resposta(
        resposta,
        "por outro ângulo",
        "conversa",
    )

    assert ajustada == resposta
    assert "conclusão correta" in ajustada
