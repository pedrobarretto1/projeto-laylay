# Critério declarado na autoria e vinculado à publicação — 25/10/2026

## Escopo e base preservada

Pedro autorizou estudar e registrar critérios na autoria para explicar gostos,
sem promover proposta da IA a prova. Validação sem voz e com ações simuladas.
Continuação do contrato de opinião autoral, sem criar outra raiz para o mesmo
mecanismo e sem consolidar F1/C5/C7/AUT. HEAD
`c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`; worktree suja
preservada. Nenhum commit, shutdown ou mudança de modelo/voz/configuração.

`resultados_testes/criterio_autoral_20261025/baseline.json` congela HEAD,
branch, status e hashes de 529 fontes anteriores. `fontes_antes/` preserva os
owners antes do candidato; `candidato_contra_base.patch` delimita a alteração
desta investigação, inclusive arquivos que já eram novos na worktree.

## Raiz e falsificações

O contrato anterior registrava a posição publicada, mas não oferecia um campo
para declarar seu critério na emissão original. Os seis turnos do baseline
instalado receberam HTTP200 e publicaram corretamente o limite de motivo ausente.
Portanto, não eram falha de transporte ou perda da preferência entregue.

Primeira fronteira RED: o protocolo de autoria recusava `criterio_autoral`
como campo não contratado. Separadamente, a captura de uma emissão explícita
descartava esse metadado. `contrato_red.xml` conserva ambas as falhas. Não era
possível corrigir apenas o prompt nem pedir uma explicação posterior: isso
reconstruiria um critério histórico que nunca foi registrado. O registro de
publicação, já existente, também não podia tornar a proposta uma causa comprovada.

Foram falsificadas as alternativas: preferência ausente no histórico; serviço
LLM indisponível; informação textual suficiente para provar a causa; metadado
proposto suficiente para comprovar publicação. A prova exigida agora é somente
de declaração e entrega, nunca de verdade factual ou causalidade psicológica.

## Contrato e responsáveis

1. `opiniao_autoral`: negocia um critério na emissão original de uma escolha
   subjetiva. Códigos iniciais: curiosidade, afinidade estética, clareza,
   simplicidade ou não declarado. São critérios normativos adotados naquele
   ato, sem afirmar propriedades do objeto, sensações ou experiência humana.
   Nenhum gosto ou critério específico é fixado pelo host.
2. `suporte_autoria`: conserva o código como **proposto** na mesma emissão,
   consulta, fala e turno. O critério não é inserido na lista de fontes. A
   declaração continua pendente de revisão; prova e autoridade permanecem falsas.
3. `opiniao_autoral`: admite o vínculo somente com suporte nativo da mesma
   emissão e realização integral aceita pela revisão. Reescrita precisa de
   declaração própria; mescla não herda o critério de uma das partes. O código
   não pode ser criado retrospectivamente numa pergunta de motivo.
4. `orquestrador_fala_runtime`: captura o vínculo junto à emissão e somente o
   entrega ao registro após callback de publicação bem-sucedida, com conteúdo
   exato e sessão compatível. Proposta ou entrega recusada não viram publicação.
5. `criterio_autoral` e `registro_semantico`: vinculam critério, hash normalizado
   da emissão, consulta, declaração, ocorrência e timestamp. A consulta posterior
   exige origem e portadora publicadas no registro canônico. Repetição e
   esclarecimento mantêm a origem; não renovam seu TTL de 900 segundos. Segundo
   canal não cria outra autoria nem reescreve a ocorrência. Dict serializado,
   outra fala, outra consulta, outro turno, origem ausente ou expirada não bastam.
6. `persistencia_memoria`: usa a projeção do registro para guardar a descrição
   em JSON, sem reconstruir uma credencial nativa a partir desses dados. O
   snapshot não modifica o estado vivo. A renovação de sessão já existente
   limpa as falas transitórias. Não foi criado gosto durável nem restauração
   automática de critérios como fatos.

Uma explicação informa o critério declarado naquela autoria. Ela não transforma
"simplicidade" em "Linux é mais simples", nem "afinidade estética" em prova de
uma emoção vivenciada. Sem critério registrado, conserva o limite anterior.
Alvo/predicado/polaridade divergentes continuam sem criar outro gosto. A recusa
dessa premissa possui publicação própria e não transporta o critério alheio.

## Provas do candidato e correções durante a validação

`publicacao_red.xml` e `publicacao_green.xml` guardam a introdução do vínculo no
writer. Os controles seguintes encontraram uma incompatibilidade do candidato
com a confirmação por outro canal: o novo timestamp alterava a identidade do
critério. O writer passou a conservar o timestamp da publicação original.
Metadados adulterados são recusados sem lançar exceção na leitura.

`candidato_dialogo/` chegou às explicações com Qwen real, mas revelou erro ao
salvar memória: o dataclass novo não era serializável em JSON. Essa coleta não
é GREEN de entrega completa. `persistencia_red.xml` reproduz a fronteira real;
a projeção descritiva corrigiu-a sem conversão genérica de objetos desconhecidos
nem relaxamento dos validadores. Seleção de persistência e contratos vizinhos:
138 testes aprovados, incluindo conversa múltipla e persistência concorrente.

`validacao_vizinhos/` encontrou outra incompatibilidade do candidato: uma recusa
correta de premissa divergente tentava transportar o critério da opinião anterior,
e o registro rejeitava a publicação. `premissa_red.xml` demonstra duas variantes.
A preparação do vínculo agora exige que a declaração original faça parte da
realização integral aceita. A recusa é publicada sem critério; não há exceção
por rock, indie ou frase do usuário.

O primeiro regressivo dessa borda passou a asserção causal do ajuste e depois
falhou por enviar ID numérico diretamente a um writer que exige string. A
fixture foi corrigida para usar a mesma projeção de identidade do orquestrador;
a expectativa do contrato não foi enfraquecida. A coleta intermediária e o XML
inicial permanecem preservados. A fixture HTTP comum também passou a declarar
`nao_declarado` quando o schema exige o campo, conservando seus resultados neutros.

## Validação final e limites

Resultado final: **36 casos novos**, **124 testes focados aprovados**. Regressão
ampla em **108 módulos distintos**: **2.701 aprovados**, nove falhas, 44 erros,
14 ignorados, um desmarcado e 30 subtestes aprovados. Os IDs das nove falhas e
dos 44 erros são exatamente os mesmos da etapa anterior; a comparação foi
executada, não inferida pela contagem. Permanecem o comando natural antigo da
Calculadora, oito expectativas antigas de pacote/tokens e 44 erros da fixture
que tenta serializar `PerspectivaEnunciador`. Nenhum desses REDs foi ocultado
ou encerrado por este candidato.

Qwen final: **16 turnos, 16 HTTP200, 16 publicações e 16 persistências gravadas
e relidas**, com 530 fontes estáveis durante cada coleta. Seis escolhas originais
registraram critérios, e as explicações/esclarecimentos conservaram as respectivas
origens. O controle operacional separado tem três turnos e um receipt negativo
simulado, sem efeito real. A auditoria final conferiu todos esses resultados.

Resultados finais são registrados em `entrega.json`, `contrato_entrega.xml`,
`regressao_entrega.xml` e `comparacao_regressao.json`, após a auditoria das coletas.
As coletas finais `entrega_dialogo/` e `entrega_vizinhos/` usam `laylay.py`,
factories e owners instalados, Qwen real via Ollama local, persistência isolada,
voz bloqueada e adaptador externo simulado. Não usar uma composição manual como
substituta desses caminhos. A auditoria confere a resposta HTTP original, o
critério efetivamente publicado, a continuidade de origem, as flags de prova
falsas e os snapshots realmente gravados e relidos pelo armazenamento.

O controle `entrega_fumaca/` é separado: só receipt negativo de ação simulada
pode ser anunciado, sem abrir aplicativo. Não contar esse controle como
explicação de gosto. Não se prova entrega de voz nem recarga da sessão desktop.

O critério é uma declaração avaliativa de vocabulário fechado, vinculada à
autoria, não um verificador universal de razões. Explicações factuais mais ricas
ainda precisam obter fontes pertinentes, conferir a implicação de cada
proposição e distinguir essa avaliação de causa histórica. Preferências duráveis,
categorias sem cobertura, causalidade livre, clipboard e prazo mantêm seus
limites e owners anteriores. Esta etapa não encerra a compreensão geral da Laylay.

Produção deste candidato: `criterio_autoral.py` (novo), `opiniao_autoral.py`,
`suporte_autoria.py`, `registro_semantico.py`, `persistencia_memoria.py` e
`orquestrador_fala_runtime.py`. Os dois últimos participam porque são os owners
reais da entrega e persistência da declaração; não há patch em cada habilidade.
Executor, modelo, voz e configuração foram reutilizados.
