# Balancing Operator
Balancing is mainly divided into two parts. The first part is the **settlement of unmatched orders**. For orders that have not been successfully matched internally after the market P2P process, balancing will directly settle these orders with the main grid and charge a certain penalty. The second part is the **deviation settlement**. It calculates the deviation between the actual buy/sell electricity of households and the committed buy/sell electricity within the same timeslot. These deviations will be prioritized for matching within the community, and the remaining deviations that cannot be matched internally will be settled with the main grid and a penalty will be charged.

- **main.py** 
- **data.py:** Stores sample market records and actual records for testing
- **validators.py:** Checks inputs for duplicate entries and buy/sell conflicts
- **utils.py:** Shared math helpers, constants, and deviation classifier
- **part1_unmatched.py:** Settles unmatched orders against the main grid with penalty
- **part2_deviation.py:** Matches deviations internally and settles remainder with grid
- **Price_Cal.py:** The hourly average from 2026-1-1 to 2026-3-1 found on Octopus
- csv_agile_L_South_Western_England.csv (ToU)
- csv_agileoutgoing_L_South_Western_England.csv (FiT)


Expected Input:
- **"market_records":** matched and unmatched electricity of each household (shows in data.py)
- **"actual records":** real buy/sell electricity of each household (shows in data.py)
- **"PRICE_TABLE" :** Main grid price (FiT(sell) and ToU(buy)) like: {"00:00": {"buy": 18.701638, "sell": 8.031167},
                                                                      "01:00": {"buy": 18.295287, "sell": 7.874833},
                                                                      ...}

Expected Output:
- **Unmatched settlement:** includes {
                "household_id";
                "timeslot";
                "unmatched_buy_kwh": Unmatched buying volume;
                "unmatched_sell_kwh": Unmatched selling volume;
                "grid_trade_direction";
                "penalty_amount": Penalty cost;
                "final_settlement_unit_price": Unit price including penalty;
                "unmatched_net_amount": Final net payment amount
            }
- **Deviation settlement:** includes {
                "household_id";
                "timeslot";
                "deviation_order_kwh": Absolute deviation;
                "deviation_type";
                "internal_trade_direction";
                "internal_matched_kwh": Internal matching trading volume;
                "counterparty_list": Counterparty details;
                "final_grid_trade_direction";
                "final_grid_kwh"：Volume of trades with the grid;
                "penalty_amount": Penalty cost;
                "final_settlement_unit_price": Unit price including penalty;
                "deviation_net_amount": Final net payment amount
            }


Each household's final settlement for a given timeslot consists of three components:

**Final net amount** (per household, per timeslot) **= matched_net_amount**(from Market Operator) **+ unmatched_net_amount**(from Balancing Operator Part 1) **+ deviation_net_amount**(from Balancing Operator Part 2)

In the balancing section, buying (paying) is negative and selling (receiving) is positive

**Key Changes**
1. Convert a single file to multiple modules
2. Field refactor：committed_* → matched_* + unmatched_*
3. Part 2 internal matching price mechanism changed: Dual spread pricing → Single midpoint price
4. Remaining allocation: Change from fixed alphabetical order to rotation priority
5. More complete verification: Added buy/sell mutual exclusion verification

