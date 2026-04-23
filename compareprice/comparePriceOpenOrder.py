import traceback
import util
import logging
from datetime import datetime
from consts import *
from order_execution import execute_open_order

async def compare_price_open_order(
        orderbook_check,
        exchange_data,
        remain_bid_balance,
        check_data,
        trade_data,
        position_data,
        acc_ticker_count,
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

    open_message_list = []
    open_flag = 0
    close_mode = 0

    # 티거 데이터 비교
    for ticker in orderbook_check:
        try:
            if open_flag == 1:
                continue

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
            btc_open_gimp = open_bid_btc / open_ask_btc * 100 - 100

            """ 
                주문 조건
                잔고, 주문 플래그, 거래량 많은 티커, 슬리피지가 적은 티커, 진입 안한 티커, RSI 계산, Trailing Stop 등   
            """
            if remain_bid_balance['balance'] < 0:
                continue

            if order_flag['open'] == 0:
                if ticker not in exchange_data['upbit_top_ticker']:
                    continue

                # 진입 Trailing Stop 로직 추가
                if 'open_min_gimp' not in position_data[ticker] or position_data[ticker]['open_min_gimp'] == 0:
                    position_data[ticker]['open_min_gimp'] = open_gimp
                    position_data[ticker]['open_stop_gimp'] = open_gimp + OPEN_TS_GRID
                    position_data[ticker]['open_ts_count'] = 0

                if open_gimp < position_data[ticker]['open_min_gimp']:
                    position_data[ticker]['open_min_gimp'] = open_gimp
                    position_data[ticker]['open_stop_gimp'] = open_gimp + OPEN_TS_GRID
                    position_data[ticker]['open_ts_count'] = 0

                if open_gimp - close_gimp > CURR_GIMP_GAP:
                    continue

                if btc_open_gimp < open_gimp - 0.75:
                    continue

                # 분할 매수 X
                if position_data[ticker]['open_install_count'] != 0:
                    continue

                if position_data[ticker]['open_limit_count'] < OPEN_LIMIT_COUNT:
                    rsi_15_gap = exchange_data['upbit_15_rsi'][ticker] - exchange_data['binance_15_rsi'][ticker]
                    rsi_240_gap = exchange_data['upbit_240_rsi'][ticker] - exchange_data['binance_240_rsi'][ticker]

                    # 4시간 RSI 과매도 (급락일 때 PASS)
                    if exchange_data['upbit_240_rsi'][ticker] <= 35 and exchange_data['binance_240_rsi'][ticker] <= 35:
                        position_data[ticker]['open_limit_count'] = 0
                        continue

                    # 4시간 RSI 과매수, 방망이 길게 가져가기
                    elif exchange_data['upbit_240_rsi'][ticker] >= 65 and exchange_data['binance_240_rsi'][ticker] >= 65:
                        if rsi_15_gap > 0:
                            position_data[ticker]['open_limit_count'] = 0

                        if rsi_240_gap > -1 or rsi_15_gap > -1:
                            continue

                        close_mode = 0
                    else:
                        # 과매도 (급락일 때 PASS)
                        if exchange_data['upbit_15_rsi'][ticker] <= 35 and exchange_data['binance_15_rsi'][ticker] <= 35:
                            continue
                        # 과매수 일 때
                        elif exchange_data['upbit_15_rsi'][ticker] >= 65 and exchange_data['binance_15_rsi'][ticker] >= 65:
                            if rsi_15_gap > 0:
                                position_data[ticker]['open_limit_count'] = 0

                            if rsi_15_gap > -1:
                                continue
                        else:
                            if rsi_15_gap > 0:
                                position_data[ticker]['open_limit_count'] = 0

                            if rsi_15_gap > -3:
                                continue
                        if rsi_240_gap > 1.5:
                            close_mode = 1
                        else:
                            close_mode = 2

                    position_data[ticker]['open_limit_count'] += 1
                    continue
            #if position_data[ticker]['open_limit_count'] < OPEN_LIMIT_COUNT:
            #    continue

            if open_gimp > position_data[ticker]['open_stop_gimp']:
                position_data[ticker]['open_ts_count'] += 1

            if position_data[ticker]['open_ts_count'] < OPEN_TS_COUNT:
                continue

            elif order_flag['open'] == 1:
                if ticker != order_flag['ticker']:
                    continue
                if open_gimp > check_data[ticker]['open_gimp']:
                    continue
            elif order_flag['open'] == -1:
                continue

            open_installment = OPEN_INSTALLMENT

            # 매수/매도(숏) 기준 가격 잡기 (개수 계산)
            open_quantity = round(BALANCE * open_installment / (open_bid * LEVERAGE), exchange_data[ticker]['quantity_precision'])

            if open_quantity == 0 or open_ask * open_quantity < TETHER * exchange_data[ticker]['min_notional']:
                logging.info(f"SKIP|{ticker}|{round(open_gimp, 2)}%|진입수량적음|{open_quantity}|OPEN_INSTALL|{open_installment}|OPEN_BID|{open_bid}|PRECISION|{exchange_data[ticker]['quantity_precision']}")
                continue
            elif open_ask * open_quantity < TETHER * exchange_data[ticker]['min_notional']:
                logging.info(f"SKIP|{ticker}|{round(open_gimp, 2)}%|주문금액적음|{open_ask * open_quantity:,}원|MIN_NOTIONAL|{TETHER * exchange_data[ticker]['min_notional']:,}원")
                continue

            upbit_open_bid_price = open_bid * open_quantity * LEVERAGE

            if remain_bid_balance['balance'] - upbit_open_bid_price < 0:
                logging.info(f"SKIP|{ticker}|{round(open_gimp, 2)}%|잔고부족|REMAIN_BID|{remain_bid_balance['balance']}|OPEN_BID|{upbit_open_bid_price}")
                continue

            order_success, order_result = await execute_open_order(
                ticker,
                open_bid,
                open_ask,
                upbit_open_bid_price,
                open_quantity,
            )

            if not order_success:
                message = f'{ticker} 진입 실패 {round(open_gimp, 3)}%\n'
                message += 'UPBIT 주문❌, ' if order_result['uuid'] == 0 else 'UPBIT 주문✅, '
                message += 'BINANCE 주문❌' if order_result['orderId'] == 0 else 'BINANCE 주문✅'
                await util.send_to_telegram(message)
                continue

            logging.info(f"CHECK_ORDER_RESULT|{order_result}")
            remain_bid_balance['balance'] -= order_result['upbit_price'] * order_result['upbit_quantity']
            order_open_gimp = order_result['upbit_price'] / order_result['binance_price'] * 100 - 100

            # 진입 성공 시 포지션 데이터 Update
            if position_data[ticker]['open_install_count'] == 0:
                position_data[ticker]['open_timestamp'] = datetime.now().timestamp()
                position_ticker_count['count'] += 1

            position_data[ticker]['open_install_count'] += 1
            position_data[ticker]['acc_open_install_count'] += 1
            position_data[ticker]['position_gimp_acc'].append(order_open_gimp)
            position_data[ticker]['position_gimp_acc_weight'].append(open_installment)
            position_data[ticker]['open_limit_count'] = 0
            position_data[ticker]['open_ts_count'] = 0
            position_data[ticker]['open_min_gimp'] = 0
            position_data[ticker]['open_stop_gimp'] = 0

            if close_mode == 0:
                position_data[ticker]['target_grid'] = CLOSE_GIMP_GAP + 0.1
            elif close_mode == 1:
                position_data[ticker]['target_grid'] = CLOSE_GIMP_GAP - 0.1
            elif close_mode == 2:
                position_data[ticker]['target_grid'] = CLOSE_GIMP_GAP

            temp_gimp = 0
            for i in range(len(position_data[ticker]['position_gimp_acc_weight'])):
                weight = position_data[ticker]['position_gimp_acc_weight'][i] / sum(position_data[ticker]['position_gimp_acc_weight'])
                temp_gimp += position_data[ticker]['position_gimp_acc'][i] * weight
            position_data[ticker]['position_gimp'] = round(temp_gimp, 3)
            position_data[ticker]['position'] = 1
            position_data[ticker]['close_count'] = 0

            trade_data[ticker]['upbit_total_quantity'] += order_result['upbit_quantity']
            trade_data[ticker]['binance_total_quantity'] += order_result['binance_quantity']
            trade_data[ticker]['open_bid_price_acc'] += order_result['upbit_price'] * order_result['upbit_quantity']
            trade_data[ticker]['open_ask_price_acc'] += order_result['binance_price'] * order_result['binance_quantity']

            check_data[ticker].update({
                "open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask
            })

            # Telegram 주문 알림 데이터
            message = (f"{ticker} 진입\n"
                       f"요청주문김프: {round(open_gimp, 3)}%|{round(order_open_gimp, 3)}%\n"
                       f"목표종료: {round(order_open_gimp + position_data[ticker]['target_grid'],3)}%({round(position_data[ticker]['target_grid'],3)})%\n"
                       f"RSI: {round(exchange_data['upbit_15_rsi'][ticker], 2)}%|{round(exchange_data['binance_15_rsi'][ticker], 2)}%\n"
                       f"누적진입김프: {position_data[ticker]['position_gimp']}%\n"
                       f"BTC김프: {round(btc_open_gimp, 3)}%\n"
                       f"변동성: {acc_ticker_count[ticker]['open_count']}\n"
                       f"분할매수매도: {position_data[ticker]['open_install_count']}|{position_data[ticker]['close_install_count']}\n"
                       f"요청가격: {round(open_bid, 2):,}원/{round(open_ask, 2):,}원\n"
                       f"주문가격: {round(order_result['upbit_price'], 2):,}원|{round(order_result['binance_price'], 2):,}원\n"
                       f"슬리피지: {round(order_result['upbit_price'] / open_bid * 100 - 100, 3)}%|{round(order_result['binance_price'] / open_ask * 100 - 100, 3)}%\n"
                       f"진입누적가격: {round(trade_data[ticker]['open_bid_price_acc'], 2):,}원|{round(trade_data[ticker]['open_ask_price_acc'], 2):,}원\n"
                       f"종료누적가격: {round(trade_data[ticker]['close_ask_price_acc'], 2):,}원|{round(trade_data[ticker]['close_ask_price_acc'], 2):,}원\n"
                       f"진입수량: {order_result['upbit_quantity']}|{order_result['binance_quantity']}\n"
                       f"총진입수량: {trade_data[ticker]['upbit_total_quantity']}|{trade_data[ticker]['binance_total_quantity']}\n"
                       f"잔액: {round(remain_bid_balance['balance'], 2):,}원\n"
                       f"고정환율: {TETHER:,}원\n")

            open_message_list.append(message)
            util.put_order_flag(order_flag)
            open_flag = 1
        except Exception as e:
            logging.info(f"OpenOrder 오류|{e}|{traceback.format_exc()}")

    for message in open_message_list:
        logging.info(f"POSITION_OPEN|{message}")
        await util.send_to_telegram("🔵" + message)
