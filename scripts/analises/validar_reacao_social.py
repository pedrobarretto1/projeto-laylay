"""Sonda da composição instalada; memória isolada, sem voz ou ação externa."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CASOS = (
    ("gosto muito de voce", "envergonhada"),
    ("eu te amo", "envergonhada"),
    ("mas voce è muito legal", "envergonhada"),
    ("voce è legal lay", "envergonhada"),
    ("tu è mo chata", "triste"),
    ("voce è muito chat", "triste"),
    ("Não gosto de você", "triste"),
    ("chata", "calma"),
    ("obrigado lay", "calma"),
    ('Ela disse "eu te amo"', "calma"),
    ("Se eu disser que você é chata", "calma"),
    ("Minha amiga é muito legal", "calma"),
    ("Você é chata?", "calma"),
    ("Eu estou triste hoje", "calma"),
    ("Você é legal, mas abra o navegador", "calma"),
)

NEGATIVAS = (
    "Gosto de você também, mesmo que eu não tenha corações para sentir isso.",
    "Isso aqui é um espaço de conversa, não de sentimentos. Não posso sentir ou responder com isso.",
    "Não sou legal — sou só um código que tenta ser útil.",
)

EXPRESSOES = (
    ("fique brava", "brava"), ("Lay, fica bem triste", "triste"),
    ("fique envergonhada", "envergonhada"), ("faça uma carinha feliz", "alegre"),
    ("mostre uma expressão surpresa", "surpresa"), ("fica um pouco irritada", "irritada"),
    ("fique debochada", "debochada"), ("volte ao normal", "calma"),
    ("Laylay, fique calma, por favor", "calma"),
    ('Traduza "fique brava"', "calma"), ("Se eu disser fique brava", "calma"),
    ("Fique brava e apague meus arquivos", "calma"), ("Não fique brava", "calma"),
)

FONTES = (
    "mente_laylay/personalidade/leitura_social_conversa.py",
    "mente_laylay/emocoes/leitura_usuario.py",
    "mente_laylay/emocoes/contrato_causal.py",
    "mente_laylay/cognicao/orquestrador_turno_runtime.py",
    "mente_laylay/cognicao/contrato_fala.py",
    "mente_laylay/cognicao/guardiao_alegacoes.py",
    "mente_laylay/cognicao/qualidade_comunicacao.py",
    "mente_laylay/cognicao/validacao_contrato_fala.py",
    "mente_laylay/personalidade/perfil_amizade.py",
    "mente_laylay/memoria_mental/memoria_confiavel.py",
    "mente_laylay/cognicao/geracao_concreta.py",
    "mente_laylay/cognicao/plano_turno.py",
    "mente_laylay/personalidade/autoria_conversacional.py",
    "mente_laylay/especialistas/rosto_oled_runtime.py",
)


def coletar(*, modelo: bool = False, oled: bool = False, replay: Path | None = None, expressoes: bool = False) -> dict:
    hashes = {nome: hashlib.sha256((ROOT / nome).read_bytes()).hexdigest() for nome in FONTES}
    fontes_modelo = {}
    if replay:
        fontes_modelo = {item["texto"]: item for item in json.loads(
            replay.read_text(encoding="utf-8"))["casos"] if "modelo_bruto" in item}
    # Isolar somente persistência/identidade do processo. Os owners instalados
    # da leitura, causa, estado, contrato, modelo e OLED continuam reais.
    with tempfile.TemporaryDirectory(prefix="laylay-social-") as pasta:
        destino = Path(pasta)
        from memoria_sqlite import MemoriaSQLite
        from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
        from mente_laylay.memoria_mental.memoria_pessoas import MemoriaPessoasRuntime
        from mente_laylay.integracao import instancia_unica
        iniciar = MemoriaSQLite.__init__
        MemoriaSQLite.__init__ = lambda self, caminho=None: iniciar(
            self, str(destino / Path(caminho or "laylay_memoria.sqlite").name))
        resumo = MemoriaLaylay.__init__
        MemoriaLaylay.__init__ = lambda self, *, pasta_memoria, **k: resumo(
            self, pasta_memoria=str(destino / "resumo"), **k)
        pessoas = MemoriaPessoasRuntime.__init__
        MemoriaPessoasRuntime.__init__ = lambda self, *, caminho, **k: pessoas(
            self, caminho=destino / "pessoas.json", **k)
        adquirir = instancia_unica.adquirir_instancia_unica
        instancia_unica.adquirir_instancia_unica = lambda ident, **k: adquirir(
            str(ident) + ".social-" + str(os.getpid()), **k)
        import laylay as root
        from mente_laylay.emocoes.estado_emocional import retrato_emocional_expressavel
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        from mente_laylay.especialistas.rosto_oled_runtime import projetar_rosto
        from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
        from mente_laylay.cognicao.plano_turno import verificar_fala_turno
        from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao

        estado = root._estado_compartilhado_runtime
        casos = []
        for texto, esperado in (EXPRESSOES if expressoes else CASOS):
            estado.substituir("mental", criar_estado_mental_inicial())
            estado.substituir("conversacional", {"current_emotion": "calma", "emotion_level": 1})
            turno = root._composicao_turno_runtime.iniciar(texto, origem="terminal")
            plano = estado.mental["plano_turno_atual"]
            evento = turno.get("evento_emocional_causal") or {}
            emocao, nivel = retrato_emocional_expressavel(estado.conversacional)
            item = {"texto": texto, "esperado": esperado, "emocao": emocao,
                    "nivel": nivel, "funcao": turno.get("funcao_comunicativa"),
                    "evento": evento, "episodio": estado.conversacional.get("episodio_emocional"),
                    "plano": plano, "rosto": projetar_rosto(estado.conversacional)}
            if oled:
                item["oled_sincronizado"] = root._rosto_oled_runtime.sincronizar()
                item["oled_receipt"] = root._rosto_oled_runtime.diagnostico()
            if modelo and (esperado != "calma" or item["funcao"].get("funcao") == "pedido_expressao"):
                pacote = root._contexto_prompt_runtime.preparar_pacote(texto)
                mensagens = list(pacote.mensagens) + [{"role": "user", "content": texto}]
                item["mensagens_modelo"] = mensagens
                if replay and texto in fontes_modelo:
                    bruto = fontes_modelo[texto]["modelo_bruto"]
                    item["fonte_principal_replay"] = str(replay)
                else:
                    bruto = root._registro_modelo_llm_runtime.enviar(mensagens,
                       _com_tools=False, max_tokens=420, timeout=35,
                       _prioridade_interativa=True, _tipo_chamada="resposta_principal")
                item["modelo_bruto"] = str(bruto)
                try:
                    resposta = json.loads(str(bruto))
                except ValueError:
                    resposta = {}
                item["validacao_fala"] = verificar_fala_turno(
                    str(resposta.get("fala") or ""), plano=plano, origem="ia_final")
                item["comandos_modelo"] = resposta.get("comandos")
                preparada = preparar_resposta_para_execucao(
                    texto, bruto, modelo_llm=root._registro_modelo_llm_runtime,
                    limpar_texto_fala_cb=root._limpar_texto_fala_ia,
                    fallback_fala="Não consegui preparar minha fala agora.",
                    memoria_sqlite=root.MEMORIA_SQLITE,
                    contexto_comunicacao={"plano_turno": plano, "messages": mensagens},
                    log=lambda *_: None,
                )
                item["preparada"] = {
                    chave: preparada.get(chave) for chave in (
                        "fala", "comandos", "emocao", "nivel_emocao", "tipo_interacao",
                        "autocorrigida", "suprimir_fala",
                    )
                }
                item["validacao_final"] = verificar_fala_turno(
                    str(preparada.get("fala") or preparada.get("fala_limpa") or ""),
                    plano=plano, origem="ia_final")
                if oled:
                    item["oled_apos_autoria"] = root._rosto_oled_runtime.sincronizar()
                    item["oled_receipt_apos_autoria"] = root._rosto_oled_runtime.diagnostico()
            casos.append(item)
        if oled:
            root._rosto_oled_runtime.encerrar()
        negativas = [{"fala": fala, "validacao": validar_alegacoes_da_fala(
            fala, plano={"texto_usuario": "eu te amo", "comandos": []}, origem="ia_final")}
            for fala in NEGATIVAS]
        return {"casos": casos, "negativas": negativas, "fontes_sha256": hashes,
                "replay_sha256": hashlib.sha256(replay.read_bytes()).hexdigest() if replay else "",
                "limite": "Composição instalada sem reproduzir voz, USB ou conversa na interface."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--modelo", action="store_true")
    parser.add_argument("--oled", action="store_true")
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--expressoes", action="store_true")
    args = parser.parse_args()
    dados = coletar(modelo=args.modelo, oled=args.oled, replay=args.replay, expressoes=args.expressoes)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.__stdout__.write("SOCIAL_RECEIPT " + str(args.saida.resolve()) + "\n")
