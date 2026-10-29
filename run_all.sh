#!/usr/bin/env bash
# Jalankan seluruh pipeline dari nol, lalu uji dashboard.
set -euo pipefail
rm -rf data/sim data/clean outputs/*.csv
python3 -I scripts/generate_push_test.py
python3 -I src/01_ingest_clean.py
python3 -I src/02_spc.py > /dev/null
python3 -I src/03_validate.py > /dev/null
python3 -I src/04_validate_baseline_sensitivity.py > /dev/null
python3 -I src/05_duckdb_load.py
python3 -I -m pytest -q tests/test_dashboard.py
