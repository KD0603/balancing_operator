"""
main.py — Entry point for the balancing part.

Orchestrates:
  1. Data loading       (data.py)
  2. Validation         (validators.py)
  3. Price lookup       (Price_Cal.py)
  4. Part 1 settlement  (part1_unmatched.py)
  5. Part 2 settlement  (part2_deviation.py)
"""

from Price_Cal import build_price_table
from data import market_records, actual_records
from validators import validate_records
from part1_unmatched import settle_unmatched_table
from part2_deviation import settle_deviation_merged_table


class PriceProvider:
    def __init__(self):
        self.price_table = build_price_table()

    def get_prices(self, timeslot):
        if timeslot not in self.price_table:
            raise ValueError(f"Missing price for timeslot {timeslot}")
        return self.price_table[timeslot]


def final_settle(market_records_final, actual_records_final):
    validate_records(market_records_final, actual_records_final)
    price_provider = PriceProvider()

    return {
        "part_1_unmatched_table": settle_unmatched_table(market_records_final, price_provider),
        "part_2_deviation_merged_table": settle_deviation_merged_table(market_records_final, actual_records_final, price_provider),
    }


if __name__ == "__main__":
    result = final_settle(market_records, actual_records)

    print("=== Part 1: Unmatched Settlement ===")
    for row in result["part_1_unmatched_table"]:
        print(row)

    print("\n=== Part 2: Deviation Settlement ===")
    for row in result["part_2_deviation_merged_table"]:
        print(row)