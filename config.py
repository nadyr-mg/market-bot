import logging
from json import load
from typing import Dict

API_KEY = "1c15115b-b5b6-4920-9629-4c444e346613"
PAIRS = ['WAX/ETH']
# PAIRS = ['LOC/ETH', 'WAX/ETH', 'CVC/ETH']
MIN_SPREAD = 10
PERIOD = 15
BALANCE_USED_PART = 0.5

REF_PRICE_DEVIATION = 0.05

COIN_IDS = {
    "ETH": "ETH",
    # "LOC": "572475a4-8fef-4e39-909e-85f6bbbc10c4",
    "WAX": "6e25e8ab-5779-4543-855b-71f4857b47d5",
    # "CVC": "f9fb5970-2fc4-4b08-900b-870f245e430b",
}

with open("reference_markets.json") as file:
    REF_MARKETS = load(file)  # type: Dict

USED_REF_MARKETS = {market for market in REF_MARKETS.values() if market}

with open("min_amounts.json") as file:
    MIN_AMOUNTS = load(file)  # type: Dict

# setup default logging level
logging.basicConfig(level=logging.INFO)
