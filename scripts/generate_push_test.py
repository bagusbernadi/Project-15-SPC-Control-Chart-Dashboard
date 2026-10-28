"""Project 15: data simulasi file CSV mesin push test (perekatan lensa lampu depan). Seed tetap.

Satu file per run, 5 sampel per run, gaya dalam gram (format angka koma, pemisah titik koma).
2 model x 2 kondisi (sebelum/sesudah oven) x 2 mesin, +-3 bulan, 600 run (3.000 baris hasil ukur).
Hasil (data/sim/): runs/*.csv (file mesin), ground_truth.json. Spec: LSL 1.500 g, USL 19.000 g.
Jalankan: python scripts/generate_push_test.py   (versi data: v1)
"""
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sim"
SEED = 15260401
DATA_VERSION = "v1"
LSL, USL = 1500.0, 19000.0
START = date(2026, 4, 1)
N_DAYS = 91                       # Apr - Jun 2026
RUNS_PER_DAY = 7                  # 91 hari x 7 = 637 -> dipangkas ke 600
N_RUNS = 600
SAMPLES = 5
MODELS = ["Model A", "Model B"]
CONDS = ["before_oven", "after_oven"]
COND_TAG = {"before_oven": "SebelumOven", "after_oven": "SetelahOven"}
MACHINES = ["PT-01", "PT-02"]
BASE = {("Model A", "before_oven"): 7200.0, ("Model A", "after_oven"): 8600.0,
        ("Model B", "before_oven"): 6800.0, ("Model B", "after_oven"): 8300.0}
UNIT_SD, RUN_SD = 850.0, 150.0

# Fakta tertanam
DRIFT_B = dict(model="Model B", cond="after_oven", start_day=55, ramp_days=7, drop_g=5400.0)      # turun bertahap +-1 minggu
SUDDEN_A = dict(model="Model A", cond="before_oven", start_day=30, length_days=3, shift="Shift 2", drop_g=2600.0)
WIDE_MACHINE = dict(machine="PT-02", start_day=14, length_days=14, sd_factor=1.9)
DIRTY_RATE = 0.025                 # +-2,5% file kotor

rng = np.random.default_rng(SEED)


def fmt(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


runs = []
for day in range(N_DAYS):
    for _ in range(RUNS_PER_DAY):
        if len(runs) >= N_RUNS:
            break
        model = MODELS[int(rng.integers(0, 2))]
        cond = CONDS[int(rng.integers(0, 2))]
        runs.append(dict(day=day, model=model, cond=cond,
                         machine=MACHINES[int(rng.integers(0, 2))],
                         shift="Shift 1" if rng.random() < 0.5 else "Shift 2"))

dirty = set(int(i) for i in rng.choice(len(runs), int(round(DIRTY_RATE * len(runs))), replace=False))
(OUT / "runs").mkdir(parents=True, exist_ok=True)
rows_total, ng_total = 0, 0
for i, r in enumerate(runs):
    mu = BASE[(r["model"], r["cond"])] + rng.normal(0, RUN_SD)
    sd = UNIT_SD
    if r["model"] == DRIFT_B["model"] and r["cond"] == DRIFT_B["cond"] and r["day"] >= DRIFT_B["start_day"]:
        mu -= DRIFT_B["drop_g"] * min(1.0, (r["day"] - DRIFT_B["start_day"] + 1) / DRIFT_B["ramp_days"])
    if (r["model"] == SUDDEN_A["model"] and r["cond"] == SUDDEN_A["cond"] and r["shift"] == SUDDEN_A["shift"]
            and SUDDEN_A["start_day"] <= r["day"] < SUDDEN_A["start_day"] + SUDDEN_A["length_days"]):
        mu -= SUDDEN_A["drop_g"]
    if r["machine"] == WIDE_MACHINE["machine"] and WIDE_MACHINE["start_day"] <= r["day"] < WIDE_MACHINE["start_day"] + WIDE_MACHINE["length_days"]:
        sd *= WIDE_MACHINE["sd_factor"]
    vals = np.round(rng.normal(mu, sd, SAMPLES), 1)
    ng_total += int(np.sum((vals < LSL) | (vals > USL)))
    rows_total += SAMPLES
    d = START + timedelta(days=r["day"])
    name = f"R{i + 1:04d}_{r['model'].replace(' ', '')}_{COND_TAG[r['cond']]}.csv"
    lines = ["Test Program;DS20KG", "Test Mode;Destructive", f"Run ID;R{i + 1:04d}",
             f"Test Date;{d.strftime('%d/%m/%Y')}", f"Shift;{r['shift']}", f"Machine;{r['machine']}",
             f"Model;{r['model']}", f"Condition;{r['cond']}",
             f"LSL (g);{fmt(LSL, 0)}", f"USL (g);{fmt(USL, 0)}", "Sample No;Force (g)"]
    body = [f"{j + 1};{fmt(v)}" for j, v in enumerate(vals)]
    if i in dirty:                                   # data kotor: gaya kosong, nol, atau baris ganda
        k = int(rng.integers(0, 3))
        if k == 0:
            body[int(rng.integers(0, SAMPLES))] = f"{int(rng.integers(1, SAMPLES + 1))};"
        elif k == 1:
            body[int(rng.integers(0, SAMPLES))] = f"{int(rng.integers(1, SAMPLES + 1))};{fmt(0.0)}"
        else:
            body.append(body[int(rng.integers(0, SAMPLES))])
    (OUT / "runs" / name).write_text("\n".join(lines + body) + "\n", encoding="utf-8")

gt = {"seed": SEED, "version": DATA_VERSION, "n_runs": len(runs), "n_rows_clean": rows_total,
      "lsl_g": LSL, "usl_g": USL, "ng_values_clean": ng_total,
      "facts": [
          {"id": 1, "fact": "Model B setelah oven turun bertahap", "from": str(START + timedelta(days=DRIFT_B["start_day"])),
           "ramp_days": DRIFT_B["ramp_days"], "drop_g": DRIFT_B["drop_g"]},
          {"id": 2, "fact": "Model A sebelum oven turun mendadak 3 hari di Shift 2",
           "from": str(START + timedelta(days=SUDDEN_A["start_day"])), "days": SUDDEN_A["length_days"], "drop_g": SUDDEN_A["drop_g"]},
          {"id": 3, "fact": "Mesin PT-02 sebaran membesar", "from": str(START + timedelta(days=WIDE_MACHINE["start_day"])),
           "days": WIDE_MACHINE["length_days"], "sd_factor": WIDE_MACHINE["sd_factor"]},
          {"id": 4, "fact": "Setelah oven lebih tinggi daripada sebelum oven", "base_g": {f"{k[0]}|{k[1]}": v for k, v in BASE.items()}},
          {"id": 5, "fact": "File kotor", "n_files": len(dirty), "rate": DIRTY_RATE}]}
(OUT / "ground_truth.json").write_text(json.dumps(gt, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"{len(runs)} file, {rows_total} baris hasil ukur, {len(dirty)} file kotor -> {OUT / 'runs'}")
