from logging import error

import ccxt

from main_funcs import *

# initialization
logging.info('Starting Bot ...')

is_passed = check_conf_files()
if not is_passed:
    logging.error("found inconsistencies in configuration files")
    exit(1)

lykke = Market(ccxt.lykke({'apiKey': API_KEY}))

placed_orders = init_placed_orders(lykke)

opened_ref_markets = {market_name: Market(getattr(ccxt, market_name)())
                      for market_name in USED_REF_MARKETS}  # type: Dict[str, Market]
cached_ref_books = {market_name: CachedObject() for market_name in USED_REF_MARKETS}  # type: Dict[str, CachedObject]

fail_wait_infos = {pair: WaitInfo(INIT_FAIL_WAIT_TIME) for pair in PAIRS}  # type: Dict[str, WaitInfo]

placing_objects = ObjectsForPlacing(lykke, placed_orders, opened_ref_markets, cached_ref_books)

while True:
    try:
        coins_spend_amount = get_spend_amounts(placing_objects.market)
        info('')  # print line break for better readability
        iterate_pairs(placing_objects, fail_wait_infos, coins_spend_amount)
    except Exception as err:
        if isinstance(err, KeyboardInterrupt):
            raise
        else:
            error('unexpected error occurred: {}'.format(str(err)))

    logging.info('going to sleep for: {} seconds\n'.format(PERIOD))
    sleep(PERIOD)
