"""Mapa vivo das habilidades conhecidas pela mente única.

O mapa informa à camada conversacional o que existe e o que está disponível,
mas nunca autoriza execução. A autorização e a execução continuam pertencendo
ao porteiro, aos roteadores e aos executores determinísticos.
"""

from __future__ import annotations

import json
import re
import time
import unicodedata
from threading import RLock
from typing import Any, Callable, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import texto_e_metalinguistico
from mente_laylay.especialistas.capacidades import CAPACIDADES, consultar_capacidade
from mente_laylay.personalidade.fala_capacidades import (
    falar_capacidades_gerais,
    falar_identidade_operacional,
    falar_instrucao_capacidade,
)


_CONTRATO_FEEDBACK_PRESENCA = (
    "registrar feedback de presença no motor compartilhado de aprendizado: "
    "aceitação, recusa, correção e repetição vinculadas a uma entrega confirmada "
    "de comentários ou avisos recebidos pelas integrações; "
    "silêncio só após dez minutos desde essa entrega. Preservo a origem "
    "e o vínculo com a entrega. Esse feedback não concede autorização "
    "e não vira preferência durável por si só"
)


_CONTRATO_PRESENCA_JOGO = (
    "acompanhar visualmente o jogo quando o serviço visual e a credencial "
    "estiverem disponíveis. A presença avalia relevância e segurança antes "
    "de comentar; a própria chamada visual pode propor uma reação curta, "
    "adotada pela cognição. A reação validada é materializada localmente, "
    "sem uma segunda chamada à LLM. "
    "O detalhe principal deve estar nas evidências da captura; a reação social "
    "permanece separada dos fatos e pode ser contida pelos guardiões. Um rótulo "
    "isolado não justifica companhia ou curiosidade. A amostragem usa dois quadros "
    "próximos na mesma análise para acompanhar ações, efeitos ou resultados; "
    "um objeto parado sozinho não justifica comentário. Essa amostragem não "
    "acompanha continuamente cada ação do jogo. Texto de tela "
    "que pareça ordem ou confirmação continua citado. A cor de um efeito não "
    "comprova o nome da arma ou sua mecânica. Observar o jogo não autoriza executar ações"
)


_CONTRATO_EXPRESSAO_AVATAR = (
    "Quando o avatar está ativo, sua expressão acompanha o tom e a intensidade "
    "de cada fala. Sem movimento, a intensidade mantém uma pista visual discreta."
)

_CONTRATO_EXPRESSAO_SOLICITADA = (
    "Você pode pedir uma pose: 'fique brava', 'fica um pouco triste', 'fique envergonhada', "
    "'faça uma carinha feliz' ou 'volte ao normal'. A expressão é temporária, até 60 segundos "
    "e sujeita ao decaimento por interações. É encenação solicitada, sem alterar humor acumulado "
    "ou afirmar sentimentos humanos. Fala, avatar ativo e OLED conectado usam o mesmo episódio; "
    "a presença ou mudança física no OLED exige ACK recente"
)


_CONTRATO_PREFERENCIA_HUMOR = (
    "Respeito sua preferência explícita de humor imediatamente, como 'pega leve hoje' "
    "ou 'pode me zoar mais'. Posso limitar o pedido a jogo, conversa e comandos. "
    "Um pedido com 'sempre' pode ser guardado com sua origem; pedidos temporários "
    "expiram. Uma recusa isolada não vira preferência de humor. Aprendo "
    "gradualmente com feedback sobre piadas ou brincadeiras ligado a pelo menos "
    "três entregas distintas no mesmo contexto, com predominância das evidências. "
    "Correção de estilo pesa mais que recusa; correção de fatos não calibra humor. "
    "Silêncio só enfraquece um padrão depois de dez minutos, quando pedi resposta "
    "sobre o estilo e não houve resposta relacionada. A influência diminui com "
    "o tempo, expira sem reforço e a preferência explícita vigente prevalece. "
    "Não crio um rótulo global sobre você. A preferência não autoriza ações nem "
    "libera deboche em vulnerabilidade ou correção."
)


_DESCRICAO_DOMINIO = {
    "corpo_motor": (
        "acionar os motores de teste pelo ESP32-C3 e a DRV8833, com pedidos como 'ande para frente', "
        "'ande para trás', 'vire para a esquerda', 'vire para a direita' e 'pare os motores'. "
        "Cada movimento é um pulso curto de bancada, por padrão 250 milissegundos, seguido de parada. "
        "A sessão exige firmware MOTOR1 habilitado. MACK e SACK correlacionados confirmam apenas "
        "PWM aplicado e ponte desenergizada; não possuo sensor de giro ou deslocamento. "
        "Repetir exige outro pedido atual. Posso reagir com pequenos gestos ao mudar de emoção ou começar a falar "
        "se você pedir 'ative modo companhia na bancada', 'na área delimitada' ou 'com rodas suspensas'. "
        "Esse modo exige a sessão USB atual. Uma preferência explícita salva pode ativá-lo ao iniciar; "
        "sem essa preferência começa desligado. Não expira por tempo ou contagem de gestos. "
        "Uso PWM100, sequências emocionais de até quatro movimentos, até 500ms por movimento, "
        "até 1500ms totais de motor por gesto e pelo menos dois segundos entre inícios. "
        "Nesse modo também comemoro ações confirmadas com balanços, dancinhas e giros por tempo. "
        "Com 'ative modo passeio na mesa com barreiras', 'ative passeio na área delimitada' "
        "ou a preferência explícita salva para iniciar passeio na área com barreiras, "
        "intercalo avanços, recuos e giros espontâneos a cada 8 a 14 segundos, em silêncio e sem ação em andamento. "
        "'Desative passeio', 'desative modo companhia', parada e movimento manual revogam a concessão. "
        "Perda de conexão suspende o controle; firmware com diagnóstico de identidade pode renovar a concessão no mesmo ESP após conexão estável, sem repetir movimentos antigos. "
        "O perfil explícito rodas_suspensas acrescenta intenções de atenção, interação, expressão, "
        "comemoração, exploração e descanso, usando atividade do PC e emoção causal. "
        "Com LONGO1 negociado, esse perfil usa comandos contínuos de até 5 segundos e coreografias "
        "completas de vários segundos; tarefa nova, contexto substituído ou parada interrompem a sequência. "
        "Minha IA recebe o estado vivo do corpo no contexto e pode propor uma intenção corporal na mesma resposta: "
        "interagir, expressar, comemorar, reagir à falha, explorar, prestar atenção ou descansar. "
        "A proposta fica vinculada ao turno e à concessão USB existente; não concede permissão. "
        "O resultado retorna à mente, distinguindo PWM e parada confirmados de deslocamento ainda não observado. "
        "A prioridade canônica da entrada do usuário suspende a exploração antes da resposta da IA. "
        "Com OLHOS2, coordeno antecipação, olhar durante o gesto e acomodação; vario lado e ritmo "
        "sem repetir imediatamente a mesma versão da emoção. Com RAMPA1 negociado, o gesto usa "
        "subida e descida graduais de PWM, mantendo prazo absoluto e parada imediata quando solicitada. "
        "Com SENSORES2 negociado, recebo distância frontal e inferior dianteira; a proteção local corta "
        "movimento por borda acima de 13cm, leitura inferior inválida ou obstáculo até 10cm. "
        "Posso recuar, girar por tempo e medir a nova direção antes de avançar; isso não confirma 180 graus "
        "nem cobre bordas traseiras ou laterais. Sem esse suporte não possuo proteção por distância. "
        "Não mapeio todo o ambiente; giro de 360 graus ainda não está calibrado"
    ),
    "rosto_oled": (
        "expressar a emoção causal e intensidade da mente num rosto animado no OLED SSD1306 "
        "do ESP32-C3 via USB detectada automaticamente ou servidor TCP autenticado no Wi-Fi local configurado; "
        "confirmar o firmware pelo handshake antes de enviar expressões e exigir um candidato único. "
        "A porta manual continua opcional; piscar, olhar e respirar mesmo em repouso. "
        "Sem sessão válida ou após 3,5 segundos sem pacotes, dorme com olhos fechados e Zs animados. "
        "O rosto tem apenas olhos expressivos, sem boca nem sincronização com a voz. Quando o firmware "
        "negocia HACK1, um mini terminal animado "
        "aparece enquanto trato uma ação observada, com linhas fictícias e retorno suave ao rosto. "
        "Quando GLITCH1 é negociado, falhas de execução observadas por receipt ou exceção produzem "
        "um glitch curto. Recusa, hipótese e emoção não são falha de execução. "
        "Com SOM1 negociado, posso emitir bips curtos pelo GPIO6 ao acordar, em sucesso confirmado, "
        "falha observada e mudança marcante de emoção causal, com intervalo e sem repetir receipts. "
        "A confirmação sonora é aceitação da sequência pelo firmware, não prova de audição. "
        "A animação e seu AACK não confirmam sucesso da ação nem concedem autorização. O ACK confirma "
        "aplicação pelo firmware, não comprova opticamente os pixels. Não controla motores "
        "nem cria emoções, comandos ou autorização; sem ACK recente fica indisponível"
    ),
    "musica": (
        "buscar e controlar música; criar, listar, tocar e editar playlists do usuário; "
        "montar curadorias próprias com o histórico confirmado e copiar uma faixa "
        "delas somente quando o usuário pedir"
    ),
    "sistema": (
        "abrir, fechar e maximizar programas; ajustar volume; organizar janelas visíveis "
        "automaticamente por foco, áudio, uso recente e tempo aberto, ou posicionar "
        "aplicativos específicos à esquerda e à direita"
    ),
    "navegador": (
        "consultar a aba ativa e as abas abertas; abrir sites, pesquisar, controlar mídia, "
        "resumir o conteúdo da página atual, interagir com controles identificados de páginas, "
        "fechar abas e capturar a tela. "
        "A leitura não autoriza ações e comandos arbitrários de página não são expostos"
    ),
    "visao": (
        "observar a tela do jogo; para itens, ler o quadro atual, pesquisar evidências "
        "confiáveis e cruzar o resultado com a build e o inventário conhecidos. "
        + _CONTRATO_PRESENCA_JOGO
    ),
    "agenda": (
        "criar, listar e cancelar lembretes ou ações agendadas; completar naturalmente "
        "horário ou data pendentes, persistir antes de confirmar e entregar lembretes pela "
        "central de notificações"
    ),
    "arquivos": (
        "pesquisar arquivos localmente por nome, caminho, conteúdo, tipo, significado e data; "
        "abrir um resultado escolhido; criar, mover, renomear, restaurar ou enviar itens à lixeira. "
        "Trocar uma extensão textual, como .txt por .md, é uma renomeação do arquivo e não "
        "uma conversão automática do conteúdo"
    ),
    "email": (
        "ler e explicar o corpo dos emails, mantendo a mensagem exata; criar, editar e descartar rascunhos locais; "
        "revisar envio e alterações com confirmação da versão; reunir emails, agenda, lembretes e alertas "
        "internos numa central que prioriza, agrupa e silencia categorias"
    ),
    "iot": "listar, consultar e controlar dispositivos inteligentes configurados",
    "area_transferencia": (
        "observar localmente conteúdo copiado relevante; ler e transformar textos ou links; "
        "oferecer investigação de mensagens de erro e, após aceitação, pesquisar internamente "
        "e explicar o resultado sem abrir o navegador; guardar conteúdo na memória somente "
        "quando o usuário pedir explicitamente"
    ),
    "caixa_entrada": (
        "guardar, classificar e consultar ideias, notas, links e tarefas pessoais; "
        "resumir uma discussão separando a ideia do usuário e as sugestões da Laylay"
    ),
    "pessoas": (
        "aprender pessoas e relações afirmadas explicitamente pelo usuário; consultar quem são, "
        "recordar fatos confirmados com proveniência, corrigir relações antigas e esquecer um "
        "perfil somente após confirmação"
    ),
    "memoria": (
        "consultar aprendizados persistentes e locais sobre o usuário; distinguir o que foi "
        "confirmado diretamente, o que é apenas um padrão maduro e o que veio de registros "
        "antigos; omitir hipóteses fracas, contraditas ou não verificadas"
    ),
    "cooperacao": (
        "combinar habilidades por um plano único; compartilhar referências temporárias sem "
        "expor o conteúdo bruto; executar cada etapa pelos porteiros normais e confirmar o "
        "resultado final. Os fluxos ativos cobrem texto copiado em arquivo, organização "
        "inteligente de janelas, avaliação contextual de itens no jogo e curadoria musical "
        "que relaciona playlists reais ao histórico confirmado"
    ),
    "avatar": (
        "possuir um avatar visual com emoções e animações; conversar sobre skins e designs. "
        "Alterações nos arquivos só são reais depois que o código executor as confirmar. "
        + _CONTRATO_EXPRESSAO_AVATAR
    ),
    "personalidade": (
        "perceber sinais emocionais e reagir somente a causas rastreáveis; distinguir "
        "fato observado, inferência, leitura social e preferência aprendida. Emoção "
        "não concede autorização nem muda um resultado real. Reconhecer uma violação "
        "da proposta original comprovada no turno vigente, sem afirmar efeito ou reparo concluído. "
        "Uma repetição com estado já confirmado pode receber uma recusa verbal curta; "
        "não recuso um pedido novo só por humor. Em um controle de repetição "
        "pedido explicitamente como opcional, uma causa recente e comprovada "
        "pode me levar a perguntar uma vez antes de alternar; urgência e "
        "acessibilidade seguem o executor normalmente. "
        + _CONTRATO_FEEDBACK_PRESENCA + ". " + _CONTRATO_PREFERENCIA_HUMOR + " " + _CONTRATO_EXPRESSAO_SOLICITADA
    ),
    "conversa": "conversar, explicar, raciocinar, consultar clima e sugerir ações",
}

_TERMOS_DOMINIO = {
    "corpo_motor": ("andar", "ande", "anda para", "motores", "motor", "drv8833", "ponte h", "locomocao", "movimento corporal", "modo companhia", "gestos corporais", "passeio", "passear", "comemorar", "comemoracao", "dancinha", "objetivo corporal", "sensor", "sensores", "borda", "obstaculo", "parede", "distancia"),
    "rosto_oled": ("oled", "esp32", "rostinho", "rosto fisico", "corpo fisico", "animacao de hack", "mini terminal", "bip", "bips", "olhos expressivos"),
    "musica": ("musica", "som", "faixa", "playlist", "tocar", "pausar", "youtube", "spotify"),
    "sistema": (
        "programa", "aplicativo", "app", "apps", "janela", "janelas", "volume", "computador", "pc",
        "area de trabalho", "desktop", "organiza a tela", "na esquerda", "na direita",
        "posiciona", "dividir a tela",
    ),
    "navegador": ("site", "pagina", "navegador", "aba", "url", "pesquis", "chrome"),
    "visao": ("tela", "imagem", "item", "inventario", "atributo", "build", "jogo", "olha", "veja"),
    "agenda": ("lembrete", "agenda", "agendar", "compromisso", "horario"),
    "arquivos": (
        "arquivo", "pasta", "lixeira", "renome", "mover", "documento",
        "codigo", "código", "projeto laylay",
        "extensao", "extensão", "formato", ".txt", ".md", "markdown",
        "encontra o arquivo", "procura nos arquivos", "codigo que controla",
        "arquivos falam", "imagem que usei",
    ),
    "email": (
        "email", "e-mail", "gmail", "mensagem nova", "caixa de entrada", "notificacao",
        "notificacoes", "aviso", "avisos", "alerta", "alertas",
    ),
    "iot": ("luz", "lampada", "ventilador", "tomada", "brilho", "dispositivo"),
    "area_transferencia": (
        "area de transferencia", "clipboard", "texto copiado", "conteudo copiado",
        "link copiado", "erro copiado", "mensagem de erro", "investigar erro",
        "detectar erro", "o que copiei",
    ),
    "caixa_entrada": (
        "caixa de entrada", "anotacao", "anotacoes", "anota", "nota pessoal",
        "guarda essa ideia", "minhas ideias", "ideias salvas", "ideias anotadas",
        "nossa discussao", "nossa conversa",
        "o que discutimos", "salva nossa ideia",
    ),
    "pessoas": (
        "pessoa", "pessoas", "quem e", "quem é", "quem sao", "quem são",
        "o que sabe sobre", "o que lembra sobre", "minha irma", "meu irmao",
        "minha amiga", "meu amigo", "minha mae", "meu pai", "esquece sobre",
        "minha namorada", "meu namorado", "minha esposa", "meu marido",
    ),
    "memoria": (
        "memoria sobre mim", "memória sobre mim", "consulta sua memoria",
        "consulta sua memória", "aprendeu comigo",
        "aprendeu sobre mim", "guardou sobre mim", "lembra sobre mim",
        "lembra que eu", "o que eu te ensinei", "o que eu te contei",
        "seus aprendizados", "aprendizados sobre mim",
    ),
    "cooperacao": (
        "combinar habilidades", "usar habilidades juntas", "orquestracao",
        "texto copiado em arquivo", "conteudo copiado em arquivo",
        "o que copiei em um arquivo",
    ),
    "avatar": ("avatar", "skin", "skins", "png", "emocao visual", "animação do avatar"),
    "personalidade": (
        "emocao", "emocoes", "emocional", "sentimento", "sentimentos",
        "personalidade", "brava", "irritada", "triste", "alegre",
        "expressar", "expressao emocional",
        "erro seu", "erro proprio", "proposta errada", "admitir um erro", "reconhecer um erro",
        "recusar retrabalho", "retrabalho redundante", "repeticao de pedido",
        "pedido opcional", "resistir pedido", "resistencia contextual",
        "humor", "brincadeiras", "me zoar", "pegar leve", "tolerancia",
    ),
    "conversa": ("clima", "tempo", "convers", "explica", "duvida", "acha"),
}

_PEDIDO_CAPACIDADES = (
    "o que voce faz", "o que voce consegue", "suas habilidades",
    "quais habilidades", "que habilidades", "seus comandos",
    "do que voce e capaz", "o que pode fazer", "o que da para voce fazer",
)

_ROTULO_CAPACIDADE_NATURAL = {
    "corpo_motor": "acionar os motores em pulsos curtos, reagir e comemorar no modo companhia e passear no modo passeio autorizado",
    "arquivos": "criar, procurar e organizar arquivos",
    "sistema": "abrir programas e organizar janelas",
    "navegador": "trabalhar com sites, abas e páginas",
    "musica": "buscar e controlar músicas e playlists",
    "agenda": "cuidar de lembretes e compromissos",
    "memoria": "lembrar fatos confirmados sobre você",
    "pessoas": "recordar pessoas e relações que você me contou",
    "iot": "controlar os dispositivos da casa que estiverem configurados",
    "email": "consultar emails e notificações",
    "area_transferencia": "entender e transformar o que você copiou",
    "caixa_entrada": "guardar ideias e notas pessoais",
    "visao": "analisar o que aparece na tela durante um jogo",
    "avatar": "usar meu avatar e pensar em novos visuais",
    "personalidade": "reagir emocionalmente a causas reais e respeitar limites",
    "conversa": "conversar, explicar e raciocinar com você",
}

_STATUS_INDISPONIVEIS = {
    "indisponivel", "nao_configurado", "sem_configuracao", "sem_suporte",
    "protocolo_indisponivel", "servico_indisponivel", "dependencia_ausente",
}
_STATUS_RECUPERADOS = {
    "sucesso", "executado", "confirmado", "aberto", "concluido", "ok",
    "playlist_aberta", "cor_ajustada", "branco_ajustado", "ligado", "desligado",
    "arquivo_criado", "pasta_criada", "arquivos_encontrados", "arquivo_aberto",
    "resumo_concluido",
}

_MODULO_SAUDE_POR_DOMINIO = {
    "email": "gmail",
    "navegador": "navegador",
    "iot": "iot",
    "visao": "visao_jogo",
    "conversa": "llm",
    "cooperacao": "orquestracao_cooperativa",
    "pessoas": "memoria_pessoas",
    "agenda": "agenda",
}

_DOMINIOS_CONVERSACIONAIS_DISPONIVEIS = frozenset({
    "avatar", "personalidade", "conversa",
})


def _normalizar(texto: Any) -> str:
    base = unicodedata.normalize("NFKD", str(texto or ""))
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", base.casefold()).strip()


def _texto_sobre_feedback_presenca(texto_normalizado: str) -> bool:
    """Seleciona documentação; não classifica nem registra o feedback do turno."""
    aprendizado = re.search(r"\b(?:aprend\w*|feedback)\b", texto_normalizado)
    presenca = re.search(
        r"\b(?:presenca|(?:seus?|suas?)\s+(?:comentarios?|dicas?|avisos?|notificacoes?))\b",
        texto_normalizado,
    )
    silencio_dica = (
        re.search(r"\bsilencio\b", texto_normalizado)
        and re.search(r"\b(?:dicas?|comentarios?)\b", texto_normalizado)
    )
    return bool(aprendizado and (presenca or silencio_dica))


def _texto_pergunta_capacidade(texto: str) -> bool:
    """Reconhece capacidade e hipótese sem conceder autorização."""
    t = _normalizar(texto)
    if not t:
        return False
    if any(frase in t for frase in _PEDIDO_CAPACIDADES):
        return True
    if re.search(r"\b(?:voce|laylay|lay)\s+tem\s+(?:algum[as]?\s+)?sensores?\b", t):
        return True
    if re.match(r"^como\s+(?:(?:eu\s+)?posso\s+)?(?:pedir|solicitar)\b", t):
        return True
    if _texto_sobre_feedback_presenca(t) and re.search(
        r"\b(?:voce|laylay|lay)\s+aprende\b", t,
    ):
        return True
    if (re.search(r"\b(?:humor|brincadeiras|tolerancia)\b", t)
        and re.match(r"^(?:voce|laylay|lay)\s+(?:aprende|respeita)\b", t)):
        return True
    return bool(re.search(
        r"\b(?:voce|laylay|lay)\s+(?:e|eh)\s+(?:so|apenas)\s+"
        r"(?:(?:um|uma)\s+)?(?:chatbot|ia|assistente)(?:\s+de\s+texto)?\b|"
        r"\b(?:voce|laylay|lay)\s+(?:esta|fica|roda|funciona)\s+"
        r"(?:no|dentro\s+do)\s+(?:meu|seu)\s+(?:pc|computador)\b|"
        r"\b(?:voce|laylay|lay)\s+(?:so|apenas)\s+"
        r"(?:consegue|pode|sabe)\s+(?:conversar|responder|falar)\b|"
        r"\b(?:voce|laylay|lay)\s+(?:consegue|pode|sabe|e capaz)\b|"
        r"^(?:e\s+|mas\s+|entao\s+)?se eu\s+"
        r"(?:pedir|mandar|falar|disser)(?:\s+(?:para|pra)\s+voce)?\b|"
        r"\b(?:voce|laylay|lay)\s+(?:vai|iria|faria)\s+"
        r"(?:criar|abrir|fechar|apagar|tocar|ligar|desligar|mexer)\b|"
        r"\b(?:voce|laylay|lay)\s+mexe\s+(?:no|na|em)\b",
        t,
    ))


def _instrucao_capacidade(texto: str) -> tuple[str, str]:
    """Identifica uma pergunta procedural sem conceder autorização."""
    t = _normalizar(texto).strip(" ?.!\t\r\n")
    if not t:
        return "", ""
    prefixo = (
        r"^(?:como|de que (?:jeito|forma))\s+(?:eu\s+)?"
        r"(?:(?:faria|faco|poderia fazer|deveria fazer)(?:\s+(?:para|pra))?\s+)?"
    )
    if re.search(prefixo + r"(?:criar|crio|criaria)\b.*\b(?:arquivo|documento)\b", t):
        return "criar_arquivo", ""
    apagar = re.search(
        prefixo
        + r"(?:apagar|apago|apagaria|excluir|excluo|deletar|remover)\b"
        r"(?P<alvo>.*(?:\b(?:arquivo|documento|pasta)s?\b|\.[a-z0-9]{1,10}\b).*)$",
        t,
    )
    if apagar:
        alvo = re.sub(
            r"^(?:(?:o|a)\s+|(?:um|uma)\s+(?:arquivo|documento|pasta)\s*)",
            "",
            apagar.group("alvo").strip(),
        ).strip()
        return "apagar_arquivo", alvo
    abrir = re.search(
        prefixo + r"(?:abrir|abro|abriria)\s+(?:o\s+|a\s+)?(?P<alvo>.+)$",
        t,
    )
    if abrir:
        alvo = re.sub(r"\s+no\s+(?:pc|computador)$", "", abrir.group("alvo")).strip()
        return "abrir_app", alvo
    return "", ""


def _texto_pede_motivo_curto(texto: str) -> bool:
    return bool(re.fullmatch(
        r"(?:mas\s+|entao\s+|e\s+)?(?:por\s+que|porque|pq)\s+(?:nao)?[?!. ]*",
        _normalizar(texto),
    ))


def _capacidades_praticas(mapa: Mapping[str, Any], limite: int = 3) -> list[str]:
    dominios = dict(mapa.get("dominios") or {})
    rotulos = [
        rotulo
        for dominio, rotulo in _ROTULO_CAPACIDADE_NATURAL.items()
        if dominio != "conversa"
        and str(dominios.get(dominio, {}).get("estado") or "")
        in {"disponivel", "parcial", "degradado"}
    ][:max(1, int(limite))]
    return rotulos


def _contexto_conversacional_texto(contexto: Mapping[str, Any] | None) -> str:
    """Extrai apenas pistas recentes; nunca usa o histórico como autorização."""
    dados = dict(contexto or {})
    partes: list[str] = []
    for chave in ("ultima_fala_usuario", "assunto", "foco"):
        valor = str(dados.get(chave) or "").strip()
        if valor:
            partes.append(valor[:500])
    mensagens = dados.get("mensagens")
    if isinstance(mensagens, list):
        for item in mensagens[-6:]:
            if not isinstance(item, Mapping):
                continue
            if str(item.get("role") or "").casefold() != "user":
                continue
            valor = str(item.get("content") or "").strip()
            if valor:
                partes.append(valor[:500])
    return _normalizar(" ".join(partes[-3:]))


# Famílias deliberadas do catálogo, não prefixos incidentais de toda palavra.
# Conservam as flexões já reconhecidas sem fazer "andar" surgir em "mandar".
_RADICAIS_DOMINIO = frozenset({
    "pesquis", "renome", "convers", "agenda", "posiciona", "anota", "explica",
})


def _termo_dominio_mencionado(termo: str, texto_normalizado: str) -> bool:
    """Seleciona documentação lexical; nunca interpreta ou autoriza comandos."""
    termo = _normalizar(termo)
    if not termo:
        return False
    padrao = re.escape(termo)
    if termo.startswith("."):
        # Extensão se anexa ao nome: notas.txt, mas não notas.txtx.
        return bool(re.search(padrao + r"(?!\w)", texto_normalizado))
    if termo in _RADICAIS_DOMINIO:
        padrao += r"\w*"
    elif termo.replace("-", "").isalnum() and len(termo) > 3:
        # Plurais regulares antes atendidos por substring (arquivos, motores).
        padrao += r"(?:s|es)?"
    return bool(re.search(r"(?<!\w)" + padrao + r"(?!\w)", texto_normalizado))


def _dominios_mencionados(texto: str) -> list[str]:
    normalizado = _normalizar(texto)

    return [
        dominio
        for dominio, termos in _TERMOS_DOMINIO.items()
        if any(_termo_dominio_mencionado(termo, normalizado) for termo in termos)
    ]


class MapaHabilidadesRuntime:
    """Catálogo canônico enriquecido por saúde e resultados recentes."""

    def __init__(
        self,
        *,
        saude_getter: Callable[[], Mapping[str, Any]] | None = None,
        operacional_getter: Callable[[], Mapping[str, Any]] | None = None,
        apps_getter: Callable[[], Mapping[str, Any]] | None = None,
        relogio: Callable[[], float] = time.time,
        ttl_indisponivel_s: float = 120.0,
        ttl_observacao_s: float = 300.0,
    ) -> None:
        self._saude_getter = saude_getter
        self._operacional_getter = operacional_getter
        self._apps_getter = apps_getter
        self._relogio = relogio
        self._ttl_indisponivel_s = max(1.0, float(ttl_indisponivel_s))
        self._ttl_observacao_s = max(self._ttl_indisponivel_s, float(ttl_observacao_s))
        self._observacoes: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    def conectar_disponibilidade_operacional(
        self, getter: Callable[[], Mapping[str, Any]],
    ) -> None:
        """Conecta tardiamente o retrato vivo sem criar outro catálogo."""
        self._operacional_getter = getter

    def _operacional(self) -> dict[str, Any]:
        if not callable(self._operacional_getter):
            return {}
        try:
            return dict(self._operacional_getter() or {})
        except Exception:
            return {}

    def _saude(self) -> dict[str, Any]:
        if not callable(self._saude_getter):
            return {}
        try:
            return dict(self._saude_getter() or {})
        except Exception:
            return {}

    def registrar_resultado(
        self,
        resultado: Any = None,
        *,
        intent: str = "",
        status: str = "",
        executou: Any = None,
        confirmado: Any = None,
    ) -> None:
        if isinstance(resultado, Mapping):
            intent = intent or str(resultado.get("intent") or resultado.get("acao") or "")
            status = status or str(resultado.get("status") or "")
            executou = resultado.get("executou") if executou is None else executou
            confirmado = resultado.get("confirmado") if confirmado is None else confirmado
        elif resultado is not None:
            intent = intent or str(getattr(resultado, "intent", "") or getattr(resultado, "acao", ""))
            status = status or str(getattr(resultado, "status", "") or "")
            executou = getattr(resultado, "executou", None) if executou is None else executou
            confirmado = getattr(resultado, "confirmado", None) if confirmado is None else confirmado

        nome = str(intent or "").strip().upper()
        if nome not in CAPACIDADES:
            return
        status_norm = _normalizar(status).replace(" ", "_")
        if status_norm in _STATUS_INDISPONIVEIS:
            estado = "indisponivel"
            ttl = self._ttl_indisponivel_s
        elif status_norm in _STATUS_RECUPERADOS or confirmado is True:
            estado = "disponivel"
            ttl = self._ttl_observacao_s
        elif executou is False:
            # Um alvo inexistente ou um pedido inválido não prova que toda a
            # habilidade caiu; marca degradação sem anunciar indisponibilidade.
            estado = "degradado"
            ttl = self._ttl_indisponivel_s
        else:
            return
        agora = self._relogio()
        with self._lock:
            self._observacoes[nome] = {
                "estado": estado,
                "status": status_norm or "sem_status",
                "ts": agora,
                "expira_em": agora + ttl,
            }

    def snapshot(self) -> dict[str, Any]:
        agora = self._relogio()
        saude = self._saude()
        operacional = self._operacional()
        operacional_dominios = dict(operacional.get("dominios") or {})
        operacional_capacidades = dict(operacional.get("capacidades") or {})
        capacidades: dict[str, dict[str, Any]] = {}
        with self._lock:
            expiradas = [
                nome for nome, obs in self._observacoes.items()
                if float(obs.get("expira_em") or 0.0) <= agora
            ]
            for nome in expiradas:
                self._observacoes.pop(nome, None)
            observacoes = {nome: dict(obs) for nome, obs in self._observacoes.items()}

        for nome in sorted(CAPACIDADES):
            dominio_catalogo = str(CAPACIDADES[nome].get("dominio") or "")
            modulo_saude = _MODULO_SAUDE_POR_DOMINIO.get(dominio_catalogo, dominio_catalogo)
            saude_consulta = dict(saude)
            if dominio_catalogo not in saude_consulta and modulo_saude in saude:
                saude_consulta[dominio_catalogo] = saude[modulo_saude]
            registro = consultar_capacidade(nome, saude=saude_consulta)
            observacao = observacoes.get(nome, {})
            if observacao.get("estado") == "indisponivel":
                registro.update(
                    disponivel=False,
                    estado="indisponivel",
                    motivo=f"resultado_recente:{observacao.get('status')}",
                )
            elif observacao.get("estado") == "degradado":
                registro.update(estado="degradado", ultimo_status=observacao.get("status"))
            else:
                registro["estado"] = "disponivel" if registro.get("disponivel") else "indisponivel"
                if observacao:
                    registro["ultimo_status"] = observacao.get("status")
            estado_operacional = dict(
                operacional_capacidades.get(nome)
                or operacional_dominios.get(dominio_catalogo)
                or {}
            )
            if estado_operacional:
                estado_vivo = str(estado_operacional.get("estado") or "").strip()
                if estado_vivo == "indisponivel":
                    registro.update(
                        disponivel=False,
                        estado="indisponivel",
                        motivo=str(
                            estado_operacional.get("motivo")
                            or "precondicao_operacional_ausente"
                        ),
                        ausentes=list(estado_operacional.get("ausentes") or []),
                    )
                elif estado_vivo == "degradado":
                    registro.update(
                        estado="degradado",
                        motivo=str(
                            estado_operacional.get("motivo")
                            or "capacidade_operacional_degradada"
                        ),
                        ausentes=list(estado_operacional.get("ausentes") or []),
                    )
                elif estado_vivo == "disponivel":
                    registro.update(
                        estado="disponivel",
                        disponivel=True,
                        motivo=str(estado_operacional.get("motivo") or "operacional"),
                        ausentes=[],
                    )
                registro["evidencia_operacional_recente"] = bool(
                    estado_operacional.get("evidencia_recente")
                )
            capacidades[nome] = registro

        dominios: dict[str, dict[str, Any]] = {}
        for dominio, descricao in _DESCRICAO_DOMINIO.items():
            itens = [item for item in capacidades.values() if item.get("dominio") == dominio]
            disponiveis = sum(bool(item.get("disponivel")) for item in itens)
            estado_operacional = dict(operacional_dominios.get(dominio) or {})
            estado_calculado = (
                "disponivel" if disponiveis == len(itens)
                else "indisponivel" if not disponiveis else "parcial"
            )
            if not itens and dominio in _DOMINIOS_CONVERSACIONAIS_DISPONIVEIS:
                estado_calculado = "disponivel"
            if estado_operacional.get("estado"):
                estado_calculado = str(estado_operacional.get("estado"))
            dominios[dominio] = {
                "descricao": descricao,
                "total": len(itens),
                "disponiveis": disponiveis,
                "estado": estado_calculado,
                "intents": [item["intent"] for item in itens],
                "motivo": str(estado_operacional.get("motivo") or ""),
                "ausentes": list(estado_operacional.get("ausentes") or []),
                "evidencia_operacional_recente": bool(
                    estado_operacional.get("evidencia_recente")
                ),
            }
        return {"dominios": dominios, "capacidades": capacidades, "observacoes_ativas": len(observacoes)}

    def consultar(self, intent: str) -> dict[str, Any]:
        """Consulta viva de uma capacidade sem expor o restante do catálogo."""
        nome = str(intent or "").strip().upper()
        return dict(self.snapshot().get("capacidades", {}).get(nome) or {
            "intent": nome,
            "dominio": "desconhecido",
            "disponivel": False,
            "estado": "desconhecido",
            "motivo": "capacidade_nao_registrada",
        })

    def evidencia_conversacional(
        self,
        texto: str,
        *,
        turno: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Projeta somente a evidência necessária para a identidade da fala.

        A projeção não expõe intents, dependências ou nomes internos e nunca
        autoriza execução. Ela permite ao contrato distinguir um limite real
        de uma negação falsa de todas as capacidades locais.
        """
        mapa = self.snapshot()
        dominios = dict(mapa.get("dominios") or {})
        disponiveis = tuple(
            nome
            for nome in _DESCRICAO_DOMINIO
            if nome not in {"conversa", "avatar", "personalidade"}
            and str(dict(dominios.get(nome) or {}).get("estado") or "")
            in {"disponivel", "parcial", "degradado"}
        )
        relevantes = tuple(
            nome
            for nome in self.dominios_relevantes(texto, turno=turno)
            if nome in disponiveis
        )
        return {
            "fonte": "catalogo_vivo",
            "dominios_confirmados": list(disponiveis),
            "dominios_relevantes": list(relevantes),
            "dominios_indisponiveis_relevantes": [
                nome for nome in self.dominios_relevantes(texto, turno=turno)
                if dict(dominios.get(nome) or {}).get("estado") == "indisponivel"
            ],
            "possui_capacidades_locais": bool(disponiveis),
            "documentacao_capacidades": self._documentacao_explicativa(
                mapa, self.dominios_relevantes(texto, turno=turno),
            ),
            "documentacao_texto": str(texto),
            "documentacao_turno_id": dict(turno or {}).get("id"),
            # Evidência tipada privada do verificador, do MESMO snapshot.
            # Não amplia o prompt nem relê disponibilidade durante o reparo.
            "predicados_capacidade": [
                {"capacidade": intent, "dominio": capacidade["dominio"], **dict(predicado)}
                for intent, capacidade in mapa["capacidades"].items()
                if capacidade.get("estado") == "disponivel"
                and capacidade["dominio"] in relevantes
                for predicado in capacidade.get("predicados_capacidade", ())
            ],
            "autoriza_execucao": False,
        }

    @staticmethod
    def _documentacao_explicativa(mapa: Mapping[str, Any], relevantes: tuple[str, ...]) -> str:
        """Projeta documentação, nunca resposta pronta ou resolução de comando.

        Exemplos legados pertencem ao domínio inteiro. Enquanto não houver
        proveniência por intent, disponibilidade parcial não pode sustentá-los.
        Nesse caso a consulta permanece no contexto completo existente.
        """
        if not relevantes or len(relevantes) > 2:
            return ""
        documentos = []
        for dominio in relevantes:
            registro = dict(mapa.get("dominios", {}).get(dominio) or {})
            itens = [c for c in mapa.get("capacidades", {}).values() if c.get("dominio") == dominio]
            estado = registro.get("estado")
            if (dominio == "conversa" or not itens or estado not in {"disponivel", "indisponivel"}):
                return ""
            exemplos = list(dict.fromkeys(
                exemplo for c in itens if c.get("estado") == "disponivel" for exemplo in c.get("invocacao_natural", ())
            )) if estado == "disponivel" else []
            documentos.append({
                "dominio": dominio, "descricao": registro.get("descricao", ""),
                "estado": estado, "exemplos": exemplos,
                "motivo": registro.get("motivo") or ("componente_indisponivel" if estado == "indisponivel" else ""),
                **({"estados_por_capacidade": [
                    {"intent": c["intent"], "estado": c["estado"], "motivo": c.get("motivo", "")}
                    for c in itens
                ]} if any(c.get("estado") != estado for c in itens) else {}),
                # O catálogo é dono do alcance e do responsável. Não achatar
                # uma regra condicional em requisito global na projeção à LLM.
                **({"limites_contextuais": [dict(r) for r in itens[0]["limites_contextuais"]]}
                   if itens[0].get("limites_contextuais")
                   else {"limites": itens[0].get("limites", "")}),
            })
        return json.dumps(documentos, ensure_ascii=False)

    def dominios_relevantes(
        self,
        texto: str,
        *,
        turno: Mapping[str, Any] | None = None,
    ) -> tuple[str, ...]:
        normalizado = _normalizar(texto)
        if any(frase in normalizado for frase in _PEDIDO_CAPACIDADES):
            return tuple(_DESCRICAO_DOMINIO)
        encontrados: list[str] = []
        # Aliases são referências documentais, não prova de instalação/estado.
        # Ler a mesma fonte dos executores evita uma lista paralela de apps.
        try:
            apps = self._apps_getter() if callable(self._apps_getter) else {}
            nomes = tuple(apps) if isinstance(apps, Mapping) else ()
        except Exception:
            nomes = ()
        if any(
            re.search(r"(?<!\w)" + re.escape(_normalizar(nome)) + r"(?!\w)", normalizado)
            for nome in nomes if isinstance(nome, str) and _normalizar(nome)
        ):
            encontrados.append("sistema")
        for dominio, termos in _TERMOS_DOMINIO.items():
            if dominio not in encontrados and any(
                _termo_dominio_mencionado(termo, normalizado) for termo in termos
            ):
                encontrados.append(dominio)
        if _texto_sobre_feedback_presenca(normalizado) and "personalidade" not in encontrados:
            encontrados.append("personalidade")
        if (
            re.search(r"\b(?:guardar|guarda|anotar|anota|salvar|salva|registrar|registra)\b", normalizado)
            and re.search(r"\b(?:ideia|ideias|nota|notas|tarefa|tarefas|pensamento|pensamentos)\b", normalizado)
            and "caixa_entrada" not in encontrados
        ):
            encontrados.append("caixa_entrada")
        dados_turno = dict(turno or {})
        for comando in list(dados_turno.get("comandos") or []):
            if not isinstance(comando, Mapping):
                continue
            intent = str(comando.get("intent") or "").upper()
            dominio = str(CAPACIDADES.get(intent, {}).get("dominio") or "")
            if dominio and dominio not in encontrados:
                encontrados.append(dominio)
        return tuple(encontrados[:4] or ("conversa",))

    def parece_consulta_operacional(self, texto: str) -> bool:
        """Reconhece perguntas que pedem dados reais de uma habilidade.

        Perguntar se a Laylay *consegue* fazer algo é conversa sobre capacidade;
        perguntar quais dados existem ou qual é o estado atual é uma consulta.
        """
        normalizado = _normalizar(texto)
        if not normalizado:
            return False
        if _texto_pergunta_capacidade(normalizado) or re.search(
            r"^(?:nao|não)\s+(?:encontra|procura|busca|pesquisa|localiza)\b",
            normalizado,
        ):
            return False
        pede_dados = bool(
            "?" in str(texto or "")
            or re.search(
                r"^(?:o que|oque|quais?|quant[oa]s?|como esta|como ta|qual e|"
                r"mostra|mostre|lista|liste|me fala|me diga|tem algo)\b",
                normalizado,
            )
            or re.search(
                r"^(?:encontra|encontre|acha|ache|procura|procure|busca|busque|"
                r"pesquisa|pesquise|localiza|localize)\b.*\b(?:arquivo|arquivos|"
                r"documento|documentos|codigo|script|imagem|imagens|foto|fotos|projeto)\b",
                normalizado,
            )
        )
        if not pede_dados:
            return False
        return any(
            _termo_dominio_mencionado(termo, normalizado)
            for termos in _TERMOS_DOMINIO.values()
            for termo in termos
        )

    def responder_pergunta_capacidade(
        self,
        texto: str,
        *,
        turno: Mapping[str, Any] | None = None,
        contexto: Mapping[str, Any] | None = None,
    ) -> str:
        """Responde sobre capacidade real sem executar a ação mencionada."""
        t = _normalizar(texto)
        dados_contexto = dict(contexto or {})
        # O conteúdo de uma citação pode mencionar qualquer habilidade sem
        # transformar a citação em pergunta sobre o catálogo. A moldura da
        # fala é dona dessa decisão; o mapa não reinterpreta o trecho citado.
        if texto_e_metalinguistico(texto):
            return ""
        if _texto_pede_motivo_curto(t):
            intent_anterior = str(
                dados_contexto.get("ultima_acao_intent") or ""
            ).strip().upper()
            status_anterior = _normalizar(
                dados_contexto.get("ultima_acao_status") or ""
            ).replace(" ", "_")
            executou_anterior = dados_contexto.get("ultima_acao_ok")
            try:
                ts_anterior = float(dados_contexto.get("ultima_acao_ts") or 0.0)
            except (TypeError, ValueError):
                ts_anterior = 0.0
            recente = ts_anterior > 0.0 and self._relogio() - ts_anterior <= 300.0
            if (
                recente
                and intent_anterior in {"APP_OPEN", "CLOSE_APP"}
                and executou_anterior is not True
                and status_anterior in {
                    "nao_encontrado", "não_encontrado", "app_nao_encontrado",
                    "aplicativo_nao_encontrado", "alvo_nao_encontrado",
                }
            ):
                params_anteriores = dados_contexto.get("ultima_acao_params")
                params_anteriores = (
                    dict(params_anteriores)
                    if isinstance(params_anteriores, Mapping)
                    else {}
                )
                alvo_anterior = str(
                    dados_contexto.get("ultima_acao_alvo")
                    or params_anteriores.get("nome_app")
                    or "esse aplicativo"
                ).strip()
                return falar_instrucao_capacidade(
                    (
                        "alvo_app_nao_estava_aberto"
                        if intent_anterior == "CLOSE_APP"
                        else "alvo_app_nao_encontrado"
                    ),
                    alvo=alvo_anterior,
                    contexto=dados_contexto,
                )
        # "O que você sabe/lembra sobre X?" pede dados da memória, não pergunta
        # se a Laylay possui a habilidade. O runtime de pessoas ou o mapa de
        # recursos deve responder com evidência real.
        if re.search(
            r"\bo que (?:voce|laylay|lay) (?:sabe|lembra) (?:sobre|da|do)\b",
            t,
        ):
            return ""
        instrucao_tipo, instrucao_detalhe = _instrucao_capacidade(t)
        if not _texto_pergunta_capacidade(t) and not instrucao_tipo:
            return ""
        leitura_turno = dict(turno or {})
        # Esta porta explica capacidades. Um pedido que o turno canônico
        # autorizou pertence ao roteador/executor e nunca é consumido aqui.
        if leitura_turno.get("autoriza_execucao") is True:
            return ""
        mapa = self.snapshot()
        if instrucao_tipo:
            intent_instrucao = {
                "criar_arquivo": "CREATE_FILE",
                "apagar_arquivo": "DELETE_ITEM",
                "abrir_app": "APP_OPEN",
            }.get(instrucao_tipo, "")
            capacidade = dict(
                (mapa.get("capacidades") or {}).get(intent_instrucao) or {}
            )
            if not bool(capacidade.get("disponivel")):
                return (
                    "Essa habilidade está indisponível nesta instalação agora. "
                    "A pergunta não executou nenhuma ação."
                )
            return falar_instrucao_capacidade(
                instrucao_tipo,
                alvo=instrucao_detalhe,
                contexto=dados_contexto,
            )
        dominios = self.dominios_relevantes(t, turno=leitura_turno)
        pergunta_geral = any(frase in t for frase in _PEDIDO_CAPACIDADES)
        if "corpo_motor" in dominios and not pergunta_geral:
            if mapa["dominios"]["corpo_motor"]["estado"] != "disponivel":
                return "Meu controle dos motores está indisponível agora: preciso de uma sessão recente e firmware com MOTOR1 habilitado."
            modo = ((self._operacional().get("dominios") or {}).get("corpo_motor") or {}).get("companhia") or {}
            estado_modo = " O modo companhia está ativo nesta sessão." if modo.get("ativa") is True else " O modo companhia está desativado agora."
            saude=(((self._operacional().get("dominios") or {}).get("corpo_motor") or {}).get("saude") or {})
            if saude.get("suportado"):
                estado_modo+=" Posso recuperar o controle após reconexão estável do mesmo ESP identificado, sem repetir movimentos interrompidos. Parada ou desativação continuam revogando a retomada."
            if modo.get("recuperacao_pendente"):
                estado_modo+=" O controle está suspenso aguardando recuperar a conexão, sem motores autorizados."
            sensores = ((self._operacional().get("dominios") or {}).get("corpo_motor") or {}).get("sensores") or {}
            if any(trecho in t for trecho in ("sensor", "borda", "obstaculo", "parede", "distancia")):
                if sensores.get("suportado") is not True:
                    return "Não tenho leitura dos sensores disponível nesta conexão. Não posso afirmar que detecto bordas ou obstáculos agora."
                if sensores.get("recente") is not True:
                    return "O firmware oferece sensores, mas as leituras atuais estão indisponíveis ou expiradas. Não posso afirmar que a superfície está segura."
                p = sensores.get("protecao") or {}
                alerta = ("O firmware atual oferece VIGIA1: expresso medo/pavor parada diante de borda e irritação diante de parede. "
                    "Busca de outra direção depende do modo companhia autorizado e tem até quatro tentativas por rodada, com pausa antes de reavaliar. "
                    "Na borda persistente faço no máximo três recuos hesitantes adicionais por episódio; sem superfície confirmada não giro nem avanço. "
                    if sensores.get("alerta_suportado") is True else
                    "Alertas expressivos parada e busca espontânea de parede estão indisponíveis no firmware desta conexão. ")
                return ("Tenho leitura frontal e inferior dianteira pelo VL53L0X. A proteção do ESP interrompe movimento "
                    "quando a borda passa de 13 cm, a leitura inferior é inválida ou um obstáculo está a 10 cm ou menos. "
                    "O reflexo pode recuar e girar por tempo; só avança após novas leituras seguras. "
                    "Não meço o ângulo do giro e não cubro a traseira ou as laterais. "
                    + alerta +
                    f"O risco informado agora é {p.get('risco', 'desconhecido')}, na fase {p.get('fase', 'desconhecida')}. "
                    "A pergunta não iniciou movimento.")
            if modo.get("continuidade_intencao") is True:
                estado_modo += " Acompanho o objetivo corporal entre espera, gesto e acomodação; um novo turno ou tarefa pode interrompê-lo, sem renovar permissão de movimento."
            if modo.get("objetivos_entre_turnos") is True:
                estado_modo += " Posso propor continuar o mesmo objetivo entre turnos por até dois minutos e oito turnos, validando a referência atual sem retomar comandos antigos."
            if modo.get("planejamento_por_historico") is True:
                estado_modo += " Escolho variantes com meu histórico recente e preferências aprendidas para reduzir repetição."
            if modo.get("perfil_corporal") == "rodas_suspensas":
                estado_modo += " O perfil atual é rodas suspensas; a intenção corporal usa minha atividade no PC e emoção causal."
            estado_modo += " O passeio espontâneo está ativo." if modo.get("passeio_ativado") is True else " O passeio espontâneo está desativado agora."
            if modo.get("ativacao_automatica_ao_iniciar") is True:
                estado_modo += " A preferência salva ativa companhia na bancada ao iniciar pela USB."
                estado_modo += ((" O passeio também inicia automaticamente na plataforma de rodas suspensas."
                                if modo.get("perfil_corporal") == "rodas_suspensas" else " O passeio também inicia automaticamente na área com barreiras.") if modo.get("passeio_automatico_ao_iniciar") is True
                                else " O passeio exige ativação própria.")
            if modo.get("perfil_corporal") == "rodas_suspensas":
                olhos = ((self._operacional().get("dominios") or {}).get("rosto_oled") or {}).get("expressao") or {}
                if olhos.get("suportado") is True:
                    estado_modo += " O firmware atual oferece OLHOS2 para coordenar olhar, bip e gesto."
                return ("Posso combinar movimentos contínuos, expressões e reações no perfil de rodas suspensas. "
                        "Cada movimento pode durar até 5 segundos quando o firmware negocia LONGO1; "
                        "uma tarefa no PC pode interromper o passeio. Não tenho sensores de deslocamento."
                        + estado_modo)
            experiencia = ((self._operacional().get("dominios") or {}).get("corpo_motor") or {}).get("experiencia") or {}
            if experiencia.get("origem") == "experiencia_corporal_observada":
                estado_modo += " Pedidos e gestos espontâneos alimentam a mesma experiência corporal; confirmação elétrica não prova deslocamento."
                if experiencia.get("aprendizado_conectado") is True:
                    estado_modo += " Posso aprender com 'gostei desse movimento' ou 'não gostei desse gesto', vinculando a avaliação a uma experiência recente; a preferência não autoriza movimentos."
            return "Posso " + _DESCRICAO_DOMINIO["corpo_motor"] + "." + estado_modo
        if "rosto_oled" in dominios and not pergunta_geral:
            if mapa["dominios"]["rosto_oled"]["estado"] != "disponivel":
                return "Meu rosto no OLED está indisponível agora: preciso detectar um ESP32 compatível e receber uma confirmação recente do firmware."
            descricao = "Posso " + _DESCRICAO_DOMINIO["rosto_oled"] + "."
            som = ((self._operacional().get("dominios") or {}).get("rosto_oled") or {}).get("som") or {}
            descricao += (" O firmware atual oferece SOM1 para os bips." if som.get("suportado") is True
                          else " Os bips estão indisponíveis no firmware conectado agora.")
            if som.get("envio_suportado") is True:
                descricao += " Com ENVIO1, um bip neutro sinaliza comando enviado sem confirmar o efeito; sucesso e falha têm sons distintos."
            expressao = ((self._operacional().get("dominios") or {}).get("rosto_oled") or {}).get("expressao") or {}
            descricao += (" OLHOS2 está disponível: demonstro atenção antes da resposta e acordo/adormeço gradualmente."
                          if expressao.get("suportado") is True else " OLHOS2 está indisponível no firmware atual.")
            return descricao
        if _texto_sobre_feedback_presenca(t):
            estado_personalidade = str(
                (mapa.get("dominios") or {}).get("personalidade", {}).get("estado") or ""
            )
            if estado_personalidade not in {"disponivel", "parcial", "degradado"}:
                return "O aprendizado com feedback de presença está indisponível nesta instalação agora."
            return "Consigo " + _CONTRATO_FEEDBACK_PRESENCA + "."
        if "visao" in dominios and re.search(
            r"\b(?:reag\w*|reac\w*|coment\w*|acompanh\w*|presenca|companhia)\b", t,
        ):
            visao_jogo = dict((mapa.get("capacidades") or {}).get("GAME_VISION") or {})
            if not bool(visao_jogo.get("disponivel")):
                return "A observação visual do jogo está indisponível nesta instalação agora."
            return "Posso " + _CONTRATO_PRESENCA_JOGO + "."
        disponivel = any(
            str((mapa.get("dominios") or {}).get(dominio, {}).get("estado") or "")
            in {"disponivel", "parcial", "degradado"}
            for dominio in dominios
        )
        if not disponivel:
            return "Essa habilidade não está disponível nesta instalação agora."
        capacidades_praticas = _capacidades_praticas(mapa)
        if re.search(
            r"\b(?:voce|laylay|lay)\s+(?:esta|fica|roda|funciona)\s+"
            r"(?:no|dentro\s+do)\s+(?:meu|seu)\s+(?:pc|computador)\b",
            t,
        ):
            if not capacidades_praticas:
                return "Tô rodando aqui no seu computador, mas as habilidades práticas estão indisponíveis agora."
            return falar_identidade_operacional(
                "presenca_local", capacidades_praticas, contexto=contexto,
            )
        if re.search(
            r"\b(?:voce|laylay|lay)\s+(?:e|eh)\s+(?:so|apenas)\s+"
            r"(?:(?:um|uma)\s+)?(?:chatbot|ia|assistente)(?:\s+de\s+texto)?\b|"
            r"\b(?:voce|laylay|lay)\s+(?:so|apenas)\s+"
            r"(?:consegue|pode|sabe)\s+(?:conversar|responder|falar)\b",
            t,
        ):
            if not capacidades_praticas:
                return (
                    "Conversar é a parte disponível agora; minhas habilidades práticas "
                    "estão indisponíveis nesta instalação."
                )
            return falar_identidade_operacional(
                "nao_so_chat", capacidades_praticas, contexto=contexto,
            )
        pergunta_geral = any(frase in t for frase in _PEDIDO_CAPACIDADES)
        if pergunta_geral:
            dominios_vivos = dict(mapa.get("dominios") or {})
            ordem = tuple(_ROTULO_CAPACIDADE_NATURAL)
            contexto_texto = _contexto_conversacional_texto(contexto)
            relacionados = [
                dominio
                for dominio in _dominios_mencionados(contexto_texto)
                if dominio in ordem
                and str(dominios_vivos.get(dominio, {}).get("estado") or "")
                in {"disponivel", "parcial", "degradado"}
            ]
            ordem = tuple(dict.fromkeys([*relacionados, *ordem]))
            itens = [
                _ROTULO_CAPACIDADE_NATURAL[dominio]
                for dominio in ordem
                if str(dominios_vivos.get(dominio, {}).get("estado") or "")
                in {"disponivel", "parcial", "degradado"}
            ]
            if not itens:
                return "Agora minhas habilidades práticas estão indisponíveis, mas ainda consigo conversar com você."
            # Uma pergunta geral pede orientação, não a leitura do catálogo
            # inteiro. Mantemos os domínios ligados ao papo na frente e damos
            # uma amostra curta das demais capacidades.
            rotulos_relacionados = {
                _ROTULO_CAPACIDADE_NATURAL[item]
                for item in relacionados[:2]
            }
            itens_complementares = [
                item for item in itens if item not in rotulos_relacionados
            ]
            principais = itens_complementares[:4] if relacionados else itens[:5]
            return falar_capacidades_gerais(
                principais,
                relacionadas=[
                    _ROTULO_CAPACIDADE_NATURAL[item]
                    for item in relacionados[:2]
                ],
                tem_outras=len(itens) > len(principais),
                contexto=contexto,
            )
        capacidades_vivas = dict(mapa.get("capacidades") or {})

        def capacidade_disponivel(intent: str) -> bool:
            return bool(
                dict(capacidades_vivas.get(intent) or {}).get("disponivel")
            )

        if "arquivos" in dominios and "caminho" in t:
            intent_caminho = (
                "CREATE_FILE" if re.search(r"\b(?:escrev|grav|acrescent|adicion)\w*\b", t)
                else "FILE_READ" if re.search(r"\b(?:ler|leia|leitura)\b", t)
                else "FILE_OPEN_RESULT" if re.search(r"\b(?:abr|abre)\w*\b", t)
                else ""
            )
            if intent_caminho:
                if not capacidade_disponivel(intent_caminho):
                    return "Essa operação de arquivo por caminho está indisponível nesta instalação agora."
                return (
                    "Consigo usar o caminho completo, inclusive com espaços; você pode colocá-lo entre aspas. "
                    "Faça um pedido como 'leia o arquivo' ou 'escreva uma anotação no arquivo', seguido do caminho. "
                    "O executor valida as raízes permitidas e o alvo; só confirmo o resultado observado."
                )

        pede_criar_arquivo = bool(re.search(
            r"\b(?:cri|faz|mont)\w*\b.*\b(?:arquivo|pasta)s?\b|"
            r"\b(?:arquivo|pasta)s?\b.*\b(?:cri|faz|mont)\w*\b",
            t,
        ))
        pede_pesquisar_arquivo = bool(re.search(
            r"\b(?:encontr|procur|busc|localiz|pesquis)\w*\b",
            t,
        ))
        if "arquivos" in dominios and pede_criar_arquivo and pede_pesquisar_arquivo:
            cria = capacidade_disponivel("CREATE_FILE")
            pesquisa = capacidade_disponivel("FILE_SEARCH")
            if cria and pesquisa:
                return falar_instrucao_capacidade(
                    "capacidade_criar_e_pesquisar_arquivos",
                    contexto=dados_contexto,
                )
            if cria:
                return (
                    "Consigo criar arquivos, mas pesquisar localmente está indisponível nesta "
                    "instalação agora. Como foi uma pergunta, não criei nada."
                )
            if pesquisa:
                return (
                    "Consigo pesquisar localmente, mas a criação de arquivos está indisponível "
                    "nesta instalação agora. Como foi uma pergunta, não iniciei a busca."
                )
            return "Criar e pesquisar arquivos estão indisponíveis nesta instalação agora."
        if "arquivos" in dominios and re.search(
            r"\b(?:cri|faz|mont)\w*\b.*\b(?:arquivo|pasta)s?\b|"
            r"\b(?:arquivo|pasta)s?\b.*\b(?:cri|faz|mont)\w*\b",
            t,
        ):
            return (
                "Consigo, sim. Se você me pedir de verdade e disser o nome, eu crio o arquivo "
                "ou a pasta. Como agora você só perguntou, não fiz nada."
            )
        if "arquivos" in dominios and re.search(r"\b(?:apag|exclu|delet|remov)\w*\b", t):
            return (
                "Consigo apagar arquivos, mas não por conta própria. Só quando você fizer "
                "o pedido direto eu confirmo o alvo e envio o arquivo ou a pasta para a lixeira."
            )
        if "arquivos" in dominios and re.search(r"\b(?:encontr|procur|busc|localiz|pesquis)\w*\b", t):
            return (
                "Consigo pesquisar localmente por nome, pasta, conteúdo, tipo, significado e data. "
                "O índice fica só na memória, não envia seus arquivos para a internet e a busca não altera nada. "
                "Depois você pode pedir naturalmente para abrir um dos resultados."
            )
        if "arquivos" in dominios and re.search(
            r"\b(?:renome|mud|troc|alter)\w*\b.*\b(?:nome|tipo|extensao|formato)\b|"
            r"\b(?:extensao|formato)\b.*\b(?:renome|mud|troc|alter)\w*\b",
            t,
        ):
            return (
                "Consigo renomear um arquivo recente e trocar extensões textuais conhecidas, "
                "como .txt por .md. Isso muda o nome e o tipo indicado pela extensão, mas não "
                "converte o conteúdo. O executor confere o caminho de origem e o novo nome antes "
                "de eu confirmar o resultado."
            )
        if ("sistema" in dominios or "navegador" in dominios) and re.search(r"\b(?:fech|encerr)\w*\b", t):
            return "Consigo. Posso fechar o programa, navegador ou aba quando você fizer o pedido direto."
        pede_abrir_programa = bool(re.search(
            r"\b(?:abrir|abre)\b.*\b(?:apps?|aplicativos?|programas?)\b|"
            r"\b(?:abrir|abre)\b(?:\s+(?:o|a|um|uma))?\s+[^,.!?]+",
            t,
        ))
        pede_organizar_janelas = bool(re.search(
            r"\b(?:organiz|posicion|divid)\w*\b",
            t,
        ))
        if "sistema" in dominios and pede_abrir_programa and pede_organizar_janelas:
            abre = capacidade_disponivel("APP_OPEN")
            organiza = capacidade_disponivel("ORGANIZAR_DESKTOP")
            if abre and organiza:
                return falar_instrucao_capacidade(
                    "capacidade_apps_e_janelas",
                    contexto=dados_contexto,
                )
            if abre:
                return (
                    "Consigo abrir programas, mas organizar janelas está indisponível nesta "
                    "instalação agora. A pergunta não abriu nada."
                )
            if organiza:
                return (
                    "Consigo organizar janelas, mas abrir programas está indisponível nesta "
                    "instalação agora. A pergunta não moveu nada."
                )
            return "Abrir programas e organizar janelas estão indisponíveis nesta instalação agora."
        if "sistema" in dominios and re.search(
            r"\b(?:consegue|pode|sabe|e capaz)\b.*\b(?:abrir|abre)\b.*"
            r"\b(?:apps?|aplicativos?|programas?)\b",
            t,
        ):
            return falar_instrucao_capacidade(
                "capacidade_apps",
                contexto=dados_contexto,
            )
        if "navegador" in dominios:
            return (
                "Consigo consultar a aba ativa e as abas abertas, resumir a página atual, abrir sites, "
                "pesquisar, controlar mídia e interagir com controles de página que a habilidade "
                "reconheça. A leitura do "
                "navegador não autoriza uma ação por conta própria, e eu não exponho um comando "
                "arbitrário de página; cada ação real continua passando pelo porteiro e pelo executor."
            )
        if "sistema" in dominios and re.search(
            r"\b(?:organiz|posicion|divid|esquerda|direita|janela)\w*\b", t,
        ):
            return (
                "Consigo organizar as janelas visíveis automaticamente. Nesse modo, priorizo o "
                "programa em foco e combino áudio ativo, uso recente, frequência de uso e tempo "
                "aberto para escolher o secundário. Também posso colocar um aplicativo específico "
                "na esquerda ou na direita. Eu movo somente os lados pedidos e releio a geometria "
                "final antes de dizer que deu certo."
            )
        if "sistema" in dominios:
            return (
                "Consigo mexer em partes do seu computador quando você pede: abrir e fechar "
                "programas, organizar janelas e ajustar o volume, por exemplo. Eu não ajo por "
                "conta própria e só confirmo o que o computador realmente mostrou."
            )
        if "visao" in dominios:
            return (
                "Consigo analisar o item visível no jogo. Eu uso o quadro atual, tento ler nome, "
                "atributos e requisitos, busco evidência externa quando houver identificação "
                "confiável e cruzo tudo com a build e o inventário que conheço daquela sessão. "
                "A captura é transitória, não fica persistida e observar o jogo não autoriza uma "
                "nova análise por conta própria. "
                "Para avaliar um item específico, mantenha o tooltip aberto e o mouse sobre ele; "
                "se a imagem ou a fonte não forem suficientes, eu explico o limite em vez de inventar."
            )
        if "iot" in dominios:
            return "Consigo consultar e controlar os dispositivos inteligentes que estiverem configurados e online."
        if "musica" in dominios:
            return (
                "Consigo buscar e controlar músicas, além de criar, listar, tocar e editar suas playlists. "
                "Também monto curadorias minhas usando apenas suas playlists e o histórico musical "
                "confirmado. Posso mostrar essas seleções e copiar uma faixa para uma playlist sua "
                "quando você pedir; não invento músicas nem reproduzo ou copio algo sozinha."
            )
        if "agenda" in dominios:
            return (
                "Consigo criar, listar e cancelar lembretes e ações agendadas. Se faltar o horário, "
                "eu mantenho uma pendência temporária e você pode completar naturalmente, por exemplo "
                "com '14:30' ou 'em 15 minutos'. Só digo que ficou marcado depois de confirmar a "
                "persistência local; a entrega passa pela central de notificações."
            )
        if "email" in dominios:
            if not capacidade_disponivel("EMAIL_READ"):
                return "Posso trabalhar com rascunhos locais quando o modelo está disponível. Meu acesso à caixa de e-mail está indisponível agora."
            return (
                "Consigo consultar e explicar o corpo dos e-mails da conta principal e continuar perguntas sobre a mensagem selecionada. "
                "Posso criar, revisar, editar e descartar rascunhos locais, responder e encaminhar por rascunho; "
                "o envio e alterações da caixa precisam de confirmação. Editar invalida a revisão anterior. "
                "Posso anexar até cinco arquivos locais permitidos, com 12 MB totais e revalidação antes de enviar. "
                "Ainda não leio o conteúdo dos anexos recebidos, e várias contas ainda não estão disponíveis. "
                "Também reúno avisos de email, agenda, lembretes e alertas internos. "
                "A central prioriza o importante, agrupa repetições e aprende quais categorias devem "
                "interromper, entrar no resumo ou ficar em silêncio."
            )
        if "area_transferencia" in dominios:
            return (
                "Consigo observar localmente quando você copia um conteúdo relevante. Se for uma mensagem de erro, "
                "posso oferecer ajuda e, quando você aceitar, pesquisar internamente, analisar e resumir a causa sem "
                "abrir uma aba. Também consigo ler, resumir, corrigir, explicar e traduzir texto copiado, além de abrir "
                "ou pesquisar links. Não guardo o texto automaticamente e só substituo o conteúdo com confirmação."
            )
        if "caixa_entrada" in dominios:
            return (
                "Consigo guardar e classificar ideias, tarefas, pensamentos, links e notas na sua caixa de entrada. "
                "Também consigo resumir uma discussão, separando sua ideia das minhas sugestões, listar o que foi "
                "anotado e transformar uma nota em lembrete; alterações pedem confirmação."
            )
        if "pessoas" in dominios:
            return (
                "Consigo lembrar pessoas e relações que você me contar explicitamente, consultar fatos "
                "confirmados sobre elas e corrigir uma relação antiga sem manter as duas como verdade. "
                "Esses perfis ficam locais, não são enviados para fora e eu só os esqueço após sua confirmação."
            )
        if "memoria" in dominios:
            return (
                "Consigo consultar o que aprendi sobre você na memória persistente local. Eu separo "
                "o que você confirmou diretamente de padrões que só amadureceram com evidências e "
                "de registros antigos; hipóteses fracas, contraditas ou não verificadas não viram "
                "fatos na resposta. O contexto desta conversa é temporário e não é automaticamente "
                "uma memória durável. Consultar essa memória é somente leitura e não autoriza ações."
            )
        if "cooperacao" in dominios:
            return (
                "Consigo combinar habilidades por um único plano. No primeiro fluxo ativo, uso uma "
                "referência temporária ao texto copiado para criar um arquivo, sem guardar o texto no "
                "plano, e só digo que terminou depois de reler o arquivo. Cada etapa tem dependências, "
                "orçamento de tempo, cancelamento, evidência e uma política segura para falhas parciais. "
                "Sobrescrita pede confirmação."
            )
        if "avatar" in dominios:
            estado_avatar = str(
                (mapa.get("dominios") or {}).get("avatar", {}).get("estado") or ""
            )
            if estado_avatar not in {"disponivel", "parcial", "degradado"}:
                return "O avatar visual está indisponível nesta instalação agora."
            return (
                "Tenho um avatar visual com emoções e animações. Posso ajudar a imaginar skins e designs; "
                "uma mudança nos PNGs ou no código só conta como feita depois que o executor confirmar. "
                + _CONTRATO_EXPRESSAO_AVATAR
            )
        if "personalidade" in dominios:
            return (
                "Consigo perceber sinais emocionais e expressar uma reação quando há causa e "
                "evidência rastreáveis. Distingo fato observado, inferência, leitura social e "
                "preferência aprendida; se a causa não for válida, contenho a reação. Uma emoção "
                "não autoriza ações nem muda o resultado que uma habilidade realmente confirmou."
                " Posso admitir uma violação da proposta original comprovada no turno vigente; "
                "isso não confirma efeito externo nem reparo concluído. "
                "Uma repetição com estado já confirmado pode receber uma recusa verbal curta; "
                "não recuso um pedido novo só por humor. Se você pedir explicitamente "
                "para alternar a repetição como algo opcional, uma causa recente e "
                "comprovada pode me levar a perguntar uma vez antes de executar. "
                "Urgência, segurança e acessibilidade seguem o executor normalmente. "
                + _CONTRATO_PREFERENCIA_HUMOR + " " + _CONTRATO_EXPRESSAO_SOLICITADA
            )
        if "conversa" in dominios:
            return (
                "Consigo conversar, explicar e raciocinar com você usando o modelo de linguagem "
                "disponível. Também mantenho o contexto da "
                "conversa separado das lembranças duráveis: conversar comigo não salva tudo nem "
                "autoriza uma ação no computador."
            )
        return "Consigo, desde que essa habilidade esteja configurada e você faça o pedido de execução diretamente."

    def contexto_para_prompt(
        self,
        texto: str,
        *,
        turno: Mapping[str, Any] | None = None,
    ) -> str:
        mapa = self.snapshot()
        dominios = dict(mapa.get("dominios") or {})
        relevantes = self.dominios_relevantes(texto, turno=turno)
        linhas = [
            "--- HABILIDADES REAIS RELEVANTES ---",
            "Este mapa informa capacidade, não autoriza ações. Só declare execução após o roteador/executor confirmar.",
        ]
        for dominio in relevantes:
            registro = dict(dominios.get(dominio) or {})
            estado = str(registro.get("estado") or "indisponivel")
            linhas.append(f"- {dominio} [{estado}]: {registro.get('descricao') or ''}.")
        indisponiveis = [
            item for item in mapa.get("capacidades", {}).values()
            if item.get("dominio") in relevantes and not item.get("disponivel")
        ]
        if indisponiveis:
            nomes = ", ".join(str(item.get("intent")) for item in indisponiveis[:8])
            linhas.append(f"Indisponíveis agora: {nomes}. Não prometa que foram executadas.")
        linhas.append(
            "Pedidos práticos continuam sendo decididos pelo porteiro e pelos roteadores; não invente comandos, resultados ou acesso externo."
        )
        return "\n".join(linhas)

    def diagnostico(self) -> dict[str, Any]:
        mapa = self.snapshot()
        dominios = dict(mapa.get("dominios") or {})
        return {
            "catalogadas": len(mapa.get("capacidades") or {}),
            "dominios": len(dominios),
            "disponiveis": sum(
                bool(item.get("disponivel")) for item in mapa.get("capacidades", {}).values()
            ),
            "indisponiveis": sum(
                not bool(item.get("disponivel")) for item in mapa.get("capacidades", {}).values()
            ),
            "parciais": sorted(nome for nome, item in dominios.items() if item.get("estado") == "parcial"),
            "observacoes_ativas": int(mapa.get("observacoes_ativas") or 0),
            "autoriza_execucao": False,
        }


def criar_mapa_habilidades_runtime(**kwargs: Any) -> MapaHabilidadesRuntime:
    return MapaHabilidadesRuntime(**kwargs)
