import util
import logging
from collections import deque
from consts import *
from api import upbit, binance

async def compare_price_order(orderbook_check, exchange_data, remain_bid_balance, check_data, trade_data,
                                position_data, accum_ticker_count, accum_ticker_data, position_ticker_count):
    """ self.exchange_price 저장된 거래소별 코인정보를 비교하고 특정 (%)이상 갭발생시 알림 전달하는 함수 """
    base_exchange = UPBIT
    compare_exchange = BINANCE
    open_message_list = []
    close_message_list = []

    for ticker in orderbook_check:
        if ticker in ["USD"]:  # 스테이블코인은 비교 제외
            continue

        # 가격 정보가 없으면 pass
        if orderbook_check[ticker][base_exchange] is None or orderbook_check[ticker][compare_exchange] is None:
            continue

        open_bid = float(orderbook_check[ticker][base_exchange]['balance_ask_average'])
        close_bid = float(orderbook_check[ticker][base_exchange]['balance_bid_average'])

        open_ask = float(orderbook_check[ticker][compare_exchange]['balance_bid_average'])
        close_ask = float(orderbook_check[ticker][compare_exchange]['balance_ask_average'])

        open_bid_btc = float(orderbook_check['BTC'][base_exchange]['balance_ask_average'])
        open_ask_btc = float(orderbook_check['BTC'][compare_exchange]['balance_bid_average'])

        ## 가격이 없는 친구들 PASS
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

        curr_gimp_gap = open_gimp - close_gimp if open_gimp > close_gimp else 0

        ## 데이터 값 초기화
        if ticker not in check_data:
            print("Update Check Data")
            check_data[ticker] = {"open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                                  "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask}
        if ticker not in position_data:
            position_data[ticker] = {"open_install_count": 0, "close_install_count": 0, "position": 0,
                                     "position_gimp": 0, "position_gimp_accum": 0, "accum_open_install_count": 0}
        if ticker not in trade_data:
            trade_data[ticker] = {"open_bid_price_accum": 0, "open_ask_price_accum": 0, "close_bid_price_accum": 0,
                                  "close_ask_price_accum": 0, "close_quantity": 0,
                                  "upbit_total_quantity": 0, "binance_total_quantity": 0,
                                  "trade_profit": 0, "profit_count": 0, "total_profit": 0}

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
        '''
        logging.info(f"ORDER|{ticker}|GIMP|{open_gimp}/{close_gimp}|LOW_GIMP|{check_data[ticker]['open_gimp']}"
                     f"|BTC_GIMP|{btc_open_gimp}|AVG_GIMP|{round(average_open_gimp,2)}"
                     f"|COUNT|{sum(accum_ticker_count[ticker])}"
                     f"|OPEN|{open_bid}/{open_ask}|CLOSE|{close_bid}/{close_ask}"
                     f"|POSITION_CNT|{position_ticker_count['count']}")'''

        if remain_bid_balance['balance'] < 0:
            accum_ticker_count[ticker].append(0)
            continue

        ## 포지션 진입 로직
        if open_gimp < check_data[ticker]['open_gimp']:
            # open_gimp 이 Update 되면 close_gimp은 그 시점으로 gap 수정
            check_data[ticker].update({"open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask})
            check_data[ticker].update({"close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask})
            open_install_count = position_data[ticker]['open_install_count']

            ## 진입/종료 갭차이 너무 많이 들어가면 들어가지 않음
            if curr_gimp_gap > CURR_GIMP_GAP:
                accum_ticker_count[ticker].append(0)
                continue

            if position_ticker_count['count'] >= POSITION_TICKER_COUNT:
                accum_ticker_count[ticker].append(0)
                continue

            if open_install_count == 0 and sum(accum_ticker_count[ticker]) <= OPEN_GIMP_COUNT:
                accum_ticker_count[ticker].append(0)
                continue

            if open_install_count > 0 and position_data[ticker]['position_gimp'] * INSTALL_WEIGHT < open_gimp:
                accum_ticker_count[ticker].append(0)
                continue

            if open_gimp > average_open_gimp or open_gimp > btc_open_gimp * BTC_GAP:
                accum_ticker_count[ticker].append(0)
                continue

            # 매수/매도(숏) 기준 가격 잡기 (개수 계산)
            temp_quantity = round(BALANCE * OPEN_INSTALLMENT / open_bid, exchange_data[ticker]['quantity_precision'])
            if temp_quantity == 0:
                logging.info(f"SKIP|{ticker}|진입수량적음|OPEN_BID|{temp_quantity}|PRECISION|{exchange_data[ticker]['quantity_precision']}")
                continue
            upbit_open_bid_price = open_bid * temp_quantity

            if remain_bid_balance['balance'] - upbit_open_bid_price > 0:
                remain_bid_balance['balance'] -= upbit_open_bid_price
            else:
                accum_ticker_count[ticker].append(0)
                continue

            ## 진입 성공 시 포지션 데이터 Update
            position_data[ticker]['open_install_count'] += 1
            position_data[ticker]['accum_open_install_count'] += 1
            position_data[ticker]['position_gimp_accum'] += open_gimp
            position_data[ticker]['position_gimp'] = round(position_data[ticker]['position_gimp_accum'] / position_data[ticker]['open_install_count'], 2)
            position_data[ticker]['position'] = 1
            position_data[ticker]['close_count'] = 0

            # 주문 로직
            upbit_market = 'KRW-' + ticker
            upbit_side = 'bid'
            upbit_price = upbit_open_bid_price
            upbit_quantity = 0  ## 매수 시는 사용 안함
            upbit_open_quantity = upbit.spot_order(upbit_market, upbit_side, upbit_price, upbit_quantity)

            binance_market = ticker + 'USDT'
            binance_side = 'ask'
            binance_open_quantity = round(upbit_open_quantity, exchange_data[ticker]['quantity_precision'])
            binance.futures_order(binance_market, binance_side, binance_open_quantity)

            #trade_data[ticker].update({"open_quantity": open_quantity})
            upbit_total_quantity = upbit_open_quantity + trade_data[ticker]['upbit_total_quantity']
            binance_total_quantity = binance_open_quantity + trade_data[ticker]['binance_total_quantity']

            if position_data[ticker]['open_install_count'] > 1:
                trade_data[ticker].update({"upbit_total_quantity": upbit_total_quantity})
                trade_data[ticker].update({"binance_total_quantity": binance_total_quantity})
            else:
                trade_data[ticker].update({"upbit_total_quantity": upbit_open_quantity})
                trade_data[ticker].update({"binance_total_quantity": binance_open_quantity})
                position_ticker_count['count'] += 1

            upbit_open_bid_price_accum = upbit_open_bid_price + trade_data[ticker]['open_bid_price_accum']
            binance_open_bid_price_accum = open_ask * binance_open_quantity + trade_data[ticker]['open_ask_price_accum']

            #trade_price = open_bid if open_bid > open_ask else open_ask
            #open_quantity = BALANCE * OPEN_INSTALLMENT / trade_price  ## 분할 진입을 위해서, 임시 수량 계산
            #open_bid_price = open_bid * open_quantity + trade_data[ticker]['open_bid_price_accum']  ## 누적 매수 금액
            #open_ask_price = open_ask * open_quantity + trade_data[ticker]['open_ask_price_accum']  ## 누적 매도 금액
            # 진입 성공 시 거래 데이터 Update
            trade_data[ticker].update({"open_bid_price_accum": upbit_open_bid_price_accum, "open_ask_price_accum": binance_open_bid_price_accum})

            # 텔레그램 전송 및 로깅 데이터
            message = (f"TICKER[{ticker}]"
                       f"|진입김프[{position_data[ticker]['position_gimp']}]"
                       f"|평균진입김프[{round(average_open_gimp, 2)}]"
                       f"|BTC진입김프[{round(btc_open_gimp, 2)}]"
                       f"|변동성CNT[{sum(accum_ticker_count[ticker])}]"
                       f"|분할매수CNT[{position_data[ticker]['open_install_count']}]"
                       f"|진입가격|{open_bid}/{open_ask}"
                       f"|매수금액[{trade_data[ticker]['open_bid_price_accum']}/{trade_data[ticker]['open_ask_price_accum']}]"
                       f"|거래수량[{upbit_open_quantity}/{binance_open_quantity}]"
                       f"|총거래수량[{trade_data[ticker]['upbit_total_quantity']}/{trade_data[ticker]['binance_total_quantity']}]"
                       f"|잔액[{round(remain_bid_balance['balance'], 2)}]"
                       f"|환율[{exchange_data['USD']['base']} ]")
            ### 주문 로직
            open_message_list.append(message)

        ## 저점 진입 김프 <-> 현재 포지션 종료 김프 계산하여 수익 변동성 확인
        if close_gimp - check_data[ticker]['open_gimp'] > OPEN_GIMP_GAP:
            check_data[ticker].update({"open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask})
            check_data[ticker].update({"close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask})
            accum_ticker_count[ticker].append(1)
        else:
            accum_ticker_count[ticker].append(0)

        ## 포지션 종료 로직
        if position_data[ticker]['position'] == 1:
            close_gimp_gimp = close_gimp - position_data[ticker]['position_gimp']
            if close_gimp_gimp > CLOSE_GIMP_GAP:
                position_data[ticker]['close_install_count'] += 1
                # 종료 시점 금액 계산
                upbit_total_quantity = trade_data[ticker]['upbit_total_quantity']
                binance_total_quantity = trade_data[ticker]['binance_total_quantity']

                ## 익절 분할 횟수 Count 도달할 시 계산 로직 변경
                if position_data[ticker]['close_install_count'] * CLOSE_INSTALLMENT == 1:
                    upbit_close_quantity = upbit_total_quantity - trade_data[ticker]['close_quantity']
                    binance_close_quantity = binance_total_quantity - trade_data[ticker]['close_quantity']
                    # 주문 로직
                    upbit_market = 'KRW-' + ticker
                    upbit_side = 'ask'
                    upbit_price = 0  ## 매도시에는 사용 안함
                    upbit_quantity = upbit_close_quantity
                    upbit.spot_order(upbit_market, upbit_side, upbit_price, upbit_quantity)

                    binance_market = ticker + 'USDT'
                    binance_side = 'bid'
                    binance.futures_order_all(binance_market, binance_side)

                    install_open_bid_price = trade_data[ticker]['open_bid_price_accum'] * CLOSE_INSTALLMENT
                    install_open_ask_price = trade_data[ticker]['open_ask_price_accum'] * CLOSE_INSTALLMENT
                    install_close_bid_price = close_bid * upbit_close_quantity
                    install_close_ask_price = close_ask * binance_close_quantity

                    trade_data[ticker]['close_bid_price_accum'] += trade_data[ticker]['open_bid_price_accum'] - trade_data[ticker]['close_bid_price_accum']
                    trade_data[ticker]['close_ask_price_accum'] += trade_data[ticker]['open_ask_price_accum'] - trade_data[ticker]['close_ask_price_accum']
                    trade_data[ticker]['close_quantity'] += upbit_close_quantity
                    position_ticker_count['count'] -= 1
                ## 익절 분할 횟수 Count 도달하지 않을 시
                else:
                    close_quantity = round(upbit_total_quantity * CLOSE_INSTALLMENT, exchange_data[ticker]['quantity_precision'])
                    # 주문 로직
                    upbit_market = 'KRW-' + ticker
                    upbit_side = 'ask'
                    upbit_price = 0  ## 매도시에는 사용 안함
                    upbit_close_quantity = close_quantity
                    binance_market = ticker + 'USDT'
                    binance_side = 'bid'
                    binance_close_quantity = close_quantity

                    upbit.spot_order(upbit_market, upbit_side, upbit_price, upbit_close_quantity)
                    binance.futures_order(binance_market, binance_side, binance_close_quantity)

                    install_open_bid_price = trade_data[ticker]['open_bid_price_accum'] * CLOSE_INSTALLMENT
                    install_open_ask_price = trade_data[ticker]['open_ask_price_accum'] * CLOSE_INSTALLMENT
                    install_close_bid_price = close_bid * close_quantity
                    install_close_ask_price = close_ask * close_quantity

                    trade_data[ticker]['close_bid_price_accum'] += trade_data[ticker]['open_bid_price_accum'] * CLOSE_INSTALLMENT
                    trade_data[ticker]['close_ask_price_accum'] += trade_data[ticker]['open_ask_price_accum'] * CLOSE_INSTALLMENT
                    trade_data[ticker]['close_quantity'] += close_quantity

                ## 수익 계션 로직
                open_profit = install_close_bid_price - install_open_bid_price
                close_profit = install_open_ask_price - install_close_ask_price

                open_fee = install_open_bid_price * UPBIT_FEE + install_open_ask_price * BINANCE_FEE
                close_fee = install_close_bid_price * UPBIT_FEE + install_close_ask_price * BINANCE_FEE
                total_fee = open_fee + close_fee

                total_profit = round(open_profit + close_profit - total_fee, 2)
                trade_data[ticker].update({"trade_profit": total_profit})
                trade_data[ticker]['profit_count'] += 1
                trade_data[ticker]['total_profit'] += trade_data[ticker]['trade_profit']
                remain_bid_balance['balance'] += install_open_bid_price
                
                ## 메세지 저장
                message = (f"TICKER[{ticker}]"
                           f"|진입종료GIMP[{position_data[ticker]['position_gimp']} <-> {close_gimp}]"
                           f"|김프차이[{round(close_gimp - position_data[ticker]['position_gimp'], 2)}]"
                           f"|분할매수CNT[{position_data[ticker]['open_install_count']}]"
                           f"|분할매도CNT[{position_data[ticker]['close_install_count']}]"
                           f"|거래이익[{trade_data[ticker]['trade_profit']}]"
                           f"|총이익[{trade_data[ticker]['total_profit']}]"
                           f"|거래수량[{upbit_close_quantity}/{binance_close_quantity}]"
                           f"|현물진입종료금액[{trade_data[ticker]['open_bid_price_accum']}/{trade_data[ticker]['close_bid_price_accum']}]"
                           f"|선물진입종료금액[{trade_data[ticker]['open_ask_price_accum']}/{trade_data[ticker]['close_ask_price_accum']}]"
                           f"|총수량[{trade_data[ticker]['upbit_total_quantity']}]"
                           f"|잔액[{round(remain_bid_balance['balance'], 2)}]"
                           f"|환율[{exchange_data['USD']['base']}]")
                close_message_list.append(message)
                
                # 변수 클리어
                if position_data[ticker]['close_install_count'] * CLOSE_INSTALLMENT == 1:
                    # 종료 시점 데이터 갱신
                    position_data[ticker].update({"position": 0, "close_count": 0, "position_gimp_accum": 0, "open_install_count": 0, "close_install_count": 0})
                    trade_data[ticker].update({"open_bid_price_accum": 0, "open_ask_price_accum": 0, "close_bid_price_accum": 0, "close_ask_price_accum": 0,
                                               "close_quantity": 0, "upbit_total_quantity": 0, "trade_profit": 0})
                    
                    # 현재 시점으로 데이터 갱신
                    check_data[ticker].update({"open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask})
                    check_data[ticker].update({"close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask})

    for message in open_message_list:
        logging.info(f"POSITION_OPEN|{message}", )
        message.replace("|", "\n")
        await util.send_to_telegram("🔵진입\n" + message)

    for message in close_message_list:
        logging.info(f"POSITION_CLOSE|{message}" )
        message.replace("|", "\n")
        await util.send_to_telegram("🔴탈출\n" + message)

def update_open_check_data(ticker, check_data, open_gimp, open_bid, open_ask):
    check_data[ticker].update({"open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask})

def update_close_check_data(ticker, check_data, close_gimp, close_bid, close_ask):
    check_data[ticker].update({"close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask})

def update_open_position_data(ticker, position_data, open_gimp):
    position_data[ticker]['open_install_count'] += 1
    position_data[ticker]['accum_open_install_count'] += 1
    position_data[ticker]['position_gimp_accum'] += open_gimp
    position_data[ticker]['position_gimp'] = round(position_data[ticker]['position_gimp_accum']
                                                  / position_data[ticker]['open_install_count'], 2)
    position_data[ticker]['position'] = 1
    position_data[ticker]['close_count'] = 0

def update_close_trade_data(ticker, trade_data):
    trade_data[ticker].update({"open_bid_price_accum": 0, "open_ask_price_accum": 0,
                               "close_bid_price_accum": 0, "close_ask_price_accum": 0,
                             "close_quantity": 0, "upbit_total_quantity": 0,"trade_profit": 0})

def update_close_position_data(ticker, position_data):
    position_data[ticker].update({"position": 0, "close_count": 0, "position_gimp_accum": 0,
                                  "open_install_count": 0, "close_install_count": 0})

def get_ticker_profit(trade_data, open_profit, close_profit, total_fee, ticker):
    total_profit = round(open_profit + close_profit - total_fee, 2)
    trade_data[ticker].update({"trade_profit": total_profit})
    trade_data[ticker]['profit_count'] += 1
    trade_data[ticker]['total_profit'] += trade_data[ticker]['trade_profit']

    return trade_data
