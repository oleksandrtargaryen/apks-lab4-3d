#!/usr/bin/env python3
"""Лабораторна робота №4 (АПКС): генерація 2D-контурів цифри «8» і тексту ПІБ у DXF.

Група КІ-408 → цифра 8. Цифра — заокруглений прямокутник із двома вікнами,
тобто три горизонтальні перемички; на кожній — один напис:
  верхня   — ПРІЗВИЩЕ   (опуклий, Extrude + Union/Join)
  середня  — ІМ'Я       (увігнутий, Extrude + Subtract/Cut)
  нижня    — ПО БАТЬКОВІ (наскрізний, Cut на всю товщину)

Шари DXF (окремо зовнішні контури та «дірки», щоб в AutoCAD працювали REGION/SUBTRACT):
  DIGIT_OUTER, DIGIT_HOLES, SURNAME_OUTER, SURNAME_HOLES,
  NAME_OUTER, NAME_HOLES, PATRONYMIC_OUTER, PATRONYMIC_HOLES

Залежності: ezdxf, fonttools, shapely, matplotlib.
Запуск: python3 gen_dxf.py  -> dxf/digit8_full.dxf, dxf/digit8_only.dxf, docs/img/preview_2d.png
"""
from pathlib import Path

import ezdxf
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

# Геометрія цифри, мм
W, H = 100.0, 140.0          # габарит
SIDE = 18.0                  # ширина вертикальних стінок
BAR = 20.0                   # висота горизонтальних перемичок
R_OUT, R_IN = 22.0, 8.0      # радіуси заокруглень зовні / у вікнах
THICK = 10.0                 # товщина цифри (висота екструзії)
TEXT_H = 8.0                 # висота великих літер
TOP_INSET = 6.0              # верхнє кільце вужче на 2×6 мм
MID_Y0, MID_Y1 = 60.0, 80.0  # перекриття кілець (середня перемичка)

TEXTS = [  # (шар, рядок, центр Y перемички, тип операції, глибина)
    ("SURNAME", "БАРТОШКО", H - BAR / 2, "опуклий (Union/Join)", "+2.0 мм над поверхнею"),
    ("NAME", "ОЛЕКСАНДР", (MID_Y0 + MID_Y1) / 2 + 1, "увігнутий (Subtract/Cut)", "−1.5 мм у глибину"),
    ("PATRONYMIC", "ІГОРОВИЧ", BAR / 2, "наскрізний (Subtract/Cut)", f"> {THICK} мм (наскрізь, 12 мм)"),
]


def rounded_rect(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=16)


def digit8():
    # Класична «8»: верхнє кільце вужче за нижнє, у місці стику — «талія».
    top = rounded_rect(TOP_INSET, MID_Y0, W - TOP_INSET, H, R_OUT)
    bottom = rounded_rect(0, 0, W, MID_Y1, R_OUT + 2)
    outer = unary_union([top, bottom])
    w_low = rounded_rect(SIDE, BAR, W - SIDE, MID_Y0 - 2, R_IN)
    w_up = rounded_rect(TOP_INSET + SIDE - 2, MID_Y1 + 4, W - TOP_INSET - SIDE + 2, H - BAR, R_IN)
    return outer.difference(w_low).difference(w_up)


class FlatPen(BasePen):
    """Перетворює контури гліфа (криві Безьє) на ламані."""

    def __init__(self, glyphset, steps=8):
        super().__init__(glyphset)
        self.contours, self.cur, self.steps = [], [], steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            self.cur.append((mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0],
                             mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            self.cur.append((mt**2 * p0[0] + 2 * mt * t * p1[0] + t**2 * p2[0],
                             mt**2 * p0[1] + 2 * mt * t * p1[1] + t**2 * p2[1]))

    def _closePath(self):
        if len(self.cur) > 2:
            self.contours.append(self.cur)
        self.cur = []


def text_polygons(text, font, cx, cy, cap_h):
    """Повертає shapely-геометрію напису з центром (cx, cy) і висотою великих літер cap_h."""
    cmap, gs = font.getBestCmap(), font.getGlyphSet()
    cap = font["OS/2"].sCapHeight or font["head"].unitsPerEm * 0.716
    k = cap_h / cap
    x, polys = 0.0, []
    for ch in text:
        gname = cmap[ord(ch)]
        pen = FlatPen(gs)
        gs[gname].draw(pen)
        rings = [Polygon([(x + px, py) for px, py in c]) for c in pen.contours]
        # even-odd: зовнішні контури мінус внутрішні (дірки літер О, Р, А, Д, Б …)
        geom = None
        for r in sorted(rings, key=lambda p: -abs(p.area)):
            r = r.buffer(0)
            geom = r if geom is None else (geom.difference(r) if geom.contains(r) else geom.union(r))
        if geom is not None:
            polys.append(geom)
        x += gs[gname].width
    g = unary_union(polys)
    minx, miny, maxx, maxy = g.bounds
    from shapely import affinity
    g = affinity.translate(g, -(minx + maxx) / 2, -cap / 2)
    g = affinity.scale(g, k, k, origin=(0, 0))
    return affinity.translate(g, cx, cy)


def iter_polys(g):
    return list(g.geoms) if hasattr(g, "geoms") else [g]


def add_geom(msp, g, layer):
    for p in iter_polys(g):
        msp.add_lwpolyline(list(p.exterior.coords)[:-1], close=True, dxfattribs={"layer": f"{layer}_OUTER"})
        for hole in p.interiors:
            msp.add_lwpolyline(list(hole.coords)[:-1], close=True, dxfattribs={"layer": f"{layer}_HOLES"})


def new_doc():
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    colors = {"DIGIT": 7, "SURNAME": 1, "NAME": 3, "PATRONYMIC": 5}
    for name, c in colors.items():
        doc.layers.add(f"{name}_OUTER", color=c)
        doc.layers.add(f"{name}_HOLES", color=c)
    return doc


def main():
    root = Path(__file__).resolve().parent
    font = TTFont(FONT)
    d8 = digit8()
    texts = {layer: text_polygons(s, font, W / 2, cy, TEXT_H) for layer, s, cy, _, _ in TEXTS}

    # Самоперевірка: кожен напис повністю на матеріалі цифри з запасом ≥ 1.5 мм
    for layer, g in texts.items():
        assert d8.buffer(-1.5).contains(g), f"{layer}: напис виходить за матеріал цифри"
        minx, _, maxx, _ = g.bounds
        print(f"{layer:10s} ширина {maxx - minx:5.1f} мм, площа {g.area:6.1f} мм²")
    assert d8.is_valid and len(list(d8.interiors)) == 2

    (root / "dxf").mkdir(exist_ok=True)
    doc = new_doc()
    add_geom(doc.modelspace(), d8, "DIGIT")
    doc.saveas(root / "dxf" / "digit8_only.dxf")
    for layer, g in texts.items():
        add_geom(doc.modelspace(), g, layer)
    doc.saveas(root / "dxf" / "digit8_full.dxf")

    # Попередній перегляд
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(5.5, 7.2))
    def fill(g, **kw):
        for p in iter_polys(g):
            ax.fill(*p.exterior.xy, **kw)
            for h in p.interiors:
                ax.fill(*h.xy, color="white")
    fill(d8, color="#c9ced6", ec="#333")
    fill(texts["SURNAME"], color="#d64545")
    fill(texts["NAME"], color="#2f9e44")
    fill(texts["PATRONYMIC"], color="#1c7ed6")
    ax.set_aspect("equal")
    ax.set_title("Цифра 8 (КІ-408): червоний — опуклий, зелений — увігнутий,\nсиній — наскрізний", fontsize=8)
    ax.set_xlabel("мм")
    (root / "docs" / "img").mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(root / "docs" / "img" / "preview_2d.png", dpi=160)
    print("OK:", root / "dxf" / "digit8_full.dxf")


if __name__ == "__main__":
    main()
