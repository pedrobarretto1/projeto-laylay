# Reencontro da biblioteca — diagnóstico e correções por contrato

Sessão investigada: `20261101T172322Z-4d9e8c27`, sete rodadas, seis turnos
retomados, Qwen3 4B Instruct. A ponte foi preservada aberta. Caminho real:
`C:\Users\pbarr\Downloads\pasta organizada\programacao\PY\ponte_laylay\sessoes_chatgpt\20261101T172322Z-4d9e8c27`.

Base: `1197daf0d6b5e69b7243f571542bf17666274ea2`, branch
`codex/correcao-autoria-conversa-20261030`, worktree anterior preservada.
Plano com responsáveis e critérios: ../planos/PLANO_BIBLIOTECA_RETORNO_20261101.md.
Artefatos locais: `C:\Users\pbarr\.codex\worktrees\publicacao-conversa-segura\laylay\resultados_testes\biblioteca_retorno_20261101`.

## O que os registros comprovam

O snapshot da sessão tem os 539 fontes atuais; só três arquivos neurais
diferem em EOL, sem diferença de código. Não atribuir estas falhas a uma
sessão que carregou código antigo. O pacote efetivamente usado difere do
antigo pacote de Documents na seleção de provedor; a reprodução usa sua
factory real, não assume equivalência entre as pontes.

Rodada 1: geração principal bem-sucedida; reparo de comunicação recusado por
prazo. Rodadas 3/5: histórias geradas com sucesso, mas publicação substituída
pelo host por “Entendi a ação que você pediu...”; falhas_geracao vazio não
implica qualidade nem classificação correta. Eventos confirmam autorização
e texto operacional indevidos nessas duas entradas.

O leitor de autoria e a qualidade responsáveis pelos sintomas já estavam
iguais antes da última etapa da rodada 6. A repetição do sintoma é real; a
evidência não mostra que a correção do adjunto/lookup tenha reintroduzido
estas causas. Comparação em comparacao_ultima_etapa.json. São lacunas dos
contratos anteriores, sem apagar ou recontar os IDs históricos.

## Autoria/operação — rodadas 3 e 5

“Continue nossa história com uma reviravolta engraçada, em duas frases”
escapava do match integral: o leitor reconhecia extensão ou tom, mas não a
composição de conteúdo e formato. Na rodada 5, a moldura “Agora tente assim”
e a autoria de mini-história com tema também ficavam fora. Sem o detector
real injetado, a sonda simples desta última retornava conversa; a composição
real, com o mesmo histórico e detector, reproduziu comando e execução exigida.
Por isso o diagnóstico não foi baseado apenas na classificação isolada.

O verificador aplicava sua proteção legítima de não confirmar ação sem
executor a um turno indevidamente operacional. Replays antes dos candidatos
reproduziram a contingência em ambas as entradas, mesmo com histórias prontas.
Timeout não é necessário para esse sintoma; modelo e transporte não omitiram
as histórias. Não se alterou a frase de fallback para escondê-lo.

Contrato compartilhado em normalizacao_linguagem: objeto discursivo, conteúdo,
formato e canal precisam fechar o ato inteiro. Prefácio de reformulação só
projeta a instrução seguinte para esse leitor; não muda a fala original ou
autoriza recurso externo. Tema nominal pode ter relativa finita com complemento
nominal, usando a morfologia compartilhada. Não é campo de prosa arbitrária
capaz de absorver outra instrução ou destino.

RED inicial: 10 falhas e seis controles verdes. Revisão independente encontrou
relativa absorvendo “: abra o navegador”, “no bloco de notas” e “por e-mail”.
Três REDs adicionais foram confirmados e o contrato da relativa foi restringido;
os contraexemplos voltaram a ficar fora da transformação conversacional.
Não se adicionaram exceções para bolinhas, bibliotecárias ou números de rodada.

## Consulta de consequência — rodada 1

Primeira rejeição comprovada em validar_aderencia_contrato_fala:
ato_opiniao_nao_respondido. “O que você acha que aconteceria se...” ganhava
obrigação avaliativa de posição/critério. A resposta histórica efetivamente
propunha uma consequência; não precisava dizer “acho” para responder.

Falsificações com composição controlada: sem histórico, o mesmo RED; sem
saudação, o mesmo RED; removendo só “você acha que” da pergunta, a mesma resposta
passava; prefixando só “Acho que” na resposta, também passava. Um cenário real
de bateria acabando durante gravação mostrou a mesma falha. Portanto, ampliar
ficção ou ignorar cumprimentos seria patch na camada errada.

O prazo expirado é um limite real registrado, mas posterior à decisão indevida
de reparar. O replay rápido anterior ainda tentava reparo e atingia limite de
chamadas; não se aumentou orçamento. Com a obrigação correta, o mesmo retorno
principal publica em uma chamada e não solicita a recuperação desnecessária.
Isso não comprova eliminação de todos os timeouts em futuras gerações lentas.

texto_pede_opiniao continua protegendo a rota conversacional; não retirar essa
proteção de “acha”. Um leitor compartilhado mais restrito qualifica a consulta
de consequência condicionada. Não é todo verbo futuro/condicional, ficção,
factualidade ou licença semântica. contrato_fala usa as fontes textuais dos
atos e conserva avaliações independentes. O limite 32 é da leitura contextual
já existente; não amplia o schema autoral nem o limite de execução.

Uma segunda imposição duplicada em qualidade_comunicacao ainda rejeitava o
caso real de bateria, embora o contrato já estivesse correto. Foi demonstrada
por novo RED; a qualidade agora consome a finalidade positiva do owner sob
PerspectivaEnunciador nativa vigente, identidade e texto conferidos. Ausência
de opinião não prova projeção; a guarda lexical anterior continua nos outros
casos e para fonte ausente/inválida.

A revisão encontrou e bloqueou duas generalizações indevidas do candidato:
dispensar perguntas favoritas/avaliativas não cobertas pelo owner e absorver
avaliação junto da consequência. Contraexemplos de vírgula/cópula e fonte
inválida foram incorporados. Outra revisão confirmou seis REDs com duas
perguntas em ambas as ordens: qualificar apenas uma não dispensa a outra.
Agora a finalidade positiva exige todas as consultas qualificadas; demais
guardas permanecem. Não há outro parser de consequência na qualidade.

## Prova de composição e revisão

55 testes finais novos aprovados: autoria/modificadores, consequência/avaliação
e seis composições nativas. Revisão independente final: 49 testes locais e
sondas adicionais, sem bloqueios restantes no escopo. Achados e ensaios
intermediários permanecem nos XMLs/logs; a primeira regressão ampliada foi
interrompida e arquivada antes de aplicar o último ajuste de cobertura.

Mesma factory do pacote da sessão, root, histórico, plano, revisores, orçamento
e publicação; HTTP fixo, perfil privado, auditoria de efeitos e voz bloqueados.
Nas três entradas históricas, uma chamada e uma publicação, sem execução
exigida, sem degradação ou bloqueio. Rodadas 1/5 publicam a fala histórica
inteira. Na rodada 3, a normalização preexistente de reticências para ponto
permanece; não declarar literalidade byte a byte desse caso. Controle real de
bateria publica cautela sem exigir “acho”, e receipts propostos APP_OPEN e
MEDIA_CONTROL não produzem efeito ou autorização.

Propostas da IA continuam propostas. Não se certifica a verdade das narrativas,
causas internas ou equivalência factual; a revisão factual e os executores não
foram alterados. Não houve nova conversa Qwen, emissão de voz ou ação externa.

## Instalação e limites

Produção alterada: normalizacao_linguagem, contrato_fala e qualidade_comunicacao.
Instalação original conferida por 539 hashes, backup e apply_patch; três
candidatos idênticos e 536 outros fontes preservados, incluindo EOL neural.
Três módulos novos e fixture textual. Nenhum commit, push, shutdown ou reinício
da sessão de Pedro. A primeira invocação do venv usou um nome de teste inexistente
e não executou testes; o log ficou preservado e não é evidência de aprovação.
Venv original, invocação corrigida: 170 testes aprovados, zero falhas/erros,
nove módulos em 82,96 segundos. `original_final.xml/log` incluem as seis
composições com o pacote real da sessão.

Regressão final: 160 módulos, 4.750 aprovados, 25 skips, um deselected,
três subtests, zero falhas/erros/xfails em 603,53 segundos. Mantido o filtro
anterior do perfil explicativo, sem exclusão nova. Auditoria por classe/nome
confirmou os 44 IDs históricos e os dois casos musicais originais aprovados.
Os 539 fontes permaneceram estáveis durante a execução; três candidatos iguais
no original e 536 outros fontes originais preservados. `resumo_final.json`
registra os totais conferidos. O log amplo interrompido está separado e não
substitui esta prova final.

As três ocorrências relatadas ficam corrigidas no recorte demonstrado, com
composição nativa controlada e regressão relevante. Não se declara nova sessão
Qwen validada, qualidade universal das falas ou eliminação de todo timeout.

O relato também contém, na rodada 4, justificativa pessoal produzida pelo
modelo ao explicar sua própria resposta; este relatório não comprova a causa
dela nem encerra a revisão dessa explicação livre. A qualidade/adequação da
piada longa da rodada 6 tampouco é validada pelo sucesso técnico. São evidências
separadas, sem acrescentar patches a estas duas raízes.

Testes naturais continuam com Pedro. Sessões já abertas mantêm seu snapshot;
uma nova sessão carrega os candidatos instalados. O processo aberto não foi
tocado para forçar uma aprovação.
