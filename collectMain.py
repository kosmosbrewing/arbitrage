import asyncio
from collections import Counter

import api.checkRSI
from compareprice import comparePrice
from api import upbit, binance, bithumb, checkOrderbook, checkRSI
import util
import traceback
import logging
from consts import *

"""
    :param exchange : 거래소 명
    :param exchange_data : 거래소 별 가격 데이터를 저장할 딕셔너리
    ex) {'USD': {'base': 1349.0}, 'MBL': {'Upbit': 4.29}, 'TRX': {'Upbit': 119.0} }
    :param orderbook_info:거래소 별 거래대금 데이터를 저장할 딕셔너리
    ex) {'BTC': {'Upbit': 214.1, 'Binance': None}}
"""

class Premium:
    def __init__(self):
        self.exchange_data = {}
        self.orderbook_info = {}  # 거래소별 호가 데이터 저장
        self.orderbook_check = {}
        self.socket_connect = {"Upbit": 0, "Binance": 0}
        self.check_data = {}
        self.trade_data = {}
        self.position_data = {}
        self.accum_ticker_count = {}
        self.accum_ticker_data = {}
        self.remain_bid_balance = {"balance": BALANCE}
        self.position_ticker_count = {"count": 0}

        util.setup_collect_logging()

    async def run(self):
        # 달러가격 및 거래소별 소켓연결, 누적거래대금을 조회가 동작하도록 만드는 main함수
        common_ticker = checkOrderbook.get_common_orderbook_ticker()
        await asyncio.wait([
            asyncio.create_task(upbit.connect_socket_spot_orderbook(self.orderbook_info, self.socket_connect, common_ticker))
            , asyncio.create_task(binance.connect_socket_futures_orderbook(self.orderbook_info, self.socket_connect, common_ticker))
            , asyncio.create_task(self.compare_price())
            , asyncio.create_task(self.check_orderbook())
            , asyncio.create_task(self.get_usdt_price())
            , asyncio.create_task(self.get_15_rsi())
            , asyncio.create_task(self.get_240_rsi())
        ])

    async def compare_price(self):
        await asyncio.sleep(COMPARE_PRICE_START_DELAY)
        while True:
            try:
                await asyncio.sleep(COMPARE_PRICE_CHECK)
                orderbook_check = self.orderbook_check.copy()
                exchange_data = self.exchange_data.copy()
                socket_connect = self.socket_connect.copy()

                if socket_connect['Upbit'] == 0 or socket_connect['Binance'] == 0:
                    logging.info(f"Socket 연결 끊어 짐 : {socket_connect}, compare_price_order {SOCKET_RETRY_TIME}초 후 재시도")
                    await asyncio.sleep(SOCKET_RETRY_TIME)
                else:
                    comparePrice.compare_price(exchange_data, orderbook_check, self.check_data,
                                               self.accum_ticker_count, self.accum_ticker_data)

            except Exception as e:
                logging.info(traceback.format_exc())

    async def check_orderbook(self):
        await asyncio.sleep(CHECK_ORDERBOOK_START_DELAY)
        while True:
            try:
                await asyncio.sleep(0.1)
                orderbook_info = self.orderbook_info.copy()
                checkOrderbook.check_orderbook(orderbook_info, self.orderbook_check)

            except Exception as e:
                logging.info(traceback.format_exc())

    async def get_usdt_price(self):
        """ 두나무 API를 이용해 달러가격을 조회하는 함수
        while문을 통해 일정 주기를 기준으로 무한히 반복 """
        while True:
            try:
                bithumb.get_usdt_price(self.orderbook_info)
                await asyncio.sleep(20)
            except Exception as e:
                logging.info(traceback.format_exc())

    async def get_15_rsi(self):
        self.exchange_data['upbit_15_rsi'] = {}
        self.exchange_data['binance_15_rsi'] = {}

        duplicates = api.checkRSI.get_duplicate_ticker()

        try:
            while True:
                await checkRSI.check_15_rsi(self.exchange_data, duplicates)
                await asyncio.sleep(20)
        except Exception as e:
            logging.info(traceback.format_exc())

    async def get_240_rsi(self):
        self.exchange_data['upbit_240_rsi'] = {}
        self.exchange_data['binance_240_rsi'] = {}

        duplicates = api.checkRSI.get_duplicate_ticker()

        try:
            while True:
                await checkRSI.check_240_rsi(self.exchange_data, duplicates)
                await asyncio.sleep(30)
        except Exception as e:
            logging.info(traceback.format_exc())

if __name__ == "__main__":
    premium = Premium()
    asyncio.run(premium.run())
