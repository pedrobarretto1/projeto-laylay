# Rodada6 — enquadramento e referência textual da própria fala

Autorização: Pedro pediu resolver as duas pendências registradas na etapa
da biblioteca. Plano: ../planos/PLANO_RODADA6_20261101.md. Base congelada:
1197daf0d6b5e69b7243f571542bf17666274ea2,
codex/correcao-autoria-conversa-20261030; worktree anterior preservada.
Artefatos: resultados_testes/rodada6_20261101, baseline/status/SHA256 de539fontes.
Pasta central absoluta: `C:\Users\pbarr\.codex\worktrees\publicacao-conversa-segura\laylay\resultados_testes\rodada6_20261101`.

## Enquadramento nominal antes da pergunta

O próprio classificador reproduzia a falha sem modelo. “Como professora”
também virava pergunta; não era defeito exclusivo da sigla IA. Na entrada6,
a interrogação posterior fazia a vírgula separar “Como IA” da matriz declarativa,
criando uma segunda pergunta e uma obrigação de resposta sem fonte histórica.
O binder estava preservando os atos recebidos; não deveria reparar esse corte.

Owners: normalizacao_linguagem lê o adjunto, morfologia_oracao fornece evidência
nominal e modalidade_turno preserva a matriz e a fonte integral. O mesmo leitor
é consumido na segmentação e classificação; não há parser no executor. A matriz
continua podendo ser conversa, pergunta, proibição, condição ou ordem direta.
O prefixo não autoriza, não veta sozinho e não fornece suporte factual.

Contraprova inicial:13REDs legítimos,11controles. Duas expectativas iniciais
foram descartadas porque não eram controles existentes: “Como se fosse IA,
abra...” e arquivo com “não” dentro do nome citado já falhavam no baseline.
Não usar esses sintomas para ampliar o patch. Logs iniciais preservados.

Primeiro candidato passou24testes, mas a revisão independente encontrou
caixa alta promovendo verbos como FUNCIONA a nome.3REDs adicionais cobriram
caixa alta e repetição de cabeçalho. Corrigido no owner lexical: IA possui
expansão nominal documentada “inteligência artificial”; a forma verbal ia
continua com os mesmos bits no índice congelado. Caixa alta só seleciona a
leitura registrada, não cria substantivo. Sigla desconhecida/índice indisponível
conservam a leitura anterior. Não há lista de frases de conversa.

A fonte lexical do cabeçalho serve somente para conferir a grafia da sigla.
Usa a porta canônica de fontes textuais. Repetições com grafia concordante
podem fornecer essa propriedade comum; fontes conflitantes abstêm-se. Isso
não identifica ocorrência, efeito ou autoridade. O ato mantém fonte integral.
Revisão final:29testes aprovados, sem novo blocker nesta fronteira.

## Referência indireta não é prova da proposição

O registro5 continha a fala entregue e os IDs; TTL e publicação não eram a
causa. Recuperação antiga exigia o literal inteiro dentro da consulta ou um
deítico selecionado pelo owner contextual. Até trecho literal parcial falhava,
inclusive sem troca de pessoa. Portanto, substituir consegue/consigo sozinho
não resolveria o contrato. A pergunta continuava histórica; a primeira perda
era a identificação textual, antes da autoria, binder e publicação.

Owners: referencias_linguagem lê a referência indireta; identidade_conversacional
expõe o mapa de perspectiva que o realizador já utilizava; registro_semantico
seleciona a ocorrência. Somente as flexões cobertas são projetadas. Complementos
expressos, polaridade, tempo e modalidade não são aproximados por similaridade.
Uma referência explícita não encontrada não vira elipse da última fala.
Histórico com mais de um candidato permanece ambíguo; validade e canais continuam
conferidos. seletor_contexto conserva a responsabilidade pela elipse deítica.

O complemento abreviado “não consegue inventar” localiza a fonte, mas a fala
entregue permanece inteira, inclusive “de novo o que não existe”. Não se emite
essa abreviação como proposição semanticamente equivalente. O leitor considera
uma consulta histórica interrogativa dentro do ato integral; comentários não
ganham fonte e uma segunda referência explícita não é descartada silenciosamente.

RED inicial:11falhas/37controles. Controles adversariais adicionais demonstraram
que vírgula sozinha não delimita uma forma pessoal própria; o recorte agora exige
estrutura lexical mais restrita e não atravessa prefácios/subordinação sem prova.
Registro detalhado em parafrase/DIAGNOSTICO.md e REDs preservados na pasta.
Os candidatos/hashes daquela subpasta são intermediários. O diff final de
toda a etapa é candidato.diff na pasta central, com os hashes de ampla_fontes.json;
não aplicar patches intermediários sobre a instalação já corrigida.

A revisão independente posterior provou outro limite: título, menção ou palavras
atribuídas a outra pessoa também podem conter o trecho pessoal. Não se criou
blacklist para essas três frases. A premissa de certificar assertividade por
esse leitor raso foi abandonada. Contrato final é **referência textual**, com
prova_afirmacao=False, prova_equivalencia=False e prova_causa=False no retorno
singular.3REDs de qualificação confirmados antes dessa restrição.

A fonte continua integral e observada, não proposta da IA tratada como prova.
O owner explicacao_fala_historica responde sobre o trecho e a ausência de motivo
registrado. Não diz que a alegação foi afirmada como verdade ou corretamente
interpretada. Revisão independente conferiu consumidores,66testes e6sondas de
contrato/plano, com pacote fechado e rejeição de causa inventada. Sem blockers
restantes nesse contrato. O código não oferece juiz semântico universal.

## Composição da entrada6 e segurança

Fixture rastreável conserva entrada/histórico. Registro reconstruído pelas
portas reais de fala observada, sem criar receipts. Factory/root/plano/binder,
codec e publicação nativos; HTTP fixo, perfil privado, rede/efeitos/voz bloqueados.
Nenhuma conversa nova Qwen nem ação no processo pessoal.

Prova em composicao/*/resultado.json:6atos, apenas1pergunta real; fonte integral
singular na última parte; resposta publicada,1HTTP, degradada=false,
falhas_geracao=[], comandos=[], autoriza=false, efeitos=[], voz=false.
Sem pergunta artificial sobre “Como IA”, ocorrência ausente indevida, aviso de
resultado operacional ou placeholder de parte não respondida. A realização
declara que o motivo de usar a formulação não ficou registrado; não aprova
o draft6 que inventava uma justificativa.

Os testes históricos da etapa anterior foram atualizados com o novo contrato,
preservando seus IDs e a entrada integral:7atos/ausência eram evidências da
pendência, não expectativas permanentes. O helper da fala6 agora usa apenas
registro textual, em vez de anexar um receipt IoT artificial. Os demais controles
mantêm receipts tipados, inclusive falhas de arquivos/IoT e causas não comprovadas.

## Instalação e validação

Produção alterada:7owners acima; revisão/orçamento/executores não foram
relaxados. Testes:3novos módulos e ajuste do histórico misto. Instalação original
ae7b8775/main conferida por539hashes, backup e apply_patch;7candidatos idênticos,
532outros fontes preservados, inclusive os três neurais com EOL diferente.
Nenhum commit, push, shutdown ou reinício da ponte existente.

Foco anterior à última restrição:374aprovados,1skip; qualificação posterior:
86aprovados, incluindo composição6. Venv original final:377aprovados,1skip,
zero falhas/erros em20,41segundos,13módulos (original.xml/log).
Regressão ampla final:157módulos,4.695aprovados,25skips,1deselected,3subtests,
zero falhas/erros/xfails em576,82segundos. Mantido o filtro anterior do perfil
explicativo, sem exclusão nova. Auditoria XML conferiu44IDs históricos aprovados
e ambos os casos musicais originais aprovados.539fontes permaneceram estáveis;
7candidatos instalados idênticos e532outros fontes originais preservados.
Resultados em ampla.xml/log, original.xml/log e resumo_final.json. Revisões
independentes encerradas sem blockers nos respectivos contratos.

As duas pendências técnicas ficam validadas nesse recorte, na composição nativa
e na regressão relevante. Não se declara conversa espontânea Qwen validada,
compreensão geral ou equivalência semântica universal a partir desses verdes.

## Limites mantidos

As duas pendências técnicas da rodada6 não são memória semântica universal,
certeza de equivalência de paráfrases ou acesso à causa interna do modelo.
Novas flexões/siglas/estruturas fora do recorte abstêm-se. A dupla ordem repetida
com enquadramento ainda tem segmentação contaminada nos snapshots anteriores;
foi registrada como limite preexistente, sem ampliar esta correção.

Os testes naturais permanecem com Pedro. Uma sessão da ponte que já copiou as
fontes anteriores precisa ser substituída por uma nova para carregar as mudanças.
