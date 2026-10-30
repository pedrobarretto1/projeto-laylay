# Opinião concreta e correção de assunto — 25/10/2026

## Continuação do mesmo contrato: pergunta pessoal não é pesquisa sobre “Favorito”

Base congelada: HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch
`main`, worktree suja preservada. Estado inicial e hashes de 530 fontes em
`resultados_testes/dialogo_jogos_musica_20261025/baseline.json`. Cópias anteriores,
REDs, candidatos descartados e coletas foram preservados nessa pasta. Nenhum
commit, troca de modelo/voz ou alteração de configuração.

O log de Pedro trouxe uma pergunta sobre jogo favorito respondida com um aviso
de conferência de citações. A reprodução atual não repetiu a frase exata: antes
da autoria, tentou pesquisar uma entidade chamada **Favorito** e terminou em
limite de fontes. A primeira divergência está no leitor compartilhado: reconhecia
`você gosta de indie?`, mas não `voce tem um jogo favorito?`. O mesmo owner não
lia a moldura `to so perguntando se ...` nem o espaço deslocado de `d emusica`.

Falsificações: não é uma exigência factual legítima do gosto; a pergunta pessoal
não pede características de um título. Também não é falha geral do transporte:
as coletas online obtiveram HTTP 200 e o caminho polar já admitia a posição
subjetiva. Houve uma coleta intermediária com o servidor Ollama desligado,
preservada em `candidato_dialogo`; ela não valida o candidato. O mesmo serviço
local foi iniciado, sem trocar o modelo configurado `qwen3:4b-instruct`.

Contrato e responsáveis:

| Decisão | Owner | Critério de validação |
| --- | --- | --- |
| Ler a pergunta subjetiva integral e sua perspectiva | `referencias_linguagem.consulta_opiniao_propria` | Pergunta própria e variações entram; terceiro, citação e ato operacional adicional não são absorvidos |
| Impedir que referência incidental vire tema de pesquisa | `fundamentacao_factual.extrair_tema_fundamentacao` | Reutiliza o mesmo leitor antes do retrato; “Favorito” contextual não provoca pesquisa |
| Negociar e conferir a posição autoral | `opiniao_autoral` | Uma resposta direta, vinculada ao turno, sem causa, experiência, capacidade ou autoridade inventadas |
| Conferir fatos acrescentados | Revisor compartilhado existente | Nenhuma dispensa global da conferência; proposta da IA continua sem poder factual |

O vocabulário de categorias é nominal, compartilhado entre leitura e autoria,
com flexão de artigo/plural; não é catálogo de obras nem lista de preferências.
O deslocamento da preposição só é recuperado quando o operando reconstruído
tem tipo nominal conhecido ou gênero musical do léxico já existente.
`d eminem` continua ambíguo, sem correção cega. A moldura de esclarecimento é
integral; não captura uma pergunta seguida de outra instrução.

### Hipótese descartada: nomear livremente um título

Um candidato permitiu nomeação subjetiva limitada. A revisão encontrou primeiro
coordenação de orações no slot e um limite de tamanho divergente. Delimitar o
nome resolveu a separação textual, mas a composição mostrou o limite conceitual:
a IA propôs títulos sem identidade/categoria fundamentadas. Publicar “meu filme
favorito é ...” implica essa categoria; aspas e `prova_factual=False` não a
comprovam. Quatro REDs adicionais reproduzem a aceitação indevida, inclusive
quando a fala livre já havia sido publicada. Publicação não qualifica o alvo.

Esse candidato foi **removido**, não considerado encerramento. A diferença está
em `candidato_nomeacao_descartado.diff`; coletas intermediárias não são prova do
estado final. Os testes positivos passaram a exigir o contrato mais restrito,
com negativos que impedem voltar à nomeação sem fundamento. Não se enfraqueceu
a rejeição de causa, experiência ou capacidades.

Sem inventário de alvos fundamentados, a resposta agora é natural e específica:
`Ainda não escolhi um jogo favorito.` Para gosto de categoria, a autoria pode
responder `Eu gosto de jogos.` ou `Eu gosto de música.` conforme o objeto lido.
Não escolhemos um título fixo pelo host nem transformamos geração anterior em
fonte factual. Nomear favoritos concretos no futuro exige reutilizar o owner
de identidade/categoria, separadamente da escolha subjetiva.

### Provas finais e limites

`test_perguntas_gosto_conversa.py` cobre o texto de Pedro, outros domínios,
negação de fontes propostas, turno estrangeiro, continuidade após explicação e
recusa de nomes sem alvo fundamentado. O foco conjunto tem **221 aprovados**,
incluindo as raízes de ato atual e voz, que possuem relatórios separados.

A coleta final `conversa_sem_titulos_propostos` usa a composição instalada,
Ollama/Qwen reais, persistência isolada gravada/relida e 18 turnos contínuos.
Perguntas de gosto/favorito/esclarecimento/correção foram revisadas como
`opiniao_autoral_vinculada`, sem avisos de citações, pesquisa obrigatória ou
limite de tentativas nesses turnos. A fala e a declaração permanecem vinculadas.
Modelo não foi trocado; não houve voz ou ação externa. Controle separado de
três turnos em `seguranca_final_atual` preserva receipt negativo da ação simulada.

Regressão ampla em **118 módulos**: **2.943 aprovados**, nove falhas, 44 erros,
14 ignorados, um desmarcado e 30 subtestes aprovados. A comparação confirmou
exatamente os mesmos IDs das nove falhas e 44 erros da etapa anterior: comando
natural antigo da Calculadora, expectativas antigas de pacote/tokens e fixture
que serializa `PerspectivaEnunciador`. Não foram corrigidos nem reclassificados.
Comparação, hashes e diffs separados constam de `manifesto.json`,
`comparacao_regressao.json` e `auditar.py`. A auditoria final passou, incluindo
20 HTTP 200 nos 18 turnos e fontes sem drift. Não declarar suíte global verde.

Continuam abertos: excesso técnico em saudações/bem-estar; sentido do verbo
`importante` no relato (não assumir “portando”); adequação de explicações livres;
preferências duráveis e nomeação com identidade/categoria fundamentadas. O
relato foi retomado sem saudação antiga, mas o modelo ainda o interpreta como
“curtir” o jogo. Isso não comprova compreensão do projeto de adaptação.

Produção desta continuação: `referencias_linguagem.py`, `opiniao_autoral.py`,
`fundamentacao_factual.py`. O candidato no wrapper `suporte_autoria.py` foi
retirado; revisão factual, normalização, executores e composição permaneceram
como estavam no início desta etapa. F1/C5/C7/AUT não foram fundidos ou encerrados.

## Pedido, base e limites

Pedro autorizou continuar a correção de respostas vagas, justificativas
inventadas sobre gostos e falhas ao corrigir o assunto. Os testes permanecem
sem voz e sem efeitos reais. HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`,
branch `main`, worktree suja preservada. Nenhum commit, shutdown, troca de
modelo, voz ou configuração. A mudança paralela do hotspot não pertence a esta
investigação. Não reabrir ou fundir as raízes históricas F1/C5/C7/AUT.

Estado inicial, hashes de 528 fontes e cópias dos oito owners anteriores em
`resultados_testes/opiniao_concreta_20261025/`. O módulo autoral novo eleva
o inventário a 529 fontes. Coletas anteriores não foram regravadas com o
candidato novo. `fontes_candidato1` e `fontes_revisao` preservam as fronteiras
intermediárias que receberam correções de validação.

## Cadeia causal demonstrada

### Pergunta de preferência não é pergunta factual genérica

`qual o seu estilo musical?` chega como pergunta sem autoridade, mas o leitor
canônico não a reconhece como opinião: a forma nominal exigia favorito/preferido.
O contrato então emite `resposta_direta` sem o ato subjetivo específico.
`qual é seu gênero musical?` reproduz a mesma perda; não é uma frase única.

### Forma de uma justificativa não comprova seu apoio

Para `voce gosta de indie?`, a pergunta já chegava como opinião, mas a revisão
aceitava `Gosto de música indie porque é o que me faz ficar mais próxima de você.`
A contagem de termos e o conector causal serviam como substitutos de critério
concreto. Nenhuma fonte comprovava essa causa. Já a resposta suficiente
`Eu gosto de indie.` recebia `opiniao_sem_criterio_concreto`, incentivando uma
explicação adicional que a pergunta não havia exigido.

Portanto, acrescentar mais exemplos de concretude ao prompt não repara a
admissão: o contrato precisava distinguir declaração subjetiva de alegação
factual/causal. Opinião da IA continua proposta autoral, sem prova de sentimento,
experiência, memória, capacidade ou efeito.

### Correção de assunto perde-se pela contração

`estou falando de musica` era classificado como correção, mas
`estou falando da musica` como conversa. A diferença está antes da geração.
O leitor canônico de retificação nominal agora identifica o objeto através de
de/do/da/dos/das, preservando pessoa e ausência de autoridade. Não transforma
o assunto corrigido em instrução para tocar música ou executar outra ação.

## Falsificações e REDs

`diagnostico_antes.json` registra classificação, atos, obrigações e revisão dos
cinco controles. O prompt de personalidade já exigia concretude e gosto sem
experiência inventada: não era falta dessa instrução. Nas coletas anteriores,
HTTP 200 e publicação da fala existiam; não era indisponibilidade do modelo nem
perda de histórico. O placeholder histórico e a perda do esclarecimento composto
já tinham candidatos próprios e não foram usados como nova explicação.

O teste canônico registrou **17 falhas e sete controles aprovados** antes de
alterar produção. As falhas atingiram as fronteiras esperadas, não imports.
Em seguida foram demonstradas cinco bordas adicionais: correção exata em
programação/software/bebidas, mesma decisão na revisão direta e enum nativo
adulterado. Acentos no objeto também precisaram ser preservados; normalização
estrutural não pode virar alteração da entidade da resposta.

### Composição: revisão factual ainda tratava opinião entregue como característica externa

A primeira conversa de 15 turnos não terminou GREEN. No turno 14, após
`Eu não gosto de jazz.`, o pedido `estou falando da música` gerou fonte e enum
corretos, e o Qwen devolveu a realização correta. A revisão factual, anterior
à de qualidade, rejeitou o nome jazz como característica externa sem fonte e
trocou o texto por contingência. O esclarecimento seguinte herdou essa falha.
Isso não foi contado como duas raízes novas nem como sucesso do diálogo.

`vizinhos_final/` preserva essa coleta. Três REDs causais com jazz/rock/samba
confirmaram a fronteira, e uma causa acrescentada permaneceu corretamente
recusada. O primeiro arquivo `factual_red.xml` falhou por nome errado da API no
teste e não é prova causal; `factual_red_causal.xml` usa `verificar_fala_turno`
e alcança a revisão real. Nenhum teste foi enfraquecido para esconder a falha.

O mesmo owner autoral agora chega à revisão factual pelo plano atual.
Somente uma realização integral já conferida preserva seu caráter subjetivo;
primeira pessoa genérica, causa, característica, turno divergente, comandos ou
fonte expirada não recebem a exceção. As demais guardas do turno continuam.
Produção adicional necessária: `fundamentacao_factual.py` e o wiring em
`plano_turno.py`. Ambos foram copiados depois de conferir seus hashes com o
baseline original. Não remover a proteção contra características inventadas.

## Contrato e owners

- `referencias_linguagem`: lê a lacuna de opinião simples e o objeto da
  retificação, sem decidir verdade, gosto ou execução. Nomes copiados devem ser
  literais; referências pessoais, possessivos, dêiticos e alternativas extras
  ficam fora desse recorte até haver resolução própria.
- `normalizacao_linguagem` e `modalidade_turno`: reutilizam os leitores
  canônicos, preservando o caráter subjetivo e corretivo sem conceder autoridade.
- `memoria_pessoas`: expõe seu léxico já existente de gêneros; não passa o gosto
  do usuário para a Laylay nem fornece uma preferência pessoal à autora.
- `opiniao_autoral`: define snapshot nativo efêmero ligado a texto, turno e
  perspectiva. Categoria musical conhecida, gosto polar nominal simples e
  escolha binária explícita possuem realizações concretas. O modelo pode escolher
  sua posição; o host confere apenas o ato, o alvo e sua continuidade.
- `contrato_fala`: instala esse contrato só sem comandos, execução, evento,
  metalinguagem ou outro owner histórico. Não substitui revisões de alegações,
  receipts ou explicações de efeitos.
- `contexto_resposta_ia`: negocia a representação na primeira autoria, antes
  de gastar o orçamento com prosa livre inválida. Reutiliza o wrapper canônico
  `autoria_com_suporte_v2`, que conserva enum e ausência de comandos.
- `qualidade_comunicacao` e `validacao_contrato_fala`: consultam a mesma
  decisão. Uma preferência simples não exige uma causa inventada; prosa adicional
  fora do ato contratado é recusada. O reparo usa o mesmo pacote da autoria.
- `fundamentacao_factual` e `plano_turno`: passam o plano vigente e reutilizam
  a conferência integral da opinião antes de classificá-la como fato externo.
  Sem essa integração, um GREEN na qualidade era compensado por outro RED.

Uma opinião entregue pode ser retomada pelo registro de fala canônico e por
`ReferenciaFalaConsulta`, com identidade e TTL original. `ultima_resposta`
isolada não é fonte dessa retomada. Só a declaração integral da gramática
coberta pode ser esclarecida; uma cláusula causal livre não é absorvida como
se fosse opinião simples. A retificação conserva um objeto literal ou uma
categoria musical reconhecida pelo léxico, sem reclassificar entidades pela IA.

O tipo nativo sozinho também não basta: o consumidor regenera as opções da
pergunta e revalida modo, texto, turno, categoria e vínculo à publicação.
Não há gênero fixado no código nem preferência durável criada. A escolha
`Não tenho um estilo musical preferido.` é legítima; não significa incapacidade
de conversar, perceber áudio ou utilizar memória.

## Revisão independente

A revisão somente leitura encontrou quatro defeitos reais no candidato:
copiar mim/você/possessivos invertia perspectiva; o leitor da publicação não
reconhecia a própria correção em outros assuntos; o não acentuado não recebia
o mesmo contrato; três alternativas viravam uma escolha binária vaga.

Todos foram reproduzidos antes dos ajustes. A correção reutiliza o detector
canônico de referência contextual, recusa operandos pessoais não resolvidos,
preserva acentos e fecha o conjunto entre produção e leitura da própria fala.
Não foi criado um reescritor privado de pessoa. Reavaliação independente:
dez testes aprovados, nenhum novo achado acionável nesses deltas. O teste novo
completo soma 49 casos, incluindo factory instalada com cinco turnos, fonte
estrangeira/expirada, enum alterado, citação, terceiro, comando e troca de assunto.

Após o RED de composição factual, o módulo soma 53 casos. A revisão adicional
aprovou 80 testes sem a factory e verificou controles de causa, fato externo,
plano ausente/incompatível, autoridade, comandos e fonte expirada. Não encontrou
isenção factual genérica. A factory e as coletas finais ficaram com a execução
principal para conferir toda a composição.

## Provas na composição instalada

As coletas usam a factory de `laylay.py`, interpretador real, preparador,
transporte local Qwen, autoria, revisão e publicação textual. A persistência é
isolada e os adaptadores de voz/efeitos são barrados. O executor real não é
invocado. A pesquisa contextual permanece no modo desativado já existente
nessas sondas; nenhuma conclusão depende de pesquisa ou de fatos musicais.

`auditar.py` confere, por turno, resposta única, enum efetivamente transportado,
ausência de comandos, uma geração HTTP 200 e revisão final sem prova factual,
semântica ou autoridade. Há transcrições completas nas pastas das coletas.
As observações abaixo não são prova da sessão desktop aberta ter recarregado
o código, nem de entrega de voz.

No candidato integrado, o diálogo original de cinco turnos manteve respostas
diretas e o vínculo de indie nos esclarecimentos/correção. A conversa de 15
turnos repetiu o contrato em programação, Windows/Linux, chá/café, indie e jazz.
A falha anterior no turno 14 não reapareceu: a opinião sobre jazz foi preservada
na correção e no esclarecimento seguinte. As duas coletas finais somam **20
turnos, 20 publicações e 20 HTTP 200**, sem tentativas adicionais de autoria,
sem voz, sem executor e sem alteração das 529 fontes durante cada coleta.

Exemplos observados (escolhas da autora, não preferências configuradas):

- Estilo musical → `Não tenho um estilo musical preferido.`
- “como assim? você não tem nenhum em específico?” →
  `Quis dizer que não tenho um estilo musical preferido.`
- “estou falando da música”, após opinião sobre indie →
  `Sim, estou falando de música: eu não gosto de indie.`
- Correção sobre jazz → `Sim, estou falando de música: eu não gosto de jazz.`

A suíte focada final passou com **394 aprovados e um ignorado**, incluindo
fundamentação factual e os owners históricos/contextuais vizinhos. A anotação
de retorno foi incluída antes dessas coletas e da última regressão. Não houve
alteração de corpo de função depois das validações integradas.

Regressão integrada em **101 módulos distintos**: **2.534 aprovados, nove
falhas, 44 erros, 14 ignorados, um desmarcado e 30 subtestes aprovados**.
`comparacao_regressao.json` compara os IDs, sem apagar casos: as nove falhas
e os 44 erros são exatamente os mesmos do baseline anterior. As falhas são
o comando de calculadora já conhecido e oito expectativas antigas de pacote/
tokens; os 44 erros compartilham a fixture anterior de serialização de
`PerspectivaEnunciador`. A contraprova anterior dessa fixture está preservada
na etapa de categoria. Os nomes completos de todos os casos estão na comparação
e no log. A suíte ampla continua RED; não tratá-la como aprovação global.

`entrega.json` sela os hashes dos **11 arquivos de produção deste candidato**,
as métricas finais e os limites. O diff `candidato_contra_base.patch` usa as
cópias da worktree inicial, incluindo os candidatos antigos que já existiam;
não atribui o diff acumulado do HEAD inteiro a esta correção.

## Critérios e fronteiras que continuam abertas

Critérios deste recorte: resposta direta à lacuna subjetiva; nenhuma causa,
experiência ou incapacidade acrescentada; correção preserva o assunto;
esclarecimento preserva a declaração realmente publicada; fonte inválida ou
alvo não resolvido não se autovalida; nenhuma opinião autoriza efeitos.

Isso não é um verificador universal de prosa. Permanecem fora do recorte:
justificativas causais livres solicitadas pelo usuário, categorias de opinião
sem léxico/catálogo, mais de duas alternativas, referência pessoal não resolvida,
paráfrases arbitrárias, preferência durável e estabilidade depois de qualquer
quantidade de distratores. A redução a uma posição curta é deliberada para
essas perguntas simples; explicações mais ricas exigem apoio próprio, não uma
causa preenchida pelo modelo.

Clipboard, resumos diários e timeout histórico não foram corrigidos nesta raiz.
Não apagar essas pendências porque não reapareceram no diálogo protegido.
Validar o recorte não encerra compreensão ou coerência geral da Laylay.
