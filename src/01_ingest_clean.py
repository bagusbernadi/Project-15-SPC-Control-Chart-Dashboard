"""Baca file CSV mesin push test (format ';' dan koma desimal), bersihkan, dan buat tabel run.

Input : data/sim/runs/*.csv
Output: data/clean/measurements.csv (1 baris = 1 sampel valid)
        data/clean/runs.csv         (1 baris = 1 run, xbar, R, status subgroup)
        outputs/parse_log.csv      (setiap sampel/file yang dibuang atau diubah)
Aturan:
- nilai kosong dibuang (log).
- nilai 0 g dibuang: tidak fisik untuk uji ini (log).
- nomor sampel ganda dalam satu file: baris pertama dipertahankan (log).
- run dipakai untuk X-bar/R hanya jika tepat 5 sampel valid (n = 5). Run lain ditandai 'excluded'.
"""
import csv
import os
import re
from pathlib import Path

import pandas as pd

SRC = Path("data/sim/runs")
SUBGROUP_N = 5
LOG = []


def num(s):
    return float(s.strip().replace(",", "."))


def parse_file(path):
    meta, samples = {}, []
    header_done = False
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            if not header_done:
                if line.startswith("Sample No;"):
                    header_done = True
                    continue
                k, _, v = line.partition(";")
                meta[k.strip()] = v.strip()
                continue
            j, _, v = line.partition(";")
            samples.append((j.strip(), v.strip()))
    return meta, samples


def main():
    os.makedirs("data/clean", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    meas, runs = [], []
    for path in sorted(SRC.glob("*.csv")):
        meta, samples = parse_file(path)
        run_id = meta["Run ID"]
        seen = set()
        valid = []
        for sno, raw in samples:
            if not re.fullmatch(r"\d+", sno):
                LOG.append([run_id, path.name, sno, raw, "dibuang", "nomor sampel tidak valid"])
                continue
            if sno in seen:
                LOG.append([run_id, path.name, sno, raw, "dibuang", "nomor sampel ganda"])
                continue
            seen.add(sno)
            if raw == "":
                LOG.append([run_id, path.name, sno, raw, "dibuang", "nilai kosong"])
                continue
            v = num(raw)
            if v == 0:
                LOG.append([run_id, path.name, sno, raw, "dibuang", "nol gram"])
                continue
            valid.append((int(sno), v))
        # Catatan: urutan sampel dari file, untuk tie-breaker
        valid.sort()
        for sno, v in valid:
            meas.append({"run_id": run_id, "test_date": pd.to_datetime(meta["Test Date"], format="%d/%m/%Y").date().isoformat(),
                         "shift": meta["Shift"], "machine": meta["Machine"], "model": meta["Model"],
                         "condition": meta["Condition"], "sample_no": sno, "force_g": v, "file": path.name})
        n_valid = len(valid)
        status = "included" if n_valid == SUBGROUP_N else "excluded"
        if n_valid != SUBGROUP_N:
            LOG.append([run_id, path.name, "", "", "run dikecualikan", f"n valid = {n_valid}, butuh {SUBGROUP_N}"])
        vals = [v for _, v in valid]
        runs.append({"run_id": run_id, "test_date": pd.to_datetime(meta["Test Date"], format="%d/%m/%Y").date().isoformat(),
                     "shift": meta["Shift"], "machine": meta["Machine"], "model": meta["Model"],
                     "condition": meta["Condition"], "n_valid": n_valid,
                     "xbar_g": (sum(vals) / n_valid) if n_valid else "",
                     "range_g": (max(vals) - min(vals)) if n_valid else "", "status": status, "file": path.name})

    m = pd.DataFrame(meas).sort_values(["run_id", "sample_no"], kind="mergesort")
    r = pd.DataFrame(runs).sort_values(["test_date", "run_id"], kind="mergesort")
    m.to_csv("data/clean/measurements.csv", index=False)
    r.to_csv("data/clean/runs.csv", index=False)
    with open("outputs/parse_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["run_id", "file", "sample_no", "raw_value", "aksi", "alasan"])
        w.writerows(sorted(LOG, key=lambda x: (x[0], x[1], str(x[2]), x[4], x[5])))
    print(f"runs {len(r)} (included {int((r.status == 'included').sum())}), sampel valid {len(m)}, log {len(LOG)}")


if __name__ == "__main__":
    main()
