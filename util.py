import traceback
import telegram
import asyncio
import aiohttp
import logging
import datetime
import json
import os
from logging.handlers import TimedRotatingFileHandler

from api import hana
from consts import *
from datetime import datetime, timezone, timedelta
bot = None
chat_id_list = None

def setup_collect_logging():
    logging.basicConfig(level=logging.INFO)
    # TimedRotatingFileHandler를 설정하여 날짜별로 로그 파일을 회전
    if ENV == 'real':
        log_file_path = '/root/arbitrage/log/premium.log'
    elif ENV == 'local':
        log_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/premium.log'

    # 파일 핸들러 생성 및 설정

    file_handler = TimedRotatingFileHandler(filename=log_file_path, when='midnight', interval=1, backupCount=30)
    file_handler.suffix = "%Y%m%d"
    file_handler.setLevel(logging.INFO)

    # 로그 포매터 설정
    if ENV == 'real':
        formatter = logging.Formatter('[%(asctime)s][%(levelname)s]:%(message)s')
    elif ENV == 'local':
        formatter = logging.Formatter('[%(asctime)s][%(levelname)s]:%(message)s ...(%(filename)s:%(lineno)d)')

    file_handler.setFormatter(formatter)

    # 루트 로거에 핸들러 추가
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

def setup_order_logging():
    logging.basicConfig(level=logging.INFO)
    # TimedRotatingFileHandler를 설정하여 날짜별로 로그 파일을 회전
    if ENV == 'real':
        log_file_path = '/root/arbitrage/log/order.log'
    elif ENV == 'local':
        log_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/order.log'

    # 파일 핸들러 생성 및 설정

    file_handler = TimedRotatingFileHandler(filename=log_file_path, when='midnight', interval=1, backupCount=30)
    file_handler.suffix = "%Y%m%d"
    file_handler.setLevel(logging.INFO)

    # 로그 포매터 설정
    if ENV == 'real':
        formatter = logging.Formatter('[%(asctime)s][%(levelname)s]:%(message)s')
    elif ENV == 'local':
        formatter = logging.Formatter('[%(asctime)s][%(levelname)s]:%(message)s ...(%(filename)s:%(lineno)d)')

    file_handler.setFormatter(formatter)

    # 루트 로거에 핸들러 추가
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

async def get_chat_id():
    logging.info("Telegram Chat ID 요청합니다..")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates') as response:
                if response.status == 200:
                    data = await response.json()
                    chat_id_group = data['result']
                    chat_id_list = []
                    for result in chat_id_group:
                        chat_id_list.append(result['message']['chat']['id'])
                    chat_id_list = list(set(chat_id_list))
                    logging.info(f"Telegram Chat ID 응답 : {chat_id_list}")
                    return chat_id_list
                else:
                    logging.info(f"Telegram Chat ID 요청 응답 오류: {response.status}")
        except aiohttp.ClientError as e:
            logging.info(f"Telegram 세션 연결 오류: {e}")

async def send_to_telegram(message):
    # 텔레그램 메시지 보내는 함수, 최대 3회 연결, 3회 전송 재시도 수행
    global bot
    global chat_id_list

    if chat_id_list is None:
        chat_id_list = await get_chat_id()
        #logging.info(f"Telegram Chat ID 값 취득 : {get_chat_id()}")
        # chat_id_list = ['1109591824'] # 준우
        # chat_id_list = ['1109591824', '2121677449']  #
        chat_id_list = ['2121677449']  # 규빈
        logging.info(f"Telegram Chat ID 값 취득 : {chat_id_list}")

    if bot is None:
        logging.info("Telegram 연결 시도...")
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    for chat_id in chat_id_list:
        for i in range(3):
            try:
                # logging.info(f"Telegram [{chat_id}], msg 전송 {message}")
                await bot.send_message(chat_id, message[:TELEGRAM_MESSAGE_MAX_SIZE])
                break
            except telegram.error.TimedOut as e:
                logging.info(f"Telegram {chat_id} msg 전송 오류... {i + 1} 재시도... : {e}")
                
                await asyncio.sleep(5)
            except Exception as e:
                logging.info(f"Telegram 연결 해제... {e}")
                bot = None
                break

async def send_to_telegram_image(image):
    # 텔레그램 메시지 보내는 함수, 최대 3회 연결, 3회 전송 재시도 수행
    global bot
    global chat_id_list

    message = '[News Coo 🦤]\n🔵진입김프(UPBIT⬆️/BINANCE⬇️)|\n🔴탈출김프(UPBIT⬇️/BINANCE⬆️)|\n⚫️Bitcoin진입김프(UPBIT⬆️/BINANCE⬇️)'
    if chat_id_list is None:
        chat_id_list = await get_chat_id()
        chat_id_list = ['1109591824', '2121677449']  #
        logging.info(f"Telegram Chat ID 값 취득 : {chat_id_list}")

    if bot is None:
        logging.info("Telegram 연결 시도...")
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    for chat_id in chat_id_list:
        for i in range(3):
            try:
                # logging.info(f"Telegram [{chat_id}], msg 전송 {message}")
                await bot.send_message(chat_id, message[:TELEGRAM_MESSAGE_MAX_SIZE])
                await bot.send_photo(chat_id, photo=open(image, 'rb'))
                break
            except telegram.error.TimedOut as e:
                logging.info(f"Telegram {chat_id} msg 전송 오류... {i + 1} 재시도... : {e}")
                await asyncio.sleep(5)
            except Exception as e:
                logging.info(f"Telegram 연결 해제... {e}")
                bot = None
                break

def is_need_reset_socket(start_time):
    now = datetime.now()
    one_days_ago = now - timedelta(days=1)

    if start_time < one_days_ago:
        return True
    else:
        return

def load_remain_position(position_data, trade_data, position_ticker_count):
    if ENV == 'real':
        load_path = '/root/arbitrage/data/position_data.DAT'
    elif ENV == 'local':
        load_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/position_data.DAT'

    if os.path.exists(load_path):
        with open(load_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for line in lines:
            try:
                split_data = line.split('|')
                ticker = split_data[0]
                type = split_data[1]
                data = split_data[2]
                if type == 'POSITION':
                    position_ticker_count['count'] += 1
                    position_data[ticker] = json.loads(data)
                    logging.info(f"FILE_LOAD|POSITION_DATA|{ticker}")
                elif type == 'TRADE':
                    trade_data[ticker] = json.loads(data)
                    logging.info(f"FILE_LOAD|TRADE_DATA|{ticker}")
            except Exception as e:
                logging.info(e)
                
    else:
        logging.info(f"{load_path} There is no file")

def put_remain_position(position_data, trade_data):
    put_path = ''
    put_data = ''

    if ENV == 'real':
        put_path = '/root/arbitrage/data/position_data.DAT'
    elif ENV == 'local':
        put_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/position_data.DAT'

    for ticker in position_data:
        if position_data[ticker]['position'] == 1:
            put_data += ticker + "|POSITION|" + json.dumps(position_data[ticker]) + "|\n"
            put_data += ticker + "|TRADE|" + json.dumps(trade_data[ticker]) + "|\n"

    with open(put_path, 'w') as file:
        file.write(put_data)

def load_profit_data(message):
    year_month = datetime.now().strftime("%Y%m")
    if ENV == 'real':
        load_path = '/root/arbitrage/data/profit_data_'+year_month+'.DAT'
    elif ENV == 'local':
        load_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/profit_data_'+year_month+'.DAT'

    if os.path.exists(load_path):
        with open(load_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        acc_profit = 0
        acc_profit_rate =0
        for line in lines:
            try:
                split_data = line.split('|')
                ticker = split_data[1]
                profit = split_data[7]
                profit_rate = split_data[9]

                acc_profit += float(profit)
                acc_profit_rate += float(profit_rate)
            except:
                continue

        if acc_profit > 0:
            logging.info(f"FILE_LOAD|PROFIT_DATA {acc_profit}|{acc_profit_rate}")
            message = f"{round(acc_profit,0):,}원|{round(acc_profit_rate,3)}%"
    else:
        logging.info(f"{load_path} There is no file")
        
    return message

def put_profit_data(ticker, open_gimp, close_gimp, profit, balance):
    put_path = ''

    year_month = datetime.now().strftime("%Y%m")
    time = datetime.now().strftime("%Y-%m-%d %H:%m")
    if ENV == 'real':
        put_path = '/root/arbitrage/data/profit_data_'+year_month+'.DAT'
    elif ENV == 'local':
        put_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/profit_data_'+year_month+'.DAT'

    put_data = (
            str(time) + '|' + str(ticker) + "|OPEN|" + str(open_gimp) + '|CLOSE|' + str(close_gimp)
            + '|PROFIT|' + str(profit) + '|PROFIT_RATE|' + str(round(float(profit)/(float(balance) * 2) * 100, 3)) + '\n'
    )
    with open(put_path, 'a') as file:
        file.write(put_data)


def load_orderbook_check(orderbook_check):
    if ENV == 'real':
        load_path = '/root/arbitrage/data/orderbook_check.json'
    elif ENV == 'local':
        load_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/orderbook_check.json'

    if os.path.exists(load_path):
        with open(load_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for line in lines:
            try:
                print("LOAD orderbook CHECK")
                orderbook_check.update(json.loads(line))
                print(orderbook_check)
            except Exception as e:
                logging.info(e)
    else:
        logging.info(f"{load_path} There is no file")

def put_orderbook_check(orderbook_check):
    put_path = ''

    if ENV == 'real':
        put_path = '/root/arbitrage/data/orderbook_check.json'
    elif ENV == 'local':
        put_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/orderbook_check.json'

    put_data = json.dumps(orderbook_check)

    with open(put_path, 'w') as file:
        file.write(put_data)

def load_profit_count(position_data):
    if ENV == 'real':
        load_path = '/root/arbitrage/data/profit_count.DAT'
    elif ENV == 'local':
        load_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/profit_count.DAT'

    if os.path.exists(load_path):
        with open(load_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for line in lines:
            try:
                split_data = line.split('|')
                ticker = split_data[0]
                data = split_data[1]
                temp_data = json.loads(data)
                if ticker in position_data:
                    position_data[ticker]['profit_count'] = temp_data['profit_count']
                elif ticker not in position_data:
                    position_data[ticker] = json.loads(data)
                logging.info(f"FILE_LOAD|PROFIT_COUNT|{ticker}")
                
            except Exception as e:
                logging.info(e)
    else:
        logging.info(f"{load_path} There is no file")

def put_profit_count(position_data):
    put_path = ''
    put_data = ''

    if ENV == 'real':
        put_path = '/root/arbitrage/data/profit_count.DAT'
    elif ENV == 'local':
        put_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/profit_count.DAT'

    for ticker in position_data:
        if position_data[ticker]['profit_count'] >= 1 and position_data[ticker]['position'] == 0:
            put_data += ticker + "|" + json.dumps(position_data[ticker]) + "\n"

    with open(put_path, 'w') as file:
        file.write(put_data)

def load_top_ticker(exchange_data):
    if ENV == 'real':
        load_path = '/root/arbitrage/data/upbit_top_ticker.json'
    elif ENV == 'local':
        load_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/upbit_top_ticker.json'

    if os.path.exists(load_path):
        with open(load_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for line in lines:
            try:
                exchange_data['upbit_top_ticker'] = eval(line)
            except Exception as e:
                logging.info(e)
    else:
        print(f"There is no File {load_path}")
        logging.info(f"{load_path} There is no file")

def put_top_ticker(exchange_data):
    put_path = ''
    temp_data = {}

    if ENV == 'real':
        put_path = '/root/arbitrage/data/upbit_top_ticker.json'
    elif ENV == 'local':
        put_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/upbit_top_ticker.json'

    put_data = json.dumps(exchange_data['upbit_top_ticker'])
    with open(put_path, 'w') as file:
        file.write(put_data)

def load_order_flag(order_flag):
    if ENV == 'real':
        load_path = '/root/arbitrage/data/order_flag.json'
    elif ENV == 'local':
        load_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/order_flag.json'

    if os.path.exists(load_path):
        with open(load_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for line in lines:
            try:
                order_flag.update(json.loads(line))
            except Exception as e:
                logging.info(e)
    else:
        print(f"There is no File {load_path}")
        logging.info(f"{load_path} There is no file")

def put_order_flag(order_flag):
    put_path = ''

    if ENV == 'real':
        put_path = '/root/arbitrage/data/order_flag.json'
    elif ENV == 'local':
        put_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/order_flag.json'

    put_data = json.dumps(order_flag)
    with open(put_path, 'w') as file:
        file.write(put_data)

def load_low_gimp(exchange_data):
    if ENV == 'real':
        load_path = '/root/arbitrage/data/low_gimp.DAT'
    elif ENV == 'local':
        load_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/low_gimp.DAT'

    if os.path.exists(load_path):
        with open(load_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for line in lines:
            try:
                data = line.split('|')
                low_gimp = float(data[0])
                exchange_data['low_gimp'] = low_gimp
            except Exception as e:
                logging.info(e)

    else:
        print(f"There is no File {load_path}")
        logging.info(f"{load_path} There is no file")

def put_low_gimp(exchange_data):
    put_path = ''

    if ENV == 'real':
        put_path = '/root/arbitrage/data/low_gimp.DAT'
    elif ENV == 'local':
        put_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/low_gimp.DAT'

    put_data = str(exchange_data['low_gimp'])
    with open(put_path, 'w') as file:
        file.write(put_data)

def load_close_mode(exchange_data):
    if ENV == 'real':
        load_path = '/root/arbitrage/data/close_mode.DAT'
    elif ENV == 'local':
        load_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/close_mode.DAT'

    if os.path.exists(load_path):
        with open(load_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        for line in lines:
            try:
                data = line.split('|')
                close_mode = int(data[0])
                exchange_data['close_mode'] = close_mode
            except Exception as e:
                logging.info(e)

    else:
        print(f"There is no File {load_path}")
        logging.info(f"{load_path} There is no file")

def put_close_mode(exchange_data):
    put_path = ''

    if ENV == 'real':
        put_path = '/root/arbitrage/data/close_mode.DAT'
    elif ENV == 'local':
        put_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/low_gimpclose_mode.DAT'

    put_data = str(exchange_data['close_mode'])
    with open(put_path, 'w') as file:
        file.write(put_data)

def load_history_data():
    # 오늘 날짜 가져오기
    now_date = datetime.date.today()
    today = now_date.strftime("%Y%m%d")
    # 하루 전 날짜 계산
    yesterday = now_date - datetime.timedelta(days=1)
    yesterday = yesterday.strftime("%Y%m%d")

    if ENV == 'real':
        history_file_path = '/root/arbitrage/log/premium_data_'+yesterday
    elif ENV == 'local':
        history_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/premium_data_'+yesterday
        history_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/premium_data'

    if os.path.exists(history_file_path):
        logging.info(history_file_path)
        with open(history_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    else:
        logging.info(f"{history_file_path} 파일이 존재하지 않습니다.")

    return lines

def get_profit_position(orderbook_check, position_data, trade_data, remain_bid_balance, exchange_data):
    # 오늘 날짜 가져오기
    try:
        usd_price = hana.get_currency_data("USD")
        btc_open_gimp = 0
        open_timestamp = []
        open_message = {}
        message = ''

        open_bid_btc = float(orderbook_check['BTC']['Upbit']['balance_ask_average'])
        open_bid_eth = float(orderbook_check['ETH']['Upbit']['balance_ask_average'])
        open_bid_xrp = float(orderbook_check['XRP']['Upbit']['balance_ask_average'])

        open_ask_btc = float(orderbook_check['BTC']['Binance']['balance_bid_average'])
        open_ask_eth = float(orderbook_check['XRP']['Binance']['balance_bid_average'])
        open_ask_xrp = float(orderbook_check['ETH']['Binance']['balance_bid_average'])

        real_open_bid_btc = float(orderbook_check['BTC']['Upbit']['balance_ask_average'])
        real_open_bid_eth = float(orderbook_check['ETH']['Upbit']['balance_ask_average'])
        real_open_bid_xrp = float(orderbook_check['XRP']['Upbit']['balance_ask_average'])

        real_open_ask_btc = float(orderbook_check['BTC']['Binance']['balance_bid_average']) / TETHER * usd_price
        real_open_ask_eth = float(orderbook_check['XRP']['Binance']['balance_bid_average']) / TETHER * usd_price
        real_open_ask_xrp = float(orderbook_check['ETH']['Binance']['balance_bid_average']) / TETHER * usd_price

        if real_open_bid_btc == 0 or real_open_ask_btc == 0:
            message = f"🌚 1분 후 재시도..."
            return message
        if real_open_bid_eth == 0 or real_open_ask_eth == 0:
            message = f"🌚 1분 후 재시도..."
            return message
        if real_open_bid_xrp == 0 or real_open_ask_xrp == 0:
            message = f"🌚 1분 후 재시도..."
            return message
        if open_bid_btc == 0 or open_ask_btc == 0:
            message = f"🌚 1분 후 재시도..."
            return message
        if open_bid_eth == 0 or open_ask_eth == 0:
            message = f"🌚 1분 후 재시도..."
            return message
        if open_bid_xrp == 0 or open_ask_xrp == 0:
            message = f"🌚 1분 후 재시도..."
            return message

        fix_open_bid = open_bid_btc + open_bid_eth + open_bid_xrp
        fix_open_ask = open_ask_btc + open_ask_eth + open_ask_xrp

        real_open_bid = real_open_bid_btc + real_open_bid_eth + real_open_bid_xrp
        real_open_ask = real_open_ask_btc + real_open_ask_eth + real_open_ask_xrp
        fix_open_gimp = round(fix_open_bid / fix_open_ask * 100 - 100, 2)
        real_open_gimp = round(real_open_bid / real_open_ask * 100 - 100, 2)

        message = f"🌟고정김프:{fix_open_gimp}%|실제김프:{real_open_gimp}%\n"

        position_gimp_list = []
        position_ticker_list = []
        for ticker in position_data:
            if position_data[ticker]['position'] == 1:
                time_object_utc = datetime.utcfromtimestamp(position_data[ticker]['open_timestamp'])
                time_object_korea = time_object_utc.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=9)))

                position_gimp_list.append(position_data[ticker]['position_gimp'])
                position_ticker_list.append(ticker)

                close_bid = float(orderbook_check[ticker]['Upbit']['balance_bid_average'])
                close_ask = float(orderbook_check[ticker]['Binance']['balance_ask_average'])

                if close_bid == 0 or close_ask == 0:
                    open_timestamp.append(time_object_korea)
                    open_message[time_object_korea] = (
                        f"🌚{ticker}({position_data[ticker]['open_install_count']}/{position_data[ticker]['close_install_count']})"
                        f"|{round(position_data[ticker]['position_gimp'],2)}%|조회오류"
                        f"|{round(trade_data[ticker]['open_bid_price_acc']) - round(trade_data[ticker]['close_bid_price_acc']):,}원"
                        f"|{time_object_korea.strftime('%d일 %H:%M')}\n"
                    )
                else:
                    close_gimp = round(close_bid / close_ask * 100 - 100, 2)
                    open_timestamp.append(time_object_korea)
                    open_message[time_object_korea] = (
                        f"🌝{ticker}({position_data[ticker]['open_install_count']}/{position_data[ticker]['close_install_count']})"
                        f"|{round(position_data[ticker]['position_gimp'],2)}%|{close_gimp}%"
                        f"|{round(trade_data[ticker]['open_bid_price_acc']) - round(trade_data[ticker]['close_bid_price_acc']):,}원"
                        f"|{time_object_korea.strftime('%d일 %H:%M')}\n"
                    )
        for i in range(len(open_timestamp)):
            timestamp = min(open_timestamp)
            temp_message = str(open_message[timestamp])
            message += temp_message
            open_timestamp.remove(timestamp)

        if len(position_gimp_list) > 0:
            min_position_gimp = min(position_gimp_list)
            ticker_index = position_gimp_list.index(min_position_gimp)
            min_ticker = position_ticker_list[ticker_index]

            message += f"🙆🏻진입현황({len(position_gimp_list)}/{POSITION_MAX_COUNT})\n"
            '''
            if real_open_gimp < 1.8:
                install_weight = 0.2
            elif 1.8 <= real_open_gimp < 2.8:
                install_weight = 0.3
            elif 2.8 <= real_open_gimp < 3.8:
                install_weight = 0.4
            elif real_open_gimp > 3.8:
                install_weight = 0.5
                
            open_gimp_limit = min_position_gimp - install_weight
            
            if exchange_data['close_mode'] == 0:
                close_gimp_gap = CLOSE_GIMP_GAP + len(position_gimp_list) * 0.012
            elif exchange_data['close_mode'] == 1:
                close_gimp_gap = CLOSE_GIMP_GAP - 0.1 + len(position_gimp_list) * 0.012
            elif exchange_data['close_mode'] == 2:
                close_gimp_gap = CLOSE_GIMP_GAP - 0.2 + len(position_gimp_list) * 0.012
            elif exchange_data['close_mode'] == 3:
                close_gimp_gap = CLOSE_GIMP_GAP - 0.3 + len(position_gimp_list) * 0.012
            message += f"🙆🏻진입현황({len(position_gimp_list)}/{POSITION_MAX_COUNT})|{min_position_gimp}% 이하\n"
            message += f"🌊물타기|{min_ticker}|{round(open_gimp_limit, 2)}% 이하\n"
            message += f"⚡️종료모드|{exchange_data['close_mode']}|{round(close_gimp_gap,2)}% 이상\n"
            '''
        if remain_bid_balance['balance'] < BALANCE:
            message += f"💰잔액: {round(remain_bid_balance['balance']):,}원"

        if len(message) == 0:
            message = f"🌚 진입 정보 없음"

        return message
    except Exception as e:
        message = f"🌚 1분 후 재시도..."
        logging.info(traceback.format_exc())
        return message
