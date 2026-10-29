"""Validasi terhadap ground truth simulasi (HANYA skrip ini yang membaca data/sim/ground_truth.json).

Cek yang dilakukan:
1. Deteksi tiap fault yang ditanam: run pertama setelah onset yang kena alert, dan delay dalam run.
2. False alarm: alert di run yang tidak berada di jendela fault mana pun, setelah baseline.
3. Cpk bergulir < 1,33: tanggal pertama per aliran.
4. Kualitas data: jumlah file kotor di ground truth vs file yang punya entri log.
5. Uji pemulihan (Monte Carlo): proses sintetis dengan limit dari outputs/spc_limits.csv.
   ARL0 (false alarm per run) dan ARL1 (delay rata-rata) untuk pergeseran 1, 2, 3 sigma.

Output: outputs/validation.csv, outputs/arl_recovery.csv
"""
import json

import numpy as np
import pandas as pd

from importlib import util as _u
spec = _u.spec_from_file_location("spc", "src/02_spc.py")
spc = _u.module_from_spec(spec)
spec.loader.exec_module(spc)

GT = json.load(open("data/sim/ground_truth.json", encoding="utf-8"))
WINDOWS = {
    "F1 Model B after_oven drift": {"stream": "Model B | after_oven", "start": "2026-05-26", "end": "2026-06-30"},
    "F2 Model A before_oven mendadak (Shift 2)": {"stream": "Model A | before_oven", "start": "2026-05-01", "end": "2026-05-03", "shift": "Shift 2"},
    "F3 PT-02 sebaran membesar": {"stream": "*", "machine": "PT-02", "start": "2026-04-15", "end": "2026-04-28"},
}

runs = pd.read_csv("outputs/spc_runs.csv")
runs["test_date"] = pd.to_datetime(runs.test_date)
lim = pd.read_csv("outputs/spc_limits.csv")
rc = pd.read_csv("data/clean/cpk_rolling.csv")
rc["test_date"] = pd.to_datetime(rc.test_date)
spc_base = pd.Timestamp(spc.BASELINE_END)

def in_window(row):
    for name, w in WINDOWS.items():
        if w["stream"] not in ("*", row.stream):
            continue
        if "machine" in w:
            if row.machine != w["machine"]:
                continue
        if "shift" in w:
            if row["shift"] != w["shift"]:
                continue
        if pd.Timestamp(w["start"]) <= row.test_date <= pd.Timestamp(w["end"]):
            return name
    return ""

runs["fault_window"] = runs.apply(in_window, axis=1)
rows = []
# 1. deteksi per fault
for name, w in WINDOWS.items():
    sub = runs[runs.fault_window == name]
    if w["stream"] == "*":
        streams = sorted(sub.stream.unique())
    else:
        streams = [w["stream"]]
    for s in streams:
        ss = runs[(runs.stream == s)].copy()
        cand = ss[(ss.fault_window == name)]
        hit_x = cand[cand.alert_x]
        hit_r = cand[cand.alert_r]
        first_x = hit_x.test_date.min() if len(hit_x) else pd.NaT
        first_r = hit_r.test_date.min() if len(hit_r) else pd.NaT
        n_before = int((cand.test_date <= first_x).sum()) if len(hit_x) else np.nan
        rows.append({"cek": "deteksi", "fault": name, "stream": s, "n_run_di_jendela": len(cand),
                     "alert_xbar_pertama": "" if pd.isna(first_x) else first_x.date().isoformat(),
                     "run_ke_alert_xbar": n_before,
                     "alert_R_pertama": "" if pd.isna(first_r) else first_r.date().isoformat(),
                     "n_alert_xbar_di_jendela": len(hit_x), "n_alert_R_di_jendela": len(hit_r)})

# 2. false alarm: alert di luar jendela fault, setelah baseline
post = runs[runs.test_date >= spc_base]
outside = post[post.fault_window == ""]
for s, g in outside.groupby("stream"):
    fx, fr = int(g.alert_x.sum()), int(g.alert_r.sum())
    rows.append({"cek": "false_alarm", "fault": "di luar jendela", "stream": s, "n_run_di_jendela": len(g),
                 "alert_xbar_pertama": "", "run_ke_alert_xbar": "", "alert_R_pertama": "",
                 "n_alert_xbar_di_jendela": fx, "n_alert_R_di_jendela": fr})
n_out = len(outside)
rows.append({"cek": "false_alarm_rate", "fault": "semua aliran di luar jendela", "stream": "gabungan",
             "n_run_di_jendela": n_out,
             "alert_xbar_pertama": f"{outside.alert_x.mean():.4f}", "run_ke_alert_xbar": "",
             "alert_R_pertama": f"{outside.alert_r.mean():.4f}", "n_alert_xbar_di_jendela": int(outside.alert_x.sum()),
             "n_alert_R_di_jendela": int(outside.alert_r.sum())})

# 3. Cpk bergulir < 1,33 pertama per aliran
for s, g in rc.groupby("stream"):
    hit = g[g.below_133]
    rows.append({"cek": "cpk_rolling_below_1_33", "fault": "", "stream": s, "n_run_di_jendela": len(g),
                 "alert_xbar_pertama": hit.test_date.min().date().isoformat() if len(hit) else "",
                 "run_ke_alert_xbar": "", "alert_R_pertama": "", "n_alert_xbar_di_jendela": int(len(hit)),
                 "n_alert_R_di_jendela": ""})

# 4. kualitas data
pl = pd.read_csv("outputs/parse_log.csv")
files_with_issue = pl.file.nunique()
rows.append({"cek": "file_kotor", "fault": f"ground truth {GT['facts'][4]['n_files']} file", "stream": "data",
             "n_run_di_jendela": GT["n_runs"], "alert_xbar_pertama": "", "run_ke_alert_xbar": "",
             "alert_R_pertama": "", "n_alert_xbar_di_jendela": files_with_issue, "n_alert_R_di_jendela": ""})

# 5. fakta 4: setelah oven > sebelum oven (rata-rata baseline per model)
b = lim.set_index("stream")
rows.append({"cek": "fakta4_after_gt_before", "fault": "Model A", "stream": "Model A",
             "n_run_di_jendela": "", "alert_xbar_pertama": "",
             "run_ke_alert_xbar": "", "alert_R_pertama": "",
             "n_alert_xbar_di_jendela": round(float(b.loc["Model A | after_oven", "xbar_cl_g"] - b.loc["Model A | before_oven", "xbar_cl_g"]), 1),
             "n_alert_R_di_jendela": ""})

pd.DataFrame(rows).to_csv("outputs/validation.csv", index=False)

# 6. uji pemulihan: Monte Carlo ARL
rng = np.random.default_rng(15260401)
arl = []
L = 200          # run per simulasi
REP = 2000
for shift_sd in [0.0, 1.0, 2.0, 3.0]:
    base_mu = float(b.loc["Model A | before_oven", "xbar_cl_g"])
    sig_x = float(b.loc["Model A | before_oven", "sigma_within_g"]) / np.sqrt(spc.N)
    cl = base_mu
    ucl, lcl = cl + 3 * sig_x, cl - 3 * sig_x
    delays, fa_count, fa_runs = [], 0, 0
    for _ in range(REP):
        onset = L // 2
        x = rng.normal(cl, sig_x, L)
        x[onset:] += shift_sd * sig_x
        flags = np.zeros(L, bool)
        r1, r2, r4 = spc.we_flags(x, cl, sig_x)
        flags = r1 | r2 | r4
        pre = flags[:onset]
        fa_count += int(pre.any())
        fa_runs += onset
        post = np.where(flags[onset:])[0]
        if shift_sd > 0:
            delays.append(post[0] + 1 if len(post) else L - onset)
    arl.append({"pergeseran_sigma": shift_sd, "replikasi": REP,
                "ARL0_false_alarm_per_run": (fa_count / fa_runs) if shift_sd == 0 else "",
                "ARL1_rata_run": float(np.mean(delays)) if delays else "",
                "P_alert_sebelum_onset": (fa_count / REP) if shift_sd == 0 else ""})
pd.DataFrame(arl).to_csv("outputs/arl_recovery.csv", index=False)
print(pd.DataFrame(rows).to_string(index=False))
print(pd.DataFrame(arl).to_string(index=False))
