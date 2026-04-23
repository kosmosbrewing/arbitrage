import hashlib
import hmac
import logging
import os
import time
from datetime import datetime, timedelta, timezone

import aiohttp
import requests

from consts import TETHER


async def funding_fee():
    access_key = os.environ['BINANCE_OPEN_API_ACCESS_KEY']
    secret_key = os.environ['BINANCE_OPEN_API_SECRET_KEY']
    server_url = 'https://fapi.binance.com/fapi/v1/income'
    timestamp = int(time.time() * 1000)

    payload = {
        'incomeType': 'FUNDING_FEE',
        'timestamp': timestamp
    }
    query_string = '&'.join(["{}={}".format(k, v) for k, v in payload.items()])
    headers = {
        'X-MBX-APIKEY': access_key
    }
    signature = hmac.new(
        key=secret_key.encode('utf-8'),
        msg=query_string.encode('utf-8'),
        digestmod=hashlib.sha256,
    ).hexdigest()
    payload = {
        'incomeType': 'FUNDING_FEE',
        'timestamp': timestamp,
        'signature': signature
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(server_url, headers=headers, params=payload) as res:
                data = await res.json()

        sum_income = 0
        start_date = ''
        end_date = ''
        i = 0

        for current_fee in data:
            if i == 0:
                time_object_utc = datetime.fromtimestamp(current_fee['time'] / 1000, tz=timezone.utc)
                time_object_korea = time_object_utc.astimezone(timezone(timedelta(hours=9)))
                start_date = time_object_korea.strftime('%m-%d %H:%M')
            elif i == len(data) - 1:
                time_object_utc = datetime.fromtimestamp(current_fee['time'] / 1000, tz=timezone.utc)
                time_object_korea = time_object_utc.astimezone(timezone(timedelta(hours=9)))
                end_date = time_object_korea.strftime('%m-%d %H:%M')
            sum_income += float(current_fee['income'])
            i += 1

        return f"🤑총 펀딩피: {round(sum_income * TETHER, 0):,}원|조회 일자: {start_date} ~ {end_date}"
    except Exception as exc:
        logging.info(f"Exception : {exc}")


def change_margintype_all_ticker():
    access_key = os.environ['BINANCE_OPEN_API_ACCESS_KEY']
    secret_key = os.environ['BINANCE_OPEN_API_SECRET_KEY']
    server_url = 'https://fapi.binance.com/fapi/v1/marginType'
    new_leverage = 'ISOLATED'

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-MBX-APIKEY': access_key
    }
    exchange_info_url = 'https://fapi.binance.com/fapi/v1/exchangeInfo'
    exchange_info_response = requests.get(exchange_info_url)
    symbols = exchange_info_response.json()['symbols']

    for symbol_info in symbols:
        symbol = symbol_info['symbol']
        timestamp = int(time.time() * 1000)
        params = {
            'symbol': symbol,
            'marginType': new_leverage,
            'timestamp': timestamp
        }
        query_string = '&'.join([f'{key}={params[key]}' for key in params])
        signature = hmac.new(secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        response = requests.post(server_url, params={**params, 'signature': signature}, headers=headers)
        data = response.json()
        logging.info(f"Symbol: {symbol}, Leverage: {new_leverage}, Response: {data}")
        time.sleep(0.1)


def change_leverage_all_ticker():
    access_key = os.environ['BINANCE_OPEN_API_ACCESS_KEY']
    secret_key = os.environ['BINANCE_OPEN_API_SECRET_KEY']
    server_url = 'https://fapi.binance.com/fapi/v1/leverage'
    new_leverage = 2

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-MBX-APIKEY': access_key
    }
    exchange_info_url = 'https://fapi.binance.com/fapi/v1/exchangeInfo'
    exchange_info_response = requests.get(exchange_info_url)
    symbols = exchange_info_response.json()['symbols']

    for symbol_info in symbols:
        symbol = symbol_info['symbol']
        timestamp = int(time.time() * 1000)
        params = {
            'symbol': symbol,
            'leverage': new_leverage,
            'timestamp': timestamp
        }
        query_string = '&'.join([f'{key}={params[key]}' for key in params])
        signature = hmac.new(secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        response = requests.post(server_url, params={**params, 'signature': signature}, headers=headers)
        data = response.json()
        logging.info(f"Symbol: {symbol}, Leverage: {new_leverage}, Response: {data}")
        time.sleep(0.1)
