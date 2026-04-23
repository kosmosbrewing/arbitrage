import asyncio
import logging

import aiohttp
import telegram

from consts import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_MESSAGE_MAX_SIZE

bot = None
chat_id_list = None


def _default_chat_ids():
    if TELEGRAM_CHAT_ID > 0:
        return [TELEGRAM_CHAT_ID]
    return []


async def get_chat_id():
    if not TELEGRAM_BOT_TOKEN:
        logging.info("TELEGRAM_BOT_TOKEN is not set; skipping Telegram chat id lookup")
        return _default_chat_ids()

    logging.info("Telegram Chat ID 요청합니다..")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates') as response:
                if response.status == 200:
                    data = await response.json()
                    chat_id_group = data['result']
                    current_chat_ids = []
                    for result in chat_id_group:
                        current_chat_ids.append(result['message']['chat']['id'])
                    current_chat_ids = list(set(current_chat_ids))
                    logging.info(f"Telegram Chat ID 응답 : {current_chat_ids}")
                    if len(current_chat_ids) > 0:
                        return current_chat_ids
                    return _default_chat_ids()

                logging.info(f"Telegram Chat ID 요청 응답 오류: {response.status}")
        except aiohttp.ClientError as exc:
            logging.info(f"Telegram 세션 연결 오류: {exc}")

    return _default_chat_ids()


async def send_to_telegram(message):
    global bot
    global chat_id_list

    if not TELEGRAM_BOT_TOKEN:
        logging.info("TELEGRAM_BOT_TOKEN is not set; skipping Telegram message send")
        return

    if chat_id_list is None:
        chat_id_list = await get_chat_id()
    if not chat_id_list:
        chat_id_list = _default_chat_ids()
    if not chat_id_list:
        logging.info("TELEGRAM_CHAT_ID is not set; skipping Telegram message send")
        return

    if bot is None:
        logging.info(f"Telegram Chat ID 값 취득 : {chat_id_list}")
        logging.info("Telegram 연결 시도...")
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    for chat_id in chat_id_list:
        for retry in range(3):
            try:
                await bot.send_message(chat_id, message[:TELEGRAM_MESSAGE_MAX_SIZE])
                break
            except telegram.error.TimedOut as exc:
                logging.info(f"Telegram {chat_id} msg 전송 오류... {retry + 1} 재시도... : {exc}")
                await asyncio.sleep(5)
            except Exception as exc:
                logging.info(f"Telegram 연결 해제... {exc}")
                bot = None
                break


async def send_to_telegram_image(image):
    global bot
    global chat_id_list

    if not TELEGRAM_BOT_TOKEN:
        logging.info("TELEGRAM_BOT_TOKEN is not set; skipping Telegram image send")
        return

    message = '[News Coo 🦤]\n🔵진입김프(UPBIT⬆️/BINANCE⬇️)|\n🔴탈출김프(UPBIT⬇️/BINANCE⬆️)|\n⚫️Bitcoin진입김프(UPBIT⬆️/BINANCE⬇️)'
    if chat_id_list is None:
        chat_id_list = await get_chat_id()
    if not chat_id_list:
        chat_id_list = _default_chat_ids()
    if not chat_id_list:
        logging.info("TELEGRAM_CHAT_ID is not set; skipping Telegram image send")
        return

    if bot is None:
        logging.info(f"Telegram Chat ID 값 취득 : {chat_id_list}")
        logging.info("Telegram 연결 시도...")
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    for chat_id in chat_id_list:
        for retry in range(3):
            try:
                await bot.send_message(chat_id, message[:TELEGRAM_MESSAGE_MAX_SIZE])
                await bot.send_photo(chat_id, photo=open(image, 'rb'))
                break
            except telegram.error.TimedOut as exc:
                logging.info(f"Telegram {chat_id} msg 전송 오류... {retry + 1} 재시도... : {exc}")
                await asyncio.sleep(5)
            except Exception as exc:
                logging.info(f"Telegram 연결 해제... {exc}")
                bot = None
                break
