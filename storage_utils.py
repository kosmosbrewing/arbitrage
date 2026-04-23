import datetime
import json
import logging
import os

from consts import ENV


def _data_dir():
    if ENV == 'real':
        return '/root/arbitrage/data'
    return 'C:/Users/skdba/PycharmProjects/arbitrage/data'


def _log_dir():
    if ENV == 'real':
        return '/root/arbitrage/log'
    return 'C:/Users/skdba/PycharmProjects/arbitrage/log'


def _data_path(filename):
    return os.path.join(_data_dir(), filename)


def _log_path(filename):
    return os.path.join(_log_dir(), filename)


def _read_lines(path, missing_message="There is no file"):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as file:
            return file.readlines()

    logging.info(f"{path} {missing_message}")
    return []


def load_remain_position(position_data, trade_data, position_ticker_count):
    lines = _read_lines(_data_path('position_data.DAT'))
    for line in lines:
        try:
            split_data = line.split('|')
            ticker = split_data[0]
            position_type = split_data[1]
            data = split_data[2]
            if position_type == 'POSITION':
                position_ticker_count['count'] += 1
                position_data[ticker] = json.loads(data)
                logging.info(f"FILE_LOAD|POSITION_DATA|{ticker}")
            elif position_type == 'TRADE':
                trade_data[ticker] = json.loads(data)
                logging.info(f"FILE_LOAD|TRADE_DATA|{ticker}")
        except Exception as exc:
            logging.info(exc)


def put_remain_position(position_data, trade_data):
    put_data = ''
    for ticker in position_data:
        if position_data[ticker]['position'] == 1:
            put_data += ticker + "|POSITION|" + json.dumps(position_data[ticker]) + "|\n"
            put_data += ticker + "|TRADE|" + json.dumps(trade_data[ticker]) + "|\n"

    with open(_data_path('position_data.DAT'), 'w') as file:
        file.write(put_data)


def load_profit_data(message):
    year_month = datetime.datetime.now().strftime("%Y%m")
    lines = _read_lines(_data_path(f'profit_data_{year_month}.DAT'))
    acc_profit = 0
    acc_profit_rate = 0

    for line in lines:
        try:
            split_data = line.split('|')
            profit = split_data[7]
            profit_rate = split_data[9]
            acc_profit += float(profit)
            acc_profit_rate += float(profit_rate)
        except Exception:
            continue

    if acc_profit > 0:
        logging.info(f"FILE_LOAD|PROFIT_DATA {acc_profit}|{acc_profit_rate}")
        return f"{round(acc_profit, 0):,}원|{round(acc_profit_rate, 3)}%"
    return message


def put_profit_data(ticker, open_gimp, close_gimp, profit, balance):
    year_month = datetime.datetime.now().strftime("%Y%m")
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%m")
    put_data = (
        str(current_time) + '|' + str(ticker) + "|OPEN|" + str(open_gimp) + '|CLOSE|' + str(close_gimp)
        + '|PROFIT|' + str(profit) + '|PROFIT_RATE|' + str(round(float(profit) / (float(balance) * 2) * 100, 3)) + '\n'
    )
    with open(_data_path(f'profit_data_{year_month}.DAT'), 'a') as file:
        file.write(put_data)


def load_orderbook_check(orderbook_check):
    lines = _read_lines(_data_path('orderbook_check.json'))
    for line in lines:
        try:
            orderbook_check.update(json.loads(line))
        except Exception as exc:
            logging.info(exc)


def put_orderbook_check(orderbook_check):
    with open(_data_path('orderbook_check.json'), 'w') as file:
        file.write(json.dumps(orderbook_check))


def load_profit_count(position_data):
    lines = _read_lines(_data_path('profit_count.DAT'))
    for line in lines:
        try:
            split_data = line.split('|')
            ticker = split_data[0]
            data = split_data[1]
            temp_data = json.loads(data)
            if ticker in position_data:
                position_data[ticker]['profit_count'] = temp_data['profit_count']
            else:
                position_data[ticker] = json.loads(data)
            logging.info(f"FILE_LOAD|PROFIT_COUNT|{ticker}")
        except Exception as exc:
            logging.info(exc)


def put_profit_count(position_data):
    put_data = ''
    for ticker in position_data:
        if position_data[ticker]['profit_count'] >= 1 and position_data[ticker]['position'] == 0:
            put_data += ticker + "|" + json.dumps(position_data[ticker]) + "\n"

    with open(_data_path('profit_count.DAT'), 'w') as file:
        file.write(put_data)


def load_top_ticker(exchange_data):
    lines = _read_lines(_data_path('upbit_top_ticker.json'))
    for line in lines:
        try:
            exchange_data['upbit_top_ticker'] = json.loads(line)
        except Exception as exc:
            logging.info(exc)


def put_top_ticker(exchange_data):
    with open(_data_path('upbit_top_ticker.json'), 'w') as file:
        file.write(json.dumps(exchange_data['upbit_top_ticker']))


def load_order_flag(order_flag):
    lines = _read_lines(_data_path('order_flag.json'))
    for line in lines:
        try:
            order_flag.update(json.loads(line))
        except Exception as exc:
            logging.info(exc)


def put_order_flag(order_flag):
    with open(_data_path('order_flag.json'), 'w') as file:
        file.write(json.dumps(order_flag))


def load_low_gimp(exchange_data):
    lines = _read_lines(_data_path('low_gimp.DAT'))
    for line in lines:
        try:
            data = line.split('|')
            exchange_data['low_gimp'] = float(data[0])
        except Exception as exc:
            logging.info(exc)


def put_low_gimp(exchange_data):
    with open(_data_path('low_gimp.DAT'), 'w') as file:
        file.write(str(exchange_data['low_gimp']))


def load_close_mode(exchange_data):
    lines = _read_lines(_data_path('close_mode.DAT'))
    for line in lines:
        try:
            data = line.split('|')
            exchange_data['close_mode'] = int(data[0])
        except Exception as exc:
            logging.info(exc)


def put_close_mode(exchange_data):
    with open(_data_path('close_mode.DAT'), 'w') as file:
        file.write(str(exchange_data['close_mode']))


def load_history_data():
    now_date = datetime.date.today()
    yesterday = (now_date - datetime.timedelta(days=1)).strftime("%Y%m%d")

    if ENV == 'real':
        history_file_path = _log_path(f'premium_data_{yesterday}')
    else:
        history_file_path = _log_path('premium_data')

    return _read_lines(history_file_path, missing_message='파일이 존재하지 않습니다.')
