"""Dashboard SPC push test (data simulasi). 4 halaman: Ringkasan, Peta Kontrol, Alert & Validasi, Data & Kualitas.

Sumber: outputs/ (dihasilkan oleh src/). Tidak membaca data/sim/ground_truth.json.
Jalankan: streamlit run dashboard/app.py
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
CPK_MIN = 1.33
PAGES = ["Ringkasan", "Peta Kontrol", "Alert & Validasi", "Data & Kualitas"]

REQ = {
    "dashboard_runs.csv": ["run_id", "test_date", "shift", "machine", "model", "condition", "stream",
                           "xbar_g", "range_g", "z_x", "alert_x", "alert_r", "cpk_rolling", "below_133"],
    "spc_limits.csv": ["stream", "xbar_cl_g", "xbar_ucl_g", "xbar_lcl_g", "r_ucl_g", "r_lcl_g", "cp", "cpk",
                       "cpk_ci_low", "cpk_ci_high", "n_baseline_run", "n_baseline_sampel"],
    "validation.csv": ["cek", "fault", "stream", "n_run_di_jendela", "alert_xbar_pertama"],
    "arl_recovery.csv": ["pergeseran_sigma", "replikasi", "ARL0_false_alarm_per_run", "ARL1_rata_run"],
    "baseline_sensitivity.csv": ["baseline", "baseline_sampai_sebelum", "metrik", "nilai", "n"],
    "parse_log.csv": ["run_id", "file", "sample_no", "raw_value", "aksi", "alasan"],
}


@st.cache_data
def load(name):
    df = pd.read_csv(OUT / name)
    missing = [c for c in REQ[name] if c not in df.columns]
    if missing:
        raise ValueError(f"{name} tidak punya kolom: {missing}")
    return df


def page_summary(runs, lim):
    st.header("Ringkasan")
    st.caption("Data simulasi. Limit dari baseline 1–14 April 2026.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Run dipakai", f"{len(runs)}")
    c2.metric("Alert X-bar", f"{int(runs.alert_x.sum())}")
    c3.metric("Alert R", f"{int(runs.alert_r.sum())}")
    c4.metric("Aliran Cpk baseline < 1,33", f"{int((lim.cpk < CPK_MIN).sum())} dari {len(lim)}")
    st.subheader("Cpk per aliran (baseline, dengan CI 95%)")
    st.dataframe(lim[["stream", "cpk", "cpk_ci_low", "cpk_ci_high", "cp"]].round(3), hide_index=True, use_container_width=True)
    st.subheader("Cpk bergulir terakhir per aliran")
    last = runs.sort_values(["stream", "test_date", "run_id"]).groupby("stream").tail(1)
    st.dataframe(last[["stream", "test_date", "cpk_rolling", "below_133"]].round(3), hide_index=True, use_container_width=True)


def page_control(runs, lim):
    st.header("Peta Kontrol")
    stream = st.selectbox("Aliran", sorted(runs.stream.unique()))
    d = runs[runs.stream == stream].sort_values(["test_date", "run_id"])
    L = lim[lim.stream == stream].iloc[0]
    fig = go.Figure()
    fig.add_scatter(x=d.test_date, y=d.xbar_g, mode="lines+markers", name="X-bar (g)")
    fig.add_hline(y=L.xbar_cl_g, line_dash="solid", annotation_text="CL")
    fig.add_hline(y=L.xbar_ucl_g, line_dash="dash", annotation_text="UCL")
    fig.add_hline(y=L.xbar_lcl_g, line_dash="dash", annotation_text="LCL")
    a = d[d.alert_x]
    fig.add_scatter(x=a.test_date, y=a.xbar_g, mode="markers", name="alert X-bar", marker=dict(color="red", size=9))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)

    fig2 = go.Figure()
    fig2.add_scatter(x=d.test_date, y=d.range_g, mode="lines+markers", name="R (g)")
    fig2.add_hline(y=L.r_ucl_g, line_dash="dash", annotation_text="UCL R")
    b = d[d.alert_r]
    fig2.add_scatter(x=b.test_date, y=b.range_g, mode="markers", name="alert R", marker=dict(color="red", size=9))
    fig2.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = go.Figure()
    fig3.add_scatter(x=d.test_date, y=d.cpk_rolling, mode="lines", name="Cpk bergulir (30 run)")
    fig3.add_hline(y=CPK_MIN, line_dash="dash", annotation_text="1,33")
    fig3.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig3, use_container_width=True)


def page_alerts(runs, val, arl, sens):
    st.header("Alert & Validasi")
    st.subheader("Alert per aliran (xbar dan R)")
    summ = runs.groupby("stream").agg(run=("run_id", "size"), alert_x=("alert_x", "sum"), alert_r=("alert_r", "sum")).reset_index()
    st.dataframe(summ, hide_index=True, use_container_width=True)
    st.subheader("Deteksi fault yang ditanam (validasi)")
    st.dataframe(val[val.cek == "deteksi"][["fault", "stream", "n_run_di_jendela", "alert_xbar_pertama", "run_ke_alert_xbar", "alert_R_pertama"]],
                 hide_index=True, use_container_width=True)
    st.subheader("ARL (uji pemulihan Monte Carlo)")
    st.dataframe(arl, hide_index=True, use_container_width=True)
    st.subheader("Sensitivitas panjang baseline")
    st.dataframe(sens, hide_index=True, use_container_width=True)


def page_quality(parse_log):
    st.header("Data & Kualitas")
    st.caption("Setiap sampel atau run yang dibuang atau diubah. Dihitung dari file CSV mesin.")
    st.dataframe(parse_log.groupby(["aksi", "alasan"]).size().reset_index(name="jumlah"), hide_index=True, use_container_width=True)
    st.subheader("Detail log")
    st.dataframe(parse_log, hide_index=True, use_container_width=True)


def main():
    st.set_page_config(page_title="SPC Push Test", layout="wide")
    page = st.sidebar.radio("Halaman", PAGES)
    runs = load("dashboard_runs.csv")
    lim = load("spc_limits.csv")
    if page == "Ringkasan":
        page_summary(runs, lim)
    elif page == "Peta Kontrol":
        page_control(runs, lim)
    elif page == "Alert & Validasi":
        page_alerts(runs, load("validation.csv"), load("arl_recovery.csv"), load("baseline_sensitivity.csv"))
    else:
        page_quality(load("parse_log.csv"))


main()
