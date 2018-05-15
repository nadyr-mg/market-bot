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

    : str) -> None:
    self.id = order_id
    self.order_type = order_type


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


def start_waiting(self, addition: float

) -> None:
self.wait_time = self.init_wait_time + addition
self._captured_moment = default_timer()


def is_done_waiting(self) ->


bool:
if self._captured_moment is None:
    return True

is_done = default_timer() - self._captured_moment > self.wait_time
if is_done:
    self._captured_moment = None
return is_done


class Orders:
    def __init__(self, order_type: str

    ) -> None:
    self.orders = []  # type: List[Order]
    self.order_type = order_type

    self.wait_time_set = False
    self.wait_info = WaitInfo(0)


def add(self, order_id: str

) -> None:
self.orders.append(Order(order_id, self.order_type))


def pop(self, idx: int

) -> Order:
return self.orders.pop(idx)


def get(self, idx: int

) -> Order:
return self.orders[idx]


def set_wait_time(self) ->


None:
if not self.wait_time_set:
    # waiting for random time after cancellation
    wait_time = randint(*AFTER_CANCEL_WAIT_BOUNDS)
    self.wait_info.start_waiting(wait_time)
    self.wait_time_set = True


def is_placing_available(self) ->


bool:
is_available = self.wait_info.is_done_waiting()
if is_available:
    # done with waiting, reset flag
    self.wait_time_set = False
return is_available


def reverse_enum(iterable):
    for idx in range(len(iterable) - 1, -1, -1):
        yield idx, iterable[idx]


def init_placed_orders(market: Market

) -> Dict[str, Dict[str, Orders]]:
orders = market.fetch_orders()
placed_orders = {pair: {"bid": Orders("bid"), "ask": Orders("ask")}
                 for pair in PAIRS}  # type: Dict[str, Dict[str, Orders]]
for order in orders:
    if order["status"] == "open" or order["info"]["Status"] == "Processing":
        pair = order["symbol"]
        if pair not in placed_orders:
            logging.info("Found order with pair '{}' not listed in variable PAIRS".format(pair))
            continue

        order_type = "bid" if order["amount"] > 0 else "ask"
        placed_orders[pair][order_type].add(order["id"])

return placed_orders


def get_ref_book(pair: str, opened_ref_markets

: Dict[str, Market], cached_ref_books: Dict[str, CachedObject]):
ref_market = opened_ref_markets[REF_MARKETS[pair]]  # using opened markets

logging.info("Getting reference market order book for: {0}".format(pair))
cached_ref_book = cached_ref_books[REF_MARKETS[pair]]
if cached_ref_book.get_downtime() > REF_BOOK_RELEVANCE_TIME:
    cached_ref_book.update_value(ref_market.fetch_order_book(pair))

return cached_ref_book.get_value()


def get_best_prices(market: Market, ref_book

: Dict, pair: str) -> Tuple[float, float]:
book = market.fetch_order_book(pair)
ref_price_deviation = REF_PRICE_DEVIATIONS[pair]


def _get_best_price(order_type: str

) -> float:
if book[order_type]:
    return book[order_type][0][0]
else:
    logging.info("There are no {0} in the orderbook".format(order_type))

    logging.info("Getting the best price for {0} from the reference orderbook".format(order_type))
    price = ref_book[order_type][0][0]

    addition = price * ref_price_deviation
    logging.info("Calculating best price for {} with a deviation of:{}".format(order_type, ref_price_deviation))
    return price + addition if order_type == "asks" else price - addition

return _get_best_price("bids"), _get_best_price("asks")


def get_orders_relevancy(ref_book: Dict, highest_bid_price

: float,
  lowest_ask_price: float, pair: str) -> Dict[str, bool]:
spread = get_change(lowest_ask_price, highest_bid_price)
logging.info('Spread between best bid and best ask: {0:.2f}\n'.format(spread))

ref_highest_bid_price = ref_book["bids"][0][0]
ref_lowest_ask_price = ref_book["asks"][0][0]

ref_price_deviation = REF_PRICE_DEVIATIONS[pair]
ref_bid_deviation = ref_highest_bid_price * ref_price_deviation
ref_ask_deviation = ref_lowest_ask_price * ref_price_deviation

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


def convert_to_one(balance_pair: List[float], convert_price

: float) -> float:
return balance_pair[0] + int(balance_pair[1] / convert_price)


def is_above_min_size(pair: str, amount

: float) -> bool:
coin_to_spend = pair.partition("/")[0]
min_amount = MIN_AMOUNTS[coin_to_spend]

all_ok = True
if amount < min_amount:
    logging.info("Too small amount to place")
    logging.info("{coin}: amount: {amount} < {min}".format(coin=coin_to_spend, amount=amount, min=min_amount))

    all_ok = False

return all_ok


def check_conf_files() ->


bool:
is_check_passed = True

for pair in PAIRS:
    # reference_markets.json
    if pair not in REF_MARKETS:
        logging.warning("Pair '{}' is not found in the reference markets mapping".format(pair))
        is_check_passed = False

    # ref_deviations.json
    if pair not in REF_PRICE_DEVIATIONS:
        logging.warning("Pair '{}' is not found in the reference deviations mapping".format(pair))
        is_check_passed = False

# min_amounts.json
for coin in COIN_IDS:
    if coin not in MIN_AMOUNTS:
        logging.warning("Coin: '{}'; coin is not found in the min amounts mapping".format(coin))
        is_check_passed = False

return is_check_passed


def is_round_successful(buy_order: Dict, sell_order

: Dict, buy_price: float, sell_price: float) -> bool:
buy_amount = buy_order["filled"]
sell_amount = sell_order["filled"]

buy_cost = buy_order["cost"]
sell_cost = sell_order["cost"]

amount_traded = min(buy_amount, sell_amount)
expected_profit = (sell_price - buy_price) * amount_traded
profit_deviation = expected_profit * ACCEPTABLE_PROFIT_DEVIATION
logging.info("expected profit: {}".format(expected_profit))

if buy_amount == sell_amount:  # A complete Trade
    actual_profit = sell_cost - buy_cost
    logging.info("actual profit: {}".format(actual_profit))

    result = abs(actual_profit - expected_profit) < profit_deviation
else:  # A partial trade
    actual_profit = (sell_order["price"] - buy_order["price"]) * amount_traded
    logging.info("actual profit: {}".format(actual_profit))

    if amount_traded == sell_amount:  # in case of filled_sell < filled_buy
        actual_profit2 = sell_cost - sell_amount * buy_price
    else:
        actual_profit2 = buy_amount * sell_price - buy_cost
    logging.info("actual profit2: {}".format(actual_profit2))

    result = abs(actual_profit - expected_profit) < profit_deviation and \
             abs(actual_profit2 - expected_profit) < profit_deviation

return result
