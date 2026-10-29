-- View KPI Project 15. Dijalankan oleh src/05_duckdb_load.py.
CREATE OR REPLACE VIEW v_runs AS
SELECT run_id, test_date, shift, machine, model, condition, stream,
       xbar_g, range_g, z_x, alert_x, alert_r
FROM spc_runs
ORDER BY stream, test_date, run_id;

CREATE OR REPLACE VIEW v_stream_summary AS
SELECT m.model || ' | ' || m.condition AS stream,
       COUNT(DISTINCT m.run_id) AS n_run,
       COUNT(*) AS n_sampel,
       AVG(m.force_g) AS mean_g,
       STDDEV_SAMP(m.force_g) AS sd_g,
       SUM(CASE WHEN m.force_g < 1500 OR m.force_g > 19000 THEN 1 ELSE 0 END) AS n_ng
FROM measurements m
JOIN runs_included r USING (run_id)
GROUP BY 1
ORDER BY 1;

CREATE OR REPLACE VIEW v_dashboard AS
SELECT v.run_id, v.test_date, v.shift, v.machine, v.model, v.condition, v.stream,
       v.xbar_g, v.range_g, v.z_x, v.alert_x, v.alert_r,
       c.cpk_rolling, c.below_133
FROM v_runs v
LEFT JOIN cpk_rolling c USING (run_id, stream)
ORDER BY v.stream, v.test_date, v.run_id;
