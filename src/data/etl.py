from pathlib import Path
import pandas as pd

EXPECTED = ["accounts.csv", "products.csv", "sales_teams.csv", "sales_pipeline.csv"]

def load_data(raw_dir="data/raw"):
    root = Path(raw_dir)
    missing = [f for f in EXPECTED if not (root/f).exists()]
    if missing:
        raise FileNotFoundError(f"Missing dataset files: {', '.join(missing)}")
    accounts = pd.read_csv(root/"accounts.csv")
    products = pd.read_csv(root/"products.csv")
    teams = pd.read_csv(root/"sales_teams.csv")
    pipeline = pd.read_csv(root/"sales_pipeline.csv")
    pipeline["product"] = pipeline["product"].replace({"GTXPro": "GTX Pro"})
    pipeline["account"] = pipeline["account"].fillna("Unassigned Account")
    pipeline["engage_date"] = pd.to_datetime(pipeline["engage_date"], errors="coerce")
    pipeline["close_date"] = pd.to_datetime(pipeline["close_date"], errors="coerce")
    pipeline["close_value"] = pd.to_numeric(pipeline["close_value"], errors="coerce")
    products = products.rename(columns={"sales_price": "list_price"})
    merged = pipeline.merge(products, on="product", how="left")
    merged = merged.merge(accounts, on="account", how="left")
    merged = merged.merge(teams, on="sales_agent", how="left")
    return merged, accounts, products, teams
