"""Isolamento de filesystem no subprocesso, sem alterar a composição fonte."""

PREPARAR_BASE = '''
# Executado antes de qualquer import da aplicação.
import os
base_privada = perfil/'base_privada'
perfil_privado = perfil/'perfil_privado'
for diretorio in (base_privada,perfil_privado,perfil_privado/'Roaming',perfil_privado/'Local'):
    diretorio.mkdir(parents=True,exist_ok=True)
os.environ.update(USERPROFILE=str(perfil_privado),APPDATA=str(perfil_privado/'Roaming'),
    LOCALAPPDATA=str(perfil_privado/'Local'),LAYLAY_IOT_MODO='simulado',
    LAYLAY_MICROFONE_ATIVO='0',LAYLAY_FALAS_INICIAIS='0',LAYLAY_BRIEFING_INICIAL='0')
assert Path.home().resolve().is_relative_to(perfil.resolve())
chaves_modelo={'LAYLAY_LLM_BACKEND','LAYLAY_LLM_BASE_URL','LAYLAY_LLM_MODEL'}
linhas=[]
for linha in (raiz/'configuracao.env').read_text(encoding='utf-8-sig').splitlines():
    chave,sep,valor=linha.strip().partition('=')
    if sep and chave in chaves_modelo:linhas.append(chave+'='+valor)
(base_privada/'configuracao.env').write_text('\\n'.join(linhas)+'\\n',encoding='utf8')
sys.path.insert(0,str(raiz))
os.chdir(base_privada)
violacoes_isolamento=[]
def conferir_destino_privado(caminho):
    if isinstance(caminho,int):return
    if str(caminho)==':memory:':return
    if os.path.normcase(str(caminho))==os.path.normcase(os.devnull):return
    if not Path(caminho).resolve().is_relative_to(perfil.resolve()):
        violacoes_isolamento.append(str(caminho))
        raise PermissionError('Persistência fora do perfil privado de teste')
def auditar_isolamento(evento,args):
    if evento in {'socket.connect','subprocess.Popen','os.system'}:
        violacoes_isolamento.append(evento)
        raise PermissionError('Efeito externo não participa desta prova')
    if evento=='open':
        modo=args[1] or ''
        flags=args[2] or 0
        if any(c in modo for c in 'wax+') or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
            conferir_destino_privado(args[0])
    if evento=='sqlite3.connect':conferir_destino_privado(args[0])
    if evento in {'os.mkdir','os.remove','os.rmdir'}:conferir_destino_privado(args[0])
    if evento in {'os.rename','shutil.move'}:
        conferir_destino_privado(args[0]);conferir_destino_privado(args[1])
sys.addaudithook(auditar_isolamento)
'''


def isolar_base_do_codigo(codigo: str, *, variavel_fonte: str = 'codigo') -> str:
    """PASTA_MEMORIA sozinha não cobre migrações, playlists nem Path.home()."""
    if variavel_fonte not in {'codigo','fonte'}:raise ValueError('fonte não prevista')
    antigo = f"def get_code(self,nome):return compile({variavel_fonte},self.path,'exec')"
    assert codigo.count(antigo)==1
    novo = f'''def get_code(self,nome):
        import ast
        arvore=ast.parse({variavel_fonte},filename=self.path)
        bases=[n for n in arvore.body if isinstance(n,ast.Assign) and
            any(isinstance(t,ast.Name) and t.id=='_base_dir' for t in n.targets)]
        assert len(bases)==1
        bases[0].value=ast.copy_location(ast.Constant(str(base_privada)),bases[0].value)
        return compile(ast.fix_missing_locations(arvore),self.path,'exec')'''
    codigo = codigo.replace(antigo,novo)
    marcador = 'from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada'
    assert codigo.count(marcador)==1
    # As strings são códigos de topo após dedent, como no factory compartilhado.
    linhas = codigo.splitlines(True)
    for i,linha in enumerate(linhas):
        if marcador in linha:
            indentacao = linha[:len(linha)-len(linha.lstrip())]
            linhas[i:i] = [indentacao+l+'\n' for l in PREPARAR_BASE.splitlines()]
            break
    codigo = ''.join(linhas)
    marcador_root = "root=preparar_instalacao_isolada(perfil/'simulada',requisicao_http=http)"
    if marcador_root not in codigo:marcador_root = "root = preparar_instalacao_isolada(perfil/'simulada')"
    assert codigo.count(marcador_root)==1
    verificacao = '''
assert Path(root._base_dir).resolve().is_relative_to(perfil.resolve())
assert Path(root.PASTA_MEMORIA).resolve().is_relative_to(perfil.resolve())
assert Path(root.playlists_state_file).resolve().is_relative_to(perfil.resolve())
assert Path(root.playlists_legacy_file).resolve().is_relative_to(perfil.resolve())
assert not violacoes_isolamento,violacoes_isolamento
'''
    # Preservar a indentação do bloco de topo da string.
    linha_root = next(l for l in codigo.splitlines() if marcador_root in l)
    espacos = linha_root[:len(linha_root)-len(linha_root.lstrip())]
    codigo = codigo.replace(linha_root,linha_root+'\n'+''.join(espacos+l+'\n' for l in verificacao.splitlines()))
    linhas_saida = [l for l in codigo.splitlines() if 'sys.__stdout__.write(' in l]
    assert len(linhas_saida)==1
    linha = linhas_saida[0]
    espacos = linha[:len(linha)-len(linha.lstrip())]
    return codigo.replace(linha,espacos+'assert not violacoes_isolamento,violacoes_isolamento\n'+linha)
