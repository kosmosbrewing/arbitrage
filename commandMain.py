from matplotlib import pyplot as plt
import util
import traceback
import logging
import subprocess

from api import upbit
from consts import *
from aiogram import Bot, Dispatcher, executor, types
from graph import graphUtil

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
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.allowed_chat_id = 2121677449

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
        self.orderbook_check = {}
        self.position_data = {}
        self.trade_data = {}
        self.remain_bid_balance = {"balance": BALANCE}
        self.position_ticker_count = {"count": 0, "open_gimp_limit": 0}

        chat_id = message.chat.id

        if chat_id != self.allowed_chat_id:
            await message.reply("죄송합니다. 이 채팅에 참여할 권한이 없습니다.")
        else:
            util.load_orderbook_check(self.orderbook_check)
            util.load_remain_position(self.position_data, self.trade_data, self.position_ticker_count)
            util.load_close_mode(self.exchange_data)

            for ticker in self.position_data:
                if self.position_data[ticker]['position'] == 1:
                    self.remain_bid_balance['balance'] -= self.trade_data[ticker]['open_bid_price_acc'] - self.trade_data[ticker]['close_bid_price_acc']

            message = util.get_profit_position(self.orderbook_check, self.position_data, self.trade_data, self.remain_bid_balance, self.exchange_data)
            await self.bot.send_message(chat_id=self.allowed_chat_id , text=message)

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
                flag = args[0]
                ticker = args[1]
                order_flag = {}

                if flag == 'open':
                    order_flag = {"open": 1, "close": 0, "ticker": ticker}
                elif flag == 'close':
                    order_flag = {"open": 0, "close": 1, "ticker": ticker}
                elif flag == 'stop_open':
                    order_flag = {"open": -1, "close": 0, "ticker": ticker}
                elif flag == 'init':
                    order_flag = {"open": 0, "close": 0, "ticker": ticker}

                util.put_order_flag(order_flag)

                message = f"🌝 진입/종료 강제 Flag 설정 완료 : {order_flag}"
                await self.bot.send_message(chat_id=self.allowed_chat_id, text=message)
            except Exception as e:
                message = '🌚 오류 발생..'
                await self.bot.send_message(chat_id=self.allowed_chat_id, text=message)
                logging.info(traceback.format_exc())

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
                low_gimp = args[0]

                exchange_data = {}
                exchange_data['low_gimp'] = low_gimp

                util.put_low_gimp(exchange_data)

                message = f"🌝 진입 그리드 최저 값 설정 : {exchange_data}%"
                await self.bot.send_message(chat_id=self.allowed_chat_id, text=message)

            except Exception as e:
                message = '🌚 오류 발생..'
                await self.bot.send_message(chat_id=self.allowed_chat_id, text=message)
                logging.info(traceback.format_exc())

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
                close_mode = args[0]

                exchange_data = {}
                exchange_data['close_mode'] = close_mode

                util.put_close_mode(exchange_data)

                message = f"🌝 종료 모드 설정 : {exchange_data}\n"
                await self.bot.send_message(chat_id=self.allowed_chat_id, text=message)

            except Exception as e:
                message = '🌚 오류 발생..'
                await self.bot.send_message(chat_id=self.allowed_chat_id, text=message)
                logging.info(traceback.format_exc())

    async def restart(self, message: types.Message):
        command, *args = message.text.split()

        chat_id = message.chat.id

        if chat_id != self.allowed_chat_id:
            await message.reply("죄송합니다. 이 채팅에 참여할 권한이 없습니다.")
        else:
            try:
                # 실행할 명령어
                execute_shell = "/root/arbitrage/bin/main_restart.sh"  # 예: 리눅스의 경우 "ls", 윈도우의 경우 "dir"

                # subprocess.Popen을 사용하여 명령어 실행
                process = subprocess.Popen(execute_shell, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # 명령어 실행 결과를 가져오기
                output, error = process.communicate()

                # 에러 출력 (있으면)
                if error:
                    message = f"🌚 Main Restart 수행 실패"
                    await self.bot.send_message(chat_id=self.allowed_chat_id, text=message)
                    logging.info(error.decode("utf-8"))
                else:
                    message = f"🌝 Main Restart 수행 성공!"
                    await self.bot.send_message(chat_id=self.allowed_chat_id, text=message)

            except Exception as e:
                message = '🌚 오류 발생..'
                await self.bot.send_message(chat_id=self.allowed_chat_id, text=message)
                logging.info(traceback.format_exc())

    async def graph(self, message: types.Message):
        command, *args = message.text.split()

        chat_id = message.chat.id

        if chat_id != self.allowed_chat_id:
            await message.reply("죄송합니다. 이 채팅에 참여할 권한이 없습니다.")
        else:

            if not args:
                await message.reply("🌚 날짜를 입력 하세요.")
                return

            # 입력된 날짜를 추출
            date = args[0]
            logging.info(f"그래프 기준 일자: {date}")
            try:
                if ENV == 'real':
                    image_file_path = '/root/arbitrage/image/arbitrage_' + str(date)
                elif ENV == 'local':
                    image_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/image/arbitrage_' + str(date)

                lines = graphUtil.load_history_data(date)

                plt.clf()
                front_gap = {}
                measure_ticker = {}
                exchange_data = {}

                util.load_top_ticker(exchange_data)
                logging.info(f"TOP TICKER {exchange_data}")
                for ticker in exchange_data['upbit_top_ticker']:
                    measure_ticker[ticker] = {"units": []}

                for line in lines:
                    try:
                        split_data = line.split('|')
                        date_time = split_data[0].split('[INFO')[0]
                        date = date_time.split(' ')[0].split('[')[1]
                        date_hour = date_time.split(' ')[1].split(':')[0]
                        date_min = date_time.split(' ')[1].split(':')[1]
                        date_second = date_time.split(' ')[1].split(':')[2].split(',')[0]
                        hour_min_second = date_hour + ":" + date_min + ":" + date_second

                        ticker = split_data[1]
                        open_gap = float(split_data[3])
                        close_gap = float(split_data[6])
                        btc_open_gap = float(split_data[9])
                    except:
                        continue

                    if ticker not in front_gap:
                        front_gap[ticker] = {"front_open_gap": open_gap, "front_close_gap": close_gap,
                                             "front_btc_open_gap": btc_open_gap}

                    front_open_gap = front_gap[ticker]['front_open_gap']
                    front_close_gap = front_gap[ticker]['front_close_gap']
                    front_btc_open_gap = front_gap[ticker]['front_btc_open_gap']

                    if abs(open_gap - front_open_gap) > 3 or abs(close_gap - front_close_gap) > 3 or abs(btc_open_gap - front_btc_open_gap) > 3:
                        continue

                    front_gap[ticker]['front_open_gap'] = open_gap
                    front_gap[ticker]['front_close_gap'] = close_gap
                    front_gap[ticker]['front_btc_open_gap'] = btc_open_gap

                    # 전일자 데이터 담기
                    if ticker in measure_ticker:
                        measure_ticker[ticker]['units'].append({"open_gap": open_gap, "close_gap": close_gap,
                                                                "btc_open_gap": btc_open_gap, "hour_min_second": hour_min_second})

                # 그래프 변수 초기화
                subplot_loc = []
                for i in range(0, 100):
                    subplot_loc.append([221, 222, 223, 224])

                figure_idx = 0
                subplot_idx = 0
                image_set = []

                delete_ticker = []
                for ticker in measure_ticker:
                    if len(measure_ticker[ticker]['units']) < 10:
                        logging.info(f"Graph 출력 티커 제거 {ticker}")
                        delete_ticker.append(ticker)

                for ticker in delete_ticker:
                    del measure_ticker[ticker]

                for graph_ticker in measure_ticker:
                    # 데이터 준비
                    open_gap = []
                    close_gap = []
                    btc_open_gap = []
                    time = []

                    for i in range(0, len(measure_ticker[graph_ticker]['units'])):
                        open_gap.append(float(measure_ticker[graph_ticker]['units'][i]['open_gap']))
                        close_gap.append(float(measure_ticker[graph_ticker]['units'][i]['close_gap']))
                        btc_open_gap.append(float(measure_ticker[graph_ticker]['units'][i]['btc_open_gap']))
                        time.append(measure_ticker[graph_ticker]['units'][i]['hour_min_second'])

                    time_len = len(time)

                    # 그래프 그리기
                    if subplot_idx == 0:
                        plt.figure(figure_idx, figsize=(18, 12))           # 그래프 크기
                    plt.subplot(subplot_loc[figure_idx][subplot_idx])  # 그래프 위치
                    plt.title(graph_ticker + '[' + date + ']')

                    plt.xlabel('time')
                    plt.ylabel('gap')

                    plt.plot(time, open_gap, label='open', color='blue', linewidth=0.6)
                    plt.plot(time, close_gap, label='close', color='red', linewidth=0.6)
                    plt.plot(time, btc_open_gap, label='open', color='black', linewidth=0.6)

                    show_x_values = [time[0], time[round(time_len / 6)], time[round(time_len * 2 / 6)],
                                     time[round(time_len * 3 / 6)], time[round(time_len * 4 / 6)],
                                     time[round(time_len * 5 / 6)], time[time_len - 1]]

                    plt.xticks(show_x_values)
                    for val in show_x_values:
                        plt.axvline(x=val, color='lightgray', linestyle='--', linewidth=0.7)

                    subplot_idx += 1

                    if subplot_idx == 4:
                        image_temp = image_file_path + '_' + str(figure_idx + 1) + '.png'
                        image_set.append(image_temp)
                        plt.savefig(image_temp, format='png')
                        figure_idx += 1
                        subplot_idx = 0
                        plt.close('all')

                if subplot_idx > 0:
                    image_temp = image_file_path + '_' + str(figure_idx + 1) + '.png'
                    image_set.append(image_temp)
                    plt.savefig(image_temp, format='png')

                message = f'[News Coo 🦤] 기준일자: {date}\n🔵진입김프|🔴탈출김프|⚫️Bitcoin진입김프'
                await self.bot.send_message(chat_id=self.allowed_chat_id, text=message)

                for image in image_set:
                    with open(image, 'rb') as photo:
                        logging.info(f"Send Photo {photo}")
                        await self.bot.send_photo(chat_id=self.allowed_chat_id, photo=photo)

            except Exception as e:
                message = '🌚 오류 발생..'
                await self.bot.send_message(chat_id=self.allowed_chat_id, text=message)
                logging.info(traceback.format_exc())

if __name__ == "__main__":
    premium = Premium()