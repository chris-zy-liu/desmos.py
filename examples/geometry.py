"""Geometric primitives + buttons."""
from desmos import Graph


def main():
    g = Graph(bounds=(-5, 5, -5, 5), title="Geometry demo")

    r = g.slider("r", 0.1, 4, value=1.5, step=0.05)
    g.circle((0, 0), r, color="#2d70b3")
    g.rectangle((-2, -1), 1, 2, color="#c74440", fill_opacity=0.3)
    g.line((-4, -4), (4, 4), color="#388c46")
    g.point((1, 1), draggable="XY", color="#fa7e19", label="drag me")
    g.text("Origin", (0, 0), color="#000000")

    g.button("Grow",   at=( 4,  4), action=r.set(r * 1.2))
    g.button("Shrink", at=( 4,  3), action=r.set(r / 1.2))

    g.to_html("geometry.html")
    print("Wrote geometry.html")


if __name__ == "__main__":
    main()
