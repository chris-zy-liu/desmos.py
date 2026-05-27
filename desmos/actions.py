"""LaTeX-backed value objects and the action DSL.

LatexExpr wraps a LaTeX string and supports arithmetic so that action
right-hand-sides can be built fluently (``zoom.set(zoom * 0.5)``).

This is intentionally minimal — it is NOT the general Python-to-Desmos
expression layer. For that, use ``@g.func``.
"""
from __future__ import annotations
from typing import Union

Number = Union[int, float]


def _latex_of(x: object) -> str:
    if isinstance(x, LatexExpr):
        return x.latex
    if isinstance(x, bool):
        return "1" if x else "0"
    if isinstance(x, (int, float)):
        # Avoid trailing scientific notation in LaTeX.
        if isinstance(x, float) and x.is_integer():
            return str(int(x))
        return repr(x)
    if isinstance(x, tuple) and len(x) == 2:
        return rf"\left({_latex_of(x[0])},{_latex_of(x[1])}\right)"
    raise TypeError(f"cannot convert {type(x).__name__} to Desmos LaTeX")


class LatexExpr:
    __slots__ = ("latex",)

    def __init__(self, latex: str):
        self.latex = latex

    def _wrap(self, parenthesize: bool = True) -> str:
        if parenthesize:
            return rf"\left({self.latex}\right)"
        return self.latex

    # -- arithmetic --
    def __add__(self, other):  return LatexExpr(f"{self._wrap()}+{_paren(other)}")
    def __radd__(self, other): return LatexExpr(f"{_paren(other)}+{self._wrap()}")
    def __sub__(self, other):  return LatexExpr(f"{self._wrap()}-{_paren(other)}")
    def __rsub__(self, other): return LatexExpr(f"{_paren(other)}-{self._wrap()}")
    def __mul__(self, other):  return LatexExpr(f"{self._wrap()}\\cdot {_paren(other)}")
    def __rmul__(self, other): return LatexExpr(f"{_paren(other)}\\cdot {self._wrap()}")
    def __truediv__(self, other):  return LatexExpr(rf"\frac{{{self.latex}}}{{{_latex_of(other)}}}")
    def __rtruediv__(self, other): return LatexExpr(rf"\frac{{{_latex_of(other)}}}{{{self.latex}}}")
    def __pow__(self, other):  return LatexExpr(rf"{self._wrap()}^{{{_latex_of(other)}}}")
    def __neg__(self):         return LatexExpr(f"-{self._wrap()}")
    def __pos__(self):         return self

    def __repr__(self):
        return f"LatexExpr({self.latex!r})"


def _paren(x: object) -> str:
    """Render a value with parens if it's a compound LatexExpr; bare otherwise."""
    if isinstance(x, LatexExpr):
        return x._wrap()
    return _latex_of(x)


class Var(LatexExpr):
    """A named Desmos variable. Constructed via ``Graph.var`` / ``Graph.slider``."""
    __slots__ = ("name", "_expr_id")

    def __init__(self, name: str, expr_id: str):
        super().__init__(name)
        self.name = name
        self._expr_id = expr_id

    def set(self, rhs) -> "Action":
        return Action([(self.name, _latex_of(rhs))])

    def __repr__(self):
        return f"Var({self.name!r})"


class Action:
    """One or more ``lhs -> rhs`` assignments, comma-joined for Desmos."""
    __slots__ = ("assignments",)

    def __init__(self, assignments: list[tuple[str, str]]):
        self.assignments = list(assignments)

    @classmethod
    def sequence(cls, actions) -> "Action":
        merged: list[tuple[str, str]] = []
        for a in actions:
            if isinstance(a, Action):
                merged.extend(a.assignments)
            else:
                raise TypeError(f"expected Action, got {type(a).__name__}")
        return cls(merged)

    def then(self, other: "Action") -> "Action":
        return Action.sequence([self, other])

    @property
    def latex(self) -> str:
        return ",".join(rf"{lhs}\to {rhs}" for lhs, rhs in self.assignments)

    def __repr__(self):
        return f"Action({self.latex!r})"
