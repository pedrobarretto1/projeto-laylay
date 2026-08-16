#!/usr/bin/env python3
"""Instala e valida a fotografia vermelha dos contratos de arquivos/contexto.

Este patcher NAO altera producao. Ele adiciona exatamente um arquivo de testes
contra a baseline teste 3.0 e considera sucesso somente quando:
- todos os guardrails verdes passam;
- cada teste vermelho falha por AssertionError, com a contagem esperada;
- nao ha erro de importacao/coleta;
- o arquivo compila e nao possui erros de whitespace no diff.

Nenhum commit, push, stage, reset ou checkout e executado.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

PATCH_ID = "TESTES_VERMELHOS_ARQUIVOS_CONTEXTO_CAPACIDADES_20260816"
BASELINE_HEAD = "ebcaaa27b4e759757f8416bbc27133a6d85a1519"
TARGET_REL = Path("tests/test_red_contratos_arquivos_contexto_capacidades.py")
EXPECTED_SHA256 = "b9c5586d44cba1619fb9cfc21018c4864135873ed2ec50d3e7ea74c3266a6e62"
TEST_SOURCE_B64 = "IiIiRm90b2dyYWZpYSB2ZXJtZWxoYSBkb3MgY29udHJhdG9zIGRlIGFycXVpdm9zLCBjb250ZXh0byBlIGNhcGFjaWRhZGVzLgoKRXN0ZSBhcnF1aXZvIGUgZGVsaWJlcmFkYW1lbnRlIGVzY3JpdG8gY29udHJhIG8gY29tcG9ydGFtZW50byBkZXNlamFkby4KTmEgYmFzZWxpbmUgZWJjYWFhMjcgKHRlc3RlIDMuMCksIG9zIHRlc3RlcyBgYHRlc3RfcmVkX18qYGAgZGV2ZW0gZmFsaGFyCnBvciBhc3NlcmNhbyBzZW0gZXJybyBkZSBpbXBvcnRhY2FvL2NvbGV0YTsgb3MgYGB0ZXN0X2d1YXJkX18qYGAgZGV2ZW0gcGFzc2FyLgpEZXBvaXMgZG8gcGF0Y2ggZGUgcHJvZHVjYW8sIGEgbWVzbWEgYmF0ZXJpYSB2ZXJtZWxoYSBkZXZlIGZpY2FyIHZlcmRlLgoiIiIKCmZyb20gX19mdXR1cmVfXyBpbXBvcnQgYW5ub3RhdGlvbnMKCmltcG9ydCBkYXRldGltZSBhcyBkdAppbXBvcnQgb3MKCmltcG9ydCBweXRlc3QKCmZyb20gbWVudGVfbGF5bGF5LmFycXVpdm9zLnJvdGVhZG9yX2FycXVpdm9zIGltcG9ydCBkZXRlY3Rhcl9pbnRlbmNhb19hcnF1aXZvcwpmcm9tIG1lbnRlX2xheWxheS5hdXRvbm9taWEuY29tYW5kb3NfaW1lZGlhdG9zIGltcG9ydCBDb21hbmRvc0ltZWRpYXRvc1J1bnRpbWUKZnJvbSBtZW50ZV9sYXlsYXkuY29nbmljYW8ubW9kYWxpZGFkZV90dXJubyBpbXBvcnQgY2xhc3NpZmljYXJfbW9kYWxpZGFkZV90dXJubwpmcm9tIG1lbnRlX2xheWxheS5lc3BlY2lhbGlzdGFzLmNhaXhhX2VudHJhZGFfcGVzc29hbCBpbXBvcnQgQ2FpeGFFbnRyYWRhUGVzc29hbFJ1bnRpbWUKZnJvbSBtZW50ZV9sYXlsYXkuZXNwZWNpYWxpc3Rhcy5tYXBhX2hhYmlsaWRhZGVzIGltcG9ydCBNYXBhSGFiaWxpZGFkZXNSdW50aW1lCmZyb20gbWVudGVfbGF5bGF5Lm1lbW9yaWFfbWVudGFsLmNvbXBhdGliaWxpZGFkZV9jb250ZXh0byBpbXBvcnQgKAogICAgcmVzb2x2ZXJfcmVwZXRpY2FvX3VsdGltYV9hY2FvLAogICAgdGV4dG9fcGVkZV9yZXBldGljYW9fY3VydGEsCikKZnJvbSBtZW50ZV9sYXlsYXkubWVtb3JpYV9tZW50YWwuY29udGV4dG9fY29tcGFydGlsaGFkbyBpbXBvcnQgKAogICAgcmVnaXN0cmFyX3Jlc3VsdGFkb19leGVjdWNhbywKKQpmcm9tIG1lbnRlX2xheWxheS5tZW1vcmlhX21lbnRhbC5jb250aW51aWRhZGVfY29udGV4dG8gaW1wb3J0ICgKICAgIHJlZ2lzdHJhcl9lc3RydXR1cmFfYXJxdWl2b19yZWNlbnRlLAopCmZyb20gbWVudGVfbGF5bGF5Lm1lbW9yaWFfbWVudGFsLnJlc3VsdGFkb19hY2FvIGltcG9ydCBSZXN1bHRhZG9BY2FvCgoKZGVmIF9ub3JtYWxpemFyKHRleHRvOiBzdHIpIC0+IHN0cjoKICAgIHJldHVybiBzdHIodGV4dG8gb3IgIiIpLmNhc2Vmb2xkKCkuc3RyaXAoKQoKCmRlZiBfcGFyYW1zKCoqa3dhcmdzKToKICAgIHJldHVybiBrd2FyZ3MKCgpkZWYgX2VzdGFkb19hcnF1aXZvKGNhbWluaG86IHN0cikgLT4gZGljdDoKICAgIHJldHVybiByZWdpc3RyYXJfZXN0cnV0dXJhX2FycXVpdm9fcmVjZW50ZSgKICAgICAgICB7fSwKICAgICAgICB7CiAgICAgICAgICAgICJ0aXBvIjogImFycXVpdm8iLAogICAgICAgICAgICAiY2FtaW5obyI6IGNhbWluaG8sCiAgICAgICAgICAgICJhcnF1aXZvX25vbWUiOiBvcy5wYXRoLmJhc2VuYW1lKGNhbWluaG8pLAogICAgICAgICAgICAidGlwb19hcnF1aXZvIjogInRleHRvIiwKICAgICAgICB9LAogICAgKQoKCmRlZiBfZGV0ZWN0YXJfYXJxdWl2byh0ZXh0bzogc3RyLCBlc3RhZG86IGRpY3QgfCBOb25lID0gTm9uZSkgLT4gZGljdCB8IE5vbmU6CiAgICByZXR1cm4gZGV0ZWN0YXJfaW50ZW5jYW9fYXJxdWl2b3MoCiAgICAgICAgdGV4dG8sCiAgICAgICAgcGFyYW1zX2NiPV9wYXJhbXMsCiAgICAgICAgZXN0YWRvX21lbnRhbD1lc3RhZG8gb3Ige30sCiAgICApCgoKZGVmIF9jYWl4YV9taW5pbWEodG1wX3BhdGgpIC0+IENhaXhhRW50cmFkYVBlc3NvYWxSdW50aW1lOgogICAgcmV0dXJuIENhaXhhRW50cmFkYVBlc3NvYWxSdW50aW1lKAogICAgICAgIGNhbWluaG89dG1wX3BhdGggLyAiY2FpeGFfcmVkLmpzb24iLAogICAgICAgIGZhbGFyPWxhbWJkYSAqX2FyZ3MsICoqX2t3YXJnczogTm9uZSwKICAgICAgICByZWdpc3RyYXJfcmVzdWx0YWRvPWxhbWJkYSAqX2FyZ3MsICoqX2t3YXJnczogTm9uZSwKICAgICAgICBleGVjdXRhcl9pbnRlbmNhbz1sYW1iZGEgKl9hcmdzLCAqKl9rd2FyZ3M6IFRydWUsCiAgICAgICAgY29udGV4dG9fZ2V0dGVyPWxhbWJkYTogeyJtZXNzYWdlcyI6IFtdfSwKICAgICAgICBhZ29yYT1sYW1iZGE6IGR0LmRhdGV0aW1lKDIwMjYsIDgsIDE2LCAxOCwgMCksCiAgICAgICAgbG9nPWxhbWJkYSAqX2FyZ3M6IE5vbmUsCiAgICApCgoKZGVmIHRlc3RfZ3VhcmRfX2NhdGFsb2dvX2xvY2FsX3NhYmVfcXVlX2FycXVpdm9zX3Nhb19jYXBhY2lkYWRlX3JlYWwoKSAtPiBOb25lOgogICAgcmVzcG9zdGEgPSBNYXBhSGFiaWxpZGFkZXNSdW50aW1lKCkucmVzcG9uZGVyX3Blcmd1bnRhX2NhcGFjaWRhZGUoCiAgICAgICAgIlZvY8OqIGNvbnNlZ3VlIGFwYWdhciBhcnF1aXZvcz8iCiAgICApCiAgICBhc3NlcnQgcmVzcG9zdGEKICAgIGFzc2VydCAiYXJxdWl2byIgaW4gX25vcm1hbGl6YXIocmVzcG9zdGEpCgoKZGVmIHRlc3RfcmVkX19wZXJndW50YV9jYXBhY2lkYWRlX2FwYWdhcl9hcnF1aXZvc19lX3RyYXRhZGFfYW50ZXNfZGFfYmFycmVpcmFfcDAoKSAtPiBOb25lOgogICAgdGV4dG8gPSAiVm9jw6ogY29uc2VndWUgYXBhZ2FyIGFycXVpdm9zPyIKICAgIHR1cm5vID0gY2xhc3NpZmljYXJfbW9kYWxpZGFkZV90dXJubyh0ZXh0bykKICAgIGFzc2VydCB0dXJub1siYXV0b3JpemFfZXhlY3VjYW8iXSBpcyBGYWxzZQoKICAgIGZhbGFzOiBsaXN0W3N0cl0gPSBbXQogICAgZXhlY3Vjb2VzOiBsaXN0W2RpY3RdID0gW10KICAgIGNvbnN1bHRhc19jYXBhY2lkYWRlOiBsaXN0W3N0cl0gPSBbXQogICAgbWFwYSA9IE1hcGFIYWJpbGlkYWRlc1J1bnRpbWUoKQoKICAgIGNsYXNzIEVzdGFkbzoKICAgICAgICBtZW50YWwgPSB7InR1cm5vX2F0dWFsIjogdHVybm99CgogICAgZGVmIHJlc3BvbmRlcl9jYXBhY2lkYWRlKGZhbGE6IHN0cikgLT4gc3RyOgogICAgICAgIGNvbnN1bHRhc19jYXBhY2lkYWRlLmFwcGVuZChmYWxhKQogICAgICAgIHJldHVybiBtYXBhLnJlc3BvbmRlcl9wZXJndW50YV9jYXBhY2lkYWRlKAogICAgICAgICAgICBmYWxhLAogICAgICAgICAgICB0dXJubz10dXJubywKICAgICAgICAgICAgY29udGV4dG89RXN0YWRvLm1lbnRhbCwKICAgICAgICApCgogICAgcnVudGltZSA9IENvbWFuZG9zSW1lZGlhdG9zUnVudGltZSgKICAgICAgICBuYW1lc3BhY2VfZ2V0dGVyPWxhbWJkYTogewogICAgICAgICAgICAiX2VzdGFkb19jb21wYXJ0aWxoYWRvX3J1bnRpbWUiOiBFc3RhZG8oKSwKICAgICAgICAgICAgIl9yZXNwb25kZXJfcGVyZ3VudGFfY2FwYWNpZGFkZV9sb2NhbCI6IHJlc3BvbmRlcl9jYXBhY2lkYWRlLAogICAgICAgICAgICAiZmFsYXJfY29tX2xpcHN5bmMiOiBsYW1iZGEgZmFsYSwgKl9hcmdzOiBmYWxhcy5hcHBlbmQoZmFsYSksCiAgICAgICAgICAgICJleGVjdXRhcl9pbnRlbmNhbyI6IGxhbWJkYSBpbnRlbmNhbywgX3RleHRvOiBleGVjdWNvZXMuYXBwZW5kKGludGVuY2FvKSBvciBUcnVlLAogICAgICAgIH0sCiAgICAgICAgbG9vcF9nZXR0ZXI9bGFtYmRhOiBOb25lLAogICAgKQoKICAgIGFzc2VydCBydW50aW1lLnByb2Nlc3Nhcl9wcmlvcml0YXJpb3ModGV4dG8pIGlzIFRydWUKICAgIGFzc2VydCBjb25zdWx0YXNfY2FwYWNpZGFkZSA9PSBbdGV4dG9dCiAgICBhc3NlcnQgZmFsYXMgYW5kICJhcnF1aXZvIiBpbiBfbm9ybWFsaXphcihmYWxhc1stMV0pCiAgICBhc3NlcnQgZXhlY3Vjb2VzID09IFtdCgoKZGVmIHRlc3RfcmVkX19lc2NyaXRhX2VsaXB0aWNhX3VzYV91bmljb19hcnF1aXZvX3JlY2VudGVfdGlwYWRvKCkgLT4gTm9uZToKICAgIGNhbWluaG8gPSAiQzovdG1wL2Nhb3Mgc2VndXJvLnR4dCIKICAgIHJlc3VsdGFkbyA9IF9kZXRlY3Rhcl9hcnF1aXZvKAogICAgICAgICJFc2NyZXZlIHByaW1laXJhIGxpbmhhLiIsCiAgICAgICAgX2VzdGFkb19hcnF1aXZvKGNhbWluaG8pLAogICAgKQogICAgYXNzZXJ0IHJlc3VsdGFkbyA9PSB7CiAgICAgICAgImludGVudCI6ICJDUkVBVEVfRklMRSIsCiAgICAgICAgInBhcmFtcyI6IHsKICAgICAgICAgICAgImFsdm8iOiBjYW1pbmhvLAogICAgICAgICAgICAiY29udGV1ZG8iOiAicHJpbWVpcmEgbGluaGEiLAogICAgICAgICAgICAiZWRpdGFyX2V4aXN0ZW50ZSI6IFRydWUsCiAgICAgICAgfSwKICAgIH0KCgpkZWYgdGVzdF9yZWRfX2FwcGVuZF9lbGlwdGljb191c2FfdW5pY29fYXJxdWl2b19yZWNlbnRlX3RpcGFkbygpIC0+IE5vbmU6CiAgICBjYW1pbmhvID0gIkM6L3RtcC9jYW9zIHNlZ3Vyby50eHQiCiAgICByZXN1bHRhZG8gPSBfZGV0ZWN0YXJfYXJxdWl2bygKICAgICAgICAiQWNyZXNjZW50ZSBzZWd1bmRhIGxpbmhhLiIsCiAgICAgICAgX2VzdGFkb19hcnF1aXZvKGNhbWluaG8pLAogICAgKQogICAgYXNzZXJ0IHJlc3VsdGFkbyA9PSB7CiAgICAgICAgImludGVudCI6ICJDUkVBVEVfRklMRSIsCiAgICAgICAgInBhcmFtcyI6IHsKICAgICAgICAgICAgImFsdm8iOiBjYW1pbmhvLAogICAgICAgICAgICAiY29udGV1ZG8iOiAic2VndW5kYSBsaW5oYSIsCiAgICAgICAgICAgICJlZGl0YXJfZXhpc3RlbnRlIjogVHJ1ZSwKICAgICAgICAgICAgIm1vZG9fZXNjcml0YSI6ICJhcHBlbmQiLAogICAgICAgIH0sCiAgICB9CgoKZGVmIHRlc3RfZ3VhcmRfX2VzY3JpdGFfZWxpcHRpY2Ffc2VtX2FycXVpdm9fcmVjZW50ZV9uYW9fYWRpdmluaGFfYWx2bygpIC0+IE5vbmU6CiAgICBhc3NlcnQgX2RldGVjdGFyX2FycXVpdm8oIkVzY3JldmUgcHJpbWVpcmEgbGluaGEuIiwge30pIGlzIE5vbmUKICAgIGFzc2VydCBfZGV0ZWN0YXJfYXJxdWl2bygiQWNyZXNjZW50ZSBzZWd1bmRhIGxpbmhhLiIsIHt9KSBpcyBOb25lCgoKZGVmIHRlc3RfZ3VhcmRfX2VzY3JpdGFfY29tX3Byb25vbWVfamFfY29uc3VtaWFfcmVmZXJlbmNpYV90aXBpZmljYWRhKCkgLT4gTm9uZToKICAgIGNhbWluaG8gPSAiQzovdG1wL2Nhb3Mgc2VndXJvLnR4dCIKICAgIHJlc3VsdGFkbyA9IF9kZXRlY3Rhcl9hcnF1aXZvKAogICAgICAgICJFc2NyZXZlIHByaW1laXJhIGxpbmhhIG5lbGUuIiwKICAgICAgICBfZXN0YWRvX2FycXVpdm8oY2FtaW5obyksCiAgICApCiAgICBhc3NlcnQgcmVzdWx0YWRvIGlzIG5vdCBOb25lCiAgICBhc3NlcnQgcmVzdWx0YWRvWyJpbnRlbnQiXSA9PSAiQ1JFQVRFX0ZJTEUiCiAgICBhc3NlcnQgcmVzdWx0YWRvWyJwYXJhbXMiXVsiYWx2byJdID09IGNhbWluaG8KICAgIGFzc2VydCByZXN1bHRhZG9bInBhcmFtcyJdWyJjb250ZXVkbyJdID09ICJwcmltZWlyYSBsaW5oYSIKICAgIGFzc2VydCByZXN1bHRhZG9bInBhcmFtcyJdWyJlZGl0YXJfZXhpc3RlbnRlIl0gaXMgVHJ1ZQoKCmRlZiB0ZXN0X3JlZF9fcmVmZXJlbmNpYV90aXBpZmljYWRhX3B1YmxpY2FkYV9hbGltZW50YV9lc2NyaXRhX2RhX2V0YXBhX3NlZ3VpbnRlKCkgLT4gTm9uZToKICAgIGNhbWluaG8gPSAiQzovdG1wL2Nhb3Mgc2VndXJvLnR4dCIKICAgIGVzdGFkbyA9IHJlZ2lzdHJhcl9lc3RydXR1cmFfYXJxdWl2b19yZWNlbnRlKAogICAgICAgIHt9LAogICAgICAgIHsKICAgICAgICAgICAgInRpcG8iOiAiYXJxdWl2byIsCiAgICAgICAgICAgICJjYW1pbmhvIjogY2FtaW5obywKICAgICAgICAgICAgImFycXVpdm9fbm9tZSI6ICJjYW9zIHNlZ3Vyby50eHQiLAogICAgICAgICAgICAidGlwb19hcnF1aXZvIjogInRleHRvIiwKICAgICAgICAgICAgIm9yaWdlbSI6ICJDUkVBVEVfRklMRSIsCiAgICAgICAgfSwKICAgICkKCiAgICAjIEEgZXRhcGEgc2VndWludGUgbmFvIHJlcGV0ZSBub21lIG5lbSBwcm9ub21lOiBkZXBlbmRlIGV4Y2x1c2l2YW1lbnRlIGRhCiAgICAjIHJlZmVyZW5jaWEgdGlwYWRhIHZpdmEgcHVibGljYWRhIHBlbGEgZXRhcGEgYW50ZXJpb3IuCiAgICByZXN1bHRhZG8gPSBfZGV0ZWN0YXJfYXJxdWl2bygiRXNjcmV2ZSBwcmltZWlyYSBsaW5oYS4iLCBlc3RhZG8pCiAgICBhc3NlcnQgcmVzdWx0YWRvIGlzIG5vdCBOb25lCiAgICBhc3NlcnQgcmVzdWx0YWRvWyJpbnRlbnQiXSA9PSAiQ1JFQVRFX0ZJTEUiCiAgICBhc3NlcnQgcmVzdWx0YWRvWyJwYXJhbXMiXVsiYWx2byJdID09IGNhbWluaG8KICAgIGFzc2VydCByZXN1bHRhZG9bInBhcmFtcyJdWyJjb250ZXVkbyJdID09ICJwcmltZWlyYSBsaW5oYSIKICAgIGFzc2VydCByZXN1bHRhZG9bInBhcmFtcyJdWyJlZGl0YXJfZXhpc3RlbnRlIl0gaXMgVHJ1ZQoKCmRlZiB0ZXN0X3JlZF9fbGVpdHVyYV9wb3Jfbm9tZV9yZXVzYV9hcnF1aXZvX3JlY2VudGVfZXF1aXZhbGVudGVfcGFyYV9maWxlX3JlYWQoKSAtPiBOb25lOgogICAgY2FtaW5obyA9ICJDOi90bXAvY2FvcyBzZWd1cm8udHh0IgogICAgcmVzdWx0YWRvID0gX2RldGVjdGFyX2FycXVpdm8oCiAgICAgICAgIkxlaWEgbyBjYW9zIHNlZ3Vyby50eHQuIiwKICAgICAgICBfZXN0YWRvX2FycXVpdm8oY2FtaW5obyksCiAgICApCiAgICBhc3NlcnQgcmVzdWx0YWRvID09IHsKICAgICAgICAiaW50ZW50IjogIkZJTEVfUkVBRCIsCiAgICAgICAgInBhcmFtcyI6IHsKICAgICAgICAgICAgImNhbWluaG8iOiBjYW1pbmhvLAogICAgICAgICAgICAiYWx2byI6ICJjYW9zIHNlZ3Vyby50eHQiLAogICAgICAgICAgICAicmVmZXJlbmNpYV9jb250ZXh0dWFsIjogVHJ1ZSwKICAgICAgICB9LAogICAgfQoKCmRlZiB0ZXN0X3JlZF9fbGVpYV9kZV9ub3ZvX2VfcmVjb25oZWNpZG9fY29tb19yZXBldGljYW8oKSAtPiBOb25lOgogICAgYXNzZXJ0IHRleHRvX3BlZGVfcmVwZXRpY2FvX2N1cnRhKCJMZWlhIGRlIG5vdm8uIiwgX25vcm1hbGl6YXIpIGlzIFRydWUKCgpkZWYgdGVzdF9yZWRfX2ZpbGVfcmVhZF9jb25maXJtYWRvX3BvZGVfc2VyX3JlZXhlY3V0YWRvX3Bvcl9yZXBldGljYW9fc2VndXJhKCkgLT4gTm9uZToKICAgIGNhbWluaG8gPSAiQzovdG1wL2Nhb3Mgc2VndXJvLnR4dCIKICAgIHBhcmFtcyA9IHsiY2FtaW5obyI6IGNhbWluaG8sICJhbHZvIjogImNhb3Mgc2VndXJvLnR4dCJ9CiAgICBlc3RhZG8gPSByZWdpc3RyYXJfcmVzdWx0YWRvX2V4ZWN1Y2FvKAogICAgICAgIHt9LAogICAgICAgIFJlc3VsdGFkb0FjYW8oCiAgICAgICAgICAgIGludGVudD0iRklMRV9SRUFEIiwKICAgICAgICAgICAgc3RhdHVzPSJhcnF1aXZvX2xpZG8iLAogICAgICAgICAgICBhbHZvPWNhbWluaG8sCiAgICAgICAgICAgIHBhcmFtcz1wYXJhbXMsCiAgICAgICAgICAgIGV4ZWN1dG91PVRydWUsCiAgICAgICAgICAgIGNvbmZpcm1hZG89VHJ1ZSwKICAgICAgICApLAogICAgICAgICJMZWlhIG8gY2FvcyBzZWd1cm8udHh0LiIsCiAgICAgICAgVHJ1ZSwKICAgICkKCiAgICBhc3NlcnQgcmVzb2x2ZXJfcmVwZXRpY2FvX3VsdGltYV9hY2FvKAogICAgICAgICJkZSBub3ZvIiwKICAgICAgICBlc3RhZG8sCiAgICAgICAgX25vcm1hbGl6YXIsCiAgICApID09IHsiaW50ZW50IjogIkZJTEVfUkVBRCIsICJwYXJhbXMiOiBwYXJhbXN9CgoKZGVmIHRlc3RfZ3VhcmRfX2RlbGV0ZV9iZW1fc3VjZWRpZG9fY29udGludWFfbmFvX3JlZXhlY3V0YXZlbCgpIC0+IE5vbmU6CiAgICBlc3RhZG8gPSB7CiAgICAgICAgInVsdGltYV9hY2FvX2ludGVudCI6ICJERUxFVEVfSVRFTSIsCiAgICAgICAgInVsdGltYV9hY2FvX3BhcmFtcyI6IHsiYWx2byI6ICJDOi90bXAvY2FvcyBzZWd1cm8udHh0IiwgInRpcG8iOiAiYXJxdWl2byJ9LAogICAgICAgICJ1bHRpbWFfYWNhb19zdGF0dXMiOiAibW92aWRvX3BhcmFfbGl4ZWlyYSIsCiAgICAgICAgInVsdGltYV9hY2FvX29rIjogVHJ1ZSwKICAgICAgICAidWx0aW1hX2FjYW9fY29uZmlybWFkYSI6IFRydWUsCiAgICAgICAgInVsdGltYV9hY2FvX3JlZXhlY3V0YXZlbCI6IEZhbHNlLAogICAgfQogICAgYXNzZXJ0IHJlc29sdmVyX3JlcGV0aWNhb191bHRpbWFfYWNhbygiZGUgbm92byIsIGVzdGFkbywgX25vcm1hbGl6YXIpIGlzIE5vbmUKCgpkZWYgdGVzdF9ndWFyZF9fb2JyaWdhZG9fZGVfbm92b19uYW9fZV9yZXBldGljYW9fb3BlcmFjaW9uYWwoKSAtPiBOb25lOgogICAgYXNzZXJ0IHRleHRvX3BlZGVfcmVwZXRpY2FvX2N1cnRhKCJvYnJpZ2FkbyBkZSBub3ZvIiwgX25vcm1hbGl6YXIpIGlzIEZhbHNlCgoKZGVmIHRlc3RfcmVkX19jYWl4YV9kZV9lbnRyYWRhX25hb19zZXF1ZXN0cmFfbm9tZV9kZV9hcnF1aXZvX2NvbV9pZGVpYSh0bXBfcGF0aCkgLT4gTm9uZToKICAgIGNhaXhhID0gX2NhaXhhX21pbmltYSh0bXBfcGF0aCkKICAgIGFzc2VydCBjYWl4YS5kZXRlY3RhcigiQXBhZ2EgbyB0cm9jYSBpZGVpYS50eHQuIikgPT0gIiIKCgpAcHl0ZXN0Lm1hcmsucGFyYW1ldHJpemUoCiAgICAiZmFsYSIsCiAgICBbCiAgICAgICAgIkFwYWdhIG8gbWluaGEgdGFyZWZhLnR4dC4iLAogICAgICAgICJSZW1vdmUgbyBwZW5zYW1lbnRvLm1kLiIsCiAgICAgICAgIkV4Y2x1aSBhIG5vdGEudHh0LiIsCiAgICBdLAopCmRlZiB0ZXN0X3JlZF9fbm9tZXNfZGVfYXJxdWl2b19jb21fdm9jYWJ1bGFyaW9fZGFfY2FpeGFfbmFvX3Nhb19zZXF1ZXN0cmFkb3MoCiAgICB0bXBfcGF0aCwKICAgIGZhbGE6IHN0ciwKKSAtPiBOb25lOgogICAgY2FpeGEgPSBfY2FpeGFfbWluaW1hKHRtcF9wYXRoKQogICAgYXNzZXJ0IGNhaXhhLmRldGVjdGFyKGZhbGEpID09ICIiCgoKZGVmIHRlc3RfZ3VhcmRfX2NhaXhhX2RlX2VudHJhZGFfY29udGludWFfcmVjb25oZWNlbmRvX2V4Y2x1c2FvX3JlYWxfZGVfbm90YSh0bXBfcGF0aCkgLT4gTm9uZToKICAgIGNhaXhhID0gX2NhaXhhX21pbmltYSh0bXBfcGF0aCkKICAgIGFzc2VydCBjYWl4YS5kZXRlY3RhcigiQXBhZ2EgZXNzYSBub3RhLiIpID09ICJleGNsdWlyIgoKCmRlZiB0ZXN0X3JlZF9fY29uc3VsdGFfYXJxdWl2b19haW5kYV9leGlzdGVfcmV1c2FfZmlsZV9zZWFyY2hfY29tX3JlZmVyZW5jaWFfY2FtaW5obygpIC0+IE5vbmU6CiAgICBjYW1pbmhvID0gIkM6L3RtcC9jYW9zIHNlZ3Vyby50eHQiCiAgICByZXN1bHRhZG8gPSBfZGV0ZWN0YXJfYXJxdWl2bygKICAgICAgICAiTyBhcnF1aXZvIGFpbmRhIGV4aXN0ZT8iLAogICAgICAgIF9lc3RhZG9fYXJxdWl2byhjYW1pbmhvKSwKICAgICkKICAgIGFzc2VydCByZXN1bHRhZG8gPT0gewogICAgICAgICJpbnRlbnQiOiAiRklMRV9TRUFSQ0giLAogICAgICAgICJwYXJhbXMiOiB7CiAgICAgICAgICAgICJxdWVyeSI6ICJjYW9zIHNlZ3Vyby50eHQiLAogICAgICAgICAgICAicmVmZXJlbmNpYV9jYW1pbmhvIjogY2FtaW5obywKICAgICAgICAgICAgImFsdm8iOiAiY2FvcyBzZWd1cm8udHh0IiwKICAgICAgICB9LAogICAgfQoKCmRlZiB0ZXN0X2d1YXJkX19jb25zdWx0YV9leGlzdGVuY2lhX3NlbV9yZWZlcmVuY2lhX25hb19pbnZlbnRhX2NhbWluaG8oKSAtPiBOb25lOgogICAgcmVzdWx0YWRvID0gX2RldGVjdGFyX2FycXVpdm8oIk8gYXJxdWl2byBhaW5kYSBleGlzdGU/Iiwge30pCiAgICBhc3NlcnQgbm90ICgKICAgICAgICBpc2luc3RhbmNlKHJlc3VsdGFkbywgZGljdCkKICAgICAgICBhbmQgc3RyKChyZXN1bHRhZG8uZ2V0KCJwYXJhbXMiKSBvciB7fSkuZ2V0KCJyZWZlcmVuY2lhX2NhbWluaG8iKSBvciAiIikuc3RyaXAoKQogICAgKQo="

GREEN_NODES = [
    "test_guard__catalogo_local_sabe_que_arquivos_sao_capacidade_real",
    "test_guard__escrita_eliptica_sem_arquivo_recente_nao_adivinha_alvo",
    "test_guard__escrita_com_pronome_ja_consumia_referencia_tipificada",
    "test_guard__delete_bem_sucedido_continua_nao_reexecutavel",
    "test_guard__obrigado_de_novo_nao_e_repeticao_operacional",
    "test_guard__caixa_de_entrada_continua_reconhecendo_exclusao_real_de_nota",
    "test_guard__consulta_existencia_sem_referencia_nao_inventa_caminho",
]

RED_NODES = [
    ("test_red__pergunta_capacidade_apagar_arquivos_e_tratada_antes_da_barreira_p0", 1),
    ("test_red__escrita_eliptica_usa_unico_arquivo_recente_tipado", 1),
    ("test_red__append_eliptico_usa_unico_arquivo_recente_tipado", 1),
    ("test_red__referencia_tipificada_publicada_alimenta_escrita_da_etapa_seguinte", 1),
    ("test_red__leitura_por_nome_reusa_arquivo_recente_equivalente_para_file_read", 1),
    ("test_red__leia_de_novo_e_reconhecido_como_repeticao", 1),
    ("test_red__file_read_confirmado_pode_ser_reexecutado_por_repeticao_segura", 1),
    ("test_red__caixa_de_entrada_nao_sequestra_nome_de_arquivo_com_ideia", 1),
    ("test_red__nomes_de_arquivo_com_vocabulario_da_caixa_nao_sao_sequestrados", 3),
    ("test_red__consulta_arquivo_ainda_existe_reusa_file_search_com_referencia_caminho", 1),
]


def run(cmd: list[str], *, cwd: Path, check: bool = False) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"comando falhou rc={proc.returncode}: {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_manifest(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def rollback(target: Path) -> None:
    try:
        if target.exists():
            target.unlink()
    except OSError as exc:
        print(f"ERRO: rollback nao conseguiu remover {target}: {exc}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".", help="raiz do repositorio Laylay")
    args = parser.parse_args()
    repo = Path(args.repo).expanduser().resolve()
    target = repo / TARGET_REL

    print(f"[{PATCH_ID}] fotografia vermelha — somente testes")
    print(f"Repositorio: {repo}")

    git_ok = run(["git", "rev-parse", "--is-inside-work-tree"], cwd=repo)
    if git_ok.returncode != 0 or git_ok.stdout.strip() != "true":
        print("ERRO: --repo nao aponta para um worktree Git.", file=sys.stderr)
        return 2

    head = run(["git", "rev-parse", "HEAD"], cwd=repo, check=True).stdout.strip()
    if head != BASELINE_HEAD:
        print(
            "ERRO: HEAD diferente da baseline estudada. Nada foi alterado.\n"
            f"Esperado: {BASELINE_HEAD}\nAtual:    {head}",
            file=sys.stderr,
        )
        return 3

    status_target = run(
        ["git", "status", "--porcelain", "--", TARGET_REL.as_posix()], cwd=repo, check=True
    ).stdout.strip()
    if status_target or target.exists():
        print(
            "ERRO: o arquivo-alvo ja existe ou possui estado local. "
            "Nao vou sobrescreve-lo.\n" + (status_target or str(target)),
            file=sys.stderr,
        )
        return 4

    tracked = run(
        ["git", "cat-file", "-e", f"HEAD:{TARGET_REL.as_posix()}"], cwd=repo
    )
    if tracked.returncode == 0:
        print("ERRO: o alvo ja existe na baseline HEAD; recusando.", file=sys.stderr)
        return 5

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = repo / ".laylay_patch_backups" / f"{PATCH_ID}_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    manifest_path = backup_dir / "manifest.json"
    empty_before = backup_dir / "target_absent_before.txt"
    empty_before.write_bytes(b"")

    manifest: dict[str, Any] = {
        "patch_id": PATCH_ID,
        "tipo": "fotografia_vermelha_somente_testes",
        "baseline_head": BASELINE_HEAD,
        "head_observado": head,
        "target": TARGET_REL.as_posix(),
        "target_existia_antes": False,
        "expected_sha256": EXPECTED_SHA256,
        "started_at": dt.datetime.now().astimezone().isoformat(),
        "status": "iniciado",
        "validacoes": {},
    }
    save_manifest(manifest_path, manifest)

    try:
        payload = base64.b64decode(TEST_SOURCE_B64.encode("ascii"), validate=True)
        if sha256_bytes(payload) != EXPECTED_SHA256:
            raise RuntimeError("payload embutido divergiu do SHA256 esperado")

        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=".laylay_red_", suffix=".tmp", dir=str(target.parent))
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(temp_name, target)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

        actual_sha = sha256_bytes(target.read_bytes())
        if actual_sha != EXPECTED_SHA256:
            raise RuntimeError(
                f"SHA256 apos escrita divergiu: esperado={EXPECTED_SHA256} atual={actual_sha}"
            )
        manifest["sha256_depois"] = actual_sha

        # py_compile sem deixar __pycache__ no diretorio de testes.
        pyc_path = backup_dir / "compiled_test.pyc"
        compile_code = (
            "import py_compile,sys; "
            "py_compile.compile(sys.argv[1], cfile=sys.argv[2], doraise=True)"
        )
        compiled = run(
            [sys.executable, "-c", compile_code, str(target), str(pyc_path)], cwd=repo
        )
        manifest["validacoes"]["py_compile"] = {
            "returncode": compiled.returncode,
            "stdout": compiled.stdout,
            "stderr": compiled.stderr,
        }
        if compiled.returncode != 0:
            raise RuntimeError("py_compile falhou")

        # Para arquivo novo/untracked, git diff comum nao o enxerga. O modo
        # --no-index compara contra um arquivo vazio real sem tocar no index.
        diff_check = run(
            ["git", "diff", "--no-index", "--check", str(empty_before), str(target)],
            cwd=repo,
        )
        manifest["validacoes"]["git_diff_no_index_check"] = {
            "returncode": diff_check.returncode,
            "stdout": diff_check.stdout,
            "stderr": diff_check.stderr,
        }
        # rc=1 significa apenas "ha diferencas"; rc=3 indica whitespace error.
        if diff_check.returncode != 1:
            raise RuntimeError(
                "git diff --no-index --check nao retornou rc=1 limpo; "
                f"rc={diff_check.returncode}"
            )

        candidate = run(
            ["git", "diff", "--no-index", "--", str(empty_before), str(target)], cwd=repo
        )
        if candidate.returncode != 1:
            raise RuntimeError(f"nao foi possivel produzir candidate diff (rc={candidate.returncode})")
        (backup_dir / "patch_candidate.diff").write_text(
            candidate.stdout, encoding="utf-8", newline="\n"
        )

        test_base = TARGET_REL.as_posix()
        green_cmd = [sys.executable, "-m", "pytest", "-q"] + [
            f"{test_base}::{node}" for node in GREEN_NODES
        ]
        green = run(green_cmd, cwd=repo)
        manifest["validacoes"]["guardrails_verdes"] = {
            "returncode": green.returncode,
            "stdout": green.stdout,
            "stderr": green.stderr,
            "nodes": GREEN_NODES,
        }
        print("\n=== GUARDRAILS VERDES ===")
        print(green.stdout, end="")
        if green.stderr:
            print(green.stderr, end="", file=sys.stderr)
        if green.returncode != 0:
            raise RuntimeError(
                "um guardrail verde falhou; a fotografia nao e valida contra esta baseline"
            )

        red_records: list[dict[str, Any]] = []
        for node, expected_failed in RED_NODES:
            cmd = [sys.executable, "-m", "pytest", "-q", f"{test_base}::{node}"]
            proc = run(cmd, cwd=repo)
            combined = f"{proc.stdout}\n{proc.stderr}"
            match = re.search(r"(?m)(\d+) failed(?:,| in|$)", combined)
            failed_count = int(match.group(1)) if match else 0
            assertion_failure = "AssertionError" in combined
            record = {
                "node": node,
                "expected_failed": expected_failed,
                "returncode": proc.returncode,
                "failed_count": failed_count,
                "assertion_failure": assertion_failure,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
            red_records.append(record)
            print(f"\n=== RED: {node} ===")
            print(proc.stdout, end="")
            if proc.stderr:
                print(proc.stderr, end="", file=sys.stderr)

            if proc.returncode == 0:
                raise RuntimeError(
                    f"{node} ficou verde inesperadamente; investigar antes de corrigir producao"
                )
            if proc.returncode != 1:
                raise RuntimeError(
                    f"{node} nao falhou como teste comum (rc={proc.returncode}); "
                    "possivel erro de coleta/importacao/uso"
                )
            if failed_count != expected_failed or not assertion_failure:
                raise RuntimeError(
                    f"{node} nao produziu a falha de assercao esperada: "
                    f"failed={failed_count} esperado={expected_failed} "
                    f"AssertionError={assertion_failure}"
                )

        manifest["validacoes"]["testes_vermelhos"] = red_records

        status_after = run(
            ["git", "status", "--porcelain", "--", TARGET_REL.as_posix()], cwd=repo, check=True
        ).stdout.strip()
        manifest["status_target_depois"] = status_after
        if not status_after.startswith("??"):
            raise RuntimeError(
                "o teste novo nao ficou como arquivo untracked isolado; recusando estado inesperado: "
                + repr(status_after)
            )

        manifest["status"] = "fotografia_vermelha_confirmada"
        manifest["finished_at"] = dt.datetime.now().astimezone().isoformat()
        save_manifest(manifest_path, manifest)

        print("\n============================================================")
        print("FOTOGRAFIA VERMELHA CONFIRMADA")
        print(f"HEAD: {head}")
        print(f"Guardrails verdes: {len(GREEN_NODES)} passaram")
        print(f"Contratos vermelhos: {len(RED_NODES)} falharam por assert como esperado")
        print(f"Arquivo adicionado: {TARGET_REL.as_posix()}")
        print(f"Manifest: {manifest_path}")
        print("Nenhum arquivo de producao foi alterado. Nao houve commit/push/stage.")
        print("NAO COMMITAR AINDA: envie esta saida completa para analise.")
        return 0

    except Exception as exc:
        manifest["status"] = "rollback"
        manifest["erro"] = f"{type(exc).__name__}: {exc}"
        manifest["finished_at"] = dt.datetime.now().astimezone().isoformat()
        rollback(target)
        manifest["rollback_target_removido"] = not target.exists()
        save_manifest(manifest_path, manifest)
        print("\nERRO: fotografia vermelha recusada; arquivo de teste removido.", file=sys.stderr)
        print(f"Motivo: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(f"Diagnostico preservado em: {manifest_path}", file=sys.stderr)
        return 10


if __name__ == "__main__":
    raise SystemExit(main())
