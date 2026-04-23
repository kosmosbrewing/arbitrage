import logging

from command_handlers import (
    handle_current,
    handle_graph,
    handle_order,
    handle_restart,
    handle_set_close,
    handle_set_grid,
    send_error,
)
import util
from consts import *
from aiogram import Bot, Dispatcher, executor, types

class Premium:
    def __init__(self):
        self.exchange_data = {}  # 거래소별 가격 데이터를 저장할 딕셔너리
        self.orderbook_info = {}  # 거래소별 호가 데이터 저장
        self.orderbook_check = {}
        self.check_data = {}
        self.trade_data = {}
        self.position_data = {}
        self.acc_ticker_count = {}
        self.acc_ticker_data = {}
        self.remain_bid_balance = {"balance": BALANCE}
        self.position_ticker_count = {"count": 0, "open_gimp_limit": 0}
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set")
        if TELEGRAM_CHAT_ID <= 0:
            raise ValueError("TELEGRAM_CHAT_ID is not set")
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.allowed_chat_id = TELEGRAM_CHAT_ID

        util.setup_order_logging()

        # 경고 메시지를 무시하기 위해 logging 레벨을 조정
        logging.getLogger('matplotlib').setLevel(logging.WARNING)

        dp = Dispatcher(self.bot)
        dp.register_message_handler(self.current, commands="current")
        dp.register_message_handler(self.graph, commands="graph")
        dp.register_message_handler(self.set_grid, commands="set_grid")
        dp.register_message_handler(self.order, commands="order")
        dp.register_message_handler(self.restart, commands="restart")
        dp.register_message_handler(self.set_close, commands="set_close")
        executor.start_polling(dp)

    async def current(self, message: types.Message):
        chat_id = message.chat.id

        if chat_id != self.allowed_chat_id:
            await message.reply("죄송합니다. 이 채팅에 참여할 권한이 없습니다.")
        else:
            try:
                await handle_current(self)
            except Exception:
                await send_error(self.bot, self.allowed_chat_id)

    async def order(self, message: types.Message):
        command, *args = message.text.split()

        chat_id = message.chat.id

        if chat_id != self.allowed_chat_id:
            await message.reply("죄송합니다. 이 채팅에 참여할 권한이 없습니다.")
        else:
            if not args:
                await message.reply("🌚 Flag를 입력 하세요. (open/close/stop_open/init)")
                return
            try:
                await handle_order(self.bot, self.allowed_chat_id, args)
            except Exception:
                await send_error(self.bot, self.allowed_chat_id)

    async def set_grid(self, message: types.Message):
        command, *args = message.text.split()

        chat_id = message.chat.id

        if chat_id != self.allowed_chat_id:
            await message.reply("죄송합니다. 이 채팅에 참여할 권한이 없습니다.")
        else:
            if not args:
                await message.reply("🌚 숫자를 입력 하세요.")
                return
            try:
                await handle_set_grid(self.bot, self.allowed_chat_id, args)
            except Exception:
                await send_error(self.bot, self.allowed_chat_id)

    async def set_close(self, message: types.Message):
        command, *args = message.text.split()

        chat_id = message.chat.id

        if chat_id != self.allowed_chat_id:
            await message.reply("죄송합니다. 이 채팅에 참여할 권한이 없습니다.")
        else:
            if not args:
                await message.reply("🌚 숫자를 입력 하세요.")
                return
            try:
                await handle_set_close(self.bot, self.allowed_chat_id, args)
            except Exception:
                await send_error(self.bot, self.allowed_chat_id)

    async def restart(self, message: types.Message):
        command, *args = message.text.split()

        chat_id = message.chat.id

        if chat_id != self.allowed_chat_id:
            await message.reply("죄송합니다. 이 채팅에 참여할 권한이 없습니다.")
        else:
            try:
                await handle_restart(self.bot, self.allowed_chat_id)
            except Exception:
                await send_error(self.bot, self.allowed_chat_id)

    async def graph(self, message: types.Message):
        command, *args = message.text.split()
        chat_id = message.chat.id

        if chat_id != self.allowed_chat_id:
            await message.reply("죄송합니다. 이 채팅에 참여할 권한이 없습니다.")
        else:
            if not args:
                await message.reply("🌚 날짜를 입력 하세요.")
                return

            date = args[0]
            try:
                await handle_graph(date)
            except Exception:
                await send_error(self.bot, self.allowed_chat_id)

if __name__ == "__main__":
    premium = Premium()
