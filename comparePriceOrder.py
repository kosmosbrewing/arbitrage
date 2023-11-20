import util
import logging
from collections import deque
from consts import *

async def compare_price_order(orderbook_check, remain_bid_balance, check_data, trade_data,
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
            trade_data[ticker] = {"open_bid_price": 0, "open_ask_price": 0, "close_bid_price": 0,
                                  "close_ask_price": 0, "open_quantity": 0, "close_quantity": 0,
                                  "total_quantity": 0, "trade_profit": 0, "profit_count": 0, "total_profit": 0}

        if ticker not in accum_ticker_count:
            queue = deque(maxlen=FRONT_OPEN_COUNT)
            accum_ticker_count[ticker] = queue
            accum_ticker_count[ticker].append(0)

        if ticker not in accum_ticker_data:
            queue = deque(maxlen=FRONT_AVERAGE_COUNT)
            accum_ticker_data[ticker] = queue

        accum_ticker_data[ticker].append(close_gimp)
        average_open_gimp = sum(accum_ticker_data[ticker]) / len(accum_ticker_data[ticker])

        logging.info(f"ORDER|{ticker}|GIMP|{open_gimp}/{close_gimp}|LOW_GIMP|{check_data[ticker]['open_gimp']}"
                     f"|BTC_GIMP|{btc_open_gimp}|AVG_GIMP|{average_open_gimp}|COUNT|{sum(accum_ticker_count[ticker])}"
                     f"|OPEN|{open_bid}/{open_ask}|CLOSE|{close_bid}/{close_ask}"
                     f"|POSITION_CNT|{position_ticker_count['count']}")

        if remain_bid_balance['balance'] < 0:
            accum_ticker_count[ticker].append(0)
            continue

        ## 현재 김프가 저점일 때
        if open_gimp < check_data[ticker]['open_gimp']:
            # open_gimp 이 Update 되면 close_gimp은 그 시점으로 gap 수정
            update_open_check_data(ticker, check_data, open_gimp, open_bid, open_ask)
            update_close_check_data(ticker, check_data, close_gimp, close_bid, close_ask)
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

            if open_gimp > average_open_gimp and open_gimp > btc_open_gimp * BTC_GAP:
                accum_ticker_count[ticker].append(0)
                continue

            # 매수/매도(숏) 기준 가격 잡기 (개수 계산)
            trade_price = open_bid if open_bid > open_ask else open_ask
            open_quantity = BALANCE * OPEN_INSTALLMENT / trade_price  ## 분할 진입을 위해서, 임시 수량 계산
            open_bid_price = open_bid * open_quantity + trade_data[ticker]['open_bid_price']  ## 누적 매수 금액
            open_ask_price = open_ask * open_quantity + trade_data[ticker]['open_ask_price']  ## 누적 매도 금액

            if remain_bid_balance['balance'] - open_bid * open_quantity > 0:
                remain_bid_balance['balance'] -= open_bid * open_quantity
            else:
                accum_ticker_count[ticker].append(0)
                continue

            update_open_position_data(ticker, position_data, open_gimp)
            trade_data[ticker].update({"open_bid_price": open_bid_price, "open_ask_price": open_ask_price})

            upbit_market = 'KRW-' + ticker
            upbit_side = 'bid'
            upbit_price = trade_data[ticker]['open_bid_price']
            upbit_quantity = trade_data[ticker]['open_quantity']  ## 매수 시는 사용 안함
            # open_quantity = upbit.spot_order(upbit_market, upbit_side, upbit_price, upbit_quantity)

            binance_market = ticker + 'USDT'
            binance_side = 'ask'
            binance_quantity = trade_data[ticker]['open_quantity']
            binance_quantity = open_quantity
            # binance.futures_order(binance_market, binance_side, binance_quantity)

            trade_data[ticker].update({"open_quantity": open_quantity})
            total_quantity = open_quantity + trade_data[ticker]['total_quantity']

            if position_data[ticker]['open_install_count'] > 1:
                trade_data[ticker].update({"total_quantity": total_quantity})
            else:
                position_ticker_count['count'] += 1
                trade_data[ticker].update({"total_quantity": open_quantity})

            message = (f"POSITION_OPEN|{ticker}|P_OPEN_GIMP|{position_data[ticker]['position_gimp']}"
                       f"|C_CLOSE_GIMP|{close_gimp}|C_OPEN_GIMP|{open_gimp}|AVG_OPEN_GIMP|{round(average_open_gimp, 2)}"
                       f"|BTC_OPEN_GIMP|{round(btc_open_gimp, 2)}|OPEN_COUNT|{sum(accum_ticker_count[ticker])}"
                       f"|INSATLL|{position_data[ticker]['open_install_count']}|BID_PRICE|{trade_data[ticker]['open_bid_price']}"
                       f"|TRD_QUANTITY|{trade_data[ticker]['open_quantity']}|TOT_QUANTITY|{trade_data[ticker]['total_quantity']}"
                       f"|BALANCE|{round(remain_bid_balance['balance'], 2)}")
            ### 주문 로직
            open_message_list.append(message)

        ## 저점 진입 김프 <-> 현재 포지션 종료 김프 계산하여 수익 변동성 확인
        if close_gimp - check_data[ticker]['open_gimp'] > OPEN_GIMP_GAP:
            update_open_check_data(ticker, check_data, open_gimp, open_bid, open_ask)
            update_close_check_data(ticker, check_data, close_gimp, close_bid, close_ask)
            accum_ticker_count[ticker].append(1)
        else:
            accum_ticker_count[ticker].append(0)

        if position_data[ticker]['position'] == 1:
            ## 익절
            close_gimp_gimp = close_gimp - position_data[ticker]['position_gimp']
            if close_gimp_gimp > CLOSE_GIMP_GAP:
                position_data[ticker]['close_install_count'] += 1

                # 종료 시점 금액 계산
                total_quantity = trade_data[ticker]['total_quantity']

                ## 익절 분할 횟수 Count 도달할 시 계산 로직 변경
                if position_data[ticker]['close_install_count'] * CLOSE_INSTALLMENT == 1:
                    close_quantity = total_quantity - trade_data[ticker]['close_quantity']

                    install_open_bid_price = trade_data[ticker]['open_bid_price'] - trade_data[ticker][
                        'close_bid_price']
                    install_open_ask_price = trade_data[ticker]['open_ask_price'] - trade_data[ticker][
                        'close_ask_price']
                    install_close_bid_price = close_bid * close_quantity
                    install_close_ask_price = close_ask * close_quantity

                    trade_data[ticker]['close_bid_price'] += trade_data[ticker]['open_bid_price'] - trade_data[ticker]['close_bid_price']
                    trade_data[ticker]['close_ask_price'] += trade_data[ticker]['open_ask_price'] - trade_data[ticker]['close_bid_price']
                    trade_data[ticker]['close_quantity'] += close_quantity
                    position_ticker_count['count'] -= 1
                ## 익절 분할 횟수 Count 도달하지 않을 시
                else:
                    close_quantity = total_quantity * CLOSE_INSTALLMENT

                    install_open_bid_price = trade_data[ticker]['open_bid_price'] * CLOSE_INSTALLMENT
                    install_open_ask_price = trade_data[ticker]['open_ask_price'] * CLOSE_INSTALLMENT
                    install_close_bid_price = close_bid * close_quantity
                    install_close_ask_price = close_ask * close_quantity

                    trade_data[ticker]['close_bid_price'] += trade_data[ticker][
                                                                 'open_bid_price'] * CLOSE_INSTALLMENT
                    trade_data[ticker]['close_ask_price'] += trade_data[ticker][
                                                                 'open_ask_price'] * CLOSE_INSTALLMENT
                    trade_data[ticker]['close_quantity'] += close_quantity

                open_profit = install_close_bid_price - install_open_bid_price
                close_profit = install_open_ask_price - install_close_ask_price

                open_fee = install_open_bid_price * UPBIT_FEE + install_open_ask_price * BINANCE_FEE
                close_fee = install_close_bid_price * UPBIT_FEE + install_close_ask_price * BINANCE_FEE
                total_fee = open_fee + close_fee

                # 손익 갱신
                get_ticker_profit(trade_data, open_profit, close_profit, total_fee, ticker)
                remain_bid_balance['balance'] += install_open_bid_price

                upbit_market = 'KRW-' + ticker
                upbit_side = 'ask'
                upbit_price = install_close_bid_price  ## 매도시에는 사용 안함
                upbit_quantity = close_quantity
                binance_market = ticker + 'USDT'
                binance_side = 'bid'
                binance_quantity = close_quantity

                # 주문 로직
                # upbit.spot_order(upbit_market, upbit_side, upbit_price, upbit_quantity)
                # binance.futures_order(binance_market, binance_side, binance_quantity)

                message = (f"POSITION_CLOSE|{ticker}"
                           f"|P_OPEN_GIMP|{position_data[ticker]['position_gimp']}|P_CLOSE_GIMP|{close_gimp}"
                           f"|GIMP_GAP|{round(close_gimp - position_data[ticker]['position_gimp'], 2)}"
                           f"|C_INSTALL|{position_data[ticker]['close_install_count']}|O_INSTALL|{position_data[ticker]['open_install_count']}"
                           f"|C_PROFIT|{trade_data[ticker]['trade_profit']}|T_PROFIT|{trade_data[ticker]['total_profit']}"
                           f"|TRD_QUANTITY|{close_quantity}|TOT_QUANTITY|{trade_data[ticker]['total_quantity']}"
                           f"|BALANCE|{round(remain_bid_balance['balance'], 2)}")
                close_message_list.append(message)

                if position_data[ticker]['close_install_count'] * CLOSE_INSTALLMENT == 1:
                    # 종료 시점 데이터 갱신
                    update_close_position_data(ticker, position_data)
                    update_close_trade_data(ticker, trade_data)

                    update_open_check_data(ticker, check_data, open_gimp, open_bid, open_ask)
                    update_close_check_data(ticker, check_data, close_gimp, close_bid, close_ask)

    for message in open_message_list:
        logging.info(message)
        await util.send_to_telegram("🔵진입\n" + message)

    for message in close_message_list:
        logging.info(message)
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
    trade_data[ticker].update({"open_bid_price": 0, "open_ask_price": 0,
                               "close_bid_price": 0, "close_ask_price": 0,
                               "open_quantity": 0, "close_quantity": 0, "total_quantity": 0,"trade_profit": 0})

def update_close_position_data(ticker, position_data):
    position_data[ticker].update({"position": 0, "close_count": 0, "position_gimp_accum": 0,
                                  "open_install_count": 0, "close_install_count": 0})

def get_ticker_profit(trade_data, open_profit, close_profit, total_fee, ticker):
    total_profit = round(open_profit + close_profit - total_fee, 2)
    trade_data[ticker].update({"trade_profit": total_profit})
    trade_data[ticker]['profit_count'] += 1
    trade_data[ticker]['total_profit'] += trade_data[ticker]['trade_profit']

    return trade_data
