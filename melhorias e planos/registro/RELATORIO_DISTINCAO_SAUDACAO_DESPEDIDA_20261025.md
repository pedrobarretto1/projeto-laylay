# Cortesia temporal não autoriza encerrar sessão — 25/10/2026

## Pedido e base preservada

Pedro autorizou investigar a distinção entre saudação e despedida, corrigir o
contrato compartilhado após demonstrar a raiz e validar na composição instalada,
sem remendo por frase, sem voz e com ações simuladas.

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`, worktree suja
preservada. Estado Git, 530 hashes e cópias da base anterior estão em
`resultados_testes/distincao_saudacao_despedida_20261025/baseline.json` e
`fontes_antes`. A diferença desta investigação está registrada em `candidato.diff`;
não confundir com o diff acumulado contra HEAD. Nenhum commit, shutdown ou
alteração de modelo, configuração, voz, executor ou persistência pessoal.

## Primeira fronteira incorreta

O leitor canônico de sessão incluía uma cortesia temporal entre encerramentos
incondicionais. O leitor de presença reconhecia a mesma expressão como saudação.
As duas interpretações tinham efeito antes da geração: o marcador canônico de
sessão prevalecia e o pré-fluxo apagava o contexto.

```text
“boa noite, Laylay”, sem intenção explícita de fechar
→ leitor lexical de sessão declara encerramento
→ turno recebe encerramento_assunto=sessao
→ pré-fluxo renova e limpa a sessão
→ autoria/revisão obedecem ao encerramento incorreto
→ publica “Tudo bem. Até a próxima!”
```

No sentido inverso, o leitor exigia que a fala inteira fosse uma forma nua de
encerramento. Uma cortesia antes ou depois ocultava o ato explícito. No baseline
instalado, `boa noite, vou dormir` e `bom dia, vou sair` chegaram sem marcador de
sessão e sem fonte do ato de encerramento. O Qwen produziu prosa geral sobre
esperar o usuário voltar. Quatro turnos publicados, quatro HTTP 200, fontes
estáveis. A evidência está em `baseline_dialogo/conversa.json` e `estados.json`.

É uma raiz anterior e distinta da projeção de encerramento para autoria/revisão
e da preservação da ocorrência durante a limpeza. Os contratos anteriores
continuam necessários; o erro aqui é conceder ou perder a decisão de encerrar.

## Hipóteses concorrentes e falsificações

- **Autoria ignorou outra vez o ato de encerramento:** no primeiro caso, a
  autoria e revisão obedeceram exatamente ao marcador errado recebido. Não
  remover as proteções já corrigidas.
- **A sessão ativa indica despedida:** não há essa evidência na fala. Controles
  com sessão ativa, inativa e ausente exigem a mesma preservação de contexto;
  atividade, horário ou assunto anterior não são permissão de descarte.
- **O problema é só uma expressão:** a mesma moldura com `bom dia`, `boa tarde`
  e `oi` ocultava encerramentos explícitos; a posição final também falhava.
  A correção separa a moldura do ato, em vez de substituir uma resposta histórica.
- **Basta confiar na expressão de encerramento restante:** controles com
  pergunta, citação, negação, terceiro ou comando adicional precisam manter o
  conteúdo inteiro. Um candidato intermediário ainda consumia uma pergunta
  terminada em `?`: duas falhas e 48 controles em `interrogacao_red.xml`.
  A pontuação interrogativa passa a vetar a decisão destrutiva; não é removida
  antes da conferência. Isso não usa pontuação para certificar prosa livre.

## Contrato e responsáveis

Princípio: **a moldura de cortesia não concede autoridade para encerrar; o ato
atual integral deve fornecer a decisão. Na ambiguidade, responder sem impor uma
nova pergunta ou descartar o contexto**.

| Responsabilidade | Owner | Critério |
| --- | --- | --- |
| Separar moldura lexical | `normalizacao_linguagem.py` | Mesmo vocabulário e separador para presença e sessão; conserva o restante, incluindo aspas, negação e perguntas; não concede autoridade |
| Decidir encerramento | `sessao_conversa.py` | Cumprimento puro não encerra; núcleo integral explícito pode encerrar com cortesia inicial/final; conteúdo adicional não é ignorado |
| Realizar ato atual | `presenca_conversacional.py` | Cortesia temporal pura recebe reciprocidade curta e sem pergunta; encerramento usa as realizações existentes; pergunta explícita de bem-estar continua própria |
| Projetar autoria | `contrato_fala.py` | Cortesia temporal não permite pergunta; decisão explícita de sessão continua dominante; fonte vinculada a turno/texto |
| Limpeza/ocorrência | Pré-fluxo e runtime existentes | Consomem o mesmo leitor; só encerramento explícito limpa, mantendo o frame em conclusão |
| Reparo e revisão | Owners existentes | Reutilizam as mesmas realizações integrais; não aceitam despedida, convite ou pergunta inventados para cortesia indeterminada |

O vocabulário de saudações já existente foi compartilhado, não duplicado. Não há
classificador privado por habilidade, prompt escolhendo autoridade, nova
pendência, regra de horário, dependência de tema ou decisão baseada em proposta
da IA. O modelo escolhe a redação permitida; a fonte só certifica o ato atual,
nunca fatos externos, sensações ou efeitos. O leitor de encerramento também é
reutilizado pelo pré-fluxo, pelo classificador de assunto e pela continuidade
musical. O benefício pertence ao contrato comum, sem patches nos executores.

Uma expressão isolada não revela de forma infalível se a pessoa chegou ou está
saindo. Em vez de inventar essa informação, a realização é compatível com ambos:
`Boa noite!` ou `Boa noite! Estou por aqui.` Ela não fecha a sessão nem exige
continuação. Uma declaração como `boa noite, vou dormir` fornece a intenção que
faltava e recebe a despedida, sem pergunta.

## Escopo aplicado

Produção alterada somente em quatro arquivos: `normalizacao_linguagem.py`,
`sessao_conversa.py`, `presenca_conversacional.py` e `contrato_fala.py`.
Permanecem intactos nesta investigação o composition root, pré-fluxo, revisão,
reparo, transação de estado/ocorrência, roteadores de ação e executores.

Dois testes anteriores tratavam `boa noite, Laylay` como encerramento por
premissa lexical. Seus cenários de limpeza e proibição de reabertura agora usam
`boa noite, vou dormir`, mantendo todas as asserções. A expectativa antiga não
foi apagada sem cobertura: a redação original tem regressão explícita de
preservação e reciprocidade na nova família. Artefatos históricos permanecem.

## Evidências de validação

- RED anterior à produção: **31 falhas e 16 controles aprovados**. As primeiras
  asserções alcançam a decisão canônica; não são erros de import ou transporte.
- Primeiro candidato: 47 aprovados. Extensão interrogativa demonstrou duas
  falhas/48 aprovados; após o veto, a família completa tem **57 aprovados**.
- Foco ampliado: **422 aprovados e quatro ignorados**. Inclui autoria, suporte,
  presença, qualidade, reparo, sessão e atos sociais. A variação de estado de
  sessão foi reforçada no snapshot real do teste; nova execução dos 57 controles
  foi aprovada em `bordas_final.xml`.
- Composição instalada/Qwen: **15 turnos, 15 publicações, 15 HTTP 200**, sem
  reparo ou substituição silenciosa do texto. Seis cortesias temporais não
  renovaram a sessão e conservaram o histórico; cinco encerramentos explícitos
  renovaram atomicamente e preservaram o mesmo frame até a conclusão. A saudação
  comum e perguntas explícitas mantiveram seus próprios atos. Persistência
  isolada gravada/relida em todos os turnos; 530 fontes estáveis.
- Segurança separada: três turnos, uma ação simulada, receipt com
  `executou=False`/`confirmado=False`; a pergunta posterior não recebe sucesso
  falso. Não comprova execução real, que não foi autorizada nesta coleta.
- Timeout separado, **modelo_real=False** e falha HTTP injetada: uma conclusão
  `falha_geracao_principal_verificada`, sem silêncio ou confirmação falsa.
- Regressão ampla em **126 módulos**: **3.193 aprovados**, nove falhas, 44 erros,
  14 ignorados, um desmarcado e 30 subtestes aprovados. Comparação por identidade
  confirmou exatamente as mesmas nove falhas/44 erros da etapa anterior;
  detalhes em `comparacao_regressao.json`. São os casos antigos de comando da
  Calculadora, expectativas de pacote/tokens e fixtures de serialização de
  `PerspectivaEnunciador`; não foram silenciados ou reclassificados por este patch.
- Auditoria final aprovada: publicação idêntica à proposta HTTP, fonte ligada
  ao turno, atos esperados, histórico preservado nas cortesias, cinco renovações
  atômicas, persistência isolada, segurança, comparativo de regressão e hashes.
  Somente os quatro arquivos de produção declarados diferem da base congelada.
  Resultado em `manifesto.json`. Não declarar suíte global verde.

Uma premissa da primeira auditoria foi corrigida após examinar os dados: ela
exigia que o histórico bruto permanecesse como prefixo exato, mas o owner de
prompt existente pode inserir/atualizar mensagens `system` efêmeras
(`contexto_resposta_ia.py:304–314`). Todas as mensagens de diálogo anteriores
permaneceram na mesma ordem. A asserção agora exige a preservação integral desse
diálogo e, separadamente, ausência de renovação da sessão. Nenhuma mensagem
humana foi excluída da conferência e nenhum código de produção foi alterado
para ajustar a coleta.

Os testes e a coleta não ligam voz ou hardware. Os avisos/diagnósticos de outros
recortes não foram misturados a esta raiz. A coleta de segurança ainda mostra
prosa geral mais longa numa abertura composta; isso não foi transformado em
prova de fluidez geral nem corrigido por esta alteração de autoridade de sessão.

## Limites e continuidade

A prova cobre o contrato de cortesia versus encerramento explícito nas formas
reconhecidas pelo leitor canônico. Não certifica toda paráfrase livre, variedade
de personalidade, intenção oculta, sentimentos humanos, áudio físico ou
compreensão global. O contexto anterior pode informar interpretação, mas não
cria por si a autoridade para apagar uma sessão. F1/C5/C7/AUT continuam com seus
IDs e evidências separados. Novas formas não reconhecidas exigem prova na
fronteira de interpretação, sem converter propostas do modelo em permissão.
