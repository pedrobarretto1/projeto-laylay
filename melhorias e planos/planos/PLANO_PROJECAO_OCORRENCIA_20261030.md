# Rodada 18 — correlação textual e publicação

Base: 1197daf0d6b5e69b7243f571542bf17666274ea2, branch
codex/correcao-autoria-conversa-20261030, worktree com candidatos anteriores
preservados. Manifesto congelado em resultados_testes/sem_publicacao_18_20261030/baseline.json.

Ocorrência: casa-20261030-18, sessão 20261030T195853Z-0d4ab6c2.
O modelo respondeu; o validador recusou a ocorrência antes da publicação.
Entrada de 510 caracteres, projeção de 500 terminando em espaço. Normalizar
novamente essa projeção produz 499 caracteres, enquanto o plano completo
produz 500. Snapshot histórico contém a mesma regra. Relacionar esta raiz
à fronteira já registrada como xfail em test_coerencia_revisao_bloqueada;
não atribuir os demais problemas de conversa a ela.

Contraprova posterior: esse xfail continua RED após corrigir a projeção; sua
revisão compacta a fonte além do recorte. Mecanismo separado, preservado.
Não remover o xfail nem ampliar o candidato para encerrá-lo nesta etapa.

Contrato e owner: decisao_turno.py compara a mesma projeção idempotente nos
contratos de coerência e vínculo. Identidade, tipos, revisão operacional e
autorização permanecem decisões distintas. Recorte não prova sufixo, parâmetro
ou efeito. Revisor e publicador não devem compensar identidade falsa.

Validação: RED de recorte com whitespace; controles 499/500/501/650, divergência
interna/ID/operação, quatro domínios sem autorização; writer transacional;
replay do retorno histórico e autoria alternativa na factory real, com 34
mensagens históricas fixadas. Voz desligada, efeitos bloqueados/simulados,
HTTP fixo, perfil privado. Provar orçamento não esgotado e publicação nativa.
Executar regressivos relevantes e instalar somente delta com hashes/backup.
Testes naturais continuam com Pedro. Sem commit, push ou desligamento nesta etapa.
