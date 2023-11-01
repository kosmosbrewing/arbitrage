import asyncio
import checkOrderbook
import comparePrice
from api import upbit, binance
import util
import traceback
import logging
from consts import *

"""
    :param exchange : 거래소 명
    :param exchange_price : 거래소 별 가격 데이터를 저장할 딕셔너리
    ex) {'USD': {'base': 1349.0}, 'MBL': {'Upbit': 4.29}, 'TRX': {'Upbit': 119.0} }
    :param orderbook_info:거래소 별 거래대금 데이터를 저장할 딕셔너리
    ex) {'BTC': {'Upbit': 214.1, 'Binance': None}}
"""

class Premium:
    def __init__(self):
        self.exchange_price = {}  # 거래소별 가격 데이터를 저장할 딕셔너리
        self.orderbook_info = {}  # 거래소별 호가 데이터 저장
        self.orderbook_check = {}
        util.setup_logging()

    async def run(self):
        logging.info('Start Premium Bot')
        await util.send_to_telegram('Start Premium Bot')
        # 달러가격 및 거래소별 소켓연결, 누적거래대금을 조회가 동작하도록 만드는 main함수

        await asyncio.wait([
            asyncio.create_task(self.get_usd_price())
            , asyncio.create_task(upbit.connect_socket_spot_orderbook(self.exchange_price, self.orderbook_info))
            , asyncio.create_task(binance.connect_socket_futures_orderbook(self.exchange_price, self.orderbook_info))
            , asyncio.create_task(comparePrice.compare_price(self.exchange_price, self.orderbook_check))
            , asyncio.create_task(checkOrderbook.check_orderbook(self.orderbook_info, self.orderbook_check))

            # , asyncio.create_task(upbit.connect_socket_spot_ticker(self.exchange_price))
            # , asyncio.create_task(binance.connect_socket_spot_ticker(self.exchange_price))
            # , asyncio.create_task(binance.connect_socket_futures_ticker(self.exchange_price))
            #, asyncio.create_task(self.time_diff_checker())
        ])

    async def get_usd_price(self):
        """ 두나무 API를 이용해 달러가격을 조회하는 함수
        while문을 통해 일정 주기를 기준으로 무한히 반복 """
        while True:
            try:
                upbit.get_usd_price(self.exchange_price)
                await asyncio.sleep(DOLLAR_UPDATE)  # 달러가격 업데이트 주기, 1시간
            except Exception as e:
                await util.send_to_telegram(traceback.format_exc())

if __name__ == "__main__":
    premium = Premium()
    asyncio.run(premium.run())
