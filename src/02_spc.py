"""SPC per aliran (Model x Kondisi): limit dari baseline, Western Electric, Cp/Cpk dengan CI.

Baseline: run included dengan test_date sebelum BASELINE_END (fase awal, dibekukan).
Limit X-bar/R dihitung dari baseline lalu diterapkan ke seluruh data berikutnya.
Skrip ini TIDAK membaca data/sim/ground_truth.json (itu hanya untuk 03_validate.py).

Output: outputs/spc_limits.csv, outputs/spc_runs.csv (per run: xbar, R, flag), outputs/spc_first_alerts.csv,
        data/clean/cpk_rolling.csv
"""
import os

import numpy as np
import pandas as pd

LSL, USL = 1500.0, 19000.0
N = 5
D2, D3, D4, A2 = 2.326, 0.0, 2.114, 0.577
BASELINE_END = "2026-04-15"          # fase awal: 1-14 April 2026 (sebelum fault pertama di 15 April)
ROLL = 30
Z = 1.959964
CPK_MIN = 1.33
STREAM = ["model", "condition"]


def cpk_parts(mean, sd):
    cp = (USL - LSL) / (6 * sd)
    cpk = min(USL - mean, mean - LSL) / (3 * sd)
    return cp, cpk


def cpk_ci(cpk, n):
    se = np.sqrt(1 / (9 * n) + cpk ** 2 / (2 * (n - 1)))
    return cpk - Z * se, cpk + Z * se


def we_flags(x, cl, sigma):
    """Western Electric: R1 (>3s), R2 (2 dari 3 > 2s sisi sama), R4 (8 berurutan sisi sama)."""
    n = len(x)
    z = (np.asarray(x) - cl) / sigma
    r1 = np.abs(z) > 3
    r2 = np.zeros(n, bool)
    r4 = np.zeros(n, bool)
    for i in range(n):
        if i >= 2:
            w = z[i - 2:i + 1]
            if (np.sum(w > 2) >= 2) or (np.sum(w < -2) >= 2):
                r2[i] = True
        if i >= 7:
            w = z[i - 7:i + 1]
            if np.all(w > 0) or np.all(w < 0):
                r4[i] = True
    return r1, r2, r4


def main():
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("data/clean", exist_ok=True)
    m = pd.read_csv("data/clean/measurements.csv")
    r = pd.read_csv("data/clean/runs.csv")
    r = r[r.status == "included"].copy()
    r = r.sort_values(["test_date", "run_id"], kind="mergesort").reset_index(drop=True)
    m = m[m.run_id.isin(r.run_id)]
    r["stream"] = r.model + " | " + r.condition
    m = m.merge(r[["run_id", "stream"]], on="run_id", how="left")

    limits, out_runs, first, roll_rows = [], [], [], []
    for s, rs in r.groupby("stream", sort=True):
        base = rs[rs.test_date < BASELINE_END]
        rbar = base.range_g.mean()
        xbar_cl = base.xbar_g.mean()
        sig = rbar / D2
        sig_x = sig / np.sqrt(N)
        ucl_x, lcl_x = xbar_cl + 3 * sig_x, xbar_cl - 3 * sig_x
        ucl_r, lcl_r = D4 * rbar, D3 * rbar
        bsamp = m[(m.stream == s) & (m.run_id.isin(base.run_id))].force_g
        cp, cpk = cpk_parts(bsamp.mean(), sig)
        lo, hi = cpk_ci(cpk, len(bsamp))
        limits.append({"stream": s, "n_baseline_run": len(base), "n_baseline_sampel": len(bsamp),
                       "xbar_cl_g": xbar_cl, "xbar_ucl_g": ucl_x, "xbar_lcl_g": lcl_x,
                       "rbar_g": rbar, "r_ucl_g": ucl_r, "r_lcl_g": lcl_r, "sigma_within_g": sig,
                       "cp": cp, "cpk": cpk, "cpk_ci_low": lo, "cpk_ci_high": hi})

        rs = rs.copy()
        rs["z_x"] = (rs.xbar_g - xbar_cl) / sig_x
        rs["r1_x"], rs["r2_x"], rs["r4_x"] = we_flags(rs.xbar_g.values, xbar_cl, sig_x)
        rs["r1_r"] = (rs.range_g > ucl_r) | (rs.range_g < lcl_r)
        rs["alert_x"] = rs.r1_x | rs.r2_x | rs.r4_x
        rs["alert_r"] = rs.r1_r
        rs["stream"] = s
        out_runs.append(rs)

        for flag, name in [("alert_x", "xbar (WE)"), ("alert_r", "R (>UCL)")]:
            hit = rs[rs[flag]]
            first.append({"stream": s, "chart": name, "n_alert": len(hit),
                          "first_run": hit.run_id.iloc[0] if len(hit) else "",
                          "first_date": hit.test_date.iloc[0] if len(hit) else ""})

        # Cpk bergulir (jendela ROLL run) dari semua sampel valid di jendela
        cur = m[m.stream == s].copy()
        order = rs.run_id.tolist()
        for i in range(len(order)):
            if i + 1 < ROLL:
                continue
            win = order[i + 1 - ROLL:i + 1]
            vals = cur[cur.run_id.isin(win)].force_g
            mu, sd = vals.mean(), vals.std(ddof=1)
            _, cpk_w = cpk_parts(mu, sd)
            roll_rows.append({"stream": s, "run_id": order[i], "test_date": rs.test_date.iloc[i],
                              "cpk_rolling": cpk_w, "below_133": cpk_w < CPK_MIN})

    lim = pd.DataFrame(limits)
    lim.to_csv("outputs/spc_limits.csv", index=False)
    runs_all = pd.concat(out_runs).sort_values(["stream", "test_date", "run_id"], kind="mergesort")
    runs_all.to_csv("outputs/spc_runs.csv", index=False)
    fa = pd.DataFrame(first).sort_values(["stream", "chart"], kind="mergesort")
    fa.to_csv("outputs/spc_first_alerts.csv", index=False)
    rc = pd.DataFrame(roll_rows).sort_values(["stream", "test_date", "run_id"], kind="mergesort")
    rc.to_csv("data/clean/cpk_rolling.csv", index=False)
    print(lim[["stream", "cpk", "cpk_ci_low", "cpk_ci_high"]].round(3).to_string(index=False))
    print(fa.to_string(index=False))


if __name__ == "__main__":
    main()
