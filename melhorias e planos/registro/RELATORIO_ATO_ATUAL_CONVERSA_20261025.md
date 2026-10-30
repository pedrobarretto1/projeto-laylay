# Ato social anterior não substitui o relato atual — 25/10/2026

Base: HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`,
worktree preservada. Artefatos em `resultados_testes/dialogo_jogos_musica_20261025`.
Esta raiz é diferente da interpretação de perguntas de gosto e da repetição
de áudio. Não declara causa comum entre elas ou entre F1/C5/C7/AUT.

## Cadeia causal e falsificações

O relato de Pedro sobre o dia e Ultrakill foi classificado como conversa,
sem autorização nem comandos. A geração voltou a responder como Laylay estava.
O contrato exigia o conteúdo atual na primeira frase, mas a aceitação verificava
uma âncora temática posterior. Assim, uma saudação antiga acrescida de um nome
do relato passava. O juiz final confirmou essa aceitação indevida.

Não era execução operacional: classificação e plano não pediam ação. Não era
falta da fala atual: os registros reais preservavam texto e histórico. A origem
exata da influência sobre o modelo histórico continua hipótese, pois não existe
o payload bruto daquela execução. O RED demonstrado está na aceitação comum.

Na primeira correção, o veto eliminou o reinício evidente, mas a composição
mostrou reparo sem resposta útil: recebia novamente perguntas sociais antigas e
o rascunho refutado. Mesmo um erro inicial de perspectiva podia acabar em nova
saudação. Portanto, o ato atual precisa sobreviver também à autoria do reparo.

## Contrato e responsáveis

| Responsabilidade | Owner | Validação |
| --- | --- | --- |
| Identificar relato atual não operacional | `validacao_contrato_fala._contrato_relato_atual` | Identidade do turno, origem comum, função informação/conquista, ato conversa e roteiro direto com âncora literal |
| Recusar saudação/bem-estar reiniciados sem ato atual correspondente | `validacao_contrato_fala` | Nome do assunto depois da saudação não compensa responder a outro ato |
| Preservar o ato na nova autoria | `qualidade_comunicacao` | `relato_atual` mantém texto, falante e flags falsas; reparo não reapresenta saudação antiga ou rascunho errado como base |
| Produzir a reação | Qwen pelo runtime instalado | Resposta continua autoral e revisada; nenhuma frase temática fixa escrita pelo host |

O detector negativo não reutiliza o regex amplo de presença, que também aceita
“fala”, “estou aqui” e “por aqui”. Isso preserva conteúdo contextual legítimo.
Saudação pedida agora, saudação citada, repetição literal e retomada explícita de
bem-estar possuem controles positivos. Notas e apresentação protegem o mesmo
contrato fora de jogos. Não foi inferido o verbo correto do texto com erro.

## Evidência e alcance

RED inicial: cinco falhas e sete controles verdes. Candidato inicial ainda
falhava nos relatos classificados como conquista; guarda foi corrigida pelo
contrato, sem alterar sua classificação legítima. RED posterior do reparo por
perspectiva foi reproduzido antes da projeção do ato atual.

`test_continuidade_relato_sem_saudacao.py` possui 14 controles/regressivos; foco
conjunto final **221 aprovados**. Revisão independente conferiu a projeção e a
ausência de novos bloqueadores no escopo. `continuidade.diff` mantém a diferença
exata contra o começo desta investigação, sem incluir trabalho paralelo antigo.

Na coleta instalada final de 18 turnos, o relato recebeu uma reação ao assunto,
sem reiniciar saudação e sem estourar tentativas nesse turno. O Qwen interpretou
o texto como uma experiência positiva com o jogo. O sentido de “importante”
continua não comprovado: esta prova **não** demonstra que entendeu adaptação de
um jogo para navegador. Saudações iniciais ainda podem ser técnicas e longas;
ficam registradas como outra fronteira, sem marcar conversa geral como concluída.

Produção alterada nesta raiz: `validacao_contrato_fala.py` e
`qualidade_comunicacao.py`. Nenhum executor, configuração, modelo ou voz foi
alterado por esta raiz. Sem áudio/efeitos reais, sem commit. Resultados amplos e
seus REDs anteriores são comparados por identidade no manifesto da etapa.
