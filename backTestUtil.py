from logging.handlers import TimedRotatingFileHandler
import logging
import datetime
import os
from consts import *

bot = None
chat_id_list = None
# 오늘 날짜 가져오기
now_date = datetime.date.today()
today = now_date.strftime("%Y%m%d")
# 하루 전 날짜 계산
yesterday = now_date - datetime.timedelta(days=1)
yesterday = yesterday.strftime("%Y%m%d")

def setup_logging():
    logging.basicConfig(level=logging.INFO)
    # TimedRotatingFileHandler를 설정하여 날짜별로 로그 파일을 회전
    if ENV == 'real':
        log_file_path = '/root/arbitrage/log/backtest.log_' + today
    elif ENV == 'local':
        log_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/backtest.log'

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

def load_history_data():
    # 오늘 날짜 가져오기
    if ENV == 'real':
        history_file_path = '/root/arbitrage/log/premium_data_' + yesterday
        history_file_path = '/root/arbitrage/log/premium_data_all'
    elif ENV == 'local':
        history_file_path = 'C:/Users/skdba/PycharmProjects/arbitrage/log/premium_data_all'

    if os.path.exists(history_file_path):
        print(history_file_path)
        with open(history_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    else:
        print(f"{history_file_path} 파일이 존재하지 않습니다.")

    return lines
