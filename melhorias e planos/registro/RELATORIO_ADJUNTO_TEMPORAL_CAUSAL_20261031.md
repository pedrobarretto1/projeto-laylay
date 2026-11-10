# Segmentação causal — adjunto e matriz da mesma pergunta

Base1197daf0d6b5e69b7243f571542bf17666274ea2,
codex/correcao-autoria-conversa-20261030.Worktree anterior preservada.
Manifesto539fontes/status em resultados_testes/segmentacao_causal_20261031.

## Primeira divergência e contraprovas

Pendência histórica de test_finalidade_contexto_historico:
Quando disse "Registrei o resultado do pedido.", por que aconteceu?
Leitor compartilhado identifica finalidade "fala" na consulta integral.
Segmentador corta na vírgula com origem PERGUNTA_INDEPENDENTE e publica dois
segmentos.A atribuição temporal e a pergunta matriz perdem o vínculo;nenhum
recorte isolado conserva finalidade histórica.O binder usa corretamente cada
fonte por ato e não reconstrói a relação perdida;não deve ser compensado ali.

Disponibilidade de fonte foi falsificada como causa:registro semântico contém
a fala e o mesmo leitor reconhece o texto integral.Recuperação por recência ou
remoção da revisão não são soluções.A segmentação antecede transporte e geração;
RED é reproduzido sem chamar modelo.Fonte integral preservada e falso motivo
recusado após o candidato falsificam necessidade de relaxar a revisão.

Controle interno:com sujeito explícito "você",a regra de condição pessoal já
conservava parte desses enunciados;elipse e outras formas não recebiam a mesma
dependência.Não ampliar condições operacionais para corrigir adjunto temporal.

## Contrato e escopo

Único owner de produção alterado:modalidade_turno.py,fronteira de vírgula.
Adjunto temporal inicial e sua matriz interrogativa não são atos independentes.
Leitura usa pergunta canônica e texto fora de citações;vírgula citada não é
fronteira;prefixo já pontuado ou coordenação independente não recebe a proteção.
Frase de exemplo não aparece em produção;não há regra por domínio ou turno.

Dependência textual não qualifica agente,passado,fonte,fato,ficção ou permissão.
Essas decisões continuam em seus owners.Citações/ficção/futuro não ganham
obrigação histórica;fronteira forte separa perguntas e comandos seguintes.
Não se funde a consulta inteira nem se resegmenta o binder.A fonte canônica
continua literal,com intervalo integral para o ato,sem inventar suporte.

Delta comparado ao baseline sujo em candidato.diff;demais538fontes preservadas,
inclusive as correções anteriores de projeção e fonte de revisão.

## RED, controles e composição

RED histórico confirmado com --runxfail:1falha/34controles.RED novo10falhas/
11controles após corrigir a preparação da fonte que exigia resultados=().
Variações de atribuição,matriz,aspas e pontuação;ações em arquivos/IoT/música;
ficção/futuro;pergunta e ordem independentes;binding com duas falas observadas.
GREEN inicial56,foco111aprovados/um skip opcional de modelo real.
Caso histórico e ID preservados;removida só a marca xfail realmente resolvida.

Factory real da ponte/root,perfil privado e HTTP fixo.Primeira entrada prepara
uma fala publicada nativamente:"Podemos conversar sobre o projeto.".Segunda
consulta usa a atribuição temporal dessa fala;não é conversa nova com Qwen.
Baseline do único owner carregado da fonte congelada no subprocesso:dois
segmentos,zero fontes históricas vinculadas,aviso sobre verificação de fontes.
Candidato:um segmento,fonte publicada exata,conclusão limitada sem degradação,
uma chamada para a consulta e uma publicação nativa correspondente.

Prova da publicação anterior serve apenas para demonstrar o que Laylay disse,
nunca efeito ou causa.A fonte não possui resultado operacional;a conclusão
explicita esse limite.Draft que inventa queda do servidor é recusado no
contrato de saída e não chega às publicações.Falha de geração é preservada na
resposta degradada,sem encerrar a ponte.Não esconder esse controle como sucesso
do modelo.Provas:runtime_baseline.json,runtime_candidato.json e perfis/composicao.

Sonda preliminar só com histórico importado retornou falha de contrato de saída
e contingência histórica;não prova que o caminho normal estava corrigido.
Substituída pela comparação controlada com publicação nativa e payload válido
para a conclusão catalogada;owner de revisão/orçamento não foi modificado.

## Regressão e instalação

Vizinhos adicionais fora da seleção ampla:310aprovados e duas falhas de negação
musical em escopo_ato_unico.As mesmas duas falhas e310aprovados se reproduzem
com o owner anterior;IDs e contraprovas em vizinhos_baseline.xml/log e
falhas_vizinhas_anteriores.json.Não são encerradas,nem entram no patch causal.

Instalação original ae7b8775/main por delta apply_patch,hash antes da escrita,
backup do owner/teste anterior,dois novos módulos de teste.No venv original:
291aprovados,um skip opcional,zero falhas/erros em16,63segundos,nove módulos.
Só modalidade_turno mudou em539fontes;demais538,intactos.Três fontes neurais
com EOL distinto preservadas.Sem reiniciar ou encerrar sessão pessoal.

Regressão ampla134módulos:4.019aprovados,25skips,um deselected,três subtests,
zero falhas/erros/xfails em431,81segundos.Mesmo filtro anterior de composição
do perfil explicativo,sem exclusão nova.Auditoria XML confirma44IDs anteriores
aprovados e os quatro históricos causais ativos/aprovados,inclusive a antiga
pendência.Oito casos de revisão de espaços da etapa anterior permanecem verdes.
539fontes estáveis durante a execução.Provas ampla.xml/log e resumo_final.json.
Esta seleção principal verde não apaga as duas falhas vizinhas preexistentes
documentadas acima nem declara a suíte global aprovada.

## Limites

Sem inferência Qwen nova,voz,ações reais,commit,push ou desligamento.Testes
naturais ficam com Pedro;abrir nova sessão para carregar a instalação atual.
Não prova entendimento semântico universal,nem encerra as duas negações
musicais anteriores,qualidade livre ou coerência geral da conversa.
