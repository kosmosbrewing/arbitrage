# STRATEGY.md — Quick Reference

> Updated: 2026-04-06
> Purpose: 현재 전략 파라미터와 진입/청산 로직 quick reference

---

## 핵심 파라미터

### 자본/포지션
| 파라미터 | 값 | 설명 |
|---|---|---|
| `BALANCE` | 1억 KRW | 총 투자금 (Upbit 기준) |
| `LEVERAGE` | 1x | Binance 선물 레버리지 |
| `POSITION_MAX_COUNT` | 4 | 최대 동시 포지션 |
| `TETHER` | 1,330 | 고정 환율 (KRW/USD) |

### 진입 조건
| 파라미터 | 값 | 설명 |
|---|---|---|
| `CURR_GIMP_GAP` | 0.2% | open_gimp - close_gimp 허용 최대 스프레드 |
| `OPEN_INSTALLMENT` | 0.33 | 분할 진입 비율 (잔고의 33%) |
| `OPEN_GIMP_GAP` | 0.15% | 변동성 카운트 김프 조건 |
| `OPEN_GIMP_COUNT` | 3 | 변동성 카운트 횟수 |
| `BTC_GAP` | 1.2% | 상수 정의값. 현재 진입 로직은 이 값 대신 `0.75`를 하드코딩 사용 |
| `OPEN_TS_GRID` | 0.15% | 진입 Trailing Stop 그리드 |
| `OPEN_TS_COUNT` | 5 | 진입 TS 확인 횟수 |

### 청산 조건
| 파라미터 | 값 | 설명 |
|---|---|---|
| `CLOSE_GIMP_GAP` | 0.5% | 기본 청산 김프 갭 |
| `CLOSE_INSTALLMENT` | 1.0 | 청산 비율 (100% 일괄) |
| `CLOSE_TS_GRID` | 0.15% | 청산 Trailing Stop 그리드 |
| `CLOSE_TS_COUNT` | 5 | 청산 TS 확인 횟수 |

### 수수료
| 항목 | 값 |
|---|---|
| Upbit 수수료 | 0.05% |
| Binance 수수료 | 0.05% |
| 왕복 수수료 합계 | ~0.2% |

---

## 진입 로직 (comparePriceOpenOrder.py)

### 7단계 필터 체인
```
① Balance     → remain_bid_balance < 0 시 스킵 (1차) + 실제 주문금액 차감 가능 여부 확인 (2차)
② Top Ticker  → exchange_data['upbit_top_ticker']에 포함
③ Trailing    → open_min_gimp 추적 → open_stop_gimp 계산
④ Spread      → open_gimp - close_gimp <= CURR_GIMP_GAP (스프레드 과대 시 스킵)
⑤ BTC Anchor  → btc_open_gimp >= open_gimp - 0.75 (BTC 대비 과도한 괴리 시 스킵)
⑥ RSI Filter  → 4h RSI: 양쪽 거래소 <= 35 시 스킵 + 카운트 리셋
                 4h RSI: 양쪽 거래소 >= 65 시 240/15 RSI GAP 둘 다 확인
                 15m RSI: 4h 중립 구간에서 <= 35 스킵, >= 65 / 중립 각각 다른 GAP 적용
⑦ TS Confirm  → open_ts_count >= OPEN_TS_COUNT (5회)
```

### RSI GAP 시그널
```
RSI GAP = Upbit RSI - Binance RSI

RSI GAP > 0: Upbit 과열 → open_limit_count 리셋 (재카운트)
RSI GAP < -1 (4h) 또는 < -1/-3 (15m): 진입 허용
RSI GAP 양수 구간이 클수록 진입 보수적

* 4h RSI: 양쪽 모두 <= 35 또는 >= 65일 때만 적용
* 15m RSI: 4h가 중립(35~65)일 때 적용
```

### 김프 계산 모드
```
시뮬레이션:
  open_gimp  = Upbit ask / Binance bid × 100 - 100
  close_gimp = Upbit bid / Binance ask × 100 - 100

라이브 체결 후:
  order_open_gimp = upbit_price / (binance_price × TETHER) × 100 - 100
```

주의: 시뮬레이션의 `open_gimp`/`close_gimp`는 절대 김프(%)가 아니라 교차환율 비율이다.
티커 간 상대 비교와 진입-청산 간 차이 계산 용도로만 해석한다.

### Dynamic Target Grid (close_mode별)
| close_mode | target_grid | 설명 |
|---|---|---|
| 0 (기본) | 0.6% | 보수적 |
| 1 (공격) | 0.4% | 빠른 회전 |
| 2 (중립) | 0.5% | 균형 |

---

## 청산 로직 (comparePriceCloseOrder.py)

### 4-Trigger 청산 (하나라도 충족 시 청산)
```
① Target Gap    → close_gimp - position_gimp >= target_grid
② Forced Close  → order_flag 또는 텔레그램 /order close 명령
③ Stop-Loss     → stop_loss_count >= 5 (at -0.3%)
④ Close TS      → close_ts_count >= CLOSE_TS_COUNT (5회)
```

### Trailing Stop 메커니즘
```
진입 TS:
  open_min_gimp = min(open_min_gimp, current_open_gimp)
  open_stop_gimp = open_min_gimp + OPEN_TS_GRID
  if current > open_stop_gimp → open_ts_count++

청산 TS:
  close_max_gimp = max(close_max_gimp, current_close_gimp)
  close_stop_gimp = close_max_gimp - CLOSE_TS_GRID
  if current < close_stop_gimp → close_ts_count++
```

---

## 슬리피지 관리

### 4-Layer 시스템
| Layer | 위치 | 역할 |
|---|---|---|
| VWAP | `checkOrderbook.py` | 주문 크기 기반 예상 체결가 계산 |
| Spread Filter | `comparePriceOpenOrder.py` | 매수/매도 김프 스프레드 확인 |
| Min Notional | `comparePriceOpenOrder.py` | 최소 거래 금액 확인 |
| Post-Trade | `comparePriceOpenOrder.py` | 체결 후 실제 슬리피지 측정 |

---

## 수익 구조

### Per-Trade
```
매수 시 김프: 2.0% (예시)
매도 시 김프: 2.5% (예시)
총 수익: 0.5%
수수료 차감: -0.2% (Upbit 0.05% × 2 + Binance 0.05% × 2)
순수익: ~0.3%
```

### Monthly (추정)
```
회전율: 10-15회/월
Per-Trade 순수익: 0.25-0.3%
월간: 2.5-4.5%
+ 펀딩비 수익: 0.3-0.5%/월 (상승장)
합계: 3-5%/월
```
