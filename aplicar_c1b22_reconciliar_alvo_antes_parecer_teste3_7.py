#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# C1-B2.2 production patcher. No git add/commit/push/reset/restore/checkout.

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime

HEAD = "eb71185c19d3727292d60be13abf0b4417f18581"
TARGET = "mente_laylay/cognicao/orquestrador_turno_runtime.py"
TEST_NEW = "tests/test_regressao_c1b22_turno155_parecer_alvo_resolvido.py"

BLOBS = {
    "mente_laylay/autonomia/roteador_deterministico.py": "46ab5da3aa94fdcf43d042f24e2f46f45e410ade",
    "mente_laylay/autonomia/coordenador_intencao.py": "09431feecd3d083afc509770a4918e59d2111add",
    "mente_laylay/autonomia/comandos_imediatos.py": "27706613cb505219479664a664db038cac78c037",
    "mente_laylay/cognicao/modalidade_turno.py": "80ddf3ac498cb9cf2cfdbb7d74e0e770d2d9e241",
    "mente_laylay/cognicao/arbitro_turno.py": "7756a15a8538291a118f8b4f3ab900157fa10927",
    "mente_laylay/cognicao/orquestrador_turno_runtime.py": "5ea518bb9ad55316ad776c6c7f9ffe2bfe06dd9c",
    "mente_laylay/cognicao/retrato_turno.py": "c2a536c1351b02c9bca399d50d1d7862ed1a6b53",
    "mente_laylay/cognicao/plano_turno.py": "a5aa5294ca813f4f78368ff6d4ca6f1ee8874113",
    "mente_laylay/cognicao/composicao_turno.py": "133bb7d1d7aa7b2e2d61ac4ae6f40db5559b276f",
    "mente_laylay/cognicao/contratos_turno.py": "21aea640ffa188abfe5432888a6d3608d2778e35",
    "mente_laylay/especialistas/operacional.py": "2ee4bbdeedd139f9b98e3611fc13442114c3835c",
    "mente_laylay/especialistas/coordenador.py": "3dd436b789d774ce72030645622d95722faabebf",
    "mente_laylay/especialistas/capacidades.py": "bfc031833b46d650fb6cc6cf4e07d44150c26710",
    "mente_laylay/integracao/composicao_entrada_interacao.py": "752727272b6ffe5e97f0ab34a1b8fa2e04004fb7",
    "mente_laylay/memoria_mental/compatibilidade_contexto.py": "768944f808002d8c24f697c0b2769a31d536eb3e",
    "mente_laylay/cognicao/decisao_turno.py": "09b0dc8536eeef8ccd32d8a30165b6a9c32b71d9",
    "mente_laylay/autonomia/roteador_intencao.py": "570cfbec2adae8be4a795e70b5d90512ff944901",
    "tests/test_regressao_c1b_turno155_maximiza_eliptico.py": "b77189f1369e7e33e6b841c46cd53b49910dadd8",
    "tests/test_regressao_c1_turno159_buffer_operacional.py": "88679011a03c34b21e1cdd1871da542fe927f4a4",
}
FOCUSED = (
    "tests/test_regressao_c1b_turno155_maximiza_eliptico.py",
    "tests/test_regressao_c1_turno159_buffer_operacional.py",
)

EXPECTED_BASELINE_FAILURES = ['tests/test_regressoes_roteiro_117_turnos_20260814.py::test_leia_conteudo_dele_e_novamente_usa_leitura_local_segura', 'tests/test_regressoes_roteiro_117_turnos_20260814.py::test_porta_prioritaria_entrega_continuacoes_ao_executor_antes_de_arquivo_e_llm[Abre o primeiro resultado.-comando0]', 'tests/test_regressoes_roteiro_117_turnos_20260814.py::test_porta_prioritaria_entrega_continuacoes_ao_executor_antes_de_arquivo_e_llm[Deixa ela azul.-comando4]', 'tests/test_regressoes_roteiro_117_turnos_20260814.py::test_porta_prioritaria_entrega_continuacoes_ao_executor_antes_de_arquivo_e_llm[Vai para a pr\\xf3xima faixa.-comando2]', 'tests/test_regressoes_roteiro_117_turnos_20260814.py::test_porta_prioritaria_entrega_continuacoes_ao_executor_antes_de_arquivo_e_llm[Volta para a aba anterior.-comando1]', 'tests/test_regressoes_roteiro_117_turnos_20260814.py::test_porta_prioritaria_entrega_continuacoes_ao_executor_antes_de_arquivo_e_llm[Volta para a faixa anterior.-comando3]', 'tests/test_retrato_arbitro_inteligente.py::test_comentario_sobre_jogo_nao_herda_comando_de_musica']
SHA_BEFORE = "2d9315177f905bf4b7c3036cbcaafc7a11c9c8095616c75f5fe84efbf71d8711"
SHA_AFTER = "8cb5b5573de06fa20fc79c8439fc4794d65a1b40e9fd8f47d6c1b704212d4e1d"
DIFF_AUDITED_ARTIFACT_SHA = "29ddf1d20d26b98f4e496c21dd1d4ccda6ef0364ea067cb9ee4b8d8d84318903"
DIFF_AUDITED_NORMALIZED_SHA = "eed8004e132a0306211e448e5efdf6540d0d3c4d7ec3c754bc1d76c0c546716b"
COMBINED_DIFF_NORMALIZED_SHA = "8b4366cca2499c7854baedf4e7009d15085c8500c32b50ce2b8fb61bf88a7c01"

HELPER = 'def reconciliar_alvo_eliptico_janela_confirmado(texto: str, *, turno: dict, retrato: dict, mente: dict) -> tuple[dict, dict]:\n    """Resolve somente o alvo contextual comprovado do `maximiza` exato.\n\n    Não cria autoridade. A ação precisa já estar autorizada e o mesmo app\n    precisa existir simultaneamente em `ultimo_app_janela` e na entidade app\n    congelada do retrato.\n    """\n    leitura = dict(turno or {})\n    snapshot = dict(retrato or {})\n    forma = str(texto or "").casefold().strip(" \\t\\r\\n.,!?;:")\n    if forma != "maximiza":\n        return leitura, snapshot\n    if not bool(leitura.get("autoriza_execucao")):\n        return leitura, snapshot\n    if not bool(leitura.get("requer_esclarecimento")):\n        return leitura, snapshot\n    ultimo_app = str(dict(mente or {}).get("ultimo_app_janela") or "").strip()\n    entidade_app = dict(dict(snapshot.get("entidades") or {}).get("app") or {})\n    nome_app = str(entidade_app.get("nome") or "").strip()\n    if not ultimo_app or not nome_app:\n        return leitura, snapshot\n    if ultimo_app.casefold() != nome_app.casefold():\n        return leitura, snapshot\n    referencia = dict(entidade_app)\n    snapshot["referencia_tipo"] = "app"\n    snapshot["referencia_resolvida"] = referencia\n    leitura["requer_esclarecimento"] = False\n    leitura["depende_contexto"] = True\n    leitura["referencia_resolvida"] = referencia\n    leitura["alvo_contextual_resolvido"] = {\n        "tipo": "app", "nome": nome_app,\n        "origem": "elipse_operacional_maximiza_confirmada",\n    }\n    return leitura, snapshot'
TEST_CONTENT = '# -*- coding: utf-8 -*-\n"""Regressão permanente C1-B2.2 — alvo elíptico resolvido antes do parecer."""\n\nfrom copy import deepcopy\nimport re,time,pytest\nfrom mente_laylay.autonomia.coordenador_intencao import resolver_intencao\nfrom mente_laylay.autonomia.roteador_deterministico import detectar_janela_contextual\nfrom mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno\nfrom mente_laylay.cognicao.orquestrador_turno_runtime import reconciliar_alvo_eliptico_janela_confirmado\nfrom mente_laylay.cognicao.plano_turno import planejar_turno\nfrom mente_laylay.cognicao.retrato_turno import construir_retrato_turno\nfrom mente_laylay.especialistas.operacional import construir_parecer_operacional\nfrom mente_laylay.memoria_mental.compatibilidade_contexto import texto_depende_de_contexto as dep_rt\n\ndef norm(t): return re.sub(r"\\s+"," ",str(t or "").casefold()).strip(" .,!?:;")\ndef dep(t): return bool(dep_rt(t,norm))\ndef estado(app=\'opera\',ent=\'opera\'):\n    a=time.time(); e={"ultimo_app_janela":app,"focos_por_dominio":{}}\n    if ent: e[\'focos_por_dominio\'][\'app\']={"tipo":"janela","alvo":ent,"topico":ent,"habilidade":"janela","intencao":"APP_OPEN","texto":"Abre o Opera.","resposta":"ja_aberto_focado","ts":a}\n    return e,a\n\ndef prep(texto=\'maximiza\',app=\'opera\',ent=\'opera\'):\n    e,a=estado(app,ent); t=classificar_modalidade_turno(texto); r,_=construir_retrato_turno(texto,turno=t,mente=e,contexto_perceptivo={},playlist_state={},jogo_contexto={},agora=a); return e,t,r\n\ndef ctx(turno,retrato,candidato,trilha):\n    return {"normalizar_texto":norm,"refinar_contexto_mental":lambda _t:None,"turno_atual":deepcopy(turno),"retrato_turno_atual":deepcopy(retrato),"extrair_agendamento":lambda _t:None,"extrair_acao_agendada":lambda _t:None,"texto_cancela_acao_agora":lambda _t:False,"texto_depende_de_contexto":dep,"continuidade_geral":{},"detectar_intencao_deterministica":lambda _t:deepcopy(candidato),"limpar_nome_playlist":lambda v:str(v or \'\').strip(),"musica_estado_get":lambda _k,default=\'\':default,"resolver_comando_midia_contextual_forcado":lambda _t:None,"resolver_comando_contextual_forcado":lambda _t:None,"resolver_comando_acao_geral_contextual_forcado":lambda _t:None,"resolver_repeticao_ultima_acao":lambda _t:None,"tentar_intencao_ai_primeiro":lambda _t:None,"texto_parece_consulta_operacional":lambda _t:True,"registrar_arbitragem_turno":lambda _t,a:trilha.append(deepcopy(a)),"pendencia_agenda":{},"pendencia_acao":{},"pendencia_acao_runtime":None,"lembrete_pendente":False}\n\ndef test_exato_reconcilia_sem_criar_autoridade():\n    e,t,r=prep(); assert t[\'autoriza_execucao\'] is True and t[\'requer_esclarecimento\'] is True\n    t2,r2=reconciliar_alvo_eliptico_janela_confirmado(\'maximiza\',turno=t,retrato=r,mente=e)\n    assert t2[\'autoriza_execucao\'] is True and t2[\'requer_esclarecimento\'] is False\n    assert r2[\'referencia_tipo\']==\'app\' and r2[\'referencia_resolvida\'][\'nome\']==\'opera\'\n\n@pytest.mark.parametrize(\'texto\',[\'maximizar\',\'maximize\',\'maximiza ele\',\'não maximiza\',\'abre\',\'fecha\',\'esquerda\',\'direita\'])\ndef test_nao_generaliza(texto):\n    e,_,r=prep(); t=classificar_modalidade_turno(texto); antes=(deepcopy(t),deepcopy(r)); assert reconciliar_alvo_eliptico_janela_confirmado(texto,turno=t,retrato=r,mente=e)==antes\n\ndef test_sem_app_nao_reconcilia():\n    e,t,r=prep(app=\'\',ent=\'\'); t2,r2=reconciliar_alvo_eliptico_janela_confirmado(\'maximiza\',turno=t,retrato=r,mente=e); assert t2[\'requer_esclarecimento\'] is True and r2[\'referencia_resolvida\']=={}\n\ndef test_mismatch_nao_reconcilia():\n    e,t,r=prep(app=\'opera\',ent=\'chrome\'); t2,_=reconciliar_alvo_eliptico_janela_confirmado(\'maximiza\',turno=t,retrato=r,mente=e); assert t2[\'requer_esclarecimento\'] is True\n\ndef test_site_only_nao_reconcilia():\n    e,a=estado(app=\'\',ent=\'\')\n    e[\'focos_por_dominio\'][\'site\']={\'tipo\':\'site\',\'alvo\':\'wikipedia\',\'topico\':\'wikipedia\',\'ts\':a}\n    t=classificar_modalidade_turno(\'maximiza\')\n    r,_=construir_retrato_turno(\'maximiza\',turno=t,mente=e,contexto_perceptivo={},playlist_state={},jogo_contexto={},agora=a)\n    t2,r2=reconciliar_alvo_eliptico_janela_confirmado(\'maximiza\',turno=t,retrato=r,mente=e)\n    assert t2[\'requer_esclarecimento\'] is True\n    assert r2.get(\'referencia_resolvida\')=={}\n\ndef test_autoridade_falsa_nao_e_promovida():\n    e,t,r=prep()\n    t=deepcopy(t); t[\'autoriza_execucao\']=False\n    t2,r2=reconciliar_alvo_eliptico_janela_confirmado(\'maximiza\',turno=t,retrato=r,mente=e)\n    assert t2[\'autoriza_execucao\'] is False\n    assert t2[\'requer_esclarecimento\'] is True\n    assert r2.get(\'referencia_resolvida\')=={}\n\ndef test_end_to_end_coordenador_e_contrato():\n    e,t,r=prep(); t,r=reconciliar_alvo_eliptico_janela_confirmado(\'maximiza\',turno=t,retrato=r,mente=e)\n    p=construir_parecer_operacional(\'maximiza\',turno=t,retrato=r); assert p[\'autoriza_execucao\'] is True and p[\'requer_esclarecimento\'] is False\n    t[\'especialistas\']={\'operacional\':p}\n    c=detectar_janela_contextual(\'maximiza\',params_cb=lambda **kw:kw,estado_mental=e,texto_depende_de_contexto=dep)\n    trilha=[]; res=resolver_intencao(\'maximiza\',\'candidate\',ctx(t,r,c,trilha)); assert res==({\'intent\':\'MAXIMIZE_WINDOW\',\'params\':{\'nome_app\':\'opera\'}},\'deterministico-explicito\')\n    contrato=trilha[-1][\'contrato_decisao\']; assert contrato[\'permite_acao\'] is True and contrato[\'requer_esclarecimento\'] is False and contrato[\'intencao\']==\'MAXIMIZE_WINDOW\'\n\n\ndef test_segmento_preserva_leitura_original_mas_contrato_top_level_usa_alvo_resolvido():\n    e,t,r=prep()\n    assert t[\'segmentos\'][0][\'requer_esclarecimento\'] is True\n    t2,_=reconciliar_alvo_eliptico_janela_confirmado(\'maximiza\',turno=t,retrato=r,mente=e)\n    assert t2[\'segmentos\'][0][\'requer_esclarecimento\'] is True\n    assert t2[\'requer_esclarecimento\'] is False\n    plano=planejar_turno(\'maximiza\',turno=t2,mente=e)\n    contrato=dict(plano.get(\'decisao_turno\') or {})\n    assert plano[\'autoriza_execucao\'] is True\n    assert contrato[\'permite_acao\'] is True\n    assert contrato[\'requer_esclarecimento\'] is False\n'


def run(cmd, cwd, *, text=True):
    return subprocess.run(
        [str(x) for x in cmd],
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
        encoding="utf-8" if text else None,
        errors="replace" if text else None,
    )


def git(repo, *args, text=True, check=True):
    p = run(["git", *args], repo, text=text)
    if check and p.returncode:
        so = p.stdout if text else p.stdout.decode("utf-8", "replace")
        se = p.stderr if text else p.stderr.decode("utf-8", "replace")
        raise RuntimeError(f"git {' '.join(args)} falhou rc={p.returncode}:\n{so}\n{se}")
    return p


def sha(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def nul_paths(raw):
    return [x.decode("utf-8", "replace") for x in raw.split(b"\0") if x]


def unstaged(repo):
    return set(nul_paths(git(repo, "diff", "--name-only", "-z", text=False).stdout))


def staged(repo):
    return set(nul_paths(git(repo, "diff", "--cached", "--name-only", "-z", text=False).stdout))


def untracked(repo):
    return set(nul_paths(git(repo, "ls-files", "--others", "--exclude-standard", "-z", text=False).stdout))


def blob(repo, rel):
    bits = git(repo, "ls-tree", "HEAD", "--", rel).stdout.strip().split()
    if len(bits) < 3:
        raise RuntimeError(f"ausente no HEAD: {rel}")
    return bits[2]


def canonical(repo, rel):
    return bytes(git(repo, "show", f"HEAD:{rel}", text=False).stdout)


def diff_bytes(repo, rel):
    return bytes(git(repo, "diff", "--binary", "--", rel, text=False).stdout)


def snapshot_diffs(repo, paths):
    return {p: sha(diff_bytes(repo, p)) for p in sorted(paths)}


def assert_preserved(repo, pre_paths, pre_sha, *, target_expected):
    current = unstaged(repo)
    expected = set(pre_paths)
    if target_expected:
        expected.add(TARGET)
    if current != expected:
        raise RuntimeError(
            f"tracked alterados divergiram: esperado={sorted(expected)} observado={sorted(current)}"
        )
    if staged(repo):
        raise RuntimeError(f"staging deixou de estar vazio: {sorted(staged(repo))}")
    for rel in sorted(pre_paths):
        got = sha(diff_bytes(repo, rel))
        if got != pre_sha[rel]:
            raise RuntimeError(f"diff preexistente mudou: {rel}")


def pytest_python(repo):
    cand = []
    if os.name == "nt":
        cand += [repo/".venv314"/"Scripts"/"python.exe", repo/".venv"/"Scripts"/"python.exe"]
    else:
        cand += [repo/".venv314"/"bin"/"python", repo/".venv"/"bin"/"python"]
    cand.append(Path(sys.executable))
    for p in cand:
        if p.exists():
            q = run([p, "-m", "pytest", "--version"], repo)
            if q.returncode == 0:
                return str(p), (q.stdout + q.stderr).strip()
    raise RuntimeError("pytest indisponível")


def suite_turno(repo):
    pats = ("tests/test_*turno*.py", "tests/test_*retrato*.py", "tests/test_*especialista*.py")
    files = []
    for pat in pats:
        files.extend(repo.glob(pat))
    return sorted({
        p.relative_to(repo).as_posix()
        for p in files
        if p.is_file() and p.relative_to(repo).as_posix() != TEST_NEW
    })


def failed_nodeids(output):
    out = []
    for line in str(output or "").splitlines():
        line = line.strip()
        if not line.startswith("FAILED "):
            continue
        nodeid = line[7:].strip()
        if " - " in nodeid:
            nodeid = nodeid.split(" - ", 1)[0].strip()
        if nodeid:
            out.append(nodeid)
    return sorted(set(out))


def summary(output):
    m = re.search(r"(?:(?P<failed>\d+) failed,\s*)?(?P<passed>\d+) passed", str(output or ""), re.I)
    if not m:
        return {"failed": None, "passed": None}
    return {"failed": int(m.group("failed") or 0), "passed": int(m.group("passed") or 0)}


def transform(canonical_before):
    if b"\r\n" in canonical_before:
        raise RuntimeError("blob canônico com CRLF inesperado")
    before = canonical_before.decode("utf-8")

    a1 = "    return resultado\n\n_ORIGENS_ENTRADA_VALIDAS = {"
    if before.count(a1) != 1:
        raise RuntimeError(f"âncora helper divergente: {before.count(a1)}")
    after = before.replace(
        a1,
        "    return resultado\n\n" + HELPER + "\n\n_ORIGENS_ENTRADA_VALIDAS = {",
        1,
    )

    a2 = (
        "    retrato_turno, entidades_recentes = ns['_construir_retrato_turno_mente']"
        "(texto_cognitivo, turno=turno, mente=mente_antes_turno, "
        "contexto_perceptivo=ns['_obter_contexto_perceptivo'](), "
        "playlist_state=ns['playlist_state'], jogo_contexto=jogo_contexto)\n"
        "    atualidade_factual = dict(retrato_turno.get('atualidade_factual') or {})"
    )
    if after.count(a2) != 1:
        raise RuntimeError(f"âncora reconciliação divergente: {after.count(a2)}")
    r2 = (
        "    retrato_turno, entidades_recentes = ns['_construir_retrato_turno_mente']"
        "(texto_cognitivo, turno=turno, mente=mente_antes_turno, "
        "contexto_perceptivo=ns['_obter_contexto_perceptivo'](), "
        "playlist_state=ns['playlist_state'], jogo_contexto=jogo_contexto)\n"
        "    turno, retrato_turno = reconciliar_alvo_eliptico_janela_confirmado(\n"
        "        texto_cognitivo, turno=turno, retrato=retrato_turno, mente=mente_antes_turno,\n"
        "    )\n"
        "    atualidade_factual = dict(retrato_turno.get('atualidade_factual') or {})"
    )
    after = after.replace(a2, r2, 1)

    udiff = "".join(difflib.unified_diff(
        before.splitlines(True),
        after.splitlines(True),
        fromfile=f"a/{TARGET}",
        tofile=f"b/{TARGET}",
    ))
    return after.encode("utf-8"), udiff


def preserve_newlines(work_before, canonical_after):
    crlf = work_before.count(b"\r\n")
    lf = work_before.count(b"\n")
    return canonical_after.replace(b"\n", b"\r\n") if crlf > 0 and crlf == lf else canonical_after


def newfile_diff():
    return "".join(difflib.unified_diff(
        [],
        TEST_CONTENT.splitlines(True),
        fromfile="/dev/null",
        tofile=f"b/{TEST_NEW}",
    ))


def self_test():
    sample = "FAILED tests/a.py::test_a - x\nFAILED tests/b.py::test_b\n2 failed, 7 passed in 0.1s\n"
    assert failed_nodeids(sample) == ["tests/a.py::test_a", "tests/b.py::test_b"]
    assert summary(sample) == {"failed": 2, "passed": 7}
    compile(TEST_CONTENT, TEST_NEW, "exec")
    assert preserve_newlines(b"a\r\n", b"b\n") == b"b\r\n"
    assert preserve_newlines(b"a\n", b"b\n") == b"b\n"
    assert re.fullmatch(r"[0-9a-f]{40}", HEAD)
    assert all(re.fullmatch(r"[0-9a-f]{40}", x) for x in BLOBS.values())
    assert re.fullmatch(r"[0-9a-f]{64}", DIFF_AUDITED_ARTIFACT_SHA)
    assert re.fullmatch(r"[0-9a-f]{64}", DIFF_AUDITED_NORMALIZED_SHA)
    assert re.fullmatch(r"[0-9a-f]{64}", COMBINED_DIFF_NORMALIZED_SHA)
    assert len(EXPECTED_BASELINE_FAILURES) == 7
    assert len(set(EXPECTED_BASELINE_FAILURES)) == 7
    test_tree = __import__("ast").parse(TEST_CONTENT)
    funcs = [n for n in test_tree.body if isinstance(n, __import__("ast").FunctionDef) and n.name.startswith("test_")]
    assert len(funcs) == 8
    assert "test_segmento_preserva_leitura_original_mas_contrato_top_level_usa_alvo_resolvido" in {n.name for n in funcs}
    print("SELF-TEST PASS")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Aplica C1-B2.2 com rollback e auditoria.")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()

    repo = Path(args.repo).resolve()
    if not (repo/".git").exists():
        raise SystemExit("--repo deve apontar para a raiz Git")

    lines = []
    def emit(s=""):
        print(s); lines.append(s)

    emit("C1-B2.2 — PATCH DE PRODUÇÃO / TESTE 3.7")
    emit("="*76)
    emit(f"HEAD travado: {HEAD}")

    root = repo.parent/"laylay_patch_artifacts_c1b22"/datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    root.mkdir(parents=True, exist_ok=False)
    backup = root/"backup"; backup.mkdir()
    logp = root/"log_patch_c1b22_reconciliar_alvo.txt"
    manp = root/"manifest_patch_c1b22_reconciliar_alvo.json"
    diffp = root/"diff_patch_c1b22_reconciliar_alvo.diff"
    backp = backup/"orquestrador_turno_runtime.py.before"

    man = {
        "schema": 1,
        "status": "preflight",
        "expected_head": HEAD,
        "expected_blobs": dict(BLOBS),
        "production_written": False,
        "permanent_test_written": False,
        "rollback_executed": False,
        "executor_called": False,
        "artifacts": {"log": str(logp), "manifest": str(manp), "diff": str(diffp), "backup": str(backp)},
    }

    target = repo/TARGET
    testp = repo/TEST_NEW
    old_work = None
    wrote_target = False
    wrote_test = False
    pre_paths = set()
    pre_sha = {}
    untracked_before = set()

    try:
        head = git(repo, "rev-parse", "HEAD").stdout.strip()
        man["head_observed"] = head
        if head != HEAD:
            raise RuntimeError(f"HEAD divergente: {head} != {HEAD}")
        if staged(repo):
            raise RuntimeError(f"staging não está vazio: {sorted(staged(repo))}")

        bad = {k:v for k,v in BLOBS.items() if not re.fullmatch(r"[0-9a-f]{40}", v)}
        if bad:
            raise RuntimeError(f"locks inválidos no patcher: {bad}")
        observed = {}
        for rel, exp in BLOBS.items():
            got = blob(repo, rel); observed[rel] = got
            if got != exp:
                raise RuntimeError(f"blob divergente {rel}: observado={got} esperado={exp}")
        man["blobs_observed"] = observed
        emit("preflight HEAD/blobs ........................ PASS")

        pre_paths = unstaged(repo)
        if TARGET in pre_paths:
            raise RuntimeError(f"target já está modificado: {TARGET}")
        untracked_before = untracked(repo)
        if TEST_NEW in untracked_before or testp.exists():
            raise RuntimeError(f"teste permanente já existe: {TEST_NEW}")
        if git(repo, "ls-files", "--error-unmatch", TEST_NEW, check=False).returncode == 0:
            raise RuntimeError(f"teste permanente já é tracked: {TEST_NEW}")
        pre_sha = snapshot_diffs(repo, pre_paths)
        man["preexisting_tracked_paths"] = sorted(pre_paths)
        man["preexisting_diff_sha256"] = dict(pre_sha)
        man["untracked_before"] = sorted(untracked_before)

        before = canonical(repo, TARGET)
        if sha(before) != SHA_BEFORE:
            raise RuntimeError(f"SHA canônico before divergente: {sha(before)}")
        old_work = target.read_bytes()
        backp.write_bytes(old_work)

        after, audiff = transform(before)
        if sha(after) != SHA_AFTER:
            raise RuntimeError(f"SHA canônico after divergente: {sha(after)}")
        if sha(audiff) != DIFF_AUDITED_NORMALIZED_SHA:
            raise RuntimeError(
                "diff normalizado LF não é o candidato auditado: "
                f"{sha(audiff)} != {DIFF_AUDITED_NORMALIZED_SHA}"
            )
        man["candidate_diff_sha256_normalized_lf"] = sha(audiff)
        man["candidate_diff_artifact_sha256_original_crlf"] = DIFF_AUDITED_ARTIFACT_SHA
        man["target_sha256_before"] = sha(before)
        man["target_sha256_after_expected"] = sha(after)
        man["permanent_test_sha256_expected"] = sha(TEST_CONTENT)
        compile(TEST_CONTENT, TEST_NEW, "exec")
        emit("candidato byte-idêntico ao diff auditado ....... PASS")

        py, pyver = pytest_python(repo)
        man["pytest_python"] = py
        man["pytest_version"] = pyver

        fb = run([py, "-m", "pytest", "-q", *FOCUSED], repo)
        fbo = (fb.stdout+fb.stderr).strip()
        man["baseline_focused"] = {"rc": fb.returncode, "output": fbo}
        if fb.returncode or "26 passed" not in fbo:
            raise RuntimeError("baseline C1-A/C1-B não está 26/26:\n"+fbo)
        emit("baseline C1-A + C1-B ....................... PASS (26/26)")

        suite = suite_turno(repo)
        dirty_suite = sorted(set(suite) & pre_paths)
        if dirty_suite:
            raise RuntimeError(
                "arquivo(s) da suíte ampla possuem alteração local; baseline diferencial recusado: "
                + ", ".join(dirty_suite)
            )
        bb = run([py, "-m", "pytest", "-q", *suite], repo)
        bbo = (bb.stdout+bb.stderr).strip()
        if bb.returncode not in (0,1):
            raise RuntimeError("suite baseline teve erro de infraestrutura:\n"+bbo)
        base_fail = failed_nodeids(bbo)
        if base_fail != EXPECTED_BASELINE_FAILURES:
            raise RuntimeError(
                "fingerprint vermelho do baseline 3.7 divergiu do candidato auditado: "
                f"esperado={EXPECTED_BASELINE_FAILURES!r} observado={base_fail!r}"
            )
        man["baseline_broad"] = {
            "files": suite, "rc": bb.returncode, "summary": summary(bbo),
            "failed_nodeids": base_fail, "expected_failed_nodeids": EXPECTED_BASELINE_FAILURES,
            "output": bbo
        }
        emit(f"baseline suite ampla ........................ PASS (7 débitos exatos congelados)")

        assert_preserved(repo, pre_paths, pre_sha, target_expected=False)
        if untracked(repo) != untracked_before:
            raise RuntimeError("baseline tests alteraram untracked não ignorados")

        target.write_bytes(preserve_newlines(old_work, after)); wrote_target = True
        testp.write_text(TEST_CONTENT, encoding="utf-8", newline="\n"); wrote_test = True
        man["production_written"] = True
        man["permanent_test_written"] = True

        assert_preserved(repo, pre_paths, pre_sha, target_expected=True)
        expected_untracked = set(untracked_before)|{TEST_NEW}
        if untracked(repo) != expected_untracked:
            raise RuntimeError("untracked pós-escrita divergiu")

        if sha(target.read_bytes().replace(b"\r\n",b"\n")) != SHA_AFTER:
            raise RuntimeError("target escrito não corresponde ao candidato")
        if sha(testp.read_bytes()) != sha(TEST_CONTENT):
            raise RuntimeError("teste permanente escrito divergiu")

        pc = run([py, "-m", "py_compile", TARGET, TEST_NEW], repo)
        if pc.returncode:
            raise RuntimeError("py_compile falhou:\n"+pc.stdout+pc.stderr)
        emit("py_compile produção + teste .................. PASS")

        nr = run([py, "-m", "pytest", "-q", TEST_NEW], repo)
        nro = (nr.stdout+nr.stderr).strip()
        man["permanent_regression"] = {"rc": nr.returncode, "output": nro}
        if nr.returncode or "15 passed" not in nro:
            raise RuntimeError("regressão permanente não ficou 15/15:\n"+nro)
        emit("regressão permanente C1-B2.2 ............... PASS (15/15)")

        fa = run([py, "-m", "pytest", "-q", *FOCUSED], repo)
        fao = (fa.stdout+fa.stderr).strip()
        man["focused_after"] = {"rc": fa.returncode, "output": fao}
        if fa.returncode or "26 passed" not in fao:
            raise RuntimeError("C1-A/C1-B regrediram:\n"+fao)
        emit("C1-A + C1-B após patch ..................... PASS (26/26)")

        ba = run([py, "-m", "pytest", "-q", *suite], repo)
        bao = (ba.stdout+ba.stderr).strip()
        if ba.returncode not in (0,1):
            raise RuntimeError("suite pós-patch teve erro de infraestrutura:\n"+bao)
        after_fail = failed_nodeids(bao)
        new = sorted(set(after_fail)-set(base_fail))
        missing = sorted(set(base_fail)-set(after_fail))
        man["broad_after"] = {
            "files": suite, "rc": ba.returncode, "summary": summary(bao),
            "failed_nodeids": after_fail, "new_failures_vs_baseline": new,
            "missing_failures_vs_baseline": missing,
            "same_failure_fingerprint": after_fail == base_fail,
            "output": bao,
        }
        if new or missing or after_fail != base_fail:
            raise RuntimeError(f"fingerprint amplo mudou: novos={new} ausentes={missing}")
        emit(f"suite ampla diferencial ..................... PASS ({len(after_fail)} débitos; 0 novos)")

        assert_preserved(repo, pre_paths, pre_sha, target_expected=True)
        if untracked(repo) != expected_untracked:
            raise RuntimeError("testes alteraram untracked não ignorados")

        combined = audiff + newfile_diff()
        combined_sha = sha(combined)
        if combined_sha != COMBINED_DIFF_NORMALIZED_SHA:
            raise RuntimeError(
                "diff combinado normalizado divergiu do patch congelado: "
                f"{combined_sha} != {COMBINED_DIFF_NORMALIZED_SHA}"
            )
        diffp.write_text(combined, encoding="utf-8", newline="\n")
        if sha(diffp.read_bytes()) != COMBINED_DIFF_NORMALIZED_SHA:
            raise RuntimeError("arquivo diff combinado sofreu tradução inesperada de newline")
        man["combined_diff_sha256"] = sha(diffp.read_bytes())
        man["permanent_test_sha256"] = sha(testp.read_bytes())
        man["git_status_after"] = git(repo, "status", "--short").stdout.splitlines()
        man["preexisting_preserved"] = True
        man["staging_empty"] = not bool(staged(repo))
        man["status"] = "patch_applied_tests_green_pending_real_chaos"

        emit("")
        emit("✅ C1-B2.2 PATCH APLICADO E REGRESSÕES VERDES")
        emit("produção alterada: SIM — somente orquestrador_turno_runtime.py")
        emit("regressão permanente criada: SIM")
        emit("autoridade criada pelo contexto: NÃO")
        emit("tracked preexistente preservado: SIM")
        emit("staging preservado vazio: SIM")
        emit("rollback executado: NÃO")
        emit("git add/commit/push: NÃO")
        emit("estado: PENDENTE DE TESTE REAL 154→155")

    except Exception as exc:
        man["status"] = "failed"
        man["error_type"] = type(exc).__name__
        man["error"] = str(exc)
        emit("")
        emit(f"❌ PATCHER RECUSOU/FALHOU: {type(exc).__name__}: {exc}")
        if wrote_target or wrote_test:
            errs = []
            try:
                if wrote_target and old_work is not None:
                    target.write_bytes(old_work)
                if wrote_test and testp.exists():
                    testp.unlink()
                man["rollback_executed"] = True
            except Exception as e:
                errs.append(f"restore bytes/test: {type(e).__name__}: {e}")
            try:
                assert_preserved(repo, pre_paths, pre_sha, target_expected=False)
            except Exception as e:
                errs.append(f"tracked: {type(e).__name__}: {e}")
            try:
                if untracked(repo) != untracked_before:
                    errs.append("untracked não retornou ao snapshot")
            except Exception as e:
                errs.append(f"untracked check: {type(e).__name__}: {e}")
            man["rollback_errors"] = errs
            man["rollback_integrity"] = not bool(errs)
            emit("rollback executado: SIM")
            emit("rollback íntegro: " + ("SIM" if not errs else "NÃO"))
            if not errs:
                man["production_written"] = False
                man["permanent_test_written"] = False
            else:
                # Não declarar restauração se qualquer verificação do rollback falhou.
                man["production_state_after_failed_rollback"] = "NAO_CONFIRMADO"
        else:
            emit("produção alterada: NÃO")
            emit("rollback executado: NÃO")
            man["production_written"] = False
            man["permanent_test_written"] = False

    finally:
        try:
            logp.write_text("\n".join(lines)+"\n", encoding="utf-8", newline="\n")
            man["artifacts_sha256"] = {
                "log": sha(logp.read_bytes()),
                "diff": sha(diffp.read_bytes()) if diffp.exists() else "",
                "backup": sha(backp.read_bytes()) if backp.exists() else "",
            }
            manp.write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
            print(f"log: {logp}")
            print(f"manifest: {manp}")
            if diffp.exists():
                print(f"diff: {diffp}")
        except Exception as e:
            print(f"⚠️ falha ao persistir artefatos: {type(e).__name__}: {e}")

    return 0 if man.get("status") == "patch_applied_tests_green_pending_real_chaos" else 2


if __name__ == "__main__":
    raise SystemExit(main())
