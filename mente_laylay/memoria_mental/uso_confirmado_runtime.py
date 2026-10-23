"""Projeção factual do uso confirmado; frequência nunca concede autoridade."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import math
import re
import threading
import time
from datetime import datetime
from typing import Any

from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao, STATUS_RESULTADO_JA_SATISFEITO


def _numero(valor: Any) -> float:
    if isinstance(valor, bool):
        return 0.0
    try:
        numero = float(valor)
        return numero if math.isfinite(numero) else 0.0
    except (ValueError, TypeError):
        return 0.0


def _video(valor: Any) -> str:
    texto = str(valor or '')
    encontrado = re.search(r'(?:[?&]v=|youtu\.be/)([A-Za-z0-9_-]{11})(?:[^A-Za-z0-9_-]|$)', texto)
    return encontrado.group(1) if encontrado else ''


def inicio_sem_historico() -> dict[str, Any]:
    return {'freshness': 'unavailable', 'observed_at': 0.0, 'observed_since': 0.0,
        'periods': {str(dias): {'playlists': [], 'actions': []} for dias in (7, 30)}}


@dataclass(frozen=True)
class _CandidatoPlaylist:
    identidade: str
    nome: str
    inicio: float
    recebido: float
    tab: int
    video: str


class UsoConfirmadoRuntime:
    def __init__(self, *, motor_aprendizado: Any, memoria_sqlite: Any,
        playlist_state_getter: Callable[[], Mapping[str, Any]] | None = None,
        capacidade_getter: Callable[[str], Mapping[str, Any]] | None = None,
        clock: Callable[[], float] = time.time, log: Callable[[str], Any] = print) -> None:
        self.motor = motor_aprendizado
        self.memoria = memoria_sqlite
        self.playlist_state_getter = playlist_state_getter or (lambda: {})
        self.capacidade_getter = capacidade_getter
        self.clock = clock
        self.log = log
        self._lock = threading.RLock()
        self._candidatos: dict[str, _CandidatoPlaylist] = {}

    def _persistir(self, identidade: str, valor: dict[str, Any]) -> bool:
        return bool(self.motor.registrar_evidencia(chave='uso_confirmado:' + valor['kind'],
            tipo='uso_confirmado', escopo='interface', valor=valor, sinal=0.0,
            origem='executor_confirmado', evidencia='Resultado factual confirmado, sem autorização de repetição.',
            contexto={'proveniencia': {'id_solicitacao': identidade}},
            id_evento='uso:' + valor['kind'] + ':' + identidade))

    def observar_resultado(self, resultado: ResultadoAcao) -> bool:
        """Aceita somente contratos tipados da porta de publicação do executor."""
        if type(resultado) is not ResultadoAcao or resultado.origem != 'executor':
            return False
        identidade = resultado.id_solicitacao
        if (not identidade or len(identidade) > 180 or resultado.executou is not True
            or resultado.status in STATUS_RESULTADO_JA_SATISFEITO
            or any(x in resultado.status for x in ('falha', 'erro', 'cancel', 'aguardando', 'bloqueado'))):
            return False
        if resultado.intent == 'PLAYLIST_PLAY':
            if resultado.confirmado is False or resultado.status not in {'playlist_aberta', 'playlist_enviada_sem_confirmacao'}:
                return False
            return self._candidatar_playlist(resultado)
        if resultado.confirmado is not True:
            return False
        params = resultado.params
        valor: dict[str, Any] | None = None
        if resultado.intent == 'APP_OPEN':
            nome = str(params.get('nome_app') or resultado.alvo or '').strip().casefold()
            if nome in {'visual studio code', 'vscode', 'vs code', 'code'}:
                valor = {'kind': 'acao', 'id': 'open_vscode', 'title': 'Abrir VS Code',
                    'intent': resultado.intent, 'target': 'visual_studio_code'}
        elif resultado.intent == 'IOT_CONTROL':
            alvo = str(params.get('alvo') or resultado.alvo or '').strip().casefold()
            acao = str(params.get('acao') or '').casefold()
            if re.fullmatch(r'[a-z0-9_]{1,64}', alvo) and acao in {'ligar', 'desligar'}:
                valor = {'kind': 'acao', 'id': 'iot_power', 'title': 'Ligar ou desligar dispositivo',
                    'intent': resultado.intent, 'target': alvo, 'action': acao}
        elif resultado.intent in {'ORGANIZAR_DESKTOP', 'BRIEFING_REPEAT'}:
            identificador, titulo = {'ORGANIZAR_DESKTOP': ('organize_desktop', 'Organizar desktop'),
                'BRIEFING_REPEAT': ('briefing', 'Briefing')}[resultado.intent]
            valor = {'kind': 'acao', 'id': identificador, 'title': titulo, 'intent': resultado.intent}
        elif resultado.intent == 'VOLUME':
            nivel = params.get('nivel_volume')
            if type(nivel) is int and 0 <= nivel <= 100:
                valor = {'kind': 'acao', 'id': 'volume_set', 'title': 'Ajustar volume',
                    'intent': resultado.intent, 'level': nivel}
        return self._persistir(identidade, valor) if valor else False

    def _candidatar_playlist(self, resultado: ResultadoAcao) -> bool:
        agora = self.clock()
        inicio = _numero(resultado.inicio_execucao)
        nome = str(resultado.params.get('nome_playlist') or resultado.alvo or '').strip()
        if not nome or len(nome) > 80 or inicio <= 0 or not 0 <= agora - inicio <= 120:
            return False
        estado = dict(self.playlist_state_getter() or {})
        tab = estado.get('tab_id')
        video = _video(estado.get('last_url'))
        if estado.get('name') != nome or type(tab) is not int or tab < 0 or not video:
            return False
        candidato = _CandidatoPlaylist(resultado.id_solicitacao, nome, inicio, agora, tab, video)
        with self._lock:
            self._candidatos = {k: v for k, v in self._candidatos.items() if agora - v.recebido <= 120}
            anterior = self._candidatos.get(candidato.identidade)
            if anterior and (anterior.nome, anterior.tab, anterior.video) != (nome, tab, video):
                return False
            self._candidatos[candidato.identidade] = anterior or candidato
        # O WS pode observar o play antes de a publicação do receipt voltar.
        player = estado.get('player')
        if isinstance(player, Mapping):
            self.observar_player(player, estado)
        return True

    def observar_player(self, player: Mapping[str, Any], playlist_state: Mapping[str, Any]) -> None:
        agora = self.clock()
        observado = _numero(player.get('observed_at'))
        origem = _numero(player.get('_source_observed_at')) / 1000.0
        if (player.get('state') != 'playing' or player.get('is_ad') is not False
            or not 0 <= agora - observado <= 12 or not 0 <= agora - origem <= 12):
            return
        with self._lock:
            for identidade, candidato in list(self._candidatos.items()):
                if agora - candidato.recebido > 120:
                    del self._candidatos[identidade]
                    continue
                if (observado < candidato.inicio or origem < candidato.inicio
                    or type(player.get('tab_id')) is not int or player.get('tab_id') != candidato.tab
                    or playlist_state.get('tab_id') != candidato.tab
                    or playlist_state.get('name') != candidato.nome
                    or player.get('video_id') != candidato.video
                    or _video(playlist_state.get('last_url')) != candidato.video):
                    continue
                valor = {'kind': 'playlist', 'name': candidato.nome, 'video_id': candidato.video,
                    'tab_id': candidato.tab, 'intent': 'PLAYLIST_PLAY'}
                if self._persistir(identidade, valor):
                    del self._candidatos[identidade]

    def snapshot(self) -> dict[str, Any]:
        agora = self.clock()
        resultado = inicio_sem_historico()
        try:
            eventos = self.memoria.listar_eventos_aprendizado_tipo('uso_confirmado', desde=agora - 30 * 86400)
        except Exception:
            return resultado
        resultado.update(freshness='fresh', observed_at=agora)
        if len(eventos) >= 10000:
            resultado['freshness'] = 'stale'  # Recorte limitado; não fingir histórico completo.
        instantes = []
        capacidades: dict[str, Mapping[str, Any]] = {}
        for dias in (7, 30):
            playlists: dict[str, dict[str, Any]] = {}
            acoes: dict[str, dict[str, Any]] = {}
            for evento in eventos:
                if evento.get('origem') != 'executor_confirmado' or not str(evento.get('id_evento') or '').startswith('uso:'):
                    continue
                try:
                    instante = datetime.fromisoformat(evento['criado_em']).timestamp()
                except (ValueError, KeyError, TypeError):
                    continue
                if not 0 <= agora - instante <= dias * 86400:
                    continue
                instantes.append(instante)
                valor = evento.get('valor') or {}
                if valor.get('kind') == 'playlist':
                    nome = valor['name']
                    item = playlists.setdefault(nome, {'name': nome, 'confirmed_plays': 0,
                        'last_played_at': 0.0, 'reason': 'Reproduções iniciadas confirmadas pelo player no período.'})
                    item['confirmed_plays'] += 1
                    item['last_played_at'] = max(item['last_played_at'], instante)
                elif valor.get('kind') == 'acao':
                    if not callable(self.capacidade_getter):
                        continue
                    try:
                        intent = valor['intent']
                        if intent not in capacidades:
                            capacidades[intent] = self.capacidade_getter(intent) or {}
                        capacidade = capacidades[intent]
                    except Exception:
                        continue
                    if capacidade.get('disponivel') is not True or capacidade.get('estado') == 'indisponivel':
                        continue
                    item = acoes.setdefault(valor['id'], {'id': valor['id'], 'title': valor['title'],
                        'confirmed_uses': 0, 'last_used_at': 0.0,
                        'reason': 'Ações com resultado confirmado no período; repetir exige sua escolha.'})
                    item['confirmed_uses'] += 1
                    item['last_used_at'] = max(item['last_used_at'], instante)
            resultado['periods'][str(dias)] = {
                'playlists': sorted(playlists.values(), key=lambda i: (-i['confirmed_plays'], -i['last_played_at'], i['name']))[:12],
                'actions': sorted(acoes.values(), key=lambda i: (-i['confirmed_uses'], -i['last_used_at'], i['id']))[:12]}
        resultado['observed_since'] = min(instantes, default=0.0)
        return resultado


def criar_uso_confirmado_runtime(**kwargs: Any) -> UsoConfirmadoRuntime:
    return UsoConfirmadoRuntime(**kwargs)
