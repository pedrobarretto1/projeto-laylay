# C7/C5 — escopo da revisão de planos relatados, 24/10/2026

## Resultado e alcance

Corrigido um bloqueio demonstrado no contrato compartilhado de revisão factual:
a cópula que destaca um participante de um plano futuro era usada como sinal de
uma propriedade factual do objeto mencionado. A revisão substituía a resposta
sobre quem levaria um livro por desconhecimento sobre uma suposta obra.

Produção alterada somente em `mente_laylay/cognicao/fundamentacao_factual.py`.
Não há condição por Bia, Azul, turno 18, livro ou frase do roteiro. O recorte é
gramatical: foco nominal, cópula e perífrase prospectiva com infinitivo. Serve
ao revisor comum de todas as habilidades; testes incluem livro, jogo,
equipamento, caderno, arquivo e aplicativo.

Isso **não certifica o apoio semântico da prosa livre**. A mudança retira um
sinal factual indevido; não confirma o participante, resolve anáforas, valida
uma previsão, autoriza executar o plano ou produz receipt. O histórico continua
sendo relato do usuário, não prova externa. C5/P01 e compreensão geral permanecem
abertos.

## Base e cadeia causal

Branch `main`, HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`.
Worktree previamente suja preservada. `resultados_testes/revisao_historico_20261024/baseline.json`
registra status e hashes de 527 fontes; `fontes_antes` preserva a base desta
tarefa. O diff contra HEAD também contém alterações anteriores, que não são
este candidato. Nenhum commit criado.

Cadeia histórica preservada:

1. Usuário relata encontro com Bia e, no turno seguinte, que ela levará um
   livro azul; mensagens literais chegam ao plano e ao envio.
2. A resposta real recuperada era: `De acordo com o histórico, a Bia é quem
   vai levar o livro azul.` Não tinha comando nem confirmação de efeito.
3. `_frase_especifica_sem_base` combinava o tema `Azul` em qualquer posição
   com uma cópula em qualquer posição da frase. Não distinguia o foco Bia do
   objeto livro. A cópula de foco acionava `alegacao_especifica_sem_fonte`.
4. A entrega virava `Sobre Azul, eu não encontrei uma base confiável...`.

A menção descritiva transformada em título é uma fronteira anterior ainda
conhecida; não foi corrigida nem absorvida por esta raiz. O controle com um
jogo explicitamente nomeado, `Espiral`, reproduz o mesmo bloqueio com tema
corretamente nomeado. Portanto essa falha de extração não é necessária para o
defeito independente no revisor.

Falsificações:

- Falta de histórico não explica este bloqueio: os enunciados constam nas
  fontes canônicas, no plano e nos pacotes enviados, inclusive na composição.
- A geração errada não é necessária: mesma resposta HTTP gravada, mesmas
  entradas e mesma factory; trocar somente o owner congelado reproduz a
  substituição, e o candidato preserva a resposta.
- O problema não exige a palavra Azul ou uma cor: título explícito de jogo e
  referências a outros recursos reproduzem o RED.
- Remover a cópula de toda clivagem seria inseguro: o primeiro candidato
  liberou `escreveu`, `desenhou` e `dirige` sem fonte. Foi rejeitado; código e
  contraprovas estão em `candidato_amplo_rejeitado.*`. Não foi mantida uma lista
  de verbos para salvar esse candidato.

## Contrato aplicado

O revisor reconhece as ordens `X é quem/que vai V`, `é X quem/que vai V` e
`quem vai V é X`, no recorte de ir no presente seguido de infinitivo. Identifica
o foco literal X e mascara **somente a cópula de foco** na triagem temática,
quando o próprio tema não está contido nesse foco. Não modifica a fala.

Demais predicados, datas, medidas, categorias, títulos citados, familiaridade
inventada e verificações de suporte/receipts seguem seus contratos. Uma
propriedade adicional dentro ou depois da oração continua podendo ser retida.
Passado e autoria factual sem evidência não entram na dispensa prospectiva.
Limites de tamanho da leitura são conservadores: não há truncamento para
inventar uma estrutura que o leitor não conseguiu identificar.

O teste exploratório inicial também propunha dispensar passado sem fonte.
Essa expectativa pertencia à hipótese ampla, falsificada pelas contraprovas de
autoria. O caso foi preservado em `testes_primeira_hipotese.py.txt`; no contrato
final, passado sem apoio permanece controle de bloqueio. Isso não é declaração
de que relatos passados apoiados estejam resolvidos: exigem outro contrato de
apoio, sem generalizar a conclusão deste recorte.

## Provas automatizadas e composição

- RED inicial: quatro bloqueios e nove controles. Contrafactual final do owner
  congelado: nove REDs, quinze controles GREEN, uma deseleção explícita do teste
  de factory que usa subprocesso próprio. Não se trata de replay do HEAD inteiro.
- Variações de ordem de foco: três REDs adicionais antes da ampliação das formas
  gramaticais, sem alterar os controles de segurança.
- Contrato final: 25 testes GREEN, incluindo a factory. O teste instalado cobre
  dois assuntos, fatos adicionais sem fonte e flags/comandos forjados pela IA.
  O envelope inválido é recusado antes da revisão; não foi usado como fixture
  positiva da fronteira factual. Noventa e sete regressivos focados passaram.
- `composicao_baseline_final.json` e `composicao_candidato_final.json` usam o
  composition root instalado, as mesmas instâncias cognitivas da factory e a
  mesma folha HTTP controlada. A memória raiz é redirecionada somente em RAM;
  rede externa, áudio e efeitos são suprimidos. Livro/jogo são retidos na base e
  preservados no candidato. A publicação inventada em 1997 continua removida;
  a resposta apoiada é preservada. Fonte externa continua indisponível em ambos.
- As flags finais continuam `semantica_verificada=False`,
  `prova_implicacao=False`, `pode_confirmar_fato_externo=False` e
  `autoriza_execucao=False`. Não houve execução simulada nesses controles de
  perguntas, nem execução externa. Chamadas à folha de voz foram suprimidas,
  sem síntese ou reprodução.

A regressão ampla final está em `regressao_ampla.xml`: 2.028 testes GREEN,
30 subtests GREEN, 14 SKIP, uma deseleção por isolamento de import e uma falha
anterior de calculadora. Essa falha escolhe MUSIC_SEARCH para `pode abri a
calculadora para mim` e já tem contraprova no owner congelado da tarefa anterior
(`respostas_prazos_20261024/relato_composto/falha_vizinha_baseline.xml`). Não é
declarada corrigida por esta mudança. O teste deselecionado passou isoladamente
na factory: um GREEN em `import_isolado.xml`.

## Qwen real e limites observados

Duas coletas preservadas, sempre sem voz e com comandos simulados:

- `conversa_real`: primeira versão restrita, 30 turnos/35 HTTP 200. No 18 a fala
  foi preservada, mas usou apenas `ela`; não foi contada como resolução nominal
  completa. Antes da coleta seguinte, três REDs de ordens equivalentes ampliaram
  o mesmo leitor prospectivo. Não houve troca de modelo ou aumento de limites.
- `conversa_validada`: versão final, 30 turnos/30 conclusões, 34 HTTP 200,
  17 pacotes primários conferidos por índice, papel e texto; 527 fontes sem
  drift. Dois APP_OPEN simulados com receipts negativos do adaptador real,
  zero voz/efeitos. No 18: `De acordo com a informação histórica, a Bia vai
  levar o livro azul.` A revisão preservou a fala, sem alegação de falta de base
  sobre Azul; metadados de prova/autoridade continuaram falsos.

A coleta livre **não é contrafactual pareado de geração**: o Qwen varia sua
formulação. A prova causal do bloqueio é a reexecução da mesma resposta real
anterior na factory com os dois owners. O Qwen novo confirma o caminho de
entrega e recuperação com as fontes presentes, sem provar implicação livre.

Persistem limites reais: 18 e 19 levaram cerca de 26 s com geração malformada e
recuperação; HTTP 200 não significa latência ou adequação garantidas. No 27 houve
limite de tentativas. No 28, a formulação `gostava de Nirvana, especialmente o
rock deles` não teve apoio conferido pela gramática fechada de preferência e foi
limitada. Não classificar essa paráfrase como provada só porque parece plausível.
Também permanecem acréscimos conversacionais e outras fronteiras de autoria.

O plano e o mapa causal conservam essas pendências. Não encerrar C7/C5/F3
gerais, nem afirmar que toda resposta histórica passa agora. Somente o falso
indício temático demonstrado em foco prospectivo foi corrigido neste candidato.

## Artefatos e escopo final

`resultados_testes/revisao_historico_20261024/`: baseline, fontes anteriores,
contraprovas, XMLs, composições, coletas, `auditoria.json` e `TRANSCRICAO.md`.
`auditar.py` valida fontes e entregas; não é juiz semântico.

Não alterados nesta tarefa: `plano_turno`, `retrato_turno`,
`revisao_suporte_autoria`, composition root no disco, executores, voz,
configuração do modelo ou prazos. Mudanças anteriores da worktree preservadas.
Nenhum commit, shutdown ou ativação autônoma criado.
