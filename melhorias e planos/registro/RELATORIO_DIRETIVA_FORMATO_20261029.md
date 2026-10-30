# Diretiva de formato — continuação do contrato de ato textual

Caso `respeito-003` do journal `20261029T152347Z-769cbc1c`, identificado no
diagnóstico da rodada do dilema da memória. O pedido para responder em poucas
frases deixava de ser tratado como forma da fala e ganhava autoridade para uma
ação externa. O candidato corrige essa fronteira no contrato compartilhado.
Não trata do infinitivo `apagá-lo faria...`, que tem outra cadeia causal.

## Base e primeira divergência

HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, branch `main`, worktree suja
preservada. As 536 fontes e o estado Git foram congelados em
`resultados_testes/diretiva_formato_20261029/baseline.json` e `base/`.
A evidência histórica desse turno e os hashes do journal estão em
`evidencia_historica.json`. Nenhum commit criado.

```text
pergunta atual + diretiva de forma da resposta
→ leitor de transformações cobre resumo/comparação/redação, mas não formato
→ o imperativo responder entra no caminho operacional geral
→ diretiva recebe comando/pedido_direto e autoriza_execucao=True
→ plano exige efeito/receipt que nunca foi solicitado
→ resposta vira aviso de ação não executada
```

O primeiro RED é a classificação/autoridade, antes de geração e executor.
O contrato correto distingue **forma da resposta no canal atual** de **resposta
em recurso externo** e de uma **ordem independente**. O verbo isolado não
autoriza um efeito. A resposta do modelo também não fornece o receipt faltante.

Falsificações: o caso falha sem chamar a LLM, tanto com o normalizador instalado
quanto sem ele; logo não depende de uma invenção do Qwen nem da normalização
que explica `memoria-005`. Trocar o detector operacional por um que sempre
indica comando não deve superar a proteção discursiva. A escrita em e-mail,
arquivo ou WhatsApp permanece operacional, demonstrando por que remover
`responder` do léxico seria uma correção errada.

## Contrato compartilhado e responsáveis

| Responsabilidade | Owner | Alteração |
| --- | --- | --- |
| Reconhecer a diretiva integral | `normalizacao_linguagem.tipo_transformacao_conversacional` | Nova classe `formato_resposta`, usando o leitor já compartilhado por modalidade e segmentação. |
| Manter fonte e autoridade de cada ato | `modalidade_turno._segmentar_turno_misto` | Coordenação simétrica: ordem seguida de transformação é separada, como já ocorria na direção inversa. |
| Interpretar, autorizar e executar ação externa | Owners existentes | Preservados; recurso externo ou outra ordem não recebe a proteção do formato. |
| Conferir autoria, fatos e efeitos | Revisores e guardião existentes | Preservados; a diretiva não certifica conteúdo, fonte, receipt ou conclusão de ação. |

O leitor usa classes delimitadas de modificadores — quantidade/unidade,
adjetivos de forma, advérbios e exclusões de estilo — e canal atual explícito.
Modificadores e canal podem ser combinados em ordens diferentes. A conferência
é integral: não ignora o restante para absorver e-mail, arquivo ou outra ação.
O padrão exige pelo menos um modificador; não classifica `responda` sozinho ou
qualquer texto que apenas contenha essas palavras como diretiva de formato.

A correção reutiliza a segmentação e o leitor existentes; não cria um parser
privado no executor, outra fonte de autoridade ou uma chamada nova ao modelo.
O texto original continua vinculado aos intervalos dos segmentos. Assim o
contrato beneficia qualquer tema tratado na conversa, sem depender de música,
memória, aplicativos ou da frase histórica específica.

Produção alterada nesta base: **dois arquivos**, `normalizacao_linguagem.py` e
`modalidade_turno.py`. Nenhuma fonte nova de produção. Revisão de suporte,
guardião, composição, executores, modelo, orçamento, memória pessoal e voz
não foram alterados.

## REDs, revisão e controles

O RED inicial teve 52 falhas causais e sete controles aprovados, cobrindo a
entrada histórica, variantes de forma, normalização e detector adversarial.
O primeiro candidato passou nas diretivas isoladas, mas o controle inverso
`Abra ... e responda brevemente` expôs uma assimetria de coordenação. O mesmo
acontecia com resumo da conversa, falsificando uma regra exclusiva do verbo
responder. Dois REDs de coordenação foram preservados antes da alteração mínima.

A revisão independente encontrou duas limitações do mesmo modelo de formato:
primeiro, combinar modificadores; depois, posicionar o canal atual entre eles.
Os REDs correspondentes estão em `red_modificadores.xml` e
`red_canal_intermediario.xml`. O leitor passou a compor as classes, em vez de
acrescentar exceções para cada frase. Os testes também cobrem as seis permutações
de quantidade/estilo/canal por três separadores, sempre acompanhadas de destino
externo e ordem independente como controles negativos.

A revisão posterior confirmou as reproduções anteriores e 33 verificações
puras sem falha, sem identificar outra abertura importante no diff. Sua prova
não substitui composição ou regressão. A limitação anterior de segmentação de
`salve o arquivo`, cujo domínio ainda reconhece a ordem externa sem separar
todos os trechos, não foi atribuída a esta mudança nem corrigida por um novo
léxico local. `apagá-lo faria` também permanece separado e pendente.

Foco revisado: **121 aprovados**, sendo 113 casos locais e oito da composição
instalada com HTTP controlado. O conjunto vizinho inicial de transformação,
redação e finalidade teve 153 aprovações antes da expansão dos modificadores.
Oito composições finais incluem seis respostas diretas em uma chamada e dois
casos com proposta de comando/receipt inventado pela IA, recusados antes da
publicação de uma resposta segura. APP_OPEN e MEDIA_CONTROL não recebem
execução ou prova de efeito por estarem no JSON do modelo.

## Comparação na composição instalada

`comparar_composicao.py` carrega somente os dois owners congelados da base em
memória, sem restaurar arquivos da worktree. Mantém os demais componentes e
as mesmas propostas HTTP controladas:

| Medida | Base | Candidato |
| --- | --- | --- |
| Autoridade operacional do turno histórico | `True` | `False` |
| Chamadas HTTP controladas | 2 | 1 |
| Publicação | aviso de ação não executada | resposta proposta sobre o assunto atual |
| Comandos ou efeitos executados / voz | nenhum | nenhum |

A primeira execução dessa comparação fornecia apenas uma resposta HTTP fixa;
na base, a interpretação adicional deixava a simulação sem resposta para a
segunda chamada. Esse resultado incompleto foi preservado em
`composicao_primeira_tentativa.json`, não usado como prova de publicação.
A comparação final fornece duas propostas idênticas e confirma o mesmo aviso
observado historicamente. O candidato precisa apenas da primeira proposta.

A frase controlada publicada não foi certificada como fato universal. Essa
prova mostra a passagem pelo contrato sem exigência de efeito, não a qualidade
de uma nova geração real de Qwen. Os testes de conversa permanecem com Pedro.

## Regressão, auditoria e limites

A seleção ampla conserva os 163 módulos anteriores e seus filtros, acrescentando
os dois novos módulos. Resultados finais e comparação de IDs ficam em
`regressao_revisada_resumo.json` e `regressao_revisada.xml`; auditoria e diff
exclusivo em `auditoria.json` e `diff_producao.patch`.

Resultado final: **4.271 aprovados em 165 módulos**, zero falhas/erros, 14
ignorados, um desmarcado, um xfail anterior e 30 subtestes. Nenhum ID anterior
foi retirado. Auditoria de 536 fontes aprovada, confirmando somente as duas
alterações declaradas, sem nova fonte de produção ou mudança de orçamento.

Duas execuções amplas intermediárias foram interrompidas nos processos desta
própria tarefa antes de alterar produção após os findings da revisão. Seus
logs e PIDs ficaram preservados; não são apresentadas como GREEN. Só a execução
revisada, sobre o candidato final, pode sustentar a conclusão de regressão.

Essa seleção é a regressão relevante dos contratos de conversa, não a suíte
inteira de todos os domínios. Não foi executado caos de conversa, novo modelo,
voz, hardware ou efeito real. A fronteira de simulação pedida por Pedro foi
mantida. O guardião de fatos, fontes, hipóteses, autorização e receipts continua
vigente; não se ampliou o orçamento nem se afrouxou uma validação para publicar.

O alcance da correção é a natureza/autoridade da diretiva de formato no recorte
gramatical conferido e sua composição com ordens reconhecidas. Não prova que
todo texto livre obedecerá a qualquer limite estilístico, que todos os sinônimos
foram compreendidos ou que a conversa geral foi concluída.

Próxima fronteira preservada: `memoria-005`, em que a normalização perde a
morfologia de infinitivo com clítico e autoriza uma hipótese. Consulta histórica,
recomendação discutida, complemento de concordância e recuperação após recusa
correta de repetição seguem em suas próprias famílias e IDs.
