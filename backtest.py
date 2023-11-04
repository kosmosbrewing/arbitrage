import os
import datetime
from consts import *
from collections import deque

def load_history_data():
    # 오늘 날짜 가져오기
    today = datetime.date.today()
    # 하루 전 날짜 계산
    yesterday = today - datetime.timedelta(days=1)
    yesterday = yesterday.strftime("%Y%m%d")

    if ENV == 'real':
        history_file_path = '/root/arbitrage/log/premium_data_'+yesterday
    elif ENV == 'local':
        history_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/premium_data_'+yesterday
        history_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/premium_data'

    if os.path.exists(history_file_path):
        print(history_file_path)
        with open(history_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    else:
        print(f"{history_file_path} 파일이 존재하지 않습니다.")

    return lines

def data_initailize(ticker, position_data, trade_data, accum_ticker_count, accum_ticker_data):
    if ticker not in position_data:
        # installment_count =  분할매수 횟수
        # position =  현재 진입해있는지 (포지션 잡았는지) 업비트롱, 바이낸스숏
        # position_gimp = 현재 포지션 진입해있는 김프 값
        # installment_count =  분할매수 횟수
        # close_count = 손절로직 동작 체크 횟수
        position_data[ticker] = {"installment_count": 0, "position": 0, "position_gimp": 0,
                                 "position_gimp_accum": 0, "close_count": 0}
    if ticker not in trade_data:
        # open_bid_amount =  포지션 진입 업비트 현물 매수 총 금액
        # open_ask_amount = 포지션 종료 업비트 현물 매도 총 금액
        # close_bid_amount = 포지션 종료 업비트 선물 매수 총 금액 (숏 종료)
        # close_ask_amount = 포지션 진입 업비트 선물 매도 총 금액 (숏 진입)
        # trade_quantity = 거래 수량
        # trade_profit = 거래 손익
        # profit_count = 손익 횟수
        # total_profit = 총 손익
        
        trade_data[ticker] = {"open_bid_amount": 0, "open_ask_amount": 0, "close_bid_amount": 0, "close_ask_amount": 0,
                              "trade_quantity": 0, "trade_profit": 0, "profit_count": 0, "total_profit": 0}
    if ticker not in accum_ticker_count:
        queue = deque(maxlen=FRONT_OPEN_COUNT)
        accum_ticker_count[ticker] = queue
        accum_ticker_count[ticker].append(0)

    if ticker not in accum_ticker_data:
        queue = deque(maxlen=FRONT_AVERAGE_COUNT)
        accum_ticker_data[ticker] = queue

def update_open_check_data(ticker, check_data, open_gimp, open_bid, open_ask):
    check_data[ticker].update({"open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask})

def update_close_check_data(ticker, check_data, close_gimp, close_bid, close_ask):
    check_data[ticker].update({"close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask})

def update_open_position_data(ticker, position_data, open_gimp):
    position_data[ticker]['installment_count'] += 1
    position_data[ticker]['position_gimp_accum'] += open_gimp
    position_data[ticker]['position_gimp'] = round(position_data[ticker]['position_gimp_accum']
                                                  / position_data[ticker]['installment_count'], 2)
    position_data[ticker]['position'] = 1
    position_data[ticker]['close_count'] = 0

def update_close_trade_data(ticker, trade_data):
    trade_data[ticker].update({"open_bid_amount": 0, "open_ask_amount": 0,
                               "close_bid_amount": 0, "close_ask_amount": 0,
                               "trade_quantity": 0, "trade_profit": 0})

def update_close_position_data(ticker, position_data):
    position_data[ticker].update({"position": 0, "close_count": 0, "installment_count": 0, "position_gimp_accum": 0})

def get_ticker_profit(trade_data, ticker):
    open_profit = trade_data[ticker]['close_bid_amount'] - trade_data[ticker]['open_bid_amount']
    close_profit = trade_data[ticker]['open_ask_amount'] - trade_data[ticker]['close_ask_amount']

    open_fee = trade_data[ticker]['open_bid_amount'] * UPBIT_FEE + trade_data[ticker]['open_ask_amount'] * BINANCE_FEE
    close_fee = trade_data[ticker]['close_bid_amount'] * UPBIT_FEE + trade_data[ticker]['close_ask_amount'] * BINANCE_FEE

    total_fee = open_fee + close_fee
    total_profit = round(open_profit + close_profit - total_fee, 2)
    trade_data[ticker].update({"trade_profit": total_profit})
    trade_data[ticker]['profit_count'] += 1
    trade_data[ticker]['total_profit'] += trade_data[ticker]['trade_profit']

    return trade_data

def get_measure_ticker():
    check_data = {}
    trade_data = {}
    position_data = {}
    measure_ticker = {}
    accum_ticker_count = {}
    accum_ticker_data = {}

    lines = load_history_data()
    remain_bid_balance = BALANCE

    for line in lines:
        split_data = line.split('|')
        date_time = split_data[0].split('[INFO')[0]
        ticker = split_data[1]
        open_gimp = float(split_data[5])
        open_data = split_data[6].split('/')
        open_bid = float(open_data[0].replace(',', '')) ## 매수 평단가
        open_ask = float(open_data[1].replace(',', '')) ## 매도(숏) 평단가
        close_gimp = float(split_data[8])
        close_data = split_data[9].split('/')
        close_bid = float(close_data[0].replace(',', '')) ## 매도(매수 종료) 평단가
        close_ask = float(close_data[1].replace(',', '')) ## 매수(매도(숏) 종료) 평단가

        curr_gimp_gap = open_gimp - close_gimp if open_gimp > close_gimp else 0

        ## 데이터 값 초기화
        if ticker not in check_data:
            check_data[ticker] = {"open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                                  "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask,
                                  "front_open_gimp": open_gimp, "front_close_gimp": close_gimp}

        data_initailize(ticker, position_data, trade_data, accum_ticker_count, accum_ticker_data)

        ## 진입/종료 갭차이 너무 많이 들어가면 들어가지 않음
        if curr_gimp_gap > CURR_GIMP_GAP:
            continue
        else:
            accum_ticker_data[ticker].append(open_gimp)
            average_open_gimp = sum(accum_ticker_data[ticker]) / len(accum_ticker_data[ticker])

        ## 현재 김프가 저점일 때
        if open_gimp < check_data[ticker]['open_gimp']:
            # open_gimp 이 Update 되면 close_gimp은 그 시점으로 gap 수정
            update_open_check_data(ticker, check_data, open_gimp, open_bid, open_ask)
            update_close_check_data(ticker, check_data, close_gimp, close_bid, close_ask)

            ## 진입 로직
            if sum(accum_ticker_count[ticker]) > OPEN_GIMP_COUNT and open_gimp - average_open_gimp < FRONT_AVERAGE_GIMP:
                ## 분할 진입 시 더 저점인지 확인
                if position_data[ticker]['installment_count'] > 1 and position_data[ticker]['position_gimp'] > open_gimp:
                    continue

                # 매수/매도(숏) 기준 가격 잡기 (개수 계산)
                trade_price = open_bid if open_bid > open_ask else open_ask
                trade_quantity = BALANCE * OPEN_INSTALLMENT / trade_price  ## 분할 진입을 위해서
                remain_bid_balance -= open_bid * trade_quantity
                open_bid_amount = open_bid * trade_quantity + trade_data[ticker]['open_bid_amount']
                open_ask_amount = open_ask * trade_quantity + trade_data[ticker]['open_ask_amount']
                trade_quantity += trade_data[ticker]['trade_quantity']

                # 잔고 부족할 시 PASS
                # if remain_bid_balance < 0 or remain_ask_balance < 0:
                #if open_bid_amount > BALANCE:
                #    continue
                if remain_bid_balance < 0:
                    print(f"{date_time} {ticker} | 진입 시도, 잔고 없음")
                    continue

                update_open_position_data(ticker, position_data, open_gimp)
                trade_data[ticker].update({"open_bid_amount": open_bid_amount, "open_ask_amount": open_ask_amount,
                                           "trade_quantity": trade_quantity})
                ### 주문 로직
                print(f"{date_time} {ticker}|진입|CHK|{position_data[ticker]['position_gimp']}|OPEN|{open_gimp}|CLOSE|{close_gimp}"
                    f"|GAP|{round(close_gimp - open_gimp, 2)}|PROFIT|{trade_data[ticker]['total_profit']}|BALANCE|{remain_bid_balance}|AVG|{average_open_gimp}")
                print(f"{date_time} {ticker}|{position_data[ticker]}")
                print(f"{date_time} {ticker}|{trade_data[ticker]}")

        ## 저점 진입 김프 <-> 현재 포지션 종료 김프 계산하여 수익 변동성 확인
        if close_gimp - check_data[ticker]['open_gimp'] > OPEN_GIMP_GAP:
            update_open_check_data(ticker, check_data, open_gimp, open_bid, open_ask)
            update_close_check_data(ticker, check_data, close_gimp, close_bid, close_ask)
            accum_ticker_count[ticker].append(1)

            print(f"{date_time} {ticker}|갭포착|CHK|{position_data[ticker]['position_gimp']}|OPEN|{open_gimp}|"
                  f"CLOSE|{close_gimp}|OPEN_COUNT|{sum(accum_ticker_count[ticker])}|AVG|{average_open_gimp}")
        else:
            accum_ticker_count[ticker].append(0)

        if position_data[ticker]['position'] == 1:
            ## 익절
            close_diff_gimp = close_gimp - position_data[ticker]['position_gimp']
            if close_diff_gimp > CLOSE_GIMP_GAP:
                # 종료 시점 금액 계산
                trade_quantity = trade_data[ticker]['trade_quantity']
                close_bid_amount = close_bid * trade_quantity
                close_ask_amount = close_ask * trade_quantity

                trade_data[ticker].update({"close_bid_amount": close_bid_amount, "close_ask_amount": close_ask_amount})
                get_ticker_profit(trade_data, ticker)
                remain_bid_balance += trade_data[ticker]['open_bid_amount']

                print(f"{date_time} {ticker}|익절|OPEN|{position_data[ticker]['position_gimp']}|CLOSE|{close_gimp}"
                      f"|GAP|{round(close_gimp - position_data[ticker]['position_gimp'], 2)}|PROFIT|{trade_data[ticker]['trade_profit']}"
                      f"|TOTAL_PROFIT|{trade_data[ticker]['total_profit']}")
                print(f"{date_time} {ticker}|{position_data[ticker]}")
                print(f"{date_time} {ticker}|{trade_data[ticker]}")

                update_close_position_data(ticker, position_data)
                update_close_trade_data(ticker, trade_data)

                # 종료 시점 데이터 갱신
                update_open_check_data(ticker, check_data, open_gimp, open_bid, open_ask)
                update_close_check_data(ticker, check_data, close_gimp, close_bid, close_ask)

                measure_ticker[ticker] = {"units": []}

            check_stop_loss_gimp = position_data[ticker]['position_gimp'] - close_gimp
            ## 손절 포착
            if check_stop_loss_gimp > STOP_LOSS_GIMP_GAP:
                position_data[ticker]['close_count'] += 1
                print(f"{date_time} {ticker}|손절포착|OPEN|{position_data[ticker]['position_gimp']}|"
                      f"CLOSE|{close_gimp}|GAP|{round(close_gimp - position_data[ticker]['position_gimp'], 2)}|"
                      f"CLOSE_COUNT|{position_data[ticker]['close_count']}")
            ## 손절 로직
            if position_data[ticker]['close_count'] >= STOP_LOSS_COUNT:
                trade_quantity = trade_data[ticker]['trade_quantity']
                close_bid_amount = close_bid * trade_quantity
                close_ask_amount = close_ask * trade_quantity

                trade_data[ticker].update({"close_bid_amount": close_bid_amount, "close_ask_amount": close_ask_amount})
                get_ticker_profit(trade_data, ticker)

                # 종료 시점 데이터 갱신
                update_open_check_data(ticker, check_data, open_gimp, open_bid, open_ask)
                update_close_check_data(ticker, check_data, close_gimp, close_bid, close_ask)
                
                update_close_position_data(ticker, position_data)
                update_close_trade_data(ticker, trade_data)

                print(f"{date_time} {ticker}|손절|OPEN|{position_data[ticker]['position_gimp']}|CLOSE|{close_gimp}"
                      f"|GAP|{round(close_gimp - position_data[ticker]['position_gimp'], 2)}|PROFIT|{trade_data[ticker]['total_profit']}")

                print(f"{date_time} {ticker}|{check_data[ticker]}")
                print(f"{date_time} {ticker}|{trade_data[ticker]}")
                measure_ticker[ticker] = {"units": []}

    for ticker in measure_ticker:
        print(f"{date_time} {ticker}|손익 발생!")
        print(f"{date_time} {ticker}|{position_data[ticker]}")
        print(f"{date_time} {ticker}|{trade_data[ticker]}")

    for ticker in position_data:
        if position_data[ticker]['position'] == 1:
            print(f"{date_time} {ticker}|포지션 유지중|OPEN|{position_data[ticker]['position_gimp']}")
            print(f"{date_time} {ticker}|{trade_data[ticker]}")

if __name__ == "__main__":
    get_measure_ticker()