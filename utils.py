import math
from typing import Dict

PENALTY_RATE = 0.05
TRADE_UNIT = 0.01

# Tail difference allocation round record
_bonus_round_counter: Dict[str, int] = {}
_current_round: int = 0


def _get_bonus_priority(household_id: str) -> int:
    return _bonus_round_counter.get(household_id, 0)


def _record_bonus(household_id: str) -> None:
    global _current_round
    _current_round += 1
    _bonus_round_counter[household_id] = _current_round

# Round to 6 decimal places
def round6(x, n=6):
    return round(float(x), n)

# Round down to the nearest trade unit
def quantize(x):
    rounded = round(float(x), 8)
    return round6(math.floor(rounded / TRADE_UNIT) * TRADE_UNIT)

# Calculate the internal trading price
def get_internal_price(grid_buy, grid_sell):
    if grid_buy < grid_sell:
        raise ValueError(
            f"Abnormal price data: grid_buy ({grid_buy}) < grid_sell ({grid_sell}). "
            "Please check the price table."
        )
    return round6((grid_buy + grid_sell) / 2)

# Calculate deviation type and amount
def classify_deviation(scheduled_buy, scheduled_sell, actual_buy, actual_sell):
    scheduled_net = scheduled_sell - scheduled_buy
    actual_net = actual_sell - actual_buy
    deviation = actual_net - scheduled_net

    if deviation > 0:
        tp = "surplus"
    elif deviation < 0:
        tp = "shortage"
    else:
        tp = "balanced"

    return round6(deviation), tp, round6(abs(deviation))