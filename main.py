from time import sleep

from common import *

# initialization
lykke = ccxt.lykke({'apiKey': API_KEY})

placed_orders = init_placed_orders(lykke)


def place_orders(market: ccxt.lykke, placed_orders

: Dict[str, Orders],
  buy_amount: float, sell_amount: float, pair: str) -> None:
logging.info("Entering place_orders func, pair: {}".format(pair))

if pair not in REF_MARKETS:
    logging.warning("Pair '{}' is not found in the reference markets mapping".format(pair))
    return
ref_market = getattr(ccxt, REF_MARKETS[pair])()
ref_book = ref_market.fetch_order_book(pair)

highest_bid_price, lowest_ask_price = get_best_prices(market, ref_book, pair)

situation_relevant = is_situation_relevant(ref_book, highest_bid_price, lowest_ask_price)
logging.info('Is situation relevant?: {}\n'.format(situation_relevant))

cur_orders = placed_orders.get(pair, None)  # type: Orders

balance_pair = get_balance_pair(market, pair)

if cur_orders:
    logging.info("Found placed orders")

    bid_order = market.fetch_order(cur_orders.bid_id)
    ask_order = market.fetch_order(cur_orders.ask_id)

    bid_status = bid_order["status"]
    ask_status = ask_order["status"]
    logging.info('checking current bid status {} : {}\nand ask status {} : {} \n'
                 .format(cur_orders.bid_id, bid_status, cur_orders.ask_id, ask_status))
    if bid_status == ask_status == "open":
        if not situation_relevant or cur_orders.are_irrelevant(bid_order["price"], ask_order["price"],
                                                               highest_bid_price, lowest_ask_price):
            logging.info("Orders are opened and irrelevant. Cancellation...")
            cur_orders.cancel(market)
    elif (bid_status == "closed" or bid_status == "canceled") and \
            (ask_status == "closed" or ask_status == "canceled"):
        logging.info("Orders are already closed. Deleting from dict 'placed_orders'...")
        del placed_orders[pair]

        if bid_status == ask_status == "closed":
            logging.info("Pair: {}; End of round")

            if cur_orders.last_balance_pair is None:
                logging.info("Last balance pair was lost, can't define successful round")
            else:
                last_balance_pair = cur_orders.last_balance_pair
                coins = pair.split("/")

                logging.info("Balance before round: {} - {}; {} - {}".format(coins[0], last_balance_pair[0],
                                                                             coins[1], last_balance_pair[1]))
                logging.info("Balance after round: {} - {}; {} - {}".format(coins[0], balance_pair[0],
                                                                            coins[1], balance_pair[1]))

                # check if round was successful
                last_amount = convert_to_one(last_balance_pair, highest_bid_price)
                cur_amount = convert_to_one(balance_pair, highest_bid_price)
                if last_amount < cur_amount:
                    logging.info("Round ended successfully")
                else:
                    logging.info("Round ended unsuccessfully")
    else:
        logging.info("One of the orders is closed and one is opened. Cancellation...")
        cur_orders.partial_cancel(market, bid_status, ask_status)

        return  # wait until orders will be closed

if situation_relevant:
    logging.info("No orders were found. Placing orders...")

    bid_price = highest_bid_price + 0.000001
    ask_price = lowest_ask_price - 0.000001

    converted_buy_amount = int(buy_amount / bid_price)
    # amount you spend to sell - first coin, amount you spend to buy -  second coin
    if not check_min_size(pair, sell_amount, converted_buy_amount):
        return

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

    logging.info('going to sleep for: {0}'.format(PERIOD))
    sleep(PERIOD)
