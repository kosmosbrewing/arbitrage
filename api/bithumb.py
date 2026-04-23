import requests

from consts import BITHUMB, EXCHANGE_LIST, ORDERBOOK_SIZE

"""
Docs: https://apidocs.bithumb.com/reference
"""


def get_usdt_price(orderbook_info):
    """Fetch USDT/KRW orderbook from Bithumb and merge into shared orderbook_info."""
    exchange = BITHUMB

    data = requests.get("https://api.bithumb.com/public/orderbook/USDT_KRW").json()

    ticker = data["data"]["order_currency"]
    bid_len = len(data["data"]["bids"])
    ask_len = len(data["data"]["asks"])

    if ticker not in orderbook_info:
        orderbook_info[ticker] = {}
        for exchange_list in EXCHANGE_LIST:
            orderbook_info[ticker][exchange_list] = {"orderbook_units": []}
            for _ in range(ORDERBOOK_SIZE):
                orderbook_info[ticker][exchange_list]["orderbook_units"].append(
                    {"ask_price": 0, "bid_price": 0, "ask_size": 0, "bid_size": 0}
                )

    ask_count = min(ask_len, ORDERBOOK_SIZE)
    for i in range(ask_count):
        orderbook_info[ticker][exchange]["orderbook_units"][i]["ask_price"] = float(
            data["data"]["asks"][i]["price"]
        )
        orderbook_info[ticker][exchange]["orderbook_units"][i]["ask_size"] = data[
            "data"
        ]["asks"][i]["quantity"]

    bid_count = min(bid_len, ORDERBOOK_SIZE)
    for i in range(bid_count):
        orderbook_info[ticker][exchange]["orderbook_units"][i]["bid_price"] = float(
            data["data"]["bids"][i]["price"]
        )
        orderbook_info[ticker][exchange]["orderbook_units"][i]["bid_size"] = data[
            "data"
        ]["bids"][i]["quantity"]
