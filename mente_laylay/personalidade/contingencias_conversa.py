"""Contingências locais determinísticas da conversa."""

from __future__ import annotations

import ast
import random
import re
from typing import Any, Dict

from mente_laylay.personalidade.base_conversa import _ajustar, _normalizar


def _numero_matematico(valor: float) -> str:
    if abs(valor - round(valor)) < 1e-10:
        return str(int(round(valor)))
    return f"{valor:.8f}".rstrip("0").rstrip(".").replace(".", ",")


def _avaliar_expressao_linear(no: ast.AST) -> tuple[float, float]:
    """Avalia uma AST como ``a*x + b`` sem executar código arbitrário."""
    if isinstance(no, ast.Expression):
        return _avaliar_expressao_linear(no.body)
    if isinstance(no, ast.Constant) and isinstance(no.value, (int, float)):
        return 0.0, float(no.value)
    if isinstance(no, ast.Name) and no.id.casefold() == "x":
        return 1.0, 0.0
    if isinstance(no, ast.UnaryOp) and isinstance(no.op, (ast.UAdd, ast.USub)):
        a, b = _avaliar_expressao_linear(no.operand)
        fator = -1.0 if isinstance(no.op, ast.USub) else 1.0
        return fator * a, fator * b
    if isinstance(no, ast.BinOp):
        ae, be = _avaliar_expressao_linear(no.left)
        ad, bd = _avaliar_expressao_linear(no.right)
        if isinstance(no.op, ast.Add):
            return ae + ad, be + bd
        if isinstance(no.op, ast.Sub):
            return ae - ad, be - bd
        if isinstance(no.op, ast.Mult):
            if abs(ae) > 1e-12 and abs(ad) > 1e-12:
                raise ValueError("expressão não linear")
            if abs(ae) > 1e-12:
                return ae * bd, be * bd
            if abs(ad) > 1e-12:
                return ad * be, bd * be
            return 0.0, be * bd
        if isinstance(no.op, ast.Div):
            if abs(ad) > 1e-12 or abs(bd) < 1e-12:
                raise ValueError("divisão não linear ou por zero")
            return ae / bd, be / bd
    raise ValueError("notação não suportada")


def _formatar_expressao_linear(a: float, b: float) -> str:
    partes: list[str] = []
    if abs(a) > 1e-10:
        if abs(a - 1.0) < 1e-10:
            partes.append("x")
        elif abs(a + 1.0) < 1e-10:
            partes.append("-x")
        else:
            partes.append(f"{_numero_matematico(a)}x")
    if abs(b) > 1e-10 or not partes:
        numero = _numero_matematico(abs(b) if partes else b)
        if partes:
            partes.append(("+ " if b >= 0 else "- ") + numero)
        else:
            partes.append(numero)
    return " ".join(partes)


def resolver_equacao_linear_local(texto_usuario: str) -> str:
    """Resolve com segurança uma equação linear em x e entrega passos curtos."""
    bruto = str(texto_usuario or "")
    if "=" not in bruto:
        return ""
    equacao = bruto.split(":", 1)[-1] if ":" in bruto else bruto
    equacao = equacao.replace("–", "-").replace("—", "-").replace("−", "-")
    equacao = equacao.replace("×", "*").replace("÷", "/").replace(",", ".")
    equacao = equacao.strip(" \t\r\n?.!")
    if equacao.count("=") != 1 or not re.fullmatch(r"[\d.xX+\-*/()=\s]+", equacao):
        return ""
    esquerda, direita = equacao.split("=", 1)

    def preparar(expressao: str) -> str:
        s = re.sub(r"\s+", "", expressao).replace("X", "x")
        s = re.sub(r"(?<=\d)(?=[x(])|(?<=x)(?=\()|(?<=\))(?=[\dx(])", "*", s)
        return s

    try:
        ae, be = _avaliar_expressao_linear(ast.parse(preparar(esquerda), mode="eval"))
        ad, bd = _avaliar_expressao_linear(ast.parse(preparar(direita), mode="eval"))
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError):
        return ""

    coeficiente = ae - ad
    constante = bd - be
    esquerda_simples = _formatar_expressao_linear(ae, be)
    direita_simples = _formatar_expressao_linear(ad, bd)
    if abs(coeficiente) < 1e-10:
        return (
            "Simplificando os dois lados, eles ficam iguais; por isso há infinitas soluções."
            if abs(constante) < 1e-10 else
            "Simplificando os dois lados, surge uma contradição; portanto essa equação não tem solução."
        )
    solucao = constante / coeficiente
    return (
        f"Vamos por partes. Distribuindo os parênteses e juntando termos semelhantes, "
        f"o lado esquerdo vira {esquerda_simples} e o direito vira {direita_simples}. "
        f"Passando os termos, ficamos com {_numero_matematico(coeficiente)}x igual a "
        f"{_numero_matematico(constante)}. Dividindo por {_numero_matematico(coeficiente)}, "
        f"x é igual a {_numero_matematico(solucao)}."
    )


def responder_matematica_simples(ctx: Dict[str, Any], texto_usuario: str) -> str:
    linear = resolver_equacao_linear_local(texto_usuario)
    if linear:
        return _ajustar(ctx, linear, texto_usuario)
    t = _normalizar(ctx, texto_usuario)
    if not t:
        return ""
    m = re.fullmatch(
        r"(?:quanto\s+(?:e|é)\s+)?(?P<a>-?\d+(?:[,.]\d+)?)\s*(?P<op>\+|mais|-|menos|x|vezes|\*|dividido por|dividido|/)\s*(?P<b>-?\d+(?:[,.]\d+)?)\??",
        t,
    )
    if not m:
        return ""
    try:
        a = float(str(m.group("a")).replace(",", "."))
        b = float(str(m.group("b")).replace(",", "."))
        op = str(m.group("op") or "").strip()
        if op in {"+", "mais"}:
            res = a + b
        elif op in {"-", "menos"}:
            res = a - b
        elif op in {"x", "vezes", "*"}:
            res = a * b
        elif op in {"dividido por", "dividido", "/"}:
            if b == 0:
                return "Dividir por zero? Aí nem eu faço esse pacto com o caos."
            res = a / b
        else:
            return ""
        if float(res).is_integer():
            res_txt = str(int(res))
        else:
            res_txt = f"{res:.4f}".rstrip("0").rstrip(".")
        return _ajustar(ctx, random.choice([
            f"Dá {res_txt}. Matemática sem drama.",
            f"{res_txt}. Essa eu peguei sem tropeçar.",
            f"Resultado: {res_txt}.",
        ]), texto_usuario)
    except Exception:
        return ""
