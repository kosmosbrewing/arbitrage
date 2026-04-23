import os


def _get_env_int(name, default=0):
    value = os.getenv(name)
    if value in (None, ""):
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_env_choice(name, default, allowed_values):
    value = os.getenv(name, default)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in allowed_values:
        return normalized
    return default


# Envirodment
ENV = 'local'

# Exchanges
UPBIT = 'Upbit'
BINANCE = 'Binance'
BITHUMB = 'Bithumb'
EXCHANGE_LIST = [UPBIT, BINANCE, BITHUMB]

# WEBSOCKET
SOCKET_PING_INTERVAL = 30
SOCKET_RETRY_TIME = 10
SOCKET_PING_TIMEOUT = 30

# TELEGRAM
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = _get_env_int("TELEGRAM_CHAT_ID", 0)
TELEGRAM_MESSAGE_MAX_SIZE = 4095

# EXECUTION
EXECUTION_MODE = _get_env_choice("EXECUTION_MODE", "paper", {"paper", "live"})

# DELAY
GET_ORDER_DATA_DELAY = 20 * 3600          # Binance Order Data 수신 주기
GET_TOP_TICKER_DELAY = 60 * 60            # UPBIT TOP TICKER 수신 주기
SOCKET_ORDERBOOK_DELAY = 15
CHECK_ORDERBOOK_START_DELAY = 60          # 호가창 계산 실행대기
COMPARE_PRICE_START_DELAY = 2 * 60        # ComparePrice 시작 딜레이
COMPARE_PRICE_ORDER_DELAY = 3 * 60        # ComparePriceOrder OPEN/CLOSE 시작 딜레이
COMPARE_PRICE_CHECK_DELAY = 90            # ComparePriceCheck 시작 딜레이
CHECK_REAL_GIMP_DELAY = 95		  # CheckRealGimp 시작 딜레이 
COMPARE_PRICE_ORDER = 10                  # ComparePriceOrder OPEN/CLOSE 수행 주기
COMPARE_PRICE_CHECK = 20                  # ComparePriceCheck 수행 주기
CHECK_REAL_GIMP = 20                      # CheckRealGimp 수행 주기
TIME_DIFF_CHECK_DELAY = 30 * 60           # 바이낸스 서버와 시간비교 주기, 30분
POSITION_PROFIT_UPDATE = 120 * 60         # Position Profit Update 수행 주기

ORDERBOOK_SIZE = 7         # 호가 상하방 몇틱 저장할 지 지정
CURR_GIMP_GAP = 0.2        # 현재 진입/종료 김프 차이
OPEN_INSTALLMENT = 0.33
OPEN_GIMP_GAP = 0.15       # 변동성 COUNT 할 김프 조건 (ex. 현재 종료 김프 - 저점 진입 김프 = 0.3)
RE_OPEN_GIMP_GAP = 0.5     # 재진입 티커 김프 조건
OPEN_GIMP_COUNT = 3        # 변동성 COUNT 횟수
OPEN_LIMIT_COUNT = 75
INSTALL_WEIGHT = 0.33      # 분할 진입 가중치
FRONT_OPEN_COUNT = 150     # 직전 변동성 COUNT 확인 횟수 (ex. 직전 20개 확인)
FRONT_AVERAGE_COUNT = 600  # 직전 진입 평균 김프 확인 횟수 (ex. 직전 10개 확인)
CLOSE_GIMP_GAP = 0.5         # 포지션 종료 조건 ( 현재 종료 김프 - 포지션 진입 김프 = 0.8)
CLOSE_INSTALLMENT = 1    # 분할 종료 가중치
BTC_GAP = 1.2              # BTC 갭
POSITION_MAX_COUNT = 4     # 최대 들어갈 티커 개수
POSITION_CHECK_COUNT = 3   # 진입 중인 다른 티커 김프 확인 개수
GRID_CHECK_GAP = 0.5
LEVERAGE = 1
OPEN_TS_GRID=0.15
CLOSE_TS_GRID=0.15
OPEN_TS_COUNT=5
CLOSE_TS_COUNT=5


# ETC
MILLION = 100000000    # 억
BALANCE = 100000000      # 수행 잔고 (업비트 기준)
UPBIT_FEE = 0.0005     # Upbit 수수료
BINANCE_FEE = 0.0005   # Binanace 수수료
TETHER = 1330          # 기준 환율
