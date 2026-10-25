# C5 — apoio individual nas explicações livres

Base: main, HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`, worktree já
modificada. Pedido: estudar erros livres, corrigir contrato compartilhado depois
da prova e validar na composição real. Histórico C5 preservado; não é uma nova
raiz por assunto nem encerramento geral de F1/C5/C7.

## Raiz demonstrada e contraprovas

Pedido → contrato semântico de ensino → autoria com declaração → revisão →
publicação. O contrato já deliberava `explicacao_didatica` antes da geração.
Na revisão, `requer_revisao` dependia apenas de referências propostas, fontes
presentes ou atualidade. Sem pesquisa e com `fontes=[]`, desaparecia a obrigação
e a explicação livre voltava a ser publicada. Ausência de apoio não provava
conteúdo; também não demonstrava que cada frase fosse falsa. A falha comprovada
é essa admissão, não uma explicação completa para o conhecimento errado do Qwen.

`red.xml`:7 falhas causais e3 controles sociais. `red_instalada_alcancada.xml`:
6 falhas na fronteira de revisão, em três assuntos/duas rotas. Em ciência e
programação houve4 publicações integrais sem apoio. Na instância linguística,
uma guarda posterior já substituía o texto por contingência, sem consertar a
obrigação ausente: não contar6 publicações indevidas nem usar compensação como
prova de saúde do contrato.

Falsificações: remover histórico ou usar prompt mínimo não corrigiu o conteúdo
nas ablações históricas; perda do envelope não explica declarações completas
capturadas; geração probabilística não é necessária para reproduzir a admissão,
que também ocorre com propostas controladas. Transporte/codec/IDs presentes
não são prova semântica. Não mexer no codec por ausência bruta do campo `fala`.

Revisão do candidato encontrou4 REDs em `red_proposta_operacional.xml`: comando
meramente proposto/bloqueado podia dispensar a obrigação. Corrigida a mesma
fronteira: quem determina a finalidade é o contrato do host; uma lista de
comandos da proposta não a substitui. Resultado operacional permanece sob os
receipts e a finalidade canônica correspondente.

## Contrato, responsáveis e escopo

| Owner | Responsabilidade e critério |
| --- | --- |
| `cognicao/contrato_fala.py` | Qualificar obrigação pelo roteiro didático/reensino do host ligado ao turno atual; conservá-la nas representações completa e compacta. Não classificar verdade por tema, expressão ou confiança. |
| `cognicao/revisao_suporte_autoria.py` | Aplicar conferência por unidade mesmo sem pesquisa; declaração ausente/inválida/dicionário/outra ocorrência/reescrita não elimina a obrigação. Comando proposto ou bloqueado não a dispensa. |

Sem apoio conferível, publicar um limite verdadeiro, sem inventar regra,
referência, causa ou efeito. Com fonte individual válida, conservar somente o
alcance já conferido: identidade literal permite citação atribuída, não verdade
externa certificada. Fonte irrelevante, recorte não conferido e autocertificação
do modelo não validam a proposição. `semantica_verificada`, `prova_implicacao`,
`pode_confirmar_fato_externo` e `autoriza_execucao` permanecem falsos.

Produção alterada nesta tarefa: **somente os dois owners acima**. Teste novo:
`scripts/tests/test_obrigacao_apoio_explicacao.py`. Nenhuma mudança em executor,
voz, configuração de modelo, pesquisa multifonte, interface ou hardware.
Arquivos prontos no workspace, sem edição manual pendente. Nenhum commit,
reset, reinício da sessão pessoal ou shutdown. Alterações paralelas preservadas.

## Validação e limites da prova

Artefatos em `resultados_testes/autoria_livre_obrigacao_20261023/`:

- `instalada_guardas.xml`: **41 aprovados**, incluindo12 ciclos instalados
  nas duas rotas: ausência de apoio, fonte literal, fonte irrelevante e comando
  operacional indevido. Uma publicação por turno, zero efeitos externos;
  captura, preparação, revisão e publicação canônicas mantidas. Modelo e
  disponibilidade das fontes controlados; isso não prova descoberta web real.
- `regressao_final.xml`: **1.286 aprovados,30 subtestes aprovados,12 skips,
  2 falhas,1 desmarcado**. As falhas são
  `test_autoria_reescritas::test_composicao_transporta_suporte_proprio_de_reparo_e_partes[4/6]`:
  esperam `principal` como primeira chamada, mas observam `interpretacao`.
  Mesmos IDs e primeira asserção em `reescritas_baseline.xml`, usando apenas
  os dois owners anteriores, inclusive nos subprocessos, com SHA conferido.
  Não foram apagadas, relaxadas ou chamadas de regressão resolvida.
- O teste desmarcado importa a root na sessão pessoal; aprovado separadamente
  na instalação isolada em `import_final.xml`, sem modificar suas asserções.
- `qwen_final/conversa.json`: **3 turnos/4 HTTP200/zero drift** com o modelo
  local selecionado. Ensino e “não entendi” conservam a obrigação; agradecimento
  segue social. Uma publicação por turno, zero executores externos; resultado
  publicado coincide com a realização do verificador. A geração real não é prova
  de conteúdo. Coletas intermediárias em `qwen_real` e `qwen_continuidade`
  preservadas; o candidato final é identificado pelos hashes da última coleta.
- `baseline.json`, backups `.antes`, `candidato.diff` e `verificacao_entrega.json`
  conservam base, escopo e hashes. Não atualizar baselines históricos anteriores.

O primeiro ensaio instalado falhou na captura do stdout (`StopIteration`), antes
da asserção causal; foi corrigida somente a coleta para `sys.__stdout__`.
Um controle positivo inicial usava uma resposta de5 palavras, rejeitada pela
guarda existente de entrega mínima de7. `diagnostico_qualidade.json` preserva a
causa; a fixture passou a conter uma explicação completa, mantendo as asserções
de fonte/citação/publicação. Não remover ou relaxar a guarda para fazer passar.

**Limite funcional:** esta correção impede publicação irrestrita na explicação
didática sem apoio; não ensinou gramática, ciência ou programação ao modelo.
Sem fonte, ela informa o limite, o que pode reduzir a utilidade. Aquisição de
fontes suficientes e explicações corretas, naturais e apoiadas continuam sendo
trabalho necessário. Pesquisa multifonte não foi ativada implicitamente.

**Próxima fronteira:** obter e conservar conteúdo pertinente para a pergunta e
conferir sua realização explicativa sem depender de autocertificação. Verdade
de fonte externa, implicação livre, perguntas factuais fora do roteiro didático,
composições mistas, criação ficcional e qualidade geral de conversa não estão
certificadas por esta prova. Não ampliar o bloqueio a toda conversa nem declarar
compreensão global concluída. P19, segmentação musical e demais pendências
históricas continuam separadas. Sem prova de áudio, uso diário ou efeito físico.

Reabrir a Laylay para carregar os módulos alterados; a instância pessoal aberta
não foi reiniciada durante a investigação.
