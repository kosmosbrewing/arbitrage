import asyncio
import util
import traceback
import logging
from consts import *

def compare_price(exchange_price, orderbook_check):
    """ self.exchange_price 저장된 거래소별 코인정보를 비교하고 특정 (%)이상 갭발생시 알림 전달하는 함수 """
    base_message = "🔥프리미엄 정보\n"
    message_dict = {}  # 갭 발생시 알람을 보낼 메시지를 저장해둘 딕셔너리
    message_list = [""]  # message_dict에 저장했던 메시지들을 보낼 순서대로 저장한 리스트

    for ticker in orderbook_check:
        if ticker in ["USD", "USDT"]:  # 스테이블코인은 비교 제외
            continue

        # 해당 코인이 상장되어 있는 거래소 목록
        # exchange_list = list(orderbook_check[ticker])

        base_exchange = UPBIT
        compare_exchange = BINANCE
        # 가격 정보가 없으면 pass
        if orderbook_check[ticker][base_exchange] is None or orderbook_check[ticker][compare_exchange] is None:
            continue

        open_base_orderbook_check = float(orderbook_check[ticker][base_exchange]['balance_ask_average'])
        close_base_orderbook_check = float(orderbook_check[ticker][base_exchange]['balance_bid_average'])

        open_compare_orderbook_check = float(orderbook_check[ticker][compare_exchange]['balance_bid_average'])
        close_compare_orderbook_check = float(orderbook_check[ticker][compare_exchange]['balance_ask_average'])

        open_base_btc_price = float(orderbook_check['BTC'][base_exchange]['balance_ask_average'])
        open_compare_btc_price = float(orderbook_check['BTC'][compare_exchange]['balance_bid_average'])

        if open_base_orderbook_check == 0 or close_base_orderbook_check == 0:
            continue

        if open_compare_orderbook_check == 0 or close_compare_orderbook_check == 0:
            continue

        if open_base_btc_price == 0 or open_compare_btc_price == 0:
            continue

        # 거래소간의 가격차이(%)
        if open_base_orderbook_check > open_compare_orderbook_check:
            open_diff = round(
                (open_base_orderbook_check - open_compare_orderbook_check) / open_compare_orderbook_check * 100, 2)
        elif open_compare_orderbook_check > open_base_orderbook_check:
            open_diff = round(
                (open_compare_orderbook_check - open_base_orderbook_check) / open_base_orderbook_check * 100, 2) * -1

        if close_base_orderbook_check > close_compare_orderbook_check:
            close_diff = round(
                (close_base_orderbook_check - close_compare_orderbook_check) / close_compare_orderbook_check * 100, 2)
        elif close_compare_orderbook_check > close_base_orderbook_check:
            close_diff = round(
                (close_compare_orderbook_check - close_base_orderbook_check) / close_base_orderbook_check * 100, 2) * -1

        if open_base_btc_price > open_compare_btc_price:
            btc_open_diff = round((open_base_btc_price - open_compare_btc_price) / open_compare_btc_price * 100, 2)
        elif open_compare_btc_price > open_base_btc_price:
            btc_open_diff = round((open_compare_btc_price - open_base_btc_price) / open_base_btc_price * 100, 2) * -1

        # ASK : 매도, BID ; 매수, ASK/BID 호가만큼 시장가로 긁으면 매수/매도 금액
        message = "Premium|"
        try:
            message += "{}|{}|{}|".format(ticker, base_exchange, compare_exchange)
            message += "OPEN|{}|{}/{}|".format(open_diff, f"{open_base_orderbook_check:,.2f}",
                                               f"{open_compare_orderbook_check:,.2f}")

            message += "CLOSE|{}|{}/{}|".format(close_diff, f"{close_base_orderbook_check:,.2f}",
                                                f"{close_compare_orderbook_check:,.2f}")
            message += "BTCOPEN|{}|".format(btc_open_diff)
            message += "AMOUNT|{}/{}|".format(
                f"{orderbook_check[ticker][base_exchange]['ask_amount']:,.0f}",
                f"{orderbook_check[ticker][compare_exchange]['bid_amount']:,.0f}")
            message += "DOLLAR|{}".format(exchange_price["USD"]['base'])
        except:
            message += "호가미수신"

        logging.info(f"{message}")
        message_dict[open_diff] = message  # 발생갭을 키값으로 message 저장

    # 갭 순서로 메시지 정렬
    message_dict = dict(sorted(message_dict.items(), reverse=True))  # 메시지 갭발생순으로 정렬

    # 메세지 로깅 및 텔레그램 사이즈에 맞게 전처리
    for i in message_dict:
        # logging.info(f"Premium|{message_dict[i]}")
        if len(message_list[len(message_list) - 1]) + len(message_dict[i]) < TELEGRAM_MESSAGE_MAX_SIZE:
            message_list[len(message_list) - 1] += message_dict[i] + "\n"
        else:
            message_list.append(message_dict[i] + "\n")
    message_list[0] = base_message + message_list[0]  # 알림 첫줄 구분용 문구추가

    # 정렬한 메시지를 순서대로 텔레그램 알람전송
    #for message in message_list:
    #    await util.send_to_telegram(message)


