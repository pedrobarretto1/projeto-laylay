# Roadmap do avatar da Laylay

Este arquivo concentra somente a evolução visual do avatar. Mudanças de conversa,
memória, comandos, aprendizado e autonomia continuam nos módulos da mente da Laylay.

## Estado atual

- [x] Janela transparente, sem borda e sempre visível.
- [x] Posição e tamanho persistidos.
- [x] Arraste com o mouse e menu pelo botão direito.
- [x] Imagem parada própria para cada emoção disponível.
- [x] Imagem falando própria para cada emoção disponível.
- [x] Catálogo recursivo: cada emoção pode ficar organizada em sua pasta.
- [x] Início da animação sincronizado ao começo real do áudio.
- [x] Processo visual isolado: uma falha no avatar não encerra a assistente.
- [x] Encerramento automático se o processo principal ou o CMD for fechado.
- [x] Fallback para a fala genérica ou imagem parada quando uma boca não existe.

## Convenção dos arquivos

Cada emoção fica em sua própria pasta, com uma imagem parada e outra falando:

```text
avatar/
├── animada/
│   ├── laylay_animada.png
│   └── laylay_animada_falando.png
├── brava/
│   ├── laylay_brava.png
│   └── laylay_brava_falando.png
├── calma/
│   ├── laylay_calma.png
│   └── laylay_calma_falando.png
├── envergonhada/
├── feliz/
├── surpresa/
└── triste/
```

O nome da pasta define a emoção. No arquivo de fala, use `falando` no nome.
Uma imagem genérica `laylay_falando.png` na raiz continua opcional como fallback.
Pastas novas também são catalogadas automaticamente.

As imagens devem ser PNG RGBA, com fundo realmente transparente e dimensões iguais.

## Próximas etapas

### 1. Expressões emocionais

- [x] Adicionar os PNGs das emoções já reconhecidas.
- [x] Mapear sinônimos da mente para as expressões disponíveis.
- [x] Alternar entre boca fechada e falando dentro da emoção atual.
- [ ] Manter a expressão por alguns instantes depois da fala.
- [ ] Usar intensidade emocional para escolher variações suaves ou fortes.
- [x] Evitar trocas rápidas quando duas emoções aparecem em sequência.

### 2. Animações de repouso

- [ ] Piscar em intervalos naturais e não periódicos.
- [x] Criar movimento sutil de respiração.
- [x] Usar movimento levemente mais vivo enquanto ela fala.
- [x] Atualizar a movimentação em 15 quadros por segundo.
- [x] Permitir desligar o movimento pelo menu.
- [ ] Reduzir animações durante jogos ou modo de economia.
- [ ] Pausar animações quando o avatar estiver oculto.

### 3. Boca guiada pelo áudio

- [ ] Adicionar boca fechada, semiaberta e aberta.
- [ ] Medir a amplitude do áudio reproduzido.
- [ ] Suavizar a troca dos quadros para evitar tremulação.
- [ ] Manter sincronização também no TTS de fallback.

### 4. Reações visuais

- [ ] Reação curta ao concluir um comando.
- [ ] Reação diferente para falha ou dispositivo indisponível.
- [ ] Reação discreta quando começa a ouvir.
- [ ] Reação de pensamento enquanto prepara uma resposta demorada.

### 5. Acessibilidade e uso diário

- [ ] Balão de fala opcional.
- [x] Controle de opacidade.
- [ ] Modo clique-através com atalho para destravar.
- [ ] Escolha de monitor e posição por monitor.
- [ ] Perfis de tamanho para trabalho, jogo e tela cheia.

## Regras de integração

- O avatar apenas representa o estado; ele não decide emoções nem ações.
- O processo visual nunca deve bloquear voz, conversa ou comandos.
- Falta de imagem sempre deve cair em um fallback conhecido.
- Nenhum estado visual deve ser usado como confirmação de uma ação real.
- Novas animações precisam ter opção de desativação e custo baixo de CPU.
