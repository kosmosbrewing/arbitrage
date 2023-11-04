import os
import datetime
from consts import *

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
        history_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/premium_data_20231103'

    if os.path.exists(history_file_path):
        print(history_file_path)
        with open(history_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    else:
        print(f"{history_file_path} 파일이 존재하지 않습니다.")

    return lines

def get_measure_ticker():
    check_data = {}
    trade_data = {}
    position_data = {}
    measure_ticker = {}

    lines = load_history_data()
    btc_open_gap = 0
    max_count = 0
    front_count = 0
    remain_bid_balance = BALANCE

    for line in lines:
        split_data = line.split('|')
        date_time = split_data[0].split('[INFO')[0]
        ticker = split_data[1]
        open_gap = float(split_data[5])
        open_data = split_data[6].split('/')
        open_bid = float(open_data[0].replace(',', '')) ## 매수 평단가
        open_ask = float(open_data[1].replace(',', '')) ## 매도(숏) 평단가
        close_gap = float(split_data[8])
        close_data = split_data[9].split('/')
        close_bid = float(close_data[0].replace(',', '')) ## 매도(매수 종료) 평단가
        close_ask = float(close_data[1].replace(',', '')) ## 매수(매도(숏) 종료) 평단가
        usd = float(split_data[15])

        ## 데이터 값 초기화
        if ticker not in check_data:
            check_data[ticker] = {"open_gap": open_gap, "open_bid": open_bid, "open_ask": open_ask,
                                        "close_gap": close_gap, "close_bid": close_bid, "close_aks": close_ask,
                                  "front_open_gap": open_gap, "front_close_gap": close_gap}
        if ticker not in position_data:
            position_data[ticker] = {"open_count": 0, "position": 0, "position_gap": 0,
                                    "close_count": 0, "position_gap_accum": 0, "installment_count": 0}
        if ticker not in trade_data:
            trade_data[ticker] = {"open_bid_amount": 0, "open_ask_amount": 0, "close_bid_amount": 0, "close_ask_amount": 0,
                                  "trade_quantity": 0, "trade_profit": 0, "profit_count": 0, "total_profit": 0}

        if open_gap > close_gap and open_gap - close_gap > CURR_GAP:
            continue

        if position_data[ticker]['open_count'] > front_count:
            max_count = position_data[ticker]['open_count']
            max_ticker = ticker
        front_count = position_data[ticker]['open_count']

        if open_gap < check_data[ticker]['open_gap']:
            # open_gap 이 Update 되면 close_gap은 그 시점으로 gap 수정
            check_data[ticker].update({"open_gap": open_gap, "open_bid": open_bid, "open_ask": open_ask})
            check_data[ticker].update({"close_gap": close_gap, "close_bid": close_bid, "close_aks": close_ask})

            ## 진입
            if position_data[ticker]['open_count'] >= MEASURE_OPEN_COUNT and max_ticker == ticker:
                #if position_data[ticker]['installment_count'] == 0 and open_switch == 1:
                #    continue
                if position_data[ticker]['installment_count'] > 1:
                    #if open_ticker != ticker or position_data[ticker]['position_gap'] > open_gap:
                    if position_data[ticker]['position_gap'] > open_gap:
                        continue

                   # 매수/매도(숏) 기준 가격 잡기 (개수 계산)
                trade_price = open_bid if open_bid > open_ask else open_ask
                trade_quantity = BALANCE * OPEN_INSTALLMENT / trade_price  ## 분할 진입을 위해서
                #trade_quantity = BALANCE * OPEN_INSTALLMENT * (position_data[ticker]['installment_count'] + 1) / trade_price  ## 분할 진입을 위해서
                remain_bid_balance -= float(open_bid * trade_quantity)
                open_bid_amount = float(open_bid * trade_quantity) + trade_data[ticker]['open_bid_amount']
                open_ask_amount = float(open_ask * trade_quantity) + trade_data[ticker]['open_ask_amount']
                trade_quantity += trade_data[ticker]['trade_quantity']

                # 잔고 부족할 시 PASS
                # if remain_bid_balance < 0 or remain_ask_balance < 0:
                #if open_bid_amount > BALANCE:
                #    continue
                if remain_bid_balance < 0:
                    print(f"{date_time} {ticker} | 진입 시도, 잔고 없음")
                    continue

                '''
                if position_data[ticker]['position_gap'] - btc_open_gap > POSITION_BTC_GAP:
                    print(f"{date_time} {ticker}|김프 너무 과열|진입 데이터 초기화")
                    position_data[ticker]['open_count'] = 0
                    max_count = 0
                    continue'''

                position_data[ticker]['installment_count'] += 1
                position_data[ticker]['position_gap_accum'] += open_gap
                position_data[ticker]['position_gap'] = round(position_data[ticker]['position_gap_accum']
                                                              / position_data[ticker]['installment_count'], 2)
                position_data[ticker]['position'] = 1
                position_data[ticker]['close_count'] = 0
                trade_data[ticker].update({"open_bid_amount": open_bid_amount, "open_ask_amount": open_ask_amount,
                                           "trade_quantity": trade_quantity})
                open_switch = 1
                open_ticker = ticker
                # position_data['main_ticker'] = ticker

                ### 주문 로직
                print(f"{date_time} {ticker}|진입|CHK|{position_data[ticker]['position_gap']}|OPEN|{open_gap}|CLOSE|{close_gap}"
                    f"|GAP|{round(close_gap - open_gap, 2)}|PROFIT|{trade_data[ticker]['total_profit']}|BALANCE|{remain_bid_balance}")
                print(f"{date_time} {ticker}|{position_data[ticker]}")
                print(f"{date_time} {ticker}|{trade_data[ticker]}")

        ## 갭포착
        if close_gap - check_data[ticker]['open_gap'] > MEASURE_OPEN_GAP:
            position_data[ticker]['open_count'] += 1
            print(f"{date_time} {ticker}|갭포착|CHK|{check_data[ticker]['open_gap']}|OPEN|{open_gap}|"
                 f"CLOSE|{close_gap}|OPEN_COUNT|{position_data[ticker]['open_count']}")
            check_data[ticker].update({"open_gap": open_gap, "open_bid": open_bid, "open_ask": open_ask})
            check_data[ticker].update({"close_gap": close_gap, "close_bid": close_bid, "close_aks": close_ask})

        if position_data[ticker]['position'] == 1:
            ## 익절
            close_diff_gap = close_gap - position_data[ticker]['position_gap']
            if close_diff_gap > MEASURE_CLOSE_GAP:
                # 종료 시점 금액 계산
                trade_quantity = trade_data[ticker]['trade_quantity']
                close_bid_amount = float(close_bid * trade_quantity)
                close_ask_amount = float(close_ask * trade_quantity)
                trade_data[ticker].update({"close_bid_amount": close_bid_amount, "close_ask_amount": close_ask_amount})
                get_ticker_profit(trade_data, ticker)

                remain_bid_balance += trade_data[ticker]['open_bid_amount']

                print(f"{date_time} {ticker}|익절|OPEN|{position_data[ticker]['position_gap']}|CLOSE|{close_gap}"
                      f"|GAP|{round(close_gap - position_data[ticker]['position_gap'], 2)}|PROFIT|{trade_data[ticker]['trade_profit']}"
                      f"|TOTAL_PROFIT|{trade_data[ticker]['total_profit']}")
                print(f"{date_time} {ticker}|{position_data[ticker]}")
                print(f"{date_time} {ticker}|{trade_data[ticker]}")
                      
                # 종료 시점 데이터 갱신
                check_data[ticker].update({"open_gap": open_gap, "open_bid": open_bid, "open_ask": open_ask})
                check_data[ticker].update({"close_gap": close_gap, "close_bid": close_bid, "close_aks": close_ask})
                position_data[ticker].update({"open_count": 0, "position": 0,
                                              "installment_count": 0, "position_gap_accum": 0})
                trade_data[ticker].update({"open_bid_amount": 0, "open_ask_amount": 0,
                                           "close_bid_amount": 0, "close_ask_amount": 0,
                                           "trade_quantity": 0, "trade_profit": 0})
                open_switch = 1
                open_ticker = ticker
                measure_ticker[ticker] = {"units": []}

                #for ticker in position_data:
                #    position_data[ticker].update({"open_count": 0})

            check_stop_loss_gap = position_data[ticker]['position_gap'] - close_gap
            
            ## 손절
            if check_stop_loss_gap > MEASURE_STOP_LOSS:
                position_data[ticker]['close_count'] += 1
                print(f"{date_time} {ticker}|손절포착|OPEN|{position_data[ticker]['position_gap']}|"
                      f"CLOSE|{close_gap}|GAP|{round(close_gap - position_data[ticker]['position_gap'], 2)}|"
                      f"CLOSE_COUNT|{position_data[ticker]['close_count']}")

            if position_data[ticker]['close_count'] >= 3:
                trade_quantity = trade_data[ticker]['trade_quantity']
                close_bid_amount = float(close_bid * trade_quantity)
                close_ask_amount = float(close_ask * trade_quantity)
                trade_data[ticker].update({"close_bid_amount": close_bid_amount, "close_ask_amount": close_ask_amount})
                get_ticker_profit(trade_data, ticker)

                # 종료 시점 데이터 갱신
                check_data[ticker].update({"open_gap": open_gap, "open_bid": open_bid, "open_ask": open_ask})
                check_data[ticker].update({"close_gap": close_gap, "close_bid": close_bid, "close_aks": close_ask})
                position_data[ticker].update({"position": 0,
                                              "close_count": 0, "installment_count": 0, "position_gap_accum": 0})
                trade_data[ticker].update({"open_bid_amount": 0, "open_ask_amount": 0,
                                           "close_bid_amount": 0, "close_ask_amount": 0,
                                           "trade_quantity": 0, "trade_profit": 0})
                print(f"{date_time} {ticker}|손절|OPEN|{position_data[ticker]['position_gap']}|CLOSE|{close_gap}"
                      f"|GAP|{round(close_gap - position_data[ticker]['position_gap'], 2)}|PROFIT|{trade_data[ticker]['total_profit']}")
                open_switch = 1
                open_ticker = ticker

                # print(f"{date_time} {ticker}|{check_data[ticker]}")
                # print(f"{date_time} {ticker}|{trade_data[ticker]}")
                measure_ticker[ticker] = {"units": []}

    for ticker in measure_ticker:
        print(f"{date_time} {ticker}|손익 발생!")
        print(f"{date_time} {ticker}|{position_data[ticker]}")
        print(f"{date_time} {ticker}|{trade_data[ticker]}")

    for ticker in position_data:
        if position_data[ticker]['position'] == 1:
            print(f"{date_time} {ticker}|포지션 유지중|OPEN|{position_data[ticker]['position_gap']}")
            print(f"{date_time} {ticker}|{trade_data[ticker]}")
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

if __name__ == "__main__":
    get_measure_ticker()