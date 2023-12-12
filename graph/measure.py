import os
import datetime
import graphUtil

def get_measure_ticker():
    check_data = {}
    trade_data = {}
    position_data = {}
    measure_ticker = {}

    lines = graphUtil.load_history_data()
    btc_open_gap = 0

    for line in lines:
        try:
            split_data = line.split('|')
            date_time = split_data[0].split('[INFO')[0]
            ticker = split_data[1]
            open_gap = float(split_data[3])
            open_data = split_data[4].split('/')
            open_bid = float(open_data[0].replace(',', '')) ## 매수 평단가
            open_ask = float(open_data[1].replace(',', '')) ## 매도(숏) 평단가
            close_gap = float(split_data[6])
            close_data = split_data[7].split('/')
            close_bid = float(close_data[0].replace(',', '')) ## 매도(매수 종료) 평단가
            close_ask = float(close_data[1].replace(',', '')) ## 매수(매도(숏) 종료) 평단가
        except:
            continue

        ## 데이터 값 초기화
        if ticker not in check_data:
            check_data[ticker] = {"open_gap": open_gap, "open_bid": open_bid, "open_ask": open_ask,
                                        "close_gap": close_gap, "close_bid": close_bid, "close_aks": close_ask,
                                  "front_open_gap": open_gap, "front_close_gap": close_gap}
        if ticker not in position_data:
            position_data[ticker] = {"open_count": 0, "open_check_gap": 0, "position": 0, "position_gap": 0,
                                    "close_count": 0, "position_gap_accum": 0, "installment_count": 0}

        if open_gap > close_gap and open_gap - close_gap > 1.0:
            continue


        if open_gap < check_data[ticker]['open_gap']:
            # open_gap 이 Update 되면 close_gap은 그 시점으로 gap 수정
            #print(f"{date_time} {ticker}|CURR|{open_gap}|CHECK|{check_data[ticker]['open_gap']} OPEN 갱신")

            check_data[ticker].update({"open_gap": open_gap, "open_bid": open_bid, "open_ask": open_ask})
            check_data[ticker].update({"close_gap": close_gap, "close_bid": close_bid, "close_aks": close_ask})


        ## Close 고점 계산
        if close_gap > check_data[ticker]['close_gap']:
            # Close 고점 데이터 갱신
            check_data[ticker].update({"close_gap": close_gap, "close_bid": close_bid, "close_aks": close_ask})

        close_diff_gap = check_data[ticker]['close_gap'] - check_data[ticker]['open_gap']

        if close_diff_gap > 1.3:
            ## 종료 시점 금액 계산
            # 종료 시점 데이터 갱신
            check_data[ticker].update({"open_gap": open_gap, "open_bid": open_bid, "open_ask": open_ask})
            check_data[ticker].update({"close_gap": close_gap, "close_bid": close_bid, "close_aks": close_ask})
            position_data[ticker]['open_count'] += 1

            measure_ticker[ticker] = {"units": []}

            if len(measure_ticker) > 10:
                continue

    for ticker in measure_ticker:
        print(f"{ticker}")

    return measure_ticker