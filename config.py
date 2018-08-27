import logging
from json import load
from typing import Dict
from os.path import join

from configuration_files import config_dir

API_KEY = "1c15115b-b5b6-4920-9629-4c444e346613"

## for this pair "LKK1Y/LKK" LKK is used not LYKKE
PAIRS = ['ZEC/USD', "ZRX/ETH", "ZRX/BTC"]
# PAIRS = ['LOC/ETH', 'WAX/ETH', 'CVC/ETH']
COIN_IDS = {
    "ETH": "ETH",
    "BTC": "BTC",
    "USD": "USD",
    "EUR": "EUR",
    "WAX": "6e25e8ab-5779-4543-855b-71f4857b47d5",
    # "LOC": "572475a4-8fef-4e39-909e-85f6bbbc10c4",
    # "WTC": "168f13bf-bfea-4931-91ff-e449850d694e",
    # "PPT": "98385941-89b3-45c2-ae8e-b64c6f3bbac9",
    # "CVC": "f9fb5970-2fc4-4b08-900b-870f245e430b",
    "LYKKE": "LKK",
    "LKK": "LKK",
    "LKK1Y": "LKK1Y",
    "ZEC": "b2c591a2-6c2d-4130-89cd-71813481bb76",
    "ZRX": "14cc3c2d-9b96-4e78-8674-b6dc60dd1d99",

}
MIN_SPREAD = 5
PERIOD = 15

NO_CANCEL = 2
NO_CANCEL_ORDERS_LIMIT = 20

# empty list means default type
BOT_TYPE = []

# This variable defines distribution of coins balances. Don't exceed 100% for coin's balance
# e.g.: for 'WAX/ETH': {'WAX': 1, 'ETH': 0.5}, 'CVC/ETH': {'CVC': 1, 'ETH': 0.6}, got 110% for ETH
USED_BALANCE_PAIRS = {
    'WAX/ETH': {
        'WAX': 1,
        'ETH': 1,
    }
    ,
    'LYKKE/EUR': {
        'LYKKE': 0.5,
        'EUR': 1,
    }
    ,
    'LYKKE/USD': {
        'LYKKE': 0.5,
        'USD': 0.3,
    }
    ,
    'ZEC/USD': {
        'ZEC': 1,
        'USD': 1,
    }
    ,
    'LKK1Y/LKK': {
        'LKK1Y': 1,
        'LKK': 1,
    }
    ,
    'ZRX/BTC': {
        'ZRX': 0.45,
        'BTC': 0.45,
    }
    ,
    'ZRX/ETH': {
        'ZRX': 0.45,
        'ETH': 0.45,
    }
}
AMOUNT_THRESHOLD = 0.03  # Balance should go below/above this threshold to change order sizes for coins
# how much money should be freed to recalculate order sizes
FREED_AMOUNT_PERCENTAGE = 0.2

ACCEPTABLE_PROFIT_DEVIATION = 0.05

# Wait time
MINUTE = 60

INIT_ORDERS_WAIT = 10

INIT_FAIL_WAIT_TIME = 3 * MINUTE
INC_WAIT_TIME = 2 * MINUTE

REF_BOOK_RELEVANCE_TIME = 5 * MINUTE

AFTER_CANCEL_WAIT_BOUNDS = (3 * MINUTE, 7 * MINUTE)

# Json files
with open(join(config_dir, "reference_markets.json")) as file:
    REF_MARKETS = load(file)  # type: Dict

USED_REF_MARKETS = {market for market in REF_MARKETS.values() if market}

with open(join(config_dir, "min_amounts.json")) as file:
    MIN_AMOUNTS = load(file)  # type: Dict

with open(join(config_dir, "ref_deviations.json")) as file:
    REF_PRICE_DEVIATIONS = load(file)  # type: Dict

# Logging
LOG_FILENAME = 'log_files/info.log'

ORDERS_LOG_FILENAME = 'log_files/placed_orders.log'

# save logs to the file if True
# if False, unexpected error will be send by email only with traceback (no logs)
DEBUG = True

# setup default logging level
logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# create console handler and set level to info
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

if DEBUG:
    # create error file handler and set level to error
    handler = logging.FileHandler(LOG_FILENAME, 'w')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

orders_logger = logging.getLogger('placed_orders')
orders_logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

handler = logging.FileHandler(ORDERS_LOG_FILENAME)
handler.setFormatter(formatter)
orders_logger.addHandler(handler)


FILLED_ORDERS_FILE = 'log_files/filled_orders.json'

# Email
# how many lines of logs to send by an email if unexpected error occurs
LINES_TO_SEND = 15

FROM_EMAIL = 'crypto.notification.bot@gmail.com'
LOGIN, PASSW = 'crypto.notification.bot@gmail.com', "g123*"  # credentials for authentication in your gmail account
TO_EMAIL = 'sandro.crypto.test@gmail.com'

