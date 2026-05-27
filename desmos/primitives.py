"""Geometric primitives.

Each helper returns the underlying Expression so callers can mutate style
attributes (color, hidden, ...) after creation.
"""
from __future__ import annotations
from typing import Any

from .expr import Expression
from .actions import _latex_of, LatexExpr


def _opt_style(**kwargs) -> dict[str, Any]:
    """Strip None-valued kwargs so dataclass defaults apply."""
    return {k: v for k, v in kwargs.items() if v is not None}


def circle(g, center, radius, *, color=None, line_width=None, line_style=None):
    cx, cy = center
    latex = (
        rf"\left(x-\left({_latex_of(cx)}\right)\right)^{{2}}"
        rf"+\left(y-\left({_latex_of(cy)}\right)\right)^{{2}}"
        rf"=\left({_latex_of(radius)}\right)^{{2}}"
    )
    e = Expression(id=g._new_id(), latex=latex,
                   **_opt_style(color=color, line_width=line_width, line_style=line_style))
    return g._add(e)


def rectangle(g, anchor, width, height, *, color=None, fill_opacity=None,
              line_width=None, line_style=None):
    x = LatexExpr(_latex_of(anchor[0]))
    y = LatexExpr(_latex_of(anchor[1]))
    w = LatexExpr(_latex_of(width))
    h = LatexExpr(_latex_of(height))
    pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    parts = ",".join(rf"\left({px.latex},{py.latex}\right)" for px, py in pts)
    latex = rf"\operatorname{{polygon}}\left({parts}\right)"
    style = _opt_style(color=color, line_width=line_width, line_style=line_style)
    if fill_opacity is not None:
        style["fill"] = True
        style["fill_opacity"] = str(fill_opacity)
    return g._add(Expression(id=g._new_id(), latex=latex, **style))


def point(g, position, *, draggable=None, color=None, label=None,
          point_style=None, point_size=None):
    x, y = position
    latex = rf"\left({_latex_of(x)},{_latex_of(y)}\right)"
    style = _opt_style(color=color, point_style=point_style, point_size=point_size)
    if label is not None:
        style["label"] = label
        style["show_label"] = True
    if draggable is not None:
        style["drag_mode"] = draggable  # "X" | "Y" | "XY" | "NONE"
    return g._add(Expression(id=g._new_id(), latex=latex, **style))


def line(g, p1, p2, *, color=None, line_width=None, line_style=None):
    parts = ",".join(rf"\left({_latex_of(p[0])},{_latex_of(p[1])}\right)" for p in (p1, p2))
    latex = rf"\operatorname{{polygon}}\left({parts}\right)"
    return g._add(Expression(
        id=g._new_id(), latex=latex,
        **_opt_style(color=color, line_width=line_width, line_style=line_style),
    ))


def arrow(g, p1, p2, *, color=None, head_size=0.15, line_width=None):
    """Draw an arrow from ``p1`` to ``p2`` with a filled triangle head.

    Endpoints must be plain numbers (the head geometry is precomputed in Python).
    For vector fields with dynamic endpoints, use ``line`` with vectorised
    LaTeX or build the head LaTeX yourself.
    """
    import math
    x1, y1 = float(p1[0]), float(p1[1])
    x2, y2 = float(p2[0]), float(p2[1])
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length == 0:
        return line(g, p1, p2, color=color, line_width=line_width)
    ux, uy = dx / length, dy / length              # unit along arrow
    nx, ny = -uy, ux                                # unit perpendicular
    bx, by = x2 - ux * head_size, y2 - uy * head_size
    lx, ly = bx + nx * head_size * 0.5, by + ny * head_size * 0.5
    rx, ry = bx - nx * head_size * 0.5, by - ny * head_size * 0.5
    pts = [(x1, y1), (x2, y2), (lx, ly), (x2, y2), (rx, ry)]
    parts = ",".join(rf"\left({_latex_of(px)},{_latex_of(py)}\right)" for px, py in pts)
    latex = rf"\operatorname{{polygon}}\left({parts}\right)"
    return g._add(Expression(
        id=g._new_id(), latex=latex,
        **_opt_style(color=color, line_width=line_width),
    ))


def text(g, label, position, *, color=None):
    x, y = position
    latex = rf"\left({_latex_of(x)},{_latex_of(y)}\right)"
    return g._add(Expression(
        id=g._new_id(), latex=latex, label=label, show_label=True,
        point_style="OPEN", point_size="1",
        **_opt_style(color=color),
    ))
