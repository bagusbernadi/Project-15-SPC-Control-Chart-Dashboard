"""Muat data ke DuckDB, jalankan sql/kpi.sql, cek silang dengan pandas, dan ekspor CSV untuk dashboard.

Input : data/clean/measurements.csv, data/clean/runs.csv, data/clean/cpk_rolling.csv, outputs/spc_runs.csv
Output: data/clean/p15.duckdb (tidak di-commit)
        outputs/dashboard_runs.csv   (sumber dashboard)
        outputs/sql_vs_pandas.csv    (cek silang SQL vs pandas)
"""
import os

import duckdb
import pandas as pd

DB = "data/clean/p15.duckdb"
TOL = 1e-9


def main():
    if os.path.exists(DB):
        os.remove(DB)
    con = duckdb.connect(DB)
    con.execute("CREATE TABLE measurements AS SELECT * FROM read_csv_auto('data/clean/measurements.csv', header=true) ORDER BY run_id, sample_no")
    con.execute("CREATE TABLE runs AS SELECT * FROM read_csv_auto('data/clean/runs.csv', header=true) ORDER BY test_date, run_id")
    con.execute("CREATE TABLE runs_included AS SELECT * FROM runs WHERE status = 'included' ORDER BY test_date, run_id")
    con.execute("CREATE TABLE cpk_rolling AS SELECT * FROM read_csv_auto('data/clean/cpk_rolling.csv', header=true) ORDER BY stream, test_date, run_id")
    con.execute("CREATE TABLE spc_runs AS SELECT * FROM read_csv_auto('outputs/spc_runs.csv', header=true) ORDER BY stream, test_date, run_id")
    with open("sql/kpi.sql", encoding="utf-8") as f:
        con.execute(f.read())

    # Cek silang: ringkasan per aliran dari SQL vs pandas
    sql_sum = con.execute("SELECT stream, n_sampel, mean_g, sd_g, n_ng FROM v_stream_summary ORDER BY stream").df()
    m = pd.read_csv("data/clean/measurements.csv")
    r = pd.read_csv("data/clean/runs.csv")
    r = r[r.status == "included"][["run_id"]]
    m = m[m.run_id.isin(r.run_id)].copy()
    m["stream"] = m.model + " | " + m.condition
    pd_sum = (m.groupby("stream").force_g.agg(n_sampel="size", mean_g="mean", sd_g="std")
              .reset_index())
    pd_sum["n_ng"] = m.assign(ng=(m.force_g < 1500) | (m.force_g > 19000)).groupby("stream").ng.sum().values
    pd_sum = pd_sum.sort_values("stream").reset_index(drop=True)
    sql_sum = sql_sum.sort_values("stream").reset_index(drop=True)
    rows = []
    for i in range(len(sql_sum)):
        for col in ["n_sampel", "mean_g", "sd_g", "n_ng"]:
            d = abs(float(sql_sum.loc[i, col]) - float(pd_sum.loc[i, col]))
            rows.append([sql_sum.loc[i, "stream"], col, float(sql_sum.loc[i, col]), float(pd_sum.loc[i, col]), d, d <= TOL * max(1.0, abs(float(pd_sum.loc[i, col])))])
    pd.DataFrame(rows, columns=["stream", "kolom", "sql", "pandas", "selisih", "sama"]).to_csv("outputs/sql_vs_pandas.csv", index=False)
    assert all(x[5] for x in rows), "SQL dan pandas tidak sama"

    dash = con.execute("SELECT * FROM v_dashboard").df()
    dash.to_csv("outputs/dashboard_runs.csv", index=False)
    con.close()
    print("cek silang:", len(rows), "nilai sama; dashboard:", len(dash), "baris")


if __name__ == "__main__":
    main()
