[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 15: SPC Control Chart & Capability Dashboard with Automated Alerts

**Status: Analisis dan dashboard selesai (WIP, branch `project-15-build`). Belum di-deploy. GitHub Actions dan `check_std` belum.**

**Status awal: Design (rancangan).** Halaman rancangan ada di [`index.html`](index.html). Analisis, dashboard, dan angka hasil belum dikerjakan, sehingga bagian Analysis, Recommendation, dan Impact di bawah masih kosong.

**Tujuan:** membangun dashboard SPC yang memantau kekuatan ikatan glue pada perekatan lensa lampu depan sepeda motor dari hasil force push test, untuk mendeteksi proses yang mulai keluar kendali atau Cpk yang turun di bawah 1,33 sebelum banyak produk NG terbentuk, dengan alert otomatis.

| | |
|---|---|
| Kategori | Manufaktur sepeda motor |
| Tingkat | Sedang |
| Data | Data simulasi meniru format file CSV mesin push test |
| Tools | DuckDB + SQL, Python (pandas, NumPy, SciPy), Excel, Streamlit + Plotly, GitHub Actions (opsional) |

## 1. Problem

**Pertanyaan utama:** Kapan proses perekatan lensa lampu keluar kendali atau Cpk turun di bawah 1,33, dan apakah sinyal itu bisa terlihat sebelum banyak hasil uji NG?

Rancangan memecahnya menjadi 14 pertanyaan (9 Utama, 4 Pendukung, 1 Tambahan) dalam tema stabilitas, capability, perbandingan model dan kondisi, alert, dampak, dan validitas. Daftar lengkap ada di bagian 2 halaman rancangan.

## 2. Data

- Data simulasi meniru format file CSV mesin push test: satu file per run, beberapa sampel per run, gaya dalam gram, spec 1500–19000 g. Generator: `scripts/generate_push_test.py`. Versi data: v1. Tanggal dibuat: 28 Okt 2026. Seed: 15260401. Hasil v1: 600 file CSV (3.000 baris hasil ukur).
- Ukuran (perkiraan): 2 model (Model A, Model B) × 2 kondisi (sebelum dan sesudah oven), ±600 run, ±3.000 baris hasil ukur, ±3 bulan.
- Rencana tabel: `test_run`, `measurement`, `spec_limit`, `alert_log`.

## 3. Analysis

Data simulasi (600 run, 2.988 sampel valid, 592 run dipakai). Angka dari `src/02_spc.py` dan validasi di `src/03_validate.py`. Asumsi di `docs/definitions.md`. Semua data simulasi (karangan).

**Hasil (fase baseline 1 sampai 14 April 2026, limit diterapkan ke seluruh data):**

- Cpk per aliran (baseline): Model A sesudah oven 2,63 (CI 2,28 sampai 2,97), Model A sebelum oven 2,19 (1,94 sampai 2,44), Model B sesudah oven 2,34 (2,03 sampai 2,65), Model B sebelum oven 1,98 (1,69 sampai 2,26).
- Fakta 4 (sesudah oven lebih tinggi): selisih rata-rata Model A sebesar 1.366 g. Terkonfirmasi di Model A.
- Fakta 1 (Model B sesudah oven turun bertahap): alert X-bar pertama 26 Mei 2026 (run pertama di jendela). Cpk bergulir di bawah 1,33 pertama kali 30 Mei 2026. Sesuai ground truth.
- Fakta 2 (Model A sebelum oven turun mendadak di Shift 2, 1–3 Mei): hanya 2 run di jendela, terdeteksi di run pertama (2 Mei). Jumlah run terlalu kecil untuk kesimpulan kuat.
- Fakta 3 (PT-02 sebaran membesar, 15–28 April): alert R-chart dan X-bar muncul di keempat aliran. Terdeteksi di run pertama atau dalam beberapa run.
- Fakta 5 (data kotor): 15 file dengan entri log, sesuai ground truth.
- False alarm di luar jendela fault: 2,3% run (9 dari 391) untuk X-bar, 0,5% (2 dari 391) untuk R.
- Monte Carlo (2.000 replikasi, limit dari baseline): ARL0 sekitar 180 run (false alarm 0,56% per run). ARL1: 10,8 run untuk pergeseran 1σ, 3,3 untuk 2σ, 1,6 untuk 3σ.
- Sensitivitas baseline (A1): dengan baseline 7 hari, false alarm X-bar 3,6% per run. Dengan 14 hari (default) 2,3%. Dengan 21 hari 1,9%, tetapi baseline 21 hari sudah memuat awal fault PT-02 (15 April). Deteksi F3 turun dari 4 ke 3 aliran. Itu sebabnya 14 hari dipilih sebagai baseline bersih terpanjang.

**Catatan:** hasil ini dari data simulasi. Nilainya membuktikan metode bekerja pada fault yang ditanam, bukan kondisi pabrik nyata.

## 4. Recommendation

Belum dikerjakan (menunggu dashboard dan aturan alert final).

## 5. Impact

Belum dikerjakan. Rumus yang akan dipakai (semua hasil diberi label `estimated` / `simulated`):

```
NG terhindari = run sebelum alert × unit per run × rate NG
```

Fakta yang sengaja ditanam di data simulasi (ground truth):
1. Model B sesudah oven turun bertahap ±1 minggu sampai Cpk < 1,33 dan muncul beberapa NG.
2. Model A sebelum oven turun mendadak 3 hari di satu shift.
3. Satu mesin uji dengan sebaran membesar ±2 minggu.
4. Hasil sesudah oven lebih tinggi daripada sebelum oven.
5. 2–3% data kotor.

## 4. Recommendation

Belum dikerjakan. Output yang direncanakan: aturan alert dan kelompok proses yang perlu tindakan.

## 5. Impact

Belum dikerjakan. Rumus yang akan dipakai (semua hasil diberi label `estimated` / `simulated`):

```
NG terhindari = run sebelum alert × unit per run × rate NG
```

## Batasan yang sudah diketahui

- Spec sangat lebar, sehingga Cpk ditentukan sisi bawah.
- Distribusi kekuatan ikatan belum tentu normal.
- Uji destruktif membatasi jumlah sampel.
- Alert menunjukkan perubahan, bukan penyebab.

## Status pengerjaan (WIP)

| Item | Status |
|---|---|
| Generator data simulasi (`scripts/generate_push_test.py`) | selesai, 600 file, seed 15260401, dijalankan ulang |
| Ingest dan cleaning (`src/01_ingest_clean.py`) | selesai, log di `outputs/parse_log.csv` |
| SPC: limit baseline, Western Electric, Cp/Cpk CI, Cpk bergulir (`src/02_spc.py`) | selesai |
| Validasi ground truth dan ARL (`src/03_validate.py`) | selesai |
| Sensitivitas baseline 7, 14, 21 hari (`src/04_validate_baseline_sensitivity.py`) | selesai |
| Load ke DuckDB dan SQL (`src/05_duckdb_load.py`, `sql/kpi.sql`) | selesai, 16 nilai cek silang sama |
| Dashboard Streamlit 4 halaman (`dashboard/app.py`) + AppTest (`tests/test_dashboard.py`, 3 lulus) | selesai; belum di-deploy |
| GitHub Actions alert (opsional) | belum; belum dijalankan di GitHub |
| `report_lib.py`, `report.css`, `check_std` dari Project-4 | belum |
| Uji dari nol dua kali (`run_all.sh`) | selesai, checksum identik |

## Struktur repository

```
index.html   Halaman rancangan project (bisa dibuka di browser atau lewat GitHub Pages)
README.md    Dokumen ini
```

Folder `docs/`, `data/`, `scripts/`, `sql/`, `notebooks/`, `dashboard/`, dan `outputs/` ditambahkan saat pengerjaan dimulai.
