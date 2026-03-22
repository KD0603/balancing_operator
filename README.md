# Balancing Operator
Balancing is mainly divided into two parts. The first part is the settlement of un-matched orders. For orders that have not been successfully matched internally after the market P2P process, balancing will directly settle these orders with the main grid and charge a certain penalty. The second part is the deviation settlement. It calculates the deviation between the actual buy/sell electricity of households and the committed buy/sell electricity within the same timeslot. These deviations will be prioritized for matching within the community, and the remaining deviations that cannot be matched internally will be settled with the main grid and a penalty will be charged.

- Price_Cal.py: The hourly average from 2026-1-1 to 2026-3-1 found on Octopus
- balancing_part.py


Expected Input:
- "market_records"
- "actual records"
- "PRICE_TABLE" : Main grid price (FiT and ToU)

Expected Output:
- Unmatched settlement: includes household ID, timeslot, unmatched orders, final settlement price
- Deviation settlement: includes household ID, timeslot, deviation order, deviation type, internal transaction volume, internal transaction price, internal transaction party, grid transaction volume, grid transaction price, final settlement price

