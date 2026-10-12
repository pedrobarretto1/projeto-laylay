"""Prova nativa da aba, sem iniciar a IA ou alterar o navegador escolhido.

Uso: python scripts/analises/validar_streaming_local.py --titulo "título único"
Deixe um vídeo em reprodução na janela indicada, sem minimizar.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from cliente.terminal_laylay_2 import JanelaLaylay


class TransporteSemMente(QObject):
    mensagem = Signal(dict)
    conectado = Signal(bool)
    falha = Signal(str)

    def enfileirar(self, mensagem: dict) -> bool:
        raise AssertionError(f"Streaming tentou acessar a mente: {mensagem.get('type')}")

    def parar(self) -> None:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--titulo", required=True)
    parser.add_argument("--saida", type=Path)
    parser.add_argument("--largura", type=int, default=1250)
    parser.add_argument("--altura", type=int, default=850)
    parser.add_argument("--esperar-fechamento", action="store_true",
                        help="Depois da prova positiva, aguarda fechar a origem para provar falha segura.")
    parser.add_argument("--esperar-ajuste", action="store_true",
                        help="Aguarda alterar o tamanho do vídeo no navegador para provar autoajuste.")
    args = parser.parse_args()
    app = QApplication.instance() or QApplication([])
    assert app.platformName() != "offscreen", "Esta prova requer o Windows real."
    worker = TransporteSemMente()
    janela = JanelaLaylay(worker, RAIZ)
    janela.resize(args.largura, args.altura)
    janela.show()
    janela.selecionar_pagina("streaming")
    QTest.qWait(80)
    pagina = janela._garantir_pagina_carregada("streaming")
    prazo_fontes = time.monotonic() + 10
    while time.monotonic() < prazo_fontes and not pagina._janelas:
        QTest.qWait(100)
    enviados: list[dict] = []
    janela.enviar_json.connect(enviados.append)
    hashes: set[str] = set()
    quadros = 0

    def observar(imagem) -> None:
        nonlocal quadros
        quadros += 1
        hashes.add(hashlib.sha256(bytes(imagem.constBits())).hexdigest())

    pagina.captura.imagem_recebida.connect(observar)
    try:
        indices = [i for i, origem in enumerate(pagina._janelas)
                   if args.titulo.casefold() in origem.titulo.casefold()]
        assert len(indices) == 1, f"Exija título único. Encontradas: {pagina.janelas.count()} janelas; matches={len(indices)}"
        pagina.janelas.setCurrentIndex(indices[0])
        QTest.mouseClick(pagina.transmitir, Qt.LeftButton)
        prazo = time.monotonic() + 10
        while time.monotonic() < prazo and len(hashes) < 12 and pagina.captura.estado != "erro":
            QTest.qWait(100)
        assert pagina.captura.estado == "transmitindo", pagina.estado.text()
        assert len(hashes) >= 12, f"Não comprovou imagem em movimento: {len(hashes)} frames distintos"
        tamanho = [pagina.visor.imagem.width(), pagina.visor.imagem.height()]
        assert not pagina.visor.imagem.isNull(), "Sem enquadramento confirmado"
        fonte = pagina.fontes.fontes[pagina._chave_ativa]
        proporcao = fonte.video[2] / fonte.video[3]
        assert abs(tamanho[0] / tamanho[1] - proporcao) < .02
        assert not enviados, "Emitiu mensagem para a mente"
        if args.saida:
            args.saida.mkdir(parents=True, exist_ok=True)
            janela.grab().save(str(args.saida / "streaming_janela_real.png"))
        if args.esperar_ajuste:
            print("PRONTO_PARA_AJUSTAR_VIDEO", flush=True)
            prazo = time.monotonic() + 30
            while time.monotonic() < prazo and pagina.visor.imagem.width() == tamanho[0]:
                QTest.qWait(100)
            assert not pagina.visor.imagem.isNull(), "Autoajuste perdeu a geometria do vídeo"
            assert pagina.visor.imagem.width() != tamanho[0], "Tamanho do vídeo não foi atualizado"
            if args.saida:
                janela.grab().save(str(args.saida / "streaming_video_ajustado.png"))
        QTest.mouseClick(pagina.flutuante, Qt.LeftButton)
        QTest.qWait(250)
        assert pagina._popup is not None and pagina._popup.isVisible()
        QTest.keyClick(pagina._popup, Qt.Key_Escape)
        assert pagina._popup is None
        QTest.mouseClick(pagina.tela_cheia, Qt.LeftButton)
        QTest.qWait(250)
        assert pagina._popup.isFullScreen()
        QTest.keyClick(pagina._popup, Qt.Key_Escape)
        QTest.mouseClick(pagina.parar, Qt.LeftButton)
        assert pagina.captura.estado == "parado"
        assert pagina.captura._captura is None and pagina.visor.imagem.isNull()
        pagina.iniciar()
        QTest.qWait(400)
        if args.esperar_fechamento:
            print("PRONTO_PARA_FECHAR_ORIGEM", flush=True)
            prazo = time.monotonic() + 30
            while time.monotonic() < prazo and pagina.captura._captura is not None:
                QTest.qWait(100)
            assert "indisponível" in pagina.estado.text() or pagina.captura.estado == "erro", "Fechamento da origem não foi comunicado"
            assert pagina.captura._captura is None and pagina.visor.imagem.isNull()
            assert not pagina.tela_cheia.isEnabled()
        janela.selecionar_pagina("conversa")
        assert pagina.captura._captura is None and pagina.visor.imagem.isNull()
        assert enviados == []
        print(json.dumps({"runtime": "Windows/Qt", "quadros": quadros,
                          "imagens_distintas": len(hashes), "resolucao": tamanho,
                          "video_automatico": "GREEN", "flutuante": "GREEN", "tela_cheia": "GREEN",
                          "resize_do_video": "GREEN" if args.esperar_ajuste else "não testado",
                          "origem_fechada": "GREEN" if args.esperar_fechamento else "não testada",
                          "parada_e_saida": "GREEN", "mensagens_para_ia": len(enviados)}, ensure_ascii=False))
    finally:
        janela.close()
        app.processEvents()


if __name__ == "__main__":
    main()
