# -*- coding: utf-8 -*-
"""第 4 步：用云端 Dreapex TMM 独立核对自写 TMM。

云端模型完全按作业口径设置：Air / H / L / H / L / Glass，常数折射率，
正入射，400-800 nm 步长 10 nm。取若干代表性膜系比对。

结果写入 results/dreapex_crosscheck.json
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np

sys.path.insert(0, r"G:/工作/pi-workspace/薄膜技术/_过程文件")
from _tmm import call, fetch_blob  # noqa: E402
from _util import parse            # noqa: E402

sys.path.insert(0, "src")
import params as P   # noqa: E402
import tmm           # noqa: E402

WLS = [float(w) for w in P.WAVELENGTHS]


def deep_find(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = deep_find(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = deep_find(v, key)
            if r is not None:
                return r
    return None


def find_url(obj):
    if isinstance(obj, dict):
        for k in ("blobRef", "blobUrl", "fetchUrl", "url"):
            if isinstance(obj.get(k), str) and obj[k].startswith("http"):
                return obj[k]
        for v in obj.values():
            r = find_url(v)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_url(v)
            if r:
                return r
    return None


CASES = {
    "QW480": [tmm.quarter_wave_thickness(480.0, 2.30), tmm.quarter_wave_thickness(480.0, 1.45),
              tmm.quarter_wave_thickness(480.0, 2.30), tmm.quarter_wave_thickness(480.0, 1.45)],
    "QW600": [tmm.quarter_wave_thickness(600.0, 2.30), tmm.quarter_wave_thickness(600.0, 1.45),
              tmm.quarter_wave_thickness(600.0, 2.30), tmm.quarter_wave_thickness(600.0, 1.45)],
    "randA": [100.0, 60.0, 150.0, 90.0],
    "randB": [45.5, 179.9, 40.1, 120.3],
    "randC": [40.0, 40.0, 180.0, 180.0],
}

out = {"wavelengths_nm": WLS, "cases": {}}

for name, ds in CASES.items():
    ds = [float(round(x, 6)) for x in ds]
    mid = parse(call("model_create", {"label": "ai4s_crosscheck"}))["model_id"]
    call("structure_clearStructure", {"model_id": mid})
    call("surroundings_setSurroundingMedium",
         {"model_id": mid, "type": "incidence",
          "patch": {"name": "Air", "n": P.N_INCIDENT, "k": 0, "indexType": "Constant"}})
    call("surroundings_setSurroundingMedium",
         {"model_id": mid, "type": "transmission",
          "patch": {"name": "Glass", "n": P.N_SUBSTRATE, "k": 0, "indexType": "Constant"}})
    layers = [{"name": f"L{i+1}", "thickness": d, "indexType": "Constant", "n": n, "k": 0}
              for i, (d, n) in enumerate(zip(ds, [P.N_HIGH, P.N_LOW, P.N_HIGH, P.N_LOW]))]
    call("structure_replaceWithLayers", {"model_id": mid, "layers": layers})
    call("optics_setWavelengthSampling",
         {"model_id": mid, "wavelengthMode": "Sweep",
          "wavelengthFrom": 400.0, "wavelengthTo": 800.0, "wavelengthStep": 10.0})
    call("optics_setIncidentAngleAzimuth", {"model_id": mid, "incidentAngle": 0, "pRatio": 0.5})
    call("optics_setDetectors", {"model_id": mid, "detectorList": {"tmm": ["R", "T", "A"], "leda": []}})

    t0 = time.perf_counter()
    raw_res = parse(call("simulation_runCalculation", {"model_id": mid}))
    dt = time.perf_counter() - t0

    wl = deep_find(raw_res, "wavelength_list")
    R = deep_find(raw_res, "R_list")
    T = deep_find(raw_res, "T_list")
    if wl is None or R is None:
        url = find_url(raw_res)
        if url:
            blob = fetch_blob(url)
            wl = wl or deep_find(blob, "wavelength_list")
            R = R or deep_find(blob, "R_list")
            T = T or deep_find(blob, "T_list")
    if wl is None or R is None:
        out["cases"][name] = {"error": "no R_list in response", "keys": str(list(raw_res))[:300]}
        continue

    wl = np.asarray(wl, dtype=float)
    R = np.asarray(R, dtype=float)
    R_local = tmm.reflectance_char_matrix(ds, wl)[0]
    out["cases"][name] = {
        "thickness_nm": ds,
        "n_wavelengths": int(wl.size),
        "wavelength_match": bool(np.allclose(wl, WLS)),
        "R_dreapex": R.tolist(),
        "R_local": R_local.tolist(),
        "max_abs_diff": float(np.max(np.abs(R - R_local))),
        "run_seconds": dt,
    }
    print(f"{name}: max|dR| = {out['cases'][name]['max_abs_diff']:.3e}  "
          f"(wl match={out['cases'][name]['wavelength_match']}, {dt:.1f}s)")
    try:
        call("model_dispose", {"model_id": mid})
    except Exception:
        pass

diffs = [c.get("max_abs_diff") for c in out["cases"].values() if "max_abs_diff" in c]
out["summary"] = {"n_cases": len(diffs), "max_abs_diff": float(max(diffs)) if diffs else None}
print("\nsummary:", json.dumps(out["summary"], ensure_ascii=False))
(P.RES_DIR / "dreapex_crosscheck.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("written:", P.RES_DIR / "dreapex_crosscheck.json")
