# Teste automatizado da Laylay

Iniciado em 2026-08-31T15:22:47.

## 001. Você

Coloca a playlist red151 fonte.

_Enviado em 2026-08-31T15:22:52._

### Laylay

Deixei red151 fonte aberto e em foco. Tô colocando pra tocar.

**Plano observado:** `PLAYLIST_PLAY` → `playlist_aberta` (executou=True, confirmado=True).

---

## 002. Você

Coloca a playlist z51.

_Enviado em 2026-08-31T15:22:57._

### Laylay

Você ainda não criou a playlist z51. Quer que eu salve essa música nela?

**Plano observado:** `PLAYLIST_PLAY` → `playlist_nao_encontrada` (executou=False, confirmado=False).

---

## 003. Você

pausa a música

_Enviado em 2026-08-31T15:22:57._

### Laylay

Pausei. A música fica quieta até você chamar.

**Plano observado:** `MEDIA_CONTROL` → `midia_pause` (executou=True, confirmado=True).

---

## 004. Você

continua a música

_Enviado em 2026-08-31T15:22:59._

### Laylay

Dei play. A música voltou a ocupar o ambiente.

**Plano observado:** `MEDIA_CONTROL` → `midia_play` (executou=True, confirmado=True).

---

## 005. Você

qual música está tocando?

_Enviado em 2026-08-31T15:23:01._

### Laylay

Está tocando Anny - SE EU TE PEDIR ft. Lucas A.R.T.

**Plano observado:** `MUSIC_STATUS` → `midia_status_consultado` (executou=True, confirmado=True).

---

## 006. Você

sim

_Enviado em 2026-08-31T15:23:01._

### Laylay

Eu me adiantei na fala, mas essa ação não foi executada nem confirmada.

**Plano observado:** planejado; sem comando operacional.

---

## 007. Você

Mostra a playlist z51.

_Enviado em 2026-08-31T15:23:02._

### Laylay

A playlist Z51 é curtinha: 1 música. A principal é Anny - SE EU TE PEDIR ft. Lucas A.R.T.

**Plano observado:** `PLAYLIST_LIST` → `playlists_listadas` (executou=True, confirmado=True).

---

## Roteiro concluído
