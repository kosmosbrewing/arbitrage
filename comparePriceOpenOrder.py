import traceback

import util
import logging
import asyncio
from datetime import datetime
from consts import *
from api import upbit, binance

async def compare_price_open_order(orderbook_check, exchange_data, remain_bid_balance, check_data, trade_data,
                                position_data, acc_ticker_count, acc_ticker_data, position_ticker_count):
    """ self.exchange_price 저장된 거래소별 코인정보를 비교하고 특정 (%)이상 갭발생시 알림 전달하는 함수 """
    open_message_list = []

    for ticker in orderbook_check:
        try:
            # 가격 정보가 없으면 pass
            if orderbook_check[ticker]['Upbit'] is None or orderbook_check[ticker]['Binance'] is None:
                continue

            open_bid = float(orderbook_check[ticker]['Upbit']['balance_ask_average'])
            close_bid = float(orderbook_check[ticker]['Upbit']['balance_bid_average'])

            open_ask = float(orderbook_check[ticker]['Binance']['balance_bid_average'])
            close_ask = float(orderbook_check[ticker]['Binance']['balance_ask_average'])

            open_bid_btc = float(orderbook_check['BTC']['Upbit']['balance_ask_average'])
            open_ask_btc = float(orderbook_check['BTC']['Binance']['balance_bid_average'])

            ## 가격이 없는 친구들 PASS
            if open_bid == 0 or close_bid == 0:
                continue
            if open_ask == 0 or close_ask == 0:
                continue
            if open_bid_btc == 0 or open_ask_btc == 0:
                continue

            open_gimp = round(open_bid / open_ask * 100 - 100, 3)
            close_gimp = round(close_bid / close_ask * 100 - 100, 3)
            btc_open_gimp = round(open_bid_btc / open_ask_btc * 100 - 100, 3)

            if remain_bid_balance['balance'] < 0:
                continue

            ## 포지션 진입 로직
            if open_gimp < check_data[ticker]['open_gimp']:
                # open_gimp 이 Update 되면 close_gimp은 그 시점으로 gap 수정
                check_data[ticker].update({
                    "open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                    "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask
                })

                if open_gimp - close_gimp > CURR_GIMP_GAP:
                    continue

                if position_data[ticker]['open_install_count'] == 0 and position_ticker_count['count'] < 3:
                    if position_data[ticker]['profit_count'] > 0 and open_gimp > position_data[ticker]['front_close_gimp'] - RE_OPEN_GIMP_GAP:
                        continue

                    if acc_ticker_count[ticker]['open_count'] <= OPEN_GIMP_COUNT:
                        continue

                    if acc_ticker_data[ticker]['fall_check'] == 0 or open_gimp > btc_open_gimp * BTC_GAP:
                        continue

                elif position_data[ticker]['open_install_count'] == 0 and position_ticker_count['count'] >= 3:
                    if acc_ticker_data[ticker]['fall_check'] == 0 or open_gimp > btc_open_gimp * BTC_GAP:
                        position_data[ticker]['open_limit_count'] = 0
                        continue

                    if open_gimp > position_ticker_count['open_gimp_limit']:
                        continue

                    position_data[ticker]['open_limit_count'] += 1

                    if position_data[ticker]['open_limit_count'] < 3 or position_ticker_count['count'] >= POSITION_TICKER_COUNT:
                        continue

                elif position_data[ticker]['open_install_count'] > 0:
                    if position_data[ticker]['position_gimp'] * INSTALL_WEIGHT < open_gimp:
                        continue

                ## 김프 별 분할 진입 가중치 다르게 설정 (승률에 따라서, 켈리 공식 참조)
                if open_gimp < -1.5:
                    OPEN_INSTALLMENT = 0.25
                elif -1.5 <= open_gimp < 0.5:
                    OPEN_INSTALLMENT = 0.2
                elif 0.5 <= open_gimp < 1.5:
                    OPEN_INSTALLMENT = 0.15
                elif 1.5 <= open_gimp < 2.5:
                    OPEN_INSTALLMENT = 0.1
                elif 2.5 <= open_gimp < 3.5:
                    if open_gimp < btc_open_gimp * 0.9:
                        OPEN_INSTALLMENT = 0.1
                    else:
                        OPEN_INSTALLMENT = 0.08
                elif 3.5 <= open_gimp:
                    if open_gimp < btc_open_gimp * 0.9:
                        OPEN_INSTALLMENT = 0.08
                    else:
                        OPEN_INSTALLMENT = 0.06

                # 매수/매도(숏) 기준 가격 잡기 (개수 계산)
                open_quantity = round(BALANCE * OPEN_INSTALLMENT / open_bid, exchange_data[ticker]['quantity_precision'])

                if open_quantity == 0 or open_ask * open_quantity < TETHER * exchange_data[ticker]['min_notional']:
                    logging.info(f"SKIP|{ticker}|진입수량적음|{open_quantity}|PRECISION|{exchange_data[ticker]['quantity_precision']}")
                    continue
                elif open_ask * open_quantity < TETHER * exchange_data[ticker]['min_notional']:
                    logging.info(f"SKIP|{ticker}|주문금액적음|{open_ask * open_quantity:,}원|MIN_NOTIONAL|{TETHER * exchange_data[ticker]['min_notional']:,}원")
                    continue

                upbit_open_bid_price = open_bid * open_quantity

                if remain_bid_balance['balance'] - upbit_open_bid_price < 0:
                    logging.info(f"SKIP|{ticker}|잔고부족|REMAIN_BID|{remain_bid_balance['balance']}|OPEN_BID|{upbit_open_bid_price}")
                    continue

                order_lock = asyncio.Lock()
                check_order_lock = asyncio.Lock()
                order_result = {
                    'uuid': 0, 'orderId': 0, 'upbit_price': 0, 'upbit_quantity': 0, 'binance_price': 0, 'binance_quantity': 0
                }

                await asyncio.gather(
                    ## UPBIT : ticker, side, price, quantity, order_result, lock
                    ## BINANCE : ticker, side, quantity, order_result, lock
                    upbit.spot_order('KRW-'+ticker, 'bid', upbit_open_bid_price, 0, order_result, order_lock),
                    binance.futures_order(ticker+'USDT', 'ask', open_quantity, order_result, order_lock)
                )

                if order_result['uuid'] == 0 or order_result['orderId'] == 0:
                    message = f'{ticker} 진입 실패 {open_gimp}%\n'
                    message += 'UPBIT 주문❌, ' if order_result['uuid'] == 0 else 'UPBIT 주문✅, '
                    message += 'BINANCE 주문❌' if order_result['orderId'] == 0 else 'BINANCE 주문✅'
                    await util.send_to_telegram(message)
                    continue

                async with order_lock:
                    await asyncio.gather(
                        upbit.check_order(order_result, check_order_lock),
                        binance.check_order(ticker+'USDT', order_result, check_order_lock)
                    )

                async with check_order_lock:
                    logging.info(f"CHECK_ORDER_RESULT|{order_result}")
                    remain_bid_balance['balance'] -= order_result['upbit_price'] * order_result['upbit_quantity']
                    order_result['binance_price'] = order_result['binance_price'] * TETHER
                    order_open_gimp = round(order_result['upbit_price'] / order_result['binance_price'] * 100 - 100, 3)

                    ## 진입 성공 시 포지션 데이터 Update
                    if position_data[ticker]['open_install_count'] == 0:
                        position_data[ticker]['open_timestamp'] = datetime.now().timestamp()
                        position_ticker_count['count'] += 1

                    position_data[ticker]['open_install_count'] += 1
                    position_data[ticker]['acc_open_install_count'] += 1
                    position_data[ticker]['position_gimp_acc'].append(order_open_gimp)
                    position_data[ticker]['position_gimp_acc_weight'].append(OPEN_INSTALLMENT)
                    position_data[ticker]['open_limit_count'] = 0

                    temp_gimp = 0
                    for i in range(len(position_data[ticker]['position_gimp_acc_weight'])):
                        weight = position_data[ticker]['position_gimp_acc_weight'][i] / sum(position_data[ticker]['position_gimp_acc_weight'])
                        temp_gimp += position_data[ticker]['position_gimp_acc'][i] * weight
                    position_data[ticker]['position_gimp'] = round(temp_gimp, 2)
                    position_data[ticker]['position'] = 1
                    position_data[ticker]['close_count'] = 0

                    trade_data[ticker]['upbit_total_quantity'] += order_result['upbit_quantity']
                    trade_data[ticker]['binance_total_quantity'] += order_result['binance_quantity']
                    trade_data[ticker]['open_bid_price_acc'] += order_result['upbit_price'] * order_result['upbit_quantity']
                    trade_data[ticker]['open_ask_price_acc'] += order_result['binance_price'] * order_result['binance_quantity']

                    # 텔레그램 전송 및 로깅 데이터
                    message = (f"{ticker} 진입\n"
                               f"요청김프: {open_gimp}%\n"
                               f"주문김프: {order_open_gimp}%\n"
                               f"누적진입김프: {position_data[ticker]['position_gimp']}%\n"
                               f"BTC김프: {round(btc_open_gimp, 3)}%\n"
                               f"변동성: {acc_ticker_count[ticker]['open_count']}\n"
                               f"분할매수매도: {position_data[ticker]['open_install_count']}/{position_data[ticker]['close_install_count']}\n"
                               f"요청가격: {open_bid:,}원/{open_ask:,}원\n"
                               f"주문가격: {round(order_result['upbit_price'],2):,}원/{round(order_result['binance_price'],2):,}원\n"
                               f"슬리피지: {round(order_result['upbit_price'] / open_bid * 100 - 100, 3)}%/{round(order_result['binance_price'] / open_ask * 100 - 100, 3)}%\n"
                               f"진입누적가격: {round(trade_data[ticker]['open_bid_price_acc'],2):,}원/{round(trade_data[ticker]['open_ask_price_acc'],2):,}원\n"
                               f"종료누적가격: {round(trade_data[ticker]['close_ask_price_acc'],2):,}원/{round(trade_data[ticker]['close_ask_price_acc'],2):,}원\n"
                               f"진입수량: {order_result['upbit_quantity']}/{order_result['binance_quantity']}\n"
                               f"총진입수량: {trade_data[ticker]['upbit_total_quantity']}/{trade_data[ticker]['binance_total_quantity']}\n"
                               f"잔액: {round(remain_bid_balance['balance'], 2):,}원\n"
                               f"고정환율: {TETHER:,}원\n")
                    # 주문 로직
                    open_message_list.append(message)
        except Exception as e:
            logging.info(f"OpenOrder 오류: {traceback.format_exc()}")
            continue

    for message in open_message_list:
        logging.info(f"POSITION_OPEN|{message}")
        await util.send_to_telegram("🔵" + message)
