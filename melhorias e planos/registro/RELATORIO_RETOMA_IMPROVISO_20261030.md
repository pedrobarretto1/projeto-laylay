# Retomada do improviso — revisão por raiz causal

## Base, escopo e reprodução

Sessão20261030T094314Z-5cf00cff, oito evidências trazidas por Pedro:
rodada-nova-001/006/008/010/012/013/014/015. As538 fontes da sessão coincidem
com a base congelada desta investigação. A ponte retomou seis pares entregues
da sessão anterior. Histórico fornece contexto, não prova factual ou autorização.

Base original: c91cae1bd407b02db946ae7bc752d1ed3269bfd9, main suja preservada.
Fontes, estado Git e hashes em resultados_testes/retoma_improviso_20261030/base
e baseline.json. Durante o trabalho houve commit externo ae7b8775. A base
não foi atualizada; a auditoria usa o conteúdo congelado, registra o HEAD
observado e verifica as538 fontes. Nenhum commit foi criado no main por esta
investigação. Não houve Qwen novo, conversa espontânea, voz ou efeito externo.

O journal preserva saída pós-codec, não corpo HTTP original. Primeiro replay
recolocava `fala` junto do V5 e falhou no formato: essa coleta foi mantida em
fronteiras_base.json/log como erro de fixture. A reconstrução seguinte remove
esse campo do wire V5 e junta todas as `partes` em `texto`, conservando palavras,
ordem e fontes. A rota legada recebe `fala` somente quando a negociação o pede.
fronteiras_reconstruidas.json reproduz os oito sintomas, com variação de texto
nas contingências escolhidas pelo host. Não se inventou o conteúdo das emissões.

## Causas separadas e contratos

| Evidência | Primeira divergência | Owner / contrato corrigido |
| --- | --- | --- |
|006|“sou obrigado a imaginar” vira agradecimento, encerramento e reparos desnecessários|referencias_linguagem confere a construção de gratidão; leitura_usuario e leitura_social_conversa reutilizam o mesmo leitor. Obrigação, clítico e auxiliar reflexivo não viram agradecimento|
|013|rótulo afetivo/frustração vira declaração de estado pessoal inexistente|contrato_fala exige declaração própria; não promove o rótulo emocional a relato literal. Leitor comum preserva estados explícitos, inclusive “me sinto”/“tô com medo”; validação do núcleo reutiliza a fonte|
|014|“tudo bem” acolhe a interlocutora, mas um “eu” de outra frase decide a perspectiva|interpretacao_social vincula pessoa ao recorte de estado. Contingência de qualidade respeita a estratégia recebida e não reinterpreta a expressão como nova pergunta de bem-estar|
|008/012/014|Qwen copia extensamente a fala atual, e a revisão só confere cópia das respostas anteriores da própria Laylay|qualidade_comunicacao confere também a PerspectivaEnunciador nativa vigente; continuidade_resposta compartilha a comparação de blocos.32 palavras copiadas em blocos de oito, cobrindo80% da candidata, vetam esse eco. O piso64 do reuso antigo permanece|
|001/006/010|interrogação, tema mutável e tempo pertencem a frases diferentes dentro de um só segmento; pergunta citada também contamina a consulta|referencias_linguagem oferece fronteiras fortes fora de aspas; fundamentacao_factual avalia cada enunciado, sem herdar a modalidade interrogativa do composto. Confirmação elíptica conserva sua proposição; fontes de segmentação inválidas mantêm análise conservadora|
|013|“o que viria à sua cabeça agora?” vira consulta externa recente|owner factual reconhece elaboração da interlocutora, inclusive matriz após adjunto condicional. Preço/cargo/disponibilidade e consulta externa explícita mantêm prioridade e evidência|
|015|modelo responde “tô bem” ao estado declarado pelo usuário e promete memória|a declaração de estado do usuário continua exigindo acolhimento; proposta histórica inadequada não foi liberada. Resposta pertinente controlada já passava na base; não atribuir novo bug ao mesmo sintoma de contingência|
|015 e variantes|agradecimento verdadeiro impõe uma frase/fechamento e ignora a continuação atual|contrato_fala publica exclusividade integral conferida pelo leitor comum; geracao_concreta conserva os demais atos. Coordenação não ganha fechamento obrigatório sem prova de escopo nominal; o agradecimento continua reconhecido|

São famílias/contratos, não uma raiz nova para cada número de turno. IDs
anteriores e F1/C5/C7/AUT permanecem preservados. Não houve alteração de persona,
imposição de tamanho único nem dispensa global de revisão para humor/ficção.

## Falsificações e validação

- Coincidência das fontes falsifica código antigo da sessão como explicação.
- Cópia já presente na proposta do modelo falsifica duplicação de entrega pela ponte.
- Leituras puras reproduzem os erros sem HTTP, modelo ou executores; transporte
  indisponível não explica as primeiras decisões incorretas.
- A atualidade indevida é demonstrável sem classificar o texto como ficção:
  não foi necessário aceitar um rótulo proposto pela IA ou retirar a revisão.
- “Obrigado a todos” e gratidão genuína continuam reconhecidos. Correção sem
  declaração não força estado; declarações explícitas conservam acolhimento.
- Reprodução explicitamente pedida aceita somente o objeto literal; uma cópia
  disfarçada de contribuição continua sujeita ao veto. Retomada breve e resposta
  nova permanecem permitidas. Fonte de outro turno/dict não fornece autoridade.
- Perguntas atuais reais, confirmação de preço e receipt inventado continuam
  recusando alegações sem fonte/execução. O orçamento de duas chamadas não mudou.

RED inicial:17 falhas/16 controles. Atualidade:16 falhas/nove controles.
Revisão independente: oito REDs preservados, corrigidos nos mesmos owners.
Foco final:95 aprovados em quatro módulos, incluindo13 composições instaladas
com HTTP fixo, perfil privado auditado, publicação/orçamento nativos e ações
bloqueadas. Oito respostas pertinentes passam em uma chamada; três cópias
históricas são recusadas e recebem redação nova no reparo único.
Com os vizinhos de atos discursivos:167 aprovados e quatro opcionais de modelo
pulados. No worktree exportado,95 aprovados com a mesma composição e sem chave.

Revisão independente:32 verificações puras após os três achados iniciais e31
na relação final de gratidão composta, sem apontamento pendente nesses recortes.
Comparação instalada:16 percursos, oito base/oito candidato.
Casos015 e alguns conteúdos adequados já passam na base; não declarar todas
as oito entradas como oito regressões corrigidas. Comparação e replays preservam
os resultados negativos, não só os verdes.

Primeira ampla preservada em regressao_antes_gratidao:4.850 aprovados,zero
falhas/erros,nenhum ID anterior ausente. Esse conjunto foi coletado antes da
última correção de gratidão e não representa a versão final.

Regressão ampla relevante final:195 módulos,4.859 aprovados,14 pulados,
um desmarcado pelo filtro anterior,um xfail e30 subtestes aprovados, em675,78s.
Exit0,nenhuma falha/erro e nenhum ID anterior ausente. Mesmos filtros do conjunto
anterior, incluindo a exclusão preexistente de
test_composicao_principal_injeta_rota_que_respeita_perfil_explicativo.
Não é a suíte completa nem conversa espontânea do modelo. Auditoria final:
538 fontes,dez owners alterados,528 preservadas; baseline/HEAD observado mantidos.

## Publicação sem dados privados

O commit paralelo ae7b8775 inclui configuracao.env com credencial preenchida.
Esse commit não será enviado como ancestral da publicação. Worktree gerenciado
publicacao-conversa-segura parte do c91cae1b que está no remoto. A branch
codex/correcao-autoria-conversa-20261030 recebe código, testes e documentação
acumulados e validados, incluindo as dependências das correções anteriores.
Configuração pessoal, estado de hotspot, memória, journals e resultados locais
ficam fora. O main e o commit paralelo permanecem intactos.

O primeiro foco no export falhou na preparação porque o harness existente
exige configuracao.env. Não é RED de produção: foi criado ali arquivo ignorado
somente com backend/URL/modelo, sem chave ou dados pessoais. O foco95 passou
nessa configuração; equivalência das538 fontes conferida, normalizando apenas
CRLF/LF. Manifesto e auditoria precedem commit/push. Arquivo ignorado de
teste não participa do commit. Não registrar valores de credenciais em logs.

O índice seguro foi conferido por lista explícita de212 arquivos de código,
testes e documentação acumulados. A checagem de whitespace encontrou somente
linhas vazias adicionais no final de dois testes anteriores de redação; foram
removidas sem alterar testes/expectativas. Nenhum dado privado ou artefato
local foi incluído para satisfazer a preparação dos testes.
Destino do commit/push: branch segura indicada acima; recibos locais de commit
e publicação em resultados_testes/retoma_improviso_20261030. O main e a
configuração original ficam preservados. Desligamento autorizado por Pedro
somente depois da confirmação do push.

## Limites

A prova controlada confirma contratos e entrega de propostas pertinentes; não
prova que o Qwen as escolherá espontaneamente. As propostas históricas ainda
contêm exageros, pronomes inadequados e promessas de memória; não são prova de
experiência ou armazenamento. Cópia curta, paráfrase semântica, seleção de temas
e timing literário exigem evidência própria. Testes naturais permanecem com
Pedro; não declarar compreensão global, memória autônoma ou factualidade livre
concluídas. A credencial do commit local paralelo requer cuidado antes de uma
futura publicação independente desse histórico.
