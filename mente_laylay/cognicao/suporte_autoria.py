"""Suporte declarado pela autora: proveniência textual, sem prova semântica."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt

from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal, SnapshotComandoIA
from mente_laylay.cognicao.estado_tecnico_llm import categoria_estado_tecnico_llm

_MOTIVOS_SEM_FONTE = ("nao_utilizada", "insuficiente")


@dataclass(frozen=True, slots=True)
class SuporteAutoriaProposto:
    turno_id: str
    texto_usuario: str
    fala_original: str
    declaracao: SnapshotComandoIA
    semantica_verificada: bool = field(default=False, init=False)
    prova_implicacao: bool = field(default=False, init=False)
    autoriza_execucao: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if (type(self.turno_id) is not str or not self.turno_id
            or type(self.texto_usuario) is not str or not self.texto_usuario
            or type(self.fala_original) is not str or type(self.declaracao) is not SnapshotComandoIA):
            raise ValueError("Declaração exige emissão e consulta capturadas pelo host.")


@dataclass(frozen=True, slots=True)
class AutoriaRevisadaProposta:
    """Montagem literal das emissões aceitas pelo host; não prova seu apoio."""
    turno_id: str
    texto_usuario: str
    principal_sha256: str
    fala_original: str
    partes: tuple[SuporteAutoriaProposto, ...]
    semantica_verificada: bool = field(default=False, init=False)
    prova_implicacao: bool = field(default=False, init=False)
    autoriza_execucao: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if (type(self.partes) is not tuple or not 1 <= len(self.partes) <= 8
            or type(self.principal_sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", self.principal_sha256) is None
            or any(type(p) is not SuporteAutoriaProposto or p.turno_id != self.turno_id
                   or p.texto_usuario != self.texto_usuario for p in self.partes)
            or self.fala_original != " ".join(p.fala_original for p in self.partes)
            or not 0 < len(self.fala_original) <= 4000):
            raise ValueError("montagem_autoral_sem_vinculo_literal")
        declaracoes = [p.declaracao.como_dict() for p in self.partes]
        if (any(d.get("estado") != "revisao_semantica_pendente"
                or d.get("cobertura_textual") is not True for d in declaracoes)
            or sum(len(p.get('partes') or [p['texto']])
                   for d in declaracoes for p in d['proposicoes']) > 8):
            raise ValueError("montagem_autoral_sem_cobertura")

    def suporte_composto(self) -> SuporteAutoriaProposto:
        proposicoes, cursor = [], 0
        for parte in self.partes:
            for proposta in parte.declaracao.como_dict()["proposicoes"]:
                inicio, fim = proposta["intervalo"]
                proposicoes.append({**proposta, "intervalo": [cursor + inicio, cursor + fim]})
            cursor += len(parte.fala_original) + 1
        dados = {"estado": "revisao_semantica_pendente", "motivos": [],
                 "cobertura_textual": True, "proposicoes": proposicoes}
        # Uma mescla não herda silenciosamente o critério de uma das partes.
        if len(self.partes) == 1:
            criterio = self.partes[0].declaracao.como_dict().get('criterio_autoral_proposto')
            if criterio is not None:
                dados['criterio_autoral_proposto'] = criterio
            fundamento = self.partes[0].declaracao.como_dict().get('fundamento_criterio_proposto')
            if fundamento is not None:
                dados['fundamento_criterio_proposto'] = fundamento
        return SuporteAutoriaProposto(self.turno_id, self.texto_usuario, self.fala_original, SnapshotComandoIA(dados))


def capturar_autoria_revisada(
    resposta: Any, *, turno_id: str, texto_usuario: str,
) -> SuporteAutoriaProposto | None:
    """Reutiliza a captura de emissão; não registra leitura, intenção ou comandos."""
    if (not turno_id or not texto_usuario or type(resposta) is not str
        or categoria_estado_tecnico_llm(resposta)):
        return None
    return _capturar_suporte_textual(resposta, turno_id, texto_usuario, ())


def montar_autoria_revisada(
    resposta_principal: str, fala: str, partes: tuple[SuporteAutoriaProposto, ...],
) -> AutoriaRevisadaProposta | None:
    if not partes or any(type(p) is not SuporteAutoriaProposto for p in partes):
        return None
    try:
        return AutoriaRevisadaProposta(partes[0].turno_id, partes[0].texto_usuario,
            hashlib.sha256(str(resposta_principal).encode('utf-8')).hexdigest(), fala, partes)
    except ValueError:
        return None


def capturar_suporte_autoria(
    principal: Any, *, fontes_no_contexto: tuple[str, ...] = (),
) -> SuporteAutoriaProposto | None:
    """Ancora até oito trechos no texto original, sem verificar suas relações.

    Campo ausente mantém o contrato anterior. Campo presente malformado conserva
    uma recusa explícita, nunca uma declaração parcial ou implicitamente válida.
    Existir no contexto não comprova que uma fonte sustenta a proposição.
    """
    if type(principal) is not ContratoPropostaPrincipal or not principal.proveniencia_conhecida:
        return None
    return _capturar_suporte_textual(principal.resposta_bruta, principal.turno_id,
                                    principal.texto_usuario, fontes_no_contexto)


def _capturar_suporte_textual(
    bruto: str, turno_id: str, texto_usuario: str, fontes_no_contexto: tuple[str, ...],
) -> SuporteAutoriaProposto | None:

    def objeto_unico(pares):
        dados = {}
        for chave, valor in pares:
            if chave in dados:
                raise ValueError("chave_duplicada")
            dados[chave] = valor
        return dados

    def invalida(motivo: str, fala: str = "") -> SuporteAutoriaProposto:
        return SuporteAutoriaProposto(turno_id, texto_usuario, fala,
            SnapshotComandoIA({"estado": "declaracao_invalida", "motivos": [motivo],
                "proposicoes": [], "cobertura_textual": False}))

    if len(bruto) > 32000:
        return invalida("envelope_excede_limite") if '"suporte_proposicoes"' in bruto else None
    try:
        dados = json.loads(bruto, object_pairs_hook=objeto_unico,
                           parse_constant=lambda _v: (_ for _ in ()).throw(ValueError("numero_invalido")))
    except (TypeError, ValueError, RecursionError):
        return invalida("envelope_nao_conferivel") if re.search(r'"suporte_proposicoes"\s*:', bruto) else None
    if not isinstance(dados, dict) or "suporte_proposicoes" not in dados:
        return None
    try:
        fala, declaracao = conferir_suporte_proposicoes(dados, fontes_no_contexto=fontes_no_contexto)
    except ValueError as erro:
        fala = dados.get("fala")
        return invalida(str(erro), fala.strip() if isinstance(fala, str) else "")
    return SuporteAutoriaProposto(turno_id, texto_usuario, fala,
        SnapshotComandoIA(declaracao))


def conferir_suporte_proposicoes(
    dados: dict[str, Any], *, fontes_no_contexto: tuple[str, ...] = (),
) -> tuple[str, dict[str, Any]]:
    """Confere somente forma/cobertura; compartilhado por emissão e captura."""
    fala = dados.get("fala")
    if not isinstance(fala, str) or not fala.strip() or len(fala) > 4000:
        raise ValueError("fala_original_invalida")
    fala = fala.strip()
    itens = dados.get("suporte_proposicoes")
    if not isinstance(itens, list) or not 1 <= len(itens) <= 8:
        raise ValueError("lista_de_proposicoes_invalida")
    cursor, proposicoes, quantidade_partes = 0, [], 0
    disponiveis = {f for f in fontes_no_contexto if type(f) is str}
    for item in itens:
        if (not isinstance(item, dict) or set(item) - {"ato"} not in (
                {"texto", "fontes"}, {"texto", "fontes", "sem_fonte"},
                {"partes", "fontes"}, {"partes", "fontes", "sem_fonte"})
            or not isinstance(item["fontes"], list) or len(item["fontes"]) > 8
            or any(type(f) is not str or not f.strip() or len(f) > 200 for f in item["fontes"])
            or len(set(item["fontes"])) != len(item["fontes"])):
            raise ValueError("proposicao_malformada")
        partes = item['partes'] if 'partes' in item else [item['texto']]
        if (not isinstance(partes, list) or not 1 <= len(partes) <= 8
            or any(type(p) is not str or not p.strip() or p != p.strip() or len(p) > 500 for p in partes)):
            raise ValueError('partes_autorais_malformadas')
        quantidade_partes += len(partes)
        if quantidade_partes > 8:
            raise ValueError('limite_de_partes_autorais')
        if "ato" in item and (type(item["ato"]) is not str or re.fullmatch(r"ato:[0-9a-f]{24}", item["ato"]) is None):
            raise ValueError("alvo_discursivo_malformado")
        if "sem_fonte" in item and (item["fontes"] or item["sem_fonte"] not in _MOTIVOS_SEM_FONTE):
            raise ValueError("ausencia_de_fonte_invalida")
        # Partes são transporte da mesma proposição. Conferir fonte no texto
        # integral impede dar apoio independente a um fragmento sem ressalva.
        literal = ' '.join(partes)
        inicio = fala.find(literal, cursor)
        if (inicio < 0 or fala.find(literal) != inicio or fala.find(literal, inicio + 1) >= 0
            or fala[cursor:inicio].strip()):
            raise ValueError("ancora_ausente_ambigua_ou_sem_cobertura")
        fim = inicio + len(literal)
        proposicoes.append({"texto": literal, "intervalo": [inicio, fim], "fontes": list(item["fontes"]),
            "fontes_no_contexto": [f for f in item["fontes"] if f in disponiveis],
            "fontes_ausentes": [f for f in item["fontes"] if f not in disponiveis]})
        if 'partes' in item:
            proposicoes[-1]['partes'] = list(partes)
        if "sem_fonte" in item:
            proposicoes[-1]["sem_fonte_declarada"] = item["sem_fonte"]
        if "ato" in item:
            proposicoes[-1]["ato_proposto"] = item["ato"]
        cursor = fim
    if fala[cursor:].strip():
        raise ValueError("cobertura_textual_incompleta")
    declaracao = {"estado": "revisao_semantica_pendente", "motivos": [],
                  "proposicoes": proposicoes, "cobertura_textual": True}
    if 'criterio_autoral' in dados:
        from mente_laylay.cognicao.criterio_autoral import validar_codigo_criterio
        declaracao['criterio_autoral_proposto'] = validar_codigo_criterio(dados['criterio_autoral'])
    if 'fundamento_criterio' in dados:
        fundamento = dados['fundamento_criterio']
        if type(fundamento) is not str or (fundamento != 'sem_fundamento' and re.fullmatch('[0-9a-f]{64}', fundamento) is None):
            raise ValueError('fundamento_criterio_nao_contratado')
        declaracao['fundamento_criterio_proposto'] = fundamento
    return fala, declaracao


def capturar_suporte_autoria_obrigatoria(
    principal: Any, *, fontes_no_contexto: tuple[str, ...] = (),
) -> SuporteAutoriaProposto | None:
    """Ausência na emissão do host não libera confirmação por fonte global.

    Não cria uma proposta ou atribui suporte à recuperação: conserva somente
    o estado negativo da emissão principal, mesmo quando ela falhou.
    """
    suporte = capturar_suporte_autoria(principal, fontes_no_contexto=fontes_no_contexto)
    if suporte is not None:
        return suporte
    if (type(principal) is not ContratoPropostaPrincipal
        or not principal.turno_id or not principal.texto_usuario):
        return None
    return SuporteAutoriaProposto(principal.turno_id, principal.texto_usuario, "",
        SnapshotComandoIA({"estado": "declaracao_ausente", "motivos": [principal.estado],
                          "proposicoes": [], "cobertura_textual": False}))


def _particionar_transporte_literal(fala: str) -> tuple[str, ...]:
    """Divide só em espaços reponíveis, sem inferir fronteiras semânticas."""
    if type(fala) is not str or not 0 < len(fala) <= 4000 or fala != fala.strip():
        return ()
    partes: list[str] = []
    restante = fala
    while len(restante) > 500:
        corte = next((i for i in range(500, 0, -1) if restante[i] == " "
            and not restante[i - 1].isspace() and not restante[i + 1].isspace()), None)
        if corte is None or len(partes) >= 7:
            return ()
        partes.append(restante[:corte])
        restante = restante[corte + 1:]
    partes.append(restante)
    return tuple(partes) if " ".join(partes) == fala else ()


def segmentar_realizacao_autoral(fala: str) -> tuple[str, ...]:
    """Realizações finitas mantêm âncoras independentes e cobertura integral."""
    partes = _particionar_transporte_literal(fala)
    if not partes:
        return ()
    try:
        conferir_suporte_proposicoes({"fala": fala, "suporte_proposicoes": [
            {"texto": parte, "fontes": []} for parte in partes]})
    except ValueError:
        return ()
    return partes


def exigir_suporte_no_pacote_autoral(
    pacote: PacotePrompt, *, referencias_disponiveis: tuple[str, ...] = (),
) -> PacotePrompt:
    """Negocia declaração obrigatória; não valida implicação ou autoridade.

    Usado no envio principal atual e nas rotas autorais de recuperação do host.
    Um codec já existente conserva integralmente suas próprias restrições.
    """
    from dataclasses import replace
    from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt

    if type(pacote) is not PacotePrompt:
        raise TypeError("Autoria exige pacote do preparador canônico.")
    if (type(referencias_disponiveis) is not tuple or len(referencias_disponiveis) > 8
        or any(type(r) is not str or not 0 < len(r) <= 200 or r != r.strip() or not r.isprintable()
               for r in referencias_disponiveis) or len(set(referencias_disponiveis)) != len(referencias_disponiveis)):
        raise ValueError("inventario_de_referencias_invalido")
    base = pacote.contrato_saida
    if base is not None and base.nome in {'autoria_livre_v5', 'autoria_referenciada_v5'}:
        if base.nome == 'autoria_referenciada_v5':
            formas = base.response_format['json_schema']['schema']['properties']['suporte_proposicoes']['items']['anyOf']
            existentes = tuple(formas[0]['properties']['fontes']['items']['enum'])
        else:
            existentes = ()
        if referencias_disponiveis and existentes != referencias_disponiveis:
            raise ValueError('inventario_autoral_divergente')
        return pacote
    if base is not None and base.nome in {"autoria_por_ato_v4", "autoria_por_ato_v5"}:
        ramos = base.response_format["json_schema"]["schema"]["properties"]["suporte_proposicoes"]["items"]["anyOf"]
        existentes = tuple(next(r["properties"]["fontes"]["items"]["enum"]
                                for r in ramos if r["properties"]["fontes"].get("minItems") == 1))
        if referencias_disponiveis and referencias_disponiveis != existentes:
            raise ValueError("inventario_autoral_divergente")
        return pacote
    if base is not None and base.nome == "autoria_referenciada_v3":
        formas = base.response_format["json_schema"]["schema"]["properties"]["suporte_proposicoes"]["items"]["anyOf"]
        existentes = tuple(formas[0]["properties"]["fontes"]["items"]["enum"])
        if referencias_disponiveis and existentes != referencias_disponiveis:
            raise ValueError("inventario_autoral_divergente")
        # Uma recuperação que já recebe o codec não pode enfraquecer o catálogo.
        return pacote
    from mente_laylay.cognicao.contratos_turno import TIPOS_INTERACAO_IA

    objeto = {"type": "object", "additionalProperties": True}
    esquema = (base.response_format["json_schema"]["schema"] if base is not None else {
        "type": "object", "properties": {
            "emocao": {"type": "string"}, "nivel_emocao": {"type": "integer"},
            "tipo_interacao": {"type": "string", "enum": sorted(TIPOS_INTERACAO_IA)},
            "leitura_turno": {"anyOf": [objeto, {"type": "array", "items": {
                "anyOf": [{"type": "string"}, objeto]}}]},
            "leitura_emocional": objeto,
            "comandos": {"type": "array", "items": objeto},
            "aprendizados": {"type": "array", "items": {"anyOf": [{"type": "string"}, objeto]}},
            "intencao_corporal": objeto,
        }, "required": [], "additionalProperties": False,
    })
    esquema["properties"]["suporte_proposicoes"] = {
        "type": "array", "minItems": 1, "maxItems": 8, "items": {
            "type": "object", "additionalProperties": False, "required": ["texto", "fontes"],
            "properties": {"texto": {"type": "string", "minLength": 1, "maxLength": 4000},
                "fontes": {"type": "array", "maxItems": 8 if referencias_disponiveis else 0, "uniqueItems": True,
                    "items": {"type": "string", "minLength": 1, "maxLength": 200}}},
        },
    }
    if referencias_disponiveis:
        unidade = esquema["properties"]["suporte_proposicoes"]["items"]
        referencia = {**unidade, "properties": {**unidade["properties"], "fontes": {
            **unidade["properties"]["fontes"], "minItems": 1,
            "items": {"type": "string", "enum": list(referencias_disponiveis)}}}}
        ausencia = {**unidade, "required": ["texto", "fontes", "sem_fonte"], "properties": {
            **unidade["properties"], "fontes": {"type": "array", "maxItems": 0, "items": {"type": "string"}},
            "sem_fonte": {"type": "string", "enum": list(_MOTIVOS_SEM_FONTE)}}}
        esquema["properties"]["suporte_proposicoes"]["items"] = {"anyOf": [referencia, ausencia]}
    # Uma única representação autoral. A fala é projeção literal das unidades;
    # o modelo não produz uma segunda cópia que poderia divergir do suporte.
    fala_contratada = esquema["properties"].pop("fala", {})
    realizacoes = fala_contratada.get("enum", ())
    sequencias = tuple(segmentar_realizacao_autoral(fala) for fala in realizacoes)
    if realizacoes:
        # Uma escolha literal do owner não pode virar prosa livre só porque
        # passou a ser transportada na representação autoral compartilhada.
        unidades = esquema["properties"]["suporte_proposicoes"]
        if not all(sequencias):
            raise ValueError("realizacao_sem_representacao_autoral_integral")
        unidades["minItems"] = min(map(len, sequencias))
        unidades["maxItems"] = max(map(len, sequencias))
        for forma in unidades["items"].get("anyOf", [unidades["items"]]):
            forma["properties"]["texto"] = (dict(fala_contratada) if unidades["maxItems"] == 1 else {
                "type": "string", "minLength": 1, "maxLength": 500,
                "enum": list(dict.fromkeys(parte for seq in sequencias for parte in seq))})
            if not referencias_disponiveis:
                forma["properties"]["fontes"]["maxItems"] = 0
    esquema["required"] = [k for k in esquema["required"] if k != "fala"]
    esquema["required"].append("suporte_proposicoes")

    def validar(dados: dict[str, Any]) -> None:
        if len(json.dumps(dados, ensure_ascii=False, allow_nan=False)) > 32000:
            raise ValueError("envelope_excede_limite")
        if 'tipo_interacao' in dados and (
            type(dados['tipo_interacao']) is not str or dados['tipo_interacao'] not in TIPOS_INTERACAO_IA
        ):
            raise ValueError('tipo_interacao_fora_do_contrato')
        if "fala" in dados:
            raise ValueError("fala_independente_na_autoria")
        if not set(dados).issubset(esquema["properties"]):
            raise ValueError("campo_autoral_nao_contratado")
        unidades = dados.get("suporte_proposicoes")
        if (not isinstance(unidades, list) or not 1 <= len(unidades) <= 8
            or any(not isinstance(p, dict) or type(p.get("texto")) is not str for p in unidades)):
            raise ValueError("lista_de_proposicoes_invalida")
        fala = " ".join(p["texto"] for p in unidades)
        if realizacoes and (tuple(p["texto"] for p in unidades) not in sequencias or fala not in realizacoes
            or (not referencias_disponiveis and any(p.get("fontes") != [] for p in unidades))):
            raise ValueError("realizacao_fora_do_contrato_base")
        canonicas = []
        for unidade in unidades:
            if 'partes' in unidade:
                raise ValueError('partes_nao_negociadas_na_emissao')
            if len(unidade['texto']) > 500 and not realizacoes:
                partes = _particionar_transporte_literal(unidade['texto'])
                if not partes:
                    raise ValueError('proposicao_sem_transporte_integral')
                canonicas.append({**{k:v for k,v in unidade.items() if k != 'texto'}, 'partes':list(partes)})
            else:
                canonicas.append(unidade)
        projetados = {**dados, 'suporte_proposicoes':canonicas, "fala": fala}
        conferir_suporte_proposicoes(projetados)
        for unidade in unidades:
            if referencias_disponiveis:
                if unidade["fontes"]:
                    if any(f not in referencias_disponiveis for f in unidade["fontes"]):
                        raise ValueError("referencia_fora_do_inventario")
                elif "sem_fonte" not in unidade:
                    raise ValueError("ausencia_de_referencia_nao_declarada")
            else:
                if unidade["fontes"]:
                    raise ValueError("referencia_fora_do_inventario")
                if "sem_fonte" in unidade:
                    raise ValueError("decisao_de_fonte_nao_negociada")
        if base is not None:
            base.validar({k: v for k, v in projetados.items() if k != "suporte_proposicoes"})
        # A projeção só é publicada depois de ambos os contratos passarem.
        dados['suporte_proposicoes'] = canonicas
        dados["fala"] = fala

    nome = (("autoria_referenciada_v3" if referencias_disponiveis else "autoria_com_suporte_v2")
            if realizacoes else ('autoria_referenciada_v5' if referencias_disponiveis else 'autoria_livre_v5'))
    codec = ContratoSaidaEstruturada(nome, "[AUTORIA_COM_SUPORTE]", esquema, validar)
    instrucao = (
        "CONTRATO DE AUTORIA COM SUPORTE: nesta emissão não escreva o campo fala. "
        "Escreva sua resposta em suporte_proposicoes, obrigatório, na forma "
        '[{"texto":"primeira proposição da resposta","fontes":[]}]. '
        "O host junta os textos na ordem para formar a fala, sem alterar palavras. "
        "Uma unidade por proposição completa, até oito proposições e 4000 caracteres na resposta inteira, sem repetição ambígua. "
        "Não corte uma palavra ou ideia para caber em 500 caracteres: o host divide o transporte "
        "em até oito partes de 500, preservando integralmente cada proposição e suas referências. "
        "Use fontes=[] quando não houver ID disponível; não invente fontes. IDs são referências propostas, "
        "não prova de verdade ou implicação. Não declare verificação nem autorização. "
        "Preserve todas as outras restrições do turno e o schema do transporte. Não emita marcadores ou Markdown."
    )
    if realizacoes and max(map(len, sequencias)) > 1:
        instrucao += (
            "\nA realização do owner ocupa várias unidades literais de transporte. "
            "Copie todas na ordem apresentada no enum, sem omitir, repetir, mesclar opções "
            "ou completar palavras. O host exige reconstrução integral da realização. "
            "A divisão não prova fronteiras de proposições, apoio semântico ou autoridade.")
    if referencias_disponiveis:
        instrucao += (
            "\nREFERÊNCIAS DISPONÍVEIS NESTE ENVIO (o ID é a URL exata): "
            + json.dumps(referencias_disponiveis, ensure_ascii=False)
            + '. Para cada unidade baseada nesses trechos, proponha os IDs usados em fontes; '
            'referências vão nesse campo, sem acrescentar URLs ao texto da unidade. '
            'Fontes=[] sozinho não é uma decisão válida aqui. Se não usou fonte, declare '
            'sem_fonte="nao_utilizada"; se os trechos não sustentam a resposta, '
            'sem_fonte="insuficiente", ambos com fontes=[]. Não preencha citações por proximidade '
            'nem cite só porque uma URL existe. A revisão do host confere o apoio depois; '
            'sua indicação ou ausência são propostas, sem prova de verdade ou autorização.'
        )
    mensagens = [dict(m) for m in pacote.mensagens]
    indice = next((i for i in range(len(mensagens) - 1, -1, -1) if mensagens[i].get("role") == "user"), len(mensagens))
    if indice > 0 and mensagens[indice - 1].get("role") == "system":
        mensagens[indice - 1]["content"] = str(mensagens[indice - 1].get("content") or "") + "\n" + instrucao
    else:
        mensagens.insert(indice, {"role": "system", "content": instrucao})
    return replace(pacote, mensagens=tuple(mensagens), contrato_saida=codec,
                   reserva_saida_tokens=max(1024, pacote.reserva_saida_tokens))


def vincular_atos_no_pacote_autoral(pacote: PacotePrompt, *, plano: dict[str, Any]) -> PacotePrompt:
    """Declara alvos da mesma emissão; não confere apoio, pertinência ou efeito."""
    from dataclasses import replace
    from mente_laylay.cognicao.validacao_contrato_fala import inventariar_atos_autoria
    from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada
    base = pacote.contrato_saida
    if (pacote.contexto_fechado or base is None or base.nome not in {"autoria_referenciada_v3", "autoria_referenciada_v5"}
        or not pacote.mensagens or pacote.mensagens[-1].get("role") != "user"):
        return pacote
    consulta = pacote.mensagens[-1].get("content")
    if consulta != plano.get("texto_usuario"):
        # Reescritas do preparador transportam a mesma entrada num payload
        # estruturado. Isso vincula a tarefa, sem tomar o rascunho por fonte.
        try:
            payload = json.loads(consulta)
        except (TypeError, ValueError):
            return pacote
        if type(payload) is not dict or payload.get("mensagem_atual") != plano.get("texto_usuario"):
            return pacote
    inventario = inventariar_atos_autoria(plano)
    if not inventario:
        return pacote
    esquema = base.response_format["json_schema"]["schema"]
    unidades = esquema["properties"]["suporte_proposicoes"]
    formas = unidades["items"]["anyOf"]
    ramos = []
    for ato in inventario:
        for forma in formas:
            ramo = json.loads(json.dumps(forma))
            if ato["realizacoes"]:
                if "sem_fonte" not in ramo["properties"]:
                    continue
                ramo["properties"]["texto"]["enum"] = ato["realizacoes"]
                ramo["properties"]["sem_fonte"]["enum"] = ["nao_utilizada"]
            ramo["required"].append("ato")
            ramo["properties"]["ato"] = {"type": "string", "const": ato["id"]}
            ramos.append(ramo)
    unidades.update(minItems=len(inventario), items={"anyOf": ramos})
    alvos = {a["id"]: a for a in inventario}

    def validar(dados: dict[str, Any]) -> None:
        itens = dados.get("suporte_proposicoes")
        if not isinstance(itens, list) or not len(inventario) <= len(itens) <= 8:
            raise ValueError("atos_autorais_sem_cobertura")
        anteriores = []
        for item in itens:
            if not isinstance(item, dict) or type(item.get("ato")) is not str or item["ato"] not in alvos:
                raise ValueError("alvo_discursivo_nao_oferecido")
            ato = alvos[item["ato"]]
            anteriores.append(ato["ordem"])
            if ato["realizacoes"] and (item.get("texto") not in ato["realizacoes"]
                or item.get("fontes") != [] or item.get("sem_fonte") != "nao_utilizada"):
                raise ValueError("realizacao_discursiva_incompativel")
        if anteriores != sorted(anteriores) or set(anteriores) != set(range(len(inventario))):
            raise ValueError("atos_autorais_sem_cobertura_ordenada")
        projetados = {**dados, "suporte_proposicoes": [{k: v for k, v in i.items() if k != "ato"} for i in itens]}
        base.validar(projetados)
        dados['suporte_proposicoes'] = [
            {**p, 'ato':original['ato']} for p, original in zip(projetados['suporte_proposicoes'], itens)]
        dados["fala"] = projetados["fala"]

    codec = ContratoSaidaEstruturada("autoria_por_ato_v5" if base.nome == 'autoria_referenciada_v5' else 'autoria_por_ato_v4',
                                    "[AUTORIA_POR_ATO]", esquema, validar)
    mensagens = [dict(m) for m in pacote.mensagens]
    # Âncoras, ocorrência e certificados ficam no host. Para escolher o alvo,
    # a autora só precisa do ID, tipo e conteúdo; opções já estão no schema.
    alvos_prompt = [{"id": a["id"], "tipo": a["tipo"], "texto_original": a["texto_original"]} for a in inventario]
    instrucao = (
        "ATOS DESTA EMISSÃO (IDs do host, não prova): " + json.dumps(alvos_prompt, ensure_ascii=False)
        + ". Cada unidade de suporte_proposicoes deve indicar ato com um ID deste inventário. "
        "Cubra todos os atos na ordem. Uma unidade trata de um ato; separe reação social e "
        "afirmação factual. Na saudação escolha uma realização do schema sem acrescentar "
        "prosa. Nas perguntas declare as fontes efetivamente usadas ou a ausência prevista "
        "no schema. Indicar alvo ou fonte não comprova pertinência, apoio, verdade ou execução; "
        "o host fará a conferência independente. Não escreva fala independente." )
    # A preparação preserva o par atual system/user. A negociação estende
    # essa mesma instrução; criar outra deslocaria contrato, fontes e receipts.
    indice = len(mensagens) - 1
    if indice > 0 and mensagens[indice - 1].get("role") == "system":
        mensagens[indice - 1]["content"] = str(mensagens[indice - 1].get("content") or "") + "\n" + instrucao
    else:
        mensagens.insert(indice, {"role": "system", "content": instrucao})
    return replace(pacote, mensagens=tuple(mensagens), contrato_saida=codec)
