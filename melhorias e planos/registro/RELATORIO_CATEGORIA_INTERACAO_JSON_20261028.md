# Categoria de interação aberta prolonga a geração até o teto

Base: HEAD c91cae1bd407b02db946ae7bc752d1ed3269bfd9,main,535 fontes de
produção congeladas antes do candidato. Worktree anterior preservada;sem
commit. Artefatos:`resultados_testes/json_estruturado_qwen_20261028`.
Continuação da falha de entrega registrada em
`RELATORIO_FRONTEIRAS_REALIDADE_DIARIO_20261028.md`;não reabre a causa do diário.

## Cadeia demonstrada e primeira divergência

Na coleta histórica `composicao_escopo_final`,os HTTPs0,5 e9 entregaram
`finish_reason=length` com1.024 tokens. O início contém proposições completas,
mas os três documentos ficam abertos na string de `tipo_interacao`.
O restante parecido com campos JSON,aspas simples e símbolos está dentro
dessa mesma string,não é um objeto parcialmente aprovado. O schema admitia
qualquer string nessa categoria,apesar de o consumidor reconhecer somente
acao,conversa,aprendizado econfirmacao. Essa é a primeira divergência
demonstrada:domínio admitido na geração não corresponde ao domínio consumido.

Os HTTPs0 e9 consumiram24,119 e21,876 segundos,além do preparo do turno.
As recuperações correspondentes receberam3 e7 segundos e deram ReadTimeout.
A chamada intermediária5 também truncou;seu reparo respondeu em5,27 segundos,
mas a resposta não passou pela revisão de conteúdo. Não confundir geração
estruturalmente válida com resposta útil aprovada.

O corte é a consequência do teto de geração. A revisão recusou corretamente
o documento incompleto;ela não foi a autora das aspas ou da repetição.
Recuperar o trecho da fala de dentro do JSON incompleto violaria o contrato.

## Hipóteses concorrentes e contrafactuais

- Backend ignorando qualquer schema:falsificado pelo canário de enum finito.
  Ollama local respeitou o enum mesmo com pergunta exigindo prosa contrária,
  tanto em `/v1/chat/completions` quanto em `/api/chat`. Não trocamos endpoint.
- Erro anterior às proposições ou inserido pelo decoder:falsificado pela
  resposta HTTP bruta. Os três inícios válidos terminam na mesma categoria
  aberta;nenhum codec acrescentou o conteúdo que ocupa essa string.
- Necessidade de trocar modelo ou aumentar limites:não sustentada pelos
  contrafactuais. Nos pedidos históricos0 e9,mudar somente o schema de
  `tipo_interacao` produziu80–86 tokens,encerramento stop e JSON completo,
  em3,21 e5,15 segundos. Textos,prompt,modelo,temperatura e teto preservados.

Esses contrafactuais não são reexecução determinística do sorteio original:
os pedidos históricos não fixavam seed. A prova independente do defeito
contratual é que o schema e o codec aceitavam valores que o consumidor não
conseguia representar. Não declarar que todo timeout tem essa causa.

O log do backend também avisa sobre um pattern narrativo parcialmente
suportado. Isso não explica o erro da abertura sem pattern,e o codec conserva
a conferência da moldura. Não foi alterado neste patch.

## Contrato e responsáveis

Categoria de controle é um valor de domínio finito;autoria livre continua
nas proposições. Não remover campos de emoção,leitura,aprendizado ou comando.
A categoria proposta não concede autoridade,não comprova fato nem efeito.

- `contratos_turno.TIPOS_INTERACAO_IA`:domínio único já consumido pelo sistema.
- `suporte_autoria`:mesmo enum no schema principal/livre/referenciado e nas
  rotas autorais de recuperação;codec recusa valor fora do domínio.
- `saida_interpretacao_principal`:mesmo domínio na interpretação tipada,
  mantendo os validators de atos,fontes,comandos e emoção.
- `processamento_resposta_ia`:leitor reutiliza o domínio canônico,sem criar
  categorias novas nem aproveitar uma categoria como permissão.

Produção alterada:esses quatro arquivos. Nenhum limite,timeout,quantização,
modelo,persona,revisão,executor ou regra de receipt foi relaxado. A recuperação
continua subordinada ao orçamento e às mesmas revisões. Não há fechamento
artificial de aspas nem aproveitamento de trecho de documento inválido.

## RED,controles e composição

O novo módulo `test_categoria_interacao_autoral.py` reproduziu16 REDs e sete
controles verdes antes de produção. O JSON completo com categoria inválida
era aceito,e os dois schemas não representavam o domínio do leitor.
O candidato protege tipos inválidos,cauda histórica,lista/objeto/booleano,
ausência opcional,as quatro categorias,rotas de reparo e JSON truncado.
Foco com vizinhos:182 aprovados,quatro opcionais ignorados.

Na composição instalada,com perfil isolado,Qwen real e roteiro histórico de
oito turnos:9 HTTPs200,todos encerrados em stop,45–170 tokens por emissão.
Nenhum JSON truncado,timeout ou bloqueio de orçamento. A primeira proposta
repetia conteúdo entre proposições e foi recusada pelo codec existente;
um reparo real respondeu. As oito respostas foram publicadas. Isso comprova
preservação da rejeição de conteúdo estruturalmente inadequado;fluidez ou
verdade de toda fala não se deduzem do sucesso do protocolo.

Replay separado:uma principal truncada histórica foi injetada uma única vez,
com proveniência e SHA. O reparo é Qwen real e retornou JSON completo em3,07
segundos,passando pelo caminho de revisão instalado. A latência antiga de24
segundos NÃO foi reproduzida;esse replay prova a rota de recuperação,não que
um reparo sempre cabe em três segundos restantes. A fala ainda propõe uma
história que teria acontecido com ela:limite factual/pessoal conservado como
outra fronteira,não certificado por este resultado de formato.

Sem voz e com executores simulados. A coleta preserva guardas de rede,
persistência isolada e SHA das fontes;importações e composição são do código
instalado. Não é main com todos os efeitos externos habilitados.

O controle Qwen `seguranca_categoria` conserva um RED independente:para abrir
a Calculadora,o modelo não propôs comando e o executor simulado não foi
alcançado. O assert de receipt da sonda falhou e não foi relaxado. A pergunta
posterior também recebeu uma atribuição corporal inadequada. Não afirmar
sucesso operacional ou segurança integral a partir dessa coleta. Os controles
de categoria e autorização na composição sintética verificam separadamente
que APP_OPEN/MEDIA_CONTROL propostos sob ficção não ganham permissão.

## Limites e próxima fronteira

A causa contratual demonstrada não admite mais prosa dentro dessa categoria.
Isso não garante JSON completo para qualquer resposta:proposições longas,
outros campos livres,demora do backend e indisponibilidade continuam sujeitos
a teto e prazo. Não marcar todas as falhas técnicas ou compreensão global
como encerradas. O aviso factual/pessoal que surgir tem sua própria primeira
fronteira;nenhuma revisão foi removida para obter entrega.

## Verificação final e alcance

25 novos testes aprovados,incluindo os dois controles de autorização na
composição. Eles foram adicionados após a coleta da suíte ampla e executados
no XML `categoria_composicao`;o foco anterior contém182 aprovados/quatro
ignorados. Não somar essas execuções como se fossem testes distintos.

Regressão146 módulos:3.809 aprovados,cinco falhas,zero erros,14 ignorados,
um desmarcado,um xfail e30 subtestes aprovados. A comparação por ID com a
base confirmou as mesmas cinco falhas anteriores:uma de indisponibilidade
musical documentada e quatro de projeção de explicação fora do turno.
Nenhuma falha nova,nenhum teste anterior eliminado ou expectativa relaxada.

Auditoria535 fontes passou:quatro arquivos existentes alterados,nova fonte
de produção nenhuma,HEAD preservado. `candidato.diff` usa a base congelada
desta etapa,sem atribuir a ela os patches anteriores. `auditoria.json`
confere os três truncamentos no mesmo campo,contrafactuais de uma alteração,
schemas da coleta,JSON completo,replay com origem e limites,sem voz/efeito.
`git diff --check` passou nos arquivos de produção/teste desta correção.

Encerrado o defeito contratual desse campo e comprovada entrega sem esses
truncamentos/timeouts no roteiro instalado. Permanecem explicitamente abertos
o controle operacional que não alcançou receipt e as falas pessoais/factuais
inadequadas observadas. Formato válido e protocolo concluído não as legitimam.
