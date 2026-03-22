import pandas as pd

def build_price_table():
    tou_csv = "csv_agile_L_South_Western_England.csv"
    fit_csv = "csv_agileoutgoing_L_South_Western_England.csv"
    cols = ["timestamp", "time_period", "zone", "region", "price"]

    tou_df = pd.read_csv(tou_csv, names=cols)
    fit_df = pd.read_csv(fit_csv, names=cols)

    tou_df["timestamp"] = pd.to_datetime(tou_df["timestamp"], utc=True)
    fit_df["timestamp"] = pd.to_datetime(fit_df["timestamp"], utc=True)

    start = pd.Timestamp("2026-01-01 00:00:00", tz="UTC")
    end = pd.Timestamp("2026-03-02 00:00:00", tz="UTC")

    tou_df = tou_df[(tou_df["timestamp"] >= start) & (tou_df["timestamp"] < end)].copy()
    fit_df = fit_df[(fit_df["timestamp"] >= start) & (fit_df["timestamp"] < end)].copy()

    tou_df["hour"] = tou_df["timestamp"].dt.strftime("%H:00")
    fit_df["hour"] = fit_df["timestamp"].dt.strftime("%H:00")

    tou_avg = tou_df.groupby("hour", as_index=False)["price"].mean().rename(columns={"price": "ToU_avg"})
    fit_avg = fit_df.groupby("hour", as_index=False)["price"].mean().rename(columns={"price": "FiT_avg"})

    result = pd.merge(tou_avg, fit_avg, on="hour", how="inner")

    return {
        row["hour"]: {
            "buy": float(row["ToU_avg"]),
            "sell": float(row["FiT_avg"]),
        }
        for _, row in result.iterrows()
    }