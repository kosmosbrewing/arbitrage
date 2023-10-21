# Exchanges
UPBIT = 'Upbit'
BINANCE = 'Binance'
FTX = 'FTX'
BYBIT = 'Bybit'
OKX = 'OKX'
BITGET = 'Bitget'
# All Exchanges
EXCHANGE_LIST = [UPBIT, BINANCE]
# EXCHANGE_LIST = [UPBIT, BINANCE]
# WEBSOCKET
SOCKET_PING_INTERVAL = 20 # 20초
SOCKET_RETRY_TIME = 30 # 30초
SOCKET_PING_TIMEOUT = 30 # 30초

# TELEGRAM
TELEGRAM_BOT_TOKEN = "6690231866:AAEUWgkWPaML-tx8VplLo4BPE9tabyq-9i8"
TELEGRAM_MESSAGE_MAX_SIZE = 4095

# DELAY
DOLLAR_UPDATE = 60 * 60 # 달러가격 업데이트 주기, 1시간
SOCKET_ORDERBOOK_DELAY = 30
#COMPARE_PRICE_DELAY = 5 * 10 # 가격비교 최초 실행대기, 5분
COMPARE_PRICE_DELAY = 5 * 60 # 가격비교 최초 실행대기, 5분
CHECK_ORDERBOOK_DELAY = 2 * 60 # 호가창 계산 실행대기
TIME_DIFF_CHECK_DELAY = 30 * 60 # 바이낸스 서버와 시간비교 주기, 30분

ORDERBOOK_SIZE = 5 # 호가 상하방 몇틱 저장할 지 지정

# ETC
MILLION = 100000000 # 억
BALANCE = 10000000 # 천만원
NOTI_GAP_STANDARD = 0.1 # TODO 거래소간 차이가 발생할 때 알림을 보낼 기준(%) 개인별로 설정
