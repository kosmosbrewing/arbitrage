import asyncio
import checkOrderbook
import comparePrice
import comparePriceOrder
import line_profiler
from api import upbit, binance
import util
import traceback
import logging
from datetime import datetime
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
        self.socket_connect = [0, 0]
        self.check_data = {}
        self.trade_data = {}
        self.position_data = {}
        self.accum_ticker_count = {}
        self.accum_ticker_data = {}
        self.remain_bid_balance = {"balance": BALANCE}

        util.setup_logging()

    async def run(self):
        await util.send_to_telegram('🚀 Start Premium Bot 🚀')
        # 달러가격 및 거래소별 소켓연결, 누적거래대금을 조회가 동작하도록 만드는 main함수

        await asyncio.wait([
            asyncio.create_task(self.get_usd_price())
            , asyncio.create_task(upbit.connect_socket_spot_orderbook(self.exchange_price, self.orderbook_info, self.socket_connect))
            , asyncio.create_task(binance.connect_socket_futures_orderbook(self.exchange_price, self.orderbook_info, self.socket_connect))
            , asyncio.create_task(self.compare_price_order())
            #, asyncio.create_task(self.compare_price())
            , asyncio.create_task(self.check_orderbook())
            , asyncio.create_task(self.get_profit_position())
        ])

    async def compare_price_order(self):
        await asyncio.sleep(COMPARE_PRICE_START_DELAY)

        util.load_remain_position(self.position_data, self.trade_data)
        for ticker in self.trade_data:
            self.remain_bid_balance['balance'] -= self.trade_data[ticker]['open_bid_price'] - self.trade_data[ticker]['close_bid_price']
        logging.info(f"REMAIN_BALANCE|{self.remain_bid_balance['balance']}")

        while True:
            try:
                await asyncio.sleep(COMPARE_PRICE_DELAY)
                orderbook_check = self.orderbook_check.copy()
                socket_connect = self.socket_connect.copy()
                check_data = self.check_data.copy()
                trade_data = self.trade_data.copy()
                position_data = self.position_data.copy()
                accum_ticker_count = self.accum_ticker_count.copy()
                accum_ticker_data = self.accum_ticker_data.copy()

                if sum(socket_connect) < 2:
                    print(f"Socket 연결 끊어 짐(정상 2) : {sum(socket_connect)}, compare_price PASS!")
                elif sum(socket_connect) == 2:
                    await comparePriceOrder.compare_price_order(orderbook_check, self.remain_bid_balance, check_data,
                                                    trade_data, position_data, accum_ticker_count, accum_ticker_data)
                util.put_remain_position(position_data, trade_data)

            except Exception as e:
                logging.info(traceback.format_exc())

    async def compare_price(self):
        await asyncio.sleep(COMPARE_PRICE_START_DELAY)
        #logging.info("가격 비교 시작!")
        while True:
            try:
                await asyncio.sleep(COMPARE_PRICE_DELAY)
                orderbook_check = self.orderbook_check.copy()
                exchange_price = self.exchange_price.copy()
                socket_connect = self.socket_connect.copy()

                if sum(socket_connect) < 2:
                    print(f"Socket 연결 끊어 짐(정상 2) : {sum(socket_connect)}, compare_price PASS!")
                elif sum(socket_connect) == 2:
                    #logging.info("Start Compare Price")
                    comparePrice.compare_price(exchange_price, orderbook_check)

            except Exception as e:
                logging.info(traceback.format_exc())
                #await util.send_to_telegram(traceback.format_exc())

    async def check_orderbook(self):
        await asyncio.sleep(CHECK_ORDERBOOK_START_DELAY)
        while True:
            try:
                await asyncio.sleep(0.5)
                orderbook_info = self.orderbook_info.copy()
                checkOrderbook.check_orderbook(orderbook_info, self.orderbook_check)

            except Exception as e:
                logging.info(traceback.format_exc())
                #await util.send_to_telegram(traceback.format_exc())

    async def get_profit_position(self):
        """ 두나무 API를 이용해 달러가격을 조회하는 함수
        while문을 통해 일정 주기를 기준으로 무한히 반복 """
        while True:
            try:
                await asyncio.sleep(POSITION_PROFIT_UPDATE)
                trade_data = self.trade_data.copy()
                position_data = self.position_data.copy()
                message = ''

                for ticker in trade_data:
                    if trade_data[ticker]['profit_count'] > 1:
                        message += f"💵티커: {ticker}|수익: {trade_data[ticker]['total_profit']}원 \n"
                if len(message) > 0:
                    await util.send_to_telegram(message)

                message = ''
                for ticker in position_data:
                    if position_data[ticker]['position'] == 1:
                        message += (f"🌝티커: {ticker}|진입 금액: {trade_data[ticker]['open_bid_price']}원"
                                    f"|진입 김프: {position_data[ticker]['open_bid_price']}% \n")
                if len(message) > 0:
                    await util.send_to_telegram(message)
            except Exception as e:
                logging.info(traceback.format_exc())
                #await util.send_to_telegram(traceback.format_exc())

    async def get_usd_price(self):
        """ 두나무 API를 이용해 달러가격을 조회하는 함수
        while문을 통해 일정 주기를 기준으로 무한히 반복 """
        while True:
            try:
                upbit.get_usd_price(self.exchange_price)
                await asyncio.sleep(DOLLAR_UPDATE)
            except Exception as e:
                logging.info(traceback.format_exc())
                #await util.send_to_telegram(traceback.format_exc())

if __name__ == "__main__":
    premium = Premium()
    asyncio.run(premium.run())
