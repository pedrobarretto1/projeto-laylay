# Recuperação: separar estado nativo e transporte do reparo

Continuação posterior: RELATORIO_RECUSA_PRIMEIRO_REPARO_20261029.md comprova
a falsa recusa do posicionamento avaliativo pelo verificador biográfico.
No replay automatizado corrigido, o primeiro reparo é publicado integralmente
em duas chamadas, sem terceira tentativa. O RED abaixo é o resultado preservado
desta etapa anterior, não o estado posterior desse caso específico. A admissão
continua recusando terceira chamada quando o reparo é realmente inválido.

Validação final conjunta, após a extensão do adjunto com conector: 150 módulos,
3.871 aprovados, cinco falhas basais exatamente pelos mesmos IDs, nenhuma
nova e zero erros. Auditoria de 535 fontes aprovada, cinco fontes de produção
alteradas no total das quatro causas; nesta causa, três fontes. Nenhum ID
antigo removido. Auditoria/diff disponíveis nesta pasta de artefatos.

HEAD c91cae1bd407b02db946ae7bc752d1ed3269bfd9, main. Base própria de 535
fontes congelada após os candidatos de repetição e classificação. Artefatos:
resultados_testes/projecao_reparo_nativo_20261029. Worktree anterior preservada.

## Primeira divergência e falsificações

O replay de repetição recusou o corpo antigo. O primeiro reparo trouxe um
título novo, mas foi recusado por alegação pessoal sem apoio; a autoria final
então informou erro_chamada_typeerror. Essa sequência não é uma falha única.

O contrato de reparo contém RespostasAnterioresTurno nativo, capturado pelo
host para julgar reuso e sem autoridade operacional ou factual. A primeira
rota de reparo o retirava antes do JSON; criar_fala_autoral copiava o contrato
integralmente e tentava json.dumps. A exceção era anterior ao callback.

Dois pedidos criativos, com contratos produzidos pelos owners reais, repetem
a falha com zero chamadas. Callback funcionando sem esse objeto e a rota
inicial serializável falsificam indisponibilidade geral do transporte e
incapacidade do modelo de gerar texto como causas desse TypeError. O orçamento
não pode ser a origem de uma exceção anterior ao cliente; poderá ser a próxima
fronteira depois de removê-la.

## Contrato compartilhado

continuidade_resposta projeta os limites do reparo para transporte, excluindo
o campo de estado privado. qualidade_comunicacao e autoria_conversacional
usam essa mesma projeção. A fonte nativa não é convertida para str, dict ou
lista de evidências. O objeto original fica intacto no plano e continua
disponível ao juiz posterior. Estado falso no mesmo campo também não é
projetado. Tipos desconhecidos em outros campos continuam falhando fechados;
não há serializador permissivo nem descarte geral de erros.

Cinco REDs e dois controles antes da produção. Sete casos novos aprovados;
foco com autoria, continuidade, reuso e alegações pessoais: 115 aprovados.
Proposta operacional na autoria final continua rejeitada; projeção não dá
permissão de executar nem certifica o texto produzido.

## Composição instalada e limite remanescente

Replay usa a proposta principal histórica e o primeiro reparo já registrado,
mantendo os dois motivos de recusa. Esses dois HTTPs são reconstruídos dos
artefatos, sem reproduzir a latência antiga; não são novas gerações Qwen.
As chamadas posteriores usam cliente e orçamento reais, se admitidas.

Owners da base reproduzem erro_chamada_typeerror e não chegam à admissão da
autoria final. Owners corrigidos ultrapassam a serialização e chegam ao
orçamento, que recusa a terceira chamada: principal=1, reparo_comunicacao=1,
limite_chamadas_turno=2, chamadas_bloqueadas=1 por limite_chamadas.

Não houve nova geração Qwen final nesta coleta, nem título útil publicado.
O TypeError foi removido no caminho composto; recuperação útil permanece RED.
Não aumentar o limite para transformar esse resultado em verde. A próxima
investigação deve estudar o planejamento de recuperação e a recusa do primeiro
reparo antes de atribuir toda falha ao orçamento. Sem voz, efeitos reais ou
commit; nenhuma alteração no orçamento, personalidade, modelo ou segurança.

Hipótese para a próxima investigação, ainda sem candidato: o guardião
afirmacoes_interlocutor reconhece você + estar + predicado e compara esse
predicado com relatos pessoais literais. O primeiro reparo trazia concordância
argumentativa (“você está certo”), não uma nova cena biográfica. É necessário
provar a distinção entre reconhecimento social e atribuição factual, com
controles que continuem recusando estado pessoal inventado. Não excluir essa
expressão por regex nem assumir que a proposta da IA prova a própria correção.
