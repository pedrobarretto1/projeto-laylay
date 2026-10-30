# Primeiro reparo: posição no diálogo não é relato biográfico

Validação final: 152 módulos, 3.903 aprovados, cinco falhas basais pelos mesmos
IDs e nenhuma nova, zero erros; 14 ignorados, um desmarcado, um xfail e 30
subtestes. Os 32 casos novos passaram. Auditoria de 535 fontes aprovada, apenas
as duas fontes declaradas alteradas; nenhum ID anterior removido. Evidências:
regressao.xml, regressao_resumo.json, diagnostico.json, auditoria.json e
diff_producao.patch na pasta de artefatos.

Base congelada: c91cae1bd407b02db946ae7bc752d1ed3269bfd9, main, 535 fontes;
worktree anterior preservada. Artefatos: resultados_testes/recusa_primeiro_reparo_20261029.
Continuação da pendência de recuperação, sem reabrir a serialização já corrigida
nem criar outra causa por frase, rodada ou domínio.

## Cadeia causal demonstrada

1. A proposta principal histórica repete o corpo anterior: recusa legítima.
2. O primeiro reparo é um JSON válido com quatro unidades, incluindo um título
   novo. Não contém a cópia predominante da principal.
3. O verificador de atribuições captura você + estar + predicado e exige um
   relato pessoal literal equivalente. A posição avaliativa no diálogo é
   tratada como se descrevesse estado/rotina do interlocutor.
4. A qualidade devolve afirmacao_interlocutor_sem_apoio antes das demais
   conferências. O primeiro reparo inteiro é recusado.
5. A autoria final solicita outra chamada após principal + reparo. O orçamento
   recusa a terceira, mantendo o limite de duas. Não é a origem da recusa anterior.

Falsificações: JSON inválido, falta de título e repetição no primeiro reparo
não explicam esse RED. No controle de diagnóstico, retirar apenas o núcleo
avaliativo libera o restante nos mesmos revisores; posições concordantes e
discordantes simples repetem o problema. O transporte não é chamado pela
qualidade local, portanto indisponibilidade do Qwen não explica essa recusa.

## Contrato compartilhado e escopo mínimo

Owner linguístico: referencias_linguagem.natureza_predicado_pessoal. Classifica
o predicado integral em um recorte morfológico de posicionamento avaliativo
simples ou atribuição pessoal não conferida. Trabalha com a classe do predicado,
não com uma frase histórica, tema, número de rodada ou nome de habilidade.
Qualificações, causas, circunstâncias e complementos não ganham essa classe.

Owner da conferência: afirmacoes_interlocutor. Mantém o vínculo nativo entre
perspectiva, texto e turno. Posição simples não exige que o usuário tenha dito
“eu estou certo”. Uma continuação nominal infinitiva só fica fora do recorte
biográfico quando não traz outra predicação pessoal do léxico já protegido.
Estado elíptico, outro sujeito pessoal e qualificações continuam recusados.
O recorte é conservador: não confere livremente toda paráfrase avaliativa.

Não há certificado de verdade da opinião, fonte criada pela IA ou prova de
correção factual. O retorno de classificação não aprova a fala inteira; a
qualidade e a revisão final continuam conferindo seu restante. Nenhum trecho
foi cortado ou reescrito para obter aprovação. O resultado histórico integral
é mantido, incluindo o título que o modelo já tinha proposto.

Produção alterada nesta causa: afirmacoes_interlocutor.py e referencias_linguagem.py.
Nenhuma alteração no orçamento, orquestração de chamadas, modelos, personalidade,
receipts ou revisão de fontes. Nenhum commit criado.

## RED, controles e surpresa de teste

Antes da edição: oito REDs e doze controles. O módulo final tem 26 casos,
incluindo qualificações médicas, causas inventadas, estado elíptico, outras
atribuições, explicação factual sem apoio e efeitos em arquivos/aplicativos.
Foco com os contratos anteriores de autoria/continuidade/pessoal: 114 aprovados.

Dois controles novos de efeito surpreenderam: esperavam aceita=False, mas o
owner final admite aceita=True para a fala segura já ajustada, recusando o
original com “abri/apaguei”. O teste passou a exigir que o original não seja
aprovado/publicado e que o guardião mantenha execucao_alegada_sem_resultado.
Isso corrige a expectativa do teste, não a proteção de produção. Os controles
compostos também verificam que a alegação inventada não chega à publicação.

## Replay automatizado pela composição instalada

Sem conversa nova ou geração Qwen: folha HTTP controlada reapresenta as duas
respostas históricas; os owners instalados de plano, qualidade, orçamento,
autoria, revisão e publicação continuam reais. Somente dois owners da base
são carregados em memória no contrafactual; o código de produção não é trocado
no disco. Persistência isolada, voz desativada e executores interceptados.

Base: dois HTTPs, duas chamadas autorizadas, uma bloqueada e contingência.
Candidato: dois HTTPs, duas chamadas autorizadas, zero bloqueadas, uma publicação
igual ao reparo histórico integral. Mesmo limite de duas chamadas, sem tentativa
final extra. O título já presente no reparo chega ao usuário nessa composição.

Se o reparo contém biografia inventada, continua recusado e a terceira chamada
continua bloqueada. Propostas APP_OPEN/MEDIA_CONTROL não obtêm autoridade;
efeitos alegados sem receipt não são publicados. Seis casos compostos aprovados.
Nova geração e conversas livres permanecem reservadas a Pedro, por seu pedido.

Isso fecha a falsa recusa nesse recorte e seu esgotamento consequente. Não
promete recuperação de todo reparo inválido, ausência de timeout ou compreensão
semântica geral. Falhas reais continuam fechadas, sem aumentar tentativas.
