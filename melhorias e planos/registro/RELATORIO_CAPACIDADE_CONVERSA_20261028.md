# F2 — disponibilidade, tentativa e autoria na conversa — 28/10/2026

Correção do contrato compartilhado de coerência de capacidade na conversa.
Disponibilidade vem do catálogo vivo do turno; um receipt negativo não prova
incapacidade, falta de acesso ou causa da falha. A fala da IA não certifica
nenhuma dessas coisas. O recorte é limitado aos predicados e construções
conferidos, não um verificador universal de toda paráfrase de incapacidade.

É continuação de F2, conferência de alegação/fonte e separação entre diagnóstico
e nova autoria já registradas no mapa. Não se cria uma raiz por verbo, música
ou aplicativo nem se declara F2/C5/C7/AUT globalmente encerrados.

## Base, cadeia causal e falsificações

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, `main`, worktree suja
preservada. Estado Git e hashes de 532 fontes congelados em
`resultados_testes/coerencia_capacidade_conversa_20261028/baseline.json`.
Nenhum commit, configuração, modelo, voz ou executor alterados.

O turno original “eu abri a calculadora”, depois de uma tentativa simulada,
recebeu “não posso abrir aplicativos”. Os artefatos da etapa anterior mostram:

- catálogo vivo e predicado `APP_OPEN` disponíveis no plano do mesmo turno;
- receipt anterior com `executou=False`, `confirmado=False`, `ok=False`;
- contrato de resposta direta contendo só domínios genéricos, sem fonte
  detalhada de disponibilidade pertinente;
- autoria e revisão aceitaram a negativa na justificativa causal.

```text
catálogo vivo do turno tem capacidade pertinente disponível
→ contrato só retém documentação/predicado na tarefa explicativa
→ conversa perde a evidência detalhada, apesar de o catálogo tê-la encontrado
→ juízo de coerência só admite a estratégia explicativa e negativas isoladas
→ negativa geral na justificativa da fala livre passa até a publicação
```

A primeira perda demonstrada está na passagem **evidência do catálogo → contrato
da conversa**, seguida da mesma restrição de finalidade no consumidor. O reparo
também reconstruía seu payload final com o diagnóstico bruto depois de uma
projeção anterior já ter retirado a negativa; isso foi comprovado no caminho
instalado e corrigido no mesmo contrato de projeção de evidência.

Não se atribui uma causa psicológica ao Qwen. O que se prova é a admissão pelo
host de uma afirmação incompatível com sua fonte corrente, além da recirculação
do texto que já havia sido rejeitado. A nova coleta baseline não repetiu a
mesma negativa literal: inventou desconexão/falta de acesso. Foi preservada;
isso não substitui o RED causal nem prova que a falha histórica não existia.

Falsificações:

- Não era simplesmente falta de registro da habilidade: o plano e o catálogo
  do turno já possuíam o predicado disponível.
- A recusa simulada e o relato do usuário não são evidência de backend ausente.
  Controles com indisponibilidade real não podem ser reparados para sucesso.
- Não bastava adicionar mais contexto ou retirar um aviso: a negativa exata
  atravessava o juiz mesmo com fonte viva e instruções genéricas no prompt.
- Na projeção do reparo, remover o rascunho antes da escolha final de tarefa
  não bastava: o ramo de relato repunha o trecho negado a partir do diagnóstico.

## Contratos e responsáveis

| Responsabilidade | Owner | Regra |
| --- | --- | --- |
| Observar disponibilidade | `especialistas/mapa_habilidades.py` | Uma única leitura do snapshot vivo gera evidência pública e fonte privada nativa, ligada à entrada e ao turno. Domínio parcial/degradado não vira prova plena. |
| Vocabulário de predicado | `especialistas/capacidades.py` | Mesmo catálogo fornece ação, objetos e forma nominal. Léxico de um recurso não prova disponibilidade; só o predicado disponível sustenta contradição. |
| Preservar a fonte | `cognicao/fonte_capacidades_turno.py` e `contrato_fala.py` | Snapshot nativo, sem autoridade/efeito, disponível também na conversa. Não muda a tarefa para aula de capacidades e não usa JSON proposto pela IA como credencial. |
| Conferir alegação | `cognicao/validacao_contrato_fala.py` | Mesmo comparador em explicação e conversa: pessoa, finalidade, condição, citação, objeto genérico e disponibilidade corrente precisam corresponder. |
| Reautoria | `cognicao/qualidade_comunicacao.py` | Preserva fonte e assunto atual. Só depois da escolha final de tarefa projeta contradição sem o trecho rejeitado; diagnóstico completo continua no host. |

A fonte privada usa dados diretamente do snapshot, sem depender da documentação
didática: essa documentação pode estar vazia legitimamente com muitos domínios
ou disponibilidade parcial. O prompt recebe somente ações/objetos pertinentes,
sem inflar a personalidade permanente. Domínios genéricos isolados continuam
insuficientes para atestar qualquer ação específica.

A gramática de negativa cobre formas verbais e nominais declaradas no catálogo.
O caso real “não tenho controle direto de aplicações ou áudio” é lido como
coordenação integral de recursos genéricos; o léxico não autoriza controle.
Qualificadores compartilhados, como “sem autorização”, “áudio remoto” ou “no
computador de outra pessoa”, não são descartados para refutar o primeiro nome.
O objeto `aplicacao`, com plural derivado, pertence ao predicado de aplicativos,
não a uma exceção para o texto do log.

Ficção com snapshot vigente e fala delimitada continua ficção. Falas citadas
e atribuídas indiretamente, outros sujeitos, perguntas, condições e alvos
específicos não são promovidos a negativas gerais próprias. Esses limites
são conservadores e explícitos; não equivalem a prova semântica livre.

## RED e controles

RED inicial: **13 falhas/18 controles**. O candidato só foi aplicado depois
de reproduzir perda de fonte e aceitação indevida, com quatro domínios reais
do catálogo: sistema, música, IoT e navegador.

Os testes ampliados e a revisão independente expuseram limites do candidato:

- Conversão explícita das tuplas do catálogo para árvore JSON era necessária
  antes do snapshot; não se relaxou a guarda do snapshot.
- Documento didático vazio podia lançar exceção; RED preservado e fonte
  conversacional separada dessa projeção.
- Recortar causa em discurso indireto trocava o enunciador; dois REDs novos
  preservam atribuição, sem dispensar uma negativa própria em outra frase.
- Nova coleta real publicou a forma nominal de incapacidade. Três REDs
  ampliaram a leitura pelo léxico canônico, sem frase histórica no código.
- A coordenação inicialmente perdia uma restrição compartilhada: quatro REDs
  exigiram conferir a cauda inteira antes de separar os objetos.
- Controles de ficção e do mesmo predicado no modo explicativo protegeram
  finalidade e equivalência entre os consumidores.
- Replay instalado comprovou que a última montagem do reparo recolocava o
  trecho rejeitado. RED com/sem relato protege a projeção final e conserva o
  diagnóstico original intacto.

Módulo final `scripts/tests/test_capacidade_disponivel_na_conversa.py`:
**58 aprovados**. Revisão independente confirmou os recortes de fonte,
atribuição e coordenação; conferência final também validou 58 testes. Artefatos
intermediários e negativos preservados, sem tratar qualquer falha de preparação
como se fosse o RED causal original.

Foco integrado: **184 aprovações e cinco falhas anteriores**, com os mesmos
IDs do replay dos quatro owners congelados (`baseline_controles.xml`, 96
aprovações/cinco falhas). Os três módulos adicionais não estavam todos na
seleção ampla anterior. Quatro falhas exigem mensagens antigas sem negociação
de autoria; a quinta é uma expectativa de aceitação integral de uma resposta
sobre mídia indisponível. Não foram corrigidas, ignoradas ou enfraquecidas para
fazer este contrato parecer verde. O módulo novo está integralmente aprovado.

Regressão final em **138 módulos: 3.668 aprovados, cinco falhas e zero erros**;
14 ignorados, um desmarcado, um xfail e 30 subtestes aprovados. Os cinco IDs
coincidem exatamente com o replay dos controles adicionais sobre a base
congelada, e não reapareceram as 30 falhas/44 erros encerrados na etapa anterior.
Não se chama a seleção ampla de totalmente verde. As rodadas anteriores desta
pasta são intermediárias; a prova final é `regressao_integrada.xml` com fontes
estáveis e conferidas contra as coletas finais.

Produção alterada nesta investigação: `mapa_habilidades.py`, `capacidades.py`,
`contrato_fala.py`, `validacao_contrato_fala.py` e `qualidade_comunicacao.py`.
Owner novo: `fonte_capacidades_turno.py`. Um módulo novo de regressão. Não
foram editados os testes antigos para reduzir as cinco falhas basais. Os diffs
exclusivos usam as cópias congeladas da worktree, pois o diff contra HEAD contém
trabalho anterior que não pertence automaticamente a esta investigação.

## Composição instalada, replay e limites

Perfil isolado, composition root real e serviços instalados, Qwen
`qwen3:4b-instruct`, sem voz e com executores simulados. Houve coletas
intermediárias preservadas; nenhuma foi descartada por resposta inadequada.

`final_integrado`: nove publicações e sete HTTP200. Dois pedidos geraram somente
tentativas simuladas, `APP_OPEN` e `MEDIA_CONTROL`, com receipts negativos e
fala de não execução. A consulta histórica manteve o limite dos resultados.
A pergunta sobre abrir aplicativos recebeu capacidade disponível e informou
que nada foi acionado. O relato “eu retomei a música” recebeu “Entendi que você
retomou a música”, sem negar controle de áudio. O modo explicativo e a criação
ficcional também publicaram respostas dentro de seus respectivos contratos.

**Limites observados, sem esconder falhas:**

- “eu abri a calculadora” ainda recebeu pedido inadequado de contexto na
  coleta final. A ausência da negativa de capacidade não prova pertinência.
- `replay_final` reapresentou UMA emissão histórica na porta HTTP; não é nova
  geração dessa emissão. O juiz instalado não publicou a negativa. O reparo
  foi gerado pelo Qwen real com fonte corrente e sem o trecho rejeitado.
  O rascunho reconheceu o relato sem negar a capacidade, mas outra guarda
  rejeitou a conclusão e o turno terminou em limite de tentativas. Não se
  declara recuperação de resposta útil nesse replay.
- A construção “não posso realizar ações como abrir aplicativos” apareceu no
  reparo de um replay intermediário. A coleta não a publicou, mas esta família
  de paráfrase livre não recebe certificação universal do novo leitor.
- A baseline nova inventou desconexão/falta de acesso. A correção proíbe usar
  receipt negativo como prova desse diagnóstico; não é um juiz semântico
  universal de toda explicação de backend.
- A comparação usa o snapshot daquele turno, sem prometer que a disponibilidade
  de um turno anterior continua atual ou que a execução produzirá efeito.

Próxima fronteira demonstrada: conclusão útil do reparo/pertinência do relato,
mantendo capacidade, efeito e fala do usuário separados. Não ampliar orçamento,
trocar modelo ou ocultar falha para declarar compreensão completa.

Artefatos, hashes, diffs exclusivos e auditoria:
`resultados_testes/coerencia_capacidade_conversa_20261028/auditar.py`.
A auditoria passou: **533 fontes conferidas**, apenas os cinco owners
existentes e o novo arquivo declarados, snapshot final estável, HEAD preservado,
persistência isolada salva, IDs basais comparados e receipts negativos sem voz
ou efeito real. `git diff --check` passou nos arquivos modificados. Plano,
registro e mapa causal atualizados; nenhum commit criado.
