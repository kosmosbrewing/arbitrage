import hashlib
import traceback

import aiohttp
import ujson
import requests
import asyncio
import websockets
import json
import socket
import logging
import os
import time
import hmac

import util
from api.binance_admin import change_leverage_all_ticker, change_margintype_all_ticker, funding_fee
from consts import *
from datetime import datetime, timezone, timedelta
from api import checkOrderbook

"""
Docs: https://binance-docs.github.io/apidocs/spot/en/
"""
def get_all_ticker():
    """데이터 수신할 SYMBOL 목록"""
    res = requests.get("https://api.binance.com/api/v3/exchangeInfo")
    res = res.json()
    return [s['symbol'].lower() + "@miniTicker" for s in res['symbols'] if "USDT" in s['symbol']]

def get_all_book_ticker():
    """데이터 수신할 SYMBOL 목록"""
    res = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo")
    res = res.json()

    return [s['symbol'].lower() + "@depth" for s in res['symbols'] if "USDT" in s['symbol']]


def get_binance_order_data(exchange_data):
    """데이터 수신할 SYMBOL 목록"""
    res = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo")
    res = res.json()

    for s in res['symbols']:
        if "USDT" in s['symbol']:
            ticker = s['symbol'].replace("USDT", "")
            exchange_data[ticker] = {
                'quantity_precision': s['quantityPrecision'],
                'min_notional': float(s['filters'][5]['notional'])
            }

def get_min_notional(exchange_data):
    """데이터 수신할 SYMBOL 목록"""
    res = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo")
    res = res.json()

    for s in res['symbols']:
        if "USDT" in s['symbol']:
            ticker = s['symbol'].replace("USDT", "")
            exchange_data[ticker] = {'min_notional': s['quantityPrecision']}

    logging.info(f"Binance Quantity Precision 요청 : {exchange_data}")
    

async def check_order(ticker, order_result, lock):
    access_key = os.environ['BINANCE_OPEN_API_ACCESS_KEY']
    secret_key = os.environ['BINANCE_OPEN_API_SECRET_KEY']
    server_url = 'https://fapi.binance.com/fapi/v1/order'

    for i in range(5):
        timestamp = int(time.time() * 1000)

        # 주문 정보 (예시 값)
        payload = {
            'symbol': ticker,  # 거래 코인
            'orderId': order_result['orderId'],  # 주문 유형 (시장가, 지정가 등)
            'timestamp': timestamp
        }
        # 파라미터를 쿼리스트링 형태로 변환
        query_string = '&'.join(["{}={}".format(k, v) for k, v in payload.items()])
        # 헤더 설정
        headers = {
            'X-MBX-APIKEY': access_key
        }
        # 서명 생성
        signature = hmac.new(key=secret_key.encode('utf-8'), msg=query_string.encode('utf-8'),
                             digestmod=hashlib.sha256).hexdigest()
        payload = {
            'symbol': ticker,  # 거래 코인
            'orderId': order_result['orderId'],  # 주문 유형 (시장가, 지정가 등)
            'timestamp': timestamp,
            'signature': signature
        }
        # 서명을 요청 파라미터에 추가
        # server_url = f'{server_url}?{query_string}&signature={signature}'
        async with lock:

            try:
                await asyncio.sleep(0.5)

                async with aiohttp.ClientSession() as session:
                    async with session.get(server_url, headers=headers, params=payload) as res:
                        data = await res.json()

                logging.info("ORDER CHECK >> BINANCE 주문 확인 결과")
                logging.info(f"BINANCE_REQUEST >> orderId|{order_result['orderId']}")
                logging.info(f"BINANCE_RESPONSE >> \n{data}")
                order_result['binance_price'] = float(data['avgPrice'])
                order_result['binance_quantity'] = float(data['executedQty'])
                break
            except Exception as e:
                logging.info(f"ORDER CHECK >> BINANCE 주문 확인 실패.. 재시도")
                logging.info(f"Exception : {e}")

async def futures_order(ticker, side, quantity, order_result, lock):
    access_key = os.environ['BINANCE_OPEN_API_ACCESS_KEY']
    secret_key = os.environ['BINANCE_OPEN_API_SECRET_KEY']
    server_url = 'https://fapi.binance.com/fapi/v1/order'
    timestamp = int(time.time() * 1000)

    if side == 'ask':
        side = 'SELL'
    elif side == 'bid':
        side = 'BUY'

    # 주문 정보 (예시 값)
    payload = {
        'symbol': ticker,  # 거래 코인
        'side': side,  # 매수 또는 매도
        'type': 'MARKET',  # 주문 유형 (시장가, 지정가 등)
        'quantity': quantity,  # 주문 수량
        'timestamp': timestamp
    }
    # 파라미터를 쿼리스트링 형태로 변환
    query_string = '&'.join(["{}={}".format(k, v) for k, v in payload.items()])
    # 헤더 설정
    headers = {
        'X-MBX-APIKEY': access_key
    }
    # 서명 생성
    signature = hmac.new(key=secret_key.encode('utf-8'), msg=query_string.encode('utf-8'),
                         digestmod=hashlib.sha256).hexdigest()
    # 서명을 요청 파라미터에 추가
    server_url = f'{server_url}?{query_string}&signature={signature}'

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(server_url, headers=headers) as res:
                data = await res.json()

        async with lock:
            logging.info("ORDER >> BINANCE 주문 결과")
            logging.info(f"BINANCE_REQUEST >> {ticker}|SIDE|{side}|QUANTITY|{quantity}")
            logging.info(f"BINANCE_RESPONSE >>\n{data}")
            
            order_result['orderId'] = data['orderId']
    except Exception as e:
        logging.info("ORDER >> BINANCE 주문 실패")
        logging.info(f"Exception : {e}")

async def connect_socket_futures_orderbook(orderbook_info, socket_connect, common_ticker):
    """Binance 소켓연결"""
    exchange = BINANCE
    tickers = []

    for i in range(len(common_ticker)):
        tickers.append(common_ticker[i].lower() + 'usdt@depth')

    await asyncio.sleep(SOCKET_ORDERBOOK_DELAY)
    logging.info(f"{exchange} connect_socket")

    params_ticker = []

    while True:
        try:
            logging.info(f"{exchange} WebSocket 연결 합니다. (Orderbook)")

            async with (websockets.connect('wss://fstream.binance.com/ws', ping_interval=SOCKET_PING_INTERVAL,
                                          ping_timeout=SOCKET_PING_TIMEOUT, max_queue=50000) as websocket):
                socket_connect[exchange] = 1
                logging.info(f"{exchange} WebSocket 연결 완료. (Orderbook) | Socket Connect: {socket_connect}")

                for idx, ticker in enumerate(tickers):
                    params_ticker.append(ticker)

                    if len(params_ticker) > 50 or idx == len(tickers)-1:
                        subscribe_fmt = {
                            "method": "SUBSCRIBE",
                            "params": params_ticker,
                            "id": 1
                        }

                        subscribe_data = json.dumps(subscribe_fmt)

                        logging.info(f"{exchange} Orderbook 데이터 요청 등록")
                        await websocket.send(subscribe_data)
                        await asyncio.sleep(0.5)
                        params_ticker = []

                logging.info(f"{exchange} 소켓 Orderbook 데이터 수신")
                while True:
                    try:
                        data = await asyncio.wait_for(websocket.recv(), 10)
                        data = ujson.loads(data)

                        timestamp = time.time()

                        if 'T' in data:
                            time_diff = timestamp - data['T'] / 1000

                            if time_diff > 1:
                                continue
                        else:
                            continue

                        ticker = data['s'].replace("USDT", "") if 's' in data else None

                        if not ticker:  # ticker가 없는 데이터의 경우 저장 불가
                            continue

                        ask_len = len(data['a'])
                        bid_len = len(data['b'])

                        if ticker not in orderbook_info:
                            orderbook_info[ticker] = {}
                            for exchange_list in EXCHANGE_LIST:
                                orderbook_info[ticker].update({exchange_list: None})
                                orderbook_info[ticker][exchange_list] = {"orderbook_units": []}

                                for i in range(0, ORDERBOOK_SIZE):
                                    orderbook_info[ticker][exchange_list]["orderbook_units"].append({"ask_price": 0, "bid_price": 0, "ask_size": 0, "bid_size": 0})

                        if ask_len > ORDERBOOK_SIZE:
                            for i in range(0, ORDERBOOK_SIZE):
                                orderbook_info[ticker][exchange]["orderbook_units"][i]['ask_price'] = float(data['a'][i][0]) * TETHER
                                orderbook_info[ticker][exchange]["orderbook_units"][i]['ask_size'] = data['a'][i][1]
                        else:
                            for i in range(0, ask_len):
                                orderbook_info[ticker][exchange]["orderbook_units"][i]['ask_price'] = float(data['a'][i][0]) * TETHER
                                orderbook_info[ticker][exchange]["orderbook_units"][i]['ask_size'] = data['a'][i][1]
                        j = 0
                        if bid_len > ORDERBOOK_SIZE:
                            for i in range(bid_len-1, bid_len-1-ORDERBOOK_SIZE, -1):
                                orderbook_info[ticker][exchange]["orderbook_units"][j]['bid_price'] = float(data['b'][i][0]) * TETHER
                                orderbook_info[ticker][exchange]["orderbook_units"][j]['bid_size'] = data['b'][i][1]
                                j += 1
                        else:
                            for i in range(bid_len-1, -1, -1):
                                orderbook_info[ticker][exchange]["orderbook_units"][j]['bid_price'] = float(data['b'][i][0]) * TETHER
                                orderbook_info[ticker][exchange]["orderbook_units"][j]['bid_size'] = data['b'][i][1]
                                j += 1
                        '''
                        if util.is_need_reset_socket(start_time):
                            logging.info(f'{exchange} Websocket 연결 24시간 초과, 재연결 수행')
                            break
                        '''
                    except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed) as e:
                        try:
                            socket_connect[exchange] = 0
                            logging.info(f"{exchange} WebSocket 데이터 수신 Timeout {SOCKET_RETRY_TIME}초 후 재연결 합니다.")
                            logging.info(f"Exception : {e}")
                            pong = await websocket.ping()
                            await asyncio.wait_for(pong, timeout=SOCKET_RETRY_TIME)
                            socket_connect[exchange] = 1
                        except:
                            logging.info(f"{exchange} WebSocket Polling Timeout 재연결 합니다.")
                            await asyncio.sleep(SOCKET_RETRY_TIME)
                            break
                    except ConnectionResetError as e:
                        break
                logging.info(f"{exchange} WebSocket 연결 종료. (Orderbook 초기화) | Socket Connect: {socket_connect}")
                await websocket.close()
        except socket.gaierror:
            logging.info(f"{exchange} WebSocket 연결 실패 {SOCKET_RETRY_TIME}초 후 재연결 합니다.")
            await asyncio.sleep(SOCKET_RETRY_TIME)
            continue
        except ConnectionRefusedError:
            logging.info(f"{exchange} WebSocket 연결 실패 {SOCKET_RETRY_TIME}초 후 재연결 합니다.")
            await asyncio.sleep(SOCKET_RETRY_TIME)
            continue
        except Exception as e:
            logging.info(f"그외 에러 Exception : {e} {SOCKET_RETRY_TIME}초 후 재연결 합니다.")
            await asyncio.sleep(SOCKET_RETRY_TIME)
            continue
if __name__ == "__main__":
    get_all_book_ticker()
