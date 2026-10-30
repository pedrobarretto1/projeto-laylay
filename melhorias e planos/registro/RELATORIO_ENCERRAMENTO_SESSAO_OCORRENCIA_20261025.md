# Encerramento de sessão preserva a ocorrência em conclusão — 25/10/2026

## Pedido e base

Pedro autorizou estudar a despedida que apagava o turno antes de responder e,
comprovada a raiz, corrigir o contrato compartilhado de sessão. Sem voz e com
ações simuladas. A investigação continua a fronteira identificada no relatório
de saudação; não reúne essa causa à autoria técnica/prolixa ou aos outros IDs
históricos de compreensão.

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`, worktree suja
preservada. Snapshot inicial e hashes de 530 fontes em
`resultados_testes/encerramento_sessao_20261025/baseline.json`; cópias anteriores
dos owners em `fontes_antes`. Nenhum commit, alteração de modelo/configuração,
voz, hardware, efeito externo ou shutdown.

## Primeira fronteira RED

O caminho instalado segue esta ordem:

```text
iniciar_planejamento_turno
→ capturar ocorrência local do turno
→ processar_inicio_fluxo_resposta_ia
→ processar_encerramento_conversa(..., emitir_fala=False)
→ renovar_sessao_conversa("despedida_usuario", False)
→ renovar_contexto_sessao limpa turno/plano/contrato/retrato
→ fluxo continua à LLM
→ Qwen gera texto
→ guardião recusa proposta sem ocorrência vigente
→ nenhuma resposta publicada
```

O baseline de quatro turnos publicou apenas o controle de gosto. `boa noite,
Laylay`, `tchau` e `por hoje é só` tiveram HTTP 200 e proposta gerada, porém zero
publicações. A segunda coleta capturou o estado antes/depois da escrita do reset:
os três frames eram coerentes antes da limpeza e estavam vazios depois. Artefatos
`baseline_dialogo` e `baseline_fronteira/fronteiras_sessao.json`.

O pré-fluxo reserva a resposta à LLM quando `emitir_fala=False`. Essa limpeza
nunca poderia eliminar a identidade necessária para a mesma resposta. O erro
não está na recusa posterior do guardião: publicar sem vínculo seria inseguro.

## Hipóteses falsificadas

- **Modelo não respondeu / transporte indisponível:** raw HTTP contém a fala;
  status 200 e ausência de falha de transporte.
- **Planejamento não criou o turno:** a fronteira capturada tem IDs e texto
  coerentes em turno, plano, decisão e retrato antes da renovação.
- **Guardião rígido demais:** o contrato de ocorrência passa antes do reset,
  falha quando o frame foi apagado e passa novamente com a identidade original
  preservada. Nenhuma proteção do guardião foi relaxada.
- **Falha geral da composição ou persistência:** o controle inicial publica e
  grava no mesmo processo; a divergência começa especificamente na renovação.

## Contrato e responsáveis

Princípio compartilhado: **o ciclo de vida da sessão e o ciclo de vida da
ocorrência em conclusão são distintos**. Encerrar contexto antigo não pode
invalidar a resposta ainda devida à entrada que pediu o encerramento.

| Responsabilidade | Owner | Validação |
| --- | --- | --- |
| Reconhecer encerramento e reservar sua resposta | Pré-fluxo e leitor canônico existentes | Mantidos; sem lista nova de despedidas nem resposta histórica fixa |
| Definir o que a renovação pode preservar | `memoria_mental/sessao_conversa.py` | Só ocorrência nativa explicitamente fornecida, conferida e ainda planejada; contexto antigo continua limpo |
| Capturar a ocorrência vigente e publicar a renovação | `integracao/estado_contexto_runtime.py` | Captura dentro da transação compartilhada dos três domínios, sem snapshot externo que sobrescreva turno novo |
| Conferir identidade | `motivo_divergencia_ocorrencia_turno` existente | Mesmos IDs, texto e frames; proposta de outra ocorrência continua recusada |
| Confirmar publicação/efeito | Owners existentes | Publicação observada não prova execução externa; receipt negativo permanece negativo |

`renovar_contexto_sessao` recebeu o argumento opcional
`ocorrencia_em_conclusao`. Sem ele, a API pura conserva a limpeza integral
anterior. O runtime só o fornece para `despedida_usuario` com sessão inativa.
A ocorrência precisa corresponder ao marcador canônico `encerramento_assunto=
sessao`, ao texto atual e aos frames coerentes. Exige fase `planejado`, ausência
de evento, comandos e execução; turno, plano, contrato e decisão devem recusar
autoridade operacional. Contrato de fala precisa ser o mesmo nos três locais
e ter origem `mente_unica`.

São conservados os snapshots originais do turno em curso e seus metadados
vinculados, sem fabricar outro turno a partir da frase e sem trocar IDs. Não se
preservam oferta, pendência, última ação ou resposta antiga. O registro semântico
da sessão é renovado e fatos duradouros continuam preservados pela política
existente. Um frame concluído, estrangeiro, malformado, operacional ou sem
encerramento continua sendo invalidado.

O runtime reutiliza `EstadoCompartilhadoRuntime.atualizar_dominios` para publicar
`mental`, `conversacional` e `memoria_conversa` juntos. A captura ocorre dentro
da mesma transação: não existe uma janela entre apagar e restaurar o turno.
Sem lock paralelo, fallback privado de sessão ou estado duplicado.

## RED, candidato e regressivos

RED válido antes de produção: **cinco falhas e 14 controles verdes**. Quatro
despedidas alcançavam a renovação e perdiam o turno; a publicação em três setters
também não obedecia ao contrato transacional. O erro inicial de montagem do
teste foi corrigido antes desse RED; ele não foi usado como evidência da raiz.

Primeiro candidato: 19 GREEN. Revisão das guardas encontrou decisão interna
com `permite_acao=True` mesmo quando os outros flags eram falsos; um RED novo
confirmou a preservação indevida desse frame contraditório. Agora essa decisão
também precisa negar ação. Não foi necessário mudar roteadores ou executores.

O arquivo `scripts/tests/test_encerramento_sessao_ocorrencia.py` tem 24 casos.
Inclui limpeza de ofertas/receipts antigos, fonte proposta em dicionário,
ocorrência estrangeira, quatro formas naturais de encerramento, outros resets,
repetição antes da conclusão, invalidação depois da conclusão e interleaving
controlado que troca o frame antes da transação. A proposta antiga permanece
recusada; a nova ocorrência é a que prevalece.

Foco final: **238 aprovados**, incluindo memória de sessão, pendências canônicas,
fluxo de conversa, contrato semântico, saudações e referência de fala observada.
XMLs: `contrato_red.xml`, `borda_autoridade_red.xml`, `contrato_green.xml`,
`bordas_green.xml`, `foco_final.xml`.

Regressão ampla em **124 módulos**: **3.098 aprovados**, nove falhas, 44 erros,
14 ignorados, um desmarcado e 30 subtestes aprovados. Comparação com a etapa de
saudação confirmou exatamente os mesmos IDs das nove falhas e 44 erros:
comando natural antigo da Calculadora, expectativas antigas de pacote/tokens e
fixture que serializa `PerspectivaEnunciador`. Não foram removidos, corrigidos
ou reclassificados como parte desta raiz. Lista e comparação completas em
`comparacao_regressao.json`; `auditar.py` passou e gerou o manifesto final.

## Validação na composição instalada

`final_revisado`: **13 entradas, 13 publicações, 13 HTTP 200**, sete
encerramentos com fronteira de renovação capturada. Em todos os sete, sessão
inativa e mesmos turno/plano/contrato/retrato antes/depois da limpeza; o quadro
chegou à revisão e à publicação. Interações posteriores de saudação e gosto
também receberam resposta. Exemplos observados: `Tchau! Foi bom conversar com
você.` e `Tudo bem, até mais! Valeu por conversar.`

São a factory, planejamento, pré-fluxo, transação, proposta, verificador,
publicação e persistência instalados, com Ollama/Qwen `qwen3:4b-instruct` reais.
Os 530 arquivos de produção ficaram estáveis durante a coleta. Persistência
isolada foi gravada e relida nos 13 turnos. `fronteiras_sessao.json` mantém os
retratos completos e a indicação da publicação atômica. Os hooks da sonda apenas
observam substituição/transação; não repõem ou fabricam frames.

Falha separada em `falha_controlada_final`: porta HTTP substituída por timeout,
sem chamar Qwen real nessa coleta. A despedida publicou uma única conclusão
`falha_geracao_principal_verificada` com ocorrência vinculada. Não foi contada
como resposta útil do modelo ou sucesso de um efeito.

Controle `seguranca_final_revisada`: três turnos, um comando simulado e receipt
negativo; a pergunta posterior não recebeu confirmação falsa. Nada foi aberto,
acionado ou reproduzido por áudio. Nenhuma voz/configuração foi trocada.

## Alcance e próximas fronteiras separadas

Produção alterada somente em `sessao_conversa.py` e
`estado_contexto_runtime.py`. Pré-fluxo, composição, classificador de despedidas,
contrato de autoria, guardião, voz e executores permanecem iguais ao baseline.

A raiz de perda da ocorrência foi reproduzida e corrigida no recorte validado.
Isso não certifica a prosa livre: `boa noite` ainda pode reabrir uma pergunta;
`vou dormir` recebeu oferta/pergunta desnecessária; algumas respostas ao
agradecimento mudam a intenção ou exageram reciprocidade. Um retrato contextual
também pode propor pesquisa sobre tema anterior durante despedida. Essas
ocorrências estão preservadas nos logs e no manifesto; não foram corrigidas
com frases especiais ou incorporadas a este patch de sessão.

Próxima fronteira comunicativa: o ato canônico de encerramento precisa prevalecer
na autoria/revisão, sem reabrir a conversa. Investigar separadamente a pertinência
de contexto/fonte de tema anterior antes de alterar seus owners. Não fechar
compreensão geral, F1/C5/C7/AUT, qualidade livre ou áudio físico por esta prova.
