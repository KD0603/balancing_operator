"""
main.py — Entry point for the balancing settlement.
"""

from Price_Cal import build_price_table
from data import market_records, actual_records
from validators import validate_records
from part1_unmatched import settle_unmatched_table
from part2_deviation import settle_deviation_merged_table


START = "2020-01-01 00:00"
END   = "2021-01-01 00:00"


PART1_DISPLAY_FIELDS = [
    "household_id",
    "timeslot",
    "unmatched_buy_kwh",
    "unmatched_sell_kwh",
    "grid_trade_direction",
    "penalty_amount",
    "final_settlement_unit_price",
    "unmatched_net_amount",
]

PART2_DISPLAY_FIELDS = [
    "household_id",
    "timeslot",
    "deviation_order_kwh",
    "deviation_type",
    "internal_trade_direction",
    "internal_matched_kwh",
    "counterparty_list",
    "final_grid_trade_direction",
    "final_grid_kwh",
    "penalty_amount",
    "final_settlement_unit_price",
    "deviation_net_amount",
]

# Return a copy of the result with only the display fields included
def filter_output(result):
    return {
        "part_1_unmatched_table": [
            {k: a[k] for k in PART1_DISPLAY_FIELDS if k in a}
            for a in result["part_1_unmatched_table"]
        ],
        "part_2_deviation_merged_table": [
            {k: b[k] for k in PART2_DISPLAY_FIELDS if k in b}
            for b in result["part_2_deviation_merged_table"]
        ],
    }


class PriceProvider:
    def __init__(self, start, end):
        self.price_table = build_price_table(
            start_str=start,
            end_str=end,
        )

    def get_prices(self, timeslot):
        if timeslot not in self.price_table:
            raise ValueError(
                f"No price found for timeslot '{timeslot}'. "
                "Check that this datetime is within the CSV date window "
                "and that the format is 'YYYY-MM-DD HH:MM'."
            )
        return self.price_table[timeslot]


def final_settle(market_records_final, actual_records_final, start=START, end=END):
    validate_records(market_records_final, actual_records_final)
    price_provider = PriceProvider(start, end)

    return {
        "part_1_unmatched_table": settle_unmatched_table(market_records_final, price_provider),
        "part_2_deviation_merged_table": settle_deviation_merged_table(market_records_final, actual_records_final, price_provider),
    }


if __name__ == "__main__":
    full_result = final_settle(market_records, actual_records)
    display = filter_output(full_result)

    print("=== Part 1: Unmatched Settlement ===")
    for row in display["part_1_unmatched_table"]:
        print(row)

    print("\n=== Part 2: Deviation Settlement ===")
    for row in display["part_2_deviation_merged_table"]:
        print(row)
