# АПКС — Лабораторна робота №4: 3D-моделювання та підготовка до 3D-друку

**Студент:** Бартошко Олександр Ігорович, група КІ-408 → **цифра 8**  
**Дисципліна:** Автоматизоване проєктування комп'ютерних систем

| Файл | Призначення |
|---|---|
| `gen_dxf.py` | генерація контуру цифри «8» і контурів тексту ПІБ у DXF (+ самоперевірка, що текст лежить на матеріалі) |
| `dxf/digit8_only.dxf`, `dxf/digit8_full.dxf` | 2D-контури для AutoCAD / Fusion 360 |
| `docs/guide.md` | покрокова інструкція: AutoCAD → Fusion 360 → Ultimaker Cura |
| `docs/img/preview_2d.png` | попередній перегляд розташування написів |
| `gen_stl.py` | контрольна 3D-модель: ті самі Extrude / Union / Subtract у коді (manifold3d) → `stl/digit8.stl`, перевірка замкненості сітки |
| `stl/digit8.stl` | STL 100 × 140 × 12 мм, ≈ 81 см³ |
| `docs/img/cura_*.png` | Cura: налаштування (UltiMaker S5, 0.2 мм, 20 %, Brim) → 2 год 37 хв, 50 г; пошаровий перегляд |

Прізвище — опуклий текст, ім'я — увігнутий, по батькові — наскрізний.

```bash
pip install ezdxf fonttools shapely matplotlib
python3 gen_dxf.py

# STL (manifold3d має колеса для Python ≤ 3.13)
uv venv -p 3.12 .venv3d && uv pip install -p .venv3d/bin/python manifold3d trimesh ezdxf fonttools shapely matplotlib
.venv3d/bin/python gen_stl.py
```
