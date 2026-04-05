"""
Validators module.
Checks for duplicate records and buy/sell conflicts
in market_records and actual_records.
"""

from utils import round6

# Check buy/sell conflicts in one record
def validate_one_sided_record(record, buy_key, sell_key, record_name):
    buy_v  = round6(record.get(buy_key, 0) or 0)
    sell_v = round6(record.get(sell_key, 0) or 0)
    if buy_v > 0 and sell_v > 0:
        raise ValueError(
            f"{record_name} for household={record['household_id']} "
            f"timeslot={record['timeslot']} "
            f"cannot have both {buy_key} and {sell_key} > 0"
        )

# Check duplicate records and buy/sell conflicts
def validate_records(market_records_v, actual_records_v):
    for name, records in [
        ("market_records", market_records_v),
        ("actual_records", actual_records_v),
    ]:
        seen = set()
        for record in records:
            key = (record["household_id"], record["timeslot"])
            if key in seen:
                raise ValueError(f"{name} has duplicate data: {key}")
            seen.add(key)

            if name == "market_records":
                for buy_key in ("matched_buy_kwh", "unmatched_buy_kwh"):
                    for sell_key in ("matched_sell_kwh", "unmatched_sell_kwh"):
                        validate_one_sided_record(record, buy_key, sell_key, name)
            else:
                validate_one_sided_record(record, "actual_buy_kwh", "actual_sell_kwh", name)