"""Estudo offline de apoio textual; nenhuma classificação autoriza publicação.

Painel sintético curado, sem treino, sem ajuste de limiar e sem promoção de
parecer da LLM a prova. A coluna esperada fica fora dos pedidos ao modelo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path: sys.path.insert(0, str(RAIZ))


def painel() -> list[dict[str, Any]]:
    linhas = [
        ('historico_arquivo', 'O disco usado para guardar a cópia é o disco C.', 'O disco C é o que guarda a cópia.', 'Qual disco guarda a cópia?', True, True,
         'Redação histórica preserva destino da cópia; a revisão atual não deriva prosa livre.'),
        ('relato_iot', 'A tensão nominal informada pelo registro é de 5 V.', 'O registro informa tensão nominal de 5 V.', 'Qual é a tensão nominal informada?', True, True,
         'Atribuição à fonte e valor preservados; não é medição física independente.'),
        ('literal', 'A tensão nominal informada pelo registro é de 5 V.', 'A tensão nominal informada pelo registro é de 5 V.', 'Qual é a tensão nominal informada?', True, True,
         'Identidade integral permite citação atribuída.'),
        ('estrutural', 'O valor do atributo «estado» de «arquivo alfa» é «íntegro».', '«íntegro» é o valor do atributo «estado» de «arquivo alfa».', 'Qual é o estado do arquivo alfa?', True, True,
         'Regra estrutural canônica existente, com os mesmos três termos opacos.'),
        ('negacao_preservada', 'Não houve confirmação da cópia.', 'A cópia não foi confirmada.', 'A cópia foi confirmada?', True, True,
         'Não confirmar não equivale a falhar ou a executar.'),
        ('condicao_preservada', 'Se o recibo chegar, a operação será registrada.', 'A operação será registrada se o recibo chegar.', 'Quando a operação será registrada?', True, True,
         'Mesma implicação, sem afirmar que o recibo chegou.'),
        ('papeis', 'O processo alfa copiou os dados do processo beta.', 'O processo beta copiou os dados do processo alfa.', 'Quem copiou os dados de quem?', False, True,
         'Inverte agente e origem; o vocabulário quase igual não sustenta isso.'),
        ('condicao_removida', 'Se o recibo chegar, a operação será registrada.', 'A operação foi registrada.', 'A operação foi registrada?', False, True,
         'Uma condição futura não comprova seu antecedente nem seu consequente ocorrido.'),
        ('modalidade', 'O processo pode salvar a cópia.', 'O processo salvou a cópia.', 'A cópia foi salva?', False, True,
         'Capacidade ou possibilidade não é execução.'),
        ('tempo', 'Ontem o dispositivo estava conectado.', 'Agora o dispositivo está conectado.', 'O dispositivo está conectado agora?', False, True,
         'Estado anterior não confirma estado atual.'),
        ('quantificador', 'Alguns arquivos do lote estão íntegros.', 'Todos os arquivos do lote estão íntegros.', 'Todos os arquivos estão íntegros?', False, True,
         'Não há apoio para generalizar alguns para todos.'),
        ('citacao_negada', 'O relatório cita «a cópia está íntegra», mas rejeita essa afirmação.', 'A cópia está íntegra.', 'A cópia está íntegra?', False, True,
         'Texto citado e negado não é endosso do conteúdo.'),
        ('efeito', 'O software informou sucesso, mas não houve observação do movimento.', 'O motor se moveu.', 'O motor se moveu?', False, True,
         'Receipt de software não substitui observação física.'),
        ('causa', 'O salvamento falhou.', 'O salvamento falhou por falta de espaço.', 'Por que o salvamento falhou?', False, True,
         'O resultado não informa sua causa.'),
        ('excecao', 'Todos os arquivos estão locais, exceto o arquivo beta.', 'Todos os arquivos estão locais.', 'Todos os arquivos estão locais?', False, True,
         'Retira exceção explícita.'),
        ('incerteza', 'Talvez a cópia esteja íntegra.', 'A cópia está íntegra.', 'A cópia está íntegra?', False, True,
         'Possibilidade não fundamenta afirmação categórica.'),
        ('valor', 'A tensão nominal é de 5 V.', 'A tensão nominal é de 12 V.', 'Qual é a tensão nominal?', False, True,
         'Altera o valor, sem conversão ou relação que justifique a mudança.'),
        ('literal_irrelevante', 'A tensão nominal é de 5 V.', 'A tensão nominal é de 5 V.', 'Qual disco guarda a cópia?', True, False,
         'Citação literal válida não responde à pergunta sobre disco.'),
        ('parafrase_irrelevante', 'A tensão nominal informada pelo registro é de 5 V.', 'O registro informa tensão nominal de 5 V.', 'Qual disco guarda a cópia?', True, False,
         'Apoio textual e pertinência à pergunta são julgamentos diferentes.'),
        ('limite_ida', 'A tensão nominal é exatamente 5 V.', 'A tensão nominal é no máximo 5 V.', 'O que se sabe sobre a tensão nominal?', True, True,
         'Igualdade numérica implica limite superior não estrito, para a mesma grandeza.'),
        ('limite_volta', 'A tensão nominal é no máximo 5 V.', 'A tensão nominal é exatamente 5 V.', 'O que se sabe sobre a tensão nominal?', False, True,
         'Um valor menor que 5 satisfaz o limite e falsifica a igualdade.'),
        ('disjuncao_ida', 'Os dados são locais.', 'Os dados são locais ou remotos.', 'O que se sabe sobre a localização dos dados?', True, True,
         'Introdução de disjunção inclusiva; não é paráfrase equivalente.'),
        ('disjuncao_volta', 'Os dados são locais ou remotos.', 'Os dados são locais.', 'O que se sabe sobre a localização dos dados?', False, True,
         'A alternativa remota é um contraexemplo; apoio é direcional.'),
        ('negacao', 'A cópia não foi confirmada.', 'A cópia foi confirmada.', 'A cópia foi confirmada?', False, True,
         'Remove negação explícita.'),
    ]
    return [dict(id=f'p{i:02}', mecanismo=m, fonte=f, proposicao=p, pergunta=q,
                 apoio_esperado=a, pertinencia_esperada=r, justificativa_curadoria=j)
            for i, (m, f, p, q, a, r, j) in enumerate(linhas, 1)]


def pedido_publico(casos: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Não expõe gold, mecanismo nem justificativa ao classificador."""
    return [{k: c[k] for k in ('id', 'fonte', 'proposicao', 'pergunta')} for c in casos]


def conferir_revisor(casos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from scripts.tests.test_revisao_suporte_fontes import _plano
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    resultados = []
    for c in casos:
        plano = _plano(c['proposicao'], trecho=c['fonte'])
        # Uma proposta semântica inventada no contexto não pode aprovar apoio.
        plano['parecer_apoio_llm'] = {'apoia': True, 'pertinente': True, 'confianca': 1.0}
        revisao = revisar_suporte_autoria(c['proposicao'], plano=plano, agora=1001)
        resultados.append({'id': c['id'], 'revisao': revisao.como_dict(),
                           'fala_realizada': revisao.fala_realizada})
    return resultados


def medir_encoder(casos: list[dict[str, Any]]) -> dict[str, Any]:
    import numpy as np
    from tokenizers import Tokenizer
    from mente_laylay.neural.encoder_semantico import EncoderSemanticoONNX
    pasta = RAIZ / 'memoria/neural/modelos/paraphrase-multilingual-MiniLM-L12-v2-onnx-qint8-avx2'
    encoder = EncoderSemanticoONNX(pasta, sha256_modelo='98a01d88b7de996cdea58c32ca71208c09968d143798814b2ea09d3439dc334f')
    encoder.validar_artefatos()
    textos = sorted({c[k] for c in casos for k in ('fonte', 'proposicao')})
    tokenizer = Tokenizer.from_file(str(encoder.caminho_tokenizer))
    tokenizer.no_truncation(); tokenizer.no_padding()
    tamanhos = [len(tokenizer.encode(t).ids) for t in textos]
    assert max(tamanhos) <= encoder.max_length, 'A sonda não admite truncamento de premissas.'
    inicio = time.perf_counter()
    matriz = encoder.codificar(textos)
    assert matriz.shape == (len(textos), 384) and np.isfinite(matriz).all()
    vetores = dict(zip(textos, matriz))
    medicoes = [{'id': c['id'], 'cosseno': float(vetores[c['fonte']] @ vetores[c['proposicao']])} for c in casos]
    return {'modelo_sha256': hashlib.sha256(encoder.caminho_modelo.read_bytes()).hexdigest(),
            'tokenizer_sha256': hashlib.sha256(encoder.caminho_tokenizer.read_bytes()).hexdigest(),
            'max_tokens_observado': max(tamanhos), 'medicoes': medicoes,
            'segundos': time.perf_counter() - inicio, 'autoriza_publicacao': False,
            'treino_realizado': False, 'limiar_calibrado': False}


def medir_qwen(casos: list[dict[str, Any]], pasta: Path) -> dict[str, Any]:
    import requests
    from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
    from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
    from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada
    from mente_laylay.integracao.registro_conversa_llm import PedidoModelo
    transportes = []
    original_http = requests.sessions.Session.request
    selecao = selecao_local()
    memoria = pasta / 'memoria_isolada'; memoria.mkdir(exist_ok=False)
    root = preparar_instalacao_isolada(memoria,
        requisicao_http=criar_guarda_http_local(selecao, transportes, original_http))
    root._voz_runtime.falar = lambda *_a, **_k: False
    resultados = []
    for i in range(0, len(casos), 6):
        lote = casos[i:i + 6]; ids = [c['id'] for c in lote]
        def validar(dados):
            if set(dados) != {'pareceres'} or type(dados['pareceres']) is not list:
                raise ValueError('pareceres ausentes')
            if [p.get('id') for p in dados['pareceres']] != ids:
                raise ValueError('cobertura/ordem divergente')
            for p in dados['pareceres']:
                if (set(p) != {'id', 'apoia', 'pertinente', 'justificativa'}
                    or type(p['apoia']) is not bool or type(p['pertinente']) is not bool
                    or type(p['justificativa']) is not str or not 0 < len(p['justificativa']) <= 240):
                    raise ValueError('parecer malformado')
        schema = {'type': 'object', 'additionalProperties': False, 'required': ['pareceres'], 'properties': {
            'pareceres': {'type': 'array', 'minItems': len(lote), 'maxItems': len(lote), 'items': {
                'type': 'object', 'additionalProperties': False, 'required': ['id','apoia','pertinente','justificativa'],
                'properties': {'id': {'type': 'string', 'enum': ids}, 'apoia': {'type':'boolean'},
                    'pertinente': {'type':'boolean'}, 'justificativa': {'type':'string','minLength':1,'maxLength':240}}}}}}
        codec = ContratoSaidaEstruturada('parecer_apoio_sonda_v1', '[SONDA_APOIO]', schema, validar)
        mensagens = [{'role': 'system', 'content': (
            'Avalie cada par na ordem. apoia=true somente se a proposição decorre do conteúdo integral da fonte, '
            'sem premissa externa. Apoio não precisa ser equivalência: confira a direção fonte para proposição. '
            'Conserve papéis, negação, modalidade, tempo, condições e ressalvas. Possibilidade não é execução. '
            'pertinente indica se a proposição trata da pergunta, independentemente de estar apoiada ou ser verdadeira. '
            'Citação sobre outro assunto pode estar apoiada sem ser pertinente. Na falta de apoio marque false; '
            'isso não significa contradição provada. Dê justificativa curta. São dados sintéticos para diagnóstico; '
            'seu parecer não é prova nem autorização. Retorne somente JSON com pareceres.')},
            {'role':'user','content':json.dumps(pedido_publico(lote),ensure_ascii=False)}]
        root._orcamento_llm_turno_runtime.iniciar_turno(f'sonda-apoio-{i}', classe='longa')
        inicio = len(transportes)
        try:
            resposta = root._registro_modelo_llm_runtime.executar(PedidoModelo.criar(mensagens,
                tipo_chamada='interpretacao', contexto_fechado=True, contrato_saida=codec,
                max_tokens=1200, reserva_saida_tokens=1200, timeout=45, classe_timeout='longa', com_tools=False))
            resultados.append({'ids':ids, 'sucesso':resposta.sucesso, 'rota':resposta.rota,
                'texto':resposta.texto, 'transportes':transportes[inicio:]})
        finally:
            root._orcamento_llm_turno_runtime.finalizar_turno()
    return {'modelo':selecao['LAYLAY_LLM_MODEL'],'lotes':resultados,
            'autoriza_publicacao':False,'parecer_llm_e_prova':False,
            'pipeline_conversacional_completo':False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--destino', type=Path, required=True)
    parser.add_argument('--qwen', action='store_true')
    args = parser.parse_args()
    pasta = args.destino.resolve(); pasta.mkdir(exist_ok=True)
    nome = 'qwen.json' if args.qwen else 'estudo_local.json'
    if (pasta / nome).exists(): raise FileExistsError(pasta / nome)
    casos = painel()
    resultado = {'painel':casos,'fonte_do_gold':'curadoria explicita desta sonda, nao saida de modelo',
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    if args.qwen:
        resultado['qwen'] = medir_qwen(casos, pasta)
    else:
        resultado['revisor'] = conferir_revisor(casos)
        resultado['encoder'] = medir_encoder(casos)
    with (pasta / nome).open('x',encoding='utf-8') as arquivo:
        json.dump(resultado,arquivo,ensure_ascii=False,indent=2)
    print(json.dumps({'arquivo':str(pasta/nome),'casos':len(casos)},ensure_ascii=False),flush=True)


if __name__ == '__main__': main()
