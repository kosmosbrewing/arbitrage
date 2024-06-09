source ~/.bash_profile

echo "[$(date +'%Y-%m-%d %H:%M:%S')] backtest.sh"

conda activate premium

sleep 3 


# ARGUMENT 순서
# CURR_GIMP_GAP  = 0.2         - 현재 진입/종료 김프 차이
# OPEN_INSTALL = 0.1           - 분할 매수 (ex 0.1 - 10분할)
# OPEN_GIMPGAP = 0.3           - 변동성 COUNT 할 김프 조건 (ex. 현재 종료 김프 - 저점 진입 김프 = 0.3)
# OPEN_GIMPCNT = 3             - 변동성 COUNT 횟수
# INSTALL_WEIGHT = 0.6         - 분할매수 가중치
# FRONT_OPENCNT = 200          - 직전 변동성 COUNT 확인 횟수 (ex. 직전 20개 확인)
# FRONT_AVGCNT = 200           - 직전 진입 평균 김프 확인 횟수 (ex. 직전 10개 확인)
# CLOSE_GIMPGAP = 0.4          - 포지션 종료 조건 ( 현재 종료 김프 - 포지션 진입 김프 = 0.4)
# CLOSE_INSTALLMENT = 0.25     - 분할 손절
# BTC_GAP = 1.5                - BTC 김프와의 GAP
# POSITION_TICKER_COUNT        - 동시에 진입 가능한 티커 개수

#python3 /root/arbitrage/backTestMain.py 0.2  0.1 0.17 1 0.75   75  5 0.6 1/4 1.6 5 0.5
#python3 /root/arbitrage/backTestMain.py 0.2  0.1 0.17 2 0.75   75  5 0.6 1/4 1.6 5 0.5
#python3 /root/arbitrage/backTestMain.py 0.2  0.1 0.17 3 0.75   75  5 0.6 1/4 1.6 7 0.5
python3 /root/arbitrage/backtest/backTestMain.py 0.2 0.1 0.15 1 0.65   75  5 0.6 1/4 1.4 8 0.5
python3 /root/arbitrage/backtest/backTestMain.py 0.2 0.1 0.15 2 0.65   75  5 0.6 1/4 1.4 8 0.5
python3 /root/arbitrage/backtest/backTestMain.py 0.2 0.1 0.15 3 0.65   75  5 0.6 1/4 1.4 8 0.5
