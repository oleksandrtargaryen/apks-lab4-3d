"""Лабораторна №4, Етап 2 (Fusion 360): цифра «8» з написами ПІБ.

Імпортує dxf/digit8_full.dxf (окремий ескіз на кожен шар) і будує модель
операціями Extrude так, щоб у Timeline було видно New Body / Cut / Join / Cut / Cut:
  DIGIT       New Body 10 мм, вікна - Cut
  SURNAME     Join  +2 мм над верхньою гранню (дірки літер - Cut)
  NAME        Cut   -1.5 мм від верхньої грані (острівці літер - Join назад)
  PATRONYMIC  Cut   наскрізь, від -1 мм на 12 мм
Запуск: Utilities -> Add-Ins -> Scripts and Add-Ins -> «+» -> тека cad/fusion_build -> Run.
"""
import os
import traceback

import adsk.core
import adsk.fusion

HERE = os.path.dirname(os.path.realpath(__file__))
DXF = os.path.normpath(os.path.join(HERE, "..", "..", "dxf", "digit8_full.dxf"))
STL = os.path.normpath(os.path.join(HERE, "..", "..", "stl", "digit8_fusion.stl"))
THICK = 1.0  # см: API Fusion працює в сантиметрах -> 10 мм

OP = adsk.fusion.FeatureOperations


def profiles(sketch):
    col = adsk.core.ObjectCollection.create()
    for p in sketch.profiles:
        col.add(p)
    return col


def extrude(comp, sketch, op, start_mm, dist_mm, name, body=None):
    inp = comp.features.extrudeFeatures.createInput(profiles(sketch), op)
    inp.startExtent = adsk.fusion.OffsetStartDefinition.create(
        adsk.core.ValueInput.createByString(f"{start_mm} mm"))
    inp.setOneSideExtent(
        adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(f"{dist_mm} mm")),
        adsk.fusion.ExtentDirections.PositiveExtentDirection)
    if body is not None:
        inp.participantBodies = [body]
    f = comp.features.extrudeFeatures.add(inp)
    f.name = name
    return f


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        root = design.rootComponent

        opts = app.importManager.createDXF2DImportOptions(DXF, root.xYConstructionPlane)
        opts.isSingleSketchResult = False  # окремий ескіз на кожен шар DXF
        app.importManager.importToTarget(opts, root)
        sk = {s.name.upper(): s for s in root.sketches}

        def get(layer):
            # точний збіг: "NAME_OUTER" не повинен знаходити "SURNAME_OUTER"
            for name, s in sk.items():
                if name == layer or name.split(":")[-1].strip() == layer:
                    return s
            raise KeyError(f"немає ескізу для шару {layer}: {list(sk)}")

        body = extrude(root, get("DIGIT_OUTER"), OP.NewBodyFeatureOperation, 0, 10, "Digit Extrude").bodies.item(0)
        body.name = "Digit8"
        extrude(root, get("DIGIT_HOLES"), OP.CutFeatureOperation, 0, 10, "Digit windows Cut", body)
        extrude(root, get("SURNAME_OUTER"), OP.JoinFeatureOperation, 10, 2, "Surname Join +2", body)
        extrude(root, get("SURNAME_HOLES"), OP.CutFeatureOperation, 10, 2, "Surname holes Cut", body)
        extrude(root, get("NAME_OUTER"), OP.CutFeatureOperation, 8.5, 1.5, "Name Cut -1.5", body)
        extrude(root, get("NAME_HOLES"), OP.JoinFeatureOperation, 8.5, 1.5, "Name islands Join", body)
        extrude(root, get("PATRONYMIC_OUTER"), OP.CutFeatureOperation, -1, 12, "Patronymic Cut through", body)
        for s in root.sketches:
            s.isLightBulbOn = False

        vol_mm3 = sum(b.volume for b in root.bRepBodies) * 1000.0  # см3 -> мм3
        em = design.exportManager
        em.execute(em.createSTLExportOptions(body, STL))
        app.activeViewport.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
        app.activeViewport.fit()
        ui.messageBox(f"Готово.\nТіл: {root.bRepBodies.count}, об'єм {vol_mm3:,.0f} мм³ "
                      f"(контроль gen_stl.py ≈ 81 050)\nSTL: {STL}")
    except Exception:
        if ui:
            ui.messageBox("Помилка:\n" + traceback.format_exc())
