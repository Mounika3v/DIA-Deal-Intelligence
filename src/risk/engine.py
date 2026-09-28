import numpy as np
import pandas as pd

def score_deals(df: pd.DataFrame, reference_date="2017-12-31") -> pd.DataFrame:
    out = df.copy()
    ref = pd.Timestamp(reference_date)
    days = (ref - out["engage_date"]).dt.days.fillna(0).clip(lower=0)
    out["staleness_risk"] = np.where(out["deal_stage"].eq("Engaging"), (days / 180 * 45).clip(0, 45), 0)
    out["context_risk"] = np.where(out["account"].eq("Unassigned Account"), 20, 0)
    lp = pd.to_numeric(out.get("list_price"), errors="coerce").fillna(0)
    cv = pd.to_numeric(out["close_value"], errors="coerce").fillna(0)
    discount = np.where((lp > 0) & (cv > 0), ((lp - cv) / lp).clip(0, 1), 0)
    out["pricing_risk"] = (discount * 35).clip(0, 35)
    out["risk_score"] = (out["staleness_risk"] + out["context_risk"] + out["pricing_risk"]).round(1)
    out.loc[out["deal_stage"].eq("Won"), "risk_score"] = 0
    out.loc[out["deal_stage"].eq("Lost"), "risk_score"] = 100
    out["risk_category"] = pd.cut(out["risk_score"], [-0.1, 25, 50, 75, 100.1], labels=["Low", "Medium", "High", "Critical"])
    return out
