import smtplib
from email.message import EmailMessage
from traceback import format_exc
from json import dump
from numpy import isclose

from structures import *
from config import *



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
            info("Found order with pair '{}' not listed in variable PAIRS".format(pair))
            continue

        order_type = "bid" if order["amount"] > 0 else "ask"
        placed_orders[pair][order_type].add(order["id"])

return placed_orders


def get_ref_book(pair: str, opened_ref_markets

: Dict[str, Market], cached_ref_books: Dict[str, CachedObject]):
ref_market = opened_ref_markets[REF_MARKETS[pair]]  # using opened markets

info("Getting reference market order book for: {0}".format(pair))
cached_ref_book = cached_ref_books[REF_MARKETS[pair]]
if cached_ref_book.get_downtime() > REF_BOOK_RELEVANCE_TIME:
    cached_ref_book.update_value(ref_market.fetch_order_book(pair))

return cached_ref_book.get_value()


def get_best_prices(book: Dict, ref_book

: Dict, pair: str) -> Tuple[float, float]:
ref_price_deviation = REF_PRICE_DEVIATIONS[pair]


def _get_best_price(order_type: str

) -> float:
if book[order_type]:
    return book[order_type][0][0]
else:
    info("There are no {0} in the orderbook".format(order_type))

    info("Getting the best price for {0} from the reference orderbook".format(order_type))
    price = ref_book[order_type][0][0]

    addition = price * ref_price_deviation
    info("Calculating best price for {} with a deviation of:{}".format(order_type, ref_price_deviation))
    return price + addition if order_type == "asks" else price - addition

return _get_best_price("bids"), _get_best_price("asks")


def get_orders_relevancy(ref_book: Dict, highest_bid_price

: float,
  lowest_ask_price: float, pair: str) -> Dict[str, bool]:
spread = get_change(lowest_ask_price, highest_bid_price)
info('Spread is about: {0:.2f}%'.format(spread))

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
    info("Too small amount to place")
    info("{coin}: amount: {amount} < {min}".format(coin=coin_to_spend, amount=amount, min=min_amount))

    all_ok = False

return all_ok


def check_conf_files() ->


bool:
is_check_passed = True

for pair in PAIRS:
    # reference_markets.json
    if REF_MARKETS.get(pair) is None:
        logging.warning("Pair '{}' is not found in the reference markets mapping".format(pair))
        is_check_passed = False

    # ref_deviations.json
    if REF_PRICE_DEVIATIONS.get(pair) is None:
        logging.warning("Pair '{}' is not found in the reference deviations mapping".format(pair))
        is_check_passed = False

    if pair not in USED_BALANCE_PAIRS:
        logging.warning("Pair '{}' is not found in the 'USED_BALANCE_PAIRS' variable".format(pair))
        is_check_passed = False

    coins = pair.split('/')
    if coins[0] not in COIN_IDS or coins[1] not in COIN_IDS:
        logging.warning("Coin from pair '{}' is not found in the 'COIN_IDS' variable".format(pair))
        is_check_passed = False

# min_amounts.json
for coin in COIN_IDS:
    if MIN_AMOUNTS.get(coin) is None:
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
info("expected profit: {}".format(expected_profit))

if buy_amount == sell_amount:  # A complete Trade
    actual_profit = sell_cost - buy_cost
    info("actual profit: {}".format(actual_profit))

    result = abs(actual_profit - expected_profit) < profit_deviation
else:  # A partial trade
    actual_profit = (sell_order["price"] - buy_order["price"]) * amount_traded
    info("actual profit: {}".format(actual_profit))

    if amount_traded == sell_amount:  # in case of filled_sell < filled_buy
        actual_profit2 = sell_cost - sell_amount * buy_price
    else:
        actual_profit2 = buy_amount * sell_price - buy_cost
    info("actual profit2: {}".format(actual_profit2))

    result = abs(actual_profit - expected_profit) < profit_deviation and \
             abs(actual_profit2 - expected_profit) < profit_deviation

return result


def send_message(header: str, text

: str) -> None:
msg = EmailMessage()

msg['Subject'] = header
msg['From'] = FROM_EMAIL
msg['To'] = TO_EMAIL
msg.set_content(text)

with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.starttls()
    server.login(LOGIN, PASSW)

    server.send_message(msg)


def get_log_extract() ->


str:
with open(LOG_FILENAME) as file:
    logs = reversed(file.read().split('\n'))

return '\n'.join([line for idx, line in enumerate(logs) if idx < LINES_TO_SEND])


def get_last_traceback() ->


str:
return format_exc(chain=False)


def construct_order_dict(order_info):
    return {
        'Datetime': order_info['datetime'],
        'CreatedAt': order_info['info']['CreatedAt'],
        'Pair': order_info['symbol'],
        'Volume': order_info['amount'],
        'Filled': order_info['filled'],
        'Price': order_info['price'],
        'Cost': order_info['cost'],
    }


def log_filled_order(order_info):
    with open(FILLED_ORDERS_FILE) as file:
        filled_orders = load(file)  # type: Dict[str, List]

    created_at = order_info['info']['CreatedAt']
    if created_at not in filled_orders:
        filled_orders[created_at] = []

    order_dict = construct_order_dict(order_info)
    if order_dict not in filled_orders[created_at]:
        filled_orders[created_at].append(order_dict)

    with open(FILLED_ORDERS_FILE, 'w') as out:
        dump(filled_orders, out)


def get_lowest_price_diff(pair: str

) -> float:
coins = pair.split("/")
base = coins[0]
quote = coins[1]
currencies = ['USD', 'EUR', 'CHF', 'JPY', 'GBP']

if any(quote in currency for currency in currencies):
    diff = 0.00001
else:
    diff = 0.000001

return diff


def is_last_order_at_best(book: Dict, ref_book

: Dict, pair: str) -> Dict[str, bool]:
def _is_last_order_at_best(order_type: str

) -> bool:
if book[order_type]:
    if len(book[order_type]) > 1:
        last_orders_diff = abs(book[order_type][0][0] - book[order_type][1][0])
    else:
        info('Only one order in book, hence it\'s at best')
        return True
else:
    if len(ref_book[order_type]) > 1:
        last_orders_diff = abs(ref_book[order_type][0][0] - ref_book[order_type][1][0])
    else:
        info('Only one order in ref_book, hence it\'s at best')
        return True

lowest_diff = get_lowest_price_diff(pair)
info(
    "Calculating difference between two last orders, lowest diff for {0}: lowest_diff {1} | last_orders_diff: {2}".format(
        order_type, lowest_diff, last_orders_diff))
return last_orders_diff < lowest_diff or isclose(last_orders_diff, lowest_diff)

return {
    'bid': _is_last_order_at_best("bids"),
    'ask': _is_last_order_at_best("asks"),
}
