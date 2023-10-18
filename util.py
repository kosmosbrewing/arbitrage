import telegram
import asyncio
import aiohttp
import logging
from consts import *
import time
from datetime import datetime, timedelta

bot = None
chat_id_list = None

def setup_logging():
    logging.basicConfig(level=logging.INFO)
    log_file_path = 'C:/Users/skdba/OneDrive/바탕 화면/kosmos/graduate/premium/premium.log'

    # 파일 핸들러 생성 및 설정
    file_handler = logging.FileHandler(filename=log_file_path)
    file_handler.setLevel(logging.INFO)

    # 표준 출력 핸들러 생성 및 설정
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.INFO)

    # 로그 포매터 설정
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] : %(message)s ...(%(filename)s:%(lineno)d)')
    file_handler.setFormatter(formatter)

    # 루트 로거에 핸들러 추가
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    # root_logger.addHandler(console_handler)


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
                # await bot.send_message(chat_id, message[:TELEGRAM_MESSAGE_MAX_SIZE])
                break
            except telegram.error.TimedOut as e:
                logging.info(f"Telegram {chat_id} msg 전송 오류... {i + 1} 재시도... : {e}")
                await asyncio.sleep(5)
            except Exception as e:
                logging.info(f"Telegram 연결 해제... {e}")
                bot = None
                break

def clear_exchange_price(exchange, exchange_price):
    # 소켓연결이 끊어진 경우, 이전까지 받아온 데이터들은 더이상 유효하지 않기 때문에 삭제하는 역할을 하는 함수
    logging.info(f"{exchange} 데이터 클리어 : [{exchange_price}]")
    for ticker in exchange_price:
        if exchange in exchange_price[ticker]:
            del exchange_price[ticker][exchange]

def is_need_reset_socket(start_time):
    #매일 오전 9시인지 확인해 9시가 넘었다면 True를 반환 (Websocket 재연결목적)
    now = datetime.now()
    start_date_base_time = start_time.replace(hour=9, minute=0, second=0,microsecond=0)
    next_base_time = (start_time + timedelta(days=1)).replace(hour=9,minute=0, second=0, microsecond=0)
    if start_time < start_date_base_time:
        if start_date_base_time < now:
            return True
        else:
            return
    if next_base_time < now:
        return True
    else:
        return

async def test():
    await asyncio.wait([
        #asyncio.create_task(get_chat_id())
        asyncio.create_task(send_to_telegram('KOSMOS TEST'))
    ])
    #clear_exchange_price()

if __name__ == '__main__':
    asyncio.run(test())