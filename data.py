"""
Household data module.
Contains market records (matched/unmatched scheduled electricity)
and actual records (real electricity consumption/generation)
"""

market_records = [
    {"household_id": "H1", "timeslot": "2020-01-01 00:00", "matched_buy_kwh": 0, "matched_sell_kwh": 5, "unmatched_buy_kwh": 0, "unmatched_sell_kwh": 1},
    {"household_id": "H2", "timeslot": "2020-01-01 00:00", "matched_buy_kwh": 3, "matched_sell_kwh": 0, "unmatched_buy_kwh": 0, "unmatched_sell_kwh": 0},
    {"household_id": "H3", "timeslot": "2020-01-01 00:00", "matched_buy_kwh": 4, "matched_sell_kwh": 0, "unmatched_buy_kwh": 1, "unmatched_sell_kwh": 0},
    {"household_id": "H4", "timeslot": "2020-01-01 00:00", "matched_buy_kwh": 3, "matched_sell_kwh": 0, "unmatched_buy_kwh": 0, "unmatched_sell_kwh": 0},
    {"household_id": "H5", "timeslot": "2020-01-01 02:00", "matched_buy_kwh": 0, "matched_sell_kwh": 6, "unmatched_buy_kwh": 0, "unmatched_sell_kwh": 0.5},
    {"household_id": "H6", "timeslot": "2020-01-01 02:00", "matched_buy_kwh": 5, "matched_sell_kwh": 0, "unmatched_buy_kwh": 0, "unmatched_sell_kwh": 0},
    {"household_id": "H7", "timeslot": "2020-01-01 02:00", "matched_buy_kwh": 3, "matched_sell_kwh": 0, "unmatched_buy_kwh": 0.5, "unmatched_sell_kwh": 0},
]

actual_records = [
    {"household_id": "H1", "timeslot": "2020-01-01 00:00", "actual_buy_kwh": 0, "actual_sell_kwh": 6},
    {"household_id": "H2", "timeslot": "2020-01-01 00:00", "actual_buy_kwh": 4, "actual_sell_kwh": 0},
    {"household_id": "H3", "timeslot": "2020-01-01 00:00", "actual_buy_kwh": 5, "actual_sell_kwh": 0},
    {"household_id": "H4", "timeslot": "2020-01-01 00:00", "actual_buy_kwh": 1, "actual_sell_kwh": 0},
    {"household_id": "H5", "timeslot": "2020-01-01 02:00", "actual_buy_kwh": 3, "actual_sell_kwh": 0},
    {"household_id": "H6", "timeslot": "2020-01-01 02:00", "actual_buy_kwh": 4, "actual_sell_kwh": 0},
    {"household_id": "H7", "timeslot": "2020-01-01 02:00", "actual_buy_kwh": 0, "actual_sell_kwh": 6},
    {"household_id": "H8", "timeslot": "2020-01-01 02:00", "actual_buy_kwh": 2, "actual_sell_kwh": 0},
]
