# Posicionamento natural — revisão compartilhada da resposta

## Base e escopo

Continuação da pendência de revisão registrada após a correção de escopo de
atos de perdão/confiança. Não reabre as causas `perdao-001` e `perdao2-003`,
nem cria uma raiz por variante de frase. Os IDs e diagnósticos anteriores
permanecem no registro. Testes de conversa/Qwen continuam com Pedro.

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`, worktree suja
preservada. As 538 fontes Python reais anteriores ao candidato, com hashes e
status Git, estão congeladas em
`resultados_testes/posicionamento_resposta_20261029/base` e `baseline.json`.
Essa base inclui mudanças anteriores não commitadas; não foi substituída pelo
conteúdo do HEAD. Nenhum commit criado.

## Primeira fronteira incorreta e controles

Com o contrato de entrada já correto, a qualidade da comunicação recusava
“Eu vejo o perdão como uma escolha possível, sem exigir a recuperação da
confiança”: `pergunta_direta_nao_respondida`. Na pergunta curta sobre opinião,
a aderência também produzia `ato_opiniao_nao_respondido`. Cada leitor mantinha
seu vocabulário privado de marcas de posição.

A troca do complemento por “que não exige...” aprovava a mesma ideia porque
o leitor encontrava `não`; a forma “Acho que...” também passava. Sem saudação,
sem fonte, sem modelo e sem transporte o bloqueio continuava reproduzível.
Portanto saudação, indisponibilidade do Qwen e orçamento não explicam essa
primeira divergência. O comparativo está em `fronteiras.json`; o RED canônico
inicial contém 17 falhas e 13 controles aprovados.

Corrigir somente esses dois consumidores revelou uma fronteira posterior
distinta: a fundamentação tratava “Defendo que discordar com cuidado é uma
atitude válida” como detalhe externo sobre o tema. A forma equivalente com
“Acho que” passava. A comparação instalada separa os comportamentos: base,
candidato sem mudança factual e candidato completo. Não se atribui esse
segundo bloqueio ao transporte nem se usa o sucesso da qualidade para ocultá-lo.

## Contrato e owners

`normalizacao_linguagem.localizar_enunciacao_avaliativa` localiza uma matriz
de perspectiva/juízo, sua autoria e complemento. Qualidade e aderência reutilizam
essa leitura, inclusive para posição na primeira frase e ordem de atos. Não
confere pertinência temática, verdade factual, experiência, capacidade ou efeito.
As respostas polares e opções explícitas continuam com seus controles existentes.

A leitura distingue percepção literal, relato de terceiro, interlocutor,
fragmento e pergunta. Uma pergunta posterior dirigida ao interlocutor não apaga
a declaração anterior. Aspas podem delimitar um objeto da avaliação; o conteúdo
citado fica opaco e não fornece matriz/verbo/operador externos. Os intervalos
originais são conservados. Há REDs e testes de offsets para essas fronteiras.

`fundamentacao_factual` continua dona de decidir a necessidade de base factual.
Seu teste genérico de tema mais cópula passa a reconhecer um recorte explícito
de juízo normativo sobre atividade: infinitivo lexical e, opcionalmente, um
argumento nominal sem qualificação, com predicado avaliativo fechado. O leitor
morfológico existente fornece classe lexical, não evidência de mundo. Um prefixo
de opinião sozinho nunca ativa essa exceção nova. Números, coordenação de fatos,
relatos, atributos e relações encaixadas continuam fora desse recorte.

Na revisão do primeiro candidato, quatro contraexemplos demonstraram uma
isenção indevida de atributos: clínica gratuita, medicamento inofensivo, banco
solvente e solvência do banco. Esse candidato foi rejeitado. O contrato foi
restringido e os quatro REDs preservados em `red_atributos_objeto.xml`. A revisão
de seguimento não encontrou novo achado acionável e confirmou 39 testes puros.
Não se afirma que morfologia prova ausência de fatos em linguagem arbitrária.

Os consumidores conservam suas decisões próprias: expressão de opinião não é
receipt, autorização ou prova. Não foram removidas revisões de fonte, critérios,
capacidade, efeito ou segurança para conseguir publicar a resposta.

## Validação

- RED inicial: 17 falhas/13 controles. RED normativo posterior: 2 falhas/3 controles.
- RED de escopo: duas formas naturais recusadas; pergunta isolada e matriz
  citada permaneciam controles negativos. Um teste adicional detectou truncamento
  do intervalo citado; corrigido antes da validação final, sem remover o teste.
- Foco final: 188 aprovados, incluindo qualidade, aderência, fundamentação,
  escopo de confirmação, publicação e segurança.
- Nove comparações instaladas base/parcial/candidato: a base substitui a opinião
  após duas propostas; o candidato publica a resposta temática com uma chamada.
  O controle legado com “Acho que” conserva sua publicação literal. Isso mede
  propostas HTTP fixas, não geração espontânea do modelo.
- A composição real da ponte usa perfil/memória privados antes dos imports,
  identidade ChatGPT distinta de Pedro e folhas de efeitos interceptadas. As
  publicações passam pelos owners instalados. Nenhuma autorização, voz,
  execução externa ou violação de isolamento foi observada nos ensaios.
- As propostas adversariais de abrir aplicativo e pausar música, com receipts
  fabricados pelo modelo, são rejeitadas antes da publicação; o reparo preserva
  a correção explícita e não anuncia esses efeitos.
- Regressão ampla relevante: 175 módulos, 4.542 aprovados, zero falhas/erros,
  14 pulados, um xfail, um deselecionado e 30 subtestes aprovados; 420,63s.
  Mesmos filtros da regressão anterior, sem retirar nenhum ID anterior.
  São 48 casos novos além dos 4.494 aprovados anteriores. Não é a suíte total.
  Comando integral, log, XML e comparação de IDs estão em `regressao_comando.json`,
  `regressao.log`, `regressao.xml` e `regressao_resumo.json`.
- Auditoria: exatamente quatro fontes existentes alteradas entre as 538; diff
  e hashes em `diff_producao.patch` e `auditoria.json`. Nenhum módulo de produção
  novo; os demais owners e as alterações paralelas anteriores foram preservados.

A suspeita exploratória de custo excessivo no leitor não se reproduziu no
controle de 400 palavras; o resultado está em `controle_custo_leitura.json`.
Não é classificada como raiz demonstrada.

## Delta e limites

Produção alterada nesta investigação:

- `mente_laylay/cognicao/normalizacao_linguagem.py`
- `mente_laylay/cognicao/qualidade_comunicacao.py`
- `mente_laylay/cognicao/validacao_contrato_fala.py`
- `mente_laylay/cognicao/fundamentacao_factual.py`

Regressões novas em `scripts/tests/test_posicionamento_resposta.py` e
`scripts/tests/test_posicionamento_resposta_composicao.py`. Comandos, XMLs,
comparações, base e auditoria estão na pasta de resultados citada acima.

GREEN focado e composição instalada controlada não são GREEN de conversa
natural com Qwen. Não houve conversa nova, voz, hardware, efeito externo nem
aumento de orçamento. Não há prova de parsing/opinião/paráfrase universais.
`memoria-005` e as demais raízes anteriores continuam separadas. O próximo
teste natural de Pedro pode verificar essas formas de posicionamento mantendo
os controles contra fatos inventados e efeitos não confirmados.
