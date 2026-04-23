import traceback
import util
import logging
from consts import *
from order_execution import execute_close_order

async def compare_price_close_order(
        orderbook_check,
        exchange_data,
        remain_bid_balance,
        check_data,
        trade_data,
        position_data,
        position_ticker_count,
        order_flag
):
    """
            프리미엄을 계산하여 각 거래소 거래 주문을 요청한다.
            orderbook_check         :
            exchange_data           :
            remain_bid_balance      :
            check_data              :
            trade_data              :
            position_data           :
            acc_ticker_data         :
            position_ticker_count   :
            order_flag              :
    """
    close_message_list = []

    for ticker in orderbook_check:
        try:
            # 가격 정보가 없으면 pass
            if orderbook_check[ticker]['Binance'] is None or orderbook_check[ticker]['Upbit'] is None:
                continue

            open_bid = orderbook_check[ticker]['Upbit']['balance_ask_average']
            close_bid = orderbook_check[ticker]['Upbit']['balance_bid_average']
            open_ask = orderbook_check[ticker]['Binance']['balance_bid_average']
            close_ask = orderbook_check[ticker]['Binance']['balance_ask_average']
            open_bid_btc = orderbook_check['BTC']['Upbit']['balance_ask_average']
            open_ask_btc = orderbook_check['BTC']['Binance']['balance_bid_average']

            # 가격이 없는 친구들 PASS
            if open_bid == 0 or close_bid == 0 or open_ask == 0 or close_ask == 0 or open_bid_btc == 0 or open_ask_btc == 0:
                continue

            open_gimp = open_bid / open_ask * 100 - 100
            close_gimp = close_bid / close_ask * 100 - 100

            if position_data[ticker]['position'] == 1:
                # 진입 중일 떄
                close_gimp_gap = position_data[ticker]['target_grid']
                
                # 종료 Trailing Stop 추적
                if 'close_max_gimp' in position_data[ticker] and position_data[ticker]['close_max_gimp'] != 0:
                    if close_gimp > position_data[ticker]['close_max_gimp']:
                        position_data[ticker]['close_max_gimp'] = close_gimp
                        position_data[ticker]['close_stop_gimp'] = close_gimp - CLOSE_TS_GRID
                        position_data[ticker]['close_ts_count'] = 0

                    if close_gimp < position_data[ticker]['close_stop_gimp']:
                        position_data[ticker]['close_ts_count'] += 1

                # 손절

                if close_gimp - position_data[ticker]['position_gimp'] < -0.3:
                    if open_gimp - close_gimp > CURR_GIMP_GAP:
                        continue

                    position_data[ticker]['close_limit_count'] += 1

                    # elif close_gimp - position_data[ticker]['position_gimp'] > 1:
                    #    position_data[ticker]['close_limit_count'] += 1


                # 진입 종료 조건 확인
                if (close_gimp - position_data[ticker]['position_gimp'] > close_gimp_gap
                        or (order_flag['close'] == 1 and ticker == order_flag['ticker'])
                        or position_data[ticker]['close_limit_count'] >= 5
                        or position_data[ticker]['close_ts_count'] >= CLOSE_TS_COUNT):
                    # 종료 Trailing Stop 로직 추가
                    if 'close_max_gimp' not in position_data[ticker] or position_data[ticker]['close_max_gimp'] == 0:
                        position_data[ticker]['close_max_gimp'] = close_gimp
                        position_data[ticker]['close_stop_gimp'] = close_gimp - CLOSE_TS_GRID
                        position_data[ticker]['close_ts_count'] = 0
                        continue

                    # 분할 종료 계산
                    if close_gimp - position_data[ticker]['position_gimp'] > CLOSE_GIMP_GAP:
                        close_installment = CLOSE_INSTALLMENT + 1
                    else:
                        close_installment = CLOSE_INSTALLMENT

                    # 익절 분할 횟수 Count 도달하지 않을 시
                    if (position_data[ticker]['close_install_count'] + 1) * close_installment < 1:
                        upbit_quantity = round(trade_data[ticker]['upbit_total_quantity'] * close_installment, exchange_data[ticker]['quantity_precision'])
                        binance_quantity = round(trade_data[ticker]['binance_total_quantity'] * close_installment, exchange_data[ticker]['quantity_precision'])

                        if close_ask * binance_quantity < TETHER * exchange_data[ticker]['min_notional']:
                            position_data[ticker]['close_install_count'] += 1
                            logging.info(f"SKIP|{ticker}|주문금액적음|{open_ask * binance_quantity:,}원|MIN_NOTIONAL|{TETHER * exchange_data[ticker]['min_notional']:,}원")
                            continue

                        order_success, order_result = await execute_close_order(
                            ticker,
                            close_bid,
                            close_ask,
                            upbit_quantity,
                            binance_quantity,
                        )

                        if not order_success:
                            message = f'{ticker} 종료 실패 {round(position_data[ticker]["position_gimp"], 3)}%-{round(close_gimp, 3)}%\n'
                            message += 'UPBIT 주문❌, ' if order_result['uuid'] == 0 else 'UPBIT 주문✅, '
                            message += 'BINANCE 주문❌' if order_result['orderId'] == 0 else 'BINANCE 주문✅'
                            await util.send_to_telegram(message)
                            continue

                        logging.info(f"CHECK_ORDER_RESULT|{order_result}")
                        remain_bid_balance['balance'] += order_result['upbit_price'] * order_result['upbit_quantity']
                        order_close_gimp = round(
                            order_result['upbit_price'] / order_result['binance_price'] * 100 - 100, 3)

                        position_data[ticker]['close_limit_count'] = 0
                        position_data[ticker]['close_install_count'] += 1

                        trade_data[ticker]['close_bid_price_acc'] += order_result['upbit_price'] * order_result['upbit_quantity']
                        trade_data[ticker]['close_ask_price_acc'] += order_result['binance_price'] * order_result['binance_quantity']
                        trade_data[ticker]['upbit_close_quantity'] += order_result['upbit_quantity']
                        trade_data[ticker]['binance_close_quantity'] += order_result['binance_quantity']

                        # 메세지 저장
                        message = (f"{ticker} 분할 종료\n"
                                   f"진입종료김프: {position_data[ticker]['position_gimp']}%|{order_close_gimp}%({round(order_close_gimp - position_data[ticker]['position_gimp'], 3)}%)\n"
                                   f"분할매수매도: {position_data[ticker]['open_install_count']}|{position_data[ticker]['close_install_count']}\n"
                                   f"요청주문김프: {round(close_gimp, 3)}%|{round(order_close_gimp, 3)}%\n"
                                   f"슬리피지: {round(order_result['upbit_price'] / close_bid * 100 - 100, 3)}%|{round(order_result['binance_price'] / close_ask * 100 - 100, 3)}%\n"
                                   f"잔액: {round(remain_bid_balance['balance'], 2):,}원\n"
                                   f"고정환율: {TETHER:,}원\n")
                        close_message_list.append(message)
                    # 익절 분할 횟수 Count 도달할 시 계산 로직 변경
                    elif (position_data[ticker]['close_install_count'] + 1) * close_installment >= 1:
                        # 마지막 남은 개수 한 번에 종료
                        upbit_quantity = trade_data[ticker]['upbit_total_quantity'] - trade_data[ticker]['upbit_close_quantity']
                        binance_quantity = round(trade_data[ticker]['binance_total_quantity'] - trade_data[ticker]['binance_close_quantity'], exchange_data[ticker]['quantity_precision'])

                        order_success, order_result = await execute_close_order(
                            ticker,
                            close_bid,
                            close_ask,
                            upbit_quantity,
                            binance_quantity,
                        )

                        if not order_success:
                            message = f'{ticker} 종료 실패 {round(position_data[ticker]["position_gimp"], 3)}%-{round(close_gimp, 3)}%\n'
                            message += 'UPBIT 주문❌, ' if order_result['uuid'] == 0 else 'UPBIT 주문✅, '
                            message += 'BINANCE 주문❌' if order_result['orderId'] == 0 else 'BINANCE 주문✅'
                            await util.send_to_telegram(message)
                            continue

                        logging.info(f"CHECK_ORDER_RESULT|{order_result}")
                        remain_bid_balance['balance'] += order_result['upbit_price'] * order_result['upbit_quantity']
                        order_close_gimp = round(
                            order_result['upbit_price'] / order_result['binance_price'] * 100 - 100, 2)

                        position_data[ticker]['close_limit_count'] = 0
                        position_data[ticker]['close_install_count'] += 1
                        position_ticker_count['count'] -= 1

                        trade_data[ticker]['close_bid_price_acc'] += order_result['upbit_price'] * order_result[
                            'upbit_quantity']
                        trade_data[ticker]['close_ask_price_acc'] += order_result['binance_price'] * order_result[
                            'binance_quantity']
                        trade_data[ticker]['upbit_close_quantity'] += order_result['upbit_quantity']
                        trade_data[ticker]['binance_close_quantity'] += order_result['binance_quantity']

                        # 최종 수익 계산 로직
                        upbit_fee = trade_data[ticker]['open_bid_price_acc'] * UPBIT_FEE + trade_data[ticker][
                            'open_ask_price_acc'] * UPBIT_FEE
                        binance_fee = trade_data[ticker]['close_bid_price_acc'] * BINANCE_FEE + trade_data[ticker][
                            'close_ask_price_acc'] * BINANCE_FEE

                        upbit_profit = trade_data[ticker]['close_bid_price_acc'] - trade_data[ticker]['open_bid_price_acc'] - upbit_fee
                        binance_profit = trade_data[ticker]['open_ask_price_acc'] - trade_data[ticker]['close_ask_price_acc'] - binance_fee

                        trade_data[ticker]['trade_profit'] = round(upbit_profit + binance_profit, 2)
                        trade_data[ticker]['total_profit'] += trade_data[ticker]['trade_profit']
                        position_data[ticker]['profit_count'] += 1
                        position_data[ticker]['target_grid'] = 0

                        # 메세지 저장
                        message = (f"{ticker} 종료\n"
                                   f"진입종료김프:{position_data[ticker]['position_gimp']}%|{order_close_gimp}%({round(order_close_gimp - position_data[ticker]['position_gimp'], 3)}%)\n"
                                   f"거래손익: UPBIT({round(upbit_profit, 2):,}원) + BINANCE({round(binance_profit, 2):,}원) = {trade_data[ticker]['trade_profit']:,}원\n"
                                   f"수익률: {round(trade_data[ticker]['trade_profit'] / (BALANCE * 2) * 100, 3)}%\n"
                                   f"분할매수매도: {position_data[ticker]['open_install_count']}|{position_data[ticker]['close_install_count']}\n"
                                   f"요청주문김프: {round(close_gimp, 3)}%|{round(order_close_gimp, 3)}%\n"
                                   f"슬리피지: {round(order_result['upbit_price'] / close_bid * 100 - 100, 3)}%|{round(order_result['binance_price'] / close_ask * 100 - 100, 3)}%\n"
                                   f"요청가격: {round(close_bid, 2):,}원|{round(close_ask, 2):,}원\n"
                                   f"주문가격: {round(order_result['upbit_price'], 2):,}원|{round(order_result['binance_price'], 2):,}원\n"
                                   f"진입누적가격: {round(trade_data[ticker]['open_bid_price_acc'], 2):,}원|{round(trade_data[ticker]['open_ask_price_acc'], 2):,}원\n"
                                   f"종료누적가격: {round(trade_data[ticker]['close_bid_price_acc'], 2):,}원|{round(trade_data[ticker]['close_ask_price_acc'], 2):,}원\n"
                                   f"종료수량: {order_result['upbit_quantity']}|{order_result['binance_quantity']}\n"
                                   f"총진입수량: {trade_data[ticker]['upbit_total_quantity']}|{trade_data[ticker]['binance_total_quantity']}\n"
                                   f"잔액: {round(remain_bid_balance['balance'], 2):,}원\n"
                                   f"고정환율: {TETHER:,}원")
                        close_message_list.append(message)
                        order_flag = {"open": 0, "close": 0, "ticker": 0}
                        util.put_order_flag(order_flag)
                        util.put_profit_data(ticker, position_data[ticker]['position_gimp'], order_close_gimp,
                                             trade_data[ticker]['trade_profit'], BALANCE)

                        # 현재 시점으로 데이터 갱신
                        check_data[ticker] = {
                            "open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                            "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask
                        }

                        # 포지션 데이터 초기화
                        position_data[ticker].update({
                            "open_install_count": 0, "close_install_count": 0, "acc_open_install_count": 0,
                            "position": 0, "position_gimp": 0, "position_gimp_acc": [], "position_gimp_acc_weight": [],
                            "open_timestamp": 0, "open_limit_count": 0, "close_limit_count": 0,
                            "target_grid": 0, "open_ts_count": 0, "close_ts_count": 0,
                            "open_min_gimp": 0, "open_stop_gimp": 0, "close_max_gimp": 0, "close_stop_gimp": 0
                        })

                        # profit_count, total_profit 제외하고 값 갱신
                        trade_data[ticker].update({
                            "open_bid_price_acc": 0, "open_ask_price_acc": 0,
                            "close_bid_price_acc": 0, "close_ask_price_acc": 0,
                            "upbit_total_quantity": 0, "upbit_close_quantity": 0,
                            "binance_total_quantity": 0, "binance_close_quantity": 0, "trade_profit": 0
                        })

                        logging.info(f'종료 데이터 초기화 (check, position, trade)')
        except Exception as e:
            logging.info(f"CloseOrder 오류|{e}|{traceback.format_exc()}")

    for message in close_message_list:
        logging.info(f"POSITION_CLOSE|{message}")
        await util.send_to_telegram("🔴" + message)
