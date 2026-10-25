# C5/P01 — recuperação para a explicação solicitada

Base: main, HEAD `ae5b064f4034614693cf6f54ece6fca1834fb534`, worktree já
modificada. Autorização atual: estudar obtenção de fontes e corrigir o contrato
compartilhado após comprovação. Histórico C5/P01 preservado, sem encerrar
precisão factual ou compreensão geral. Base e backups em
`resultados_testes/fontes_explicacao_20261023/`.

## Raiz demonstrada

O leitor reconhecia o assunto didático, mas o orquestrador apagava a consulta
quando `modo_multifonte` estava desativado. Essa proteção nasceu de uma falha
real: presença de páginas não impedia o Qwen de extrapolar. Não era correto
simplesmente remover a proteção ou trocar a configuração para `ativo`.

O contrato faltante era separar **recuperação solicitada** de **influência
irrestrita**. A etapa anterior já mantinha a obrigação independente de apoio
individual na revisão. Agora o host delibera a finalidade primeiro e encaminha
a leitura do assunto autossuficiente, conservando aquela revisão. A proposta
do modelo não escolhe a autoridade, não solicita a busca e não aprova a fonte.

Com os três owners anteriores carregados em memória, serviço da factory real
ligado e HTTP de folha controlado, o coletor leu duas páginas nos controles,
mas o caminho instalado fez zero chamadas e manteve fundamentação vazia.
`red_base_alcancada.xml`:6 REDs, três assuntos nas duas rotas. Parser íntegro,
coletor apto e ausência de geração necessária falsificam perda de extração,
indisponibilidade do provedor no controle e omissão de ferramenta pela IA como
causa necessária desse recorte.

## Responsáveis e contrato

| Owner alterado | Responsabilidade e critério |
| --- | --- |
| `cognicao/pesquisa_multifonte.py` | Identificar conservadoramente consulta autossuficiente. Referência pessoal/local, endereço ou foco contextual não resolvido não vira busca pública por suposição. Reutilizar o coletor e o leitor existentes. |
| `cognicao/pesquisa_contextual.py` | Recuperar apoio com o mesmo orçamento interativo, cache de páginas e coordenação de trabalhos em andamento. Resumo legado não substitui páginas individuais; consulta/foco têm chaves próprias. |
| `cognicao/orquestrador_turno_runtime.py` | Encaminhar somente após finalidade didática/reensino do host ligado ao turno. Atualizar evidência pelo mesmo owner do contrato, sem autorização operacional. Registrar motivo, quantidade lida e estado da pesquisa no turno. |

`modo_multifonte` amplo permanece **desativado**; nenhuma configuração foi
alterada. A autorização atual permite esta rota de leitura para a explicação
solicitada, não a ativação geral da ideia antiga de pesquisa em cinco camadas.
Não criar buscador, parser de comando, executor ou revisor paralelo.

Tempo de leitura excedido retorna pendência pelo orçamento existente. O
trabalho pode concluir no cache; não modifica a fonte do turno já publicado e
não injeta conteúdo em uma consulta nova. Reensino compatível consulta o mesmo
assunto/foco. Falha ou fonte ausente não vira sucesso, nem força uso de resumo
agregado. Nenhum aumento de timeout ou troca de modelo/voz.

Página e URL presentes continuam sendo contexto. A revisão confere cada
proposição; literal integral permite **citação atribuída**, não certificação de
verdade. `semantica_verificada`, `prova_implicacao`, confirmação de fato externo
e autorização permanecem falsas. Fonte lida não valida automaticamente
paráfrase, exemplo ou conclusão adicional.

## Evidência atual

- `foco_final.xml`: **26 aprovações**, sendo14 controles de escopo,
  cache e concorrência, mais12 ciclos instalados. Três assuntos nas duas
  rotas recuperam páginas; os negativos retêm acréscimos, páginas irrelevantes
  e consultas contextuais. Uma publicação por turno, zero executores mutantes.
  As folhas HTTP/modelo são controladas, não os owners de pesquisa ou revisão.
- `regressao_final.xml`: **1.324 aprovações,30 subtestes,12 skips opcionais,
  2 falhas preexistentes,1 desmarcado**. Não é suíte ampla verde. Falhas
  `test_autoria_reescritas::test_composicao_transporta_suporte_proprio_de_reparo_e_partes[4/6]`
  esperam `principal` como primeira chamada, mas recebem `interpretacao`.
  Mesmos IDs e mensagens em `reescritas_baseline.xml`, com os três owners
  anteriores carregados também nos filhos e SHA conferido. Testes preservados.
- O desmarcado importa a root diretamente e encontra a sessão pessoal aberta;
  o mesmo teste passou isoladamente em `import_final.xml`, sem relaxar asserções.
- `qwen_fontes_controladas/conversa.json`: **3 turnos/3 HTTP200/zero drift**.
  Fontes chegaram ao plano e ao contexto autoral. As3 respostas foram limitadas
  porque houve omissão de referências ou conteúdo adicional não conferido.
  Isso falsifica que recuperar fonte baste para produzir uma aula útil.
- `web_real/conversa.json`: **2 turnos/3 HTTP200 do Qwen/zero drift**. Primeiro
  turno: orçamento esgotado, publicação de limite, sem fonte retroativa. No
  “não entendi”, o cache ofereceu **5 páginas lidas**. Uma proposição literal
  foi publicada com atribuição; as outras2 ficaram sem apoio conferido e foram
  retidas. O trecho veio da página de [fotossíntese da Toda Matéria](https://www.todamateria.com.br/fotossintese/).
  Essa é identificação da origem observada, não endosso científico da página.
- Na web real foram observados6 GETs HTTP200 e1 `ConnectTimeout`. Falha do
  provedor registrada separadamente; não afirmar disponibilidade universal.
  GET público e LLM local foram as únicas folhas de rede permitidas pela sonda.
  Sem áudio, reprodução musical ou outra ação mutante comprovada.

O piso existente de duas páginas/domínios e o teto de cinco foram preservados.
Cinco fontes são observação dessa coleta, não prova de verdade por contagem.
Seleção lexical de trechos e admissibilidade não certificam implicação livre,
qualidade editorial ou pertinência semântica universal.

## Correção da própria investigação

O helper de isolamento de autorização desconecta pesquisa do registro de
serviços. Por isso `red_instalada.xml` e `diagnostico.xml` iniciais não provam
esta fronteira em produção. A sonda foi corrigida para reconectar a **mesma
instância que a composição real criou**, com identidade conferida por asserção.
O candidato já havia sido aplicado quando a limitação foi descoberta.
Interrompidas as alterações, a contraprova em memória dos três arquivos
anteriores alcançou o RED causal em `red_base_alcancada.xml`, sem restaurar ou
apagar a worktree. Não apresentar o primeiro RED inválido como prova anterior
ao patch. O GREEN seguinte, `green_caminho.xml`, usa a mesma ligação corrigida.

Auxiliares neurais do helper continuam fora do recorte; pesquisa, planejamento,
preparação, codec, revisão e publicação usados aqui são os owners instalados.
Isso não comprova uso diário da sessão pessoal ou todas as combinações entre
habilidades. Os resultados de rede/Qwen são separados dos controles sintéticos.

## Limites e próxima fronteira

O recorte de consulta autossuficiente é conservador: pode rejeitar temas
legítimos com pronomes ou foco contextual, inclusive a comparação solta entre
“eu” e “mim”. Não se resolveu esse sentido por exceção de frase. Referências
locais exigem fonte contextual apropriada ou melhor qualificação semântica.

A aquisição agora funciona nesse caminho, mas **autoria apoiada e natural
continua aberta**. O teste real mostrou que o Qwen ainda acrescenta conteúdo
ou omite referência apesar de receber a fonte. Próxima fronteira é realizar
uma explicação útil dentro do alcance conferível da evidência, distinguindo
definição, exemplo e conclusão, sem exigir uma segunda opinião do mesmo modelo
como prova e sem preencher lacunas por plausibilidade.

Escopo desta tarefa: somente os três owners listados e dois arquivos de teste
novos. `candidato.diff`/`verificacao_entrega.json` preservam hashes e comparação
com a base. Nenhum commit, reset, mudança de configuração, reinício pessoal ou
shutdown; UI, hardware e alterações paralelas preservados. Reabrir a Laylay
para carregar os módulos modificados no disco.
