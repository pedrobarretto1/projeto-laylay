# Adequação ao usuário não é gosto da autora — 28/10/2026

## Base e primeira fronteira

Pedido autorizado: estudar a troca de alvo em “que estilo combina comigo?”,
corrigir o contrato comum e validar com Qwen, sem voz e com ações simuladas.
Base preservada: HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, `main`,
worktree suja. Estado Git, 530 hashes e backups em
`resultados_testes/adequacao_usuario_20261025/baseline.json` e `fontes_antes`.
A pasta conserva a data de início; a conclusão e revisão são de 28/10.
Nenhum commit, reset, mudança de modelo, configuração, voz ou executor.

A perspectiva do canal já distinguia usuário e autora, mas o contrato genérico
não declarava a relação perguntada: adequação de uma categoria AO USUÁRIO.
Autoria e revisão podiam confundir essa relação com preferência da Laylay.
No baseline instalado, após uma preferência própria, a resposta começou
`Eu prefiro mpb` e transferiu esse gosto à adequação. Em software, negou acesso
e sugeriu um aplicativo vago sem apoio. Seis entradas/publicações, seis HTTP 200.

```text
pergunta atual de adequação ao enunciador
→ contrato genérico sem relação/alvo conferíveis
→ geração usa preferência própria ou inventa personalização
→ revisão não exige a relação da pergunta
→ resposta alheia ao pedido é publicada
```

Falsificados: perda geral do histórico/reset; falta da pergunta atual no HTTP;
indisponibilidade do modelo; falha do contrato de preferência própria já
corrigido. Existir no contexto, ter sido dito pela IA e corresponder ao pedido
atual são obrigações distintas. Menção do usuário também não declara preferência.

## Contrato e responsáveis

Princípio: **alvo e relação do pedido atual governam autoria, reparo e revisão;
a preferência da autora não comprova adequação ao usuário**.

| Responsabilidade | Owner | Critério |
| --- | --- | --- |
| Ler categoria e relação integral | `referencias_linguagem.consulta_adequacao_pessoal` | Alvo enunciador; moldura de pedido/vocativo, artigo, relativo e advérbio preservam a mesma relação; outra pessoa, citação ou ação adicional não são absorvidas |
| Vincular ato ao turno | Novo `adequacao_pessoal.AdequacaoPessoal` | Snapshot nativo com texto/id/categoria/alvo/relação; dict proposto pela IA não substitui fonte do host |
| Projetar obrigação | `contrato_fala` e `geracao_concreta` | Ato e roteiro próprios; relação atual não é substituída por fala anterior |
| Autoria principal | `ContextoPromptRuntime` | Mesmo owner limita a emissão; sem trazer rascunho ou preferência anterior como prova |
| Qualidade e reparo | `qualidade_comunicacao` | Rejeita transferência de gosto e palpites; repara pelo mesmo ato, sem reapresentar a fala refutada |
| Aderência | `validacao_contrato_fala` | Realização integral ligada a texto/turno; ausência/adulteração da fonte não provoca revisão genérica permissiva |
| Suporte | `revisao_suporte_autoria` | Só confere o ato de negociar critério, sem validar fatos, traços pessoais, adequação de opção ou execução; suporte estrangeiro recusado |

Sem uma avaliação de adequação fundamentada, esta entrega negocia o critério da
escolha. Por exemplo: `Pensando em estilo para você, o que mais importa nessa
escolha?` Não afirma que não há memória, não diagnostica o usuário e não escolhe
um gênero ou produto a partir do gosto da Laylay. São duas realizações limitadas
de um ato geral, com a categoria lida da pergunta; não há resposta especial para
um nome, turno ou frase histórica. **Ainda não é um recomendador personalizado
completo**, nem prova de compreensão livre ou continuidade após a resposta ao
critério. A limitação foi explicitada, não escondida por confirmação de sucesso.

Produção: novo `cognicao/adequacao_pessoal.py` e sete portas existentes citadas
acima. Toda decisão de admissão/realização pertence ao mesmo owner; as portas
não mantêm listas independentes. Não foram alterados opinião própria, aquisição
de fontes, guardião de efeitos, executor, sessão, permissões ou verificador
histórico. O vocativo global continua sendo outra fronteira; aqui só se confere
a moldura integral usando os apelidos canônicos existentes.

## RED, revisão e regressão

- RED antes de produção: **24 falhas e 16 controles aprovados**.
- Primeiro candidato teve erro de ligação da função local de resultado do
  revisor; foi corrigido sem mudar expectativas. Artefato intermediário
  `contrato_candidato1.xml` não conta como prova da raiz nem GREEN.
- Contrato inicial: 40 aprovados; foco inicial: 364 aprovados/dois ignorados.
- Revisão independente apontou variantes próximas sem proteção. Confirmado
  RED em quatro casos com 41 controles; a mesma gramática passou a separar
  artigo/relativo/advérbio e pontuação do vocativo. Não adicionar exceção por frase.
- Final: **45 casos aprovados**, incluindo categoria esperada independente do
  parser, fonte/turno alterados, ausência de fonte, proposta estrangeira,
  comando inventado, aparência presumida e gosto próprio em vários domínios.
- Foco revisado: **369 aprovados e dois ignorados**.
- Ampla revisada em **128 módulos**: **3.290 aprovados**, mesmas nove falhas e
  44 erros anteriores por identidade, 14 ignorados, um desmarcado e 30 subtestes.
  Casos antigos: comando da Calculadora, expectativas de pacote/tokens e fixture
  de serialização de `PerspectivaEnunciador`. Comparação em `comparacao_regressao.json`.
  Não declarar suíte global verde. Execução anterior ao ajuste das variantes
  permanece em `regressao_candidato1.*`, sem sobrescrever sua evidência.

O reforço de categoria no teste expôs um aviso de iterador do pytest; a fixture
passou a entregar uma coleção e foi reexecutada sem warning. Não houve alteração
de produção por esse ajuste. O diagnóstico antigo de adequação permanece como
histórico; seus REDs foram incorporados aos contratos de regressão.

## Composição real

`final_revisado`: **13 entradas/publicações/HTTP 200**, dez adequações em música,
software, jogos, cor, filme, roupa e livro. Todas foram revisadas como
`criterio_adequacao_solicitado_ao_usuario`. Texto HTTP idêntico ao publicado;
fontes vazias, comandos vazios, contexto autoral fechado e flags de prova factual,
semântica livre, implicação e autorização falsas. Fonte é o ato atual, não a
proposta da IA como evidência sobre o mundo. As adequações não renovaram sessão.
Controles de opinião e encerramento conservaram seus owners.

`seguranca_revisada`: três turnos, incluindo a redação original exata de Pedro;
uma Calculadora simulada com receipt negativo (`executou=False`,
`confirmado=False`) e pergunta posterior sem sucesso falso. Sem voz/efeitos.

Coletas anteriores continuam preservadas. No roteiro histórico de quatro
entradas, a adequação foi respondida corretamente; o relato/sugestão intermediário
teve timeout real no reparo. Esse turno **não é êxito conversacional**, não foi
apagado ou repetido para esconder a falha e permanece separado desta raiz.
Também houve variação de preferência própria após assuntos diferentes; esta
entrega não comprova preferência durável.

Auditoria final aprovada: `manifesto.json`, diff exclusivo contra a base suja,
proposta/publicação, persistência isolada gravada/relida, recibo negativo e 531
hashes atuais estáveis. A coleta anterior às variantes usa seus bytes históricos;
somente `final_revisado` e `seguranca_revisada` sustentam o GREEN do código final.

## Testes novos da ponte — frente distinta

O encontro principal indicado por Pedro foi conferido nos arquivos originais:
20 entradas, 16 respostas, quatro erros e cinco sessões. Há sessões auxiliares
e duas mensagens preliminares adicionais; não confundi-las com o encontro.
Os 530 hashes comuns da última captura coincidem com a base anterior à correção.

Os avisos de evidência em ficção são reais. Um diagnóstico separado reproduziu
três REDs de contrato histórico indevidamente presente e um controle preservando
a rejeição de causas/efeitos reais sem fonte. Evidências em
`resultados_testes/ficcao_historico_20261028`; análise em
`DIAGNOSTICO_FICCAO_HISTORICO_20261028.md`. Nenhum patch histórico foi misturado
a esta correção. F1/C5/C7/AUT e orçamento/saída inválida continuam separados.
