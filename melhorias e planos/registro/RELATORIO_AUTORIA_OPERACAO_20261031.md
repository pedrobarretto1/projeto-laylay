# Autoria conversacional não exige executor externo

Continuação do diagnóstico do observatório,autorizada por Pedro.
Base1197daf0d6b5e69b7243f571542bf17666274ea2,
codex/correcao-autoria-conversa-20261030.Worktree anterior preservada.
Baseline/status/SHA256 de539fontes em resultados_testes/autoria_operacao_20261031.

## Causa e contrato

Sessão20261031T155409Z-4eb70d7b,rodada-nova-02/03.Modelo escreveu narrativa e
piada;host publicou "Entendi a ação...".Transformações do discurso e forma
da resposta não eram reconhecidas pelo leitor compartilhado.Núcleos
"acrescente uma reviravolta inesperada nessa cena" e "responda naturalmente
e só com a fala" viravam pedidos práticos com autorização e execução exigida.
Verificador do plano então aplicava corretamente sua regra de não confirmar
ação sem executor,porém a um turno que não deveria ter essa obrigação.

Controle "responda brevemente" já é formato conversacional.O mesmo problema
é reproduzido sem modelo;retorno principal histórico teve sucesso na rodada3,
falsificando timeout/modelo pequeno/transporte como causa dessa substituição.
Destinos de e-mail/arquivo continuam operacionais,logo não retirar "responda"
ou "acrescente" de todos os verbos operacionais.Nem alterar a mensagem final.

Owner único de produção alterado:normalizacao_linguagem.tipo_transformacao_conversacional.
Dois papéis da mesma distinção:autoria com verbo+objeto discursivo+destino
discursivo integral;e formato com componentes combináveis de forma e canal
da própria fala.Ato integral não absorve destino externo nem ordem seguinte.
Reconhece determinantes,objetos narrativos,modificador e destino discursivo;
não escolhe fonte,nem concede verdade,execução ou efeito ao conteúdo criado.
Segmentação e modalidade existentes consomem esse leitor,sem novo parser no
executor.Nenhuma mudança em guardião,revisão,verificador de receipts ou orçamento.

Gramática é explícita e limitada,não um classificador semântico universal.
Destinos/atributos fora do recorte permanecem nos contratos existentes.
Forma de resposta não permite efeitos alegados pelo modelo nem dispensa
revisão factual ou suporte sobre o interlocutor.

## RED e controles

RED conclusivo com a fonte anterior congelada e testes finais:13falhas/
13controles,sem alterar produção para fazer replay.Fontes antigas carregadas
só no subprocesso de contraprova.Histórico e variantes de autoria/forma,
destino externo,ordem composta,citação,condição,negação e fonte da diretiva.

Primeiro RED incluiu expectativa operacional para "Inclua uma piada no
e-mail",não reconhecida pelo baseline;substituída pelo controle existente
"Acrescente uma piada no e-mail",sem ampliar o parser externo nesta etapa.
Uma asserção nova de fonte de todos os segmentos revelou normalização antiga
"comigo"→"codigo" no fim da rodada2,não causada pelo candidato.O vínculo
literal foi testado separadamente com diretiva íntegra;entrada histórica
mantém classificação testada.O comportamento lexical está aberto,sem patch.

Revisão independente (skill requesting-code-review) identificou omissão de
esse/este;RED demonstrativo confirmou uma falha e25controles.O candidato
agora declara os seis determinantes,sem regex de gênero incompleta.Revisão
final sem blockers:26testes e11probes adicionais de segurança aprovados.
Foco final169aprovados,zero falhas/erros,58,56segundos,seis módulos.

## Composição real instalada e autoria controlada

Factory da ponte,root,planner,cliente,orçamento,revisores,orquestrador e
observador nativos.HTTP fixo,perfis privados antes do import,audit hook
bloqueia rede/efeitos/persistência pessoal;voz desligada.Testes naturais
continuam com Pedro.Nenhuma conversa Qwen nova.

Fixture preserva entradas integrais,histórico e retornos pós-codec da sessão.
Esses eventos não são payload HTTP bruto:replay projeta a fala integral em
suporte_proposicoes.texto/fontes=[] e comandos=[],sem transformar a proposta
em prova.Partes históricas/"fala" pós-codec foram recusadas quando tentadas
como wire;sondas iniciais preservadas,não são prova conclusiva.

Replay pareado do único owner,mesma entrada/histórico/drafts:
baseline requer_execucao=True,contingência operacional nas duas rodadas;
candidato requer_execucao=False,texto_operacional vazio,e essa contingência
deixa de ocorrer.A revisão permanece ativa.Draft2 principal/reparo ainda
atingem resultado_operacional_sem_evidencia e prazo/orçamento;draft3 ainda
atinge afirmacao_interlocutor_sem_apoio.Sem fornecer reparo válido,a entrega
é contingência técnica,documentada.Não declarar que toda autoria histórica
foi recuperada ou que esses outros mecanismos estão corrigidos.

Controles positivos:mini narrativa explicitamente ficcional com a mesma
diretiva de enriquecimento publica a autoria literal "Na história,..." em uma
chamada;entrada histórica3 com autoria adequada também publica integralmente
em uma chamada,sem degradação.No schema ficcional existente,a moldura
"Na história,..." é exigida;fornecer "Eu diria..." nessa rota causou rejeição
de contrato de saída,sem justificar enfraquecer schema.

Sonda de recuperação histórica3:principal histórico recusado,segundo draft
adequado aprovado,duas chamadas,zero bloqueios,uma publicação,não degradada.
recuperacao_historica03.json.Propostas de APP_OPEN/MEDIA_CONTROL com receipts
forjados continuam bloqueadas e o reparo conversacional pode publicar.
Não se infere efeito ou autoridade da voz do modelo.Mensagens técnicas
residuais são evidências abertas,sem remendo por frase.

## Instalação e regressão

Original ae7b8775/main:hash antes de escrita,backup,delta apply_patch.Um owner,
dois novos módulos de teste e fixture textual;demais538fontes preservadas,
incluindo os três neurais com EOL diferente.Nenhuma sessão pessoal reiniciada.
Venv original297aprovados,zero falhas/erros em60,55segundos,oito módulos.
Arquivo de produção igual ao candidato e hashes estáveis após testes.
Regressão ampliada151módulos:4.538aprovados,25skips,um deselected,três subtests,
zero falhas/erros/xfails em499,04segundos.Mantido o filtro prévio do teste de
composição do perfil explicativo,sem exclusão nova.Auditoria XML confirmou
44IDs anteriores aprovados,ambos históricos musicais aprovados e539fontes
estáveis.Sem inferir suíte global ou qualidade espontânea do modelo.
Provas ampla.xml/log,original.xml/log,resumo_final.json e candidato.diff.

## Limites preservados

Rodada2:normalização lexical,alegação ficcional tomada como resultado
operacional e esgotamento de reparos permanecem fronteiras distintas.
Rodada3:suporte das afirmações sobre interlocutor permanece sujeito a revisão.
Não trocar modelo/aumentar orçamento/dispensar guardas para fazê-los passar.
Não há prova de espontaneidade,coerência longa ou efeito físico.
Sem voz,ações reais,commit,push ou desligamento nesta etapa.Nova sessão da
ponte é necessária para testar a instalação atual;testes de conversa com Pedro.
