from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Expression:
    """A single entry in the Desmos expressions list."""
    id: str
    latex: str = ""
    color: str | None = None
    hidden: bool = False
    secret: bool = False
    label: str | None = None
    show_label: bool = False
    drag_mode: str | None = None  # "X", "Y", "XY", "NONE"
    slider: dict[str, Any] | None = None
    clickable_info: dict[str, Any] | None = None
    color_latex: str | None = None
    points: bool | None = None
    lines: bool | None = None
    fill: bool | None = None
    fill_opacity: str | None = None
    line_width: str | None = None
    line_style: str | None = None  # "SOLID", "DASHED", "DOTTED"
    point_style: str | None = None  # "POINT", "OPEN", "CROSS"
    point_size: str | None = None

    def to_state(self) -> dict[str, Any]:
        d: dict[str, Any] = {"type": "expression", "id": self.id, "latex": self.latex}
        if self.color is not None:        d["color"] = self.color
        if self.hidden:                   d["hidden"] = True
        if self.secret:                   d["secret"] = True
        if self.label is not None:        d["label"] = self.label
        if self.show_label:               d["showLabel"] = True
        if self.drag_mode is not None:    d["dragMode"] = self.drag_mode
        if self.slider is not None:       d["slider"] = self.slider
        if self.clickable_info is not None: d["clickableInfo"] = self.clickable_info
        if self.color_latex is not None:  d["colorLatex"] = self.color_latex
        if self.points is not None:       d["points"] = self.points
        if self.lines is not None:        d["lines"] = self.lines
        if self.fill is not None:         d["fill"] = self.fill
        if self.fill_opacity is not None: d["fillOpacity"] = self.fill_opacity
        if self.line_width is not None:   d["lineWidth"] = self.line_width
        if self.line_style is not None:   d["lineStyle"] = self.line_style
        if self.point_style is not None:  d["pointStyle"] = self.point_style
        if self.point_size is not None:   d["pointSize"] = self.point_size
        return d
