"""A concessão corporal acompanha a sessão confirmada, sem depender do cabo."""
import pytest
from scripts.tests.test_companhia_corporal import montar


def test_catalogo_vivo_descreve_companhia_nos_dois_canais():
    from mente_laylay.especialistas.capacidades import consultar_capacidade
    registro = consultar_capacidade('CORPO_COMPANHIA')
    assert 'USB ou Wi-Fi autenticado' in registro['limites']
    assert 'TCP autenticada' in str(registro)
    assert 'modo AUTO' in registro['identificacao_usb_condicional']


@pytest.mark.parametrize('autenticado', [True, False])
def test_preferencia_de_companhia_aceita_rede_so_apos_autenticacao(autenticado):
    _, _, rosto, corpo, _, agora = montar(automatico=True, passeio=True)
    original = rosto.diagnostico
    rosto.diagnostico = lambda: {**original(), 'transporte': 'tcp', 'canal_autenticado': autenticado}
    resultado = corpo.companhia.processar()
    assert corpo.companhia.diagnostico()['ativa'] is autenticado, resultado
    assert corpo.companhia.autorizar_busca_obstaculos(rosto.diagnostico()['sessao']) is autenticado
    if autenticado:
        c = corpo.companhia._concessao
        meta = {'concessao_id': c['id'], 'proposto_em': agora[0], 'perfil': 'bancada'}
        assert corpo.companhia._vigente(meta)
        rosto.diagnostico = lambda: {**original(), 'transporte': 'tcp', 'canal_autenticado': False}
        assert not corpo.companhia._vigente(meta)
