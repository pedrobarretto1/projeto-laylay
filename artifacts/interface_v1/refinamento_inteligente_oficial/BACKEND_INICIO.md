# Início inteligente: contrato factual

Base: main, HEAD b128f4e48b774352846a40672de493d19c30f109. Worktree suja preservada,
inclusive candidatos paralelos de cognição, comparação de resultados e corpo.

## Primeira fronteira

Receipts reais chegavam ao registrador contextual sem observador de uso factual.
O RED `test_receipt_tipado_alimenta_uso_antes_da_publicacao_contextual` alcançou
essa porta real e obteve `observados=[]`. O candidato registra estatística antes
do veto contextual, sem promover um efeito tardio ao turno corrente. Objetos
serializados/propostas/dicts não entram como receipts tipados nessa observação.

Não usar quantidade de faixas do catálogo como audições. O histórico musical
legado registra títulos por hora, inclusive metadados repetidos/troca de aba;
não identifica reproduções de playlists. Essas duas alternativas foram
falsificadas por código antes do candidato.

## Contrato

`UsoConfirmadoRuntime` recebe o mesmo ResultadoAcao de voz, chat e painel;
persiste evidência via MotorAprendizado e SQLite existentes. `id_evento` é
derivado do id_solicitacao canônico. Replay não soma; identidade divergente é
recusada pelo owner transacional. Falha, incerteza, proposta e no-op não são
efeitos novos. O aprendizado de confiabilidade existente não foi alterado.

Playlists exigem seleção identificada, playlist/aba/vídeo correspondentes,
playing observado após início real da invocação, amostra recente e ausência de
anúncio explicitamente observada. Ausência do boolean de anúncio é desconhecida.
Um player aceito antes do receipt também pode confirmar a seleção; heartbeat,
auto-next e reconexão não criam outra seleção. Conta reproduções iniciadas
confirmadas, não duração ou conclusão da faixa.

O DOM/eleição já existente da extensão agora publica o boolean isAd no mesmo
player_state. Não foram criados UUIDs de playback, permissões, novas capturas
ou comandos de execução. A extensão já carregada precisa carregar o código
atualizado para fornecer esse campo; fonte antiga mantém ranking vazio com
honestidade.

`dashboard.home` publica apenas frequência/frescor/período 7 ou 30 dias, com
campos fechados de playlists e IDs de ações existentes. Nenhum parâmetro livre,
receipt, URL ou caminho entra no agregado público. A disponibilidade vem do
catálogo vivo; frequência nunca concede autorização. Memória/retomar/contexto
continuam nas projeções existentes. Preferências de fixar/ocultar são do owner
QSettings, fora deste backend.

## Validação

RED causal de publicação: 1 failed. RED de anúncio na função DOM real executada
em Node: 2 failed (campo isAd ausente). RED de documentação recuperada pelo
catálogo vivo: 3 failed. Cada RED foi confirmado antes do respectivo candidato.

`backend_regressivos.xml`: 92 passed, 10.22 segundos. Inclui SQLite temporário
real; restart/dedupe/replay divergente; execução de PlaylistRuntime,
OperacoesMusicais, registros tipados, executor, adaptador e ChromeWs reais com
somente folha externa de navegador/fala controlada; observação antes/depois do
receipt; 7/30 dias; sanitização; catálogo vivo e resultado parcial entre dois
domínios. Node executa as funções reais do content script e da eleição de
background em DOM controlado, com boolean true/false/desconhecido.

Regressão adicional anterior: 248 passed, 62.87 segundos em comparação de
resultado, proveniência, bridge e aprendizado. As alterações de timestamp foram
limitadas a PLAYLIST_PLAY sem fontes tipadas preexistentes. Os testes do
contrato novo estão em scripts/tests/test_uso_confirmado_inicio.py.

Não é prova de reprodução no Chrome pessoal nem uso estatístico diário. Nenhum
histórico privado foi aberto, nenhum aparelho foi acionado, nenhuma extensão
foi instalada/recarregada, nenhum commit ou push foi criado. A validação Qt e
visual pertence à integração coordenada pela raiz desta tarefa.
