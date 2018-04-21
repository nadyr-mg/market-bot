from typing import Dict, List, Tuple

import ccxt

from config import *


class Orders:
    def __init__(self, bid_id: str, ask_id

    : str, last_balance_pair: List[float] = None) -> None:
    self.bid_id = bid_id
    self.ask_id = ask_id
    self.last_balance_pair = last_balance_pair


@staticmethod
def are_irrelevant(bid_price: float, ask_price

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


def get_best_prices(market: ccxt.lykke, ref_book

: Dict, pair: str) -> Tuple[float, float]:
book = market.fetch_order_book(pair)


def _get_best_price(order_type: str

) -> float:
if book[order_type]:
    return book[order_type][0][0]
else:
    price = ref_book[order_type][0][0]
    addition = price * REF_PRICE_DEVIATION
    return price + addition if order_type == "asks" else price - addition

return _get_best_price("bids"), _get_best_price("asks")


def is_situation_relevant(ref_book: Dict, highest_bid_price

: float, lowest_ask_price: float) -> bool:
spread = get_change(lowest_ask_price, highest_bid_price)
logging.info('Spread between best bid and best ask: {0:.2f}\n'.format(spread))

ref_highest_bid_price = ref_book["bids"][0][0]
ref_lowest_ask_price = ref_book["asks"][0][0]

ref_bid_deviation = ref_highest_bid_price * REF_PRICE_DEVIATION
ref_ask_deviation = ref_lowest_ask_price * REF_PRICE_DEVIATION

return ref_highest_bid_price - highest_bid_price >= ref_bid_deviation and \
       lowest_ask_price - ref_lowest_ask_price >= ref_ask_deviation and \
       spread > MIN_SPREAD


def check_min_size(pair: str, coin1_amount

: float, coin2_amount: float) -> bool:
coins = pair.split("/")
if coins[0] not in MIN_AMOUNTS or coins[1] not in MIN_AMOUNTS:
    logging.warning("Coins: ['{}', '{}']; some coins are not found in the min amounts mapping".format(*coins))
    return False

all_ok = True
if coin1_amount < MIN_AMOUNTS[coins[0]] or coin2_amount < MIN_AMOUNTS[coins[1]]:
    logging.info("Too small amount to place")
    logging.info("{coin}: {amount} - {min}".format(coin=coins[0], amount=coin1_amount, min=MIN_AMOUNTS[coins[0]]))
    logging.info("{coin}: {amount} - {min}".format(coin=coins[1], amount=coin2_amount, min=MIN_AMOUNTS[coins[1]]))

    all_ok = False

return all_ok
