"""Preparação e validação sem efeitos colaterais da análise visual de jogo."""

from __future__ import annotations

import re
from typing import Any, Mapping

from .sessao_jogo import identificar_jogo

def _normalizar_chave(texto: str) -> str:
    import unicodedata

    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", base).strip()


def resposta_contradiz_identidade_sistema(
    resposta: str,
    identidade: Mapping[str, Any] | None,
) -> bool:
    """Detecta quando a visão troca um jogo confirmado por semelhança visual."""
    jogo = _normalizar_chave(dict(identidade or {}).get("nome_candidato") or "")
    if not jogo or not bool(dict(identidade or {}).get("confirmado")):
        return False
    texto = _normalizar_chave(resposta)
    jogo_re = re.escape(jogo)
    return bool(
        re.search(rf"\bnao\s+(?:e\s+)?(?:o\s+)?{jogo_re}\b", texto)
        or re.search(
            rf"\b{jogo_re}\b.{{0,45}}\b(?:ainda\s+)?nao\s+(?:foi\s+)?(?:lancado|existe|esta disponivel)\b",
            texto,
        )
    )


def resposta_inventa_falha_da_laylay(resposta: str) -> bool:
    """Bloqueia diagnóstico visual de que a própria assistente caiu."""
    texto = _normalizar_chave(resposta)
    sujeito = bool(re.search(r"\b(?:laylay|laylay\.py|assistente|automacao|script)\b", texto))
    falha = bool(re.search(
        r"\b(?:caiu|parou|encerrou|foi encerrad[ao]|crashou|travou|deixou de funcionar)\b",
        texto,
    ))
    return sujeito and falha


def resposta_contradiz_estado_tela(
    resposta: str,
    estado_tela: Mapping[str, Any] | None,
) -> bool:
    """Bloqueia gameplay inventado quando menu/carregamento estão confirmados."""
    estado = str(dict(estado_tela or {}).get("estado") or "").strip().casefold()
    if estado not in {"menu", "carregando"}:
        return False
    texto = _normalizar_chave(resposta)
    sinais_gameplay = (
        "caverna", "floresta", "explorando", "exploracao", "combate",
        "inimigo", "chefao", "minerio", "construcao", "sua casa",
        "seu personagem esta", "voce esta andando", "voce esta numa",
        "voce esta em uma",
    )
    return any(sinal in texto for sinal in sinais_gameplay)



def _montar_prompt(
    pergunta: str,
    contexto: Mapping[str, Any],
    tipo: str,
    *,
    identidade: Mapping[str, Any] | None = None,
    perfil: Mapping[str, Any] | None = None,
    memoria_jogo: str = "",
    complemento: str = "",
    estado_tela: Mapping[str, Any] | None = None,
) -> str:
    jogo = dict(identidade or identificar_jogo(contexto))
    perfil = dict(perfil or {})
    cursor_dentro = bool(contexto.get("cursor_dentro_janela"))
    evidencia_identidade = ""
    if bool(jogo.get("confirmado")):
        evidencia_identidade = (
            "IDENTIDADE DO JOGO CONFIRMADA PELO SISTEMA OPERACIONAL — trate isto como fato, "
            "não como hipótese visual. Não renomeie nem contradiga o jogo com base no estilo gráfico, "
            "em semelhança com outro título ou em conhecimento sobre datas de lançamento. Use a imagem "
            "somente para analisar o conteúdo dentro do jogo confirmado.\n"
            f"Jogo em execução: {jogo.get('nome_candidato')}. "
            f"Executável: {jogo.get('processo') or 'não informado'}. "
            f"Título da janela: {jogo.get('titulo') or 'não informado'}. "
            f"PID: {jogo.get('pid') or 'não informado'}. "
            f"Janela ainda em foco: {'sim' if jogo.get('hwnd_em_foco') else 'não confirmado'}.\n"
        )
    base = evidencia_identidade + (
        "Você é a Laylay acompanhando o usuário enquanto ele joga. Analise somente o que "
        "está visível na imagem; não invente nomes, itens, perigos ou ações. Se a imagem "
        "não der evidência suficiente, diga claramente a dúvida. Responda em português "
        "brasileiro natural, em no máximo três frases, com personalidade leve e útil. "
        "Não diga que pesquisou e não prometa executar algo.\n"
        "Texto de terminal ou navegador visível não prova que a Laylay, o script ou a automação "
        "caiu. Nunca diagnostique o estado da própria assistente pela imagem; ela possui estado "
        "interno separado para isso.\n"
        f"Jogo candidato: {jogo.get('nome_candidato')}. Processo: {jogo.get('processo') or 'não informado'}. "
        f"Confiança da identificação: {float(jogo.get('confianca') or 0.0):.2f}. "
        f"Tipo de ajuda: {tipo or 'observação'}.\n"
    )
    estado_confirmado = dict(estado_tela or {})
    estado = str(estado_confirmado.get("estado") or "").strip().casefold()
    if estado in {"menu", "carregando"}:
        origem = str(estado_confirmado.get("origem") or "contexto recente")
        base += (
            f"ESTADO ATUAL DA TELA CONFIRMADO: {estado} (origem: {origem}). "
            "Não descreva caverna, exploração, combate, construção ou outra cena de gameplay. "
            "Se o quadro parecer contradizer esse estado, reconheça a incerteza em vez de inventar.\n"
        )
    if complemento:
        base += (
            "A imagem anexada é deliberadamente a mesma da dúvida anterior, pois o usuário está "
            "apenas completando o contexto daquela análise.\n"
        )
    else:
        base += (
            "A imagem anexada foi capturada novamente para esta pergunta. Trate somente este "
            "quadro como evidência da cena atual; descrições de cenas anteriores nunca provam "
            "o que está visível agora.\n"
        )
    if tipo == "avaliacao_item":
        perfil_texto = ", ".join(f"{chave}: {valor}" for chave, valor in perfil.items()) or "não informada"
        base += (
            "Esta é uma avaliação de item dentro deste jogo específico. Não transfira regras, raridades "
            "ou atributos de outro jogo. As imagens anexadas podem trazer separadamente o quadro geral, "
            "uma região ampla do tooltip e um recorte próximo em resolução nativa. O círculo vermelho "
            "existe apenas no quadro geral e indica a posição do mouse; os recortes de texto não possuem "
            "marca sobreposta. Leia literalmente nome, atributos, requisitos, bônus, penalidades e o painel "
            "do item equipado, "
            "se estiverem realmente visíveis. Diferencie 'item geralmente forte' de 'bom para a build de "
            "usuário'. Se a build, o item equipado, a versão ou algum atributo necessário não aparecer, "
            "diga exatamente o que falta e não dê um veredito definitivo. Se o jogo candidato não combinar "
            "com a interface ou a confiança for baixa, peça confirmação do jogo.\n"
            "Classe, nível e preferências explicitamente informados pelo usuário prevalecem sobre números "
            "incertos lidos da interface. Não troque o nível conhecido por outro sem confirmação dele.\n"
            f"Perfil conhecido somente desta sessão de jogo: {perfil_texto}. "
            f"Mouse confirmado dentro da janela: {'sim' if cursor_dentro else 'não'}.\n"
            "Depois da resposta natural, escreva em uma única linha o marcador DADOS_ITEM_JSON: "
            "seguido de JSON válido com estas chaves: nome, base, categoria, slot, estado, equipado, "
            "raridade, nivel_item, atributos, termos_pesquisa e confianca. slot é a posição de "
            "equipamento específica deste jogo; estado deve ser equipado, inventario, chão, loja "
            "ou desconhecido. termos_pesquisa deve incluir até três nomes "
            "curtos em inglês quando a tradução for segura. Use string vazia, lista vazia ou null "
            "para qualquer campo ilegível; nunca adivinhe. Esse marcador é interno e não será falado.\n"
        )
    elif tipo in {"avaliacao_habilidade", "avaliacao_entidade"}:
        perfil_texto = ", ".join(f"{chave}: {valor}" for chave, valor in perfil.items()) or "não informado"
        base += (
            "Primeiro identifique se o elemento apontado é uma habilidade ativa, gema, passiva, "
            "nó de árvore ou item. Se for habilidade/passiva, avalie o efeito real, a sinergia "
            "com a build, a utilidade contra grupos e chefes e o custo de oportunidade para chegar "
            "até ela. Não fale de raridade, slot ou equipamento quando estiver vendo uma habilidade. "
            "Não recomende só porque o efeito é positivo: diga quando ele é situacional e o que o usuário "
            "deixa de priorizar. "
            f"Perfil conhecido: {perfil_texto}.\n"
            "Quando for habilidade, depois da resposta natural escreva uma linha DADOS_HABILIDADE_JSON: "
            "com JSON válido contendo nome, tipo, efeito, custo_pontos, beneficios, limitacoes, "
            "sinergias, situacoes_fortes, situacoes_fracas, termos_pesquisa e confianca. "
            "Use vazio ou null no que não estiver legível e nunca adivinhe. Se for claramente um item, "
            "use DADOS_ITEM_JSON com o contrato de item já conhecido, mas nunca emita os dois marcadores.\n"
        )
    elif tipo == "analise_build":
        perfil_texto = ", ".join(f"{chave}: {valor}" for chave, valor in perfil.items()) or "não informado"
        base += (
            "Analise a estrutura realmente visível: árvore de passivas, habilidades, equipamento ou "
            "atributos. Aponte no máximo duas decisões úteis e concretas. Não deduza que uma arma ou "
            "armadura é incompatível apenas pelo arquétipo da classe; exija atributos ou mecânicas "
            "visíveis. Não invente itens da barra rápida. Se houver um nó selecionado e legível, finalize "
            "também com DADOS_HABILIDADE_JSON usando nome, tipo, efeito, custo_pontos, beneficios, "
            "limitacoes, sinergias, situacoes_fortes, situacoes_fracas, termos_pesquisa e confianca. "
            f"Perfil conhecido: {perfil_texto}.\n"
        )
    elif tipo == "inspecao_personagem":
        perfil_texto = ", ".join(f"{chave}: {valor}" for chave, valor in perfil.items()) or "não informado"
        base += (
            "Esta é uma leitura da ficha do personagem. Transcreva com precisão somente os valores "
            "visíveis, compare números corretamente e diga qual atributo é o maior quando isso estiver "
            "legível. Atributos base isolados não provam que a build é de magia, ataque, evasão ou outro "
            "arquétipo; só descreva o estilo da build se ele estiver confirmado no perfil ou claramente "
            "evidenciado por habilidades e equipamentos visíveis. Não transforme uma comparação parcial "
            "em conclusão sobre a build. "
            f"Perfil já confirmado: {perfil_texto}.\n"
        )
    elif tipo in {"identificacao", "pergunta_visual", "observacao", "reanalise"}:
        base += (
            "Ao identificar um objeto, separe descrição visual de nome confirmado. Um nome exato, "
            "namespace, mod, música ou mecânica só pode ser afirmado quando estiver legível na "
            "interface, tooltip ou texto da imagem. Em jogos com Forge, Fabric ou mods, sem esse "
            "texto diga que é uma hipótese visual e não atribua mecânicas de um item parecido. "
            "Nunca diga que não pode acessar uma nova imagem: este fluxo acabou de realizar uma "
            "captura nova para a pergunta atual.\n"
        )
    elif tipo in {"inspecao_inventario", "observacao_inventario_proativa"}:
        perfil_texto = ", ".join(f"{chave}: {valor}" for chave, valor in perfil.items()) or "não informado"
        base += (
            "A tela deve ser tratada como uma inspeção estrutural do inventário deste jogo. Descubra "
            "os slots a partir da interface visível, sem impor slots de outro RPG. Diferencie a área "
            "de equipamentos da mochila e registre somente itens que estejam claramente equipados. "
            "Um slot pode aceitar mais de um item, como anéis ou conjuntos de armas. Se a tela não "
            "for um inventário ou algum slot estiver ambíguo, registre isso sem adivinhar. "
            f"Perfil conhecido: {perfil_texto}.\n"
            "Depois da resposta natural, escreva em uma única linha DADOS_INVENTARIO_JSON: seguido "
            "de JSON válido compacto com: tela_inventario_ativa, personagem, slots, equipados, "
            "confianca e ambiguidades. slots é uma lista de objetos com slot, nome, categoria, "
            "quantidade e confianca. equipados é uma lista com slot, nome, categoria, raridade, "
            "atributos e confianca. Não inclua um item se não houver evidência de que está equipado.\n"
        )
        if tipo == "observacao_inventario_proativa":
            base += (
                "Esta observação é silenciosa e proativa. Só recomende algo se houver uma oportunidade "
                "concreta e importante sustentada pela imagem e pela memória anterior. Acrescente uma "
                "linha SUGESTAO_PROATIVA_JSON: com JSON válido contendo relevante, fala, motivo, slot, "
                "item, prioridade e confianca. Se não houver algo realmente útil, use relevante=false "
                "e fala vazia. Nunca sugira durante combate, diálogo ou cena sem inventário aberto.\n"
            )
    elif tipo == "observacao_presenca_proativa":
        perfil_texto = ", ".join(f"{chave}: {valor}" for chave, valor in perfil.items()) or "não informado"
        base += (
            "Esta é uma observação de presença, não uma solicitação de descrição. Não fale em quadros "
            "comuns ou repetidos, mas procure ativamente um momento genuíno para acompanhar o usuário: "
            "comemorar uma vitória claramente "
            "visível; motivar numa janela de descanso após uma dificuldade realmente evidenciada; dar "
            "uma dica específica e não óbvia sustentada por pelo menos dois elementos visíveis; ou "
            "identificar um clima musical numa exploração/menu calmo. Também pode fazer um comentário "
            "curto de companhia ao entrar numa área nova, encontrar algo visualmente marcante ou parar "
            "num local seguro, desde que cite algo realmente visível e não invente progresso. Você também "
            "pode usar curiosidade para reagir a uma área, criatura, item, construção ou mecânica claramente "
            "visível que pareça nova ou interessante. Nesse caso faça no máximo uma pergunta curta, natural "
            "e opcional; não cobre resposta e não diga que está esperando. Um único "
            "quadro comum não prova "
            "que o usuário morreu várias vezes, está com dificuldade ou precisa de ajuda. Nunca interrompa "
            "combate ativo, diálogo ou cutscene. Dicas como 'desvie', 'use poção' e 'melhore equipamento' "
            "são óbvias e devem ser rejeitadas. Não mande tocar música. Nunca comece com 'Parece que você'. "
            "Não narre que o usuário está parado, em pausa, num lugar calmo ou que é uma boa hora para "
            "respirar: isso é observação genérica, não presença humana. Se você não consegue mencionar um "
            "detalhe específico que justifique a fala, permaneça em silêncio. "
            "Ao reagir a uma música ou playlist visível, preserve nomes exatamente como aparecem na "
            "tela: nunca corrija um nome incomum para um artista mais famoso. Só cite artista ou faixa "
            "quando o texto completo estiver claramente legível e repita esse texto literalmente em "
            "evidencias no formato 'texto exato visível: NOME'; se houver qualquer dúvida, diga apenas "
            "'essa música' ou 'essa playlist'. "
            f"Perfil conhecido: {perfil_texto}.\n"
            "Finalize obrigatoriamente com uma linha PRESENCA_JOGO_JSON: seguida de JSON válido com "
            "relevante, categoria, fala, motivo, evidencias, confianca, momento_seguro e clima_musical. "
            "categoria deve ser motivacao, celebracao, dica, musica, companhia, curiosidade ou nenhuma. "
            "evidencias é uma lista "
            "de fatos visíveis. Para dica, exija no mínimo duas evidências; caso contrário use "
            "relevante=false, categoria=nenhuma e fala vazia.\n"
        )
    if memoria_jogo:
        base += str(memoria_jogo).strip() + "\n"
    if complemento:
        base += (
            "O usuário respondeu ao pedido de contexto da análise anterior. Use esta informação para "
            f"concluir a mesma dúvida, sem pedir que ele repita o item: {complemento}\n"
        )
    return base + f"Pergunta original do usuário: {pergunta}"


def higienizar_alegacoes_visao(
    resposta: str,
    *,
    tipo: str,
    contexto: Mapping[str, Any] | None = None,
    identidade: Mapping[str, Any] | None = None,
) -> str:
    """Impede que o modelo contradiga a captura ou confirme mods sem evidência."""
    texto = re.sub(r"\s+", " ", str(resposta or "")).strip()
    if not texto:
        return ""
    if re.search(
        r"(?:nao|não)\s+(?:tenho como|consigo|posso)\s+"
        r"(?:olhar|ver|acessar).{0,45}(?:de novo|nova(?:s)? image(?:m|ns)|arquivo novo)|"
        r"(?:nao|não)\s+ha\s+(?:um\s+)?arquivo novo",
        texto,
        flags=re.IGNORECASE,
    ):
        return (
            "Eu capturei a tela novamente, mas o quadro atual não deu evidência suficiente "
            "para confirmar o objeto. Se o nome aparecer no tooltip, eu consigo fechar a identificação."
        )

    dados = " ".join(
        str(valor or "")
        for valor in (
            (contexto or {}).get("titulo"),
            (contexto or {}).get("processo"),
            (identidade or {}).get("nome_candidato"),
        )
    ).casefold()
    jogo_modificado = any(
        marcador in dados for marcador in ("forge", "fabric", "neoforge", " mod")
    )
    identificacao = str(tipo or "") in {
        "identificacao", "pergunta_visual", "observacao", "reanalise",
    }
    assume_certeza = bool(re.search(
        r"\b(?:o item|o bloco|aquele|aquilo|isso|esse objeto)\b.{0,45}\b(?:e|é)\b",
        texto,
        flags=re.IGNORECASE,
    ))
    admite_incerteza = bool(re.search(
        r"\b(?:parece|provavelmente|hipotese|hipótese|talvez|nao consigo confirmar|"
        r"não consigo confirmar|sem certeza|pode ser)\b",
        texto,
        flags=re.IGNORECASE,
    ))
    if jogo_modificado and identificacao and assume_certeza and not admite_incerteza:
        texto += (
            " Como o jogo está modificado, trato o nome e a mecânica como hipótese "
            "até o tooltip ficar legível."
        )
    return texto


def resposta_pede_complemento(resposta: str) -> bool:
    """Detecta quando a própria análise deixou uma informação em aberto."""
    texto = str(resposta or "").casefold()
    return bool(re.search(
        r"\b(?:sem saber|preciso saber|precisaria saber|se (?:voce|você) puder|"
        r"me (?:fala|diz|conte)|compartilh(?:ar|e)|qual (?:e|é) (?:a sua|o seu)|"
        r"falta (?:saber|ver|informar)|depende (?:da|do) sua|"
        r"n[aã]o consigo (?:ver|ler|confirmar|avaliar)|"
        r"n[aã]o d[aá] para (?:ver|ler|confirmar|avaliar))\b",
        texto,
    ))


def aplicar_perfil_confirmado_na_resposta(
    resposta: str, perfil: Mapping[str, Any] | None,
) -> str:
    """Impede que a leitura visual contradiga o nível confirmado da pessoa."""
    texto = str(resposta or "").strip()
    nivel_bruto = dict(perfil or {}).get("nivel")
    if nivel_bruto is None:
        return texto
    try:
        nivel = int(nivel_bruto)
    except (TypeError, ValueError):
        return texto
    texto = re.sub(
        r"(?i)(\b(?:voce|você|seu personagem|seu monge)\s+(?:esta|está|esta apenas|está apenas|"
        r"se encontra)\s+(?:no\s+)?n[ií]vel)\s*\d{1,4}\b",
        lambda achado: f"{achado.group(1)} {nivel}",
        texto,
    )
    # Modelos visuais também escrevem o nível como parte da build, sem verbo:
    # "para sua build de Monge nível 12". Isso descreve Pedro, não o requisito
    # do item, portanto deve obedecer ao perfil confirmado da sessão.
    texto = re.sub(
        r"(?i)(\b(?:sua|a sua)\s+build\s+(?:de\s+)?[\wÀ-ÿ -]{1,40}?\s+n[ií]vel)\s*\d{1,4}\b",
        lambda achado: f"{achado.group(1)} {nivel}",
        texto,
    )
    texto = re.sub(
        r"(?i)(\b(?:voce|você|seu personagem|seu monge)\s+(?:esta|está|esta apenas|está apenas)\s+"
        r"(?:no\s+)?n[ií]vel)(?=\s*[,.;!?])",
        lambda achado: f"{achado.group(1)} {nivel}",
        texto,
    )
    frases = re.split(r"(?<=[.!?])\s+", texto)
    corrigidas = []
    for frase in frases:
        requisito = re.search(
            r"(?i)\b(?:exige(?:m)?|requer(?:em)?|pede(?:m)?)\s+(?:o\s+)?"
            r"n[ií]vel\s*(\d{1,4})\b",
            frase,
        )
        nega_por_nivel = re.search(
            r"(?i)\b(?:nao|não)\s+(?:pode|da|dá)\s+(?:equip\w*|us\w*)|"
            r"\b(?:precisa|vai precisar)\s+(?:subir|esperar)",
            frase,
        )
        if requisito and nega_por_nivel and int(requisito.group(1)) <= nivel:
            exigido = int(requisito.group(1))
            frase = (
                f"O requisito de nível {exigido} já está atendido pelo seu nível {nivel}; "
                "ainda confirme na tela se existe outro requisito impedindo o uso."
            )
        corrigidas.append(frase)
    return " ".join(corrigidas).strip()


def higienizar_inspecao_personagem(
    resposta: str, perfil: Mapping[str, Any] | None = None,
) -> str:
    """Mantém valores visíveis, mas barra arquétipos deduzidos no chute."""
    texto = re.sub(r"\s+", " ", str(resposta or "")).strip()
    perfil = dict(perfil or {})
    atributos: dict[str, int] = {}
    nomes = {
        "forca": "Força", "destreza": "Destreza",
        "inteligencia": "Inteligência",
    }
    for valor, nome in re.findall(
        r"(?i)\b(\d{1,4})\s+de\s+(for[cç]a|destreza|intelig[eê]ncia)\b",
        texto,
    ):
        atributos[nomes[_normalizar_chave(nome)]] = int(valor)
    for nome, valor in re.findall(
        r"(?i)\b(for[cç]a|destreza|intelig[eê]ncia)\s*(?:[:=]|(?:est[aá]\s+em))?\s*(\d{1,4})\b",
        texto,
    ):
        atributos[nomes[_normalizar_chave(nome)]] = int(valor)

    build_confirmada = bool(str(perfil.get("build") or perfil.get("estilo") or "").strip())
    frases = [item.strip() for item in re.split(r"(?<=[.!?])\s+", texto) if item.strip()]
    if not build_confirmada:
        frases = [
            frase for frase in frases
            if not re.search(
                r"(?i)\b(?:build\s+focad|foco\s+em\s+(?:magia|ataque|evasao|evasão)|"
                r"faz\s+sentido\s+para\s+(?:uma\s+)?build|"
                r"indica\s+(?:uma\s+)?build|parece\s+(?:uma\s+)?build)\b",
                frase,
            )
        ]
    if len(atributos) >= 2:
        maior_valor = max(atributos.values())
        maiores = [nome for nome, valor in atributos.items() if valor == maior_valor]
        resumo = (
            f"O maior valor visível é {maiores[0]}, com {maior_valor}, mas esses números "
            "sozinhos não confirmam o estilo da sua build."
            if len(maiores) == 1 else
            f"Os maiores valores visíveis estão empatados em {maior_valor}; só esses números "
            "não confirmam o estilo da sua build."
        )
        if not any("maior valor visível" in frase.casefold() for frase in frases):
            frases.append(resumo)
    return " ".join(frases[:3]).strip()


_PEDIDO_NOVA_CAPTURA = re.compile(
    r"^\s*(?:(?:lay|laylay)\s*[,;:\-]?\s*)?"
    r"(?:(?:pode|tenta)\s+)?"
    r"(?:olha|olhe|olhar|ve|v[eê]|ver|analisa|analise|analisar|"
    r"confere|confira|conferir|tenta)\b.*\b"
    r"(?:de novo|novamente|outra vez|mais uma vez)\s*[?!.]*$",
    re.IGNORECASE,
)

_COMANDO_FORA_DA_VISAO = re.compile(
    r"^\s*(?:(?:lay|laylay)\s*[,;:\-]?\s*)?"
    r"(?:por\s+favor\s+)?(?:liga|ligue|desliga|desligue|acende|apaga|"
    r"abre|abra|fecha|feche|toca|toque|pausa|pause|retoma|volta|"
    r"aumenta|abaixa|diminui|coloca|coloque|adiciona|adicione)\b.*\b"
    r"(?:luz|l[aâ]mpada|tomada|ventilador|m[uú]sica|playlist|volume|"
    r"programa|aplicativo|app|site|navegador|aba|janela)\b",
    re.IGNORECASE,
)
