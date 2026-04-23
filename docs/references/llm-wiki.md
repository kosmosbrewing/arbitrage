# LLM Wiki — 프로젝트 레퍼런스

> Purpose: LLM 에이전트가 이 프로젝트를 빠르게 이해하기 위한 참조 문서
> Updated: 2026-04-06

---

## 한 줄 요약

Upbit(한국 거래소) 현물 매수 + Binance(글로벌 거래소) 선물 숏으로 김프(Korea Premium) 차익을 자동 수익화하는 Python 봇.

---

## 도메인 용어

| 용어 | 영문 | 설명 |
|---|---|---|
| 김프 | Korea Premium | 한국 거래소와 글로벌 거래소 간 가격 차이 (%) |
| 진입 김프 | Open Premium | 매수 시점의 김프 (Upbit ask / Binance bid) |
| 청산 김프 | Close Premium | 매도 시점의 김프 (Upbit bid / Binance ask) |
| 김프 갭 | Gimp Gap | 청산 김프 - 진입 김프 = 예상 수익 |
| 호가 | Orderbook | 매수/매도 주문 대기 목록 |
| VWAP | Volume Weighted Avg Price | 거래량 가중 평균가 |
| RSI GAP | RSI Gap | Upbit RSI - Binance RSI (한국 시장 과열 지표) |
| Trailing Stop (TS) | Trailing Stop | 저점/고점 추적 후 반전 시 실행 |
| 분할 진입 | Installment Trading | 자금을 나눠서 단계적 진입 |
| 펀딩비 | Funding Fee | 선물 시장에서 롱/숏 간 주기적 정산 비용 |
| 랜딩 | Lending | 보유 자산을 빌려주고 이자를 받는 서비스 |

---

## 프로세스 구조

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ main.py     │     │collectMain  │     │commandMain  │
│ 트레이딩     │     │ 데이터 수집  │     │ 텔레그램     │
│ 12 tasks    │     │ 7 tasks     │     │ aiogram     │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────── .DAT/.json 파일 공유 ─────────┘
```

3개 프로세스는 **독립 실행**되며, `.DAT`/`.json` 파일로 상태를 공유한다.

---

## 코드 진입점

| 작업 | 파일 | 설명 |
|---|---|---|
| 전략 이해 | `compareprice/comparePriceOpenOrder.py` | 7단계 진입 필터, 핵심 전략 로직 |
| 청산 이해 | `compareprice/comparePriceCloseOrder.py` | 4-trigger 청산 로직 |
| 설정 확인 | `consts.py` | 모든 파라미터 |
| 주문 실행 | `api/upbit.py`, `api/binance.py` | REST API 주문 + WebSocket |
| 슬리피지 | `api/checkOrderbook.py` | VWAP 계산 |
| RSI | `api/checkRSI.py` | RSI 계산 + RSI GAP |
| 유틸리티 | `util.py` | 텔레그램, 파일 I/O, 로깅 |

---

## 주요 데이터 흐름

```
1. WebSocket → orderbook_info (실시간 호가)
2. orderbook_info → checkOrderbook → orderbook_check (VWAP 포함)
3. orderbook_check → comparePriceOpenOrder (진입 판단)
4. orderbook_check → comparePriceCloseOrder (청산 판단)
5. 주문 실행 → position_data / trade_data (상태 갱신)
6. position_data → .DAT 파일 (영속화)
```

---

## 듀얼 모드

코드에 **라이브 모드**와 **시뮬레이션 모드**가 공존한다.

- 라이브: Python 삼중 따옴표(`'''...'''`)로 감싸진 블록 → 주석 해제하면 실제 API 호출
- 시뮬레이션: 현재 활성 코드 → 호가 가격 직접 사용, API 호출 없음

전환 방법: 삼중 따옴표를 추가/제거하여 활성 블록을 토글.

### 김프 계산 해석
- 시뮬레이션: `open_gimp = Upbit ask / Binance bid × 100 - 100`
- 라이브 체결 후: `order_open_gimp = upbit_price / (binance_price × TETHER) × 100 - 100`
- 해석 주의: 시뮬레이션의 `open_gimp`/`close_gimp`는 절대 환산 김프가 아니라 상대 비교용 비율이다.

---

## 알려진 주의사항

1. **최근 해결됨 (2026-04-06)**: `eval()` 제거, Telegram 토큰/Chat ID 환경변수화, RSI 초기화 오류 수정, ETH/XRP 스왑 수정, deprecated timestamp 수정, `main.py` 비교 버그 수정
2. **데드코드**: `bithumb.py:60-162` (upbit.py에서 복사된 미사용 코드)
3. **출력 정리 필요**: `commandMain.py`, `graph/`, `backtest/`, `crawl/`에 `print()` 기반 디버그/도구 코드 다수
4. **중복 헬퍼**: `checkRSI.get_duplicate_ticker()` — `checkOrderbook.get_common_orderbook_ticker()`와 역할 중복
5. **필터 로직**: 코드의 필터는 **스킵 조건**(`continue`)으로 구현됨 — "조건 충족 시 통과"가 아니라 "조건 충족 시 제외"

## 현재 P1 우선순위

1. TD-1~TD-6, TD-19 우선 해결: `eval()`, 토큰/Chat ID 하드코딩, RSI 변수 오류, ETH/XRP 스왑, `main.py` 비교 버그
2. 구조 검증 스크립트 추가: 파일 크기, `eval()`, `print()` 자동 검출
3. 대형 파일 분리: `util.py`, `commandMain.py`, `api/binance.py`

---

## 자주 참조하는 파라미터

| 파라미터 | 값 | 위치 | 의미 |
|---|---|---|---|
| `BALANCE` | 1억 | consts.py | 총 투자금 |
| `LEVERAGE` | 1 | consts.py | 선물 레버리지 |
| `POSITION_MAX_COUNT` | 4 | consts.py | 최대 동시 포지션 |
| `CURR_GIMP_GAP` | 0.2% | consts.py | 진입 시 허용 최대 스프레드 |
| `BTC_GAP` | 1.2% | consts.py | 정의는 존재하지만 현재 진입 로직은 `0.75` 하드코딩 사용 |
| `CLOSE_GIMP_GAP` | 0.5% | consts.py | 청산 목표 김프 갭 |
| `OPEN_TS_GRID` | 0.15% | consts.py | 진입 TS 그리드 |
| `CLOSE_TS_GRID` | 0.15% | consts.py | 청산 TS 그리드 |
| `OPEN_TS_COUNT` | 5 | consts.py | 진입 TS 확인 횟수 |
| `CLOSE_TS_COUNT` | 5 | consts.py | 청산 TS 확인 횟수 |
| `UPBIT_FEE` | 0.05% | consts.py | Upbit 수수료 |
| `BINANCE_FEE` | 0.05% | consts.py | Binance 수수료 |
| `TETHER` | 1,330 | consts.py | 고정 환율 |
