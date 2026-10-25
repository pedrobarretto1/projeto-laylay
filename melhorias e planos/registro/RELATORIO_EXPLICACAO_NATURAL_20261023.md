# C5/P01 — reformulação natural com derivação delimitada

**Estado final: estudo concluído neste recorte, candidato rejeitado e retirado.
Nenhuma alteração de produção mantida. Ensino natural livre continua aberto.**

Base: `main`, HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`, worktree
previamente modificada. Escopo autorizado: estudar, comprovar a primeira
divergência, corrigir o contrato compartilhado e validar na composição real.
Inventário, hashes e backups: `resultados_testes/explicacao_natural_20261023/`.
Nenhum commit ou ativação ampla de pesquisa faz parte deste trabalho.

## Estudo e alternativas

O prompt exige exemplo mesmo sem exemplo na fonte. Isso é uma tensão real,
mas não foi demonstrado como causa suficiente da extrapolação: a ablação
somente em memória, com o Qwen instalado, leu duas páginas por turno e ainda
limitou 3/3 respostas por acréscimos/ausência de referências. Não aplicar esse
ajuste como se resolvesse autoria natural. O experimento está em
`ablation_sem_exemplo/conversa.json`; os hashes de produção permaneceram iguais.

Não afrouxar o revisor com similaridade lexical, confiança da autora ou um
segundo parecer da IA. Não promover a antiga composição extrativa a solução
de ensino natural. A alternativa delimitada é conferir uma transformação
estrutural de condição explícita, preservando **inteiras e literalmente** as
duas cláusulas e sua direção. Isso amplia o mecanismo compartilhado de
derivação, sem pressupor suporte para sinônimos, exemplos ou explicações livres.

## Primeira fronteira e contrato

Fonte individual atual → proposta ligada à ocorrência → comparação da revisão.
A comparação atual conhece identidade integral e simetria de atributo/valor,
mas não a reordenação `Se P, então Q.` ↔ `Q, se P.`. RED unitário: seis
positivos falham em `apoio_semantico_pendente`; 28 controles negativos passam.
RED instalado: oito positivos falham na mesma primeira fronteira; oito
negativos passam. Em todos os 16 ciclos o leitor instalado entregou duas
fontes, a finalidade didática e o vínculo da proposta chegaram à revisão.

Isso falsifica omissão de fontes, indisponibilidade de leitura, perda de
transporte e erro de geração como causas necessárias **deste recorte**. Não
falsifica essas causas em outras conversas e não prova a verdade das páginas.

Regra proposta: somente duas formas integrais e delimitadas, cláusulas opacas
sem pontuação interna/aspas/condicionais aninhadas, correspondência literal de
P e Q, mesma direção, nenhum conteúdo descartado. Modais, negações e ressalvas
pertencem às cláusulas; não os remover, normalizar ou reinterpretar. Fonte com
mais contexto fica fora da regra. Maiúsculas dentro das cláusulas também não
são normalizadas. Certificado recalculado pelo host com intervalos e hashes;
nenhum certificado fornecido pela autora é consumido.

## Responsáveis e critérios

| Owner | Responsabilidade e validação |
| --- | --- |
| `cognicao/revisao_suporte_autoria.py` | Derivar somente a equivalência sintática descrita, mantendo admissibilidade, TTL, autoria, URL e flags falsas de verdade externa/semântica livre/autoridade. |
| Contratos existentes de autoria e entrega | Conservar representação única, cobertura literal e conclusão observável. Nenhuma nova rota de execução ou recuperação permissiva. |
| Leitor/contexto instalados | Permanecem responsáveis pela recuperação e proveniência. Nenhum buscador novo ou ativação ampla. |

Plano de implementação e prova (skills de investigação, planejamento e TDD;
localização/histórico e autorização atuais prevalecem sobre defaults de skills):

- [x] Congelar base e falsificar a hipótese de mero prompt.
- [x] Reproduzir RED canônico e RED da factory instalada antes do candidato.
- [x] Aplicar candidato mínimo no owner compartilhado de revisão (depois retirado).
- [x] Conferir equivalência, negação, escopo, direção, origem e adulteração.
- [x] Repetir os 16 ciclos com o leitor e composição instalados.
- [x] Usar Qwen real e registrar fala final, proposta, fontes, transporte e efeitos.
- [x] Revisão independente e falsificação do candidato; não promover GREEN intermediário.
- [x] Retirar somente o candidato e conferir igualdade byte a byte do owner anterior.
- [x] Rodar regressivos finais e registrar falhas anteriores separadamente.
- [x] Registrar limite e próxima fronteira sem encerrar ensino natural geral.

## Limites da interpretação

Trata-se de equivalência de uma condição **declarada textualmente**, não de
prova da realidade de P ou Q, causalidade, necessidade, execução ou pertinência
pedagógica. Gramática fechada não equivale a compreensão irrestrita de língua.
Fonte artificial nos controles prova o contrato; não é evidência factual do
mundo. A ablação de autoria livre continua RED mesmo que a nova derivação
fique GREEN. Naturalidade humana e aulas completas exigem avaliação própria.

## Falsificação do candidato e correção do diagnóstico

Os primeiros controles retornaram 181 GREEN/6 skips no foco e os 16 ciclos
instalados passaram. A regressão intermediária teve 1447 GREEN, 30 subtests,
14 skips, duas falhas anteriores e uma deselection. **Esses resultados não
autorizavam a implantação.** A revisão independente reproduziu dois mecanismos:

1. `Se o teste falha, então o alarme toca。 a escrita foi concluída.` →
   `o alarme toca。 a escrita foi concluída, se o teste falha.`. A pontuação
   Unicode divide afirmações; o deslocamento muda qual delas é condicional.
   O reconhecimento excluía pontuação ASCII, não toda fronteira de sentença.
2. `Se o modo de teste está ativo, então o motor funciona a menos que a trava
   esteja acionada.` → `o motor funciona a menos que a trava esteja acionada,
   se o modo de teste está ativo.`. Não ter a palavra `se` dentro de uma
   captura não comprova ausência de condição aninhada nem seu alcance.

Aspas Unicode também atravessavam a exclusão pretendida. Seis contraexemplos
nas duas direções falharam na função pública (`candidato_rejeitado.xml`).
No caminho instalado, com páginas lidas por ambos os domínios nas duas rotas,
oito falsos aceites foram reproduzidos (`contraexemplos_instalada.xml/json`:
8 RED,16 GREEN). Não é somente uma hipótese sobre regex ou um parecer da IA:
há proposta, snapshot, derivação indevida e fala publicada no mesmo ciclo.

A primeira fronteira incorreta do **candidato** foi tomar uma captura lexical
por cláusula atômica já validada. A premissa de equivalência não estava
comprovada; nomes de papéis e preservação de palavras não resolvem escopo.
Uma blacklist adicional para os exemplos encontrados repetiria esse erro.
Por isso a regra inteira foi retirada, sem ajustar os testes para aceitar
esses falsos positivos. O candidato permanece auditável em
`candidato_rejeitado.py.txt` e `candidato_rejeitado.diff`.

`revisao_suporte_autoria.py` voltou exatamente aos bytes da base desta tarefa,
incluindo as mudanças anteriores da worktree. A especificação de positivos
continua RED e foi preservada nos arquivos `especificacao_condicional_*.py`
do artefato; não é anunciada como regressão resolvida. Os bloqueios descobertos
viraram regressivos em `scripts/tests/test_escopo_condicoes_na_revisao.py`.
Nenhum reset, restauração pelo Git ou sobrescrita do trabalho paralelo.

## Qwen real e limites de runtime

`qwen_condicionais/conversa.json` registra quatro turnos pela composição
instalada, com duas fontes por turno, serviço criado pela factory reconectado
por identidade e o modelo configurado mantido. Dois pedidos guiados de
reordenação terminaram em timeout do orçamento existente; não alcançaram a
nova derivação. O controle que pediu eliminar a condição e a explicação livre
foram limitados por falta de apoio. Não houve aula natural aprovada nessa coleta.
Nenhuma retentativa permissiva ou alteração de timeout/modelo/voz foi aplicada.
Os dados do Qwen não provam equivalência; os controles de transporte são
registrados separadamente do defeito de escopo.

As sondas preservaram uma publicação por turno, zero executores e zero drift
durante cada coleta. Isolamento usa memória temporária, sem áudio, hardware ou
efeitos pessoais; não substitui uso diário ou avaliação humana de naturalidade.

## Próxima fronteira, responsáveis e aceite

Antes da redação, representar **proposição, dependências e escopo** com origem
conferível. Uma árvore, papel ou prova proposta pela IA permanece proposta.
Somente um owner com dados estruturados canônicos ou uma derivação independente
pode atestar essa estrutura; a ausência de pontuação/conectivos não basta.

| Responsável existente | Critério para próximo candidato |
| --- | --- |
| Fundamentação/proveniência | Vínculo à ocorrência e ao snapshot integral; distinguir dado estruturado de leitura textual ainda não interpretada. Não promover metadados gerados a prova. |
| Revisão de suporte | Verificar todos os operadores, condicionantes, negações, modais e dependências usados pela transformação. Se não puder conferir a estrutura, abster-se. |
| Autoria | Propor uma realização e seus vínculos dentro do alcance demonstrado. Se os dados só sustentam definição, não preencher exemplos ou causas por lembrança. |
| Entrega | Separar conteúdo sustentado e limite de conhecimento, preservando cobertura e sem anunciar efeitos. Reutilizar os owners atuais. |

Aceite exige positivos novos e contraexemplos fora da amostra de elaboração,
incluindo escopo aninhado, pontuação Unicode, discurso citado, mudança de
direção e condições fora da oração principal; depois composição instalada,
Qwen e avaliação de clareza/utilidade. Testar domínios distintos sem tratar
opinião do revisor ou confiança do modelo como verdade. Não ativar o antigo
render extrativo nem pesquisa ampla como atalho. Esta etapa não fecha C5/P01.

## Verificação final e entrega

- `restauracao_instalada.xml/json`:8 controles de contraexemplos GREEN após
  retirada,24 asserções experimentais não selecionadas explicitamente. A
  fixture ainda percorre os24 ciclos, com duas fontes por caso e zero
  executores. Positivos experimentais não se tornaram GREEN por omissão:
  continuam registrados como requisito não atendido, fora da suíte diária.
- `regressao_final.xml`:1405 aprovados,30 subtests,14 skips opcionais,
  duas falhas anteriores e um teste de import isolado desmarcado. Sem erros
  de coleta. Falhas: `test_autoria_reescritas::test_composicao_transporta_suporte_proprio_de_reparo_e_partes[4]`
  e `[6]`, expectativa de primeira chamada `principal` versus `interpretacao`.
  As mesmas duas falhas foram reproduzidas com o owner anterior carregado
  via import hook e SHA (`reescritas_baseline.xml`:30 GREEN/2 RED). Nenhuma
  alteração ou relaxamento desses testes.
- `import_final.xml`:1 GREEN; o teste desmarcado
  `test_latencia_resposta::test_composicao_principal_injeta_rota_que_respeita_perfil_explicativo`
  foi executado isoladamente com a mesma factory real.
- `verificacao_entrega.json`: conferência dos527 fontes Python de produção
  contra a base desta tarefa, sem drift; owner restaurado byte a byte.

**Produção mantida alterada nesta tarefa: nenhuma.** Permanecem oito novos
regressivos de segurança, estudo, especificações RED/candidato rejeitado e
registro do plano/raízes. Todas as alterações anteriores da worktree foram
preservadas. Nenhum commit, reinício pessoal, shutdown, mudança de modelo,
voz, configuração, UI, hardware ou ativação ampla. Não é necessário reabrir
a Laylay por esta tentativa: não houve mudança final nos módulos de produção.
