# Perdão/confiança — confirmação e continuidade predicativa

## Escopo e base

Continuação do DIAGNOSTICO_PERDAO_CONFIANCA_20261029.md, autorizada por Pedro.
Preservados os IDs `perdao-001`, `perdao2-003` e o controle `perdao2-011`.
São **duas raízes de produção**, com owners e provas separados. Ajustes no
ambiente de validação são relatados à parte. Não reclassificar orçamento
como causa primária nem contar cada variante de teste como outra raiz.

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`, worktree suja
preservada. As 536 fontes anteriores foram congeladas antes dos candidatos em
`resultados_testes/escopo_atos_20261029/base` e `baseline.json`.
Nenhum commit criado. A auditoria diferencia este delta das mudanças anteriores.

## 1. Confirmação exige polaridade no próprio ato

Na abertura, o leitor compartilhado reunia `não` e `quero` de orações distintas.
Devolvia False, e a modalidade criava uma recusa. O contrato de fala pedia
reconhecer não execução em vez de discutir perdão. Reparos posteriores consumiam
o orçamento. O journal histórico registra duas emissões válidas e bloqueio
temporal; não registra JSON malformado nessa abertura.

Owner corrigido: `memoria_mental/aprendizado_rotina_musica.py`, função
`classificar_confirmacao_local`, já utilizada por modalidade e pendências
de vários domínios. A confirmação deixa de usar sacos de palavras; as leituras
de polaridade ficam ancoradas no ato matriz. O aceite legado `quero sim tocar`
permanece; o modo de aceite genérico continua sem absorver esses verbos.
Formas não demonstradas são devolvidas como None ao owner contextual.

Recusas como `Por enquanto não quero`, `Não, eu quero deixar como está` e
`Não posso abrir agora` permanecem negativas. Conversa independente preserva
pendência ativa de arquivos, música e e-mail; recusa real a resolve. Uma menção
a `sim` dentro de uma pergunta não aceita a oferta. Não foram alterados os
executores, receipts, políticas de autorização ou limites de chamadas.

RED inicial: 34 falhas e 14 controles aprovados. Propostas intermediárias que
perdiam recusas ou introduziam `preciso` como falsa recusa foram rejeitadas;
seus REDs estão preservados, sem reinterpretá-los como sucesso.

## 2. Coordenação não remove o sujeito do predicado

Em `perdao2-003`, o corte após vírgula/mas extraía `continua sofrendo o prejuízo`
da oração sobre `a outra pessoa`. O recorte adquiria autoridade de pedido
direto e substituía a resposta temática pelo aviso de ação não executada.
Isso já ocorria antes do candidato de diretiva de formato; independe do
normalizador instalado. Não é a causa morfológica de `memoria-005`.

Owner da decisão: `cognicao/modalidade_turno.py`, admissão da fronteira entre
atos. O novo leitor `morfologia_oracao.py` fornece somente evidência linguística
para conservar a oração. Não decide habilidade, alvo, autorização ou efeito.
O classificador operacional existente continua sendo o único owner de autoridade.

Foram descartados candidatos que supunham predicação por sufixo ou quantidade
de palavras. Eles bloqueavam `Boa tarde`, `Excelente ideia`, `Muito obrigada`
e `Uma boa ideia` antes de uma ordem legítima. Não foram criadas exceções para
essas frases. A solução usa formas finitas e concordância nominal/adjetival
de um índice offline do [PortiLexicon-UD](https://github.com/LuceleneL/PortiLexicon-UD),
fonte já utilizada nas pesquisas morfológicas do projeto.

O índice tem commit/hash fixados, gerador reprodutível, licença MIT e atribuição
inteiras no recurso. `VERB.tsv` confere com o hash já congelado no gerador
condicional anterior. Classes nominais completas não são tratadas como orações;
nomes próprios unitários, pronomes, adjuntos e clíticos têm controles próprios.
Imperativos formais são lidos pela morfologia real, não por conjugação presumida.

Os intervalos citados passam pelo leitor canônico `texto_fora_de_citacoes` e
permanecem opacos. Uma palavra dentro de aspas não vira sujeito/verbo ao remover
pontuação. Saudações reutilizam `separar_saudacao_inicial`. Ordens anteriores
já demonstradas, cortesia e pontuação forte conservam seus caminhos existentes.
Índice indisponível não é prova de independência para extrair outro comando.

O recurso gerado é um módulo Python de aproximadamente 3,1 MB, para acompanhar
a cópia filtrada da ponte e a coleta de módulos do empacotamento atual. O leitor
faz busca binária em bytes e cache pequeno, sem criar um dict de 862 mil formas.
Não instala pacote/modelo nem consulta a rede no runtime. É um leitor raso,
sem garantia de análise universal de relativas, coordenações ou nomes compostos.

## Provas e limites

- **216 testes focados aprovados**: 181 dos contratos desta entrega (incluindo
  cinco composições instaladas), 34 da oferta de abas e um canário de isolamento.
  As composições usam portas, origem, modo silencioso e identidade da ponte.
- Nove comparações instaladas: base, somente confirmação corrigida e candidato
  completo, para os três IDs preservados. Substituição de owners antigos ocorre
  somente em memória; não houve restore da worktree.
- `perdao-001`: a base seleciona negação operacional, faz duas chamadas e bloqueia
  outra; somente a correção de confirmação já publica a opinião fixa em uma
  chamada, sem bloqueio. O ensaio não reproduz os tempos da sessão histórica.
- `perdao2-003`: a correção de confirmação sozinha não resolve a autoridade
  indevida; o candidato completo publica a opinião fixa sem autoridade em uma
  chamada. Isso falsifica a hipótese de uma raiz única para os dois sintomas.
- `perdao2-011`: a objeção histórica preservada continua sendo publicada
  integralmente em uma chamada nas três variantes. Não certifica a verdade
  universal do argumento nem um estado subjetivo da assistente.
- Dois controles de comandos/receipts falsos propostos pela IA são rejeitados
  e reparados sem execução. Voz e efeitos reais permaneceram suprimidos.
- A função real de cópia da ponte foi executada isoladamente sem abrir conversa.
  Os dois novos módulos chegam byte a byte à cópia; a classificação nessa cópia
  conserva relato e pedidos legítimos. Não foi executado build portátil.
- 1.002 consultas binárias conferidas contra o índice, sem divergência. Revisão
  independente conferiu outras 202 consultas, 174 testes puros e 47 sondas de
  modalidade/citações. Leitura fria sem instrumentação na revisão: cerca de
  275 ms, mais importação; memória retida aproximada de 16 MiB. A sonda com
  tracemalloc é preservada separadamente e não representa latência normal.

Regressão ampla relevante final: **4.494 aprovados, zero falhas/erros**, em 173
módulos; 14 skipped, um deselected e um xfailed preservados, com 30 subtestes
aprovados. Nenhum ID da ampla anterior ou da rodada RED desapareceu. Não é
declaração de suíte total, build portátil ou semântica universal.
Três execuções intermediárias foram
interrompidas antes de alterar os candidatos; seus logs e árvores de processos
estão preservados. Não contam como GREEN. Os filtros anteriores são mantidos.

Uma rodada completa anterior está preservada em `red_ampla_*`: 4.474 aprovados,
duas falhas e 15 erros de fixture. As duas regressões reais eram aceites como
`sim, pode esquecer/substituir`: voltaram a ser aceitos pelo ato matriz, sem
reintroduzir o saco de palavras. RED antes do ajuste e 107 controles aprovados.

## Correção do ambiente de validação, separada das raízes de produção

A ampliação incluiu uma fixture antiga antes de conferir todo seu isolamento.
Ela importava a composição pessoal e seu log revelava o catálogo de playlists;
depois falhava ao serializar `PerspectivaEnunciador`. Não se deve atribuir seus
15 erros ao modelo nem converter o funcionamento parcial em evidência GREEN.

A fixture agora reutiliza a instalação fonte, com base/perfil/diretório atual
privados antes dos imports e código de produção original, alterando em memória
somente os caminhos de filesystem. Configuração copiada contém apenas as três
chaves locais do modelo. Quatro asserts conferem base, memória, playlists e
legado; dois asserts e auditoria do filho rejeitam tentativas de escrita,
migração, SQLite, rede ou processos fora do ensaio. `os.devnull` é o único sink
especial permitido. Não se alterou HOME nem foi iniciada conversa com Qwen.

O utilitário é compartilhado por essa fixture e pelos cinco compostos desta
entrega; as nove comparações foram refeitas com ele, sem violações. Um canário
em diretórios descartáveis confirma que origem externa não é escrita/movida;
desativar a guarda somente em memória produz o RED esperado. Essa auditoria é
uma guarda do processo Python do ensaio, não um sandbox geral do sistema.

Serialização de dataclasses ocorre somente no diagnóstico, preservando campos;
tipos desconhecidos continuam falhando. AST das 17 funções de teste, incluindo
asserções e parâmetros, é idêntica à anterior; os mesmos 34 casos passam.
`fixture_baseline.json`, `diff_fixture.patch` e `fixture_auditoria.json` documentam
a mudança. A auditoria de fontes não equivale a snapshot histórico dos dados
pessoais; não alegar retroativamente que a fixture antiga estava isolada.

Há outra fronteira registrada, sem patch nesta entrega: a resposta de opinião
`Oi! Eu vejo o perdão como uma escolha possível...` é recusada por
`pergunta_direta_nao_respondida`, apesar de atender ao roteiro multiacto. É um
limite do leitor de posição da revisão, diferente das duas causas acima.
O teste de publicação usa uma opinião explícita com `Acho`, preservando a
verificação em vez de dispensá-la. Ensaios anteriores rejeitados são mantidos
em `abertura_qualidade.json`, `abertura_candidato.json` e XMLs intermediários.

`Não preciso conhecer o autor para gostar da música` é None no leitor de
confirmação, mas a modalidade musical já o classificava como recusa na base.
Esse resultado preexistente foi separado dos testes do helper; não foi usado
para justificar alteração de outra guarda nem ocultado como correção desta raiz.

Produção alterada: `modalidade_turno.py` e `aprendizado_rotina_musica.py`.
Produção adicionada: `morfologia_oracao.py` e `lexico_morfologico_dados.py`.
As demais 534 fontes anteriores estão intactas contra a base congelada.
Não houve conversa nova/Qwen real, áudio, hardware, ação externa, alteração
de orçamento, personalidade ou revisão factual. Conversas reais seguem com Pedro.

Artefatos, manifestos, gerador, auditoria e comandos exatos:
`resultados_testes/escopo_atos_20261029`.
