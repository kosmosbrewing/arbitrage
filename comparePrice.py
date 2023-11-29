import asyncio
import util
import traceback
from collections import deque
import logging
from consts import *

def compare_price(exchange_data, orderbook_check, check_data, accum_ticker_count, accum_ticker_data):
    """ self.exchange_data 저장된 거래소별 코인정보를 비교하고 특정 (%)이상 갭발생시 알림 전달하는 함수 """
    for ticker in orderbook_check:
        if ticker in ["USD", "USDT"]:  # 스테이블코인은 비교 제외
            continue

        base_exchange = UPBIT
        compare_exchange = BINANCE
        # 가격 정보가 없으면 pass
        if orderbook_check[ticker][base_exchange] is None or orderbook_check[ticker][compare_exchange] is None:
            continue

        open_bid = float(orderbook_check[ticker][base_exchange]['balance_ask_average'])
        close_bid = float(orderbook_check[ticker][base_exchange]['balance_bid_average'])

        open_ask = float(orderbook_check[ticker][compare_exchange]['balance_bid_average'])
        close_ask = float(orderbook_check[ticker][compare_exchange]['balance_ask_average'])

        open_bid_btc = float(orderbook_check['BTC'][base_exchange]['balance_ask_average'])
        open_ask_btc = float(orderbook_check['BTC'][compare_exchange]['balance_bid_average'])

        if open_bid == 0 or close_bid == 0:
            continue

        if open_ask == 0 or close_ask == 0:
            continue

        if open_bid_btc == 0 or open_ask_btc == 0:
            continue

        # 거래소간의 가격차이(%)
        if open_bid > open_ask:
            open_gimp = round((open_bid - open_ask) / open_ask * 100, 2)
        elif open_ask > open_bid:
            open_gimp = round((open_ask - open_bid) / open_bid * 100, 2) * -1

        if close_bid > close_ask:
            close_gimp = round((close_bid - close_ask) / close_ask * 100, 2)
        elif close_ask > close_bid:
            close_gimp = round((close_ask - close_bid) / close_bid * 100, 2) * -1

        if open_bid_btc > open_ask_btc:
            btc_open_gimp = round((open_bid_btc - open_ask_btc) / open_ask_btc * 100, 2)
        elif open_ask_btc > open_bid_btc:
            btc_open_gimp = round((open_ask_btc - open_bid_btc) / open_bid_btc * 100, 2) * -1

        ## 데이터 값 초기화
        if ticker not in check_data:
            check_data[ticker] = {"open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                                    "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask}

        if ticker not in accum_ticker_count:
            queue = deque(maxlen=FRONT_OPEN_COUNT)
            accum_ticker_count[ticker] = queue
            accum_ticker_count[ticker].append(0)

        if ticker not in accum_ticker_data:
            queue = deque(maxlen=FRONT_AVERAGE_COUNT)
            accum_ticker_data[ticker] = queue

        accum_ticker_data[ticker].append(open_gimp)

        if len(accum_ticker_data[ticker]) < FRONT_AVERAGE_COUNT:
            average_open_gimp = sum(accum_ticker_data[ticker]) / len(accum_ticker_data[ticker])
        else:
            average_open_gimp = sum(accum_ticker_data[ticker]) / FRONT_AVERAGE_COUNT

        if open_gimp < check_data[ticker]['open_gimp']:
            check_data[ticker].update({"open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                                       "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask})

        ## 저점 진입 김프 <-> 현재 포지션 종료 김프 계산하여 수익 변동성 확인
        if close_gimp - check_data[ticker]['open_gimp'] > OPEN_GIMP_GAP:
            check_data[ticker].update({"open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                                       "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask})
            accum_ticker_count[ticker].append(1)
        else:
            accum_ticker_count[ticker].append(0)

        # ASK : 매도, BID ; 매수, ASK/BID 호가만큼 시장가로 긁으면 매수/매도 금액
        message = f"Premium|{ticker}"
        try:
            #message += "{}|{}|{}|".format(ticker, base_exchange, compare_exchange)
            message += "|OPEN|{}|{}/{}".format(open_gimp, f"{open_bid:,.2f}", f"{open_ask:,.2f}")
            message += "|CLOSE|{}|{}/{}".format(close_gimp, f"{close_bid:,.2f}", f"{close_ask:,.2f}")
            message += "|BTC_OPEN|{}".format(btc_open_gimp)
            message += "|LOW_OPEN|{}".format(check_data[ticker]['open_gimp'])
            message += "|AVG_OPEN|{}".format(round(average_open_gimp,2))
            message += "|OPEN_CNT|{}".format(sum(accum_ticker_count[ticker]))
            message += "|AMOUNT|{}/{}".format(f"{orderbook_check[ticker][base_exchange]['ask_amount']:,.0f}",
                f"{orderbook_check[ticker][compare_exchange]['bid_amount']:,.0f}")
            message += "|DOLLAR|{}".format(exchange_data["USD"]['base'])
        except:
            message += "호가미수신"

        logging.info(f"{message}")