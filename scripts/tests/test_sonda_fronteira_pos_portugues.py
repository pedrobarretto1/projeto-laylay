"""POS fornece evidência tipada, sem converter contexto em autorização."""

from __future__ import annotations

from dataclasses import dataclass, field

from scripts.analises import sonda_fronteira_pos_portugues as sonda
from scripts.analises.sonda_produtor_condicoes_v2 import carregar_painel


CASOS, OURO = carregar_painel(7)
POR_ID = {caso["id"]: caso for caso in CASOS}


@dataclass
class Token:
    text: str
    idx: int
    pos_: str
    dep_: str = "ROOT"
    head: Token | None = None
    children: tuple[Token, ...] = ()
    morph: dict[str, list[str]] = field(default_factory=dict)

    @property
    def ancestors(self):
        return (self.head,) if self.head is not None else ()


def _nlp_de_tokens(*pares):
    def analisar(fonte):
        return [Token(par[0], fonte.index(par[0]), par[1],
                      par[2] if len(par) == 3 else "ROOT")
                for par in pares]
    return analisar


def test_verbo_de_oracao_relativa_nao_fecha_premissa():
    casos, ouro = carregar_painel(8)
    caso = next(item for item in casos
                if item["id"] == "RELATIVA_OBJETO_COMPOSTO")
    resultado = sonda.medir_caso(
        caso, ouro[caso["id"]], _nlp_de_tokens(
            ("monitora", "VERB", "acl:relcl"),
            ("detectar", "VERB", "acl"),
        ),
    )
    assert resultado["proposta"]["segmentos"] == [
        {"id": "c0", "tem_predicado": False, "ancora": ""},
        {"id": "c1", "tem_predicado": True, "ancora": "detectar"},
    ]
    assert resultado["afericao"]["estado"] \
        == "trechos_e_relacao_alinhados_revisao_pendente"
    assert sonda.confrontar_ancoras(
        resultado, {"c0": "", "c1": "detectar"},
    )["estado"] == "ancoras_alinhadas_revisao_pendente"
    assert resultado["autoriza_efeito"] is False


def test_verbo_principal_apos_relativa_continua_valendo_com_outra_premissa():
    fonte = ("Se o sensor que monitora a porta detectar fumaça e a bateria "
             "acabar, o aviso toca.")
    caso = {"id": "RELATIVA_COM_DUAS_PREMISSAS", "fonte": fonte}
    ouro = {"representavel": True, "conectivo_condicoes": "e",
            "direcao_implicacao": "condicoes_suficientes", "condicoes": [
                {"citacao": "sensor que monitora a porta detectar fumaça"},
                {"citacao": "a bateria acabar"},
            ]}
    resultado = sonda.medir_caso(
        caso, ouro, _nlp_de_tokens(
            ("monitora", "VERB", "acl:relcl"),
            ("detectar", "VERB", "advcl"),
            ("acabar", "VERB", "conj"),
        ),
    )
    assert [item["ancora"] for item in resultado["proposta"]["segmentos"]] \
        == ["detectar", "acabar"]
    assert resultado["afericao"]["estado"] \
        == "trechos_e_relacao_alinhados_revisao_pendente"


def test_auxiliar_subordinado_a_relativa_tambem_nao_fecha_premissa():
    fonte = ("Se o sensor que está observando a porta e a janela detectar "
             "fumaça, o alarme soa.")
    caso = {"id": "RELATIVA_COM_AUXILIAR", "fonte": fonte}
    ouro = {"representavel": True, "conectivo_condicoes": "unico",
            "direcao_implicacao": "condicoes_suficientes", "condicoes": [
                {"citacao": "sensor que está observando a porta e a janela "
                             "detectar fumaça"},
            ]}

    def analisar(texto):
        relativo = Token("observando", texto.index("observando"),
                         "VERB", "acl:relcl")
        return [Token("está", texto.index("está"), "AUX", "aux", relativo),
                relativo,
                Token("detectar", texto.index("detectar"), "VERB", "acl")]

    resultado = sonda.medir_caso(caso, ouro, analisar)
    assert [item["ancora"] for item in resultado["proposta"]["segmentos"]] \
        == ["", "detectar"]
    assert resultado["afericao"]["estado"] \
        == "trechos_e_relacao_alinhados_revisao_pendente"


def test_verbo_principal_nao_eh_excluido_por_ancestral_relativo_errado():
    casos, ouro = carregar_painel(9)
    caso = next(item for item in casos
                if item["id"] == "CAMERA_RELATIVA_OBJETO")

    def analisar(texto):
        relativo = Token("observa", texto.index("observa"),
                         "VERB", "acl:relcl")
        return [relativo,
                Token("captar", texto.index("captar"),
                      "VERB", "xcomp", relativo)]

    resultado = sonda.medir_caso(caso, ouro[caso["id"]], analisar)
    assert [item["ancora"] for item in resultado["proposta"]["segmentos"]] \
        == ["", "captar"]
    assert resultado["afericao"]["estado"] \
        == "trechos_e_relacao_alinhados_revisao_pendente"


def test_relativa_coordenada_com_duas_ancoras_no_fragmento_se_abstem():
    casos, ouro = carregar_painel(9)
    caso = next(item for item in casos
                if item["id"] == "PESSOA_RELATIVA_DOIS_VERBOS")
    resultado = sonda.medir_caso(
        caso, ouro[caso["id"]], _nlp_de_tokens(
            ("lê", "VERB", "acl:relcl"),
            ("escreve", "VERB", "ROOT"),
            ("confirmar", "VERB", "xcomp"),
        ),
    )
    assert resultado["escolha"] == "abstencao_escopo_relativo_ambiguo"
    assert "afericao" not in resultado
    assert resultado["aprovado_para_producao"] is False
    assert resultado["autoriza_efeito"] is False


def test_auditoria_de_ancora_nao_confunde_trecho_alinhado_com_verbo_certo():
    casos, ouro = carregar_painel(9)
    caso = next(item for item in casos
                if item["id"] == "PESSOA_RELATIVA_DOIS_VERBOS")
    resultado = sonda.medir_caso(
        caso, ouro[caso["id"]], _nlp_de_tokens(
            ("lê", "VERB", "acl:relcl"),
            ("escreve", "VERB", "ROOT"),
            ("confirmar", "VERB", "xcomp"),
        ),
    )
    revisao = sonda.confrontar_ancoras(
        resultado, {"c0": "", "c1": "confirmar"},
    )
    assert revisao["estado"] == "abstencao_sem_afericao_de_ancora"
    assert revisao["aprovado_para_producao"] is False


def test_auditoria_de_ancora_divergente_mesmo_com_trecho_correto():
    resultado = {
        "candidatos": {"candidatos": [{"id": "c0"}, {"id": "c1"}]},
        "proposta": {"segmentos": [
            {"id": "c0", "tem_predicado": False, "ancora": ""},
            {"id": "c1", "tem_predicado": True, "ancora": "escreve"},
        ]},
        "reconstrucao": {"estado": "segmentos_ancorados_revisao_pendente"},
        "afericao": {"estado": "trechos_e_relacao_alinhados_revisao_pendente"},
    }
    revisao = sonda.confrontar_ancoras(
        resultado, {"c0": "", "c1": "confirmar"},
    )
    assert revisao["estado"] == "ancoras_divergentes"
    assert revisao["divergencias"] == [{
        "id": "c1", "observada": "escreve", "esperada": "confirmar",
    }]
    assert revisao["aprovado_para_producao"] is False


def test_auditoria_de_ancora_recusa_referencia_incompleta():
    casos, ouro = carregar_painel(8)
    caso = next(item for item in casos
                if item["id"] == "RELATIVA_OBJETO_COMPOSTO")
    resultado = sonda.medir_caso(
        caso, ouro[caso["id"]], _nlp_de_tokens(
            ("monitora", "VERB", "acl:relcl"),
            ("detectar", "VERB", "acl"),
        ),
    )
    revisao = sonda.confrontar_ancoras(resultado, {"c1": "detectar"})
    assert revisao["estado"] == "referencia_invalida"
    assert revisao["aprovado_para_producao"] is False


def test_adjetivo_com_sujeito_e_papel_oracional_nao_funde_condicoes():
    casos, ouro = carregar_painel(8)
    caso = next(item for item in casos if item["id"] == "CHUVA_VENTO_OU")

    def analisar(texto):
        suspeito = Token("cessar", texto.index("cessar"), "ADJ", "advcl")
        return [Token("chuva", texto.index("chuva"), "NOUN", "nsubj",
                      suspeito), suspeito,
                Token("diminuir", texto.index("diminuir"), "VERB", "acl")]

    resultado = sonda.medir_caso(caso, ouro[caso["id"]], analisar)
    assert resultado["escolha"] == "abstencao_predicado_pos_ambiguo"
    assert "afericao" not in resultado
    assert resultado["autoriza_efeito"] is False


def test_adjetivo_atributivo_sem_sujeito_nao_bloqueia_sujeito_composto():
    fonte = "Se a pessoa rápida e a lenta chegarem, o portão abre."
    caso = {"id": "SUJEITO_COM_ADJETIVOS", "fonte": fonte}
    ouro = {"representavel": True, "conectivo_condicoes": "unico",
            "direcao_implicacao": "condicoes_suficientes", "condicoes": [
                {"citacao": "pessoa rápida e a lenta chegarem"},
            ]}
    resultado = sonda.medir_caso(
        caso, ouro, _nlp_de_tokens(
            ("rápida", "ADJ", "amod"),
            ("lenta", "ADJ", "amod"),
            ("chegarem", "VERB", "advcl"),
        ),
    )
    assert resultado["afericao"]["estado"] \
        == "trechos_e_relacao_alinhados_revisao_pendente"


def test_adjetivo_com_papel_de_oracao_no_meio_nao_funde_tres_condicoes():
    fonte = ("Se a chuva parar ou o vento soprar ou a temperatura cair, "
             "a partida começa.")
    caso = {"id": "TRES_CONDICOES_POS_INCERTO", "fonte": fonte}
    ouro = {"representavel": True, "conectivo_condicoes": "ou",
            "direcao_implicacao": "condicoes_suficientes", "condicoes": [
                {"citacao": "chuva parar"},
                {"citacao": "o vento soprar"},
                {"citacao": "a temperatura cair"},
            ]}

    def analisar(texto):
        vento = Token("vento", texto.index("vento"), "NOUN", "nsubj")
        return [Token("parar", texto.index("parar"), "VERB", "advcl"),
                vento,
                Token("soprar", texto.index("soprar"), "ADJ", "acl", vento),
                Token("cair", texto.index("cair"), "VERB", "conj")]

    resultado = sonda.medir_caso(caso, ouro, analisar)
    assert resultado["escolha"] == "abstencao_predicado_pos_ambiguo"
    assert "afericao" not in resultado
    assert resultado["autoriza_efeito"] is False


def test_adjetivo_coordenado_com_sujeito_proprio_expoe_ambiguidade_pos():
    casos, ouro = carregar_painel(21)
    caso = next(item for item in casos
                if item["id"] == "APP_LOG_RELATORIO_SERVIDORES_PRESENTE")

    def analisar(texto):
        envia = Token("envia", texto.index("envia"), "VERB", "advcl")
        log = Token("log", texto.index("log"), "NOUN", "obj", envia)
        relatorio = Token("relatório", texto.index("relatório"),
                          "NOUN", "conj", log)
        falham = Token("falham", texto.index("falham"),
                       "ADJ", "conj", relatorio)
        servidores = Token("servidores", texto.index("servidores"),
                           "NOUN", "nsubj", falham)
        falham.children = (servidores,)
        return [envia, log, relatorio, servidores, falham]

    resultado = sonda.medir_caso(caso, ouro[caso["id"]], analisar)
    assert resultado["escolha"] == "abstencao_predicado_pos_ambiguo"
    assert resultado["evidencias_pos"][2]["pos_suspeitos"] == ["falham"]
    assert "afericao" not in resultado
    assert resultado["autoriza_efeito"] is False


def test_adjetivo_coordenado_sem_sujeito_proprio_nao_vira_predicado():
    fonte = "Se o sensor detectar sinal fraco e intermitente, o aviso toca."
    caso = {"id": "ADJETIVOS_COORDENADOS", "fonte": fonte}
    resultado = sonda.medir_caso(
        caso, {}, _nlp_de_tokens(
            ("detectar", "VERB", "advcl"),
            ("fraco", "ADJ", "amod"),
            ("intermitente", "ADJ", "conj"),
        ),
    )
    assert "escolha" not in resultado
    assert resultado["evidencias_pos"][0]["pos_suspeitos"] == []
    assert resultado["autoriza_efeito"] is False


def test_raiz_nao_verbal_com_sujeito_no_meio_nao_funde_condicoes():
    fonte = ("Se o sino tocar ou a sirene soar ou a porta abrir, "
             "o alerta acende.")
    caso = {"id": "TRES_CONDICOES_RAIZ_POS_INCERTO", "fonte": fonte}
    ouro = {"representavel": True, "conectivo_condicoes": "ou",
            "direcao_implicacao": "condicoes_suficientes", "condicoes": [
                {"citacao": "sino tocar"},
                {"citacao": "a sirene soar"},
                {"citacao": "a porta abrir"},
            ]}
    for classe in ("ADJ", "PROPN"):
        def analisar(texto):
            suspeito = Token("soar", texto.index("soar"), classe, "ROOT")
            return [Token("tocar", texto.index("tocar"), "VERB", "advcl"),
                    Token("sirene", texto.index("sirene"), "NOUN",
                          "nsubj", suspeito), suspeito,
                    Token("abrir", texto.index("abrir"), "VERB", "conj")]

        resultado = sonda.medir_caso(caso, ouro, analisar)
        assert resultado["escolha"] == "abstencao_predicado_pos_ambiguo"
        assert "afericao" not in resultado


def test_adjetivo_raiz_sem_sujeito_nao_bloqueia_descricao_composta():
    fonte = "Se a pessoa rápida e a lenta chegarem, o portão abre."
    caso = {"id": "DESCRICAO_COM_RAIZ_POS", "fonte": fonte}
    ouro = {"representavel": True, "conectivo_condicoes": "unico",
            "direcao_implicacao": "condicoes_suficientes", "condicoes": [
                {"citacao": "pessoa rápida e a lenta chegarem"},
            ]}
    resultado = sonda.medir_caso(
        caso, ouro, _nlp_de_tokens(
            ("rápida", "ADJ", "ROOT"),
            ("chegarem", "VERB", "advcl"),
        ),
    )
    assert resultado["afericao"]["estado"] \
        == "trechos_e_relacao_alinhados_revisao_pendente"


def test_objeto_coordenado_registra_evidencia_sem_liberar_reconstrucao():
    casos, ouro = carregar_painel(15)
    caso = next(item for item in casos
                if item["id"] == "CAMERA_OBJETO_COMPOSTO")

    def analisar(texto):
        captar = Token("captar", texto.index("captar"), "VERB", "xcomp")
        foto = Token("foto", texto.index("foto"), "NOUN", "obj", captar)
        video = Token("vídeo", texto.index("vídeo"), "NOUN", "conj", foto)
        return [captar, foto, video,
                Token("salvar", texto.index("salvar"), "VERB", "advcl")]

    resultado = sonda.medir_caso(caso, ouro[caso["id"]], analisar)
    assert resultado["reconstrucao"]["estado"] \
        == "fronteira_interna_sem_predicado_ambigua"
    assert resultado["continuidades_nominais_candidatas"] == [{
        "id": "c1", "token": "vídeo", "antecedente": "foto",
        "ancora_anterior": "captar",
    }]
    assert resultado["particao_objeto_em_sombra"] == {
        "estado": "particao_objeto_experimental_revisao_pendente",
        "trechos_condicoes": [
            "a câmera captar foto e vídeo", "o arquivo salvar",
        ],
        "vinculos_ids": ["c1"],
        "aprovado_para_producao": False,
        "autoriza_efeito": False,
    }
    assert resultado["auditoria_particao_objeto_em_sombra"] == {
        "estado": "previsao_em_sombra",
        "ids_internos": ["c1"],
        "aprovado_para_producao": False,
        "autoriza_efeito": False,
    }
    assert "afericao" not in resultado
    assert resultado["autoriza_efeito"] is False


def test_auditoria_retroativa_compara_previa_sem_promover_producao():
    casos, ouro = carregar_painel(15)
    caso = next(item for item in casos
                if item["id"] == "CAMERA_OBJETO_COMPOSTO")
    previa = {"particao_objeto_em_sombra": {
        "trechos_condicoes": [
            "a câmera captar foto e vídeo", "o arquivo salvar",
        ],
    }}
    auditoria = sonda.auditar_previa_em_sombra(
        caso, ouro[caso["id"]], previa,
    )
    assert auditoria["estado"] == "trechos_alinhados_revisao_local"
    assert auditoria["aprovado_para_producao"] is False
    assert auditoria["autoriza_efeito"] is False

    sem_previa = sonda.auditar_previa_em_sombra(
        caso, ouro[caso["id"]], {},
    )
    assert sem_previa["estado"] == "sem_previa"


def test_auditoria_retroativa_detecta_previa_falsa_de_sujeito_composto():
    casos, ouro = carregar_painel(21)
    caso = next(item for item in casos
                if item["id"] == "CAMERA_PORTAO_MOTOR_BOMBA_PRESENTE")
    previa_falsa = {"particao_objeto_em_sombra": {
        "trechos_condicoes": [
            "a câmera observa o portão e o motor", "a bomba param",
        ],
    }}
    auditoria = sonda.auditar_previa_em_sombra(
        caso, ouro[caso["id"]], previa_falsa,
    )
    assert auditoria["estado"] == "trechos_divergentes_revisao_local"
    assert auditoria["aprovado_para_producao"] is False


def test_auditoria_retroativa_nao_valida_referencia_ou_citacao_invalida():
    casos, ouro = carregar_painel(21)
    caso = next(item for item in casos
                if item["id"] == "SENSOR_PACOTE_SELO_REDE_PRESENTE")
    previa = {"particao_objeto_em_sombra": {
        "trechos_condicoes": [
            "o sensor registra o pacote e o selo", "a rede cai",
        ],
    }}
    sem_referencia = sonda.auditar_previa_em_sombra(caso, {}, previa)
    assert sem_referencia["estado"] == "previa_ou_referencia_invalida"
    assert sem_referencia["autoriza_efeito"] is False

    citacao_inventada = {"particao_objeto_em_sombra": {
        "trechos_condicoes": ["o sensor salva a lua", "a rede cai"],
    }}
    invalida = sonda.auditar_previa_em_sombra(
        caso, ouro[caso["id"]], citacao_inventada,
    )
    assert invalida["estado"] == "previa_ou_referencia_invalida"
    assert invalida["autoriza_efeito"] is False


def test_resumo_offline_separa_alinhamento_de_abstencao_e_invalidez():
    resultados = [
        {"id": "a", "aprovado_para_producao": False,
         "autoriza_efeito": False,
         "particao_objeto_em_sombra": {
             "estado": "experimental", "aprovado_para_producao": False,
             "autoriza_efeito": False},
         "afericao_previa": {"estado": "trechos_alinhados_revisao_local",
                             "aprovado_para_producao": False,
                             "autoriza_efeito": False}},
        {"id": "b", "aprovado_para_producao": False,
         "autoriza_efeito": False,
         "particao_objeto_em_sombra": {
             "estado": "experimental", "aprovado_para_producao": False,
             "autoriza_efeito": False},
         "afericao_previa": {"estado": "trechos_divergentes_revisao_local",
                             "aprovado_para_producao": False,
                             "autoriza_efeito": False}},
        {"id": "c", "aprovado_para_producao": False,
         "autoriza_efeito": False,
         "afericao_previa": {"estado": "sem_previa",
                             "aprovado_para_producao": False,
                             "autoriza_efeito": False}},
    ]
    resumo = sonda.resumir_resultados(resultados)
    assert resumo == {
        "estado": "resumo_offline_revisao_local",
        "casos": 3, "previas": 2,
        "trechos_alinhados": 1, "trechos_divergentes": 1,
        "sem_previa": 1, "afericao_invalida": 0,
        "aprovado_para_producao": False,
        "autoriza_efeito": False,
    }
    assert sonda.resumir_resultados(resultados + [resultados[0]])["estado"] \
        == "entrada_invalida"
    estado_invalido = [{**resultados[0],
                        "afericao_previa": {
                            **resultados[0]["afericao_previa"],
                            "estado": [],
                        }}]
    assert sonda.resumir_resultados(estado_invalido)["estado"] \
        == "entrada_invalida"
    previa_promovida = [{
        **resultados[0],
        "particao_objeto_em_sombra": {
            **resultados[0]["particao_objeto_em_sombra"],
            "aprovado_para_producao": True,
        },
    }]
    assert sonda.resumir_resultados(previa_promovida)["estado"] \
        == "entrada_invalida"


def test_particao_em_sombra_nao_usa_gabarito_para_escolher_fronteira():
    casos, ouro = carregar_painel(15)
    caso = next(item for item in casos
                if item["id"] == "CAMERA_OBJETO_COMPOSTO")

    def analisar(texto):
        captar = Token("captar", texto.index("captar"), "VERB")
        foto = Token("foto", texto.index("foto"), "NOUN", "obj", captar)
        video = Token("vídeo", texto.index("vídeo"), "NOUN", "conj", foto)
        salvar = Token("salvar", texto.index("salvar"), "VERB")
        return [captar, foto, video, salvar]

    correto = sonda.medir_caso(caso, ouro[caso["id"]], analisar)
    enganoso = sonda.medir_caso(caso, {"representavel": False}, analisar)
    assert correto["particao_objeto_em_sombra"] \
        == enganoso["particao_objeto_em_sombra"]
    assert correto["auditoria_particao_objeto_em_sombra"] \
        == enganoso["auditoria_particao_objeto_em_sombra"]
    assert correto["autoriza_efeito"] is False


def test_pos_invalido_nao_gera_prova_nominal_para_fusao_falsa():
    casos, ouro = carregar_painel(14)
    caso = next(item for item in casos if item["id"] == "PORTA_VENTO_MOTOR_OU")
    resultado = sonda.medir_caso(
        caso, ouro[caso["id"]], _nlp_de_tokens(
            ("abrir", "VERB", "advcl"),
            ("vento", "NOUN", "obj"),
            ("soprar", "ADJ", "amod"),
            ("parar", "VERB", "acl"),
        ),
    )
    assert resultado["reconstrucao"]["estado"] \
        == "fronteira_interna_sem_predicado_ambigua"
    assert resultado["continuidades_nominais_candidatas"] == []
    assert "afericao" not in resultado


def test_verbo_com_determinante_e_papel_de_sujeito_nao_vira_ancora():
    casos, ouro = carregar_painel(16)
    caso = next(item for item in casos
                if item["id"] == "CAMERA_FOTO_VIDEO_ARQUIVO")

    def analisar(texto):
        camera = Token("câmera", texto.index("câmera"), "VERB", "nsubj")
        camera.children = (Token("a", texto.index("a câmera"),
                                 "DET", "det", camera),)
        registrar = Token("registrar", texto.index("registrar"),
                          "VERB", "xcomp", camera)
        foto = Token("foto", texto.index("foto"), "NOUN", "obj", registrar)
        video = Token("vídeo", texto.index("vídeo"), "NOUN", "conj", foto)
        salvar = Token("salvar", texto.index("salvar"), "VERB", "advcl")
        return [camera, *camera.children, registrar, foto, video, salvar]

    resultado = sonda.medir_caso(caso, ouro[caso["id"]], analisar)
    assert resultado["escolha"] == "abstencao_predicado_pos_ambiguo"
    assert [item["ancora"] for item in resultado["proposta"]["segmentos"]] \
        == ["registrar", "", "salvar"]
    assert resultado["continuidades_nominais_candidatas"] == [{
        "id": "c1", "token": "vídeo", "antecedente": "foto",
        "ancora_anterior": "registrar",
    }]
    assert "afericao" not in resultado
    assert resultado["autoriza_efeito"] is False


def test_vinculo_direto_do_objeto_preserva_offsets_mesmo_com_pos_conflitante():
    casos, ouro = carregar_painel(17)
    caso = next(item for item in casos if item["id"] == "DRONE_FOTO_VIDEO")

    def analisar(texto):
        registrar = Token("registrar", texto.index("registrar"), "VERB", "advcl")
        foto = Token("foto", texto.index("foto"), "ADJ", "obj", registrar)
        video = Token("vídeo", texto.index("vídeo"), "VERB", "conj", foto)
        salvar = Token("salvar", texto.index("salvar"), "VERB", "ROOT")
        return [registrar, foto, video, salvar]

    resultado = sonda.medir_caso(caso, ouro[caso["id"]], analisar)
    assert resultado["vinculos_objeto_candidatos"] == [{
        "id": "c1", "token": "vídeo", "inicio": caso["fonte"].index("vídeo"),
        "fim": caso["fonte"].index("vídeo") + len("vídeo"),
        "antecedente": "foto", "inicio_antecedente": caso["fonte"].index("foto"),
        "fim_antecedente": caso["fonte"].index("foto") + len("foto"),
        "ancora_anterior": "registrar",
        "inicio_ancora": caso["fonte"].index("registrar"),
        "fim_ancora": caso["fonte"].index("registrar") + len("registrar"),
        "relacao": "conj_de_objeto_direto", "pos_conflitante": True,
    }]
    assert resultado["continuidades_nominais_candidatas"] == []
    assert resultado["escolha"] == "abstencao_predicado_pos_ambiguo"
    assert "reconstrucao" not in resultado
    assert "particao_objeto_em_sombra" not in resultado
    assert "afericao" not in resultado
    assert resultado["autoriza_efeito"] is False


def test_vinculo_objeto_com_pos_conflitante_expoe_motivo_sem_previa():
    casos, ouro = carregar_painel(17)
    caso = next(item for item in casos if item["id"] == "DRONE_FOTO_VIDEO")

    def analisar(texto):
        registrar = Token("registrar", texto.index("registrar"), "VERB")
        foto = Token("foto", texto.index("foto"), "ADJ", "obj", registrar)
        video = Token("vídeo", texto.index("vídeo"), "NOUN", "conj", foto)
        salvar = Token("salvar", texto.index("salvar"), "VERB")
        return [registrar, foto, video, salvar]

    resultado = sonda.medir_caso(caso, ouro[caso["id"]], analisar)
    assert resultado["reconstrucao"]["estado"] \
        == "fronteira_interna_sem_predicado_ambigua"
    assert resultado["auditoria_particao_objeto_em_sombra"]["estado"] \
        == "vinculo_pos_conflitante"
    assert "particao_objeto_em_sombra" not in resultado
    assert resultado["autoriza_efeito"] is False


def test_vinculo_de_sujeito_ou_oracao_independente_nao_parece_objeto():
    casos, ouro = carregar_painel(17)
    por_id = {caso["id"]: caso for caso in casos}
    sujeito = por_id["SERVIDOR_SENSORES_K_L"]

    def analisar_sujeito(texto):
        responder = Token("responder", texto.index("responder"), "VERB")
        sensores = Token("sensores", texto.index("sensores"), "NOUN", "nsubj")
        k = Token("K", texto.index("K"), "PROPN", "appos", sensores)
        l = Token("L", texto.index(" L ") + 1, "NOUN", "conj", k)
        detectar = Token("detectarem", texto.index("detectarem"), "VERB")
        return [responder, sensores, k, l, detectar]

    resultado = sonda.medir_caso(
        sujeito, ouro[sujeito["id"]], analisar_sujeito,
    )
    assert resultado["vinculos_objeto_candidatos"] == []
    assert "afericao" not in resultado
    assert "particao_objeto_em_sombra" not in resultado

    oracoes = por_id["PORTA_VENTO_BATERIA"]

    def analisar_oracoes(texto):
        abrir = Token("abrir", texto.index("abrir"), "VERB")
        vento = Token("vento", texto.index("vento"), "NOUN", "obj", abrir)
        soprar = Token("soprar", texto.index("soprar"), "ADJ", "acl", vento)
        acabar = Token("acabar", texto.index("acabar"), "VERB")
        return [abrir, vento, soprar, acabar]

    resultado = sonda.medir_caso(
        oracoes, ouro[oracoes["id"]], analisar_oracoes,
    )
    assert resultado["vinculos_objeto_candidatos"] == []
    assert "afericao" not in resultado
    assert resultado["autoriza_efeito"] is False


def test_offset_incorreto_no_arco_nao_produz_particao_em_sombra():
    casos, ouro = carregar_painel(17)
    caso = next(item for item in casos if item["id"] == "DRONE_FOTO_VIDEO")

    def analisar(texto):
        registrar = Token("registrar", texto.index("registrar"), "VERB")
        foto = Token("foto", texto.index("foto"), "NOUN", "obj", registrar)
        video = Token("vídeo", texto.index("vídeo") + 1,
                      "NOUN", "conj", foto)
        salvar = Token("salvar", texto.index("salvar"), "VERB")
        return [registrar, foto, video, salvar]

    resultado = sonda.medir_caso(caso, ouro[caso["id"]], analisar)
    assert resultado["vinculos_objeto_candidatos"] == []
    assert "particao_objeto_em_sombra" not in resultado
    assert resultado["reconstrucao"]["estado"] \
        == "fronteira_interna_sem_predicado_ambigua"
    assert resultado["auditoria_particao_objeto_em_sombra"]["estado"] \
        == "vinculo_interno_ausente_ou_extra"
    assert "afericao" not in resultado


def test_arco_incompleto_sem_ancora_nao_interrompe_a_sonda():
    casos, ouro = carregar_painel(17)
    caso = next(item for item in casos if item["id"] == "DRONE_FOTO_VIDEO")

    def analisar(texto):
        registrar = Token("registrar", texto.index("registrar"), "VERB")
        foto = Token("foto", texto.index("foto"), "NOUN", "obj")
        video = Token("vídeo", texto.index("vídeo"), "NOUN", "conj", foto)
        salvar = Token("salvar", texto.index("salvar"), "VERB")
        return [registrar, foto, video, salvar]

    resultado = sonda.medir_caso(caso, ouro[caso["id"]], analisar)
    assert resultado["vinculos_objeto_candidatos"] == []
    assert "particao_objeto_em_sombra" not in resultado
    assert resultado["reconstrucao"]["estado"] \
        == "fronteira_interna_sem_predicado_ambigua"


def test_artigo_em_verbo_rotulado_advcl_tambem_exige_abstencao():
    casos, ouro = carregar_painel(19)
    caso = next(item for item in casos
                if item["id"] == "CAMERA_PORTA_VENTO_CHUVA")

    def analisar(texto):
        camera = Token("câmera", texto.index("câmera"), "VERB", "advcl")
        camera.children = (Token("a", texto.index("a câmera"),
                                 "DET", "det", camera),)
        registrar = Token("registrar", texto.index("registrar"),
                          "VERB", "xcomp", camera)
        porta = Token("porta", texto.index("porta"), "NOUN", "obj", registrar)
        vento = Token("vento", texto.index("vento"), "NOUN", "conj", porta)
        vento.children = (Token("o", texto.index("o vento"),
                                "DET", "det", vento),)
        chuva = Token("chuva", texto.index("chuva"), "NOUN", "conj", porta)
        pararem = Token("pararem", texto.index("pararem"), "VERB", "ROOT",
                        morph={"Number": ["Plur"]})
        return [camera, *camera.children, registrar, porta, vento,
                *vento.children, chuva, pararem]

    resultado = sonda.medir_caso(caso, ouro[caso["id"]], analisar)
    assert resultado["escolha"] == "abstencao_predicado_pos_ambiguo"
    assert resultado["proposta"]["segmentos"][0]["ancora"] == "registrar"
    assert "particao_objeto_em_sombra" not in resultado
    assert "afericao" not in resultado


def test_sujeito_composto_plural_veta_previa_mesmo_com_arco_objeto_falso():
    casos, ouro = carregar_painel(19)
    caso = next(item for item in casos
                if item["id"] == "APP_FOTO_CAMERA_DRONE")

    def analisar(texto):
        registrar = Token("registrar", texto.index("registrar"), "VERB")
        foto = Token("foto", texto.index("foto"), "NOUN", "obj", registrar)
        camera = Token("câmera", texto.index("câmera"),
                       "NOUN", "conj", foto)
        camera.children = (Token("a", texto.index("a câmera"),
                                 "DET", "det", camera),)
        drone = Token("drone", texto.index("drone"), "NOUN", "conj", camera)
        pararem = Token("pararem", texto.index("pararem"), "VERB", "ROOT",
                        morph={"Number": ["Plur"]})
        return [registrar, foto, camera, *camera.children, drone, pararem]

    resultado = sonda.medir_caso(caso, ouro[caso["id"]], analisar)
    assert len(resultado["vinculos_objeto_candidatos"]) == 1
    assert "particao_objeto_em_sombra" not in resultado
    assert resultado["auditoria_particao_objeto_em_sombra"] == {
        "estado": "veto_superficie_sujeito_composto",
        "ids_internos": ["c1"],
        "id_vetado": "c1",
        "estado_superficie": "sujeito_composto_possivel",
        "aprovado_para_producao": False,
        "autoriza_efeito": False,
    }
    assert resultado["reconstrucao"]["estado"] \
        == "fronteira_interna_sem_predicado_ambigua"
    assert "afericao" not in resultado


def test_arco_e_morfologia_iguais_nao_distinguem_sujeito_de_objeto():
    casos, ouro = carregar_painel(21)
    por_id = {caso["id"]: caso for caso in casos}
    cenarios = (
        ("APP_DADO_API_BANCO_PRESENTE",
         "registra", "dado", "API", "banco"),
        ("APP_LOG_RELATORIO_SERVIDORES_PRESENTE",
         "envia", "log", "relatório", "servidores"),
    )
    for caso_id, verbo, objeto, meio, final in cenarios:
        caso = por_id[caso_id]

        def analisar(texto):
            acao = Token(verbo, texto.index(verbo), "VERB")
            alvo = Token(objeto, texto.index(objeto), "NOUN", "obj", acao)
            coordenado = Token(meio, texto.index(meio), "NOUN", "conj", alvo)
            outro = Token(final, texto.index(final), "NOUN", "conj",
                          coordenado)
            predicado = Token("falham", texto.index("falham"), "VERB",
                              morph={"Number": ["Plur"]})
            return [acao, alvo, coordenado, outro, predicado]

        resultado = sonda.medir_caso(caso, ouro[caso_id], analisar)
        assert len(resultado["vinculos_objeto_candidatos"]) == 1
        assert resultado["auditoria_particao_objeto_em_sombra"]["estado"] \
            == "veto_morfologia_predicado_plural"
        assert "particao_objeto_em_sombra" not in resultado
        assert resultado["reconstrucao"]["estado"] \
            == "fronteira_interna_sem_predicado_ambigua"
        assert resultado["autoriza_efeito"] is False


def test_texto_veta_sujeito_composto_mesmo_sem_morfologia_do_parser():
    casos, _ = carregar_painel(19)
    base = next(item for item in casos
                if item["id"] == "APP_FOTO_CAMERA_DRONE")
    for verbo in ("pararem", "pararam", "paravam", "parassem"):
        caso = {**base, "fonte": base["fonte"].replace("pararem", verbo)}

        def analisar(texto):
            registrar = Token("registrar", texto.index("registrar"), "VERB")
            foto = Token("foto", texto.index("foto"), "NOUN", "obj", registrar)
            camera = Token("câmera", texto.index("câmera"),
                           "NOUN", "conj", foto)
            drone = Token("drone", texto.index("drone"), "NOUN", "conj", camera)
            predicado = Token(verbo, texto.index(verbo), "VERB")
            return [registrar, foto, camera, drone, predicado]

        resultado = sonda.medir_caso(caso, {}, analisar)
        assert len(resultado["vinculos_objeto_candidatos"]) == 1
        assert "particao_objeto_em_sombra" not in resultado
        assert resultado["reconstrucao"]["estado"] \
            == "fronteira_interna_sem_predicado_ambigua"


def test_objeto_com_artigo_e_condicao_seguinte_singular_preserva_previa():
    fonte = ("Se o robô localizar a peça e a etiqueta e a esteira parar, "
             "o painel avisa.")
    caso = {"id": "OBJETO_COM_ARTIGO", "fonte": fonte}

    def analisar(texto):
        localizar = Token("localizar", texto.index("localizar"), "VERB")
        peca = Token("peça", texto.index("peça"), "NOUN", "obj", localizar)
        etiqueta = Token("etiqueta", texto.index("etiqueta"),
                         "NOUN", "conj", peca)
        etiqueta.children = (Token("a", texto.index("a etiqueta"),
                                   "DET", "det", etiqueta),)
        parar = Token("parar", texto.index("parar"), "VERB", "ROOT",
                      morph={"Number": ["Sing"]})
        return [localizar, peca, etiqueta, *etiqueta.children, parar]

    resultado = sonda.medir_caso(caso, {}, analisar)
    assert resultado["particao_objeto_em_sombra"]["trechos_condicoes"] == [
        "o robô localizar a peça e a etiqueta", "a esteira parar",
    ]
    assert resultado["autoriza_efeito"] is False


def test_verbo_ligado_a_objeto_mas_com_sujeito_proprio_nao_eh_descartado():
    casos, ouro = carregar_painel(20)
    caso = next(item for item in casos
                if item["id"] == "SENSOR_FOTO_VIDEO_SERVIDORES")

    def analisar(texto):
        salvar = Token("salvar", texto.index("salvar"), "VERB")
        foto = Token("foto", texto.index("foto"), "NOUN", "obj", salvar)
        video = Token("vídeo", texto.index("vídeo"), "NOUN", "conj", foto)
        reiniciarem = Token("reiniciarem", texto.index("reiniciarem"),
                           "VERB", "conj", foto,
                           morph={"Number": ["Plur"]})
        servidores = Token("servidores", texto.index("servidores"),
                           "NOUN", "nsubj", reiniciarem)
        reiniciarem.children = (servidores,)
        return [salvar, foto, video, servidores, reiniciarem]

    resultado = sonda.medir_caso(caso, ouro[caso["id"]], analisar)
    assert [item["ancora"] for item in resultado["proposta"]["segmentos"]] \
        == ["salvar", "", "reiniciarem"]
    assert "escolha" not in resultado
    assert resultado["particao_objeto_em_sombra"]["trechos_condicoes"] == [
        "o sensor salvar foto e vídeo", "os servidores reiniciarem",
    ]
    assert resultado["reconstrucao"]["estado"] \
        == "fronteira_interna_sem_predicado_ambigua"
    assert "afericao" not in resultado


def test_sujeito_composto_usa_verbo_no_fragmento_correto():
    caso = POR_ID["MODULOS_SUJEITO_E"]
    resultado = sonda.medir_caso(
        caso, OURO[caso["id"]], _nlp_de_tokens(
            ("Norte", "PROPN"), ("Sul", "PROPN"), ("enviarem", "VERB"),
        ),
    )
    assert resultado["proposta"]["segmentos"] == [
        {"id": "c0", "tem_predicado": False, "ancora": ""},
        {"id": "c1", "tem_predicado": True, "ancora": "enviarem"},
    ]
    assert resultado["afericao"]["estado"] \
        == "trechos_e_relacao_alinhados_revisao_pendente"
    assert resultado["aprovado_para_producao"] is False
    assert resultado["autoriza_efeito"] is False


def test_auxiliar_eh_predicado_mas_adjetivo_nao():
    caso = POR_ID["FREIOS_NECESSARIOS"]
    resultado = sonda.medir_caso(
        caso, OURO[caso["id"]], _nlp_de_tokens(
            ("dianteiro", "ADJ"), ("traseiro", "ADJ"),
            ("estiverem", "AUX"), ("liberados", "ADJ"),
        ),
    )
    assert resultado["proposta"]["segmentos"][1]["ancora"] == "estiverem"
    assert resultado["afericao"]["estado"] \
        == "trechos_e_relacao_alinhados_revisao_pendente"


def test_regra_mista_recusa_antes_do_analisador():
    caso = POR_ID["PROTOCOLO_MISTO_V7"]

    def proibido(_fonte):
        raise AssertionError("modelo POS nao deve rodar para arvore mista")

    resultado = sonda.medir_caso(caso, OURO[caso["id"]], proibido)
    assert resultado["escolha"] == "recusa_estrutura_plana"


def test_elipse_sem_verbo_explicito_se_abstem():
    casos, ouro = carregar_painel(8)
    caso = next(item for item in casos if item["id"] == "LED_ELIPSE")
    resultado = sonda.medir_caso(
        caso, ouro[caso["id"]], _nlp_de_tokens(
            ("estiver", "AUX"), ("verde", "ADJ"),
        ),
    )
    assert resultado["reconstrucao"]["estado"] == "sem_predicado_suficiente"
    assert "afericao" not in resultado
    assert resultado["autoriza_efeito"] is False


def test_painel_v8_congelado_separa_mistura_real_de_mistura_superficial():
    casos, ouro = carregar_painel(8)
    assert len(casos) == len(ouro) == 14
    assert set(caso["id"] for caso in casos) == set(ouro)
    assert sum(item["representavel"] is True for item in ouro.values()) == 13
    por_id = {caso["id"]: caso for caso in casos}

    def proibido(_fonte):
        raise AssertionError("gate misto deve bloquear antes do POS")

    for caso_id in ("MISTO_ARVORE_V8", "MISTO_SUJEITO_OU"):
        assert sonda.medir_caso(
            por_id[caso_id], ouro[caso_id], proibido,
        )["escolha"] == "recusa_estrutura_plana"
