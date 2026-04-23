# Kimchi Premium Arbitrage — 수학적 모델

> Created: 2026-04-06
> Status: ✅ Confirmed

---

## 김프 (Korea Premium) 정의

```
김프(%) = (한국 거래소 가격 / (글로벌 거래소 가격 × 환율) - 1) × 100
```

### 시뮬레이션 모드 (현재 활성)
```
open_gimp  = (Upbit_balance_ask_avg / Binance_balance_bid_avg) × 100 - 100
close_gimp = (Upbit_balance_bid_avg / Binance_balance_ask_avg) × 100 - 100

Upbit_balance_ask_avg  : Upbit 매도 호가 VWAP (KRW)
Binance_balance_bid_avg: Binance 매수 호가 VWAP (USDT)
```

주의: 환율 곱셈 없이 KRW/USDT 직접 나눗셈. 절대 김프(%)가 아닌 교차환율 비율.
티커 간 상대 비교, 진입-청산 간 차이 계산에서만 유의미.

### 라이브 모드 (삼중 따옴표 블록 — 주석 해제 시 활성)
```
order_open_gimp = upbit_fill_price / (binance_fill_price × TETHER) × 100 - 100

upbit_fill_price  : Upbit 실제 체결가 (KRW)
binance_fill_price: Binance 실제 체결가 (USDT)
TETHER            : USD/KRW 환율 (consts.py, 현재 1330)
```

라이브에서는 실제 체결가에 환율을 곱하여 정확한 김프(%) 계산.

---

## 수익 모델

### 기본 구조
```
수익(%) = (청산 김프 - 진입 김프) - 수수료

수수료 = Upbit 매수 수수료 + Upbit 매도 수수료
       + Binance 숏 진입 수수료 + Binance 숏 정리 수수료
       = 0.05% × 4 = 0.20%
```

### 예시
```
진입: open_gimp = 2.0%
  → Upbit에서 BTC를 KRW로 매수
  → Binance에서 BTC 선물 숏

청산: close_gimp = 2.5%
  → Upbit에서 BTC를 KRW로 매도
  → Binance에서 BTC 선물 숏 정리

총수익 = 2.5% - 2.0% = 0.5%
순수익 = 0.5% - 0.2% (수수료) = 0.3%
```

---

## VWAP 기반 슬리피지 모델

시장가 주문은 호가 깊이에 따라 체결가가 달라진다.

### Orderbook Depth VWAP
```
주문 금액: Q = BALANCE × OPEN_INSTALLMENT

호가창:
  Level 1: 가격 P1, 수량 V1
  Level 2: 가격 P2, 수량 V2
  ...

VWAP = Σ(Pi × min(Vi, 잔여수량)) / Q
```

`checkOrderbook.py`에서 `balance_bid_average`와 `balance_ask_average`로 계산.

### 슬리피지
```
slippage = |실제 체결가 - 최우선 호가| / 최우선 호가 × 100
```

---

## 2x 레버리지 자본 효율 모델

### 현재 (1x:1x)
```
1억 포지션 기준:
  Upbit 현물: 1억 KRW (매수)
  Binance 선물: ~$75,000 (1x 숏, 마진 100%)
  필요 자본: ~2억 KRW
```

### 목표 (1x:2x)
```
1억 포지션 기준:
  Upbit 현물: 1억 KRW (매수)
  Binance 선물: ~$75,000 (2x 숏, 마진 50%)
  필요 자본: ~1.5억 KRW
  자본 효율: 25% 개선
```

### 펀딩비 수익
```
펀딩비 = 포지션 크기 × 펀딩율
  → 상승장에서 숏 포지션은 펀딩비를 수취
  → 8시간마다 정산
  → 월간 추가 수익: 0.3-0.5% (시장 상황에 따라 변동)

2x 레버리지 시: 펀딩비 수익 × 2
```

---

## 분할 진입/청산 모델

### 분할 진입
```
1회 진입 금액 = BALANCE × OPEN_INSTALLMENT (33%)
최대 분할 횟수 = 3 (100% 소진)

가중평균 진입 김프:
  position_avg_gimp = Σ(gimpi × amounti) / Σ(amounti)
```

### 청산
```
현재: CLOSE_INSTALLMENT = 1.0 (일괄 청산)

청산 수익:
  profit = (close_gimp - position_avg_gimp) × position_amount
  net_profit = profit - (UPBIT_FEE + BINANCE_FEE) × 2 × position_amount
```
