"""Load the processed data into an in-memory SQLite DB and run every named query."""
import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    con = sqlite3.connect(":memory:")
    pd.read_csv(ROOT / "data/processed/powerbi_customer_campaign.csv").to_sql("bank_marketing", con, index=False)
    out = ROOT / "data/processed/sql_results"
    out.mkdir(exist_ok=True)
    for f in sorted((ROOT / "sql").glob("*.sql")):
        for name, body in re.findall(r"-- name: (\w+)\n(.*?)(?=\n-- name:|\Z)", f.read_text(), flags=re.S):
            res = pd.read_sql_query(body, con)
            res.to_csv(out / f"{name}.csv", index=False)
            print(f"\n== {name}\n{res.to_string(index=False)}")


if __name__ == "__main__":
    main()
