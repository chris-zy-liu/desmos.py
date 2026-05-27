"""Smoke test: a parabola y = a*x^2 with a slider, written to quickstart.html."""
from desmos import Graph


def main():
    g = Graph(bounds=(-10, 10, -10, 10), title="Quickstart")
    g.expr(r"a=1", slider={"hardMin": True, "hardMax": True, "min": "-5", "max": "5", "step": "0.1"})
    g.expr(r"y=a x^{2}", color="#c74440")
    out = g.to_html("quickstart.html")
    print(f"Wrote quickstart.html ({len(out)} bytes)")


if __name__ == "__main__":
    main()
