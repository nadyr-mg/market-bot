from ccxt.base.errors import RequestTimeout

from common import *


def get_coins_balances(market: Market

) -> Dict[str, Dict]:
info('Fetching free balance ...')
balance = market.fetch_balance()

coins_balances = {}  # type: Dict[str, Dict]
for coin, coin_id in COIN_IDS.items():
    if coin_id not in balance:
        coins_balances[coin] = 0
        logging.warning('Can\'t find coin_id "{}" in balance'.format(coin_id))
        continue

    info('{}: Total balance: {:.8f}'.format(coin, balance[coin_id]["total"]))
    info('{}: Free balance: {:.8f}'.format(coin, balance[coin_id]["free"]))
    coins_balances[coin] = {
        'total': balance[coin_id]["total"],
        'free': balance[coin_id]["free"],
    }

return coins_balances


def get_spend_amounts(last_coins_spend_amount: Dict[str, Dict],
                                               coins_balances

: Dict[str, Dict[str, float]],
  last_coins_balances: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
coins_spend_amount = {}  # type: Dict[str, Dict[str, float]]
for pair in PAIRS:
    if pair not in coins_spend_amount:
        coins_spend_amount[pair] = {}

    coins = pair.split('/')
    for coin in coins:
        threshold = last_coins_balances[coin]['total'] * AMOUNT_THRESHOLD
        if abs(last_coins_balances[coin]['total'] - coins_balances[coin]['total']) >= threshold:
            coins_spend_amount[pair][coin] = coins_balances[coin]['free'] * USED_BALANCE_PAIRS[pair][coin]
        else:
            coins_spend_amount[pair][coin] = last_coins_spend_amount[pair][coin]

        info('pair: {}, coin: {}, order size: {:.8f}'.format(pair, coin, coins_spend_amount[pair][coin]))

return coins_spend_amount


def iterate_pairs(placing_objects: ObjectsForPlacing, fail_wait_infos

: Dict[str, WaitInfo],
  coins_spend_amount: Dict[str, Dict[str, float]]):
for pair in PAIRS:
    fail_wait_info = fail_wait_infos[pair]
    if not fail_wait_info.is_done_waiting():
        continue

    coins = pair.split("/")
    coin1_amount, coin2_amount = coins_spend_amount[pair][coins[0]], coins_spend_amount[pair][coins[1]]

    try:
        # first amount is what you spend to sell, second - what you spend to buy
        place_orders(placing_objects, coin2_amount, coin1_amount, pair)
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
main_book = market.fetch_order_book(pair)

highest_bid_price, lowest_ask_price = get_best_prices(main_book, ref_book, pair)
info("Current best bid at: {:.8f}".format(highest_bid_price))
info("Current best ask at: {:.8f}".format(lowest_ask_price))

is_orders_at_best = is_last_order_at_best(main_book, ref_book, pair)
info("Is current orders at best: {}".format(is_orders_at_best))

orders_relevancy = get_orders_relevancy(ref_book, highest_bid_price, lowest_ask_price, pair)
info('Checking whether bid and ask are better then ref market: {}'.format(orders_relevancy))

cur_orders = placed_orders[pair]  # type: Dict[str, Orders]

is_some_order_cancelled = handle_placed_orders(market, cur_orders, orders_relevancy, is_orders_at_best,
                                               highest_bid_price, lowest_ask_price)
if is_some_order_cancelled:
    # better get back to a main loop and recalculate balance
    return

for order_type in ("bid", "ask"):
    if not orders_relevancy[order_type] or not cur_orders[order_type].is_placing_available():
        continue

    if cur_orders[order_type].is_empty():
        addition = get_lowest_price_diff(pair)

        info('------------------  {} addition'.format(addition))
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
                                       is_orders_at_best: Dict[
                                                              str, bool], highest_bid_price: float, lowest_ask_price: float) -> bool:
is_some_order_cancelled = False  # is some order was cancelled during handling
if not cur_orders["bid"].is_empty() or not cur_orders["ask"].is_empty():
    info("Found placed orders on trading market")

    for order_type in cur_orders:
        for order_idx, order in reverse_enum(cur_orders[order_type].orders):
            order_info = market.fetch_order(order.id)

            if order_info['info']['Status'] == 'Matched' or order_info['info']['Status'] == 'Processing':
                info('logging order to a file')
                log_filled_order(order_info)

            status = order_info["status"]
            best_price = highest_bid_price if order_type == "bid" else lowest_ask_price
            info("checking current {} status '{}': {}".format(order_type, status, order.id))
            if status == "open":
                relevant_value = order.is_relevant(order_info["price"], best_price)
                if not orders_relevancy[order_type] or not is_orders_at_best[order_type] or not relevant_value:
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
