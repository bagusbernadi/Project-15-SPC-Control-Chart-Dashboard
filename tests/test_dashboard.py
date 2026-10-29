"""Uji dashboard dengan Streamlit AppTest: setiap halaman dirender tanpa error, dan kolom yang dipakai ada di CSV."""
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "dashboard" / "app.py")
PAGES = ["Ringkasan", "Peta Kontrol", "Alert & Validasi", "Data & Kualitas"]


def run_page(name):
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    at.sidebar.radio[0].set_value(name).run()
    assert not at.exception, at.exception
    return at


def test_each_page_renders_without_exception():
    for p in PAGES:
        at = run_page(p)
        assert len(at.main.children) > 0


def test_control_chart_selector_works():
    at = run_page("Peta Kontrol")
    assert len(at.selectbox) >= 1
    streams = at.selectbox[0].options
    at.selectbox[0].set_value(streams[-1]).run()
    assert not at.exception


def test_dashboard_columns_exist_in_csv():
    runs = pd.read_csv(ROOT / "outputs" / "dashboard_runs.csv")
    for c in ["run_id", "test_date", "stream", "xbar_g", "range_g", "alert_x", "alert_r", "cpk_rolling", "below_133"]:
        assert c in runs.columns, c
