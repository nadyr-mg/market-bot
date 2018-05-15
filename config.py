import logging
from json import load
from typing import Dict
from os.path import join

from configuration_files import config_dir


API_KEY = "1c15115b-b5b6-4920-9629-4c444e346613"
PAIRS = ['WAX/ETH']
# PAIRS = ['LOC/ETH', 'WAX/ETH', 'CVC/ETH']
MIN_SPREAD = 10
PERIOD = 15
BALANCE_REMAIN_PART = 0.7

ACCEPTABLE_PROFIT_DEVIATION = 0.05

MINUTE = 60

INIT_FAIL_WAIT_TIME = 3 * MINUTE
INC_WAIT_TIME = 2 * MINUTE

REF_BOOK_RELEVANCE_TIME = 5 * MINUTE

AFTER_CANCEL_WAIT_BOUNDS = (3 * MINUTE, 7 * MINUTE)


COIN_IDS = {
    "ETH": "ETH",
    "WAX": "6e25e8ab-5779-4543-855b-71f4857b47d5",
    # "LOC": "572475a4-8fef-4e39-909e-85f6bbbc10c4",
    # "WTC": "168f13bf-bfea-4931-91ff-e449850d694e",
    # "PPT": "98385941-89b3-45c2-ae8e-b64c6f3bbac9",
    # "CVC": "f9fb5970-2fc4-4b08-900b-870f245e430b",
}

with open(join(config_dir, "reference_markets.json")) as file:
    REF_MARKETS = load(file)  # type: Dict

USED_REF_MARKETS = {market for market in REF_MARKETS.values() if market}

with open(join(config_dir, "min_amounts.json")) as file:
    MIN_AMOUNTS = load(file)  # type: Dict

with open(join(config_dir, "ref_deviations.json")) as file:
    REF_PRICE_DEVIATIONS = load(file)  # type: Dict

# setup default logging level
logging.basicConfig(level=logging.INFO)
