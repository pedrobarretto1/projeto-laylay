# Prévia isolada do refinamento

Pedido de Pedro em 20/10/2026: produzir a prévia das nove abas com base no estudo, sem alterar a interface oficial. Posteriormente autorizou commit, push e desligamento ao concluir.

## Separação dos artefatos

- Interface oficial: `cliente/terminal_2/web_v1/`.
- Prévia de refinamento: `artifacts/interface_v1/previa_refinada/` (cópia versionada independente).
- Estudo: `artifacts/interface_v1/estudo_refinamento/ESTUDO_REFINAMENTO.md`.
- A prévia pode ser aberta por `index.html`, sem a Laylay, ou servida localmente. Sua indicação de demonstração permanece visível.

Dados, estados, mensagens, música, dispositivos e resultados da prévia são exemplos locais. Nenhuma ação chega ao transporte da Laylay, Ollama, microfone, player externo, dispositivos IoT ou captura de janelas. Alterações no formulário da prévia não mudam as configurações oficiais.

## Preservação da V1

SHA256 antes da construção da prévia:

- `index.html`: `3c05aaa260340fa432c9ba686cdcb499ec02b19f3b9daafdd630a105a842ba44`.
- `interface.js`: `1eed9234ee69fcd93537a55d19dc783ec59ac50dfe048968aa0978adb6fa136e`.
- `paginas.js`: `ec31d38a00517ce371e46917c27a010081318e12affc329d581073b0274c870a`.

As alterações da V1 e seus testes já estavam na worktree antes desta prévia. Pedro ampliou explicitamente o escopo: 'pode fazer o push e commit de todos mesmo'. O commit autorizado reúne toda a worktree versionável, incluindo as alterações paralelas de mente, firmware, corpo, registros e respectivos testes. A inclusão dessas mudanças não significa que foram implementadas ou causalmente validadas pelo trabalho da prévia; seus resultados de teste precisam ser registrados separadamente. Credenciais e arquivos privados ignorados pelo Git não são adicionados à força.

## Verificação

A base oficial passou novamente pelos oito módulos de teste novos da interface: **54 passed em 37,93 s**. Essa rodada valida a V1 existente; não transforma as interações de demonstração em funcionalidades reais.

Rodada ampliada dos **53 módulos de testes novos ou alterados** da worktree: **1494 passed, 34 skipped, 10 failed em 487,10 s**. Não foi executada a suíte completa do repositório nesta rodada. As dez falhas pertencem às alterações paralelas de corpo/cognição e permanecem registradas, sem enfraquecer expectativas ou misturar suas correções à prévia:

- `scripts/tests/test_medidas_resultado_imediato.py`: nove casos; primeira perda observada entre receipt de rotação qualificado e publicação do campo `medicoes` (lista vazia). Cinco casos de composição instalada e quatro de adaptação pelo executor. Isso identifica a fronteira vermelha, não encerra o diagnóstico da raiz.
- `scripts/tests/test_motivo_decisao_composicao.py::test_fonte_e_contrato_cabem_inteiros_no_transporte_local`: instrução corporal com 4015 caracteres excede o limite esperado de 3800. Raiz não investigada nesta etapa visual.

A autorização de commit de toda a worktree preserva esses candidatos e testes vermelhos; não representa declaração de que todos os contratos da Laylay estão corrigidos. Nenhum teste foi alterado para esconder as falhas.

O carregamento direto por `file://` foi confirmado no navegador: nove abas, adaptador local presente e objeto Qt ausente. Os hashes dos três arquivos oficiais foram conferidos novamente e permanecem iguais aos valores acima. Em 1440×900 e 1366×768, as nove abas não apresentaram controles ou títulos cortados horizontalmente; o botão de abrir Streaming aparece na primeira dobra. A rolagem da aba Sistema voltou a 400 px após visitar Memória; o mascote e o botão musical conservaram identidade DOM após dez eventos de estado.

**Revisão visual independente: PASS na segunda rodada.** As nove abas foram examinadas com dados e vazias em 1440 px e 375 px, além da navegação intermediária em 1366 px e 768 px. Foram aprovados o menu móvel com nomes e foco, as 24 amostras dos gráficos, os temas violeta/ciano, os modos completo/painel/ilha, a preservação de rascunho entre modos, buscas de memória/faixa, medidor musical simulado, consulta DEV e abertura do player demonstrativo. O navegador não registrou erros JavaScript. A primeira rodada exigiu revisão da navegação móvel, legenda dos gráficos e indicação de demonstração; a segunda confirmou as correções.

Limites visuais menores registrados pelo avaliador: texto final da indicação de demonstração usa reticências em 375 px (a identificação permanece visível); fonte do painel rápido é mais compacta; linhas de playlist próximas do player fixo precisam da rolagem normal para o clique. O refinamento continua sendo proposta visual, sem validação de novos efeitos no runtime oficial.

## Cópia para continuidade

Os sete arquivos da prévia foram copiados para `previa_refinada/`, com comparação SHA256 arquivo a arquivo. `node --check` passou para os três JavaScripts dessa cópia. As capturas das nove abas, painel rápido, ilha e início em 375 px estão em `estudo_refinamento/previa_capturas/`. O README permite reabrir `index.html` após reiniciar o PC, sem depender do servidor temporário.

A checagem final também percorreu as nove abas em 768×800 e 375×812 sem cortes horizontais de títulos/controles. A avaliação confirmou busca por memória (um resultado), busca de faixa (Space Song), reprodução simulada por linha e atualização do medidor a partir dos três valores do evento de demonstração. Esses efeitos existem apenas no adaptador da prévia.

A inspeção do índice não encontrou arquivos com nomes de credenciais ou padrões fortes de chave privada/token; arquivos privados ignorados continuam ignorados. `git diff --cached --check` apontou espaços finais nos logs históricos preservados e linhas em branco finais em bundles HTML/JS já existentes; esses avisos de formatação não foram apresentados como teste funcional nem motivaram alteração dos registros históricos ou da interface oficial.
