# Envirodment
ENV = 'local'

# Exchanges
UPBIT = 'Upbit'
BINANCE = 'Binance'
EXCHANGE_LIST = [UPBIT, BINANCE]

# WEBSOCKET
SOCKET_PING_INTERVAL = 20
SOCKET_RETRY_TIME = 30
SOCKET_PING_TIMEOUT = 30

# TELEGRAM
TELEGRAM_BOT_TOKEN = "6690231866:AAEUWgkWPaML-tx8VplLo4BPE9tabyq-9i8"
TELEGRAM_MESSAGE_MAX_SIZE = 4095

# DELAY
GET_ORDER_DATA_DELAY = 20 * 3600          # Binance Order Data 수신 주기
SOCKET_ORDERBOOK_DELAY = 30
CHECK_ORDERBOOK_START_DELAY = 2 * 60      # 호가창 계산 실행대기
COMPARE_PRICE_START_DELAY = 2 * 60        # ComparePrice 시작 딜레이
COMPARE_PRICE_ORDER_DELAY = 3 * 60        # ComparePrice*Order 시작 딜레이
COMPARE_PRICE_CHECK_DELAY = 90            # ComparePriceOpenCheck 시작 딜레이
COMPARE_PRICE_CHECK = 20                  # ComparePriceOpenCheck 수행 주기
CHECK_REAL_GIMP_DELAY = 60
TIME_DIFF_CHECK_DELAY = 30 * 60           # 바이낸스 서버와 시간비교 주기, 30분
POSITION_PROFIT_UPDATE = 120 * 60         # Position Profit Update 수행 주기

ORDERBOOK_SIZE = 6         # 호가 상하방 몇틱 저장할 지 지정
CURR_GIMP_GAP = 0.2        # 현재 진입/종료 김프 차이
OPEN_GIMP_GAP = 0.15       # 변동성 COUNT 할 김프 조건 (ex. 현재 종료 김프 - 저점 진입 김프 = 0.3)
RE_OPEN_GIMP_GAP = 0.5     # 재진입 티커 김프 조건
OPEN_GIMP_COUNT = 2        # 변동성 COUNT 횟수
INSTALL_WEIGHT = 0.7       # 분할 진입 가중치
FRONT_OPEN_COUNT = 150     # 직전 변동성 COUNT 확인 횟수 (ex. 직전 20개 확인)
FRONT_AVERAGE_COUNT = 360  # 직전 진입 평균 김프 확인 횟수 (ex. 직전 10개 확인)
CLOSE_GIMP_GAP = 0.5       # 포지션 종료 조건 ( 현재 종료 김프 - 포지션 진입 김프 = 0.8)
CLOSE_INSTALLMENT = 0.5    # 분할 종료 가중치
BTC_GAP = 1.4              # BTC 갭
POSITION_MAX_COUNT = 1     # 최대 들어갈 티커 개수
POSITION_CHECK_COUNT = 3   # 진입 중인 다른 티커 김프 확인 개수
GRID_CHECK_GAP = 0.7

# ETC
MILLION = 100000000    # 억
BALANCE = 2500000      # 수행 잔고 (업비트 기준)
UPBIT_FEE = 0.0005     # Upbit 수수료
BINANCE_FEE = 0.0004   # Binanace 수수료
TETHER = 1330          # 기준 환율