import asyncio
import datetime
import logging
import os
from datetime import date

import aiohttp
import telegram

bot = None
chat_id_list = None
ENV = 'real'
TELEGRAM_BOT_TOKEN = "6690231866:AAEUWgkWPaML-tx8VplLo4BPE9tabyq-9i8"
TELEGRAM_MESSAGE_MAX_SIZE = 4096

def load_history_data():
    # 오늘 날짜 가져오기
    now_date = date.today()
    # 하루 전 날짜 계산
    yesterday = now_date - datetime.timedelta(days=1)
    yesterday = yesterday.strftime("%Y%m%d")

    if ENV == 'real':
        history_file_path = '/root/arbitrage/log/premium_data_'+yesterday
    elif ENV == 'local':
        history_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/premium_data_'+yesterday
    
    if os.path.exists(history_file_path):
        print(history_file_path)
        with open(history_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    else:
        print(f"{history_file_path} 파일이 존재하지 않습니다.")

    return lines
async def get_chat_id():
    print("Telegram Chat ID 요청합니다..")
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
                    print(f"Telegram Chat ID 응답 : {chat_id_list}")
                    return chat_id_list
                else:
                    print(f"Telegram Chat ID 요청 응답 오류: {response.status}")
        except aiohttp.ClientError as e:
            print(f"Telegram 세션연결 오류: {e}")
async def send_to_telegram(message):
    # 텔레그램 메시지 보내는 함수, 최대 3회 연결, 3회 전송 재시도 수행
    global bot
    global chat_id_list

    if chat_id_list is None:
        chat_id_list = await get_chat_id()
        #print(f"Telegram Chat ID 값 취득 : {get_chat_id()}")
        # chat_id_list = ['1109591824'] # 준우
        # chat_id_list = ['2121677449']  # 규빈
        chat_id_list = ['1109591824', '2121677449']  #
        print(f"Telegram Chat ID 값 취득 : {chat_id_list}")

    if bot is None:
        print("Telegram 연결 시도...")
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    for chat_id in chat_id_list:
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
    global chat_id_list

    if chat_id_list is None:
        chat_id_list = await get_chat_id()
        chat_id_list = ['1109591824', '2121677449']  #
        print(f"Telegram Chat ID 값 취득 : {chat_id_list}")

    if bot is None:
        print("Telegram 연결 시도...")
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    for chat_id in chat_id_list:
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