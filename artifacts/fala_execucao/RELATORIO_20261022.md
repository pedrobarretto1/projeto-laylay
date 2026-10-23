# AUT-08 — progresso, execução e conclusão do mesmo objetivo

## Resultado

Piloto instalado para **texto copiado → arquivo novo**, reutilizando as habilidades
de área de transferência e arquivos. O objetivo conserva o quadro, governança,
dependências e receipts existentes. O anúncio não consome a conclusão do turno.

**GREEN de runtime de diagnóstico:**
[ensaio final](20261022_201936_sucesso/relatorio.json), com composição importada de
`laylay.py`, clipboard Windows, Edge TTS `pt-BR-FranciscaNeural`, sounddevice e
escrita/releitura de arquivo reais. Memória isolada; os serviços da sessão desktop
existente não foram reiniciados. Não é uma certificação de audição humana.

No relógio monotônico do mesmo processo:

| Evidência | Instante / resultado |
| --- | --- |
| Primeiro áudio começou no player | 4551.8574331 s |
| Arquivo observado com hash correto e stream ativo | 4551.8708364 s |
| Reprodução do anúncio terminou | 4556.5308705 s |
| Áudio da conclusão começou | 4557.4461233 s |
| Reprodução da conclusão terminou | 4561.7491065 s |
| Plano e etapa de arquivo | confirmados, `arquivo_criado` |
| Áudios confirmados pelo runtime | 2 |

O conteúdo foi observado **13,4 ms após o primeiro áudio**, enquanto o stream ainda
estava ativo. A confirmação final só foi publicada após receipt e conferência.

## Base preservada

Branch `main`, HEAD `b128f4e48b774352846a40672de493d19c30f109`.
Worktree já suja antes da investigação, incluindo UI, corpo, histórico, receipts
e autoria. Nenhum reset, limpeza, pull, commit ou alteração de configuração.
Os diffs gerais de `laylay.py`, mapa e orquestrador de fala incluem trabalho
anterior e não devem ser atribuídos integralmente a este piloto.

## Primeira fronteira e falsificações

1. A fila já trabalha em thread separada e aceita `wait=False`: falta de thread
   não explica a ausência de uma experiência de progresso/conclusão.
2. A reprodução local anterior aceitou o anúncio, mas recusou a confirmação com
   `candidato após início da entrega descartado`. A proteção de uma resposta por
   turno confundia anúncio e conclusão. Os dois primeiros REDs do novo contrato
   exigiram a porta explícita de progresso ainda ausente.
3. A pendência histórica de resultado tardio não foi reaplicada: os **156 testes**
   de `test_receipt_ocorrencia_execucao.py` já passaram antes do candidato.
4. A contraprova com `executor_cooperacao.py` de HEAD mostrou cancelamento durante
   o último efeito retornando `ok=True, estado=confirmado`. O candidato conserva o
   receipt do efeito em curso, mas finaliza o objetivo como cancelado.

## Contrato e owners

- `ProgressoFala` é um sinal efêmero de entrega, sem permissão ou receipt.
- Orquestrador de fala publica anúncio separado, pelo guardião canônico, com ID
  próprio. Voz não reserva o espaço da confirmação final para esse anúncio.
- O sinal de início nasce **depois de `sounddevice.play`**, não ao enfileirar,
  marcar `is_speaking`, iniciar a síntese ou publicar texto.
- A espera é limitada ao início do áudio. Falha/timeout de voz libera o trabalho;
  anúncio que perdeu validade não toca posteriormente.
- Executor cooperativo revalida cancelamento, prazo, ocorrência e autorização
  depois da preparação, antes do efeito. O callback de anúncio não autoriza.
- No piloto, o ciclo canônico executa pela porta de execução silenciosa já
  existente. O coordenador recebe `ExecucaoObservada`, confere turno, invocação,
  plano, receipt, status e conteúdo relido. A conclusão usa esse receipt original.
  `ultima_acao_*` não certifica o caminho novo instalado.
- O anúncio é opcional e o mecanismo de espera/revalidação é compartilhado.
  Controles locais cobrem `CREATE_FILE` e `APP_OPEN`; somente o fluxo do clipboard
  foi conectado ao anúncio nesta entrega.

## Validação

- **21 testes novos locais**: progresso/conclusão, descarte obsoleto, fronteira de
  áudio, alegação sem receipt, falta de autorização, revogação, cancelamento,
  mudança de ocorrência, orçamento, falha de voz e catálogo contextual.
- **1 regressão nova da composição instalada**: disco real, clipboard com apenas
  a porta de leitura do SO controlada, voz em modo silencioso pelo contrato real;
  owners compartilhados permanecem reais. Sucesso, idempotência, falha parcial,
  cancelamento, linguagem negativa/hipotética e receipt entregue identificado.
- Seleção com vizinhos: **325 aprovados, 1 desmarcado**.
- Regressão ampliada: **552 aprovados, 2 falhas, 1 desmarcado**. Não é suíte ampla
  verde. XML e hashes em [regressão](regressao_20261022/manifesto.json) e
  [saída do pytest](regressao_20261022/pytest.txt). Os 11 arquivos acompanhados
  permaneceram com hashes iguais antes/depois dessa regressão.
- `git diff --check` focado sem erros.

### Controles executados no runtime de diagnóstico

| Controle | Evidência | Resultado |
| --- | --- | --- |
| Sucesso, áudio e gravação simultâneos | [ensaio final](20261022_201936_sucesso/relatorio.json) | GREEN; dois áudios, hash e plano confirmados |
| Cancelamento antes do efeito | [cancelamento](20261022_201403_cancelamento/relatorio.json) | GREEN; arquivo ausente e objetivo cancelado |
| Mudança de turno durante preparação | [troca de turno](20261022_201841_troca_turno/relatorio.json) | GREEN; sem gravação ou confirmação no turno novo |
| Clipboard disponível, escrita bloqueada pelo estado real do destino | [falha parcial](20261022_201726_falha/relatorio.json) | GREEN; primeira habilidade confirmada, segunda falhou, sem sucesso integral |
| Voz desativada explicitamente no ensaio | [modo silencioso](20261022_201510_sem_audio/relatorio.json) | GREEN; texto e arquivo conferidos, sem exigir áudio |

As rodadas anteriores foram preservadas, inclusive erros do próprio coletor e
falhas do provedor; não certificam o candidato final. O teste de cancelamento real
usa a API canônica do quadro; isso não comprova um novo parser de cancelamento por
voz. O clipboard foi restaurado e os dados serializáveis conferidos; bitmaps
foram preservados pelos formatos DIB sintetizáveis do Windows. Nenhum conteúdo
original do clipboard foi escrito nos artefatos.

## Pendências independentes preservadas

- `test_composicao_instalada_transporta_publicacao_real_com_efeito_isolado` falha
  ao serializar `SuporteAutoriaProposto`. Mesma falha reproduzida com os três
  argumentos do novo wiring removidos **somente do código carregado em memória**;
  não se alterou o teste nem a worktree. Esse teste foi desmarcado na seleção
  maior e sua falha continua registrada.
- Dois controles `[3]`/`[5]` de
  `test_transporte_real_preserva_orcamento_e_contexto_fechado_de_varios_receipts`
  falham com `estrutura_composta_invalida`. Reproduzidos também carregando em
  memória `confirmacao_llm.py` de HEAD; outros componentes continuam na worktree.
  Essa contraprova não é replay de toda a árvore histórica. Não houve patch
  nesse módulo nem enfraquecimento das expectativas.
- Nas primeiras rodadas, a apresentação local de arquivos reconstruiu um
  receipt sem identidade adequada para o registro de fala. O piloto passou a
  consumir o receipt original pela execução silenciosa canônica; não se declara
  corrigida a apresentação de todas as operações de arquivo.
- O serviço de TTS apresentou HTTP 429 intermitente. Texto e efeitos preservados,
  sem trocar a voz. A rodada final confirmou os dois áudios; disponibilidade
  contínua do serviço não está garantida.

## Escopo de produção desta tarefa

`laylay.py` (três conexões); `autonomia/executor_cooperacao.py`;
`autonomia/orquestracao_cooperativa.py`; `personalidade/progresso_fala.py`;
`personalidade/voz_runtime.py`; `personalidade/orquestrador_fala_runtime.py`;
`especialistas/capacidades.py`; `especialistas/mapa_habilidades.py`, sob
`mente_laylay/` quando aplicável. Testes e coletor entregues prontos.

Modelo, identidade de voz, configuração, firmware, executores de domínio,
parser de confirmação e histórico paralelo preservados. Nenhum commit criado.

Este é um objetivo curto, efêmero e delimitado. Não implementa metas persistentes,
retomada após reinício, paralelismo irrestrito ou sincronização por palavra falada.
Não encerra AUT-01, P05/P07 ou as demais entregas de autonomia. A sessão desktop
já aberta precisa recarregar o código no próximo reinício normal.
