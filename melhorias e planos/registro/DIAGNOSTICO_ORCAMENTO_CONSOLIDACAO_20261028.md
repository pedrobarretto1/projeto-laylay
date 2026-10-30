# Quinta interação — geração auxiliar no orçamento da resposta

Base congelada: HEAD c91cae1bd407b02db946ae7bc752d1ed3269bfd9, main,
534 fontes. Artefatos em `resultados_testes/orcamento_consolidacao_20261028`.
Worktree anterior preservada. Não foi alterada a ponte atualizada.

Novos journals de Documents confirmam19 entradas/16 retornos de protocolo,
três erros e19 publicações. As três sessões com erro chegaram à quinta entrada;
outra encerrou normalmente após quatro. max_rodadas=0; o limite da ponte não
causou os erros. Snapshots sem divergência dos fontes no início desta análise.

Primeira fronteira comprovada: adicionar_interacao persiste a fala e chama
atualizar_resumo_diario a cada cinco. Binding do composition root usa tipo
principal por omissão, permitindo interação. A chamada ainda está dentro do
orçamento do turno principal, já consumido ou expirado. Diário preserva lote
em falha, mas o adaptador da ponte usa o último resultado de qualquer geração
para definir modelo_falhou; uma publicação anterior não impede erro fatal.
Não atribuir todos os problemas ao revisor: aventura-005 tem também uma
tentativa autoral bloqueada antes do resumo. Esses eventos foram conservados.

RED de composição instalada, com orçamento e callbacks reais e só HTTP
sintético: cinco registros pedem mais uma geração tipo principal, permitindo
interação; orçamento a recusa. Não era falta de texto gerado nem contador da
ponte. Segundo RED demonstrou lock do diário mantido durante geração.

Foi experimentado um candidato de consolidação diferida pelo gerenciador
existente, fonte independente de contexto, tipo manutenção, guarda global de
turno ativo e consumo somente do lote capturado. Passou81 casos focados.
A revisão independente, porém, reproduziu dois bloqueadores:

- Manutenção admitida em ócio já segura o transporte quando começa um turno;
  a principal espera1,5s e falha como ocupada. Admissão não é preempção.
- Capturar50 interações e receber outra durante geração trunca o prefixo;
  a guarda rejeita o resumo e a primeira interação desaparece do arquivo.

O candidato **foi retirado integralmente** dos quatro arquivos por patch
controlado, após conservar suas versões e hashes em candidato_rejeitado/.
Os hashes voltaram exatamente à base desta investigação. Sem reset/restore,
sem remover alterações antigas, sem commit/modelo/voz/efeitos alterados.
Testes experimentais do candidato estão nos artefatos, fora da suíte regular.

Raiz ainda aberta. O contrato necessário distingue resultado do turno de
manutenção e preserva identidade, lote, prioridade e cancelamento reais.
Não resolver aumentando orçamento, ignorando falhas ou reduzindo inteligência.
Uma próxima implementação precisa proteger a fala que chega durante uma
geração auxiliar e persistir também o lote em processamento; verde de
admissão/worker isolado não comprova isso. O aviso de fontes no começo de
sessão é outra investigação, com propostas e fontes específicas conservadas.
