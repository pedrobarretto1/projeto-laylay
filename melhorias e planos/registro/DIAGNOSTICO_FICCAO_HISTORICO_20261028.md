# Perguntas imaginativas recebendo limite histórico — diagnóstico de 28/10

**Status histórico deste diagnóstico: RED anterior ao candidato.**

Atualização posterior: a admissão por finalidade foi corrigida e validada no
recorte histórico. Ver `RELATORIO_FINALIDADE_HISTORICA_20261028.md`, incluindo
os limites de qualidade e o RED vizinho preservado. O texto abaixo mantém a
evidência anterior ao patch.

Origem autorizada: `C:/Users/pbarr/Documents/Codex/2026-10-28/ch/work/ponte_sessoes`.
Arquivos originais somente lidos. O relato do outro chat foi tratado como
hipótese, não como prova da causa. A triagem literal confirma o encontro
principal de 20 entradas/16 respostas/quatro erros em cinco sessões, separando
mensagens preliminares e sessões sem conversa. Cinco respostas do encontro
contêm os avisos de evidência citados. Artefatos e hashes em
`resultados_testes/ficcao_historico_20261028/triagem.json`.

Os 530 arquivos de código comuns à última captura são idênticos à base da
investigação de adequação. Os eventos brutos também mostram bloqueios de
orçamento e uma saída estruturada inválida; são famílias separadas. O aviso de
fonte pode ser uma resposta publicada, não necessariamente um dos quatro erros
técnicos que encerraram a ponte. Não usar a contagem de erros para medir toda
a qualidade da conversa.

## Primeira fronteira reproduzida

Três textos originais — carta imaginada, mascote fictício e nome na aventura —
foram passados ao classificador/plano/contrato reais com uma fala de história
publicada pelo registro canônico. Todos receberam a chave
`explicacoes_historicas_por_ato` com valor `None`.

```text
contexto narrativo anterior disponível
→ consulta_historica_multipla admite pelo booleano fonte_identificada
→ vínculo por ato exige atos de pergunta/deliberação
→ os trechos legítimos de conversa tornam o vínculo inválido
→ contrato guarda None como falha de vínculo histórico
→ owner histórico publica limite de evidência, apesar de o pedido ser imaginativo
```

Owners a investigar: elegibilidade em `explicacao_fala_historica.py`, distinção
entre contexto e obrigação em `contrato_fala.py` e seleção da finalidade da
pergunta. A conferência histórica não deve ser simplesmente removida: o mesmo
diagnóstico mantém um controle com duas consultas a ações passadas reais, em
que uma causa inventada é substituída por limite observado, sem confirmar efeito.

`test_diagnostico.py`: **três falhas e um controle aprovado**, com código real e
sem LLM/voz/efeitos. A primeira versão do controle supunha que `aceita` deveria
ser falso; ao inspecionar o retorno, confirmou-se que o finalizador publicava
um limite ajustado e não a afirmação falsa. A expectativa foi corrigida para
esse contrato observável. Preflight preservado, sem contá-lo como outra falha.

Ainda falta delimitar a regra de admissão por finalidade para não prejudicar
referências históricas implícitas legítimas, criar REDs vizinhos e validar
primário/reparo/Qwen na composição real após eventual candidato. Não declarar
esta raiz corrigida nem usar um filtro da expressão “história fictícia”.
Proteções operacionais, autorização, receipts e efeitos devem permanecer intactos.
