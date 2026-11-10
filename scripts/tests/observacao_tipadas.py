"""Exportação de observações de teste; nunca devolve credenciais ao runtime."""
from __future__ import annotations

from pathlib import Path
import textwrap
from typing import Any


def projetar_tipo_observado(valor: Any) -> dict[str, Any]:
    """Allowlist explícita; um tipo novo exige revisar seu contrato."""
    from mente_laylay.cognicao.fonte_capacidades_turno import FonteCapacidadesTurno
    from mente_laylay.cognicao.referencias_linguagem import PerspectivaEnunciador

    if type(valor) in (FonteCapacidadesTurno, PerspectivaEnunciador):
        return {'tipo_observado': type(valor).__name__, 'projecao': valor.para_prompt()}
    raise TypeError(f"Tipo não previsto na observação: {type(valor).__name__}")


def isolar_codigo_observado(codigo: str, perfil: Path) -> str:
    """Reutiliza o isolamento privado existente antes de importar a aplicação."""
    from scripts.tests.instalacao_privada import isolar_base_do_codigo

    abertura = textwrap.dedent('''
        import importlib.abc, importlib.machinery, importlib.util
        import os, sys
        from pathlib import Path
        from types import ModuleType
        raiz = Path.cwd()
        perfil = Path(PERFIL_OBSERVADO)
        os.environ.update(TMP=str(perfil), TEMP=str(perfil))
        import tempfile
        tempfile.tempdir = str(perfil)
        apps = ModuleType('AppOpener')
        apps.open = apps.close = lambda *args, **kwargs: False
        apps.give_appnames = lambda *args, **kwargs: {}
        sys.modules['AppOpener'] = apps
        fonte = (raiz/'laylay.py').read_bytes()
        class Loader(importlib.machinery.SourceFileLoader):
            def get_code(self,nome):return compile(fonte,self.path,'exec')
        class Finder(importlib.abc.MetaPathFinder):
            def find_spec(self,nome,path=None,target=None):
                if nome=='laylay':
                    return importlib.util.spec_from_loader(nome,Loader(nome,str(raiz/'laylay.py')))
        sys.meta_path.insert(0,Finder())
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        root = preparar_instalacao_isolada(perfil/'simulada')
        root._voz_runtime.falar = lambda *args, **kwargs: False
        exec(CODIGO_OBSERVADO)
        sys.__stdout__.write('')
    ''').replace('PERFIL_OBSERVADO', repr(str(perfil)))
    abertura = isolar_base_do_codigo(abertura, variavel_fonte='fonte')
    return abertura.replace('CODIGO_OBSERVADO', repr(codigo))
