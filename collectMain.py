import asyncio
import checkOrderbook
import comparePrice
import comparePriceOrder
from api import upbit, binance
import util
import traceback
import logging
from consts import *

"""
    :param exchange : 거래소 명
    :param exchagne_data : 거래소 별 가격 데이터를 저장할 딕셔너리
    ex) {'USD': {'base': 1349.0}, 'MBL': {'Upbit': 4.29}, 'TRX': {'Upbit': 119.0} }
    :param orderbook_info:거래소 별 거래대금 데이터를 저장할 딕셔너리
    ex) {'BTC': {'Upbit': 214.1, 'Binance': None}}
"""

class Premium:
    def __init__(self):
        self.exchagne_data = {}  # 거래소별 가격 데이터를 저장할 딕셔너리
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

        await asyncio.wait([
            asyncio.create_task(upbit.connect_socket_spot_orderbook(self.orderbook_info, self.socket_connect))
            , asyncio.create_task(binance.connect_socket_futures_orderbook(self.orderbook_info, self.socket_connect))
            , asyncio.create_task(self.compare_price())
            , asyncio.create_task(self.check_orderbook())
        ])

    async def compare_price(self):
        await asyncio.sleep(COMPARE_PRICE_START_DELAY)
        while True:
            try:
                await asyncio.sleep(COMPARE_PRICE_CHECK)
                orderbook_check = self.orderbook_check.copy()
                exchagne_data = self.exchagne_data.copy()
                socket_connect = self.socket_connect.copy()

                if socket_connect['Upbit'] == 0 or socket_connect['Binance'] == 0:
                    logging.info(f"Socket 연결 끊어 짐 : {socket_connect}, compare_price_order {SOCKET_RETRY_TIME}초 후 재시도")
                    await asyncio.sleep(SOCKET_RETRY_TIME)
                else:
                    comparePrice.compare_price(exchagne_data, orderbook_check, self.check_data,
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

    async def get_usd_price(self):
        """ 두나무 API를 이용해 달러가격을 조회하는 함수
        while문을 통해 일정 주기를 기준으로 무한히 반복 """
        while True:
            try:
                upbit.get_usd_price(self.exchagne_data)
                await asyncio.sleep(DOLLAR_UPDATE)
            except Exception as e:
                logging.info(traceback.format_exc())

if __name__ == "__main__":
    premium = Premium()
    asyncio.run(premium.run())
