"""Sensitivitas panjang baseline (A1): 7, 14 (default), dan 21 hari. Ini skrip validasi: membaca ground truth.

Untuk tiap baseline: limit per aliran, false alarm di luar jendela fault, dan deteksi tiap fault.
Output: outputs/baseline_sensitivity.csv
"""
import importlib.util as u

import numpy as np
import pandas as pd

spec = u.spec_from_file_location("spc", "src/02_spc.py")
spc = u.module_from_spec(spec)
spec.loader.exec_module(spc)

WINDOWS = [
    ("F1", "Model B | after_oven", None, "2026-05-26", "2026-06-30"),
    ("F2", "Model A | before_oven", "Shift 2", "2026-05-01", "2026-05-03"),
    ("F3", "*", "PT-02", "2026-04-15", "2026-04-28"),
]
VARIANTS = [("7 hari", "2026-04-08"), ("14 hari (default)", "2026-04-15"), ("21 hari", "2026-04-22")]

r = pd.read_csv("data/clean/runs.csv")
r = r[r.status == "included"].copy()
r["test_date"] = pd.to_datetime(r.test_date)
r["stream"] = r.model + " | " + r.condition


def window_of(row):
    for name, stream, machine_or_shift, s, e in WINDOWS:
        if stream not in ("*", row.stream):
            continue
        if name == "F3" and row.machine != "PT-02":
            continue
        if name == "F2" and row["shift"] != "Shift 2":
            continue
        if pd.Timestamp(s) <= row.test_date <= pd.Timestamp(e):
            return name
    return ""


r["fault"] = r.apply(window_of, axis=1)
rows = []
for label, end in VARIANTS:
    base_end = pd.Timestamp(end)
    alerts = {}
    for s, g in r.groupby("stream"):
        g = g.sort_values(["test_date", "run_id"], kind="mergesort").copy()
        base = g[g.test_date < base_end]
        rbar = base.range_g.mean()
        cl = base.xbar_g.mean()
        sig = rbar / spc.D2
        sig_x = sig / np.sqrt(spc.N)
        g["alert_x"] = False
        r1, r2, r4 = spc.we_flags(g.xbar_g.values, cl, sig_x)
        g["alert_x"] = r1 | r2 | r4
        g["alert_r"] = (g.range_g > spc.D4 * rbar) | (g.range_g < spc.D3 * rbar)
        alerts[s] = g
    allg = pd.concat(alerts.values())
    post = allg[(allg.test_date >= base_end) & (allg.fault == "")]
    rows.append({"baseline": label, "baseline_sampai_sebelum": end, "metrik": "false alarm xbar per run",
                 "nilai": round(post.alert_x.mean(), 4), "n": len(post)})
    rows.append({"baseline": label, "baseline_sampai_sebelum": end, "metrik": "false alarm R per run",
                 "nilai": round(post.alert_r.mean(), 4), "n": len(post)})
    for name, stream, _, s, e in WINDOWS:
        if stream == "*":
            streams = sorted(allg[allg.fault == name].stream.unique())
        else:
            streams = [stream]
        det = 0
        for st in streams:
            g = alerts[st]
            hit = g[(g.fault == name) & g.alert_x]
            det += int(len(hit) > 0)
        rows.append({"baseline": label, "baseline_sampai_sebelum": end, "metrik": f"{name} aliran terdeteksi (xbar)",
                     "nilai": det, "n": len(streams)})
pd.DataFrame(rows).to_csv("outputs/baseline_sensitivity.csv", index=False)
print(pd.DataFrame(rows).to_string(index=False))
