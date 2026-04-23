# ARCHITECTURE.md — Kimchi Premium Arbitrage Bot

> 이 문서는 모듈 구조, 의존성 방향, 데이터 흐름을 정의한다.
> 새 파일 생성 전 반드시 이 문서의 의존성 규칙을 확인하라.

---

## 1. 3-프로세스 아키텍처

```text
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   main.py       │  │ collectMain.py  │  │ commandMain.py  │
│   (트레이딩 봇)  │  │ (데이터 수집)    │  │ (텔레그램 명령)  │
│                 │  │                 │  │                 │
│ 12 async tasks  │  │  7 async tasks  │  │  aiogram router │
│ 주문 실행       │  │  로깅 전용       │  │  원격 제어       │
└─────────────────┘  └─────────────────┘  └─────────────────┘
        │                    │                     │
        └────────────────────┼─────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  공유 상태       │
                    │  .DAT / .json   │
                    │  파일 기반 영속화 │
                    └─────────────────┘
```

각 프로세스는 독립 실행되며, 파일 기반으로 상태를 공유한다.

## 2. 모듈 맵 (16개)

| 모듈 | 책임 | 핵심 함수/클래스 |
|---|---|---|
| **consts.py** | 설정 상수, 환경변수 | `ENV`, `BALANCE`, `LEVERAGE`, 모든 파라미터 |
| **util.py** | 텔레그램, 파일 I/O, 로깅, 수익 리포트 | `send_to_telegram()`, `load_*/put_*` 시리즈 |
| **main.py** | 메인 트레이딩 봇 (주문 실행) | `Premium` 클래스, 12 async tasks |
| **collectMain.py** | 데이터 수집 전용 봇 | 7 async tasks, 로깅 전용 |
| **commandMain.py** | 텔레그램 명령어 처리 | aiogram 핸들러, `/current`, `/graph`, `/order` |
| **api/upbit.py** | Upbit 현물 API + WebSocket | `spot_order()`, `check_order()`, `accum_top_ticker()` |
| **api/binance.py** | Binance 선물 API + WebSocket | `futures_order()`, `check_order()`, `funding_fee()` |
| **api/bithumb.py** | Bithumb USDT/KRW 가격 조회 | `get_usdt_price()` |
| **api/hana.py** | 하나은행 USD/KRW 환율 조회 | `get_currency_data()` |
| **api/checkOrderbook.py** | 호가 데이터 검증 + VWAP 계산 | `check_orderbook()`, `get_common_orderbook_ticker()` |
| **api/checkRealGimp.py** | 실시간 김프 계산 (실환율 기반) | `check_real_gimp()` |
| **api/checkRSI.py** | RSI 지표 계산 (15m/4h) | `check_15_rsi()`, `check_240_rsi()`, `rsi()` |
| **compareprice/comparePrice.py** | 김프 비교 분석 (로깅 전용) | `compare_price()` |
| **compareprice/comparePriceCheck.py** | 포지션 상태 초기화/추적 | `compare_price_check()` |
| **compareprice/comparePriceOpenOrder.py** | 진입 주문 로직 (7단계 필터) | `compare_price_open_order()` |
| **compareprice/comparePriceCloseOrder.py** | 청산 주문 로직 (4-trigger) | `compare_price_close_order()` |

### 보조 모듈

| 모듈 | 책임 |
|---|---|
| **backtest/** | 백테스트 엔진 (4 파일) |
| **graph/** | 김프 변동 시각화 (6 파일) |
| **crawl/** | Upbit 신규 상장 모니터링 |
| **bin/** | 운영 셸 스크립트 (16 파일) |

## 3. 의존성 방향 규칙

```
                    ┌─────────────┐
                    │ consts.py   │ ← 모든 모듈이 참조 가능
                    │ (설정 상수)  │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌─────▼──────┐  ┌──────▼──────┐
   │ api/upbit   │  │ api/binance│  │ api/hana    │  ← 거래소/외부 API 레이어
   │ api/bithumb │  │            │  │             │
   └─────────────┘  └────────────┘  └─────────────┘
          │                │                │
          └────────┬───────┘                │
                   │                        │
          ┌────────▼────────┐               │
          │ api/check*      │◄──────────────┘  ← 데이터 가공 레이어
          │ (Orderbook,     │
          │  RealGimp, RSI) │
          └────────┬────────┘
                   │
          ┌────────▼────────┐
          │ compareprice/   │  ← 전략/주문 레이어
          │ (Open, Close,   │
          │  Check, Compare)│
          └────────┬────────┘
                   │
   ┌───────────────┼───────────────┐
   │               │               │
┌──▼──┐      ┌────▼────┐    ┌─────▼─────┐
│main │      │collect  │    │command    │  ← 엔트리포인트 레이어
│.py  │      │Main.py  │    │Main.py    │
└─────┘      └─────────┘    └───────────┘

독립 모듈 (엔트리포인트에서만 호출):
  util.py       ← consts.py, api/hana.py 참조 (⚠️ api/ 의존 존재)
  backtest/     ← api/, consts.py 참조 (런타임과 격리)
  graph/        ← util.py 참조
  crawl/        ← 독립
```

### 금지 규칙

| 금지 | 이유 |
|---|---|
| compareprice/ → main.py | 전략이 엔트리포인트에 의존하면 안 됨 |
| api/ → compareprice/ | API 레이어가 전략에 의존하면 안 됨 |
| consts.py → 다른 모듈 | 설정은 독립적이어야 함 |
| backtest/ → compareprice/ | 백테스트는 런타임과 격리해야 함 |

### ⚠️ 알려진 의존성 위반

```
util.py → api/hana.py (get_currency_data 호출)
```

**현상:** util.py가 환율 조회를 위해 api/hana.py를 직접 import. 현재 런타임 문제 없음.
**향후 해결:** 환율 데이터를 exchange_data에 주입하는 방식으로 역전하거나, util.py에서 hana 의존을 제거.

## 4. 데이터 흐름

### 실시간 데이터 수집
```
Upbit WebSocket    ──→ orderbook_info['Upbit'][ticker]
Binance WebSocket  ──→ orderbook_info['Binance'][ticker]
하나은행 POST      ──→ exchange_data['dollar']
Bithumb REST       ──→ exchange_data['bithumb_usdt']
Upbit REST (누적)  ──→ exchange_data['upbit_top_ticker']
```

### 호가 가공
```
orderbook_info → checkOrderbook.check_orderbook()
  → orderbook_check[ticker]['Upbit_bid']          # 매수 최우선가
  → orderbook_check[ticker]['Binance_ask']         # 매도 최우선가
  → orderbook_check[ticker]['balance_bid_average']  # VWAP (주문 크기 기반)
  → orderbook_check[ticker]['balance_ask_average']  # VWAP (주문 크기 기반)
```

### 김프 계산
```
# 시뮬레이션 모드: VWAP 가격 직접 나눗셈 (KRW/USDT 비율)
open_gimp  = (Upbit_balance_ask_avg / Binance_balance_bid_avg) × 100 - 100
close_gimp = (Upbit_balance_bid_avg / Binance_balance_ask_avg) × 100 - 100

# 라이브 모드: 체결 후 Binance 가격에 TETHER(환율) 곱셈
order_open_gimp = upbit_price / (binance_price × TETHER) × 100 - 100

gimp_gap = close_gimp - position_gimp  # 수익률
```

주의: 시뮬레이션 모드에서 `open_gimp`/`close_gimp`는 절대 김프(%)가 아니라 교차환율 비율이다.
티커 간 상대비교, 진입-청산 간 차이 계산에서만 의미 있다.

### 진입 흐름 (comparePriceOpenOrder)
```
orderbook_check + exchange_data
  → Balance < 0 skip (1차 체크)
  → Top Ticker Filter (상위 거래량 티커만)
  → Trailing Stop Tracking (open_min_gimp → open_stop_gimp)
  → Spread Skip (open_gimp - close_gimp > CURR_GIMP_GAP → 스프레드 과대, 스킵)
  → BTC Anchor Skip (btc_open_gimp < open_gimp - 0.75 → BTC 괴리 과대, 스킵)
  → Existing Position Skip (open_install_count != 0 → 스킵)
  → RSI Filters (양쪽 4h<=35 스킵/리셋, 양쪽 4h>=65면 240/15 GAP 확인, 그 외 15m 분기)
  → open_limit_count 누적 → OPEN_LIMIT_COUNT(75) 도달 시 진행
  → TS Confirmation (open_ts_count >= OPEN_TS_COUNT)
  → 주문금액 잔고 차감 가능 확인 (2차 체크)
  → asyncio.gather(upbit.spot_order, binance.futures_order) [라이브]
  → check_order() × 2 → 슬리피지 측정 → 포지션 기록
```

### 청산 흐름 (comparePriceCloseOrder)
```
position_data + orderbook_check
  → Target Gimp Gap (close_gimp - position_gimp >= target_grid)
  → Forced Close Flag 확인
  → Stop-Loss (count >= 5 at -0.3%)
  → Close Trailing Stop (close_ts_count >= CLOSE_TS_COUNT)
  → asyncio.gather(upbit.spot_order, binance.futures_order)
  → P&L 계산 → 수수료 차감 → 수익 영속화
```

## 5. 공유 상태 객체

### 인메모리 (Premium 클래스 인스턴스)
| 객체 | 용도 |
|---|---|
| `exchange_data` | 환율, RSI, 탑 티커, 실시간 김프 |
| `orderbook_info` | 원본 호가 데이터 (WebSocket) |
| `orderbook_check` | 가공된 호가 + VWAP |
| `position_data` | 포지션 상태 (진입 여부, 김프, 수량) |
| `trade_data` | 거래 데이터 (진입가, 수량, 분할 카운트) |
| `check_data` | 변동성 신호, trailing stop 상태 |
| `remain_bid_balance` | 잔여 투자 가능 금액 |
| `position_ticker_count` | 현재 포지션 개수 |
| `order_flag` | 주문 실행 중 동시 진입 방지 플래그 |

### 파일 기반 영속화
| 파일 | 용도 | 포맷 |
|---|---|---|
| `data/position_data.DAT` | 포지션 복구 | Python repr |
| `data/orderbook_check.DAT` | 호가 스냅샷 | Python repr |
| `data/order_flag.json` | 주문 플래그 | JSON |
| `data/chat_id.DAT` | 텔레그램 채팅 ID | 텍스트 |
| `data/low_gimp.DAT` | 저점 김프 데이터 | Python repr |
| `data/profit_data_*.DAT` | 월별 수익 누적 | Python repr |

## 6. 주문 실행 모델

### 듀얼 모드
- **라이브 모드**: `asyncio.gather(upbit.spot_order, binance.futures_order)` → 동시 체결 → `check_order()` 검증
- **시뮬레이션 모드**: 호가 가격 직접 사용, API 호출 없음
- 토글: Python 삼중 따옴표(`'''...'''`) 블록으로 코드 전환

### 인증
| 거래소 | 방식 | 구현 |
|---|---|---|
| Upbit | JWT (SHA512) | `api/upbit.py:spot_order()` |
| Binance | HMAC-SHA256 | `api/binance.py:futures_order()` |

### 4-Layer 슬리피지 관리
1. **Orderbook Depth VWAP**: 주문 크기만큼의 호가 깊이를 시뮬레이션하여 예상 체결가 계산
2. **Bid-Ask Spread Filter**: open_gimp - close_gimp 스프레드가 임계값 이상인지 확인
3. **Min Notional Check**: 최소 거래 금액 충족 검증
4. **Post-Trade Measurement**: 체결 후 실제 슬리피지 측정 및 기록
