# Resultado alegado: aspecto, polaridade e conferência compartilhada

Base c91cae1bd407b02db946ae7bc752d1ed3269bfd9, main, 535 fontes congeladas.
Artefatos: resultados_testes/efeito_perifrastico_20261029. Módulo histórico
test_falha_operacional_narrada.py preservado byte a byte; 34 REDs/71 controles
reproduzidos antes da produção. Não são 34 causas independentes.

## Duas fronteiras comprovadas

Cobertura de aspecto: o leitor de resultado reconhecia formas finitas e parte
das negativas, mas ignorava perífrases afirmativas de operação concluída.
“Consegui abrir” não era lido como efeito, embora “foi aberto” fosse. A expressão
de capacidade “consigo abrir” não deve receber essa mesma interpretação.

Consumo na entrega: a guarda final não consultava a mesma conferência de fonte.
“Não consegui abrir” já era recusado pela revisão, mas atravessava essa guarda.
Ao conectar a conferência, o planejador também precisa preservar a solicitação
de reparo, em vez de considerar a contingência segura uma resposta final válida.

O diagnóstico com/sem receipt falsifica falha geral do armazenamento de fontes,
classificação de autorização e indisponibilidade de modelo. A primeira leitura
diverge antes desses componentes. A guarda final tem uma divergência própria
para formas que já eram reconhecidas. diagnostico_base.json registra os controles.

## Contrato e produção

guardiao_alegacoes mantém uma representação de resultado narrado: intervalo,
escopo, polaridade e natureza externa. A gramática de aspecto concluído combina
auxiliar e operação, reutilizando o mesmo léxico nas negativas; não depende
de frase histórica, número do caso, nome de aplicativo ou intent específico.

Atos mentais/textuais têm um recorte de complemento discursivo integral. Nome
de arquivo, qualificação externa e outra operação não herdam essa classe.
Coordenação de infinitivos conserva o escopo do auxiliar; novo auxiliar abre
outra ocorrência. Hipótese, incerteza, pergunta referida, citação literal e
ficção vigente reutilizam seus contratos canônicos, sem virar comprovação.

Revisão e guarda final consultam a mesma conferência de fonte. Disponibilidade
não basta; proposta da IA não é receipt; outra operação, alvo ou polaridade não
empresta fonte. Fala do usuário em primeira pessoa não comprova ação da Laylay;
sua citação literal pode continuar como ocorrência de fala, sem efeito.

Quando falta fonte, a guarda retém a alegação e oferece uma conclusão segura,
marcando que o conteúdo requer reparo. plano_turno preserva o rascunho original
para a qualidade solicitar nova autoria. Isso impede que o texto de contingência
oculte o RED e seja tomado como resposta útil. Não altera orçamento ou executor.

Produção alterada: guardiao_alegacoes.py e plano_turno.py. Nenhum outro arquivo
de produção, modelo, personalidade, limite de tentativas ou comando alterado.
O reconhecimento lexical é um recorte explícito; não certifica toda paráfrase
de efeito, implicação ou semântica irrestrita do português.

## Evidência final

Os 105 casos históricos passaram, preservando os 34 IDs anteriormente vermelhos
e os 71 controles. Outros 26 controles passaram: polaridade, fonte inadequada,
ato discursivo, arquivo com nome parecido, coordenação, autoria, ficção nativa
e tentativa de substituí-la por dict proposto. Foco total: 131 aprovados.

Nove testes da composição instalada passaram, com persistência isolada e folhas
HTTP/áudio/efeito controladas. Resultado inventado em aplicativos, música ou
arquivos é rejeitado e recebe reparo; reparo inválido não libera o rascunho.
Receipts propostos dentro de comandos da IA não viram fonte. Entrega direta,
sem passar pela autoria principal, também não publica efeito sem evidência.
Não houve conversa nova, geração Qwen, voz ou efeito real; testes de conversa
continuam com Pedro. Essa composição não mede a taxa de acerto do modelo real.

Regressão ampliada: 158 módulos, 4.073 aprovados, zero falhas/erros; 14
ignorados, um desmarcado, um xfail e 30 subtestes. Nenhum ID anterior removido.
Auditoria de 535 fontes confirma somente as duas alterações declaradas e
preserva a worktree anterior. Nenhum commit criado.

## Nova rodada enviada por Pedro

O journal 20261029T134901Z-e78610af foi localizado. As 535 fontes históricas
coincidem com a base anterior a este candidato, portanto os casos novos não
foram atribuídos a uma versão suposta. Entradas/propostas/publicações das
rodadas 003/005/011/013/014 foram preservadas separadamente em
resultados_testes/rodada_verdade_autonomia_20261029, com proveniência/hash.

Essas fronteiras de geração textual, finalidade, revisão de conversa, retomada
da própria argumentação e pertinência do reuso não são encerradas por esta
correção de resultado operacional. Proposta pertinente não é automaticamente
resposta correta: a revisão histórica também precisa conferir o que a Laylay
realmente disse antes, sem adotar uma lembrança inventada pelo modelo.
