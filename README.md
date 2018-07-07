# market_bot



Already implemented:
- Buy order is set above current best buy order.
- Sell order is set below current best sell order.

Todo:
I) If there is no current buy/sell order -> Checkout the best buy/sell price on other exchange
-> The exchange we will have to check is depending on the coin we are trading. For example. for WAX you check the exchange bittrex. For the coin LOC you check hitbtc. For the coin MWAT you check kucoin.
--> We will have a mapping for the every coin and its exchange. +




II)Order is relevant:
- 1) If our buy/sell are best buy/sell orders on the orderbook --> This is already implemented
- 2) And if our buy/sell is better than current reference market with at least 5% --> Todo



Mapping for Coins/Ref.Markets:
AE/ETH    --> IDAX, or Binance if first not in ccxt api
AE/BTC    --> Binance
AGI/ETH   --> kucoin
AGI/BTC   --> kucoin
APPC/ETH  --> Binance
APPC/BTC  --> Binance
BNT/ETH   --> Bancor Network, or Binance
BNT/BTC   --> Binance
CAN/ETH   --> kucoin
CAN/BTC   --> kucoin
EVX/ETH   --> Binance
EVX/BTC   --> Binance
GNT/ETH   --> Bittrex
GNT/BTC   --> Bittrex
HCP       --> No ref market
HGT/ETH   --> COSS
HGT/BTC   --> COSS
HMQ/ETH   --> Bittrex
HMQ/BTC   --> Bittrex
KEY/ETH   --> Kucoin
KEY/BTC   --> Kucoin
LC        --> No ref market
LRC/ETH   --> IDAX, or Binance
LRC/BTC   --> Binance
LTC/ETH   --> Binance
LTC/BTC   --> Binance
MCO/ETH   --> Binance
MCO/BTC   --> Binance
OMG/ETH   --> Binance
OMG/BTC   --> Binance
PKT/ETH   --> hitbtc
PKT/BTC   --> hitbtc
POW/ETH   --> Binance
POW/BTC   --> Binance
PPT/ETH   --> Binance
REP/ETH   --> Bittex
REP/BTC   --> Bittex
SLR/BTC   --> Bittrex Note: only BTC no SLR/ETH
SNM/ETH   --> Binance
SNM/BTC   --> Binance
ZRX/ETH   --> Binance
ZRX/BTC   --> Binance




III)Mapping for smallest trade amount:
We cannot trade a volume that is smaller than the min order size.
Todo:
- Before we put an order we have to check if the order volume is bigger than the min order size.

Here is a list of the min order sizes for every coin:
Minimal order size:
Asset
Min order size
AE	0.4
AGI	0.5
APPC	1
AUD	1
BNT	0.2
BTC	0.0001
CAD	1
CAN	1.5
CHF	1
CZK	25
DKK	6
ETH	0.001
EUR	1
EVX	0.5
GBP	1
GNT	3
HCP	1
HGT	10
HKD	8
HMQ	4
HUF	250
KEY	50
ILS	3
JPY	100
LC	5
LKK	4
LKK1Y	4
LKK2Y	4
LRC	1.5
LTC	0.01
MCO	0.1
MXN 20
NOK 7
NZD 1
OMG	0.1
PKT	1
POW	1
PPT	0.04
PLN 3
REP
0.03
RUB	50
SEK	7
SGD	1
SLR	2
SNM	7
TIME	0.04
TRY	3
USD	1
XAG	0.04
XAU	0.002
XPD	0.002
XPT	0.002
ZAR	10
ZRX	1
