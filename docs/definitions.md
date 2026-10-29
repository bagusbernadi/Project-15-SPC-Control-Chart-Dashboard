# Definisi dan asumsi Project 15

## Definisi (sesuai rancangan)

- Subgroup = satu run push test, n = 5 sampel. Hanya run dengan tepat 5 sampel valid dipakai (X-bar/R).
- Aliran (stream) = Model × Kondisi (sebelum/sesudah oven): 4 aliran.
- Cp = (USL − LSL) / (6σ). Cpk = min(USL − μ, μ − LSL) / (3σ). LSL = 1.500 g, USL = 19.000 g (spec dari file mesin).
- σ untuk Cp/Cpk = R̄ / d2, d2 = 2,326 (n = 5). Cpk CI 95% dengan pendekatan Bissell.
- Cpk bergulir = jendela 30 run per aliran, σ dari sampel individu di jendela.
- Alert = Western Electric (R1 > 3σ, R2 2 dari 3 > 2σ sisi sama, R4 8 berurutan sisi sama) pada X-bar. R-chart: alert jika di luar UCL/LCL.

## Asumsi (label ASUMSI, belum diuji sensitivitasnya kecuali disebut)

| No | Asumsi | Nilai | Alasan | Status uji |
|---|---|---|---|---|
| A1 | Fase awal (baseline) = 1–14 April 2026 | test_date < 15 April | Fault pertama (PT-02 sebaran membesar) mulai 15 April. Baseline dibekukan sebelum fault | Belum diuji 7 atau 21 hari (lihat item terbuka) |
| A2 | Limit X-bar/R dihitung dari baseline per aliran, lalu dipakai ke data berikutnya | — | Rancangan: batas dari fase awal, bukan seluruh data | Diterapkan |
| A3 | Western Electric: R1, R2, R4 dipakai bersama | — | Rancangan Analysis: "aturan alert (Western Electric rules)" | Versi R1 saja dihitung di 03 (tidak dilaporkan terpisah) |
| A4 | Run dengan < 5 sampel valid dikecualikan (8 run) | — | X-bar/R butuh n tetap | Dampak kecil (8 dari 600) |
| A5 | Nilai 0 g dianggap tidak fisik | — | Log: 0 g hanya dari file kotor | Tidak diuji |
| A6 | Alert "sebelum/sesudah" dihitung per aliran, bukan per shift | — | Rancangan: per proses | Fault F2 hanya di Shift 2, dilihat per aliran (dilaporkan apa adanya) |
| A7 | Cpk CI: Bissell, z = 1,96 | — | Pendekatan umum | Tidak diuji dengan bootstrap |

## Data simulasi

- Semua data simulasi (karangan). Generator `scripts/generate_push_test.py`, seed 15260401, versi v1.
- Kebenaran simulasi (`data/sim/ground_truth.json`) hanya dibaca `src/03_validate.py`. `src/01_ingest_clean.py` dan `src/02_spc.py` tidak membacanya.
