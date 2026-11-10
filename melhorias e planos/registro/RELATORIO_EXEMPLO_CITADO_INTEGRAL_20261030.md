# Exemplo de fala perde o escopo na revisão factual — 30/10

## Base e evidência

HEAD `1197daf0d6b5e69b7243f571542bf17666274ea2`, branch
`codex/correcao-autoria-conversa-20261030`, worktree inicialmente limpa.
Sessão `C:/Users/pbarr/Downloads/ponte_laylay/sessoes_chatgpt/20261030T195853Z-0d4ab6c2`,
ID `casa-20261030-14`. A entrada pede como formular uma crítica hipotética.
O retorno de reparo contém o exemplo completo; a publicação remove seu início
e conserva a continuação com aspas quebradas.

Artefatos em `resultados_testes/exemplo_citado_20261030`: baseline, fontes
congeladas, REDs, XMLs, comparação instalada e registros de regressão. Fixture
reproduz a entrada, a autoria histórica, o resultado cortado e os 13 pares
anteriores publicados. O retorno `modelo_retornou` é pós-codec, não corpo HTTP.
No replay, a fala é fornecida pelo contrato V5 canônico de suporte, sem
confundir os campos sintetizados com o wire do modelo.

## Primeira fronteira e contrato

Geração reparada contém o exemplo → processamento conserva a fala → revisão
factual perde o papel enunciativo → remove trecho → publicador confirma texto
já modificado. O aviso `alegacao_especifica_sem_fonte` não é causado pelo
transporte. Não tratar a mera publicação como atendimento ao pedido.

O owner `fundamentacao_factual` limita a leitura de citações a 100 caracteres,
reconhece apenas algumas flexões introdutoras e separa frases dentro do objeto
citado. A menção de papel `criador` na condição também é tomada como detalhe
factual, embora `Se ... eu diria: ...` não afirme a ocorrência da condição.

Contrato: um exemplo delimitado de enunciado é dado textual completo. Seu
papel acompanha a revisão sem se transformar em prova de fatos, fonte externa,
autorização, receipt ou efeito. Afirmações externas e citações factuais mantêm
os verificadores existentes, com a mesma granularidade por oração.

Hipóteses falsificadas: o corte exato é reproduzido sem transporte; a higiene
final e o detector de experiência física não removem esse trecho; o problema
não exige nova conversa ou uma nova resposta do modelo para ocorrer.

## Candidato e responsabilidade

Produção alterada somente em:

- `mente_laylay/cognicao/fundamentacao_factual.py`: reconhece o objeto citado
  sem o teto semântico de 100 caracteres; usa as flexões condicionais de
  enunciação; projeta a moldura local `Se ..., eu diria/responderia/escreveria`
  apenas quando governa um exemplo reconhecido; predicação nominal externa
  explícita ainda identifica obra. Protege só intervalos do papel `enunciado`.
- `mente_laylay/cognicao/referencias_linguagem.py`: permite ao owner fornecer
  intervalos estruturais e conservar sua política de ponto e vírgula. O
  comportamento padrão dos demais consumidores permanece igual à base.

`plano_turno`, publicador, orçamento, codec, personalidade e executores não
foram alterados. Nenhum catálogo de frases históricas ou bypass por gênero.
O exemplo não pode anunciar efeito externo sem o respectivo receipt.

## Revisão, REDs e decisões de escopo

RED inicial final: 23 falhas esperadas e dois controles verdes; falha histórica
também alcança a composição instalada e publica o mesmo corte. Candidato
inicial insuficiente e seus resultados intermediários foram preservados.

Revisão independente somente leitura encontrou e tornou RED:

- Agrupar citações factuais transfere opinião, primeira medida ou nome de
  candidato para outra afirmação sem fonte. Candidato final agrupa somente
  exemplos, conservando todos os verificadores factuais por oração.
- `diria: "X" é um filme` continuava sendo título. Predicação externa nominal
  tem precedência; não se torna exemplo por causa do verbo introdutor.
- Markdown já possuía papel de enunciado, mas não tinha seu intervalo
  preservado. O mesmo owner passa os intervalos nativos ao segmentador.
- Fechar a frase na pontuação interna das aspas separava sujeito e predicado
  externos, inclusive numa consulta sobre o presidente. Essa tentativa foi
  retirada por completo; pontuação interna não inventa fronteira externa.
- O factual antigo não separava ponto e vírgula: mudar isso soltava predicado
  com sujeito elíptico. O owner conserva explicitamente a política anterior.

Dois asserts novos exigiam rejeitar citações factuais inteiras; a expectativa
era maior que o contrato aprovado e alterava a granularidade histórica. Foram
corrigidos para exigir rejeição da afirmação sem fonte. O teste de preservação
do exemplo vizinho usa fronteira externa explícita. Sem essa fronteira, a
rejeição conservadora do bloco pode incluir o exemplo, mas nunca liberar o
fato inválido. Os controles negativos originais e seus IDs foram mantidos.

## Provas e limites

Foco final: 217 aprovados em quatro módulos, incluindo 49 novos casos e três
composições instaladas controladas. Comparação no mesmo adapter/root e histórico:
owners congelados publicam o corte histórico exato; candidato publica a fala
integral, uma HTTP por caminho, sem voz, efeitos, autoridade ou violação do
perfil isolado. `comparacao_instalada.json` conserva os resultados.

Revisão final independente: nenhum novo bloqueio, 46 testes puros aprovados;
3.000 entradas sintéticas com segmentador padrão equivalente à base e outras
3.000 comparações conservando granularidade factual sem exemplos protegidos.
Isso não prova entendimento semântico universal.

Regressão ampliada final em123 módulos:3.625 aprovados,24 falhas,30 erros,
25 skips,um xfail e um teste desmarcado pelo mesmo filtro prévio. Os54 resultados
negativos foram reproduzidos por ID e classe com os dois owners congelados,
inclusive nos subprocessos; `baseline_importada.json` confere os caminhos.
Nenhum desses resultados apareceu apenas com o candidato. Dez falhas eram
ausência da pasta de saída de `limites_tematicos_20261030`: após preparo, os
mesmos dez testes passaram na base e no candidato. Restam14 falhas/30 erros
anteriores. Não declarar suíte ampliada verde e não confundir54 evidências com
54 raízes novas. IDs, filtros e expectativas preexistentes foram preservados.
Resultados em `resumo_final.json`; demais pendências incluem controles de
volume, relato de alívio, expectativa antiga de estado, recuperação histórica,
classificação condicional e fixtures incompatíveis com objetos tipados.

O erro de serialização de
`FonteCapacidadesTurno` no fixture de correlação também ocorre com os dois
owners congelados (`baseline_serializacao.xml`), sem alteração de produção;
é uma pendência independente, não motivo para enfraquecer a revisão.

Instalação: todos671 arquivos do snapshot original ainda coincidiam com a
base antes da escrita. Guardas por hash dos dois owners e comparação dos
documentos contra HEAD antecederam a aplicação do delta na cópia original
`C:/Users/pbarr/Downloads/pasta organizada/programacao/PY/projeto lay/laylay`.
Os49 testes novos passaram novamente nessa cópia, incluindo as três
composições isoladas. Depois, os671 fontes ficaram equivalentes entre cópia
original e worktree; somente os dois owners diferem da sessão histórica.
`instalacao_original.json` registra a conferência. Configuração privada e
alterações paralelas foram preservadas. Nenhum processo pessoal foi iniciado,
encerrado ou reiniciado; uma sessão já aberta pode continuar com seu snapshot
antigo. O próximo teste natural deve abrir nova sessão da ponte.

Sem nova conversa/Qwen, rede, voz, efeito real ou alteração de configurações
privadas. Rodadas3/16/18, perguntas abertas, seleção temática, criatividade e
troca de interlocutor permanecem em suas investigações, sem encerramento por
semelhança de sintomas. Nenhum commit, push ou desligamento nesta etapa.
