# Recuperação temática — contrato atual, posicionamento e recusa do codec

## Escopo e base

Continuação autorizada de `identidade3-006` e `identidade-retoma-003`, preservando
seus IDs e os diagnósticos anteriores. Testes de conversa/Qwen continuam com
Pedro. Esta investigação usa propostas preservadas e respostas controladas,
sem voz ou efeitos reais. Não trata duas ocorrências como duas raízes iguais,
nem cria uma correção por assunto ou frase.

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, main, worktree suja preservada.
As 538 fontes anteriores ao candidato, hashes e status Git estão congelados em
`resultados_testes/limites_tematicos_20261030/base` e `baseline.json`.
Não houve commit, troca de modelo, aumento de prazo/chamadas ou alteração dos
executores, ponte e regras de revisão factual nesta etapa.

## Correção de uma premissa do replay anterior

Os journals registram a emissão já decodificada: proposições longas aparecem
em `partes` criadas pelo host. O produtor V5 negocia `texto` integral. O replay
da etapa anterior retirava `fala`, mas reapresentava `partes` como saída HTTP;
o codec corretamente recusava essa representação. Assim, aquelas substituições
iniciais por contingência não comprovavam uma falha semântica de produção.

A coleta inválida foi preservada em `fronteiras.json` desta etapa e nos
artefatos anteriores. O replay corrigido recompõe somente o transporte:
`texto = " ".join(partes)`, preservando referências e ordem. As três propostas
bem-sucedidas dos dois casos reconstruíram exatamente o campo `fala` do journal;
conferência em `reconstrucao_transporte.json`. Não se reparou a redação da IA,
não se inventou o corpo da chamada historicamente recusada e não se flexibilizou
o codec de produção para aceitar o replay antigo.

Com o transporte correto, os dois rascunhos principais são legitimamente
recusados por reutilização extensa de falas anteriores. Não é perda geral de
histórico nem ausência de capacidade do revisor de detectar repetição. Retirar
esse veto publicaria novamente uma resposta antiga no lugar da pergunta atual.

## Fronteiras demonstradas e responsáveis

| Família causal | Primeira divergência demonstrada | Contrato corrigido |
| --- | --- | --- |
| Recuperação do ato atual após reuso | Retorno antecipado de `qualidade_comunicacao` descartava estratégia, atos, sequência e limites do contrato atual | A recusa lexical conserva sua prioridade, mas o pacote de recuperação reutiliza o contrato de reparo do owner de aderência; o histórico recusado não vira prova nem volta integralmente ao prompt |
| Posicionamento dialógico confundido com biografia | `natureza_predicado_pessoal` deixava de reconhecer o mesmo juízo quando havia modificador adverbial; a oração impessoal após a pausa era absorvida como estado de “você” | O leitor compartilhado confere modificadores no léxico morfológico existente e conserva a oração impessoal no recorte de haver existencial presente; não certifica verdade do juízo ou da continuação |
| Perda da categoria de falha na saída negociada | `ServicoModeloLLMRuntime` devolvia vazio em `contrato_saida_invalido`; a porta legada de texto perdia a categoria e a recuperação tratava vazio como autoria/contexto insuficiente | A recusa conserva sentinela canônica e `sucesso=False`. A principal pode receber um reparo de formato; recusa no próprio reparo conserva conclusão técnica vinculada ao turno, sem terceira autoria |

Os dois primeiros casos compartilham a perda do contrato de recuperação; o
primeiro tem também a recusa dialógica. No segundo, o journal observa recusa
de formato, mas não conserva o corpo HTTP recusado. Não há evidência suficiente
para afirmar por que o Qwen produziu esse corpo inválido. O candidato corrige
a perda comprovada do resultado negativo, sem atribuí-la a uma causa interna
especulativa do modelo.

O replay de comparação final usa os oito owners congelados em memória no modo
base, preservando a worktree. `fronteiras_base_final.json` e
`fronteiras_candidato_final.json` registram a comparação. No segundo caso,
somente a principal está disponível: ela é reutilizada pela coleta para observar
a recusa de repetição. Não se confunde isso com reproduzir o corpo inválido
ausente do journal. A perda da categoria é demonstrada separadamente por nove
recusas controladas e pela composição instalada, sem inventar evidência histórica.

Hipóteses concorrentes falsificadas:

- Orçamento ou indisponibilidade não explicam a perda de atos do pacote: ela
  ocorre em função pura, antes da chamada. O mesmo defeito aparece em pedidos
  de nome de projeto e em uma pergunta composta de estado pessoal/opinião.
- Falta de relato biográfico não justifica exigir prova para uma posição de
  concordância/discordância. A forma sem advérbio já era admitida, e modificadores
  de vários juízos reproduziram a divergência. Nova biografia continua bloqueada.
- Um JSON truncado, uma declaração obrigatória ausente e uma referência não
  oferecida são recusados pelo codec. Todos perdiam a categoria antes do patch,
  mesmo com transporte bem-sucedido. Não é necessário deduzir timeout para
  explicar a conversão de falha de contrato em vazio.

## Limites das correções

O juízo reconhecido não certifica que o interlocutor está correto. Uma afirmação
como “Você está totalmente correto sobre seu diagnóstico médico” continua fora
do recorte; também continuam recusadas novas atribuições pessoais, sujeito
omitido na continuação e haver mais infinitivo de obrigação. O leitor não faz
análise semântica universal de toda coordenação ou experiência subjetiva.

O reparo histórico de `identidade3-006`, no replay corrigido, ultrapassa a falsa
recusa biográfica após o candidato. Isso não comprova a consistência filosófica
de suas conclusões nem a verdade de afirmações sobre consciência. O controle
de recuperação útil usa uma redação nova, explícita quanto à incerteza e sem
fatos específicos inventados; ela é proposta de teste, não prova factual.

Um controle exploratório mostrou outro limite anterior: quando não há base
factual selecionada, a rota livre configura o owner factual para conferir
somente relatos pessoais. Não se presume cobertura factual universal nesse
modo. O teste de datas foi ajustado para oferecer a base selecionada necessária
e alcançar o contrato que pretendia verificar. A revisão factual não foi
modificada para encobrir esse resultado; a lacuna geral permanece vinculada à
fronteira factual livre/F1 e não foi contada como nova raiz deste patch.

A nova categoria `contrato_saida_invalido` não resgata texto incompatível, não
diagnostica hardware/modelo e não vira receipt de execução. JSON/prosa da IA
com o nome da categoria não fornecem a fonte negativa nativa. A conclusão é
sobre a geração, não uma resposta temática bem-sucedida. Se o primeiro reparo
continua semanticamente ruim, os limites de chamadas e a revisão permanecem.

### Recuperação da principal e resultado da regressão vermelha

A primeira regressão ampla encontrou 17 falhas e 4.603 aprovações. Foi preservada
integralmente em `regressao_red_1`. Uma falha demonstrou uma regressão real do
candidato: tornar a recusa explícita impedia o reparo legítimo da principal.
O teste instalado de recuperação de histórico continuou vermelho e foi usado
como controle obrigatório, sem alterar sua expectativa nem ampliar orçamento.

O owner de preparação passa a encaminhar somente essa principal recusada ao
reparo de formato existente. O pedido usa a pergunta e as fontes do host; não
reaproveita como evidência o corpo descartado nem a sentinela técnica. A nova
autoria continua pelo codec, vínculo de suporte e revisão. O próprio reparo
não retorna a essa entrada para gerar outro reparo.

Na composição, a chamada ainda era adiada antes do transporte: o reparo de
formato estava classificado como tarefa secundária durante uma interação ativa.
O helper agora declara prioridade interativa, como parte da resposta síncrona
em curso. Isso não altera autoridade operacional, timeout, quantidade de chamadas
ou contrato de saída. O teste instalado original voltou a publicar a resposta
esperada, conservando exatamente as ocorrências de fontes do pedido principal.

As outras 16 falhas eram expectativas de parecer posterior a uma recusa anterior:
o coletor excluía blocos excessivos/fontes impertinentes, mas a proposta fixa
insistia em citar uma URL não oferecida. O codec corretamente rejeitava. Os
mesmos IDs agora conferem recusa nativa, publicação limitada, ausência da afirmação
recusada, nenhuma execução e somente principal + um reparo. Não se fabrica um
`revisao_suporte_autoria` para uma autoria que não atravessou o codec. Controles
de referência válida continuam alcançando e exigindo a revisão semântica.

## REDs, composição e regressão

- RED dos contratos:13 falhas e1 controle; quatro perdas de contrato e nove
  variantes de recusa do codec. RED dialógico separado:4 falhas e6 controles.
- Foco anterior:155 aprovados; foco adicional de emissão/codec:122 aprovados e
  dois testes opcionais de modelo real pulados. Esses conjuntos se sobrepõem;
  não somar as contagens como casos exclusivos.
- Dez composições finais pelo construtor real do adaptador, root instalado,
  orçamento e publicação nativa, com HTTP controlado e perfil privado auditado.
  Dois reparos temáticos novos publicados em duas chamadas, sem terceira
  admissão ou bloqueio. Saída inválida do primeiro reparo permanece degradada,
  com causa explícita, duas chamadas e nenhuma terceira tentativa.
- Recuperação completa após o ajuste:171 aprovados e quatro testes opcionais
  de modelo real pulados. Inclui recuperação de principal com resultado válido,
  recusa no reparo e timeout no reparo; ambos os negativos mantêm duas chamadas
  e diagnóstico, sem terceiro bloqueio de orçamento. Os conjuntos de foco
  anteriores se sobrepõem e não devem ser somados.
- Controles instalados recusam efeito sem receipt, biografia não informada e
  detalhe factual sem apoio na base selecionada. A referência interna oferecida
  ao codec foi aceita formalmente e recusada como prova externa pelo revisor;
  esse controle não depende de uma rejeição anterior por referência desconhecida.
- Regressão ampla relevante final:184 módulos,4.623 aprovados,zero falhas/erros,
  14 pulados,um deselecionado,um xfail e30 subtestes aprovados;591,69s. Mesmo
  filtro da ampla anterior e nenhum ID anterior removido. Comando integral,
  log, XML e comparação de IDs preservados em `regressao_comando.json`,
  `regressao.log`, `regressao.xml` e `regressao_resumo.json`.

Dois testes anteriores que exigiam `texto == ""` em recusa do codec passam a
conferir a categoria negativa, a rota e a ausência do rascunho recusado. O
teste tipificado da principal recebe a mesma atualização. Os quatro casos
históricos `reparo_valido` da fixture de emissão ofereciam uma principal sem
suporte; o reparo antes surgia pela perda da categoria, na rota semântica.
A fixture agora fornece seu candidato válido em `reparo_json`, a rota correta,
e exige principal + reparo, suporte revisado e rejeição da referência interna
como prova externa. IDs mantidos, sem remover cenários ou liberar autoria falsa.

O primeiro ensaio composto desta etapa falhou ao serializar objetos nativos
no diagnóstico. A coleta foi corrigida para projetar somente atos e conclusão
necessários às asserções; produção não ganhou serializador permissivo.

## Delta e próximos testes

Produção alterada, exatamente oito fontes existentes:

- `mente_laylay/cognicao/qualidade_comunicacao.py`
- `mente_laylay/cognicao/referencias_linguagem.py`
- `mente_laylay/cognicao/afirmacoes_interlocutor.py`
- `mente_laylay/cognicao/estado_tecnico_llm.py`
- `mente_laylay/integracao/cliente_llm_runtime.py`
- `mente_laylay/personalidade/contingencia_natural.py`
- `mente_laylay/autonomia/higiene_resposta_ia.py`
- `mente_laylay/autonomia/processamento_resposta_ia.py`

As demais 530 fontes foram preservadas por hash. Não houve módulo novo de
produção, alteração na ponte ou commit. REDs, comparação de base, rastreamento,
comandos, XMLs e diff exclusivo estão em `resultados_testes/limites_tematicos_20261030`.

GREEN de contrato e composição controlada não é prova de que o Qwen passará a
produzir espontaneamente argumentos coerentes ou JSON sempre válido. A próxima
conversa de Pedro deve observar a pertinência do reparo e seu apoio às fontes;
em caso de falha de formato, o registro agora preserva essa causa em vez de
substituí-la por falta de contexto ou orçamento. As outras raízes e IDs do plano
permanecem separados.
