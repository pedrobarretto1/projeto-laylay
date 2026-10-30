# As 30 falhas e os 44 erros — correções por causa — 28/10/2026

Escopo: os **mesmos 74 IDs** da regressão anterior, sem excluir, renomear ou
marcar esses casos como ignorados. Não são 74 defeitos independentes. O trabalho
foi organizado pelas quatro causas abaixo, preservando C5/F1/C7/AUT e os
artefatos anteriores. Não se declara a conversa inteira resolvida.

Continuação posterior da negativa de capacidade observada na coleta:
`RELATORIO_CAPACIDADE_CONVERSA_20261028.md`. Os 74 IDs deste relatório continuam
aprovados; os números e limites abaixo permanecem como evidência desta etapa.

Base congelada: HEAD `c91cae1bd407b02db946ae7bc752d1ed3269bfd9`, `main`,
worktree suja preservada, 532 fontes, estado Git e 74 IDs em
`resultados_testes/regressao_74_20261028/baseline.json`.
Reprodução antes das alterações: **30 falhas, 44 erros, 135 aprovações**.

## Causas e contratos

| Grupo | Primeira fronteira demonstrada | Correção e owner | Critério |
| --- | --- | --- | --- |
| 44 erros em `test_composicao_turno` | Fixture tenta exportar tipos nativos, incluindo `PerspectivaEnunciador`, como JSON sem projeção | Somente fixture: `default=asdict` para projeção de diagnóstico, sem converter o runtime em dicionários nem usar `str` para ocultar tipos desconhecidos | Todos os mesmos IDs executam asserções, sem erro de setup |
| Oito falhas em `test_geracao_limite_sem_estado` | Expectativa anterior à autoria obrigatória exigia mensagens sem contrato e exatamente 256 tokens | Somente teste: conserva a entrada literal e modo aberto/fechado, exige suporte negociado e respeita a reserva real. Modelo simulado devolve saída que passa pelo codec | Não remover suporte nem reduzir orçamento para satisfazer expectativa antiga |
| 21 falhas em `test_autoria_historica_integral` | Leitor só reconhece finalidade histórica causal; perde consulta a resultados de fala passada apesar de registro/receipts válidos | `referencias_linguagem.py`: moldura temporal atribuída à própria fala, com pergunta principal retrospectiva | Reutilizar fonte real; não inventar causa ou efeito; futuro, outro agente e conteúdo apenas citado não escolhem essa fonte |
| Uma falha de pedido modal para Calculadora | Rota de app recebe entrada bruta; outras rotas veem núcleo modal recuperado. Extrator de app perde o verbo antes do lookup, deixando busca musical vencer | `roteador_deterministico.py`: extrator reutiliza `extrair_nucleo_pedido_operacional` antes do lookup | Mesmo aplicativo nas formas modais; sem lista privada de erros, sem trocar prioridades ou inferir permissão nova |

### Fixture de composição: sete controles antes ocultos

Depois da projeção JSON correta, sete asserções dentro dos 44 casos passaram
a executar e falharam. Os controles entregavam `params={}` onde o owner atual
exigia identidade exata de operação/alvo. A mensagem era “proposta sem vínculo
ao ato autorizado”, não uma falha de serialização restante.

O teste agora materializa a proposta de controle a partir do escopo publicado
pelo próprio callback instalado, conservando o intent esperado. Não inventa
alias IoT, alvo retificado ou autorização. A resolução é lazy: lista vazia
termina antes desse diagnóstico; o candidato incompleto apenas provoca a
conferência e continua recusado. O controle positivo usa a proposta exata
devolvida pelo owner real.

Mantiveram-se as provas de rejeição de retrato estrangeiro, principal antiga
após troca de turno e operação divergente. Acrescentou-se conferência de que
o candidato com parâmetros vazios continua recusado quando o vínculo exige
os parâmetros publicados. Nenhum executor foi afrouxado. São sete casos
dentro da lista original, não sete novas raízes somadas artificialmente.

### Consulta histórica: evidência e falsificações

“Quando você disse ‘Registrei o resultado do pedido.’, o que estava confirmado
em cada ação?” tinha fala observada e receipts de oito etapas. A modalidade
não operacional permitia consulta; o primeiro RED relevante era a finalidade
vazia no leitor e, depois, ausência de contrato histórico. A falta de dados
ou incapacidade de transportar realizações longas não explicava esse caso:
perguntas causais com as mesmas fontes e o codec existente serviram de controles.

O novo recorte reconhece a pergunta de resultados passados, sem exigir “por
quê”. Não considera a citação prova de execução. Conserva os próprios receipts,
limites de estado atual, fonte estrangeira/expirada e ausência de causa.

Testes novos: **15 REDs/cinco controles** inicialmente. A primeira ampliação
também alcançava perguntas futuras após uma fala citada; dois REDs adicionais
demonstraram essa abertura. A regra final exige retrospectiva na pergunta
principal, não apenas na oração de atribuição. **22 casos finais aprovados**.
Não se redesenhou a segmentação: o xfail anterior da atribuição elíptica e
pergunta causal em segmentos separados continua fora destes 74.

### Pedido modal: evidência e falsificações

O núcleo canônico recuperava `abrir a calculadora para mim`, e o lookup do
mesmo app funcionava com esse núcleo e com “pode abrir”. Logo, não era ausência
da Calculadora no catálogo nem prioridade musical. O extrator recebia o bruto
e não reutilizava a leitura já existente. A correção reaproveita o mesmo owner
lexical; não adiciona `if` para “abri” ou para o nome da Calculadora.
O módulo de pedidos modais passou com **107 aprovações**, incluindo controles
de discussão/permissão e formas vizinhas.

## Escopo de arquivos

Produção alterada nesta tarefa:

- `mente_laylay/cognicao/referencias_linguagem.py`;
- `mente_laylay/autonomia/roteador_deterministico.py`.

Testes atualizados: `test_composicao_turno.py`,
`test_geracao_limite_sem_estado.py`. Novo:
`test_consulta_resultado_retrospectivo.py`.

Contrato de autoria, reservas, executores, receipts, configuração, modelo,
voz e composition root preservados. Os diffs exclusivos são comparados com
as cópias congeladas, sem atribuir trabalho anterior da worktree a estas causas.
Nenhum commit criado.

## Validação instalada e limites

Foco final: **231 aprovados**, sem falhas, erros ou skips. Auditoria compara
os IDs e exige aprovação de cada um dos 74 originais.

Regressão final em **134 módulos**: **3.514 aprovados, zero falhas e zero
erros**; 14 ignorados, um desmarcado, um xfail e 30 subtestes aprovados.
Os 74 originais estão presentes e aprovados, sem marcação de skip/xfail.
A seleção anterior foi mantida e ampliada com o módulo novo e a negociação
histórica; não se reduziu a seleção para produzir o resultado verde.
O xfail e a exclusão anteriores não pertencem aos 74 e permanecem explícitos.

Uma primeira ampla sem a restrição adicional de futuro passou com 3.512 casos.
Os dois controles novos falharam no candidato e justificaram a restrição;
depois disso foram repetidos foco, composição e ampla na versão final.

Composição instalada com Qwen real, serviços da raiz, perfil isolado, sem voz
e com executores simulados. Duas coletas preservadas, sem repetir para apagar
falhas livres. Na coleta final:

- “pode abri a calculadora para mim” e “preciso que você abra a calculadora”
  chegam a `APP_OPEN`, não `MUSIC_SEARCH`; só esses dois pedidos geram tentativa.
- Receipts simulados: `executou=False`, `confirmado=False`, `ok=False`;
  publicação comunica a não execução. Nenhum efeito real.
- Consulta temporal do primeiro resultado publica a realização limitada do
  registro: execução não concluída, efeito não confirmado, causa não informada
  e sem prova do estado atual. Fonte histórica válida no juiz instalado.
- Depois de duas falas idênticas, a pergunta pede qual ocorrência, em vez de
  escolher arbitrariamente uma fonte. Ausência de episódio do navegador
  também conserva o limite e não dispara ação.
- A pergunta imaginativa não recebe contrato histórico.

**A conversa livre não ficou globalmente verde.** Na primeira coleta, o relato
do usuário terminou em limite de tentativas. Na final, esse relato recebeu
negação indevida de capacidade (“não posso abrir aplicativos”), e a criação
imaginativa terminou em limite de tentativas. Os textos brutos, planos e
respostas estão preservados; essas ocorrências não foram contadas como testes
aprovados nem atribuídas a uma causa já comprovada. A recusa simulada não prova
incapacidade de abrir apps. Essa distinção continua uma fronteira a estudar.

Artefatos e auditoria reproduzível:
`resultados_testes/regressao_74_20261028/auditar.py` e `auditoria.json`.
Os resultados antigos de 30/44 continuam válidos como registros históricos;
o novo fechamento corresponde aos mesmos IDs, não a uma redução da seleção.
A auditoria final passou: 74/74 IDs aprovados, 532 fontes conferidas, somente
os dois owners declarados modificados, snapshot instalado estável, HEAD
preservado, receipts negativos e ausência de voz/efeitos reais conferidos.
`git diff --check` passou nos arquivos alterados. Plano e mapa causal atualizados.
