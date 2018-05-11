import ccxt
from ccxt.base.errors import RequestTimeout

from common import *


def place_orders(market: Market, placed_orders

: Dict[str, Dict[str, Orders]],
  buy_amount: float, sell_amount: float, pair: str) -> None:
logging.info("Entering place_orders func, pair: {}".format(pair))

ref_book = get_ref_book(pair, opened_ref_markets, cached_ref_books)
if ref_book is None:
    return

highest_bid_price, lowest_ask_price = get_best_prices(market, ref_book, pair)
logging.info("Getting/calculating best bid price: {0}".format(highest_bid_price))
logging.info("Getting/calculating best ask price: {0}".format(lowest_ask_price))

orders_relevancy = get_orders_relevancy(ref_book, highest_bid_price, lowest_ask_price)
logging.info('Is orders are relevant?\n{}'.format(orders_relevancy))

cur_orders = placed_orders[pair]  # type: Dict[str, Orders]

if cur_orders["bid"] or cur_orders["ask"]:
    logging.info("Found placed orders on trading market")

    for order_type in cur_orders:
        for order_idx, order in reverse_enum(cur_orders[order_type].orders):
            order_info = market.fetch_order(order.id)

            status = order_info["status"]
            best_price = highest_bid_price if order_type == "bid" else lowest_ask_price
            logging.info("checking current {} status '{}': {}\n".format(order_type, status, order.id))
            if status == "open":
                relevant_value = order.is_relevant(order_info["price"], best_price)
                if not orders_relevancy[order_type] or not relevant_value:
                    logging.info("Order is opened and irrelevant. Cancellation...")

                    # All open orders have the same price, hence if one is irrelevant -> all are irrelevant
                    order.cancel(market)
                    cur_orders[order_type].set_wait_time()
            else:
                logging.info("Order is already closed. Deleting from dict 'placed_orders'...")
                cur_orders[order_type].pop_order(order_idx)

                # TODO: define successful round

    for order_type in ("bid", "ask"):
        if not orders_relevancy[order_type] or not cur_orders[order_type].is_placing_available():
            continue

        # we don't want to place an order that will be above our other orders
        if cur_orders[order_type]:
            addition = 0
        else:
            addition = 0.000001

        if order_type == "bid":
            price = highest_bid_price + addition
            amount = int(buy_amount / price)

            create_order = market.create_limit_buy_order
        else:
            price = lowest_ask_price - addition
            amount = sell_amount

            create_order = market.create_limit_sell_order

        if is_above_min_size(pair, amount):
            logging.info("Placing {} order with amount {}".format(order_type, amount))

            order_id = create_order(pair, amount, price)['info']
            cur_orders[order_type].add_order(order_id)  # initialization
logging.info('Starting Bot ...')

lykke = Market(ccxt.lykke({'apiKey': API_KEY}))

placed_orders = init_placed_orders(lykke)

opened_ref_markets = {market_name: Market(getattr(ccxt, market_name)())
                      for market_name in USED_REF_MARKETS}  # type: Dict[str, Market]
cached_ref_books = {market_name: CachedObject() for market_name in USED_REF_MARKETS}  # type: Dict[str, CachedObject]

fail_wait_infos = {pair: WaitInfo(INIT_FAIL_WAIT_TIME) for pair in PAIRS}  # type: Dict[str, WaitInfo]

while True:
    logging.info('Fetching free balance ...')
    balance = lykke.fetch_balance()

    coins_spend_amount = {}  # type: Dict[str, float]
    for coin, coin_id in COIN_IDS.items():
        if coin_id not in balance:
            coins_spend_amount[coin] = 0
            logging.info('Order size for {0}: {1}'.format(coin, coins_spend_amount[coin]))
            continue

        occur_cnt = sum([1 for pair in PAIRS if coin in pair])

        remaining_balance = balance[coin_id]["total"] * BALANCE_REMAIN_PART
        coin_balance = balance[coin_id]["free"] - remaining_balance
        logging.info('+{0} : {1}'.format(coin, coin_balance))

        coins_spend_amount[coin] = coin_balance / occur_cnt
        logging.info('Order size for {0}: {1}'.format(coin, coins_spend_amount[coin]))

    for pair in PAIRS:
        fail_wait_info = fail_wait_infos[pair]
        if not fail_wait_info.is_done_waiting():
            continue

        coins = pair.split("/")
        coin1_spend_amount, coin2_spend_amount = coins_spend_amount[coins[0]], coins_spend_amount[coins[1]]

        try:
            # first amount is what you spend to sell, second - what you spend to buy
            place_orders(lykke, placed_orders, coin2_spend_amount, coin1_spend_amount, pair)
        except RequestTimeout:
            logging.warning('while processing pair {}, RequestTimeout error occurred'.format(pair))

            fail_wait_info.start_waiting(randint(0, 2 * MINUTE))

            # if next error will occur, then wait time will increase by INC_WAIT_TIME
            fail_wait_info.init_wait_time += INC_WAIT_TIME
        else:
            # placed orders successfully, restore initial wait time
            fail_wait_info.init_wait_time = INIT_FAIL_WAIT_TIME

    logging.info('going to sleep for: {}\n'.format(PERIOD))
    sleep(PERIOD)
