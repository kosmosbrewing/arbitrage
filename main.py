import asyncio

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

import util
import traceback
import logging
from consts import *
from compareprice import comparePriceOpenOrder, comparePriceOpenCheck, comparePriceCloseOrder
from datetime import datetime, timezone, timedelta
from api import upbit, binance, checkOrderbook, checkRealGimp

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

        util.setup_order_logging()

    async def run(self):
        await util.send_to_telegram('🚀 Start Premium Bot 🚀')
        # 달러가격 및 거래소별 소켓연결, 누적거래대금을 조회가 동작하도록 만드는 main함수

        await asyncio.wait([
            asyncio.create_task(self.get_binance_order_data())
            , asyncio.create_task(self.check_real_gimp())
            , asyncio.create_task(upbit.connect_socket_spot_orderbook(self.orderbook_info, self.socket_connect))
            , asyncio.create_task(binance.connect_socket_futures_orderbook(self.orderbook_info, self.socket_connect))
            , asyncio.create_task(self.check_orderbook())
            , asyncio.create_task(self.compare_price_open_order())
            , asyncio.create_task(self.compare_price_close_order())
            , asyncio.create_task(self.compare_price_open_check())
            , asyncio.create_task(self.get_profit_position())
        ])

    async def get_binance_order_data(self):
        while True:
            try:
                binance.get_binance_order_data(self.exchange_data)
                await asyncio.sleep(GET_ORDER_DATA_DELAY)
            except Exception as e:
                logging.info(traceback.format_exc())

    async def check_real_gimp(self):
        """ 두나무 API를 이용해 달러가격을 조회하는 함수
        while문을 통해 일정 주기를 기준으로 무한히 반복 """
        await asyncio.sleep(CHECK_ORDERBOOK_START_DELAY)
        logging.info(f"Check Real Gimp 기동")
        util.load_low_gimp(self.exchange_data)

        while True:
            try:
                await asyncio.sleep(10)
                orderbook_info = self.orderbook_info.copy()
                await checkRealGimp.check_real_gimp(orderbook_info, self.exchange_data)
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
                await asyncio.sleep(0.2)
                orderbook_check = self.orderbook_check.copy()
                exchange_data = self.exchange_data.copy()
                socket_connect = self.socket_connect.copy()

                if socket_connect['Upbit'] == 0 or socket_connect['Binance'] == 0:
                    logging.info(f"Socket 연결 끊어 짐 : {socket_connect}, compare_price_open_order {SOCKET_RETRY_TIME}초 후 재시도")
                    await asyncio.sleep(SOCKET_RETRY_TIME)
                else:
                    await comparePriceOpenOrder.compare_price_open_order(orderbook_check, exchange_data,
                                                                         self.remain_bid_balance, self.check_data, self.trade_data, self.position_data,
                                                                         self.acc_ticker_count, self.acc_ticker_data, self.position_ticker_count)
            except Exception as e:
                logging.info(traceback.format_exc())

    async def compare_price_close_order(self):
        await asyncio.sleep(COMPARE_PRICE_ORDER_DELAY)
        logging.info(f"ComparePrice Close Order 기동")
        while True:
            try:
                await asyncio.sleep(0.2)
                orderbook_check = self.orderbook_check.copy()
                exchange_data = self.exchange_data.copy()
                socket_connect = self.socket_connect.copy()

                if socket_connect['Upbit'] == 0 or socket_connect['Binance'] == 0:
                    logging.info(f"Socket 연결 끊어 짐 : {socket_connect}, compare_price_close_order {SOCKET_RETRY_TIME}초 후 재시도")
                    await asyncio.sleep(SOCKET_RETRY_TIME)
                else:
                    await comparePriceCloseOrder.compare_price_close_order(orderbook_check, exchange_data,
                                                                           self.remain_bid_balance, self.check_data, self.trade_data, self.position_data,
                                                                           self.position_ticker_count)
            except Exception as e:
                logging.info(traceback.format_exc())

    async def compare_price_open_check(self):
        await asyncio.sleep(COMPARE_PRICE_CHECK_DELAY)
        logging.info(f"ComparePrice Open Check 기동")

        util.load_remain_position(self.position_data, self.trade_data, self.position_ticker_count)
        util.load_profit_count(self.position_data)

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
                    message = f"Socket 연결 끊어 짐 : {socket_connect}, compare_price_open_check {SOCKET_RETRY_TIME}초 후 재시도"
                    logging.info(message)
                    await util.send_to_telegram(message)
                    await asyncio.sleep(SOCKET_RETRY_TIME)
                else:
                    await comparePriceOpenCheck.compare_price_open_check(orderbook_check, self.check_data, self.trade_data,
                                                                         self.position_data, self.acc_ticker_count, self.acc_ticker_data,
                                                                         self.position_ticker_count)

                util.put_remain_position(self.position_data, self.trade_data)
                util.put_profit_count(self.position_data)
            except Exception as e:
                logging.info(traceback.format_exc())

    async def get_profit_position(self):
        await asyncio.sleep(240)
        logging.info(f"Get Profit Position 기동")

        while True:
            try:
                orderbook_check = self.orderbook_check.copy()

                btc_open_gimp = 0
                open_timestamp = []
                open_message = {}
                message = ''
                for ticker in self.position_data:
                    if self.position_data[ticker]['position'] == 1:
                        time_object_utc = datetime.utcfromtimestamp(self.position_data[ticker]['open_timestamp'])
                        time_object_korea = time_object_utc.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=9)))

                        close_bid = float(orderbook_check[ticker]['Upbit']['balance_bid_average'])
                        close_ask = float(orderbook_check[ticker]['Binance']['balance_ask_average'])
                        open_bid_btc = float(orderbook_check['BTC']['Upbit']['balance_ask_average'])
                        open_ask_btc = float(orderbook_check['BTC']['Binance']['balance_bid_average'])

                        if close_bid == 0 or close_ask == 0:
                            continue
                        if open_bid_btc == 0 or open_ask_btc == 0:
                            continue

                        close_gimp = round(close_bid / close_ask * 100 - 100, 2)
                        btc_open_gimp = round(open_bid_btc / open_ask_btc * 100 - 100, 2)

                        open_timestamp.append(time_object_korea)
                        open_message[time_object_korea] = (
                                f"🌝{ticker}({self.position_data[ticker]['open_install_count']})"
                                f"|{self.position_data[ticker]['position_gimp']}~{close_gimp}%"
                                f"|{round(self.trade_data[ticker]['open_bid_price_acc'],0):,}원"
                                f"|{time_object_korea.strftime('%m-%d %H:%M')}\n"
                        )

                for i in range(len(open_timestamp)):
                    timestamp = min(open_timestamp)
                    temp_message = str(open_message[timestamp])
                    message += temp_message
                    open_timestamp.remove(timestamp)

                if self.remain_bid_balance['balance'] < BALANCE:
                    message += f"💰잔액: {round(self.remain_bid_balance['balance'], 0):,}원|BTC김프: {btc_open_gimp}%"

                if len(message) > 0:
                    await util.send_to_telegram(message)
                else:
                    message = f"🌚 진입 정보 없음"
                    await util.send_to_telegram(message)

                message = ''
                message = util.load_profit_data(message)

                if len(message) > 0:
                    message = f"💵이번 달 총 수익: {message}\n"
                    message += await binance.funding_fee()
                    await util.send_to_telegram(message)
                else:
                    message = f"🌚 수익 정보 없음"
                    await util.send_to_telegram(message)

                await asyncio.sleep(POSITION_PROFIT_UPDATE)
            except Exception as e:
                logging.info(traceback.format_exc())
    '''
    def current(update: Update) -> None:
        print("실행됐삼")
        update.message.reply_text('다른 명령어가 실행되었습니다.')
    def telegram_command(self) -> None:
        try:
            updater = Updater(TELEGRAM_BOT_TOKEN)
            dp = updater.dispatcher
            dp.add_handler(CommandHandler("current", self.current))
            updater.start_polling()
            updater.idle()
        except Exception as e:
            logging.info(traceback.format_exc())'''

if __name__ == "__main__":
    premium = Premium()
    asyncio.run(premium.run())



