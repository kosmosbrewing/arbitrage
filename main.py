import asyncio
import util
import traceback
import logging
from consts import *
from compareprice import comparePriceOpenOrder, comparePriceCheck, comparePriceCloseOrder
from api import upbit, binance, checkOrderbook, checkRealGimp, checkRSI

class Premium:
    def __init__(self):
        self.exchange_data = {}  # 거래소별 가격 데이터를 저장할 딕셔너리
        self.orderbook_info = {}  # 거래소별 호가 데이터 저장
        self.orderbook_check = {}
        self.socket_connect = {"Upbit": 0, "Binance": 0}
        self.check_data = {}
        self.trade_data = {}
        self.position_data = {}
        self.acc_ticker_count = {}
        self.acc_ticker_data = {}
        self.remain_bid_balance = {"balance": BALANCE}
        self.position_ticker_count = {"count": 0, "open_gimp_limit": 0}
        self.order_flag = {"open": 0, "close": 0, "ticker": 0}

        util.setup_order_logging()

    async def run(self):
        await util.send_to_telegram('🚀 Start Premium Bot 🚀')

        await asyncio.wait([
            asyncio.create_task(self.get_binance_order_data())
            , asyncio.create_task(self.get_upbit_top_ticker())
            , asyncio.create_task(self.check_real_gimp())
            , asyncio.create_task(upbit.connect_socket_spot_orderbook(self.orderbook_info, self.socket_connect))
            , asyncio.create_task(binance.connect_socket_futures_orderbook(self.orderbook_info, self.socket_connect))
            , asyncio.create_task(self.check_orderbook())
            , asyncio.create_task(self.compare_price_open_order())
            , asyncio.create_task(self.compare_price_close_order())
            , asyncio.create_task(self.compare_price_check())
            , asyncio.create_task(self.get_profit_position())
            , asyncio.create_task(self.get_15_rsi())
            , asyncio.create_task(self.get_240_rsi())
        ])

    async def get_binance_order_data(self):
        while True:
            try:
                logging.info(f"Binance Quantity Precision 요청")

                binance.get_binance_order_data(self.exchange_data)
                await asyncio.sleep(GET_ORDER_DATA_DELAY)
            except Exception as e:
                logging.info(traceback.format_exc())

    async def get_upbit_top_ticker(self):
        while True:
            try:
                logging.info(f"Upbit Top Ticker 요청")
                await upbit.accum_top_ticker(self.exchange_data)
                util.put_top_ticker(self.exchange_data)
                await asyncio.sleep(GET_TOP_TICKER_DELAY)
            except Exception as e:
                logging.info(traceback.format_exc())

    async def check_real_gimp(self):
        """ 두나무 API를 이용해 달러가격을 조회하는 함수
        while문을 통해 일정 주기를 기준으로 무한히 반복 """
        await asyncio.sleep(CHECK_REAL_GIMP_DELAY)
        logging.info(f"Check Real Gimp 기동")

        while True:
            try:
                util.load_low_gimp(self.exchange_data)

                await asyncio.sleep(CHECK_REAL_GIMP)
                orderbook_info = self.orderbook_info.copy()
                await checkRealGimp.check_real_gimp(orderbook_info, self.exchange_data, self.acc_ticker_count)
            except Exception as e:
                logging.info(traceback.format_exc())

    async def check_orderbook(self):
        await asyncio.sleep(CHECK_ORDERBOOK_START_DELAY)
        logging.info(f"Check Orderbook 기동")
        while True:
            try:
                await asyncio.sleep(0.1)
                orderbook_info = self.orderbook_info.copy()
                checkOrderbook.check_orderbook(orderbook_info, self.orderbook_check)

            except Exception as e:
                logging.info(traceback.format_exc())

    async def compare_price_open_order(self):
        await asyncio.sleep(COMPARE_PRICE_ORDER_DELAY)
        logging.info(f"ComparePrice Open Order 기동")
        while True:
            try:
                await asyncio.sleep(COMPARE_PRICE_ORDER)
                orderbook_check = self.orderbook_check.copy()
                exchange_data = self.exchange_data.copy()
                socket_connect = self.socket_connect.copy()

                if socket_connect['Upbit'] == 0 or socket_connect['Binance'] == 0:
                    logging.info(f"Socket 연결 끊어 짐 : {socket_connect}, compare_price_open_order {SOCKET_RETRY_TIME}초 후 재시도")
                    await asyncio.sleep(SOCKET_RETRY_TIME)
                else:
                    await comparePriceOpenOrder.compare_price_open_order(orderbook_check, exchange_data,
                                                                         self.remain_bid_balance, self.check_data, self.trade_data, self.position_data,
                                                                         self.acc_ticker_count, self.position_ticker_count, self.order_flag)
            except Exception as e:
                logging.info(traceback.format_exc())

    async def compare_price_close_order(self):
        await asyncio.sleep(COMPARE_PRICE_ORDER_DELAY)
        logging.info(f"ComparePrice Close Order 기동")
        while True:
            try:
                await asyncio.sleep(COMPARE_PRICE_ORDER)
                orderbook_check = self.orderbook_check.copy()
                exchange_data = self.exchange_data.copy()
                socket_connect = self.socket_connect.copy()

                if socket_connect['Upbit'] == 0 or socket_connect['Binance'] == 0:
                    logging.info(f"Socket 연결 끊어 짐 : {socket_connect}, compare_price_close_order {SOCKET_RETRY_TIME}초 후 재시도")
                    await asyncio.sleep(SOCKET_RETRY_TIME)
                else:
                    await comparePriceCloseOrder.compare_price_close_order(orderbook_check, exchange_data,
                                                                           self.remain_bid_balance, self.check_data, self.trade_data, self.position_data,
                                                                           self.position_ticker_count, self.order_flag)
            except Exception as e:
                logging.info(traceback.format_exc())

    async def compare_price_check(self):
        await asyncio.sleep(COMPARE_PRICE_CHECK_DELAY)
        logging.info(f"ComparePrice Check 기동")

        util.load_remain_position(self.position_data, self.trade_data, self.position_ticker_count)
        util.load_profit_count(self.position_data)
        util.put_order_flag(self.order_flag)

        for ticker in self.position_data:
            if self.position_data[ticker]['position'] == 1:
                self.remain_bid_balance['balance'] -= self.trade_data[ticker]['open_bid_price_acc'] - self.trade_data[ticker]['close_bid_price_acc']
                logging.info(f"REMAIN_BALANCE|{self.remain_bid_balance['balance']}|{self.trade_data[ticker]['open_bid_price_acc']}-{self.trade_data[ticker]['close_bid_price_acc']}")
        logging.info(f"REMAIN_BALANCE|{self.remain_bid_balance['balance']}|REMAIN_POSITION_COUNT|{self.position_ticker_count['count']}")

        while True:
            try:
                await asyncio.sleep(COMPARE_PRICE_CHECK)
                orderbook_check = self.orderbook_check.copy()
                socket_connect = self.socket_connect.copy()

                if socket_connect['Upbit'] == 0 or socket_connect['Binance'] == 0:
                    message = f"🌚 Socket 연결 끊어 짐 : {socket_connect}, compare_price_open_check {SOCKET_RETRY_TIME}초 후 재시도"
                    logging.info(message)
                    await util.send_to_telegram(message)
                    await asyncio.sleep(SOCKET_RETRY_TIME)
                else:
                    await comparePriceCheck.compare_price_check(orderbook_check, self.check_data, self.trade_data,
                                                                         self.position_data, self.acc_ticker_count, self.acc_ticker_data,
                                                                         self.position_ticker_count, self.exchange_data)

                util.put_remain_position(self.position_data, self.trade_data)
                util.put_profit_count(self.position_data)
                util.put_orderbook_check(self.orderbook_check)
                util.load_order_flag(self.order_flag)
                util.load_close_mode(self.exchange_data)
            except Exception as e:
                logging.info(traceback.format_exc())

    async def get_profit_position(self):
        await asyncio.sleep(240)
        logging.info(f"Get Profit Position 기동")

        while True:
            try:
                orderbook_check = self.orderbook_check.copy()
                message = util.get_profit_position(orderbook_check, self.position_data, self.trade_data, self.remain_bid_balance, self.exchange_data)

                await util.send_to_telegram(message)

                message = ''
                message = util.load_profit_data(message)

                if len(message) > 0:
                    message = f"💵이번 달 총 수익: {message}\n"
                    message += await binance.funding_fee()
                else:
                    message = f"🌚 수익 정보 없음"

                await util.send_to_telegram(message)
                await asyncio.sleep(POSITION_PROFIT_UPDATE)

            except Exception as e:
                logging.info(traceback.format_exc())

    async def get_15_rsi(self):
        self.exchange_data['upbit_15_rsi'] = {}
        self.exchange_data['binance_15_rsi'] = {}

        duplicates = checkRSI.get_duplicate_ticker()

        try:
            while True:
                await checkRSI.check_15_rsi(self.exchange_data, duplicates)
                await asyncio.sleep(20)
        except Exception as e:
            logging.info(traceback.format_exc())

    async def get_240_rsi(self):
        self.exchange_data['upbit_240_rsi'] = {}
        self.exchange_data['binance_240_rsi'] = {}

        duplicates = checkRSI.get_duplicate_ticker()

        try:
            while True:
                await checkRSI.check_240_rsi(self.exchange_data, duplicates)
                await asyncio.sleep(30)
        except Exception as e:
            logging.info(traceback.format_exc())

if __name__ == "__main__":
    premium = Premium()
    asyncio.run(premium.run())






