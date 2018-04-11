from time import sleep

import ccxt

API_KEY = ""
PAIRS = ['WAX/ETH']  # ['LOC/ETH', 'WAX/ETH', 'CVC/ETH']
MIN_SPREAD = 10
PERIOD = 30
BALANCE_USED_PART = 0.5

COIN_IDS = {
    "ETH": "ETH",
    "LOC": "572475a4-8fef-4e39-909e-85f6bbbc10c4",
    "WAX": "6e25e8ab-5779-4543-855b-71f4857b47d5",
    "CVC": "f9fb5970-2fc4-4b08-900b-870f245e430b"
}


def get_change(val1: float, val2

: float) -> float:
if not val2:
    return 0
return ((val1 - val2) / val2) * 100.0


class Order:
    def __init__(self, order_id: str, is_ask

    : bool = False) -> None:
    self.id = order_id
    self.is_ask = is_ask

    self.is_cancelled = False


def is_relevant(self, cur_price: float, best_price

: float) -> bool:
if self.is_ask:
    if cur_price > best_price:
        return False
else:
    if cur_price < best_price:
        return False
return True  # initialization
lykke = ccxt.lykke({
    'apiKey': API_KEY,
})

placed_orders = {}


def place_orders(lykke: ccxt.lykke, placed_orders

: dict, buy_amount: float, sell_amount: float, pair: str) -> None:
book = lykke.fetch_order_book(pair)

if not book["bids"] or not book["asks"]:
    return

highest_bid_price = book["bids"][0][0]
lowest_ask_price = book["asks"][0][0]

# remove order from dict if it's closed; close the order if it's opened and it's not relevant
if pair in placed_orders:
    for order, best_price in ((placed_orders[pair]["bid"], highest_bid_price),
                              (placed_orders[pair]["ask"], lowest_ask_price)):
        order_info = lykke.fetch_order(order.id)

        if order_info["status"] == "closed":
            # check if round was successful
            del placed_orders[pair]
        elif order_info["status"] == "open":  # close order if it's not relevant
            if not order.is_relevant(order_info["price"], best_price) and not order.is_cancelled:
                lykke.cancel_order(order.id)
                order.is_cancelled = True
            return
        else:
            return

spread = get_change(lowest_ask_price, highest_bid_price)

if spread > MIN_SPREAD:
    bid_price = highest_bid_price + highest_bid_price * 0.02  # increase by 2 percent
    ask_price = lowest_ask_price - lowest_ask_price * 0.02  # decrease by 2 percent

    bid_id = lykke.create_limit_buy_order(pair, buy_amount, bid_price)
    ask_id = lykke.create_limit_sell_order(pair, sell_amount, ask_price)

    placed_orders[pair] = {
        "bid": Order(bid_id),
        "ask": Order(ask_id, is_ask=True)
    }

while True:
    balance = lykke.fetch_balance()
    for pair in PAIRS:
        coins = pair.split("/")
        amounts = []  # first amount is what you sell, second - what you buy

        for coin in coins:
            occur_cnt = sum([1 for pair in PAIRS if coin in pair])
            coin_id = COIN_IDS[coin]

            coin_balance = balance[coin_id]["free"] * BALANCE_USED_PART
            amount = coin_balance / occur_cnt
            amounts.append(amount)

        place_orders(lykke, placed_orders, amounts[1], amounts[0], pair)

    sleep(PERIOD)
