import asyncio
import logging
import time
import traceback
from datetime import datetime, timezone
import pandas as pd
import requests
from api import upbit, binance
from api.checkOrderbook import get_common_orderbook_ticker

"""
Docs: https://apidocs.bithumb.com/reference
"""

async def check_15_rsi(exchange_data, duplicates):
    for ticker in duplicates:
        if ticker not in exchange_data['upbit_15_rsi']:
            exchange_data['upbit_15_rsi'][ticker] = 0

        if ticker not in exchange_data['binance_15_rsi']:
             exchange_data['binance_15_rsi'][ticker] = 0

        await asyncio.gather(
            check_upbit_rsi(exchange_data, ticker, 15),
            check_binance_rsi(exchange_data, ticker, 15)
        )


async def check_240_rsi(exchange_data, duplicates):
    for ticker in duplicates:
        if ticker not in exchange_data['upbit_240_rsi']:
             exchange_data['upbit_240_rsi'][ticker] = 0

        if ticker not in exchange_data['binance_240_rsi']:
             exchange_data['binance_240_rsi'][ticker] = 0

        await asyncio.gather(
            check_upbit_rsi(exchange_data, ticker, 240),
            check_binance_rsi(exchange_data, ticker, 240)
        )

async def check_upbit_rsi(exchange_data, ticker, interval):
    sum_rsi = 0
    count = 1

    try:
        for i in range(count):
            url = 'https://api.upbit.com/v1/candles/minutes/' + str(interval)
            market = "KRW-"+ticker
            queryString = {"market": market, "count": "200"}

            data = requests.get(url, params=queryString).json()
            df = pd.DataFrame(data)

            df = df.reindex(index=df.index[::-1]).reset_index()

            last_rsi = rsi(df, 12).iloc[-1]
            sum_rsi += last_rsi

        u_rsi = 'upbit_' + str(interval) + '_rsi'
        exchange_data[u_rsi][ticker] = round(sum_rsi / count, 2)
    except Exception as e:
        logging.info(traceback.format_exc())

    # print(f"평균 UPBIT RSI : {exchange_data[ticker]['upbit_rsi']}")

async def check_binance_rsi(exchange_data, ticker, interval):
    sum_rsi = 0
    count = 1
    interval_param = 0

    if interval == 15:
        interval_param = '15m'
    elif interval == 240:
        interval_param = '4h'

    try:
        for i in range(count):
            url = 'https://fapi.binance.com/fapi/v1/klines'
            symbol = ticker+"USDT"
            queryString = {"symbol": symbol, "interval": interval_param, "limit": "200"}

            data = requests.get(url, params=queryString).json()
            json_data = []

            for entry in data:
                timestamp_seconds = entry[0] / 1000.0
                utc_time = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)

                json_entry = {
                    "timestamp": utc_time.isoformat(),
                    "trade_price": float(entry[4])
                }
                json_data.append(json_entry)

            df = pd.DataFrame(json_data)

            last_rsi = rsi(df, 12).iloc[-1]
            sum_rsi += last_rsi

        b_rsi = 'binance_' + str(interval) + '_rsi'
        exchange_data[b_rsi][ticker] = round(sum_rsi / count, 2)
    except Exception as e:
        logging.info(traceback.format_exc())

    #print(f"평균 BINANCE RSI : {exchange_data[ticker]['binance_rsi']}")

def rsi(ohlc: pd.DataFrame, period: int = 14):
    #OHLC : O(시가), H(고가), L(저가), C(종가) or trade_price

    ohlc["trade_price"] = ohlc["trade_price"]
    delta = ohlc["trade_price"].diff()

    gains, declines = delta.copy(), delta.copy()
    gains[gains < 0] = 0
    declines[declines > 0] = 0

    au = gains.ewm(com=period - 1, min_periods=period).mean()
    ad = declines.abs().ewm(com=period - 1, min_periods=period).mean()
    RS = au / ad

    return round(pd.Series(100 - (100 / (1 + RS)), name="RSI"), 2)

# 중복 티커 헬퍼는 checkOrderbook.get_common_orderbook_ticker()를 단일 원천으로 사용한다.
# Backwards-compat alias so legacy callers keep working after TD-11 consolidation.
get_duplicate_ticker = get_common_orderbook_ticker

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    exchange_data = {}
    exchange_data['upbit_15_rsi'] = {}
    exchange_data['binance_15_rsi'] = {}
    exchange_data['upbit_240_rsi'] = {}
    exchange_data['binance_240_rsi'] = {}

    duplicates = get_common_orderbook_ticker()
    logging.info(duplicates)
    while True:
        try:
            asyncio.run(check_240_rsi(exchange_data, duplicates))
            #asyncio.gather(check_15_rsi(exchange_data, 15, duplicates))

            logging.info("")
            time.sleep(10)
        except Exception as e:
            logging.info(traceback.format_exc())



