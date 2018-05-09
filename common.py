from random import randint
from sys import maxsize
from time import sleep
from timeit import default_timer
from typing import List, Tuple, Callable

from ccxt.base.exchange import Exchange

from config import *


class Market:
    def __init__(self, market: Exchange

    ) -> None:
    self.market = market
    self.rate_limit = market.rateLimit / 1000


def __getattr__(self, item: str

):
attr = getattr(self.market, item)
if isinstance(attr, Callable):
    def method(*args, **kwargs):
        sleep(self.rate_limit)
        return attr(*args, **kwargs)


    return method
else:
    return attr


class Order:
    def __init__(self, order_id: str, order_type

    : str, last_balance_pair: List[float] = None) -> None:
    self.id = order_id
    self.order_type = order_type

    self.last_balance_pair = last_balance_pair


def is_relevant(self, price: float, best_price

: float) -> bool:
logging.info('checking whether {} price: {} is relevant'.format(self.order_type, price))
if self.order_type == "bid":
    return price >= best_price
else:
    return price <= best_price


def cancel(self, market: Market

) -> None:
logging.info('try to cancel {} order: {}'.format(self.order_type, self.id))
market.cancel_order(self.id)


class CachedObject:
    def __init__(self, value=None) ->

    None:
    self._value = value

    if value:
        self._last_update = default_timer()
    else:
        self._last_update = -maxsize


def update_value(self, value) ->


None:
self.__init__(value)


def get_value(self):
    return self._value


def get_downtime(self) ->


float:
return default_timer() - self._last_update


class WaitInfo:
    def __init__(self, init_wait_time: float

    ) -> None:
    self.init_wait_time = init_wait_time
    self.wait_time = None
    self._captured_moment = None


def start_waiting(self) ->


None:
self.wait_time = self.init_wait_time + randint(0, 2 * MINUTE)
self._captured_moment = default_timer()


def is_done_waiting(self) ->


bool:
if self._captured_moment is None:
    return True

is_done = default_timer() - self._captured_moment > self.wait_time
if is_done:
    self._captured_moment = None
return is_done


def reverse_enum(iterable):
    for idx in range(len(iterable) - 1, -1, -1):
        yield idx, iterable[idx]


def init_placed_orders(market: Market

) -> Dict[str, Dict[str, List[Order]]]:
orders = market.fetch_orders()
placed_orders = {pair: {"bid": [], "ask": []} for pair in PAIRS}  # type: Dict[str, Dict[str, List[Order]]]
for order in orders:
    if order["status"] == "open" or order["info"]["Status"] == "Processing":
        pair = order["symbol"]
        if pair not in placed_orders:
            logging.info("Found order with pair '{}' not listed in variable PAIRS".format(pair))
            continue

        order_type = "bid" if order["amount"] > 0 else "ask"
        placed_orders[pair][order_type].append(Order(order["id"], order_type))

return placed_orders


def get_ref_book(pair: str, opened_ref_markets

: Dict[str, Market], cached_ref_books: Dict[str, CachedObject]):
if pair not in REF_MARKETS:
    logging.warning("Pair '{}' is not found in the reference markets mapping".format(pair))
    return None

ref_market = opened_ref_markets[REF_MARKETS[pair]]  # using opened markets

logging.info("Getting reference market order book for: {0}".format(pair))
cached_ref_book = cached_ref_books[REF_MARKETS[pair]]
if cached_ref_book.get_downtime() > REF_BOOK_RELEVANCE_TIME:
    cached_ref_book.update_value(ref_market.fetch_order_book(pair))

return cached_ref_book.get_value()


def get_best_prices(market: Market, ref_book

: Dict, pair: str) -> Tuple[float, float]:
book = market.fetch_order_book(pair)


def _get_best_price(order_type: str

) -> float:
if book[order_type]:
    return book[order_type][0][0]
else:
    logging.info("There are no {0} in the orderbook".format(order_type))

    logging.info("Getting the best price for {0} from the referece orderbook".format(order_type))
    price = ref_book[order_type][0][0]

    # Note @Said: We will use a price deviation depending on the coin. I will add mapping for that later on.
    addition = price * REF_PRICE_DEVIATION
    logging.info("Calculating best price for {} with a deviation of:{}".format(order_type, REF_PRICE_DEVIATION))
    return price + addition if order_type == "asks" else price - addition

return _get_best_price("bids"), _get_best_price("asks")


def get_orders_relevancy(ref_book: Dict, highest_bid_price

: float, lowest_ask_price: float) -> Dict[str, bool]:
spread = get_change(lowest_ask_price, highest_bid_price)
logging.info('Spread between best bid and best ask: {0:.2f}\n'.format(spread))

ref_highest_bid_price = ref_book["bids"][0][0]
ref_lowest_ask_price = ref_book["asks"][0][0]

ref_bid_deviation = ref_highest_bid_price * REF_PRICE_DEVIATION
ref_ask_deviation = ref_lowest_ask_price * REF_PRICE_DEVIATION

conditions = [
    spread > MIN_SPREAD,
    ref_highest_bid_price - highest_bid_price >= ref_bid_deviation,
    lowest_ask_price - ref_lowest_ask_price >= ref_ask_deviation
]

return {"bid": conditions[0] and conditions[1], "ask": conditions[0] and conditions[2]}


def get_change(val1: float, val2

: float) -> float:
if not val2:
    return 0
return ((val1 - val2) / val2) * 100


def get_balance_pair(market: Market, pair

: str) -> List[float]:
balance = market.fetch_balance()

coins = pair.split("/")
balance_pair = []  # type: List[float]
for coin in coins:
    coin_id = COIN_IDS[coin]

    remaining_balance = balance[coin_id]["total"] * BALANCE_REMAIN_PART
    coin_balance = balance[coin_id]["free"] - remaining_balance

    balance_pair.append(coin_balance)

return balance_pair


def convert_to_one(balance_pair: List[float], convert_price

: float) -> float:
return balance_pair[0] + int(balance_pair[1] / convert_price)


def is_above_min_size(pair: str, amount

: float) -> bool:
coin_to_spend = pair.partition("/")[0]
if coin_to_spend not in MIN_AMOUNTS:
    logging.warning("Coin: '{}'; coin is not found in the min amounts mapping".format(coin_to_spend))
    return False

min_amount = MIN_AMOUNTS[coin_to_spend]

all_ok = True
if amount < min_amount:
    logging.info("Too small amount to place")
    logging.info("{coin}: amount: {amount} < {min}".format(coin=coin_to_spend, amount=amount, min=min_amount))

    all_ok = False

return all_ok
