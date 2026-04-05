"""
Part 2: Deviation Settlement.
Settles the deviation between scheduled and actual electricity,
first via internal peer-to-peer matching, then against the main grid.
"""

from collections import defaultdict
from utils import (round6, quantize, PENALTY_RATE, get_internal_price, classify_deviation,
    _get_bonus_priority, _record_bonus, TRADE_UNIT)


# Record one internal trade between a seller and a buyer
def add_trade(seller, buyer, kwh, internal_price):
    kwh = quantize(kwh)
    if kwh <= 0:
        return

    seller["internal_matched_kwh"] = round6(seller["internal_matched_kwh"] + kwh)
    buyer["internal_matched_kwh"] = round6(buyer["internal_matched_kwh"] + kwh)

    seller["remaining_kwh"] = round6(seller["remaining_kwh"] - kwh)
    buyer["remaining_kwh"] = round6(buyer["remaining_kwh"] - kwh)

    seller["internal_trade_amount"] = round6(seller["internal_trade_amount"] + kwh * internal_price)
    buyer["internal_trade_amount"] = round6(buyer["internal_trade_amount"] + kwh * internal_price)

    seller["internal_trade_direction"] = "sell"
    buyer["internal_trade_direction"] = "buy"

    seller["counterparty_list"].append({
        "household_id": buyer["household_id"],
        "direction": "sell_to",
        "kwh": round6(kwh),
        "price": round6(internal_price),
    })
    buyer["counterparty_list"].append({
        "household_id": seller["household_id"],
        "direction": "buy_from",
        "kwh": round6(kwh),
        "price": round6(internal_price),
    })

    seller["detail_list"].append(f"sell_to {buyer['household_id']}: {kwh:.2f} kWh @ {internal_price}")
    buyer["detail_list"].append(f"buy_from {seller['household_id']}: {kwh:.2f} kWh @ {internal_price}")

# Split the total amount equally and allocate any remainder fairly
def split_amount_equally(rows, total_amount):
    allocations = {h["household_id"]: 0.0 for h in rows}

    total_amount = quantize(total_amount)
    if total_amount <= 0:
        return allocations

    active_rows = [a for a in rows if quantize(a["remaining_kwh"]) > 0]
    if not active_rows:
        return allocations

    # Equal allocation
    avg_share = quantize(total_amount / len(active_rows))
    used = 0.0

    for a in active_rows:
        hid = a["household_id"]
        cap = quantize(a["remaining_kwh"])
        give = quantize(min(avg_share, cap))
        allocations[hid] = give
        used = round6(used + give)

    remain = quantize(total_amount - used)

    # Allocate the remainder by rotation priority
    priority_order = sorted(active_rows,key=lambda x: (_get_bonus_priority(x["household_id"]), x["household_id"]))

    for a in priority_order:
        if remain < TRADE_UNIT:
            break
        hid = a["household_id"]
        cap_left = quantize(a["remaining_kwh"] - allocations[hid])
        if cap_left >= TRADE_UNIT:
            allocations[hid] = round6(allocations[hid] + TRADE_UNIT)
            remain = round6(remain - TRADE_UNIT)
            _record_bonus(hid)

    return {hid: quantize(v) for hid, v in allocations.items()}

# Match surplus and shortage participants through internal trading
def internal_match(surplus_rows, shortage_rows, internal_price):
    surplus_rows = [i for i in surplus_rows  if quantize(i["remaining_kwh"]) > 0]
    shortage_rows = [j for j in shortage_rows if quantize(j["remaining_kwh"]) > 0]

    while surplus_rows and shortage_rows:
        surplus_rows.sort(key=lambda x: (quantize(x["remaining_kwh"]), x["household_id"]))
        shortage_rows.sort(key=lambda x: (quantize(x["remaining_kwh"]), x["household_id"]))

        min_surplus = quantize(surplus_rows[0]["remaining_kwh"])
        min_shortage = quantize(shortage_rows[0]["remaining_kwh"])

        surplus_group = [s for s in surplus_rows  if quantize(s["remaining_kwh"]) == min_surplus]
        shortage_group = [s for s in shortage_rows if quantize(s["remaining_kwh"]) == min_shortage]

        total_surplus = quantize(sum(quantize(r["remaining_kwh"]) for r in surplus_group))
        total_shortage = quantize(sum(quantize(r["remaining_kwh"]) for r in shortage_group))
        matched_total = quantize(min(total_surplus, total_shortage))

        if matched_total <= 0:
            break

        seller_alloc = split_amount_equally(surplus_group,  matched_total)
        buyer_alloc = split_amount_equally(shortage_group, matched_total)

        sellers = [
            [row, quantize(seller_alloc[row["household_id"]])]
            for row in surplus_group
            if quantize(seller_alloc[row["household_id"]]) > 0
        ]
        buyers = [
            [row, quantize(buyer_alloc[row["household_id"]])]
            for row in shortage_group
            if quantize(buyer_alloc[row["household_id"]]) > 0
        ]

        i, j = 0, 0
        while i < len(sellers) and j < len(buyers):
            seller_row, seller_amt = sellers[i]
            buyer_row, buyer_amt = buyers[j]

            deal = quantize(min(seller_amt, buyer_amt))
            add_trade(seller_row, buyer_row, deal, internal_price)

            sellers[i][1] = quantize(sellers[i][1] - deal)
            buyers[j][1] = quantize(buyers[j][1] - deal)

            if sellers[i][1] <= 0:
                i += 1
            if buyers[j][1] <= 0:
                j += 1

        surplus_rows = [r for r in surplus_rows if quantize(r["remaining_kwh"]) > 0]
        shortage_rows = [r for r in shortage_rows if quantize(r["remaining_kwh"]) > 0]


# Main settlement function
def settle_deviation_merged_table(market_records_d, actual_records_d, price_provider):
    market_map = {(r["household_id"], r["timeslot"]): r for r in market_records_d}
    actual_map = {(r["household_id"], r["timeslot"]): r for r in actual_records_d}
    all_keys = sorted(set(market_map) | set(actual_map), key=lambda x: (x[1], x[0]))

    grouped = defaultdict(list)
    for household_id, timeslot in all_keys:
        grouped[timeslot].append(household_id)

    summary = []

    for timeslot, household_ids in grouped.items():
        prices = price_provider.get_prices(timeslot)
        grid_buy = round6(prices["buy"])
        grid_sell = round6(prices["sell"])
        internal_price = get_internal_price(grid_buy, grid_sell)

        rows = []
        surplus_rows = []
        shortage_rows = []

        for household_id in household_ids:
            m = market_map.get((household_id, timeslot), {})
            a = actual_map.get((household_id, timeslot), {})

            is_unscheduled = (household_id, timeslot) not in market_map

            matched_buy = round6(m.get("matched_buy_kwh", 0) or 0)
            matched_sell = round6(m.get("matched_sell_kwh", 0) or 0)
            unmatched_buy = round6(m.get("unmatched_buy_kwh", 0) or 0)
            unmatched_sell = round6(m.get("unmatched_sell_kwh", 0) or 0)
            actual_buy = round6(a.get("actual_buy_kwh", 0) or 0)
            actual_sell = round6(a.get("actual_sell_kwh", 0) or 0)

            scheduled_buy = round6(matched_buy + unmatched_buy)
            scheduled_sell = round6(matched_sell + unmatched_sell)

            deviation_net_kwh, deviation_type, deviation_kwh = classify_deviation(scheduled_buy, scheduled_sell, actual_buy, actual_sell)

            deviation_settle = {
                "household_id": household_id,
                "timeslot": timeslot,
                "is_unscheduled": is_unscheduled,
                "scheduled_buy_kwh": scheduled_buy,
                "scheduled_sell_kwh": scheduled_sell,
                "actual_buy_kwh": actual_buy,
                "actual_sell_kwh": actual_sell,
                "deviation_net_kwh": deviation_net_kwh,
                "deviation_order_kwh": deviation_kwh,
                "deviation_type": deviation_type,
                "internal_trade_direction": "",
                "internal_matched_kwh": 0.0,
                "internal_price_used": internal_price if deviation_type in ["surplus", "shortage"] else 0.0,
                "internal_trade_amount": 0.0,
                "internal_trade_detail_text": "",
                "counterparty_list":  [],
                "final_grid_trade_direction": "",
                "final_grid_kwh": 0.0,
                "grid_price_used": 0.0,
                "final_grid_amount": 0.0,
                "penalty_amount": 0.0,
                "final_settlement_unit_price": 0.0,
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
            internal_match(surplus_rows, shortage_rows, internal_price)

        for deviation_settle in rows:
            remaining_kwh = deviation_settle.pop("remaining_kwh")
            detail_list = deviation_settle.pop("detail_list")

            deviation_settle["internal_trade_detail_text"] = "; ".join(detail_list)
            penalty = 0.0

            if remaining_kwh > 0 and deviation_settle["deviation_type"] in ["surplus", "shortage"]:
                if deviation_settle["deviation_type"] == "shortage":
                    deviation_settle["final_grid_trade_direction"] = "buy_from_grid"
                    price = grid_buy
                else:
                    deviation_settle["final_grid_trade_direction"] = "sell_to_grid"
                    price = grid_sell

                deviation_settle["final_grid_kwh"] = round6(remaining_kwh)
                deviation_settle["grid_price_used"] = price
                deviation_settle["final_grid_amount"] = round6(remaining_kwh * price)
                penalty = round6(deviation_settle["final_grid_amount"] * PENALTY_RATE)

            deviation_settle["penalty_amount"] = penalty

            if deviation_settle["deviation_type"] == "surplus":
                deviation_settle["deviation_net_amount"] = round6(deviation_settle["internal_trade_amount"] + deviation_settle["final_grid_amount"] - penalty)
            elif deviation_settle["deviation_type"] == "shortage":
                deviation_settle["deviation_net_amount"] = round6(-deviation_settle["internal_trade_amount"] - deviation_settle["final_grid_amount"] - penalty)
            else:
                deviation_settle["internal_price_used"] = 0.0
                deviation_settle["deviation_net_amount"] = 0.0

            total_settled_kwh = round6(deviation_settle["internal_matched_kwh"] + deviation_settle["final_grid_kwh"])
            if total_settled_kwh > 0:
                deviation_settle["final_settlement_unit_price"] = round6(abs(deviation_settle["deviation_net_amount"]) / total_settled_kwh)

            summary.append(deviation_settle)

    return summary