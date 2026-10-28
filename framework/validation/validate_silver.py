import os
from databricks import sql
from datetime import datetime, timezone

HOST = os.environ["DATABRICKS_HOST"]
HTTP_PATH = os.environ["DATABRICKS_HTTP_PATH"]
TOKEN = os.environ["DATABRICKS_TOKEN"]

RUN_ID = os.environ.get("RUN_ID", "manual")
SILVER_TABLE = os.environ.get("SILVER_TABLE", "gameday.silver_customers_v2")

def fetch_one(cur, stmt: str):
    cur.execute(stmt)
    return cur.fetchall()[0][0]

def main():
    checked_at = datetime.now(timezone.utc).isoformat()
    print(f"✅ Validating table: {SILVER_TABLE}")
    print(f"✅ RUN_ID: {RUN_ID}")

    with sql.connect(server_hostname=HOST, http_path=HTTP_PATH, access_token=TOKEN) as conn:
        with conn.cursor() as cur:
            total = fetch_one(cur, f"SELECT COUNT(*) FROM {SILVER_TABLE}")
            name_null = fetch_one(cur, f"SELECT COUNT(*) FROM {SILVER_TABLE} WHERE dq_is_name_null = true")
            underage = fetch_one(cur, f"SELECT COUNT(*) FROM {SILVER_TABLE} WHERE dq_is_underage = true")
            # País coherente: un código con un solo nombre/región y un nombre con un solo código
            country_conflicts = fetch_one(cur, f"""
                SELECT COUNT(*) FROM (
                    SELECT country_code FROM {SILVER_TABLE}
                    WHERE country_code IS NOT NULL
                    GROUP BY country_code
                    HAVING COUNT(DISTINCT country_name, region) > 1
                    UNION ALL
                    SELECT country_name FROM {SILVER_TABLE}
                    WHERE country_name IS NOT NULL
                    GROUP BY country_name
                    HAVING COUNT(DISTINCT country_code) > 1
                ) AS conflicts
            """)
            # Un registro por cliente: COUNT(DISTINCT) ignora NULL, así que un id nulo también cuenta
            duplicates = fetch_one(cur, f"SELECT COUNT(*) - COUNT(DISTINCT customer_id) FROM {SILVER_TABLE}")

            # Guarda resultados en ops_dq_results
            cur.execute(
                "INSERT INTO gameday.ops_dq_results VALUES (?, current_timestamp(), ?, 'total_rows', 'INFO', ?, ?)",
                (RUN_ID, SILVER_TABLE, float(total), f"checked_at={checked_at}")
            )

            cur.execute(
                "INSERT INTO gameday.ops_dq_results VALUES (?, current_timestamp(), ?, 'name_null_count', ?, ?, ?)",
                (RUN_ID, SILVER_TABLE, "FAIL" if name_null > 0 else "PASS", float(name_null), "name is null/empty")
            )

            cur.execute(
                "INSERT INTO gameday.ops_dq_results VALUES (?, current_timestamp(), ?, 'underage_count', ?, ?, ?)",
                (RUN_ID, SILVER_TABLE, "WARN" if underage > 0 else "PASS", float(underage), "age < 18")
            )

            cur.execute(
                "INSERT INTO gameday.ops_dq_results VALUES (?, current_timestamp(), ?, 'country_mapping_conflicts', ?, ?, ?)",
                (RUN_ID, SILVER_TABLE, "FAIL" if country_conflicts > 0 else "PASS", float(country_conflicts),
                 "country_code with >1 name/region or country_name with >1 code")
            )

            cur.execute(
                "INSERT INTO gameday.ops_dq_results VALUES (?, current_timestamp(), ?, 'duplicate_customer_id_count', ?, ?, ?)",
                (RUN_ID, SILVER_TABLE, "FAIL" if duplicates > 0 else "PASS", float(duplicates),
                 "rows beyond one per customer_id (includes null ids)")
            )

    print(f"✅ Validation completed: total={total}, name_null={name_null}, underage={underage}, "
          f"country_conflicts={country_conflicts}, duplicates={duplicates}")

    # Catálogo de países incoherente o clientes duplicados cortan el pipeline: Gold no se publica
    if country_conflicts > 0 or duplicates > 0:
        raise SystemExit(f"❌ country_mapping_conflicts={country_conflicts}, "
                         f"duplicate_customer_id_count={duplicates}: Gold is not published")

if __name__ == "__main__":
    main()
