from __future__ import annotations
import json
from pathlib import Path
from typing import Any

import inspect

from .expr import Expression
from .actions import Action, Var, LatexExpr, _latex_of
from .translate import Translator, _func_ident
from . import primitives as _prim
from . import iter as _iter


_TEMPLATE_PATH = Path(__file__).parent / "template.html"


def _normalize_name(name: str) -> str:
    """Multi-character bare identifiers must be subscripted for Desmos
    (``zoom`` would otherwise parse as ``z * o * o * m``). Names that already
    contain ``_`` or LaTeX commands are passed through unchanged."""
    if "_" in name or "\\" in name or "{" in name:
        return name
    if len(name) <= 1:
        return name
    return f"{name[0]}_{{{name[1:]}}}"


def _to_action(a) -> Action:
    if isinstance(a, Action):
        return a
    if isinstance(a, (list, tuple)):
        return Action.sequence(a)
    raise TypeError(f"expected Action or list of Actions, got {type(a).__name__}")


class Graph:
    def __init__(
        self,
        bounds: tuple[float, float, float, float] = (-10, 10, -10, 10),
        *,
        title: str = "Desmos Graph",
    ):
        # bounds: (xmin, xmax, ymin, ymax)
        self.xmin, self.xmax, self.ymin, self.ymax = bounds
        self.title = title
        self._expressions: list[Expression] = []
        self._next_id = 1
        self._ticker: dict[str, Any] | None = None

    # ---- id management ----
    def _new_id(self) -> str:
        i = self._next_id
        self._next_id += 1
        return str(i)

    def _add(self, expr: Expression) -> Expression:
        self._expressions.append(expr)
        return expr

    # ---- low-level expression entry ----
    def expr(self, latex: str, *, color: str | None = None, **kwargs) -> Expression:
        """Add a raw-LaTeX expression."""
        e = Expression(id=self._new_id(), latex=latex, color=color, **kwargs)
        return self._add(e)

    # ---- variables and sliders ----
    def var(self, name: str, value) -> Var:
        """Define a named variable: ``name = value``."""
        latex_name = _normalize_name(name)
        eid = self._new_id()
        self._add(Expression(id=eid, latex=f"{latex_name}={_latex_of(value)}", hidden=True))
        return Var(latex_name, eid)

    def slider(
        self,
        name: str,
        min: float,
        max: float,
        *,
        value: float | None = None,
        step: float | None = None,
        hard_bounds: bool = True,
    ) -> Var:
        """Define a variable with a slider UI."""
        if value is None:
            value = (min + max) / 2
        slider_cfg: dict = {
            "hardMin": bool(hard_bounds),
            "hardMax": bool(hard_bounds),
            "min": str(min),
            "max": str(max),
        }
        if step is not None:
            slider_cfg["step"] = str(step)
        latex_name = _normalize_name(name)
        eid = self._new_id()
        self._add(Expression(id=eid, latex=f"{latex_name}={_latex_of(value)}", slider=slider_cfg))
        return Var(latex_name, eid)

    # ---- actions, buttons, ticker ----
    def action(self, *assignments) -> Action:
        """Sequence one or more actions into a single Action."""
        if len(assignments) == 1 and isinstance(assignments[0], (list, tuple)):
            return _to_action(assignments[0])
        return Action.sequence(list(assignments))

    def button(
        self,
        text: str,
        *,
        action,
        at: tuple[float, float],
        color: str | None = None,
    ) -> Expression:
        """Create a clickable labeled point that runs ``action`` when clicked."""
        act = _to_action(action)
        e = Expression(
            id=self._new_id(),
            latex=rf"\left({_latex_of(at[0])},{_latex_of(at[1])}\right)",
            color=color,
            label=text,
            show_label=True,
            drag_mode="NONE",
            clickable_info={
                "enabled": True,
                "description": text,
                "latex": act.latex,
            },
        )
        return self._add(e)

    # ---- geometric primitives ----
    def circle(self, center, radius, **kw):    return _prim.circle(self, center, radius, **kw)
    def rectangle(self, anchor, width, height, **kw):
        return _prim.rectangle(self, anchor, width, height, **kw)
    def point(self, position, **kw):           return _prim.point(self, position, **kw)
    def line(self, p1, p2, **kw):              return _prim.line(self, p1, p2, **kw)
    def text(self, label, position, **kw):     return _prim.text(self, label, position, **kw)

    # ---- iteration + heatmap ----
    def iterate(self, step, x0, *, name, extra_params=()):
        return _iter.iterate(self, step, x0, name=name, extra_params=list(extra_params))
    def heatmap(self, value_fn, *, x_range, y_range, max_value, **kw):
        return _iter.heatmap(self, value_fn, x_range=x_range, y_range=y_range,
                             max_value=max_value, **kw)

    # ---- @g.func: compile a Python function to a Desmos function expression ----
    def func(self, fn):
        """Decorator: compile a Python function to a Desmos function expression."""
        src = inspect.getsource(fn)
        # Strip the @g.func decorator line if present, since getsource includes it.
        src = self._strip_decorator(src)
        latex_name, params, body = Translator().compile_function(src)
        latex = rf"{latex_name}\left({','.join(params)}\right)={body}"
        eid = self._new_id()
        self._add(Expression(id=eid, latex=latex))
        return LatexExpr(latex_name)  # so callers can reference it in raw expressions if needed

    @staticmethod
    def _strip_decorator(src: str) -> str:
        import textwrap
        src = textwrap.dedent(src)
        lines = src.splitlines()
        out = []
        skipping = True
        for line in lines:
            if skipping and line.lstrip().startswith("@"):
                continue
            skipping = False
            out.append(line)
        return "\n".join(out)

    def ticker(self, action, *, rate_ms: float = 30, open: bool = True) -> None:
        """Set the graph-wide ticker action (runs continuously)."""
        act = _to_action(action)
        self._ticker = {
            "handlerLatex": act.latex,
            "minStepLatex": str(rate_ms),
            "open": open,
        }

    # ---- state assembly ----
    def to_state(self) -> dict[str, Any]:
        state: dict[str, Any] = {
            "version": 11,
            "graph": {
                "viewport": {
                    "xmin": self.xmin, "xmax": self.xmax,
                    "ymin": self.ymin, "ymax": self.ymax,
                }
            },
            "expressions": {"list": [e.to_state() for e in self._expressions]},
        }
        if self._ticker is not None:
            state["expressions"]["ticker"] = self._ticker
        return state

    def to_state_json(self, *, indent: int | None = None) -> str:
        return json.dumps(self.to_state(), indent=indent)

    # ---- output ----
    def to_html(self, path: str | Path | None = None) -> str:
        template = _TEMPLATE_PATH.read_text()
        # State JSON is embedded as a JS object literal; json.dumps is valid JS.
        html = template.replace("__TITLE__", self.title).replace(
            "__STATE_JSON__", self.to_state_json()
        )
        if path is not None:
            Path(path).write_text(html)
        return html
