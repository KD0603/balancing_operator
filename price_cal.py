"""
price_cal.py
Builds a price lookup table from two Agile Octopus CSV files.

Price table key format: "YYYY-MM-DD HH:MM" (UTC, always :00 minutes)
This match the timeslot format used in data.py.
"""

import pandas as pd


def build_price_table(
    tou_csv="csv_agile_L_South_Western_England.csv",
    fit_csv="csv_agileoutgoing_L_South_Western_England.csv",
    start_str="2020-01-01 00:00",
    end_str="2021-01-01 00:00",
):

    cols = ["timestamp", "time_period", "zone", "region", "price"]

    tou_df = pd.read_csv(tou_csv, names=cols)
    fit_df = pd.read_csv(fit_csv, names=cols)

    tou_df["timestamp"] = pd.to_datetime(tou_df["timestamp"], utc=True)
    fit_df["timestamp"] = pd.to_datetime(fit_df["timestamp"], utc=True)

    start = pd.Timestamp(start_str, tz="UTC")
    end = pd.Timestamp(end_str,   tz="UTC")

    tou_df = tou_df[(tou_df["timestamp"] >= start) & (tou_df["timestamp"] < end)].copy()
    fit_df = fit_df[(fit_df["timestamp"] >= start) & (fit_df["timestamp"] < end)].copy()

    if tou_df.empty or fit_df.empty:
        raise ValueError(
            f"No price data found between {start_str} and {end_str}. "
            "Please check the CSV files and the date window."
        )

    tou_df["hour_key"] = tou_df["timestamp"].dt.floor("h")
    fit_df["hour_key"] = fit_df["timestamp"].dt.floor("h")

    tou_hr = (
        tou_df.groupby("hour_key", as_index=False)["price"]
        .mean()
        .rename(columns={"price": "ToU"})
    )
    fit_hr = (
        fit_df.groupby("hour_key", as_index=False)["price"]
        .mean()
        .rename(columns={"price": "FiT"})
    )

    result = pd.merge(tou_hr, fit_hr, on="hour_key", how="inner")

    if result.empty:
        raise ValueError(
            "Price merge produced an empty table. "
            "Check that both CSV files cover the same date range."
        )

    return {
        row["hour_key"].strftime("%Y-%m-%d %H:%M"): {
            "buy": float(row["ToU"]) / 1000,
            "sell": float(row["FiT"]) / 1000,
        }
        for _, row in result.iterrows()
    }
