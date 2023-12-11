import telegram
import asyncio
import aiohttp
import logging
import datetime
import json
import os
from logging.handlers import TimedRotatingFileHandler
from consts import *
from datetime import datetime, timedelta

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
            logging.info(f"Telegram 세션연결 오류: {e}")
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
    #매일 오전 9시인지 확인해 9시가 넘었다면 True를 반환 (Websocket 재연결목적)
    now = datetime.now()
    start_date_base_time = start_time.replace(hour=9, minute=0, second=0, microsecond=0)
    next_base_time = (start_time + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    if start_time < start_date_base_time:
        if start_date_base_time < now:
            return True
        else:
            return
    if next_base_time < now:
        return True
    else:
        return

def load_remain_position(position_data, trade_data, position_ticker_count):
    if ENV == 'real':
        load_path = '/root/arbitrage/conf/position_data.DAT'
    elif ENV == 'local':
        load_path = 'C:/Users/skdba/PycharmProjects/arbitrage/conf/position_data.DAT'

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
                    logging.info(f"FILE_LOAD|POSITION_TRADE|{ticker}\n{position_data[ticker] }")
                elif type == 'TRADE':
                    trade_data[ticker] = json.loads(data)
                    logging.info(f"FILE_LOAD|POSITION_TRADE|{ticker}\n{trade_data[ticker]}")
                
            except Exception as e:
                logging.info(e)
                
    else:
        logging.info(f"{load_path} There is no file")
        

def put_remain_position(position_data, trade_data):
    put_path = ''
    put_data = ''

    if ENV == 'real':
        put_path = '/root/arbitrage/conf/position_data.DAT'
    elif ENV == 'local':
        put_path = 'C:/Users/skdba/PycharmProjects/arbitrage/conf/position_data.DAT'

    for ticker in position_data:
        if position_data[ticker]['position'] == 1:
            put_data += ticker + "|POSITION|" + json.dumps(position_data[ticker]) + "|\n"
            put_data += ticker + "|TRADE|" + json.dumps(trade_data[ticker]) + "|\n"

    with open(put_path, 'w') as file:
        file.write(put_data)

def load_profit_data(message):
    year_month = datetime.now().strftime("%Y%m")
    if ENV == 'real':
        load_path = '/root/arbitrage/conf/profit_data_'+year_month+'.DAT'
    elif ENV == 'local':
        load_path = 'C:/Users/skdba/PycharmProjects/arbitrage/conf/profit_data_'+year_month+'.DAT'

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
            message = f"{round(acc_profit,2):,}원|{round(acc_profit_rate,3)}%"
    else:
        logging.info(f"{load_path} There is no file")
        
    return message

def put_profit_data(ticker, open_gimp, close_gimp, profit, balance):
    put_path = ''

    year_month = datetime.now().strftime("%Y%m")
    time = datetime.now().strftime("%Y-%m-%d %H:%m")
    if ENV == 'real':
        put_path = '/root/arbitrage/conf/profit_data_'+year_month+'.DAT'
    elif ENV == 'local':
        put_path = 'C:/Users/skdba/PycharmProjects/arbitrage/conf/profit_data_'+year_month+'.DAT'

    put_data = (
            str(time) + '|' + str(ticker) + "|OPEN|" + str(open_gimp) + '|CLOSE|' + str(close_gimp)
            + '|PROFIT|' + str(profit) + '|PROFIT_RATE|' + str(round(float(profit)/(float(balance) * 2) * 100, 3)) + '\n'
    )
    with open(put_path, 'a') as file:
        file.write(put_data)

def load_profit_count(position_data):
    if ENV == 'real':
        load_path = '/root/arbitrage/conf/profit_count.DAT'
    elif ENV == 'local':
        load_path = 'C:/Users/skdba/PycharmProjects/arbitrage/conf/profit_count.DAT'

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
                    position_data[ticker]['front_close_gimp'] = temp_data['front_close_gimp']
                elif ticker not in position_data:
                    position_data[ticker] = json.loads(data)
                logging.info(f"FILE_LOAD|PROFIT_COUNT|{ticker}\n{position_data[ticker]}")
                
            except Exception as e:
                logging.info(e)
    else:
        logging.info(f"{load_path} There is no file")
        

def put_profit_count(position_data):
    put_path = ''
    put_data = ''

    if ENV == 'real':
        put_path = '/root/arbitrage/conf/profit_count.DAT'
    elif ENV == 'local':
        put_path = 'C:/Users/skdba/PycharmProjects/arbitrage/conf/profit_count.DAT'

    for ticker in position_data:
        if position_data[ticker]['profit_count'] >= 1 and position_data[ticker]['position'] == 0:
            put_data += ticker + "|" + json.dumps(position_data[ticker]) + "\n"

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
        #history_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/premium_data_20231107'
        history_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/premium_data'

    if os.path.exists(history_file_path):
        logging.info(history_file_path)
        with open(history_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    else:
        logging.info(f"{history_file_path} 파일이 존재하지 않습니다.")

    return lines
