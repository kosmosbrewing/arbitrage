import util
import logging
import asyncio
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
        if open_bid >= open_ask:
            open_gimp = round((open_bid - open_ask) / open_ask * 100, 2)
        elif open_ask > open_bid:
            open_gimp = round((open_ask - open_bid) / open_bid * 100, 2) * -1

        if close_bid >= close_ask:
            close_gimp = round((close_bid - close_ask) / close_ask * 100, 2)
        elif close_ask > close_bid:
            close_gimp = round((close_ask - close_bid) / close_bid * 100, 2) * -1

        if open_bid_btc >= open_ask_btc:
            btc_open_gimp = round((open_bid_btc - open_ask_btc) / open_ask_btc * 100, 2)
        elif open_ask_btc > open_bid_btc:
            btc_open_gimp = round((open_ask_btc - open_bid_btc) / open_bid_btc * 100, 2) * -1

        curr_gimp_gap = open_gimp - close_gimp if open_gimp > close_gimp else 0

        ## 데이터 값 초기화
        if ticker not in check_data:
            check_data[ticker] = {"open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                                  "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask}
        if ticker not in position_data:
            position_data[ticker] = {"open_install_count": 0, "close_install_count": 0, "position": 0,
                                     "position_gimp": 0, "position_gimp_accum": 0, "accum_open_install_count": 0}
        if ticker not in trade_data:
            trade_data[ticker] = {"open_bid_price_accum": 0, "open_ask_price_accum": 0, "close_bid_price_accum": 0,
                                  "close_ask_price_accum": 0, "upbit_close_quantity": 0, "binance_close_quantity": 0,
                                  "upbit_total_quantity": 0, "binance_total_quantity": 0, "trade_profit": 0,
                                  "profit_count": 0, "total_profit": 0}

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

        if remain_bid_balance['balance'] < 0:
            accum_ticker_count[ticker].append(0)
            continue

        ## 포지션 진입 로직
        if open_gimp < check_data[ticker]['open_gimp']:
            # open_gimp 이 Update 되면 close_gimp은 그 시점으로 gap 수정
            check_data[ticker].update({"open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                                    "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask})
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
            open_quantity = round(BALANCE * OPEN_INSTALLMENT / open_bid, exchange_data[ticker]['quantity_precision'])

            if open_quantity == 0:
                logging.info(f"SKIP|UPBIT|{ticker}|진입수량적음|OPEN_BID|{open_quantity}|PRECISION|{exchange_data[ticker]['quantity_precision']}")
                continue

            upbit_open_bid_price = open_bid * open_quantity

            if remain_bid_balance['balance'] - upbit_open_bid_price < 0:
                logging.info(f"SKIP|{ticker}|잔고부족|REMAIN_BID|{remain_bid_balance['balance']}|OPEN_BID|{upbit_open_bid_price}")
                accum_ticker_count[ticker].append(0)
                continue

            order_lock = asyncio.Lock()
            check_order_lock = asyncio.Lock()
            order_result = {'uuid': 0, 'orderId': 0, 'upbit_price': 0, 'upbit_quantity': 0, 'binance_price': 0, 'binance_quantity': 0}

            await asyncio.gather(
                ## UPBIT : ticker, side, price, quantity, order_result, lock
                ## BINANCE : ticker, side, quantity, order_result, lock
                upbit.spot_order('KRW-'+ticker, 'bid', upbit_open_bid_price, 0, order_result, order_lock),
                binance.futures_order(ticker+'USDT', 'ask', open_quantity, order_result, order_lock)
            )

            if order_result['uuid'] == 0 or order_result['orderId'] == 0:
                message = ''
                message += 'UPBIT 주문 실패 ❌, ' if order_result['uuid'] == 0 else 'UPBIT 주문 성공 ✅, '
                message += 'BINANCE 주문 실패 ❌' if order_result['uuid'] == 0 else 'BINANCE 주문 성공 ✅'
                await util.send_to_telegram(message)
                continue

            async with order_lock:
                await asyncio.gather(
                    upbit.check_order(order_result, check_order_lock),
                    binance.check_order(ticker+'USDT', order_result, check_order_lock)
                )

            async with check_order_lock:
                logging.info(f"CHECK_ORDER_RESULT|{order_result}")
                remain_bid_balance['balance'] -= order_result['upbit_price']
                order_result['binance_price'] = order_result['binance_price'] * exchange_data['USD']['base']

                if order_result['upbit_price'] >= order_result['binance_price']:
                    order_open_gimp = round((order_result['upbit_price'] - order_result['binance_price']) / order_result['binance_price'] * 100, 2)
                else:
                    order_open_gimp = round((order_result['binance_price'] - order_result['upbit_price']) / order_result['upbit_price'] * 100, 2) * -1

                ## 진입 성공 시 포지션 데이터 Update
                position_data[ticker]['open_install_count'] += 1
                position_data[ticker]['accum_open_install_count'] += 1
                position_data[ticker]['position_gimp_accum'] += order_open_gimp
                position_data[ticker]['position_gimp'] = round(position_data[ticker]['position_gimp_accum'] / position_data[ticker]['open_install_count'], 2)
                position_data[ticker]['position'] = 1
                position_data[ticker]['close_count'] = 0

                if position_data[ticker]['open_install_count'] == 1:
                    position_ticker_count['count'] += 1

                trade_data[ticker]['upbit_total_quantity'] += order_result['upbit_quantity']
                trade_data[ticker]['binance_total_quantity'] += order_result['binance_quantity']
                trade_data[ticker]['open_bid_price_accum'] += order_result['upbit_price']
                trade_data[ticker]['open_ask_price_accum'] += order_result['binance_price']

                # 텔레그램 전송 및 로깅 데이터
                message = (f"{ticker}"
                           f"|요청주문김프|{open_gimp}/{order_open_gimp}"
                           f"|누적김프|{position_data[ticker]['position_gimp']}"
                           f"|평균김프|{round(average_open_gimp, 2)}"
                           f"|BTC김프|{round(btc_open_gimp, 2)}"
                           f"|변동성|{sum(accum_ticker_count[ticker])}"
                           f"|분할매수매도|{position_data[ticker]['open_install_count']}/{position_data[ticker]['close_install_count']}"
                           f"|요청가격|{open_bid}/{open_ask}"
                           f"|주문가격|{order_result['upbit_price']}/{order_result['binance_price']}"
                           f"|진입누적가격|{trade_data[ticker]['open_bid_price_accum']}/{trade_data[ticker]['open_ask_price_accum']}"
                           f"|종료누적가격|{trade_data[ticker]['close_ask_price_accum']}/{trade_data[ticker]['close_ask_price_accum']}"
                           f"|요청수량|{open_quantity}/{open_quantity}"
                           f"|주문수량|{order_result['upbit_quantity']}/{order_result['binance_quantity']}"
                           f"|총거래수량|{trade_data[ticker]['upbit_total_quantity']}/{trade_data[ticker]['binance_total_quantity']}"
                           f"|잔액|{round(remain_bid_balance['balance'], 2)}"
                           f"|환율|{exchange_data['USD']['base']}")
                # 주문 로직
                open_message_list.append(message)

        ## 저점 진입 김프 <-> 현재 포지션 종료 김프 계산하여 수익 변동성 확인
        if close_gimp - check_data[ticker]['open_gimp'] > OPEN_GIMP_GAP:
            check_data[ticker].update({"open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                                       "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask})
            accum_ticker_count[ticker].append(1)
        else:
            accum_ticker_count[ticker].append(0)

        ## 진입 중일 떄
        if position_data[ticker]['position'] == 1:
            ## 진입 종료 조건 확인
            if close_gimp - position_data[ticker]['position_gimp'] > CLOSE_GIMP_GAP:
                order_lock = asyncio.Lock()
                check_order_lock = asyncio.Lock()
                order_result = {'uuid': 0, 'orderId': 0, 'upbit_price': 0, 'upbit_quantity': 0, 'binance_price': 0, 'binance_quantity': 0}

                ## 익절 분할 횟수 Count 도달하지 않을 시
                if position_data[ticker]['close_install_count'] * CLOSE_INSTALLMENT != 1:
                    upbit_quantity = round(trade_data[ticker]['upbit_total_quantity'] * CLOSE_INSTALLMENT, exchange_data[ticker]['quantity_precision'])
                    binance_quantity = round(trade_data[ticker]['binance_total_quantity'] * CLOSE_INSTALLMENT, exchange_data[ticker]['quantity_precision'])

                    ## UPBIT : ticker, side, price, quantity, order_result, lock
                    ## BINANCE : ticker, side, quantity, order_result, lock
                    await asyncio.gather(
                        upbit.spot_order('KRW-' + ticker, 'ask', 0, upbit_quantity, order_result, order_lock),
                        binance.futures_order(ticker + 'USDT', 'bid', binance_quantity, order_result, order_lock)
                    )

                    if order_result['uuid'] == 0 or order_result['orderId'] == 0:
                        message = ''
                        message += 'UPBIT 주문 실패 ❌, ' if order_result['uuid'] == 0 else 'UPBIT 주문 성공 ✅, '
                        message += 'BINANCE 주문 실패 ❌' if order_result['uuid'] == 0 else 'BINANCE 주문 성공 ✅'
                        await util.send_to_telegram(message)
                        continue

                    async with order_lock:
                        await asyncio.gather(
                            upbit.check_order(order_result, check_order_lock),
                            binance.check_order(ticker + 'USDT', order_result, check_order_lock)
                        )

                    async with check_order_lock:
                        logging.info(f"CHECK_ORDER_RESULT|{order_result}")
                        remain_bid_balance['balance'] += order_result['upbit_price']
                        order_result['binance_price'] = order_result['binance_price'] * exchange_data['USD']['base']

                        if order_result['upbit_price'] >= order_result['binance_price']:
                            order_close_gimp = round((order_result['upbit_price'] - order_result['binance_price']) / order_result['binance_price'] * 100, 2)
                        else:
                            order_close_gimp = round(
                                (order_result['binance_price'] - order_result['upbit_price']) / order_result['upbit_price'] * 100, 2) * -1

                        position_data[ticker]['close_install_count'] += 1

                        trade_data[ticker]['close_bid_price_accum'] += order_result['upbit_price']
                        trade_data[ticker]['close_ask_price_accum'] += order_result['binance_price']
                        trade_data[ticker]['upbit_close_quantity'] += order_result['upbit_quantity']
                        trade_data[ticker]['binance_close_quantity'] += order_result['binance_quantity']

                        ## 메세지 저장
                        message = (f"{ticker}"
                                   f"|진입종료김프|{position_data[ticker]['position_gimp']}<->{order_close_gimp}"
                                   f"|김프차이|{round(order_close_gimp - position_data[ticker]['position_gimp'], 2)}|"
                                   f"|요청주문김프|{close_gimp}/{order_close_gimp}"
                                   f"|분할매수매도|{position_data[ticker]['open_install_count']}/{position_data[ticker]['close_install_count']}"
                                   f"|거래총이익|{trade_data[ticker]['trade_profit']}/{trade_data[ticker]['total_profit']}"
                                   f"|요청가격|{close_bid}/{close_ask}"
                                   f"|주문가격|{order_result['upbit_price']}/{order_result['binance_price']}"
                                   f"|진입누적가격|{trade_data[ticker]['open_bid_price_accum']}/{trade_data[ticker]['open_ask_price_accum']}"
                                   f"|종료누적가격|{trade_data[ticker]['close_ask_price_accum']}/{trade_data[ticker]['close_ask_price_accum']}"
                                   f"|요청수량[{upbit_quantity}/{binance_quantity}]"
                                   f"|주문수량|{order_result['upbit_quantity']}/{order_result['binance_quantity']}"
                                   f"|총거래수량|{trade_data[ticker]['upbit_total_quantity']}/{trade_data[ticker]['binance_total_quantity']}"
                                   f"|잔액[{round(remain_bid_balance['balance'], 2)}]"
                                   f"|환율[{exchange_data['USD']['base']}]")
                        close_message_list.append(message)

                ## 익절 분할 횟수 Count 도달할 시 계산 로직 변경
                elif position_data[ticker]['close_install_count'] * CLOSE_INSTALLMENT == 1:
                    ## 마지막 남은 개수 한 번에 종료
                    upbit_quantity = round(trade_data[ticker]['upbit_total_quantity'] - trade_data[ticker]['upbit_close_quantity'], exchange_data[ticker]['quantity_precision'])
                    binance_quantity = round(trade_data[ticker]['binance_total_quantity'] - trade_data[ticker]['binance_close_quantity'], exchange_data[ticker]['quantity_precision'])

                    ## UPBIT : ticker, side, price, quantity, order_result, lock
                    ## BINANCE : ticker, side, quantity, order_result, lock
                    await asyncio.gather(
                        upbit.spot_order('KRW-'+ticker, 'ask', 0, upbit_quantity, order_result, order_lock),
                        binance.futures_order(ticker+'USDT', 'bid', binance_quantity, order_result, order_lock)
                    )
                    ## 주문 제대로 안들어갈 시
                    if order_result['uuid'] == 0 or order_result['orderId'] == 0:
                        message = ''
                        message += 'UPBIT 주문 실패 ❌, ' if order_result['uuid'] == 0 else 'UPBIT 주문 성공 ✅, '
                        message += 'BINANCE 주문 실패 ❌' if order_result['uuid'] == 0 else 'BINANCE 주문 성공 ✅'
                        await util.send_to_telegram(message)
                        continue
                    
                    ## 주문 확인
                    async with order_lock:
                        await asyncio.gather(
                            upbit.check_order(order_result, check_order_lock),
                            binance.check_order(ticker+'USDT', order_result, check_order_lock)
                        )

                    async with check_order_lock:
                        logging.info(f"CHECK_ORDER_RESULT|{order_result}")
                        remain_bid_balance['balance'] += order_result['upbit_price']
                        order_result['binance_price'] = order_result['binance_price'] * exchange_data['USD']['base']

                        if order_result['upbit_price'] >= order_result['binance_price']:
                            order_close_gimp = round((order_result['upbit_price'] - order_result['binance_price']) / order_result['binance_price'] * 100, 2)
                        else:
                            order_close_gimp = round((order_result['binance_price'] - order_result['upbit_price']) / order_result['upbit_price'] * 100, 2) * -1

                        position_data[ticker]['close_install_count'] += 1
                        position_ticker_count['count'] -= 1

                        trade_data[ticker]['close_bid_price_accum'] += order_result['upbit_price']
                        trade_data[ticker]['close_ask_price_accum'] += order_result['binance_price']
                        trade_data[ticker]['upbit_close_quantity'] += order_result['upbit_quantity']
                        trade_data[ticker]['binance_close_quantity'] += order_result['binance_quantity']

                        ## 최종 수익 계산 로직
                        open_profit = trade_data[ticker]['close_bid_price_accum'] - trade_data[ticker]['open_bid_price_accum']
                        close_profit = trade_data[ticker]['open_ask_price_accum'] - trade_data[ticker]['close_ask_price_accum']
                        open_fee = trade_data[ticker]['open_bid_price_accum'] * UPBIT_FEE + trade_data[ticker]['open_ask_price_accum'] * BINANCE_FEE
                        close_fee = trade_data[ticker]['close_bid_price_accum'] * UPBIT_FEE + - trade_data[ticker]['close_ask_price_accum'] * BINANCE_FEE

                        trade_data[ticker]['trade_profit'] = round(open_profit + close_profit - open_fee - close_fee, 2)
                        trade_data[ticker]['total_profit'] += trade_data[ticker]['trade_profit']
                        trade_data[ticker]['profit_count'] += 1

                        ## 메세지 저장
                        message = (f"{ticker}"
                                   f"|진입종료김프|{position_data[ticker]['position_gimp']}<->{order_close_gimp}"
                                   f"|김프차이|{round(order_close_gimp - position_data[ticker]['position_gimp'], 2)}|"
                                   f"|요청주문김프|{close_gimp}/{order_close_gimp}"
                                   f"|분할매수매도|{position_data[ticker]['open_install_count']}/{position_data[ticker]['close_install_count']}"
                                   f"|거래총이익|{trade_data[ticker]['trade_profit']}/{trade_data[ticker]['total_profit']}"
                                   f"|요청가격|{close_bid}/{close_ask}"
                                   f"|주문가격|{order_result['upbit_price']}/{order_result['binance_price']}"
                                   f"|진입누적가격|{trade_data[ticker]['open_bid_price_accum']}/{trade_data[ticker]['open_ask_price_accum']}"
                                   f"|종료누적가격|{trade_data[ticker]['close_ask_price_accum']}/{trade_data[ticker]['close_ask_price_accum']}"
                                   f"|요청수량[{upbit_quantity}/{binance_quantity}]"
                                   f"|주문수량|{order_result['upbit_quantity']}/{order_result['binance_quantity']}"
                                   f"|총거래수량|{trade_data[ticker]['upbit_total_quantity']}/{trade_data[ticker]['binance_total_quantity']}"
                                   f"|잔액[{round(remain_bid_balance['balance'], 2)}]"
                                   f"|환율[{exchange_data['USD']['base']}]")
                        close_message_list.append(message)

                        # 현재 시점으로 데이터 갱신
                        check_data[ticker].update({
                            "open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                            "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask}
                        )
                        # 포지션 데이터 초기화
                        position_data[ticker].update(
                            {"open_install_count": 0, "close_install_count": 0, "position": 0,
                                "position_gimp": 0, "position_gimp_accum": 0, "accum_open_install_count": 0}
                        )
                        ## profit_count, total_profit 제외하고 값 갱신
                        trade_data[ticker].update(
                            {"open_bid_price_accum": 0, "open_ask_price_accum": 0, "close_bid_price_accum": 0, "close_ask_price_accum": 0,
                                "upbit_close_quantity": 0, "binance_close_quantity": 0, "upbit_total_quantity": 0, "binance_total_quantity": 0,
                             "trade_profit": 0}
                        )
                        logging.info(f'종료 check_data 초기화|{check_data[ticker]}')
                        logging.info(f'종료 position_data 초기화|{position_data[ticker]}')
                        logging.info(f'종료 trade_data 초기화|{trade_data[ticker]}')

    for message in open_message_list:
        logging.info(f"POSITION_OPEN|{message}", )
        message.replace("|", "\n")
        await util.send_to_telegram("🔵진입\n" + message)

    for message in close_message_list:
        logging.info(f"POSITION_CLOSE|{message}" )
        message.replace("|", "\n")
        await util.send_to_telegram("🔴탈출\n" + message)
