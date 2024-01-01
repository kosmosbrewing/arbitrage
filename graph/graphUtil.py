import asyncio
import datetime
import logging
import os
import aiohttp
import requests
import telegram

bot = None
chat_id_list = None
ENV = 'real'
TELEGRAM_BOT_TOKEN = "6729803794:AAEEX8oOTfTp2iYXnCrTMcNm7aDwewuGJL0"
TELEGRAM_MESSAGE_MAX_SIZE = 4096

def load_history_data(date):
    # 오늘 날짜 가져오기
    now_date = datetime.date.today()

    if ENV == 'real':
        history_file_path = '/root/arbitrage/log/premium_data_'+ str(date)
    elif ENV == 'local':
        history_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/premium_data_'+ str(date)

    if os.path.exists(history_file_path):
        logging.info(history_file_path)
        with open(history_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    else:
        logging.info(f"{history_file_path} 파일이 존재하지 않습니다.")

    return lines

def load_chat_id():
    load_path = ''
    lines = ''
    # 오늘 날짜 가져오기
    if ENV == 'real':
        load_path = '/root/arbitrage/data/chat_id.DAT'
    elif ENV == 'local':
        load_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/chat_id.DAT'
    
    if os.path.exists(load_path):
        with open(load_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

    else:
        print(f"{load_path} 파일이 존재하지 않습니다.")

    return lines

def put_chat_id(chat_id_list):
    put_path = ''
    put_data = ''

    # 오늘 날짜 가져오기
    if ENV == 'real':
        put_path = '/root/arbitrage/data/chat_id.DAT'
    elif ENV == 'local':
        put_path = 'C:/Users/skdba/PycharmProjects/arbitrage/data/chat_id.DAT'

    if len(chat_id_list) > 0:
        for chat_id in chat_id_list:
            put_data += str(chat_id) + "\n"

        with open(put_path, 'a') as file:
            file.write(put_data)

def get_chat_id():
    print("Telegram Chat ID 요청합니다..")
    try:
        response = requests.get(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates')
        if response.status_code == 200:
            data = response.json()
            chat_id_group = data['result']
            temp_list = []
            for result in chat_id_group:
                temp_list.append(result['message']['chat']['id'])
            chat_id_list = list(set(temp_list))
            print(f"Telegram Chat ID 응답 : {chat_id_list}, Put Chat Id")
            put_chat_id(chat_id_list)
        else:
            print(f"Telegram Chat ID 요청 응답 오류: {response.status}")
    except aiohttp.ClientError as e:
        print(f"Telegram 세션연결 오류: {e}")

def get_chat_id_list():
    print("Telegram Chat ID 요청합니다..")
    try:
        print(f"Load Put Chat Id")
        lines = load_chat_id()
        temp_list = []
        for line in lines:
            chat_id = line.split('\n')[0]
            temp_list.append(chat_id)
        send_chat_id_list = list(set(temp_list))

        return send_chat_id_list
    except Exception as e:
        print(f"Get Chat ID List 오류: {e}")

async def send_to_telegram(message):
    # 텔레그램 메시지 보내는 함수, 최대 3회 연결, 3회 전송 재시도 수행
    global bot

    get_chat_id()
    send_chat_id_list = get_chat_id_list()
    # chat_id_list = ['1109591824'] # 준우
    # chat_id_list = ['2121677449']  # 규빈
    print(f"Telegram Chat ID 값 취득 : {send_chat_id_list}")

    if bot is None:
        print("Telegram 연결 시도...")
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    for chat_id in send_chat_id_list:
        chat_id = int(chat_id)
        for i in range(3):
            try:
                # print(f"Telegram [{chat_id}], msg 전송 {message}")
                await bot.send_message(chat_id, message[:TELEGRAM_MESSAGE_MAX_SIZE])
                break
            except telegram.error.TimedOut as e:
                print(f"Telegram {chat_id} msg 전송 오류... {i + 1} 재시도... : {e}")

                await asyncio.sleep(5)
            except Exception as e:
                print(f"Telegram 연결 해제... {e}")
                bot = None
                break

async def send_to_telegram_image(image):
    # 텔레그램 메시지 보내는 함수, 최대 3회 연결, 3회 전송 재시도 수행
    global bot
    get_chat_id()
    send_chat_id_list = get_chat_id_list()
    # chat_id_list = ['1109591824'] # 준우
    # chat_id_list = ['2121677449']  # 규빈
    print(f"Telegram Chat ID 값 취득 : {send_chat_id_list}")

    if bot is None:
        print("Telegram 연결 시도...")
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    for chat_id in send_chat_id_list:
        chat_id = int(chat_id)
        for i in range(3):
            try:
                await bot.send_photo(chat_id, photo=open(image, 'rb'))
                break
            except telegram.error.TimedOut as e:
                print(f"Telegram {chat_id} msg 전송 오류... {i + 1} 재시도... : {e}")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Telegram 연결 해제... {e}")
                bot = None
                break