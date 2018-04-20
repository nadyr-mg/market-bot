from time import sleep

from common import *

# initialization
lykke = ccxt.lykke({
    'apiKey': API_KEY,
})

placed_orders = init_placed_orders(lykke)


def place_orders(market: ccxt.lykke, placed_orders

: Dict[str, Orders],
  buy_amount: float, sell_amount: float, pair: str) -> None:
print("Entering place_orders func, pair: {}".format(pair))

book = market.fetch_order_book(pair)

if not book["bids"] or not book["asks"]:
    print('Bid/Ask orders are missing => We cannot place an orders')
    return

highest_bid_price = book["bids"][0][0]
lowest_ask_price = book["asks"][0][0]

spread = get_change(lowest_ask_price, highest_bid_price)
print('Spread between best bid and best ask:{0}\n'.format(spread))

cur_orders = placed_orders.get(pair, None)  # type: Orders

balance_pair = get_balance_pair(market, pair)

if cur_orders:
    print("Found placed orders")

    bid_order = market.fetch_order(cur_orders.bid_id)
    ask_order = market.fetch_order(cur_orders.ask_id)

    bid_status = bid_order["status"]
    ask_status = ask_order["status"]
    print('checking current bid status {0} : {1}\nand ask status {2} : {3} \n'
          .format(cur_orders.bid_id, bid_status, cur_orders.ask_id, ask_status))
    if bid_status == ask_status == "open":
        if spread <= MIN_SPREAD or cur_orders.is_irrelevant(bid_order["price"], ask_order["price"],
                                                            highest_bid_price, lowest_ask_price):
            print("Orders are opened and irrelevant. Cancellation...")
            cur_orders.cancel(market)
    elif (bid_status == "closed" or bid_status == "canceled") and \
            (ask_status == "closed" or ask_status == "canceled"):
        print("Orders are already closed. Deleting from dict 'placed_orders'...")
        del placed_orders[pair]

        if bid_status == ask_status == "closed":
            print("Pair: {}; End of round")

            if cur_orders.last_balance_pair is None:
                print("Last balance pair was lost, can't define successful round")
            else:
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
    else:
        print("One of the orders is closed and one is opened. Cancellation...")
        cur_orders.partial_cancel(market, bid_status, ask_status)

        return  # wait until orders will be closed

if spread > MIN_SPREAD:
    print("No orders were found. Placing orders...")

    bid_price = highest_bid_price + 0.000001  # just increase the order by the minimum amount, for eth it would be 0.000001
    ask_price = lowest_ask_price - 0.000001

    converted_buy_amount = int(buy_amount / bid_price)
    bid_id = market.create_limit_buy_order(pair, converted_buy_amount, bid_price)['info']
    ask_id = market.create_limit_sell_order(pair, sell_amount, ask_price)['info']

    placed_orders[pair] = Orders(bid_id, ask_id, balance_pair)


while True:
    balance = lykke.fetch_balance()

    coins_spend_amount = {}  # type: Dict[str, float]
    for coin, coin_id in COIN_IDS.items():
        occur_cnt = sum([1 for pair in PAIRS if coin in pair])

        coin_balance = balance[coin_id]["free"] * BALANCE_USED_PART

        coins_spend_amount[coin] = coin_balance / occur_cnt

    # coins_spend_amount = {  # Debug: Minimal amounts
    #     "WAX": 2.5,
    #     "ETH": 0.0019,
    # }

    for pair in PAIRS:
        coins = pair.split("/")
        coin1_spend_amount, coin2_spend_amount = coins_spend_amount[coins[0]], coins_spend_amount[coins[1]]

        # first amount is what you spend to sell, second - what you spend to buy
        place_orders(lykke, placed_orders, coin2_spend_amount, coin1_spend_amount, pair)

    print('going to sleep for: {0}'.format(PERIOD))
    sleep(PERIOD)
