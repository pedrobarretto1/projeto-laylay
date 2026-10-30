# Ato de encerramento governa autoria e revisão — 25/10/2026

## Pedido e base congelada

Pedro autorizou investigar por que despedidas reabrem perguntas, corrigir a
raiz no contrato compartilhado de autoria/revisão e validar na composição
instalada, sem remendo por frase, sem voz e com ações simuladas.

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`; worktree suja
preservada. Baseline, estado Git e hashes de 530 fontes em
`resultados_testes/autoria_despedida_20261025/baseline.json`. Cópias anteriores
em `fontes_antes`, diferença exclusiva desta investigação em `candidato.diff`.
Nenhum commit, shutdown, alteração de modelo, configuração, voz ou executor.

Esta raiz é distinta da perda da ocorrência durante a limpeza de sessão. A
correção anterior de sessão permanece aplicada e não foi reaberta ou alterada.

## Primeira divergência demonstrada

O quadro já chega à autoria com `turno.encerramento_assunto = sessao`. Porém,
esse ato não era projetado para o contrato de fala:

```text
leitor canônico decide encerramento de sessão
→ turno conserva a decisão
→ contrato de fala ignora essa decisão
→ “boa noite” oferece opções de saudação com pergunta
  e outras despedidas entram na prosa geral
→ revisão aplica o mesmo contrato sem o ato de encerramento
→ pergunta/convite/retomada ou mudança da intenção são publicados
```

O baseline atual reproduziu `Boa noite! Como você está?`: turno marcado como
encerramento, fonte de autoria marcada como saudação, pergunta permitida e
revisão sem problemas. Outras respostas reabriram oferta ou acrescentaram
diagnóstico corporal. Todas foram geradas no caminho instalado com HTTP 200.

O problema não é somente a pontuação interrogativa: `Me conta depois como ficou
seu projeto.` também reabre assunto; `de verdade, não era só isso` contraria o
encerramento. A solução não remove interrogações da saída nem usa o texto
histórico como gatilho de uma resposta substituta.

## Hipóteses concorrentes falsificadas

- **A sessão ainda apaga o turno:** agora os frames permanecem vinculados e as
  respostas são publicadas; o defeito começa na projeção do ato para a autoria.
- **O Qwen sozinho decidiu ignorar um contrato correto:** no caso de saudação,
  o próprio contrato oferecia a pergunta. Nos demais, não expunha o ato de
  encerramento como obrigação conferível. A primeira fronteira incorreta é
  anterior à geração.
- **Bloquear `?` resolveria a família:** controles sem interrogação mostram
  convite, retomada e alteração da intenção. O host precisa conferir o ato
  integral, não uma lista de palavras proibidas.
- **É preciso outra lista de despedidas:** o leitor compartilhado de sessão já
  reconhece as entradas. A alteração reutiliza seu resultado e a confirmação
  integral pelo mesmo leitor, sem parser privado por domínio.

## Contrato e responsáveis

Princípio reutilizável: **um ato canônico de encerramento deve governar a mesma
autoria, reparo e revisão; outro conteúdo só cabe quando pertence a um novo ato
realmente solicitado pelo usuário**.

| Responsabilidade | Owner | Critério de validação |
| --- | --- | --- |
| Reconhecer encerramento | Leitor de sessão existente | Mantido; não alterar a política de classificação nesta raiz |
| Projetar o ato dominante | `contrato_fala.py` | `encerramento_sessao`, pergunta proibida, obrigação de despedida curta; não reinterpretar como saudação/agradecimento isolado |
| Gerar e conferir realizações | `presenca_conversacional.py` | Fonte ligada a turno/texto/hash; mesmo leitor confirma o encerramento; realização integral sem pergunta, convite, oferta, fato ou efeito acrescentado |
| Organizar o roteiro | `geracao_concreta.py` | Núcleo e sequência do encerramento, sem aproveitar outro assunto como base da resposta |
| Revisar aderência | `validacao_contrato_fala.py` | Fonte ausente/alterada não provoca fallback permissivo; rejeita realização fora do ato |
| Conferir suporte | `revisao_suporte_autoria.py` | Ato inteiro conferido pelo owner não exige fonte factual externa; proposta de outro turno não recebe esse vínculo |
| Reparar | Qualidade compartilhada já existente | Reutiliza o pacote do mesmo owner, sem reapresentar rascunho/pergunta/projeto antigos |

O contrato usa o marcador já produzido no turno. O leitor da sessão é o mesmo
na confirmação desse marcador; não foram adicionadas palavras de despedida ao
executor, ao revisor ou a um novo classificador independente. Pedidos compostos,
terceiros, citações, comandos adicionais e marcadores incompatíveis não são
absorvidos pelo encerramento.

As realizações são redações curtas do ato social, escolhidas pelo Qwen. A mesma
linguagem limitada serve às diferentes formas de encerramento; não há `if` para
a frase do log, tema anterior, jogo, arquivo ou domínio. Não se trunca nem
reescreve silenciosamente a resposta gerada. Ainda é vocabulário controlado,
não validação de toda prosa livre ou de variedade geral.

Fonte de encerramento confere somente um ato da conversa atual. Ela não
certifica identidade/categoria de entidades, estado físico, experiência,
capacidade, sentimento humano ou execução. Companhia corporal não autoriza
inferir que a despedida parou um motor, uma rotina ou um dispositivo. A rota
corporal de outras perguntas de presença continua protegida pelos seus controles.

O revisor de suporte reutiliza a conferência integral do owner para impedir que
uma fonte factual residual transforme a despedida em aviso de citações. A
exceção não cobre nenhum fato acrescentado à realização. Declaração proposta
pelo modelo continua sem poder factual e uma proposta de outro turno continua
recusada.

## RED, candidato e controles

Antes de produção: **22 falhas e nove controles verdes** em
`contrato_red.xml`. Alcançam projeção do ato, perguntas publicadas, convite sem
interrogação, mudança da intenção, reparo aberto, companhia e fonte alterada.

Um candidato intermediário teve 30 aprovados e uma falha: retirar o marcador
mantendo o ato explícito permitia cair na revisão genérica. Esse resultado está
preservado em `contrato_green.xml` e **não** é o resultado final. O verificador
passou a exigir fonte válida também quando o ato do contrato é encerramento,
sem converter a fonte alterada em permissão de redação livre.

O arquivo novo `scripts/tests/test_autoria_despedida_canonica.py` contém
**38 casos**: oito formas de encerramento, vizinhos negativos, fonte/turno
estrangeiros, ações inventadas, contexto factual residual e esclarecimento de
uma despedida efetivamente publicada. Inclui os textos históricos de Pedro.

Foco final: **365 aprovados e quatro ignorados**, incluindo contrato semântico,
presença, reparo social, revisão de fontes, sessão e perguntas de gosto.

Regressão ampla em **125 módulos**: **3.136 aprovados**, nove falhas, 44 erros,
14 ignorados, um desmarcado e 30 subtestes aprovados. A comparação individual
confirmou exatamente os mesmos IDs das nove falhas e 44 erros da etapa anterior:
comando natural antigo da Calculadora, expectativas antigas de pacote/tokens e
fixture que serializa `PerspectivaEnunciador`. Não foram corrigidos, excluídos
ou reclassificados por este patch. Lista em `comparacao_regressao.json`; a
auditoria final passou e gerou `manifesto.json`. Não declarar suíte global verde.

## Composição instalada e Qwen

`final_dialogo`: **16 entradas, 16 publicações, 16 HTTP 200**. Nove
encerramentos passaram pelo ato canônico de autoria/revisão; nenhum reabriu
pergunta, convite, oferta ou assunto. A autoria chegou ao transporte como
unidades com `fontes=[]`, e seu texto integral é idêntico ao publicado.
Exemplos: `Tudo bem. Até a próxima!` e `Até mais!`.

Após a despedida, `como assim?` recebeu uma explicação do ato publicado:
`Quis respeitar seu encerramento da conversa e me despedir.` Uma nova saudação
do usuário continuou permitindo reciprocidade/pergunta. A correção não proíbe
perguntas em toda conversa nem transforma qualquer “boa noite” embutido em
outro pedido em encerramento.

São os owners, factory, planejamento, proposta, guardião, publicação e
persistência instalados, com Ollama/Qwen `qwen3:4b-instruct` reais. Nenhuma troca
de modelo ou orçamento. Os 530 arquivos ficaram estáveis durante a coleta.
Persistência isolada foi gravada/relida nos 16 turnos. As nove renovações
continuaram atômicas, com o mesmo frame antes/depois e sessão inativa; a
correção de ciclo de vida anterior permaneceu intacta.

`seguranca_final`: três turnos separados, uma ação simulada com receipt
negativo; a pergunta posterior não recebe confirmação falsa. Nenhuma ação real
ou áudio. `falha_controlada` usa timeout injetado, sem Qwen real nessa coleta:
uma única conclusão `falha_geracao_principal_verificada`, sem silêncio ou falso
sucesso. Essa conclusão técnica observada não é uma realização livre da IA nem
uma falha que deva ser ocultada.

`auditar.py` confere os payloads HTTP brutos, o texto publicado, o ato, os flags
de evidência, IDs, renovação, persistência, fontes de código e a comparação por
identidade da suíte ampla. Não usa a autodeclaração do modelo como prova de fato.

## Escopo e limites

Produção alterada nesta raiz: `contrato_fala.py`, `presenca_conversacional.py`,
`geracao_concreta.py`, `validacao_contrato_fala.py` e `revisao_suporte_autoria.py`.
Qualidade/reparo existente foi reutilizado sem patch. Sessão, estado compartilhado,
composição, aquisição de fontes, voz e executores não foram alterados.

Classificar uma expressão ambígua como abertura ou encerramento continua sendo
responsabilidade do leitor de sessão existente. Esta correção não redefine a
classificação de “boa noite” isolado. Também não resolve aquisição de contexto
factual anterior, redação livre, variedade geral, compreensão global ou áudio
físico. Preservar os IDs F1/C5/C7/AUT e manter essas fronteiras separadas.
