# Inventario Musical da Laylay

## Objetivo

Mapear a area de musica, playlists, YouTube e recomendacao conversacional antes
de mover mais codigo para fora do `laylay.py`.

Essa parte precisa de cuidado extra porque mistura:

- memoria musical;
- playlist atual;
- ultima playlist usada;
- busca no YouTube;
- comandos do Chrome;
- controle de midia;
- fala da Laylay;
- contexto curto da conversa.

A regra principal continua valendo:

Todas essas partes devem funcionar como uma mente unica. A separacao em modulos
e apenas organizacional; a decisao precisa continuar compartilhando contexto,
memoria curta, resultado real das acoes e personalidade.

---

## Estado atual

O `laylay.py` esta com cerca de 7598 linhas e ainda concentra parte relevante da
mente musical.

Ja existem modulos fortes em `mente_laylay`, mas o arquivo principal ainda segura
a camada runtime, ou seja, a parte que realmente fala com Chrome, toca playlist,
le aba ativa e sincroniza estado vivo.

---

## Modulos ja existentes

### `mente_laylay/memoria_mental/playlist_mental.py`

Ja contem uma boa parte da logica pura de playlist:

- normalizacao de texto;
- correcao fonetica;
- limpeza de nome de playlist;
- resolucao contextual de nome de playlist;
- leitura e escrita de `playlists.json`;
- criacao segura do arquivo;
- limpeza de URL do YouTube;
- limpeza de titulo;
- fingerprint de titulo e canal;
- deteccao de duplicata;
- adicao de URL na playlist;
- listagem de URLs;
- leitura de item por indice;
- tamanho da playlist;
- fala estilosa para conteudo de playlist;
- deteccao textual de mover faixa entre playlists.

### `mente_laylay/memoria_mental/estado_musical.py`

Ja guarda o contrato basico de estado musical:

- `ultima_playlist`;
- `playlist_bloqueada_ate`;
- `playlist_state`;
- bloqueio temporario de playlist;
- verificacao se a playlist esta bloqueada.

### `mente_laylay/memoria_mental/busca_youtube.py`

Ja guarda a parte pura da busca musical:

- normalizacao de query musical;
- pontuacao de resultado do YouTube;
- filtro contra album, mix, compilacao e playlist;
- extracao de resultados de busca;
- preferencia por faixa unica.

### `mente_laylay/memoria_mental/curadoria_musical.py`

Ja guarda a curadoria das playlists proprias da Laylay:

- analise das playlists do Pedro;
- criacao de listas da Laylay;
- escolha de faixas por titulo, artista e origem;
- busca de faixa dentro das playlists da Laylay.

### `mente_laylay/memoria_mental/musica_conversacional.py`

Ja guarda a parte conversacional leve:

- detectar pedido vago de sugestao musical;
- sugerir musica como opiniao, sem executar comando;
- evitar transformar recomendacao vaga em busca tecnica.

### `mente_laylay/autonomia/controle_midia.py`

Ja executa `MEDIA_CONTROL` com logs e validacao:

- pause;
- play;
- toggle;
- next;
- prev;
- replay;
- volume absoluto;
- rota por Chrome, nativo ou PC B;
- uso de playlist interna quando existe playlist ativa.

---

## O que ainda esta no `laylay.py`

### 1. Runtime de busca musical

Funcoes ainda presentes:

- `_buscar_videos_youtube_fila`;
- `_tentar_proxima_musica`;
- `_verificar_musica_autonoma`;
- `_buscar_primeiro_video_youtube`.

Dependencias sensiveis:

- fila global de busca musical;
- `validar_e_enviar_comando`;
- `falar_com_lipsync`;
- `enviar_mensagem`;
- estado de tentativa anterior.

Risco de extracao: medio.

Motivo: mexe com execucao real no Chrome e fallback quando o primeiro resultado
falha.

### 2. Wrappers de playlist e persistencia

Funcoes ainda presentes:

- `_playlists_load`;
- `_playlists_save`;
- `_ensure_playlists_file`;
- `LIST_PLAYLIST_CONTENT`;
- `list_playlist_urls`;
- `add_to_playlist_url`;
- `add_to_playlist_from_active_tab`;
- `ADD_TO_PLAYLIST`;
- `delete_playlist`;
- `playlist_len`.

Muitas ja delegam para `playlist_mental.py`.

Risco de extracao: baixo a medio.

Motivo: uma parte ja esta modularizada, mas ainda existe cache vivo
`playlists_carregadas` e integracao com aba ativa.

### 3. Estado de reproducao de playlist

Funcoes ainda presentes:

- `_playlist_shuffle_start`;
- `_playlist_avancar_proxima`;
- `_playlist_voltar_anterior`;
- `play_playlist`;
- `_playlist_primeira_url`;
- `_playlist_item_at`.

Dependencias sensiveis:

- `playlist_state`;
- `indice_atual`;
- `_musica_estado_set`;
- `_resolver_nome_playlist_contextual`;
- `validar_e_enviar_comando`;
- YouTube na mesma aba;
- resposta real do comando.

Risco de extracao: alto.

Motivo: e a parte que mais pode quebrar `coloca playlist anime`, `proxima`,
`volta a musica` e retomada contextual.

### 4. Apelidos e correcao fonetica

Funcoes ainda presentes:

- `_remover_acentos`;
- `_aplicar_correcao_fonetica`;
- `_normalizar_texto_com_apelidos`;
- `_carregar_apelidos_memoria`;
- `_aprender_apelido`;
- funcoes de ensino de apelido.

Risco de extracao: alto se misturado com playlist.

Motivo: apesar de ajudar playlist, isso nao e so musica. Tambem serve para
amigos, artistas, apps, sites e conversa geral. Deve virar modulo proprio de
linguagem/memoria semantica, nao ser colocado dentro da playlist.

### 5. Recomendacao/opiniao musical conversacional

Funcoes ainda presentes:

- `_responder_pedido_direcao_musical_generica`;
- `_processar_confirmacao_sugestao_musical`.

Parte pura ja esta em `musica_conversacional.py`, mas a parte que fala e executa
a confirmacao ainda esta no `laylay.py`.

Risco de extracao: medio.

Motivo: conversa e comando se encontram aqui. Precisa preservar a diferenca
entre "me recomenda" e "toca essa".

---

## Problemas estruturais encontrados

### 1. Duplicacao parcial

Algumas funcoes existem como wrapper no `laylay.py` e implementacao real em
`playlist_mental.py`.

Isso e aceitavel por compatibilidade, mas precisa diminuir com cuidado.

### 2. Runtime ainda acoplado ao arquivo principal

O `laylay.py` ainda decide e executa:

- abrir musica;
- tocar playlist;
- avancar playlist;
- voltar playlist;
- salvar musica da aba ativa.

Essa camada precisa virar um runtime musical com injecao de callbacks, parecido
com o que foi feito no Gmail.

### 3. Estado musical espalhado

O contrato base esta em `estado_musical.py`, mas o uso real ainda aparece em
varios lugares:

- `playlist_state`;
- `indice_atual`;
- `ultima_playlist`;
- cache de playlists;
- resultado real da acao.

### 4. Apelidos nao devem ser presos a playlist

Como apelidos servem para toda a Laylay, essa parte deve ir para um modulo de
linguagem/memoria semantica em uma etapa separada.

---

## Plano de extracao recomendado

## Fase M1 - Consolidar utilidades puras de playlist

Objetivo:

Mover ou eliminar wrappers simples que ainda duplicam `playlist_mental.py`.

Alvos:

- `_yt_clean_url`;
- `_remover_acentos`;
- `_aplicar_correcao_fonetica` duplicada;
- `_ORDINAL_IDX` duplicado;
- `_playlist_item_label`;
- `_playlist_item_match`;
- `_pedido_lista_geral_playlist`;
- `_listar_playlists_salvas`.

Risco: baixo.

Validacao:

- `python -m py_compile laylay.py mente_laylay/memoria_mental/playlist_mental.py`;
- listar playlists;
- listar conteudo de uma playlist;
- salvar musica na playlist.

## Fase M2 - Criar `PlaylistRuntime`

Objetivo:

Criar um runtime em:

`mente_laylay/memoria_mental/playlist_runtime.py`

Esse runtime deve receber callbacks do `laylay.py`, por exemplo:

- caminho do arquivo de playlists;
- caminho legado;
- funcao de solicitar aba ativa;
- funcao de enviar comando ao Chrome;
- funcao de abrir URL musical;
- funcao de registrar ultima playlist;
- referencia ao `playlist_state`;
- funcao de fala, se necessario.

Responsabilidades:

- carregar playlists;
- atualizar cache;
- adicionar URL;
- adicionar da aba ativa;
- apagar playlist;
- listar playlist;
- manter compatibilidade com nomes antigos.

Risco: medio.

Validacao:

- `coloca essa musica na playlist anime`;
- `quais sao minhas playlists`;
- `o que tem na playlist anime`;
- `apaga a playlist teste`.

## Fase M3 - Mover execucao de playlist

Objetivo:

Levar para o runtime:

- `play_playlist`;
- `_playlist_avancar_proxima`;
- `_playlist_voltar_anterior`;
- `_playlist_shuffle_start`.

Risco: alto.

Motivo:

Essas funcoes conversam com Chrome, estado vivo, indice atual e controle de
midia.

Validacao:

- `coloca a playlist anime`;
- `proxima`;
- `volta a musica`;
- `pausa ela`;
- `despausa ela`;
- confirmar que a mesma aba do YouTube e reutilizada.

## Fase M4 - Separar busca musical runtime

Objetivo:

Mover a fila de busca musical para um runtime proprio ou para o mesmo runtime
musical.

Alvos:

- `_buscar_videos_youtube_fila`;
- `_tentar_proxima_musica`;
- `_verificar_musica_autonoma`;
- `_buscar_primeiro_video_youtube`.

Risco: medio.

Validacao:

- `toca rock`;
- `toca Vivendo do Ocio - Nostalgia`;
- fallback quando o primeiro resultado nao abre.

## Fase M5 - Separar fala musical conversacional

Objetivo:

Mover a parte que fala e confirma sugestao musical para um runtime pequeno que
usa `musica_conversacional.py`.

Alvos:

- `_responder_pedido_direcao_musical_generica`;
- `_processar_confirmacao_sugestao_musical`.

Risco: medio.

Validacao:

- `me recomenda uma musica`;
- `me fala uma musica`;
- `quero ouvir`;
- `quero outra`;
- garantir que recomendacao vaga nao vira busca automatica sem confirmacao.

## Fase M6 - Separar apelidos e PLN global

Objetivo:

Mover apelidos, correcao fonetica e normalizacao ensinavel para um modulo geral,
nao musical.

Possivel caminho:

`mente_laylay/cognicao/linguagem_aprendida.py`

Risco: alto.

Motivo:

Afeta todas as habilidades, nao so playlist.

---

## Proximo passo recomendado

Comecar pela Fase M1.

Ela reduz duplicacao e prepara o terreno sem mexer ainda no coracao da execucao
musical. Depois disso, a melhor extracao real e criar `PlaylistRuntime`, seguindo
o mesmo estilo usado no `GmailRuntime`.

---

## Testes minimos antes de mexer na Fase M2

Falas de teste:

1. `quais sao minhas playlists`
2. `o que tem na playlist anime`
3. `coloca essa musica na playlist anime`
4. `coloca a playlist anime`
5. `proxima`
6. `volta a musica`
7. `pausa ela`
8. `despausa ela`
9. `me recomenda uma musica`
10. `quero ouvir`

Esses testes cobrem conversa, memoria, playlist, YouTube, controle de midia e
continuidade contextual.
