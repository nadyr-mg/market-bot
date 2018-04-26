import ccxt

from common import *

# initialization
logging.info('Starting Bot ...')

lykke = Market(ccxt.lykke({'apiKey': API_KEY}))

placed_orders = init_placed_orders(lykke)
cancel_half_opened_orders(lykke, placed_orders)

opened_ref_markets = {market_name: Market(getattr(ccxt, market_name)())
                      for market_name in USED_REF_MARKETS}  # type: Dict[str, Market]


def place_orders(market: Market, placed_orders

: Dict[str, Orders],
  buy_amount: float, sell_amount: float, pair: str) -> None:
logging.info("Entering place_orders func, pair: {}".format(pair))

if pair not in REF_MARKETS:
    logging.warning("Pair '{}' is not found in the reference markets mapping".format(pair))
    return
ref_market = opened_ref_markets[REF_MARKETS[pair]]  # using opened markets

logging.info("Getting reference market order book for: {0}".format(pair))
ref_book = ref_market.fetch_order_book(pair)

highest_bid_price, lowest_ask_price = get_best_prices(market, ref_book, pair)
logging.info("Getting/calculating best bid price: {0}".format(highest_bid_price))
logging.info("Getting/calculating best ask price: {0}".format(lowest_ask_price))

situation_relevant = is_situation_relevant(ref_book, highest_bid_price, lowest_ask_price)
logging.info('Is situation relevant?: {}\n'.format(situation_relevant))

cur_orders = placed_orders.get(pair, None)  # type: Orders

balance_pair = get_balance_pair(market, pair)

if cur_orders:
    logging.info("Found placed orders on trading market")

    bid_order = market.fetch_order(cur_orders.bid_id)
    ask_order = market.fetch_order(cur_orders.ask_id)

    bid_status = bid_order["status"]
    ask_status = ask_order["status"]
    logging.info('checking current bid status {} : {}\nand ask status {} : {} \n'
                 .format(cur_orders.bid_id, bid_status, cur_orders.ask_id, ask_status))
    if bid_status == ask_status == "open":
        relevant_value = cur_orders.are_relevant(bid_order["price"], ask_order["price"],
                                                 highest_bid_price, lowest_ask_price)
        if not situation_relevant or not relevant_value:
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
    if not is_above_min_size(pair, converted_buy_amount) or \
            not is_above_min_size(pair, sell_amount):
        return

    bid_id = market.create_limit_buy_order(pair, converted_buy_amount, bid_price)['info']
    ask_id = market.create_limit_sell_order(pair, sell_amount, ask_price)['info']

    placed_orders[pair] = Orders(bid_id, ask_id, balance_pair)


while True:
    logging.info('Fetching free balance ...')
    balance = lykke.fetch_balance()

    coins_spend_amount = {}  # type: Dict[str, float]
    for coin, coin_id in COIN_IDS.items():
        occur_cnt = sum([1 for pair in PAIRS if coin in pair])

        coin_balance = balance[coin_id]["free"] * BALANCE_USED_PART
        logging.info('+{0} : {1}'.format(coin, balance[coin_id]["free"]))
        coins_spend_amount[coin] = coin_balance / occur_cnt
        logging.info('Order size for {0}: {1}'.format(coin, coins_spend_amount[coin]))

    # coins_spend_amount = {  # Debug: Minimal amounts
    #     "WAX": MIN_AMOUNTS["WAX"],
    #     "ETH": MIN_AMOUNTS["ETH"],
    # }

    for pair in PAIRS:
        coins = pair.split("/")
        coin1_spend_amount, coin2_spend_amount = coins_spend_amount[coins[0]], coins_spend_amount[coins[1]]

        # first amount is what you spend to sell, second - what you spend to buy
        place_orders(lykke, placed_orders, coin2_spend_amount, coin1_spend_amount, pair)

    logging.info('going to sleep for: {}\n'.format(PERIOD))
    sleep(PERIOD)
