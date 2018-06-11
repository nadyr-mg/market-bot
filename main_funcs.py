from ccxt.base.errors import RequestTimeout

from common import *


def get_spend_amounts(market: Market

) -> Dict[str, float]:
info('Fetching free balance ...')
balance = market.fetch_balance()

coins_spend_amount = {}  # type: Dict[str, float]
for coin, coin_id in COIN_IDS.items():
    if coin_id not in balance:
        coins_spend_amount[coin] = 0
        info('Order size for {0}: {1}'.format(coin, coins_spend_amount[coin]))
        continue

    occur_cnt = max(1, sum([1 for pair in PAIRS if coin in pair]))  ## is this right ? Otherwise we get devision by zero

    remaining_balance = balance[coin_id]["total"] * BALANCE_REMAIN_PART
    coin_balance = balance[coin_id]["free"] - remaining_balance
    info('{} Balance: {:.8f}'.format(coin, coin_balance))

    coins_spend_amount[coin] = coin_balance / occur_cnt
    info('Order size for {}: {:.8f}'.format(coin, coins_spend_amount[coin]))

return coins_spend_amount


def iterate_pairs(placing_objects: ObjectsForPlacing, fail_wait_infos

: Dict[str, WaitInfo],
  coins_spend_amount: Dict[str, float]):
for pair in PAIRS:
    fail_wait_info = fail_wait_infos[pair]
    if not fail_wait_info.is_done_waiting():
        continue

    coins = pair.split("/")
    coin1_spend_amount, coin2_spend_amount = coins_spend_amount[coins[0]], coins_spend_amount[coins[1]]

    try:
        # first amount is what you spend to sell, second - what you spend to buy
        place_orders(placing_objects, coin2_spend_amount, coin1_spend_amount, pair)
    except RequestTimeout:
        logging.warning('while processing pair {}, RequestTimeout error occurred'.format(pair))

        fail_wait_info.start_waiting(randint(0, 2 * MINUTE))

        # if next error will occur, then wait time will increase by INC_WAIT_TIME
        fail_wait_info.init_wait_time += INC_WAIT_TIME
    else:
        # placed orders successfully, restore initial wait time
        fail_wait_info.init_wait_time = INIT_FAIL_WAIT_TIME

    info('')  # print line break for better readability


def place_orders(placing_objects: ObjectsForPlacing, buy_amount

: float, sell_amount: float, pair: str) -> None:
info("Entering place_orders function...")
market, placed_orders, opened_ref_markets, cached_ref_books = placing_objects.unpack_objects()

ref_book = get_ref_book(pair, opened_ref_markets, cached_ref_books)

highest_bid_price, lowest_ask_price = get_best_prices(market, ref_book, pair)
info("Current best bid at: {:.8f}".format(highest_bid_price))
info("Current best ask at: {:.8f}".format(lowest_ask_price))

orders_relevancy = get_orders_relevancy(ref_book, highest_bid_price, lowest_ask_price, pair)
info('Checking whether bid and ask are better then ref market: {}'.format(orders_relevancy))

cur_orders = placed_orders[pair]  # type: Dict[str, Orders]

is_some_order_cancelled = handle_placed_orders(market, cur_orders, orders_relevancy, highest_bid_price,
                                               lowest_ask_price)
if is_some_order_cancelled:
    # better get back to a main loop and recalculate balance
    return

for order_type in ("bid", "ask"):
    if not orders_relevancy[order_type] or not cur_orders[order_type].is_placing_available():
        continue

    if cur_orders[order_type].is_empty():
        coins = pair.split("/")
        base = coins[0]
        quote = coins[1]
        currencies = ['USD', 'EUR', 'CHF', 'JPY', 'GBP']
        if (quote == 'ETH' or quote == 'BTC'):
            addition = 0.000001
        if any(quote in currency for currency in currencies):
            addition = 0.00001
            info('------------------  0.00001 addition')
    else:  # we don't want to place an order that will be above our other orders
        addition = 0

    if order_type == "bid":
        price = highest_bid_price + addition
        amount = int(buy_amount / price)

        create_order = market.create_limit_buy_order
    else:
        price = lowest_ask_price - addition
        amount = sell_amount

        create_order = market.create_limit_sell_order

    if is_above_min_size(pair, amount):
        info("Placing {} order, price: {}, amount: {}".format(order_type, price, amount))

        order_id = create_order(pair, amount, price)['info']
        cur_orders[order_type].add(order_id)


def handle_placed_orders(market: Market, cur_orders

: Dict[str, Orders], orders_relevancy: Dict[str, bool],
                                       highest_bid_price: float, lowest_ask_price: float) -> bool:
is_some_order_cancelled = False  # is some order was cancelled during handling
if not cur_orders["bid"].is_empty() or not cur_orders["ask"].is_empty():
    info("Found placed orders on trading market")

    for order_type in cur_orders:
        for order_idx, order in reverse_enum(cur_orders[order_type].orders):
            order_info = market.fetch_order(order.id)

            status = order_info["status"]
            best_price = highest_bid_price if order_type == "bid" else lowest_ask_price
            info("checking current {} status '{}': {}".format(order_type, status, order.id))
            if status == "open":
                relevant_value = order.is_relevant(order_info["price"], best_price)
                if not orders_relevancy[order_type] or not relevant_value:
                    info("Order is opened and irrelevant. Cancellation...")

                    # All opened orders have the same price, hence if one is irrelevant -> all are irrelevant
                    order.cancel(market)
                    cur_orders[order_type].set_wait_time()

                    is_some_order_cancelled = True
            else:
                info("Order is already closed. Deleting from dict 'placed_orders'...")
                cur_orders[order_type].pop(order_idx)

                if status == "closed":
                    opposite_type = "ask" if order_type == "bid" else "bid"
                    if order_idx < len(cur_orders[opposite_type].orders):
                        opposite_order = cur_orders[opposite_type].get(order_idx)
                        opposite_order_info = market.fetch_order(opposite_order.id)

                        # bringing to a proper order
                        if order_type == "ask":
                            order_info, opposite_order_info = opposite_order_info, order_info

                        info("Defining round for 'bid': {}, 'ask': {}".format(order_info["id"],
                                                                              opposite_order_info["id"]))
                        if is_round_successful(order_info, opposite_order_info,
                                               highest_bid_price, lowest_ask_price):
                            info("Round ended successfully")
                        else:
                            info("Round ended unsuccessfully")

return is_some_order_cancelled
