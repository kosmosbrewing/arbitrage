# 7-Stage Entry Filter Chain

> Created: 2026-04-06
> Updated: 2026-04-06
> Status: ✅ Confirmed
> Source: `compareprice/comparePriceOpenOrder.py`

---

## 개요

진입은 7개의 독립적인 필터를 순차 통과해야만 실행된다.
각 필터는 `continue`(스킵) 조건으로 구현되어 있다 — 조건에 걸리면 해당 티커를 건너뛴다.

```
orderbook_check + exchange_data (for문: 티커 순회)
  │
  ├─① Balance > 0 ──────── NO → skip
  ├─② Top Ticker 포함 ──── NO → skip
  ├─③ Trailing Stop ────── tracking (저점 추적)
  ├─④ Spread 과대 ─────── YES(> CURR_GIMP_GAP) → skip
  ├─⑤ BTC 괴리 과대 ───── YES(< open_gimp - 0.75) → skip
  ├─⑥ RSI 조건 미충족 ─── YES → skip (+ open_limit_count 누적)
  │    └─ open_limit_count < 75 → 누적 후 continue
  ├─⑦ TS count < 5 ────── YES → skip
  ├─  주문금액 잔고 초과 ── YES → skip
  │
  ▼
  ENTRY EXECUTION
```

---

## 상세

### ① Balance Check
```python
if remain_bid_balance['balance'] < 0:
    continue
```
- **1차 체크**: 잔고가 음수인지 확인 (대략적 필터)
- **2차 체크**: 실제 주문 금액 차감 후 잔고 음수 여부 재확인
- 두 단계로 나뉘어 있음에 주의

### ② Top Ticker Filter
```python
if ticker not in exchange_data['upbit_top_ticker']:
    continue
```
- Upbit 15분 누적 거래량 상위 티커만 진입 대상
- `upbit.accum_top_ticker()`에서 `GET_TOP_TICKER_DELAY`(1시간) 주기로 갱신
- 유동성 부족 티커 자동 제외

### ③ Trailing Stop Tracking
```python
# 초기화
if 'open_min_gimp' not in position_data[ticker] or position_data[ticker]['open_min_gimp'] == 0:
    position_data[ticker]['open_min_gimp'] = open_gimp
    position_data[ticker]['open_stop_gimp'] = open_gimp + OPEN_TS_GRID
    position_data[ticker]['open_ts_count'] = 0

# 저점 갱신
if open_gimp < position_data[ticker]['open_min_gimp']:
    position_data[ticker]['open_min_gimp'] = open_gimp
    position_data[ticker]['open_stop_gimp'] = open_gimp + OPEN_TS_GRID
    position_data[ticker]['open_ts_count'] = 0  # 리셋
```
- 진입 김프의 저점(`open_min_gimp`)을 지속 추적
- 새 저점이 나올 때마다 stop 기준과 카운트를 리셋
- "떨어지다가 올라오기 시작할 때" 포착하는 역할

### ④ Spread Check — **스킵 조건**
```python
if open_gimp - close_gimp > CURR_GIMP_GAP:  # 0.2%
    continue  # 스프레드 과대 → 스킵
```
- `open_gimp - close_gimp`는 매수/매도 김프 간 스프레드 (실행 비용)
- 스프레드가 `CURR_GIMP_GAP`(0.2%)보다 **크면** 실행 비용이 과대하므로 **스킵**
- 스프레드가 작을수록 실행 효율이 높아 진입에 유리

### ⑤ BTC Anchor — **스킵 조건**
```python
if btc_open_gimp < open_gimp - 0.75:
    continue  # BTC 대비 괴리 과대 → 스킵
```
- `btc_open_gimp < open_gimp - 0.75`: BTC 김프가 해당 티커 김프보다 0.75% 이상 낮음
- 참고: `consts.py`에 `BTC_GAP = 1.2`가 정의되어 있지만, 현재 진입 로직은 이 상수를 사용하지 않고 `0.75`를 하드코딩한다.
- 의미: 해당 알트코인이 BTC 대비 과도하게 김프가 높은 상태
- 알트코인 단독 과열은 구조적 김프가 아닌 일시적 왜곡 가능성 → 스킵

### ⑥ RSI Filters (lines 93-134) — **가장 복잡한 필터**

`open_limit_count`가 `OPEN_LIMIT_COUNT`(75) 미만이면 RSI 조건을 체크하고 카운트를 누적한 뒤 `continue`. 75에 도달해야 다음 단계로 진행.
추가로 `position_data[ticker]['open_install_count'] != 0`이면 이미 진입 중인 티커로 간주하고 RSI 이전에 스킵한다.

#### 4시간 RSI (lines 98-131)
```python
# 과매도: 양쪽 모두 <= 35 → 급락 중, 스킵
if upbit_240_rsi <= 35 and binance_240_rsi <= 35:
    open_limit_count = 0  # 리셋
    continue

# 과매수: 양쪽 모두 >= 65 → 240/15 RSI GAP 둘 다 확인
elif upbit_240_rsi >= 65 and binance_240_rsi >= 65:
    if rsi_15_gap > 0:          # 15m Upbit 과열 → 리셋
        open_limit_count = 0
    if rsi_240_gap > -1 or rsi_15_gap > -1:  # 둘 중 하나라도 GAP 부족 → 스킵
        continue
    close_mode = 0  # 보수적 청산
```

#### 15분 RSI (4h가 중립 35~65일 때, lines 112-131)
```python
# 15m 양쪽 <= 35 → 급락, 스킵
# 15m 양쪽 >= 65 → rsi_15_gap > -1이면 스킵
# 15m 중립 → rsi_15_gap > -3이면 스킵

# close_mode 결정:
if rsi_240_gap > 1.5:
    close_mode = 1  # 공격적 (4h 갭 넓으면 빠른 회전)
else:
    close_mode = 2  # 균형
```

**핵심**: RSI GAP이 음수(= Binance RSI가 Upbit보다 높음)일수록 진입에 유리.
음수 갭이 클수록(< -1, < -3) 더 쉽게 필터를 통과한다.

### ⑦ TS Confirmation
```python
if open_gimp > position_data[ticker]['open_stop_gimp']:
    position_data[ticker]['open_ts_count'] += 1

if position_data[ticker]['open_ts_count'] < OPEN_TS_COUNT:  # 5
    continue
```
- 김프가 `open_stop_gimp`(저점 + 0.15%)를 넘으면 카운트 +1
- 5회 이상 확인되어야 진입 → 일시적 반등(1-2회)은 노이즈로 간주

---

## Dynamic Target Grid

진입 시 `close_mode`(RSI 필터에서 결정)에 따라 청산 목표가 달라진다.

| close_mode | target_grid | 산출 | 전략 |
|---|---|---|---|
| 0 | 0.6% | `CLOSE_GIMP_GAP + 0.1` | 보수적 — 4h 과매수 구간, 넓은 갭 |
| 1 | 0.4% | `CLOSE_GIMP_GAP - 0.1` | 공격적 — 4h RSI GAP 넓음, 빠른 회전 |
| 2 | 0.5% | `CLOSE_GIMP_GAP` | 균형 — 기본 설정 |

`CLOSE_GIMP_GAP`(현재 0.5%)이 변경되면 target_grid도 연동된다.
텔레그램 `/set_close` 명령으로 실시간 변경 가능.

---

## 가중평균 포지션 김프 (lines 201-205)

분할 진입 시 포지션 김프는 가중평균으로 계산:

```python
temp_gimp = 0
for i in range(len(position_gimp_acc_weight)):
    weight = position_gimp_acc_weight[i] / sum(position_gimp_acc_weight)
    temp_gimp += position_gimp_acc[i] * weight
position_data[ticker]['position_gimp'] = round(temp_gimp, 3)
```

각 분할 진입의 `OPEN_INSTALLMENT`(0.33) 비중으로 가중평균.
이 가중평균 김프가 청산 시 기준(`position_gimp`)이 된다.
