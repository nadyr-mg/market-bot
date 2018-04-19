from time import sleep
from typing import Dict, Tuple

import ccxt

API_KEY = "1c15115b-b5b6-4920-9629-4c444e346613"
PAIRS = ['WAX/ETH']
# PAIRS = ['LOC/ETH', 'WAX/ETH', 'CVC/ETH']
MIN_SPREAD = 10
PERIOD = 30
BALANCE_USED_PART = 0.5

# COIN_IDS = {
#    "ETH": "ETH",
#    "LOC": "572475a4-8fef-4e39-909e-85f6bbbc10c4",
#    "WAX": "6e25e8ab-5779-4543-855b-71f4857b47d5",
#    "CVC": "f9fb5970-2fc4-4b08-900b-870f245e430b"
#}

COIN_IDS = {
    "ETH": "ETH",
    "WAX": "6e25e8ab-5779-4543-855b-71f4857b47d5"
}


def get_change(val1: float, val2

: float) -> float:
if not val2:
    return 0
return ((val1 - val2) / val2) * 100.0


class Orders:
    def __init__(self, bid_id: str, ask_id

    : str, last_balance_pair: Tuple[float, float]) -> None:
    self.bid_id = bid_id
    self.ask_id = ask_id
    self.last_balance_pair = last_balance_pair

    self.were_cancelled = False


@staticmethod
def is_irrelevant(bid_price: float, ask_price

: float,
  highest_bid_price: float, lowest_ask_price: float) -> bool:
print('checking whether bid price:{0} and ask price:{1} are relevant'.format(bid_price, ask_price))
return bid_price < highest_bid_price or ask_price > lowest_ask_price


def cancel(self, market: ccxt.lykke

) -> None:
print('try to cancel bid order:{0} \n and ask order: {1}'.format(self.bid_id, self.ask_id))
market.cancel_order(self.bid_id)
market.cancel_order(self.ask_id)
## we still need to check the if the orders where realy canceld or not
## --> check with lykke.fetch_open_orders() or with lykke.fetch_order() and check if order status is canceled

self.were_cancelled = True


def partial_cancel(self, market: ccxt.lykke, bid_status

: str, ask_status: str) -> None:
print('try to partialy cancel open bid/ask orders:\n')
if bid_status == "open":
    print('try to partialy cancel open bid order:{0}\n'.format(self.bid_id))
    market.cancel_order(self.bid_id)
if ask_status == "open":
    print('try to partialy cancel open ask order:{0}\n'.format(self.ask_id))
    market.cancel_order(self.ask_id)

self.were_cancelled = True


class CoinInfo:
    def __init__(self, spend_amount: float, balance

    : float) -> None:
    self.spend_amount = spend_amount
    self.balance = balance  # initialization
lykke = ccxt.lykke({
    'apiKey': API_KEY,
})

placed_orders = {}  ## -> Should be initailized with the our current orders -> lykke.fetch_open_orders()


# are you checking whether you already have placed orders or not ?
def place_orders(market: ccxt.lykke, placed_orders

: Dict[str, Orders], balance_pair: Tuple[float, float],
                                   buy_amount: float, sell_amount: float, pair: str) -> None:
print('Preparing to place orders:\n')
book = market.fetch_order_book(pair)

if not book["bids"] or not book[
    "asks"]:  # what is this doing ? checking whether we have bid or ask orders in the orderbook ? If the orderbook is empty it quites the function ?
    print('Bid/Ask orders are missing => We cannot place an orders')
    return

highest_bid_price = book["bids"][0][0]
lowest_ask_price = book["asks"][0][0]

spread = get_change(lowest_ask_price, highest_bid_price)
print('Spread between best bid and best ask:{0}\n'.format(spread))

cur_orders = placed_orders.get(pair, None)  # type: Orders

if cur_orders:
    bid_order = market.fetch_order(cur_orders.bid_id)
    ask_order = market.fetch_order(cur_orders.ask_id)

    bid_status = bid_order["status"]
    ask_status = ask_order["status"]
    print('checking current bid status {0} : {1} \nand ask status {2} : {3} \n'.format(cur_orders.bid_id, bid_status,
                                                                                       cur_orders.ask_id, ask_status))

    if bid_status == "open" and ask_status == "open":
        if spread <= MIN_SPREAD or cur_orders.is_irrelevant(bid_order["price"], ask_order["price"],
                                                            highest_bid_price, lowest_ask_price):
            cur_orders.cancel(market)
            return
    elif bid_status == "closed" and ask_status == "closed":
        del placed_orders[pair]

        if not cur_orders.were_cancelled:
            print("Pair: {}; End of round")

            last_balance_pair = cur_orders.last_balance_pair
            coins = pair.split("/")

            print("Balance before round: {} - {}; {} - {}".format(coins[0], last_balance_pair[0],
                                                                  coins[1], last_balance_pair[1]))
            print("Balance after round: {} - {}; {} - {}".format(coins[0], balance_pair[0],
                                                                 coins[1], balance_pair[1]))

            # check if round was successful
            last_amount = convert_to_one(last_balance_pair, highest_bid_price)
            cur_amount = convert_to_one(balance_pair, highest_bid_price)
            if last_amount < cur_amount:
                print("Round ended successfully")
            else:
                print("Round ended unsuccessfully")

            return
    else:
        cur_orders.partial_cancel(market, bid_status, ask_status)
        return  # wait until orders will be closed

if spread > MIN_SPREAD:
    print('Spread > min spread of: '.format(MIN_SPREAD))
    bid_price = highest_bid_price + 0.000001  # just increase the order by the minimum amount, for eth it would be 0.000001
    ask_price = lowest_ask_price - 0.000001

    converted_buy_amount = int(buy_amount / bid_price)
    bid_id = market.create_limit_buy_order(pair, converted_buy_amount, bid_price)
    # print(bid_id['info']," <- Bid ID") # --> 'info' contains the id, this is the root cause for the issue --> should be fixed
    ask_id = market.create_limit_sell_order(pair, sell_amount, ask_price)

    print('placing bid and ask orders\n')
    placed_orders[pair] = Orders(bid_id['info'], ask_id['info'],
                                 balance_pair)  # using ['info'] is a workaround --> should be fixed

def convert_to_one(balance_pair, convert_price):
    return balance_pair[0] + int(balance_pair[1] / convert_price)


while True:
    balance = lykke.fetch_balance()

    coins_info = {}  # type: Dict[str, CoinInfo]
    for coin, coin_id in COIN_IDS.items():
        occur_cnt = sum([1 for pair in PAIRS if coin in pair])

        coin_balance = balance[coin_id]["free"] * BALANCE_USED_PART

        amount = coin_balance / occur_cnt
        coins_info[coin] = CoinInfo(amount, coin_balance)

    for pair in PAIRS:
        coins = pair.split("/")
        coin1_info, coin2_info = coins_info[coins[0]], coins_info[coins[1]]

        balance_pair = (coin1_info.balance, coin2_info.balance)

        # first amount is what you spend to sell, second - what you spend to buy
        place_orders(lykke, placed_orders, balance_pair, coin2_info.spend_amount, coin1_info.spend_amount, pair)
        ##
        ## => Bot keeps adding orders to the same pair -> It does not recognis its own orders so it keeps adding up Orders

    print('going to sleep for: {0}'.format(PERIOD))
    sleep(PERIOD)
