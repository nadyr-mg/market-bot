from typing import Dict, List

import ccxt

from config import *


class Orders:
    def __init__(self, bid_id: str, ask_id

    : str, last_balance_pair: List[float] = None) -> None:
    self.bid_id = bid_id
    self.ask_id = ask_id
    self.last_balance_pair = last_balance_pair


@staticmethod
def is_irrelevant(bid_price: float, ask_price

: float,
  highest_bid_price: float, lowest_ask_price: float) -> bool:
logging.info('checking whether bid price:{0} and ask price:{1} are relevant'.format(bid_price, ask_price))
return bid_price < highest_bid_price or ask_price > lowest_ask_price


def cancel(self, market: ccxt.lykke

) -> None:
logging.info('try to cancel bid order:{0} \n and ask order: {1}'.format(self.bid_id, self.ask_id))
market.cancel_order(self.bid_id)
market.cancel_order(self.ask_id)


def partial_cancel(self, market: ccxt.lykke, bid_status

: str, ask_status: str) -> None:
logging.info('try to partialy cancel open bid/ask orders:')
if bid_status == "open":
    logging.info('try to partialy cancel open bid order:{0}\n'.format(self.bid_id))
    market.cancel_order(self.bid_id)
if ask_status == "open":
    logging.info('try to partialy cancel open ask order:{0}\n'.format(self.ask_id))
    market.cancel_order(self.ask_id)


def get_change(val1: float, val2

: float) -> float:
if not val2:
    return 0
return ((val1 - val2) / val2) * 100.0


def convert_to_one(balance_pair: List[float], convert_price

: float) -> float:
return balance_pair[0] + int(balance_pair[1] / convert_price)


def get_balance_pair(market: ccxt.lykke, pair

: str) -> List[float]:
balance = market.fetch_balance()

coins = pair.split("/")
balance_pair = []  # type: List[float]
for coin in coins:
    coin_id = COIN_IDS[coin]
    coin_balance = balance[coin_id]["free"] * BALANCE_USED_PART

    balance_pair.append(coin_balance)

# balance_pair = [2.5, 0.0019]  # Debug: Minimal balances
return balance_pair


def init_placed_orders(market: ccxt.lykke

) -> Dict[str, Orders]:
orders = market.fetch_open_orders()
grouped_orders = {}  # type: Dict[str, Dict]
for order in orders:
    pair = order["symbol"]
    if pair not in grouped_orders:
        grouped_orders[pair] = {}

    order_type = "bid" if order["amount"] > 0 else "ask"
    grouped_orders[pair][order_type] = order["id"]

placed_orders = {}  # type: Dict[str, Orders]
for pair, orders_pair in grouped_orders.items():
    placed_orders[pair] = Orders(orders_pair["bid"], orders_pair["ask"])

return placed_orders
