import traceback
import util
import logging
import asyncio
from datetime import datetime
from consts import *
from api import upbit, binance

async def compare_price_open_order(orderbook_check, exchange_data, remain_bid_balance, check_data, trade_data,
                                position_data, acc_ticker_count, position_ticker_count, order_flag):
    """ self.exchange_price 저장된 거래소별 코인정보를 비교하고 특정 (%)이상 갭발생시 알림 전달하는 함수 """
    open_message_list = []

    for ticker in orderbook_check:
        try:
            if orderbook_check[ticker]['Binance'] is None or orderbook_check[ticker]['Upbit'] is None:
                continue

            open_bid = orderbook_check[ticker]['Upbit']['balance_ask_average']
            close_bid = orderbook_check[ticker]['Upbit']['balance_bid_average']
            open_ask = orderbook_check[ticker]['Binance']['balance_bid_average']
            close_ask = orderbook_check[ticker]['Binance']['balance_ask_average']
            open_bid_btc = orderbook_check['BTC']['Upbit']['balance_ask_average']
            open_ask_btc = orderbook_check['BTC']['Binance']['balance_bid_average']

            ## 가격이 없는 친구들 PASS
            if open_bid == 0 or close_bid == 0 or open_ask == 0 or close_ask == 0 or open_bid_btc == 0 or open_ask_btc == 0:
                continue

            open_gimp = open_bid / open_ask * 100 - 100
            close_gimp = close_bid / close_ask * 100 - 100
            btc_open_gimp = open_bid_btc / open_ask_btc * 100 - 100

            if remain_bid_balance['balance'] < 0:
                continue

            ## 포지션 진입 로직
            if open_gimp < check_data[ticker]['open_gimp']:
                # open_gimp 이 Update 되면 close_gimp은 그 시점으로 gap 수정
                check_data[ticker] = {
                    "open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                    "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask
                }
                if order_flag['open'] == 0:
                    if open_gimp - close_gimp > CURR_GIMP_GAP:
                        continue

                    if position_data[ticker]['open_install_count'] == 0 and open_gimp > btc_open_gimp * BTC_GAP:
                        continue

                    if position_data[ticker]['open_install_count'] == 0:
                        if position_ticker_count['count'] == 0 and exchange_data['grid_check'] == 0:
                            continue

                        if position_ticker_count['count'] >= POSITION_MAX_COUNT:
                            continue

                        if exchange_data['avg_gimp'] < 1.8:
                            install_weight = INSTALL_WEIGHT
                        elif 1.8 <= exchange_data['avg_gimp'] < 2.8:
                            install_weight = INSTALL_WEIGHT + 0.02
                        elif 2.8 <= exchange_data['avg_gimp'] < 3.8:
                            install_weight = INSTALL_WEIGHT + 0
                        elif exchange_data['avg_gimp'] > 3.8:
                            install_weight = INSTALL_WEIGHT + 0.06

                        if exchange_data['front_position_gimp'] - install_weight < open_gimp:
                            continue

                        if position_data[ticker]['profit_count'] > 0 and open_gimp > position_data[ticker]['front_close_gimp'] - RE_OPEN_GIMP_GAP:
                            continue

                        position_data[ticker]['open_limit_count'] += 1
                        if position_data[ticker]['open_limit_count'] < 2:
                            continue

                    elif position_data[ticker]['open_install_count'] > 0:
                        if position_data[ticker]['open_install_check'] == 0:
                            continue

                        if open_gimp > position_ticker_count['open_gimp_limit']:
                            continue

                        position_data[ticker]['open_limit_count'] += 1
                        if position_data[ticker]['open_limit_count'] < 2:
                            continue

                elif order_flag['open'] == 1:
                    if ticker != order_flag['ticker']:
                        continue
                elif order_flag['open'] == -1:
                    continue

                open_installment = OPEN_INSTALLMENT

                # 매수/매도(숏) 기준 가격 잡기 (개수 계산)
                open_quantity = round(BALANCE * open_installment / open_bid, exchange_data[ticker]['quantity_precision'])

                if open_quantity == 0 or open_ask * open_quantity < TETHER * exchange_data[ticker]['min_notional']:
                    logging.info(f"SKIP|{ticker}|{round(open_gimp,2)}%|진입수량적음|{open_quantity}|OPEN_INSTALL|{open_installment}|OPEN_BID|{open_bid}|PRECISION|{exchange_data[ticker]['quantity_precision']}")
                    continue
                elif open_ask * open_quantity < TETHER * exchange_data[ticker]['min_notional']:
                    logging.info(f"SKIP|{ticker}|{round(open_gimp,2)}%|주문금액적음|{open_ask * open_quantity:,}원|MIN_NOTIONAL|{TETHER * exchange_data[ticker]['min_notional']:,}원")
                    continue

                upbit_open_bid_price = open_bid * open_quantity

                if remain_bid_balance['balance'] - upbit_open_bid_price < 0:
                    logging.info(f"SKIP|{ticker}|{round(open_gimp,2)}%|잔고부족|REMAIN_BID|{remain_bid_balance['balance']}|OPEN_BID|{upbit_open_bid_price}")
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
                    message = f'{ticker} 진입 실패 {round(open_gimp,3)}%\n'
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
                    order_open_gimp = order_result['upbit_price'] / order_result['binance_price'] * 100 - 100

                    ## 진입 성공 시 포지션 데이터 Update
                    if position_data[ticker]['open_install_count'] == 0:
                        position_data[ticker]['open_timestamp'] = datetime.now().timestamp()
                        position_ticker_count['count'] += 1

                    position_data[ticker]['open_install_count'] += 1
                    position_data[ticker]['acc_open_install_count'] += 1
                    position_data[ticker]['position_gimp_acc'].append(order_open_gimp)
                    position_data[ticker]['position_gimp_acc_weight'].append(open_installment)
                    position_data[ticker]['open_limit_count'] = 0
                    position_data[ticker]['front_position_gimp'] = order_open_gimp

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

                    # 텔레그램 전송 및 로깅 데이터
                    message = (f"{ticker} 진입\n"
                               f"요청주문김프: {round(open_gimp,3)}%|{round(order_open_gimp,3)}%\n"
                               f"누적진입김프: {position_data[ticker]['position_gimp']}%\n"
                               f"직전최소진입김프: {round(exchange_data['front_position_gimp'],2)}%\n"
                               f"BTC김프: {round(btc_open_gimp, 3)}%\n"
                               f"변동성: {acc_ticker_count[ticker]['open_count']}\n"
                               f"분할매수매도: {position_data[ticker]['open_install_count']}|{position_data[ticker]['close_install_count']}\n"
                               f"요청가격: {round(open_bid,2):,}원/{round(open_ask,2):,}원\n"
                               f"주문가격: {round(order_result['upbit_price'],2):,}원|{round(order_result['binance_price'],2):,}원\n"
                               f"슬리피지: {round(order_result['upbit_price'] / open_bid * 100 - 100, 3)}%|{round(order_result['binance_price'] / open_ask * 100 - 100, 3)}%\n"
                               f"진입누적가격: {round(trade_data[ticker]['open_bid_price_acc'],2):,}원|{round(trade_data[ticker]['open_ask_price_acc'],2):,}원\n"
                               f"종료누적가격: {round(trade_data[ticker]['close_ask_price_acc'],2):,}원|{round(trade_data[ticker]['close_ask_price_acc'],2):,}원\n"
                               f"진입수량: {order_result['upbit_quantity']}|{order_result['binance_quantity']}\n"
                               f"총진입수량: {trade_data[ticker]['upbit_total_quantity']}|{trade_data[ticker]['binance_total_quantity']}\n"
                               f"잔액: {round(remain_bid_balance['balance'], 2):,}원\n"
                               f"고정환율: {TETHER:,}원\n")
                    # 주문 로직
                    open_message_list.append(message)
                    order_flag = {"open": 0, "close": 0, "ticker": 0}
                    util.put_order_flag(order_flag)

        except Exception as e:
            logging.info(f"OpenOrder 오류: {traceback.format_exc()}")
            '''
            check_data[ticker] = {
                "open_gimp": open_gimp, "open_bid": open_bid, "open_ask": open_ask,
                "close_gimp": close_gimp, "close_bid": close_bid, "close_ask": close_ask
            }

            position_data[ticker] = {
                "open_install_count": 0, "close_install_count": 0, "acc_open_install_count": 0,
                "position": 0, "position_gimp": 0, "position_gimp_acc": [], "position_gimp_acc_weight": [],
                "profit_count": 0, "front_close_gimp": 0, "open_timestamp": 0, "open_limit_count": 0,
                "open_install_check": 0, "front_position_gimp": 0, "close_limit_count": 0
            }

            trade_data[ticker] = {
                "open_bid_price_acc": 0, "open_ask_price_acc": 0,
                "close_bid_price_acc": 0, "close_ask_price_acc": 0,
                "upbit_total_quantity": 0, "upbit_close_quantity": 0,
                "binance_total_quantity": 0, "binance_close_quantity": 0,
                "trade_profit": 0, "total_profit": 0
            }'''

    for message in open_message_list:
        logging.info(f"POSITION_OPEN|{message}")
        await util.send_to_telegram("🔵" + message)
