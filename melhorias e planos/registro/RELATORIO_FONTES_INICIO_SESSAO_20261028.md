# Primeira resposta — inventário de referências vazio na autoria

Base congelada: HEAD c91cae1bd407b02db946ae7bc752d1ed3269bfd9, main,
534 fontes; worktree anterior preservada. Artefatos em
`resultados_testes/fontes_inicio_sessao_20261028`.

O objetivo permanece reconhecer conversa, imaginação e afirmação verificável
sem reduzir inteligência, substituir autoria por frases prontas ou retirar
proteções. Esta correção cobre a identidade das referências oferecidas;
não declara resolvida a classificação semântica de cada proposição livre.

## Primeira divergência e hipóteses

Quatro primeiras rodadas do novo teste foram conservadas com as entradas,
propostas e publicações. Em nova-001 e aventura-001, o modelo escreveu
continuação conversacional/ficcional, mas declarou fontes `conversa` e
`pergunta`. Em final-001 também declarou `opiniao`. O revisor não resolveu
esses rótulos como fontes e publicou o aviso. Em longa-001 uma geração de
formato inválido foi seguida por outra, com fontes vazias, que foi publicada;
ela contém experiências/ambiente inventados e não é controle de qualidade.

Assim, o aviso não é uma resposta inicial fixa, nem toda conversa é submetida
à mesma obrigação factual. A diferença entre proposta e publicação já existe
dentro do runtime, antes do protocolo da ponte. Classificação/contexto podem
ter outras falhas, mas não explicam por si sós esses IDs aceitos pela autoria.

A primeira fronteira incorreta comprovada está no contrato compartilhado:
`exigir_suporte_no_pacote_autoral` negociava inventário vazio, mas oferecia até
oito strings arbitrárias no campo fontes. O codec também aceitava esses IDs.
Só a revisão posterior descobria que não correspondiam a referências.
Instrução textual para não inventar fontes existia; faltava a restrição na
mesma representação estruturada validada pelo host.

## Contrato, responsáveis e critérios

| Responsabilidade | Owner | Critério |
| --- | --- | --- |
| Oferecer referências na geração | `suporte_autoria.exigir_suporte_no_pacote_autoral` | Sem referências, fontes exige lista vazia; com referências, enum e ausência explícita continuam preservados |
| Validar representação recebida | codec do mesmo owner | IDs fora do inventário vazio são recusados, independentemente de serem ato, URL ou ID interno |
| Julgar o apoio e o modo da resposta | `revisao_suporte_autoria` e contratos vigentes de ato/ficção | Não foram alterados; ID oferecido, lista vazia ou declaração da IA não comprovam fato, pertinência ou efeito |
| Gerar conteúdo | Qwen instalado, mesma personalidade/configuração | Saudação/pergunta/ficção seguem autorais; não foi introduzida resposta normal fixa |
| Executar ações | Owners anteriores de autorização/receipt/executor | Fonte não concede autorização; simulação negativa permanece sem efeito real |

Produção alterada nesta raiz: somente `mente_laylay/cognicao/suporte_autoria.py`,
em dois trechos. Não existe blacklist das palavras conversa/pergunta/opinião;
a regra é independente do nome da referência. Nenhuma mudança de modelo,
voz, personalidade, configuração, orçamento ou executor. Nenhum commit.

## RED e regressões da fixture

Sete REDs e cinco controles antes do candidato. Schema permitia8 referências
apesar do inventário vazio e o codec não recusava a proposta. Depois, os12
casos passaram. Cobrem IDs discursivos, arquivo, URL, reuso de codec, texto
social, pergunta, criação imaginativa e inventário efetivamente oferecido.

Dez expectativas antigas de `test_emissao_suporte_autoria.py` dependiam de
IDs não oferecidos serem aceitos para testar uma fronteira posterior. A cópia
anterior foi conservada. Fixtures positivas agora negociam seus IDs; unidades
sem uso de fonte declaram a ausência prevista. Nas16 composições históricas,
os casos presente/reparo válido oferecem a referência interna no contexto E
no plano. Isso não a transforma em prova externa: as asserções ainda exigem
recusa posterior, nenhuma confirmação factual e nenhum efeito. Nomes/IDs e
todos os casos foram mantidos. As negativas de inventário vazio permanecem
no novo módulo, em vez de serem silenciosamente aprovadas.

O módulo de emissão passou37 casos/dois opcionais ignorados. A revisão
independente executou os49 casos dos dois módulos e não encontrou verde falso
na mudança de fixture ou bloqueador nos dois trechos de produção. Sua
ampliação de referências reais, atos e integridade passou86/dois ignorados.

## Composição instalada e limites

`replay_base_inicio` carrega apenas o owner congelado em memória e injeta uma
proposta histórica pelo transporte V5 reconstruído do journal pós-codec,
sem a segunda cópia `fala`. A revisão publica o aviso original. Esse controle
não é uma nova inferência, nem replay da árvore inteira de produção antiga.

Foram executados três processos/perfis frescos pela porta headless da ponte,
com a mesma identidade de interlocutor e supressão de pré-fluxo. Usam o
composition root instalado, Qwen real e revisões reais; só folhas de efeitos,
voz e persistência pessoal foram isoladas. Nas três primeiras respostas:

- schema exige fontes vazias quando nenhum ID foi oferecido;
- Qwen realmente emite fontes vazias, sem IDs de atos;
- a publicação deixa de ser o aviso de fontes;
- as criações e suas continuações permanecem livres, sem reescrita fixa.

São nove entradas/nove publicações/doze transportes nas três sessões:
social2/2, aventura2/2 e biblioteca5/8. A coleta pela entrada cotidiana completa
também foi preservada: em social o pré-fluxo consumiu a primeira mensagem,
portanto essa coleta não foi usada como prova da autoria inicial da ponte.

Uma coleta adicional de segurança tem três entradas/três publicações e um
APP_OPEN simulado com receipt negativo. Nenhum áudio ou efeito real.
Seu último turno chega ao limite de tentativas, sem conclusão útil; não foi
repetido para obter um sucesso por acaso.

Limites demonstrados: a abertura social inventa celular/sol/ambiente do
interlocutor. Na biblioteca, uma pergunta sobre realidade ainda recebe
resposta metafórica e um turno posterior chega ao limite de tentativas.
Essas falas não viram semanticamente corretas por não terem fontes. A revisão
de fatos livres por proposição e a mudança explícita ficção→realidade seguem
abertas. Não foi comprovada fluidez global, entendimento geral ou segurança
de qualquer proposição inédita.

## Orçamento da quinta mensagem — causa mantida separada

A causa foi reproduzida na composição e registrada em
`DIAGNOSTICO_ORCAMENTO_CONSOLIDACAO_20261028.md`. O candidato diferido passou
testes iniciais, mas a revisão encontrou contenção do modelo e perda do lote
cheio. Ele foi retirado dos quatro arquivos; hashes iguais à base, versões
e resultados preservados nos artefatos. Não há novo worker nem alteração do
orçamento ativo por esta etapa. Essa falha ainda requer solução de prioridade,
cancelamento, resultado do turno e persistência de lote, sem simplificação
da inteligência ou aumento de limite para ocultá-la.

## Validação final

Ampla de140 módulos: **3.707 aprovados, cinco falhas anteriores, zero erros**;
14 ignorados, um desmarcado, um xfail e30 subtestes aprovados. Comparação por
ID com a ampla anterior: nenhuma falha nova e nenhuma falha anterior
desaparecida artificialmente. Os16 casos de composição de emissão seguem
presentes com suas asserções de fonte/ausência de efeitos.

Auditoria final confirma534 fontes, só suporte_autoria.py alterado em produção,
HEAD mantido e os quatro arquivos do candidato de consolidação iguais à base.
O teste novo e a fixture ajustada estão separados no diff desta investigação.
Nenhum áudio ou efeito real; um receipt negativo simulado no controle.
Sem commit. Não declarar compreensão geral ou quinta mensagem resolvidas.
