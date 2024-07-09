import util
import backTestUtil
from backTestConsts import *
from collections import deque

def data_initailize(ticker, position_data, trade_data, accum_ticker_count, accum_ticker_data):
    if ticker not in position_data:
        # open_install_count =  분할매수 횟수
        # position =  현재 진입해있는지 (포지션 잡았는지) 업비트롱, 바이낸스숏
        # position_gimp = 현재 포지션 진입해있는 김프 값
        # open_install_count =  분할매수 횟수
        # close_count = 손절로직 동작 체크 횟수
        position_data[ticker] = {"open_install_count": 0, "close_install_count": 0, "position": 0, "position_gimp": 0,
                                 "position_gimp_accum": [], "close_count": 0, "accum_open_install_count": 0,
                                 "position_gimp_accum_weight": []
                                 }
    if ticker not in trade_data:
        # open_bid_price =  포지션 진입 업비트 현물 매수 총 금액
        # open_ask_price = 포지션 종료 업비트 현물 매도 총 금액
        # close_bid_price = 포지션 종료 업비트 선물 매수 총 금액 (숏 종료)
        # close_ask_price = 포지션 진입 업비트 선물 매도 총 금액 (숏 진입)
        # open_quantity = 거래 수량
        # trade_profit = 거래 손익
        # profit_count = 손익 횟수
        # total_profit = 총 손익
        trade_data[ticker] = {"open_bid_price": 0, "open_ask_price": 0, "close_bid_price": 0, "close_ask_price": 0,
                              "open_quantity": 0, "close_quantity": 0, "total_quantity": 0,
                              "trade_profit": 0, "profit_count": 0, "total_profit": 0}

    if ticker not in accum_ticker_count:
        queue = deque(maxlen=FRONT_OPEN_COUNT)
        accum_ticker_count[ticker] = queue
        accum_ticker_count[ticker].append(0)

    if ticker not in accum_ticker_data:
        queue = deque(maxlen=FRONT_AVERAGE_COUNT)
        accum_ticker_data[ticker] = queue


def get_measure_ticker():
    check_data = {}
    trade_data = {}
    position_data = {}
    accum_ticker_count = {}
    accum_ticker_data = {}
    position_ticker_count = 0

    #util.load_remain_position(position_data, trade_data)

    lines = backTestUtil.load_history_data()
    remain_bid_balance = BALANCE

    for line in lines:
        try:
            split_data = line.split('|')
            date_time = split_data[0].split('[INFO')[0]
            ticker = split_data[1]
            open_gimp = float(split_data[3])
            open_data = split_data[4].split('/')
            open_bid = float(open_data[0].replace(',', ''))  # 매수 평단가
            open_ask = float(open_data[1].replace(',', ''))  # 매도(숏) 평단가
            close_gimp = float(split_data[6])
            close_data = split_data[7].split('/')
            close_bid = float(close_data[0].replace(',', ''))  # 매도(매수 종료) 평단가
            close_ask = float(close_data[1].replace(',', ''))  # 매수(매도(숏) 종료) 평단가
            btc_open_gimp = float(split_data[9])
        except:
            continue

        curr_gimp_gap = open_gimp - close_gimp if open_gimp > close_gimp else 0


        # 데이터 값 초기화
        if ticker not in check_data:
            check_data[ticker] = {"open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                                  "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask,
                                  "front_open_gimp": open_gimp}

        data_initailize(ticker, position_data, trade_data, accum_ticker_count, accum_ticker_data)

        accum_ticker_data[ticker].append(close_gimp)
        average_open_gimp = sum(accum_ticker_data[ticker]) / len(accum_ticker_data[ticker])

        if remain_bid_balance < 0:
            accum_ticker_count[ticker].append(0)
            continue

        # 현재 김프가 저점일 때
        if open_gimp < check_data[ticker]['open_gimp']:
            # open_gimp 이 Update 되면 close_gimp은 그 시점으로 gap 수정
            update_open_check_data(ticker, check_data, open_gimp, open_bid, open_ask)
            update_close_check_data(ticker, check_data, close_gimp, close_bid, close_ask)
            open_install_count = position_data[ticker]['open_install_count']

            # 진입/종료 갭차이 너무 많이 들어가면 들어가지 않음
            if curr_gimp_gap > CURR_GIMP_GAP:
                accum_ticker_count[ticker].append(0)
                continue

            if position_ticker_count >= POSITION_TICKER_COUNT:
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
            open_quantity = BALANCE * OPEN_INSTALLMENT / trade_price  # 분할 진입을 위해서
            open_bid_price = open_bid * open_quantity + trade_data[ticker]['open_bid_price']
            open_ask_price = open_ask * open_quantity + trade_data[ticker]['open_ask_price']

            # 잔고 부족할 시 PASS
            if remain_bid_balance - open_bid * open_quantity > 0:
                remain_bid_balance -= open_bid * open_quantity
            else:
                accum_ticker_count[ticker].append(0)
                continue

            update_open_position_data(ticker, position_data, open_gimp)
            trade_data[ticker].update({"open_bid_price": open_bid_price, "open_ask_price": open_ask_price})

            upbit_market = 'KRW-' + ticker
            upbit_side = 'bid'
            upbit_price = trade_data[ticker]['open_bid_price']
            upbit_quantity = trade_data[ticker]['open_quantity']

            #upbit.spot_order(upbit_market, upbit_side, upbit_price, upbit_quantity)

            binance_market = ticker+'USDT'
            binance_side = 'ask'
            binance_quantity = trade_data[ticker]['open_quantity']
            #binance.futures_order(binance_market, binance_side, binance_quantity)

            trade_data[ticker].update({"open_quantity": open_quantity})
            total_quantity = open_quantity + trade_data[ticker]['total_quantity']

            if position_data[ticker]['open_install_count'] > 1:
                trade_data[ticker].update({"total_quantity": total_quantity})
            else:
                position_ticker_count += 1
                trade_data[ticker].update({"total_quantity": open_quantity})

            ## 주문 로직
            print(f"{date_time}{ticker}|진입|P_OPEN_GIMP|{position_data[ticker]['position_gimp']}"
                f"|C_CLOSE_GIMP|{close_gimp}|C_OPEN_GIMP|{open_gimp}|AVG_OPEN_GIMP|{round(average_open_gimp, 2)}"
                f"|BTC_OPEN_GIMP|{round(btc_open_gimp, 2)}|OPEN_COUNT|{sum(accum_ticker_count[ticker])}"
                f"|INSATLL|{position_data[ticker]['open_install_count']}|BID_PRICE|{trade_data[ticker]['open_bid_price']}"
                f"|TRD_QUANTITY|{trade_data[ticker]['open_quantity']}|TOT_QUANTITY|{trade_data[ticker]['total_quantity']}"
                f"|BALANCE|{round(remain_bid_balance, 2)}")

        # 저점 진입 김프 <-> 현재 포지션 종료 김프 계산하여 수익 변동성 확인
        if close_gimp - check_data[ticker]['open_gimp'] > OPEN_GIMP_GAP:
            update_open_check_data(ticker, check_data, open_gimp, open_bid, open_ask)
            update_close_check_data(ticker, check_data, close_gimp, close_bid, close_ask)
            accum_ticker_count[ticker].append(1)
        else:
            accum_ticker_count[ticker].append(0)

        if position_data[ticker]['position'] == 1:
            # 익절
            close_diff_gimp = close_gimp - position_data[ticker]['position_gimp']
            if close_diff_gimp > CLOSE_GIMP_GAP:
                position_data[ticker]['close_install_count'] += 1

                # 종료 시점 금액 계산
                total_quantity = trade_data[ticker]['total_quantity']

                # 익절 분할 횟수 Count 도달할 시 계산 로직 변경
                if position_data[ticker]['close_install_count'] * CLOSE_INSTALLMENT == 1:
                    close_quantity = total_quantity - trade_data[ticker]['close_quantity']

                    install_open_bid_price = trade_data[ticker]['open_bid_price'] - trade_data[ticker]['close_bid_price']
                    install_open_ask_price = trade_data[ticker]['open_ask_price'] - trade_data[ticker]['close_ask_price']
                    install_close_bid_price = close_bid * close_quantity
                    install_close_ask_price = close_ask * close_quantity

                    trade_data[ticker]['close_bid_price'] += trade_data[ticker]['open_bid_price'] - trade_data[ticker]['close_bid_price']
                    trade_data[ticker]['close_ask_price'] += trade_data[ticker]['open_ask_price'] - trade_data[ticker]['close_bid_price']
                    trade_data[ticker]['close_quantity'] += close_quantity
                    position_ticker_count -= 1
                # 익절 분할 횟수 Count 도달하지 않을 시
                else:
                    close_quantity = total_quantity * CLOSE_INSTALLMENT

                    install_open_bid_price = trade_data[ticker]['open_bid_price'] * CLOSE_INSTALLMENT
                    install_open_ask_price = trade_data[ticker]['open_ask_price'] * CLOSE_INSTALLMENT
                    install_close_bid_price = close_bid * close_quantity
                    install_close_ask_price = close_ask * close_quantity

                    trade_data[ticker]['close_bid_price'] += trade_data[ticker]['open_bid_price'] * CLOSE_INSTALLMENT
                    trade_data[ticker]['close_ask_price'] += trade_data[ticker]['open_ask_price'] * CLOSE_INSTALLMENT
                    trade_data[ticker]['close_quantity'] += close_quantity

                open_profit = install_close_bid_price - install_open_bid_price
                close_profit = install_open_ask_price - install_close_ask_price

                open_fee = install_open_bid_price * UPBIT_FEE + install_open_ask_price * BINANCE_FEE
                close_fee = install_close_bid_price * UPBIT_FEE + install_close_ask_price * BINANCE_FEE
                total_fee = open_fee + close_fee

                # 손익 갱신
                get_ticker_profit(trade_data, open_profit, close_profit, total_fee, ticker)
                remain_bid_balance += install_open_bid_price

                #print(f"잔고|{remain_bid_balance}|매수금액|{trade_data[ticker]['open_bid_price']}|익절금액|{trade_data[ticker]['close_bid_price']}")


                upbit_market = 'KRW-' + ticker
                upbit_side = 'ask'
                upbit_price = install_close_bid_price # 매도시에는 사용 안함
                upbit_quantity = close_quantity
                binance_market = ticker + 'USDT'
                binance_side = 'bid'
                binance_quantity = close_quantity

                # 주문 로직
                #upbit.spot_order(upbit_market, upbit_side, upbit_price, upbit_quantity)
                #binance.futures_order(binance_market, binance_side, binance_quantity)

                print(
                    f"{date_time}{ticker}|익절|P_OPEN_GIMP|{position_data[ticker]['position_gimp']}|P_CLOSE_GIMP|{close_gimp}"
                    f"|GIMP_GAP|{round(close_gimp - position_data[ticker]['position_gimp'], 2)}"
                    f"|C_INSTALL|{position_data[ticker]['close_install_count']}|O_INSTALL|{position_data[ticker]['open_install_count']}"
                    f"|C_PROFIT|{trade_data[ticker]['trade_profit']}|T_PROFIT|{trade_data[ticker]['total_profit']}"
                    f"|TRD_QUANTITY|{close_quantity}|TOT_QUANTITY|{trade_data[ticker]['total_quantity']}"
                    f"|BALANCE|{round(remain_bid_balance, 2)}")

                if position_data[ticker]['close_install_count'] * CLOSE_INSTALLMENT == 1:
                    # 종료 시점 데이터 갱신
                    update_close_position_data(ticker, position_data)
                    update_close_trade_data(ticker, trade_data)

                    update_open_check_data(ticker, check_data, open_gimp, open_bid, open_ask)
                    update_close_check_data(ticker, check_data, close_gimp, close_bid, close_ask)

    for ticker in trade_data:
        if trade_data[ticker]['profit_count'] >= 1:
            print(f"{date_time}{ticker}|손익|OPEN_COUNT|{position_data[ticker]['accum_open_install_count']}"
              f"|PROFIT_COUNT|{trade_data[ticker]['profit_count']}"
              f"|T_PROFIT|{trade_data[ticker]['total_profit']}")

    for ticker in position_data:
        if position_data[ticker]['position'] == 1:
            print(f"{date_time}{ticker}|포지션유지|P_OPEN_GIMP|{position_data[ticker]['position_gimp']}"
                  f"|AVG_OPEN_GIMP|{round(average_open_gimp, 2)}|OPEN_COUNT|{sum(accum_ticker_count[ticker])}"
                  f"|INSATLL|{position_data[ticker]['open_install_count']}"
                  f"|BID_PRICE|{trade_data[ticker]['open_bid_price']}|BALANCE|{round(remain_bid_balance, 2)}")

    util.put_remain_position(position_data, trade_data)

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

if __name__ == "__main__":
    get_measure_ticker()