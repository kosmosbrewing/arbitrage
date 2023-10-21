import requests
from consts import *
import util
import asyncio
import websockets
import json
import socket
import logging
import uuid
from datetime import datetime
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
    res = requests.get("https://api.binance.com/api/v3/exchangeInfo")
    res = res.json()
    return [s['symbol'].lower() + "@depth" for s in res['symbols'] if "USDT" in s['symbol']]

async def connect_socket_spot_ticker(exchange_price):
    """Binance 소켓연결"""
    global exchange
    exchange = 'Binance'

    logging.info(f"{exchange} connect_socket")
    while True:
        try:
            await util.send_to_telegram('[{}] Creating new connection...'.format(exchange))
            start_time = datetime.now()
            util.clear_exchange_price(exchange, exchange_price)

            logging.info(f"{exchange} WebSocket 연결 합니다.")
            async with websockets.connect('wss://stream.binance.com:9443/ws', ping_interval=SOCKET_PING_INTERVAL,
                                          ping_timeout=SOCKET_PING_TIMEOUT, max_queue=10000) as websocket:
                logging.info(f"{exchange} WebSocket 연결 완료.")

                params_ticker = []
                tickers = get_all_ticker()
                for idx, ticker in enumerate(tickers):
                    params_ticker.append(ticker)

                    if len(params_ticker) > 50 or idx == len(tickers)-1:
                        subscribe_fmt = {
                            "method": "SUBSCRIBE",
                            "params": params_ticker,
                            "id": 1
                        }

                        subscribe_data = json.dumps(subscribe_fmt)

                        logging.info(f"{exchange} 데이터 요청 등록")
                        await websocket.send(subscribe_data)
                        await asyncio.sleep(1)
                        params_ticker = []

                logging.info(f"{exchange} 소켓 데이터 수신")
                while True:
                    try:
                        data = await asyncio.wait_for(websocket.recv(), 10)
                        data = json.loads(data)

                        ticker = data['s'].replace("USDT", "") if 's' in data else None
                        if not ticker:  # ticker가 없는 데이터의 경우 저장 불가
                            continue
                        if ticker not in exchange_price:
                            exchange_price[ticker] = {exchange: None}

                        exchange_price[ticker][exchange] = float(data['c']) * \
                        exchange_price['USD']['base'] if 'USD' in exchange_price else 0  * \
                        exchange_price['USDT']['base'] if 'c' in data and 'USDT' in exchange_price else 1

                        # logging.info(ticker, data) # 결과출력 테스트(주석)
                        # 해외거래소 코인의 가격은 (가격 * USD(환율) * USDT/USD)
                        # logging.info(f"{exchange} 가격표 확인", exchange_price)

                        if util.is_need_reset_socket(start_time):  # 매일 아침 9시 소켓 재연결
                            await util.send_to_telegram('[{}] Time to new connection...'.format(exchange))
                            break

                    except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                        try:
                            logging.info(f"{exchange} WebSocket 데이터 수신 Timeout {SOCKET_PING_TIMEOUT}초 후 재연결 합니다.")
                            pong = await websocket.ping()
                            await asyncio.wait_for(pong, timeout=SOCKET_PING_TIMEOUT)
                        except:
                            logging.info(f"{exchange} WebSocket Polling Timeout {SOCKET_RETRY_TIME}초 후 재연결 합니다.")
                            await asyncio.sleep(SOCKET_RETRY_TIME)
                            break
                await websocket.close()
        except socket.gaierror:
            logging.info(f"{exchange} WebSocket 연결 실패 {SOCKET_RETRY_TIME}초 후 재연결 합니다.")
            await asyncio.sleep(SOCKET_RETRY_TIME)
            continue
        except ConnectionRefusedError:
            logging.info(f"{exchange} WebSocket 연결 실패 {SOCKET_RETRY_TIME}초 후 재연결 합니다.")
            await asyncio.sleep(SOCKET_RETRY_TIME)
            continue


async def connect_socket_futures_ticker(exchange_price):
    """Binance 소켓연결"""
    global exchange
    exchange = 'Binance'
    logging.info(f"{exchange} connect_socket")
    while True:
        try:
            await util.send_to_telegram('[{}] Creating new connection...'.format(exchange))
            start_time = datetime.now()
            util.clear_exchange_price(exchange, exchange_price)

            logging.info(f"{exchange} WebSocket 연결 합니다. (Spot)")
            async with websockets.connect('wss://fstream.binance.com/ws', ping_interval=SOCKET_PING_INTERVAL,
                                          ping_timeout=SOCKET_PING_TIMEOUT, max_queue=10000) as websocket:
                logging.info(f"{exchange} WebSocket 연결 완료. (Spot)")

                params_ticker = []
                tickers = get_all_ticker()
                for idx, ticker in enumerate(tickers):
                    params_ticker.append(ticker)

                    if len(params_ticker) > 50 or idx == len(tickers)-1:
                        subscribe_fmt = {
                            "method": "SUBSCRIBE",
                            "params": params_ticker,
                            "id": 1
                        }

                        subscribe_data = json.dumps(subscribe_fmt)

                        logging.info(f"{exchange} Futures 데이터 요청 등록")
                        await websocket.send(subscribe_data)
                        await asyncio.sleep(1)
                        # print("TEST : ", params_ticker)
                        params_ticker = []

                logging.info(f"{exchange} 소켓 Futures 데이터 수신")
                while True:
                    try:
                        data = await asyncio.wait_for(websocket.recv(), 10)
                        data = json.loads(data)

                        ticker = data['s'].replace("USDT", "") if 's' in data else None

                        if not ticker:  # ticker가 없는 데이터의 경우 저장 불가
                            continue
                        if ticker not in exchange_price:
                            exchange_price[ticker] = {}
                            for exchange_list in EXCHANGE_LIST:
                                exchange_price[ticker].update({exchange_list: None})

                        if 'USD' in exchange_price:
                            usd_price = exchange_price['USD']['base']
                        else:
                            usd_price = 0

                        exchange_price[ticker][exchange] = float(data['c']) * usd_price

                        # if ticker == 'BTC':
                        #    print(f"선물 데이터 출력 : {ticker} | {exchange_price[ticker]}")

                        if util.is_need_reset_socket(start_time):  # 매일 아침 9시 소켓 재연결
                            await util.send_to_telegram('[{}] Time to new connection...'.format(exchange))
                            break

                    except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                        try:
                            logging.info(f"{exchange} WebSocket 데이터 수신 Timeout {SOCKET_PING_TIMEOUT}초 후 재연결 합니다.")
                            pong = await websocket.ping()
                            await asyncio.wait_for(pong, timeout=SOCKET_PING_TIMEOUT)
                        except:
                            logging.info(f"{exchange} WebSocket Polling Timeout {SOCKET_RETRY_TIME}초 후 재연결 합니다.")
                            await asyncio.sleep(SOCKET_RETRY_TIME)
                            break
                await websocket.close()
        except socket.gaierror:
            logging.info(f"{exchange} WebSocket 연결 실패 {SOCKET_RETRY_TIME}초 후 재연결 합니다.")
            await asyncio.sleep(SOCKET_RETRY_TIME)
            continue
        except ConnectionRefusedError:
            logging.info(f"{exchange} WebSocket 연결 실패 {SOCKET_RETRY_TIME}초 후 재연결 합니다.")
            await asyncio.sleep(SOCKET_RETRY_TIME)
            continue

async def connect_socket_futures_orderbook(exchange_price, exchange_price_orderbook):
    """Binance 소켓연결"""
    global exchange
    exchange = 'Binance'
    await asyncio.sleep(SOCKET_ORDERBOOK_DELAY)
    logging.info(f"{exchange} connect_socket")
    while True:
        try:
            await util.send_to_telegram('[{}] Creating new connection...'.format(exchange))
            start_time = datetime.now()
            # util.clear_exchange_price(exchange, exchange_price)

            logging.info(f"{exchange} WebSocket 연결 합니다. (Orderbook)")
            async with (websockets.connect('wss://fstream.binance.com/ws', ping_interval=SOCKET_PING_INTERVAL,
                                          ping_timeout=SOCKET_PING_TIMEOUT, max_queue=10000) as websocket):
                logging.info(f"{exchange} WebSocket 연결 완료. (Orderbook)")

                params_ticker = []
                tickers = get_all_book_ticker()
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
                        await asyncio.sleep(1)
                        # print("TEST : ", params_ticker)
                        params_ticker = []

                logging.info(f"{exchange} 소켓 Orderbook 데이터 수신")
                while True:
                    try:
                        data = await asyncio.wait_for(websocket.recv(), 10)
                        data = json.loads(data)

                        ticker = data['s'].replace("USDT", "") if 's' in data else None

                        if not ticker:  # ticker가 없는 데이터의 경우 저장 불가
                            continue

                        if 'USD' in exchange_price:
                            usd_price = exchange_price['USD']['base']
                        else:
                            usd_price = 0

                        orderbook_units_temp = []
                        ask_len = len(data['a'])
                        bid_len = len(data['b'])

                        for i in range(0,ORDERBOOK_SIZE):
                            orderbook_units_temp.append({"ask_price" : 0, "bid_price" : 0, "ask_size" : 0, "bid_size" : 0 })

                        if ask_len > ORDERBOOK_SIZE:
                            for i in range(0, ORDERBOOK_SIZE):
                                orderbook_units_temp[i].update({"ask_price": float(data['a'][i][0]) * usd_price
                                                                , "ask_size": data['a'][i][1]})
                        else:
                            for i in range(0, ask_len):
                                orderbook_units_temp[i].update({"ask_price": float(data['a'][i][0]) * usd_price
                                                                , "ask_size": data['a'][i][1]})
                        j = 0
                        if bid_len > ORDERBOOK_SIZE:
                            for i in range(bid_len-1, bid_len-1-ORDERBOOK_SIZE,-1):
                                orderbook_units_temp[j]['bid_price'] = float(data['b'][i][0]) * usd_price
                                orderbook_units_temp[j]['bid_size'] = data['b'][i][1]
                                j += 1
                        else:
                            for i in range(bid_len-1, -1,-1):
                                orderbook_units_temp[j]['bid_price'] = float(data['b'][i][0]) * usd_price
                                orderbook_units_temp[j]['bid_size'] = data['b'][i][1]
                                j += 1

                        if ticker not in exchange_price_orderbook:
                            exchange_price_orderbook[ticker] = {}
                            for exchange_list in EXCHANGE_LIST:
                                exchange_price_orderbook[ticker].update({exchange_list: None})
                                exchange_price_orderbook[ticker][exchange_list] = {"orderbook_units": [None]}

                        # 호가 데이터 저장
                        exchange_price_orderbook[ticker][exchange]["orderbook_units"] = orderbook_units_temp

                        if util.is_need_reset_socket(start_time):  # 매일 아침 9시 소켓 재연결
                            await util.send_to_telegram('[{}] Time to new connection...'.format(exchange))
                            break

                    except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                        try:
                            logging.info(f"{exchange} WebSocket 데이터 수신 Timeout {SOCKET_PING_TIMEOUT}초 후 재연결 합니다.")
                            pong = await websocket.ping()
                            await asyncio.wait_for(pong, timeout=SOCKET_PING_TIMEOUT)
                        except:
                            logging.info(f"{exchange} WebSocket Polling Timeout {SOCKET_RETRY_TIME}초 후 재연결 합니다.")
                            await asyncio.sleep(SOCKET_RETRY_TIME)
                            break
                await websocket.close()
        except socket.gaierror:
            logging.info(f"{exchange} WebSocket 연결 실패 {SOCKET_RETRY_TIME}초 후 재연결 합니다.")
            await asyncio.sleep(SOCKET_RETRY_TIME)
            continue
        except ConnectionRefusedError:
            logging.info(f"{exchange} WebSocket 연결 실패 {SOCKET_RETRY_TIME}초 후 재연결 합니다.")
            await asyncio.sleep(SOCKET_RETRY_TIME)
            continue