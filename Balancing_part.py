from collections import defaultdict
import math
from Price_Cal import build_price_table


class PriceProvider:
    PRICE_TABLE = build_price_table()

    def get_prices(self, timeslot):
        if timeslot not in self.PRICE_TABLE:
            raise ValueError(f"Missing price for timeslot {timeslot}")
        return self.PRICE_TABLE[timeslot]


INTERNAL_PRICE_DELTA = 0.5
PENALTY_RATE = 0.05
TRADE_UNIT = 0.01


def r(x, n=6):
    return round(float(x), n)


def q(x):
    return r(math.floor((x + 1e-12) / TRADE_UNIT) * TRADE_UNIT)

# Check for duplicate orders within the same household and timeslot
def validate_records(market_records_v, actual_records_v):
    for name, records in [("market_records", market_records_v), ("actual_records", actual_records_v)]:
        seen = set()
        for v in records:
            key = (v["household_id"], v["timeslot"])
            if key in seen:
                raise ValueError(f"{name} has duplicate data: {key}")
            seen.add(key)


def get_internal_prices(grid_buy, grid_sell):
    mid = (grid_buy + grid_sell) / 2
    return r(mid), r(mid + INTERNAL_PRICE_DELTA), r(mid - INTERNAL_PRICE_DELTA)


def classify_deviation(committed_buy, committed_sell, actual_buy, actual_sell):
    committed_net = (committed_sell or 0) - (committed_buy or 0)
    actual_net = (actual_sell or 0) - (actual_buy or 0)
    deviation = actual_net - committed_net
    # Type of deviation
    if deviation > 0:
        tp = "surplus"
    elif deviation < 0:
        tp = "shortage"
    else:
        tp = "balanced"

    return r(deviation), tp, r(abs(deviation))

#
def add_trade(seller, buyer, kwh, internal_buy_price, internal_sell_price):
    kwh = q(kwh)
    if kwh <= 0:
        return

    # Update cumulative transaction electricity
    seller["internal_matched_kwh"] = r(seller["internal_matched_kwh"] + kwh)
    buyer["internal_matched_kwh"] = r(buyer["internal_matched_kwh"] + kwh)

    # Update remaining tradable electricity
    seller["remaining_kwh"] = r(seller["remaining_kwh"] - kwh)
    buyer["remaining_kwh"] = r(buyer["remaining_kwh"] - kwh)

    # Calculate and accumulate transaction amounts
    seller["internal_trade_amount"] = r(seller["internal_trade_amount"] + kwh * internal_sell_price)
    buyer["internal_trade_amount"] = r(buyer["internal_trade_amount"] + kwh * internal_buy_price)

    seller["internal_trade_direction"] = "sell"
    buyer["internal_trade_direction"] = "buy"

    # Record transaction details
    seller["detail_list"].append(f"sell_to {buyer['household_id']}: {kwh:.2f} kWh @ {internal_sell_price}")
    buyer["detail_list"].append(f"buy_from {seller['household_id']}: {kwh:.2f} kWh @ {internal_buy_price}")

# Fair distribution of total electricity
def split_amount_equally(rows, total_amount):
    allocations = {h["household_id"]: 0.0 for h in rows}

    total_amount = q(total_amount)
    if total_amount <= 0:
        return allocations

    active_rows = []
    for a in rows:
        if q(a["remaining_kwh"]) > 0:
            active_rows.append(a)

    if not active_rows:
        return allocations

    # Divided
    avg_share = q(total_amount / len(active_rows))
    used = 0.0

    for a in active_rows:
        hid = a["household_id"]
        cap = q(a["remaining_kwh"])
        give = q(min(avg_share, cap))

        allocations[hid] = give
        used = r(used + give)

    # Deal with remain
    remain = q(total_amount - used)

    for a in sorted(active_rows, key=lambda x: x["household_id"]):
        if remain < TRADE_UNIT:
            break

        hid = a["household_id"]
        cap_left = q(a["remaining_kwh"] - allocations[hid])

        if cap_left >= TRADE_UNIT:
            allocations[hid] = r(allocations[hid] + TRADE_UNIT)
            remain = r(remain - TRADE_UNIT)

    return {hid: q(v) for hid, v in allocations.items()}


def internal_match(surplus_rows, shortage_rows, internal_buy_price, internal_sell_price):
    surplus_rows = [i for i in surplus_rows if q(i["remaining_kwh"]) > 0]
    shortage_rows = [j for j in shortage_rows if q(j["remaining_kwh"]) > 0]

    while surplus_rows and shortage_rows:
        surplus_rows.sort(key=lambda x: (q(x["remaining_kwh"]), x["household_id"]))
        shortage_rows.sort(key=lambda x: (q(x["remaining_kwh"]), x["household_id"]))

        min_surplus = q(surplus_rows[0]["remaining_kwh"])
        min_shortage = q(shortage_rows[0]["remaining_kwh"])

        surplus_group = [sur for sur in surplus_rows if q(sur["remaining_kwh"]) == min_surplus]
        shortage_group = [sh for sh in shortage_rows if q(sh["remaining_kwh"]) == min_shortage]

        total_surplus = q(sum(q(sur_row["remaining_kwh"]) for sur_row in surplus_group))
        total_shortage = q(sum(q(sh_row["remaining_kwh"]) for sh_row in shortage_group))
        matched_total = q(min(total_surplus, total_shortage))

        if matched_total <= 0:
            break

        seller_alloc = split_amount_equally(surplus_group, matched_total)
        buyer_alloc = split_amount_equally(shortage_group, matched_total)

        sellers = [[row_a, q(seller_alloc[row_a["household_id"]])] for row_a in surplus_group if q(seller_alloc[row_a["household_id"]]) > 0]
        buyers = [[row_b, q(buyer_alloc[row_b["household_id"]])] for row_b in shortage_group if q(buyer_alloc[row_b["household_id"]]) > 0]

        i, j = 0, 0
        while i < len(sellers) and j < len(buyers):
            seller_row, seller_amt = sellers[i]
            buyer_row, buyer_amt = buyers[j]

            deal = q(min(seller_amt, buyer_amt))
            add_trade(seller_row, buyer_row, deal, internal_buy_price, internal_sell_price)

            sellers[i][1] = q(sellers[i][1] - deal)
            buyers[j][1] = q(buyers[j][1] - deal)

            if sellers[i][1] <= 0:
                i += 1
            if buyers[j][1] <= 0:
                j += 1

        surplus_rows = [row_sur for row_sur in surplus_rows if q(row_sur["remaining_kwh"]) > 0]
        shortage_rows = [row_sh for row_sh in shortage_rows if q(row_sh["remaining_kwh"]) > 0]

# Part 1: Settle the unmatched parts of the market with the main grid
def settle_unmatched_table(market_records_u, price_provider):
    settle_res = []

    for l in market_records_u:
        household_id = l["household_id"]
        timeslot = l["timeslot"]
        unmatched_buy_kwh = r(l.get("unmatched_buy_kwh", 0) or 0)
        unmatched_sell_kwh = r(l.get("unmatched_sell_kwh", 0) or 0)

        # Get the grid price
        prices = price_provider.get_prices(timeslot)
        grid_buy = r(prices["buy"])
        grid_sell = r(prices["sell"])

        # Calculate settle price
        buy_cost = r(unmatched_buy_kwh * grid_buy) if unmatched_buy_kwh > 0 else 0.0
        sell_revenue = r(unmatched_sell_kwh * grid_sell) if unmatched_sell_kwh > 0 else 0.0

        buy_penalty = r(buy_cost * PENALTY_RATE) if unmatched_buy_kwh > 0 else 0.0
        sell_penalty = r(sell_revenue * PENALTY_RATE) if unmatched_sell_kwh > 0 else 0.0

        settle_res.append({
            "household_id": household_id,
            "timeslot": timeslot,
            "unmatched_buy_kwh": unmatched_buy_kwh,
            "unmatched_sell_kwh": unmatched_sell_kwh,
            "unmatched_net_amount": r(sell_revenue - buy_cost - buy_penalty - sell_penalty),
        })

    return settle_res

# Part 2: Settle the deviation between committed and actual electricity
def settle_deviation_merged_table(market_records_d, actual_records_d, price_provider):
    market_map = {(row_d["household_id"], row_d["timeslot"]): row_d for row_d in market_records_d}
    actual_map = {(row_d["household_id"], row_d["timeslot"]): row_d for row_d in actual_records_d}
    all_keys = sorted(set(market_map) | set(actual_map), key=lambda x: (x[1], x[0]))

    grouped = defaultdict(list)
    for household_id, timeslot in all_keys:
        grouped[timeslot].append(household_id)

    summary = []

    for timeslot, household_ids in grouped.items():
        prices = price_provider.get_prices(timeslot)
        grid_buy = r(prices["buy"])
        grid_sell = r(prices["sell"])
        _, internal_buy_price, internal_sell_price = get_internal_prices(grid_buy, grid_sell)

        rows = []
        surplus_rows = []
        shortage_rows = []

        for household_id in household_ids:
            m = market_map.get((household_id, timeslot), {})
            a = actual_map.get((household_id, timeslot), {})

            committed_buy = r(m.get("committed_buy_kwh", 0) or 0)
            committed_sell = r(m.get("committed_sell_kwh", 0) or 0)
            actual_buy = r(a.get("actual_buy_kwh", 0) or 0)
            actual_sell = r(a.get("actual_sell_kwh", 0) or 0)

            deviation_net_kwh, deviation_type, deviation_kwh = classify_deviation(
                committed_buy, committed_sell, actual_buy, actual_sell
            )

            deviation_settle = {
                "household_id": household_id,
                "timeslot": timeslot,
                "deviation_net_kwh": deviation_net_kwh,
                "deviation_type": deviation_type,
                "internal_trade_direction": "",
                "internal_matched_kwh": 0.0,
                "internal_trade_amount": 0.0,
                "internal_trade_detail_text": "",
                "final_grid_trade_direction": "",
                "final_grid_kwh": 0.0,
                "final_grid_amount": 0.0,
                "deviation_net_amount": 0.0,
                "remaining_kwh": deviation_kwh,
                "detail_list": [],
            }

            rows.append(deviation_settle)

            if deviation_type == "surplus" and deviation_kwh > 0:
                surplus_rows.append(deviation_settle)
            elif deviation_type == "shortage" and deviation_kwh > 0:
                shortage_rows.append(deviation_settle)

        if surplus_rows and shortage_rows:
            internal_match(surplus_rows, shortage_rows, internal_buy_price, internal_sell_price)

        for deviation_settle in rows:
            deviation_settle["internal_trade_detail_text"] = "; ".join(deviation_settle["detail_list"])
            remain = deviation_settle["remaining_kwh"]
            penalty = 0.0

            if remain > 0 and deviation_settle["deviation_type"] in ["surplus", "shortage"]:
                if deviation_settle["deviation_type"] == "shortage":
                    deviation_settle["final_grid_trade_direction"] = "buy_from_grid"
                    price = grid_buy
                else:
                    deviation_settle["final_grid_trade_direction"] = "sell_to_grid"
                    price = grid_sell

                deviation_settle["final_grid_kwh"] = r(remain)
                deviation_settle["final_grid_amount"] = r(remain * price)
                penalty = r(deviation_settle["final_grid_amount"] * PENALTY_RATE)


            if deviation_settle["deviation_type"] == "surplus":
                deviation_settle["deviation_net_amount"] = r(
                    deviation_settle["internal_trade_amount"] + deviation_settle["final_grid_amount"] - penalty
                )
            elif deviation_settle["deviation_type"] == "shortage":
                deviation_settle["deviation_net_amount"] = r(
                    -deviation_settle["internal_trade_amount"] - deviation_settle["final_grid_amount"] - penalty
                )
            else:
                deviation_settle["deviation_net_amount"] = 0.0

            del deviation_settle["remaining_kwh"]
            del deviation_settle["detail_list"]

            summary.append(deviation_settle)

    return summary


def final_settle(market_records_final, actual_records_final):
    validate_records(market_records_final, actual_records_final)
    price_provider = PriceProvider()

    return {
        "part_1_unmatched_table": settle_unmatched_table(market_records_final, price_provider),
        "part_2_deviation_merged_table": settle_deviation_merged_table(market_records_final, actual_records_final, price_provider),
    }


if __name__ == "__main__":
    market_records = [
        {"household_id": "H1", "timeslot": "00:00", "committed_buy_kwh": 0, "committed_sell_kwh": 5, "unmatched_buy_kwh": 0, "unmatched_sell_kwh": 1},
        {"household_id": "H2", "timeslot": "00:00", "committed_buy_kwh": 3, "committed_sell_kwh": 0, "unmatched_buy_kwh": 0, "unmatched_sell_kwh": 0},
        {"household_id": "H3", "timeslot": "00:00", "committed_buy_kwh": 4, "committed_sell_kwh": 0, "unmatched_buy_kwh": 1, "unmatched_sell_kwh": 0},
        {"household_id": "H4", "timeslot": "00:00", "committed_buy_kwh": 2, "committed_sell_kwh": 0, "unmatched_buy_kwh": 0, "unmatched_sell_kwh": 0},
        {"household_id": "H5", "timeslot": "02:00", "committed_buy_kwh": 0, "committed_sell_kwh": 6, "unmatched_buy_kwh": 0, "unmatched_sell_kwh": 0.5},
        {"household_id": "H6", "timeslot": "02:00", "committed_buy_kwh": 5, "committed_sell_kwh": 0, "unmatched_buy_kwh": 0, "unmatched_sell_kwh": 0},
        {"household_id": "H7", "timeslot": "02:00", "committed_buy_kwh": 3, "committed_sell_kwh": 0, "unmatched_buy_kwh": 0.5, "unmatched_sell_kwh": 0},
    ]

    actual_records = [
        {"household_id": "H1", "timeslot": "00:00", "actual_buy_kwh": 0, "actual_sell_kwh": 6},
        {"household_id": "H2", "timeslot": "00:00", "actual_buy_kwh": 4, "actual_sell_kwh": 0},
        {"household_id": "H3", "timeslot": "00:00", "actual_buy_kwh": 5, "actual_sell_kwh": 0},
        {"household_id": "H4", "timeslot": "00:00", "actual_buy_kwh": 3, "actual_sell_kwh": 0},
        {"household_id": "H5", "timeslot": "02:00", "actual_buy_kwh": 3, "actual_sell_kwh": 0},
        {"household_id": "H6", "timeslot": "02:00", "actual_buy_kwh": 4, "actual_sell_kwh": 0},
        {"household_id": "H7", "timeslot": "02:00", "actual_buy_kwh": 0, "actual_sell_kwh": 6},
        {"household_id": "H8", "timeslot": "02:00", "actual_buy_kwh": 2, "actual_sell_kwh": 0},
    ]

    result = final_settle(market_records, actual_records)

    print("=== Part 1: Unmatched Settlement ===")
    for row in result["part_1_unmatched_table"]:
        print(row)

    print("\n=== Part 2: Deviation Settlement ===")
    for row in result["part_2_deviation_merged_table"]:
        print(row)