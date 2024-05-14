import asyncio
import json
import logging
import time
import traceback
from datetime import datetime, timezone, timedelta
import aiohttp
import pandas as pd
import requests
from collections import Counter
from api import upbit, binance

"""
Docs: https://apidocs.bithumb.com/reference
"""

async def check_15_rsi(exchange_data, duplicates):
    for ticker in duplicates:
        if ticker not in exchange_data['upbit_15_rsi']:
            exchange_data['upbit_15_rsi'][ticker] = 0

        if ticker not in exchange_data['binance_15_rsi']:
             exchange_data['upbit_15_rsi'][ticker] = 0

        await asyncio.gather(
            check_upbit_rsi(exchange_data, ticker, 15),
            check_binance_rsi(exchange_data, ticker, 15)
        )
async def check_240_rsi(exchange_data, duplicates):
    for ticker in duplicates:
        if ticker not in exchange_data['upbit_240_rsi']:
             exchange_data['binance_240_rsi'][ticker] = 0

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
            print(f"{ticker} {i+1} UPBIT {interval} RSI : {last_rsi}")
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
                utc_time = datetime.utcfromtimestamp(timestamp_seconds)

                json_entry = {
                    "timestamp": utc_time.isoformat(),
                    "trade_price": float(entry[4])
                }
                json_data.append(json_entry)

            json_string = json.loads(json.dumps(json_data))
            df = pd.DataFrame(json_string)

            last_rsi = rsi(df, 12).iloc[-1]
            print(f"{ticker} {i+1} BINANCE {interval} RSI : {last_rsi}")
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

def get_duplicate_ticker():
    krw_ticker = upbit.get_all_ticker()
    usdt_ticker = binance.get_all_book_ticker()

    for i in range(len(krw_ticker)):
        krw_ticker[i] = krw_ticker[i].split('-')[1]

    for i in range(len(usdt_ticker)):
        usdt_ticker[i] = usdt_ticker[i].replace("usdt@depth", "")
        usdt_ticker[i] = usdt_ticker[i].upper()

    krw_ticker = set(krw_ticker)
    usdt_ticker = set(usdt_ticker)

    counter = Counter(list(krw_ticker) + list(usdt_ticker))

    # 빈도가 1보다 큰 요소들을 찾아 중복된 값을 구합니다.
    return [element for element, count in counter.items() if count > 1]

if __name__ == "__main__":
    exchange_data = {}
    exchange_data['upbit_15_rsi'] = {}
    exchange_data['binance_15_rsi'] = {}
    exchange_data['upbit_240_rsi'] = {}
    exchange_data['binance_240_rsi'] = {}

    duplicates = get_duplicate_ticker()
    print(duplicates)
    while True:
        try:
            asyncio.run(check_240_rsi(exchange_data, duplicates))
            #asyncio.gather(check_15_rsi(exchange_data, 15, duplicates))

            print()
            time.sleep(10)
        except Exception as e:
            print(traceback.format_exc())



