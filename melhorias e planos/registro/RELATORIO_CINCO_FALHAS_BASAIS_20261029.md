# Cinco falhas basais — expectativas e contratos independentes

Fechamento: seleção herdada ampliada para 155 módulos, 3.933 aprovados, zero
falhas/erros; 14 ignorados, um desmarcado, um xfail e 30 subtestes. Os cinco
IDs antigos estão presentes e aprovados; nenhum ID anterior foi removido nem
o filtro anterior alterado. Auditoria confirma 535 fontes de produção idênticas.
As 34 falhas do módulo adicional isolado permanecem abertas e estão discriminadas
abaixo; esse resultado não declara toda a suíte do repositório verde.

Base: c91cae1bd407b02db946ae7bc752d1ed3269bfd9, main, 535 fontes congeladas.
As duas fontes de testes antigos também foram preservadas antes das edições.
Artefatos: resultados_testes/cinco_falhas_basais_20261029.

## Resultado do diagnóstico

Os cinco IDs foram reproduzidos: cinco falhas e 86 controles aprovados. Eles
não representam cinco defeitos demonstrados do runtime. Quatro expectativas
precedem a negociação obrigatória de autoria; a quinta exige aceitação global
de uma fala que contém um estado externo sem fonte.

Não houve patch de produção. Vinte e cinco controles novos passaram com as
535 fontes exatamente iguais à base dos cinco REDs, antes de atualizar qualquer
expectativa antiga. Corrigir a produção para satisfazer as expectativas antigas
retiraria proteções válidas. As correções ficaram nos contratos dos regressivos.

## Quatro IDs: projeção didática não é negociação de autoria

Mutações históricas: autorização do turno, modalidade mista, ID do contrato
obsoleto e documento didático vazio. ContextoPromptRuntime já recusa corretamente
a projeção compacta: contexto_fechado=False, histórico preservado e nenhuma
documentação didática daquele contrato no envio.

Como a ocorrência do usuário ainda está ligada ao turno atual, concluir chama
negociar_autoria_com_fontes. O protocolo obrigatório de suporte é acrescentado
ao envio completo, sem modificar a memória. O teste antigo exigia igualdade
literal de todas as mensagens e falhava nessa instrução de segurança legítima.
No controle com ID do próprio turno obsoleto, não há vínculo de autoria atual:
o envio permanece idêntico. Esse controle já estava aprovado e foi preservado.

Falsificações: não houve projeção fechada indevida, vazamento do documento,
alteração do histórico ou dispensa de autoria. Os novos controles conferem o
schema, recusam resposta sem suporte e referência inventada, e preservam a
conversa nos transportes normal e rápido. Nenhum owner foi alterado.

Contrato dos regressivos antigos agora confere essas responsabilidades
separadamente. Função, parâmetros, fixtures, decorators e IDs foram mantidos;
somente o corpo da expectativa foi atualizado.

## Um ID: disponibilidade não aprova o restante da fala

A fixture sobre retomar música combina duas partes:

- negativa de controle de áudio, compatível com o catálogo indisponível;
- referência ao dispositivo ou app “que está tocando”, sem fonte desse estado.

O verificador não produz capacidade_documentada_negada. A única recusa é
resultado_operacional_sem_evidencia. A declaração de indisponibilidade sozinha
é aceita. Logo, falha de recuperação da disponibilidade e contradição falsa
do catálogo foram falsificadas; o teste confundia ausência de contradição de
capacidade com aprovação integral de todas as proposições.

O contrato antigo passa a exigir ausência da contradição de capacidade e
ausência de autoridade. Novos controles mantêm a recusa integral da fixture
histórica, aceitam o limite sozinho nos quatro domínios e recusam estado
inventado em música, aplicativos e navegador. Condição explícita não é
tratada como observação atual. Nenhuma regra de evidência foi removida.

## Composição instalada, sem teste de conversa

Seis controles automatizados usam a composição de laylay.py, memória isolada,
HTTP controlado, voz desativada e folhas de efeito interceptadas. Não chamam
Qwen nem iniciam uma conversa nova. A visão do contrato usada na projeção pode
ficar obsoleta; o plano real e a autoridade permanecem sob seus owners.

A projeção inadequada continua no fluxo completo, com autoria obrigatória e
resposta instrutiva publicada. Propostas APP_OPEN/MEDIA_CONTROL da IA não
autorizam ações. No catálogo indisponível, a declaração de limite é publicada;
se vier acompanhada de estado inventado, este é recusado e o reparo legítimo
preserva a indisponibilidade, sem bloqueio extra de orçamento.

Ensaios de preparação foram preservados: um apontava o getter na fachada
congelada RegistroPreparacaoConversa, em vez do serviço delegado; outro exigia
texto idêntico mesmo quando uma proposta indevida recebe reconhecimento canônico
de erro. Não são raízes de produção nem justificaram patch. O contrato final
exige instrução preservada, uma publicação, ausência de efeito e nenhum HTTP extra.

## Fronteira adicional aberta — fora dos cinco IDs

A ampliação a test_falha_operacional_narrada.py revelou 34 falhas e 71 controles
aprovados. Esse módulo não estava nos 152 módulos da seleção anterior. Os mesmos
34 IDs falham no foco combinado e na execução isolada; as 535 fontes de produção
continuam iguais à base. Assim, ordem dos outros módulos e patch de produção
desta investigação não explicam esses resultados.

Os casos cobrem perífrases de efeito como “consegui abrir”, negativa, fonte,
qualificação e reparo. Registrar como família a investigar, sem declarar 34
raízes independentes nem chamar essa cobertura de encerrada. IDs e resultados
ficam em pendencias_modulo_adicional.json, diagnostico.json, foco.xml e
modulo_adicional_isolado.xml. Não foram apagados, ignorados nem enfraquecidos.

Essa pendência não foi misturada ao alinhamento dos cinco testes. A seleção
ampla herdada mantém seus módulos e seu filtro anterior; os três novos módulos
foram acrescentados. Seu resultado deve ser reportado com esse escopo, sem
afirmar que toda a suíte do repositório está verde.

Sem alterações em produção, modelos, personalidade, orçamento ou revisão.
Dois testes existentes atualizados, três módulos novos com 25 controles.
Nenhum commit; os testes de conversa continuam com Pedro.
