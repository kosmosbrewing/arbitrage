import asyncio
from api import upbit, binance
import util
import traceback
import time
import platform
import requests
import json
import logging
import os
from consts import *

"""
    :param exchange : 거래소 명
    :param exchange_price : 거래소 별 가격 데이터를 저장할 딕셔너리
    ex) {'USD': {'base': 1349.0}, 'MBL': {'Upbit': 4.29}, 'TRX': {'Upbit': 119.0} }
    :param exchange_accum_trade_price:거래소 별 거래대금 데이터를 저장할 딕셔너리
    ex) {'BTC': {'Upbit': 214.1, 'Binance': None}}
"""

class Premium:
    def __init__(self):
        self.exchange_price = {}  # 거래소별 가격 데이터를 저장할 딕셔너리
        self.exchange_accum_trade_price = {}  # 거래소별 거래대금 데이터를 저장할 딕셔너리
        self.exchange_price_orderbook = {} # 거래소별 호가 데이터 저장
        self.exchange_check_orderbook = {}
        util.setup_logging()

    async def run(self):
        logging.info('Start Premium Bot (Kosmos in Japan)')
        await util.send_to_telegram('Start Premium Bot (Kosmos in Japan)')
        # 달러가격 및 거래소별 소켓연결, 누적거래대금을 조회가 동작하도록 만드는 main함수

        await asyncio.wait([
            asyncio.create_task(self.get_usd_price())
            , asyncio.create_task(upbit.connect_socket_spot_ticker(self.exchange_price))
            , asyncio.create_task(upbit.connect_socket_spot_orderbook(self.exchange_price, self.exchange_price_orderbook))
            #, asyncio.create_task(binance.connect_socket_spot_ticker(self.exchange_price))
            , asyncio.create_task(binance.connect_socket_futures_ticker(self.exchange_price))
            , asyncio.create_task(binance.connect_socket_futures_orderbook(self.exchange_price, self.exchange_price_orderbook))
            #, asyncio.create_task(self.check_exchange_accum_trade_price())
            , asyncio.create_task(self.compare_price())
            , asyncio.create_task(self.check_orderbook())
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
                await asyncio.wait([
                    asyncio.run(util.send_to_telegram(traceback.format_exc()))
                ])

    async def compare_price(self):
        """ self.exchange_price에 저장된 거래소별 코인정보를 비교하고 특정 (%)이상 갭발생시 알림 전달하는 함수 """
        logging.info("가격 비교 시작!")
        await util.send_to_telegram("✅ 가격비교 시작")

        base_message = "🔥프리미엄 정보\n"
        while True:
            try:
                await asyncio.sleep(COMPARE_PRICE_DELAY) # 거래소별 socket 연결을 통해 필요한 코인정보가 있어서 대기
                exchange_price = self.exchange_price.copy()  # 거래소에서 얻어온 가격데이터 복사
                message_dict = {}  # 갭 발생시 알람을 보낼 메시지를 저장해둘 딕셔너리
                message_list = [""]  # message_dict에 저장했던 메시지들을 보낼 순서대로 저장한 리스트

                for ticker in exchange_price:
                    if ticker in ["USD", "USDT"]:  # 스테이블코인은 비교 제외
                        continue

                    # 해당 코인이 상장되어 있는 거래소 목록
                    exchange_list = list(exchange_price[ticker])

                    for i in range(0, len(exchange_list) - 1):
                        base_exchange = exchange_list[i]
                        if exchange_price[ticker][base_exchange] is None:  # 가격 정보가 없으면 pass
                            continue

                        base_exchange_price =  \
                            round(float(exchange_price[ticker][base_exchange]), 2) \
                            if float(exchange_price[ticker][base_exchange]) > 0 \
                            else float(exchange_price[ticker][base_exchange])

                        for j in range(i + 1, len(exchange_list)):
                            compare_exchange = exchange_list[j]
                            if exchange_price[ticker][compare_exchange] is None:  # 가격 정보가 없으면 pass
                                continue

                            compare_exchange_price = round(float(exchange_price[ticker][compare_exchange]), 2) \
                                if float(exchange_price[ticker][compare_exchange]) > 0 \
                                else float(exchange_price[ticker][compare_exchange])

                            # 거래소간의 가격차이(%)
                            if base_exchange_price > compare_exchange_price:
                                diff = round((base_exchange_price - compare_exchange_price) / compare_exchange_price * 100, 2) \
                                    if compare_exchange_price else 0
                            elif compare_exchange_price > base_exchange_price:
                                diff = round((compare_exchange_price - base_exchange_price) / base_exchange_price * 100, 2) \
                                    if base_exchange_price else 0

                            if diff > NOTI_GAP_STANDARD:  # 미리 설정한 알림기준을 넘으면 저장
                                message = "{} | {}/{} 현선갭 프리미엄% #{}# | ".format(ticker, base_exchange, compare_exchange, diff)
                                message += "현재: #{}/{}# 원 | ".format(f"{base_exchange_price:,.2f}",
                                                                   f"{compare_exchange_price:,.2f}")
                                try:
                                    message += "매수/매도 규모: #{}/{}# 원 | ".format(
                                        f"{self.exchange_check_orderbook[ticker][base_exchange]['ask_amount']:,.0f}",
                                        f"{self.exchange_check_orderbook[ticker][compare_exchange]['bid_amount']:,.0f}")
                                    message += "매수/매도 평균: #{}/{}# 원".format(
                                        f"{self.exchange_check_orderbook[ticker][base_exchange]['ask_average']:,.2f}",
                                        f"{self.exchange_check_orderbook[ticker][compare_exchange]['bid_average']:,.2f}")
                                except Exception as e:
                                    message += "호가 값 미수신"
                                message_dict[diff] = message  # 발생갭을 키값으로 message 저장
                # 갭 순서로 메시지 정렬
                message_dict = dict(sorted(message_dict.items(), reverse=True))  # 메시지 갭발생순으로 정렬

                # 메세지 로깅 및 텔레그램 사이즈에 맞게 전처리
                for i in message_dict:
                    logging.info(f"ARBITRAGE : {message_dict[i]}")
                    if len(message_list[len(message_list) - 1]) + len(message_dict[i]) < TELEGRAM_MESSAGE_MAX_SIZE:
                        message_list[len(message_list) - 1] += message_dict[i] + "\n"
                    else:
                        message_list.append(message_dict[i] + "\n")
                message_list[0] = base_message + message_list[0]  # 알림 첫줄 구분용 문구추가
                
                # 정렬한 메시지를 순서대로 텔레그램 알람전송
                for message in message_list:
                    await util.send_to_telegram(message)
            except Exception as e:
                logging.info(traceback.format_exc())
                await util.send_to_telegram(traceback.format_exc())

    async def check_orderbook(self):
        await asyncio.sleep(CHECK_ORDERBOOK_DELAY)

        while True:
            try:
                # 루프 무한으로 실행되어 다른 작업 못하는 것 방지
                await asyncio.sleep(0.1)
                exchange_price_orderbook = self.exchange_price_orderbook.copy()

                # 거래소별 socket 연결을 통해 필요한 코인정보가 있어서 대기
                for ticker in exchange_price_orderbook:
                    if ticker in ["USD", "USDT"]:  # 스테이블코인은 비교 제외
                        continue

                    if ticker not in self.exchange_check_orderbook:
                        self.exchange_check_orderbook[ticker] = {}
                        for exchange_list in EXCHANGE_LIST:
                            self.exchange_check_orderbook[ticker].update({exchange_list: None})

                    for exchange_list in EXCHANGE_LIST:
                        ask_amount = 0
                        ask_size = 0
                        bid_amount = 0
                        bid_size = 0

                        for orderbook in exchange_price_orderbook[ticker][exchange_list]['orderbook_units']:
                            if orderbook is None:
                                continue

                            bid_amount += float(orderbook['bid_price']) * float(orderbook['bid_size'])
                            bid_size += float(orderbook['bid_size'])
                            ask_amount += float(orderbook['ask_price']) * float(orderbook['ask_size'])
                            ask_size += float(orderbook['ask_size'])

                        if bid_size == 0:
                            bid_size = 1
                        if ask_size == 0:
                            ask_size = 1

                        bid_average = round(float(bid_amount / bid_size), 2)
                        ask_average = round(float(ask_amount / ask_size), 2)

                        self.exchange_check_orderbook[ticker][exchange_list] = {"bid_amount" : bid_amount, "bid_average" : bid_average,
                                                "ask_amount" : ask_amount, "ask_average" : ask_average}
            except Exception as e:
                logging.info(traceback.format_exc())

    @staticmethod
    async def time_diff_checker():
        """ Binance API를 사용하면서 API 서버와 PC의 시간이 다르면 에러가 발생
        둘 간의 시간차이를 체크하고 PC의 시간을 동기화하는 함수 """
        while True:
            try:
                url = "https://api.binance.com/api/v1/time"
                t = time.time() * 1000
                r = requests.get(url)
                result = json.loads(r.content)
                if abs(int(t) - result["serverTime"]) > 1000:  # 1초 이상 차이가 발생시
                    await util.send_to_telegram("❗️Time diff:{}".format(int(t) - result["serverTime"]))
                '''
                if platform.system() == "Windows":
                    os.system('chcp 65001')
                    os.system('dir/w')
                    os.system('net stop w32time')
                    os.system('w32tm /unregister')
                    os.system('w32tm /register')
                    os.system('net start w32time')
                    os.system('w32tm /resync')
                '''
                await asyncio.sleep(TIME_DIFF_CHECK_DELAY)
            except Exception as e:
                await util.send_to_telegram(traceback.format_exc())

if __name__ == "__main__":
    premium = Premium()
    asyncio.run(premium.run())
