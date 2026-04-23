import logging

from matplotlib import pyplot as plt

from api import upbit
from consts import ENV
from graph import graphUtil


def _image_file_path(date):
    if ENV == 'real':
        return '/root/arbitrage/image/arbitrage_' + str(date)
    return 'C:/Users/skdba/PycharmProjects/arbitrage/image/arbitrage_' + str(date)


async def _load_measure_ticker():
    temp_list = {}
    measure_ticker = {}

    try:
        await upbit.accum_top_ticker(temp_list)
        logging.info(temp_list)
    except Exception as exc:
        logging.info(exc)

    for ticker in temp_list.get('upbit_top_ticker', []):
        measure_ticker[ticker] = {"units": []}

    measure_ticker['USDT'] = {"units": []}
    return measure_ticker


def _fill_measure_ticker(lines, measure_ticker):
    front_gap = {}
    graph_date = None

    for line in lines:
        try:
            split_data = line.split('|')
            date_time = split_data[0].split('[INFO')[0]
            graph_date = date_time.split(' ')[0].split('[')[1]
            date_hour = date_time.split(' ')[1].split(':')[0]
            date_min = date_time.split(' ')[1].split(':')[1]
            date_second = date_time.split(' ')[1].split(':')[2].split(',')[0]
            hour_min_second = date_hour + ":" + date_min + ":" + date_second

            ticker = split_data[1]
            open_gap = float(split_data[3])
            close_gap = float(split_data[6])
            btc_open_gap = float(split_data[9])
            upbit_15_rsi = float(split_data[17].split('/')[0])
            binance_15_rsi = float(split_data[19].split('/')[0])
            upbit_240_rsi = float(split_data[17].split('/')[1])
            binance_240_rsi = float(split_data[19].split('/')[1])
            rsi_15_gap = float(split_data[21].split('/')[0])
            rsi_240_gap = float(split_data[21].split('/')[1])
        except Exception:
            continue

        if ticker not in front_gap:
            front_gap[ticker] = {
                "front_open_gap": open_gap,
                "front_close_gap": close_gap,
                "front_btc_open_gap": btc_open_gap,
            }

        try:
            front_open_gap = front_gap[ticker]['front_open_gap']
            front_close_gap = front_gap[ticker]['front_close_gap']
            front_btc_open_gap = front_gap[ticker]['front_btc_open_gap']

            if (
                abs(open_gap - front_open_gap) > 1
                or abs(close_gap - front_close_gap) > 1
                or abs(btc_open_gap - front_btc_open_gap) > 1
            ):
                continue

            front_gap[ticker]['front_open_gap'] = open_gap
            front_gap[ticker]['front_close_gap'] = close_gap
            front_gap[ticker]['front_btc_open_gap'] = btc_open_gap

            if ticker in measure_ticker:
                measure_ticker[ticker]['units'].append({
                    "open_gap": open_gap,
                    "close_gap": close_gap,
                    "btc_open_gap": btc_open_gap,
                    "hour_min_second": hour_min_second,
                    "upbit_15_rsi": upbit_15_rsi,
                    "binance_15_rsi": binance_15_rsi,
                    "upbit_240_rsi": upbit_240_rsi,
                    "binance_240_rsi": binance_240_rsi,
                    "rsi_15_gap": rsi_15_gap,
                    "rsi_240_gap": rsi_240_gap,
                })
        except Exception as exc:
            logging.info(exc)

    return graph_date


def _build_graph_images(image_file_path, graph_date, measure_ticker):
    subplot_loc = []
    for _ in range(0, 100):
        subplot_loc.append([421, 423, 425, 427, 422, 424, 426, 428])

    figure_idx = 0
    subplot_idx = 0
    image_set = []
    remain_dix = 0

    for graph_ticker in measure_ticker:
        open_gap = []
        close_gap = []
        btc_open_gap = []
        upbit_15_rsi = []
        upbit_240_rsi = []
        binance_15_rsi = []
        binance_240_rsi = []
        rsi_15_gap = []
        rsi_240_gap = []
        time = []
        remain_dix = 0

        try:
            for idx in range(0, len(measure_ticker[graph_ticker]['units'])):
                unit = measure_ticker[graph_ticker]['units'][idx]
                open_gap.append(float(unit['open_gap']))
                close_gap.append(float(unit['close_gap']))
                btc_open_gap.append(float(unit['btc_open_gap']))
                time.append(unit['hour_min_second'])
                upbit_15_rsi.append(float(unit['upbit_15_rsi']))
                upbit_240_rsi.append(float(unit['upbit_240_rsi']))
                binance_15_rsi.append(float(unit['binance_15_rsi']))
                binance_240_rsi.append(float(unit['binance_240_rsi']))
                rsi_15_gap.append(float(unit['rsi_15_gap']))
                rsi_240_gap.append(float(unit['rsi_240_gap']))
        except Exception as exc:
            logging.info(f"Exception : {exc}")

        time_len = len(time)
        if time_len == 0:
            continue

        try:
            show_x_values = [
                time[0],
                time[round(time_len / 6)],
                time[round(time_len * 2 / 6)],
                time[round(time_len * 3 / 6)],
                time[round(time_len * 4 / 6)],
                time[round(time_len * 5 / 6)],
                time[time_len - 1],
            ]

            plt.figure(figure_idx, figsize=(18, 12))
            plt.subplot(subplot_loc[figure_idx][subplot_idx])
            plt.title(graph_ticker + '[' + graph_date + ']')
            plt.plot(time, open_gap, label='open', color='blue', linewidth=0.6)
            plt.plot(time, close_gap, label='close', color='red', linewidth=0.6)
            plt.plot(time, btc_open_gap, label='open', color='black', linewidth=0.6)
            plt.ylabel('gap')
            plt.xticks(show_x_values)
            for val in show_x_values:
                plt.axvline(x=val, color='lightgray', linestyle='--', linewidth=0.7)
            subplot_idx += 1

            plt.figure(figure_idx, figsize=(18, 12))
            plt.subplot(subplot_loc[figure_idx][subplot_idx])
            plt.plot(time, rsi_15_gap, label='open', color='purple', linewidth=0.6)
            plt.ylabel('rsi_15_gap')
            plt.xticks(show_x_values)
            for val in show_x_values:
                plt.axvline(x=val, color='lightgray', linestyle='--', linewidth=0.7)
            subplot_idx += 1

            plt.figure(figure_idx, figsize=(18, 12))
            plt.subplot(subplot_loc[figure_idx][subplot_idx])
            plt.plot(time, rsi_240_gap, label='open', color='pink', linewidth=0.6)
            plt.ylabel('rsi_240_gap')
            plt.xticks(show_x_values)
            for val in show_x_values:
                plt.axvline(x=val, color='lightgray', linestyle='--', linewidth=0.7)
            subplot_idx += 1

            plt.figure(figure_idx, figsize=(18, 12))
            plt.subplot(subplot_loc[figure_idx][subplot_idx])
            dark_yellow = '#FFB700'
            plt.plot(time, upbit_15_rsi, label='open', color='blue', linewidth=0.3)
            plt.plot(time, binance_15_rsi, label='open', color=dark_yellow, linewidth=0.3)
            plt.plot(time, upbit_240_rsi, label='open', color='blue', linewidth=1.75)
            plt.plot(time, binance_240_rsi, label='open', color=dark_yellow, linewidth=1.75)
            plt.ylabel('rsi 15/240')
            plt.xticks(show_x_values)
            for val in show_x_values:
                plt.axvline(x=val, color='lightgray', linestyle='--', linewidth=0.7)
            subplot_idx += 1

            if subplot_idx == len(subplot_loc[0]):
                image_temp = image_file_path + '_' + str(figure_idx + 1) + '.png'
                image_set.append(image_temp)
                plt.savefig(image_temp, format='png')
                figure_idx += 1
                subplot_idx = 0
                remain_dix = 1
        except Exception as exc:
            logging.info(f"{graph_ticker} 오류.. Continue... {exc}")

    if subplot_idx != len(subplot_loc[0]) and remain_dix == 0:
        image_temp = image_file_path + '_' + str(figure_idx + 1) + '.png'
        image_set.append(image_temp)
        plt.savefig(image_temp, format='png')

    return list(set(image_set))


async def handle_graph(date):
    logging.info(f"그래프 기준 일자: {date}")
    image_file_path = _image_file_path(date)
    lines = graphUtil.load_history_data(date)
    measure_ticker = await _load_measure_ticker()
    graph_date = _fill_measure_ticker(lines, measure_ticker) or date
    image_set = _build_graph_images(image_file_path, graph_date, measure_ticker)

    graph_message = '[News Coo 🦤]\n🔵진입김프(UPBIT⬆️/BINANCE⬇️)|\n🔴탈출김프(UPBIT⬇️/BINANCE⬆️)|\n⚫️Bitcoin진입김프(UPBIT⬆️/BINANCE⬇️)'
    await graphUtil.send_to_telegram(graph_message)

    for image in image_set:
        await graphUtil.send_to_telegram_image(image)
