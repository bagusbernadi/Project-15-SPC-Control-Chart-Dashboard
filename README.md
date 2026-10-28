[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 15: SPC Control Chart & Capability Dashboard with Automated Alerts

**Status: Design (rancangan).** Halaman rancangan ada di [`index.html`](index.html). Analisis, dashboard, dan angka hasil belum dikerjakan, sehingga bagian Analysis, Recommendation, dan Impact di bawah masih kosong.

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

Belum dikerjakan. Rencana langkah (12 langkah, tahap A sampai D) ada di bagian 6 halaman rancangan: X-bar/R chart, p-chart, Cp/Cpk dan rolling Cpk, uji normalitas, aturan alert (Western Electric rules), dan evaluasi false alarm.

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

## Struktur repository

```
index.html   Halaman rancangan project (bisa dibuka di browser atau lewat GitHub Pages)
README.md    Dokumen ini
```

Folder `docs/`, `data/`, `scripts/`, `sql/`, `notebooks/`, `dashboard/`, dan `outputs/` ditambahkan saat pengerjaan dimulai.
