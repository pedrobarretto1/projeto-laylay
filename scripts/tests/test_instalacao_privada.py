"""Canário real de arquivo: isolamento não depende de confiar no executor."""
import json
from pathlib import Path
import subprocess
import sys

from tests.instalacao_privada import PREPARAR_BASE


def test_guarda_preserva_origem_externa_e_permite_somente_persistencia_privada(tmp_path):
    origem = tmp_path/'origem';origem.mkdir()
    (origem/'configuracao.env').write_text('LAYLAY_LLM_BACKEND=ollama\nSEGREDO_NAO_COPIAR=teste\n',encoding='utf8')
    canario = origem/'legado.json';canario.write_text('preservado',encoding='utf8')
    perfil = tmp_path/'perfil';perfil.mkdir()
    codigo = '''
from pathlib import Path
import json,sys,shutil
perfil,raiz=Path(sys.argv[1]),Path(sys.argv[2])
'''+PREPARAR_BASE+'''
negadas=[]
for nome,acao in [
    ('escrita',lambda:(raiz/'legado.json').write_text('mudou')),
    ('migracao',lambda:shutil.move(str(raiz/'legado.json'),str(perfil/'copiado.json'))),
    ('rede',lambda:sys.audit('socket.connect',None,('example.test',443))),
]:
    try:acao()
    except PermissionError:negadas.append(nome)
(perfil/'permitido.json').write_text('privado')
print(json.dumps({'negadas':negadas,'home':str(Path.home()),'config':(base_privada/'configuracao.env').read_text()}))
'''
    r = subprocess.run([sys.executable,'-B','-c',codigo,str(perfil),str(origem)],
        capture_output=True,text=True,timeout=15)
    assert r.returncode==0,r.stderr
    d = json.loads(r.stdout)
    assert d['negadas']==['escrita','migracao','rede']
    assert canario.read_text()=='preservado'
    assert not (perfil/'copiado.json').exists()
    assert (perfil/'permitido.json').read_text()=='privado'
    assert Path(d['home']).is_relative_to(perfil)
    assert 'SEGREDO_NAO_COPIAR' not in d['config']
