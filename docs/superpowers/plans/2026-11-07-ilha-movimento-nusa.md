# Plano de implementação do movimento da ilha

> Skill de execução: superpowers:executing-plans. A aprovação de Pedro cobre
> a adaptação da demonstração e a abertura/recolhimento pelo mouse.

**Objetivo** — Dar à ilha da Laylay expansão, recolhimento e entrada de conteúdo
inspirados na demonstração oficial do Nusa.

**Arquitetura** — `JanelaInterfaceWebV1` decide hover, foco e geometria com os
temporizadores existentes. O HTML anima a entrada depois da confirmação de
geometria. O gesto local não passa pelo executor.

**Tecnologia** — PySide6, Qt WebEngine, JavaScript e CSS locais.

**Especificação** — `artifacts/interface_v1/nusa_20261105/ANALISE_E_PROPOSTA.md`.

## Contratos e verificação

- [x] Reproduzir a lacuna em `scripts/tests/test_terminal_desktop_integrado.py`.
  Uma passagem rápida não abre. Permanecer abre o resumo na mesma janela.
  Sair recolhe. Fechar manualmente sob o cursor exige uma nova entrada.
- [x] Ligar o dwell existente de 200 ms e a tolerância de saída de 750 ms em
  `interface_web_v1.py`. Preservar edição, arrasto, fala, transmissão e modais.
- [x] Testar a diferença observável entre trajetórias de expansão/recolhimento,
  a reversão do retângulo atual e o respeito à área útil da tela.
- [x] Aplicar curvas distintas ao Qt. Adaptar a expansão de 620 ms e o
  recolhimento de 500 ms da demonstração. Conter o movimento do retângulo
  na área útil. Deixar o pequeno rebote para o conteúdo do renderer.
- [x] Testar no QWebEngine a entrada com fade e escala após confirmação.
  Manter a transição direcional entre abas e o modo de movimento reduzido.
- [x] Aplicar o acabamento escuro na moldura desktop e conferir capturas Qt.
- [x] Rodar regressões de desktop, ponte, páginas e estabilidade. Registrar
  diferença entre a prova local da interface e a referência web do Nusa.

A revisão acrescentou três controles de continuidade e interação. A cobertura
retém cliques, a aba de trabalho sobrevive ao resumo e o rascunho guardado
permanece disponível após recolher. A regressão final teve 119 aprovações.
