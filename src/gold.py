import pandas as pd

def create_gold(df):
    print("📊 GOLD")

    metrics = pd.DataFrame({
        "total_trips": [len(df)],
        "total_revenue": [df["total_amount"].sum()]
    })

    return metrics