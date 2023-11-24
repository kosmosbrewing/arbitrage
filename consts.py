# Enviroment
ENV = 'local'
# Exchanges
UPBIT = 'Upbit'
BINANCE = 'Binance'
# All Exchanges
EXCHANGE_LIST = [UPBIT, BINANCE]
# WEBSOCKET
SOCKET_PING_INTERVAL = 20 # 20초
SOCKET_RETRY_TIME = 30 # 30초
SOCKET_PING_TIMEOUT = 30 # 30초

# TELEGRAM
TELEGRAM_BOT_TOKEN = "6690231866:AAEUWgkWPaML-tx8VplLo4BPE9tabyq-9i8"
TELEGRAM_MESSAGE_MAX_SIZE = 4095

# DELAY
DOLLAR_UPDATE = 5 * 60 # 달러가격 업데이트 주기, 5분
SOCKET_ORDERBOOK_DELAY = 30
COMPARE_PRICE_START_DELAY = 2 * 60
COMPARE_PRICE_DELAY = 10 # 가격비교 최초 실행대기, 5분
CHECK_ORDERBOOK_START_DELAY = 2 * 60 # 호가창 계산 실행대기
TIME_DIFF_CHECK_DELAY = 30 * 60 # 바이낸스 서버와 시간비교 주기, 30분
ORDERBOOK_SIZE = 6 # 호가 상하방 몇틱 저장할 지 지정

CURR_GIMP_GAP = 0.09  # 현재 진입/종료 김프 차이
# 포지션 진입 조건           #
OPEN_INSTALLMENT = 0.1  # 분할 매수 (ex 0.1 - 10분할)
OPEN_GIMP_GAP = 0.17  # 변동성 COUNT 할 김프 조건 (ex. 현재 종료 김프 - 저점 진입 김프 = 0.3)
OPEN_GIMP_COUNT = 0  # 변동성 COUNT 횟수
INSTALL_WEIGHT = 0.75 # 분할 진입 가중치
FRONT_OPEN_COUNT = 75  # 직전 변동성 COUNT 확인 횟수 (ex. 직전 20개 확인)
FRONT_AVERAGE_COUNT = 10  # 직전 진입 평균 김프 확인 횟수 (ex. 직전 10개 확인)
# 포지션 종료 조건           #
CLOSE_GIMP_GAP = 0.6  # 포지션 종료 조건 ( 현재 종료 김프 - 포지션 진입 김프 = 0.8)
CLOSE_INSTALLMENT = 0.25
BTC_GAP = 1.6
POSITION_TICKER_COUNT = 7

# ETC
POSITION_PROFIT_UPDATE = 60 * 60
MILLION = 100000000 # 억
BALANCE = 1000000 # 천만원
UPBIT_FEE = 0.0005
BINANCE_FEE = 0.0004
