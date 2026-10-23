"""Ensaio instalado: clipboard Windows → arquivo, durante TTS real.

Memória e artefatos são isolados. Não inicia os serviços da sessão desktop,
não substitui voz, executores, porteiros, receipts ou o quadro cooperativo.
O stream ativo certifica reprodução pelo player, não audição humana.
"""
from __future__ import annotations

import ast
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))


@contextmanager
def clipboard_controlado(texto: str):
    """Preserva dados; bitmap é restaurado pelo DIB que o Windows sintetiza.

    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setclipboarddata
    Nenhum handle GDI é reutilizado depois de EmptyClipboard.
    """
    import win32clipboard as clip
    import pyperclip
    anteriores = []
    clip.OpenClipboard()
    try:
        formato = clip.EnumClipboardFormats(0)
        while formato:
            valor = clip.GetClipboardData(formato)
            if formato == clip.CF_BITMAP and (
                clip.IsClipboardFormatAvailable(clip.CF_DIB) or clip.IsClipboardFormatAvailable(17)
            ):
                formato = clip.EnumClipboardFormats(formato)
                continue
            if not isinstance(valor, (str, bytes)):
                raise RuntimeError('Clipboard possui formato não serializável; ensaio não alterou o conteúdo.')
            anteriores.append((formato, valor))
            formato = clip.EnumClipboardFormats(formato)
    finally:
        clip.CloseClipboard()
    pyperclip.copy(texto)
    try:
        yield
    finally:
        # Um Ctrl+C novo do usuário tem precedência sobre a restauração.
        if pyperclip.paste() == texto:
            clip.OpenClipboard()
            try:
                clip.EmptyClipboard()
                for formato, valor in anteriores:
                    clip.SetClipboardData(formato, valor)
                for formato, valor in anteriores:
                    assert clip.GetClipboardData(formato) == valor, 'Restauração do clipboard não confirmou os dados'
            finally:
                clip.CloseClipboard()


def carregar_composicao(pasta: Path):
    from mente_laylay.integracao import instancia_unica
    adquirir = instancia_unica.adquirir_instancia_unica
    instancia_unica.adquirir_instancia_unica = lambda ident, **k: adquirir(
        str(ident) + '.fala-execucao-' + str(os.getpid()), **k)
    fonte = RAIZ / 'laylay.py'
    linha = next(n.lineno for n in ast.parse(fonte.read_text(encoding='utf-8-sig')).body
                 if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name)
                    and t.id == 'PASTA_MEMORIA' for t in n.targets))

    def isolar_memoria(frame, evento, _arg):
        if (evento == 'line' and Path(frame.f_code.co_filename) == fonte
                and frame.f_lineno > linha and 'PASTA_MEMORIA' in frame.f_globals):
            frame.f_globals['PASTA_MEMORIA'] = str(pasta / 'memoria')
            sys.settrace(None)
        return isolar_memoria
    # Única adaptação de configuração: caminho de persistência, antes de
    # qualquer factory que receba PASTA_MEMORIA. Código instalado inalterado.
    sys.settrace(isolar_memoria)
    try:
        import laylay as root
    finally:
        sys.settrace(None)
    assert Path(root.PASTA_MEMORIA) == pasta / 'memoria'
    return root


def coletar(pasta: Path, caso: str = 'sucesso') -> dict:
    pasta.mkdir(parents=True, exist_ok=False)
    os.environ['LAYLAY_ARQUIVOS_RAIZES_PERMITIDAS'] = str(pasta)
    root = carregar_composicao(pasta)
    voz = root._voz_runtime
    falas, metricas, eventos = [], [], []
    import mente_laylay.personalidade.orquestrador_fala_runtime as modulo_fala
    registrar_fala = modulo_fala.registrar_fala_observada
    def observar_registro(*a, **k):
        try:
            return registrar_fala(*a, **k)
        except ValueError as erro:
            eventos.append({'tipo': 'registro_fala_recusado', 'erro': str(erro),
                            'turno_id': k.get('turno_id'), 'canal': k.get('canal')})
            raise
    modulo_fala.registrar_fala_observada = observar_registro
    root._orquestrador_fala_runtime.registrar_observador_texto_final(
        lambda texto, *_a, **k: falas.append({'texto': texto, 'id': k.get('mensagem_id'),
                                               'ts': time.monotonic()}) or True)
    metrica_original = voz.registrar_metrica_cb
    def metrica(nome, duracao, sucesso, **dados):
        metricas.append({'nome': nome, 'duracao_ms': duracao, 'sucesso': sucesso,
                         'ts': time.monotonic()})
        if callable(metrica_original):
            metrica_original(nome, duracao, sucesso, **dados)
    voz.registrar_metrica_cb = metrica
    texto = 'Ensaio autorizado de fala e execução: conteúdo local de diagnóstico.'
    destino = pasta
    if caso == 'falha':
        destino = pasta / 'pai_que_e_arquivo.txt'
        destino.write_text('barreira real: este pai é arquivo, não diretório', encoding='utf-8')
    if caso == 'sem_audio':
        voz.definir_modo_silencioso(True, origem='ensaio_explicito')
    caminho = destino / 'objetivo_concorrente.txt'
    fim = threading.Event()
    def observar():
        viu_arquivo = False
        intercalou = False
        while not fim.wait(.002):
            if not intercalou and caso in {'cancelamento', 'troca_turno'}:
                planos = root._quadro_cooperacao_runtime.snapshot()['planos_recentes']
                if planos and any(e['estado'] == 'executando' for e in planos[-1]['etapas']):
                    intercalou = True
                    if caso == 'cancelamento':
                        root._quadro_cooperacao_runtime.solicitar_cancelamento(planos[-1]['id'])
                    else:
                        root._iniciar_planejamento_turno('como você está?', origem='terminal')
                    eventos.append({'tipo': caso, 'ts': time.monotonic()})
            if not viu_arquivo and caminho.is_file():
                digest = hashlib.sha256(caminho.read_bytes()).hexdigest()
                if digest != hashlib.sha256(texto.encode('utf-8')).hexdigest():
                    continue
                viu_arquivo = True
                try:
                    ativo = bool(voz.sd.get_stream().active)
                except Exception:
                    ativo = False
                eventos.append({'tipo': 'arquivo_observado', 'ts': time.monotonic(),
                                'stream_audio_ativo': ativo,
                                'hash': digest})
    monitor = threading.Thread(target=observar, daemon=True)
    monitor.start()
    relatorio = {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=RAIZ,
                    text=True).strip(), 'instancia': 'composicao_instalada_com_memoria_isolada',
                 'modelo': root.MODELO_OLLAMA if hasattr(root, 'MODELO_OLLAMA') else 'configuracao_preservada',
                 'voz': voz.voice, 'caso': caso, 'falas': falas, 'metricas': metricas, 'eventos': eventos}
    try:
        assert (root._orquestrador_cooperativo_runtime.anunciar_etapa.__self__
                is root._orquestrador_fala_runtime)
        with clipboard_controlado(texto):
            pedido = f'salva o que eu copiei em um arquivo chamado objetivo_concorrente dentro da pasta {destino}'
            root._coordenador_exec_runtime.processar_sync(pedido, origem='terminal')
            prazo = time.monotonic() + 45
            while time.monotonic() < prazo:
                if (voz.fila.empty() and not root._estado_compartilhado_runtime.conversacional.get('is_speaking')):
                    break
                time.sleep(.05)
        plano = root._quadro_cooperacao_runtime.snapshot()['planos_recentes'][-1]
        relatorio['plano'] = plano
        relatorio['arquivo_conferido'] = caminho.is_file() and caminho.read_text(encoding='utf-8') == texto
        relatorio['sobreposicao_observada'] = any(e.get('stream_audio_ativo') for e in eventos)
        relatorio['audios_confirmados'] = sum(m['nome'] == 'tts_reproducao' and m['sucesso'] for m in metricas)
        if caso in {'sucesso', 'sem_audio'}:
            relatorio['ok'] = (relatorio['arquivo_conferido'] and plano['estado'] == 'confirmado'
                and len(falas) >= 2 and (caso == 'sem_audio' or
                    relatorio['sobreposicao_observada'] and relatorio['audios_confirmados'] >= 2))
        else:
            esperado = 'falhou' if caso == 'falha' else 'cancelado'
            relatorio['ok'] = (not caminho.exists() and plano['estado'] == esperado
                              and plano['resultado'].get('confirmado') is False)
        relatorio['ok'] = relatorio['ok'] and not any(e['tipo'] == 'registro_fala_recusado' for e in eventos)
    except Exception as erro:
        import traceback
        relatorio['ok'] = False
        relatorio['erro'] = type(erro).__name__ + ': ' + str(erro)
        relatorio['traceback'] = traceback.format_exc()
    finally:
        fim.set()
        monitor.join(1)
        voz.encerrar()
        (pasta / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding='utf-8')
    return relatorio


if __name__ == '__main__':
    import argparse
    argumentos = argparse.ArgumentParser()
    argumentos.add_argument('--caso', choices=['sucesso', 'falha', 'cancelamento', 'troca_turno', 'sem_audio'], default='sucesso')
    args = argumentos.parse_args()
    destino = (RAIZ / 'artifacts' / 'fala_execucao' / (time.strftime('%Y%m%d_%H%M%S') + '_' + args.caso)).resolve()
    resultado = coletar(destino, args.caso)
    print(json.dumps({'ok': resultado['ok'], 'relatorio': str(destino / 'relatorio.json'),
                      'erro': resultado.get('erro')}, ensure_ascii=False))
    raise SystemExit(0 if resultado['ok'] else 1)
