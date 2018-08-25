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


def update_spend_amounts(coins_spend_amount, coins_balances, last_coins_balances):
    for pair in PAIRS:
        coins = pair.split('/')
        for coin in coins:
            threshold = last_coins_balances[coin]['total'] * AMOUNT_THRESHOLD
            freed_amount = last_coins_balances[coin]['total'] * FREED_AMOUNT_PERCENTAGE
            if abs(last_coins_balances[coin]['total'] - coins_balances[coin]['total']) >= threshold or \
                            coins_balances[coin]['free'] >= freed_amount:
                restricted_ratio = 1 - USED_BALANCE_PAIRS[pair][coin]
                total_amount = coins_balances[coin]['total']

                allowed_to_spend = coins_balances[coin]['free'] - restricted_ratio * total_amount
                coins_spend_amount[pair][coin] = min(0, allowed_to_spend)

                last_coins_balances[coin]['total'] = total_amount

            order_size = coins_spend_amount[pair].get(coin, 0)
            info('pair: {}, coin: {}, order size: {:.8f}'.format(pair, coin, order_size))


def iterate_pairs(placing_objects: ObjectsForPlacing, fail_wait_infos

: Dict[str, WaitInfo],
  coins_spend_amount: Dict[str, Dict[str, float]]):
for pair in PAIRS:
    fail_wait_info = fail_wait_infos[pair]
    if not fail_wait_info.is_done_waiting():
        continue

    try:
        place_orders(placing_objects, coins_spend_amount[pair], pair)
    except RequestTimeout:
        logging.warning('while processing pair {}, RequestTimeout error occurred'.format(pair))

        fail_wait_info.start_waiting(randint(0, 2 * MINUTE))

        # if next error will occur, then wait time will increase by INC_WAIT_TIME
        fail_wait_info.init_wait_time += INC_WAIT_TIME
    else:
        # placed orders successfully, restore initial wait time
        fail_wait_info.init_wait_time = INIT_FAIL_WAIT_TIME

    info('')  # print line break for better readability


def place_orders(placing_objects: ObjectsForPlacing, coins_spend_amount, pair

: str) -> None:
info("Entering place_orders function...")
market, placed_orders, opened_ref_markets, cached_ref_books, all_tracked_prices = placing_objects.unpack_objects()
tracked_prices = all_tracked_prices[pair]

ref_book = get_ref_book(pair, opened_ref_markets, cached_ref_books)
main_book = market.fetch_order_book(pair)

highest_bid_price, lowest_ask_price = get_best_prices(main_book, ref_book, pair)
info("Current best bid at: {:.8f}".format(highest_bid_price))
info("Current best ask at: {:.8f}".format(lowest_ask_price))

if highest_bid_price is None or lowest_ask_price is None:
    info("No orders in main order book and order book for reference market is missing, will try next iteration")
    return

is_orders_at_best = is_last_order_at_best(main_book, ref_book, pair)
info("Is current orders at best: {}".format(is_orders_at_best))

orders_relevancy = get_orders_relevancy(ref_book, highest_bid_price, lowest_ask_price, pair)
info('Checking whether bid and ask are better then ref market: {}'.format(orders_relevancy))

cur_orders = placed_orders[pair]  # type: Dict[str, Orders]

is_some_order_cancelled = handle_placed_orders(market, cur_orders, orders_relevancy, is_orders_at_best,
                                               tracked_prices, main_book, highest_bid_price, lowest_ask_price)
if is_some_order_cancelled:
    # better get back to a main loop and recalculate balance
    return

remove_empty_prices(tracked_prices)

coins = pair.split("/")
# first amount is what you spend to sell, second - what you spend to buy
sell_amount, buy_amount = coins_spend_amount[coins[0]], coins_spend_amount[coins[1]]
for order_type in ("bid", "ask"):
    if (orders_relevancy is not None and not orders_relevancy[order_type]) or \
            not cur_orders[order_type].is_placing_available():
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

    amount = get_adjusted_amount(tracked_prices, order_type, amount, price)
    if is_above_min_size(pair, amount):
        info("Placing {} order, price: {}, amount: {}".format(order_type, price, amount))
        orders_logger.info("Placing {} order, price: {}, amount: {}".format(order_type, price, amount))

        order_id = create_order(pair, amount, price)['info']
            cur_orders[order_type].add(order_id)

            # keeping track of to-be-bought/to-be-sold amount
        tracked_prices[order_type][order_id] = TrackedPrice(price)

            if order_type == "bid":
                coins_spend_amount[coins[1]] -= amount * price
            else:
                coins_spend_amount[coins[0]] -= amount


def handle_placed_orders(market: Market, cur_orders

: Dict[str, Orders], orders_relevancy: Dict[str, bool],
                                       is_orders_at_best: Dict[str, bool], tracked_prices, order_book,
                                                          highest_bid_price: float, lowest_ask_price: float) -> bool:
is_some_order_cancelled = False  # is some order was cancelled during handling
if not cur_orders["bid"].is_empty() or not cur_orders["ask"].is_empty():
    info("Found placed orders on trading market")

    for order_type in cur_orders:
        for order_idx, order in reverse_enum(cur_orders[order_type].orders):
            order_info = market.fetch_order(order.id)

            if order_info['info']['Status'] == 'Matched' or order_info['info']['Status'] == 'Processing':
                info('logging order to a file')
                log_filled_order(order_info)

                amount, filled = abs(order_info['amount']), abs(order_info['filled'])
                if order.id in tracked_prices[order_type]:
                    # filled parameter has updated for an order -> updating it in tracked_prices

                    is_last_update = amount == filled
                    new_filled_amount = filled - order.filled
                    info('Updating traked_price: {}; new filled: {}, last_update: {}'.format(order.id,
                                                                                             new_filled_amount,
                                                                                             is_last_update))

                    tracked_price = tracked_prices[order_type][order.id]
                    tracked_price.filled += new_filled_amount
                    tracked_price.is_last_update = is_last_update or tracked_price.is_last_update

                order.filled = filled

            status = order_info["status"]
            best_price = highest_bid_price if order_type == "bid" else lowest_ask_price
            info("checking current {} status '{}': {}".format(order_type, status, order.id))
            if status == "open":
                relevant_value = order.is_relevant(order_info["price"], best_price, order_book)
                if NO_CANCEL in BOT_TYPE:
                    # this condition is redundant if this feature is on
                    is_orders_at_best[order_type] = True

                if (not orders_relevancy[order_type]) or \
                        not is_orders_at_best[order_type] or not relevant_value:
                    if orders_relevancy is not None:
                        info("orders_relevancy[order_type] : {}".format(orders_relevancy[order_type]))

                        info("relevant_value: {}".format(relevant_value))
                        info("is_orders_at_best[order_type] : {}".format(is_orders_at_best[order_type]))
                        info("Order is opened and irrelevant. Cancellation...")

                    cancel_reasons = 'Prices deviate from ref market much?: {}\n' \
                        .format(orders_relevancy is not None and not orders_relevancy[order_type])
                    cancel_reasons += 'Difference between two last orders prices is too big?: {}\n' \
                        .format(not is_orders_at_best[order_type])
                    cancel_reasons += 'Order price is not better or equal to best_price?: {}\n' \
                        .format(not relevant_value)

                    orders_logger.info('canceled {} order; Reasons:\n{}'.format(order_type, cancel_reasons))

                        # All opened orders have the same price, hence if one is irrelevant -> all are irrelevant
                        order.cancel(market)
                    if NO_CANCEL not in BOT_TYPE:
                        # not keeping orders cancelled if this feature is on
                        cur_orders[order_type].set_wait_time()

                        is_some_order_cancelled = True
            else:
                info("Order is already closed. Deleting from dict 'placed_orders'...")
                cur_orders[order_type].pop(order_idx)

                # canceled order -> the last update for tracked_price
                if order.id in tracked_prices[order_type]:
                    tracked_price = tracked_prices[order_type][order.id]
                    tracked_price.is_last_update = True

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

return is_some_order_cancelled  # return adjusted amount - amount that is consistent with tracked prices
def get_adjusted_amount(tracked_prices, order_type, amount, price):
    opposite_order_type = "ask" if order_type == "bid" else "bid"
    for tracked_price in tracked_prices[opposite_order_type].values():
        track_amount, track_price = tracked_price.filled, tracked_price.price

        if not (order_type == 'bid' and price <= track_price or
                            order_type == 'ask' and price >= track_price):
            info('Found inconsistent price: {}; subtracting {} - {} = {}'.format(track_price, amount, track_amount,
                                                                                 amount - track_amount))
            amount -= track_amount

    return amount


def remove_empty_prices(tracked_prices):
    order_type = 'bid'
    opposite_order_type = 'ask'

    for key, tracked_price in list(tracked_prices[order_type].items()):
        amount, price = tracked_price.filled, tracked_price.price
        for opp_key, opp_tracked_price in list(tracked_prices[opposite_order_type].items()):
            opp_amount, opp_price = opp_tracked_price.filled, opp_tracked_price.price

            if order_type == 'bid' and price <= opp_price or \
                                    order_type == 'ask' and price >= opp_price:

                min_amount = min(amount, opp_amount)
                opp_tracked_price.filled -= min_amount
                amount -= min_amount

                info(
                    'Found opposite orders: \n{} - {}:\n amount: {}, price: {} \n {} - {}:\n amount: {}, price: {}'.format(
                        order_type, key,
                        amount, price,
                        opposite_order_type, opp_key,
                        opp_amount, opp_price
                    ))

                if opp_tracked_price.is_last_update and opp_tracked_price.filled == 0:
                    del tracked_prices[opposite_order_type][opp_key]

        if tracked_price.is_last_update and amount == 0:
            del tracked_prices[order_type][key]
        else:
            tracked_price.filled = amount
