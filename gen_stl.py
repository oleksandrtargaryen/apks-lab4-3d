#!/usr/bin/env python3
"""Лабораторна робота №4 (АПКС): 3D-модель цифри «8» → STL (контрольна модель).

Ті самі 2D-контури, що й у gen_dxf.py, і ті самі операції, що в AutoCAD / Fusion 360:
  тіло      = Extrude(цифра, 10 мм)
  прізвище  = Union(тіло, Extrude(БАРТОШКО, 2 мм) на верхній грані)        — опуклий
  ім'я      = Subtract(тіло, Extrude(ОЛЕКСАНДР, 1.5 мм) від верхньої грані) — увігнутий
  по батькові = Subtract(тіло, Extrude(ІГОРОВИЧ, 12 мм) наскрізь)           — наскрізний

Залежності: manifold3d, trimesh (+ залежності gen_dxf.py).
Запуск: python gen_stl.py -> stl/digit8.stl
"""
from pathlib import Path

import numpy as np
import trimesh
from fontTools.ttLib import TTFont
from manifold3d import CrossSection, FillRule, Manifold

from gen_dxf import FONT, TEXT_H, TEXTS, THICK, W, digit8, iter_polys, text_polygons

RAISE, ENGRAVE, THROUGH = 2.0, 1.5, 12.0


def extrude(geom, height, z0=0.0):
    """shapely (Multi)Polygon -> Manifold-призма висотою height від z0."""
    contours = []
    for p in iter_polys(geom):
        contours.append(np.asarray(p.exterior.coords[:-1]))
        contours += [np.asarray(h.coords[:-1]) for h in p.interiors]
    cs = CrossSection(contours, FillRule.EvenOdd)
    return Manifold.extrude(cs, height).translate((0, 0, z0))


def main():
    root = Path(__file__).resolve().parent
    font = TTFont(FONT)
    t = {layer: text_polygons(s, font, W / 2, cy, TEXT_H) for layer, s, cy, _, _ in TEXTS}

    body = extrude(digit8(), THICK)
    body = body + extrude(t["SURNAME"], RAISE, THICK)                 # Union / Join
    body = body - extrude(t["NAME"], ENGRAVE + 1, THICK - ENGRAVE)    # Subtract / Cut
    body = body - extrude(t["PATRONYMIC"], THROUGH, -1.0)             # Subtract наскрізь

    m = body.to_mesh()
    mesh = trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts, process=True)
    assert mesh.is_watertight and mesh.is_volume, "сітка не замкнена"
    (root / "stl").mkdir(exist_ok=True)
    out = root / "stl" / "digit8.stl"
    mesh.export(out)
    ext = mesh.bounds[1] - mesh.bounds[0]
    print(f"OK: {out}")
    print(f"габарит {ext[0]:.1f} × {ext[1]:.1f} × {ext[2]:.1f} мм, "
          f"об'єм {mesh.volume / 1000:.2f} см³, трикутників {len(mesh.faces)}, "
          f"genus {body.genus()}")


if __name__ == "__main__":
    main()
