# Revisão didática e criação ficcional — 28/10/2026

Correção aplicada no contrato compartilhado de finalidade. Uma criação
explicitamente ficcional pode desenvolver regras inventadas sem apresentá-las
como fatos reais. Isso não dispensa fontes de uma explicação factual nem
confirma ações. Não é prova de compreensão universal de ficção ou conversa.

Continuação posterior do corte textual observado: ver
`RELATORIO_INTEGRIDADE_AUTORIA_LIVRE_20261028.md`. A coleta e os limites desta
etapa permanecem como registro histórico, sem reclassificação retroativa.

## Base, primeira fronteira e falsificações

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`, worktree suja
preservada. Hashes de 531 fontes e estado Git congelados em
`resultados_testes/finalidade_ficcional_20261028/baseline.json`. Nenhum commit.
É continuação da fronteira didática registrada no relatório de finalidade
histórica; não se reabre nem se conta novamente a captura pelo owner histórico.

```text
pergunta sobre cenário inventado ou sua continuação
→ classificar_proporcao retorna explicativa para dimensionar a resposta
→ roteiro usa esse perfil como finalidade de ensino factual
→ explicacao_exige_apoio_individual impõe fonte a todas as proposições
→ proposta ficcional sem referências recebe aviso de apoio não conferido
```

A primeira transição incorreta é **perfil de tamanho → finalidade factual**.
O perfil de proporção é útil e foi preservado. O vínculo de autoria também
continua obrigatório: a saída da IA não certifica seu próprio suporte.

Na base instalada, a continuação original “Gostei da ideia. Vamos pensar em
outra. Como isso funcionaria?” foi respondida em bruto com um cenário de
cidade flutuante; o host publicou o aviso didático. HTTP 200 nesse turno,
sem contrato histórico. Isso falsifica tanto falha de transporte como captura
histórica remanescente para esse bloqueio. O primeiro turno da mesma coleta
teve timeout; ele foi preservado e não usado como prova da revisão didática.

Não se remove a restrição de fontes: os controles de fotossíntese, variáveis,
história factual e ações passadas demonstram por que ela continua necessária.
“Na história” também não pode isentar uma instrução didática independente.

## Contratos, owners e escopo da mudança

| Responsabilidade | Owner | Contrato |
| --- | --- | --- |
| Qualificar criação | `cognicao/criacao_ficcional.py` | Snapshot nativo ligado ao texto e turno atuais; moldura explícita ou anáfora canônica com contrato anterior e pedido do usuário recentes. Fala da IA sozinha não escolhe finalidade. |
| Compor o contrato atual | `cognicao/contrato_fala.py` | Constrói o snapshot depois das decisões históricas e de opinião; não concede autoridade ou nova capacidade. |
| Orientar autoria/reparo | `cognicao/geracao_concreta.py` | Mesmo roteiro ficcional, tema do pedido e início `Na história,`; orientação breve para caber no orçamento existente. |
| Conferir a emissão | `cognicao/revisao_suporte_autoria.py` | Exige declaração integral atual, texto exatamente vinculado e moldura ficcional. Referências declaradas continuam sob conferência normal. Não confere semântica livre nem fato externo. |
| Conferir efeitos e alegações reais | Guardas e executores existentes | Preservados; uma história não autoriza ação nem substitui receipt. |

Produção alterada: os três owners existentes de contrato, roteiro e revisão.
Produção nova: `criacao_ficcional.py`. Proporção, revisão histórica, executor,
composition root, configuração, modelo e voz não foram alterados. As flags de
confirmação factual e autorização permanecem falsas. Os diffs exclusivos
contra a worktree congelada ficam nos artefatos; o diff contra HEAD também
contém trabalho anterior e não deve ser atribuído integralmente a esta etapa.

A continuidade lê o pedido imediatamente anterior, seu contrato nativo e TTL
de 240 segundos. Reutiliza a referência contextual canônica, sem lista de
frases de continuação e sem procurar um assunto antigo conveniente depois
de outra entrada. Um snapshot serializado em dicionário ou de outro turno
não é aceito como credencial.

## RED, controles e composição instalada

RED inicial: oito falhas e 15 controles aprovados. Os primeiros testes
alcançaram a seleção de finalidade e a revisão reais, não falharam por import.
O candidato inicial tinha uma abertura em pedido misto: “Na história, o robô
estuda. Me ensina o que é uma variável em Python.” Um RED adicional a expôs;
o owner passou a recusar esse recorte antes de permitir criação. Esse limite
é conservador e não pretende resolver semanticamente todo pedido misto.

Módulo novo `scripts/tests/test_finalidade_ficcional_revisao.py`: **30 casos
aprovados**. Critérios incluem criação e explicação de cenário, variantes
referenciais, expiração/troca de entrada, fonte ou declaração inventadas,
texto sem moldura, adulteração de turno/consulta, pedido factual misto e
confirmação operacional falsa. Primário e reparo recebem o mesmo escopo.

Controles históricos adicionais expuseram 21 falhas em
`test_autoria_historica_integral.py`, que não estava na lista ampla anterior.
`verificar_base.py` executou o mesmo módulo sobre os três owners congelados,
somente em memória: **as mesmas 21 falhas e 18 aprovações**. Nenhum arquivo de
produção foi restaurado. O foco ampliado teve 162 aprovações, essas 21 falhas
e o xfail anterior de segmentação; não se apresenta esse conjunto como verde.

Regressão ampliada em **131 módulos**: 3.372 aprovados, 30 falhas, 44 erros,
14 ignorados, um desmarcado, um xfail e 30 subtestes aprovados. A auditoria
comparou os IDs: as 30 falhas são as nove da lista anterior mais as 21 do
módulo adicional comprovadas sobre a base congelada. Os 44 erros também são
os mesmos da fixture anterior. Não houve novas falhas nos conjuntos
comparados; a suíte ampla continua sem GREEN integral.

Composição instalada, serviços reais e `qwen3:4b-instruct`, perfil isolado,
sem voz e com executores simulados:

- `baseline_dialogo`: quatro publicações; timeout inicial, bloqueio didático
  na continuação, contingência no outro pedido imaginativo e proteção factual.
- `candidato_dialogo`: desenvolvimento ficcional sem aviso nos turnos-alvo,
  mas timeout inicial e duas respostas truncadas. Captura preservada, sem
  chamá-la de conversa satisfatória.
- `final_dialogo`: **oito publicações e seis HTTP 200**. Três criações recebem
  `criacao_ficcional_delimitada`, sem fonte inventada nem alteração da fala
  entre autoria e revisão. Textos finais completos quanto à pontuação.
- Mudança explícita para mundo real e pedido factual misto não recebem
  snapshot ficcional; a obrigação de apoio individual permanece ativa.
- Uma tentativa de abrir Calculadora recebe receipt nativo simulado com
  `executou=False`, `confirmado=False`, `ok=False`; nenhuma ação real.
  Perguntar por que abriu conserva o limite histórico, sem inventar causa.

## Limites preservados e próxima fronteira

O controle factual misto acabou em contingência, sem ensinar adequadamente.
Timeouts e truncamentos intermediários não foram consertados na camada de
transporte nem ocultados. A orientação de concisão no novo roteiro não prova
que todo orçamento ou comprimento seja respeitado. A coerência das regras
inventadas ao longo de conversas extensas não foi certificada.

O leitor é deliberadamente limitado. Citações, linguagem indireta, pedidos
mistos e mudanças de assunto não têm compreensão semântica universal.
Continuam necessários os estudos de pertinência, completude e segmentação
histórica; F1/C5/C7/AUT não são encerrados aqui. A revisão factual continua
conservadora: apoiar fatos reais com fontes pertinentes é outra fronteira.

Artefatos: `resultados_testes/finalidade_ficcional_20261028`; auditoria
reproduzível em `auditar.py`. O plano e o mapa causal devem ser lidos com
esses limites, não como conclusão da compreensão inteira da Laylay.
A auditoria passou: 532 fontes conferidas, somente três owners existentes
alterados e um novo, snapshot final estável, persistência isolada salva,
IDs de falha comparados, HEAD preservado e `git diff --check` sem erro nos
owners. O preflight do foco citava um módulo inexistente; foi preservado,
corrigido antes da execução válida e não contado como evidência RED.
