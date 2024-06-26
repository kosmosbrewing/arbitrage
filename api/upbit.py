import time
import aiohttp
import pyupbit
from consts import *
import asyncio
import websockets
import json
import socket
import logging
import jwt
import hashlib
import os
import requests
import uuid
import ujson
from urllib.parse import urlencode, unquote
"""
Docs: https://pyupbit.readthedocs.io/en/latest/
"""
def get_all_ticker():
    """데이터 수신할 TICKER 목록(KRW, BTC마켓 합산)"""
    krw_ticker = pyupbit.get_tickers(fiat="KRW")
    btc_ticker = pyupbit.get_tickers(fiat="BTC")
    only_in_btc = [ticker for ticker in btc_ticker if "KRW-" + ticker.split("-")[1] not in krw_ticker]

    return krw_ticker
    #return krw_ticker + only_in_btc

def get_usd_price():
    """UPBIT 달러정보 조회"""
    data = requests.get('https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD').json()
    usd_price = float(data[0]['basePrice'])

    return usd_price
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
        

async def connect_socket_spot_orderbook(orderbook_info, socket_connect, common_ticker):
    """UPBIT 소켓연결 후 실시간 가격 저장"""
    exchange = UPBIT
    tickers = []
    for i in range(len(common_ticker)):
        tickers.append('KRW-' + common_ticker[i])

    await asyncio.sleep(SOCKET_ORDERBOOK_DELAY)
    logging.info(f"{exchange} connect_socket_orderbook")
    while True:
        try:
            logging.info(f"{exchange} WebSocket 연결 합니다. (Orderbook)")

            async with (websockets.connect('wss://api.upbit.com/websocket/v1', ping_interval=SOCKET_PING_INTERVAL,
                                           ping_timeout=SOCKET_PING_TIMEOUT, max_queue=50000) as websocket):
                socket_connect[exchange] = 1
                logging.info(f"{exchange} WebSocket 연결 완료. (Orderbook) | Socket Connect: {socket_connect}")

                subscribe_fmt = [
                    {'ticket': str(uuid.uuid4())[:6]},
                    {
                        'type': 'orderbook',
                        'codes': tickers,
                        'isOnlyRealtime': True
                    },
                ]
                subscribe_data = json.dumps(subscribe_fmt)

                logging.info(f"{exchange} Orderbook 데이터 요청 등록")
                await websocket.send(subscribe_data)

                logging.info(f"{exchange} 소켓 Orderbook 데이터 수신")
                while True:
                    try:
                        data = await asyncio.wait_for(websocket.recv(), 10)
                        data = ujson.loads(data)

                        timestamp = time.time()

                        if 'timestamp' in data:
                            time_diff = timestamp - data['timestamp']/1000

                            if time_diff > 1:
                                continue
                        else:
                            continue

                        if 'code' not in data: # 응답 데이터(딕셔너리)에 code가 없는 경우 제외
                            logging.info(f"{exchange} [Data error] : {data}")
                            continue

                        #base_ticker = data['code'].split('-')[0] # KRW-BTC > KRW(기준통화)
                        ticker = data['code'].split('-')[1]     # KRW-BTC > BTC(시세조회대코인)
                        orderbook_len = len(data['orderbook_units'])

                        if ticker not in orderbook_info:
                            orderbook_info[ticker] = {}
                            for exchange_list in EXCHANGE_LIST:
                                orderbook_info[ticker].update({exchange_list: None})
                                orderbook_info[ticker][exchange_list] = {"orderbook_units": []}
                                for i in range(0, ORDERBOOK_SIZE):
                                    orderbook_info[ticker][exchange_list]["orderbook_units"].append({"ask_price": 0, "bid_price": 0, "ask_size": 0, "bid_size": 0})

                        if orderbook_len > ORDERBOOK_SIZE:
                            for i in range(0, ORDERBOOK_SIZE):
                                orderbook_info[ticker][exchange]["orderbook_units"][i] = data['orderbook_units'][i]
                        else:
                            for i in range(0, orderbook_len):
                                orderbook_info[ticker][exchange]["orderbook_units"][i] = data['orderbook_units'][i]

                        '''
                        if util.is_need_reset_socket(start_time):
                            logging.info(f'{exchange} Websocket 연결 24시간 초과, 재연결 수행')
                            break
                        '''
                    except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed) as e:
                        try:
                            socket_connect[exchange] = 0
                            logging.info(f"{exchange} WebSocket 데이터 수신 Timeout {SOCKET_PING_TIMEOUT}초 후 재연결 합니다.")
                            pong = await websocket.ping()
                            await asyncio.wait_for(pong, timeout=SOCKET_PING_TIMEOUT)
                            socket_connect[exchange] = 1
                        except:
                            logging.info(f"{exchange} WebSocket Polling Timeout {SOCKET_RETRY_TIME}초 후 재연결 합니다.")
                            await asyncio.sleep(SOCKET_RETRY_TIME)
                            break
                    except ConnectionResetError as e:
                        break
                logging.info(f"{exchange} WebSocket 연결 종료. (Orderbook 초기화) | Socket Connect: {socket_connect}")
                await websocket.close()
        except socket.gaierror:
            logging.info(f"{exchange} WebSocket 연결 실패 {SOCKET_RETRY_TIME}초 후 재연결 합니다.")
            await asyncio.sleep(SOCKET_RETRY_TIME)
        except Exception as e:
            logging.info(f"그외 에러 Exception : {e} {SOCKET_RETRY_TIME}초 후 재연결 합니다.")
            await asyncio.sleep(SOCKET_RETRY_TIME)
            continue


async def accum_top_ticker(exchange_data):
    server_url = 'https://api.upbit.com'

    exchange = UPBIT
    ticker_list = []
    accum_list = []

    exchange_data['upbit_top_ticker'] = []

    for ticker in get_all_ticker():
        symbol = ticker.split("-")[1]

        params = {
            'market': ticker,
            'count': 1
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(server_url + '/v1/candles/minutes/15', params=params) as res:
                data = await res.json()

        await asyncio.sleep(0.3)

        ticker_list.append(symbol)
        accum_list.append(data[0]['candle_acc_trade_price'])

    for i in range(POSITION_MAX_COUNT+3):
        max_accum_data = max(accum_list)
        ticker_index = accum_list.index(max_accum_data)
        max_ticker = ticker_list[ticker_index]

        exchange_data['upbit_top_ticker'].append(max_ticker)

        accum_list.remove(max_accum_data)
        ticker_list.remove(max_ticker)

    exchange_data['upbit_top_ticker'] = list(set(exchange_data['upbit_top_ticker']))
    logging.info(f"UPBIT_TOP_TICKER : {exchange_data['upbit_top_ticker']}")
