# Projeção descritiva de critério no contexto — 25/10/2026

## Raiz e base

Durante a continuação autorizada da relação entre descrição e critério, a
primeira coleta instalada/Qwen revelou uma falha anterior ao julgamento:
turnos posteriores à publicação do critério ficavam sem resposta. A primeira
fronteira RED foi priorizada, antes de alterar a seleção semântica da pergunta.

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, `main`, worktree suja
preservada. Base/status/hashes de530 fontes em
`resultados_testes/relacao_criterio_20261025/baseline.json`. A cópia anterior de
`registro_semantico.py` está em `fontes_antes/`; demais mudanças do HEAD não
pertencem a este candidato. Sem voz, efeitos externos, commit ou configuração.

`baseline_dialogo/` e `baseline_rastro/` preservam a reprodução: leitura,
preferência e porquê publicavam resposta; os três turnos seguintes não chegavam
ao HTTP e não publicavam nada. O erro era
`CriterioAutoralPublicado is not JSON serializable`. A fonte nativa já estava
no histórico; a persistência a havia projetado corretamente em descrição JSON.

## Primeira divergência e falsificações

`recuperar_evidencia_da_fala` entrega um snapshot nativo para revisão do host.
Isso é correto: converter essa fonte na recuperação eliminaria sua identidade
tipada para os consumidores que a validam. `formatar_evidencia_da_fala`, porém,
tentava fazer `json.dumps` desse mesmo objeto para o prompt genérico. As rotas
fechadas de opinião anteriores não haviam exposto esse caminho.

`projecao_red.xml` reproduziu sete falhas na fronteira exata, em música/software/
bebidas, com e sem fundamento aninhado e com receipt negativo associado.
Um controle de tipo desconhecido já era rejeitado, como deve continuar sendo.
`contraprovas.xml` falsifica falha geral do JSON/registro e falha da recuperação:
fala sem anexo já é transportada; projeção durável já descreve o anexo; o
snapshot recuperado conserva o tipo nativo. HTTP/modelo/timeout não explicam a
falha que ocorria antes do envio.

## Contrato corrigido

Produção desta raiz: somente `memoria_mental/registro_semantico.py`.
O formatter reaproveita `projetar_registro_semantico_persistivel` para os itens
observados antes de montar o JSON do prompt. Não entra um serializer genérico,
`default=str`, fallback permissivo ou cópia privada de lógica de tipo.

O contrato compartilhado passa a respeitar as duas representações:

- Host/revisores: fonte nativa da publicação, identidade e validade existentes.
- Prompt/armazenamento: descrição do mesmo registro, com campos de prova e
  autoridade falsos, sem possibilidade de reconstruir credencial nativa.

IDs, timestamps, conteúdo e receipts são preservados. Alterar a descrição
decodificada não modifica o registro vivo. Tipo de anexo desconhecido continua
falhando explicitamente. A projeção não concede execução ou verdade factual.

## Validação e fronteira seguinte

Onze testes novos: seis combinações de domínio/base, receipt e isolamento,
rejeição de tipo desconhecido, dois controles e composição instalada. O teste
de identidade de objeto foi corrigido: o seletor já devolvia cópia; comparar
tipo/valor preservado é o contrato, não exigir a mesma instância Python. O
regressivo instalado também passou a distinguir projeção contextual de pacote
fechado escolhido depois: não se deve exigir que todo prompt final repita um
anexo que o owner daquele pacote não precisa expor. A prova central permanece
envio/publicação alcançados; o conteúdo descritivo é conferido no formatter.

`contrato_green.xml` e `instalada_final.xml` aprovam os controles. Revisão
independente comparou a cópia anterior, confirmou ausência de mutação/promoção
de autoridade e não encontrou bloqueador. `candidato_dialogo/` comprovou seis
turnos com seis HTTP200 e seis respostas. Os três turnos antes silenciosos
deixaram de falhar na serialização.

Essa coleta tornou visível **outra raiz**: as respostas agora existentes
discutiam resultados operacionais quando o usuário perguntava sobre critério.
Esse RED não foi chamado de GREEN semântico nem corrigido no formatter. Sua
investigação separada está em `RELATORIO_RELACAO_CRITERIO_20261025.md`.

A regressão final conjunta teve2.858 aprovados em113 módulos distintos,com os
mesmos nove failures e44 errors anteriores por ID,14 ignorados,um desmarcado
e30 subtestes aprovados. Nenhum desses REDs foi encerrado. A lista individual
fica na comparação. O foco final conjunto aprovou265 testes e ignorou dois.

A regressão final conjunta, a comparação de falhas por ID e os hashes desta
raiz estão em `regressao.xml`, `comparacao_regressao.json`,
`projecao_contextual.patch` e `entrega.json` no diretório de evidências. O teste
de runtime usa `laylay.py` e owners instalados, persistência isolada, Qwen real,
voz bloqueada e executor simulado. Não comprova entrega de áudio ou recarga da
sessão desktop. F1/C5/C7/AUT e mudanças paralelas preservados.
