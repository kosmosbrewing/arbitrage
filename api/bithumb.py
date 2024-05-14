import aiohttp
from consts import *
import asyncio
import logging
import jwt
import hashlib
import os
import requests
import uuid
from urllib.parse import urlencode, unquote
"""
Docs: https://apidocs.bithumb.com/reference
"""

def get_usdt_price(orderbook_info):
    """UPBIT 달러정보 조회"""
    exchange = BITHUMB

    data = requests.get('https://api.bithumb.com/public/orderbook/USDT_KRW').json()

    ticker = data['data']['order_currency']
    bid_len = len(data['data']['bids'])
    ask_len = len(data['data']['asks'])

    if ticker not in orderbook_info:
        orderbook_info[ticker] = {}
        for exchange_list in EXCHANGE_LIST:
            orderbook_info[ticker].update({exchange_list: None})
            orderbook_info[ticker][exchange_list] = {"orderbook_units": []}
            for i in range(0, ORDERBOOK_SIZE):
                orderbook_info[ticker][exchange_list]["orderbook_units"].append({"ask_price": 0, "bid_price": 0, "ask_size": 0, "bid_size": 0})

    if ticker not in orderbook_info:
        orderbook_info[ticker] = {}
        for exchange_list in EXCHANGE_LIST:
            orderbook_info[ticker].update({exchange_list: None})
            orderbook_info[ticker][exchange_list] = {"orderbook_units": []}

            for i in range(0, ORDERBOOK_SIZE):
                orderbook_info[ticker][exchange_list]["orderbook_units"].append({"ask_price": 0, "bid_price": 0, "ask_size": 0, "bid_size": 0})

    if ask_len > ORDERBOOK_SIZE:
        for i in range(0, ORDERBOOK_SIZE):
            orderbook_info[ticker][exchange]["orderbook_units"][i]['ask_price'] = float(data['data']['asks'][i]['price'])
            orderbook_info[ticker][exchange]["orderbook_units"][i]['ask_size'] = data['data']['asks'][i]['quantity']
    else:
        for i in range(0, ask_len):
            orderbook_info[ticker][exchange]["orderbook_units"][i]['ask_price'] = float(data['data']['asks'][i]['price'])
            orderbook_info[ticker][exchange]["orderbook_units"][i]['ask_size'] = data['data']['asks'][i]['quantity']

    if bid_len > ORDERBOOK_SIZE:
        for i in range(0, ORDERBOOK_SIZE):
            orderbook_info[ticker][exchange]["orderbook_units"][i]['bid_price'] = float(data['data']['bids'][i]['price'])
            orderbook_info[ticker][exchange]["orderbook_units"][i]['bid_size'] = data['data']['bids'][i]['quantity']

    else:
        for i in range(0, bid_len):
            orderbook_info[ticker][exchange]["orderbook_units"][i]['bid_price'] = float(data['data']['bids'][i]['price'])
            orderbook_info[ticker][exchange]["orderbook_units"][i]['bid_size'] = data['data']['bids'][i]['quantity']
async def check_order(order_result, lock):
    access_key = os.environ['UPBIT_OPEN_API_ACCESS_KEY']
    secret_key = os.environ['UPBIT_OPEN_API_SECRET_KEY']
    server_url = 'https://api.upbit.com'

    for i in range(5):
        params = {
            'uuid': order_result['uuid']
        }
        query_string = unquote(urlencode(params, doseq=True)).encode("utf-8")
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()

        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, secret_key)
        authorization = 'Bearer {}'.format(jwt_token)
        headers = {
            'Authorization': authorization,
        }
        async with lock:
            try:
                await asyncio.sleep(0.5)

                async with aiohttp.ClientSession() as session:
                    async with session.get(server_url + '/v1/order', params=params, headers=headers) as res:
                        data = await res.json()

                logging.info("ORDER CHECK >> UPBIT 주문 확인 결과")
                logging.info(f"UPBIT_REQUEST >> uuid|{order_result['uuid']}")
                logging.info(f"UPBIT_RESPONSE >> \n{data}")

                for trade in data['trades']:
                    order_result['upbit_price'] += float(trade['price']) * float(trade['volume'])
                    order_result['upbit_quantity'] += float(trade['volume'])
                order_result['upbit_price'] = order_result['upbit_price'] / order_result['upbit_quantity']
                break
            except Exception as e:
                logging.info("ORDER CHECK >> UPBIT 주문 확인 실패... 재시도")
                logging.info(f"Exception : {e}")



        

async def spot_order(ticker, side, price, volume, order_result, lock):
    access_key = os.environ['UPBIT_OPEN_API_ACCESS_KEY']
    secret_key = os.environ['UPBIT_OPEN_API_SECRET_KEY']
    server_url = 'https://api.upbit.com'

    params = {
        'market': ticker,
        'side': side
    }
    if side == 'bid':
        params['price'] = price
        params['ord_type'] = 'price'
    elif side == 'ask':
        params['ord_type'] = 'market'
        params['volume'] = volume

    query_string = unquote(urlencode(params, doseq=True)).encode("utf-8")
    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()

    payload = {
        'access_key': access_key,
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }

    jwt_token = jwt.encode(payload, secret_key)
    authorization = 'Bearer {}'.format(jwt_token)
    headers = {
        'Authorization': authorization,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(server_url + '/v1/orders', json=params, headers=headers) as res:
            data = await res.json()

    try:
        async with lock:
            logging.info("ORDER >> UPBIT 주문 결과")
            if side == 'bid':
                logging.info(f"UPBIT_REQUEST >> {ticker}|SIDE|{side}|PRICE|{price}")
            elif side == 'ask':
                logging.info(f"UPBIT_REQUEST >> {ticker}|SIDE|{side}|QUANTITY|{volume}")
            logging.info(f"UPBIT_RESPONSE >>\n{data}")
            
            order_result['uuid'] = data['uuid']
    except Exception as e:
        logging.info("ORDER >> UPBIT 주문 실패")
        logging.info(f"Exception : {e}")
        
