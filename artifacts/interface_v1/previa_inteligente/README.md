# Laylay — prévia do Início inteligente

Abra `index.html` diretamente ou sirva esta pasta com um servidor HTTP local. A página não precisa de instalação, biblioteca externa ou conexão de rede.

- Clique na ilha para abrir. Hover não expande. Todas as nove abas usam a mesma moldura.
- Arraste pelo corpo compacto ou pelo cabeçalho livre. A posição dura apenas esta sessão da prévia.
- “Rever entrada” repete a chegada animada. Esc ou “−” recolhem.
- O controle “Manter aberta na prévia” permite explorar sem pressa; desmarque para experimentar o recolhimento após 20 segundos sem interação.
- Início: cenários Dia, Noite e Sem histórico, ranking de 7/30 dias, fixar/ocultar/restaurar sugestões e explicações de origem.
- Música, dispositivos, conversa, terminal, gráficos e fontes de vídeo são simulações locais. Não há áudio, captura de tela, IA, comandos ao sistema ou acesso a dados pessoais.
- Configurações são temporárias e afetam apenas esta prévia. Não há gravação em configurações oficiais.

Atalhos de inspeção: `?page=home&expanded=1` (também `chat`, `automation`, `music`, `streaming`, `memory`, `system`, `dev`, `settings`), `&scenario=empty` / `day` / `night`.

API de diagnóstico: `window.LaylayPreview.getState()`, `navigate(page)`, `expand()`, `collapse()`, `replayIntro()`, `setScenario(scenario)`, `setPeriod(7|30)`, `setKeepOpen(boolean)`, `setReducedMotion(boolean)`. Sem transportes ou efeitos externos.

Assets locais: o CSS do mascote é uma cópia da construção aprovada. Ícones são esquemas SVG simples; capas e paisagem de exemplo são composições CSS. Não há recursos remotos.
