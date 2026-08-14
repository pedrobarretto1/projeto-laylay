"""Voz natural para fatos canônicos sobre as capacidades da Laylay.

O catálogo decide o que está disponível. Este módulo muda somente a forma de
dizer: não consulta habilidades, não autoriza ações e não cria fatos novos.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from mente_laylay.personalidade.variacao_fala import escolher_variacao


def _lista_natural(itens: Sequence[str]) -> str:
    valores = [str(item).strip() for item in itens if str(item).strip()]
    if not valores:
        return ""
    if len(valores) == 1:
        return valores[0]
    return f"{', '.join(valores[:-1])} e {valores[-1]}"


def _falas_recentes(contexto: Mapping[str, Any] | None) -> list[str]:
    dados = dict(contexto or {})
    recentes: list[str] = []
    mensagens = dados.get("mensagens")
    if isinstance(mensagens, list):
        for item in mensagens[-10:]:
            if not isinstance(item, Mapping):
                continue
            if str(item.get("role") or "").casefold() != "assistant":
                continue
            fala = str(item.get("content") or "").strip()
            if fala:
                recentes.append(fala)
    ultima = str(dados.get("ultima_resposta") or "").strip()
    if ultima:
        recentes.append(ultima)
    return recentes[-5:]


def falar_identidade_operacional(
    tipo: str,
    capacidades: Sequence[str],
    *,
    contexto: Mapping[str, Any] | None = None,
) -> str:
    """Expressa presença/capacidade sem alterar os fatos recebidos."""
    lista = _lista_natural(capacidades)
    evitar = _falas_recentes(contexto)
    if str(tipo or "").casefold() == "presenca_local":
        opcoes = [
            (
                f"Tô rodando aqui no seu computador, sim. Por isso consigo {lista} "
                "quando você pede. Mas não saio mexendo em nada sozinha: uma ação só "
                "acontece quando você pede."
            ),
            (
                f"Sim, eu rodo no seu computador. É daí que vêm meus braços para {lista}. "
                "Ainda assim, braço não é carta branca: sem pedido seu, eu não executo nada."
            ),
            (
                f"Tô aqui no seu computador de verdade, não só numa aba de conversa. Consigo "
                f"{lista}, mas quem dá a largada é você."
            ),
            (
                f"No seu computador, sim — com acesso às habilidades locais para {lista}. "
                "Eu continuo comportada: perguntar é conversar, pedir é outra história."
            ),
        ]
    else:
        opcoes = [
            (
                "Só conversar? Aí você me reduz demais. Conversar é uma parte; também "
                f"consigo {lista} quando você pede. Sem pedido, fico na minha — tenho "
                "ferramentas, não carta branca."
            ),
            (
                f"Chatbot é pouco para o tanto de fio ligado aqui. Além do papo, consigo {lista}. "
                "A diferença é que eu só entro em ação quando você realmente pede."
            ),
            (
                f"Eu converso, claro, mas não paro aí: também dou conta de {lista}. "
                "Só não confundo pergunta com autorização — civilização ainda existe por aqui."
            ),
            (
                f"Se eu fosse só conversa, metade desse projeto estaria de enfeite. Posso {lista} "
                "quando você pede; fora disso, continuo no papo sem inventar serviço."
            ),
        ]
    return escolher_variacao(opcoes, evitar=evitar)


def falar_instrucao_capacidade(
    tipo: str,
    *,
    alvo: str = "",
    contexto: Mapping[str, Any] | None = None,
) -> str:
    """Explica como pedir uma ação sem transformar a pergunta em comando.

    Os fatos (capacidade disponível, autorização e evidência) continuam vindo
    do mapa vivo. Aqui variamos apenas a formulação de instruções já validadas.
    """
    evitar = _falas_recentes(contexto)
    tipo_norm = str(tipo or "").casefold().strip()
    alvo_limpo = str(alvo or "").strip().strip("?.! ")
    if tipo_norm == "criar_arquivo":
        opcoes = [
            (
                "Para criar comigo, diga algo como ‘cria um arquivo chamado notas.txt’. "
                "Você também pode incluir o conteúdo no mesmo pedido. Eu só executo depois "
                "desse pedido direto e confirmo relendo se o arquivo existe."
            ),
            (
                "É só me passar um pedido direto com o nome: ‘crie o arquivo notas.txt’. "
                "Se quiser texto dentro dele, acrescente ‘e escreva ...’. Esta pergunta só "
                "explica o caminho; não criou nada."
            ),
            (
                "O formato mais simples é ‘cria um arquivo chamado notas.txt’ — e, se houver "
                "conteúdo, já diga na sequência. A criação só acontece no pedido de verdade; "
                "depois eu verifico o arquivo antes de confirmar."
            ),
        ]
    elif tipo_norm == "apagar_arquivo":
        nome = alvo_limpo or "notas.txt"
        opcoes = [
            (
                f"Para apagar comigo, diga ‘apaga o arquivo {nome}’. Eu resolvo o alvo, "
                "mostro o caminho e peço sua confirmação antes de enviá-lo à lixeira. "
                "Perguntar como fazer não apaga nada."
            ),
            (
                f"Você pode pedir diretamente ‘envia {nome} para a lixeira’. Antes de mexer "
                "no arquivo, eu confirmo com você qual é o caminho; só então faço e verifico "
                "o resultado."
            ),
            (
                f"Diga o nome no pedido, por exemplo ‘apague {nome}’. Eu não salto a etapa "
                "de confirmação: identifico o arquivo, peço o seu sim e uso a lixeira para "
                "ainda dar chance de restaurar."
            ),
        ]
    elif tipo_norm == "abrir_app":
        nome = alvo_limpo or "o aplicativo"
        opcoes = [
            (
                f"Para abrir {nome} comigo, diga ‘abre {nome}’. Eu procuro o programa instalado "
                "e, se ele já estiver aberto, trago a janela para a frente. Esta pergunta não "
                "abriu nada."
            ),
            (
                f"O pedido direto é simples: ‘abra {nome}’. Aí eu tento localizar {nome}, abrir "
                "ou focar a janela e só confirmo o que o computador mostrar. Agora eu apenas "
                "expliquei, sem executar."
            ),
            (
                f"Você pode mandar ‘abre {nome} e deixa em foco’. Eu aciono a habilidade local "
                "e verifico a janela; como aqui foi uma pergunta de procedimento, {nome} ficou "
                "como estava."
            ),
        ]
    elif tipo_norm == "capacidade_apps":
        opcoes = [
            (
                "Consigo abrir aplicativos instalados e trazer para a frente uma janela que já "
                "esteja aberta. Aqui você só perguntou sobre a habilidade, então não acionei nada."
            ),
            (
                "Sim. Quando você pede pelo nome, eu tento localizar o programa, abrir ou focar "
                "a janela e verifico o resultado. Perguntar se eu consigo não executa o pedido."
            ),
            (
                "Abro apps, sim — desde que o computador reconheça o nome ou a janela. Mas esta "
                "foi uma consulta de capacidade; nenhum aplicativo foi aberto."
            ),
        ]
    elif tipo_norm == "capacidade_apps_e_janelas":
        opcoes = [
            (
                "Consigo abrir programas e organizar janelas visíveis, sim. Como você só "
                "perguntou sobre essas habilidades, não abri nem movi nada."
            ),
            (
                "Tenho as duas habilidades: abrir programas instalados e organizar janelas "
                "na tela. Esta foi uma consulta, então o computador ficou como estava."
            ),
            (
                "Sim: abro programas e também organizo janelas quando você pede diretamente. "
                "A pergunta por si só não executou nenhuma das duas ações."
            ),
        ]
    elif tipo_norm == "capacidade_criar_e_pesquisar_arquivos":
        opcoes = [
            (
                "Consigo criar arquivos e pesquisar localmente os que já existem por nome, "
                "pasta, conteúdo, tipo, significado ou data. Aqui você só perguntou; não criei "
                "nem procurei nada."
            ),
            (
                "Tenho as duas capacidades: criar arquivos quando você dá o nome e pesquisar "
                "localmente por vários critérios. Como isto foi uma consulta, nenhum arquivo "
                "foi alterado."
            ),
            (
                "Sim. Posso criar arquivos e pesquisar localmente no seu computador, sem mandar "
                "o conteúdo para a internet. A pergunta não virou comando escondido."
            ),
        ]
    elif tipo_norm == "alvo_app_nao_encontrado":
        nome = alvo_limpo or "esse aplicativo"
        opcoes = [
            (
                f"Porque não encontrei {nome} entre os programas instalados nem nas janelas "
                "abertas. Foi uma falha desse alvo, não falta de acesso: eu continuo conseguindo "
                "abrir aplicativos que o computador reconheça."
            ),
            (
                f"O computador não reconheceu {nome} como aplicativo instalado ou janela aberta. "
                "Minha capacidade de abrir apps continua ativa; esse nome específico é que não "
                "levou a um alvo válido."
            ),
            (
                f"{nome} não apareceu na busca local por programas e janelas. Então eu parei sem "
                "inventar sucesso — consigo abrir apps, mas preciso que o alvo exista ou tenha um "
                "nome reconhecível."
            ),
        ]
    else:
        return ""
    return escolher_variacao(opcoes, evitar=evitar)


def falar_capacidades_gerais(
    principais: Sequence[str],
    *,
    relacionadas: Sequence[str] = (),
    tem_outras: bool = False,
    contexto: Mapping[str, Any] | None = None,
) -> str:
    """Apresenta uma amostra real do catálogo sem soar como manual."""
    lista = _lista_natural(principais)
    assunto = _lista_natural(relacionadas)
    outras = (
        " Tenho outras habilidades menores e confiro o estado delas quando você perguntar."
        if tem_outras else ""
    )
    evitar = _falas_recentes(contexto)
    if assunto:
        opcoes = [
            (
                f"Pelo assunto da conversa, eu começaria por {assunto}. No geral, consigo {lista}."
                f"{outras} Eu só mexo de verdade quando você pede."
            ),
            (
                f"Como a gente estava falando disso, {assunto} vem primeiro. Fora daí, também "
                f"consigo {lista}.{outras} Pergunta continua sendo pergunta; ação só nasce de pedido."
            ),
            (
                f"Nesse papo, meu braço mais útil é {assunto}. Mas o repertório vai além: consigo "
                f"{lista}.{outras} Nada disso me autoriza a agir sozinha."
            ),
        ]
    else:
        opcoes = [
            (
                f"No geral, consigo {lista}.{outras} Eu só mexo de verdade quando você pede; "
                "perguntar não executa nada."
            ),
            (
                f"Tenho bastante braço por aqui: consigo {lista}.{outras} Mas relaxa, uma pergunta "
                "não vira comando escondido."
            ),
            (
                f"Não fico só no papo. Posso {lista}.{outras} Meu limite é simples: conversa é "
                "conversa, ação precisa de pedido."
            ),
            (
                f"Por aqui eu dou conta de {lista}.{outras} E não, eu não uso curiosidade como "
                "desculpa para sair clicando nas coisas."
            ),
        ]
    return escolher_variacao(opcoes, evitar=evitar)
