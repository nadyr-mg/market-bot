from time import sleep

import ccxt

API_KEY = ""
PAIRS = ['LOC/ETH', 'WAX/ETH', 'CVC/ETH']
MIN_SPREAD = 10
PERIOD = 30
BALANCE_USED_PART = 0.2

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


class Orders:
    def __init__(self, bid_id: str, ask_id

    : str) -> None:
    self.bid_id = bid_id
    self.ask_id = ask_id

    self.were_cancelled = False


@staticmethod
def is_irrelevant(bid_price: float, ask_price

: float,
  highest_bid_price: float, lowest_ask_price: float) -> bool:
return bid_price < highest_bid_price or ask_price > lowest_ask_price


def cancel(self, lykke: ccxt.lykke

) -> None:
lykke.cancel_order(self.bid_id)
lykke.cancel_order(self.ask_id)

self.were_cancelled = True


def partial_cancel(self, lykke: ccxt.lykke, bid_status

: str, ask_status: str) -> None:
if bid_status == "open":
    lykke.cancel_order(self.bid_id)
if ask_status == "open":
    lykke.cancel_order(self.ask_id)

self.were_cancelled = True  # initialization
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

spread = get_change(lowest_ask_price, highest_bid_price)

cur_orders = placed_orders.get(pair, None)  # type: Orders

if cur_orders:
    bid_order = lykke.fetch_order(cur_orders.bid_id)
    ask_order = lykke.fetch_order(cur_orders.ask_id)

    bid_status = bid_order["status"]
    ask_status = ask_order["status"]

    if bid_status == "open" and ask_status == "open":
        if spread <= MIN_SPREAD or cur_orders.is_irrelevant(bid_order["price"], ask_order["price"],
                                                            highest_bid_price, lowest_ask_price):
            cur_orders.cancel(lykke)
            return
    elif bid_status == "closed" and ask_status == "closed":
        del placed_orders[pair]

        if not cur_orders.were_cancelled:
            # check if round was successful
            print("Pair: {}; End of round")

            snd_currency = pair.partition("/")[2]  # for now it's always 'ETH'
            print("Spent {} {} for buy order".format(bid_order["cost"], snd_currency))
            print("Gained {} {} for sell order".format(ask_order["cost"], snd_currency))

            if bid_order["cost"] < ask_order["cost"]:
                print("Round ended successful")
            else:
                print("Round ended unsuccessful")

            return
    else:
        cur_orders.partial_cancel(lykke, bid_status, ask_status)
        return  # wait until orders will be closed

if spread > MIN_SPREAD:
    bid_price = highest_bid_price + 0.000001  # just increase the order by the minimum amount, for eth it would be 0.000001
    ask_price = lowest_ask_price - 0.000001

    bid_id = lykke.create_limit_buy_order(pair, buy_amount, bid_price)  # TODO: convert buy amount in WAX/LOC/CVC
    ask_id = lykke.create_limit_sell_order(pair, sell_amount, ask_price)

    placed_orders[pair] = Orders(bid_id, ask_id)


while True:
    balance = lykke.fetch_balance()
    for pair in PAIRS:
        coins = pair.split("/")
        amounts = []  # first amount is what you spend to sell, second - what you spend to buy

        for coin in coins:
            occur_cnt = sum([1 for pair in PAIRS if coin in pair])
            coin_id = COIN_IDS[coin]

            coin_balance = balance[coin_id]["free"] * BALANCE_USED_PART
            amount = coin_balance / occur_cnt
            amounts.append(amount)

        place_orders(lykke, placed_orders, amounts[1], amounts[0], pair)

    sleep(PERIOD)
